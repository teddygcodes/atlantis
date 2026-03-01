"""Takeoff agents: Counter, Checker, Reconciler, Judge.

Mirrors sydyn/agents.py exactly — same patterns, same JSON extraction helpers,
same response dataclasses. Domain logic replaced with lighting takeoff specifics.
"""

import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

from takeoff.extraction import FixtureSchedule, AreaCount, PlanNote, PanelData, extract_json_from_response


@dataclass
class TakeoffResponse:
    """Output from a takeoff agent."""
    agent_role: str
    data: dict
    raw_response: str
    reasoning: Optional[str] = None


# ─── Counter Agent ────────────────────────────────────────────────────────────

class Counter:
    """Produces a complete fixture count from extracted drawing data.

    Equivalent to Researcher in Sydyn — proposes the initial takeoff count.
    """

    def __init__(self, model_router):
        self.model_router = model_router

    def generate_count(
        self,
        fixture_schedule: FixtureSchedule,
        area_counts: List[AreaCount],
        plan_notes: List[PlanNote],
        panel_data: Optional[PanelData] = None
    ) -> TakeoffResponse:
        """Generate a complete fixture count organized by type tag and area.

        Args:
            fixture_schedule: Extracted fixture schedule
            area_counts: Per-area extraction results from RCP snippets
            plan_notes: Constraints from plan notes snippets
            panel_data: Panel schedule data (optional, for cross-reference)

        Returns:
            TakeoffResponse with structured fixture counts
        """
        # Build schedule summary
        schedule_lines = []
        for tag, info in fixture_schedule.fixtures.items():
            desc = info.get("description", "unknown") if isinstance(info, dict) else str(info)
            wattage = info.get("wattage") if isinstance(info, dict) else None
            watt_str = f" ({wattage}W)" if wattage else ""
            schedule_lines.append(f"  Type {tag}: {desc}{watt_str}")
        schedule_text = "\n".join(schedule_lines) if schedule_lines else "  No fixture schedule extracted."

        # Build area count summary
        area_lines = []
        for ac in area_counts:
            counts_str = ", ".join(f"{tag}:{count}" for tag, count in ac.counts_by_type.items())
            area_lines.append(f"  Area '{ac.area_label}': {counts_str}")
            if ac.notes:
                area_lines.append(f"    Notes: {'; '.join(ac.notes)}")
            if ac.warnings:
                area_lines.append(f"    Warnings: {'; '.join(ac.warnings)}")
        areas_text = "\n".join(area_lines) if area_lines else "  No RCP areas extracted."

        # Build plan notes summary
        notes_lines = [f"  - [{n.constraint_type}] {n.text}" for n in plan_notes]
        notes_text = "\n".join(notes_lines) if notes_lines else "  No plan notes."

        # Panel data summary
        panel_text = "No panel schedule provided."
        if panel_data and panel_data.circuits:
            panel_text = f"Panel '{panel_data.panel_name}': total load = {panel_data.total_load_va} VA across {len(panel_data.circuits)} circuits."

        system_prompt = """You are the COUNTER agent in the Takeoff adversarial system — the electrical estimator performing the initial fixture count.

Your role: Produce a complete, organized fixture count from the extracted drawing data.

Rules:
1. Aggregate per-area extraction counts into totals per type tag
2. Every type tag from the fixture schedule MUST appear (even if count is 0)
3. Assign difficulty codes: S=Standard (troffer), M=Moderate (recessed), D=Difficult (needs lift), E=Extreme (custom)
4. List accessories for each fixture type (mounting clips, flex whips, J-boxes, sensors)
5. Flag any type tags that appear in area counts but NOT in the fixture schedule as "UNSCHEDULED"
6. Flag any ambiguous or assumed quantities
7. Cross-reference with plan notes — add quantities specified in notes if not already in RCP counts

CRITICAL: Respond with ONLY a valid JSON object. No markdown. No explanation before or after.

Output format:
{
  "fixture_counts": [
    {
      "type_tag": "A",
      "description": "2x4 LED Recessed Troffer",
      "counts_by_area": {
        "Floor 2 North Wing": 24,
        "Floor 2 South Wing": 18
      },
      "total": 42,
      "difficulty": "S",
      "notes": "Per fixture schedule sheet E-001",
      "accessories": ["mounting clips", "flex whip"],
      "flags": []
    }
  ],
  "areas_covered": ["Floor 2 North Wing", "Floor 2 South Wing"],
  "grand_total_fixtures": 142,
  "reasoning": "Aggregated counts from 3 RCP areas..."
}"""

        user_prompt = f"""FIXTURE SCHEDULE:
{schedule_text}

RCP AREA COUNTS (extracted from drawing snippets):
{areas_text}

PLAN NOTES:
{notes_text}

PANEL LOAD DATA:
{panel_text}

Produce the complete fixture count. Aggregate all per-area counts, assign difficulty codes, list accessories, and flag any issues."""

        response = self.model_router.complete(
            task_type="takeoff_counter",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000
        )

        try:
            data = extract_json_from_response(response.content, "COUNTER")
            print(f"[COUNTER] {len(data.get('fixture_counts', []))} fixture types, {data.get('grand_total_fixtures', 0)} total fixtures")
            return TakeoffResponse(
                agent_role="counter",
                data=data,
                raw_response=response.content,
                reasoning=data.get("reasoning")
            )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[COUNTER] ERROR: Failed to parse JSON response: {e}")
            return TakeoffResponse(agent_role="counter", data={}, raw_response=response.content)


