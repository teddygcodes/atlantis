"""
Objective validators for Atlantis claims.

These run BEFORE the LLM judge and add factual checks that don't rely on
another LLM's opinion. Results are injected into the judge prompt as
OBJECTIVE_VALIDATION_NOTES so the judge can weigh them.

Each validator returns a dict:
  {"passed": bool, "notes": [str], "severity": "info"|"warning"|"flag"}

"flag" means the judge should treat this as strong evidence against the claim.
"warning" means the judge should note it but not auto-destroy.
"info" means neutral context.
"""

from __future__ import annotations

import re
import json
from typing import List, Dict, Optional, Tuple

from governance.anchors import DOMAIN_ANCHORS


# ─── UNIVERSAL VALIDATORS (all domains) ────────────────────────────

def check_citation_validity(
    claim_text: str,
    cited_ids: List[str],
    archive_ids: set,
) -> dict:
    """
    Verify that every cited display_id actually exists in the archive.
    No LLM needed — pure set membership check.
    """
    notes = []
    invalid = [cid for cid in cited_ids if cid not in archive_ids]
    if invalid:
        notes.append(
            f"INVALID CITATIONS: {invalid} do not exist in the archive. "
            f"Claim references non-existent entries."
        )
        return {"passed": False, "notes": notes, "severity": "flag"}

    if cited_ids:
        notes.append(f"All {len(cited_ids)} citations verified as existing archive entries.")
    return {"passed": True, "notes": notes, "severity": "info"}


def check_self_contradiction(claim_text: str) -> dict:
    """
    Detect obvious self-contradictions in a claim.
    Looks for patterns like "X is true ... X is not true" or
    "always ... never" about the same subject within the claim.
    """
    notes = []
    text_lower = claim_text.lower()

    # Check for negation of own conclusion
    lines = claim_text.strip().splitlines()
    conclusion = ""
    position = ""
    for line in lines:
        lu = line.strip().upper()
        if lu.startswith("CONCLUSION:"):
            conclusion = line.split(":", 1)[1].strip().lower()
        if lu.startswith("POSITION:") or lu.startswith("HYPOTHESIS:"):
            position = line.split(":", 1)[1].strip().lower()

    if conclusion and position:
        # Check if conclusion negates position
        pos_words = set(position.split())
        conc_words = set(conclusion.split())
        # If they share subject words but one has "not"/"no" and other doesn't
        shared = pos_words & conc_words
        pos_has_neg = bool({"not", "no", "never", "cannot", "impossible"} & pos_words)
        conc_has_neg = bool({"not", "no", "never", "cannot", "impossible"} & conc_words)
        if len(shared) > 3 and pos_has_neg != conc_has_neg:
            notes.append(
                "SELF-CONTRADICTION DETECTED: Position and Conclusion appear to "
                "assert opposite claims."
            )
            return {"passed": False, "notes": notes, "severity": "flag"}

    return {"passed": True, "notes": notes, "severity": "info"}


def check_circular_reasoning(claim_text: str) -> dict:
    """
    Detect when the conclusion is essentially a restatement of the position.
    Uses token overlap ratio — if conclusion shares >80% of position tokens,
    the claim is likely circular.
    """
    notes = []
    lines = claim_text.strip().splitlines()
    conclusion = ""
    position = ""
    for line in lines:
        lu = line.strip().upper()
        if lu.startswith("CONCLUSION:"):
            conclusion = line.split(":", 1)[1].strip().lower()
        if lu.startswith("POSITION:") or lu.startswith("HYPOTHESIS:"):
            position = line.split(":", 1)[1].strip().lower()

    if conclusion and position:
        # Remove common stop words
        stop = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                "that", "this", "it", "of", "in", "to", "for", "and", "or",
                "on", "at", "by", "with", "from", "as", "but", "if", "so"}
        pos_tokens = set(position.split()) - stop
        conc_tokens = set(conclusion.split()) - stop

        if pos_tokens and conc_tokens:
            overlap = len(pos_tokens & conc_tokens)
            ratio = overlap / max(len(pos_tokens), len(conc_tokens))
            if ratio > 0.80:
                notes.append(
                    f"CIRCULAR REASONING: Conclusion restates the position "
                    f"({ratio:.0%} token overlap). No new reasoning provided."
                )
                return {"passed": False, "notes": notes, "severity": "flag"}
            elif ratio > 0.60:
                notes.append(
                    f"HIGH SIMILARITY: Conclusion closely mirrors position "
                    f"({ratio:.0%} token overlap). May lack genuine reasoning chain."
                )
                return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


