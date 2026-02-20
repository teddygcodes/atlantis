"""
Atlantis V2 — State System
============================
Adversarial rival pairs. Claims must survive challenge to enter Archive.

Key structures:
- ArchiveEntry: full record of every claim, challenge, rebuttal, and outcome
- RivalPair: two States locked in permanent cross-challenge
- State: 4 agents (Researcher, Critic, Senator, Lab), token budget
- StateManager: tracks all active pairs and States
- Pipeline functions: validation, normalization, decomposition, judging
"""

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple

from agents.base import (
    AgentConfig,
    FounderProfile,
    create_state_researcher,
    create_state_critic,
    create_state_senator,
    create_state_lab,
    create_city_analyst,
    create_town_builder,
)
from core.models import ModelRouter
from core.persistence import PersistenceLayer
from config.settings import (
    TOKEN_VALUES,
    REASONING_DEPTH_BY_TIER,
    SCORING_RUBRIC,
    WARMUP_CYCLES,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json_response(content: str, default: dict = None) -> dict:
    """Extract JSON from LLM response, tolerating surrounding text."""
    if not content:
        return default or {}
    start = content.find('{')
    if start == -1:
        return default or {}
    depth = 0
    for i in range(start, len(content)):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
        if depth == 0:
            try:
                return json.loads(content[start:i+1])
            except json.JSONDecodeError:
                return default or {}
    return default or {}


# ═══════════════════════════════════════
# ARCHIVE ENTRY DATACLASS
# ═══════════════════════════════════════

@dataclass
class ArchiveEntry:
    """
    Full V2 Archive entry — matches DB schema exactly.
    Append-only: text fields never modified after creation. Status can change.
    """
    entry_id: str
    display_id: str
    entry_type: str                          # claim|analysis|proposal|principle|governance_record
    source_state: str
    source_entity: str                       # e.g. "Axiom Alpha Researcher"
    cycle_created: int
    status: str                              # surviving|partial|retracted|destroyed|founding|
                                             # overturned|foundation_challenged|chain_broken
    archive_tier: str = "quarantine"         # main|quarantine|graveyard
    claim_type: str = ""                     # foundation|discovery|challenge
    position: str = ""
    reasoning_chain: List[str] = field(default_factory=list)
    conclusion: str = ""
    keywords: List[str] = field(default_factory=list)
    raw_claim_text: str = ""
    raw_challenge_text: str = ""
    raw_rebuttal_text: str = ""
    lab_origin_text: str = ""
    explicit_premises: List[str] = field(default_factory=list)
    implicit_assumptions: List[str] = field(default_factory=list)
    challenge_step_targeted: str = ""
    challenger_entity: str = ""
    outcome: str = ""
    ruling_type: str = ""
    outcome_reasoning: str = ""
    open_questions: List[str] = field(default_factory=list)
    drama_score: int = 0
    novelty_score: int = 0
    depth_score: int = 0
    citations: List[str] = field(default_factory=list)
    referenced_by: List[str] = field(default_factory=list)
    stability_score: int = 1
    impact_score: int = 0
    tokens_earned: int = 0
    unverified_numerics: List[str] = field(default_factory=list)
    auto_filled_gap: bool = False
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════
# RIVAL PAIR DATACLASS
# ═══════════════════════════════════════

@dataclass
class RivalPair:
    domain: str
    state_a: 'State'
    state_b: 'State'
    pair_id: str
    cycle_formed: int
    warmup_remaining: int = 0
    domain_type: str = "philosophical"  # empirical|philosophical


# ═══════════════════════════════════════
# STATE CLASS
# ═══════════════════════════════════════

class State:
    """
    An adversarial research State with 4 agents.
    Researcher produces claims. Critic challenges rivals. Senator votes/appeals.
    Lab generates radical hypotheses.
    """

    def __init__(
        self,
        name: str,
        domain: str,
        approach: str,
        budget: int,
        db: PersistenceLayer,
        models: ModelRouter,
        cycle_formed: int,
    ):
        self.name = name
        self.domain = domain
        self.approach = approach
        self.token_budget = budget
        self.tier = 0
        self.consecutive_probation = 0
        self.cities: List['City'] = []
        self.towns: List['Town'] = []
        self.is_active = True

        self.researcher_config: AgentConfig = create_state_researcher(name, domain, approach)
        self.critic_config: AgentConfig = create_state_critic(name, domain, approach)
        self.senator_config: AgentConfig = create_state_senator(name, domain)
        self.lab_config: AgentConfig = create_state_lab(name, domain, approach)

        self.db = db
        self.models = models

        db.save_state_budget(
            state_name=name,
            domain=domain,
            approach=approach,
            budget=budget,
            rival_name="",
            cycle=cycle_formed,
        )

    def produce_claim(
        self,
        archive_context: str,
        meta_learning: str,
        cycle_number: int,
        previous_claims_summary: str,
        lab_hypothesis: Optional[str] = None,
    ) -> str:
        """
        Researcher decides: formalize Lab hypothesis or produce own claim.
        Returns raw claim text.
        """
        base = (
            f"Domain: {self.domain}\nApproach: {self.approach}\n\n"
            f"CURRENT CYCLE: {cycle_number}\n"
            "PREVIOUS CLAIM POSITIONS (from your State):\n"
            f"{previous_claims_summary}\n\n"
            "You must not repeat previous claims. "
            "Build on, challenge, or extend prior work.\n\n"
            f"ARCHIVE CONTEXT (MAIN archive only; citable):\n{archive_context}\n\n"
            f"META-LEARNING (graveyard claims; learn but do not cite):\n{meta_learning}\n\n"
        )
        if lab_hypothesis:
            base += (
                f"LAB HYPOTHESIS (optional — you may formalize this):\n{lab_hypothesis}\n\n"
            )
        archive_is_empty = (
            not archive_context.strip()
            or "no citable main-archive claims" in archive_context.lower()
        )
        claim_type_hint = (
            "NOTE: The Archive has no citable main claims yet. Produce a DISCOVERY claim "
            "(first-principles reasoning — no citations required).\n\n"
            if archive_is_empty
            else "Produce a Foundation, Discovery, or Challenge claim.\n\n"
        )
        base += (
            f"{claim_type_hint}"
            "Use this structure:\n\n"
            "CLAIM TYPE: [Foundation|Discovery|Challenge]\n"
            "POSITION: [one sentence]\n"
            "STEP 1: [reasoning]\n"
            "STEP 2: [reasoning]\n"
            "(add steps as needed)\n"
            "CONCLUSION: [one sentence]\n"
            "CITATIONS: [#ID, #ID] (if applicable)\n"
            "KEYWORDS: [3-5 terms]"
        )
        response = self.models.complete(
            task_type="researcher_claims",
            system_prompt=self.researcher_config.system_prompt,
            user_prompt=base,
            max_tokens=1200,
        )
        return response.content or ""

    def produce_lab_hypothesis(
        self, open_questions: str, destroyed_claims: str
    ) -> Optional[str]:
        """Lab Agent generates radical hypothesis — max 1 per cycle."""
        response = self.models.complete(
            task_type="federal_lab",
            system_prompt=self.lab_config.system_prompt,
            user_prompt=(
                f"Open questions from your domain:\n{open_questions}\n\n"
                f"Recently destroyed claims:\n{destroyed_claims}\n\n"
                f"Generate a radical hypothesis using the prefix: "
                f"'HYPOTHESIS — UNVERIFIED: '"
            ),
            max_tokens=600,
        )
        content = response.content or ""
        if "HYPOTHESIS" in content.upper():
            return content
        return None

    def produce_challenge(
        self, rival_claim_full: str, rival_premises: dict, constitution_context: str = ""
    ) -> str:
        """
        Critic challenges rival's claim. Must target a specific reasoning step.
        NEVER truncates the rival claim.
        """
        premises_text = (
            f"Explicit premises: {rival_premises.get('explicit_premises', [])}\n"
            f"Implicit assumptions: {rival_premises.get('implicit_assumptions', [])}"
        )
        constitution_block = (
            f"PHASE 2 CONSTITUTIONAL EXTRACT (authoritative):\n{constitution_context}\n\n"
            if constitution_context else ""
        )
        response = self.models.complete(
            task_type="critic_challenges",
            system_prompt=self.critic_config.system_prompt,
            user_prompt=(
                f"{constitution_block}"
                f"RIVAL CLAIM (full text):\n{rival_claim_full}\n\n"
                f"DECOMPOSED PREMISES:\n{premises_text}\n\n"
                f"Challenge this claim. Identify a specific step and explain why it fails.\n"
                f"Format:\n"
                f"STEP TARGETED: [step number or phrase]\n"
                f"FLAW: [explain the logical flaw]\n"
                f"ALTERNATIVE: [what the evidence actually supports]\n"
                f"EVIDENCE: [your counter-evidence]"
            ),
            max_tokens=800,
        )
        return response.content or ""

    def produce_rebuttal(
        self, challenge_text: str, original_claim: str, constitution_context: str = ""
    ) -> str:
        """
        Researcher rebuts a challenge (from rival Critic OR Federal Lab).
        Must choose Option A (Defend), B (Concede and Narrow), or C (Retract).
        """
        constitution_block = (
            f"PHASE 2 CONSTITUTIONAL EXTRACT (authoritative):\n{constitution_context}\n\n"
            if constitution_context else ""
        )
        response = self.models.complete(
            task_type="researcher_rebuttals",
            system_prompt=self.researcher_config.system_prompt,
            user_prompt=(
                f"{constitution_block}"
                f"YOUR ORIGINAL CLAIM:\n{original_claim}\n\n"
                f"CHALLENGE:\n{challenge_text}\n\n"
                f"Choose your response:\n"
                f"Option A — DEFEND: rebut the challenge with new reasoning\n"
                f"Option B — CONCEDE AND NARROW: acknowledge partial flaw, narrow the claim\n"
                f"Option C — RETRACT: the challenge is fatal, withdraw the claim\n\n"
                f"Begin with 'OPTION A:', 'OPTION B:', or 'OPTION C:'"
            ),
            max_tokens=800,
        )
        return response.content or ""

    def produce_senate_vote(
        self, motion_text: str, context: str
    ) -> str:
        """Senator votes on a Senate motion (pair formation, dissolution, etc.)."""
        row = self.db.get_state_budget_row(self.name)
        budget = row.get("token_budget", self.token_budget) if row else self.token_budget
        surviving = self.db.get_surviving_claims_count(self.name)

        response = self.models.complete(
            task_type="researcher_claims",
            system_prompt=self.senator_config.system_prompt,
            user_prompt=(
                f"State: {self.name} | Domain: {self.domain} | Tier: {self.tier}\n"
                f"Token budget: {budget} | Surviving claims: {surviving}\n\n"
                f"MOTION: {motion_text}\n\n"
                f"CONTEXT:\n{context}\n\n"
                f"Vote YES or NO. Begin with 'YES:' or 'NO:' then explain (1-2 sentences)."
            ),
            max_tokens=200,
        )
        return response.content or ""

    def earn_tokens(self, amount: int):
        self.token_budget += amount
        self.db.update_state_budget(self.name, amount)

    def deduct_tokens(self, amount: int):
        """Clamps to 0 floor."""
        actual = min(amount, self.token_budget)
        self.token_budget = max(0, self.token_budget - amount)
        self.db.update_state_budget(self.name, -actual)

    def __repr__(self) -> str:
        return f"State({self.name}, {self.domain}, tier={self.tier}, budget={self.token_budget})"


def detect_claim_type(claim_text: str) -> str:
    """Best-effort claim type detection from raw claim text."""
    text_upper = (claim_text or "").upper()
    explicit_type_patterns = [
        r"\bCLAIM\s*TYPE\b\s*[:\-]?\s*(FOUNDATION|DISCOVERY|CHALLENGE)",
        r"\bTYPE\b\s*[:\-]?\s*(FOUNDATION|DISCOVERY|CHALLENGE)",
        r"\b(FOUNDATION|DISCOVERY|CHALLENGE)\s+CLAIM\b",
        r"^\s*(FOUNDATION|DISCOVERY|CHALLENGE)\b",
    ]
    explicit_types = {
        m.group(1).upper()
        for p in explicit_type_patterns
        for m in re.finditer(p, text_upper, re.IGNORECASE | re.MULTILINE)
    }

    if len(explicit_types) == 1:
        return next(iter(explicit_types)).lower()
    if len(explicit_types) > 1:
        return ""

    implies_challenge = bool(re.search(
        r"\b(reservation|concern|critic|reject|wrong|fails?|flaw|counter|dispute|challenge)\b",
        text_upper,
        re.IGNORECASE,
    ))
    implies_discovery = bool(re.search(
        r"\b(new|novel|propose|hypothesis|discover|introduce|first principles?|findings?|analysis)\b",
        text_upper,
        re.IGNORECASE,
    ))

    if implies_challenge:
        return "challenge"
    if implies_discovery:
        return "discovery"
    return ""


def needs_discovery_gap_autofill(claim_text: str) -> bool:
    """True when a Discovery claim is missing the GAP ADDRESSED field."""
    return detect_claim_type(claim_text) == "discovery" and not bool(re.search(
        r"^\s*GAP\s+ADDRESSED\s*[:\-]\s*.+$",
        claim_text or "",
        re.IGNORECASE | re.MULTILINE,
    ))


def append_gap_addressed_to_claim(claim_text: str, gap_text: str) -> str:
    """Append a generated GAP ADDRESSED section to claim text."""
    cleaned_claim = (claim_text or "").rstrip()
    cleaned_gap = (gap_text or "").strip()
    if not cleaned_gap:
        return cleaned_claim
    return f"{cleaned_claim}\nGAP ADDRESSED: {cleaned_gap}\n"


def autofill_discovery_gap(claim_text: str, models: ModelRouter) -> Tuple[str, bool]:
    """
    For Discovery claims missing GAP ADDRESSED, generate and append it using a cheap Haiku normalization call.
    Returns (possibly updated claim_text, auto_filled_gap flag).
    """
    if not needs_discovery_gap_autofill(claim_text):
        return claim_text, False

    position_match = re.search(r"^\s*POSITION\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
    conclusion_match = re.search(r"^\s*CONCLUSION\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
    position = position_match.group(1).strip() if position_match else ""
    conclusion = conclusion_match.group(1).strip() if conclusion_match else ""

    response = models.complete(
        task_type="normalization",
        system_prompt=(
            "Given this Discovery claim, write 1-3 sentences describing what gap in existing knowledge this claim addresses. "
            "Respond with only the GAP ADDRESSED text, nothing else."
        ),
        user_prompt=(
            f"POSITION:\n{position}\n\n"
            f"CONCLUSION:\n{conclusion}"
        ),
        max_tokens=180,
    )
    gap_text = (response.content or "").strip()
    if not gap_text:
        return claim_text, False
    return append_gap_addressed_to_claim(claim_text, gap_text), True


# ═══════════════════════════════════════
# STATE MANAGER
# ═══════════════════════════════════════

class StateManager:
    """Tracks all active rival pairs and States."""

    def __init__(self, db: PersistenceLayer, models: ModelRouter):
        self.db = db
        self.models = models
        self.pairs: List[RivalPair] = []
        self._states: Dict[str, State] = {}

    def add_pair(self, pair: RivalPair):
        self.pairs.append(pair)
        self._states[pair.state_a.name] = pair.state_a
        self._states[pair.state_b.name] = pair.state_b
        # Link rivals in DB
        self.db.update_rival_link(pair.state_a.name, pair.state_b.name)
        self.db.update_rival_link(pair.state_b.name, pair.state_a.name)

    def get_state(self, name: str) -> Optional[State]:
        return self._states.get(name)

    def get_active_pairs(self) -> List[RivalPair]:
        return [
            p for p in self.pairs
            if p.state_a.is_active or p.state_b.is_active
        ]

    def get_all_active_states(self) -> List[State]:
        seen = {}
        for p in self.pairs:
            for s in (p.state_a, p.state_b):
                if s.is_active and s.name not in seen:
                    seen[s.name] = s
        return list(seen.values())

    def dissolve_state(self, state_name: str, replacement: Optional[State] = None):
        """
        Mark State inactive in DB and in-memory.
        If replacement provided, swap into the pair with warmup=WARMUP_CYCLES.
        """
        state = self._states.get(state_name)
        if not state:
            return
        state.is_active = False
        self.db.dissolve_state(state_name)

        if replacement:
            self._states[replacement.name] = replacement
            for pair in self.pairs:
                if pair.state_a.name == state_name:
                    pair.state_a = replacement
                    pair.warmup_remaining = WARMUP_CYCLES
                elif pair.state_b.name == state_name:
                    pair.state_b = replacement
                    pair.warmup_remaining = WARMUP_CYCLES


# ═══════════════════════════════════════
# PIPELINE FUNCTIONS (MODULE-LEVEL)
# ═══════════════════════════════════════

def validate_claim(
    claim_text: str,
    models: ModelRouter,
    db: PersistenceLayer,
    domain_type: str = "philosophical",
) -> Tuple[bool, List[str]]:
    """
    Structural validation. Returns (is_valid, error_list).
    Flexible extraction supports natural LLM prose plus templated responses.
    No token cost on failure — checked before any LLM judge call.
    """
    errors: List[str] = []
    warnings: List[str] = []
    text_upper = claim_text.upper()
    strict_empirical = (domain_type or "philosophical").strip().lower() == "empirical"

    # Must declare or clearly imply a claim type.
    explicit_type_patterns = [
        r"\bCLAIM\s*TYPE\b\s*[:\-]?\s*(FOUNDATION|DISCOVERY|CHALLENGE)",
        r"\bTYPE\b\s*[:\-]?\s*(FOUNDATION|DISCOVERY|CHALLENGE)",
        r"\b(FOUNDATION|DISCOVERY|CHALLENGE)\s+CLAIM\b",
        r"^\s*(FOUNDATION|DISCOVERY|CHALLENGE)\b",
    ]
    explicit_types = {
        m.group(1).upper()
        for p in explicit_type_patterns
        for m in re.finditer(p, text_upper, re.IGNORECASE | re.MULTILINE)
    }
    has_explicit_type = bool(explicit_types)
    implies_challenge = bool(re.search(
        r"\b(reservation|concern|critic|reject|wrong|fails?|flaw|counter|dispute|challenge)\b",
        text_upper,
        re.IGNORECASE,
    ))
    implies_discovery = bool(re.search(
        r"\b(new|novel|propose|hypothesis|discover|introduce|first principles?|findings?|analysis)\b",
        text_upper,
        re.IGNORECASE,
    ))
    has_type = has_explicit_type or implies_challenge or implies_discovery
    if not has_type:
        errors.append("Missing CLAIM TYPE declaration (Foundation|Discovery|Challenge)")

    claim_type = detect_claim_type(claim_text)
    if len(explicit_types) > 1:
        errors.append("Ambiguous CLAIM TYPE: include exactly one of Foundation|Discovery|Challenge")
        claim_type = ""

    # Must have at least one reasoning step, explicit OR natural-language chain.
    has_explicit_step = bool(re.search(r'\bSTEP\s*\d+\b', claim_text, re.IGNORECASE))
    has_numbered_reasoning = bool(re.search(r'^\s*\d+[\).:-]\s+.+', claim_text, re.IGNORECASE | re.MULTILINE))
    reasoning_cues = len(re.findall(r'\b(because|therefore|thus|implies|since|so that|while|combined with)\b', text_upper, re.IGNORECASE))
    sentence_count = len([s for s in re.split(r'[.!?]+', claim_text) if s.strip()])
    has_structured_reasoning_sections = bool(re.search(r"\b(CONCEPTS?|FRAMEWORKS?|EVIDENCE|APPLICATIONS?|CONNECTIONS?)\s*:", text_upper))
    has_step = has_explicit_step or has_numbered_reasoning or (reasoning_cues >= 1 and sentence_count >= 2) or has_structured_reasoning_sections
    if not has_step:
        errors.append("Missing at least one reasoning STEP")

    # Must have a position or conclusion (templated field OR natural-language conclusion sentence).
    has_position_header = bool(re.search(r'\bPOSITION\b\s*[:\-]', text_upper))
    has_conclusion_header = bool(re.search(r'\b(CONCLUSION|THEREFORE|FINAL\s+CLAIM)\b\s*[:\-]?', text_upper))
    has_natural_conclusion = bool(re.search(
        r"\b(i\s+(propose|conclude|argue|identify)|we\s+(propose|conclude|argue|identify)|this\s+(implies|shows)|in\s+conclusion|key\s+findings?)\b",
        text_upper,
        re.IGNORECASE,
    ))
    if claim_type in {"foundation", "discovery"} and not (has_position_header or has_conclusion_header or has_natural_conclusion):
        errors.append("Missing POSITION or CONCLUSION statement")

    surviving_claims = db.get_surviving_claims() if db else []
    main_ids = {
        c.get("display_id")
        for c in surviving_claims
        if c.get("archive_tier") == "main" and c.get("display_id")
    }

    if claim_type == "discovery":
        position_match = re.search(r"^\s*POSITION\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
        if not position_match:
            msg = "Discovery claims should include POSITION with an operational definition"
            if strict_empirical:
                errors.append(msg)
            else:
                warnings.append(msg)
        else:
            position_text = position_match.group(1)
            has_operational_definition = bool(re.search(
                r"\b(defined as|operational(?:ly)?|measured by|quantified by|observed as|when\s+measured|by\s+tracking)\b",
                position_text,
                re.IGNORECASE,
            ))
            if not has_operational_definition:
                msg = "Discovery POSITION should include an operational definition"
                if strict_empirical:
                    errors.append(msg)
                else:
                    warnings.append(msg)

        step_lines = re.findall(r"^\s*STEP\s*\d+\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
        has_testable_step = any(re.search(
            r"\b(testable|falsifiable|predicts?|would\s+(increase|decrease|change)|if\s+.+\s+then|can\s+be\s+tested|experiment)\b",
            s,
            re.IGNORECASE,
        ) for s in step_lines)
        if not has_testable_step:
            msg = "Discovery claims should include at least one falsifiable or testable implication in STEP lines"
            if strict_empirical:
                errors.append(msg)
            else:
                warnings.append(msg)

        if not re.search(r"^\s*GAP\s+ADDRESSED\s*[:\-]\s*.+$", claim_text, re.IGNORECASE | re.MULTILINE):
            errors.append("Discovery claims must include GAP ADDRESSED")

        numeric_candidate_lines = []
        for line in claim_text.splitlines():
            if re.match(r"^\s*(CLAIM\s*TYPE|CHALLENGE\s+TARGET|CITATIONS|DEPENDS\s+ON)\b", line, re.IGNORECASE):
                continue
            cleaned = re.sub(r"#\d{3}\b", "", line)
            cleaned = re.sub(r"^\s*STEP\s*\d+\s*[:\-]?", "", cleaned, flags=re.IGNORECASE)
            if re.search(r"\b\d+(?:\.\d+)?\b", cleaned):
                numeric_candidate_lines.append(cleaned)
        has_numeric_assertion = bool(numeric_candidate_lines)
        has_estimate_with_assumptions = bool(re.search(
            r"^\s*ESTIMATE\s*[:\-].+\bASSUMPTIONS?\b",
            claim_text,
            re.IGNORECASE | re.MULTILINE,
        ))
        has_evidence_class = bool(re.search(r"\bEVIDENCE\s+CLASS\b\s*[:\-]\s*.+", claim_text, re.IGNORECASE))
        if has_numeric_assertion and not (has_estimate_with_assumptions or has_evidence_class):
            msg = "Discovery numeric assertions require ESTIMATE with assumptions or an EVIDENCE CLASS"
            if strict_empirical:
                errors.append(msg)
            else:
                warnings.append(msg)

    if claim_type == "foundation":
        citations_line = re.search(r"^\s*CITATIONS\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
        cited_ids = set(re.findall(r"#\d{3}", citations_line.group(1) if citations_line else ""))
        valid_citations = cited_ids & main_ids
        if not citations_line:
            errors.append("Foundation claims must include CITATIONS with at least one main archive #ID")
        elif not valid_citations:
            errors.append("Foundation CITATIONS must include at least one valid main archive #ID")

        depends_line = re.search(r"^\s*DEPENDS\s+ON\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
        if not depends_line or not re.search(r"#\d{3}", depends_line.group(1)):
            errors.append("Foundation claims must include DEPENDS ON with prior claim #ID(s)")

        if not re.search(r"^\s*SCOPE\s+BOUNDARY\s*[:\-]\s*.+$", claim_text, re.IGNORECASE | re.MULTILINE):
            errors.append("Foundation claims must include SCOPE BOUNDARY")

    if claim_type == "challenge":
        target_line = re.search(r"^\s*CHALLENGE\s+TARGET\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
        if not target_line or not re.search(r"#\d{3}", target_line.group(1)):
            errors.append("Challenge claims must include CHALLENGE TARGET with a specific #ID")

        if not re.search(r"\bSTEP\s*\d+\b", claim_text, re.IGNORECASE):
            errors.append("Challenge claims must identify which STEP number is being attacked")

        alternative_line = re.search(r"^\s*PROPOSED\s+ALTERNATIVE\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
        if not alternative_line or len(alternative_line.group(1).strip()) < 5:
            errors.append("Challenge claims must include a substantive PROPOSED ALTERNATIVE")

    if errors:
        print("[validate_claim] claim rejected. reasons=", errors)
        print("[validate_claim] claim excerpt=", repr(claim_text[:800]))
    if warnings:
        print("[validate_claim] soft validation warnings=", warnings)

    return (len(errors) == 0, errors)


def extract_validation_rejection_types(claim_text: str, errors: List[str]) -> List[str]:
    """Map validate_claim failures (and soft discovery misses) to budget rejection counters."""
    rejection_types: List[str] = []
    error_text = "\n".join(errors or []).lower()

    if "gap addressed" in error_text:
        rejection_types.append("missing_gap_addressed")
    if "citations" in error_text:
        rejection_types.append("missing_citations")
    if "challenge target" in error_text:
        rejection_types.append("missing_challenge_target")

    # Soft discovery checks are counted even when they are warnings in non-empirical domains.
    position_match = re.search(r"^\s*POSITION\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
    if not position_match:
        rejection_types.append("missing_operational_definition")
    else:
        position_text = position_match.group(1)
        has_operational_definition = bool(re.search(
            r"\b(defined as|operational(?:ly)?|measured by|quantified by|observed as|when\s+measured|by\s+tracking)\b",
            position_text,
            re.IGNORECASE,
        ))
        if not has_operational_definition:
            rejection_types.append("missing_operational_definition")

    step_lines = re.findall(r"^\s*STEP\s*\d+\s*[:\-]\s*(.+)$", claim_text, re.IGNORECASE | re.MULTILINE)
    has_testable_step = any(re.search(
        r"\b(testable|falsifiable|predicts?|would\s+(increase|decrease|change)|if\s+.+\s+then|can\s+be\s+tested|experiment)\b",
        s,
        re.IGNORECASE,
    ) for s in step_lines)
    if not has_testable_step:
        rejection_types.append("missing_testable_implication")

    deduped = []
    for key in rejection_types:
        if key not in deduped:
            deduped.append(key)
    return deduped


def validate_challenge(challenge_text: str) -> Tuple[bool, str]:
    """
    Engine-side check: does challenge reference a specific step?
    Vague 'your whole argument is wrong' challenges are rejected.
    Returns (is_valid, reason).
    """
    text_upper = challenge_text.upper()
    has_target = (
        "STEP TARGETED:" in text_upper
        or bool(re.search(r'STEP\s+\d+', challenge_text, re.IGNORECASE))
        or "FLAW:" in text_upper
    )
    if not has_target:
        return (
            False,
            "Challenge must target a specific reasoning step "
            "(use 'STEP TARGETED:' or 'STEP N:')"
        )
    return (True, "")


def normalize_claim(claim_text: str, models: ModelRouter) -> dict:
    """
    Haiku call. Extracts structured fields from raw claim text.
    Returns: {claim_type, position, reasoning_chain, conclusion, citations, keywords}
    """
    response = models.complete(
        task_type="normalization",
        system_prompt=(
            "Extract structured fields from this claim. "
            "Return valid JSON only, no other text."
        ),
        user_prompt=(
            f"CLAIM TEXT:\n{claim_text}\n\n"
            f"Extract and return JSON:\n"
            f'{{"claim_type": "foundation|discovery|challenge",\n'
            f' "position": "one sentence",\n'
            f' "reasoning_chain": ["step1", "step2", ...],\n'
            f' "conclusion": "one sentence",\n'
            f' "citations": ["#ID", ...],\n'
            f' "keywords": ["term1", "term2", "term3"]}}'
        ),
        max_tokens=600,
    )
    parsed = _parse_json_response(response.content, default={
        "claim_type": "discovery",
        "position": "",
        "reasoning_chain": [],
        "conclusion": "",
        "citations": [],
        "keywords": [],
    })

    # Fallback parser for natural-language LLM outputs that do not emit strict JSON schema.
    text_upper = claim_text.upper()
    if not parsed.get("claim_type"):
        if re.search(r'\b(reservation|concern|reject|wrong|fails?|challenge|flaw)\b', text_upper, re.IGNORECASE):
            parsed["claim_type"] = "challenge"
        elif re.search(r'\b(new|novel|hypothesis|discover|first principles?)\b', text_upper, re.IGNORECASE):
            parsed["claim_type"] = "discovery"
        else:
            parsed["claim_type"] = "foundation"

    sentences = [s.strip() for s in re.split(r'[.!?]+', claim_text) if s.strip()]
    if not parsed.get("position") and sentences:
        parsed["position"] = sentences[0][:220]

    reasoning_chain = parsed.get("reasoning_chain") or []
    if not reasoning_chain:
        explicit_steps = re.findall(r'(?im)^\s*(?:STEP\s*\d+[:.-]?|\d+[\).:-])\s*(.+)$', claim_text)
        if explicit_steps:
            reasoning_chain = [s.strip() for s in explicit_steps if s.strip()]
        else:
            reasoning_like = [
                s for s in sentences
                if re.search(r'\b(because|therefore|thus|implies|since|while|combined with|risks?|fails?|leads to)\b', s, re.IGNORECASE)
            ]
            reasoning_chain = reasoning_like[:4]
            if len(reasoning_chain) < 2:
                section_steps = re.findall(r'(?im)^\s*([A-Z][A-Z_ ]{2,})\s*:\s*(.+)$', claim_text)
                reasoning_chain.extend([f"{k.title()}: {v.strip()}" for k, v in section_steps if v.strip()])
            if len(reasoning_chain) < 2 and len(sentences) >= 3:
                reasoning_chain = sentences[1: min(len(sentences), 4)]
        parsed["reasoning_chain"] = reasoning_chain[:5]

    if not parsed.get("conclusion"):
        conclusion_candidates = [
            s for s in sentences
            if re.search(r'\b(therefore|thus|in conclusion|i propose|we propose|i conclude|we conclude)\b', s, re.IGNORECASE)
        ]
        parsed["conclusion"] = (conclusion_candidates[-1] if conclusion_candidates else (sentences[-1] if sentences else ""))[:240]

    if not isinstance(parsed.get("citations"), list):
        parsed["citations"] = []
    if not isinstance(parsed.get("keywords"), list) or not parsed.get("keywords"):
        words = re.findall(r'\b[a-zA-Z]{5,}\b', claim_text.lower())
        parsed["keywords"] = list(dict.fromkeys(words[:5]))

    return parsed


def run_science_gate(claim_text: str, normalized_claim: dict, models: ModelRouter) -> dict:
    """
    Haiku post-normalization scan for numeric assertions and verification status.
    Returns: {assertions: [{text, classification, source_or_assumption}], unverified_assertions: [text, ...]}
    """
    response = models.complete(
        task_type="science_gate",
        system_prompt=(
            "You are a strict numeric-claim verifier. Find all numeric assertions and classify each as "
            "CITED, ESTIMATE, or UNVERIFIED. Return valid JSON only."
        ),
        user_prompt=(
            f"RAW CLAIM TEXT:\n{claim_text}\n\n"
            f"NORMALIZED CLAIM JSON:\n{json.dumps(normalized_claim)}\n\n"
            "Numeric assertions include quantities, percentages, rates, timescales, and measurements.\n"
            "Classification rules:\n"
            "- CITED: tied to a specific source/prior claim in the text (e.g., #ID, named source).\n"
            "- ESTIMATE: explicitly framed as estimate/projection with assumptions.\n"
            "- UNVERIFIED: naked number with no explicit source or assumptions.\n\n"
            "Return JSON exactly as:\n"
            '{"assertions": [{"text": "...", "classification": "CITED|ESTIMATE|UNVERIFIED", "source_or_assumption": "..."}]}'
        ),
        max_tokens=500,
    )

    result = _parse_json_response(response.content, default={"assertions": []})
    assertions = result.get("assertions") if isinstance(result, dict) else []
    if not isinstance(assertions, list):
        assertions = []

    cleaned = []
    for item in assertions:
        if not isinstance(item, dict):
            continue
        txt = str(item.get("text", "")).strip()
        classification = str(item.get("classification", "UNVERIFIED")).upper().strip()
        if classification not in {"CITED", "ESTIMATE", "UNVERIFIED"}:
            classification = "UNVERIFIED"
        source_or_assumption = str(item.get("source_or_assumption", "")).strip()
        if txt:
            cleaned.append({
                "text": txt,
                "classification": classification,
                "source_or_assumption": source_or_assumption,
            })

    unverified = [a["text"] for a in cleaned if a.get("classification") == "UNVERIFIED"]
    return {"assertions": cleaned, "unverified_assertions": unverified}


def decompose_premises(claim_text: str, models: ModelRouter) -> dict:
    """
    Haiku call. Decomposes claim into explicit and implicit premises.
    Returns: {explicit_premises, implicit_assumptions, conclusion_depends_on}
    """
    response = models.complete(
        task_type="premise_decomposition",
        system_prompt=(
            "Decompose this claim into its logical premises. "
            "Return valid JSON only, no other text."
        ),
        user_prompt=(
            f"CLAIM TEXT:\n{claim_text}\n\n"
            f"Return JSON:\n"
            f'{{"explicit_premises": ["premise stated in text", ...],\n'
            f' "implicit_assumptions": ["assumption not stated but required", ...],\n'
            f' "conclusion_depends_on": ["key premise 1", "key premise 2"]}}'
        ),
        max_tokens=500,
    )
    return _parse_json_response(response.content, default={
        "explicit_premises": [],
        "implicit_assumptions": [],
        "conclusion_depends_on": [],
    })


def check_rebuttal_newness(
    original_claim: str, rebuttal: str, models: ModelRouter
) -> dict:
    """
    Haiku call. Does the rebuttal add new reasoning beyond restating the claim?
    Returns: {new_reasoning: bool, explanation: str}
    """
    response = models.complete(
        task_type="rebuttal_newness",
        system_prompt=(
            "Evaluate whether this rebuttal adds new reasoning. "
            "Return valid JSON only."
        ),
        user_prompt=(
            f"ORIGINAL CLAIM:\n{original_claim[:500]}\n\n"
            f"REBUTTAL:\n{rebuttal[:500]}\n\n"
            f"Does the rebuttal introduce genuinely new evidence, "
            f"reasoning, or counter-examples not present in the original?\n\n"
            f'Return JSON: {{"new_reasoning": true|false, "explanation": "one sentence"}}'
        ),
        max_tokens=200,
    )
    return _parse_json_response(response.content, default={
        "new_reasoning": True,
        "explanation": "Could not evaluate",
    })


def check_anti_loop(last_3_claims: List[str], models: ModelRouter) -> dict:
    """
    Haiku call. Detects if the researcher is repeating the same argument.
    Returns: {is_loop: bool, explanation: str}
    """
    claims_text = "\n\n---\n\n".join(
        f"Claim {i+1}:\n{c[:400]}" for i, c in enumerate(last_3_claims)
    )
    response = models.complete(
        task_type="anti_loop",
        system_prompt=(
            "Detect if these claims are repeating the same core argument. "
            "Return valid JSON only."
        ),
        user_prompt=(
            f"{claims_text}\n\n"
            f"Are these claims making substantially the same argument "
            f"(same position, same logic, just rephrased)?\n\n"
            f'Return JSON: {{"is_loop": true|false, "explanation": "one sentence"}}'
        ),
        max_tokens=200,
    )
    return _parse_json_response(response.content, default={
        "is_loop": False,
        "explanation": "Could not evaluate",
    })


def check_reasoning_depth(
    reasoning_chain: List[str], state_tier: int
) -> Tuple[bool, int]:
    """
    Checks if reasoning chain meets minimum depth for State's tier.
    Returns (meets_minimum, minimum_required).
    """
    minimum = REASONING_DEPTH_BY_TIER.get(state_tier, 2)
    return (len(reasoning_chain) >= minimum, minimum)


def _detect_option_c(rebuttal_text: str) -> bool:
    """Returns True if researcher chose Option C (retract)."""
    upper = rebuttal_text.upper()
    return "OPTION C" in upper or upper.strip().startswith("C:")


def determine_outcome(
    claim_text: str,
    challenge_text: str,
    rebuttal_text: str,
    newness_result: dict,
    domain: str,
    state_approaches: dict,
    models: ModelRouter,
    constitution_context: str = "",
    unverified_numeric_assertions: Optional[List[str]] = None,
    state_tier: int = 0,
    claim_citations: Optional[List[str]] = None,
    surviving_citation_count: Optional[int] = None,
    task_type: str = "judge",
) -> dict:
    """
    Judge determines outcome of claim exchange.
    Domain-aware. Includes SCORING_RUBRIC.
    Returns: {outcome, ruling_type, reasoning, open_questions, scores: {drama, novelty, depth}}

    Outcomes: survived | partial | retracted | destroyed
    """
    # Option C is auto-retracted before judge sees it
    if _detect_option_c(rebuttal_text):
        return {
            "outcome": "retracted",
            "ruling_type": "REJECT_SCOPE",
            "reasoning": "Researcher chose to retract (Option C).",
            "open_questions": [],
            "scores": {"drama": 3, "novelty": 1, "depth": 1},
        }

    newness_note = (
        "The rebuttal introduces NEW reasoning."
        if newness_result.get("new_reasoning")
        else f"WARNING: Rebuttal lacks new reasoning — {newness_result.get('explanation', '')}"
    )

    approaches_text = " vs ".join(
        f"{name} ({approach})" for name, approach in state_approaches.items()
    )

    unverified_numeric_assertions = unverified_numeric_assertions or []
    skepticism_note = ""
    if unverified_numeric_assertions:
        skepticism_note = (
            "This claim contains unverified numeric assertions: "
            f"{json.dumps(unverified_numeric_assertions)}. "
            "Weight these assertions with appropriate skepticism.\n\n"
        )

    constitution_block = (
        f"PHASE 2 CONSTITUTIONAL EXTRACT (authoritative):\n{constitution_context}\n\n"
        if constitution_context else ""
    )

    claim_citations = claim_citations or []
    if surviving_citation_count is None:
        surviving_citation_count = len(claim_citations)

    tier_expectations = (
        "Tier-scaled expectations:\n"
        "- Tier 0-1: Standard evaluation. New claims get reasonable benefit of the doubt.\n"
        "- Tier 2: Claims must demonstrate engagement with existing archive. "
        "Pure first-principles claims without citations should be destroyed.\n"
        "- Tier 3+: Claims must show genuine novelty beyond archive content. "
        "Restating or minor extensions of existing claims get destroyed. "
        "Require minimum 2 citations to surviving claims.\n"
    )

    response = models.complete(
        task_type=task_type,
        system_prompt=(
            "You are a domain-aware judge evaluating an adversarial knowledge exchange. "
            "You have no personality — only rigorous evaluation. "
            "Return valid JSON only."
        ),
        user_prompt=(
            f"{constitution_block}"
            f"DOMAIN: {domain}\n"
            f"APPROACHES: {approaches_text}\n\n"
            f"CLAIM:\n{claim_text}\n\n"
            f"CHALLENGE:\n{challenge_text}\n\n"
            f"REBUTTAL:\n{rebuttal_text}\n\n"
            f"REBUTTAL NEWNESS: {newness_note}\n\n"
            f"CLAIM CITATIONS: {json.dumps(claim_citations)}\n"
            f"CITATIONS TO SURVIVING CLAIMS: {surviving_citation_count}\n"
            f"This claim comes from a Tier {state_tier} State. Higher-tier States are held to stricter standards.\n\n"
            f"{tier_expectations}\n"
            f"SCORING RUBRIC:\n{SCORING_RUBRIC}\n\n"
            f"{skepticism_note}"
            f"Determine the outcome:\n"
            f"You should destroy claims that merely restate definitions, rely on thought experiments "
            f"without novel reasoning, or fail to advance beyond what previous claims already "
            f"established. A claim must demonstrate genuine intellectual progress to survive. "
            f"When in doubt, destroy.\n\n"
            f"First determine ruling_type (required):\n"
            f"- REJECT_FACT: empirically false claim\n"
            f"- REJECT_LOGIC: invalid inference or reasoning error\n"
            f"- REJECT_SCOPE: too broad, category error, or off-domain\n"
            f"- REJECT_CITATION: claims without required support\n"
            f"- REJECT_CLARITY: ambiguous or poorly defined\n"
            f"- REVISE: narrow and resubmit (not a full destruction)\n\n"
            f"Map ruling_type to outcome:\n"
            f"- REJECT_FACT and REJECT_LOGIC => destroyed\n"
            f"- REJECT_SCOPE, REJECT_CITATION, and REJECT_CLARITY => destroyed\n"
            f"- REVISE => partial\n"
            f"- survived is only allowed when the rebuttal successfully defends the claim.\n\n"
            f"If drama_score < 4 AND novelty_score < 4, the claim is routine and should receive "
            f"'destroyed' with ruling_type REJECT_SCOPE unless it demonstrates clear advancement "
            f"over existing archive entries.\n\n"
            f"Return JSON:\n"
            f'{{"outcome": "survived|partial|retracted|destroyed",\n'
            f' "ruling_type": "SURVIVED|REJECT_FACT|REJECT_LOGIC|REJECT_SCOPE|REJECT_CITATION|REJECT_CLARITY|REVISE",\n'
            f' "reasoning": "2-3 sentences",\n'
            f' "open_questions": ["question raised by exchange", ...],\n'
            f' "scores": {{"drama": 1-10, "novelty": 1-10, "depth": 1-10}}}}'
        ),
        max_tokens=600,
    )

    result = _parse_json_response(response.content, default={
        "outcome": "survived",
        "ruling_type": "SURVIVED",
        "reasoning": "Unable to parse judge response.",
        "open_questions": [],
        "scores": {"drama": 3, "novelty": 3, "depth": 3},
    })

    ruling_to_outcome = {
        "REJECT_FACT": "destroyed",
        "REJECT_LOGIC": "destroyed",
        "REJECT_SCOPE": "retracted",
        "REJECT_CITATION": "retracted",
        "REJECT_CLARITY": "retracted",
        "REVISE": "partial",
        "SURVIVED": "survived",
    }

    valid_ruling_types = set(ruling_to_outcome.keys())
    ruling_type = result.get("ruling_type", "").upper()
    if ruling_type not in valid_ruling_types:
        ruling_type = "SURVIVED"
    result["ruling_type"] = ruling_type

    mapped_outcome = ruling_to_outcome[ruling_type]
    judge_outcome = result.get("outcome")
    if judge_outcome != mapped_outcome:
        result["outcome"] = mapped_outcome

    # Normalise outcome to known values
    valid_outcomes = {"survived", "partial", "destroyed", "retracted"}
    if result.get("outcome") not in valid_outcomes:
        result["outcome"] = "survived"

    return result


def reclassify_discovery(
    position: str, domain: str, db: PersistenceLayer, models: ModelRouter
) -> Tuple[str, List[str]]:
    """
    Haiku call: does this Discovery cover existing Archive ground?
    If yes → reclassify as Foundation (requires citations).
    Returns (new_claim_type, overlapping_display_ids).
    """
    surviving = db.get_surviving_claims(domain=domain)
    if not surviving:
        return ("discovery", [])

    existing_summary = "\n".join(
        f"{c['display_id']}: {c.get('position', c.get('raw_claim_text', ''))[:120]}"
        for c in surviving[:20]
    )

    response = models.complete(
        task_type="reclassification",
        system_prompt=(
            "Determine if a new claim covers existing Archive territory. "
            "Return valid JSON only."
        ),
        user_prompt=(
            f"NEW CLAIM POSITION:\n{position}\n\n"
            f"EXISTING SURVIVING CLAIMS IN DOMAIN ({domain}):\n{existing_summary}\n\n"
            f"Does the new claim cover the same ground as any existing claims?\n\n"
            f'Return JSON: {{"overlaps": true|false, "overlapping_ids": ["#001", ...]}}'
        ),
        max_tokens=300,
    )
    result = _parse_json_response(response.content, default={
        "overlaps": False,
        "overlapping_ids": [],
    })

    if result.get("overlaps"):
        return ("foundation", result.get("overlapping_ids", []))
    return ("discovery", [])


# ═══════════════════════════════════════
# CITY
# ═══════════════════════════════════════

class City:
    """
    Auto-spawned when 5+ surviving claims from same State share 2+ citations.
    State-bound: rival States may independently form Cities on overlapping clusters.
    """

    def __init__(
        self,
        city_id: str,
        state_name: str,
        domain: str,
        cluster_ids: List[str],
        db: PersistenceLayer,
        models: ModelRouter,
        cycle: int,
    ):
        self.city_id = city_id
        self.state_name = state_name
        self.domain = domain
        self.cluster_ids = cluster_ids
        self.db = db
        self.models = models
        self.cycle = cycle
        self.analyst_config: AgentConfig = create_city_analyst(city_id, domain, state_name)

        db.save_city(
            city_id=city_id,
            state_name=state_name,
            domain=domain,
            cluster_claim_ids=cluster_ids,
            cycle=cycle,
        )

    def run_analysis(self, cluster_claims: List[dict]) -> ArchiveEntry:
        """Analyst produces structural analysis. Returns principle-type ArchiveEntry."""
        claims_text = "\n\n".join(
            f"{c.get('display_id', '?')}: {c.get('raw_claim_text', '')[:400]}"
            for c in cluster_claims
        )

        response = self.models.complete(
            task_type="researcher_claims",
            system_prompt=self.analyst_config.system_prompt,
            user_prompt=(
                f"Analyze this cluster of {len(cluster_claims)} surviving claims "
                f"from {self.state_name} in domain '{self.domain}':\n\n"
                f"{claims_text}\n\n"
                f"Identify: structural patterns, emergent principles, open research directions.\n"
                f"Format:\n"
                f"PRINCIPLE: [core structural finding]\n"
                f"REASONING: [why these claims form a coherent cluster]\n"
                f"RESEARCH DIRECTIONS: [list 2-3 open questions]"
            ),
            max_tokens=800,
        )

        display_id = self.db.next_display_id()
        self.db.increment_city_analyses(self.city_id)

        return ArchiveEntry(
            entry_id=str(uuid.uuid4()),
            display_id=display_id,
            entry_type="analysis",
            source_state=self.state_name,
            source_entity=f"{self.city_id} Analyst",
            cycle_created=self.cycle,
            status="surviving",
            archive_tier="main",
            claim_type="foundation",
            raw_claim_text=response.content or "",
            citations=self.cluster_ids,
        )

    def spawn_research_directions(self, analysis_text: str) -> List[str]:
        """Extract open questions flagged as Research Directions."""
        directions = []
        for line in analysis_text.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("•"):
                directions.append(line.lstrip("-• "))
        return directions[:3]


# ═══════════════════════════════════════
# TOWN
# ═══════════════════════════════════════

class Town:
    """
    Auto-spawned when 3+ published analyses from any Cities within same State.
    """

    def __init__(
        self,
        town_id: str,
        state_name: str,
        domain: str,
        parent_city_ids: List[str],
        db: PersistenceLayer,
        models: ModelRouter,
        cycle: int,
    ):
        self.town_id = town_id
        self.state_name = state_name
        self.domain = domain
        self.parent_city_ids = parent_city_ids
        self.db = db
        self.models = models
        self.cycle = cycle
        self.builder_config: AgentConfig = create_town_builder(town_id, domain, state_name)

        db.save_town(
            town_id=town_id,
            state_name=state_name,
            domain=domain,
            parent_city_ids=parent_city_ids,
            cycle=cycle,
        )

    def run_proposal(self, city_analyses: List[dict]) -> ArchiveEntry:
        """Builder produces proposal with full citation chain enforced."""
        analyses_text = "\n\n".join(
            f"{a.get('display_id', '?')}: {a.get('raw_claim_text', '')[:300]}"
            for a in city_analyses
        )

        response = self.models.complete(
            task_type="content_generation",
            system_prompt=self.builder_config.system_prompt,
            user_prompt=(
                f"Build an applied proposal from these City analyses "
                f"for {self.state_name} in domain '{self.domain}':\n\n"
                f"{analyses_text}\n\n"
                f"Produce a concrete, implementable proposal.\n"
                f"Format:\n"
                f"PROPOSAL: [title]\n"
                f"RATIONALE: [why this follows from the analyses]\n"
                f"MECHANISM: [how it would work]\n"
                f"CITATION CHAIN: [list all analysis IDs that support this]"
            ),
            max_tokens=800,
        )

        display_id = self.db.next_display_id()
        self.db.increment_town_proposals(self.town_id)

        return ArchiveEntry(
            entry_id=str(uuid.uuid4()),
            display_id=display_id,
            entry_type="proposal",
            source_state=self.state_name,
            source_entity=f"{self.town_id} Builder",
            cycle_created=self.cycle,
            status="surviving",
            archive_tier="main",
            raw_claim_text=response.content or "",
            citations=[a.get("display_id", "") for a in city_analyses if a.get("display_id")],
        )
