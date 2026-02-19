"""
Atlantis V2 — Persistence Layer
================================
SQLite database layer for the V2 adversarial knowledge engine.

V2 schema replaces all V1 tables. Key changes:
- archive_entries: full ArchiveEntry with claim graph (citations/referenced_by)
- display_id_counter: global sequential IDs (#001, #002, ...)
- state_budgets: token economy + probation tracking per State
- domain_health: DMI metrics per domain per cycle
- cities / towns: auto-spawned hierarchy registries

Append-only: entry text NEVER modified. Status can change.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from collections import deque


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PersistenceLayer:
    """SQLite persistence for Atlantis V2."""

    def __init__(self, db_path: str = "output/atlantis.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            self._create_tables(conn)

    def _create_tables(self, conn: sqlite3.Connection):
        conn.executescript("""
            -- Global display ID counter (one row, id=1)
            CREATE TABLE IF NOT EXISTS display_id_counter (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                current_val INTEGER DEFAULT 0
            );
            INSERT OR IGNORE INTO display_id_counter VALUES (1, 0);

            -- Archive entries — core of V2
            -- Append-only. Text never modified. Status can change.
            CREATE TABLE IF NOT EXISTS archive_entries (
                entry_id TEXT PRIMARY KEY,
                display_id TEXT UNIQUE NOT NULL,
                entry_type TEXT NOT NULL,
                source_state TEXT NOT NULL DEFAULT '',
                source_entity TEXT NOT NULL DEFAULT '',
                cycle_created INTEGER NOT NULL,
                status TEXT NOT NULL,
                claim_type TEXT DEFAULT '',
                position TEXT DEFAULT '',
                reasoning_chain_json TEXT DEFAULT '[]',
                conclusion TEXT DEFAULT '',
                keywords_json TEXT DEFAULT '[]',
                raw_claim_text TEXT NOT NULL DEFAULT '',
                raw_challenge_text TEXT DEFAULT '',
                raw_rebuttal_text TEXT DEFAULT '',
                lab_origin_text TEXT DEFAULT '',
                explicit_premises_json TEXT DEFAULT '[]',
                implicit_assumptions_json TEXT DEFAULT '[]',
                challenge_step_targeted TEXT DEFAULT '',
                challenger_entity TEXT DEFAULT '',
                outcome TEXT DEFAULT '',
                outcome_reasoning TEXT DEFAULT '',
                open_questions_json TEXT DEFAULT '[]',
                drama_score INTEGER DEFAULT 0,
                novelty_score INTEGER DEFAULT 0,
                depth_score INTEGER DEFAULT 0,
                citations_json TEXT DEFAULT '[]',
                referenced_by_json TEXT DEFAULT '[]',
                stability_score INTEGER DEFAULT 1,
                impact_score INTEGER DEFAULT 0,
                tokens_earned INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_archive_status ON archive_entries(status);
            CREATE INDEX IF NOT EXISTS idx_archive_state ON archive_entries(source_state);
            CREATE INDEX IF NOT EXISTS idx_archive_cycle ON archive_entries(cycle_created);
            CREATE INDEX IF NOT EXISTS idx_archive_type ON archive_entries(entry_type);

            -- State token budgets and metrics
            CREATE TABLE IF NOT EXISTS state_budgets (
                state_name TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                approach TEXT NOT NULL DEFAULT '',
                token_budget INTEGER NOT NULL DEFAULT 0,
                tier INTEGER DEFAULT 0,
                probation_counter INTEGER DEFAULT 0,
                total_pipeline_claims INTEGER DEFAULT 0,
                surviving_pipeline_claims INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                warmup_remaining INTEGER DEFAULT 0,
                rival_state_name TEXT DEFAULT '',
                created_at_cycle INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            -- Domain health metrics per cycle
            CREATE TABLE IF NOT EXISTS domain_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                cycle INTEGER NOT NULL,
                metrics_json TEXT NOT NULL DEFAULT '{}',
                maturity_phase TEXT NOT NULL DEFAULT 'Volatile Exploration',
                recorded_at TEXT NOT NULL,
                UNIQUE(domain, cycle)
            );

            -- Cities registry
            CREATE TABLE IF NOT EXISTS cities (
                city_id TEXT PRIMARY KEY,
                state_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                cluster_claim_ids_json TEXT NOT NULL DEFAULT '[]',
                analyses_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at_cycle INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            -- Towns registry
            CREATE TABLE IF NOT EXISTS towns (
                town_id TEXT PRIMARY KEY,
                state_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                parent_city_ids_json TEXT NOT NULL DEFAULT '[]',
                proposals_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at_cycle INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            -- System state key-value store
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            -- Event log
            CREATE TABLE IF NOT EXISTS log_entries (
                id TEXT PRIMARY KEY,
                cycle INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                metadata_json TEXT DEFAULT '{}'
            );

            CREATE INDEX IF NOT EXISTS idx_log_cycle ON log_entries(cycle);
            CREATE INDEX IF NOT EXISTS idx_log_level ON log_entries(level);
        """)

    # ═══════════════════════════════════════════════════════
    # DISPLAY ID
    # ═══════════════════════════════════════════════════════

    def next_display_id(self) -> str:
        """Atomic increment. Returns '#001' format."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE display_id_counter SET current_val = current_val + 1 WHERE id = 1"
            )
            row = conn.execute(
                "SELECT current_val FROM display_id_counter WHERE id = 1"
            ).fetchone()
            val = row["current_val"]
        return f"#{val:03d}"

    # ═══════════════════════════════════════════════════════
    # ARCHIVE ENTRIES
    # ═══════════════════════════════════════════════════════

    def save_archive_entry(self, entry) -> str:
        """
        INSERT archive entry. Accepts ArchiveEntry dataclass or dict.
        Returns display_id. Append-only.
        """
        if hasattr(entry, '__dataclass_fields__'):
            import dataclasses
            d = dataclasses.asdict(entry)
        elif hasattr(entry, '__dict__'):
            d = vars(entry)
        else:
            d = dict(entry)

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO archive_entries (
                    entry_id, display_id, entry_type, source_state, source_entity,
                    cycle_created, status, claim_type, position, reasoning_chain_json,
                    conclusion, keywords_json, raw_claim_text, raw_challenge_text,
                    raw_rebuttal_text, lab_origin_text, explicit_premises_json,
                    implicit_assumptions_json, challenge_step_targeted, challenger_entity,
                    outcome, outcome_reasoning, open_questions_json,
                    drama_score, novelty_score, depth_score,
                    citations_json, referenced_by_json,
                    stability_score, impact_score, tokens_earned, created_at
                ) VALUES (
                    :entry_id, :display_id, :entry_type, :source_state, :source_entity,
                    :cycle_created, :status, :claim_type, :position, :reasoning_chain_json,
                    :conclusion, :keywords_json, :raw_claim_text, :raw_challenge_text,
                    :raw_rebuttal_text, :lab_origin_text, :explicit_premises_json,
                    :implicit_assumptions_json, :challenge_step_targeted, :challenger_entity,
                    :outcome, :outcome_reasoning, :open_questions_json,
                    :drama_score, :novelty_score, :depth_score,
                    :citations_json, :referenced_by_json,
                    :stability_score, :impact_score, :tokens_earned, :created_at
                )
            """, {
                "entry_id": d.get("entry_id", ""),
                "display_id": d.get("display_id", ""),
                "entry_type": d.get("entry_type", "claim"),
                "source_state": d.get("source_state", ""),
                "source_entity": d.get("source_entity", ""),
                "cycle_created": d.get("cycle_created", 0),
                "status": d.get("status", "surviving"),
                "claim_type": d.get("claim_type", ""),
                "position": d.get("position", ""),
                "reasoning_chain_json": json.dumps(d.get("reasoning_chain", [])),
                "conclusion": d.get("conclusion", ""),
                "keywords_json": json.dumps(d.get("keywords", [])),
                "raw_claim_text": d.get("raw_claim_text", ""),
                "raw_challenge_text": d.get("raw_challenge_text", ""),
                "raw_rebuttal_text": d.get("raw_rebuttal_text", ""),
                "lab_origin_text": d.get("lab_origin_text", ""),
                "explicit_premises_json": json.dumps(d.get("explicit_premises", [])),
                "implicit_assumptions_json": json.dumps(d.get("implicit_assumptions", [])),
                "challenge_step_targeted": d.get("challenge_step_targeted", ""),
                "challenger_entity": d.get("challenger_entity", ""),
                "outcome": d.get("outcome", ""),
                "outcome_reasoning": d.get("outcome_reasoning", ""),
                "open_questions_json": json.dumps(d.get("open_questions", [])),
                "drama_score": d.get("drama_score", 0),
                "novelty_score": d.get("novelty_score", 0),
                "depth_score": d.get("depth_score", 0),
                "citations_json": json.dumps(d.get("citations", [])),
                "referenced_by_json": json.dumps(d.get("referenced_by", [])),
                "stability_score": d.get("stability_score", 1),
                "impact_score": d.get("impact_score", 0),
                "tokens_earned": d.get("tokens_earned", 0),
                "created_at": d.get("created_at", _now()),
            })
        return d.get("display_id", "")

    def get_archive_entry(self, display_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM archive_entries WHERE display_id = ?", (display_id,)
            ).fetchone()
        return self._unpack_entry(row) if row else None

    def get_archive_entries(
        self,
        status: Optional[str] = None,
        state_name: Optional[str] = None,
        entry_type: Optional[str] = None,
        claim_type: Optional[str] = None,
    ) -> List[Dict]:
        query = "SELECT * FROM archive_entries WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if state_name:
            query += " AND source_state = ?"
            params.append(state_name)
        if entry_type:
            query += " AND entry_type = ?"
            params.append(entry_type)
        if claim_type:
            query += " AND claim_type = ?"
            params.append(claim_type)
        query += " ORDER BY cycle_created ASC, display_id ASC"
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._unpack_entry(r) for r in rows]

    def get_surviving_claims(
        self, state_name: Optional[str] = None, domain: Optional[str] = None
    ) -> List[Dict]:
        query = "SELECT * FROM archive_entries WHERE status IN ('surviving', 'partial')"
        params = []
        if state_name:
            query += " AND source_state = ?"
            params.append(state_name)
        query += " ORDER BY impact_score DESC, stability_score DESC"
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
        results = [self._unpack_entry(r) for r in rows]
        if domain:
            domain_states = self._get_states_for_domain(domain)
            results = [r for r in results if r["source_state"] in domain_states]
        return results

    def get_surviving_claims_count(self, state_name: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM archive_entries "
                "WHERE source_state = ? AND status IN ('surviving', 'partial')",
                (state_name,)
            ).fetchone()
        return row["cnt"] if row else 0

    def count_surviving_claims(self) -> int:
        """Total surviving claims across all States (for Federal Lab activation)."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM archive_entries "
                "WHERE status IN ('surviving', 'partial')"
            ).fetchone()
        return row["cnt"] if row else 0

    def update_entry_status(self, display_id: str, new_status: str, note: str = ""):
        """Append-only: text never modified, only status changes."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE archive_entries SET status = ? WHERE display_id = ?",
                (new_status, display_id)
            )

    def update_referenced_by(self, cited_display_id: str, new_entry_display_id: str):
        """Add new_entry_display_id to cited entry's referenced_by list. Updates impact_score."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT referenced_by_json FROM archive_entries WHERE display_id = ?",
                (cited_display_id,)
            ).fetchone()
            if not row:
                return
            refs = json.loads(row["referenced_by_json"] or "[]")
            if new_entry_display_id not in refs:
                refs.append(new_entry_display_id)
                conn.execute(
                    "UPDATE archive_entries SET referenced_by_json = ?, impact_score = ? "
                    "WHERE display_id = ?",
                    (json.dumps(refs), len(refs), cited_display_id)
                )

    def update_stability_score(self, display_id: str, increment: int = 1):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE archive_entries SET stability_score = stability_score + ? "
                "WHERE display_id = ?",
                (increment, display_id)
            )

    def update_tokens_earned(self, display_id: str, tokens: int):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE archive_entries SET tokens_earned = tokens_earned + ? "
                "WHERE display_id = ?",
                (tokens, display_id)
            )

    def get_entry_dependents(self, display_id: str) -> List[str]:
        entry = self.get_archive_entry(display_id)
        if not entry:
            return []
        return entry.get("referenced_by", [])

    def get_top_impact_claims(self, domain: str, limit: int = 20) -> List[Dict]:
        """For abstraction pass: top N by impact_score in domain."""
        domain_states = self._get_states_for_domain(domain)
        if not domain_states:
            return []
        placeholders = ",".join("?" * len(domain_states))
        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM archive_entries "
                f"WHERE status IN ('surviving', 'partial') "
                f"AND source_state IN ({placeholders}) "
                f"ORDER BY impact_score DESC, stability_score DESC LIMIT ?",
                domain_states + [limit]
            ).fetchall()
        return [self._unpack_entry(r) for r in rows]

    def get_highest_impact_claim(
        self, domain: str, exclude_domain: Optional[str] = None
    ) -> Optional[Dict]:
        """Returns highest-impact surviving claim in domain (for Federal Lab)."""
        domain_states = self._get_states_for_domain(domain)
        if not domain_states:
            return None
        placeholders = ",".join("?" * len(domain_states))
        with self._get_conn() as conn:
            row = conn.execute(
                f"SELECT * FROM archive_entries "
                f"WHERE status IN ('surviving', 'partial') "
                f"AND source_state IN ({placeholders}) "
                f"ORDER BY impact_score DESC, stability_score DESC LIMIT 1",
                domain_states
            ).fetchone()
        return self._unpack_entry(row) if row else None

    def get_last_n_claims(self, state_name: str, n: int = 3) -> List[Dict]:
        """Last N claims produced by a State (for anti-loop check)."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM archive_entries "
                "WHERE source_state = ? AND entry_type = 'claim' "
                "AND status NOT IN ('founding') "
                "ORDER BY cycle_created DESC, display_id DESC LIMIT ?",
                (state_name, n)
            ).fetchall()
        return [self._unpack_entry(r) for r in rows]

    def get_destroyed_claims(self, state_name: str, limit: int = 5) -> List[Dict]:
        """Last N destroyed claims for meta-learning."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM archive_entries "
                "WHERE source_state = ? AND status = 'destroyed' "
                "ORDER BY cycle_created DESC LIMIT ?",
                (state_name, limit)
            ).fetchall()
        return [self._unpack_entry(r) for r in rows]

    def get_principle_count(self, domain: str) -> int:
        """Count principle entries in a domain (for compression_ratio)."""
        domain_states = self._get_states_for_domain(domain)
        if not domain_states:
            return 0
        placeholders = ",".join("?" * len(domain_states))
        with self._get_conn() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM archive_entries "
                f"WHERE entry_type = 'principle' AND source_state IN ({placeholders})",
                domain_states
            ).fetchone()
        return row["cnt"] if row else 0

    def get_lab_origin_stats(self, domain: str) -> Dict:
        """Returns lab_origin_claims_survived and total for lab_survival_rate."""
        domain_states = self._get_states_for_domain(domain)
        if not domain_states:
            return {"survived": 0, "total": 0}
        placeholders = ",".join("?" * len(domain_states))
        with self._get_conn() as conn:
            total_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM archive_entries "
                f"WHERE lab_origin_text != '' AND source_state IN ({placeholders})",
                domain_states
            ).fetchone()
            survived_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM archive_entries "
                f"WHERE lab_origin_text != '' "
                f"AND status IN ('surviving', 'partial') "
                f"AND source_state IN ({placeholders})",
                domain_states
            ).fetchone()
        return {
            "survived": survived_row["cnt"] if survived_row else 0,
            "total": total_row["cnt"] if total_row else 0,
        }

    def get_federal_challenge_count(self, domain: str) -> int:
        """Count Federal Lab challenges that survived in this domain."""
        domain_states = self._get_states_for_domain(domain)
        if not domain_states:
            return 0
        placeholders = ",".join("?" * len(domain_states))
        with self._get_conn() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM archive_entries "
                f"WHERE challenger_entity = 'Federal Lab' "
                f"AND status IN ('surviving', 'partial') "
                f"AND source_state IN ({placeholders})",
                domain_states
            ).fetchone()
        return row["cnt"] if row else 0

    def get_avg_dependency_depth(self, domain: str) -> float:
        """Average citation chain depth for domain (for DMI)."""
        claims = self.get_surviving_claims(domain=domain)
        if not claims:
            return 0.0
        depths = [len(c.get("citations", [])) for c in claims]
        return round(sum(depths) / len(depths), 2)

    def get_max_chain_length(self, domain: str) -> int:
        """Longest dependency chain in domain (BFS from roots)."""
        claims = self.get_surviving_claims(domain=domain)
        if not claims:
            return 0
        return max(len(c.get("citations", [])) for c in claims)

    # ═══════════════════════════════════════════════════════
    # CHAIN COLLAPSE (recursive BFS, max depth from config)
    # ═══════════════════════════════════════════════════════

    def run_chain_collapse(
        self, overturned_id: str, max_depth: int = 10
    ) -> List[str]:
        """
        BFS chain collapse. When overturned_id is overturned:
        - Claims citing ONLY flagged entries → 'foundation_challenged'
        - City analyses >50% citations flagged → 'foundation_challenged'
        - Town proposals citing flagged analyses → 'chain_broken'
        - Recurse up to max_depth. Logs if exceeded.
        Returns list of flagged display_ids.
        """
        flagged = []
        visited = set()
        queue = deque([(overturned_id, 0)])
        deep_logged = False

        while queue:
            current_id, depth = queue.popleft()
            if current_id in visited:
                continue
            visited.add(current_id)

            if depth > max_depth:
                if not deep_logged:
                    self._log_event(
                        "chain_collapse",
                        f"Deep collapse from {overturned_id} exceeded depth {max_depth} "
                        f"— manual review recommended",
                        level="warning"
                    )
                    deep_logged = True
                continue

            entry = self.get_archive_entry(current_id)
            if not entry:
                continue

            for dep_id in entry.get("referenced_by", []):
                if dep_id in visited:
                    continue
                dep = self.get_archive_entry(dep_id)
                if not dep:
                    continue
                if dep["status"] in (
                    "overturned", "foundation_challenged", "chain_broken"
                ):
                    continue

                dep_citations = dep.get("citations", [])
                dep_type = dep.get("entry_type", "claim")

                if dep_type == "analysis":
                    # City analyses: >50% threshold
                    if dep_citations:
                        flagged_count = sum(
                            1 for c in dep_citations if self._is_flagged(c)
                        )
                        if flagged_count / len(dep_citations) > 0.5:
                            self.update_entry_status(dep_id, "foundation_challenged")
                            flagged.append(dep_id)
                            queue.append((dep_id, depth + 1))

                elif dep_type == "proposal":
                    if any(self._is_flagged(c) for c in dep_citations):
                        self.update_entry_status(dep_id, "chain_broken")
                        flagged.append(dep_id)
                        queue.append((dep_id, depth + 1))

                else:
                    # Regular claims: all citations flagged → foundation_challenged
                    if dep_citations and all(
                        self._is_flagged(c) for c in dep_citations
                    ):
                        self.update_entry_status(dep_id, "foundation_challenged")
                        flagged.append(dep_id)
                        queue.append((dep_id, depth + 1))

        return flagged

    def _is_flagged(self, display_id: str) -> bool:
        entry = self.get_archive_entry(display_id)
        if not entry:
            return False
        return entry["status"] in (
            "overturned", "foundation_challenged", "chain_broken", "destroyed"
        )

    # ═══════════════════════════════════════════════════════
    # CLUSTER DETECTION (for City auto-formation)
    # ═══════════════════════════════════════════════════════

    def get_cluster_candidates(self, state_name: str) -> List[List[str]]:
        """
        Find groups of 5+ surviving claims from state_name sharing 2+ citations.
        Returns list of display_id groups (each = potential City cluster).
        """
        claims = self.get_surviving_claims(state_name=state_name)
        if len(claims) < 5:
            return []

        # citation → [claim_ids that cite it]
        citation_to_claims: Dict[str, List[str]] = {}
        for claim in claims:
            for cid in claim.get("citations", []):
                citation_to_claims.setdefault(cid, []).append(claim["display_id"])

        # Count shared citations between claim pairs
        from collections import defaultdict
        pair_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for _cid, clm_ids in citation_to_claims.items():
            for i in range(len(clm_ids)):
                for j in range(i + 1, len(clm_ids)):
                    a, b = clm_ids[i], clm_ids[j]
                    pair_counts[a][b] += 1
                    pair_counts[b][a] += 1

        # Connected components where edge = 2+ shared citations
        all_ids = [c["display_id"] for c in claims]
        parent = {cid: cid for cid in all_ids}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            parent[find(x)] = find(y)

        for a in pair_counts:
            for b, cnt in pair_counts[a].items():
                if cnt >= 2 and a in parent and b in parent:
                    union(a, b)

        groups: Dict[str, List[str]] = {}
        for cid in all_ids:
            root = find(cid)
            groups.setdefault(root, []).append(cid)

        return [g for g in groups.values() if len(g) >= 5]

    # ═══════════════════════════════════════════════════════
    # STATE BUDGETS
    # ═══════════════════════════════════════════════════════

    def save_state_budget(
        self, state_name: str, domain: str, approach: str,
        budget: int, rival_name: str, cycle: int
    ):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO state_budgets
                (state_name, domain, approach, token_budget, tier, probation_counter,
                 total_pipeline_claims, surviving_pipeline_claims, is_active,
                 warmup_remaining, rival_state_name, created_at_cycle, created_at)
                VALUES (?, ?, ?, ?, 0, 0, 0, 0, 1, 0, ?, ?, ?)
            """, (state_name, domain, approach, budget, rival_name, cycle, _now()))

    def update_state_budget(self, state_name: str, delta: int):
        """Add delta to token_budget. Always clamps to 0 floor."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE state_budgets "
                "SET token_budget = MAX(0, token_budget + ?) "
                "WHERE state_name = ?",
                (delta, state_name)
            )

    def update_rival_link(self, state_name: str, rival_name: str):
        """Set rival_state_name for a State."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE state_budgets SET rival_state_name = ? WHERE state_name = ?",
                (rival_name, state_name)
            )

    def get_state_budget_row(self, state_name: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM state_budgets WHERE state_name = ?", (state_name,)
            ).fetchone()
        return dict(row) if row else None

    def get_all_active_states(self) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM state_budgets WHERE is_active = 1"
            ).fetchall()
        return [dict(r) for r in rows]

    def increment_pipeline_claims(self, state_name: str, survived: bool):
        with self._get_conn() as conn:
            if survived:
                conn.execute(
                    "UPDATE state_budgets "
                    "SET total_pipeline_claims = total_pipeline_claims + 1, "
                    "    surviving_pipeline_claims = surviving_pipeline_claims + 1 "
                    "WHERE state_name = ?",
                    (state_name,)
                )
            else:
                conn.execute(
                    "UPDATE state_budgets "
                    "SET total_pipeline_claims = total_pipeline_claims + 1 "
                    "WHERE state_name = ?",
                    (state_name,)
                )

    def update_state_tier(self, state_name: str, new_tier: int):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE state_budgets SET tier = ? WHERE state_name = ?",
                (new_tier, state_name)
            )

    def update_state_probation(self, state_name: str, had_surviving_or_partial: bool):
        """One surviving/partial resets counter. Retracted does NOT reset."""
        with self._get_conn() as conn:
            if had_surviving_or_partial:
                conn.execute(
                    "UPDATE state_budgets SET probation_counter = 0 WHERE state_name = ?",
                    (state_name,)
                )
            else:
                conn.execute(
                    "UPDATE state_budgets SET probation_counter = probation_counter + 1 "
                    "WHERE state_name = ?",
                    (state_name,)
                )

    def update_warmup(self, state_name: str, warmup_remaining: int):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE state_budgets SET warmup_remaining = ? WHERE state_name = ?",
                (warmup_remaining, state_name)
            )

    def update_rival(self, state_name: str, rival_name: str):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE state_budgets SET rival_state_name = ? WHERE state_name = ?",
                (rival_name, state_name)
            )

    def dissolve_state(self, state_name: str):
        """Mark State + its Cities + Towns as inactive."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE state_budgets SET is_active = 0 WHERE state_name = ?",
                (state_name,)
            )
            conn.execute(
                "UPDATE cities SET is_active = 0 WHERE state_name = ?", (state_name,)
            )
            conn.execute(
                "UPDATE towns SET is_active = 0 WHERE state_name = ?", (state_name,)
            )

    def get_state_credibility(self, state_name: str) -> float:
        """surviving_pipeline_claims / total_pipeline_claims. 1.0 if none yet."""
        row = self.get_state_budget_row(state_name)
        if not row:
            return 1.0
        total = row.get("total_pipeline_claims", 0)
        surviving = row.get("surviving_pipeline_claims", 0)
        return round(surviving / total, 3) if total > 0 else 1.0

    def count_cross_domain_citations_received(self, state_name: str) -> int:
        """Entries from OTHER domains that cite THIS State's claims (Tier 5 check)."""
        row = self.get_state_budget_row(state_name)
        if not row:
            return 0
        state_domain = row.get("domain", "")

        with self._get_conn() as conn:
            state_entries = conn.execute(
                "SELECT display_id FROM archive_entries WHERE source_state = ?",
                (state_name,)
            ).fetchall()
        state_ids = {r["display_id"] for r in state_entries}
        if not state_ids:
            return 0

        all_states = self.get_all_active_states()
        other_domain_states = {
            s["state_name"] for s in all_states if s["domain"] != state_domain
        }
        if not other_domain_states:
            return 0

        count = 0
        for sid in state_ids:
            entry = self.get_archive_entry(sid)
            if not entry:
                continue
            for ref_id in entry.get("referenced_by", []):
                ref = self.get_archive_entry(ref_id)
                if ref and ref.get("source_state") in other_domain_states:
                    count += 1
        return count

    # ═══════════════════════════════════════════════════════
    # DOMAIN HEALTH
    # ═══════════════════════════════════════════════════════

    def save_domain_health(self, domain: str, cycle: int, metrics: dict):
        phase = metrics.get("maturity_phase", "Volatile Exploration")
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO domain_health
                (domain, cycle, metrics_json, maturity_phase, recorded_at)
                VALUES (?, ?, ?, ?, ?)
            """, (domain, cycle, json.dumps(metrics), phase, _now()))

    def get_domain_health(
        self, domain: Optional[str] = None, latest_only: bool = True
    ) -> Dict:
        with self._get_conn() as conn:
            if domain and latest_only:
                row = conn.execute(
                    "SELECT metrics_json FROM domain_health "
                    "WHERE domain = ? ORDER BY cycle DESC LIMIT 1",
                    (domain,)
                ).fetchone()
                return json.loads(row["metrics_json"]) if row else {}
            else:
                rows = conn.execute(
                    "SELECT domain, metrics_json FROM domain_health "
                    "WHERE (domain, cycle) IN ("
                    "  SELECT domain, MAX(cycle) FROM domain_health GROUP BY domain)"
                ).fetchall()
                return {r["domain"]: json.loads(r["metrics_json"]) for r in rows}

    def get_all_domains(self) -> List[str]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT domain FROM state_budgets WHERE is_active = 1"
            ).fetchall()
        return [r["domain"] for r in rows]

    # ═══════════════════════════════════════════════════════
    # CITIES AND TOWNS
    # ═══════════════════════════════════════════════════════

    def save_city(
        self, city_id: str, state_name: str, domain: str,
        cluster_claim_ids: List[str], cycle: int
    ):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO cities
                (city_id, state_name, domain, cluster_claim_ids_json,
                 analyses_count, is_active, created_at_cycle, created_at)
                VALUES (?, ?, ?, ?, 0, 1, ?, ?)
            """, (city_id, state_name, domain, json.dumps(cluster_claim_ids), cycle, _now()))

    def save_town(
        self, town_id: str, state_name: str, domain: str,
        parent_city_ids: List[str], cycle: int
    ):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO towns
                (town_id, state_name, domain, parent_city_ids_json,
                 proposals_count, is_active, created_at_cycle, created_at)
                VALUES (?, ?, ?, ?, 0, 1, ?, ?)
            """, (town_id, state_name, domain, json.dumps(parent_city_ids), cycle, _now()))

    def increment_city_analyses(self, city_id: str):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE cities SET analyses_count = analyses_count + 1 WHERE city_id = ?",
                (city_id,)
            )

    def increment_town_proposals(self, town_id: str):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE towns SET proposals_count = proposals_count + 1 WHERE town_id = ?",
                (town_id,)
            )

    def get_active_cities(self, state_name: str) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM cities WHERE state_name = ? AND is_active = 1",
                (state_name,)
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["cluster_claim_ids"] = json.loads(d.pop("cluster_claim_ids_json", "[]"))
            result.append(d)
        return result

    def get_active_towns(self, state_name: str) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM towns WHERE state_name = ? AND is_active = 1",
                (state_name,)
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["parent_city_ids"] = json.loads(d.pop("parent_city_ids_json", "[]"))
            result.append(d)
        return result

    def get_active_city_count(self, state_name: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM cities WHERE state_name = ? AND is_active = 1",
                (state_name,)
            ).fetchone()
        return row["cnt"] if row else 0

    def get_active_town_count(self, state_name: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM towns WHERE state_name = ? AND is_active = 1",
                (state_name,)
            ).fetchone()
        return row["cnt"] if row else 0

    def count_published_city_analyses(self, state_name: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT SUM(analyses_count) as total FROM cities "
                "WHERE state_name = ? AND is_active = 1",
                (state_name,)
            ).fetchone()
        val = row["total"] if row else 0
        return val or 0

    def get_active_cities_in_domain(self, domain: str) -> List[Dict]:
        """All active Cities across all States for a given domain."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM cities WHERE domain = ? AND is_active = 1", (domain,)
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["cluster_claim_ids"] = json.loads(d.pop("cluster_claim_ids_json", "[]"))
            result.append(d)
        return result

    def get_active_towns_in_domain(self, domain: str) -> List[Dict]:
        """All active Towns across all States for a given domain."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM towns WHERE domain = ? AND is_active = 1", (domain,)
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["parent_city_ids"] = json.loads(d.pop("parent_city_ids_json", "[]"))
            result.append(d)
        return result

    def get_all_archive_entries(self) -> List[Dict]:
        """Return ALL archive entries regardless of status (for export)."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM archive_entries ORDER BY display_id"
            ).fetchall()
        return [self._unpack_entry(r) for r in rows]

    # ═══════════════════════════════════════════════════════
    # SYSTEM STATE (key-value)
    # ═══════════════════════════════════════════════════════

    def set_state(self, key: str, value: Any):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO system_state (key, value, updated_at) "
                "VALUES (?, ?, ?)",
                (key, json.dumps(value), _now())
            )

    def get_state(self, key: str, default=None) -> Any:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM system_state WHERE key = ?", (key,)
            ).fetchone()
        return json.loads(row["value"]) if row else default

    # ═══════════════════════════════════════════════════════
    # EVENT LOG
    # ═══════════════════════════════════════════════════════

    def log_event(
        self, cycle: int, level: str, category: str,
        title: str, summary: str, metadata: dict = None
    ):
        import uuid
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO log_entries
                (id, cycle, timestamp, level, category, title, summary, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), cycle, _now(), level, category,
                title, summary, json.dumps(metadata or {})
            ))

    def _log_event(self, category: str, message: str, level: str = "info"):
        self.log_event(0, level, category, message, message)

    # ═══════════════════════════════════════════════════════
    # EXPORT
    # ═══════════════════════════════════════════════════════

    def get_all_entries_for_export(self) -> List[Dict]:
        """All archive entries for archive.md / archive.json export."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM archive_entries ORDER BY cycle_created ASC, display_id ASC"
            ).fetchall()
        return [self._unpack_entry(r) for r in rows]

    # ═══════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════

    def _unpack_entry(self, row) -> Dict:
        """Convert DB row to dict with JSON fields unpacked."""
        d = dict(row)
        json_fields = {
            "reasoning_chain_json": "reasoning_chain",
            "keywords_json": "keywords",
            "explicit_premises_json": "explicit_premises",
            "implicit_assumptions_json": "implicit_assumptions",
            "open_questions_json": "open_questions",
            "citations_json": "citations",
            "referenced_by_json": "referenced_by",
        }
        for db_field, py_field in json_fields.items():
            raw = d.pop(db_field, "[]")
            try:
                d[py_field] = json.loads(raw or "[]")
            except (json.JSONDecodeError, TypeError):
                d[py_field] = []
        return d

    def _get_states_for_domain(self, domain: str) -> List[str]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT state_name FROM state_budgets WHERE domain = ? AND is_active = 1",
                (domain,)
            ).fetchall()
        return [r["state_name"] for r in rows]
