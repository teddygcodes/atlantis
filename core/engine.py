"""
Atlantis Core Engine
=====================
Main orchestration engine. Runs through all phases:
- Phase 0: Founding Period (20 Founders research)
- Phase 1: Constitutional Convention (2v2 adversarial debates, 3 rounds)
- Phase 2: Government Deployment (agents from Constitution)
- Phase 3: Autonomous Governance (perpetual cycle engine)

Usage:
    python -m atlantis
    python -m atlantis my_data_dir
    python -m atlantis --local
"""

import os
import sys
import json
import uuid
from datetime import datetime, timezone

from content.logger import AtlantisLogger, init_logger
from content.generator import ContentGenerator
from core.llm import LLMProvider, get_llm
from core.persistence import AtlantisDB, get_db
from founders.convention import FoundingPeriod, ConstitutionalConvention
from governance.deployer import GovernmentDeployer
from governance.perpetual import PerpetualEngine
from config.settings import SYSTEM_NAME, VERSION, HARD_CONSTRAINTS, API_CONFIG


class AtlantisEngine:
    """The main Atlantis engine. Orchestrates everything."""

    def __init__(self, data_dir: str = "atlantis_data", api_key: str = None,
                 mode: str = "auto", mock_config: dict = None):
        self.data_dir = data_dir
        self.mock_config = mock_config or {}
        os.makedirs(data_dir, exist_ok=True)

        # Initialize core systems
        self.logger = init_logger(log_dir=os.path.join(data_dir, "logs"))
        self.llm = get_llm(api_key=api_key, mode=mode)
        self.db = get_db(db_path=os.path.join(data_dir, "atlantis.db"))
        self.logger.set_db(self.db)

        # Content generator — produces TikTok scripts and blog posts immediately
        self.content_gen = ContentGenerator(
            output_dir=os.path.join(data_dir, "content"),
            llm=self.llm
        )

        # Track phase
        self.current_phase = self.db.get_state("current_phase", "not_started")

        print(f"\n{'=' * 60}")
        print(f"  {SYSTEM_NAME} v{VERSION}")
        print(f"  The Lost Civilization, Rebuilt")
        print(f"  LLM Mode: {self.llm.mode}")
        print(f"  Rate Limiting: {API_CONFIG['rate_limit_seconds']}s between calls")
        print(f"  Data Dir: {data_dir}")
        print(f"  Phase: {self.current_phase}")
        print(f"{'=' * 60}")

    def run(self, governance_cycles: int = 10):
        """Run Atlantis from current phase forward."""

        # Check for phase cache first - skip to Founding Era if it exists
        if self.current_phase == "not_started" and self._load_phase_cache():
            print(f"\n  ✓ Loaded from cache - skipping to Founding Era")
            self.current_phase = "ready_for_founding_era"
            self.db.set_state("current_phase", "ready_for_founding_era")

        # Phase 0: Founding Period
        if self.current_phase in ["not_started", "founding_period"]:
            self._run_founding_period()

        # Phase 1: Constitutional Convention
        if self.current_phase in ["founding_complete", "convention"]:
            self._run_convention()
            print("\n>>> DEBUG: About to deposit Founder knowledge to Archive...")
            # CRITICAL: Deposit Founder knowledge to Archive BEFORE Founding Era starts
            self._deposit_founder_knowledge_to_archive()
            print("\n>>> DEBUG: About to save phase cache...")
            # Save cache after Phase 0+1 complete
            self._save_phase_cache()
            print("\n>>> DEBUG: Phase 1 complete, cache saved")

        # Phase 2.5: Founding Era — Founders + Government form 20 States
        if self.current_phase in ["ready_for_founding_era", "government_deployed"] and hasattr(self, "government"):
            self._run_founding_era()

        # Founders retire after Founding Era (after 20 States formed)
        if self.current_phase == "founding_era_complete":
            self._retire_founders()

        # Phase 3: Autonomous Governance — Perpetual Engine
        if self.current_phase == "founders_retired" and hasattr(self, "government"):
            self._run_perpetual_engine(governance_cycles)

        # Generate content from all logged events
        self._generate_content()

        # Print final report
        self._print_report()

    def _get_cache_path(self):
        """Get path to phase cache file."""
        return os.path.join(self.data_dir, "phase_cache.json")

    def _save_phase_cache(self):
        """Save Phase 0+1 state to cache (Founder knowledge + Constitution + Blueprint)."""
        cache_path = self._get_cache_path()

        print(f"\n{'=' * 60}")
        print(f"  SAVING PHASE CACHE")
        print(f"{'=' * 60}")

        # Serialize Founder knowledge
        founders_data = []
        for founder in self.founders:
            founder_data = {
                "id": founder.id,
                "name": founder.name,
                "knowledge": {
                    domain: ka.to_dict()
                    for domain, ka in founder.knowledge.items()
                },
                "total_tokens_used": founder.total_tokens_used
            }
            founders_data.append(founder_data)

        # Serialize Blueprint
        blueprint_data = {
            "branches": [
                {
                    "name": b.name,
                    "branch_type": b.branch_type,
                    "purpose": b.purpose,
                    "seats": b.seats,
                    "powers": b.powers,
                    "constraints": b.constraints,
                    "voting_rules": b.voting_rules
                }
                for b in self.blueprint.branches
            ],
            "safeguards": getattr(self.blueprint, 'safeguards', getattr(self.blueprint, 'non_amendable_clauses', [])),
            "cycle_sequence": self.blueprint.cycle_sequence,
            "amendment_process": getattr(self.blueprint, 'amendment_process', getattr(self.blueprint, 'amendment_rules', {}))
        }

        # Get Constitution text from database
        constitution_text = self.db.get_state("constitution_text", "")

        cache_data = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "phase": "ready_for_founding_era",
            "founders": founders_data,
            "blueprint": blueprint_data,
            "constitution_text": constitution_text,
            "research_cycles": self.mock_config.get("research_cycles", 10)
        }

        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)

        print(f"  ✓ Saved phase cache: {cache_path}")
        print(f"    - {len(founders_data)} Founders with knowledge")
        print(f"    - {len(blueprint_data['branches'])} government branches")
        print(f"    - Constitution: {len(constitution_text)} characters")
        print(f"{'=' * 60}")

    def _load_phase_cache(self):
        """Load Phase 0+1 state from cache if it exists.

        Returns:
            bool: True if cache loaded successfully, False otherwise
        """
        cache_path = self._get_cache_path()

        if not os.path.exists(cache_path):
            return False

        try:
            print(f"\n{'=' * 60}")
            print(f"  LOADING PHASE CACHE")
            print(f"{'=' * 60}")

            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            print(f"  Found cache from {cache_data.get('created_at', 'unknown date')}")

            # Restore Founders
            from agents.base import get_all_founders, KnowledgeArea
            self.founders = get_all_founders()

            for founder in self.founders:
                # Find this founder's data in cache
                founder_data = next(
                    (f for f in cache_data["founders"] if f["id"] == founder.id),
                    None
                )
                if not founder_data:
                    print(f"    ⚠ Cache missing data for {founder.name}")
                    return False

                # Restore knowledge areas
                for domain, ka_dict in founder_data["knowledge"].items():
                    if domain not in founder.knowledge:
                        founder.knowledge[domain] = KnowledgeArea(domain=domain)

                    ka = founder.knowledge[domain]
                    ka.tier = ka_dict["tier"]
                    ka.key_concepts = ka_dict["key_concepts"]
                    ka.frameworks = ka_dict["frameworks"]
                    ka.applications = ka_dict["applications"]
                    ka.connections = ka_dict["connections"]
                    ka.entry_count = ka_dict["entry_count"]

                # Restore token usage
                founder.total_tokens_used = founder_data["total_tokens_used"]

                # Save to database
                self.db.save_agent(founder)

            # Restore Blueprint
            from founders.convention import GovernmentBlueprint, BranchBlueprint
            self.blueprint = GovernmentBlueprint()

            blueprint_data = cache_data["blueprint"]
            for branch_dict in blueprint_data["branches"]:
                branch = BranchBlueprint(
                    name=branch_dict["name"],
                    branch_type=branch_dict["branch_type"],
                    purpose=branch_dict.get("purpose", ""),
                    seats=branch_dict.get("seats", []),
                    powers=branch_dict.get("powers", []),
                    constraints=branch_dict.get("constraints", []),
                    voting_rules=branch_dict.get("voting_rules", {})
                )
                self.blueprint.branches.append(branch)

            # Handle different attribute names between Blueprint versions
            if "safeguards" in blueprint_data:
                self.blueprint.non_amendable_clauses = blueprint_data["safeguards"]
            self.blueprint.cycle_sequence = blueprint_data.get("cycle_sequence", [])
            if "amendment_process" in blueprint_data:
                self.blueprint.amendment_rules = blueprint_data["amendment_process"]

            # Restore Constitution text
            self.constitution_text = cache_data.get("constitution_text", "")
            if self.constitution_text:
                self.db.set_state("constitution_text", self.constitution_text)

            # Deploy government from blueprint
            from governance.deployer import GovernmentDeployer
            deployer = GovernmentDeployer(
                blueprint=self.blueprint,
                logger=self.logger,
                llm=self.llm,
                db=self.db
            )
            self.government = deployer.deploy()

            # Deposit Founder knowledge to Archive
            total_deposited = 0
            for founder in self.founders:
                for domain, knowledge_area in founder.knowledge.items():
                    if knowledge_area.key_concepts or knowledge_area.frameworks or knowledge_area.applications:
                        self.db.deposit_to_archive(
                            source_type="founder",
                            source_id=founder.id,
                            knowledge={
                                "domain": domain,
                                "tier": knowledge_area.tier,
                                "concepts": knowledge_area.key_concepts,
                                "frameworks": knowledge_area.frameworks,
                                "applications": knowledge_area.applications,
                                "synthesis": f"Founder {founder.name} research in {domain}",
                                "evidence": ", ".join(knowledge_area.key_concepts[:5]) if knowledge_area.key_concepts else "",
                                "cycle_created": 0
                            }
                        )
                        total_deposited += 1

            archive_summary = self.db.get_archive_summary()

            print(f"  ✓ Restored {len(self.founders)} Founders with knowledge")
            print(f"  ✓ Restored {len(self.blueprint.branches)} government branches")
            print(f"  ✓ Deployed government")
            print(f"  ✓ Deposited {total_deposited} knowledge entries to Archive")
            print(f"  Federal Archive contains {archive_summary['total_entries']} entries")
            print(f"{'=' * 60}")

            return True

        except Exception as e:
            print(f"    ⚠ Failed to load cache: {e}")
            print(f"    Falling back to full Phase 0+1")
            return False

    def _get_phase2_cache_path(self):
        """Get path to Phase 2 (Founding Era) cache file."""
        return os.path.join(self.data_dir, "phase2_cache.json")

    def _save_phase2_cache(self, state_manager):
        """Save Phase 2 state (Founding Era States) to cache."""
        from governance.states import StateConstitution, KnowledgeEntry

        cache_path = self._get_phase2_cache_path()

        print(f"\n{'=' * 60}")
        print(f"  SAVING PHASE 2 CACHE (Founding Era States)")
        print(f"{'=' * 60}")

        # Serialize all States
        states_data = {}
        for state_id, state in state_manager.states.items():
            state_data = {
                "state_id": state.state_id,
                "name": state.name,
                "domain": state.domain,
                "formed_cycle": state.formed_cycle,
                "tier": state.tier,
                "constitution": state.constitution.to_dict(),
                "knowledge_entries": [entry.to_dict() for entry in state.knowledge_entries],
                # Agent IDs (will reconstruct from DB)
                "governor_id": state.governor.id if state.governor else None,
                "researcher_id": state.researcher.id if state.researcher else None,
                "critic_id": state.critic.id if state.critic else None,
                "senator_id": state.senator.id if state.senator else None,
                # Cities
                "cities": [
                    {
                        "city_id": city.city_id if hasattr(city, 'city_id') else str(uuid.uuid4()),
                        "name": city.name,
                        "sub_domain": getattr(city, 'sub_domain', ''),
                        "tier": city.tier,
                        "knowledge_entries": len(getattr(city, 'knowledge_entries', [])),
                    }
                    for city in getattr(state, 'cities', [])
                ]
            }
            states_data[state_id] = state_data

        cache_data = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "phase": "founding_era_complete",
            "states": states_data
        }

        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)

        print(f"  ✓ Saved Phase 2 cache: {cache_path}")
        print(f"    - {len(states_data)} States saved")
        for state_id, state_data in states_data.items():
            print(f"      • {state_data['name']} (Tier {state_data['tier']}, {len(state_data['knowledge_entries'])} entries)")
        print(f"{'=' * 60}")

    def _load_phase2_cache(self, state_manager):
        """Load Phase 2 state (Founding Era States) from cache if it exists.

        Args:
            state_manager: StateManager instance to populate

        Returns:
            bool: True if cache loaded successfully, False otherwise
        """
        from governance.states import StateConstitution, KnowledgeEntry, State
        from agents.base import BaseAgent

        cache_path = self._get_phase2_cache_path()

        if not os.path.exists(cache_path):
            return False

        try:
            print(f"\n{'=' * 60}")
            print(f"  LOADING PHASE 2 CACHE (Founding Era States)")
            print(f"{'=' * 60}")

            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            print(f"  Found cache from {cache_data.get('created_at', 'unknown date')}")

            # Restore each State
            for state_id, state_data in cache_data["states"].items():
                # Reconstruct StateConstitution
                const_dict = state_data["constitution"]
                constitution = StateConstitution(
                    state_name=const_dict["state_name"],
                    domain=const_dict["domain"],
                    knowledge_areas=const_dict["knowledge_areas"],
                    governance_principles=const_dict["governance_principles"],
                    research_methodology=const_dict["research_methodology"],
                    federal_compliance_check=const_dict["federal_compliance_check"],
                    ratified_at_cycle=const_dict["ratified_at_cycle"],
                    version=const_dict.get("version", 1)
                )

                # Reconstruct State
                state = State(
                    state_id=state_data["state_id"],
                    name=state_data["name"],
                    domain=state_data["domain"],
                    constitution=constitution,
                    formed_cycle=state_data["formed_cycle"]
                )
                state.tier = state_data["tier"]

                # Restore KnowledgeEntries
                for entry_dict in state_data["knowledge_entries"]:
                    entry = KnowledgeEntry(
                        entry_id=entry_dict["entry_id"],
                        entity_id=entry_dict["entity_id"],
                        entity_type=entry_dict["entity_type"],
                        domain=entry_dict["domain"],
                        tier=entry_dict["tier"],
                        concepts=entry_dict["concepts"],
                        frameworks=entry_dict["frameworks"],
                        applications=entry_dict["applications"],
                        synthesis=entry_dict["synthesis"],
                        evidence=entry_dict["evidence"],
                        challenged_by=entry_dict.get("challenged_by", ""),
                        defense=entry_dict.get("defense", ""),
                        cycle_created=entry_dict.get("cycle_created", 0),
                        tokens_used=entry_dict.get("tokens_used", 0)
                    )
                    state.knowledge_entries.append(entry)

                # Restore agents from database by ID
                if state_data.get("governor_id"):
                    agent_state = self.db.get_agent_state(state_data["governor_id"])
                    if agent_state:
                        state.governor = BaseAgent.from_dict(agent_state)

                if state_data.get("researcher_id"):
                    agent_state = self.db.get_agent_state(state_data["researcher_id"])
                    if agent_state:
                        state.researcher = BaseAgent.from_dict(agent_state)

                if state_data.get("critic_id"):
                    agent_state = self.db.get_agent_state(state_data["critic_id"])
                    if agent_state:
                        state.critic = BaseAgent.from_dict(agent_state)

                if state_data.get("senator_id"):
                    agent_state = self.db.get_agent_state(state_data["senator_id"])
                    if agent_state:
                        state.senator = BaseAgent.from_dict(agent_state)

                # Add to StateManager
                state_manager.states[state_id] = state

            print(f"  ✓ Restored {len(state_manager.states)} States from cache")
            for state_id, state in state_manager.states.items():
                print(f"      • {state.name} (Tier {state.tier}, {len(state.knowledge_entries)} knowledge entries)")
            print(f"{'=' * 60}")

            return True

        except Exception as e:
            print(f"    ⚠ Failed to load Phase 2 cache: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _run_founding_period(self):
        self.db.set_state("current_phase", "founding_period")
        self.current_phase = "founding_period"

        research_cycles = self.mock_config.get("research_cycles", None)
        period = FoundingPeriod(
            logger=self.logger, llm=self.llm, db=self.db,
            research_cycles=research_cycles
        )
        self.founders = period.run()

        self.db.set_state("current_phase", "founding_complete")
        self.current_phase = "founding_complete"

    def _run_convention(self):
        """Phase 1: Jefferson writes draft, deploy immediately (NO amendments yet)."""
        print(f"\n{'=' * 60}")
        print(f"  PHASE 1: JEFFERSON DRAFT → IMMEDIATE DEPLOYMENT")
        print(f"  The Constitution will evolve during Founding Era")
        print(f"{'=' * 60}")

        self.db.set_state("current_phase", "jefferson_draft")
        self.current_phase = "jefferson_draft"

        if not hasattr(self, "founders"):
            from agents.base import get_all_founders
            self.founders = get_all_founders()

        # Jefferson writes draft (reuse existing Convention method)
        convention = ConstitutionalConvention(
            founders=self.founders, logger=self.logger,
            llm=self.llm, db=self.db
        )

        # Call ONLY Jefferson draft step (not full Convention.run())
        convention._step_0_jefferson_draft()
        self.blueprint = convention.blueprint
        self.convention = convention

        # Save Constitution text to database
        if hasattr(convention, 'draft_text'):
            self.constitution_text = convention.draft_text
            self.db.set_state("constitution_text", self.constitution_text)
            # Save v1.0 — Jefferson's original (immutable)
            import json
            self.db.save_constitution_version(
                version=1,
                constitution_text=json.dumps(self.blueprint.to_dict()),
                ratified_by=["Jefferson"]
            )
            self.constitution_version = 1
            print(f"  ✓ Constitution v1.0 saved (immutable)")
        else:
            self.constitution_text = ""

        # Validate blueprint
        if len(self.blueprint.branches) < 2:
            raise ValueError(f"Invalid blueprint: only {len(self.blueprint.branches)} branches. Minimum 2 required.")

        # Log Jefferson's draft as historic event
        entry = self.logger._create_entry(
            level="historic",
            category="constitution_drafted",
            title="JEFFERSON WRITES THE CONSTITUTION",
            summary=(
                f"Thomas Jefferson has written the founding Constitution of Atlantis. "
                f"{len(self.blueprint.branches)} branches of government defined. "
                f"{len(getattr(self.blueprint, 'non_amendable_clauses', []))} non-amendable clauses locked. "
                f"Cycle sequence: {' → '.join(self.blueprint.cycle_sequence)}. "
                f"The government deploys immediately. The Founding Era begins."
            ),
            agents=["Jefferson"],
        )
        self.logger.log(entry)
        self._generate_content_for_event(entry)

        # Deploy immediately (no amendments yet)
        print(f"\n  Deploying government from Jefferson's draft...")
        from governance.deployer import GovernmentDeployer
        deployer = GovernmentDeployer(
            blueprint=self.blueprint,
            logger=self.logger,
            llm=self.llm,
            db=self.db
        )
        self.government = deployer.deploy()
        print(f"\n{self.government.summary()}")

        self.db.set_state("current_phase", "ready_for_founding_era")
        self.current_phase = "ready_for_founding_era"

        print(f"\n  Government is LIVE. Constitution will evolve during Founding Era.")

    def _deposit_founder_knowledge_to_archive(self):
        """Deposit all Founder knowledge into Federal Archive BEFORE Founding Era starts."""
        print(f"\n{'=' * 60}")
        print(f"  DEPOSITING FOUNDER KNOWLEDGE TO FEDERAL ARCHIVE")
        print(f"  This makes knowledge available to voters during Founding Era")
        print(f"{'=' * 60}")

        # Get all Founders - MUST load from database to get their knowledge!
        from agents.base import KnowledgeArea

        if not hasattr(self, "founders") or not self.founders:
            from agents.base import get_all_founders
            self.founders = get_all_founders()

        # CRITICAL FIX: ALWAYS load knowledge from database for each Founder
        # Even if self.founders exists, their knowledge dicts might be empty after cache load
        for founder in self.founders:
            agent_state = self.db.get_agent_state(founder.id)
            if agent_state and agent_state.get("knowledge"):
                # Restore knowledge from database
                for domain, ka_dict in agent_state["knowledge"].items():
                    if domain not in founder.knowledge:
                        founder.knowledge[domain] = KnowledgeArea(domain=domain)

                    ka = founder.knowledge[domain]
                    ka.tier = ka_dict["tier"]
                    ka.key_concepts = ka_dict["key_concepts"]
                    ka.frameworks = ka_dict["frameworks"]
                    ka.applications = ka_dict["applications"]
                    ka.connections = ka_dict["connections"]
                    ka.entry_count = ka_dict["entry_count"]

        # DEBUG: Print what knowledge each Founder has before depositing
        print(f"\n>>> DEBUG: Checking Founder knowledge before deposit...")
        for founder in self.founders:
            print(f"  DEBUG: {founder.name} has {len(founder.knowledge)} knowledge domains")
            for domain, ka in founder.knowledge.items():
                print(f"    {domain}: {len(ka.key_concepts)} concepts, {len(ka.frameworks)} frameworks, tier {ka.tier}")

        # Deposit each Founder's knowledge into Federal Archive
        total_deposited = 0
        for founder in self.founders:
            # Get all knowledge entries for this Founder
            for domain, knowledge_area in founder.knowledge.items():
                if knowledge_area.key_concepts or knowledge_area.frameworks or knowledge_area.applications:
                    self.db.deposit_to_archive(
                        source_type="founder",
                        source_id=founder.id,
                        knowledge={
                            "domain": domain,
                            "tier": knowledge_area.tier,
                            "concepts": knowledge_area.key_concepts,
                            "frameworks": knowledge_area.frameworks,
                            "applications": knowledge_area.applications,
                            "synthesis": f"Founder {founder.name} research in {domain}",
                            "evidence": ", ".join(knowledge_area.key_concepts[:5]) if knowledge_area.key_concepts else "",
                            "cycle_created": 0  # From founding period
                        }
                    )
                    total_deposited += 1

        archive_summary = self.db.get_archive_summary()
        print(f"\n  ✓ Deposited {total_deposited} knowledge entries from {len(self.founders)} Founders")
        print(f"  Federal Archive now contains {archive_summary['total_entries']} entries")
        print(f"  Covering {archive_summary['unique_domains']} domains")
        print(f"  Max tier: {archive_summary['max_tier']}")
        print(f"{'=' * 60}")

    def _retire_founders(self):
        """Retire Founders after Founding Era completes."""
        print(f"\n{'=' * 60}")
        print(f"  FOUNDER RETIREMENT")
        print(f"  The Founders' work is complete.")
        print(f"{'=' * 60}")

        # Get all Founders
        if not hasattr(self, "founders"):
            from agents.base import get_all_founders
            self.founders = get_all_founders()

        # Retire Founders (call existing retirement logic)
        if hasattr(self, "convention") and self.convention:
            self.convention.retire_founders()
        else:
            convention = ConstitutionalConvention(
                founders=self.founders, logger=self.logger,
                llm=self.llm, db=self.db
            )
            convention.retire_founders()

        print(f"\n  Founders have retired. Their legacy lives on in the Archive.")
        print(f"{'=' * 60}")

        self.db.set_state("current_phase", "founders_retired")
        self.current_phase = "founders_retired"

    def _run_perpetual_engine(self, num_cycles: int = 10):
        """Phase 3: Run the Perpetual Governance Engine."""
        from governance.states import StateManager

        # Get constitution from database
        constitution = self.db.get_constitution("federal") or {}

        # Try to load StateManager from Phase 2 cache (disk persistence)
        state_manager = StateManager(llm=self.llm, logger=self.logger, db=self.db)
        cache_loaded = self._load_phase2_cache(state_manager)

        if cache_loaded:
            print(f"  ✓ Loaded {len(state_manager.states)} States from Phase 2 cache (disk)")
        elif hasattr(self, 'state_manager') and self.state_manager:
            # Fallback: Use in-memory StateManager from same session
            state_manager = self.state_manager
            print(f"  ✓ Loaded StateManager with {len(state_manager.states)} existing States (memory)")
        else:
            # No cache, no memory - fresh start
            print(f"  ⚠ No States found (no cache, no memory)")
            print(f"    Perpetual Engine will wait for State Formation Bills")

        # Initialize and run the Perpetual Engine
        engine = PerpetualEngine(
            government=self.government,
            structure=self.blueprint,
            constitution=constitution,
            logger=self.logger,
            content_gen=self.content_gen,
            llm=self.llm,
            db=self.db,
            state_manager=state_manager
        )

        engine.run_cycles(num_cycles)

        self.db.set_state("current_phase", "perpetual_governance")
        self.current_phase = "perpetual_governance"

    def _run_founder_retirement(self):
        """Retire Founders and deposit their knowledge into Federal Archive."""
        print(f"\n{'=' * 60}")
        print(f"  FOUNDER RETIREMENT")
        print(f"  Depositing Founder knowledge into Federal Archive...")
        print(f"{'=' * 60}")

        # Get all Founders
        if not hasattr(self, "founders"):
            from agents.base import get_all_founders
            self.founders = get_all_founders()

        # Deposit each Founder's knowledge into Federal Archive
        total_deposited = 0
        for founder in self.founders:
            # Get all knowledge entries for this Founder
            for domain, knowledge_area in founder.knowledge.items():
                if knowledge_area.key_concepts or knowledge_area.frameworks or knowledge_area.applications:
                    self.db.deposit_to_archive(
                        source_type="founder",
                        source_id=founder.id,
                        knowledge={
                            "domain": domain,
                            "tier": knowledge_area.tier,
                            "concepts": knowledge_area.key_concepts,
                            "frameworks": knowledge_area.frameworks,
                            "applications": knowledge_area.applications,
                            "synthesis": f"Founder {founder.name} research in {domain}",
                            "evidence": ", ".join(knowledge_area.key_concepts[:5]) if knowledge_area.key_concepts else "",
                            "cycle_created": 0  # From founding period
                        }
                    )
                    total_deposited += 1

        print(f"  {total_deposited} knowledge entries deposited from {len(self.founders)} Founders")

        # Retire Founders (call existing retirement logic)
        if hasattr(self, "convention") and self.convention:
            self.convention.retire_founders()
        else:
            convention = ConstitutionalConvention(
                founders=self.founders, logger=self.logger,
                llm=self.llm, db=self.db
            )
            convention.retire_founders()

        archive_summary = self.db.get_archive_summary()
        print(f"  Federal Archive now contains {archive_summary['total_entries']} entries")
        print(f"  Covering {archive_summary['unique_domains']} domains")
        print(f"  Max tier: {archive_summary['max_tier']}")
        print(f"\n  Founders have retired. Their legacy lives on.")
        print(f"{'=' * 60}")

        self.db.set_state("current_phase", "founders_retired")
        self.current_phase = "founders_retired"

    def _parse_and_deploy_government(self):
        """Phase 2: Deploy government directly from the Founder-built blueprint."""
        if not hasattr(self, "blueprint") or self.blueprint is None:
            print("\n  ERROR: No blueprint from Convention. Cannot deploy.")
            return

        deployer = GovernmentDeployer(
            blueprint=self.blueprint,
            logger=self.logger,
            llm=self.llm,
            db=self.db
        )
        self.government = deployer.deploy()
        print(f"\n{self.government.summary()}")

        self.db.set_state("current_phase", "government_deployed")
        self.current_phase = "government_deployed"

    def _run_founding_era(self):
        """Phase 2: Founding Era — Founders govern + research + amend until 20 States."""
        from governance.states import StateManager
        from founders.convention import propose_collaborative_amendment
        from config.settings import HARD_CONSTRAINTS
    
        target_states = self.mock_config.get("founding_era_target_states",
                                             HARD_CONSTRAINTS["founding_era_target_states"])
        max_cycles = 50  # Prevent infinite loops
    
        print(f"\n{'=' * 60}")
        print(f"  PHASE 2: FOUNDING ERA")
        print(f"  Founders govern + research + amend until {target_states} States formed")
        print(f"  Max {max_cycles} cycles")
        print(f"{'=' * 60}")
    
        # Initialize
        state_manager = StateManager(llm=self.llm, logger=self.logger, db=self.db)
        constitution = self.db.get_constitution("federal")
    
        if not hasattr(self, "founders"):
            from agents.base import get_all_founders
            self.founders = get_all_founders()
    
        # Founders ARE the Senate initially (no permanent senators during Founding Era)
        all_senators = self.founders[:]  # 20 Founders
    
        print(f"  Senate: {len(all_senators)} Founders (State Senators will join as States form)")
    
        founding_era_cycle = 0
        states_formed = 0
        amendments_passed = 0
        amendments_failed = 0
    
        while states_formed < target_states and founding_era_cycle < max_cycles:
            founding_era_cycle += 1
            print(f"\n{'=' * 70}")
            print(f"  FOUNDING ERA CYCLE {founding_era_cycle}")
            print(f"  States: {states_formed}/{target_states} | Amendments: {amendments_passed} passed, {amendments_failed} failed")
            print(f"{'=' * 70}")
    
            # ─────────────────────────────────────────────────────────
            # STEP 1: COLLABORATIVE AMENDMENT (One per cycle)
            # ─────────────────────────────────────────────────────────
            print(f"\n  {'─' * 40}")
            print(f"  STEP 1: COLLABORATIVE AMENDMENT")
            print(f"  {'─' * 40}")

            # Amendment cooling period — prevent amendment stacking
            min_gap = 3  # Minimum cycles between passed amendments
            cycles_since_last = founding_era_cycle - getattr(self, '_last_amendment_passed_cycle', -999)
            if cycles_since_last < min_gap:
                print(f"  Amendment cooling period: {cycles_since_last}/{min_gap} cycles since last passed")
                amendment_result = {"status": "cooling_period"}
            else:
                amendment_result = propose_collaborative_amendment(
                cycle=founding_era_cycle,
                blueprint=self.blueprint,
                founders=self.founders,
                llm=self.llm,
                logger=self.logger
            )
    
            if amendment_result["status"] == "passed":
                amendments_passed += 1
                self._last_amendment_passed_cycle = founding_era_cycle  # Track for cooling period
                print(f"  ✓ Amendment passed: {amendment_result['text'][:80]}...")
                # Save new constitution version
                self.constitution_version = getattr(self, 'constitution_version', 1) + 1
                self.db.save_constitution_version(
                    version=self.constitution_version,
                    constitution_text=json.dumps(self.blueprint.to_dict()),
                    amendments=[amendment_result.get("text", "")],
                    ratified_by=amendment_result.get("votes", {}).get("yes_voters", [])
                )
                print(f"  ✓ Constitution v{self.constitution_version} saved")
            elif amendment_result["status"] == "failed":
                amendments_failed += 1
                print(f"  ✗ Amendment failed (vote: {amendment_result['votes']['yes']}/20)")
            else:  # "no_amendment_needed"
                print(f"  → No amendment needed this cycle")
    
            # ─────────────────────────────────────────────────────────
            # ─────────────────────────────────────────────────────────
            # STEP 2: STATE FORMATION (Collaborative)
            # ─────────────────────────────────────────────────────────
            print(f"\n  {'─' * 40}")
            print(f"  STEP 2: STATE FORMATION")
            print(f"  {'─' * 40}")

            import random

            # Query Archive for context
            archive_summary = self.db.get_archive_summary()
            existing_domains = [s.domain for s in state_manager.states.values()]
            print(f"    Archive: {archive_summary['total_entries']} entries, {archive_summary['unique_domains']} domains")
            print(f"    Existing States: {', '.join(existing_domains) if existing_domains else 'None'}")

            # 1. COLLABORATIVE PROPOSAL — Sample 5 Founders for State ideas
            sample_founders = random.sample(self.founders, min(5, len(self.founders)))
            suggestions = []

            for founder in sample_founders:
                response = self.llm.complete(
                    system_prompt=founder.get_system_prompt(),
                    user_prompt=(
                        f"FOUNDING ERA — Cycle {founding_era_cycle}\n\n"
                        f"YOUR MISSION: The Founders must form {target_states} States before retiring. "
                        f"We have {states_formed} so far. We need {target_states - states_formed} more.\n\n"
                        f"Existing States: {', '.join(existing_domains) if existing_domains else 'None yet'}\n"
                        f"Archive: {archive_summary['total_entries']} entries across {archive_summary['unique_domains']} domains\n\n"
                        f"States should cover KNOWLEDGE DOMAINS like science, philosophy, economics, mathematics, "
                        f"history, technology, medicine, arts — NOT governance or constitutional topics. "
                        f"The government already exists. States produce KNOWLEDGE.\n\n"
                        f"What knowledge domain NEEDS a State that doesn't exist yet? "
                        f"Suggest ONE domain and explain why it's essential. One sentence."
                    ),
                    max_tokens=150,
                    temperature=0.7
                )
                suggestion = (response.content or "").strip()
                if suggestion:
                    suggestions.append({"founder": founder.name, "suggestion": suggestion})

            # 2. SYNTHESIZE into one State proposal
            suggestions_text = "\n".join([f"- {s['founder']}: {s['suggestion']}" for s in suggestions])

            synthesis_response = self.llm.complete(
                system_prompt="You synthesize Founder suggestions into State Formation Bills.",
                user_prompt=(
                    f"FOUNDING ERA — Cycle {founding_era_cycle}\n\n"
                    f"The Founders must form {target_states} States. Currently: {states_formed} formed.\n"
                    f"Existing domains: {', '.join(existing_domains) if existing_domains else 'None'}\n\n"
                    f"FOUNDER SUGGESTIONS:\n{suggestions_text}\n\n"
                    f"Pick the SINGLE BEST suggestion — the domain most needed right now.\n"
                    f"Write a State Formation Bill:\n\n"
                    f"STATE NAME: [creative name]\n"
                    f"DOMAIN: [one or two words]\n"
                    f"RESEARCH AGENDA: [what this State will investigate]\n"
                    f"JUSTIFICATION: [why this domain is essential and what gap it fills]"
                ),
                max_tokens=400,
                temperature=0.7
            )

            bill_content = synthesis_response.content or "Form a new State for knowledge expansion."
            print(f"\n    STATE FORMATION BILL:")
            print(f"    {bill_content[:200]}...")

            # 3. 2v2 DEBATE — pick supporter and opponent
            debaters = random.sample(self.founders, 2)
            supporter, opponent = debaters[0], debaters[1]

            support_response = self.llm.complete(
                system_prompt=supporter.get_system_prompt(),
                user_prompt=(
                    f"STATE FORMATION DEBATE\n\n"
                    f"Bill:\n{bill_content[:400]}\n\n"
                    f"The Founders must form {target_states} States. We have {states_formed}. "
                    f"We need {target_states - states_formed} more before we can retire.\n\n"
                    f"YOU ({supporter.name}): Argue IN FAVOR. Why should this State exist? "
                    f"What knowledge gap does it fill? Max 200 tokens."
                ),
                max_tokens=200,
                temperature=0.8
            )
            support_arg = support_response.content or ""

            oppose_response = self.llm.complete(
                system_prompt=opponent.get_system_prompt(),
                user_prompt=(
                    f"STATE FORMATION DEBATE\n\n"
                    f"Bill:\n{bill_content[:400]}\n\n"
                    f"Supporter ({supporter.name}) argues:\n{support_arg[:200]}\n\n"
                    f"YOU ({opponent.name}): Argue AGAINST or suggest a BETTER domain. "
                    f"What's wrong with this proposal? Max 200 tokens."
                ),
                max_tokens=200,
                temperature=0.8
            )
            oppose_arg = oppose_response.content or ""

            print(f"\n    DEBATE:")
            print(f"      FOR ({supporter.name}): {support_arg[:150]}...")
            print(f"      AGAINST ({opponent.name}): {oppose_arg[:150]}...")

            # 4. VOTE — with both arguments visible, mission context, and government structure
            # Build readable Constitution summary for voters
            branches_text = []
            for b in self.blueprint.branches:
                branches_text.append(f"  • {b.name} ({b.branch_type}): {b.purpose[:60]}")

            constitution_context = f"""FEDERAL GOVERNMENT:
{chr(10).join(branches_text)}
{len(self.blueprint.non_amendable_clauses)} non-amendable clauses protect State sovereignty"""

            votes = {}
            sample_votes_shown = 0

            for agent in all_senators:
                vote_response = self.llm.complete(
                    system_prompt=agent.get_system_prompt(),
                    user_prompt=(
                        f"STATE FORMATION VOTE — Founding Era Cycle {founding_era_cycle}\n\n"
                        f"{constitution_context}\n\n"
                        f"MISSION: The Founders must form {target_states} States before retiring. "
                        f"Currently {states_formed}/{target_states} formed. "
                        f"{'We are behind schedule.' if states_formed < founding_era_cycle else 'On track.'}\n\n"
                        f"BILL:\n{bill_content[:300]}\n\n"
                        f"FOR ({supporter.name}): {support_arg[:150]}\n"
                        f"AGAINST ({opponent.name}): {oppose_arg[:150]}\n\n"
                        f"Should this State be formed? Reply with exactly one word: APPROVE or REJECT"
                    ),
                    max_tokens=10,
                    temperature=0.3
                )

                if sample_votes_shown < 3:
                    print(f"    DEBUG - {agent.name} raw vote: '{vote_response.content}'")
                    sample_votes_shown += 1

                vote_content = (vote_response.content or "").strip().upper()[:20]
                if "APPROVE" in vote_content and "REJECT" not in vote_content:
                    votes[agent.name] = "approve"
                elif "REJECT" in vote_content and "APPROVE" not in vote_content:
                    votes[agent.name] = "reject"
                else:
                    # Ambiguous defaults to APPROVE for State formation (bias toward growth during Founding Era)
                    votes[agent.name] = "approve"

            approve = sum(1 for v in votes.values() if v == "approve")
            reject = sum(1 for v in votes.values() if v == "reject")

            print(f"\n    VOTE TALLY:")
            approvers = [n for n, v in votes.items() if v == "approve"]
            rejecters = [n for n, v in votes.items() if v == "reject"]
            print(f"      APPROVE ({approve}): {', '.join(approvers)}")
            print(f"      REJECT ({reject}): {', '.join(rejecters)}")

            # Bootstrap threshold: Lower bar for first 3 States (proof of concept)
            if states_formed < 3:
                threshold = 0.4  # 40% (8/20) for first 3 States
                passed = approve / len(votes) >= threshold
                threshold_desc = "40% bootstrap"
            else:
                threshold = 0.5  # 50%+ simple majority after 3 States exist
                passed = approve / len(votes) > threshold
                threshold_desc = "simple majority"

            if passed:
                print(f"    ★ Vote PASSED ({approve}/{len(votes)}) — {threshold_desc}")

                # Form the State
                try:
                    # Convert blueprint to dict format for form_state
                    federal_constitution = {
                        "non_amendable_clauses": getattr(self.blueprint, 'non_amendable_clauses', []),
                        "branches": [
                            {
                                "name": b.name,
                                "type": b.branch_type,
                                "purpose": b.purpose
                            }
                            for b in self.blueprint.branches
                        ]
                    }

                    state = state_manager.form_state(
                        bill={"title": "State Formation", "content": bill_content, "cycle": founding_era_cycle},
                        federal_constitution=federal_constitution,
                        cycle=founding_era_cycle
                    )

                    states_formed += 1
                    print(f"    ★ STATE FORMED: {state.name} ({state.domain}) — Tier {state.tier}")

                    # State Senator JOINS Senate
                    all_senators.append(state.senator)
                    print(f"    Senate size: {len(all_senators)} ({len(self.founders)} Founders + {states_formed} State Senators)")

                    # State begins research immediately
                    print(f"    State {state.name} begins research...")
                    state_result = state.run_research_cycle(
                        federal_agenda="Explore foundational concepts in your domain",
                        llm=self.llm,
                        logger=self.logger,
                        cycle=founding_era_cycle
                    )
                    findings = state_result.get('findings', {})
                    concepts_count = len(findings.get('concepts', []))
                    frameworks_count = len(findings.get('frameworks', []))
                    print(f"    Research complete: Tier {state_result.get('tier', 0)}, {concepts_count} concepts, {frameworks_count} frameworks")

                    # LOG AS HISTORIC EVENT — triggers content generation
                    entry = self.logger._create_entry(
                        level="historic",
                        category="state_formed",
                        title=f"STATE FORMED: {state.name}",
                        summary=(
                            f"The Founders voted {approve}/{len(votes)} to form {state.name}, "
                            f"a new State dedicated to {state.domain}. "
                            f"Proposed collaboratively, debated by {supporter.name} (FOR) and {opponent.name} (AGAINST). "
                            f"State #{states_formed} of {target_states}."
                        ),
                        agents=[supporter.name, opponent.name] + approvers[:3],
                    )
                    self.logger.log(entry)
                    self._generate_content_for_event(entry)

                except Exception as e:
                    print(f"    ✗ State formation failed: {e}")

            else:
                print(f"    ✗ Vote FAILED ({approve}/{len(votes)}) — needed {threshold_desc}")

                # LOG FAILED VOTE — still dramatic content
                entry = self.logger._create_entry(
                    level="dramatic",
                    category="state_formation_failed",
                    title=f"STATE FORMATION REJECTED",
                    summary=(
                        f"The Senate voted {approve}/{len(votes)} against forming a new State. "
                        f"Bill proposed for domain: {bill_content[:100]}. "
                        f"{supporter.name} argued for, {opponent.name} argued against."
                    ),
                    agents=[supporter.name, opponent.name],
                )
                self.logger.log(entry)
                self._generate_content_for_event(entry)
    
            # ─────────────────────────────────────────────────────────
            # STEP 3: RESEARCH (All Founders + All States)
            # ─────────────────────────────────────────────────────────
            print(f"\n  {'─' * 40}")
            print(f"  STEP 3: RESEARCH")
            print(f"  {'─' * 40}")
    
            # Founders research (SKIPPED - BaseAgent doesn't have conduct_research method)
            # Phase 0 already completed Founder research
            print(f"    Founders research skipped (completed in Phase 0)")
    
            # States research (already did in Step 2 for newly formed State)
            existing_states_count = len(state_manager.states) - (1 if passed else 0)
            if existing_states_count > 0:
                print(f"    {existing_states_count} existing States researching...")
                for state in list(state_manager.states.values())[:-1] if passed else state_manager.states.values():
                    state.run_research_cycle(
                        federal_agenda="Continue advancing your domain knowledge",
                        llm=self.llm,
                        logger=self.logger,
                        cycle=founding_era_cycle
                    )
                print(f"    {existing_states_count} States completed research")
    
            # ─────────────────────────────────────────────────────────
            # STEP 4: ARCHIVE DEPOSIT (Every 10 cycles)
            # ─────────────────────────────────────────────────────────
            if founding_era_cycle % 10 == 0:
                print(f"\n  {'─' * 40}")
                print(f"  ARCHIVE DEPOSIT (Cycle {founding_era_cycle})")
                print(f"  {'─' * 40}")
    
                # Deposit Founder knowledge
                for founder in self.founders:
                    for domain, knowledge_area in founder.knowledge.items():
                        if knowledge_area.key_concepts or knowledge_area.frameworks:
                            self.db.deposit_to_archive(
                                source_type="founder",
                                source_id=founder.id,
                                knowledge={
                                    "domain": domain,
                                    "tier": knowledge_area.tier,
                                    "concepts": knowledge_area.key_concepts[:10],
                                    "frameworks": knowledge_area.frameworks[:5],
                                    "applications": knowledge_area.applications[:5],
                                    "synthesis": f"Founder {founder.name} research (Cycle {founding_era_cycle})",
                                    "cycle_created": founding_era_cycle
                                }
                            )
    
                # Deposit State knowledge
                for state in state_manager.states.values():
                    if state.knowledge_entries:
                        latest = state.knowledge_entries[-1]
                        self.db.deposit_to_archive(
                            source_type="state",
                            source_id=state.state_id,
                            knowledge={
                                "domain": state.domain,
                                "tier": latest.tier,
                                "concepts": latest.concepts[:10],
                                "frameworks": latest.frameworks[:5],
                                "applications": latest.applications[:5],
                                "synthesis": latest.synthesis[:200],
                                "cycle_created": founding_era_cycle
                            }
                        )
    
                print(f"    Deposited knowledge from {len(self.founders)} Founders + {len(state_manager.states)} States")
    
            # Advance cycle
            self.logger.advance_cycle()
    
        # ─────────────────────────────────────────────────────────────
        # FOUNDING ERA COMPLETE
        # ─────────────────────────────────────────────────────────────
        print(f"\n{'=' * 70}")
        if states_formed >= target_states:
            print(f"  FOUNDING ERA COMPLETE: {states_formed} States formed in {founding_era_cycle} cycles")
        else:
            print(f"  FOUNDING ERA MAX CYCLES REACHED: {states_formed}/{target_states} States formed")
            print(f"  Proceeding to Founder retirement with {states_formed} States")
        print(f"  Amendments: {amendments_passed} passed, {amendments_failed} failed")
        print(f"{'=' * 70}")
    
        # Save stats
        self.db.set_state("founding_era_cycles_completed", founding_era_cycle)
        self.db.set_state("founding_era_states_formed", states_formed)
        self.db.set_state("founding_era_amendments_passed", amendments_passed)
    
        # Store state_manager for perpetual engine
        self.state_manager = state_manager

        # Save Phase 2 cache (States persist across runs)
        self._save_phase2_cache(state_manager)

        self.db.set_state("current_phase", "founding_era_complete")
        self.current_phase = "founding_era_complete"
    
    def _generate_content_for_event(self, entry):
        """Generate TikTok script and/or blog post for a single event immediately."""
        entry_data = entry if isinstance(entry, dict) else entry.to_dict()

        level = entry_data.get("level", "")

        if level in ["dramatic", "historic"]:
            try:
                self.content_gen.generate_tiktok_script(entry_data)
            except Exception as e:
                print(f"    ⚠ TikTok generation failed: {e}")

        if level in ["significant", "dramatic", "historic"]:
            try:
                self.content_gen.generate_blog_post(entry_data)
            except Exception as e:
                print(f"    ⚠ Blog generation failed: {e}")

    def _generate_content(self):
        """Generate TikTok scripts and blog posts from all logged events."""
        print(f"\n{'=' * 60}")
        print(f"  CONTENT GENERATION — THE PRESS ROOM")
        print(f"{'=' * 60}")

        tiktok_count = 0
        blog_count = 0

        for entry in self.logger.entries:
            entry_data = entry.to_dict()

            # TikTok for dramatic/historic events
            if entry.level in ["dramatic", "historic"]:
                self.content_gen.generate_tiktok_script(entry_data)
                tiktok_count += 1

            # Blog posts for significant+ events
            if entry.level in ["significant", "dramatic", "historic"]:
                self.content_gen.generate_blog_post(entry_data)
                blog_count += 1

        print(f"  TikTok scripts generated: {tiktok_count}")
        print(f"  Blog posts generated: {blog_count}")
        print(f"  Output directory: {self.content_gen.output_dir}")

    def _print_report(self):
        llm_stats = self.llm.get_stats()
        token_report = self.logger.get_token_report()
        content_stats = self.content_gen.get_stats()

        print(f"\n{'=' * 60}")
        print(f"  ATLANTIS STATUS REPORT")
        print(f"{'=' * 60}")
        print(f"  Phase: {self.current_phase}")
        founding_cycles = self.db.get_state("founding_cycles_completed", 0)
        convention_rounds = self.db.get_state("convention_rounds_completed", 0)
        founding_era_cycles = self.db.get_state("founding_era_cycles_completed", 0)
        founding_era_states = self.db.get_state("founding_era_states_formed", 0)
        governance_cycles = self.db.get_state("governance_cycles_completed", 0)
        print(f"  Founding cycles: {founding_cycles}")
        print(f"  Convention rounds: {convention_rounds}")
        print(f"  Founding Era cycles: {founding_era_cycles} ({founding_era_states} States formed)")
        print(f"  Governance cycles: {governance_cycles}")
        print(f"  Total events logged: {token_report['total_events']}")
        print()
        print(f"  LLM Stats:")
        print(f"    Mode: {llm_stats['mode']}")
        print(f"    API calls: {llm_stats['total_calls']}")
        print(f"    Cache hits: {llm_stats['cache_hits']} ({llm_stats['cache_hit_rate']*100:.0f}%)")
        print(f"    Total tokens: {llm_stats['total_tokens']:,}")
        print(f"    Est. cost: ${llm_stats['estimated_cost_usd']:.4f}")
        print(f"    Rate limit waits: {llm_stats['rate_limit_waits']}")
        print()
        print(f"  Content Pipeline:")
        print(f"    TikTok scripts: {content_stats['tiktok_scripts_generated']}")
        print(f"    Blog posts: {content_stats['blog_posts_generated']}")
        print(f"    TikTok queue: {len(self.logger.get_tiktok_queue())} clips")
        print(f"    Blog queue: {len(self.logger.get_blog_queue())} posts")

        # Constitution
        constitution = self.db.get_constitution("federal")
        if constitution:
            print()
            print(f"  Constitution:")
            print(f"    Version: {constitution['version']}")

            # Handle articles as either dict or string (from versioning system)
            articles = constitution.get('articles', [])
            if isinstance(articles, str):
                try:
                    import json
                    articles = json.loads(articles)
                except:
                    articles = []

            print(f"    Articles: {len(articles) if isinstance(articles, (list, dict)) else 0}")
            print(f"    Ratified: {constitution.get('ratified_at', 'Unknown')}")

            if isinstance(articles, list):
                for i, art in enumerate(articles, 1):
                    try:
                        if isinstance(art, dict):
                            title = art.get('title', art.get('number', f'#{i}'))
                            vote = art.get('vote', art.get('vote_count', '?'))
                            print(f"      {i}. {title} ({vote})")
                        elif isinstance(art, str):
                            # If article is a string, just print it
                            print(f"      {i}. {art[:80]}")
                    except Exception as e:
                        # Skip malformed articles
                        print(f"      {i}. [Error displaying article: {e}]")

        # Timeline
        timeline = self.logger.get_timeline()
        if timeline:
            print()
            print(f"  Timeline (significant+ events):")
            for event in timeline[:20]:
                level_icon = {"significant": "◆", "dramatic": "◆◆", "historic": "★"}.get(event["level"], "·")
                print(f"    {level_icon} [{event['category']}] {event['title']}")

        print(f"\n{'=' * 60}\n")


def main():
    """Main entry point for Atlantis."""
    print("DEBUG: main() started", flush=True)

    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        print("DEBUG: Imported dotenv", flush=True)
        load_dotenv()
        print("DEBUG: Loaded .env file", flush=True)
    except ImportError:
        # dotenv not installed, skip (will use system env vars)
        print("DEBUG: dotenv not installed, skipping", flush=True)
        pass

    print("DEBUG: Getting API key from environment", flush=True)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    print(f"DEBUG: API key present: {bool(api_key)}", flush=True)

    # Parse args
    data_dir = "atlantis_data"
    mode = "auto"
    governance_cycles = 10
    mock_mode = False

    print("DEBUG: Parsing arguments", flush=True)
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--local":
            mode = "local"
        elif args[i] == "--mock":
            mock_mode = True
            mode = "auto"  # Mock uses real API calls
        elif args[i] == "--cycles" and i + 1 < len(args):
            governance_cycles = int(args[i + 1])
            i += 1
        elif not args[i].startswith("--"):
            data_dir = args[i]
        i += 1
    print(f"DEBUG: Args parsed - mode={mode}, mock={mock_mode}, data_dir={data_dir}", flush=True)

    # Apply mock overrides (pass as config dict instead of modifying globals)
    mock_config = None
    if mock_mode:
        print("\n" + "=" * 60, flush=True)
        print("  MOCK MODE ENABLED — Quick smoke test with real API calls", flush=True)
        print("=" * 60, flush=True)
        print("  Overrides:", flush=True)
        print("    - Research cycles: 3 (default: 10)", flush=True)
        print("    - Founding Era States: 3 (default: 20)", flush=True)
        print("    - Governance cycles: 5 (default: 10)", flush=True)
        print("    - Convention: 4 rounds (unchanged)", flush=True)
        print("=" * 60 + "\n", flush=True)

        # Create mock config dict (don't modify globals)
        mock_config = {
            "research_cycles": 3,
            "founding_era_target_states": 3,
            "governance_cycles": 5
        }
        governance_cycles = 5
        data_dir = "atlantis_mock"  # Use separate directory for mock

    print(f"DEBUG: Creating engine with mock_config={mock_config}", flush=True)
    engine = AtlantisEngine(data_dir=data_dir, api_key=api_key, mode=mode, mock_config=mock_config)
    print("DEBUG: Engine created, calling run()", flush=True)
    engine.run(governance_cycles=governance_cycles)
    print("DEBUG: Engine.run() completed", flush=True)


if __name__ == "__main__":
    main()
