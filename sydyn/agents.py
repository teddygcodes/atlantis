"""Sydyn agents: Researcher, Adversary, Critic, Judge."""

import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

from sydyn.evidence import EvidencePack, Source


def extract_json_from_response(response_text: str, agent_name: str = "Agent") -> dict:
    """Extract and parse JSON from LLM response with multiple fallback strategies.

    Args:
        response_text: Raw LLM response
        agent_name: Agent name for logging

    Returns:
        Parsed JSON dict

    Raises:
        json.JSONDecodeError: If all parsing strategies fail
    """
    # Debug: Print first 500 chars of response
    print(f"[{agent_name}] Raw response preview: {response_text[:500]}...")

    # Strategy 1: Try direct parsing (response is pure JSON)
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract JSON from markdown code fences
    # Matches: ```json\n{...}\n``` or ```\n{...}\n```
    fence_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
    if fence_match:
        try:
            json_str = fence_match.group(1)
            print(f"[{agent_name}] Extracted JSON from code fence")
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # Strategy 3: Extract from first { to last }
    first_brace = response_text.find('{')
    last_brace = response_text.rfind('}')

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            json_str = response_text[first_brace:last_brace + 1]
            print(f"[{agent_name}] Extracted JSON from brace range")
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # All strategies failed
    print(f"[{agent_name}] ERROR: Failed to extract valid JSON from response")
    print(f"[{agent_name}] Full response:\n{response_text}")
    raise json.JSONDecodeError("Could not extract valid JSON", response_text, 0)


@dataclass
class Claim:
    """Single claim from an agent."""
    claim_id: str
    text: str
    citations: List[str]  # source_ids
    claim_type: str  # "factual" | "causal" | "evaluative" | "attack"


@dataclass
class AgentResponse:
    """Agent output with claims and metadata."""
    agent_role: str
    claims: List[Claim]
    raw_response: str
    reasoning: Optional[str] = None


class Researcher:
    """Proposes initial answer backed by evidence."""

    def __init__(self, model_router):
        """Initialize with ModelRouter."""
        self.model_router = model_router

    def generate_answer(
        self,
        query: str,
        evidence_pack: EvidencePack
    ) -> AgentResponse:
        """Generate answer with claims and citations.

        Args:
            query: User query
            evidence_pack: Evidence Pack with sources

        Returns:
            AgentResponse with claims
        """
        # Build source summary for prompt
        source_summaries = []
        for i, source in enumerate(evidence_pack.sources):
            if not source.fetch_failed:
                source_summaries.append(
                    f"[{source.source_id}] {source.title}\n"
                    f"URL: {source.url}\n"
                    f"Content: {source.text_content[:500]}...\n"
                )

        sources_text = "\n".join(source_summaries[:8])  # Limit to 8 sources

        system_prompt = """You are the RESEARCHER agent in Sydyn's adversarial search system.

Your role: Propose an initial answer to the user's query, backed by evidence.

Requirements:
1. Break your answer into atomic CLAIMS
2. Cite sources for each claim using source_ids
3. Classify each claim type: factual | causal | evaluative
4. Be precise and specific (avoid vague statements)
5. Prioritize high-credibility sources

CRITICAL: Respond with ONLY a valid JSON object. No markdown code fences. No explanation before or after. Just the raw JSON.

Output format:
{
  "reasoning": "<your thinking process>",
  "claims": [
    {
      "claim_id": "c1",
      "text": "<claim text>",
      "citations": ["source1", "source2"],
      "type": "factual"
    }
  ]
}"""

        user_prompt = f"""Query: {query}

Available Sources:
{sources_text}

Generate your answer as structured claims with citations."""

        response = self.model_router.complete(
            task_type="sydyn_researcher",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000
        )

        # Parse JSON response with fallback strategies
        try:
            data = extract_json_from_response(response.content, "RESEARCHER")
            claims = [
                Claim(
                    claim_id=c.get("claim_id", f"c{i}"),
                    text=c.get("text", ""),
                    citations=c.get("citations", []),
                    claim_type=c.get("type", "factual")
                )
                for i, c in enumerate(data.get("claims", []))
            ]

            return AgentResponse(
                agent_role="researcher",
                claims=claims,
                raw_response=response.content,
                reasoning=data.get("reasoning")
            )

        except (json.JSONDecodeError, ValueError) as e:
            print(f"[RESEARCHER] ERROR: Failed to parse JSON response: {e}")
            return AgentResponse(
                agent_role="researcher",
                claims=[],
                raw_response=response.content
            )


