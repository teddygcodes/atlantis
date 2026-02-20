"""
Atlantis V2 — Perpetual Engine
================================
Phase 2: Autonomous Governance. The forever adversarial cycle.

Each cycle:
  Steps 1-17 : All rival pairs — adversarial claim exchange
  Step 18    : Federal Lab pipeline (independent, budget-free)
  Step 19    : End-of-cycle (city/town formation, abstraction, tier,
               probation/dissolution, logs, exports)

States can and should die.
Knowledge enters the Archive ONLY if it survives challenge.
"""

import json
import copy
import os
import uuid
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple

from agents.base import AgentConfig, FounderProfile, create_federal_lab_agent
from core.models import ModelRouter
from core.persistence import PersistenceLayer
from governance.states import (
    ArchiveEntry,
    RivalPair,
    State,
    StateManager,
    City,
    Town,
    validate_claim,
    extract_validation_rejection_types,
    validate_challenge,
    autofill_discovery_gap,
    normalize_claim,
    run_science_gate,
    decompose_premises,
    check_rebuttal_newness,
    check_anti_loop,
    check_reasoning_depth,
    determine_outcome,
)
from config.settings import (
    TOKEN_VALUES,
    REASONING_DEPTH_BY_TIER,
    SENATE_MIN_QUORUM,
    SENATE_SIMPLE_MAJORITY,
    PROBATION_RESET_OUTCOMES,
    OPTION_C_UNDER_FIRE_COUNTS_PROBATION,
    DISSOLUTION_TRIGGER,
    PROBATION_TRIGGER,
    WARMUP_CYCLES,
    V2_TIERS,
    CONTENT_THRESHOLDS,
    EXECUTIVE_ELECTION_INTERVAL,
    EXECUTIVE_TERM_CYCLES,
    APPEAL_COST_TOKENS,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str):
    print(f"  {msg}")


