"""
Atlantis Persistence Layer
=======================
SQLite-based state management. Handles:
- Agent state persistence (knowledge, depth tiers)
- Constitutional document storage (versioned)
- System checkpoint/resume
- Full audit trail

If the system crashes, it resumes from last checkpoint.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional


class AtlantisDB:
    """SQLite persistence layer for Atlantis."""
    
    def __init__(self, db_path: str = "hydra.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
        self._create_tables()
    
    def _create_tables(self):
        """Create all tables if they don't exist."""
        self.conn.executescript("""
            -- System state
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            -- Agent state persistence
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                config_json TEXT NOT NULL,
                knowledge_json TEXT NOT NULL,
                total_tokens_used INTEGER DEFAULT 0,
                is_retired INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            -- Constitutional documents (versioned)
            CREATE TABLE IF NOT EXISTS constitutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                constitution_type TEXT NOT NULL,  -- 'federal' or 'state:{name}'
                version INTEGER NOT NULL,
                articles_json TEXT NOT NULL,
                ratified_by_json TEXT NOT NULL,
                ratified_at TEXT NOT NULL,
                is_current INTEGER DEFAULT 1
            );
            
            -- Constitutional articles (individual)
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                constitution_type TEXT NOT NULL,
                article_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                proposed_by TEXT NOT NULL,
                votes_json TEXT NOT NULL,
                ratified INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            
            -- Log entries (persistent audit trail)
            CREATE TABLE IF NOT EXISTS log_entries (
                id TEXT PRIMARY KEY,
                cycle INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                agents_json TEXT,
                messages_json TEXT,
                votes_json TEXT,
                outcome TEXT,
                total_tokens INTEGER DEFAULT 0,
                metadata_json TEXT,
                content_suggestions_json TEXT
            );
            
            -- System checkpoints
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle INTEGER NOT NULL,
                phase TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            
            -- States/Cities/Towns registry
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,  -- 'state', 'city', 'town'
                parent_id TEXT,             -- NULL for states
                domain TEXT NOT NULL,
                constitution_json TEXT,
                depth_tier INTEGER DEFAULT 0,
                created_at_cycle INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );

            -- State constitutions (detailed)
            CREATE TABLE IF NOT EXISTS state_constitutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                domain TEXT NOT NULL,
                knowledge_areas_json TEXT NOT NULL,
                governance_principles_json TEXT NOT NULL,
                research_methodology TEXT,
                federal_compliance_json TEXT NOT NULL,
                ratified_at_cycle INTEGER,
                created_at TEXT NOT NULL,
                is_current INTEGER DEFAULT 1
            );

            -- City charters
            CREATE TABLE IF NOT EXISTS city_charters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_id TEXT NOT NULL,
                parent_state_id TEXT NOT NULL,
                sub_domain TEXT NOT NULL,
                specialization TEXT,
                charter_text TEXT,
                state_compliance_json TEXT,
                federal_compliance_json TEXT,
                ratified_at_cycle INTEGER,
                created_at TEXT NOT NULL
            );

            -- Town charters
            CREATE TABLE IF NOT EXISTS town_charters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                town_id TEXT NOT NULL,
                parent_city_id TEXT NOT NULL,
                parent_state_id TEXT NOT NULL,
                hyper_topic TEXT NOT NULL,
                charter_text TEXT,
                city_compliance_json TEXT,
                state_compliance_json TEXT,
                federal_compliance_json TEXT,
                ratified_at_cycle INTEGER,
                created_at TEXT NOT NULL
            );

            -- Knowledge entries (research findings)
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                entry_id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                domain TEXT NOT NULL,
                tier INTEGER NOT NULL,
                concepts_json TEXT,
                frameworks_json TEXT,
                applications_json TEXT,
                synthesis TEXT,
                evidence TEXT,
                challenged_by TEXT,
                defense TEXT,
                cycle_created INTEGER NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );

            -- Federal Archive (curated knowledge for Senate/States to query)
            CREATE TABLE IF NOT EXISTS federal_archive (
                archive_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,      -- 'founder', 'state', 'city', 'town'
                source_id TEXT NOT NULL,        -- ID of originating entity
                domain TEXT NOT NULL,
                tier INTEGER NOT NULL,
                concepts_json TEXT,
                frameworks_json TEXT,
                applications_json TEXT,
                synthesis TEXT,
                evidence TEXT,
                deposited_at_cycle INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_log_cycle ON log_entries(cycle);
            CREATE INDEX IF NOT EXISTS idx_log_level ON log_entries(level);
            CREATE INDEX IF NOT EXISTS idx_log_category ON log_entries(category);
            CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
            CREATE INDEX IF NOT EXISTS idx_entities_parent ON entities(parent_id);
            CREATE INDEX IF NOT EXISTS idx_knowledge_entity ON knowledge_entries(entity_id);
            CREATE INDEX IF NOT EXISTS idx_knowledge_tier ON knowledge_entries(tier);
            CREATE INDEX IF NOT EXISTS idx_state_const_state ON state_constitutions(state_id);
            CREATE INDEX IF NOT EXISTS idx_city_charter_state ON city_charters(parent_state_id);
            CREATE INDEX IF NOT EXISTS idx_town_charter_city ON town_charters(parent_city_id);
            CREATE INDEX IF NOT EXISTS idx_archive_domain ON federal_archive(domain);
            CREATE INDEX IF NOT EXISTS idx_archive_source ON federal_archive(source_type);
            CREATE INDEX IF NOT EXISTS idx_archive_tier ON federal_archive(tier);
        """)
        self.conn.commit()
    
    # ─── System State ───
    
    def set_state(self, key: str, value) -> None:
        """Set a system state value."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT OR REPLACE INTO system_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), now)
        )
        self.conn.commit()
    
    def get_state(self, key: str, default=None):
        """Get a system state value."""
        row = self.conn.execute(
            "SELECT value FROM system_state WHERE key = ?", (key,)
        ).fetchone()
        if row:
            return json.loads(row["value"])
        return default
    
    # ─── Agent Persistence ───
    
    def save_agent(self, agent) -> None:
        """Save an agent's state to the database."""
        now = datetime.now(timezone.utc).isoformat()
        knowledge = {k: v.to_dict() for k, v in agent.knowledge.items()}
        
        self.conn.execute("""
            INSERT OR REPLACE INTO agents 
            (agent_id, name, agent_type, config_json, knowledge_json, 
             total_tokens_used, is_retired, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 
                    COALESCE((SELECT created_at FROM agents WHERE agent_id = ?), ?), ?)
        """, (
            agent.id, agent.name, agent.config.agent_type,
            json.dumps(agent.config.to_dict()),
            json.dumps(knowledge),
            agent.total_tokens_used, 0, agent.id, now, now
        ))
        self.conn.commit()
    
    def retire_agent(self, agent_id: str) -> None:
        """Mark an agent as retired."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE agents SET is_retired = 1, updated_at = ? WHERE agent_id = ?",
            (now, agent_id)
        )
        self.conn.commit()
    
    def get_agent_state(self, agent_id: str) -> Optional[dict]:
        """Get saved agent state."""
        row = self.conn.execute(
            "SELECT * FROM agents WHERE agent_id = ?", (agent_id,)
        ).fetchone()
        if row:
            return {
                "agent_id": row["agent_id"],
                "name": row["name"],
                "config": json.loads(row["config_json"]),
                "knowledge": json.loads(row["knowledge_json"]),
                "total_tokens_used": row["total_tokens_used"],
                "is_retired": bool(row["is_retired"]),
            }
        return None
    
    # ─── Constitutional Documents ───
    
    def save_article(self, constitution_type: str, article_number: int,
                     title: str, text: str, proposed_by: str,
                     votes: dict, ratified: bool) -> None:
        """Save a constitutional article."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute("""
            INSERT INTO articles 
            (constitution_type, article_number, title, text, proposed_by, votes_json, ratified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (constitution_type, article_number, title, text, proposed_by,
              json.dumps(votes), int(ratified), now))
        self.conn.commit()
    
    def save_constitution(self, constitution_type: str, articles: list[dict],
                          ratified_by: dict) -> None:
        """Save a ratified constitution."""
        now = datetime.now(timezone.utc).isoformat()
        # Mark previous versions as non-current
        self.conn.execute(
            "UPDATE constitutions SET is_current = 0 WHERE constitution_type = ?",
            (constitution_type,)
        )
        # Get next version number
        row = self.conn.execute(
            "SELECT MAX(version) as max_v FROM constitutions WHERE constitution_type = ?",
            (constitution_type,)
        ).fetchone()
        version = (row["max_v"] or 0) + 1
        
        self.conn.execute("""
            INSERT INTO constitutions (constitution_type, version, articles_json, ratified_by_json, ratified_at)
            VALUES (?, ?, ?, ?, ?)
        """, (constitution_type, version, json.dumps(articles), json.dumps(ratified_by), now))
        self.conn.commit()
    
    def get_constitution(self, constitution_type: str = "federal") -> Optional[dict]:
        """Get the current constitution."""
        row = self.conn.execute(
            "SELECT * FROM constitutions WHERE constitution_type = ? AND is_current = 1",
            (constitution_type,)
        ).fetchone()
        if row:
            return {
                "type": row["constitution_type"],
                "version": row["version"],
                "articles": json.loads(row["articles_json"]),
                "ratified_by": json.loads(row["ratified_by_json"]),
                "ratified_at": row["ratified_at"],
            }
        return None
    
    # ─── Log Persistence ───
    
    def save_log_entry(self, entry) -> None:
        """Persist a log entry to the database."""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO log_entries
                (id, cycle, timestamp, level, category, title, summary,
                 agents_json, messages_json, votes_json, outcome,
                 total_tokens, metadata_json, content_suggestions_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id, entry.cycle, entry.timestamp, entry.level,
                entry.category, entry.title, entry.summary,
                json.dumps(entry.agents_involved),
                json.dumps(entry.messages),
                json.dumps(entry.votes),
                entry.outcome, entry.total_tokens,
                json.dumps(entry.metadata),
                json.dumps(entry.content_suggestions)
            ))
            self.conn.commit()
        except Exception as e:
            print(f"[DB WARNING] Failed to save log entry {entry.id}: {e}")
    
    # ─── Checkpoints ───
    
    def save_checkpoint(self, cycle: int, phase: str, state: dict) -> None:
        """Save a system checkpoint for recovery."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO checkpoints (cycle, phase, state_json, created_at) VALUES (?, ?, ?, ?)",
            (cycle, phase, json.dumps(state), now)
        )
        self.conn.commit()
    
    def get_latest_checkpoint(self) -> Optional[dict]:
        """Get the most recent checkpoint."""
        row = self.conn.execute(
            "SELECT * FROM checkpoints ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            return {
                "cycle": row["cycle"],
                "phase": row["phase"],
                "state": json.loads(row["state_json"]),
                "created_at": row["created_at"],
            }
        return None
    
    # ─── Entity Registry ───
    
    def register_entity(self, entity_id: str, name: str, entity_type: str,
                        domain: str, cycle: int, parent_id: str = None) -> None:
        """Register a new State/City/Town."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute("""
            INSERT INTO entities (entity_id, name, entity_type, parent_id, domain,
                                  created_at_cycle, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entity_id, name, entity_type, parent_id, domain, cycle, now))
        self.conn.commit()
    
    def get_entities(self, entity_type: str = None) -> list[dict]:
        """Get all entities, optionally filtered by type."""
        if entity_type:
            rows = self.conn.execute(
                "SELECT * FROM entities WHERE entity_type = ? AND is_active = 1",
                (entity_type,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM entities WHERE is_active = 1"
            ).fetchall()
        return [dict(r) for r in rows]
    
    def get_entity_count(self, entity_type: str) -> int:
        """Count entities of a given type."""
        row = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM entities WHERE entity_type = ? AND is_active = 1",
            (entity_type,)
        ).fetchone()
        return row["cnt"]

    # ─── State Constitutions ───

    def save_state_constitution(self, state_id: str, constitution: dict) -> None:
        """Save a State constitution."""
        now = datetime.now(timezone.utc).isoformat()
        # Mark previous versions as non-current
        self.conn.execute(
            "UPDATE state_constitutions SET is_current = 0 WHERE state_id = ?",
            (state_id,)
        )
        # Get next version number
        row = self.conn.execute(
            "SELECT MAX(version) as max_v FROM state_constitutions WHERE state_id = ?",
            (state_id,)
        ).fetchone()
        version = (row["max_v"] or 0) + 1

        self.conn.execute("""
            INSERT INTO state_constitutions
            (state_id, version, domain, knowledge_areas_json, governance_principles_json,
             research_methodology, federal_compliance_json, ratified_at_cycle, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            state_id, version, constitution.get("domain", ""),
            json.dumps(constitution.get("knowledge_areas", [])),
            json.dumps(constitution.get("governance_principles", [])),
            constitution.get("research_methodology", ""),
            json.dumps(constitution.get("federal_compliance_check", {})),
            constitution.get("ratified_at_cycle", 0),
            now
        ))
        self.conn.commit()

    def get_state_constitution(self, state_id: str) -> Optional[dict]:
        """Get the current State constitution."""
        row = self.conn.execute(
            "SELECT * FROM state_constitutions WHERE state_id = ? AND is_current = 1",
            (state_id,)
        ).fetchone()
        if row:
            return {
                "state_name": state_id,
                "version": row["version"],
                "domain": row["domain"],
                "knowledge_areas": json.loads(row["knowledge_areas_json"]),
                "governance_principles": json.loads(row["governance_principles_json"]),
                "research_methodology": row["research_methodology"],
                "federal_compliance_check": json.loads(row["federal_compliance_json"]),
                "ratified_at_cycle": row["ratified_at_cycle"]
            }
        return None

    # ─── Knowledge Entries ───

    def save_knowledge_entry(self, entry: dict) -> None:
        """Save a knowledge entry."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute("""
            INSERT OR REPLACE INTO knowledge_entries
            (entry_id, entity_id, entity_type, domain, tier,
             concepts_json, frameworks_json, applications_json,
             synthesis, evidence, challenged_by, defense,
             cycle_created, tokens_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["entry_id"], entry["entity_id"], entry["entity_type"],
            entry["domain"], entry["tier"],
            json.dumps(entry.get("concepts", [])),
            json.dumps(entry.get("frameworks", [])),
            json.dumps(entry.get("applications", [])),
            entry.get("synthesis", ""),
            entry.get("evidence", ""),
            entry.get("challenged_by", ""),
            entry.get("defense", ""),
            entry.get("cycle_created", 0),
            entry.get("tokens_used", 0),
            now
        ))
        self.conn.commit()

    def get_knowledge_entries(self, entity_id: str, tier: int = None) -> list[dict]:
        """Get knowledge entries for an entity."""
        if tier is not None:
            rows = self.conn.execute(
                "SELECT * FROM knowledge_entries WHERE entity_id = ? AND tier = ?",
                (entity_id, tier)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM knowledge_entries WHERE entity_id = ?",
                (entity_id,)
            ).fetchall()

        entries = []
        for row in rows:
            entries.append({
                "entry_id": row["entry_id"],
                "entity_id": row["entity_id"],
                "entity_type": row["entity_type"],
                "domain": row["domain"],
                "tier": row["tier"],
                "concepts": json.loads(row["concepts_json"]),
                "frameworks": json.loads(row["frameworks_json"]),
                "applications": json.loads(row["applications_json"]),
                "synthesis": row["synthesis"],
                "evidence": row["evidence"],
                "challenged_by": row["challenged_by"],
                "defense": row["defense"],
                "cycle_created": row["cycle_created"],
                "tokens_used": row["tokens_used"]
            })
        return entries

    def get_state_tier_progress(self, state_id: str) -> dict:
        """Get tier progress for a State."""
        row = self.conn.execute(
            "SELECT MAX(tier) as max_tier, COUNT(*) as entry_count FROM knowledge_entries WHERE entity_id = ?",
            (state_id,)
        ).fetchone()
        return {
            "max_tier": row["max_tier"] or 0,
            "entry_count": row["entry_count"] or 0
        }

    # ─── Federal Archive ───

    def deposit_to_archive(self, source_type: str, source_id: str, knowledge: dict) -> None:
        """Deposit knowledge entry into Federal Archive."""

        # Ensure quality_score column exists
        try:
            self.conn.execute("ALTER TABLE federal_archive ADD COLUMN quality_score INTEGER DEFAULT 0")
            self.conn.commit()
        except Exception as e:
            print(f"DB error: {e}")

        archive_id = f"archive_{uuid.uuid4().hex[:12]}"

        # Calculate quality score: tier weight + content richness
        tier = knowledge.get("tier", 0)
        concepts = knowledge.get("concepts", [])
        frameworks = knowledge.get("frameworks", [])
        quality_score = (tier * 20) + len(concepts) + (len(frameworks) * 3)

        self.conn.execute(
            """INSERT INTO federal_archive
            (archive_id, source_type, source_id, domain, tier, concepts_json,
             frameworks_json, applications_json, synthesis, evidence,
             deposited_at_cycle, quality_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                archive_id,
                source_type,
                source_id,
                knowledge.get("domain", ""),
                tier,
                json.dumps(concepts),
                json.dumps(frameworks),
                json.dumps(knowledge.get("applications", [])),
                knowledge.get("synthesis", ""),
                knowledge.get("evidence", ""),
                knowledge.get("cycle_created", 0),
                quality_score,
                datetime.now(timezone.utc).isoformat()
            )
        )
        self.conn.commit()

    def query_archive(self, domain: str = None, min_tier: int = None, limit: int = 100) -> list[dict]:
        """Query Federal Archive with optional filters."""
        query = "SELECT * FROM federal_archive WHERE 1=1"
        params = []

        if domain:
            query += " AND domain = ?"
            params.append(domain)

        if min_tier is not None:
            query += " AND tier >= ?"
            params.append(min_tier)

        query += " ORDER BY tier DESC, deposited_at_cycle DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()

        entries = []
        for row in rows:
            entries.append({
                "archive_id": row["archive_id"],
                "source_type": row["source_type"],
                "source_id": row["source_id"],
                "domain": row["domain"],
                "tier": row["tier"],
                "concepts": json.loads(row["concepts_json"]),
                "frameworks": json.loads(row["frameworks_json"]),
                "applications": json.loads(row["applications_json"]),
                "synthesis": row["synthesis"],
                "evidence": row["evidence"],
                "deposited_at_cycle": row["deposited_at_cycle"]
            })
        return entries

    def get_archive_summary(self) -> dict:
        """Get summary stats from Federal Archive."""
        row = self.conn.execute(
            """SELECT
                COUNT(*) as total_entries,
                COUNT(DISTINCT domain) as unique_domains,
                MAX(tier) as max_tier,
                AVG(tier) as avg_tier
            FROM federal_archive"""
        ).fetchone()

        return {
            "total_entries": row["total_entries"] or 0,
            "unique_domains": row["unique_domains"] or 0,
            "max_tier": row["max_tier"] or 0,
            "avg_tier": round(row["avg_tier"], 2) if row["avg_tier"] else 0
        }

    # ─── Queries ───
    
    def get_log_entries(self, cycle: int = None, level: str = None,
                        category: str = None, limit: int = 100) -> list[dict]:
        """Query log entries with optional filters."""
        query = "SELECT * FROM log_entries WHERE 1=1"
        params = []
        if cycle is not None:
            query += " AND cycle = ?"
            params.append(cycle)
        if level:
            query += " AND level = ?"
            params.append(level)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def save_constitution_version(self, version, constitution_text,
                                   amendments=None, ratified_by=None):
        """Save immutable constitutional version snapshot."""
        # Mark previous versions as not current
        self.conn.execute(
            "UPDATE constitutions SET is_current = 0 WHERE constitution_type = 'federal' AND version < ?",
            (version,)
        )

        # Insert new version
        self.conn.execute(
            "INSERT INTO constitutions (constitution_type, version, articles_json, ratified_by_json, ratified_at, is_current) VALUES (?, ?, ?, ?, ?, ?)",
            ("federal", version, constitution_text,
             json.dumps(ratified_by or []),
             datetime.now(timezone.utc).isoformat(), 1)
        )
        self.conn.commit()

    def get_constitution_version(self, version=None):
        """Get specific version or current constitution."""
        if version:
            row = self.conn.execute(
                "SELECT * FROM constitutions WHERE constitution_type = 'federal' AND version = ?",
                (version,)
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT * FROM constitutions WHERE constitution_type = 'federal' AND is_current = 1"
            ).fetchone()
        return dict(row) if row else None

    def get_constitution_history(self):
        """Get all versions for audit trail."""
        rows = self.conn.execute(
            "SELECT version, ratified_at, ratified_by_json FROM constitutions WHERE constitution_type = 'federal' ORDER BY version"
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        """Close the database connection."""
        self.conn.close()


# Global DB instance
_db: Optional[AtlantisDB] = None

def get_db(db_path: str = "hydra.db") -> AtlantisDB:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        _db = AtlantisDB(db_path)
    return _db
