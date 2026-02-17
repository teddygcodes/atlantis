"""
Atlantis State System
=====================
The knowledge engine. States are self-governing under Federal authority.

States have their own constitutions (must comply with Federal).
Each State gets a Senator who sits in Federal Senate with full State knowledge.
Knowledge flows: Town → City → State → Federal Archive.
"""

import json
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime

from agents.base import BaseAgent, AgentType, AgentConfig
from core.llm import LLMProvider
from core.persistence import AtlantisDB
from content.logger import AtlantisLogger
from config.settings import HARD_CONSTRAINTS, DEPTH_TIERS
from core.exceptions import ConstitutionalViolationException, StateFormationException


def _extract_items(raw_text):
    """Extract items from a section that might be comma-separated, bulleted, or numbered."""
    items = []

    # First try: split by lines and look for bullets/numbers
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Strip bullet/number prefixes
        if line.startswith(('- ', '* ', '• ')):
            item = line.lstrip('-*• ').strip()
            if item and len(item) > 2:
                items.append(item[:100])
        elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            item = line.lstrip('0123456789.): ').strip()
            if item and len(item) > 2:
                items.append(item[:100])
        elif ',' in line:
            # Comma-separated on this line
            for part in line.split(','):
                part = part.strip()
                if part and len(part) > 2:
                    items.append(part[:100])
        elif line and len(line) > 2:
            items.append(line[:100])

    # Deduplicate preserving order
    return list(dict.fromkeys(items))


def _extract_json(raw: str) -> dict:
    """Depth-tracking JSON extractor. Handles nested braces correctly."""
    start = raw.find('{')
    if start == -1:
        raise ValueError("No JSON found")
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == '{':
            depth += 1
        elif raw[i] == '}':
            depth -= 1
        if depth == 0:
            return json.loads(raw[start:i+1])
    raise ValueError("Unmatched braces")


@dataclass
class StateConstitution:
    """A State's constitution - must comply with Federal Constitution."""
    state_name: str
    domain: str
    knowledge_areas: List[str]
    governance_principles: List[str]
    research_methodology: str
    federal_compliance_check: Dict
    ratified_at_cycle: int
    version: int = 1

    def to_dict(self):
        return {
            "state_name": self.state_name,
            "domain": self.domain,
            "knowledge_areas": self.knowledge_areas,
            "governance_principles": self.governance_principles,
            "research_methodology": self.research_methodology,
            "federal_compliance_check": self.federal_compliance_check,
            "ratified_at_cycle": self.ratified_at_cycle,
            "version": self.version
        }


@dataclass
class CityCharter:
    """City charter - must comply with State AND Federal."""
    city_name: str
    parent_state_id: str
    sub_domain: str
    specialization: str
    state_compliance_check: Dict
    federal_compliance_check: Dict
    ratified_at_cycle: int

    def to_dict(self):
        return {
            "city_name": self.city_name,
            "parent_state_id": self.parent_state_id,
            "sub_domain": self.sub_domain,
            "specialization": self.specialization,
            "state_compliance_check": self.state_compliance_check,
            "federal_compliance_check": self.federal_compliance_check,
            "ratified_at_cycle": self.ratified_at_cycle
        }


@dataclass
class TownCharter:
    """Town charter - must comply with City, State, AND Federal."""
    town_name: str
    parent_city_id: str
    parent_state_id: str
    hyper_specific_topic: str
    charter_text: str
    city_compliance_check: Dict
    state_compliance_check: Dict
    federal_compliance_check: Dict
    ratified_at_cycle: int

    def to_dict(self):
        return {
            "town_name": self.town_name,
            "parent_city_id": self.parent_city_id,
            "parent_state_id": self.parent_state_id,
            "hyper_specific_topic": self.hyper_specific_topic,
            "charter_text": self.charter_text,
            "city_compliance_check": self.city_compliance_check,
            "state_compliance_check": self.state_compliance_check,
            "federal_compliance_check": self.federal_compliance_check,
            "ratified_at_cycle": self.ratified_at_cycle
        }


@dataclass
class KnowledgeEntry:
    """A single research finding at any tier."""
    entry_id: str
    entity_id: str  # state_id, city_id, or town_id
    entity_type: str  # "state", "city", "town"
    domain: str
    tier: int
    concepts: List[str]
    frameworks: List[str]
    applications: List[str]
    synthesis: str
    evidence: str
    challenged_by: str = ""
    defense: str = ""
    cycle_created: int = 0
    tokens_used: int = 0

    def to_dict(self):
        return {
            "entry_id": self.entry_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "domain": self.domain,
            "tier": self.tier,
            "concepts": self.concepts,
            "frameworks": self.frameworks,
            "applications": self.applications,
            "synthesis": self.synthesis,
            "evidence": self.evidence,
            "challenged_by": self.challenged_by,
            "defense": self.defense,
            "cycle_created": self.cycle_created,
            "tokens_used": self.tokens_used
        }