class PerpetualEngine:
    """
    Orchestrates all rival pairs, Federal Lab, and end-of-cycle operations.
    Runs num_cycles iterations (0 = indefinite).
    """

    def __init__(
        self,
        state_manager: StateManager,
        founder_profiles: List[FounderProfile],
        constitution_text: str,
        db: PersistenceLayer,
        models: ModelRouter,
        content_gen,                   # ContentGenerator (imported in engine.py)
        config: dict,
        output_dir: str = "output",
    ):
        self.state_manager = state_manager
        self.founder_profiles = founder_profiles
        self.constitution_text = constitution_text
        self.phase2_constitution_extract = self._build_phase2_constitution_extract(constitution_text)
        self.db = db
        self.models = models
        self.content_gen = content_gen
        self.config = config
        self.output_dir = Path(output_dir)
        self.cycle = 0
        self.federal_lab_config: AgentConfig = create_federal_lab_agent()
        self.federal_lab_last_domain: Optional[str] = None
        self.cycle_log_data: dict = {}
        self._default_cycle_cost = self.config.get("cycle_cost")
        self._default_token_values = copy.deepcopy(TOKEN_VALUES)
        self._default_tier_thresholds = {
            tier: data.get("surviving_claims", 0)
            for tier, data in V2_TIERS.items()
            if tier > 0
        }
        self.active_executive: Optional[Dict] = None
        self.supreme_court_rulings: List[Dict] = []

    def run_cycles(self, num_cycles: int):
        """num_cycles=0 runs indefinitely."""
        count = 0
        while num_cycles == 0 or count < num_cycles:
            self.cycle += 1
            count += 1
            print(f"\n{'='*60}")
            print(f"  CYCLE {self.cycle}")
            print(f"{'='*60}")
            self._run_cycle()

    # ─── MAIN CYCLE ──────────────────────────────────────────────


    @staticmethod
    def _extract_article(text: str, article_heading: str) -> str:
        pattern = rf"(?ms)^##\s+{re.escape(article_heading)}\s*$\n(.*?)(?=^##\s+ARTICLE\s+|^##\s+SIGNATURES|\Z)"
        match = re.search(pattern, text)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_named_section(article_body: str, section_title: str) -> str:
        pattern = rf"(?ms)^\*\*Section\s+\d+\s*:\s*{re.escape(section_title)}\*\*\n(.*?)(?=^\*\*Section\s+\d+\s*:|\Z)"
        match = re.search(pattern, article_body)
        if not match:
            return ""
        return f"**Section: {section_title}**\n" + match.group(1).strip()

    @classmethod
    def _build_phase2_constitution_extract(cls, constitution_text: str) -> str:
        article_iv = cls._extract_article(constitution_text, "ARTICLE IV: KNOWLEDGE AND THE CLAIM PIPELINE")
        article_vi = cls._extract_article(constitution_text, "ARTICLE VI: TOKEN ECONOMY")

        requested_blocks = [
            cls._extract_named_section(article_iv, "Claim Types and Mandatory Structure"),
            cls._extract_named_section(article_iv, "Structural Validation"),
            cls._extract_named_section(article_iv, "Rebuttal Structure"),
            cls._extract_named_section(article_iv, "Four Claim Outcomes"),
            cls._extract_named_section(article_vi, "Budget"),
            cls._extract_named_section(article_vi, "Earning — Claims"),
        ]
        blocks = [b for b in requested_blocks if b]
        if not blocks:
            return constitution_text[:10000]

        extract = (
            "CONSTITUTIONAL EXTRACT FOR PHASE 2 CLAIM ADJUDICATION\n"
            "(claim validation rules, outcomes, scoring rubric, token economy)\n\n"
            + "\n\n".join(blocks)
        )
        return extract[:10000]

    def _run_cycle(self):
        self.cycle_log_data = {
            "cycle": self.cycle,
            "pairs": [],
            "federal_lab": None,
            "content": [],
            "governance": {
                "senate_quorum": {
                    "active_states": 0,
                    "minimum": SENATE_MIN_QUORUM,
                    "suspended": False,
                },
                "senate_votes": [],
                "executive": None,
                "supreme_court": [],
            },
        }

        active_states = self.state_manager.get_all_active_states()
        quorum = self.cycle_log_data["governance"]["senate_quorum"]
        quorum["active_states"] = len(active_states)
        quorum["suspended"] = len(active_states) < SENATE_MIN_QUORUM

        # Steps 1-17: All rival pairs
        for pair in self.state_manager.get_active_pairs():
            if pair.warmup_remaining > 0:
                result = self._run_warmup_pair(pair)
                pair.warmup_remaining -= 1
            else:
                result = self._run_rival_pipeline(pair)
            self.cycle_log_data["pairs"].append(result)

        # Step 18: Federal Lab (after all pairs)
        if self._is_federal_lab_eligible():
            domain = self._get_federal_lab_domain()
            if domain:
                fed_result = self._run_federal_lab_pipeline(domain)
                self.federal_lab_last_domain = domain
                self.cycle_log_data["federal_lab"] = fed_result
            else:
                _log("Federal Lab: no eligible domain (rotation cooldown or none available)")

        # Step 19: End-of-cycle operations
        self._end_of_cycle()

    # ─── RIVAL PIPELINE (STEPS 1-17) ─────────────────────────────

    def _run_rival_pipeline(self, pair: RivalPair) -> dict:
        """
        Full adversarial exchange for one pair.
        Steps 1-17 per the V2 spec.
        """
        sa, sb = pair.state_a, pair.state_b
        _log(f"Pair: {sa.name} vs {sb.name} ({pair.domain})")

        # Context for both researchers
        a_ctx = self._build_archive_context(pair.domain, sa.name)
        b_ctx = self._build_archive_context(pair.domain, sb.name)
        a_meta = self._get_meta_learning(sa.name)
        b_meta = self._get_meta_learning(sb.name)

        # Lab hypotheses (optional)
        open_q = self._get_open_questions(pair.domain)
        a_lab = sa.produce_lab_hypothesis(open_q, self._get_recently_destroyed(sa.name))
        b_lab = sb.produce_lab_hypothesis(open_q, self._get_recently_destroyed(sb.name))

        # Step 1-2: Both States produce claims
        a_raw = sa.produce_claim(
            a_ctx,
            a_meta,
            self.cycle,
            self._get_previous_claim_positions(sa.name),
            a_lab,
        )
        b_raw = sb.produce_claim(
            b_ctx,
            b_meta,
            self.cycle,
            self._get_previous_claim_positions(sb.name),
            b_lab,
        )
        _log(f"  DEBUG RAW CLAIM ({sa.name}):\n{a_raw}\n")
        _log(f"  DEBUG RAW CLAIM ({sb.name}):\n{b_raw}\n")

        # Step 2.5: Discovery GAP ADDRESSED auto-fill repair (Haiku normalization)
        a_raw, a_auto_filled_gap = autofill_discovery_gap(a_raw, self.models)
        b_raw, b_auto_filled_gap = autofill_discovery_gap(b_raw, self.models)

        # Step 3: Structural validation
        a_valid, a_errors = validate_claim(a_raw, self.models, self.db, domain_type=pair.domain_type)
        b_valid, b_errors = validate_claim(b_raw, self.models, self.db, domain_type=pair.domain_type)
        if not a_valid:
            a_rejections = extract_validation_rejection_types(a_raw, a_errors)
            self.db.increment_pipeline_claims(sa.name, False, "", self.cycle, rejection_types=a_rejections)
            _log(f"  {sa.name} claim invalid: {a_errors}")
            return {"pair": f"{sa.name} vs {sb.name}", "skipped": True, "reason": "invalid_claim_a"}
        if not b_valid:
            b_rejections = extract_validation_rejection_types(b_raw, b_errors)
            self.db.increment_pipeline_claims(sb.name, False, "", self.cycle, rejection_types=b_rejections)
            _log(f"  {sb.name} claim invalid: {b_errors}")
            return {"pair": f"{sa.name} vs {sb.name}", "skipped": True, "reason": "invalid_claim_b"}

        # Step 4: Anti-loop check
        a_last3 = self._get_last_3_claims(sa.name)
        b_last3 = self._get_last_3_claims(sb.name)
        if len(a_last3) >= 3:
            loop = check_anti_loop(a_last3, self.models)
            if loop.get("is_loop"):
                _log(f"  {sa.name} anti-loop triggered: {loop.get('explanation')}")
                return {"pair": f"{sa.name} vs {sb.name}", "skipped": True, "reason": "loop_a"}
            _log(f"  {sa.name} anti-loop check passed")
        if len(b_last3) >= 3:
            loop = check_anti_loop(b_last3, self.models)
            if loop.get("is_loop"):
                _log(f"  {sb.name} anti-loop triggered: {loop.get('explanation')}")
                return {"pair": f"{sa.name} vs {sb.name}", "skipped": True, "reason": "loop_b"}
            _log(f"  {sb.name} anti-loop check passed")

        # Step 5: Normalize both (Haiku)
        a_norm = normalize_claim(a_raw, self.models)
        b_norm = normalize_claim(b_raw, self.models)

        # Step 5.5: Science gate (Haiku post-normalization)
        a_science = run_science_gate(a_raw, a_norm, self.models)
        b_science = run_science_gate(b_raw, b_norm, self.models)

        # Step 6: Decompose both (Haiku)
        a_premises = decompose_premises(a_raw, self.models)
        b_premises = decompose_premises(b_raw, self.models)

        # Step 7: Reasoning depth enforcement
        a_meets, a_min = check_reasoning_depth(a_norm.get("reasoning_chain", []), sa.tier)
        b_meets, b_min = check_reasoning_depth(b_norm.get("reasoning_chain", []), sb.tier)
        if not a_meets:
            _log(f"  {sa.name} depth too shallow ({len(a_norm.get('reasoning_chain',[]))} steps, need {a_min})")
            return {"pair": f"{sa.name} vs {sb.name}", "skipped": True, "reason": "depth_a"}
        if not b_meets:
            _log(f"  {sb.name} depth too shallow, need {b_min}")
            return {"pair": f"{sa.name} vs {sb.name}", "skipped": True, "reason": "depth_b"}

        # Steps 8-9: Critics cross-challenge (A attacks B, B attacks A)
        a_challenge = sa.produce_challenge(b_raw, b_premises, self.phase2_constitution_extract)
        b_challenge = sb.produce_challenge(a_raw, a_premises, self.phase2_constitution_extract)

        # Step 10: Validate challenges
        a_ch_ok, _ = validate_challenge(a_challenge)
        b_ch_ok, _ = validate_challenge(b_challenge)
        if not a_ch_ok:
            _log(f"  {sa.name} challenge invalid (vague) — B's claim survives by default")
            a_challenge = ""  # B's claim auto-survives
        if not b_ch_ok:
            _log(f"  {sb.name} challenge invalid (vague) — A's claim survives by default")
            b_challenge = ""

        # Steps 11-12: Researchers rebut
        b_rebuttal = sb.produce_rebuttal(a_challenge, b_raw, self.phase2_constitution_extract) if a_challenge else "OPTION A: No challenge to rebut."
        a_rebuttal = sa.produce_rebuttal(b_challenge, a_raw, self.phase2_constitution_extract) if b_challenge else "OPTION A: No challenge to rebut."

        # Step 13: Rebuttal newness (Haiku)
        a_newness = check_rebuttal_newness(a_raw, a_rebuttal, self.models)
        b_newness = check_rebuttal_newness(b_raw, b_rebuttal, self.models)

        # Step 14: Judge determines outcomes (Sonnet)
        approaches = {sa.name: sa.approach, sb.name: sb.approach}
        a_outcome = determine_outcome(
            a_raw, b_challenge, a_rebuttal, a_newness, pair.domain, approaches, self.models,
            self.phase2_constitution_extract,
            unverified_numeric_assertions=a_science.get("unverified_assertions", []),
        )
        b_outcome = determine_outcome(
            b_raw, a_challenge, b_rebuttal, b_newness, pair.domain, approaches, self.models,
            self.phase2_constitution_extract,
            unverified_numeric_assertions=b_science.get("unverified_assertions", []),
        )

        a_outcome = self._maybe_run_supreme_court_appeal(
            state=sa,
            entry_claim_text=a_raw,
            challenge_text=b_challenge,
            rebuttal_text=a_rebuttal,
            newness_result=a_newness,
            domain=pair.domain,
            approaches=approaches,
            outcome=a_outcome,
            appeal_target_id=None,
        )
        b_outcome = self._maybe_run_supreme_court_appeal(
            state=sb,
            entry_claim_text=b_raw,
            challenge_text=a_challenge,
            rebuttal_text=b_rebuttal,
            newness_result=b_newness,
            domain=pair.domain,
            approaches=approaches,
            outcome=b_outcome,
            appeal_target_id=None,
        )

        self._apply_unverified_numeric_drama_bonus(a_outcome, b_challenge, a_science)
        self._apply_unverified_numeric_drama_bonus(b_outcome, a_challenge, b_science)

        # Step 15: Build ArchiveEntry objects and deposit
        a_entry = self._build_archive_entry(
            state=sa, raw=a_raw, challenge=b_challenge, rebuttal=a_rebuttal,
            norm=a_norm, premises=a_premises, outcome=a_outcome,
            science_gate=a_science,
            challenger_entity=f"{sb.name} Critic", lab_hypothesis=a_lab,
            auto_filled_gap=a_auto_filled_gap,
        )
        b_entry = self._build_archive_entry(
            state=sb, raw=b_raw, challenge=a_challenge, rebuttal=b_rebuttal,
            norm=b_norm, premises=b_premises, outcome=b_outcome,
            science_gate=b_science,
            challenger_entity=f"{sa.name} Critic", lab_hypothesis=b_lab,
            auto_filled_gap=b_auto_filled_gap,
        )

        self.db.save_archive_entry(a_entry)
        self.db.save_archive_entry(b_entry)

        # Update referenced_by for all citations
        for cid in a_entry.citations:
            if cid:
                self.db.update_referenced_by(cid, a_entry.display_id)
        for cid in b_entry.citations:
            if cid:
                self.db.update_referenced_by(cid, b_entry.display_id)

        # Update pipeline claim counts
        a_survived = a_outcome["outcome"] in ("survived", "partial")
        b_survived = b_outcome["outcome"] in ("survived", "partial")
        self.db.increment_pipeline_claims(sa.name, a_survived, a_outcome.get("ruling_type", ""), self.cycle)
        self.db.increment_pipeline_claims(sb.name, b_survived, b_outcome.get("ruling_type", ""), self.cycle)

        # Step 16: Apply token outcomes
        token_ledger = self._apply_token_outcomes(sa, a_norm, a_outcome, sb, b_norm, b_outcome)
        self.db.update_tokens_earned(a_entry.display_id, token_ledger[sa.name]["claim_tokens"])
        self.db.update_tokens_earned(b_entry.display_id, token_ledger[sb.name]["claim_tokens"])

        # Step 17: Update stability scores for surviving claims in domain
        self._update_stability_scores(pair.domain)

        # Probation tracking
        self.db.update_state_probation(sa.name, a_survived)
        self.db.update_state_probation(sb.name, b_survived)

        # Domain health
        self._compute_domain_health(pair.domain)

        # Content evaluation
        for entry, outcome in [(a_entry, a_outcome), (b_entry, b_outcome)]:
            content_files = self.content_gen.evaluate_and_generate({
                "drama_score": outcome["scores"].get("drama", 0),
                "novelty_score": outcome["scores"].get("novelty", 0),
                "depth_score": outcome["scores"].get("depth", 0),
                "event_type": "claim_exchange",
                "exchange": {
                    "display_id": entry.display_id,
                    "source_state": entry.source_state,
                    "claim": entry.raw_claim_text[:500],
                    "challenge": entry.raw_challenge_text[:400],
                    "rebuttal": entry.raw_rebuttal_text[:400],
                    "outcome": outcome["outcome"],
                    "domain": pair.domain,
                },
                "outcome": outcome,
            })
            self.cycle_log_data["content"].extend(content_files)

        _log(f"  {sa.name}: {a_outcome['outcome']} ({a_outcome.get('ruling_type', '')}) | {sb.name}: {b_outcome['outcome']} ({b_outcome.get('ruling_type', '')})")
        return {
            "pair": f"{sa.name} vs {sb.name}",
            "a_entry": a_entry.display_id,
            "b_entry": b_entry.display_id,
            "a_outcome": a_outcome["outcome"],
            "b_outcome": b_outcome["outcome"],
            "a_claim": a_entry.raw_claim_text,
            "b_claim": b_entry.raw_claim_text,
            "a_challenge": a_entry.raw_challenge_text,
            "b_challenge": b_entry.raw_challenge_text,
            "a_rebuttal": a_entry.raw_rebuttal_text,
            "b_rebuttal": b_entry.raw_rebuttal_text,
            "a_scores": {
                "drama": int(a_outcome["scores"].get("drama", 0)),
                "novelty": int(a_outcome["scores"].get("novelty", 0)),
                "depth": int(a_outcome["scores"].get("depth", 0)),
            },
            "a_ruling_type": a_outcome.get("ruling_type", ""),
            "a_judge_reasoning": a_outcome.get("reasoning", ""),
            "a_tokens": token_ledger[sa.name],
            "b_scores": {
                "drama": int(b_outcome["scores"].get("drama", 0)),
                "novelty": int(b_outcome["scores"].get("novelty", 0)),
                "depth": int(b_outcome["scores"].get("depth", 0)),
            },
            "b_ruling_type": b_outcome.get("ruling_type", ""),
            "b_judge_reasoning": b_outcome.get("reasoning", ""),
            "b_tokens": token_ledger[sb.name],
        }

    def _run_warmup_pair(self, pair: RivalPair) -> dict:
        """
        Warmup: both States produce claims, no cross-challenge.
        Auto-deposit as 'surviving'. No token costs or probation.
        """
        sa, sb = pair.state_a, pair.state_b
        _log(f"Warmup: {sa.name} vs {sb.name} (remaining: {pair.warmup_remaining})")

        ctx = self._build_archive_context(pair.domain, sa.name)
        meta = self._get_meta_learning(sa.name)

        for state in (sa, sb):
            raw = state.produce_claim(
                self._build_archive_context(pair.domain, state.name),
                self._get_meta_learning(state.name),
                self.cycle,
                self._get_previous_claim_positions(state.name),
            )
            display_id = self.db.next_display_id()
            entry = ArchiveEntry(
                entry_id=str(uuid.uuid4()),
                display_id=display_id,
                entry_type="claim",
                source_state=state.name,
                source_entity=f"{state.name} Researcher",
                cycle_created=self.cycle,
                status="surviving",
                archive_tier="main",
                claim_type="discovery",
                raw_claim_text=raw,
                outcome="survived",
                outcome_reasoning="Warmup cycle — no cross-challenge.",
                drama_score=1, novelty_score=3, depth_score=2,
            )
            self.db.save_archive_entry(entry)

        return {
            "pair": f"{sa.name} vs {sb.name}",
            "warmup": True,
            "remaining_after": pair.warmup_remaining - 1,
        }

    # ─── FEDERAL LAB PIPELINE (STEP 18) ──────────────────────────

    def _run_federal_lab_pipeline(self, domain: str) -> dict:
        """
        Budget-free. Finds highest-impact surviving claim and inverts an assumption.
        Separate from rival pair pipeline.
        """
        _log(f"Federal Lab → domain: {domain}")

        target = self.db.get_highest_impact_claim(domain, self.federal_lab_last_domain)
        if not target:
            _log("  Federal Lab: no eligible claim")
            return {"skipped": True, "reason": "no_eligible_claim", "domain": domain}

        # Decompose target's premises
        target_premises = decompose_premises(target.get("raw_claim_text", ""), self.models)

        # Federal Lab inverts one implicit assumption
        response = self.models.complete(
            task_type="federal_lab",
            system_prompt=self.federal_lab_config.system_prompt,
            user_prompt=(
                f"TARGET CLAIM (Archive entry {target['display_id']}):\n"
                f"{target.get('raw_claim_text', '')}\n\n"
                f"IMPLICIT ASSUMPTIONS:\n"
                f"{target_premises.get('implicit_assumptions', [])}\n\n"
                f"Invert ONE assumption and produce a Challenge Claim. "
                f"Radical thinking encouraged. Logical consistency required.\n"
                f"Format:\n"
                f"ASSUMPTION INVERTED: [which one]\n"
                f"STEP 1: [reasoning from the inversion]\n"
                f"STEP 2: [further reasoning]\n"
                f"CONCLUSION: [what this implies if the assumption is wrong]"
            ),
            max_tokens=800,
        )
        challenge_text = response.content or ""

        # Target State's Researcher rebuts
        target_state = self.state_manager.get_state(target.get("source_state", ""))
        if not target_state:
            _log(f"  Federal Lab: target state '{target.get('source_state')}' not found")
            return {"skipped": True, "reason": "target_state_not_found", "domain": domain}

        rebuttal_text = target_state.produce_rebuttal(
            challenge_text,
            target.get("raw_claim_text", ""),
            self.phase2_constitution_extract,
        )

        # Newness check
        newness = check_rebuttal_newness(
            target.get("raw_claim_text", ""), rebuttal_text, self.models
        )

        # Judge evaluates
        approaches = {target_state.name: target_state.approach}
        outcome = determine_outcome(
            target.get("raw_claim_text", ""),
            challenge_text,
            rebuttal_text,
            newness,
            domain,
            approaches,
            self.models,
            self.phase2_constitution_extract,
        )

        outcome = self._maybe_run_supreme_court_appeal(
            state=target_state,
            entry_claim_text=target.get("raw_claim_text", ""),
            challenge_text=challenge_text,
            rebuttal_text=rebuttal_text,
            newness_result=newness,
            domain=domain,
            approaches=approaches,
            outcome=outcome,
            appeal_target_id=target["display_id"],
        )

        # Deposit as separate Archive entry
        display_id = self.db.next_display_id()
        fed_entry = ArchiveEntry(
            entry_id=str(uuid.uuid4()),
            display_id=display_id,
            entry_type="claim",
            source_state=target.get("source_state", ""),
            source_entity=f"{target.get('source_state', '')} Researcher",
            cycle_created=self.cycle,
            status=outcome["outcome"],
            archive_tier=self.db._archive_tier_for_status(outcome["outcome"]),
            claim_type="challenge",
            raw_claim_text=target.get("raw_claim_text", ""),
            raw_challenge_text=challenge_text,
            raw_rebuttal_text=rebuttal_text,
            challenger_entity="Federal Lab",
            outcome=outcome["outcome"],
            outcome_reasoning=outcome.get("reasoning", ""),
            open_questions=outcome.get("open_questions", []),
            drama_score=outcome["scores"].get("drama", 0),
            novelty_score=outcome["scores"].get("novelty", 0),
            depth_score=outcome["scores"].get("depth", 0),
            citations=[target["display_id"]],
        )
        self.db.save_archive_entry(fed_entry)
        self.db.update_referenced_by(target["display_id"], fed_entry.display_id)

        # Apply token outcome to target State (Federal Lab earns nothing)
        self._apply_single_token_outcome(target_state, "discovery", outcome)

        # Update the original claim's status if overturned
        if outcome["outcome"] == "destroyed":
            self.db.update_entry_status(
                target["display_id"],
                "overturned",
                note=f"Overturned by Federal Lab in cycle {self.cycle}",
            )
            # Chain collapse
            collapsed = self.db.run_chain_collapse(
                target["display_id"],
                max_depth=self.config.get("chain_collapse_max_depth", 10),
            )
            if collapsed:
                _log(f"  Chain collapse: {len(collapsed)} entries flagged")

        _log(f"  Federal Lab outcome: {outcome['outcome']} (target: {target['display_id']})")
        inverted_assumption = "Not explicitly labeled by Federal Lab output"
        for line in challenge_text.splitlines():
            if line.strip().upper().startswith("ASSUMPTION INVERTED:"):
                parsed = line.split(":", 1)[1].strip()
                if parsed:
                    inverted_assumption = parsed
                break

        return {
            "domain": domain,
            "target_display_id": target["display_id"],
            "lab_entry_display_id": fed_entry.display_id,
            "inverted_assumption": inverted_assumption,
            "outcome": outcome["outcome"],
        }

    def _count_recursive_dependents(self, display_id: str) -> int:
        """Count unique recursive dependents of an entry (potential chain-collapse impact)."""
        visited = set()
        queue = [display_id]
        max_depth = int(self.config.get("chain_collapse_max_depth", 10))
        depth_map = {display_id: 0}

        while queue:
            current = queue.pop(0)
            depth = depth_map.get(current, 0)
            if depth >= max_depth:
                continue
            for dep_id in self.db.get_entry_dependents(current):
                if dep_id in visited:
                    continue
                visited.add(dep_id)
                queue.append(dep_id)
                depth_map[dep_id] = depth + 1
        return len(visited)

    def _run_court_appeal_vote(
        self,
        claim_text: str,
        challenge_text: str,
        rebuttal_text: str,
        outcome: dict,
        domain: str,
    ) -> Dict[str, object]:
        """Three-judge appeal vote. Returns counts and vote records."""
        judges = ["Originalist", "Pragmatist", "Protectionist"]
        records = []
        overturn = 0
        uphold = 0

        for philosophy in judges:
            response = self.models.complete(
                task_type="court_judges",
                system_prompt=(
                    f"You are a Court Judge with {philosophy} philosophy. "
                    "Decide appeal vote only. Return one line starting with OVERTURN:, UPHOLD:, or ABSTAIN:."
                ),
                user_prompt=(
                    f"DOMAIN: {domain}\n"
                    f"CURRENT OUTCOME: {outcome.get('outcome', '')} ({outcome.get('ruling_type', '')})\n\n"
                    f"CLAIM:\n{claim_text}\n\n"
                    f"CHALLENGE:\n{challenge_text}\n\n"
                    f"REBUTTAL:\n{rebuttal_text}\n\n"
                    "Vote OVERTURN or UPHOLD the current ruling."
                ),
                max_tokens=180,
            ).content or ""

            text = response.strip().upper()
            vote = "ABSTAIN"
            if text.startswith("OVERTURN"):
                vote = "OVERTURN"
                overturn += 1
            elif text.startswith("UPHOLD"):
                vote = "UPHOLD"
                uphold += 1
            records.append({"judge": philosophy, "vote": vote, "reasoning": response.strip()})

        return {
            "overturn": overturn,
            "uphold": uphold,
            "margin": abs(overturn - uphold),
            "records": records,
        }

    def _maybe_run_supreme_court_appeal(
        self,
        state: State,
        entry_claim_text: str,
        challenge_text: str,
        rebuttal_text: str,
        newness_result: dict,
        domain: str,
        approaches: Dict[str, str],
        outcome: dict,
        appeal_target_id: Optional[str],
    ) -> dict:
        """
        Supreme Court (Opus) is invoked ONLY when:
        1) Senator files appeal for a destroyed claim,
        2) Court appeal vote is tied/within 1 vote,
        3) Chain collapse would affect 3+ dependent claims.
        """
        if outcome.get("outcome") != "destroyed":
            return outcome
        if state.token_budget < APPEAL_COST_TOKENS:
            return outcome

        state.deduct_tokens(APPEAL_COST_TOKENS)
        potential_dependents = (
            self._count_recursive_dependents(appeal_target_id) if appeal_target_id else 0
        )
        vote = self._run_court_appeal_vote(
            claim_text=entry_claim_text,
            challenge_text=challenge_text,
            rebuttal_text=rebuttal_text,
            outcome=outcome,
            domain=domain,
        )
        close_vote = vote["margin"] <= 1
        invoke_supreme = close_vote and potential_dependents >= 3

        appeal_record = {
            "state": state.name,
            "domain": domain,
            "appeal_target": appeal_target_id,
            "filed": True,
            "vote": vote,
            "potential_dependents": potential_dependents,
            "invoked_supreme_court": invoke_supreme,
        }
        self.cycle_log_data["governance"]["supreme_court"].append(appeal_record)

        if not invoke_supreme:
            return outcome

        supreme_outcome = determine_outcome(
            entry_claim_text,
            challenge_text,
            rebuttal_text,
            newness_result,
            domain,
            approaches,
            self.models,
            constitution_context=self.constitution_text,
            task_type="supreme_court",
        )
        supreme_outcome["appeal_final"] = True
        supreme_outcome["reasoning"] = (
            f"{supreme_outcome.get('reasoning', '').strip()} "
            "Supreme Court ruling is final — no further appeal."
        ).strip()
        self.supreme_court_rulings.append(
            {
                "cycle": self.cycle,
                "state": state.name,
                "domain": domain,
                "appeal_target": appeal_target_id,
                "outcome": supreme_outcome.get("outcome"),
            }
        )
        return supreme_outcome

    # ─── END-OF-CYCLE (STEP 19) ──────────────────────────────────

    def _end_of_cycle(self):
        """Step 19: all post-pipeline operations."""
        # 19a. City auto-formation
        self._check_city_formation()
        # 19b. Town auto-formation
        self._check_town_formation()
        # 19c. Abstraction pass (every N cycles)
        interval = self.config.get("abstraction_pass_interval", 5)
        if self.cycle % interval == 0:
            self._run_abstraction_pass()
        # 19d. Cross-domain bridges
        self._check_cross_domain_bridges()
        # 19e. Tier advancement
        self._check_tier_advancement()
        # 19f. Probation and dissolution
        self._check_probation_and_dissolution()
        # 19g. Executive election and term management
        self._check_executive_election()
        # Refresh domain health after all system-level operations (federal lab,
        # abstraction, cities/towns) so domain_health.json reflects final cycle state.
        for domain in self._get_all_domains():
            self._compute_domain_health(domain)
        # 19h. Write cycle log
        self._write_cycle_log()
        # 19i. Update domain_health.json
        self._update_domain_health_file()
        # 19j. Export archive
        self._export_archive()

    def _check_city_formation(self):
        """
        Per State: find 5+ surviving claims sharing 2+ citations → spawn City.
        State-bound.
        """
        for state in self.state_manager.get_all_active_states():
            clusters = self.db.get_cluster_candidates(state.name)
            existing_city_ids = {c.city_id for c in state.cities}
            for cluster in clusters:
                cluster_key = frozenset(cluster)
                already_exists = any(
                    frozenset(c.cluster_ids) == cluster_key for c in state.cities
                )
                if already_exists:
                    continue

                city_id = f"city_{state.name}_{self.cycle}_{uuid.uuid4().hex[:6]}"
                city = City(
                    city_id=city_id,
                    state_name=state.name,
                    domain=state.domain,
                    cluster_ids=cluster,
                    db=self.db,
                    models=self.models,
                    cycle=self.cycle,
                )

                # Run analysis
                cluster_claims = [
                    self.db.get_archive_entry(cid) for cid in cluster
                    if self.db.get_archive_entry(cid)
                ]
                analysis_entry = city.run_analysis(cluster_claims)
                self.db.save_archive_entry(analysis_entry)
                for cid in cluster:
                    self.db.update_referenced_by(cid, analysis_entry.display_id)

                state.cities.append(city)
                state.earn_tokens(TOKEN_VALUES.get("city_published", 1000))
                _log(f"  City formed: {city_id} ({len(cluster)} claims)")

                # Content: new_city event
                self.content_gen.evaluate_and_generate({
                    "drama_score": 0,
                    "novelty_score": 5,
                    "depth_score": 0,
                    "event_type": "new_city",
                    "exchange": {
                        "city_id": city_id,
                        "state_name": state.name,
                        "domain": state.domain,
                        "cluster_count": len(cluster),
                    },
                })

    def _check_town_formation(self):
        """
        3+ published analyses from any Cities within same State → spawn Town.
        """
        for state in self.state_manager.get_all_active_states():
            if len(state.towns) > 0:
                continue  # Already has a Town (one per State for now)

            total_analyses = sum(
                self.db.get_active_cities(state.name).__len__() and
                (lambda c: c.get("analyses_count", 0))(c)
                for c in self.db.get_active_cities(state.name)
            )
            # Simpler: count analyses entries from this state's cities
            city_rows = self.db.get_active_cities(state.name)
            total_analyses = sum(r.get("analyses_count", 0) for r in city_rows)

            if total_analyses >= 3:
                parent_city_ids = [r["city_id"] for r in city_rows]
                town_id = f"town_{state.name}_{self.cycle}"
                town = Town(
                    town_id=town_id,
                    state_name=state.name,
                    domain=state.domain,
                    parent_city_ids=parent_city_ids,
                    db=self.db,
                    models=self.models,
                    cycle=self.cycle,
                )

                # Gather city analyses for proposal
                city_analyses = self.db.get_surviving_claims(state_name=state.name)
                city_analyses_filtered = [
                    e for e in city_analyses if e.get("entry_type") == "analysis"
                ][:5]

                proposal_entry = town.run_proposal(city_analyses_filtered)
                self.db.save_archive_entry(proposal_entry)

                state.towns.append(town)
                state.earn_tokens(TOKEN_VALUES.get("town_published", 500))
                _log(f"  Town formed: {town_id}")

                self.content_gen.evaluate_and_generate({
                    "drama_score": 0,
                    "novelty_score": 6,
                    "depth_score": 0,
                    "event_type": "new_town",
                    "exchange": {
                        "town_id": town_id,
                        "state_name": state.name,
                        "domain": state.domain,
                    },
                })

    def _run_abstraction_pass(self):
        """
        Per domain: top 20 highest-impact surviving claims → Haiku call → principle.
        Principle deposited with entry_type='principle', challengeable next cycle.
        """
        domains = self._get_all_domains()
        max_claims = self.config.get("abstraction_max_claims_per_domain", 20)

        for domain in domains:
            top_claims = self.db.get_top_impact_claims(domain, limit=max_claims)
            if len(top_claims) < 5:
                continue

            claims_text = "\n\n".join(
                f"{c['display_id']}: {c.get('raw_claim_text', '')[:300]}"
                for c in top_claims
            )

            response = self.models.complete(
                task_type="bridge_extraction",
                system_prompt="Extract the highest-level principles from these claims. Return principles only.",
                user_prompt=(
                    f"Domain: {domain}\n\n"
                    f"TOP {len(top_claims)} SURVIVING CLAIMS:\n{claims_text}\n\n"
                    f"Identify 2-3 domain-level principles that emerge from these claims.\n"
                    f"Format:\n"
                    f"PRINCIPLE 1: [statement]\n"
                    f"PRINCIPLE 2: [statement]\n"
                    f"PRINCIPLE 3: [statement] (optional)"
                ),
                max_tokens=500,
            )

            principles_text = response.content or ""
            display_id = self.db.next_display_id()
            principle_entry = ArchiveEntry(
                entry_id=str(uuid.uuid4()),
                display_id=display_id,
                entry_type="principle",
                source_state="Abstraction Pass",
                source_entity=f"System (Cycle {self.cycle})",
                cycle_created=self.cycle,
                status="surviving",
                archive_tier="main",
                claim_type="foundation",
                raw_claim_text=principles_text,
                citations=[c["display_id"] for c in top_claims],
            )
            self.db.save_archive_entry(principle_entry)
            _log(f"  Abstraction: principle {display_id} generated ({domain})")

    def _check_cross_domain_bridges(self):
        """
        Compare keywords across domains. 2+ shared keywords = bridge candidate.
        Log as research direction. No embeddings — pure keyword matching.
        """
        domains = self._get_all_domains()
        if len(domains) < 2:
            return

        domain_keywords: Dict[str, List[str]] = {}
        for domain in domains:
            claims = self.db.get_surviving_claims(domain=domain)
            kws = []
            for c in claims:
                try:
                    kw_list = json.loads(c.get("keywords_json", "[]"))
                    kws.extend(kw_list)
                except Exception:
                    pass
            domain_keywords[domain] = list(set(kws))

        bridges_found = []
        for i, d1 in enumerate(domains):
            for d2 in domains[i+1:]:
                shared = set(domain_keywords.get(d1, [])) & set(domain_keywords.get(d2, []))
                if len(shared) >= 2:
                    bridges_found.append((d1, d2, list(shared)))

        if bridges_found:
            _log(f"  Cross-domain bridges detected: {len(bridges_found)}")
            for d1, d2, kws in bridges_found:
                _log(f"    {d1} ↔ {d2}: {kws[:3]}")

    def _check_tier_advancement(self):
        """
        Check each State against V2_TIERS thresholds.
        Tier 1: auto. Tier 2: Founder panel. Tier 3: needs City. Tier 4: needs Town.
        Tier 5: 10+ cross-domain citations received.
        """
        for state in self.state_manager.get_all_active_states():
            current_tier = state.tier
            if current_tier >= 5:
                continue

            target_tier = current_tier + 1
            tier_info = V2_TIERS.get(target_tier, {})
            threshold = tier_info.get("surviving_claims", 999999)
            surviving = self.db.get_surviving_claims_count(state.name)

            if surviving < threshold:
                continue

            # Check additional requirements
            qualifies = False
            if target_tier == 1:
                qualifies = True
            elif target_tier == 2:
                qualifies = self._run_founder_panel(state, target_tier)
            elif target_tier == 3:
                qualifies = len(self.db.get_active_cities(state.name)) > 0
            elif target_tier == 4:
                qualifies = len(self.db.get_active_towns(state.name)) > 0
            elif target_tier == 5:
                qualifies = self.db.count_cross_domain_citations_received(state.name) >= 10

            if qualifies:
                state.tier = target_tier
                self.db.update_state_tier(state.name, target_tier)
                state.earn_tokens(TOKEN_VALUES.get("tier_advancement", 10000))
                _log(f"  {state.name} → Tier {target_tier} ({tier_info.get('name', '?')})")

                self.content_gen.evaluate_and_generate({
                    "drama_score": 6,
                    "novelty_score": 5,
                    "depth_score": 5,
                    "event_type": "tier_advancement",
                    "exchange": {
                        "state_name": state.name,
                        "new_tier": target_tier,
                        "tier_name": tier_info.get("name", ""),
                    },
                })

    def _run_founder_panel(self, state: State, target_tier: int) -> bool:
        """
        Select 3 Founders with relevant expertise.
        Majority (2/3) approval required. No State token cost.
        """
        relevant = sorted(
            self.founder_profiles,
            key=lambda fp: sum(
                1 for d in fp.expertise_domains
                if d.lower() in state.domain.lower() or state.domain.lower() in d.lower()
            ),
            reverse=True,
        )[:3]

        if len(relevant) < 3:
            relevant = self.founder_profiles[:3]

        surviving_claims = self.db.get_surviving_claims(state_name=state.name)
        claims_summary = "\n".join(
            f"- {c.get('display_id', '?')}: {c.get('raw_claim_text', '')[:200]}"
            for c in surviving_claims[:10]
        )

        approvals = 0
        for profile in relevant:
            response = self.models.complete(
                task_type="founder_panels",
                system_prompt=profile.to_panel_prompt(),
                user_prompt=(
                    f"TIER {target_tier} ADVANCEMENT REVIEW\n\n"
                    f"State: {state.name}\n"
                    f"Domain: {state.domain}\n"
                    f"Approach: {state.approach}\n\n"
                    f"SURVIVING CLAIMS (sample):\n{claims_summary}\n\n"
                    f"Does this State demonstrate sufficient depth and rigor "
                    f"for Tier {target_tier}? Reply YES or NO with a brief justification."
                ),
                max_tokens=200,
            )
            content = (response.content or "").upper()
            if content.strip().startswith("YES"):
                approvals += 1

        _log(f"  Founder panel for {state.name} Tier {target_tier}: {approvals}/3 approved")
        return approvals >= 2

    def _check_probation_and_dissolution(self):
        """
        Probation: consecutive_probation >= PROBATION_TRIGGER.
        Dissolution trigger: budget=0 AND consecutive_probation >= DISSOLUTION_TRIGGER.
        Senate vote (simple majority, quorum >= SENATE_MIN_QUORUM).
        """
        active_states = self.state_manager.get_all_active_states()
        quorum_met = len(active_states) >= SENATE_MIN_QUORUM

        for state in active_states:
            row = self.db.get_state_budget_row(state.name)
            if not row:
                continue

            probation = row.get("probation_counter", 0)
            budget = row.get("token_budget", state.token_budget)

            # Probation log
            if probation >= PROBATION_TRIGGER:
                _log(f"  {state.name} on probation (consecutive: {probation})")

            # Dissolution check
            if budget == 0 and probation >= DISSOLUTION_TRIGGER:
                _log(f"  {state.name} dissolution triggered!")

                if not quorum_met:
                    _log(f"  Senate quorum not met ({len(active_states)} < 3) — dissolution suspended")
                    continue

                # Senate vote
                dissolve = self._senate_dissolution_vote(state, active_states)
                if dissolve:
                    _log(f"  {state.name} dissolved by Senate vote.")
                    self._dissolve_state(state)
                else:
                    _log(f"  {state.name} dissolution rejected by Senate.")

    def _senate_dissolution_vote(self, candidate: State, voters: List[State]) -> bool:
        """
        Simple majority (>50%) of active States vote to dissolve.
        The candidate State does not vote on their own dissolution.
        """
        eligible = [s for s in voters if s.name != candidate.name]
        yes_votes = 0
        vote_records = []

        for voter in eligible:
            vote_text = voter.produce_senate_vote(
                motion_text=f"Dissolve {candidate.name}?",
                context=(
                    f"{candidate.name} has budget=0 and {DISSOLUTION_TRIGGER}+ consecutive probation cycles. "
                    f"Domain: {candidate.domain}. "
                    f"Surviving claims: {self.db.get_surviving_claims_count(candidate.name)}"
                ),
            )
            if vote_text.upper().strip().startswith("YES"):
                yes_votes += 1
                vote_value = "YES"
            else:
                vote_value = "NO"
            vote_records.append({"senator": voter.name, "vote": vote_value, "rationale": vote_text.strip()})

        ratio = yes_votes / len(eligible) if eligible else 0
        _log(f"  Dissolution vote: {yes_votes}/{len(eligible)} ({ratio:.0%})")
        self.cycle_log_data["governance"]["senate_votes"].append({
            "motion": f"Dissolve {candidate.name}",
            "yes_votes": yes_votes,
            "total_votes": len(eligible),
            "ratio": ratio,
            "records": vote_records,
        })
        return ratio > SENATE_SIMPLE_MAJORITY

    def _dissolve_state(self, state: State):
        """Dissolve a State, generate ALL FOUR content formats, schedule replacement."""
        self.state_manager.dissolve_state(state.name)

        # Generate all four content formats with drama=10
        self.content_gen.evaluate_and_generate({
            "drama_score": 10,
            "novelty_score": 5,
            "depth_score": 5,
            "event_type": "dissolution",
            "exchange": {
                "state_name": state.name,
                "domain": state.domain,
                "surviving_claims": self.db.get_surviving_claims_count(state.name),
                "final_budget": state.token_budget,
            },
        })

        # Explorer format explicitly gets "ruins" event
        self.content_gen.evaluate_and_generate({
            "drama_score": 0,
            "novelty_score": 0,
            "depth_score": 0,
            "event_type": "ruins",
            "exchange": {"state_name": state.name, "domain": state.domain},
        })


    def _apply_unverified_numeric_drama_bonus(self, outcome: dict, challenge_text: str, science_gate: dict):
        """+1 drama when a challenge likely targets an unverified numeric assertion."""
        unverified = [s.lower() for s in (science_gate or {}).get("unverified_assertions", []) if isinstance(s, str)]
        if not unverified:
            return
        challenge_lower = (challenge_text or "").lower()
        if not challenge_lower.strip():
            return

        targeted = any(
            numeric and (numeric in challenge_lower or any(tok in challenge_lower for tok in re.findall(r"\d+(?:\.\d+)?", numeric)))
            for numeric in unverified
        )
        if targeted and outcome.get("outcome") in ("destroyed", "retracted", "partial"):
            scores = outcome.setdefault("scores", {})
            scores["drama"] = min(10, int(scores.get("drama", 0)) + 1)

    # ─── ARCHIVE ENTRY BUILDER ────────────────────────────────────

    def _build_archive_entry(
        self,
        state: State,
        raw: str,
        challenge: str,
        rebuttal: str,
        norm: dict,
        premises: dict,
        outcome: dict,
        science_gate: Optional[dict] = None,
        challenger_entity: str = "",
        lab_hypothesis: Optional[str] = None,
        auto_filled_gap: bool = False,
    ) -> ArchiveEntry:
        display_id = self.db.next_display_id()
        out = outcome["outcome"]
        status_map = {
            "survived": "surviving",
            "partial": "partial",
            "retracted": "retracted",
            "destroyed": "destroyed",
        }
        status = status_map.get(out, "surviving")
        archive_tier_map = {
            "surviving": "main",
            "partial": "quarantine",
            "founding": "quarantine",
            "destroyed": "graveyard",
            "retracted": "graveyard",
        }
        archive_tier = archive_tier_map.get(status, "quarantine")

        science_gate = science_gate or {}

        return ArchiveEntry(
            entry_id=str(uuid.uuid4()),
            display_id=display_id,
            entry_type="claim",
            source_state=state.name,
            source_entity=f"{state.name} Researcher",
            cycle_created=self.cycle,
            status=status,
            archive_tier=archive_tier,
            claim_type=norm.get("claim_type", "discovery"),
            position=norm.get("position", ""),
            reasoning_chain=norm.get("reasoning_chain", []),
            conclusion=norm.get("conclusion", ""),
            keywords=norm.get("keywords", []),
            raw_claim_text=raw,
            raw_challenge_text=challenge,
            raw_rebuttal_text=rebuttal,
            lab_origin_text=lab_hypothesis or "",
            explicit_premises=premises.get("explicit_premises", []),
            implicit_assumptions=premises.get("implicit_assumptions", []),
            challenger_entity=challenger_entity,
            outcome=out,
            ruling_type=outcome.get("ruling_type", ""),
            outcome_reasoning=outcome.get("reasoning", ""),
            open_questions=outcome.get("open_questions", []),
            drama_score=outcome["scores"].get("drama", 0),
            novelty_score=outcome["scores"].get("novelty", 0),
            depth_score=outcome["scores"].get("depth", 0),
            citations=norm.get("citations", []),
            stability_score=1,
            tokens_earned=0,
            unverified_numerics=science_gate.get("unverified_assertions", []),
            auto_filled_gap=auto_filled_gap,
        )

    # ─── TOKEN OUTCOMES ───────────────────────────────────────────

    def _apply_token_outcomes(
        self,
        sa: State, a_norm: dict, a_outcome: dict,
        sb: State, b_norm: dict, b_outcome: dict,
    ) -> Dict[str, Dict[str, int]]:
        """
        Apply token rewards/penalties for both States based on their outcomes.
        A's Critic challenged B's claim. B's Critic challenged A's claim.
        """
        # A's claim (challenged by B)
        a_claim_tokens = self._apply_single_token_outcome(sa, a_norm.get("claim_type", "discovery"), a_outcome)
        # B's challenge on A
        b_challenge_tokens = self._apply_challenge_tokens(sb, a_outcome)

        # B's claim (challenged by A)
        b_claim_tokens = self._apply_single_token_outcome(sb, b_norm.get("claim_type", "discovery"), b_outcome)
        # A's challenge on B
        a_challenge_tokens = self._apply_challenge_tokens(sa, b_outcome)

        return {
            sa.name: {
                "claim_tokens": a_claim_tokens,
                "challenge_tokens": a_challenge_tokens,
                "net_tokens": a_claim_tokens + a_challenge_tokens,
            },
            sb.name: {
                "claim_tokens": b_claim_tokens,
                "challenge_tokens": b_challenge_tokens,
                "net_tokens": b_claim_tokens + b_challenge_tokens,
            },
        }

    def _apply_single_token_outcome(
        self, state: State, claim_type: str, outcome: dict
    ) -> int:
        """Earn/deduct tokens for claim outcome (source State)."""
        out = outcome["outcome"]
        if out == "survived":
            key = "foundation_survived" if claim_type == "foundation" else "discovery_survived"
            amount = TOKEN_VALUES.get(key, 1000)
            state.earn_tokens(amount)
            return amount
        elif out == "partial":
            key = "foundation_partial" if claim_type == "foundation" else "discovery_partial"
            amount = TOKEN_VALUES.get(key, 600)
            state.earn_tokens(amount)
            return amount
        elif out == "retracted":
            amount = TOKEN_VALUES.get("retracted", 500)
            state.earn_tokens(amount)
            return amount
        # destroyed → 0
        return 0

    def _apply_challenge_tokens(self, challenger_state: State, rival_outcome: dict) -> int:
        """Earn/deduct tokens for the challenging State based on rival's outcome."""
        out = rival_outcome["outcome"]
        if out == "destroyed":
            # Prefer the canonical challenge reward key while preserving
            # compatibility with older configs.
            amount = TOKEN_VALUES.get(
                "challenge_succeeded",
                TOKEN_VALUES.get("rival_destroyed_by_critic", 1000),
            )
            challenger_state.earn_tokens(amount)
            return amount
        elif out == "partial":
            amount = TOKEN_VALUES.get("rival_narrowed_by_critic", 800)
            challenger_state.earn_tokens(amount)
            return amount
        elif out in ("survived", "founding"):
            amount = TOKEN_VALUES.get("challenge_failed", -1000)
            challenger_state.deduct_tokens(abs(amount))
            return amount
        return 0

    # ─── STABILITY & DOMAIN HEALTH ────────────────────────────────

    def _update_stability_scores(self, domain: str):
        """Increment stability for all surviving/partial claims in domain."""
        claims = self.db.get_surviving_claims(domain=domain)
        for c in claims:
            if c.get("status") in ("surviving", "partial"):
                self.db.update_stability_score(c["display_id"], increment=1)

    def _compute_domain_health(self, domain: str) -> dict:
        """Compute DMI metrics and save to DB."""
        domain_rows = [r for r in self.db.get_all_active_states() if r.get("domain") == domain]
        domain_states = {s.get("state_name") for s in domain_rows}
        all_entries = [
            e for e in self.db.get_all_archive_entries()
            if e.get("source_state") in domain_states and e.get("entry_type") == "claim"
        ]

        total = len(all_entries)
        surviving = sum(1 for c in all_entries if c.get("status") == "surviving")
        partial = sum(1 for c in all_entries if c.get("status") == "partial")
        destroyed = sum(1 for c in all_entries if c.get("status") == "destroyed")
        total_pipeline = sum(int(r.get("total_pipeline_claims", 0) or 0) for r in domain_rows)
        surviving_pipeline = sum(int(r.get("surviving_pipeline_claims", 0) or 0) for r in domain_rows)
        survival_rate = surviving_pipeline / total_pipeline if total_pipeline > 0 else 0.0

        principles = self.db.get_principle_count(domain)
        compression_ratio = principles / max(surviving, 1)

        lab_stats = self.db.get_lab_origin_stats(domain)
        lab_total = lab_stats.get("total", 0)
        lab_survived = lab_stats.get("survived", 0)
        lab_survival_rate = lab_survived / lab_total if lab_total > 0 else 0.0

        cities = self.db.get_active_cities_in_domain(domain)
        towns = self.db.get_active_towns_in_domain(domain)

        cred = []
        for row in domain_rows[:2]:
            t = row.get("total_pipeline_claims", 0)
            s_count = row.get("surviving_pipeline_claims", 0)
            cred.append(round(s_count / t, 3) if t > 0 else 1.0)
        while len(cred) < 2:
            cred.append(1.0)

        cross_domain_citations = 0
        for entry in all_entries:
            for cid in (entry.get("citations") or []):
                cited = self.db.get_archive_entry(cid)
                if cited and cited.get("source_state") not in domain_states:
                    cross_domain_citations += 1

        failure_distribution = {}
        for row in domain_rows:
            for ruling, count in (row.get("total_rejections_by_type") or {}).items():
                failure_distribution[ruling] = failure_distribution.get(ruling, 0) + int(count)

        cycle_values = [
            int(row.get("cycles_to_first_survival"))
            for row in domain_rows
            if row.get("cycles_to_first_survival") is not None
        ]
        cycles_to_first_survival = (
            round(sum(cycle_values) / len(cycle_values), 2)
            if cycle_values else 0.0
        )

        def _topic_key(entry: dict) -> str:
            position = (entry.get("position") or "").strip().lower()
            if position:
                return position[:180]
            raw = (entry.get("raw_claim_text") or "").strip().lower()
            return raw.splitlines()[0][:180] if raw else ""

        topic_attempts = {}
        for entry in sorted(all_entries, key=lambda e: e.get("display_id", "#000")):
            key = _topic_key(entry)
            if not key:
                continue
            rec = topic_attempts.setdefault(key, {"attempts": 0, "survived": False, "depth": None})
            rec["attempts"] += 1
            if not rec["survived"] and entry.get("status") == "surviving":
                rec["survived"] = True
                rec["depth"] = rec["attempts"]

        revision_depth_values = [rec["depth"] for rec in topic_attempts.values() if rec.get("depth")]
        revision_depth = (
            round(sum(revision_depth_values) / len(revision_depth_values), 2)
            if revision_depth_values else 0.0
        )

        contradiction_trend = "increasing" if destroyed > (surviving + partial) else "stable"
        maturity_phase = self._get_maturity_phase(
            survival_rate=survival_rate,
            contradiction_trend=contradiction_trend,
            compression_ratio=compression_ratio,
            active_cities=len(cities),
            active_towns=len(towns),
            cross_domain_citations=cross_domain_citations,
        )

        metrics = {
            "cycle": self.cycle,
            "total_claims": total,
            "surviving_claims": surviving,
            "partial_claims": partial,
            "destroyed_claims": destroyed,
            "survival_rate": round(survival_rate, 3),
            "cycles_to_first_survival": cycles_to_first_survival,
            "revision_depth": revision_depth,
            "failure_distribution": failure_distribution,
            "credibility_a": cred[0],
            "credibility_b": cred[1],
            "compression_ratio": round(compression_ratio, 3),
            "contradiction_trend": contradiction_trend,
            "cross_domain_citations": cross_domain_citations,
            "lab_survival_rate": round(lab_survival_rate, 3),
            "active_cities": len(cities),
            "active_towns": len(towns),
            "maturity_phase": maturity_phase,
        }

        self.db.save_domain_health(domain, self.cycle, metrics)
        return metrics

    def _get_maturity_phase(
        self,
        survival_rate: float,
        contradiction_trend: str,
        compression_ratio: float,
        active_cities: int,
        active_towns: int,
        cross_domain_citations: int,
    ) -> str:
        if cross_domain_citations > 10 and survival_rate > 0.6:
            return "Mature Influence"
        if active_towns > 0 and cross_domain_citations > 3:
            return "Applied Integration"
        if survival_rate > 0.5 and compression_ratio > 0.2 and active_cities > 0:
            return "Structured Abstraction"
        if 0.3 <= survival_rate <= 0.5 and contradiction_trend != "increasing":
            return "Stabilizing Foundation"
        return "Volatile Exploration"


    def _check_executive_election(self):
        """Run Executive elections every 10 cycles and enforce term locking."""
        if self.active_executive and self.cycle > self.active_executive.get("term_ends_cycle", 0):
            self._clear_executive_parameters()

        if self.cycle % EXECUTIVE_ELECTION_INTERVAL != 0:
            return

        election = self._run_executive_election()
        if election:
            self.cycle_log_data["governance"]["executive"] = election

    def _clear_executive_parameters(self):
        self.config["cycle_cost"] = self._default_cycle_cost
        TOKEN_VALUES.clear()
        TOKEN_VALUES.update(copy.deepcopy(self._default_token_values))
        for tier, threshold in self._default_tier_thresholds.items():
            if tier in V2_TIERS:
                V2_TIERS[tier]["surviving_claims"] = threshold
        self.active_executive = None

    def _collect_system_metrics(self) -> Dict[str, object]:
        active_states = self.state_manager.get_all_active_states()
        domains = self._get_all_domains()
        domain_health = {
            domain: self.db.get_domain_health(domain, latest_only=True) or {}
            for domain in domains
        }

        total_surviving = sum(
            self.db.get_surviving_claims_count(state.name) for state in active_states
        )

        return {
            "cycle": self.cycle,
            "active_states": len(active_states),
            "domains": domain_health,
            "total_surviving_claims": total_surviving,
            "avg_survival_rate": (
                sum((d.get("survival_rate", 0.0) or 0.0) for d in domain_health.values()) / len(domain_health)
                if domain_health
                else 0.0
            ),
            "current_parameters": {
                "cycle_cost": self.config.get("cycle_cost", self._default_cycle_cost),
                "token_values": dict(TOKEN_VALUES),
                "tier_thresholds": {
                    str(tier): data.get("surviving_claims", 0)
                    for tier, data in V2_TIERS.items() if tier > 0
                },
            },
        }

    def _run_executive_election(self) -> Optional[Dict]:
        active_states = self.state_manager.get_all_active_states()
        metrics = self._collect_system_metrics()
        history = self.db.get_elections()
        candidates = self._generate_executive_candidates(metrics, history)
        if not candidates:
            return {"skipped": True, "reason": "candidate_generation_failed"}

        vote_records = []
        tally: Dict[str, int] = {c["name"]: 0 for c in candidates}

        for senator in active_states:
            vote = self._senator_vote_for_executive(senator, candidates, metrics)
            selected = vote.get("candidate")
            if selected not in tally:
                selected = candidates[0]["name"]
            tally[selected] += 1
            vote_records.append({
                "senator": senator.name,
                "vote": selected,
                "reasoning": vote.get("reasoning", "")
            })

        winner_name = max(tally.items(), key=lambda kv: kv[1])[0]
        winner_candidate = next(c for c in candidates if c["name"] == winner_name)
        term_ends = self.cycle + EXECUTIVE_TERM_CYCLES
        election_id = f"exec_{self.cycle}_{uuid.uuid4().hex[:8]}"

        self.db.save_election_result(
            election_id=election_id,
            cycle=self.cycle,
            winner=winner_name,
            platform=winner_candidate["platform"],
            votes=vote_records,
            term_ends_cycle=term_ends,
        )

        self._apply_executive_platform(winner_candidate["platform"], term_ends)

        _log(f"  Executive election winner: {winner_name} ({tally[winner_name]}/{len(active_states)} votes)")
        return {
            "election_id": election_id,
            "cycle": self.cycle,
            "winner": winner_name,
            "candidates": candidates,
            "votes": vote_records,
            "vote_tally": tally,
            "term_ends_cycle": term_ends,
            "platform": winner_candidate["platform"],
        }

    def _generate_executive_candidates(self, metrics: Dict[str, object], history: List[Dict]) -> List[Dict]:
        candidates = []

        def build(name: str, mandate: str) -> Optional[Dict]:
            response = self.models.complete(
                task_type="executive_election",
                system_prompt=(
                    "You are an Executive candidate for Atlantis governance. "
                    "Produce strict JSON only."
                ),
                user_prompt=(
                    f"Constitutional constraints: only adjust cycle_cost, token_values, tier_thresholds. "
                    f"Do not alter constitutional or non-amendable clauses.\n"
                    f"Role: {name}. Mandate: {mandate}.\n"
                    f"System metrics JSON:\n{json.dumps(metrics, indent=2)}\n\n"
                    f"Election history JSON:\n{json.dumps(history[-5:], indent=2)}\n\n"
                    "Return JSON object with keys: summary (string), platform (object). "
                    "platform must include cycle_cost (int), token_values (object of ints), tier_thresholds (object tier->int)."
                ),
                max_tokens=800,
            )
            raw = (response.content or "").strip()
            try:
                parsed = json.loads(raw)
                platform = parsed.get("platform") or {}
                summary = parsed.get("summary", "")
            except json.JSONDecodeError:
                parsed = {}
                summary = ""
                platform = {}

            sanitized = self._sanitize_platform(platform)
            if not summary:
                if name == "Synthesis":
                    summary = "Balance all domains with moderate parameter changes anchored to constitutional defaults."
                else:
                    summary = "Boost underperforming domains via lower cycle cost and stronger survival incentives."

            if not platform and name == "Challenger":
                sanitized["cycle_cost"] = max(100, int(self.config.get("cycle_cost", self._default_cycle_cost) * 0.9))
                for key in ("discovery_survived", "foundation_survived", "challenge_succeeded"):
                    if key in sanitized["token_values"]:
                        sanitized["token_values"][key] = int(sanitized["token_values"][key] * 1.1)

            return {
                "name": name,
                "summary": summary,
                "platform": sanitized,
                "raw": raw,
            }

        is_first = len(history) == 0
        synth = build("Synthesis", "Balance all domains and preserve constitutional intent while optimizing performance.")
        chall = build("Challenger", "Favor underperforming domains and correct weakest system metrics.")
        if synth:
            candidates.append(synth)
        if chall:
            candidates.append(chall)

        if not is_first and self.active_executive:
            incumbent = {
                "name": "Incumbent",
                "summary": "Continue current executive platform with iterative refinement based on term outcomes.",
                "platform": copy.deepcopy(self.active_executive.get("platform", {})),
                "raw": "",
            }
            candidates.insert(0, incumbent)

        return candidates

    def _sanitize_platform(self, platform: Dict) -> Dict:
        cycle_cost = int(platform.get("cycle_cost", self._default_cycle_cost))
        cycle_cost = max(100, cycle_cost)

        token_updates = platform.get("token_values") or {}
        token_values = dict(self._default_token_values)
        for key, value in token_updates.items():
            if key in token_values:
                token_values[key] = int(value)

        tier_updates = platform.get("tier_thresholds") or {}
        tier_thresholds = {str(t): v for t, v in self._default_tier_thresholds.items()}
        for tier, value in tier_updates.items():
            tier_key = str(tier)
            if tier_key in tier_thresholds:
                tier_thresholds[tier_key] = max(1, int(value))

        return {
            "cycle_cost": cycle_cost,
            "token_values": token_values,
            "tier_thresholds": tier_thresholds,
        }

    def _senator_vote_for_executive(self, senator: State, candidates: List[Dict], metrics: Dict[str, object]) -> Dict[str, str]:
        options = "\n".join(
            f"- {c['name']}: {c['summary']}\n  PLATFORM: {json.dumps(c['platform'])}"
            for c in candidates
        )
        response = senator.models.complete(
            task_type="researcher_claims",
            system_prompt=senator.senator_config.system_prompt,
            user_prompt=(
                "Executive election vote. You are one Senator with one vote.\n"
                f"Current system metrics:\n{json.dumps(metrics, indent=2)}\n\n"
                f"Candidate platforms:\n{options}\n\n"
                "Reply in JSON with keys candidate and reasoning. Candidate must exactly match one option."
            ),
            max_tokens=300,
        )
        raw = (response.content or "").strip()
        try:
            parsed = json.loads(raw)
            return {
                "candidate": str(parsed.get("candidate", "")).strip(),
                "reasoning": str(parsed.get("reasoning", "")).strip(),
            }
        except json.JSONDecodeError:
            pick = candidates[0]["name"]
            for c in candidates:
                if c["name"].lower() in raw.lower():
                    pick = c["name"]
                    break
            return {"candidate": pick, "reasoning": raw}

    def _apply_executive_platform(self, platform: Dict, term_ends_cycle: int):
        self.config["cycle_cost"] = int(platform.get("cycle_cost", self._default_cycle_cost))

        TOKEN_VALUES.clear()
        TOKEN_VALUES.update(dict(platform.get("token_values", self._default_token_values)))

        thresholds = platform.get("tier_thresholds", {})
        for tier, data in V2_TIERS.items():
            if tier == 0:
                continue
            key = str(tier)
            if key in thresholds:
                data["surviving_claims"] = int(thresholds[key])

        self.active_executive = {
            "platform": copy.deepcopy(platform),
            "term_ends_cycle": term_ends_cycle,
        }


    # ─── ARCHIVE EXPORT ───────────────────────────────────────────

    def _write_cycle_log(self):
        """Write output/logs/cycle_{N}.md with full exchange records."""
        log_dir = self.output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"cycle_{self.cycle}.md"

        lines = [
            f"# Atlantis V2 — Cycle {self.cycle}",
            f"\n_Generated: {_now()}_\n",
        ]

        governance = self.cycle_log_data.get("governance", {})
        quorum = governance.get("senate_quorum", {})
        lines.append("\n## Governance\n")
        lines.append(
            f"- Senate quorum: {quorum.get('active_states', 0)}/{quorum.get('minimum', SENATE_MIN_QUORUM)} active States"
            f" ({'SUSPENDED' if quorum.get('suspended') else 'ACTIVE'})\n"
        )

        executive = governance.get("executive")
        if executive:
            if executive.get("skipped"):
                lines.append(f"- Executive election: skipped ({executive.get('reason', 'unknown')})\n")
            else:
                lines.append(
                    f"- Executive election: winner {executive.get('winner', '?')} | term ends cycle {executive.get('term_ends_cycle', '?')}\n"
                )

                lines.append("  - Candidate platforms:\n")
                for candidate in executive.get("candidates", []):
                    lines.append(
                        f"    - {candidate.get('name', '?')}: {candidate.get('summary', '')}\n"
                        f"      platform: {json.dumps(candidate.get('platform', {}), ensure_ascii=False)}\n"
                    )

                lines.append("  - Vote records:\n")
                for record in executive.get("votes", []):
                    lines.append(
                        f"    - {record.get('senator', '?')}: {record.get('vote', '?')} — {record.get('reasoning', '')}\n"
                    )

        senate_votes = governance.get("senate_votes", [])
        if senate_votes:
            lines.append("- Senate votes this cycle:\n")
            for vote in senate_votes:
                lines.append(
                    f"  - Motion: {vote.get('motion', '?')} | Result: {vote.get('yes_votes', 0)}/{vote.get('total_votes', 0)} "
                    f"({vote.get('ratio', 0.0):.0%})\n"
                )
                for record in vote.get("records", []):
                    lines.append(f"    - {record.get('senator', '?')}: {record.get('vote', '?')}\n")
        else:
            lines.append("- Senate votes this cycle: none\n")

        for pair_result in self.cycle_log_data.get("pairs", []):
            if pair_result.get("skipped"):
                lines.append(f"\n## {pair_result.get('pair', '?')} — SKIPPED\nReason: {pair_result.get('reason', '?')}\n")
            elif pair_result.get("warmup"):
                lines.append(f"\n## {pair_result.get('pair', '?')} — WARMUP\n")
            else:
                lines.append(
                    f"\n## {pair_result.get('pair', '?')}\n"
                    f"\n### Exchange A ({pair_result.get('a_entry', '?')})\n"
                    f"**Claim**\n{pair_result.get('a_claim', '')}\n\n"
                    f"**Challenge**\n{pair_result.get('a_challenge', '')}\n\n"
                    f"**Rebuttal**\n{pair_result.get('a_rebuttal', '')}\n\n"
                    f"**Outcome**: {pair_result.get('a_outcome', '?')}\n"
                    f"**Judge reasoning**: {pair_result.get('a_judge_reasoning', '').strip() or 'No judge reasoning recorded.'}\n"
                    f"**Scores**: drama={pair_result.get('a_scores', {}).get('drama', 0)}, "
                    f"novelty={pair_result.get('a_scores', {}).get('novelty', 0)}, "
                    f"depth={pair_result.get('a_scores', {}).get('depth', 0)}\n"
                    f"**Tokens**: claim={pair_result.get('a_tokens', {}).get('claim_tokens', 0)}, "
                    f"challenge={pair_result.get('a_tokens', {}).get('challenge_tokens', 0)}, "
                    f"net={pair_result.get('a_tokens', {}).get('net_tokens', 0)}\n"
                    f"\n### Exchange B ({pair_result.get('b_entry', '?')})\n"
                    f"**Claim**\n{pair_result.get('b_claim', '')}\n\n"
                    f"**Challenge**\n{pair_result.get('b_challenge', '')}\n\n"
                    f"**Rebuttal**\n{pair_result.get('b_rebuttal', '')}\n\n"
                    f"**Outcome**: {pair_result.get('b_outcome', '?')}\n"
                    f"**Judge reasoning**: {pair_result.get('b_judge_reasoning', '').strip() or 'No judge reasoning recorded.'}\n"
                    f"**Scores**: drama={pair_result.get('b_scores', {}).get('drama', 0)}, "
                    f"novelty={pair_result.get('b_scores', {}).get('novelty', 0)}, "
                    f"depth={pair_result.get('b_scores', {}).get('depth', 0)}\n"
                    f"**Tokens**: claim={pair_result.get('b_tokens', {}).get('claim_tokens', 0)}, "
                    f"challenge={pair_result.get('b_tokens', {}).get('challenge_tokens', 0)}, "
                    f"net={pair_result.get('b_tokens', {}).get('net_tokens', 0)}\n"
                )

        domains_seen = []
        for pair_result in self.cycle_log_data.get("pairs", []):
            pair_name = pair_result.get("pair", "")
            if " vs " not in pair_name:
                continue
            left_state = pair_name.split(" vs ", 1)[0]
            state = self.state_manager.get_state(left_state)
            if state and state.domain not in domains_seen:
                domains_seen.append(state.domain)

        for domain in domains_seen:
            domain_health = self.db.get_domain_health(domain, latest_only=True) or {}
            lines.append(
                f"\n## Domain Health — {domain}\n"
                f"- Surviving claims: {domain_health.get('surviving_claims', 0)}\n"
                f"- Survival rate: {domain_health.get('survival_rate', 0.0)}\n"
                f"- Avg cycles to first survival: {domain_health.get('cycles_to_first_survival', 0.0)}\n"
                f"- Revision depth: {domain_health.get('revision_depth', 0.0)}\n"
                f"- Failure distribution: {json.dumps(domain_health.get('failure_distribution', {}), ensure_ascii=False)}\n"
                f"- Credibility (State A): {domain_health.get('credibility_a', 1.0)}\n"
                f"- Credibility (State B): {domain_health.get('credibility_b', 1.0)}\n"
                f"- Maturity phase: {domain_health.get('maturity_phase', 'unknown')}\n"
            )

        fed = self.cycle_log_data.get("federal_lab")
        if fed:
            if fed.get("skipped"):
                lines.append(f"\n## Federal Lab — SKIPPED\nReason: {fed.get('reason', '?')}\n")
            else:
                lines.append(
                    f"\n## Federal Lab\n"
                    f"- Domain: {fed.get('domain', '?')}\n"
                    f"- Target: `{fed.get('target_display_id', '?')}`\n"
                    f"- Inverted assumption: {fed.get('inverted_assumption', 'not captured')}\n"
                    f"- Lab entry: `{fed.get('lab_entry_display_id', '?')}`\n"
                    f"- Outcome: **{fed.get('outcome', '?')}**\n"
                )

        content_files = self.cycle_log_data.get("content", [])
        if content_files:
            lines.append(f"\n## Content Generated ({len(content_files)} files)\n")
            for f in content_files:
                suffix = Path(f).suffix.lower().lstrip(".")
                fmt = suffix or "unknown"
                lines.append(f"- [{fmt}] {f}\n")

        path.write_text("".join(lines), encoding="utf-8")

    def _update_domain_health_file(self):
        """Write output/domain_health.json with latest metrics for all domains."""
        domains = self._get_all_domains()
        health = {}
        for domain in domains:
            row = self.db.get_domain_health(domain, latest_only=True)
            if row:
                health[domain] = row
            else:
                health[domain] = {
                    "cycle": self.cycle,
                    "total_entries": 0,
                    "surviving": 0,
                    "partial": 0,
                    "destroyed": 0,
                    "survival_rate": 0.0,
                    "cycles_to_first_survival": 0.0,
                    "revision_depth": 0.0,
                    "failure_distribution": {},
                    "compression_ratio": 0.0,
                    "lab_survival_rate": 0.0,
                    "active_cities": 0,
                    "active_towns": 0,
                    "status": "no_eligible_claims",
                }
        out_path = self.output_dir / "domain_health.json"
        out_path.write_text(json.dumps(health, indent=2), encoding="utf-8")

    def _export_archive(self):
        """
        Rebuild output/archive.md (human-readable, grouped by archive tier).
        Rebuild output/archive.json (programmatic access).
        """
        all_entries = self.db.get_all_archive_entries()

        # Sort by display_id (which encodes insertion order)
        all_entries.sort(key=lambda e: e.get("display_id", "#000"))

        md_lines = ["# Atlantis V2 — Archive\n", f"_Last updated: cycle {self.cycle}_\n\n"]
        tier_sections = [
            ("main", "## Main Archive (Surviving)\n\n"),
            ("quarantine", "## Quarantine (Partial/Under Review)\n\n"),
            ("graveyard", "## Graveyard (Destroyed/Retracted)\n\n"),
        ]

        for tier, heading in tier_sections:
            tier_entries = [e for e in all_entries if e.get("archive_tier") == tier]
            md_lines.append(heading)
            if not tier_entries:
                md_lines.append("_No entries in this tier._\n\n")
                continue

            for e in tier_entries:
                status = e.get("status", "?")
                did = e.get("display_id", "?")
                source = e.get("source_state", "?")
                entity = e.get("source_entity", "?")
                cltype = e.get("claim_type", "?")
                outcome = e.get("outcome", "")
                outcome_reasoning = e.get("outcome_reasoning", "")
                citations = e.get("citations") or []

                scores = {
                    "Novelty": e.get("novelty_score"),
                    "Impact": e.get("impact_score"),
                    "Depth": e.get("depth_score"),
                    "Drama": e.get("drama_score"),
                    "Stability": e.get("stability_score"),
                    "Tokens": e.get("tokens_earned"),
                }
                score_line = " | ".join(
                    f"{label}: {value}" for label, value in scores.items() if value is not None
                )

                md_lines.append(
                    f"### {did} [{status.upper()}]\n"
                    f"**Source State**: {source}  |  **Entity**: {entity}\n"
                    f"**Claim Type**: {cltype}  |  **Cycle**: {e.get('cycle_created', '?')}\n\n"
                    f"#### Claim\n{e.get('raw_claim_text', '')}\n\n"
                )
                if e.get("raw_challenge_text"):
                    md_lines.append(f"#### Challenge\n{e.get('raw_challenge_text', '')}\n\n")
                if e.get("raw_rebuttal_text"):
                    md_lines.append(f"#### Rebuttal\n{e.get('raw_rebuttal_text', '')}\n\n")
                if outcome:
                    md_lines.append(f"#### Outcome\n- Status: {outcome}\n")
                    if outcome_reasoning:
                        md_lines.append(f"- Judge reasoning: {outcome_reasoning}\n")
                    md_lines.append("\n")

                md_lines.append("#### Scores\n")
                md_lines.append(f"{score_line if score_line else 'No scores recorded.'}\n\n")

                md_lines.append("#### Citations\n")
                if citations:
                    for citation in citations:
                        md_lines.append(f"- {citation}\n")
                    md_lines.append("\n")
                else:
                    md_lines.append("- None\n\n")

                md_lines.append("---\n\n")

        (self.output_dir / "archive.md").write_text("".join(md_lines), encoding="utf-8")

        # JSON archive (full data)
        (self.output_dir / "archive.json").write_text(
            json.dumps(all_entries, indent=2, default=str), encoding="utf-8"
        )

    # ─── FEDERAL LAB ELIGIBILITY ──────────────────────────────────

    def _is_federal_lab_eligible(self) -> bool:
        activation_cycle = self.config.get("federal_lab_activation_cycle", 5)
        min_claims = self.config.get("federal_lab_min_claims", 10)
        surviving = self.db.count_surviving_claims()
        return (
            self.cycle >= activation_cycle
            or surviving >= min_claims
        )

    def _get_federal_lab_domain(self) -> Optional[str]:
        """
        Find domain with eligible claims, excluding last targeted domain.
        Returns None if only one domain and it's on cooldown.
        """
        domains = self._get_all_domains()
        if not domains:
            return None
        candidates = [d for d in domains if d != self.federal_lab_last_domain]
        if not candidates:
            # All domains on cooldown (only 1 domain) — allow if multiple cycles have passed
            candidates = domains

        for domain in candidates:
            target = self.db.get_highest_impact_claim(domain)
            if target:
                return domain
        return None

    # ─── HELPERS ─────────────────────────────────────────────────

    def _build_archive_context(self, domain: str, state_name: str) -> str:
        """Summary of main-tier claims in domain for Researcher's citable context."""
        claims = self.db.get_surviving_claims(domain=domain)
        claims = [c for c in claims if c.get("archive_tier") == "main"]
        if not claims:
            return "(no citable main-archive claims in domain yet)"
        lines = []
        for c in claims[:15]:
            lines.append(
                f"{c.get('display_id', '?')} [{c.get('status', '?')}]: "
                f"{c.get('raw_claim_text', '')[:200]}"
            )
        return "\n".join(lines)

    def _get_meta_learning(self, state_name: str) -> str:
        """Last 3-5 graveyard claims from this State with judge reasoning."""
        recent = self.db.get_graveyard_claims(state_name=state_name, limit=5)
        if not recent:
            return "(no graveyard claims yet — this is your first cycles)"
        lines = []
        for e in recent:
            lines.append(
                f"{e.get('display_id', '?')}: {e.get('raw_claim_text', '')[:200]}\n"
                f"  Judge: {e.get('outcome_reasoning', 'no reasoning recorded')}"
            )
        return "\n\n".join(lines)

    def _get_open_questions(self, domain: str) -> str:
        """Open questions from City analyses in domain."""
        cities = self.db.get_active_cities_in_domain(domain)
        if not cities:
            return "(no open questions — Cities not yet formed)"
        # Get analyses entries
        analyses = [
            e for e in self.db.get_surviving_claims(domain=domain)
            if e.get("entry_type") == "analysis"
        ]
        questions = []
        for a in analyses[:5]:
            text = a.get("raw_claim_text", "")
            for line in text.split("\n"):
                if "RESEARCH DIRECTION" in line.upper() or "?" in line:
                    questions.append(line.strip())
        return "\n".join(questions[:5]) or "(no specific research directions yet)"

    def _get_recently_destroyed(self, state_name: str) -> str:
        """Recently graveyarded claims for Lab hypothesis context."""
        destroyed = self.db.get_graveyard_claims(state_name=state_name, limit=3)
        if not destroyed:
            return "(no destroyed claims)"
        return "\n".join(
            f"{e.get('display_id', '?')}: {e.get('raw_claim_text', '')[:200]}"
            for e in destroyed
        )


    def _get_previous_claim_positions(self, state_name: str) -> str:
        """Summarize this State's previous claim POSITION lines for novelty prompting."""
        claims = self.db.get_surviving_claims(state_name=state_name)
        claims.sort(key=lambda e: e.get("display_id", ""))
        if not claims:
            return "(none yet — this is your first claim cycle)"

        summaries = []
        for claim in claims:
            raw = claim.get("raw_claim_text", "")
            position = ""
            for line in raw.splitlines():
                if line.strip().upper().startswith("POSITION:"):
                    position = line.strip()
                    break
            if not position:
                position = f"POSITION: {raw.strip().splitlines()[0][:180]}" if raw.strip() else "POSITION: (empty claim text)"
            summaries.append(f"{claim.get('display_id', '?')}: {position}")

        return "\n".join(summaries[-8:])
    def _get_last_3_claims(self, state_name: str) -> List[str]:
        """Last 3 raw claim texts from this State (for anti-loop detection)."""
        claims = self.db.get_surviving_claims(state_name=state_name)
        claims.sort(key=lambda e: e.get("display_id", ""), reverse=True)
        return [c.get("raw_claim_text", "") for c in claims[:3]]

    def _get_all_domains(self) -> List[str]:
        """Unique domains across all active pairs."""
        domains = []
        seen = set()
        for pair in self.state_manager.get_active_pairs():
            if pair.domain not in seen:
                domains.append(pair.domain)
                seen.add(pair.domain)
        return domains
