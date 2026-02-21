"""
Atlantis V2 — Core Engine
===========================
Top-level orchestrator. Three phases:

  Phase 0 — Founding Period: 20 Founders research freely.
  Phase 1 — Founding Era:    Senate forms rival pairs (Founders vote).
  Phase 2 — Perpetual:       Adversarial governance cycle.

V2 requires a clean start — V1 data directories trigger SystemExit
unless --force-clean is passed.

CONSTITUTION.md must exist in the project root.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config.settings import (
    SYSTEM_NAME, VERSION,
    MOCK_CONFIG, PRODUCTION_CONFIG, DEMO_ELECTRICAL_CONFIG,
    V1_DATA_PATHS, OUTPUT_DIRS,
    MODEL_ALLOCATION,
    SENATE_PAIR_SUPERMAJORITY,
)
from core.models import ModelRouter
from core.persistence import PersistenceLayer
from agents.base import AgentConfig, FounderProfile, get_all_founder_profiles
from founders.convention import FoundingPeriod
from governance.states import State, StateManager, RivalPair
from governance.perpetual import PerpetualEngine
from content.generator import ContentGenerator


# ═══════════════════════════════════════
# ATLANTIS ENGINE
# ═══════════════════════════════════════

class AtlantisEngine:
    """
    Main V2 engine. Run with .run().
    """

    def __init__(
        self,
        config: dict = None,
        mock: bool = False,
        dry_run: bool = False,
        force_clean: bool = False,
        verbose: bool = False,
        api_key: Optional[str] = None,
        demo_electrical: bool = False,
    ):
        self._check_v1_data(force_clean)
        self.constitution_text = self._load_constitution()
        self.phase1_constitution_extract = self._build_phase1_constitution_extract()
        self.config = config or MOCK_CONFIG
        self.mock = mock
        self.dry_run = dry_run
        self.verbose = verbose
        self.demo_electrical = demo_electrical
        self.output_dir = Path("output")
        self._initialize_run_folder()
        self._prepare_output_workspace()

        self.db = PersistenceLayer(str(self.output_dir / "atlantis.db"))
        self.models = ModelRouter(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            mock_mode=mock,
            dry_run=dry_run,
        )
        self.content_gen = ContentGenerator(
            output_dir=str(self.output_dir / "content"),
            models=self.models,
        )

    # ─── PHASE ORCHESTRATION ─────────────────────────────────────

    def run(self):
        print(f"\n{'='*60}")
        print(f"  {SYSTEM_NAME} V{VERSION}")
        print(f"  The Lost Civilization, Rebuilt — Adversarial Knowledge Engine")
        print(f"{'='*60}")
        print(f"\n  Constitution: {len(self.constitution_text)} chars")
        mode = "MOCK" if self.mock else ("DRY-RUN" if self.dry_run else "PRODUCTION")
        print(f"  Config: {mode}")
        print(f"  Target pairs: {self.config['founding_era_target_pairs']}")
        print(f"  Governance cycles: {self.config['governance_cycles'] or 'indefinite'}")
        self._print_model_allocation_validation()

        # Phase 0: Founding Period
        print(f"\n{'─'*60}")
        print(f"  [Phase 0] Founder Research")
        founder_configs = self._get_all_founder_configs()
        founding = FoundingPeriod(
            founder_configs=founder_configs,
            db=self.db,
            models=self.models,
            config=self.config,
        )
        founder_profiles = founding.run(self.config["phase0_research_cycles"])
        print(f"  Phase 0 complete. {len(founder_profiles)} Founder profiles archived.")

        # Phase 1: Founding Era — Senate pair formation
        print(f"\n{'─'*60}")
        print(f"  [Phase 1] Founding Era — Rival Pair Formation")
        state_manager = self._run_founding_era(founder_profiles)
        print(f"  Phase 1 complete. {len(state_manager.pairs)} rival pairs formed.")

        if not state_manager.pairs:
            print("  WARNING: No pairs formed. Check Founder proposals and supermajority threshold.")
            print("  Cannot proceed to Phase 2 without at least one pair.")
            return

        # Phase 2: Perpetual Governance
        print(f"\n{'─'*60}")
        print(f"  [Phase 2] Autonomous Governance")
        perpetual = PerpetualEngine(
            state_manager=state_manager,
            founder_profiles=founder_profiles,
            constitution_text=self.constitution_text,
            db=self.db,
            models=self.models,
            content_gen=self.content_gen,
            config=self.config,
            output_dir=str(self.output_dir),
            verbose=self.verbose,
        )
        perpetual.run_cycles(self.config["governance_cycles"])

        self._final_report()

    def _print_model_allocation_validation(self):
        print("\n  Model allocation validation")
        for record in self.models.validate_model_allocation():
            status = "OK" if record["valid"] else "INVALID"
            print(
                f"    - {record['task_type']}: tier={record['tier']} "
                f"model={record['model_id']} [{status}]"
            )

    # ─── FOUNDING ERA ────────────────────────────────────────────

    def _run_demo_electrical_founding_era(self) -> StateManager:
        """Phase 1 demo mode: skip Senate votes and seed two empirical electrical rival pairs."""
        state_manager = StateManager(self.db, self.models)
        budget = self.config["initial_token_budget"]

        demo_pairs = [
            {
                "domain": "Lighting_Design",
                "domain_type": "empirical",
                "approach_a": (
                    "Lighting design requires fixture-by-fixture verification against reflected "
                    "ceiling plans, panel schedules, and addenda to prevent costly field errors."
                ),
                "approach_b": (
                    "Lighting design can be efficiently estimated through area-based calculations "
                    "and standard fixture density ratios without individual fixture verification."
                ),
            },
            {
                "domain": "Electrical_Estimation",
                "domain_type": "empirical",
                "approach_a": (
                    "Electrical estimation accuracy depends on cross-referencing multiple drawing "
                    "sheets (plans, schedules, details, addenda) to catch conflicts before bid "
                    "submission."
                ),
                "approach_b": (
                    "Electrical estimation is best served by single-pass automated counting tools "
                    "that prioritize speed over exhaustive cross-referencing."
                ),
            },
        ]

        print("\n  Demo electrical mode enabled: skipping Senate vote and seeding 2 empirical pairs.")
        for cycle, pair_data in enumerate(demo_pairs, start=1):
            domain = pair_data["domain"]
            approach_a = pair_data["approach_a"]
            approach_b = pair_data["approach_b"]

            state_a = State(
                name=self._generate_state_name(domain, "Alpha", cycle - 1),
                domain=domain,
                approach=approach_a,
                budget=budget,
                db=self.db,
                models=self.models,
                cycle_formed=cycle,
            )
            state_b = State(
                name=self._generate_state_name(domain, "Beta", cycle - 1),
                domain=domain,
                approach=approach_b,
                budget=budget,
                db=self.db,
                models=self.models,
                cycle_formed=cycle,
            )

            pair = RivalPair(
                domain=domain,
                state_a=state_a,
                state_b=state_b,
                pair_id=str(uuid.uuid4()),
                cycle_formed=cycle,
                warmup_remaining=0,
                domain_type=pair_data["domain_type"],
            )
            state_manager.add_pair(pair)
            print(f"    DEMO PAIR FORMED: {state_a.name} vs {state_b.name} in '{domain}'")

        return state_manager

    def _run_founding_era(self, founder_profiles: List[FounderProfile]) -> StateManager:
        """
        Phase 1: Founders propose rival pairs (domain + two approaches).
        60% supermajority vote required per pair.
        Once target_pairs formed, Founders retire from governance.
        """
        if self.demo_electrical:
            return self._run_demo_electrical_founding_era()

        state_manager = StateManager(self.db, self.models)
        target = self.config["founding_era_target_pairs"]
        max_cycles = self.config["founding_era_max_cycles"]
        founder_configs = self._get_all_founder_configs()

        formed = 0
        cycle = 0
        formed_domains: List[str] = []
        formed_domain_keys = set()

        print(f"\n  Senate: {len(founder_configs)} Founders. "
              f"Target: {target} pairs. Supermajority: {SENATE_PAIR_SUPERMAJORITY:.0%}")

        while formed < target and cycle < max_cycles:
            cycle += 1
            print(f"\n  Founding cycle {cycle}/{max_cycles} — {formed}/{target} pairs formed")

            # Each cycle: one Founder proposes a candidate pair
            proposer = founder_configs[cycle % len(founder_configs)]
            candidate = self._founder_propose_pair(proposer, formed_domains)
            if not candidate:
                print(f"    {proposer.name} did not propose a valid pair — skipping")
                continue

            domain = candidate["domain"]
            approach_a = candidate["approach_a"]
            approach_b = candidate["approach_b"]

            domain_key = domain.strip().lower()
            if domain_key in formed_domain_keys:
                print(
                    f"    Domain '{domain}' already has a formed rival pair — skipping before vote."
                )
                continue

            print(f"    Proposed by {proposer.name}: [{domain}] {approach_a} vs {approach_b}")

            # Senate vote
            yes_votes = 0
            no_votes = 0
            for fc in founder_configs:
                vote = self._founder_vote_on_pair(fc, domain, approach_a, approach_b)
                if vote:
                    yes_votes += 1
                else:
                    no_votes += 1

            total = yes_votes + no_votes
            ratio = yes_votes / total if total > 0 else 0
            print(f"    Vote: {yes_votes}/{total} ({ratio:.0%}) — "
                  f"need {SENATE_PAIR_SUPERMAJORITY:.0%}")

            if ratio >= SENATE_PAIR_SUPERMAJORITY:
                # Form the pair
                budget = self.config["initial_token_budget"]
                name_a = self._generate_state_name(domain, "Alpha", formed)
                name_b = self._generate_state_name(domain, "Beta", formed)

                state_a = State(
                    name=name_a, domain=domain, approach=approach_a,
                    budget=budget, db=self.db, models=self.models, cycle_formed=cycle,
                )
                state_b = State(
                    name=name_b, domain=domain, approach=approach_b,
                    budget=budget, db=self.db, models=self.models, cycle_formed=cycle,
                )

                pair = RivalPair(
                    domain=domain,
                    state_a=state_a,
                    state_b=state_b,
                    pair_id=str(uuid.uuid4()),
                    cycle_formed=cycle,
                    warmup_remaining=0,
                    domain_type="philosophical",
                )
                state_manager.add_pair(pair)
                formed_domains.append(domain)
                formed_domain_keys.add(domain_key)
                formed += 1
                print(f"    PAIR FORMED: {name_a} vs {name_b} in '{domain}'")
            else:
                print(f"    Pair rejected.")

        if formed == 0:
            print("  No pairs formed — using fallback pair for testing.")
            state_manager = self._fallback_pair(state_manager)

        return state_manager

    def _founder_propose_pair(
        self, fc: AgentConfig, formed_domains: List[str]
    ) -> Optional[dict]:
        """
        Founder proposes a knowledge domain and two competing approaches.
        Returns {"domain": str, "approach_a": str, "approach_b": str} or None.
        """
        response = self.models.complete(
            task_type="founder_panels",
            system_prompt=self._phase1_system_prompt(fc),
            user_prompt=(
                f"You are participating in the Founding Senate of Atlantis.\n"
                f"Propose a knowledge domain and TWO competing intellectual approaches "
                f"for a rival pair of research States.\n\n"
                f"The following domains already have rival pairs and cannot be proposed again: "
                f"[{', '.join(formed_domains) if formed_domains else 'none'}]\n\n"
                f"Format your response EXACTLY as:\n"
                f"DOMAIN: [one word or short phrase]\n"
                f"APPROACH A: [one sentence — this approach to the domain]\n"
                f"APPROACH B: [one sentence — a competing approach to the same domain]\n\n"
                f"Choose a domain where genuine intellectual disagreement is possible."
            ),
            max_tokens=300,
        )

        content = response.content or ""
        domain = self._parse_field(content, "DOMAIN")
        approach_a = self._parse_field(content, "APPROACH A")
        approach_b = self._parse_field(content, "APPROACH B")

        # Fallback for analysis-style responses that provide adjacent fields.
        if not domain:
            concepts = self._parse_field(content, "CONCEPTS")
            if concepts:
                domain = concepts.split(",", 1)[0].strip()
        if not approach_a:
            framework = self._parse_field(content, "FRAMEWORKS")
            if framework:
                approach_a = framework.split(",", 1)[0].strip()
        if not approach_b:
            applications = self._parse_field(content, "APPLICATIONS")
            if applications:
                approach_b = applications.split(",", 1)[0].strip()

        if domain and approach_a and approach_b:
            return {"domain": domain, "approach_a": approach_a, "approach_b": approach_b}

        print(
            f"    [!] Failed to parse pair proposal from {fc.name}. "
            f"Raw response:\n{content}"
        )
        return None

    def _founder_vote_on_pair(
        self, fc: AgentConfig, domain: str, approach_a: str, approach_b: str
    ) -> bool:
        """
        Founder votes YES or NO on a proposed rival pair.
        Returns True for YES.
        """
        response = self.models.complete(
            task_type="founder_vote",
            system_prompt=self._phase1_system_prompt(fc),
            user_prompt=(
                f"Senate vote: Should we form a rival pair in the domain '{domain}'?\n\n"
                f"Approach A: {approach_a}\n"
                f"Approach B: {approach_b}\n\n"
                f"Vote YES to form this pair or NO to reject.\n"
                f"Reply with just YES or NO."
            ),
            max_tokens=10,
        )
        content = re.sub(r"[*_`#\s]+", "", (response.content or "").upper())
        if content.startswith("YES"):
            return True
        if content.startswith("NO"):
            return False
        # Non-binary answer fallback: treat explicit support language as YES.
        if "APPROVE" in content or "SUPPORT" in content:
            return True
        return content.startswith("YES")


    def _phase1_system_prompt(self, fc: AgentConfig) -> str:
        """Compact Phase 1 system prompt with only pair-formation constitutional rules."""
        return (
            f"You are {fc.name}, serving in the Founding Senate of Atlantis.\n"
            f"Mandate: {fc.mandate}\n\n"
            "Constitution extract (pair formation only):\n"
            f"{self.phase1_constitution_extract}"
        )

    @staticmethod
    def _build_phase1_constitution_extract() -> str:
        """Build a short constitutional extract for Phase 1 pair proposal/voting."""
        extract = (
            "Article III, State Formation (Extract)\n"
            "1) Rival pair structure: Each knowledge domain is governed by exactly two rival States, "
            "created together as a pair and pursuing competing approaches. The Senate votes on the pair, "
            "not individual States.\n"
            "2) Supermajority requirement: Pair approval requires at least 60% YES votes from voting Senate members. "
            "If below 60%, the pair is rejected.\n"
            "3) Valid domain requirement: A valid domain is a coherent field of knowledge where sustained "
            "adversarial inquiry is possible and meaningful unresolved questions exist.\n"
            "4) Valid opposing approaches requirement: The two approaches must be distinct, genuinely conflicting "
            "methodologies or epistemic strategies applied to the same domain; they cannot be synonyms, cosmetic "
            "relabels, or different scopes of the same method.\n"
        )
        if len(extract) <= 3000:
            return extract

        # Defensive fallback: if edited longer in future, clamp to hard limit.
        return extract[:3000]

    @staticmethod
    def _parse_field(text: str, field: str) -> str:
        """Extract a field value from formatted LLM response."""
        for line in text.split("\n"):
            cleaned_line = re.sub(r"[*_`]", "", line).strip()
            cleaned_line = re.sub(r"^[#>\-\s]+", "", cleaned_line)
            match = re.match(
                rf"^{re.escape(field)}\s*:\s*(.*)$",
                cleaned_line,
                flags=re.IGNORECASE,
            )
            if match:
                return match.group(1).strip()
        return ""

    @staticmethod
    def _generate_state_name(domain: str, side: str, pair_index: int) -> str:
        """Generate State name from domain and side."""
        normalized = re.sub(r"[^A-Za-z0-9]+", "_", domain).strip("_")
        parts = [p for p in normalized.split("_") if p]

        # Prefer readability over hard truncation: keep whole words when possible.
        domain_parts = []
        char_budget = 20
        consumed = 0
        for part in parts:
            part_len = len(part)
            sep = 1 if domain_parts else 0
            if consumed + sep + part_len > char_budget:
                break
            domain_parts.append(part.title())
            consumed += sep + part_len

        if not domain_parts:
            fallback = (parts[0] if parts else "State")[:char_budget]
            domain_short = fallback.title()
        else:
            domain_short = "_".join(domain_parts)

        return f"{domain_short}_{side}"

    def _fallback_pair(self, state_manager: StateManager) -> StateManager:
        """Emergency fallback: create one pair for testing."""
        budget = self.config["initial_token_budget"]
        state_a = State(
            name="Philosophy_Alpha",
            domain="Philosophy of Knowledge",
            approach="Empiricism: knowledge derives from sensory experience and evidence.",
            budget=budget, db=self.db, models=self.models, cycle_formed=1,
        )
        state_b = State(
            name="Philosophy_Beta",
            domain="Philosophy of Knowledge",
            approach="Rationalism: knowledge derives from reason and innate principles.",
            budget=budget, db=self.db, models=self.models, cycle_formed=1,
        )
        pair = RivalPair(
            domain="Philosophy of Knowledge",
            state_a=state_a,
            state_b=state_b,
            pair_id=str(uuid.uuid4()),
            cycle_formed=1,
            warmup_remaining=0,
            domain_type="philosophical",
        )
        state_manager.add_pair(pair)
        print("  Fallback pair: Philosophy_Alpha vs Philosophy_Beta")
        return state_manager

    # ─── INFRASTRUCTURE ───────────────────────────────────────────

    def _initialize_run_folder(self):
        """Create this run's timestamped output folder under runs/."""
        self.runs_dir = Path("runs")
        self.run_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.run_output_dir = self.runs_dir / self.run_timestamp
        self.run_output_dir.mkdir(parents=True, exist_ok=True)

    def _prepare_output_workspace(self):
        """Reset output/ for a fresh run and recreate expected directories."""
        if self.output_dir.exists() or self.output_dir.is_symlink():
            if self.output_dir.is_symlink() or self.output_dir.is_file():
                self.output_dir.unlink()
            else:
                shutil.rmtree(self.output_dir)
        self._setup_output_dirs()


    def _clear_output_data(self, force_clean: bool):
        """When force-clean is requested, remove prior run artifacts in output/."""
        if not force_clean:
            return

        if not self.output_dir.exists():
            return

        for child in self.output_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

        # Recreate expected output structure after cleanup
        self._setup_output_dirs()
        print("Output data removed: ['output/*']")

    def _check_v1_data(self, force_clean: bool):
        """Detect V1 data. Refuse to start unless --force-clean."""
        v1_found = [p for p in V1_DATA_PATHS if Path(p).exists()]
        if not v1_found:
            return

        if force_clean:
            for p in v1_found:
                path = Path(p)
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            print(f"V1 data removed: {v1_found}")
            print("Starting fresh.\n")
        else:
            raise SystemExit(
                f"\nERROR: V1 data detected — V2 requires a clean start.\n"
                f"Found: {v1_found}\n\n"
                f"Remove manually or run with --force-clean.\n"
                f"WARNING: --force-clean deletes V1 data permanently."
            )

    def _load_constitution(self) -> str:
        """Load CONSTITUTION.md from project root. Required."""
        path = Path("CONSTITUTION.md")
        if not path.exists():
            raise SystemExit(
                "ERROR: CONSTITUTION.md not found in project root.\n"
                "The file must exist before V2 can run."
            )
        text = path.read_text(encoding="utf-8")
        print(f"Constitution loaded: {len(text):,} chars, {text.count(chr(10))} lines.")
        return text

    def _setup_output_dirs(self):
        """Create output directory structure."""
        for d in OUTPUT_DIRS:
            Path(d).mkdir(parents=True, exist_ok=True)
        # Ensure output root exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_all_founder_configs(self) -> List[AgentConfig]:
        """Return all 20 Founder AgentConfigs from agents/base.py."""
        from agents.base import FOUNDER_CONFIGS
        return list(FOUNDER_CONFIGS.values())

    def _save_run_artifacts(self):
        """Persist run metadata and copy this run's outputs to runs/<timestamp>/."""
        stats = self.models.get_stats()
        cost_summary_path = self.output_dir / "cost_summary.json"
        cost_summary_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")

        run_config = {
            "system": SYSTEM_NAME,
            "version": VERSION,
            "mode": "MOCK" if self.mock else ("DRY-RUN" if self.dry_run else "PRODUCTION"),
            "mock": self.mock,
            "dry_run": self.dry_run,
            "config": self.config,
        }
        run_config_path = self.output_dir / "run_config.json"
        run_config_path.write_text(json.dumps(run_config, indent=2), encoding="utf-8")

        artifacts = [
            "archive.md",
            "archive.json",
            "domain_health.json",
            "content",
            "logs",
            "cost_summary.json",
            "run_config.json",
            "executive_summary.md",
        ]
        for artifact in artifacts:
            src = self.output_dir / artifact
            if not src.exists():
                continue
            dst = self.run_output_dir / artifact
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        # Keep output/ as a "latest run" symlink when possible.
        if self.output_dir.exists() or self.output_dir.is_symlink():
            if self.output_dir.is_symlink() or self.output_dir.is_file():
                self.output_dir.unlink()
            else:
                shutil.rmtree(self.output_dir)

        try:
            os.symlink(self.run_output_dir, self.output_dir, target_is_directory=True)
        except OSError:
            shutil.copytree(self.run_output_dir, self.output_dir, dirs_exist_ok=True)

    def _build_executive_summary_input(
        self,
        domain_health: dict,
        total_survivors: int,
        total_cost_usd: float,
    ) -> str:
        """Create compact run summary input for executive-summary generation."""
        domains = sorted(self.db.get_all_domains())
        domain_list = ", ".join(domains) if domains else "None"

        if domain_health:
            avg_survival_rate = (
                sum((d.get("survival_rate", 0.0) or 0.0) for d in domain_health.values())
                / len(domain_health)
            )
        else:
            avg_survival_rate = 0.0

        surviving_positions = []
        for claim in self.db.get_surviving_claims()[:3]:
            position = (claim.get("position") or "").strip()
            if position:
                surviving_positions.append(position)
        if not surviving_positions:
            surviving_positions = ["No surviving claim positions available."]

        cycle_count = self.config.get("governance_cycles") or "indefinite"

        return (
            f"Domains: {domain_list}\n"
            f"Survivor count: {total_survivors}\n"
            f"Survival rate: {avg_survival_rate * 100:.1f}%\n"
            f"Estimated total cost (USD): ${total_cost_usd:.6f}\n"
            f"Number of governance cycles: {cycle_count}\n"
            f"Example surviving claim positions:\n"
            f"- {surviving_positions[0]}\n"
            + (f"- {surviving_positions[1]}\n" if len(surviving_positions) > 1 else "")
            + (f"- {surviving_positions[2]}\n" if len(surviving_positions) > 2 else "")
        )

    def _generate_executive_summary(self, domain_health: dict, total_survivors: int, stats: dict) -> str:
        """Generate a plain-English executive summary via Haiku and persist it."""
        system_prompt = (
            "Write a 3-paragraph executive summary of this adversarial knowledge engine "
            "run for a non-technical executive."
        )
        user_prompt = self._build_executive_summary_input(
            domain_health=domain_health,
            total_survivors=total_survivors,
            total_cost_usd=stats.get("model_router_cost_usd", 0.0),
        )

        response = self.models.complete(
            task_type="executive_summary",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=700,
        )

        summary = response.content.strip()
        if not summary:
            summary = "Executive summary unavailable for this run."

        summary_path_output = self.output_dir / "executive_summary.md"
        summary_path_run = self.run_output_dir / "executive_summary.md"
        summary_path_output.write_text(summary + "\n", encoding="utf-8")
        summary_path_run.write_text(summary + "\n", encoding="utf-8")
        return summary

    def _final_report(self):
        """Print summary and note output file locations."""
        total = self.db.count_surviving_claims()
        active = self.db.get_all_active_states()
        print(f"\n{'='*60}")
        print(f"  ATLANTIS V2 — COMPLETE")
        print(f"{'='*60}")
        print(f"  Surviving claims: {total}")
        print(f"  Active States:    {len(active)}")
        print(f"\n  Output files:")
        print(f"    output/archive.md       — Full human-readable archive")
        print(f"    output/archive.json     — Machine-readable archive")
        print(f"    output/domain_health.json — DMI metrics")
        print(f"    output/logs/            — Per-cycle logs")
        print(f"    output/content/         — Generated content (blog, newsroom, debate, explorer)")

        domain_health = self.db.get_domain_health(domain=None, latest_only=True)
        if domain_health:
            avg_cycles = sum((d.get("cycles_to_first_survival", 0.0) or 0.0) for d in domain_health.values()) / len(domain_health)
            total_survival = sum((d.get("survival_rate", 0.0) or 0.0) for d in domain_health.values()) / len(domain_health)
            rejection_counts = {}
            validation_keys = [
                "missing_gap_addressed",
                "missing_citations",
                "missing_challenge_target",
                "missing_operational_definition",
                "missing_testable_implication",
            ]
            for d in domain_health.values():
                for ruling_type, count in (d.get("failure_distribution", {}) or {}).items():
                    rejection_counts[ruling_type] = rejection_counts.get(ruling_type, 0) + int(count)

            validation_counts = {
                key: int(rejection_counts.get(key, 0) or 0)
                for key in validation_keys
            }
            if any(validation_counts.values()):
                top_reason, top_count = max(validation_counts.items(), key=lambda item: item[1])
                top_reason_summary = f"{top_reason} ({top_count} times)"
            else:
                top_reason_summary = "None (0 times)"

            print("\n  Revision Efficiency:")
            print(f"    Avg cycles to first survival: {avg_cycles:.2f}")
            print("    Validation rejections:")
            print(f"      GAP ADDRESSED missing: {validation_counts['missing_gap_addressed']}")
            print(f"      CITATIONS missing: {validation_counts['missing_citations']}")
            print(f"      CHALLENGE TARGET missing: {validation_counts['missing_challenge_target']}")
            print(f"      OPERATIONAL DEFINITION missing: {validation_counts['missing_operational_definition']}")
            print(f"      TESTABLE IMPLICATION missing: {validation_counts['missing_testable_implication']}")
            print(f"    Top rejection reason: {top_reason_summary}")
            print(f"    Survival rate: {total_survival * 100:.1f}%")
        self.models.print_cost_summary()
        stats = self.models.get_stats()
        print(f"  Total LLM calls: {stats['total_calls']}")
        if self.config["governance_cycles"]:
            per_cycle = stats["model_router_cost_usd"] / self.config["governance_cycles"]
            print(f"  Estimated cost per governance cycle: ${per_cycle:.6f}")

        executive_summary = self._generate_executive_summary(
            domain_health=domain_health,
            total_survivors=total,
            stats=stats,
        )
        print("\n  Executive Summary:")
        print("  " + "-" * 48)
        for line in executive_summary.splitlines():
            print(f"  {line}")

        self._save_run_artifacts()
        try:
            subprocess.run([sys.executable, "generate_site_data.py"], check=True)
            print("  ✓ Site data generated → lib/data.ts")
        except (subprocess.CalledProcessError, OSError) as err:
            print(f"  WARNING: Site data generation failed (optional): {err}")
        print(f"  Run saved to: {self.run_output_dir.as_posix()}/")
        print(f"\n  Done.\n")


