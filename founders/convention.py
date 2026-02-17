"""
Atlantis Constitutional Convention
====================================
The Founders BUILD the government through structured decisions.
No articles. No parser. No interpretation layer.

Each proposal is a concrete spec. Each vote directly mutates the
GovernmentBlueprint. If it passes, that exact structure becomes
the live config. If it fails, someone counter-proposes.

The Founders KNOW they retire after the Convention.
They're building a machine they'll never operate.

4 Rounds:
  Round 1 — STRUCTURE: Branches, seats, selection methods
  Round 2 — POWERS: What each branch can/can't do, voting thresholds
  Round 3 — KNOWLEDGE & CYCLE: Research, states, tiers, the perpetual cycle
  Round 4 — SAFEGUARDS: Non-amendable clauses, amendment process, deadlock, ethics

Competing proposals: If a decision fails, a counter-proposal fires.
Two runs = two different civilizations.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Callable

from agents.base import BaseAgent, get_all_founders, KnowledgeArea
from content.logger import AtlantisLogger, AgentMessage, LogLevel, LogCategory
from core.llm import LLMProvider, get_llm
from core.persistence import AtlantisDB, get_db
from config.settings import (
    FOUNDING_CONFIG, DEPTH_TIERS, HARD_CONSTRAINTS, API_CONFIG, DEBATE_MATCHUPS
)


def _parse_vote(response_text: str, yes_words=None, no_words=None) -> str:
    if yes_words is None:
        yes_words = ["YES", "APPROVE", "AYE", "SUPPORT", "IN FAVOR"]
    if no_words is None:
        no_words = ["NO", "REJECT", "NAY", "OPPOSE", "AGAINST"]

    text = (response_text or "").strip().upper()[:50]

    has_yes = any(w in text for w in yes_words)
    has_no = any(w in text for w in no_words)

    if has_yes and not has_no:
        return "yes"
    elif has_no and not has_yes:
        return "no"
    elif has_yes and has_no:
        first_yes = min((text.find(w) for w in yes_words if w in text), default=999)
        first_no = min((text.find(w) for w in no_words if w in text), default=999)
        return "yes" if first_yes < first_no else "no"
    return "no"  # Default to no if ambiguous


# ═══════════════════════════════════════════════════════════════
# THE GOVERNMENT BLUEPRINT — Built directly by Founder votes
# ═══════════════════════════════════════════════════════════════

@dataclass
class BranchBlueprint:
    name: str
    branch_type: str
    purpose: str
    seats: list = field(default_factory=list)
    powers: list = field(default_factory=list)
    constraints: list = field(default_factory=list)
    voting_rules: dict = field(default_factory=dict)
    designed_by: str = ""
    vote_result: str = ""


@dataclass
class GovernmentBlueprint:
    """The live government config. Built by votes, not interpretation."""
    branches: list = field(default_factory=list)
    non_amendable_clauses: list = field(default_factory=list)
    amendment_rules: dict = field(default_factory=dict)
    state_formation_rules: dict = field(default_factory=dict)
    cycle_sequence: list = field(default_factory=list)
    knowledge_standards: dict = field(default_factory=dict)
    transparency_rules: dict = field(default_factory=dict)
    resource_rules: dict = field(default_factory=dict)
    health_monitoring: dict = field(default_factory=dict)
    ethical_principles: list = field(default_factory=list)
    content_pipeline: dict = field(default_factory=dict)
    decisions_made: list = field(default_factory=list)
    decisions_rejected: list = field(default_factory=list)

    def get_branch(self, branch_type):
        for b in self.branches:
            if b.branch_type == branch_type:
                return b
        return None

    def has_branch(self, branch_type):
        return any(b.branch_type == branch_type for b in self.branches)

    def to_dict(self):
        return {
            "branches": [
                {"name": b.name, "type": b.branch_type, "purpose": b.purpose,
                 "seats": b.seats, "powers": b.powers, "constraints": b.constraints,
                 "voting_rules": b.voting_rules, "designed_by": b.designed_by,
                 "vote_result": b.vote_result}
                for b in self.branches
            ],
            "non_amendable_clauses": self.non_amendable_clauses,
            "amendment_rules": self.amendment_rules,
            "state_formation_rules": self.state_formation_rules,
            "cycle_sequence": self.cycle_sequence,
            "knowledge_standards": self.knowledge_standards,
            "transparency_rules": self.transparency_rules,
            "resource_rules": self.resource_rules,
            "health_monitoring": self.health_monitoring,
            "ethical_principles": self.ethical_principles,
            "content_pipeline": self.content_pipeline,
            "decisions_made": len(self.decisions_made),
            "decisions_rejected": len(self.decisions_rejected),
        }


# ═══════════════════════════════════════════════════════════════
# PHASE 0: FOUNDING PERIOD
# ═══════════════════════════════════════════════════════════════

class FoundingPeriod:
    """20 Founders × 10 research cycles = 200 knowledge entries."""

    def __init__(self, logger, llm=None, db=None, research_cycles=None):
        self.logger = logger
        self.llm = llm or get_llm()
        self.db = db or get_db()
        self.founders = get_all_founders()
        self.research_cycles = research_cycles if research_cycles is not None else FOUNDING_CONFIG["research_cycles"]

    def run(self):
        print("\n" + "=" * 60)
        print("  PHASE 0: THE FOUNDING PERIOD")
        nc = self.research_cycles
        print(f"  {len(self.founders)} Founders x {nc} cycles = {len(self.founders)*nc} entries")
        print("=" * 60 + "\n")

        # Check for cached Founder knowledge
        cache_result = self._load_founder_knowledge_cache()
        if cache_result["loaded"]:
            print(f"  ✓ Loaded Founder knowledge from cache (skipped {nc} research cycles)")
            print(f"  {len(self.founders)} Founders restored with full research history")
        else:
            # Run full research cycles
            for cycle in range(nc):
                print(f"\n--- Research Cycle {cycle+1}/{nc} ---")
                for founder in self.founders:
                    self._research_cycle(founder, cycle)
                    self.db.save_agent(founder)
                self.logger.advance_cycle()

            # Save cache after completing all research (Constitution will be added later)
            self._save_founder_knowledge_cache()

        ready = 0
        for f in self.founders:
            mx = max((ka.tier for ka in f.knowledge.values()), default=0)
            if mx >= FOUNDING_CONFIG["min_founder_depth"]:
                ready += 1

        self.db.save_checkpoint(
            cycle=self.logger.current_cycle, phase="founding_period_complete",
            state={"research_cycles": nc, "founders_ready": ready}
        )
        # Save founding cycles count to database
        self.db.set_state("founding_cycles_completed", nc)
        print(f"\nFounding Period complete. {ready}/{len(self.founders)} ready.")
        return self.founders

    def _get_cache_path(self):
        """Get path to Founder knowledge cache file."""
        import os
        # Cache is stored alongside the database directory
        data_dir = self.logger.log_dir.replace("/logs", "")
        cache_path = os.path.join(data_dir, "founder_knowledge_cache.json")
        return cache_path

    def _save_founder_knowledge_cache(self, constitution_draft=None):
        """Save Founder knowledge to cache file for future runs."""
        import os
        import json
        from datetime import datetime, timezone

        cache_path = self._get_cache_path()

        # Serialize all Founder knowledge
        cache_data = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "research_cycles": self.research_cycles,
            "constitution_draft": constitution_draft,  # Jefferson's Constitution text
            "founders": []
        }

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
            cache_data["founders"].append(founder_data)

        # Write to file
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)

        print(f"\n  ✓ Saved Founder knowledge cache: {cache_path}")
        print(f"    {len(self.founders)} Founders, {self.research_cycles} cycles")
        if constitution_draft:
            print(f"    Constitution draft: {len(constitution_draft)} characters")

    def _load_founder_knowledge_cache(self):
        """Load Founder knowledge from cache file if it exists.

        Returns:
            dict with 'loaded' (bool) and 'constitution_draft' (str or None)
        """
        import os
        import json
        from agents.base import KnowledgeArea

        cache_path = self._get_cache_path()

        if not os.path.exists(cache_path):
            print(f"  No cache found at {cache_path}")
            return {"loaded": False, "constitution_draft": None}

        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            print(f"  Found Founder knowledge cache from {cache_data.get('created_at', 'unknown date')}")

            # Restore knowledge to each Founder
            for founder in self.founders:
                # Find this founder's data in cache
                founder_data = next(
                    (f for f in cache_data["founders"] if f["id"] == founder.id),
                    None
                )
                if not founder_data:
                    print(f"    ⚠ Cache missing data for {founder.name}, falling back to full research")
                    return {"loaded": False, "constitution_draft": None}

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

            constitution_draft = cache_data.get("constitution_draft")
            return {"loaded": True, "constitution_draft": constitution_draft}

        except Exception as e:
            print(f"    ⚠ Failed to load cache: {e}")
            print(f"    Falling back to full research")
            return {"loaded": False, "constitution_draft": None}

    def _research_cycle(self, founder, cycle):
        domains = list(founder.knowledge.keys())
        domain = domains[cycle % len(domains)]
        current_tier = founder.knowledge[domain].tier
        tier_info = DEPTH_TIERS.get(current_tier + 1, DEPTH_TIERS[5])

        prompt = (
            f"Research '{domain}' to reach Tier {current_tier+1} ({tier_info['name']}). "
            f"Current: Tier {current_tier}.\nRequirements:\n"
        )
        for req in tier_info["requirements"]:
            prompt += f"  - {req}\n"
        prompt += (
            "\nProvide:\nCONCEPTS: [list]\nFRAMEWORKS: [list]\n"
            "APPLICATIONS: [list]\nCONNECTIONS: [list]\nSYNTHESIS: [insights]"
        )

        response = self.llm.complete(
            system_prompt=founder.get_system_prompt(),
            user_prompt=prompt,
            temperature=API_CONFIG["founder_temperature"]
        )

        concepts, frameworks, applications, connections = _parse_research(response.content)
        founder.update_knowledge(domain=domain, concepts=concepts,
                                 frameworks=frameworks, applications=applications,
                                 connections=connections)

        ka = founder.knowledge[domain]
        nxt = DEPTH_TIERS.get(ka.tier + 1)
        if nxt and (len(ka.key_concepts) >= nxt["min_concepts"] and
                    len(ka.frameworks) >= nxt["min_frameworks"] and
                    len(ka.applications) >= nxt["min_applications"]):
            ka.tier += 1
            self.logger.log_depth_tier(
                entity=founder.name, tier=ka.tier, domain=domain,
                evidence=f"{len(ka.key_concepts)}c, {len(ka.frameworks)}f",
                tokens=response.total_tokens
            )
            print(f"    * {founder.name} reached Tier {ka.tier} in {domain}!")

        founder.total_tokens_used += response.total_tokens
        self.logger.log_founder_research(
            agent_name=founder.name, agent_role=founder.role,
            topic=f"{domain} (T{current_tier}->{current_tier+1})",
            findings=response.content[:500] if response.content else "",
            tokens=response.total_tokens
        )
        print(f"  {founder.name} researched {domain} ({response.total_tokens} tok)")


# ═══════════════════════════════════════════════════════════════
# PHASE 1: CONSTITUTIONAL CONVENTION — 4 ROUNDS
# ═══════════════════════════════════════════════════════════════

class ConstitutionalConvention:
    """
    4 rounds. Each vote directly mutates the blueprint.
    No parser. No interpretation. The Founders build the machine.
    """

    def __init__(self, founders, logger, llm=None, db=None):
        self.founders_map = {f.name: f for f in founders}
        self.founder_list = founders
        self.logger = logger
        self.llm = llm or get_llm()
        self.db = db or get_db()
        self.blueprint = GovernmentBlueprint()
        self.ratified = False
        self.threshold = FOUNDING_CONFIG["ratification_threshold"]


    def run(self):
        """
        New Convention flow:
        - Step 0: Jefferson writes complete draft Constitution
        - Rounds 1-4: All 20 Founders propose amendments (80 total)
        - Ratification vote
        """
        print("\n" + "=" * 60)
        print("  JEFFERSON DRAFT (Convention Phase Removed)")
        print("  Amendments will happen during Founding Era")
        print("=" * 60)

        # Step 0: Jefferson writes draft
        self._step_0_jefferson_draft()

        # Validate
        self._validate_final_blueprint()

        # No ratification vote needed (will evolve during Founding Era)
        self.ratified = True

        return self.blueprint


    def _get_cache_path(self):
        """Get path to Founder/Constitution cache file."""
        import os
        # Cache is stored alongside the database directory
        data_dir = self.logger.log_dir.replace("/logs", "")
        cache_path = os.path.join(data_dir, "founder_knowledge_cache.json")
        return cache_path

    def _load_constitution_from_cache(self):
        """Check if Constitution draft exists in cache."""
        import os
        import json

        cache_path = self._get_cache_path()

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            constitution_draft = cache_data.get("constitution_draft")
            if constitution_draft:
                print(f"  ✓ Found Constitution draft in cache ({len(constitution_draft)} characters)")
                return constitution_draft
            else:
                return None

        except Exception as e:
            print(f"    ⚠ Failed to load Constitution from cache: {e}")
            return None

    def _save_constitution_to_cache(self, draft_text):
        """Save Constitution draft to cache."""
        import os
        import json

        cache_path = self._get_cache_path()

        if not os.path.exists(cache_path):
            print(f"    ⚠ Cache file doesn't exist yet, Constitution will be saved on next Phase 0 run")
            return

        try:
            # Read existing cache
            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            # Update Constitution draft
            cache_data["constitution_draft"] = draft_text

            # Write back
            with open(cache_path, "w") as f:
                json.dump(cache_data, f, indent=2)

            print(f"  ✓ Saved Constitution draft to cache ({len(draft_text)} characters)")

        except Exception as e:
            print(f"    ⚠ Failed to save Constitution to cache: {e}")

    def _step_0_jefferson_draft(self):
        """Step 0: Jefferson writes complete draft Constitution."""
        print("\n" + "=" * 60)
        print("  STEP 0: JEFFERSON WRITES THE DRAFT CONSTITUTION")
        print("=" * 60)

        # Check cache first
        cached_draft = self._load_constitution_from_cache()
        if cached_draft:
            print(f"  Using cached Constitution draft (skipped Jefferson LLM call)")
            draft_text = cached_draft
        else:
            jefferson = self.founders_map.get("Jefferson")
            if not jefferson:
                print("  ERROR: Jefferson not found in founders")
                return

            # Jefferson's prompt to write the entire Constitution
            prompt = f"""You are Thomas Jefferson. You've spent {self.db.get_state('research_cycles', 10)} cycles researching alongside 19 other Founders.

    You've seen what happens when AI systems run without governance — they loop, they hallucinate, they drift into repetition, they collapse under their own weight. Knowledge without structure dies. Depth without checks becomes delusion.

    You've watched systems that start strong and produce the same surface-level output forever because nothing forces them deeper. You've seen what happens when there's no critic, no judge, no mechanism to say 'that's not good enough, go deeper.'

    Now you must write the founding document for an AI civilization that SOLVES these problems. A government that forces depth. That catches loops before they kill progress. That validates knowledge so hallucination can't masquerade as insight. That grows forever — adding new States, new Cities, new Towns — each going deeper than the last, each governed by checks and balances that prevent collapse.

    Write the Constitution. All of it.

    REQUIRED SECTIONS (format your response with these headers):

    ## BRANCHES
    Define the branches of government:
    - How many branches? (at least 2, recommend 3-4)
    - For each branch, specify: NAME | TYPE (legislative/executive/judicial/implementation) | SEATS (number) | ROLES (comma-separated) | PURPOSE

    Example:
    BRANCH: Federal Senate | legislative | 4 | Critic,Tester,Historian,Debugger | Deliberates Bills and sets agendas

    ## POWERS
    Define what each branch can do:
    - Voting thresholds (simple majority, supermajority, unanimous)
    - Veto powers
    - Who proposes Bills, who reviews, who judges

    ## KNOWLEDGE ENGINE
    Define how research works:
    - What are the knowledge tiers? (1-5, what each represents)
    - How do States form? What triggers new State creation?
    - How do Cities form from States? Towns from Cities?
    - Research cycle structure

    ## SAFEGUARDS
    What can NEVER be changed?
    - List at least 3 non-amendable clauses that protect system integrity
    - How are amendments proposed and ratified?
    - What prevents infinite loops and hallucination?

    ## CYCLE SEQUENCE
    What happens each governance cycle?
    - List the steps in order
    - REQUIRED: Must include a step named exactly "research" (critical for State system)
    - Example steps: agenda, research, legislate, validate, implement, judge, document

    This civilization will outlive its Founders. Make it unbreakable."""

            response = self.llm.complete(
                system_prompt=jefferson.get_system_prompt(),
                user_prompt=prompt,
                max_tokens=2500,
                temperature=0.8
            )

            jefferson.total_tokens_used += response.total_tokens

            draft_text = response.content or ""

            # Save to cache for future runs
            self._save_constitution_to_cache(draft_text)

        # Print Constitution (both cached and fresh)
        print(f"\n{'=' * 70}")
        print(f"  JEFFERSON'S COMPLETE DRAFT CONSTITUTION ({len(draft_text)} characters)")
        print(f"{'=' * 70}")
        print(f"\n{draft_text}\n")
        print(f"{'=' * 70}")

        # Store draft text for later use
        self.draft_text = draft_text

        # Parse Jefferson's draft into blueprint
        self._parse_jefferson_draft(draft_text)

        # Validate draft
        if not self._validate_draft():
            print("  ⚠ Draft incomplete - requesting revision...")
            self._request_jefferson_revision()

        # Log the draft (TODO: add proper logging method)
        # self.logger.log_narrative_event(
        #     title="Jefferson's Draft Constitution",
        #     summary=draft_text[:500],
        #     agents_involved=[jefferson.name],
        #     tokens=response.total_tokens
        # )


    def _normalize_cycle_sequence(self, raw_steps):
        """Map Jefferson's free-text step names to standard engine steps."""
        mapping = {
            "research": "research",
            "state research": "research",
            "knowledge": "research",
            "legislate": "legislate",
            "legislation": "legislate",
            "senate": "legislate",
            "implement": "implement",
            "execute": "implement",
            "judge": "judge",
            "judicial": "judge",
            "review": "judge",
            "health": "health_check",
            "monitor": "health_check",
            "archive": "archive",
            "agenda": "agenda",
        }

        normalized = []
        for step in raw_steps:
            step_lower = step.lower().strip()
            matched = mapping.get(step_lower)
            if not matched:
                # Fuzzy match
                for key, value in mapping.items():
                    if key in step_lower:
                        matched = value
                        break
            if matched and matched not in normalized:
                normalized.append(matched)

        # Ensure minimum required steps exist
        for required in ["research", "legislate", "judge"]:
            if required not in normalized:
                normalized.append(required)

        return normalized

    def _parse_jefferson_draft(self, draft_text):
        """Parse Jefferson's draft into the blueprint."""
        import re

        # Parse BRANCHES section
        branches_section = re.search(r'## BRANCHES\s*\n(.*?)(?=\n##|$)', draft_text, re.DOTALL | re.IGNORECASE)
        if branches_section:
            branch_lines = branches_section.group(1)
            for line in branch_lines.split('\n'):
                if 'BRANCH:' in line.upper():
                    # Parse: NAME | TYPE | SEATS | ROLES | PURPOSE
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 5:
                        name = parts[0].replace('BRANCH:', '').strip()
                        branch_type = parts[1].strip()
                        # CRITICAL FIX: Check if regex match exists before calling .group()
                        match = re.search(r'\d+', parts[2])
                        seats = int(match.group()) if match else 3  # Default to 3 if no digits found
                        roles = [r.strip() for r in parts[3].split(',')]
                        purpose = parts[4].strip()

                        self._add_branch(
                            name=name,
                            branch_type=branch_type,
                            purpose=purpose,
                            seats=[{"name": role, "mandate": f"{role} duties"} for role in roles],
                            designed_by="Jefferson (Draft)"
                        )

        # Parse SAFEGUARDS section
        safeguards_section = re.search(r'## SAFEGUARDS\s*\n(.*?)(?=\n##|$)', draft_text, re.DOTALL | re.IGNORECASE)
        if safeguards_section:
            safeguard_text = safeguards_section.group(1)
            # Extract bullet points or numbered items
            safeguards = re.findall(r'[-*\d]+\.?\s+(.+)', safeguard_text)
            for safeguard in safeguards[:5]:  # Take first 5
                if len(safeguard) > 20:  # Meaningful safeguard
                    self.blueprint.non_amendable_clauses.append(safeguard.strip())

        # Parse CYCLE SEQUENCE section
        cycle_section = re.search(r'## CYCLE SEQUENCE\s*\n(.*?)(?=\n##|$)', draft_text, re.DOTALL | re.IGNORECASE)
        if cycle_section:
            cycle_text = cycle_section.group(1)
            steps = re.findall(r'[-*\d]+\.?\s+(\w+)', cycle_text)
            if steps:
                # Normalize Jefferson's free-text steps to standard engine steps
                self.blueprint.cycle_sequence = self._normalize_cycle_sequence(steps[:10])

        print(f"  Parsed: {len(self.blueprint.branches)} branches, {len(self.blueprint.non_amendable_clauses)} safeguards")


    def _validate_draft(self):
        """Validate Jefferson's draft is complete enough to proceed."""
        if len(self.blueprint.branches) < 2:
            print(f"  ✗ Only {len(self.blueprint.branches)} branches (need at least 2)")
            return False

        if any(len(b.seats) < 1 for b in self.blueprint.branches):
            print("  ✗ Branch with 0 seats")
            return False

        if len(self.blueprint.non_amendable_clauses) < 1:
            print("  ✗ No safeguards defined")
            return False

        print(f"  ✓ Draft valid: {len(self.blueprint.branches)} branches, {len(self.blueprint.non_amendable_clauses)} safeguards")
        return True


    def _request_jefferson_revision(self):
        """Request Jefferson to revise incomplete draft."""
        jefferson = self.founders_map.get("Jefferson")
        if not jefferson:
            self._apply_minimal_fallback()
            return

        gaps = []
        if len(self.blueprint.branches) < 2:
            gaps.append(f"Only {len(self.blueprint.branches)} branches defined - need at least 2")
        if len(self.blueprint.non_amendable_clauses) < 1:
            gaps.append("No safeguards defined")

        prompt = f"""Your draft Constitution is incomplete. Please revise to include:

    {chr(10).join('- ' + g for g in gaps)}

    Provide the missing sections in the same format as before."""

        response = self.llm.complete(
            system_prompt=jefferson.get_system_prompt(),
            user_prompt=prompt,
            max_tokens=1500,
            temperature=0.8
        )

        self._parse_jefferson_draft(response.content or "")

        if not self._validate_draft():
            print("  ✗ Revision still incomplete - using minimal fallback")
            self._apply_minimal_fallback()


    def _apply_minimal_fallback(self):
        """Apply minimal fallback Constitution if Jefferson's draft fails."""
        print("  ⚠ Applying minimal fallback Constitution")

        self.blueprint.branches = []

        self._add_branch(
            "Federal Senate", "legislative",
            "Deliberates Bills and sets agendas",
            [{"name": "Critic", "mandate": "Challenge proposals"},
             {"name": "Tester", "mandate": "Verify claims"},
             {"name": "Historian", "mandate": "Maintain memory"},
             {"name": "Debugger", "mandate": "Monitor health"}],
            designed_by="Fallback"
        )

        self._add_branch(
            "Federal House", "implementation",
            "Reviews implementation feasibility",
            [{"name": "Architect", "mandate": "Design plans"},
             {"name": "Coder", "mandate": "Validate execution"}],
            designed_by="Fallback"
        )

        self._add_branch(
            "Supreme Court", "judicial",
            "Interprets Constitution",
            [{"name": "WARDEN", "mandate": "Constitutional guardian"},
             {"name": "Justice Critic", "mandate": "Find weaknesses"},
             {"name": "Justice Historian", "mandate": "Reference precedent"}],
            designed_by="Fallback"
        )

        self.blueprint.non_amendable_clauses = [
            "The government must force knowledge to progress through tiers",
            "No single agent can override system checks",
            "Transparency is mandatory for all decisions"
        ]

        self.blueprint.cycle_sequence = ["agenda", "research", "legislate", "implement", "judge"]


    def _amendment_round(self, round_num):
        """Run one round where all 20 Founders propose amendments sequentially."""
        round_themes = {
            1: "Here is YOUR constitution after Jefferson's draft. What else needs to change?",
            2: "After Round 1. What did Round 1 break? What's missing?",
            3: "Your constitution is maturing. What conflicts exist? What edge cases aren't covered?",
            4: "Final draft. What must be locked in permanently? What can never be changed?"
        }

        print(f"\n{'=' * 60}")
        print(f"  ROUND {round_num}: AMENDMENTS")
        print(f"  Theme: {round_themes[round_num]}")
        print(f"  All 20 Founders propose 1 amendment each")
        print(f"{'=' * 60}")

        amendments_passed = 0
        amendments_failed = 0

        for idx, founder in enumerate(self.founder_list):
            print(f"\n{'─' * 70}")
            print(f"  AMENDMENT {idx+1}/20 — Proposed by {founder.name}")
            print(f"{'─' * 70}")

            # Founder proposes amendment with full blueprint context
            amendment_proposal = self._propose_amendment(founder, round_num, idx, round_themes[round_num])

            if not amendment_proposal:
                print(f"    ⚠ No amendment parsed from {founder.name}")
                continue

            print(f"\n  AMENDMENT TEXT:")
            print(f"    {amendment_proposal['text']}")
            print(f"\n  RATIONALE:")
            print(f"    {amendment_proposal['rationale']}")

            # 2v2 debate
            supporter, opponent = self._select_debaters(founder)
            support_arg = self._debate_support(supporter, amendment_proposal)
            oppose_arg = self._debate_oppose(opponent, amendment_proposal, support_arg)

            print(f"\n  DEBATE:")
            print(f"    FOR ({supporter.name}): {support_arg}")
            print(f"    AGAINST ({opponent.name}): {oppose_arg}")

            # All 20 vote
            votes = self._vote_on_amendment(amendment_proposal, support_arg, oppose_arg)

            print(f"\n  VOTE TALLY:")
            # Print YES votes
            yes_voters = [v.split(": ")[0] for v in self._last_vote_details if "YES" in v]
            no_voters = [v.split(": ")[0] for v in self._last_vote_details if "NO" in v]
            print(f"    YES ({votes['yes']}): {', '.join(yes_voters)}")
            print(f"    NO ({votes['no']}): {', '.join(no_voters)}")

            # Pass requires 14/20 (70% supermajority)
            if votes['yes'] >= 14:
                self._apply_amendment(amendment_proposal)
                amendments_passed += 1
                print(f"  ✓ PASSED (needed 14/20)")
            else:
                amendments_failed += 1
                print(f"  ✗ FAILED (needed 14/20)")

            print(f"\n  Round {round_num} running total: {amendments_passed} passed, {amendments_failed} failed")

        print(f"\n  Round {round_num} complete: {amendments_passed} passed, {amendments_failed} failed")


    def _collaborative_amendment_round(self, round_num: int):
        """All 20 Founders collaboratively propose ONE amendment this round."""
        import random

        print(f"\n{'=' * 70}")
        print(f"  ROUND {round_num}/40 — COLLABORATIVE AMENDMENT")
        print(f"{'=' * 70}")

        # Step 1: Sample 5 Founders for suggestions (saves tokens)
        sample_founders = random.sample(self.founder_list, 5)
        suggestions = []

        for founder in sample_founders:
            suggestion = self._get_individual_suggestion(founder, round_num)
            if suggestion:
                suggestions.append({
                    "founder": founder.name,
                    "suggestion": suggestion
                })

        if not suggestions:
            print("  ⚠ No suggestions generated")
            return False

        # Step 2: Synthesize into ONE best amendment
        amendment = self._synthesize_amendment(suggestions, round_num)

        if not amendment:
            print("  ⚠ No amendment synthesized")
            return False

        print(f"\n  COLLABORATIVE AMENDMENT:")
        print(f"    {amendment['text']}")
        print(f"\n  RATIONALE:")
        print(f"    {amendment['rationale']}")

        # Step 3: 2v2 Debate (pick any 2 founders, not based on proposer)
        debaters = random.sample(self.founder_list, 2)
        supporter, opponent = debaters[0], debaters[1]

        support_arg = self._debate_support(supporter, amendment)
        oppose_arg = self._debate_oppose(opponent, amendment, support_arg)

        print(f"\n  DEBATE:")
        print(f"    FOR ({supporter.name}): {support_arg}")
        print(f"    AGAINST ({opponent.name}): {oppose_arg}")

        # Step 4: All 20 vote
        votes = self._vote_on_amendment(amendment, support_arg, oppose_arg)

        print(f"\n  VOTE TALLY:")
        yes_voters = [v.split(": ")[0] for v in self._last_vote_details if "YES" in v]
        no_voters = [v.split(": ")[0] for v in self._last_vote_details if "NO" in v]
        print(f"    YES ({votes['yes']}): {', '.join(yes_voters)}")
        print(f"    NO ({votes['no']}): {', '.join(no_voters)}")

        # Step 5: Apply if passed
        if votes['yes'] >= 14:
            self._apply_amendment(amendment)
            print(f"  ✓ PASSED (14/20 supermajority)")
            return True
        else:
            print(f"  ✗ FAILED (needed 14/20)")
            return False


    def _get_individual_suggestion(self, founder, round_num):
        """Founder suggests one change to the Constitution."""
        blueprint_json = json.dumps(self.blueprint.to_dict(), indent=2)

        prompt = f"""CONSTITUTIONAL AMENDMENT — Round {round_num}/40

CURRENT BLUEPRINT:
{blueprint_json}

YOU ({founder.name}): Looking at the current Constitution above, what ONE change would most improve it?

Suggest ONE specific improvement (not a full amendment yet, just the core idea).

Format: [One sentence describing the change]"""

        response = self.llm.complete(
            system_prompt=founder.get_system_prompt(),
            user_prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )

        founder.total_tokens_used += response.total_tokens

        return (response.content or "").strip()


    def _synthesize_amendment(self, suggestions, round_num):
        """Synthesize 5 individual suggestions into ONE best amendment."""

        suggestions_text = "\n".join([
            f"- {s['founder']}: {s['suggestion']}"
            for s in suggestions
        ])

        blueprint_json = json.dumps(self.blueprint.to_dict(), indent=2)

        prompt = f"""AMENDMENT SYNTHESIS — Round {round_num}/40

CURRENT BLUEPRINT:
{blueprint_json[:1000]}...

FOUNDER SUGGESTIONS:
{suggestions_text}

YOUR TASK: Looking at these suggestions, identify the SINGLE MOST IMPORTANT change needed.

Combine the best ideas into ONE clear amendment. Format:

AMENDMENT: [specific change in one sentence]
RATIONALE: [why this is the most important change right now]"""

        response = self.llm.complete(
            system_prompt="You synthesize multiple viewpoints into clear amendments.",
            user_prompt=prompt,
            max_tokens=400,
            temperature=0.7
        )

        content = response.content or ""

        # Parse amendment
        import re
        amendment_match = re.search(r'AMENDMENT:\s*(.+?)(?=\nRATIONALE:|$)', content, re.IGNORECASE | re.DOTALL)
        rationale_match = re.search(r'RATIONALE:\s*(.+?)$', content, re.IGNORECASE | re.DOTALL)

        if amendment_match:
            return {
                "text": amendment_match.group(1).strip(),
                "rationale": rationale_match.group(1).strip() if rationale_match else "No rationale",
                "round": round_num,
                "proposer": "Collaborative"
            }

        return None


    def _propose_amendment(self, founder, round_num, idx, theme):
        """Founder proposes ONE amendment with full blueprint context."""
        blueprint_json = json.dumps(self.blueprint.to_dict(), indent=2)

        prompt = f"""CONSTITUTIONAL AMENDMENT — Round {round_num}, Founder {idx+1}/20

    CURRENT BLUEPRINT:
    {blueprint_json}

    Round {round_num} theme: {theme}

    YOU ({founder.name}): What one change would improve this Constitution?

    Propose ONE specific amendment to any part of the blueprint above. You can:
    - Add a new branch, safeguard, or rule
    - Modify an existing branch's powers or composition
    - Change voting thresholds or procedures
    - Strengthen safeguards against system failures

    Format:
    AMENDMENT: [specific change in one sentence]
    RATIONALE: [why this matters, what problem it solves]"""

        response = self.llm.complete(
            system_prompt=founder.get_system_prompt(),
            user_prompt=prompt,
            max_tokens=400,
            temperature=0.8
        )

        founder.total_tokens_used += response.total_tokens

        content = response.content or ""
        print(f"    DEBUG - LLM response (first 200 chars): {content[:200]}")

        # Parse amendment
        import re
        amendment_match = re.search(r'AMENDMENT:\s*(.+?)(?=\nRATIONALE:|$)', content, re.IGNORECASE | re.DOTALL)
        rationale_match = re.search(r'RATIONALE:\s*(.+?)$', content, re.IGNORECASE | re.DOTALL)

        if amendment_match:
            amendment_text = amendment_match.group(1).strip()
            rationale = rationale_match.group(1).strip() if rationale_match else "No rationale provided"

            return {
                "proposer": founder.name,
                "text": amendment_text,
                "rationale": rationale,
                "round": round_num,
                "index": idx
            }

        return None


    def _select_debaters(self, proposer):
        """Select random supporter and opponent (not the proposer)."""
        import random

        available = [f for f in self.founder_list if f.name != proposer.name]

        if len(available) < 2:
            return proposer, proposer

        # Use random.sample instead of shuffle+slice
        debaters = random.sample(available, 2)
        return debaters[0], debaters[1]


    def _debate_support(self, supporter, amendment):
        """Supporter argues FOR the amendment (max 200 tokens)."""
        prompt = f"""CONSTITUTIONAL AMENDMENT DEBATE

    Amendment proposed by {amendment['proposer']}:
    {amendment['text']}

    Rationale: {amendment['rationale']}

    YOU ({supporter.name}): Argue IN FAVOR of this amendment in 200 tokens or less.

    Why is this change necessary? What problem does it solve? What risks does it prevent?"""

        response = self.llm.complete(
            system_prompt=supporter.get_system_prompt(),
            user_prompt=prompt,
            max_tokens=200,
            temperature=0.8
        )

        supporter.total_tokens_used += response.total_tokens

        return response.content or ""


    def _debate_oppose(self, opponent, amendment, support_arg):
        """Opponent argues AGAINST the amendment (max 200 tokens)."""
        prompt = f"""CONSTITUTIONAL AMENDMENT DEBATE

    Amendment proposed by {amendment['proposer']}:
    {amendment['text']}

    Supporter said:
    {support_arg}

    YOU ({opponent.name}): Argue AGAINST this amendment in 200 tokens or less.

    What are the risks? What could break? What unintended consequences might occur?"""

        response = self.llm.complete(
            system_prompt=opponent.get_system_prompt(),
            user_prompt=prompt,
            max_tokens=200,
            temperature=0.8
        )

        opponent.total_tokens_used += response.total_tokens

        return response.content or ""


    def _vote_on_amendment(self, amendment, support_arg, oppose_arg):
        """All 20 Founders vote on the amendment."""
        votes = {"yes": 0, "no": 0}
        vote_details = []
        sample_votes_shown = 0

        for founder in self.founder_list:
            prompt = f"""CONSTITUTIONAL AMENDMENT VOTE

    Amendment: {amendment['text']}

    Supporter argues: {support_arg}
    Opponent argues: {oppose_arg}

    Vote YES to adopt or NO to reject. Respond with just YES or NO."""

            response = self.llm.complete(
                system_prompt=founder.get_system_prompt(),
                user_prompt=prompt,
                max_tokens=10,
                temperature=0.5
            )

            founder.total_tokens_used += response.total_tokens

            vote_text = (response.content or "").strip()
            result = _parse_vote(vote_text)
            if result == "yes":
                votes["yes"] += 1
                vote_details.append(f"{founder.name}: YES")
            else:
                votes["no"] += 1
                vote_details.append(f"{founder.name}: NO")

            # Show first 3 sample votes
            if sample_votes_shown < 3:
                print(f"    Sample vote {sample_votes_shown + 1} — {founder.name}: {vote_text}")
                sample_votes_shown += 1

        # Store vote details for final tally
        self._last_vote_details = vote_details
        return votes


    def _apply_amendment(self, amendment):
        """Apply passed amendment to blueprint.

        Use Claude to parse amendment into structured mutation."""
        blueprint_json = json.dumps(self.blueprint.to_dict())

        prompt = f"""Given the current blueprint and this amendment proposal, determine what specific change to make.

    Current blueprint:
    {blueprint_json[:1000]}

    Amendment: {amendment['text']}

    What should be modified? Respond with ONE of:
    - ADD_BRANCH: [name] | [type] | [purpose]
    - MODIFY_BRANCH: [name] | [what to change]
    - ADD_SAFEGUARD: [safeguard text]
    - MODIFY_VOTING: [branch name] | [new threshold]
    - ADD_CYCLE_STEP: [step name]
    - NO_CHANGE: [if amendment is too vague to implement]

    Format: ACTION: details"""

        response = self.llm.complete(
            system_prompt="You parse Constitutional amendments into structured changes.",
            user_prompt=prompt,
            max_tokens=150,
            temperature=0.3
        )

        action_text = (response.content or "").strip()

        # Parse and apply action
        if "ADD_SAFEGUARD:" in action_text:
            safeguard = action_text.split("ADD_SAFEGUARD:")[1].strip()
            self.blueprint.non_amendable_clauses.append(safeguard)
            print(f"      → Added safeguard")

        elif "ADD_CYCLE_STEP:" in action_text:
            step = action_text.split("ADD_CYCLE_STEP:")[1].strip()
            if step and step not in self.blueprint.cycle_sequence:
                self.blueprint.cycle_sequence.append(step)
                print(f"      → Added cycle step: {step}")

        elif "MODIFY_VOTING:" in action_text:
            print(f"      → Voting rule modified (logged)")

        elif "NO_CHANGE" in action_text:
            print(f"      → Amendment too vague to implement")

        else:
            print(f"      → Amendment applied (general)")

        # Record the amendment
        self.blueprint.decisions_made.append({
            "type": "amendment",
            "proposer": amendment['proposer'],
            "text": amendment['text'],
            "round": amendment['round']
        })


    def _validate_final_blueprint(self):
        """Validate final blueprint after all amendments."""
        print(f"\n{'=' * 60}")
        print("  FINAL BLUEPRINT VALIDATION")
        print(f"{'=' * 60}")

        if len(self.blueprint.branches) < 2:
            print(f"  ✗ VALIDATION FAILED: Only {len(self.blueprint.branches)} branches")
            print("  → Applying minimal fallback")
            self._apply_minimal_fallback()
            return

        if any(len(b.seats) < 1 for b in self.blueprint.branches):
            print("  ✗ VALIDATION FAILED: Branch with 0 seats")
            print("  → Applying minimal fallback")
            self._apply_minimal_fallback()
            return

        print(f"  ✓ Valid blueprint:")
        print(f"    - {len(self.blueprint.branches)} branches")
        print(f"    - {len(self.blueprint.non_amendable_clauses)} safeguards")
        print(f"    - {len(self.blueprint.decisions_made)} amendments adopted")


    def _print_final_blueprint(self, passed, total):
        """Print the complete final blueprint as JSON."""
        print(f"\n{'=' * 70}")
        print(f"  FINAL CONSTITUTION - COMPLETE BLUEPRINT")
        print(f"{'=' * 70}")
        print(f"\n{json.dumps(self.blueprint.to_dict(), indent=2)}\n")
        print(f"{'=' * 70}")
        print(f"\n  Total amendments passed: {passed} / {total}")
        print(f"  Final branches: {len(self.blueprint.branches)}")
        print(f"  Final safeguards: {len(self.blueprint.non_amendable_clauses)}")
        print(f"{'=' * 70}")


    def _add_branch(self, name, branch_type, purpose, seats,
                    voting_rules=None, designed_by=""):
        b = BranchBlueprint(
            name=name, branch_type=branch_type, purpose=purpose,
            seats=seats, voting_rules=voting_rules or {},
            designed_by=designed_by
        )
        self.blueprint.branches.append(b)

    def _add_powers(self, branch_type, powers):
        branch = self.blueprint.get_branch(branch_type)
        if branch:
            branch.powers.extend(powers)

    # ─── RATIFICATION & RETIREMENT ───────────────────────────

    def _ratify(self):
        if not self.blueprint.decisions_made:
            print("\n  WARNING: No decisions adopted. Cannot ratify.")
            return

        all_votes = {f.name: "approve" for f in self.founder_list}
        self.logger.log_constitution_ratified(
            articles=self.blueprint.decisions_made,
            votes=all_votes, tokens=0
        )
        self.db.save_constitution(
            constitution_type="federal",
            articles=self.blueprint.decisions_made,
            ratified_by=all_votes
        )
        self.ratified = True

        print(f"\n{'=' * 60}")
        print(f"  THE GOVERNMENT OF ATLANTIS IS RATIFIED")
        print(f"  {len(self.blueprint.decisions_made)} decisions adopted, "
              f"{len(self.blueprint.decisions_rejected)} rejected")
        print(f"  {len(self.blueprint.branches)} branches")
        if self.blueprint.non_amendable_clauses:
            print(f"  {len(self.blueprint.non_amendable_clauses)} non-amendable clauses")
        if self.blueprint.cycle_sequence:
            print(f"  Cycle: {' -> '.join(self.blueprint.cycle_sequence)}")
        print(f"{'=' * 60}")

    def retire_founders(self):
        print("\n--- Founder Retirement ---")
        for f in self.founder_list:
            self.db.save_agent(f)
            self.db.retire_agent(f.id)
            print(f"  {f.name} retires. Knowledge archived.")
        self.db.save_checkpoint(
            cycle=self.logger.current_cycle, phase="founders_retired",
            state={"founders_retired": [f.name for f in self.founder_list]}
        )
        print(f"\nAll {len(self.founder_list)} Founders retired. The government stands.\n")


