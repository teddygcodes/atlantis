"""Feature-based confidence scoring (not vibes)."""

import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta


# Feature weights from plan
FEATURE_WEIGHTS = {
    "direct_support_ratio": 0.25,      # % of DIRECT_SUPPORT citations
    "source_diversity": 0.20,          # Unique domains citing claims
    "adversary_severity": -0.15,       # Penalty for unaddressed attacks
    "constitutional_clean": 0.15,      # No violations = boost
    "evidence_freshness": 0.10,        # Avg source age < 1 year
    "claim_specificity": 0.10,         # Quantified vs vague claims
    "fast_mode_penalty": -0.05         # Fast mode skips critic
}


def calculate_confidence(
    claims: List,
    citation_grades: Dict,
    sources: List,
    attacks: List,
    critic_responses: List,
    constitutional_violations: List,
    mode: str,
    evidence_pack
) -> Dict:
    """Calculate feature-based confidence score.

    Args:
        claims: List of Claim objects from Researcher
        citation_grades: Citation verification results
        sources: List of Source objects
        attacks: List of Attack claims from Adversary
        critic_responses: List of Critic responses
        constitutional_violations: Violations from Judge
        mode: "fast" | "strict" | "liability"
        evidence_pack: EvidencePack object

    Returns:
        Dict with confidence score and features
    """
    # DEBUG: Log inputs
    print(f"\n[CONFIDENCE] Inputs:")
    print(f"  Claims: {len(claims)}")
    print(f"  Attacks: {len(attacks)}")
    print(f"  Critic responses: {len(critic_responses)}")
    print(f"  Constitutional violations: {len(constitutional_violations)}")
    if constitutional_violations:
        for v in constitutional_violations:
            print(f"    - {v.get('severity', 'UNKNOWN')}: {v.get('rule', 'Unknown rule')}")
    print(f"  Mode: {mode}")
    print(f"  Sources: {len(sources)}")

    features = {}

    # Feature 1: Direct support ratio
    total_citations = 0
    direct_support_count = 0

    for claim_id, source_grades in citation_grades.items():
        for grade, _ in source_grades.values():
            total_citations += 1
            if grade == "DIRECT_SUPPORT":
                direct_support_count += 1

    if total_citations > 0:
        features["direct_support_ratio"] = direct_support_count / total_citations
    else:
        features["direct_support_ratio"] = 0.0

    # Feature 2: Source diversity
    from urllib.parse import urlparse

    cited_domains = set()
    for claim in claims:
        for source_id in claim.citations:
            source = next((s for s in sources if s.source_id == source_id), None)
            if source and not source.fetch_failed:
                try:
                    domain = urlparse(source.url).netloc
                    cited_domains.add(domain)
                except Exception:
                    pass

    num_domains = len(cited_domains)

    if num_domains >= 3:
        features["source_diversity"] = 1.0
    elif num_domains == 2:
        features["source_diversity"] = 0.7
    else:  # num_domains <= 1
        features["source_diversity"] = 0.3

    # Feature 3: Adversary severity (penalty for unaddressed attacks)
    if attacks:
        fatal_attacks = sum(1 for a in attacks if "fatal" in a.text.lower())
        major_attacks = sum(1 for a in attacks if "major" in a.text.lower())

        # Check if attacks were addressed by critic
        if critic_responses:
            addressed_ratio = len(critic_responses) / len(attacks)
        else:
            addressed_ratio = 0.0

        # Penalty calculation
        if fatal_attacks > 0:
            severity_penalty = 1.0 * (1 - addressed_ratio)
        elif major_attacks > 0:
            severity_penalty = 0.6 * (1 - addressed_ratio)
        else:
            severity_penalty = 0.3 * (1 - addressed_ratio)

        features["adversary_severity"] = severity_penalty
    else:
        features["adversary_severity"] = 0.0

    # Feature 4: Constitutional clean
    fatal_violations = sum(1 for v in constitutional_violations if v.get("severity") == "FATAL")
    major_violations = sum(1 for v in constitutional_violations if v.get("severity") == "MAJOR")

    if fatal_violations > 0:
        features["constitutional_clean"] = 0.0
    elif major_violations > 0:
        features["constitutional_clean"] = 0.5
    else:
        features["constitutional_clean"] = 1.0

    # Feature 5: Evidence freshness
    # Simple heuristic: high-quality sources tend to be fresh
    avg_credibility = sum(s.credibility_score for s in sources if not s.fetch_failed) / len(sources) if sources else 0.5

    # Map credibility to freshness (proxy for v1)
    features["evidence_freshness"] = avg_credibility

    # Feature 6: Claim specificity
    # Count quantified claims (contains numbers)
    quantified_claims = sum(1 for c in claims if any(char.isdigit() for char in c.text))
    total_claims = len(claims)

    if total_claims > 0:
        features["claim_specificity"] = quantified_claims / total_claims
    else:
        features["claim_specificity"] = 0.0

    # Feature 7: Fast mode penalty
    if mode == "fast":
        features["fast_mode_penalty"] = 1.0
    else:
        features["fast_mode_penalty"] = 0.0

    # Calculate weighted confidence
    base_confidence = 0.5

    # DEBUG: Print feature breakdown
    print(f"\n[CONFIDENCE] Feature Breakdown:")
    print(f"  Base: {base_confidence:.3f}")
    for feature, weight in FEATURE_WEIGHTS.items():
        value = features.get(feature, 0.0)
        contribution = value * weight
        print(f"  {feature}: {value:.3f} × {weight:+.3f} = {contribution:+.3f}")

    weighted_sum = sum(
        features.get(feature, 0.0) * weight
        for feature, weight in FEATURE_WEIGHTS.items()
    )

    print(f"  Weighted Sum: {weighted_sum:+.3f}")
    confidence_score = base_confidence + weighted_sum
    print(f"  Pre-penalty Score: {confidence_score:.3f}")

    # Apply HARD penalties for constitutional violations
    # The weighted feature approach is too weak - violations must have bite
    violation_penalty = 0.0
    for v in constitutional_violations:
        severity = v.get("severity", "MINOR")
        if severity == "MAJOR":
            violation_penalty += 0.15
            print(f"  MAJOR violation penalty: -0.15")
        elif severity == "MINOR":
            violation_penalty += 0.05
            print(f"  MINOR violation penalty: -0.05")

    if violation_penalty > 0:
        confidence_score -= violation_penalty
        print(f"  After violation penalties (-{violation_penalty:.3f}): {confidence_score:.3f}")

    # Clamp to [0.0, 1.0]
    confidence_score = max(0.0, min(1.0, confidence_score))
    print(f"  Final Score: {confidence_score:.3f}")

    # HARD OVERRIDE: Judge verdict must affect confidence
    # Infer verdict from violation severities
    fatal_count = sum(1 for v in constitutional_violations if v.get("severity") == "FATAL")
    major_count = sum(1 for v in constitutional_violations if v.get("severity") == "MAJOR")
    minor_count = sum(1 for v in constitutional_violations if v.get("severity") == "MINOR")

    if fatal_count > 0:
        # BLOCK verdict - hard override to LOW confidence
        confidence_score = 0.35
        confidence_band = "VERY_LOW"
        print(f"  [HARD OVERRIDE] BLOCK verdict detected ({fatal_count} FATAL violations) → confidence = 0.35 (VERY_LOW)")
    elif major_count > 0:
        # WARN verdict with MAJOR violations
        original_score = confidence_score
        confidence_score = max(confidence_score - 0.20, 0.40)
        print(f"  [HARD OVERRIDE] WARN verdict with MAJOR violations → {original_score:.3f} - 0.20 = {confidence_score:.3f} (min 0.40)")
    elif minor_count > 0:
        # WARN verdict with only MINOR violations
        original_score = confidence_score
        confidence_score = max(confidence_score - 0.10, 0.50)
        print(f"  [HARD OVERRIDE] WARN verdict with MINOR violations → {original_score:.3f} - 0.10 = {confidence_score:.3f} (min 0.50)")
    else:
        # PASS verdict - use calculated score as-is
        print(f"  [VERDICT] PASS - using calculated score {confidence_score:.3f}")

    # Determine confidence band (after override)
    if confidence_score >= 0.85:
        confidence_band = "HIGH"
    elif confidence_score >= 0.65:
        confidence_band = "MODERATE"
    elif confidence_score >= 0.40:
        confidence_band = "LOW"
    else:
        confidence_band = "VERY_LOW"

    return {
        "score": round(confidence_score, 3),
        "band": confidence_band,
        "features": features,
        "features_json": json.dumps(features, indent=2)
    }


