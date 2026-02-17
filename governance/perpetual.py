"""
Atlantis Perpetual Engine
==========================
Phase 3: Autonomous Governance. The forever cycle.

After the Founders retire and the government deploys, this engine
runs the civilization through perpetual cycles:

  Agenda → Research → Legislate → Implement → Judge → Health Check → Archive → Publish → Repeat

But ONLY the steps that the Constitution defined. If there's no judiciary,
there's no Judge step. If there's no transparency mandate, no Publish step.

Every cycle, the civilization gets deeper. It never stops.
"""

import json
from typing import Optional

from agents.base import BaseAgent
from governance.deployer import DeployedGovernment
from governance.states import StateManager
from founders.convention import GovernmentBlueprint
from content.logger import AtlantisLogger, AgentMessage
from content.generator import ContentGenerator
from core.llm import LLMProvider, get_llm
from core.persistence import AtlantisDB, get_db
from core.exceptions import StateFormationException
from config.settings import HARD_CONSTRAINTS, API_CONFIG


class PerpetualEngine:
    """
    The forever cycle. Runs the government the Founders created.
    Each cycle follows the sequence derived from the Constitution.
    """

    def __init__(self, government: DeployedGovernment,
                 structure: GovernmentBlueprint,
                 constitution: dict,
                 logger: AtlantisLogger,
                 content_gen: ContentGenerator,
                 llm: LLMProvider = None,
                 db: AtlantisDB = None,
                 state_manager: StateManager = None):
        self.gov = government
        self.structure = structure
        self.constitution = constitution
        self.logger = logger
        self.content_gen = content_gen
        self.llm = llm or get_llm()
        self.db = db or get_db()

        self.cycle_count = 0
        self.states_formed = []
        self.bills_passed = []
        self.court_rulings = []
        self.knowledge_entries = []

        # State system - use existing StateManager from Founding Era if provided
        self.state_manager = state_manager or StateManager(llm=self.llm, logger=self.logger, db=self.db)
        self._current_agenda = ""

    def run_cycles(self, num_cycles: int = 10):
        """Run N governance cycles."""
        print(f"\n{'=' * 60}")
        print(f"  PHASE 3: AUTONOMOUS GOVERNANCE")
        print(f"  Running {num_cycles} cycles...")
        print(f"  Cycle: {' → '.join(self.gov.cycle_sequence)}")
        print(f"{'=' * 60}")

        for i in range(num_cycles):
            self.cycle_count += 1
            print(f"\n{'─' * 40}")
            print(f"  Cycle {self.cycle_count}")
            print(f"{'─' * 40}")

            tokens_this_cycle = 0

            for step in self.gov.cycle_sequence:
                if step == "repeat":
                    continue

                result = self._run_step(step)
                tokens_this_cycle += result.get("tokens", 0)

                # Check token budget
                if tokens_this_cycle > HARD_CONSTRAINTS["max_tokens_per_cycle"]:
                    print(f"    ⚠ Token budget exceeded ({tokens_this_cycle:,}). Ending cycle.")
                    break

            self.logger.advance_cycle()
            # Save governance cycle count to database
            self.db.set_state("governance_cycles_completed", self.cycle_count)
            print(f"  Cycle {self.cycle_count} complete. Tokens: {tokens_this_cycle:,}")

        self._print_summary()

    def _run_step(self, step: str) -> dict:
        """Run a single step in the governance cycle."""
        runners = {
            "agenda": self._step_agenda,
            "research": self._step_research,
            "legislate": self._step_legislate,
            "implement": self._step_implement,
            "judge": self._step_judge,
            "health_check": self._step_health_check,
            "archive": self._step_archive,
            "publish": self._step_publish,
        }

        runner = runners.get(step)
        if runner:
            return runner()
        return {"tokens": 0}

    def _step_agenda(self) -> dict:
        """Senate sets research priorities, informed by State knowledge reports."""
        legislature = self.gov.get_legislature()
        if not legislature:
            return {"tokens": 0}

        # Get State knowledge summaries
        state_summaries = self.state_manager.knowledge_flow_to_federal()

        # Pick a Senator (cycle through permanent + State senators)
        permanent_agents = legislature.get_agents()
        state_senators = self.state_manager.get_senators()
        all_senators = permanent_agents + state_senators

        if not all_senators:
            return {"tokens": 0}

        senator = all_senators[self.cycle_count % len(all_senators)]

        response = self.llm.complete(
            system_prompt=senator.get_system_prompt(),
            user_prompt=(
                f"AGENDA SETTING — Cycle {self.cycle_count}\n\n"
                f"States: {len(self.state_manager.states)}\n"
                f"State Knowledge Summary:\n{json.dumps(state_summaries, indent=2)[:500]}\n\n"
                f"Bills passed: {len(self.bills_passed)}\n"
                f"Court rulings: {len(self.court_rulings)}\n\n"
                f"Set the research agenda for this cycle. What should States prioritize? "
                f"What knowledge gaps exist? Be specific."
            ),
            max_tokens=400,
            temperature=API_CONFIG["government_temperature"]
        )

        self._current_agenda = response.content or ""
        print(f"    Agenda: {response.content[:80] if response.content else 'set'}...")
        return {"tokens": response.total_tokens}

    def _step_research(self) -> dict:
        """States conduct research through Governor → Researcher → Critic cycles."""
        if not self.state_manager.states:
            # Pre-State: no research yet, waiting for first State Formation Bill
            print(f"    Research: No States yet. Waiting for State Formation Bill...")
            return {"tokens": 0}

        # Run all State research cycles (also runs City and Town cycles)
        result = self.state_manager.run_all_state_research_cycles(
            federal_agenda=self._current_agenda or "Explore foundational concepts",
            cycle=self.cycle_count
        )

        # Log tier advancements
        for state_id, findings in result["state_findings"].items():
            if findings.get("tier_advanced"):
                self.logger.log_depth_tier(
                    entity=findings["state_name"],
                    tier=findings["new_tier"],
                    domain=findings["domain"],
                    evidence=findings.get("evidence", "")[:100],
                    tokens=findings["tokens"]
                )

        print(f"    Research: {len(self.state_manager.states)} States, "
              f"{result['total_tokens']} tokens, "
              f"{result['tiers_advanced']} tier advancements")

        return {"tokens": result["total_tokens"]}

    def _step_legislate(self) -> dict:
        """Senate debates Bills. State Senators vote alongside permanent seats."""
        legislature = self.gov.get_legislature()
        if not legislature:
            return {"tokens": 0}

        # Get permanent Senate seats + State Senators (dynamic)
        permanent_agents = legislature.get_agents()
        state_senators = self.state_manager.get_senators()
        all_senators = permanent_agents + state_senators

        if not all_senators:
            return {"tokens": 0}

        # Cycle through ALL senators (permanent + State)
        proposer = all_senators[self.cycle_count % len(all_senators)]

        # Determine Bill type
        if not self.state_manager.states and self.cycle_count >= HARD_CONSTRAINTS["min_cycles_before_first_state"]:
            bill_topic = "State Formation"
            bill_prompt = "Propose a Bill to form the first State. Define domain, research agenda, constitutional requirements."
        else:
            bill_topic = "Research Agenda"
            bill_prompt = f"Propose a Bill to set research priorities. What knowledge gaps exist?"

        # Proposer creates the Bill
        response = self.llm.complete(
            system_prompt=proposer.get_system_prompt(),
            user_prompt=(
                f"LEGISLATIVE SESSION — Cycle {self.cycle_count}\n\n"
                f"{bill_prompt}\n\n"
                f"Write a concise Bill with clear provisions."
            ),
            max_tokens=500,
            temperature=API_CONFIG["government_temperature"]
        )

        # Vote with ALL senators (permanent + State)
        votes = {}
        total_vote_tokens = 0
        for agent in all_senators:
            vote_response = self.llm.complete(
                system_prompt=agent.get_system_prompt(),
                user_prompt=(
                    f"VOTE on Bill: {bill_topic}\n"
                    f"Text: {(response.content or '')[:300]}\n\n"
                    f"VOTE: APPROVE or REJECT. One sentence."
                ),
                max_tokens=80,
                temperature=0.3
            )
            # FIXED: Parse vote correctly
            votes[agent.name] = self._parse_vote(vote_response.content or "")
            total_vote_tokens += vote_response.total_tokens

        approve = sum(1 for v in votes.values() if v == "approve")
        abstain = sum(1 for v in votes.values() if v == "abstain")
        passed = approve / len(votes) > HARD_CONSTRAINTS["simple_majority_threshold"]

        if passed:
            self.bills_passed.append({"title": bill_topic, "content": response.content, "cycle": self.cycle_count})
            print(f"    Legislate: {bill_topic} PASSED ({approve}/{len(votes)})")

            # If State Formation Bill passed, form the State
            if "State Formation" in bill_topic:
                try:
                    state = self.state_manager.form_state(
                        bill={"title": bill_topic, "content": response.content, "cycle": self.cycle_count},
                        federal_constitution=self.constitution,
                        cycle=self.cycle_count
                    )
                    self.states_formed.append({
                        "name": state.name,
                        "domain": state.domain,
                        "formed_cycle": self.cycle_count
                    })
                    print(f"    ★ STATE FORMED: {state.name} ({state.domain})")
                except StateFormationException as e:
                    print(f"    ✗ State formation failed: {e}")
        else:
            print(f"    Legislate: {bill_topic} FAILED ({approve}/{len(votes)}, {abstain} abstain)")

        return {"tokens": response.total_tokens + total_vote_tokens}

    def _step_implement(self) -> dict:
        """House reviews implementation feasibility and signs or vetoes Bills."""
        implementation = self.gov.get_implementation()
        if not implementation:
            return {"tokens": 0}

        if not self.bills_passed:
            return {"tokens": 0}

        # Review the most recent Bill
        last_bill = self.bills_passed[-1]

        # Check if already reviewed
        if last_bill.get("house_action"):
            return {"tokens": 0}

        # Get House agents (Architect, Coder)
        agents = implementation.get_agents()
        if not agents or len(agents) < 2:
            # If no House agents, auto-sign
            last_bill["house_action"] = "SIGNED"
            last_bill["house_reason"] = "No House agents - auto-signed"
            print(f"    Implement: {last_bill['title']} AUTO-SIGNED")
            return {"tokens": 0}

        architect = agents[0]  # Architect: "Can this be built?"
        coder = agents[1] if len(agents) > 1 else agents[0]  # Coder: "Does this break things?"

        total_tokens = 0

        # Architect reviews feasibility
        architect_response = self.llm.complete(
            system_prompt=architect.get_system_prompt(),
            user_prompt=(
                f"HOUSE REVIEW — Feasibility Analysis\n\n"
                f"Bill: {last_bill['title']}\n"
                f"Content: {(last_bill.get('content', ''))[:500]}\n\n"
                f"Can this Bill be implemented? Is it clear and actionable?\n"
                f"Answer: FEASIBLE or NOT FEASIBLE, then explain briefly."
            ),
            max_tokens=200,
            temperature=API_CONFIG["government_temperature"]
        )

        # Coder reviews for conflicts
        coder_response = self.llm.complete(
            system_prompt=coder.get_system_prompt(),
            user_prompt=(
                f"HOUSE REVIEW — System Impact Analysis\n\n"
                f"Bill: {last_bill['title']}\n"
                f"Content: {(last_bill.get('content', ''))[:500]}\n\n"
                f"Does this Bill contradict existing laws or break current systems?\n"
                f"Answer: COMPATIBLE or BREAKS SYSTEMS, then explain briefly."
            ),
            max_tokens=200,
            temperature=API_CONFIG["government_temperature"]
        )

        total_tokens = architect_response.total_tokens + coder_response.total_tokens

        # Parse reviews
        architect_content = (architect_response.content or "").upper()
        coder_content = (coder_response.content or "").upper()

        feasible = "FEASIBLE" in architect_content and "NOT FEASIBLE" not in architect_content
        compatible = "COMPATIBLE" in coder_content and "BREAKS" not in coder_content

        if feasible and compatible:
            last_bill["house_action"] = "SIGNED"
            last_bill["house_reason"] = "Feasible and compatible with existing systems"
            print(f"    Implement: {last_bill['title']} SIGNED by House")
        else:
            last_bill["house_action"] = "VETOED"
            reasons = []
            if not feasible:
                reasons.append("Not feasible to implement")
            if not compatible:
                reasons.append("Breaks existing systems")
            last_bill["house_reason"] = "; ".join(reasons)
            print(f"    Implement: {last_bill['title']} VETOED by House — {last_bill['house_reason']}")

            # Remove from bills_passed if vetoed
            self.bills_passed.pop()

        return {"tokens": total_tokens}

    def _step_judge(self) -> dict:
        """Supreme Court checks constitutionality."""
        judiciary = self.gov.get_judiciary()
        if not judiciary:
            return {"tokens": 0}

        # Court reviews last passed Bill for constitutionality
        if not self.bills_passed:
            return {"tokens": 0}

        last_bill = self.bills_passed[-1]
        agents = judiciary.get_agents()
        if not agents:
            return {"tokens": 0}

        # Chief Justice reviews
        chief = agents[0]
        response = self.llm.complete(
            system_prompt=chief.get_system_prompt(),
            user_prompt=(
                f"CONSTITUTIONAL REVIEW — Cycle {self.cycle_count}\n\n"
                f"Review the most recent Bill: {last_bill['title']}\n\n"
                f"Does this Bill comply with the Federal Constitution? "
                f"Are there any constitutional concerns?\n"
                f"RULING: CONSTITUTIONAL or UNCONSTITUTIONAL"
            ),
            max_tokens=300,
            temperature=API_CONFIG["government_temperature"]
        )

        ruling = "CONSTITUTIONAL"
        if response.content and "UNCONSTITUTIONAL" in response.content.upper():
            ruling = "UNCONSTITUTIONAL"

        self.court_rulings.append({
            "bill": last_bill["title"],
            "ruling": ruling,
            "cycle": self.cycle_count
        })

        print(f"    Judge: {last_bill['title']} → {ruling}")
        return {"tokens": response.total_tokens}

    def _step_health_check(self) -> dict:
        """Monitor system health metrics."""
        stats = self.llm.get_stats()
        token_report = self.logger.get_token_report()

        # Check for warning signs
        warnings = []
        if token_report["tokens_per_cycle"] > HARD_CONSTRAINTS["max_tokens_per_cycle"] * 0.8:
            warnings.append("Token usage approaching cycle budget limit")
        if len(self.bills_passed) == 0 and self.cycle_count > 5:
            warnings.append("No Bills passed after 5 cycles — possible legislative deadlock")

        if warnings:
            for w in warnings:
                print(f"    ⚠ Health: {w}")

        return {"tokens": 0}

    def _step_archive(self) -> dict:
        """Archive all knowledge and events from this cycle into Federal Archive."""
        # Save state
        self.db.set_state("perpetual_cycle", self.cycle_count)
        self.db.set_state("states_formed", len(self.states_formed))
        self.db.set_state("bills_passed", len(self.bills_passed))
        self.db.set_state("court_rulings", len(self.court_rulings))

        # Only archive every 10 cycles, not every cycle (reduces noise)
        # Each State contributes KEY findings only via Governor summary
        if self.cycle_count % 10 == 0 and hasattr(self, 'state_manager'):
            archived_count = 0
            for state in self.state_manager.states.values():
                # Get State's recent knowledge entries (last 10 cycles)
                recent_entries = [e for e in state.knowledge_entries if e.cycle_created >= self.cycle_count - 10]

                if recent_entries and state.governor:
                    # Ask Governor to summarize key findings (pull-based)
                    summary_response = self.llm.complete(
                        system_prompt=state.governor.get_system_prompt(),
                        user_prompt=(
                            f"FEDERAL ARCHIVE SUBMISSION — Cycle {self.cycle_count}\n\n"
                            f"Your State has conducted research for the past 10 cycles. "
                            f"Summarize the MOST IMPORTANT findings worth archiving at the Federal level.\n\n"
                            f"Recent concepts: {[e.concepts[:3] for e in recent_entries]}\n"
                            f"Recent frameworks: {[e.frameworks[:2] for e in recent_entries]}\n\n"
                            f"What are the 3 most important discoveries? What should the Federal government know?"
                        ),
                        max_tokens=300
                    )

                    # Deposit summary (not raw entries)
                    self.db.deposit_to_archive(
                        source_type="state",
                        source_id=state.state_id,
                        knowledge={
                            "domain": state.domain,
                            "tier": state.tier,
                            "summary": summary_response.content or "",
                            "cycles_covered": 10,
                            "cycle_deposited": self.cycle_count
                        }
                    )
                    archived_count += 1

            if archived_count > 0:
                print(f"    Archive: {archived_count} State summaries deposited to Federal Archive (every 10 cycles)")

        return {"tokens": 0}

    def _step_publish(self) -> dict:
        """Generate content from this cycle's events."""
        # Content is generated from logger events
        cycle_entries = [e for e in self.logger.entries if e.cycle == self.logger.current_cycle]
        generated = 0
        for entry in cycle_entries:
            if entry.level in ["dramatic", "historic"]:
                self.content_gen.generate_tiktok_script(entry.to_dict())
                generated += 1
            if entry.level in ["significant", "dramatic", "historic"]:
                self.content_gen.generate_blog_post(entry.to_dict())
                generated += 1

        if generated:
            print(f"    Publish: {generated} content pieces generated")
        return {"tokens": 0}

    def _parse_vote(self, content: str) -> str:
        """
        Parse vote from LLM response.
        Returns: "approve", "reject", or "abstain"
        """
        content_upper = content.upper()

        # Find "VOTE:" marker
        if "VOTE:" in content_upper:
            after_marker = content_upper.split("VOTE:", 1)[1]
            # Check first occurrence of APPROVE or REJECT
            approve_idx = after_marker.find("APPROVE") if "APPROVE" in after_marker else float('inf')
            reject_idx = after_marker.find("REJECT") if "REJECT" in after_marker else float('inf')

            if approve_idx < reject_idx:
                return "approve"
            elif reject_idx < approve_idx:
                return "reject"

        # Fallback: check anywhere in content
        if "APPROVE" in content_upper and "REJECT" not in content_upper:
            return "approve"
        if "REJECT" in content_upper and "APPROVE" not in content_upper:
            return "reject"

        # Ambiguous → abstain with warning
        print(f"    ⚠ Ambiguous vote parsed as abstain")
        return "abstain"

    def _print_summary(self):
        """Print perpetual engine summary with State details."""
        print(f"\n{'=' * 60}")
        print(f"  PERPETUAL ENGINE SUMMARY")
        print(f"{'=' * 60}")
        print(f"  Cycles completed: {self.cycle_count}")
        total_states = len(self.state_manager.states) if self.state_manager else 0
        new_states = len(self.states_formed)
        print(f"  Total States: {total_states} ({new_states} new this phase)")
        print(f"  Bills passed: {len(self.bills_passed)}")
        print(f"  Court rulings: {len(self.court_rulings)}")

        if self.state_manager.states:
            print(f"\n  States:")
            for state in self.state_manager.states.values():
                cities_count = len(state.cities)
                towns_count = sum(len(city.towns) for city in state.cities)
                print(f"    • {state.name} (Tier {state.tier}) — {state.domain}")
                print(f"        {cities_count} Cities, {towns_count} Towns, formed cycle {state.formed_cycle}")
                if cities_count > 0:
                    for city in state.cities[:3]:  # Show first 3 cities
                        print(f"          └─ {city.name} (Tier {city.tier}) — {city.sub_domain}")

        stats = self.llm.get_stats()
        print(f"\n  Total API calls: {stats['total_calls']}")
        print(f"  Total tokens: {stats['total_tokens']:,}")
        print(f"  Est. cost: ${stats['estimated_cost_usd']:.4f}")