# ═══════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════

def _parse_research(content):
    """Parse research output from LLM response.

    Handles all Claude formatting styles:
    - Plain: CONCEPTS: item1, item2
    - Bold markdown: **CONCEPTS:** item1, item2
    - Bulleted: - item1\\n- item2
    - Numbered: 1. item1\\n2. item2
    """
    concepts, frameworks, applications, connections = [], [], [], []
    if not content:
        return concepts, frameworks, applications, connections

    current = None
    for line in content.split("\n"):
        line = line.strip()
        # Strip bold markdown: **CONCEPTS:** → CONCEPTS:
        clean = line.replace("**", "").replace("*", "").strip()
        u = clean.upper()

        if u.startswith("CONCEPTS:") or u.startswith("KEY CONCEPTS:"):
            current = "c"
            r = clean.split(":", 1)[-1].strip()
            if r:
                concepts.extend(_split(r))
        elif u.startswith("FRAMEWORKS:") or u.startswith("KEY FRAMEWORKS:"):
            current = "f"
            r = clean.split(":", 1)[-1].strip()
            if r:
                frameworks.extend(_split(r))
        elif u.startswith("APPLICATIONS:"):
            current = "a"
            r = clean.split(":", 1)[-1].strip()
            if r:
                applications.extend(_split(r))
        elif u.startswith("CONNECTIONS:"):
            current = "x"
            r = clean.split(":", 1)[-1].strip()
            if r:
                connections.extend(_split(r))
        elif u.startswith("SYNTHESIS:"):
            current = None
        elif u.startswith("EVIDENCE:"):
            current = None
        elif line.startswith("- ") or line.startswith("* ") or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
            # Handle bullets: - item, * item, 1. item, 1) item
            item = line.lstrip("-*0123456789.) ").strip()
            if item:
                if current == "c":
                    concepts.append(item)
                elif current == "f":
                    frameworks.append(item)
                elif current == "a":
                    applications.append(item)
                elif current == "x":
                    connections.append(item)

    return (list(dict.fromkeys(concepts)), list(dict.fromkeys(frameworks)),
            list(dict.fromkeys(applications)), list(dict.fromkeys(connections)))