# ─── Checker Agent ────────────────────────────────────────────────────────────

class Checker:
    """Adversarial agent that attacks the Counter's count.

    Equivalent to Adversary in Sydyn — generates attacks on the initial count.
    """

    def __init__(self, model_router):
        self.model_router = model_router

    def generate_attacks(
        self,
        counter_output: dict,
        fixture_schedule: FixtureSchedule,
        area_counts: List[AreaCount],
        plan_notes: List[PlanNote],
        panel_data: Optional[PanelData] = None
    ) -> TakeoffResponse:
        """Find errors, omissions, and inconsistencies in the Counter's count.

        Args:
            counter_output: The Counter agent's full output dict
            fixture_schedule: Original fixture schedule for independent verification
            area_counts: Original per-area extraction data
            plan_notes: Plan notes constraints
            panel_data: Panel schedule (optional)

        Returns:
            TakeoffResponse with adversarial attacks
        """
        # Summarize counter output
        counter_counts = counter_output.get("fixture_counts", [])
        areas_covered = counter_output.get("areas_covered", [])
        grand_total = counter_output.get("grand_total_fixtures", 0)

        count_summary = []
        for fc in counter_counts:
            count_summary.append(f"  Type {fc.get('type_tag')}: total {fc.get('total', 0)} — areas: {list(fc.get('counts_by_area', {}).keys())}")
        count_text = "\n".join(count_summary) or "  No counts provided."

        # RCP areas available in snippets
        rcp_area_labels = [ac.area_label for ac in area_counts]
        available_areas_text = "\n".join(f"  - {label}" for label in rcp_area_labels)

        # Schedule types available
        schedule_tags = list(fixture_schedule.fixtures.keys())
        schedule_text = "\n".join(f"  - Type {tag}" for tag in schedule_tags)

        # Panel cross-reference
        panel_text = "No panel data."
        if panel_data and panel_data.total_load_va:
            # Heuristic: round numbers < 10000 that are multiples of 100 look like watts, not VA
            if panel_data.total_load_va % 100 == 0 and panel_data.total_load_va < 10000:
                print(f"[CHECKER] WARNING: Panel load {panel_data.total_load_va} may be in watts, not VA. Verify units.")
            # Estimate counter wattage
            estimated_va = 0
            for fc in counter_counts:
                tag = fc.get("type_tag")
                if tag and tag in fixture_schedule.fixtures:
                    info = fixture_schedule.fixtures[tag]
                    wattage = info.get("wattage", 0) if isinstance(info, dict) else 0
                    if wattage:
                        estimated_va += (fc.get("total", 0) * wattage)
            panel_text = f"Panel total load: {panel_data.total_load_va} VA. Estimated Counter wattage: {estimated_va}W. Discrepancy: {abs(panel_data.total_load_va - estimated_va)} VA."

        system_prompt = """You are the CHECKER agent in the Takeoff adversarial system — the second estimator doing an independent review.

Your role: Find every error, omission, and inconsistency in the Counter's takeoff.

Attack categories (use exact string):
- missed_area: Area visible in snippet data but not in Counter's areas_covered
- double_count: Counter may have counted overlapping views twice
- wrong_type: Counter assigned wrong type tag to a fixture
- missed_fixtures: Fixture types in schedule with zero count that likely exist
- math_error: Totals don't add up correctly
- missing_accessory: Required accessories not listed
- cross_reference: Panel load vs. fixture watt mismatch exceeds 15%
- missed_note: Plan note constraints not reflected in counts
- emergency_gap: Emergency fixtures or exit signs not separately tracked

Severity levels:
- critical: Will cause a wrong bid (missed room, major math error)
- major: Significant impact on bid accuracy
- minor: Small issue, easy to verify

CRITICAL: Respond with ONLY a valid JSON object. No markdown. No explanation.

Output format:
{
  "attacks": [
    {
      "attack_id": "ATK-001",
      "severity": "critical|major|minor",
      "category": "missed_area|double_count|wrong_type|missed_fixtures|math_error|missing_accessory|cross_reference|missed_note|emergency_gap",
      "description": "specific description of the issue",
      "affected_type_tag": "type tag or null",
      "affected_area": "area name or null",
      "suggested_correction": "correction text",
      "evidence": "why you believe this is an error"
    }
  ],
  "total_attacks": 0,
  "critical_count": 0,
  "summary": "overall assessment"
}"""

        user_prompt = f"""Counter's fixture count summary:
{count_text}

Counter's areas covered: {areas_covered}
Counter's grand total: {grand_total} fixtures

RCP snippet areas available:
{available_areas_text}

Fixture schedule type tags:
{schedule_text}

Panel cross-reference:
{panel_text}

Check for: missed areas, double-counted overlapping views, wrong fixture type assignments, missing fixture types that likely exist, math errors, missing accessories, emergency fixture gaps, and plan note violations."""

        response = self.model_router.complete(
            task_type="takeoff_checker",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3000
        )

        try:
            data = extract_json_from_response(response.content, "CHECKER")
            attacks = data.get("attacks", [])

            # Deduplicate attacks by (category, affected_type_tag, affected_area)
            seen: set = set()
            deduped = []
            for attack in attacks:
                key = (
                    attack.get("category", ""),
                    (attack.get("affected_type_tag") or "").upper(),
                    (attack.get("affected_area") or "").lower().strip()
                )
                if key not in seen:
                    seen.add(key)
                    deduped.append(attack)
            if len(deduped) < len(attacks):
                print(f"[CHECKER] Deduplicated {len(attacks) - len(deduped)} duplicate attacks")
            data["attacks"] = deduped
            data["total_attacks"] = len(deduped)

            critical = data.get("critical_count", 0)
            print(f"[CHECKER] {len(deduped)} attacks ({critical} critical)")
            return TakeoffResponse(
                agent_role="checker",
                data=data,
                raw_response=response.content,
                reasoning=data.get("summary")
            )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[CHECKER] ERROR: Failed to parse JSON response: {e}")
            return TakeoffResponse(agent_role="checker", data={"attacks": []}, raw_response=response.content)