class Adversary:
    """Generates attacks on the researcher's claims."""

    def __init__(self, model_router):
        """Initialize with ModelRouter."""
        self.model_router = model_router

    def generate_attacks(
        self,
        query: str,
        researcher_claims: List[Claim],
        evidence_pack: EvidencePack
    ) -> AgentResponse:
        """Generate attacks on researcher's claims.

        Args:
            query: User query
            researcher_claims: Claims from Researcher
            evidence_pack: Evidence Pack

        Returns:
            AgentResponse with attacks as claims
        """
        claims_text = "\n".join([
            f"{c.claim_id}: {c.text} (cites: {', '.join(c.citations)})"
            for c in researcher_claims
        ])

        system_prompt = """You are the ADVERSARY agent in Sydyn's adversarial search system.

Your role: Challenge the Researcher's answer with attacks.

Attack types:
- EVIDENCE_GAP: Missing or weak evidence for claim
- LOGICAL_FLAW: Reasoning error or unsupported inference
- BIAS: Source bias or cherry-picking
- SCOPE: Claim too broad or overgeneralized

Severity levels:
- MINOR: Claim needs qualification
- MAJOR: Claim requires significant revision
- FATAL: Claim should be rejected

CRITICAL: Respond with ONLY a valid JSON object. No markdown code fences. No explanation before or after. Just the raw JSON.

Output format:
{
  "reasoning": "<your analysis>",
  "attacks": [
    {
      "attack_id": "a1",
      "target_claim": "c1",
      "attack_type": "EVIDENCE_GAP",
      "severity": "MAJOR",
      "text": "<attack description>"
    }
  ]
}"""

        user_prompt = f"""Query: {query}

Researcher's Claims:
{claims_text}

Generate attacks on weak claims, unsupported inferences, or missing evidence."""

        response = self.model_router.complete(
            task_type="sydyn_adversary",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000
        )

        # Parse JSON response with fallback strategies
        try:
            data = extract_json_from_response(response.content, "ADVERSARY")
            attacks = [
                Claim(
                    claim_id=a.get("attack_id", f"a{i}"),
                    text=a.get("text", ""),
                    citations=[],  # Attacks don't cite sources
                    claim_type="attack"
                )
                for i, a in enumerate(data.get("attacks", []))
            ]

            return AgentResponse(
                agent_role="adversary",
                claims=attacks,
                raw_response=response.content,
                reasoning=data.get("reasoning")
            )

        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ADVERSARY] ERROR: Failed to parse JSON response: {e}")
            return AgentResponse(
                agent_role="adversary",
                claims=[],
                raw_response=response.content
            )


class Critic:
    """Addresses adversary attacks and proposes counterarguments."""

    def __init__(self, model_router):
        """Initialize with ModelRouter."""
        self.model_router = model_router

    def address_attacks(
        self,
        query: str,
        researcher_claims: List[Claim],
        adversary_attacks: List[Claim],
        evidence_pack: EvidencePack
    ) -> AgentResponse:
        """Address adversary attacks.

        Args:
            query: User query
            researcher_claims: Original claims
            adversary_attacks: Attacks from Adversary
            evidence_pack: Evidence Pack

        Returns:
            AgentResponse with counterarguments
        """
        claims_text = "\n".join([
            f"{c.claim_id}: {c.text}"
            for c in researcher_claims
        ])

        attacks_text = "\n".join([
            f"{a.claim_id}: {a.text}"
            for a in adversary_attacks
        ])

        system_prompt = """You are the CRITIC agent in Sydyn's adversarial search system.

Your role: Address the Adversary's attacks with counterarguments.

Strategies:
1. DEFEND: Show why attack doesn't invalidate claim
2. QUALIFY: Narrow claim scope to address attack
3. SYNTHESIZE: Explain how conflicting evidence can coexist
4. CONCEDE: Acknowledge when attack is valid

CRITICAL: Respond with ONLY a valid JSON object. No markdown code fences. No explanation before or after. Just the raw JSON.

Output format:
{
  "reasoning": "<your analysis>",
  "responses": [
    {
      "response_id": "r1",
      "target_attack": "a1",
      "strategy": "DEFEND",
      "text": "<counterargument>",
      "revised_claim": "<if claim needs revision>"
    }
  ]
}"""

        user_prompt = f"""Query: {query}

Original Claims:
{claims_text}

Adversary Attacks:
{attacks_text}

Address each attack with counterarguments or revisions."""

        response = self.model_router.complete(
            task_type="sydyn_critic",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2500
        )

        # Parse JSON response with fallback strategies
        try:
            data = extract_json_from_response(response.content, "CRITIC")
            counterarguments = [
                Claim(
                    claim_id=r.get("response_id", f"r{i}"),
                    text=r.get("text", ""),
                    citations=[],
                    claim_type="counterargument"
                )
                for i, r in enumerate(data.get("responses", []))
            ]

            return AgentResponse(
                agent_role="critic",
                claims=counterarguments,
                raw_response=response.content,
                reasoning=data.get("reasoning")
            )

        except (json.JSONDecodeError, ValueError) as e:
            print(f"[CRITIC] ERROR: Failed to parse JSON response: {e}")
            return AgentResponse(
                agent_role="critic",
                claims=[],
                raw_response=response.content
            )


