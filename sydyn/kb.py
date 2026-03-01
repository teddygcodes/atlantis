"""Knowledge base storage with 90-day re-validation."""

import hashlib
import time
from typing import Optional, Dict

from sydyn.schema import SydynDB


class KnowledgeBase:
    """Manages cached answers with re-validation."""

    REVALIDATION_PERIOD = 90 * 24 * 3600  # 90 days in seconds
    SIMILARITY_THRESHOLD = 0.85  # Threshold for considering answers similar

    def __init__(self, db: SydynDB):
        """Initialize with database connection.

        Args:
            db: SydynDB instance
        """
        self.db = db

    def query_hash(self, query: str) -> str:
        """Compute normalized query hash.

        Args:
            query: Query text

        Returns:
            SHA256 hash
        """
        # Normalize: lowercase, strip whitespace
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def has_cached_answer(self, query: str) -> bool:
        """Check if query has cached answer.

        Args:
            query: Query text

        Returns:
            True if cached answer exists
        """
        qhash = self.query_hash(query)
        entry = self.db.get_kb_entry(qhash)

        return entry is not None

    def get_cached_answer(
        self,
        query: str
    ) -> Optional[Dict]:
        """Retrieve cached answer if valid.

        Args:
            query: Query text

        Returns:
            Cached answer dict or None if expired/missing
        """
        qhash = self.query_hash(query)
        entry = self.db.get_kb_entry(qhash)

        if not entry:
            return None

        now = time.time()
        last_validated = entry.get("last_validated", 0)

        # Check if within re-validation period
        if (now - last_validated) < self.REVALIDATION_PERIOD:
            print(f"[KB] Cache HIT for query (validated {int((now - last_validated) / 86400)} days ago)")
            return {
                "answer_text": entry.get("answer_text"),
                "confidence_score": entry.get("confidence_score"),
                "confidence_features": entry.get("confidence_features"),
                "cached": True,
                "validation_count": entry.get("validation_count", 1)
            }
        else:
            print(f"[KB] Cache EXPIRED for query (last validated {int((now - last_validated) / 86400)} days ago)")
            return None

    def store_answer(
        self,
        query: str,
        answer_id: str
    ):
        """Store answer in knowledge base.

        Args:
            query: Query text
            answer_id: Query ID (links to answers table)
        """
        qhash = self.query_hash(query)

        print(f"[KB] Storing answer in knowledge base")
        self.db.store_kb_entry(qhash, query, answer_id)

    def revalidate_answer(
        self,
        query: str,
        new_answer_text: str,
        new_answer_id: str
    ) -> bool:
        """Re-validate cached answer with new query execution.

        Args:
            query: Query text
            new_answer_text: Newly generated answer
            new_answer_id: New query ID

        Returns:
            True if answers are similar (cache updated), False if diverged (cache replaced)
        """
        qhash = self.query_hash(query)
        cached_entry = self.db.get_kb_entry(qhash)

        if not cached_entry:
            print(f"[KB] No cached entry to revalidate")
            return False

        cached_answer = cached_entry.get("answer_text", "")

        # Simple similarity check: compare length and word overlap
        similarity = self._compute_similarity(cached_answer, new_answer_text)

        print(f"[KB] Similarity: {similarity:.2f} (threshold: {self.SIMILARITY_THRESHOLD})")

        if similarity >= self.SIMILARITY_THRESHOLD:
            # Answers are similar - update validation timestamp
            print(f"[KB] Answers similar - updating validation timestamp")
            self.db.update_kb_validation(qhash)
            return True
        else:
            # Answers diverged - replace with new answer
            print(f"[KB] Answers diverged - replacing cached answer")
            self.db.store_kb_entry(qhash, query, new_answer_id)
            return False

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute simple similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        # Simple word-based Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        jaccard = len(intersection) / len(union) if union else 0.0

        # Also consider length similarity
        len1 = len(text1)
        len2 = len(text2)
        length_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0.0

        # Weighted average: 70% Jaccard, 30% length ratio
        similarity = 0.7 * jaccard + 0.3 * length_ratio

        return similarity

    def get_stats(self) -> Dict:
        """Get KB statistics.

        Returns:
            Dict with stats
        """
        # Query KB table for stats
        stats = self.db.conn.execute("""
            SELECT
                COUNT(*) as total_entries,
                AVG(validation_count) as avg_validations,
                MAX(validation_count) as max_validations
            FROM kb
        """).fetchone()

        if stats:
            return {
                "total_entries": stats[0],
                "avg_validations": round(stats[1], 2) if stats[1] else 0.0,
                "max_validations": stats[2] if stats[2] else 0
            }

        return {
            "total_entries": 0,
            "avg_validations": 0.0,
            "max_validations": 0
        }