# ─── Reconciler Agent ─────────────────────────────────────────────────────────

class Reconciler:
    """Addresses Checker attacks and produces revised counts.

    Equivalent to Critic in Sydyn — either defends or concedes each attack.
    Skipped in fast mode (same as Critic in Sydyn).
    """

    def __init__(self, model_router):
        self.model_router = model_router

    def address_attacks(
        self,
        counter_output: dict,
        checker_attacks: List[Dict],
        fixture_schedule: FixtureSchedule,
        area_counts: List[AreaCount]
    ) -> TakeoffResponse:
        """Address each Checker attack — defend or concede.

        Args:
            counter_output: Original Counter counts
            checker_attacks: Attack list from Checker
            fixture_schedule: Fixture schedule for reference
            area_counts: Original RCP extraction data

        Returns:
            TakeoffResponse with responses and revised counts
        """
        # Build attacks summary
        attack_lines = []
        for a in checker_attacks:
            attack_lines.append(
                f"  [{a.get('attack_id')}] {a.get('severity').upper()} — {a.get('category')}: {a.get('description')}"
            )
            if a.get("suggested_correction"):
                attack_lines.append(f"    Suggested: {a.get('suggested_correction')}")
        attacks_text = "\n".join(attack_lines) or "  No attacks."

        # Counter's original counts
        orig_counts = {}
        for fc in counter_output.get("fixture_counts", []):
            orig_counts[fc.get("type_tag")] = fc.get("total", 0)
        orig_text = "\n".join(f"  Type {tag}: {cnt}" for tag, cnt in orig_counts.items())

        system_prompt = """You are the RECONCILER agent in the Takeoff adversarial system — the senior estimator reviewing the dispute.

Your role: Address each Checker attack with a verdict: concede, defend, or partial.

For each attack:
- CONCEDE: Accept the error. Provide corrected count.
- DEFEND: Reject the attack. Explain why Counter was correct.
- PARTIAL: Accept part of the attack. Provide partially corrected count.

After addressing all attacks, provide REVISED fixture counts incorporating all concessions.

CRITICAL: Respond with ONLY a valid JSON object. No markdown. No explanation.

Output format:
{
  "responses": [
    {
      "attack_id": "ATK-001",
      "verdict": "concede|defend|partial",
      "explanation": "why you agree or disagree",
      "revised_count": 6,
      "revised_area": "Floor 2 Break Room"
    }
  ],
  "revised_fixture_counts": {
    "A": {"total": 54, "delta": "+2", "reason": "Conceded ATK-003"},
    "B": {"total": 18, "delta": "0", "reason": "No changes"},
    "C": {"total": 6, "delta": "+6", "reason": "Conceded ATK-001 — missed break room"}
  },
  "revised_grand_total": 148,
  "reasoning": "3 of 4 attacks valid. Grand total increased from 142 to 148."
}"""

        user_prompt = f"""Counter's original counts:
{orig_text}
Counter's original grand total: {counter_output.get('grand_total_fixtures', 0)}

Checker's attacks:
{attacks_text}

Address each attack and provide revised counts."""

        response = self.model_router.complete(
            task_type="takeoff_reconciler",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3000
        )

        try:
            data = extract_json_from_response(response.content, "RECONCILER")
            concessions = sum(1 for r in data.get("responses", []) if r.get("verdict") == "concede")
            print(f"[RECONCILER] {len(data.get('responses', []))} responses ({concessions} concessions), revised total: {data.get('revised_grand_total', 'unknown')}")
            return TakeoffResponse(
                agent_role="reconciler",
                data=data,
                raw_response=response.content,
                reasoning=data.get("reasoning")
            )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[RECONCILER] ERROR: Failed to parse JSON response: {e}")
            return TakeoffResponse(agent_role="reconciler", data={}, raw_response=response.content)