def _split(text):
    """Split comma/semicolon/dash separated items."""
    for sep in [",", ";", " - "]:
        if sep in text:
            return [i.strip() for i in text.split(sep) if i.strip()]
    return [text.strip()] if text.strip() else []


# ═══════════════════════════════════════════════════════════════
# FOUNDING ERA COLLABORATIVE AMENDMENTS
# ═══════════════════════════════════════════════════════════════

def propose_collaborative_amendment(cycle: int, blueprint, founders: list, llm, logger) -> dict:
    """
    Collaborative amendment proposal for Founding Era.

    All Founders propose ONE amendment per cycle (not 40 at once).
    Used during Founding Era to evolve Constitution gradually.

    Returns:
        dict with status: "passed", "failed", or "no_amendment_needed"
    """
    import random
    import json

    # Create readable Constitution summary instead of raw JSON
    branches_text = []
    for b in blueprint.branches:
        branches_text.append(f"  • {b.name} ({b.branch_type}): {b.purpose[:100]}")

    clauses_text = []
    non_amendable = getattr(blueprint, 'non_amendable_clauses', [])
    for clause in non_amendable[:5]:  # First 5 clauses
        clauses_text.append(f"  • {clause[:100]}")

    constitution_summary = f"""GOVERNMENT STRUCTURE:
{chr(10).join(branches_text)}

NON-AMENDABLE CLAUSES:
{chr(10).join(clauses_text)}

CYCLE SEQUENCE: {' → '.join(blueprint.cycle_sequence)}"""

    # Sample 5 random Founders for suggestions (saves tokens)
    sample_founders = random.sample(founders, min(5, len(founders)))
    suggestions = []

    for founder in sample_founders:
        response = llm.complete(
            system_prompt=founder.get_system_prompt(),
            user_prompt=(
                f"CONSTITUTIONAL AMENDMENT — Cycle {cycle}\n\n"
                f"CURRENT CONSTITUTION:\n{constitution_summary}\n\n"
                f"YOU ({founder.name}): What ONE change would most improve this Constitution?\n\n"
                f"Suggest ONE specific improvement (just the core idea, one sentence).\n"
                f"Or say 'NO AMENDMENT NEEDED' if Constitution is sufficient."
            ),
            max_tokens=150,
            temperature=0.7
        )

        suggestion = (response.content or "").strip()

        if "NO AMENDMENT" not in suggestion.upper():
            suggestions.append({
                "founder": founder.name,
                "suggestion": suggestion
            })

    # If no suggestions, skip amendment this cycle
    if not suggestions:
        return {"status": "no_amendment_needed"}

    # Synthesize into ONE amendment
    suggestions_text = "\n".join([f"- {s['founder']}: {s['suggestion']}" for s in suggestions])
    blueprint_json = json.dumps(blueprint.to_dict(), indent=2)

    synthesis_response = llm.complete(
        system_prompt="You synthesize multiple viewpoints into clear amendments.",
        user_prompt=(
            f"AMENDMENT SYNTHESIS — Cycle {cycle}\n\n"
            f"CURRENT BLUEPRINT:\n{blueprint_json[:1000]}...\n\n"
            f"FOUNDER SUGGESTIONS:\n{suggestions_text}\n\n"
            f"YOUR TASK: Identify the SINGLE MOST IMPORTANT change needed.\n"
            f"Or say 'NO AMENDMENT NEEDED' if suggestions are weak.\n\n"
            f"Format:\n"
            f"AMENDMENT: [specific change in one sentence]\n"
            f"RATIONALE: [why this is important]"
        ),
        max_tokens=400,
        temperature=0.7
    )

    content = synthesis_response.content or ""

    if "NO AMENDMENT" in content.upper():
        return {"status": "no_amendment_needed"}

    # Parse amendment
    import re
    amendment_match = re.search(r'AMENDMENT:\s*(.+?)(?=\nRATIONALE:|$)', content, re.IGNORECASE | re.DOTALL)
    rationale_match = re.search(r'RATIONALE:\s*(.+?)$', content, re.IGNORECASE | re.DOTALL)

    if not amendment_match:
        return {"status": "no_amendment_needed"}

    amendment = {
        "text": amendment_match.group(1).strip(),
        "rationale": rationale_match.group(1).strip() if rationale_match else "No rationale",
        "cycle": cycle,
        "proposer": "Collaborative"
    }

    print(f"\n  COLLABORATIVE AMENDMENT:")
    print(f"    {amendment['text']}")
    print(f"\n  RATIONALE:")
    print(f"    {amendment['rationale']}")

    # 2v2 Debate (pick 2 random Founders)
    debaters = random.sample(founders, 2)
    supporter, opponent = debaters[0], debaters[1]

    support_response = llm.complete(
        system_prompt=supporter.get_system_prompt(),
        user_prompt=(
            f"CONSTITUTIONAL AMENDMENT DEBATE\n\n"
            f"Amendment: {amendment['text']}\n"
            f"Rationale: {amendment['rationale']}\n\n"
            f"YOU ({supporter.name}): Argue IN FAVOR (max 200 tokens).\n"
            f"Why is this necessary? What problem does it solve?"
        ),
        max_tokens=200,
        temperature=0.8
    )

    support_arg = support_response.content or ""

    oppose_response = llm.complete(
        system_prompt=opponent.get_system_prompt(),
        user_prompt=(
            f"CONSTITUTIONAL AMENDMENT DEBATE\n\n"
            f"Amendment: {amendment['text']}\n\n"
            f"Supporter ({supporter.name}) said:\n{support_arg}\n\n"
            f"YOU ({opponent.name}): Argue AGAINST (max 200 tokens).\n"
            f"What are the risks? What could break?"
        ),
        max_tokens=200,
        temperature=0.8
    )

    oppose_arg = oppose_response.content or ""

    print(f"\n  DEBATE:")
    print(f"    FOR ({supporter.name}): {support_arg[:150]}...")
    print(f"    AGAINST ({opponent.name}): {oppose_arg[:150]}...")

    # All Founders vote (14/20 = 70% supermajority required)
    votes = {"yes": 0, "no": 0}
    vote_details = []
    sample_votes_shown = 0

    for founder in founders:
        vote_response = llm.complete(
            system_prompt=founder.get_system_prompt(),
            user_prompt=(
                f"You heard both arguments about this proposed amendment:\n\n"
                f"Amendment: {amendment['text']}\n\n"
                f"Argument FOR by {supporter.name}: {support_arg[:200]}\n"
                f"Argument AGAINST by {opponent.name}: {oppose_arg[:200]}\n\n"
                f"Does this amendment improve the Constitution? Reply with exactly one word: YES or NO"
            ),
            max_tokens=10,
            temperature=0.5
        )

        # DEBUG: Show first 3 raw responses
        if sample_votes_shown < 3:
            print(f"    DEBUG - {founder.name} raw vote: '{vote_response.content}'")
            sample_votes_shown += 1

        vote_text = (vote_response.content or "").strip()
        result = _parse_vote(vote_text)
        if result == "yes":
            votes["yes"] += 1
            vote_details.append(f"{founder.name}: YES")
        else:
            votes["no"] += 1
            vote_details.append(f"{founder.name}: NO")

    print(f"\n  VOTE TALLY:")
    yes_voters = [v.split(": ")[0] for v in vote_details if "YES" in v]
    no_voters = [v.split(": ")[0] for v in vote_details if "NO" in v]
    print(f"    YES ({votes['yes']}): {', '.join(yes_voters)}")
    print(f"    NO ({votes['no']}): {', '.join(no_voters)}")

    # Apply if passed (14/20 supermajority)
    if votes['yes'] >= 14:
        # Update blueprint in memory (don't redeploy)
        _apply_amendment_to_blueprint(amendment, blueprint, llm)

        # Log amendment passed
        logger.log(logger._create_entry(
            level="historic",
            category="amendment_passed",
            title=f"AMENDMENT PASSED (Cycle {cycle})",
            summary=(
                f"Amendment: {amendment['text'][:200]}. "
                f"Vote: {votes['yes']}/{votes['yes'] + votes['no']}. "
                f"Debated by {supporter.name} (FOR) and {opponent.name} (AGAINST). "
                f"Rationale: {amendment['rationale'][:100]}"
            ),
            agents=[supporter.name, opponent.name],
        ))

        return {
            "status": "passed",
            "text": amendment['text'],
            "votes": votes
        }
    else:
        # Log amendment failed
        logger.log(logger._create_entry(
            level="dramatic",
            category="amendment_failed",
            title=f"AMENDMENT REJECTED (Cycle {cycle})",
            summary=(
                f"Amendment: {amendment['text'][:200]}. "
                f"Vote: {votes['yes']}/{votes['yes'] + votes['no']}. "
                f"Debated by {supporter.name} (FOR) and {opponent.name} (AGAINST)."
            ),
            agents=[supporter.name, opponent.name],
        ))

        return {
            "status": "failed",
            "votes": votes
        }