def check_numeric_consistency(claim_text: str) -> dict:
    """
    Extract all numbers from a claim and check for internal consistency.
    Catches: percentages that don't add up, contradictory magnitudes,
    numbers claimed as equal that aren't.
    """
    notes = []

    # Extract all percentages
    pct_matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", claim_text)
    percentages = [float(p) for p in pct_matches]

    # Check if any percentage > 100
    over_100 = [p for p in percentages if p > 100]
    if over_100:
        notes.append(
            f"INVALID PERCENTAGE: {over_100} exceeds 100%. "
            f"Check numeric claims."
        )
        return {"passed": False, "notes": notes, "severity": "flag"}

    # Check if percentages that should sum to 100 don't
    # (look for "X% ... Y% ... Z%" patterns near words like "total", "all", "combined")
    if len(percentages) >= 2:
        total = sum(percentages)
        sum_context = re.search(
            r"(total|combined|altogether|sum|entire|all|whole).*?(\d+(?:\.\d+)?)\s*%",
            claim_text, re.IGNORECASE
        )
        if sum_context and 95 < total < 105 and total != 100:
            notes.append(
                f"PERCENTAGE SUM: Component percentages sum to {total}%, not 100%."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


def check_reasoning_step_count(
    claim_text: str, state_tier: int
) -> dict:
    """
    Verify the claim has enough reasoning steps for its tier.
    Objective count — no LLM needed.
    Tier 0-1: 2 steps, Tier 2: 3, Tier 3: 4, Tier 4+: 5
    """
    notes = []

    # Count explicit STEP markers
    step_pattern = r"^\s*(?:STEP\s*\d+|REASONING\s*\d+|\d+[\.\)]\s+\w)"
    steps = re.findall(step_pattern, claim_text, re.MULTILINE | re.IGNORECASE)

    # Also count natural reasoning indicators
    natural_markers = re.findall(
        r"(?:^|\n)\s*(?:First|Second|Third|Fourth|Fifth|Additionally|Furthermore|Moreover|Therefore|Consequently|Thus)\b",
        claim_text, re.IGNORECASE
    )

    total_steps = max(len(steps), len(natural_markers))

    min_required = {0: 2, 1: 2, 2: 3, 3: 4, 4: 5, 5: 5}.get(state_tier, 2)

    if total_steps < min_required:
        notes.append(
            f"INSUFFICIENT REASONING: Found {total_steps} steps, "
            f"Tier {state_tier} requires minimum {min_required}."
        )
        return {"passed": False, "notes": notes, "severity": "warning"}

    notes.append(f"Reasoning depth: {total_steps} steps (Tier {state_tier} minimum: {min_required}).")
    return {"passed": True, "notes": notes, "severity": "info"}


# ─── DOMAIN-SPECIFIC VALIDATORS ────────────────────────────────────

def check_math_validity(claim_text: str) -> dict:
    """
    Basic math/logic checks for Mathematics domain claims.
    - Verify referenced theorems exist (known theorem names)
    - Check for misuse of formal logic terms
    - Flag claims about "proving" philosophical positions with math
    """
    notes = []
    text_lower = claim_text.lower()

    # Known theorem/result names that are commonly referenced
    known_results = {
        "gödel", "godel", "incompleteness", "completeness theorem",
        "axiom of choice", "zorn's lemma", "continuum hypothesis",
        "fermat", "pythagorean", "fundamental theorem", "cantor",
        "compactness", "löwenheim", "skolem", "zermelo", "fraenkel",
        "peano", "dedekind", "hilbert", "noether", "galois",
        "riemann", "euler", "gauss", "cauchy", "weierstrass",
        "bolzano", "heine-borel", "banach", "lebesgue",
    }

    # Check for "proves" + philosophical claim (common bad pattern)
    proves_philosophy = re.search(
        r"(proves?|demonstrates?|establishes?)\s+(that\s+)?"
        r"(mathematics is|numbers are|reality is|existence of|consciousness)",
        text_lower,
    )
    if proves_philosophy:
        notes.append(
            "SCOPE WARNING: Mathematical theorems prove results within formal systems. "
            "Claims that math 'proves' metaphysical positions conflate formal "
            "and philosophical domains."
        )
        return {"passed": True, "notes": notes, "severity": "warning"}

    # Check for referencing specific theorems
    referenced = [t for t in known_results if t in text_lower]
    if referenced:
        notes.append(f"References known results: {', '.join(referenced)}.")

    return {"passed": True, "notes": notes, "severity": "info"}


def check_empirical_claim(claim_text: str) -> dict:
    """
    For empirical domains (Physics, Biology, Medicine, Geography).
    - Flag unfalsifiable claims
    - Check for testable predictions
    - Warn if no measurement/observation criteria specified
    """
    notes = []
    text_lower = claim_text.lower()

    # Check for prediction/testability
    has_prediction = bool(re.search(
        r"\b(predict|falsif|measur|observ|experiment|test|data|empiric|evidence|sample|control group|variable)\b",
        text_lower
    ))

    has_unfalsifiable_markers = bool(re.search(
        r"\b(in principle|could potentially|might possibly|cannot be ruled out|unfalsifiable|by definition)\b",
        text_lower
    ))

    if has_unfalsifiable_markers and not has_prediction:
        notes.append(
            "UNFALSIFIABLE: Claim uses hedging language without specifying "
            "any testable prediction or observable criterion."
        )
        return {"passed": False, "notes": notes, "severity": "flag"}

    if not has_prediction:
        notes.append(
            "NO TESTABLE PREDICTION: Empirical domain claims should specify "
            "what observation or measurement would validate/refute them."
        )
        return {"passed": True, "notes": notes, "severity": "warning"}

    notes.append("Claim includes testable/empirical language.")
    return {"passed": True, "notes": notes, "severity": "info"}


def check_finance_claim(claim_text: str) -> dict:
    """
    For Finance/Economics domains.
    - Flag claims with specific numeric predictions without methodology
    - Check for time-horizon specification
    - Warn about survivorship bias patterns
    """
    notes = []
    text_lower = claim_text.lower()

    # Specific price/return predictions without methodology
    has_specific_number = bool(re.search(
        r"\b(will (reach|hit|exceed|fall to)|returns? of|growth of)\s+\d", text_lower
    ))
    has_methodology = bool(re.search(
        r"\b(model|regression|backtest|historical|monte carlo|simulation|var\b|sharpe|beta|alpha)\b",
        text_lower
    ))

    if has_specific_number and not has_methodology:
        notes.append(
            "UNGROUNDED PREDICTION: Specific numeric forecast without "
            "stated methodology, model, or historical basis."
        )
        return {"passed": True, "notes": notes, "severity": "warning"}

    # Check for survivorship bias
    if re.search(r"\b(successful (companies|funds|traders)|top performers?|winners?)\b", text_lower):
        if not re.search(r"\b(survivor|bias|selection|failed|losers?|excluded)\b", text_lower):
            notes.append(
                "SURVIVORSHIP BIAS RISK: Analysis references successful cases "
                "without acknowledging selection/survivorship bias."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


def check_historical_claim(claim_text: str) -> dict:
    """
    For History domain.
    - Flag presentism (judging past by modern standards without acknowledgment)
    - Check for source attribution
    - Warn about monocausal explanations
    """
    notes = []
    text_lower = claim_text.lower()

    # Monocausal red flag
    monocausal = re.search(
        r"\b(the (sole|only|single|primary) (cause|reason|factor)|caused entirely by|"
        r"solely (due to|because|responsible))\b",
        text_lower,
    )
    if monocausal:
        notes.append(
            "MONOCAUSAL WARNING: Historical events rarely have single causes. "
            "Claim attributes outcome to one factor without acknowledging complexity."
        )
        return {"passed": True, "notes": notes, "severity": "warning"}

    # Check for source references
    has_sources = bool(re.search(
        r"\b(according to|source|document|record|archive|testimony|evidence from|"
        r"cited in|referenced by|historical record)\b",
        text_lower,
    ))
    if not has_sources:
        notes.append(
            "NO SOURCE ATTRIBUTION: Historical claims should reference "
            "specific evidence, documents, or scholarly sources."
        )
        return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── DOMAIN ROUTER ──────────────────────────────────────────────────

# Map domain names to their specific validators
DOMAIN_VALIDATORS = {
    "Mathematics": [check_math_validity],
    "Physics": [check_empirical_claim],
    "Biology": [check_empirical_claim],
    "Medicine": [check_empirical_claim],
    "Geography": [check_empirical_claim],
    "Finance": [check_finance_claim],
    "Economics": [check_finance_claim],
    "Technology": [check_empirical_claim],
    "History": [check_historical_claim],
    "Philosophy": [],  # Philosophy gets universal checks only
}


def run_objective_validation(
    claim_text: str,
    domain: str,
    cited_ids: List[str],
    archive_ids: set,
    state_tier: int = 0,
) -> dict:
    """
    Run all applicable objective validators on a claim.
    Returns combined results that get injected into the judge prompt.

    Returns:
        {
            "all_passed": bool,
            "flags": [str],       # serious issues
            "warnings": [str],    # moderate concerns
            "info": [str],        # neutral context
            "summary": str,       # one-line for judge prompt injection
        }
    """
    flags = []
    warnings = []
    info = []

    # Universal validators (all domains)
    universal = [
        check_citation_validity(claim_text, cited_ids, archive_ids),
        check_self_contradiction(claim_text),
        check_circular_reasoning(claim_text),
        check_numeric_consistency(claim_text),
        check_reasoning_step_count(claim_text, state_tier),
    ]

    for result in universal:
        if result["severity"] == "flag":
            flags.extend(result["notes"])
        elif result["severity"] == "warning":
            warnings.extend(result["notes"])
        else:
            info.extend(result["notes"])

    # Domain-specific validators
    domain_checks = DOMAIN_VALIDATORS.get(domain, [])
    for check_fn in domain_checks:
        result = check_fn(claim_text)
        if result["severity"] == "flag":
            flags.extend(result["notes"])
        elif result["severity"] == "warning":
            warnings.extend(result["notes"])
        else:
            info.extend(result["notes"])

    # Real-world anchors (domain-specific computational/factual checks)
    anchor_checks = DOMAIN_ANCHORS.get(domain, [])
    for check_fn in anchor_checks:
        result = check_fn(claim_text)
        if result["severity"] == "flag":
            flags.extend(result["notes"])
        elif result["severity"] == "warning":
            warnings.extend(result["notes"])
        else:
            info.extend(result["notes"])

    all_passed = len(flags) == 0

    # Build summary for judge prompt injection
    parts = []
    if flags:
        parts.append(f"OBJECTIVE FLAGS ({len(flags)}): " + " | ".join(flags))
    if warnings:
        parts.append(f"OBJECTIVE WARNINGS ({len(warnings)}): " + " | ".join(warnings))
    if info:
        parts.append(f"CONTEXT: " + " | ".join(info))

    summary = "\n".join(parts) if parts else "No objective validation issues detected."

    return {
        "all_passed": all_passed,
        "flags": flags,
        "warnings": warnings,
        "info": info,
        "summary": summary,
    }