# ─── Judge Agent ──────────────────────────────────────────────────────────────

class Judge:
    """Evaluates the final takeoff against constitutional rules.

    Equivalent to Judge in Sydyn — constitutional quality gate.
    """

    def __init__(self, model_router, constitution: dict):
        self.model_router = model_router
        self.constitution = constitution

    def evaluate(
        self,
        counter_output: dict,
        checker_attacks: List[Dict],
        reconciler_output: Optional[dict],
        fixture_schedule: FixtureSchedule,
        mode: str = "fast"
    ) -> Dict:
        """Evaluate the complete takeoff against constitutional rules.

        Args:
            counter_output: Counter's fixture counts
            checker_attacks: Checker's attack list
            reconciler_output: Reconciler's responses (None in fast mode)
            fixture_schedule: Fixture schedule for traceability check
            mode: "fast" | "strict" | "liability"

        Returns:
            Dict with verdict, violations, flags, and ruling summary
        """
        # Build hard rules text
        hard_rules_text = "\n".join([
            f"{i+1}. {rule['name']}: {rule['description']}"
            for i, rule in enumerate(self.constitution["hard_rules"])
        ])

        # Final counts (reconciler's revised if available, else counter's)
        if reconciler_output and reconciler_output.get("revised_fixture_counts"):
            final_counts = reconciler_output["revised_fixture_counts"]
            grand_total = reconciler_output.get("revised_grand_total", 0)
            source = "Reconciler (post-adversarial)"
        else:
            final_counts_list = counter_output.get("fixture_counts", [])
            final_counts = {fc.get("type_tag"): {"total": fc.get("total")} for fc in final_counts_list}
            grand_total = counter_output.get("grand_total_fixtures", 0)
            source = "Counter (pre-adversarial)"

        # Areas
        areas = counter_output.get("areas_covered", [])

        # Schedule tags
        schedule_tags = list(fixture_schedule.fixtures.keys())

        # Attack summary
        critical_attacks = [a for a in checker_attacks if a.get("severity") == "critical"]
        unresolved = []
        if reconciler_output:
            resolved_ids = {r.get("attack_id") for r in reconciler_output.get("responses", [])}
            unresolved = [a for a in checker_attacks if a.get("attack_id") not in resolved_ids]

        system_prompt = f"""You are the JUDGE agent in the Takeoff adversarial system — the final constitutional authority.

Your role: Evaluate the takeoff against all 6 hard rules and issue a final ruling.

MODE: {mode.upper()}

HARD RULES (must enforce):
{hard_rules_text}

CRITICAL: Respond with ONLY a valid JSON object. No markdown. No explanation before or after.

Output format:
{{
  "verdict": "PASS|WARN|BLOCK",
  "violations": [
    {{
      "rule": "rule name",
      "severity": "FATAL|MAJOR|MINOR",
      "explanation": "specific reason for violation"
    }}
  ],
  "approved_counts": {{
    "A": 54,
    "B": 18
  }},
  "flags": ["list of warnings or items to verify"],
  "ruling_summary": "one paragraph ruling"
}}

PASS: No major violations — takeoff approved
WARN: Minor violations — takeoff acceptable with noted caveats
BLOCK: Fatal violations — takeoff must be redone"""

        user_prompt = f"""Final fixture counts (source: {source}):
{json.dumps(final_counts, indent=2)}

Grand total: {grand_total} fixtures
Areas covered: {areas}
Fixture schedule type tags: {schedule_tags}
Critical Checker attacks: {len(critical_attacks)}
Unresolved attacks: {len(unresolved)}

Evaluate against all 6 constitutional hard rules and issue your ruling."""

        response = self.model_router.complete(
            task_type="takeoff_judge",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000
        )

        try:
            data = extract_json_from_response(response.content, "JUDGE")
            verdict = data.get("verdict", "WARN")
            print(f"[JUDGE] Verdict: {verdict} | {len(data.get('violations', []))} violations | {len(data.get('flags', []))} flags")
            return {
                "verdict": verdict,
                "violations": data.get("violations", []),
                "approved_counts": data.get("approved_counts", {}),
                "flags": data.get("flags", []),
                "ruling_summary": data.get("ruling_summary", ""),
                "raw_response": response.content
            }
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[JUDGE] ERROR: Failed to parse JSON response: {e}")
            print(f"[JUDGE] Raw response snippet: {response.content[:200]}")
            return {
                "verdict": "BLOCK",
                "violations": [{"rule": "Parse Error", "severity": "FATAL", "explanation": f"Judge produced invalid JSON: {e}"}],
                "approved_counts": {},
                "flags": ["Judge response parse error — takeoff blocked by default"],
                "ruling_summary": "Parse error — blocking by default. Resubmit for review.",
                "raw_response": response.content
            }