def adjust_confidence_for_timeout(
    confidence_result: Dict,
    degradation_level: Optional[str]
) -> Dict:
    """Adjust confidence based on timeout degradation.

    Args:
        confidence_result: Original confidence calculation
        degradation_level: "no_critic" | "no_adversary" | "evidence_only" | None

    Returns:
        Adjusted confidence result
    """
    if not degradation_level:
        return confidence_result

    original_score = confidence_result["score"]
    features = confidence_result["features"]

    if degradation_level == "no_critic":
        # Penalty for skipping critic
        adjusted_score = original_score - 0.10
        features["timeout_penalty"] = 0.10

    elif degradation_level == "no_adversary":
        # Penalty for skipping adversary + critic
        adjusted_score = original_score - 0.15
        features["timeout_penalty"] = 0.15

    elif degradation_level == "evidence_only":
        # Major penalty for returning only evidence
        adjusted_score = 0.20  # Very low confidence
        features["timeout_penalty"] = 0.50

    else:
        adjusted_score = original_score

    # Re-clamp
    adjusted_score = max(0.0, min(1.0, adjusted_score))

    # Update band
    if adjusted_score >= 0.85:
        confidence_band = "HIGH"
    elif adjusted_score >= 0.65:
        confidence_band = "MODERATE"
    elif adjusted_score >= 0.40:
        confidence_band = "LOW"
    else:
        confidence_band = "VERY_LOW"

    return {
        "score": round(adjusted_score, 3),
        "band": confidence_band,
        "features": features,
        "features_json": json.dumps(features, indent=2),
        "degradation_level": degradation_level
    }


