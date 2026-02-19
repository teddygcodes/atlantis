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

    # ─── MAIN CYCLE ──────────────────────────────────────────────

    def _run_cycle(self):
        self.cycle_log_data = {
            "cycle": self.cycle,
            "pairs": [],
            "federal_lab": None,
            "content": [],
        }

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
        a_raw = sa.produce_claim(a_ctx, a_meta, a_lab)
        b_raw = sb.produce_claim(b_ctx, b_meta, b_lab)

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
        if len(b_last3) >= 3:
            loop = check_anti_loop(b_last3, self.models)
            if loop.get("is_loop"):
                _log(f"  {sb.name} anti-loop triggered: {loop.get('explanation')}")
                return {"pair": f"{sa.name} vs {sb.name}", "skipped": True, "reason": "loop_b"}

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

        # Steps 8-9: Critics cross-challenge (A attacks B, B attacks A)
        a_challenge = sa.produce_challenge(b_raw, b_premises)
        b_challenge = sb.produce_challenge(a_raw, a_premises)

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
        a_outcome = determine_outcome(a_raw, b_challenge, a_rebuttal, a_newness, pair.domain, approaches, self.models)
        b_outcome = determine_outcome(b_raw, a_challenge, b_rebuttal, b_newness, pair.domain, approaches, self.models)

        # Step 15: Build ArchiveEntry objects and deposit
        a_entry = self._build_archive_entry(
            state=sa, raw=a_raw, challenge=b_challenge, rebuttal=a_rebuttal,
            norm=a_norm, premises=a_premises, outcome=a_outcome,
            challenger_entity=f"{sb.name} Critic", lab_hypothesis=a_lab,
        )
        b_entry = self._build_archive_entry(
            state=sb, raw=b_raw, challenge=a_challenge, rebuttal=b_rebuttal,
            norm=b_norm, premises=b_premises, outcome=b_outcome,
            challenger_entity=f"{sa.name} Critic", lab_hypothesis=b_lab,
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
        self.db.increment_pipeline_claims(sa.name, a_survived)
        self.db.increment_pipeline_claims(sb.name, b_survived)

        # Step 16: Apply token outcomes
        self._apply_token_outcomes(sa, a_norm, a_outcome, sb, b_norm, b_outcome)

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
        quorum_met = len(active_states) >= 3  # SENATE_MIN_QUORUM

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

        ratio = yes_votes / len(eligible) if eligible else 0
        _log(f"  Dissolution vote: {yes_votes}/{len(eligible)} ({ratio:.0%})")
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
            outcome_reasoning=outcome.get("reasoning", ""),
            open_questions=outcome.get("open_questions", []),
            drama_score=outcome["scores"].get("drama", 0),
            novelty_score=outcome["scores"].get("novelty", 0),
            depth_score=outcome["scores"].get("depth", 0),
            citations=norm.get("citations", []),
            stability_score=1,
            tokens_earned=0,
        )

    # ─── TOKEN OUTCOMES ───────────────────────────────────────────

    def _apply_token_outcomes(
        self,
        sa: State, a_norm: dict, a_outcome: dict,
        sb: State, b_norm: dict, b_outcome: dict,
    ):
        """
        Apply token rewards/penalties for both States based on their outcomes.
        A's Critic challenged B's claim. B's Critic challenged A's claim.
        """
        # A's claim (challenged by B)
        self._apply_single_token_outcome(sa, a_norm.get("claim_type", "discovery"), a_outcome)
        # B's challenge on A
        self._apply_challenge_tokens(sb, a_outcome)

        # B's claim (challenged by A)
        self._apply_single_token_outcome(sb, b_norm.get("claim_type", "discovery"), b_outcome)
        # A's challenge on B
        self._apply_challenge_tokens(sa, b_outcome)

    def _apply_single_token_outcome(
        self, state: State, claim_type: str, outcome: dict
    ):
        """Earn/deduct tokens for claim outcome (source State)."""
        out = outcome["outcome"]
        if out == "survived":
            key = "foundation_survived" if claim_type == "foundation" else "discovery_survived"
            amount = TOKEN_VALUES.get(key, 1000)
            state.earn_tokens(amount)
        elif out == "partial":
            key = "foundation_partial" if claim_type == "foundation" else "discovery_partial"
            amount = TOKEN_VALUES.get(key, 600)
            state.earn_tokens(amount)
        elif out == "retracted":
            state.earn_tokens(TOKEN_VALUES.get("retracted", 500))
        # destroyed → 0

    def _apply_challenge_tokens(self, challenger_state: State, rival_outcome: dict):
        """Earn/deduct tokens for the challenging State based on rival's outcome."""
        out = rival_outcome["outcome"]
        if out == "destroyed":
            challenger_state.earn_tokens(TOKEN_VALUES.get("rival_destroyed_by_critic", 1000))
        elif out == "partial":
            challenger_state.earn_tokens(TOKEN_VALUES.get("rival_narrowed_by_critic", 800))
        elif out in ("survived", "founding"):
            challenger_state.deduct_tokens(abs(TOKEN_VALUES.get("challenge_failed", -1000)))

    # ─── STABILITY & DOMAIN HEALTH ────────────────────────────────

    def _update_stability_scores(self, domain: str):
        """Increment stability for all surviving/partial claims in domain."""
        claims = self.db.get_surviving_claims(domain=domain)
        for c in claims:
            if c.get("status") in ("surviving", "partial"):
                self.db.update_stability_score(c["display_id"], increment=1)

    def _compute_domain_health(self, domain: str) -> dict:
        """Compute DMI metrics and save to DB."""
        all_claims = self.db.get_surviving_claims(domain=domain)
        total = len(all_claims)
        surviving = sum(1 for c in all_claims if c.get("status") == "surviving")
        partial = sum(1 for c in all_claims if c.get("status") == "partial")
        destroyed = sum(1 for c in all_claims if c.get("status") == "destroyed")

        survival_rate = surviving / total if total > 0 else 0.0

        principles = self.db.get_principle_count(domain)
        surviving_nonzero = max(surviving, 1)
        compression_ratio = principles / surviving_nonzero

        lab_stats = self.db.get_lab_origin_stats(domain)
        lab_total = lab_stats.get("total", 0)
        lab_survived = lab_stats.get("survived", 0)
        lab_survival_rate = lab_survived / lab_total if lab_total > 0 else 0.0

        cities = self.db.get_active_cities_in_domain(domain)
        towns = self.db.get_active_towns_in_domain(domain)

        maturity_phase = self._get_maturity_phase(
            surviving=surviving,
            survival_rate=survival_rate,
            cities=len(cities),
            compression_ratio=compression_ratio,
        )

        metrics = {
            "cycle": self.cycle,
            "total_entries": total,
            "surviving": surviving,
            "partial": partial,
            "destroyed": destroyed,
            "survival_rate": round(survival_rate, 3),
            "compression_ratio": round(compression_ratio, 3),
            "lab_survival_rate": round(lab_survival_rate, 3),
            "active_cities": len(cities),
            "active_towns": len(towns),
        }

        self.db.save_domain_health(domain, self.cycle, metrics)
        return metrics

    def _get_maturity_phase(
        self, surviving: int, survival_rate: float, cities: int, compression_ratio: float
    ) -> str:
        if surviving < 5:
            return "Genesis"
        if surviving < 15:
            return "Emergence"
        if cities > 0:
            return "Complexity"
        if compression_ratio > 0.1:
            return "Refinement"
        return "Maturity"

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

        for pair_result in self.cycle_log_data.get("pairs", []):
            if pair_result.get("skipped"):
                lines.append(f"\n## {pair_result.get('pair', '?')} — SKIPPED\nReason: {pair_result.get('reason', '?')}\n")
            elif pair_result.get("warmup"):
                lines.append(f"\n## {pair_result.get('pair', '?')} — WARMUP\n")
            else:
                lines.append(
                    f"\n## {pair_result.get('pair', '?')}\n"
                    f"- A Entry: `{pair_result.get('a_entry', '?')}` → **{pair_result.get('a_outcome', '?')}**\n"
                    f"- B Entry: `{pair_result.get('b_entry', '?')}` → **{pair_result.get('b_outcome', '?')}**\n"
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
        """Write output/domain_health.json with latest metrics for all domains."""
        domains = self._get_all_domains()
        health = {}
        for domain in domains:
            row = self.db.get_domain_health(domain, latest_only=True)
            if row:
                health[domain] = row
        out_path = self.output_dir / "domain_health.json"
        out_path.write_text(json.dumps(health, indent=2), encoding="utf-8")

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
                f"{e.get('raw_claim_text', '')[:800]}\n\n"
            )
            if outcome:
                md_lines.append(f"_Outcome: {outcome}_\n\n")
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
        destroyed = [
            e for e in self.db.get_surviving_claims(state_name=state_name)
            if e.get("status") == "destroyed"
        ]
        destroyed.sort(key=lambda e: e.get("display_id", ""), reverse=True)
        recent = destroyed[:5]
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
