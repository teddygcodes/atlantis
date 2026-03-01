"""
Atlantis Government Deployer
==============================
Reads the GovernmentBlueprint (built directly by Founder votes)
and deploys the government. No parser. No interpretation.
The blueprint IS the spec.
"""

from agents.base import BaseAgent, AgentConfig, AgentType
from founders.convention import GovernmentBlueprint, BranchBlueprint
from content.logger import AtlantisLogger
from core.llm import LLMProvider, get_llm
from core.persistence import AtlantisDB, get_db
from core.exceptions import BlueprintValidationException


class DeployedBranch:
    def __init__(self, blueprint, agents):
        self.blueprint = blueprint
        self.agents = {a.name: a for a in agents}
        self.name = blueprint.name
        self.branch_type = blueprint.branch_type
        self.powers = blueprint.powers
        self.constraints = blueprint.constraints

    def get_agents(self):
        return list(self.agents.values())


class DeployedGovernment:
    def __init__(self):
        self.branches = {}
        self.all_agents = {}
        self.processes = {}
        self.non_amendable_clauses = []
        self.cycle_sequence = []

    def has_legislature(self):
        return "legislative" in [b.branch_type for b in self.branches.values()]

    def has_judiciary(self):
        return "judicial" in [b.branch_type for b in self.branches.values()]

    def has_implementation(self):
        return "implementation" in [b.branch_type for b in self.branches.values()]

    def get_legislature(self):
        for b in self.branches.values():
            if b.branch_type == "legislative": return b
        return None

    def get_judiciary(self):
        for b in self.branches.values():
            if b.branch_type == "judicial": return b
        return None

    def get_implementation(self):
        for b in self.branches.values():
            if b.branch_type == "implementation": return b
        return None

    def summary(self):
        lines = ["DEPLOYED GOVERNMENT"]
        lines.append(f"  Branches: {len(self.branches)}")
        for name, branch in self.branches.items():
            agents = ", ".join(branch.agents.keys())
            lines.append(f"    {name} ({branch.branch_type}): [{agents}]")
            for p in branch.powers[:3]:
                lines.append(f"      * {p}")
        lines.append(f"  Total agents: {len(self.all_agents)}")
        lines.append(f"  Non-amendable: {len(self.non_amendable_clauses)}")
        lines.append(f"  Cycle: {' -> '.join(self.cycle_sequence)}")
        return "\n".join(lines)


PERSONALITIES = {
    "WARDEN": "Constitutional guardian. Absolute authority on non-amendable clauses.",
    "Critic": "Skeptical, rigorous. Finds the weakness in every proposal.",
    "Justice Critic": "Sharp, incisive. Writes devastating dissents.",
    "Tester": "Evidence-focused. Rejects claims without proof.",
    "Historian": "Remembers everything. References precedent always.",
    "Justice Historian": "References every past ruling. Maintains consistency.",
    "Debugger": "Thinks in failure modes. Asks 'what breaks?' first.",
    "Architect": "Translates legislation into executable specs.",
    "Coder": "Validates plans work. Thinks in edge cases.",
}


