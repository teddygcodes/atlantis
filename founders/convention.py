"""
Atlantis V2 — Founding Period (Phase 0)
========================================
20 Founders research freely for N cycles.
No structural validation. No vote. No blueprint.
All output deposited as 'founding' status Archive entries.
Returns stored FounderProfile list for Tier 2/3 validation panels.

V2 has no ConstitutionalConvention. CONSTITUTION.md is loaded from file
by core/engine.py and passed as plain text to agents that need it.
"""

import json
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Optional

from agents.base import AgentConfig, FounderProfile, get_all_founder_profiles
from core.models import ModelRouter
from core.persistence import PersistenceLayer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FoundingPeriod:
    """
    Phase 0: 20 Founders research for N cycles.
    Free-form deposits to Archive. No structural validation.
    Returns stored FounderProfile list for Tier 2/3 panels.
    """

    def __init__(
        self,
        founder_configs: List[AgentConfig],
        db: PersistenceLayer,
        models: ModelRouter,
        config: dict,
    ):
        self.founder_configs = founder_configs
        self.db = db
        self.models = models
        self.config = config

    def run(self, num_cycles: int = 3) -> List[FounderProfile]:
        """
        Run Phase 0 research cycles.
        Each Founder researches in their top 2 expertise domains each cycle.
        Returns FounderProfile list (used for Tier 2/3 panels).
        """
        print(f"\n[Phase 0] Founding Period — {len(self.founder_configs)} Founders × {num_cycles} cycles")

        total_entries = 0

        for cycle in range(1, num_cycles + 1):
            print(f"\n  Research Cycle {cycle}/{num_cycles}")
            for fc in self.founder_configs:
                # Research in top 2 expertise domains
                domains = fc.knowledge_domains[:2] if fc.knowledge_domains else ["general"]
                for domain in domains:
                    entry_count = self._research_and_deposit(fc, domain, cycle)
                    total_entries += entry_count

        print(f"\n  Phase 0 complete. {total_entries} founding entries deposited.")

        profiles = get_all_founder_profiles()
        print(f"  {len(profiles)} Founder profiles stored for Tier 2/3 panels.")
        return profiles

    def _research_and_deposit(
        self, fc: AgentConfig, domain: str, cycle: int
    ) -> int:
        """
        Single Founder researches one domain.
        Deposits as founding Archive entry. Returns 1.
        """
        system_prompt = (
            f"You are {fc.name}. {fc.mandate}\n\n"
            f"Your personality: {fc.personality}\n\n"
            f"This is Phase 0 — free research before adversarial governance begins. "
            f"Write clearly and substantively. Your findings become the Archive's foundation."
        )

        user_prompt = (
            f"Research cycle {cycle}. Domain: {domain}.\n\n"
            f"Produce your most important findings in this domain as free-form text. "
            f"Be substantive — what do you know, what have you observed, what principles apply?\n\n"
            f"No required format. Write as you see fit."
        )

        try:
            response = self.models.complete(
                task_type="researcher_claims",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800,
            )
            raw_text = response.content or ""
        except Exception as e:
            print(f"    [!] {fc.name} / {domain}: LLM error — {e}")
            raw_text = f"[Error during research cycle {cycle}]"

        display_id = self.db.next_display_id()
        entry = {
            "entry_id": str(uuid4()),
            "display_id": display_id,
            "entry_type": "claim",
            "source_state": "Founding Era",
            "source_entity": fc.name,
            "cycle_created": cycle,
            "status": "founding",
            "claim_type": "discovery",
            "position": f"{fc.name} on {domain} (cycle {cycle})",
            "raw_claim_text": raw_text,
            "conclusion": "",
            "keywords": [domain],
            "reasoning_chain": [],
            "citations": [],
            "referenced_by": [],
            "stability_score": 1,
            "tokens_earned": 0,
            "created_at": _now(),
        }

        try:
            self.db.save_archive_entry(entry)
            print(f"    {fc.name} [{domain}] → {display_id}")
        except Exception as e:
            print(f"    [!] Failed to save entry for {fc.name}: {e}")

        return 1
