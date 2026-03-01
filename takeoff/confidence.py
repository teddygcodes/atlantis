"""Feature-based confidence scoring for lighting takeoffs (not vibes)."""

import json
from typing import List, Dict, Optional


# Feature weights — sum of positive weights = 0.95, fast_mode_penalty is a deduction
FEATURE_WEIGHTS = {
    "schedule_match_rate": 0.25,        # % of counted fixtures that trace to schedule
    "area_coverage": 0.20,              # % of visible RCP areas accounted for
    "adversarial_resolved": 0.15,       # % of Checker attacks resolved (conceded or defended)
    "constitutional_clean": 0.15,       # No violations = boost
    "cross_reference_match": 0.10,      # Panel schedule alignment
    "note_compliance": 0.10,            # Plan notes addressed
    "fast_mode_penalty": -0.05          # Fast mode skips Reconciler
}


def calculate_confidence(
    fixture_counts: List[Dict],
    areas_covered: List[str],
    rcp_snippets: List[Dict],
    fixture_schedule: Dict,
    checker_attacks: List[Dict],
    reconciler_responses: List[Dict],
    constitutional_violations: List[Dict],
    mode: str,
    has_panel_schedule: bool = False,
    has_plan_notes: bool = False,
    notes_addressed: bool = False
) -> Dict:
    """Calculate feature-based confidence score for a lighting takeoff.

    Args:
        fixture_counts: Final fixture count list from Counter/Reconciler
        areas_covered: Areas the Counter agent covered
        rcp_snippets: All RCP snippets provided
        fixture_schedule: Extracted fixture schedule dict
        checker_attacks: Attacks from Checker agent
        reconciler_responses: Responses from Reconciler agent
        constitutional_violations: Violations from Judge
        mode: "fast" | "strict" | "liability"
        has_panel_schedule: Whether a panel schedule snippet was provided
        has_plan_notes: Whether plan notes snippet was provided
        notes_addressed: Whether plan notes were addressed in the takeoff

    Returns:
        Dict with confidence score and features
    """
    print(f"\n[TAKEOFF CONFIDENCE] Inputs:")
    print(f"  Fixture counts: {len(fixture_counts)} types")
    print(f"  Areas covered: {len(areas_covered)}")
    print(f"  RCP snippets: {len([s for s in rcp_snippets if s.get('label') == 'rcp'])}")
    print(f"  Checker attacks: {len(checker_attacks)}")
    print(f"  Reconciler responses: {len(reconciler_responses)}")
    print(f"  Constitutional violations: {len(constitutional_violations)}")
    print(f"  Mode: {mode}")

    features = {}

    # Feature 1: Schedule match rate
    # How many counted fixture types have a corresponding schedule entry
    schedule_tags = {tag.upper() for tag in fixture_schedule.get("fixtures", {}).keys()}
    if fixture_counts and schedule_tags:
        matched = sum(1 for fc in fixture_counts if fc.get("type_tag", "").upper() in schedule_tags)
        features["schedule_match_rate"] = matched / len(fixture_counts)
    elif not fixture_counts:
        features["schedule_match_rate"] = 0.0
    else:
        # No schedule available to match against — neutral
        features["schedule_match_rate"] = 0.5

    # Feature 2: Area coverage
    # % of RCP snippets that have corresponding areas in the count
    rcp_snippet_areas = {s.get("sub_label", "").strip() for s in rcp_snippets if s.get("label") == "rcp" and s.get("sub_label")}
    covered_set = {a.strip() for a in areas_covered}

    if rcp_snippet_areas:
        coverage = len(rcp_snippet_areas & covered_set) / len(rcp_snippet_areas)
        features["area_coverage"] = coverage
    else:
        features["area_coverage"] = 1.0  # No named RCP areas to check

    # Feature 3: Adversarial resolved
    # What % of Checker attacks were explicitly addressed by Reconciler
    if checker_attacks:
        if reconciler_responses:
            resolved_attack_ids = {r.get("attack_id") for r in reconciler_responses}
            checker_attack_ids = {a.get("attack_id") for a in checker_attacks}
            resolved_ratio = len(resolved_attack_ids & checker_attack_ids) / len(checker_attack_ids)
            features["adversarial_resolved"] = resolved_ratio
        else:
            # No reconciler — attacks unaddressed (fast mode)
            features["adversarial_resolved"] = 0.0
    else:
        features["adversarial_resolved"] = 1.0  # No attacks = clean

    # Feature 4: Constitutional clean
    fatal_violations = sum(1 for v in constitutional_violations if v.get("severity") == "FATAL")
    major_violations = sum(1 for v in constitutional_violations if v.get("severity") == "MAJOR")

    if fatal_violations > 0:
        features["constitutional_clean"] = 0.0
    elif major_violations > 0:
        features["constitutional_clean"] = 0.5
    else:
        features["constitutional_clean"] = 1.0

    # Feature 5: Cross-reference match
    # Panel schedule was provided and Checker didn't flag wattage discrepancy
    if has_panel_schedule:
        panel_attack_exists = any(
            "cross_reference" in a.get("category", "") or "panel" in a.get("description", "").lower()
            for a in checker_attacks
        )
        features["cross_reference_match"] = 0.4 if panel_attack_exists else 1.0
    else:
        features["cross_reference_match"] = 0.5  # Neutral — no panel data available

    # Feature 6: Note compliance
    if has_plan_notes:
        features["note_compliance"] = 1.0 if notes_addressed else 0.3
    else:
        features["note_compliance"] = 0.5  # Neutral — no notes provided

    # Feature 7: Fast mode penalty (intentional by design — fast mode skips Reconciler)
    features["fast_mode_penalty"] = 1.0 if mode == "fast" else 0.0

    # Calculate weighted confidence
    base_confidence = 0.5

    print(f"\n[TAKEOFF CONFIDENCE] Feature Breakdown:")
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
    print(f"  Pre-override Score: {confidence_score:.3f}")

    # Apply HARD penalties for constitutional violations
    violation_penalty = 0.0
    for v in constitutional_violations:
        severity = v.get("severity", "MINOR")
        if severity == "FATAL":
            violation_penalty += 0.25
            print(f"  FATAL violation penalty: -0.25")
        elif severity == "MAJOR":
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

    # HARD OVERRIDE based on violation severity
    fatal_count = sum(1 for v in constitutional_violations if v.get("severity") == "FATAL")
    major_count = sum(1 for v in constitutional_violations if v.get("severity") == "MAJOR")
    minor_count = sum(1 for v in constitutional_violations if v.get("severity") == "MINOR")

    if fatal_count > 0:
        confidence_score = 0.25
        confidence_band = "VERY_LOW"
        print(f"  [HARD OVERRIDE] BLOCK verdict ({fatal_count} FATAL) → 0.25 (VERY_LOW)")
    elif major_count > 0:
        original = confidence_score
        confidence_score = max(confidence_score - 0.20, 0.40)
        print(f"  [HARD OVERRIDE] WARN with MAJOR → {original:.3f} - 0.20 = {confidence_score:.3f}")
    elif minor_count > 0:
        original = confidence_score
        confidence_score = max(confidence_score - 0.10, 0.50)
        print(f"  [HARD OVERRIDE] WARN with MINOR → {original:.3f} - 0.10 = {confidence_score:.3f}")
    else:
        print(f"  [VERDICT] PASS — using calculated score {confidence_score:.3f}")

    # Determine band
    if confidence_score >= 0.85:
        confidence_band = "HIGH"
    elif confidence_score >= 0.65:
        confidence_band = "MODERATE"
    elif confidence_score >= 0.40:
        confidence_band = "LOW"
    else:
        confidence_band = "VERY_LOW"

    print(f"  Final Score: {confidence_score:.3f} ({confidence_band})")

    return {
        "score": round(confidence_score, 3),
        "band": confidence_band,
        "features": features,
        "features_json": json.dumps(features, indent=2)
    }