def format_confidence_explanation(confidence_result: Dict) -> str:
    """Format confidence explanation for user output.

    Args:
        confidence_result: Confidence calculation result

    Returns:
        Human-readable explanation
    """
    features = confidence_result["features"]
    score = confidence_result["score"]
    band = confidence_result["band"]

    lines = [
        f"CONFIDENCE: {score:.2f} ({band})",
        ""
    ]

    # Direct support ratio
    direct_ratio = features.get("direct_support_ratio", 0.0)
    lines.append(f"- Direct citation support: {direct_ratio * 100:.0f}%")

    # Source diversity
    diversity = features.get("source_diversity", 0.0)
    if diversity >= 1.0:
        lines.append(f"- Source diversity: ≥3 domains ✓")
    elif diversity >= 0.7:
        lines.append(f"- Source diversity: 2 domains")
    else:
        lines.append(f"- Source diversity: <2 domains (weak)")

    # Adversary severity
    adv_severity = features.get("adversary_severity", 0.0)
    if adv_severity == 0.0:
        lines.append(f"- Adversarial review: no attacks")
    elif adv_severity < 0.3:
        lines.append(f"- Adversarial severity: minor (addressed)")
    elif adv_severity < 0.6:
        lines.append(f"- Adversarial severity: moderate")
    else:
        lines.append(f"- Adversarial severity: major (unaddressed)")

    # Constitutional clean
    const_clean = features.get("constitutional_clean", 1.0)
    if const_clean >= 1.0:
        lines.append(f"- Constitutional violations: none ✓")
    elif const_clean >= 0.5:
        lines.append(f"- Constitutional violations: minor")
    else:
        lines.append(f"- Constitutional violations: major")

    # Fast mode penalty
    if features.get("fast_mode_penalty", 0.0) > 0:
        lines.append(f"- Fast mode: critic review skipped")

    # Timeout penalty
    if "timeout_penalty" in features:
        degradation = confidence_result.get("degradation_level", "unknown")
        lines.append(f"- Timeout: degraded to {degradation}")

    return "\n".join(lines)