class Judge:
    """Evaluates answer against constitutional rules."""

    def __init__(self, model_router, constitution):
        """Initialize with ModelRouter and Constitution."""
        self.model_router = model_router
        self.constitution = constitution

    def evaluate(
        self,
        query: str,
        all_claims: List[Claim],
        citation_grades: Dict,
        evidence_pack: EvidencePack,
        mode: str = "fast"
    ) -> Dict:
        """Evaluate answer against constitution.

        Args:
            query: User query
            all_claims: All claims from all agents
            citation_grades: Citation verification results
            evidence_pack: Evidence Pack
            mode: "fast" | "strict" | "liability"

        Returns:
            Dict with verdict and violations
        """
        claims_text = "\n".join([
            f"{c.claim_id} [{c.claim_type}]: {c.text} (cites: {', '.join(c.citations)})"
            for c in all_claims if c.claim_type != "attack"
        ])

        # Build citation grades summary
        grades_summary = []
        for claim_id, source_grades in citation_grades.items():
            for source_id, (grade, explanation) in source_grades.items():
                grades_summary.append(f"{claim_id} <- {source_id}: {grade}")

        grades_text = "\n".join(grades_summary)

        hard_rules_text = "\n".join([
            f"{i+1}. {rule['name']}: {rule['description']}"
            for i, rule in enumerate(self.constitution["hard_rules"])
        ])

        system_prompt = f"""You are the JUDGE agent in Sydyn's adversarial search system.

Your role: Evaluate the answer against constitutional rules.

MODE: {mode.upper()}
{"(STRICTER THRESHOLDS for liability mode)" if mode == "liability" else ""}

HARD RULES (must enforce):
{hard_rules_text}

CRITICAL: Respond with ONLY a valid JSON object. No markdown code fences. No explanation before or after. Just the raw JSON.

Output format:
{{
  "verdict": "PASS" | "WARN" | "BLOCK",
  "violations": [
    {{
      "rule": "<rule name>",
      "claim_id": "<affected claim>",
      "severity": "MINOR" | "MAJOR" | "FATAL",
      "explanation": "<why this violates>"
    }}
  ],
  "reasoning": "<your analysis>"
}}

PASS: No major violations
WARN: Minor violations, answer acceptable with disclaimer
BLOCK: Fatal violations, answer should not be returned"""

        user_prompt = f"""Query: {query}

All Claims:
{claims_text}

Citation Grades:
{grades_text}

Evaluate against constitutional rules."""

        response = self.model_router.complete(
            task_type="sydyn_judge",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000
        )

        # Parse JSON response with fallback strategies
        try:
            data = extract_json_from_response(response.content, "JUDGE")
            return {
                "verdict": data.get("verdict", "WARN"),
                "violations": data.get("violations", []),
                "reasoning": data.get("reasoning", ""),
                "raw_response": response.content
            }

        except (json.JSONDecodeError, ValueError) as e:
            print(f"[JUDGE] ERROR: Failed to parse JSON response: {e}")
            return {
                "verdict": "WARN",
                "violations": [],
                "reasoning": "JSON parse error",
                "raw_response": response.content
            }