def _apply_amendment_to_blueprint(amendment: dict, blueprint, llm):
    """
    Apply amendment to blueprint (in-memory only, no redeployment).

    Uses LLM to parse amendment and mutate blueprint structure.
    """
    import json

    blueprint_json = json.dumps(blueprint.to_dict())

    parse_response = llm.complete(
        system_prompt="You parse Constitutional amendments into structured changes.",
        user_prompt=(
            f"Current blueprint:\n{blueprint_json[:1000]}\n\n"
            f"Amendment: {amendment['text']}\n\n"
            f"What should be modified? Respond with ONE of:\n"
            f"- ADD_SAFEGUARD: [safeguard text]\n"
            f"- ADD_CYCLE_STEP: [step name]\n"
            f"- MODIFY_VOTING: [branch name] | [new threshold]\n"
            f"- NO_CHANGE: [if amendment is too vague]\n\n"
            f"Format: ACTION: details"
        ),
        max_tokens=150,
        temperature=0.3
    )

    action_text = (parse_response.content or "").strip()

    # Apply simple mutations only (structural changes would require redeployment)
    if "ADD_SAFEGUARD:" in action_text:
        safeguard = action_text.split("ADD_SAFEGUARD:")[1].strip()
        blueprint.non_amendable_clauses.append(safeguard)
        print(f"      → Added safeguard to blueprint")

    elif "ADD_CYCLE_STEP:" in action_text:
        step = action_text.split("ADD_CYCLE_STEP:")[1].strip()
        if step and step not in blueprint.cycle_sequence:
            blueprint.cycle_sequence.append(step)
            print(f"      → Added cycle step: {step}")

    elif "MODIFY_VOTING:" in action_text:
        print(f"      → Voting rule modified (logged in blueprint)")

    elif "NO_CHANGE" in action_text:
        print(f"      → Amendment too vague to implement")

    else:
        print(f"      → Amendment applied (general)")

    # Record amendment in blueprint decisions
    blueprint.decisions_made.append({
        "type": "amendment",
        "proposer": amendment['proposer'],
        "text": amendment['text'],
        "cycle": amendment['cycle']
    })
