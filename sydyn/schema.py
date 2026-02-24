"""Sydyn database schema and persistence layer."""

import sqlite3
import time
from pathlib import Path
from typing import Optional


class SydynDB:
    """SQLite database for Sydyn query results and knowledge base."""

    def __init__(self, db_path: str = "sydyn.db"):
        """Initialize database connection with WAL mode.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrency (following Atlantis pattern)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        self._create_tables()

    def _create_tables(self):
        """Create all Sydyn database tables."""

        # Query metadata
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                query_id TEXT PRIMARY KEY,
                query_text TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at REAL NOT NULL,
                latency_ms INTEGER,
                cost_usd REAL,
                timeout_occurred INTEGER DEFAULT 0,
                degradation_level TEXT
            )
        """)

        # Final answers
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                query_id TEXT PRIMARY KEY,
                answer_text TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                confidence_features TEXT,
                constitutional_violations TEXT,
                FOREIGN KEY (query_id) REFERENCES queries(query_id)
            )
        """)

        # Extracted claims
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                query_id TEXT NOT NULL,
                claim_text TEXT NOT NULL,
                agent_role TEXT NOT NULL,
                FOREIGN KEY (query_id) REFERENCES queries(query_id)
            )
        """)

        # Sources and citations
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                snippet TEXT,
                credibility_score REAL,
                fetch_failed INTEGER DEFAULT 0
            )
        """)

        # Citation grades
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS citation_grades (
                claim_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                grade TEXT NOT NULL,
                explanation TEXT,
                PRIMARY KEY (claim_id, source_id),
                FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
                FOREIGN KEY (source_id) REFERENCES sources(source_id)
            )
        """)

        # Attack log
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS attack_log (
                attack_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id TEXT NOT NULL,
                attack_text TEXT NOT NULL,
                attack_type TEXT,
                severity TEXT,
                addressed_by_critic INTEGER DEFAULT 0,
                FOREIGN KEY (query_id) REFERENCES queries(query_id)
            )
        """)

        # Knowledge base (cached answers with re-validation)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS kb (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT NOT NULL,
                answer_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_validated REAL NOT NULL,
                validation_count INTEGER DEFAULT 1,
                FOREIGN KEY (answer_id) REFERENCES answers(query_id)
            )
        """)

        # Create indexes for common queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_queries_created
            ON queries(created_at)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_claims_query
            ON claims(query_id)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_kb_validated
            ON kb(last_validated)
        """)

        self.conn.commit()

    def store_query(self, query_id: str, query_text: str, mode: str) -> None:
        """Store query metadata."""
        self.conn.execute("""
            INSERT INTO queries (query_id, query_text, mode, created_at)
            VALUES (?, ?, ?, ?)
        """, (query_id, query_text, mode, time.time()))
        self.conn.commit()

    def update_query_metrics(
        self,
        query_id: str,
        latency_ms: int,
        cost_usd: float,
        timeout_occurred: bool = False,
        degradation_level: Optional[str] = None
    ) -> None:
        """Update query completion metrics."""
        self.conn.execute("""
            UPDATE queries
            SET latency_ms = ?, cost_usd = ?, timeout_occurred = ?, degradation_level = ?
            WHERE query_id = ?
        """, (latency_ms, cost_usd, int(timeout_occurred), degradation_level, query_id))
        self.conn.commit()

    def store_answer(
        self,
        query_id: str,
        answer_text: str,
        confidence_score: float,
        confidence_features: str,
        constitutional_violations: str
    ) -> None:
        """Store final answer with confidence and violations."""
        self.conn.execute("""
            INSERT INTO answers (
                query_id, answer_text, confidence_score,
                confidence_features, constitutional_violations
            ) VALUES (?, ?, ?, ?, ?)
        """, (query_id, answer_text, confidence_score, confidence_features, constitutional_violations))
        self.conn.commit()

    def store_claim(
        self,
        claim_id: str,
        query_id: str,
        claim_text: str,
        agent_role: str
    ) -> None:
        """Store extracted claim from agent."""
        self.conn.execute("""
            INSERT INTO claims (claim_id, query_id, claim_text, agent_role)
            VALUES (?, ?, ?, ?)
        """, (claim_id, query_id, claim_text, agent_role))
        self.conn.commit()

    def store_source(
        self,
        source_id: str,
        url: str,
        title: Optional[str] = None,
        snippet: Optional[str] = None,
        credibility_score: Optional[float] = None,
        fetch_failed: bool = False
    ) -> None:
        """Store source metadata."""
        self.conn.execute("""
            INSERT OR REPLACE INTO sources (
                source_id, url, title, snippet, credibility_score, fetch_failed
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (source_id, url, title, snippet, credibility_score, int(fetch_failed)))
        self.conn.commit()

    def store_citation_grade(
        self,
        claim_id: str,
        source_id: str,
        grade: str,
        explanation: Optional[str] = None
    ) -> None:
        """Store citation grade for claim-source pair."""
        self.conn.execute("""
            INSERT OR REPLACE INTO citation_grades (
                claim_id, source_id, grade, explanation
            ) VALUES (?, ?, ?, ?)
        """, (claim_id, source_id, grade, explanation))
        self.conn.commit()

    def store_attack(
        self,
        query_id: str,
        attack_text: str,
        attack_type: Optional[str] = None,
        severity: Optional[str] = None,
        addressed: bool = False
    ) -> None:
        """Store adversary attack."""
        self.conn.execute("""
            INSERT INTO attack_log (
                query_id, attack_text, attack_type, severity, addressed_by_critic
            ) VALUES (?, ?, ?, ?, ?)
        """, (query_id, attack_text, attack_type, severity, int(addressed)))
        self.conn.commit()

    def mark_attack_addressed(self, query_id: str, attack_text: str) -> None:
        """Mark an attack as addressed by critic."""
        self.conn.execute("""
            UPDATE attack_log
            SET addressed_by_critic = 1
            WHERE query_id = ? AND attack_text = ?
        """, (query_id, attack_text))
        self.conn.commit()

    def get_kb_entry(self, query_hash: str) -> Optional[dict]:
        """Retrieve cached answer from knowledge base."""
        row = self.conn.execute("""
            SELECT k.*, a.answer_text, a.confidence_score, a.confidence_features
            FROM kb k
            JOIN answers a ON k.answer_id = a.query_id
            WHERE k.query_hash = ?
        """, (query_hash,)).fetchone()

        return dict(row) if row else None

    def store_kb_entry(
        self,
        query_hash: str,
        query_text: str,
        answer_id: str
    ) -> None:
        """Store answer in knowledge base."""
        now = time.time()
        self.conn.execute("""
            INSERT OR REPLACE INTO kb (
                query_hash, query_text, answer_id, created_at, last_validated, validation_count
            ) VALUES (?, ?, ?, ?, ?, 1)
        """, (query_hash, query_text, answer_id, now, now))
        self.conn.commit()

    def update_kb_validation(self, query_hash: str) -> None:
        """Update KB entry validation timestamp and count."""
        self.conn.execute("""
            UPDATE kb
            SET last_validated = ?, validation_count = validation_count + 1
            WHERE query_hash = ?
        """, (time.time(), query_hash))
        self.conn.commit()

    def get_query_stats(self) -> dict:
        """Get aggregate query statistics."""
        row = self.conn.execute("""
            SELECT
                COUNT(*) as total_queries,
                AVG(latency_ms) as avg_latency,
                AVG(cost_usd) as avg_cost,
                SUM(timeout_occurred) as timeout_count,
                COUNT(DISTINCT mode) as modes_used
            FROM queries
        """).fetchone()

        return dict(row) if row else {}

    def close(self):
        """Close database connection."""
        self.conn.close()