# ═══════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Atlantis V2 — Adversarial Knowledge Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m atlantis --mock              # Quick test (3 pairs, 5 cycles)\n"
            "  python -m atlantis                     # Full production run\n"
            "  python -m atlantis --force-clean       # Remove V1 data first\n"
            "  python -m atlantis --dry-run           # Print prompts, skip API calls\n"
            "  python -m atlantis --demo-electrical   # Electrical-domain empirical demo\n"
        ),
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Use MOCK_CONFIG (fewer pairs, fewer cycles — good for testing)"
    )
    parser.add_argument(
        "--force-clean", action="store_true",
        help="Remove detected V1 data directories and start fresh"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run full pipeline and print prompts/model settings without live API calls"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print full raw claim/challenge/rebuttal text in cycle logs"
    )
    parser.add_argument(
        "--demo-electrical", action="store_true",
        help="Use electrical-domain demo pairs (empirical) and skip Senate voting in Phase 1"
    )
    args = parser.parse_args(argv)

    if args.mock:
        config = MOCK_CONFIG
    elif args.demo_electrical:
        config = DEMO_ELECTRICAL_CONFIG
    else:
        config = PRODUCTION_CONFIG

    engine = AtlantisEngine(
        config=config,
        mock=args.mock,
        dry_run=args.dry_run,
        force_clean=args.force_clean,
        verbose=args.verbose,
        demo_electrical=args.demo_electrical,
    )
    engine.run()
