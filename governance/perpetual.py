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
import os
import uuid
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
    validate_challenge,
    normalize_claim,
    decompose_premises,
    check_rebuttal_newness,
    check_anti_loop,
    check_reasoning_depth,
    determine_outcome,
)
from governance.validators import run_objective_validation
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
        self.db = db
        self.models = models
        self.content_gen = content_gen
        self.config = config
        self.output_dir = Path(output_dir)
        self.cycle = 0
        self.federal_lab_config: AgentConfig = create_federal_lab_agent()
        self.federal_lab_last_domain: Optional[str] = None
        self.cycle_log_data: dict = {}

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

        # Print final domain health summary at end of run
        health_report = self._generate_comprehensive_domain_health()
        self._print_domain_health_summary(health_report)

    # ─── MAIN CYCLE ──────────────────────────────────────────────

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
            },
        }

        active_states = self.state_manager.get_all_active_states()
        quorum = self.cycle_log_data["governance"]["senate_quorum"]
        quorum["active_states"] = len(active_states)
        quorum["suspended"] = len(active_states) < SENATE_MIN_QUORUM

        # Per-cycle operating cost for every active State
        self._apply_cycle_cost(active_states)

        # Steps 1-17: All rival pairs
        for pair in self.state_manager.get_active_pairs():
            try:
                if pair.warmup_remaining > 0:
                    result = self._run_warmup_pair(pair)
                    pair.warmup_remaining -= 1
                else:
                    result = self._run_rival_pipeline(pair)
                self.cycle_log_data["pairs"].append(result)
            except Exception as e:
                print(f"    PAIR SKIPPED: {pair.domain} — {type(e).__name__}: {e}")
                self.cycle_log_data["pairs"].append({
                    "pair": f"{pair.domain} (error)",
                    "skipped": True,
                    "reason": f"{type(e).__name__}: {str(e)[:100]}"
                })
                continue

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

        # Generate performance profiles for both States
        a_performance = self._generate_state_performance_profile(sa.name)
        b_performance = self._generate_state_performance_profile(sb.name)

        # Step 1-2: Both States produce claims
        a_raw = sa.produce_claim(
            archive_context=a_ctx,
            meta_learning=a_meta,
            cycle_number=self.cycle,
            previous_claims_summary="",
            lab_hypothesis=a_lab,
            performance_context=a_performance,
        )
        b_raw = sb.produce_claim(
            archive_context=b_ctx,
            meta_learning=b_meta,
            cycle_number=self.cycle,
            previous_claims_summary="",
            lab_hypothesis=b_lab,
            performance_context=b_performance,
        )
        _log(f"  DEBUG RAW CLAIM ({sa.name}):\n{a_raw}\n")
        _log(f"  DEBUG RAW CLAIM ({sb.name}):\n{b_raw}\n")

        # Step 3: Structural validation
        a_valid, a_errors = validate_claim(a_raw, self.models, self.db)
        b_valid, b_errors = validate_claim(b_raw, self.models, self.db)
        if not a_valid:
            _log(f"  {sa.name} claim invalid: {a_errors}")
            return {"pair": f"{sa.name} vs {sb.name}", "skipped": True, "reason": "invalid_claim_a"}
        if not b_valid:
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

        # Step 7.5: Objective validation (pre-judge factual checks)
        archive_ids = {c.get("display_id") for c in self.db.get_surviving_claims() if c.get("display_id")}

        a_validation = run_objective_validation(
            claim_text=a_raw,
            domain=pair.domain,
            cited_ids=a_norm.get("citations", []),
            archive_ids=archive_ids,
            state_tier=sa.tier,
        )
        b_validation = run_objective_validation(
            claim_text=b_raw,
            domain=pair.domain,
            cited_ids=b_norm.get("citations", []),
            archive_ids=archive_ids,
            state_tier=sb.tier,
        )

        _log(f"  {sa.name} objective validation: {'PASSED' if a_validation['all_passed'] else 'FLAGS RAISED'}")
        _log(f"  {sb.name} objective validation: {'PASSED' if b_validation['all_passed'] else 'FLAGS RAISED'}")

        # Generate critic performance profiles (Task 67)
        a_critic_profile = self._generate_critic_performance_profile(sa.name)
        b_critic_profile = self._generate_critic_performance_profile(sb.name)

        # Steps 8-9: Critics cross-challenge (A attacks B, B attacks A)
        a_challenge = sa.produce_challenge(b_raw, b_premises, critic_performance_context=a_critic_profile)
        b_challenge = sb.produce_challenge(a_raw, a_premises, critic_performance_context=b_critic_profile)

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
        b_rebuttal = sb.produce_rebuttal(a_challenge, b_raw) if a_challenge else "OPTION A: No challenge to rebut."
        a_rebuttal = sa.produce_rebuttal(b_challenge, a_raw) if b_challenge else "OPTION A: No challenge to rebut."

        # Step 13: Rebuttal newness (Haiku)
        a_newness = check_rebuttal_newness(a_raw, a_rebuttal, self.models)
        b_newness = check_rebuttal_newness(b_raw, b_rebuttal, self.models)

        # Step 14: Judge determines outcomes (Sonnet)
        approaches = {sa.name: sa.approach, sb.name: sb.approach}
        a_outcome = determine_outcome(
            a_raw, b_challenge, a_rebuttal, a_newness, pair.domain, approaches, self.models,
            objective_notes=a_validation["summary"]
        )
        b_outcome = determine_outcome(
            b_raw, a_challenge, b_rebuttal, b_newness, pair.domain, approaches, self.models,
            objective_notes=b_validation["summary"]
        )

        self._apply_anchor_flag_penalty(sa, a_outcome, a_validation)
        self._apply_anchor_flag_penalty(sb, b_outcome, b_validation)

        # Step 15: Build ArchiveEntry objects and deposit
        a_entry = self._build_archive_entry(
            state=sa, raw=a_raw, challenge=b_challenge, rebuttal=a_rebuttal,
            norm=a_norm, premises=a_premises, outcome=a_outcome,
            challenger_entity=f"{sb.name} Critic", lab_hypothesis=a_lab,
            validation_result=a_validation,
        )
        b_entry = self._build_archive_entry(
            state=sb, raw=b_raw, challenge=a_challenge, rebuttal=b_rebuttal,
            norm=b_norm, premises=b_premises, outcome=b_outcome,
            challenger_entity=f"{sa.name} Critic", lab_hypothesis=b_lab,
            validation_result=b_validation,
        )

        self.db.save_archive_entry(a_entry)
        self.db.save_archive_entry(b_entry)

        # Update referenced_by for all citations
        for cid in a_entry.citations:
            if cid:
                self._process_citation(cited_display_id=cid, citing_display_id=a_entry.display_id)
        for cid in b_entry.citations:
            if cid:
                self._process_citation(cited_display_id=cid, citing_display_id=b_entry.display_id)

        # Update pipeline claim counts
        a_survived = a_outcome["outcome"] in ("survived", "partial")
        b_survived = b_outcome["outcome"] in ("survived", "partial")
        self.db.increment_pipeline_claims(sa.name, a_survived)
        self.db.increment_pipeline_claims(sb.name, b_survived)

        # Step 16: Apply token outcomes
        claim_token_earnings = self._apply_token_outcomes(sa, a_norm, a_outcome, sb, b_norm, b_outcome)
        self.db.update_tokens_earned(a_entry.display_id, claim_token_earnings[sa.name])
        self.db.update_tokens_earned(b_entry.display_id, claim_token_earnings[sb.name])

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

        _log(f"  {sa.name}: {a_outcome['outcome']} | {sb.name}: {b_outcome['outcome']}")
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
            "b_scores": {
                "drama": int(b_outcome["scores"].get("drama", 0)),
                "novelty": int(b_outcome["scores"].get("novelty", 0)),
                "depth": int(b_outcome["scores"].get("depth", 0)),
            },
            "a_validation": {
                "all_passed": a_validation["all_passed"],
                "flags": a_validation["flags"],
                "warnings": a_validation["warnings"],
            },
            "b_validation": {
                "all_passed": b_validation["all_passed"],
                "flags": b_validation["flags"],
                "warnings": b_validation["warnings"],
            },
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
            # Generate performance profile for this State
            performance = self._generate_state_performance_profile(state.name)

            raw = state.produce_claim(
                archive_context=self._build_archive_context(pair.domain, state.name),
                meta_learning=self._get_meta_learning(state.name),
                cycle_number=self.cycle,
                previous_claims_summary="",
                performance_context=performance,
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
            challenge_text, target.get("raw_claim_text", "")
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
        self._process_citation(target["display_id"], fed_entry.display_id)

        # Apply token outcome to target State (Federal Lab earns nothing)
        fed_tokens = self._apply_single_token_outcome(target_state, "discovery", outcome)
        self.db.update_tokens_earned(fed_entry.display_id, fed_tokens)

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
        return {
            "domain": domain,
            "target_display_id": target["display_id"],
            "lab_entry_display_id": fed_entry.display_id,
            "outcome": outcome["outcome"],
        }

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
        # Refresh domain health after all system-level operations (federal lab,
        # abstraction, cities/towns) so domain_health.json reflects final cycle state.
        for domain in self._get_all_domains():
            self._compute_domain_health(domain)
        # 19g. Write cycle log
        self._write_cycle_log()
        # 19h. Update domain_health.json
        self._update_domain_health_file()
        # 19i. Export archive
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
                    self._process_citation(cid, analysis_entry.display_id)

                state.cities.append(city)
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
        challenger_entity: str = "",
        lab_hypothesis: Optional[str] = None,
        validation_result: Optional[dict] = None,
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

        validation_json = json.dumps({
            "all_passed": validation_result["all_passed"],
            "flags": validation_result["flags"],
            "warnings": validation_result["warnings"],
            "info": validation_result.get("info", []),
        }) if validation_result else None

        return ArchiveEntry(
            entry_id=str(uuid.uuid4()),
            display_id=display_id,
            entry_type="claim",
            source_state=state.name,
            source_entity=f"{state.name} Researcher",
            cycle_created=self.cycle,
            status=status,
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
            rejection_reason=outcome.get("rejection_reason", ""),
            secondary_rejection_reason=outcome.get("secondary_rejection_reason", ""),
            outcome_reasoning=outcome.get("reasoning", ""),
            open_questions=outcome.get("open_questions", []),
            drama_score=outcome["scores"].get("drama", 0),
            novelty_score=outcome["scores"].get("novelty", 0),
            depth_score=outcome["scores"].get("depth", 0),
            citations=norm.get("citations", []),
            stability_score=1,
            tokens_earned=0,
            validation_json=validation_json,
        )

    # ─── TOKEN OUTCOMES ───────────────────────────────────────────

    def _apply_cycle_cost(self, active_states: List[State]):
        """Deduct per-cycle operating cost from each active State."""
        cycle_cost = int(self.config.get("cycle_cost", 0) or 0)
        if cycle_cost <= 0:
            return
        for state in active_states:
            state.deduct_tokens(cycle_cost)

    def _record_token_event(self, state: State, amount: int, reason: str):
        """Persist non-claim token changes so ledger sums match state budgets."""
        event_entry = ArchiveEntry(
            entry_id=str(uuid.uuid4()),
            display_id=self.db.next_display_id(),
            entry_type="token_event",
            source_state=state.name,
            source_entity=f"{state.name} Treasury",
            cycle_created=self.cycle,
            status="surviving",
            claim_type="foundation",
            position=f"TOKEN_EVENT: {reason}",
            reasoning_chain=[],
            conclusion=reason,
            keywords=["token_event", reason],
            raw_claim_text=f"Token event: {reason}",
            outcome="survived",
            outcome_reasoning="",
            tokens_earned=amount,
        )
        self.db.save_archive_entry(event_entry)

    def _process_citation(self, cited_display_id: str, citing_display_id: str):
        """
        Update citation graph and award one-time Discovery first-citation bonus.
        """
        cited = self.db.get_archive_entry(cited_display_id)
        if not cited:
            return

        existing_refs = cited.get("referenced_by", []) or []
        is_first_citation = len(existing_refs) == 0 and citing_display_id not in existing_refs

        self.db.update_referenced_by(cited_display_id, citing_display_id)

        if (
            is_first_citation
            and (cited.get("claim_type") or "").lower() == "discovery"
            and cited.get("source_state")
        ):
            bonus = TOKEN_VALUES.get("discovery_first_cited", 3000)
            discoverer = self.state_manager.get_state(cited["source_state"])
            if discoverer:
                discoverer.earn_tokens(bonus)
            self.db.update_tokens_earned(cited_display_id, bonus)

    def _apply_token_outcomes(
        self,
        sa: State, a_norm: dict, a_outcome: dict,
        sb: State, b_norm: dict, b_outcome: dict,
    ) -> Dict[str, int]:
        """
        Apply token rewards/penalties for both States based on their outcomes.
        Claim rewards are recorded on claim entries; critic rewards/penalties are
        recorded as separate token_event entries.
        """
        a_claim_tokens = self._apply_single_token_outcome(sa, a_norm.get("claim_type", "discovery"), a_outcome)
        b_claim_tokens = self._apply_single_token_outcome(sb, b_norm.get("claim_type", "discovery"), b_outcome)

        # Critic outcomes are separate economic events
        self._apply_challenge_tokens(sb, a_outcome)
        self._apply_challenge_tokens(sa, b_outcome)

        return {sa.name: a_claim_tokens, sb.name: b_claim_tokens}

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
            amount = TOKEN_VALUES.get("rival_destroyed_by_critic", 1000)
            challenger_state.earn_tokens(amount)
            self._record_token_event(challenger_state, amount, "rival_destroyed_by_critic")
            return amount
        elif out in ("survived", "founding"):
            amount = abs(TOKEN_VALUES.get("challenge_failed", -1000))
            challenger_state.deduct_tokens(amount)
            self._record_token_event(challenger_state, -amount, "challenge_failed")
            return -amount
        return 0

    def _apply_anchor_flag_penalty(self, state: State, outcome: dict, validation: dict) -> int:
        """Penalize surviving claims that raised objective anchor flags."""
        if outcome.get("outcome") == "survived" and not validation.get("all_passed", True):
            amount = abs(TOKEN_VALUES.get("anchor_flagged_but_survived", -200))
            state.deduct_tokens(amount)
            self._record_token_event(state, -amount, "anchor_flagged_but_survived")
            print(f"    {state.name} penalized -200 tokens (anchor flags on surviving claim)")
            return -amount
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
        domain_states = {s.get("state_name") for s in self.db.get_all_active_states() if s.get("domain") == domain}
        all_entries = [
            e for e in self.db.get_all_archive_entries()
            if e.get("source_state") in domain_states and e.get("entry_type") == "claim"
        ]

        total = len(all_entries)
        surviving = sum(1 for c in all_entries if c.get("status") == "surviving")
        partial = sum(1 for c in all_entries if c.get("status") == "partial")
        destroyed = sum(1 for c in all_entries if c.get("status") == "destroyed")
        survival_rate = surviving / total if total > 0 else 0.0

        principles = self.db.get_principle_count(domain)
        compression_ratio = principles / max(surviving, 1)

        lab_stats = self.db.get_lab_origin_stats(domain)
        lab_total = lab_stats.get("total", 0)
        lab_survived = lab_stats.get("survived", 0)
        lab_survival_rate = lab_survived / lab_total if lab_total > 0 else 0.0

        cities = self.db.get_active_cities_in_domain(domain)
        towns = self.db.get_active_towns_in_domain(domain)

        state_rows = [r for r in self.db.get_all_active_states() if r.get("domain") == domain]
        cred = []
        for row in state_rows[:2]:
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
                    f"**Scores**: drama={pair_result.get('a_scores', {}).get('drama', 0)}, "
                    f"novelty={pair_result.get('a_scores', {}).get('novelty', 0)}, "
                    f"depth={pair_result.get('a_scores', {}).get('depth', 0)}\n"
                    f"\n### Exchange B ({pair_result.get('b_entry', '?')})\n"
                    f"**Claim**\n{pair_result.get('b_claim', '')}\n\n"
                    f"**Challenge**\n{pair_result.get('b_challenge', '')}\n\n"
                    f"**Rebuttal**\n{pair_result.get('b_rebuttal', '')}\n\n"
                    f"**Outcome**: {pair_result.get('b_outcome', '?')}\n"
                    f"**Scores**: drama={pair_result.get('b_scores', {}).get('drama', 0)}, "
                    f"novelty={pair_result.get('b_scores', {}).get('novelty', 0)}, "
                    f"depth={pair_result.get('b_scores', {}).get('depth', 0)}\n"
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
                    f"- Lab entry: `{fed.get('lab_entry_display_id', '?')}`\n"
                    f"- Outcome: **{fed.get('outcome', '?')}**\n"
                )

        content_files = self.cycle_log_data.get("content", [])
        if content_files:
            lines.append(f"\n## Content Generated ({len(content_files)} files)\n")
            for f in content_files:
                lines.append(f"- {f}\n")

        path.write_text("".join(lines), encoding="utf-8")

    def _update_domain_health_file(self):
        """
        Write comprehensive domain health report to runs/<timestamp>/domain_health.json.
        Includes all metrics, critic performance, and warning flags.
        Updated every cycle, but console summary only shown at run end.
        """
        health_report = self._generate_comprehensive_domain_health()

        # Write to runs/<timestamp>/domain_health.json
        out_path = self.output_dir / "domain_health.json"
        out_path.write_text(json.dumps(health_report, indent=2), encoding="utf-8")

    def _build_state_snapshots(self) -> list:
        """
        Build per-State per-cycle snapshots for learning system.
        Returns list of dicts with state_id, cycle, performance metrics.
        """
        snapshots = []
        all_entries = self.db.get_all_archive_entries()

        # Group entries by state and cycle
        state_cycle_map = {}
        for e in all_entries:
            state = e.get("source_state", "")
            cycle = e.get("cycle_created", 0)
            if not state or state == "Founding Era":
                continue

            key = (state, cycle)
            if key not in state_cycle_map:
                state_cycle_map[key] = {
                    "attempted": 0,
                    "survived": 0,
                    "retracted": 0,
                    "destroyed": 0,
                    "anchor_flags": 0,
                    "token_deltas": [],
                    "judge_feedback": [],
                }

            data = state_cycle_map[key]
            data["attempted"] += 1

            outcome = e.get("outcome", "")
            if outcome == "survived":
                data["survived"] += 1
            elif outcome == "retracted":
                data["retracted"] += 1
            elif outcome == "destroyed":
                data["destroyed"] += 1
            elif outcome == "partial":
                data["survived"] += 1  # Partial counts as survived

            # Count anchor flags from validation_json
            validation = e.get("validation_json")
            if validation:
                try:
                    val_data = json.loads(validation) if isinstance(validation, str) else validation
                    flags = val_data.get("flags", [])
                    data["anchor_flags"] += len(flags)
                except (json.JSONDecodeError, TypeError):
                    pass

            # Track tokens earned
            tokens = e.get("tokens_earned", 0)
            if tokens:
                data["token_deltas"].append(tokens)

            # Collect judge feedback
            reasoning = e.get("outcome_reasoning", "")
            if reasoning and len(reasoning) > 10:
                data["judge_feedback"].append(reasoning)

        # Build snapshot dicts
        for (state, cycle), data in state_cycle_map.items():
            # Compute token delta (sum of all token changes this cycle)
            token_delta = sum(data["token_deltas"])

            # Summarize judge feedback (max 200 tokens ~800 chars)
            feedback_summary = ""
            if data["judge_feedback"]:
                # Take first 3 most recent feedback items
                feedback_text = " | ".join(data["judge_feedback"][:3])
                feedback_summary = feedback_text[:800]  # Approx 200 tokens

            snapshots.append({
                "state_id": state,
                "cycle": cycle,
                "claims_attempted": data["attempted"],
                "claims_survived": data["survived"],
                "claims_retracted": data["retracted"],
                "claims_destroyed": data["destroyed"],
                "anchor_flags": data["anchor_flags"],
                "token_delta": token_delta,
                "judge_feedback_summary": feedback_summary,
            })

        # Sort by cycle, then state
        snapshots.sort(key=lambda x: (x["cycle"], x["state_id"]))
        return snapshots

    def _build_critic_snapshots(self) -> list:
        """
        Build per-critic per-cycle snapshots for learning system.
        Tracks challenge effectiveness and precision.
        """
        snapshots = []
        all_entries = self.db.get_all_archive_entries()

        # Group entries by challenger (critic) and cycle
        critic_cycle_map = {}
        for e in all_entries:
            challenger = e.get("challenger_entity", "")
            cycle = e.get("cycle_created", 0)

            # Skip if no challenger (unchallenged claims) or if Federal Lab
            if not challenger or challenger == "Federal Lab":
                continue

            key = (challenger, cycle)
            if key not in critic_cycle_map:
                critic_cycle_map[key] = {
                    "issued": 0,
                    "upheld": 0,
                    "partial": 0,
                    "overruled": 0,
                }

            data = critic_cycle_map[key]
            data["issued"] += 1

            outcome = e.get("outcome", "")
            ruling = e.get("ruling_type", "")

            # Challenge upheld if claim was destroyed or retracted
            if outcome in ("destroyed", "retracted"):
                data["upheld"] += 1
            # Partial outcomes: critic forced narrowing (counts as impact, not precision)
            elif outcome == "partial":
                data["partial"] += 1
            # Challenge overruled if claim fully survived
            elif outcome == "survived":
                data["overruled"] += 1

        # Build snapshot dicts
        for (critic, cycle), data in critic_cycle_map.items():
            total = data["issued"]
            upheld = data["upheld"]
            partial_count = data["partial"]
            overruled = data["overruled"]

            # Impact rate: challenges that changed outcome (destroyed/retracted/partial) / total
            # Measures: how often the critic forces ANY change
            impact_rate = (upheld + partial_count) / total if total > 0 else 0.0

            # Precision rate: challenges fully upheld (destroyed/retracted only) / total
            # Measures: how often the critic achieves FULL destruction
            precision_rate = upheld / total if total > 0 else 0.0

            snapshots.append({
                "critic_id": critic,
                "cycle": cycle,
                "challenges_issued": total,
                "challenges_upheld": upheld,
                "challenges_partial": partial_count,
                "challenges_overruled": overruled,
                "impact_rate": round(impact_rate, 3),
                "precision_rate": round(precision_rate, 3),
            })

        # Sort by cycle, then critic
        snapshots.sort(key=lambda x: (x["cycle"], x["critic_id"]))
        return snapshots

    def _build_domain_metrics(self) -> list:
        """
        Build per-domain aggregate metrics for entire run.
        """
        metrics = []
        all_entries = self.db.get_all_archive_entries()

        # Group entries by domain
        domain_map = {}
        for e in all_entries:
            # Infer domain from source_state (e.g., "Physics_Alpha" → "Physics")
            state = e.get("source_state", "")
            if not state or state == "Founding Era":
                continue

            # Extract domain from state name (split on underscore)
            parts = state.split("_")
            domain = parts[0] if parts else state

            if domain not in domain_map:
                domain_map[domain] = {
                    "total": 0,
                    "survived": 0,
                    "retracted": 0,
                    "destroyed": 0,
                    "anchor_flags": 0,
                    "tokens": [],
                }

            data = domain_map[domain]
            data["total"] += 1

            outcome = e.get("outcome", "")
            if outcome in ("survived", "partial"):
                data["survived"] += 1
            elif outcome == "retracted":
                data["retracted"] += 1
            elif outcome == "destroyed":
                data["destroyed"] += 1

            # Count anchor flags
            validation = e.get("validation_json")
            if validation:
                try:
                    val_data = json.loads(validation) if isinstance(validation, str) else validation
                    flags = val_data.get("flags", [])
                    data["anchor_flags"] += len(flags)
                except (json.JSONDecodeError, TypeError):
                    pass

            # Track tokens
            tokens = e.get("tokens_earned", 0)
            if tokens:
                data["tokens"].append(tokens)

        # Build metric dicts
        for domain, data in domain_map.items():
            total = data["total"]
            survived = data["survived"]
            retracted = data["retracted"]
            flags = data["anchor_flags"]

            survival_rate = survived / total if total > 0 else 0.0
            retraction_rate = retracted / total if total > 0 else 0.0
            anchor_flag_rate = flags / total if total > 0 else 0.0

            # Average tokens per outcome (all outcomes, not just survived)
            avg_tokens = sum(data["tokens"]) / len(data["tokens"]) if data["tokens"] else 0.0

            metrics.append({
                "domain": domain,
                "survival_rate": round(survival_rate, 3),
                "retraction_rate": round(retraction_rate, 3),
                "anchor_flag_rate": round(anchor_flag_rate, 3),
                "avg_tokens_per_outcome": round(avg_tokens, 1),
            })

        # Sort by domain name
        metrics.sort(key=lambda x: x["domain"])
        return metrics

    def _generate_state_performance_profile(self, state_name: str) -> str:
        """
        Generate a ~200 token descriptive performance profile for a State.
        Uses recent cycle data to inform researcher without prescribing actions.
        Profile is DESCRIPTIVE ONLY — informs what happened, not what to do.
        """
        # Get all entries for this State
        all_entries = self.db.get_all_archive_entries()
        state_entries = [e for e in all_entries if e.get("source_state") == state_name]

        if not state_entries:
            return f"{state_name}: No claims submitted yet. First cycle."

        # Compute survival stats
        total_claims = len(state_entries)
        survived = len([e for e in state_entries if e.get("outcome") in ("survived", "partial")])
        retracted = len([e for e in state_entries if e.get("outcome") == "retracted"])
        destroyed = len([e for e in state_entries if e.get("outcome") == "destroyed"])

        survival_rate = (survived / total_claims * 100) if total_claims > 0 else 0

        # Collect rejection reasons from retracted/destroyed claims
        rejection_reasons = []
        for e in state_entries:
            outcome = e.get("outcome", "")
            if outcome in ("retracted", "destroyed"):
                reason = e.get("rejection_reason", "")
                if reason:
                    rejection_reasons.append(reason)

        # Count anchor flags
        total_anchor_flags = 0
        for e in state_entries:
            validation = e.get("validation_json")
            if validation:
                try:
                    val_data = json.loads(validation) if isinstance(validation, str) else validation
                    flags = val_data.get("flags", [])
                    total_anchor_flags += len(flags)
                except (json.JSONDecodeError, TypeError):
                    pass

        # Get token trajectory (compare last cycle snapshot to overall)
        state_snapshots = [
            s for s in self._build_state_snapshots()
            if s["state_id"] == state_name
        ]
        token_trajectory = "stable"
        token_delta_total = 0
        if state_snapshots:
            # Sum all token deltas to see overall trend
            token_delta_total = sum(s["token_delta"] for s in state_snapshots)
            if token_delta_total > 1000:
                token_trajectory = "gaining"
            elif token_delta_total < -1000:
                token_trajectory = "declining"

        # Extract judge feedback themes (condensed)
        judge_feedback = []
        for e in state_entries:
            reasoning = e.get("outcome_reasoning", "")
            if reasoning and len(reasoning) > 20:
                # Extract key phrases (simple keyword extraction)
                judge_feedback.append(reasoning)

        # Condense feedback to key themes (take first 2-3 feedback items, summarize)
        feedback_summary = ""
        if judge_feedback:
            # Take most recent feedback (last 2)
            recent_feedback = judge_feedback[-2:]
            # Join and truncate to ~150 chars
            feedback_text = " | ".join(recent_feedback)
            feedback_summary = feedback_text[:150] + ("..." if len(feedback_text) > 150 else "")

        # Compute domain average survival rate for comparison
        # Infer domain from state name (e.g., "Physics_Alpha" → "Physics")
        domain = state_name.split("_")[0] if "_" in state_name else state_name
        domain_entries = [
            e for e in all_entries
            if e.get("source_state", "").startswith(domain) and e.get("source_state") != "Founding Era"
        ]
        domain_survived = len([e for e in domain_entries if e.get("outcome") in ("survived", "partial")])
        domain_total = len(domain_entries)
        domain_survival_rate = (domain_survived / domain_total * 100) if domain_total > 0 else 0

        comparison = "at domain average"
        if survival_rate > domain_survival_rate + 10:
            comparison = "above domain average"
        elif survival_rate < domain_survival_rate - 10:
            comparison = "below domain average"

        # Build profile text (target ~200 tokens, ~800 chars)
        profile_parts = []
        profile_parts.append(f"{state_name}: {survived} of {total_claims} claims survived ({survival_rate:.0f}%).")

        if retracted > 0 or destroyed > 0:
            failure_count = retracted + destroyed
            failure_text = f"{failure_count} retracted/destroyed"
            if rejection_reasons:
                # Show up to 3 unique reasons
                unique_reasons = list(set(rejection_reasons[:3]))
                failure_text += f" ({', '.join(unique_reasons)})"
            profile_parts.append(failure_text + ".")

        if total_anchor_flags > 0:
            profile_parts.append(f"{total_anchor_flags} anchor flags.")
        else:
            profile_parts.append("0 anchor flags.")

        # Token trajectory
        if token_trajectory == "gaining":
            profile_parts.append(f"Token budget gaining (+{token_delta_total:,} this run).")
        elif token_trajectory == "declining":
            profile_parts.append(f"Token budget declining ({token_delta_total:,} this run).")
        else:
            profile_parts.append("Token budget stable.")

        # Judge feedback
        if feedback_summary:
            profile_parts.append(f"Judge feedback: {feedback_summary}")

        # Comparison
        profile_parts.append(f"{comparison.capitalize()} (domain: {domain_survival_rate:.0f}%).")

        return " ".join(profile_parts)

    def _generate_critic_performance_profile(self, state_name: str) -> str:
        """
        Generate ~150 token performance profile for a State's Critic agent.
        Uses critic snapshot data to describe challenge effectiveness.
        DESCRIPTIVE ONLY - does not prescribe actions.
        """
        # Get critic snapshots for this State's critic
        # Critic entity name: "{state_name} Critic"
        critic_entity = f"{state_name} Critic"
        critic_snapshots = [
            s for s in self._build_critic_snapshots()
            if s["critic_id"] == critic_entity
        ]

        if not critic_snapshots:
            return f"{critic_entity}: No challenges issued yet. First engagement."

        # Aggregate stats across all cycles
        total_issued = sum(s["challenges_issued"] for s in critic_snapshots)
        total_upheld = sum(s["challenges_upheld"] for s in critic_snapshots)
        total_partial = sum(s["challenges_partial"] for s in critic_snapshots)
        total_overruled = sum(s["challenges_overruled"] for s in critic_snapshots)

        # Compute overall rates
        # Impact rate: challenges that caused ANY change (upheld + partial)
        impact_rate = ((total_upheld + total_partial) / total_issued * 100) if total_issued > 0 else 0
        # Precision rate: challenges that achieved FULL destruction (upheld only)
        precision_rate = (total_upheld / total_issued * 100) if total_issued > 0 else 0

        # Get judge feedback on challenges (from archive entries where this critic challenged)
        all_entries = self.db.get_all_archive_entries()
        critic_challenges = [
            e for e in all_entries
            if e.get("challenger_entity") == critic_entity
        ]

        # Extract judge feedback on challenge quality
        judge_feedback_items = []
        for e in critic_challenges:
            reasoning = e.get("outcome_reasoning", "")
            if reasoning and len(reasoning) > 20:
                judge_feedback_items.append(reasoning)

        # Condense feedback (last 1-2 items, truncate)
        feedback_summary = ""
        if judge_feedback_items:
            recent_feedback = judge_feedback_items[-1:]  # Just most recent
            feedback_text = " | ".join(recent_feedback)
            feedback_summary = feedback_text[:120] + ("..." if len(feedback_text) > 120 else "")

        # Build profile text (target ~150 tokens, ~600 chars)
        profile_parts = []
        profile_parts.append(
            f"{critic_entity}: {total_issued} challenges issued, {total_upheld} destroyed"
        )

        # Show partial count if present (claims narrowed but not destroyed)
        if total_partial > 0:
            profile_parts[-1] += f", {total_partial} narrowed"

        # Show impact rate (upheld + partial)
        profile_parts[-1] += f" ({impact_rate:.0f}% impact rate)."

        if total_overruled > 0:
            profile_parts.append(f"{total_overruled} overruled.")

        # Precision assessment (upheld / total)
        if precision_rate >= 70:
            profile_parts.append(f"High precision: {precision_rate:.0f}% fully destroyed.")
        elif precision_rate >= 40:
            profile_parts.append(f"Moderate precision: {precision_rate:.0f}% fully destroyed.")
        else:
            profile_parts.append(f"Lower precision: {precision_rate:.0f}% fully destroyed.")

        # Judge feedback
        if feedback_summary:
            profile_parts.append(f"Judge notes: {feedback_summary}")

        return " ".join(profile_parts)

    def _generate_comprehensive_domain_health(self) -> dict:
        """
        Generate comprehensive domain health report for end-of-run analysis.
        Includes all metrics, critic performance, and warning flags.
        """
        all_entries = self.db.get_all_archive_entries()
        critic_snapshots = self._build_critic_snapshots()

        # Group entries by domain
        domain_data = {}
        for e in all_entries:
            # Infer domain from source_state
            state = e.get("source_state", "")
            if not state or state == "Founding Era":
                continue

            domain = state.split("_")[0] if "_" in state else state

            if domain not in domain_data:
                domain_data[domain] = {
                    "total": 0,
                    "survived": 0,
                    "retracted": 0,
                    "destroyed": 0,
                    "anchor_flags": 0,
                    "token_spend": 0,
                    "cycles_active": set(),
                }

            data = domain_data[domain]
            data["total"] += 1
            data["cycles_active"].add(e.get("cycle_created", 0))

            outcome = e.get("outcome", "")
            if outcome in ("survived", "partial"):
                data["survived"] += 1
            elif outcome == "retracted":
                data["retracted"] += 1
            elif outcome == "destroyed":
                data["destroyed"] += 1

            # Count anchor flags
            validation = e.get("validation_json")
            if validation:
                try:
                    val_data = json.loads(validation) if isinstance(validation, str) else validation
                    flags = val_data.get("flags", [])
                    data["anchor_flags"] += len(flags)
                except (json.JSONDecodeError, TypeError):
                    pass

            # Track token spend
            tokens = e.get("tokens_earned", 0)
            data["token_spend"] += abs(tokens)  # Sum absolute value for spend tracking

        # Build health report for each domain
        health_report = {}
        for domain, data in domain_data.items():
            total = data["total"]
            survived = data["survived"]
            retracted = data["retracted"]
            destroyed = data["destroyed"]
            flags = data["anchor_flags"]

            # Calculate rates
            survival_rate = survived / total if total > 0 else 0.0
            retraction_rate = retracted / total if total > 0 else 0.0
            destruction_rate = destroyed / total if total > 0 else 0.0
            anchor_flag_rate = flags / total if total > 0 else 0.0
            avg_tokens_per_outcome = data["token_spend"] / total if total > 0 else 0.0

            # Calculate critic metrics for this domain
            domain_critics = [
                s for s in critic_snapshots
                if s["critic_id"].startswith(domain)
            ]

            critic_impact_rate = 0.0
            critic_precision_rate = 0.0
            if domain_critics:
                critic_impact_rate = sum(c["impact_rate"] for c in domain_critics) / len(domain_critics)
                critic_precision_rate = sum(c["precision_rate"] for c in domain_critics) / len(domain_critics)

            # Determine warning flags
            cycles_count = len(data["cycles_active"])
            weak_critic_warning = survival_rate > 0.90 and cycles_count >= 3
            format_issue_warning = survival_rate < 0.30
            healthy = 0.40 <= survival_rate <= 0.85

            health_report[domain] = {
                "survival_rate": round(survival_rate, 3),
                "retraction_rate": round(retraction_rate, 3),
                "destruction_rate": round(destruction_rate, 3),
                "anchor_flag_rate": round(anchor_flag_rate, 3),
                "avg_tokens_per_outcome": round(avg_tokens_per_outcome, 1),
                "critic_impact_rate": round(critic_impact_rate, 3),
                "critic_precision_rate": round(critic_precision_rate, 3),
                "total_claims": total,
                "cycles_active": cycles_count,
                "flags": {
                    "weak_critic_warning": weak_critic_warning,
                    "format_issue_warning": format_issue_warning,
                    "healthy": healthy,
                }
            }

        return health_report

    def _print_domain_health_summary(self, health_report: dict):
        """
        Print console summary of domain health ranked by survival rate.
        Shows warning flags for domains with issues.
        """
        print("\n" + "="*70)
        print("  DOMAIN HEALTH SUMMARY")
        print("="*70)

        if not health_report:
            print("  No domain data available.")
            return

        # Sort domains by survival rate (descending)
        sorted_domains = sorted(
            health_report.items(),
            key=lambda x: x[1]["survival_rate"],
            reverse=True
        )

        print(f"\n{'Domain':<20} {'Survival':<12} {'Flags':<30}")
        print("-" * 70)

        for domain, metrics in sorted_domains:
            survival = metrics["survival_rate"]
            flags = metrics["flags"]

            # Build flag display
            flag_indicators = []
            if flags["healthy"]:
                flag_indicators.append("✓ Healthy")
            if flags["weak_critic_warning"]:
                flag_indicators.append("⚠ Weak Critic")
            if flags["format_issue_warning"]:
                flag_indicators.append("⚠ Format Issues")

            flag_str = ", ".join(flag_indicators) if flag_indicators else "—"

            print(f"{domain:<20} {survival:>6.1%}       {flag_str}")

        print("\n" + "="*70)
        print(f"  Total domains: {len(health_report)}")
        healthy_count = sum(1 for m in health_report.values() if m["flags"]["healthy"])
        print(f"  Healthy domains: {healthy_count}/{len(health_report)}")
        print("="*70 + "\n")

    def _export_archive(self):
        """
        Rebuild output/archive.md (human-readable, domain+cycle order).
        Rebuild output/archive.json (programmatic access).
        """
        all_entries = self.db.get_all_archive_entries()

        # Sort by display_id (which encodes insertion order)
        all_entries.sort(key=lambda e: e.get("display_id", "#000"))

        # Markdown archive
        md_lines = ["# Atlantis V2 — Archive\n", f"_Last updated: cycle {self.cycle}_\n\n"]
        for e in all_entries:
            status = e.get("status", "?")
            did = e.get("display_id", "?")
            source = e.get("source_state", "?")
            entity = e.get("source_entity", "?")
            cltype = e.get("claim_type", "?")
            outcome = e.get("outcome", "")
            md_lines.append(
                f"## {did} [{status.upper()}]\n"
                f"**Source**: {source} / {entity}  |  **Type**: {cltype}  |  **Cycle**: {e.get('cycle_created', '?')}\n\n"
                f"### Claim\n{e.get('raw_claim_text', '')}\n\n"
            )
            if e.get("raw_challenge_text"):
                md_lines.append(f"### Challenge\n{e.get('raw_challenge_text', '')}\n\n")
            if e.get("raw_rebuttal_text"):
                md_lines.append(f"### Rebuttal\n{e.get('raw_rebuttal_text', '')}\n\n")
            if outcome:
                md_lines.append(f"_Outcome: {outcome}_\n\n")
            md_lines.append("---\n\n")

        (self.output_dir / "archive.md").write_text("".join(md_lines), encoding="utf-8")

        # JSON archive (extended schema with learning system support)
        # Add per-claim computed fields
        enhanced_entries = []
        for e in all_entries:
            # Copy all existing fields
            enhanced = dict(e)

            # Add retraction_reason (primary rejection_reason if retracted/destroyed)
            rejection = e.get("rejection_reason", "")
            retraction_reason = rejection if e.get("outcome") in ("retracted", "destroyed") else None
            enhanced["retraction_reason"] = retraction_reason

            # Add reason_tags (array of primary + secondary if present)
            reason_tags = []
            if rejection:
                reason_tags.append(rejection)
            secondary = e.get("secondary_rejection_reason", "")
            if secondary:
                reason_tags.append(secondary)
            enhanced["reason_tags"] = reason_tags

            enhanced_entries.append(enhanced)

        # Build snapshots
        state_snapshots = self._build_state_snapshots()
        critic_snapshots = self._build_critic_snapshots()
        domain_metrics = self._build_domain_metrics()

        # Structure JSON with nested keys
        archive_data = {
            "archive_entries": enhanced_entries,
            "state_snapshots": state_snapshots,
            "critic_snapshots": critic_snapshots,
            "domain_metrics": domain_metrics,
            "meta": {
                "last_cycle": self.cycle,
                "total_entries": len(enhanced_entries),
                "total_states": len(set(s["state_id"] for s in state_snapshots)),
                "total_critics": len(set(c["critic_id"] for c in critic_snapshots)),
                "total_domains": len(domain_metrics),
            }
        }

        (self.output_dir / "archive.json").write_text(
            json.dumps(archive_data, indent=2, default=str), encoding="utf-8"
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
        """Summary of surviving claims in domain for Researcher's context."""
        claims = self.db.get_surviving_claims(domain=domain)
        if not claims:
            return "(no surviving claims in domain yet)"
        lines = []
        for c in claims[:15]:
            lines.append(
                f"{c.get('display_id', '?')} [{c.get('status', '?')}]: "
                f"{c.get('raw_claim_text', '')[:200]}"
            )
        return "\n".join(lines)

    def _get_meta_learning(self, state_name: str) -> str:
        """Last 3-5 destroyed claims from this State with judge reasoning."""
        # Use get_destroyed_claims which directly queries for status='destroyed'
        recent = self.db.get_destroyed_claims(state_name=state_name, limit=5)
        if not recent:
            return "(no destroyed claims yet — this is your first cycles)"
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
        """Recently destroyed claims for Lab hypothesis context."""
        destroyed = [
            e for e in self.db.get_surviving_claims(state_name=state_name)
            if e.get("status") == "destroyed"
        ]
        destroyed.sort(key=lambda e: e.get("display_id", ""), reverse=True)
        if not destroyed:
            return "(no destroyed claims)"
        return "\n".join(
            f"{e.get('display_id', '?')}: {e.get('raw_claim_text', '')[:200]}"
            for e in destroyed[:3]
        )

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
