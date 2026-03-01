"""Sydyn main engine - orchestrates the entire pipeline."""

import json
import uuid
from typing import Optional, Dict

from core.models import ModelRouter
from core.exceptions import LLMTimeoutException
from sydyn.schema import SydynDB
from sydyn.query_classifier import classify_query
from sydyn.evidence import build_evidence_pack, verify_all_citations, calculate_source_diversity
from sydyn.agents import Researcher, Adversary, Critic, Judge
from sydyn.constitution import get_constitution, enforce_constitution
from sydyn.confidence import calculate_confidence, adjust_confidence_for_timeout, format_confidence_explanation
from sydyn.timeout import TimeoutManager, build_evidence_only_response
from sydyn.kb import KnowledgeBase


class SydynEngine:
    """Main orchestrator for Sydyn queries."""

    def __init__(
        self,
        db_path: str = "sydyn.db",
        search_provider: str = "tavily",
        model_router: Optional[ModelRouter] = None
    ):
        """Initialize Sydyn engine.

        Args:
            db_path: Path to SQLite database
            search_provider: "tavily" or "serper"
            model_router: Optional ModelRouter instance (will create if None)
        """
        self.db = SydynDB(db_path)
        self.kb = KnowledgeBase(self.db)
        self.search_provider = search_provider
        self.constitution = get_constitution()

        # Create or use provided ModelRouter
        if model_router:
            self.model_router = model_router
        else:
            self.model_router = ModelRouter()

        # Initialize agents
        self.researcher = Researcher(self.model_router)
        self.adversary = Adversary(self.model_router)
        self.critic = Critic(self.model_router)
        self.judge = Judge(self.model_router, self.constitution)

    def query(
        self,
        query_text: str,
        mode: Optional[str] = None,
        save_kb: bool = True,
        status_callback: Optional[callable] = None
    ) -> Dict:
        """Execute Sydyn query with full pipeline.

        Args:
            query_text: User query
            mode: Optional mode override ("fast" | "strict" | "liability")
            save_kb: Whether to save validated answers to KB
            status_callback: Optional callback for status updates (for SSE streaming)

        Returns:
            Dict with answer, confidence, and metadata
        """
        # Store callback for access by helper methods
        self._status_callback = status_callback

        def emit_status(message: str):
            """Emit status update if callback provided."""
            if status_callback:
                status_callback(message)

        # Generate query ID
        query_id = str(uuid.uuid4())[:8]

        # Initialize timeout manager
        timeout_mgr = TimeoutManager()
        timeout_mgr.start()

        print(f"\n[SYDYN] Query ID: {query_id}")
        print(f"[SYDYN] Query: {query_text}\n")

        emit_status("Initializing Sydyn pipeline...")

        # Step 1: Check knowledge base
        emit_status("Checking knowledge base...")
        cached_result = self.kb.get_cached_answer(query_text)
        if cached_result:
            print(f"[SYDYN] Returning cached answer (instant)")
            emit_status("Retrieved from knowledge base (instant)")
            full_result = self._reconstruct_cached_result(query_id, query_text, cached_result, timeout_mgr)
            return full_result

        # Step 2: Classify query
        emit_status("Classifying query...")
        classified_mode = classify_query(query_text, self.model_router, override_mode=mode)

        print(f"[SYDYN] Mode: {classified_mode.upper()}\n")
        emit_status(f"Query classified as {classified_mode.upper()} mode")

        # Store query metadata
        self.db.store_query(query_id, query_text, classified_mode)

        # Step 3: Build Evidence Pack
        print(f"[SYDYN] Building Evidence Pack...")
        emit_status("Building evidence pack...")
        evidence_pack = build_evidence_pack(query_text, search_provider=self.search_provider)

        if not evidence_pack.sufficient_evidence:
            print(f"[SYDYN] Insufficient evidence (<3 sources fetched)")
            return {
                "query_id": query_id,
                "query": query_text,
                "answer": "Unable to provide answer - insufficient evidence sources available.",
                "confidence": 0.2,
                "confidence_band": "VERY_LOW",
                "error": "insufficient_evidence"
            }

        # Check for timeout after evidence pack
        if timeout_mgr.should_return_evidence_only():
            evidence_only = build_evidence_only_response(evidence_pack)
            return {
                "query_id": query_id,
                "query": query_text,
                "answer": evidence_only,
                "confidence": 0.2,
                "timeout": True,
                "degradation_level": "evidence_only"
            }

        # Step 4: Run agent pipeline based on mode
        if classified_mode == "fast":
            result = self._run_fast_mode(query_id, query_text, evidence_pack, timeout_mgr)
        elif classified_mode == "strict":
            result = self._run_strict_mode(query_id, query_text, evidence_pack, timeout_mgr)
        elif classified_mode == "liability":
            result = self._run_liability_mode(query_id, query_text, evidence_pack, timeout_mgr)
        else:
            result = self._run_fast_mode(query_id, query_text, evidence_pack, timeout_mgr)

        # Update query metrics
        elapsed_ms = int(timeout_mgr.elapsed() * 1000)
        cost_usd = self._estimate_cost(classified_mode, timeout_mgr.get_degradation_level())

        self.db.update_query_metrics(
            query_id,
            latency_ms=elapsed_ms,
            cost_usd=cost_usd,
            timeout_occurred=(timeout_mgr.get_degradation_level() is not None),
            degradation_level=timeout_mgr.get_degradation_level()
        )

        result["latency_ms"] = elapsed_ms
        result["cost_usd"] = cost_usd

        # Store in KB if verdict is PASS and save_kb is True
        if save_kb and result.get("verdict") == "PASS":
            self.kb.store_answer(query_text, query_id)

        return result

    def _run_fast_mode(
        self,
        query_id: str,
        query_text: str,
        evidence_pack,
        timeout_mgr: TimeoutManager
    ) -> Dict:
        """Run fast mode pipeline (Researcher + Adversary + Judge).

        Args:
            query_id: Query ID
            query_text: Query text
            evidence_pack: EvidencePack
            timeout_mgr: TimeoutManager

        Returns:
            Result dict
        """
        print(f"[SYDYN] Running FAST mode pipeline\n")

        # Emit status helper
        def emit(msg):
            if hasattr(self, '_status_callback') and self._status_callback:
                self._status_callback(msg)

        # Researcher
        print(f"[SYDYN] Researcher generating answer...")
        emit("Researcher analyzing evidence and drafting claims...")
        researcher_response = self.researcher.generate_answer(query_text, evidence_pack)
        print(f"[SYDYN] Researcher produced {len(researcher_response.claims)} claims\n")
        emit(f"Researcher drafted {len(researcher_response.claims)} claims")

        # Adversary
        print(f"[SYDYN] Adversary generating attacks...")
        emit("Adversary generating counter-arguments...")
        adversary_response = self.adversary.generate_attacks(
            query_text,
            researcher_response.claims,
            evidence_pack
        )
        print(f"[SYDYN] Adversary produced {len(adversary_response.claims)} attacks\n")
        emit(f"Adversary generated {len(adversary_response.claims)} attacks")

        # Skip Critic in fast mode
        critic_response = None

        # Citation verification
        print(f"[SYDYN] Verifying citations...")
        emit("Verifying citations...")

        def llm_function(prompt, task_type, temperature):
            return self.model_router.complete(
                task_type=task_type,
                system_prompt="",
                user_prompt=prompt,
                max_tokens=500
            ).content

        citation_grades = verify_all_citations(
            [{"claim_id": c.claim_id, "text": c.text, "citations": c.citations} for c in researcher_response.claims],
            evidence_pack.sources,
            llm_function
        )

        # Judge
        print(f"[SYDYN] Judge evaluating against constitution...")
        emit("Judge evaluating against constitutional rules...")
        all_claims = researcher_response.claims + adversary_response.claims

        try:
            judge_result = self.judge.evaluate(
                query_text,
                all_claims,
                citation_grades,
                evidence_pack,
                mode="fast"
            )
            emit(f"Judge verdict: {judge_result.get('verdict', 'UNKNOWN')}")
        except LLMTimeoutException as e:
            print(f"[SYDYN] WARNING: Judge timed out after 30s - using degraded evaluation")
            # Return degraded judge result with WARN verdict
            judge_result = {
                "verdict": "WARN",
                "violations": [{
                    "rule": "Judge Timeout",
                    "claim_id": "system",
                    "severity": "MAJOR",
                    "explanation": "Judge evaluation timed out - answer may not be fully validated against constitution"
                }],
                "reasoning": "Judge timeout - degraded evaluation",
                "raw_response": str(e)
            }

        # Confidence scoring
        print(f"[SYDYN] Calculating confidence...")
        confidence_result = calculate_confidence(
            researcher_response.claims,
            citation_grades,
            evidence_pack.sources,
            adversary_response.claims,
            [],  # No critic in fast mode
            judge_result["violations"],
            "fast",
            evidence_pack
        )

        # Adjust for timeout if needed
        if timeout_mgr.get_degradation_level():
            confidence_result = adjust_confidence_for_timeout(
                confidence_result,
                timeout_mgr.get_degradation_level()
            )

        # Cap confidence if Judge timed out
        if judge_result.get("verdict") == "WARN" and any(
            v.get("rule") == "Judge Timeout" for v in judge_result.get("violations", [])
        ):
            print(f"[SYDYN] Capping confidence to 0.60 due to Judge timeout")
            confidence_result["score"] = min(confidence_result["score"], 0.60)
            confidence_result["band"] = "LOW"

        # Store results
        self._store_results(
            query_id,
            researcher_response,
            adversary_response,
            None,  # No critic
            citation_grades,
            evidence_pack,
            judge_result,
            confidence_result
        )

        # Build answer text
        answer_text = self._build_answer_text(researcher_response.claims)

        # Format sources for API response
        sources = []
        for source in evidence_pack.sources[:8]:  # Top 8 sources
            sources.append({
                "source_id": source.source_id,
                "url": source.url,
                "title": source.title or source.url,
                "credibility_score": source.credibility_score
            })

        return {
            "query_id": query_id,
            "query": query_text,
            "answer": answer_text,
            "confidence": confidence_result["score"],
            "confidence_band": confidence_result["band"],
            "confidence_explanation": format_confidence_explanation(confidence_result),
            "verdict": judge_result["verdict"],
            "violations": judge_result["violations"],
            "mode": "fast",
            "sources": sources,
            "claims": {
                "researcher": len(researcher_response.claims),
                "adversary": len(adversary_response.claims),
                "critic": 0  # No critic in fast mode
            }
        }

    def _run_strict_mode(
        self,
        query_id: str,
        query_text: str,
        evidence_pack,
        timeout_mgr: TimeoutManager
    ) -> Dict:
        """Run strict mode pipeline (Researcher + Adversary + Critic + Judge).

        Same structure as fast mode but includes Critic.
        """
        print(f"[SYDYN] Running STRICT mode pipeline\n")

        # Emit status helper
        def emit(msg):
            if hasattr(self, '_status_callback') and self._status_callback:
                self._status_callback(msg)

        # Researcher
        print(f"[SYDYN] Researcher generating answer...")
        emit("Researcher analyzing evidence and drafting claims...")
        researcher_response = self.researcher.generate_answer(query_text, evidence_pack)
        emit(f"Researcher drafted {len(researcher_response.claims)} claims")

        # Adversary
        print(f"[SYDYN] Adversary generating attacks...")
        emit("Adversary generating counter-arguments...")
        adversary_response = self.adversary.generate_attacks(
            query_text,
            researcher_response.claims,
            evidence_pack
        )
        emit(f"Adversary generated {len(adversary_response.claims)} attacks")

        # Critic (if not timed out)
        if timeout_mgr.should_skip_critic():
            critic_response = None
            emit("Critic skipped due to timeout")
        else:
            print(f"[SYDYN] Critic addressing attacks...")
            emit("Critic addressing adversary attacks...")
            critic_response = self.critic.address_attacks(
                query_text,
                researcher_response.claims,
                adversary_response.claims,
                evidence_pack
            )
            emit(f"Critic produced {len(critic_response.claims)} responses")

        # Citation verification
        def llm_function(prompt, task_type, temperature):
            return self.model_router.complete(
                task_type=task_type,
                system_prompt="",
                user_prompt=prompt,
                max_tokens=500
            ).content

        citation_grades = verify_all_citations(
            [{"claim_id": c.claim_id, "text": c.text, "citations": c.citations} for c in researcher_response.claims],
            evidence_pack.sources,
            llm_function
        )

        # Judge
        emit("Judge evaluating against constitutional rules...")
        all_claims = researcher_response.claims + adversary_response.claims
        if critic_response:
            all_claims += critic_response.claims

        try:
            judge_result = self.judge.evaluate(
                query_text,
                all_claims,
                citation_grades,
                evidence_pack,
                mode="strict"
            )
            emit(f"Judge verdict: {judge_result.get('verdict', 'UNKNOWN')}")
        except LLMTimeoutException as e:
            print(f"[SYDYN] WARNING: Judge timed out after 30s - using degraded evaluation")
            # Return degraded judge result with WARN verdict
            judge_result = {
                "verdict": "WARN",
                "violations": [{
                    "rule": "Judge Timeout",
                    "claim_id": "system",
                    "severity": "MAJOR",
                    "explanation": "Judge evaluation timed out - answer may not be fully validated against constitution"
                }],
                "reasoning": "Judge timeout - degraded evaluation",
                "raw_response": str(e)
            }

        # Confidence
        confidence_result = calculate_confidence(
            researcher_response.claims,
            citation_grades,
            evidence_pack.sources,
            adversary_response.claims,
            critic_response.claims if critic_response else [],
            judge_result["violations"],
            "strict",
            evidence_pack
        )

        if timeout_mgr.get_degradation_level():
            confidence_result = adjust_confidence_for_timeout(
                confidence_result,
                timeout_mgr.get_degradation_level()
            )

        # Cap confidence if Judge timed out
        if judge_result.get("verdict") == "WARN" and any(
            v.get("rule") == "Judge Timeout" for v in judge_result.get("violations", [])
        ):
            print(f"[SYDYN] Capping confidence to 0.60 due to Judge timeout")
            confidence_result["score"] = min(confidence_result["score"], 0.60)
            confidence_result["band"] = "LOW"

        # Store results
        self._store_results(
            query_id,
            researcher_response,
            adversary_response,
            critic_response,
            citation_grades,
            evidence_pack,
            judge_result,
            confidence_result
        )

        answer_text = self._build_answer_text(researcher_response.claims)

        # Format sources for API response
        sources = []
        for source in evidence_pack.sources[:8]:  # Top 8 sources
            sources.append({
                "source_id": source.source_id,
                "url": source.url,
                "title": source.title or source.url,
                "credibility_score": source.credibility_score
            })

        return {
            "query_id": query_id,
            "query": query_text,
            "answer": answer_text,
            "confidence": confidence_result["score"],
            "confidence_band": confidence_result["band"],
            "confidence_explanation": format_confidence_explanation(confidence_result),
            "verdict": judge_result["verdict"],
            "violations": judge_result["violations"],
            "mode": "strict",
            "sources": sources,
            "claims": {
                "researcher": len(researcher_response.claims),
                "adversary": len(adversary_response.claims),
                "critic": len(critic_response.claims) if critic_response else 0
            }
        }

    def _run_liability_mode(
        self,
        query_id: str,
        query_text: str,
        evidence_pack,
        timeout_mgr: TimeoutManager
    ) -> Dict:
        """Run liability mode pipeline (same as strict but stricter thresholds)."""
        # Same as strict mode for now
        result = self._run_strict_mode(query_id, query_text, evidence_pack, timeout_mgr)
        result["mode"] = "liability"
        return result

    def _reconstruct_cached_result(
        self,
        query_id: str,
        query_text: str,
        cached_data: Dict,
        timeout_mgr
    ) -> Dict:
        """Reconstruct full result from cached KB entry.

        Args:
            query_id: New query ID
            query_text: Query text
            cached_data: Cached answer data from KB
            timeout_mgr: TimeoutManager instance

        Returns:
            Full result dict with all metadata
        """
        import time

        # Get the original query_id (answer_id) from KB entry
        qhash = self.kb.query_hash(query_text)
        kb_entry = self.db.get_kb_entry(qhash)
        original_query_id = kb_entry.get("answer_id") if kb_entry else None

        # Calculate cache age
        last_validated = kb_entry.get("last_validated", time.time()) if kb_entry else time.time()
        cache_age_days = int((time.time() - last_validated) / 86400)

        # Parse confidence features to get confidence band
        confidence_features = cached_data.get("confidence_features", "{}")
        try:
            features = json.loads(confidence_features) if isinstance(confidence_features, str) else confidence_features
            confidence_band = features.get("band", "UNKNOWN")
        except:
            confidence_band = "UNKNOWN"

        # Get sources from database (if original_query_id available)
        sources = []
        if original_query_id:
            # Query sources that were cited for this query's claims
            source_rows = self.db.conn.execute("""
                SELECT DISTINCT s.source_id, s.url, s.title, s.credibility_score
                FROM sources s
                JOIN citation_grades cg ON s.source_id = cg.source_id
                JOIN claims c ON cg.claim_id = c.claim_id
                WHERE c.query_id = ?
                ORDER BY s.credibility_score DESC
                LIMIT 8
            """, (original_query_id,)).fetchall()

            for row in source_rows:
                sources.append({
                    "source_id": row[0],
                    "url": row[1],
                    "title": row[2] or row[1],
                    "credibility_score": row[3] or 0.0
                })

        # Get claims counts for audit trail
        researcher_claims = 0
        adversary_claims = 0
        critic_claims = 0

        if original_query_id:
            claim_counts = self.db.conn.execute("""
                SELECT agent_role, COUNT(*) as count
                FROM claims
                WHERE query_id = ?
                GROUP BY agent_role
            """, (original_query_id,)).fetchall()

            for row in claim_counts:
                role, count = row[0], row[1]
                if role == "researcher":
                    researcher_claims = count
                elif role == "adversary":
                    adversary_claims = count
                elif role == "critic":
                    critic_claims = count

        # Get violations (already stored as JSON string)
        violations_json = self.db.conn.execute("""
            SELECT constitutional_violations
            FROM answers
            WHERE query_id = ?
        """, (original_query_id,)).fetchone() if original_query_id else None

        violations = []
        if violations_json and violations_json[0]:
            try:
                violations = json.loads(violations_json[0])
            except:
                violations = []

        # Get query mode
        mode_row = self.db.conn.execute("""
            SELECT mode FROM queries WHERE query_id = ?
        """, (original_query_id,)).fetchone() if original_query_id else None
        mode = mode_row[0] if mode_row else "unknown"

        # Build full result matching non-cached format
        return {
            "query_id": query_id,
            "query": query_text,
            "answer": cached_data["answer_text"],
            "confidence": cached_data["confidence_score"],
            "confidence_band": confidence_band,
            "confidence_explanation": f"Cached result validated {cache_age_days} days ago",
            "verdict": "PASS",  # Cached answers always passed
            "violations": violations,
            "mode": mode,
            "sources": sources,
            "claims": {
                "researcher": researcher_claims,
                "adversary": adversary_claims,
                "critic": critic_claims
            },
            "cached": True,
            "cache_age_days": cache_age_days,
            "validation_count": cached_data.get("validation_count", 1),
            "latency_ms": int(timeout_mgr.elapsed() * 1000)
        }

    def _build_answer_text(self, claims: list) -> str:
        """Build final answer text from claims.

        Args:
            claims: List of Claim objects

        Returns:
            Answer text
        """
        lines = []

        for claim in claims:
            if claim.claim_type != "attack":
                lines.append(f"• {claim.text}")

        return "\n".join(lines)

    def _store_results(
        self,
        query_id: str,
        researcher_response,
        adversary_response,
        critic_response,
        citation_grades,
        evidence_pack,
        judge_result,
        confidence_result
    ):
        """Store all results in database.

        Args:
            query_id: Query ID
            researcher_response: AgentResponse from Researcher
            adversary_response: AgentResponse from Adversary
            critic_response: AgentResponse from Critic (or None)
            citation_grades: Citation grades dict
            evidence_pack: EvidencePack
            judge_result: Judge evaluation result
            confidence_result: Confidence calculation result
        """
        # Store answer
        answer_text = self._build_answer_text(researcher_response.claims)
        self.db.store_answer(
            query_id,
            answer_text,
            confidence_result["score"],
            confidence_result["features_json"],
            json.dumps(judge_result["violations"])
        )

        # Store claims (prefix claim_id with query_id for global uniqueness)
        for claim in researcher_response.claims:
            unique_claim_id = f"{query_id}_{claim.claim_id}"
            self.db.store_claim(unique_claim_id, query_id, claim.text, "researcher")

        for attack in adversary_response.claims:
            unique_claim_id = f"{query_id}_{attack.claim_id}"
            self.db.store_claim(unique_claim_id, query_id, attack.text, "adversary")
            self.db.store_attack(query_id, attack.text, "unknown", "unknown")

        if critic_response:
            for response in critic_response.claims:
                unique_claim_id = f"{query_id}_{response.claim_id}"
                self.db.store_claim(unique_claim_id, query_id, response.text, "critic")

        # Store sources
        for source in evidence_pack.sources:
            self.db.store_source(
                source.source_id,
                source.url,
                source.title,
                source.snippet,
                source.credibility_score,
                source.fetch_failed
            )

        # Store citation grades (use prefixed claim_ids)
        for claim_id, source_grades in citation_grades.items():
            unique_claim_id = f"{query_id}_{claim_id}"
            for source_id, (grade, explanation) in source_grades.items():
                self.db.store_citation_grade(unique_claim_id, source_id, grade, explanation)

    def _estimate_cost(self, mode: str, degradation_level: Optional[str]) -> float:
        """Estimate query cost based on mode and degradation.

        Args:
            mode: "fast" | "strict" | "liability"
            degradation_level: Degradation level if timeout occurred

        Returns:
            Estimated cost in USD
        """
        # Base costs from plan
        if mode == "fast":
            base_cost = 0.05
        elif mode == "strict":
            base_cost = 0.10
        else:  # liability
            base_cost = 0.12

        # Adjust for degradation
        if degradation_level == "no_critic":
            base_cost *= 0.85  # 15% reduction
        elif degradation_level == "no_adversary":
            base_cost *= 0.70  # 30% reduction
        elif degradation_level == "evidence_only":
            base_cost *= 0.30  # 70% reduction (only search + scoring)

        return round(base_cost, 4)