def format_confidence_explanation(confidence_result: Dict) -> str:
    """Format confidence explanation for user output.

    Args:
        confidence_result: Confidence calculation result

    Returns:
        Human-readable explanation string
    """
    features = confidence_result["features"]
    score = confidence_result["score"]
    band = confidence_result["band"]

    lines = [
        f"CONFIDENCE: {score:.2f} ({band})",
        ""
    ]

    # Schedule match rate
    schedule_match = features.get("schedule_match_rate", 0.0)
    lines.append(f"- Schedule traceability: {schedule_match * 100:.0f}% of fixture types verified")

    # Area coverage
    area_cov = features.get("area_coverage", 0.0)
    if area_cov >= 1.0:
        lines.append("- Area coverage: all RCP areas accounted for ✓")
    elif area_cov >= 0.8:
        lines.append(f"- Area coverage: {area_cov * 100:.0f}% (some areas may be missing)")
    else:
        lines.append(f"- Area coverage: {area_cov * 100:.0f}% (significant gaps)")

    # Adversarial
    adv_resolved = features.get("adversarial_resolved", 0.0)
    if adv_resolved >= 1.0:
        lines.append("- Checker attacks: all resolved ✓")
    elif adv_resolved == 0.0:
        lines.append("- Checker attacks: unaddressed (fast mode or no Reconciler)")
    else:
        lines.append(f"- Checker attacks: {adv_resolved * 100:.0f}% resolved")

    # Constitutional
    const_clean = features.get("constitutional_clean", 1.0)
    if const_clean >= 1.0:
        lines.append("- Constitutional violations: none ✓")
    elif const_clean >= 0.5:
        lines.append("- Constitutional violations: major (see flags)")
    else:
        lines.append("- Constitutional violations: fatal (takeoff blocked)")

    # Panel cross-reference
    xref = features.get("cross_reference_match", 0.5)
    if xref >= 1.0:
        lines.append("- Panel cross-reference: no discrepancies ✓")
    elif xref == 0.5:
        lines.append("- Panel cross-reference: no panel schedule provided")
    else:
        lines.append("- Panel cross-reference: wattage discrepancy flagged")

    # Fast mode penalty (by design — Reconciler skipped)
    if features.get("fast_mode_penalty", 0.0) > 0:
        lines.append("- Fast mode: Reconciler review skipped (-5%)")

    # Feature breakdown table
    lines.append("\nFeature Breakdown:")
    for feature, value in features.items():
        weight = FEATURE_WEIGHTS.get(feature, 0.0)
        contribution = value * weight
        lines.append(f"  {feature}: {value:.2f} × {weight:+.2f} = {contribution:+.3f}")

    return "\n".join(lines)