class GovernmentDeployer:
    """Deploy the government from the Founder-built blueprint."""

    def __init__(self, blueprint, logger, llm=None, db=None):
        self.blueprint = blueprint
        self.logger = logger
        self.llm = llm or get_llm()
        self.db = db or get_db()

    def deploy(self):
        # VALIDATE BLUEPRINT FIRST
        validation = self._validate_blueprint(self.blueprint)
        if not validation["valid"]:
            print(f"\n  ✗ BLUEPRINT VALIDATION FAILED:")
            for error in validation["errors"]:
                print(f"      • {error}")
            raise BlueprintValidationException(f"Blueprint validation failed: {'; '.join(validation['errors'])}")

        gov = DeployedGovernment()

        print(f"\n{'=' * 60}")
        print(f"  PHASE 2: GOVERNMENT DEPLOYMENT")
        print(f"  Deploying what the Founders built...")
        print(f"{'=' * 60}")

        for branch_bp in self.blueprint.branches:
            deployed = self._deploy_branch(branch_bp)
            gov.branches[branch_bp.name] = deployed
            for agent in deployed.get_agents():
                gov.all_agents[agent.name] = agent
                self.db.save_agent(agent)

            print(f"  > {branch_bp.name} ({branch_bp.branch_type}): "
                  f"{len(deployed.agents)} agents")
            for p in branch_bp.powers[:3]:
                print(f"      * {p}")

        gov.non_amendable_clauses = self.blueprint.non_amendable_clauses
        if gov.non_amendable_clauses:
            print(f"\n  Non-amendable clauses: {len(gov.non_amendable_clauses)}")
            for c in gov.non_amendable_clauses[:3]:
                print(f"    LOCKED: {c[:70]}")

        gov.cycle_sequence = self.blueprint.cycle_sequence
        if gov.cycle_sequence:
            print(f"\n  Cycle: {' -> '.join(gov.cycle_sequence)}")

        gov.processes = {
            "legislative": self.blueprint.has_branch("legislative"),
            "judicial": self.blueprint.has_branch("judicial"),
            "implementation": self.blueprint.has_branch("implementation"),
            "amendment": bool(self.blueprint.amendment_rules),
            "state_formation": bool(self.blueprint.state_formation_rules),
            "content_pipeline": bool(self.blueprint.content_pipeline),
            "health_monitoring": bool(self.blueprint.health_monitoring),
        }

        self.db.set_state("government_deployed", True)
        self.db.set_state("governance_blueprint", self.blueprint.to_dict())
        self.db.set_state("cycle_sequence", gov.cycle_sequence)

        # Log deployment as historic event
        self.logger.log(self.logger._create_entry(
            level="historic", category="government_deployed",
            title="GOVERNMENT DEPLOYED FROM FOUNDER BLUEPRINT",
            summary=(f"{len(gov.branches)} branches, {len(gov.all_agents)} agents, "
                     f"{len(gov.non_amendable_clauses)} non-amendable clauses"),
            agents=list(gov.all_agents.keys()),
        ))

        print(f"\n  Deployment complete. {len(gov.all_agents)} agents governing.\n")
        return gov

    def _validate_blueprint(self, blueprint: GovernmentBlueprint) -> dict:
        """Validate blueprint meets minimum requirements before deployment."""
        errors = []

        # At least 1 branch required
        if not blueprint.branches or len(blueprint.branches) == 0:
            errors.append("No branches defined in blueprint")

        # Every branch needs seats
        for branch in blueprint.branches:
            if not branch.seats or len(branch.seats) == 0:
                errors.append(f"Branch '{branch.name}' has no seats defined")

        # Cycle sequence must exist and include 'research'
        if not blueprint.cycle_sequence:
            errors.append("No cycle sequence defined")
        elif "research" not in blueprint.cycle_sequence:
            errors.append("Cycle sequence missing 'research' step (required for State system)")

        # At least 1 non-amendable clause recommended
        if not blueprint.non_amendable_clauses or len(blueprint.non_amendable_clauses) == 0:
            errors.append("WARNING: No non-amendable clauses defined (not fatal, but recommended)")

        return {
            "valid": len([e for e in errors if not e.startswith("WARNING")]) == 0,
            "errors": errors
        }

    def _deploy_branch(self, branch_bp):
        agents = []
        for seat in branch_bp.seats:
            name = seat["name"]
            if name.startswith("State Representative"):
                continue  # Dynamic seats added later

            config = AgentConfig(
                id=f"gov_{branch_bp.branch_type}_{name.lower().replace(' ', '_')}",
                name=name,
                agent_type=AgentType.GOVERNMENT.value,
                role=f"{name} - {branch_bp.name}",
                mandate=(
                    f"{seat.get('mandate', 'Serve faithfully.')} "
                    f"Authority from {branch_bp.name}. "
                    f"Powers: {', '.join(branch_bp.powers[:3]) if branch_bp.powers else 'general'}."
                ),
                personality=PERSONALITIES.get(name, "Diligent servant of the Constitution."),
                constraints=[
                    "Bound by the Federal Constitution as built by the Founders",
                    *branch_bp.constraints[:2],
                ],
                max_tokens_per_response=800,
            )
            agents.append(BaseAgent(config))
        return DeployedBranch(branch_bp, agents)