class Town:
    """A Town with 1 agent: Researcher (Tier 5 specialist)."""

    def __init__(self, town_id: str, name: str, parent_city_id: str,
                 parent_state_id: str, hyper_topic: str, charter: TownCharter):
        self.town_id = town_id
        self.name = name
        self.parent_city_id = parent_city_id
        self.parent_state_id = parent_state_id
        self.hyper_topic = hyper_topic
        self.charter = charter
        self.tier = 0  # Towns start at 0 like all other entities
        self.knowledge_entries: List[KnowledgeEntry] = []

        # 1 agent
        self.researcher: Optional[BaseAgent] = None
        self.parent_city: Optional['City'] = None  # Reference to parent City

    def _build_knowledge_context(self) -> str:
        """Build cumulative knowledge from Town archive + parent City + grandparent State."""
        # Get Town's own knowledge
        if not self.knowledge_entries:
            context = "No prior research yet. This is the first cycle."
        else:
            all_concepts = []
            all_frameworks = []
            all_applications = []

            for entry in self.knowledge_entries:
                all_concepts.extend(entry.concepts)
                all_frameworks.extend(entry.frameworks)
                all_applications.extend(entry.applications)

            all_concepts = list(set(all_concepts))[:20]
            all_frameworks = list(set(all_frameworks))[:15]
            all_applications = list(set(all_applications))[:15]

            context = f"PRIOR KNOWLEDGE (from {len(self.knowledge_entries)} previous cycles):\n\n"
            context += f"Concepts discovered: {', '.join(all_concepts)}\n\n"
            context += f"Frameworks built: {', '.join(all_frameworks)}\n\n"
            context += f"Applications found: {', '.join(all_applications)}\n\n"

        # Add parent City knowledge
        if self.parent_city and hasattr(self.parent_city, 'knowledge_entries'):
            city_concepts = []
            for entry in self.parent_city.knowledge_entries[-5:]:
                city_concepts.extend(entry.concepts)

            if city_concepts:
                context += f"\n\nPARENT CITY KNOWLEDGE ({self.parent_city.name}):\n"
                context += f"Concepts: {', '.join(list(set(city_concepts))[:10])}\n"

        # Add grandparent State knowledge
        if (self.parent_city and hasattr(self.parent_city, 'parent_state') and
            self.parent_city.parent_state and hasattr(self.parent_city.parent_state, 'knowledge_entries')):
            state_frameworks = []
            for entry in self.parent_city.parent_state.knowledge_entries[-5:]:
                state_frameworks.extend(entry.frameworks)

            if state_frameworks:
                context += f"\nGRANDPARENT STATE KNOWLEDGE ({self.parent_city.parent_state.name}):\n"
                context += f"Frameworks: {', '.join(list(set(state_frameworks))[:8])}\n"

        return context

    def query_knowledge(self, topic: str, max_entries: int = 10) -> List[dict]:
        """
        Query Town's knowledge archive for relevant findings on a topic.
        Returns list of relevant knowledge entries.
        """
        relevant = []

        for entry in self.knowledge_entries[-max_entries:]:  # Recent entries
            # Simple relevance check
            topic_lower = topic.lower()
            if (topic_lower in entry.domain.lower() or
                any(topic_lower in c.lower() for c in entry.concepts) or
                any(topic_lower in f.lower() for f in entry.frameworks)):

                relevant.append({
                    "entity": self.name,
                    "entity_type": "town",
                    "topic": entry.domain,
                    "tier": entry.tier,
                    "concepts": entry.concepts[:5],
                    "frameworks": entry.frameworks[:3],
                    "synthesis": entry.synthesis[:200] if hasattr(entry, 'synthesis') else "",
                    "cycle": entry.cycle_created
                })

        return relevant

    def run_research_cycle(self, city_agenda: str, llm: LLMProvider,
                          logger: AtlantisLogger, cycle: int) -> Dict:
        """Deep specialist research, aims for Tier 5."""
        if not self.researcher:
            return {"tokens": 0}

        # Researcher conducts deep research (with cumulative knowledge from Town + City + State)
        knowledge_context = self._build_knowledge_context()

        response = llm.complete(
            system_prompt=self.researcher.get_system_prompt(),
            user_prompt=(
                f"TOWN RESEARCH — Cycle {cycle}\n\n"
                f"City Agenda: {city_agenda}\n"
                f"Your hyper-specific topic: {self.hyper_topic}\n\n"
                f"{knowledge_context}\n\n"
                f"YOU ALREADY KNOW the above from previous cycles, your parent City, and grandparent State.\n\n"
                f"YOUR TASK: GO HYPER-DEEP. Aim for Tier 5 (Novel Insight) by:\n"
                f"  - Finding what's underneath the deepest concepts\n"
                f"  - Discovering novel connections no one has seen\n"
                f"  - Synthesizing insights that emerge from extreme specialization\n"
                f"  - Pushing past what City and State have found\n\n"
                f"Produce: CONCEPTS (novel), FRAMEWORKS (original), APPLICATIONS (breakthrough), "
                f"SYNTHESIS (Tier 5 insights), EVIDENCE (rigorous)"
            ),
            max_tokens=700,
            temperature=0.7
        )

        findings = self._parse_findings(response.content or "")

        # Create entry first (tier calculated from ALL entries below)
        entry = KnowledgeEntry(
            entry_id=f"{self.town_id}_{cycle}",
            entity_id=self.town_id,
            entity_type="town",
            domain=self.hyper_topic,
            tier=0,  # Temporary, updated below
            concepts=findings["concepts"],
            frameworks=findings["frameworks"],
            applications=findings["applications"],
            synthesis=findings["synthesis"],
            evidence=findings["evidence"],
            cycle_created=cycle,
            tokens_used=response.total_tokens
        )

        self.knowledge_entries.append(entry)

        # Calculate tier from ALL knowledge entries (cumulative)
        all_concepts = []
        all_frameworks = []
        all_applications = []
        for e in self.knowledge_entries:
            all_concepts.extend(e.concepts)
            all_frameworks.extend(e.frameworks)
            all_applications.extend(e.applications)

        cumulative_findings = {
            "concepts": all_concepts,
            "frameworks": all_frameworks,
            "applications": all_applications
        }
        new_tier = self._calculate_tier(cumulative_findings)

        # Update tier for this entry and Town
        entry.tier = new_tier
        if new_tier > self.tier:
            self.tier = new_tier
            print(f"    ⚡ TIER ADVANCEMENT: {self.name} → Tier {new_tier}!")

        return {"tokens": response.total_tokens, "tier": self.tier}

    def summarize_knowledge(self) -> Dict:
        """Summarize Town's findings."""
        if not self.knowledge_entries:
            return {"town": self.name, "tier": self.tier, "findings": "No research yet"}

        latest = self.knowledge_entries[-1]
        return {
            "town": self.name,
            "topic": self.hyper_topic,
            "tier": self.tier,
            "latest_finding": latest.synthesis[:200]
        }

    def _parse_findings(self, content: str) -> Dict:
        """Parse research findings from LLM response.

        Handles all formatting styles:
        - Plain: CONCEPTS: item1, item2
        - Bold markdown: **CONCEPTS:** item1, item2
        - Multi-line with bullets
        - Numbered lists
        """
        import re

        findings = {
            "concepts": [],
            "frameworks": [],
            "applications": [],
            "synthesis": "",
            "evidence": ""
        }

        if not content:
            return findings

        # Strip bold markdown globally: **text** → text
        clean = content.replace("**", "")

        # Extract sections using multi-line regex (captures until next section or end)
        concepts_match = re.search(
            r'CONCEPTS?:\s*(.*?)(?=\n\s*(?:FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if concepts_match:
            raw = concepts_match.group(1).strip()
            findings["concepts"] = _extract_items(raw)

        frameworks_match = re.search(
            r'FRAMEWORKS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if frameworks_match:
            raw = frameworks_match.group(1).strip()
            findings["frameworks"] = _extract_items(raw)

        applications_match = re.search(
            r'APPLICATIONS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if applications_match:
            raw = applications_match.group(1).strip()
            findings["applications"] = _extract_items(raw)

        synthesis_match = re.search(
            r'SYNTHESIS:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if synthesis_match:
            findings["synthesis"] = synthesis_match.group(1).strip()[:500]

        evidence_match = re.search(
            r'EVIDENCE:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if evidence_match:
            findings["evidence"] = evidence_match.group(1).strip()[:500]

        # Fallback: if nothing parsed, extract something from the content
        if not findings["concepts"] and not findings["frameworks"]:
            # Try splitting on commas from first substantial line
            lines = [l.strip() for l in content.split('\n') if len(l.strip()) > 10]
            if lines:
                findings["concepts"] = [w.strip('.,;:*-# ') for w in lines[0].split(',') if len(w.strip()) > 3][:10]
                findings["synthesis"] = content[:500]

        return findings

    def _calculate_tier(self, findings: Dict) -> int:
        """Calculate tier based on findings."""
        concept_count = len(findings["concepts"])
        framework_count = len(findings["frameworks"])
        app_count = len(findings["applications"])

        # Check tier requirements from DEPTH_TIERS
        if concept_count >= DEPTH_TIERS[5]["min_concepts"]:
            return 5
        elif concept_count >= DEPTH_TIERS[4]["min_concepts"]:
            return 4
        elif concept_count >= DEPTH_TIERS[3]["min_concepts"]:
            return 3
        elif concept_count >= DEPTH_TIERS[2]["min_concepts"]:
            return 2
        elif concept_count >= DEPTH_TIERS[1]["min_concepts"]:
            return 1
        return 0


class City:
    """A City with 2 agents: Researcher, Critic."""

    def __init__(self, city_id: str, name: str, parent_state_id: str,
                 sub_domain: str, charter: CityCharter):
        self.city_id = city_id
        self.name = name
        self.parent_state_id = parent_state_id
        self.sub_domain = sub_domain
        self.charter = charter
        self.tier = 0
        self.knowledge_entries: List[KnowledgeEntry] = []
        self.towns: List[Town] = []

        # 2 agents
        self.researcher: Optional[BaseAgent] = None
        self.critic: Optional[BaseAgent] = None
        self.parent_state: Optional['State'] = None  # Reference to parent State

    def _build_knowledge_context(self) -> str:
        """Build cumulative knowledge from City archive + parent State."""
        # Get City's own knowledge (same pattern as State)
        if not self.knowledge_entries:
            context = "No prior research yet. This is the first cycle."
        else:
            all_concepts = []
            all_frameworks = []
            all_applications = []
            critiques_and_defenses = []

            for entry in self.knowledge_entries:
                all_concepts.extend(entry.concepts)
                all_frameworks.extend(entry.frameworks)
                all_applications.extend(entry.applications)
                if entry.challenged_by:
                    critiques_and_defenses.append(
                        f"Cycle {entry.cycle_created}: Challenged '{entry.challenged_by[:100]}' → "
                        f"Defended '{entry.defense[:100]}'"
                    )

            all_concepts = list(set(all_concepts))[:20]
            all_frameworks = list(set(all_frameworks))[:15]
            all_applications = list(set(all_applications))[:15]

            context = f"PRIOR KNOWLEDGE (from {len(self.knowledge_entries)} previous cycles):\n\n"
            context += f"Concepts discovered: {', '.join(all_concepts)}\n\n"
            context += f"Frameworks built: {', '.join(all_frameworks)}\n\n"
            context += f"Applications found: {', '.join(all_applications)}\n\n"

            if critiques_and_defenses:
                context += f"Previous Critic challenges:\n"
                for critique in critiques_and_defenses[-5:]:
                    context += f"  - {critique}\n"

        # Add parent State knowledge
        if self.parent_state and hasattr(self.parent_state, 'knowledge_entries'):
            parent_concepts = []
            parent_frameworks = []
            for entry in self.parent_state.knowledge_entries[-10:]:  # Last 10 State cycles
                parent_concepts.extend(entry.concepts)
                parent_frameworks.extend(entry.frameworks)

            if parent_concepts or parent_frameworks:
                context += f"\n\nPARENT STATE KNOWLEDGE ({self.parent_state.name}):\n"
                context += f"Concepts: {', '.join(list(set(parent_concepts))[:10])}\n"
                context += f"Frameworks: {', '.join(list(set(parent_frameworks))[:10])}\n"

        return context

    def _is_relevant(self, entry, topic: str) -> bool:
        """Check if knowledge entry is relevant to topic."""
        topic_lower = topic.lower()
        return (topic_lower in entry.domain.lower() or
                any(topic_lower in c.lower() for c in entry.concepts) or
                any(topic_lower in f.lower() for f in entry.frameworks) or
                any(topic_lower in a.lower() for a in entry.applications))

    def query_knowledge(self, topic: str, max_entries: int = 20) -> List[dict]:
        """
        Query City's knowledge + all Towns' knowledge for relevant findings.
        Pull-based: only queries Towns when needed.
        """
        relevant = []

        # Query City's own knowledge
        for entry in self.knowledge_entries[-max_entries:]:
            if self._is_relevant(entry, topic):
                relevant.append({
                    "entity": self.name,
                    "entity_type": "city",
                    "topic": entry.domain,
                    "tier": entry.tier,
                    "concepts": entry.concepts[:5],
                    "frameworks": entry.frameworks[:3],
                    "synthesis": entry.synthesis[:200] if hasattr(entry, 'synthesis') else "",
                    "cycle": entry.cycle_created
                })

        # Query all Towns (pull on-demand)
        for town in self.towns:
            if hasattr(town, 'query_knowledge'):
                town_findings = town.query_knowledge(topic, max_entries=5)
                relevant.extend(town_findings)

        return relevant[:max_entries]  # Limit total results

    def run_research_cycle(self, state_agenda: str, llm: LLMProvider,
                          logger: AtlantisLogger, cycle: int) -> Dict:
        """Researcher → Critic adversarial loop."""
        if not self.researcher or not self.critic:
            return {"tokens": 0}

        total_tokens = 0

        # Run Town research cycles first
        for town in self.towns:
            town_result = town.run_research_cycle(state_agenda, llm, logger, cycle)
            total_tokens += town_result["tokens"]

        # Researcher researches (with cumulative knowledge)
        knowledge_context = self._build_knowledge_context()

        research_response = llm.complete(
            system_prompt=self.researcher.get_system_prompt(),
            user_prompt=(
                f"CITY RESEARCH — Cycle {cycle}\n\n"
                f"State Agenda: {state_agenda}\n"
                f"Your sub-domain: {self.sub_domain}\n\n"
                f"{knowledge_context}\n\n"
                f"YOU ALREADY KNOW the above concepts, frameworks, and applications from previous cycles "
                f"and from your parent State.\n\n"
                f"YOUR TASK: GO DEEPER in this specialized sub-domain. Don't repeat what you know:\n"
                f"  - What's underneath these concepts?\n"
                f"  - How do these frameworks connect?\n"
                f"  - What contradicts what we've found?\n"
                f"  - What new synthesis emerges?\n\n"
                f"Produce: CONCEPTS (new), FRAMEWORKS (extensions), APPLICATIONS (novel), "
                f"SYNTHESIS (deeper insights), EVIDENCE (reasoning)"
            ),
            max_tokens=600,
            temperature=0.7
        )
        total_tokens += research_response.total_tokens

        # Critic challenges (with escalation)
        recent_challenges = []
        if self.knowledge_entries:
            for entry in self.knowledge_entries[-3:]:
                if entry.challenged_by and entry.defense:
                    recent_challenges.append(
                        f"Previously: Challenged '{entry.challenged_by[:80]}' → "
                        f"Defended '{entry.defense[:80]}'"
                    )

        challenge_context = ""
        if recent_challenges:
            challenge_context = "PREVIOUS CHALLENGES:\n" + "\n".join(recent_challenges) + "\n\n"

        critique_response = llm.complete(
            system_prompt=self.critic.get_system_prompt(),
            user_prompt=(
                f"CHALLENGE THIS RESEARCH:\n{(research_response.content or '')[:500]}\n\n"
                f"{challenge_context}"
                f"Escalate pressure. Don't ask basic questions we've resolved:\n"
                f"  - What assumptions STILL haven't been tested?\n"
                f"  - Where's the evidence for these NEW claims?\n"
                f"  - What's STILL missing or weak?\n\n"
                f"Push harder than last time."
            ),
            max_tokens=300,
            temperature=0.7
        )
        total_tokens += critique_response.total_tokens

        # Researcher defends
        defense_response = llm.complete(
            system_prompt=self.researcher.get_system_prompt(),
            user_prompt=(
                f"Critic says: {(critique_response.content or '')[:300]}\n\n"
                f"Defend your findings or revise them."
            ),
            max_tokens=400,
            temperature=0.7
        )
        total_tokens += defense_response.total_tokens

        findings = self._parse_findings(research_response.content or "")

        # Create entry first (tier calculated from ALL entries below)
        entry = KnowledgeEntry(
            entry_id=f"{self.city_id}_{cycle}",
            entity_id=self.city_id,
            entity_type="city",
            domain=self.sub_domain,
            tier=0,  # Temporary, updated below
            concepts=findings["concepts"],
            frameworks=findings["frameworks"],
            applications=findings["applications"],
            synthesis=findings["synthesis"],
            evidence=findings["evidence"],
            challenged_by=(critique_response.content or "")[:200],
            defense=(defense_response.content or "")[:200],
            cycle_created=cycle,
            tokens_used=total_tokens
        )

        self.knowledge_entries.append(entry)

        # Calculate tier from ALL knowledge entries (cumulative)
        all_concepts = []
        all_frameworks = []
        all_applications = []
        for e in self.knowledge_entries:
            all_concepts.extend(e.concepts)
            all_frameworks.extend(e.frameworks)
            all_applications.extend(e.applications)

        cumulative_findings = {
            "concepts": all_concepts,
            "frameworks": all_frameworks,
            "applications": all_applications
        }
        new_tier = self._calculate_tier(cumulative_findings)

        # Update tier for this entry and City
        entry.tier = new_tier
        if new_tier > self.tier:
            self.tier = new_tier
            print(f"    ⚡ TIER ADVANCEMENT: {self.name} → Tier {new_tier}!")

        return {"tokens": total_tokens, "tier": self.tier}

    def can_form_town(self) -> tuple[bool, str]:
        """Check if City is Tier 4+."""
        if self.tier >= 4:
            if len(self.towns) >= HARD_CONSTRAINTS["max_towns_per_city"]:
                return False, f"Max towns per city reached ({HARD_CONSTRAINTS['max_towns_per_city']})"
            return True, "Can form town"
        return False, f"Must reach Tier 4 (currently Tier {self.tier})"

    def summarize_knowledge(self) -> Dict:
        """Roll up Town findings + City findings."""
        town_summaries = [town.summarize_knowledge() for town in self.towns]
        latest_finding = ""
        if self.knowledge_entries:
            latest_finding = self.knowledge_entries[-1].synthesis[:200]

        return {
            "city": self.name,
            "sub_domain": self.sub_domain,
            "tier": self.tier,
            "towns": town_summaries,
            "latest_finding": latest_finding
        }

    def _parse_findings(self, content: str) -> Dict:
        """Parse research findings from LLM response.

        Handles all formatting styles:
        - Plain: CONCEPTS: item1, item2
        - Bold markdown: **CONCEPTS:** item1, item2
        - Multi-line with bullets
        - Numbered lists
        """
        import re

        findings = {
            "concepts": [],
            "frameworks": [],
            "applications": [],
            "synthesis": "",
            "evidence": ""
        }

        if not content:
            return findings

        # Strip bold markdown globally: **text** → text
        clean = content.replace("**", "")

        # Extract sections using multi-line regex (captures until next section or end)
        concepts_match = re.search(
            r'CONCEPTS?:\s*(.*?)(?=\n\s*(?:FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if concepts_match:
            raw = concepts_match.group(1).strip()
            findings["concepts"] = _extract_items(raw)

        frameworks_match = re.search(
            r'FRAMEWORKS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if frameworks_match:
            raw = frameworks_match.group(1).strip()
            findings["frameworks"] = _extract_items(raw)

        applications_match = re.search(
            r'APPLICATIONS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if applications_match:
            raw = applications_match.group(1).strip()
            findings["applications"] = _extract_items(raw)

        synthesis_match = re.search(
            r'SYNTHESIS:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if synthesis_match:
            findings["synthesis"] = synthesis_match.group(1).strip()[:500]

        evidence_match = re.search(
            r'EVIDENCE:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if evidence_match:
            findings["evidence"] = evidence_match.group(1).strip()[:500]

        # Fallback: if nothing parsed, extract something from the content
        if not findings["concepts"] and not findings["frameworks"]:
            # Try splitting on commas from first substantial line
            lines = [l.strip() for l in content.split('\n') if len(l.strip()) > 10]
            if lines:
                findings["concepts"] = [w.strip('.,;:*-# ') for w in lines[0].split(',') if len(w.strip()) > 3][:10]
                findings["synthesis"] = content[:500]

        return findings

    def _calculate_tier(self, findings: Dict) -> int:
        """Calculate tier based on findings."""
        concept_count = len(findings["concepts"])

        if concept_count >= DEPTH_TIERS[5]["min_concepts"]:
            return 5
        elif concept_count >= DEPTH_TIERS[4]["min_concepts"]:
            return 4
        elif concept_count >= DEPTH_TIERS[3]["min_concepts"]:
            return 3
        elif concept_count >= DEPTH_TIERS[2]["min_concepts"]:
            return 2
        elif concept_count >= DEPTH_TIERS[1]["min_concepts"]:
            return 1
        return 0


class State:
    """A State with 4 agents: Governor, Researcher, Critic, Senator."""

    def __init__(self, state_id: str, name: str, domain: str,
                 constitution: StateConstitution, formed_cycle: int):
        self.state_id = state_id
        self.name = name
        self.domain = domain
        self.constitution = constitution
        self.formed_cycle = formed_cycle
        self.tier = 0
        self.knowledge_entries: List[KnowledgeEntry] = []
        self.cities: List[City] = []

        # 4 agents
        self.governor: Optional[BaseAgent] = None
        self.researcher: Optional[BaseAgent] = None
        self.critic: Optional[BaseAgent] = None
        self.senator: Optional[BaseAgent] = None

    def _build_knowledge_context(self) -> str:
        """Build cumulative knowledge summary from all prior research cycles."""
        if not self.knowledge_entries:
            return "No prior research yet. This is the first cycle."

        # Collect all concepts, frameworks, applications across all cycles
        all_concepts = []
        all_frameworks = []
        all_applications = []
        critiques_and_defenses = []

        for entry in self.knowledge_entries:
            all_concepts.extend(entry.concepts)
            all_frameworks.extend(entry.frameworks)
            all_applications.extend(entry.applications)
            if entry.challenged_by:
                critiques_and_defenses.append(
                    f"Cycle {entry.cycle_created}: Challenged '{entry.challenged_by[:100]}' → "
                    f"Defended '{entry.defense[:100]}'"
                )

        # Deduplicate and limit to save tokens
        all_concepts = list(set(all_concepts))[:20]
        all_frameworks = list(set(all_frameworks))[:15]
        all_applications = list(set(all_applications))[:15]

        context = f"PRIOR KNOWLEDGE (from {len(self.knowledge_entries)} previous cycles):\n\n"
        context += f"Concepts discovered: {', '.join(all_concepts)}\n\n"
        context += f"Frameworks built: {', '.join(all_frameworks)}\n\n"
        context += f"Applications found: {', '.join(all_applications)}\n\n"

        if critiques_and_defenses:
            context += f"Previous Critic challenges:\n"
            for critique in critiques_and_defenses[-5:]:  # Last 5 challenges
                context += f"  - {critique}\n"

        return context

    def _get_tier_requirements(self, target_tier: int) -> str:
        """Get specific requirements for reaching the next tier."""
        from config.settings import DEPTH_TIERS

        tier_info = DEPTH_TIERS.get(target_tier)
        if not tier_info:
            return "No specific requirements (maximum tier reached)"

        requirements = f"To reach Tier {target_tier} ({tier_info['name']}):\n"
        requirements += f"  - Minimum {tier_info['min_concepts']} concepts\n"
        requirements += f"  - Minimum {tier_info['min_frameworks']} frameworks\n"
        requirements += f"  - Minimum {tier_info['min_applications']} applications\n"
        requirements += f"Requirements: {', '.join(tier_info['requirements'])}\n"

        return requirements

    def _should_propose_city(self) -> tuple:
        """
        Determine if knowledge has branched enough to warrant City formation.
        Returns: (should_propose, sub_domain, rationale)
        """
        # Must be at least Tier 3 to form Cities
        if self.tier < 3:
            return False, "", ""

        # Check if we have diverse frameworks/applications indicating sub-specialization
        if len(self.knowledge_entries) < 3:
            return False, "", ""  # Need at least 3 cycles of research

        # Collect recent frameworks to identify potential sub-domains
        recent_frameworks = []
        for entry in self.knowledge_entries[-5:]:  # Last 5 cycles
            recent_frameworks.extend(entry.frameworks)

        # If we have 5+ distinct frameworks, knowledge may have branched
        if len(set(recent_frameworks)) >= 5:
            return True, "", "Multiple distinct frameworks suggest sub-specialization"

        return False, "", ""

    def _is_relevant(self, entry, topic: str) -> bool:
        """Check if knowledge entry is relevant to topic."""
        topic_lower = topic.lower()
        return (topic_lower in entry.domain.lower() or
                any(topic_lower in c.lower() for c in entry.concepts) or
                any(topic_lower in f.lower() for f in entry.frameworks) or
                any(topic_lower in a.lower() for a in entry.applications))

    def query_knowledge(self, topic: str, max_entries: int = 30) -> List[dict]:
        """
        Query State's knowledge + all Cities' + all Towns' knowledge.
        Pull-based: only queries downward when needed.
        """
        relevant = []

        # Query State's own knowledge
        for entry in self.knowledge_entries[-max_entries:]:
            if self._is_relevant(entry, topic):
                relevant.append({
                    "entity": self.name,
                    "entity_type": "state",
                    "topic": entry.domain,
                    "tier": entry.tier,
                    "concepts": entry.concepts[:5],
                    "frameworks": entry.frameworks[:3],
                    "applications": entry.applications[:3],
                    "synthesis": entry.synthesis[:200] if hasattr(entry, 'synthesis') else "",
                    "cycle": entry.cycle_created
                })

        # Query all Cities (which will query their Towns)
        for city in self.cities:
            if hasattr(city, 'query_knowledge'):
                city_findings = city.query_knowledge(topic, max_entries=10)
                relevant.extend(city_findings)

        return relevant[:max_entries]  # Limit total results

    def run_research_cycle(self, federal_agenda: str, llm: LLMProvider,
                          logger: AtlantisLogger, cycle: int) -> Dict:
        """Governor → Researcher → Critic loop. Sync Senator knowledge after."""
        if not self.governor or not self.researcher or not self.critic:
            return {"tokens": 0}

        total_tokens = 0

        # Run City research cycles first
        for city in self.cities:
            city_result = city.run_research_cycle(federal_agenda, llm, logger, cycle)
            total_tokens += city_result["tokens"]

        # 1. Governor sets State agenda (with cumulative knowledge and tier requirements)
        knowledge_context = self._build_knowledge_context()
        tier_requirements = self._get_tier_requirements(self.tier + 1)

        # Governor pulls City knowledge when setting agenda (pull-based)
        city_knowledge = []
        for city in self.cities:
            city_summary = {
                "city": city.name,
                "subdomain": getattr(city, 'sub_domain', city.domain),  # Fixed: City uses sub_domain not subdomain
                "tier": city.tier,
                "recent_concepts": city.knowledge_entries[-1].concepts[:5] if city.knowledge_entries else []
            }
            city_knowledge.append(city_summary)

        gov_response = llm.complete(
            system_prompt=self.governor.get_system_prompt(),
            user_prompt=(
                f"AGENDA SETTING — Cycle {cycle}\n\n"
                f"Federal Agenda: {federal_agenda}\n"
                f"State: {self.name} (Tier {self.tier})\n"
                f"Domain: {self.domain}\n\n"
                f"{knowledge_context}\n\n"
                f"CITY KNOWLEDGE (pulled on-demand):\n{city_knowledge}\n\n" if city_knowledge else ""
                f"{tier_requirements}\n\n"
                f"Previous cycles summary: We've conducted {len(self.knowledge_entries)} research cycles.\n\n"
                f"YOUR TASK: Set research priorities for THIS cycle. What specific gaps must we fill "
                f"to advance to Tier {self.tier + 1}? What deeper layer should we explore? "
                f"Be specific about what to investigate."
            ),
            max_tokens=300,
            temperature=0.7
        )
        state_agenda = gov_response.content or ""
        total_tokens += gov_response.total_tokens

        # 2. Researcher researches (with cumulative knowledge)
        research_response = llm.complete(
            system_prompt=self.researcher.get_system_prompt(),
            user_prompt=(
                f"STATE RESEARCH — Cycle {cycle}\n\n"
                f"Agenda: {state_agenda}\n\n"
                f"{knowledge_context}\n\n"
                f"YOU ALREADY KNOW the above concepts, frameworks, and applications. "
                f"You've been challenged by the Critic before and defended your findings.\n\n"
                f"YOUR TASK: GO DEEPER. Don't repeat what you already know. Instead:\n"
                f"  - What's underneath these concepts? What's the next layer down?\n"
                f"  - How do these frameworks connect? What's missing between them?\n"
                f"  - What contradicts or challenges what we've found?\n"
                f"  - What new synthesis emerges from combining prior findings?\n\n"
                f"Produce: CONCEPTS (new, not repeats), FRAMEWORKS (extensions or new), "
                f"APPLICATIONS (novel), SYNTHESIS (deeper insights), EVIDENCE (citations/reasoning)"
            ),
            max_tokens=800,
            temperature=0.7
        )
        total_tokens += research_response.total_tokens

        # 3. Critic challenges (with escalation based on previous challenges)
        recent_challenges = []
        if self.knowledge_entries:
            for entry in self.knowledge_entries[-3:]:  # Last 3 cycles
                if entry.challenged_by and entry.defense:
                    recent_challenges.append(
                        f"Previously: Challenged '{entry.challenged_by[:80]}' → "
                        f"Defended '{entry.defense[:80]}'"
                    )

        challenge_context = ""
        if recent_challenges:
            challenge_context = "PREVIOUS CHALLENGES:\n" + "\n".join(recent_challenges) + "\n\n"

        critique_response = llm.complete(
            system_prompt=self.critic.get_system_prompt(),
            user_prompt=(
                f"CHALLENGE THIS RESEARCH:\n{(research_response.content or '')[:500]}\n\n"
                f"{challenge_context}"
                f"YOUR TASK: Escalate pressure. Don't ask basic questions we've already resolved. "
                f"Based on our research history above:\n"
                f"  - What assumptions STILL haven't been tested?\n"
                f"  - Where's the evidence for these NEW claims?\n"
                f"  - What counterargument challenges these deeper findings?\n"
                f"  - What's STILL missing or weak?\n\n"
                f"Push harder than last time. Force the Researcher to go even deeper."
            ),
            max_tokens=400,
            temperature=0.7
        )
        total_tokens += critique_response.total_tokens

        # 4. Researcher defends
        defense_response = llm.complete(
            system_prompt=self.researcher.get_system_prompt(),
            user_prompt=(
                f"Critic says: {(critique_response.content or '')[:400]}\n\n"
                f"Defend your findings or revise them."
            ),
            max_tokens=500,
            temperature=0.7
        )
        total_tokens += defense_response.total_tokens

        # Parse findings and create knowledge entry
        # DEBUG: Show first 200 chars of research response
        print(f"    DEBUG research response: {(research_response.content or '')[:200]}")
        findings = self._parse_findings(research_response.content or "")

        # Create entry first (tier calculated from ALL entries below)
        entry = KnowledgeEntry(
            entry_id=f"{self.state_id}_{cycle}",
            entity_id=self.state_id,
            entity_type="state",
            domain=self.domain,
            tier=0,  # Will be recalculated below
            concepts=findings["concepts"],
            frameworks=findings["frameworks"],
            applications=findings["applications"],
            synthesis=findings["synthesis"],
            evidence=findings["evidence"],
            challenged_by=(critique_response.content or "")[:200],
            defense=(defense_response.content or "")[:200],
            cycle_created=cycle,
            tokens_used=total_tokens
        )

        self.knowledge_entries.append(entry)

        # Calculate tier from ALL knowledge entries (cumulative)
        all_concepts = []
        all_frameworks = []
        all_applications = []
        for e in self.knowledge_entries:
            all_concepts.extend(e.concepts)
            all_frameworks.extend(e.frameworks)
            all_applications.extend(e.applications)

        cumulative_findings = {
            "concepts": all_concepts,
            "frameworks": all_frameworks,
            "applications": all_applications
        }
        new_tier = self._calculate_tier(cumulative_findings)
        tier_advanced = new_tier > self.tier

        # Update tier for this entry and State
        entry.tier = new_tier
        if new_tier > self.tier:
            self.tier = new_tier
            print(f"    ⚡ TIER ADVANCEMENT: {self.name} → Tier {new_tier}!")

        # 6. SYNC SENATOR KNOWLEDGE
        self.sync_senator_knowledge()

        # 7. GENERATE CONTENT FROM THIS RESEARCH CYCLE
        try:
            from content.generator import generate_research_script
            script = generate_research_script(
                state=self,
                cycle=cycle,
                research_output={
                    "concepts": findings["concepts"],
                    "frameworks": findings["frameworks"],
                    "applications": findings["applications"],
                    "synthesis": findings["synthesis"],
                    "critique": (critique_response.content or "")[:300],
                    "defense": (defense_response.content or "")[:300]
                },
                llm=llm
            )

            if script:
                # Save script to file
                import os
                import json
                from datetime import datetime, timezone

                scripts_dir = os.path.join(logger.log_dir, "..", "content", "scripts")
                os.makedirs(scripts_dir, exist_ok=True)

                script_filename = f"state_{self.state_id}_cycle_{cycle}_research.txt"
                script_path = os.path.join(scripts_dir, script_filename)

                with open(script_path, "w") as f:
                    f.write(script)

                print(f"    ✓ Generated TikTok script: {script_filename} ({len(script.split())} words)")

                # Update index
                index_path = os.path.join(scripts_dir, "index.json")
                if os.path.exists(index_path):
                    with open(index_path, "r") as f:
                        index = json.load(f)
                else:
                    index = {"scripts": []}

                index["scripts"].append({
                    "id": f"state_{self.state_id}_cycle_{cycle}_research",
                    "type": "research_cycle",
                    "state": self.name,
                    "domain": self.domain,
                    "tier": self.tier,
                    "cycle": cycle,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "word_count": len(script.split())
                })

                with open(index_path, "w") as f:
                    json.dump(index, f, indent=2)

        except Exception as e:
            print(f"    ⚠ Content generation failed: {e}")

        return {
            "state_name": self.name,
            "domain": self.domain,
            "tier": self.tier,
            "tier_advanced": tier_advanced,
            "new_tier": new_tier,
            "tokens": total_tokens,
            "evidence": findings["evidence"][:100],
            "findings": findings
        }

    def sync_senator_knowledge(self):
        """
        Sync Senator's knowledge with State's latest findings.
        Pull-based: Senator queries State when needed (before votes).
        Only sync recent findings (last 3 cycles), not everything.
        """
        if not self.senator:
            return

        # Only sync recent findings (last 3 cycles), not everything
        recent_entries = self.knowledge_entries[-3:] if len(self.knowledge_entries) > 3 else self.knowledge_entries

        for entry in recent_entries:
            self.senator.update_knowledge(
                domain=entry.domain,
                tier=entry.tier,
                concepts=entry.concepts[:10],  # Limit to top 10
                frameworks=entry.frameworks[:5],  # Limit to top 5
                applications=entry.applications[:5]  # Limit to top 5
            )

    def can_form_city(self) -> tuple[bool, str]:
        """Check if State is Tier 3+."""
        if self.tier >= 3:
            if len(self.cities) >= HARD_CONSTRAINTS["max_cities_per_state"]:
                return False, f"Max cities per state reached ({HARD_CONSTRAINTS['max_cities_per_state']})"
            return True, "Can form city"
        return False, f"Must reach Tier 3 (currently Tier {self.tier})"

    def summarize_knowledge(self) -> Dict:
        """Roll up City findings + State findings."""
        city_summaries = [city.summarize_knowledge() for city in self.cities]
        latest_finding = ""
        if self.knowledge_entries:
            latest_finding = self.knowledge_entries[-1].synthesis[:200]

        return {
            "state": self.name,
            "domain": self.domain,
            "tier": self.tier,
            "cities": city_summaries,
            "latest_finding": latest_finding
        }

    def _parse_findings(self, content: str) -> Dict:
        """Parse research findings from LLM response.

        Handles all formatting styles:
        - Plain: CONCEPTS: item1, item2
        - Bold markdown: **CONCEPTS:** item1, item2
        - Multi-line with bullets
        - Numbered lists
        """
        import re

        findings = {
            "concepts": [],
            "frameworks": [],
            "applications": [],
            "synthesis": "",
            "evidence": ""
        }

        if not content:
            return findings

        # Strip bold markdown globally: **text** → text
        clean = content.replace("**", "")

        # Extract sections using multi-line regex (captures until next section or end)
        concepts_match = re.search(
            r'CONCEPTS?:\s*(.*?)(?=\n\s*(?:FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if concepts_match:
            raw = concepts_match.group(1).strip()
            findings["concepts"] = _extract_items(raw)

        frameworks_match = re.search(
            r'FRAMEWORKS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if frameworks_match:
            raw = frameworks_match.group(1).strip()
            findings["frameworks"] = _extract_items(raw)

        applications_match = re.search(
            r'APPLICATIONS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if applications_match:
            raw = applications_match.group(1).strip()
            findings["applications"] = _extract_items(raw)

        synthesis_match = re.search(
            r'SYNTHESIS:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if synthesis_match:
            findings["synthesis"] = synthesis_match.group(1).strip()[:500]

        evidence_match = re.search(
            r'EVIDENCE:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if evidence_match:
            findings["evidence"] = evidence_match.group(1).strip()[:500]

        # Fallback: if nothing parsed, extract something from the content
        if not findings["concepts"] and not findings["frameworks"]:
            # Try splitting on commas from first substantial line
            lines = [l.strip() for l in content.split('\n') if len(l.strip()) > 10]
            if lines:
                findings["concepts"] = [w.strip('.,;:*-# ') for w in lines[0].split(',') if len(w.strip()) > 3][:10]
                findings["synthesis"] = content[:500]

        return findings

    def _calculate_tier(self, findings: Dict) -> int:
        """Calculate tier based on findings."""
        concept_count = len(findings["concepts"])
        framework_count = len(findings["frameworks"])
        app_count = len(findings["applications"])

        if concept_count >= DEPTH_TIERS[5]["min_concepts"] and \
           framework_count >= DEPTH_TIERS[5]["min_frameworks"] and \
           app_count >= DEPTH_TIERS[5]["min_applications"]:
            return 5
        elif concept_count >= DEPTH_TIERS[4]["min_concepts"] and \
             framework_count >= DEPTH_TIERS[4]["min_frameworks"] and \
             app_count >= DEPTH_TIERS[4]["min_applications"]:
            return 4
        elif concept_count >= DEPTH_TIERS[3]["min_concepts"] and \
             framework_count >= DEPTH_TIERS[3]["min_frameworks"] and \
             app_count >= DEPTH_TIERS[3]["min_applications"]:
            return 3
        elif concept_count >= DEPTH_TIERS[2]["min_concepts"] and \
             framework_count >= DEPTH_TIERS[2]["min_frameworks"]:
            return 2
        elif concept_count >= DEPTH_TIERS[1]["min_concepts"]:
            return 1
        return 0


class StateManager:
    """Manages all States, enforces limits, coordinates knowledge flow."""

    def __init__(self, llm: LLMProvider, logger: AtlantisLogger, db: AtlantisDB):
        self.states: Dict[str, State] = {}
        self.llm = llm
        self.logger = logger
        self.db = db

    def form_state(self, bill: Dict, federal_constitution: Dict, cycle: int) -> State:
        """Form a State from a passed State Formation Bill."""
        # Check hard spawn cap
        if len(self.states) >= HARD_CONSTRAINTS.get("max_states", 50):
            print(f"    ✗ Maximum States reached ({HARD_CONSTRAINTS['max_states']})")
            return None

        # 1. Extract domain and agenda from Bill using LLM
        spec_response = self.llm.complete(
            system_prompt="You are a State specification generator. You ONLY output valid JSON, never prose or explanations.",
            user_prompt=(
                f"A State Formation Bill has passed:\n{bill.get('content', '')[:800]}\n\n"
                f"Extract EXACTLY what the bill proposes:\n"
                f"1. State name (use the exact name from the bill)\n"
                f"2. Primary domain (extract from the bill)\n"
                f"3. Knowledge areas (extract from the research agenda)\n\n"
                f"CRITICAL: Return ONLY valid JSON with no other text, no markdown fences, no explanation.\n"
                f"Start your response with {{ and end with }}.\n\n"
                f"Format:\n"
                f"{{\"name\": \"...\", \"domain\": \"...\", \"knowledge_areas\": [...]}}"
            ),
            max_tokens=300,
            temperature=0.5
        )

        # Debug: Print raw response
        print(f"    DEBUG - State spec raw response: {spec_response.content[:200]}")

        # Parse JSON with markdown fence handling
        import re
        try:
            raw = spec_response.content or "{}"
            # Strip markdown fences
            raw = re.sub(r'```json\s*', '', raw)
            raw = re.sub(r'```\s*', '', raw)
            # Find JSON object using depth-tracking parser
            spec = _extract_json(raw)
            print(f"    DEBUG - Parsed spec: name={spec.get('name')}, domain={spec.get('domain')}")
        except Exception as e:
            print(f"    ⚠ JSON parse failed: {e}")
            spec = {
                "name": f"State of {bill.get('title', 'Knowledge')}",
                "domain": "general_knowledge",
                "knowledge_areas": ["foundations", "frameworks", "applications"]
            }

        state_id = str(uuid.uuid4())[:8]

        # 2. Draft State Constitution
        const_response = self.llm.complete(
            system_prompt="You are a constitutional architect. You ONLY output valid JSON, never prose or explanations.",
            user_prompt=(
                f"Draft a State Constitution for {spec['name']}.\n\n"
                f"Domain: {spec['domain']}\n"
                f"Knowledge areas: {spec['knowledge_areas']}\n\n"
                f"The Constitution must:\n"
                f"1. Define how the State governs its research\n"
                f"2. Comply with Federal Constitution non-amendable clauses\n"
                f"3. Define knowledge goals and methods\n\n"
                f"Federal non-amendable clauses:\n{json.dumps(federal_constitution.get('non_amendable_clauses', []), indent=2)[:300]}\n\n"
                f"CRITICAL: Return ONLY valid JSON with no other text, no markdown fences, no explanation.\n"
                f"Start your response with {{ and end with }}.\n\n"
                f"Format (keep values SHORT to fit token limit):\n"
                f"{{\"governance_principles\": [\"principle1\", \"principle2\"], \"research_methodology\": \"brief description\"}}"
            ),
            max_tokens=800,
            temperature=0.7
        )

        try:
            raw = const_response.content or "{}"
            print(f"    DEBUG constitution raw ({len(raw)} chars): {raw[:200]!r}")
            raw = re.sub(r'```json\s*', '', raw)
            raw = re.sub(r'```\s*', '', raw)
            const_draft = _extract_json(raw)
        except Exception as e:
            print(f"    ⚠ Constitution JSON parse failed: {e}")
            const_draft = {
                "governance_principles": ["Pursue deep knowledge", "Respect Federal law"],
                "research_methodology": "Systematic research with peer review"
            }

        # 3. Validate against Federal
        is_valid, violations = self.validate_state_constitution(const_draft, federal_constitution)

        if not is_valid:
            # Redraft once
            const_response = self.llm.complete(
                system_prompt="You are a constitutional architect. You ONLY output valid JSON, never prose or explanations.",
                user_prompt=(
                    f"Previous draft violated Federal law:\n{violations}\n\n"
                    f"Redraft the State Constitution to comply.\n"
                    f"CRITICAL: Return ONLY valid JSON. No markdown, no explanation.\n"
                    f"Format: {{\"governance_principles\": [\"p1\", \"p2\"], \"research_methodology\": \"brief\"}}"
                ),
                max_tokens=800,
                temperature=0.7
            )
            try:
                raw2 = const_response.content or "{}"
                print(f"    DEBUG redraft raw ({len(raw2)} chars): {raw2[:200]!r}")
                raw2 = re.sub(r'```json\s*', '', raw2)
                raw2 = re.sub(r'```\s*', '', raw2)
                const_draft = _extract_json(raw2)
                is_valid, violations = self.validate_state_constitution(const_draft, federal_constitution)
            except Exception as e:
                print(f"    ⚠ Redraft parse error: {e}")

            if not is_valid:
                raise StateFormationException(f"Constitution violates Federal law after redraft: {violations}")

        # 4. Create State Constitution
        constitution = StateConstitution(
            state_name=spec["name"],
            domain=spec["domain"],
            knowledge_areas=spec.get("knowledge_areas", []),
            governance_principles=const_draft.get("governance_principles", []),
            research_methodology=const_draft.get("research_methodology", ""),
            federal_compliance_check={"compliant": is_valid, "violations": violations},
            ratified_at_cycle=cycle
        )

        # 5. Create State
        state = State(
            state_id=state_id,
            name=spec["name"],
            domain=spec["domain"],
            constitution=constitution,
            formed_cycle=cycle
        )

        # 6. Create 4 agents
        from agents.base import create_state_governor, create_state_researcher, create_state_critic, create_state_senator

        state.governor = create_state_governor(state_id, spec["name"], spec["domain"], constitution)
        state.researcher = create_state_researcher(state_id, spec["name"], spec["domain"])
        state.critic = create_state_critic(state_id, spec["name"], spec["domain"])
        state.senator = create_state_senator(state_id, spec["name"], spec["domain"], state.knowledge_entries)

        # 7. Register in database
        self.db.save_state_constitution(state_id, constitution.to_dict())

        self.states[state_id] = state
        return state

    def validate_state_constitution(self, draft: Dict, federal_const: Dict) -> tuple[bool, List[str]]:
        """Check if State Constitution violates Federal non-amendable clauses."""
        validation_response = self.llm.complete(
            system_prompt="You are a constitutional law expert. You ONLY output valid JSON, never prose.",
            user_prompt=(
                f"Federal Constitution non-amendable clauses:\n"
                f"{json.dumps(federal_const.get('non_amendable_clauses', []), indent=2)[:500]}\n\n"
                f"Proposed State Constitution:\n"
                f"{json.dumps(draft, indent=2)[:500]}\n\n"
                f"Does this State Constitution violate any Federal non-amendable clauses?\n"
                f"CRITICAL: Return ONLY valid JSON. No markdown, no explanation.\n"
                f"Format: {{\"compliant\": true, \"violations\": []}}"
            ),
            max_tokens=500,
            temperature=0.3
        )

        try:
            raw = validation_response.content or "{}"
            print(f"    DEBUG validation raw ({len(raw)} chars): {raw[:150]!r}")
            raw = re.sub(r'```json\s*', '', raw)
            raw = re.sub(r'```\s*', '', raw)
            result = _extract_json(raw)
            return result.get("compliant", True), result.get("violations", [])
        except Exception as e:
            print(f"    ⚠ Constitution validation parse failed: {e}")
            return False, [f"JSON parse error: {e}"]

    def run_all_state_research_cycles(self, federal_agenda: str, cycle: int) -> Dict:
        """Run research cycles for all States/Cities/Towns."""
        if not self.states:
            return {"state_findings": {}, "total_tokens": 0, "tiers_advanced": 0}

        total_tokens = 0
        tiers_advanced = 0
        state_findings = {}

        for state_id, state in self.states.items():
            result = state.run_research_cycle(federal_agenda, self.llm, self.logger, cycle)
            total_tokens += result["tokens"]
            if result.get("tier_advanced"):
                tiers_advanced += 1
            state_findings[state_id] = result

        return {
            "state_findings": state_findings,
            "total_tokens": total_tokens,
            "tiers_advanced": tiers_advanced
        }

    def get_senators(self) -> List[BaseAgent]:
        """Return all State Senators for Federal Senate voting."""
        senators = []
        for state in self.states.values():
            if state.senator:
                senators.append(state.senator)
        return senators

    def knowledge_flow_to_federal(self) -> Dict:
        """Towns → Cities → States → Federal Archive."""
        state_summaries = {}
        for state_id, state in self.states.items():
            state_summaries[state_id] = state.summarize_knowledge()

        return {
            "state_count": len(self.states),
            "state_summaries": state_summaries
        }

    def check_limits(self) -> Dict:
        """Enforce HARD_CONSTRAINTS."""
        total_cities = sum(len(state.cities) for state in self.states.values())
        total_towns = sum(
            sum(len(city.towns) for city in state.cities)
            for state in self.states.values()
        )

        return {
            "states": len(self.states),
            "max_states": HARD_CONSTRAINTS["max_states"],
            "cities": total_cities,
            "towns": total_towns,
            "at_limit": len(self.states) >= HARD_CONSTRAINTS["max_states"]
        }
