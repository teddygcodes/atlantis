"""Takeoff main engine — orchestrates the full adversarial lighting takeoff pipeline.

Mirrors sydyn/engine.py exactly:
- Same phase structure (extract → counter → checker → reconciler → judge → confidence)
- Same fast/strict/liability modes
- Same status callback pattern for SSE streaming
- Same result dict structure
"""

import json
import time
import uuid
from typing import Optional, List, Dict

from core.models import ModelRouter
from takeoff.schema import TakeoffDB
from takeoff.constitution import get_constitution, enforce_constitution
from takeoff.confidence import calculate_confidence, format_confidence_explanation
from takeoff.extraction import (
    FixtureSchedule, AreaCount, PlanNote, PanelData,
    extract_fixture_schedule, extract_rcp_counts, extract_plan_notes, extract_panel_schedule
)
from takeoff.agents import Counter, Checker, Reconciler, Judge


class TakeoffEngine:
    """Main orchestrator for adversarial lighting takeoff jobs."""

    def __init__(
        self,
        db_path: str = "takeoff.db",
        model_router: Optional[ModelRouter] = None
    ):
        """Initialize the Takeoff engine.

        Args:
            db_path: Path to SQLite database
            model_router: Optional ModelRouter (will create if None)
        """
        self.db = TakeoffDB(db_path)
        self.constitution = get_constitution()

        if model_router:
            self.model_router = model_router
        else:
            self.model_router = ModelRouter()

        # Initialize agents
        self.counter = Counter(self.model_router)
        self.checker = Checker(self.model_router)
        self.reconciler = Reconciler(self.model_router)
        self.judge = Judge(self.model_router, self.constitution)

    def run_takeoff(
        self,
        snippets: List[Dict],
        mode: Optional[str] = "strict",
        drawing_name: Optional[str] = None,
        status_callback=None
    ) -> Dict:
        """Execute the full adversarial takeoff pipeline.

        Args:
            snippets: List of snippet dicts with id, label, sub_label, image_data (base64), page_number
            mode: "fast" | "strict" | "liability"
            drawing_name: Optional display name for the drawing set
            status_callback: Optional callback for SSE status updates

        Returns:
            Dict with fixture counts, confidence, adversarial log, and metadata
        """
        self._status_callback = status_callback

        def emit(message: str):
            if status_callback:
                status_callback(message)
            print(f"[TAKEOFF] {message}")

        # Generate job ID
        job_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        emit(f"Starting takeoff job {job_id}...")

        # ─── Step 1: Validate snippets ───────────────────────────────────────
        emit("Validating snippet set...")

        fixture_snippets = [s for s in snippets if s.get("label") == "fixture_schedule"]
        rcp_snippets = [s for s in snippets if s.get("label") == "rcp"]
        notes_snippets = [s for s in snippets if s.get("label") == "plan_notes"]
        panel_snippets = [s for s in snippets if s.get("label") == "panel_schedule"]

        if not fixture_snippets:
            return {
                "job_id": job_id,
                "error": "insufficient_snippets",
                "message": "At least 1 fixture_schedule snippet is required."
            }

        if not rcp_snippets:
            return {
                "job_id": job_id,
                "error": "insufficient_snippets",
                "message": "At least 1 rcp snippet is required."
            }

        emit(f"Snippet set valid: {len(fixture_snippets)} schedule(s), {len(rcp_snippets)} RCP(s), {len(notes_snippets)} note(s), {len(panel_snippets)} panel(s)")

        # Create job record
        self.db.create_job(
            job_id=job_id,
            mode=mode,
            drawing_name=drawing_name,
            snippet_count=len(snippets)
        )
        self.db.store_snippets(job_id, snippets)

        # ─── Step 2: Extract fixture schedule ────────────────────────────────
        emit("Extracting fixture schedule...")

        fixture_schedule = FixtureSchedule()
        for fs_snippet in fixture_snippets:
            image_data = fs_snippet.get("image_data", "")
            if image_data:
                extracted = extract_fixture_schedule(image_data)
                # Merge if multiple schedule snippets
                fixture_schedule.fixtures.update(extracted.fixtures)
                fixture_schedule.warnings.extend(extracted.warnings)
                if not fixture_schedule.raw_notes:
                    fixture_schedule.raw_notes = extracted.raw_notes

        emit(f"Fixture schedule: {len(fixture_schedule.fixtures)} type tags extracted")

        # H2: Fail loudly if extraction produced no fixtures (API error, blank image, etc.)
        if not fixture_schedule.fixtures:
            warning_text = "; ".join(fixture_schedule.warnings) if fixture_schedule.warnings else "unknown reason"
            emit(f"ERROR: Fixture schedule extraction yielded 0 fixtures — {warning_text}")
            return {
                "job_id": job_id,
                "error": "extraction_failed",
                "message": f"Fixture schedule extraction failed — no fixture types found. {warning_text}"
            }

        self.db.store_fixture_schedule(job_id, {"fixtures": fixture_schedule.fixtures})

        # ─── Step 3: Extract RCP counts ───────────────────────────────────────
        area_counts: List[AreaCount] = []
        for rcp_snippet in rcp_snippets:
            area_label = rcp_snippet.get("sub_label") or f"Area {len(area_counts) + 1}"
            image_data = rcp_snippet.get("image_data", "")
            emit(f"Counting fixtures in '{area_label}'...")
            if image_data:
                area_count = extract_rcp_counts(image_data, fixture_schedule, area_label)
                area_counts.append(area_count)

        # ─── Step 4: Extract plan notes ───────────────────────────────────────
        plan_notes: List[PlanNote] = []
        for notes_snippet in notes_snippets:
            image_data = notes_snippet.get("image_data", "")
            if image_data:
                emit("Extracting plan notes...")
                notes = extract_plan_notes(image_data)
                plan_notes.extend(notes)

        # ─── Step 5: Extract panel schedule ───────────────────────────────────
        panel_data: Optional[PanelData] = None
        for panel_snippet in panel_snippets:
            image_data = panel_snippet.get("image_data", "")
            if image_data:
                emit("Extracting panel schedule for cross-reference...")
                panel_data = extract_panel_schedule(image_data)
                break  # Use first panel schedule

        # ─── Step 6: Run agent pipeline ───────────────────────────────────────
        if mode == "fast":
            result = self._run_fast_mode(
                job_id, fixture_schedule, area_counts, plan_notes, panel_data,
                rcp_snippets, emit, start_time
            )
        elif mode in ("strict", "liability"):
            result = self._run_strict_mode(
                job_id, fixture_schedule, area_counts, plan_notes, panel_data,
                rcp_snippets, emit, start_time, mode
            )
        else:
            raise ValueError(f"Unknown mode '{mode}'. Must be 'fast', 'strict', or 'liability'.")

        # Update job status
        elapsed_ms = int((time.time() - start_time) * 1000)
        self.db.update_job_status(job_id, "complete", latency_ms=elapsed_ms)
        result["latency_ms"] = elapsed_ms

        return result

    def _run_fast_mode(
        self,
        job_id: str,
        fixture_schedule: FixtureSchedule,
        area_counts: List[AreaCount],
        plan_notes: List[PlanNote],
        panel_data: Optional[PanelData],
        rcp_snippets: List[Dict],
        emit,
        start_time: float
    ) -> Dict:
        """Run fast mode: Counter + Checker + Judge (no Reconciler)."""
        print(f"[TAKEOFF] Running FAST mode pipeline")

        # Counter
        emit("Counter analyzing drawings and building fixture count...")
        counter_response = self.counter.generate_count(fixture_schedule, area_counts, plan_notes, panel_data)
        counter_output = counter_response.data
        emit(f"Counter produced count: {counter_output.get('grand_total_fixtures', 0)} total fixtures")

        # Short-circuit: zero fixtures means blank/unreadable drawing
        if counter_output.get("grand_total_fixtures", 0) == 0:
            print(f"[TAKEOFF] WARNING: Counter found 0 fixtures — blank or unreadable drawing")
            return {
                "job_id": job_id, "verdict": "BLOCK", "confidence_score": 0.25,
                "confidence_band": "VERY_LOW", "grand_total": 0, "fixture_counts": [],
                "checker_attacks": [], "reconciler_responses": [], "violations": [],
                "flags": ["No fixtures detected. Check that snippets contain a fixture schedule and RCP data."],
                "mode": "fast", "error": "No fixtures detected in provided snippets."
            }

        # Checker
        emit("Checker reviewing count for errors and omissions...")
        checker_response = self.checker.generate_attacks(
            counter_output, fixture_schedule, area_counts, plan_notes, panel_data
        )
        checker_attacks = checker_response.data.get("attacks", [])
        emit(f"Checker found {len(checker_attacks)} issues ({checker_response.data.get('critical_count', 0)} critical)")

        # No Reconciler in fast mode
        reconciler_output = None

        # Judge
        emit("Judge evaluating against constitutional rules...")
        judge_result = self.judge.evaluate(
            counter_output, checker_attacks, reconciler_output, fixture_schedule, mode="fast"
        )
        emit(f"Judge verdict: {judge_result.get('verdict')}")

        # Confidence
        fixture_counts_list = counter_output.get("fixture_counts", [])
        areas_covered = counter_output.get("areas_covered", [])

        confidence_result = calculate_confidence(
            fixture_counts=fixture_counts_list,
            areas_covered=areas_covered,
            rcp_snippets=rcp_snippets,
            fixture_schedule={"fixtures": fixture_schedule.fixtures},
            checker_attacks=checker_attacks,
            reconciler_responses=[],
            constitutional_violations=judge_result.get("violations", []),
            mode="fast",
            has_panel_schedule=panel_data is not None,
            has_plan_notes=len(plan_notes) > 0,
            notes_addressed=(
                len(plan_notes) == 0 or
                any(
                    note.text.lower()[:50] in (counter_response.reasoning or "").lower()
                    or any(
                        kw in (counter_response.reasoning or "").lower()
                        for kw in note.text.lower().split()
                        if len(kw) > 5
                    )
                    for note in plan_notes
                    if note.text
                )
            )
        )

        # Persist
        grand_total = counter_output.get("grand_total_fixtures", 0)
        self.db.store_fixture_counts(job_id, fixture_counts_list)
        self.db.store_adversarial_log(job_id, checker_attacks, [])
        self.db.store_result(
            job_id, grand_total,
            confidence_result["score"], confidence_result["band"],
            confidence_result["features_json"],
            judge_result.get("violations", []),
            judge_result.get("flags", []),
            judge_result.get("verdict", "WARN")
        )

        return self._build_result(
            job_id, counter_output, checker_attacks, None, reconciler_output,
            judge_result, confidence_result, fixture_schedule, "fast"
        )

    def _run_strict_mode(
        self,
        job_id: str,
        fixture_schedule: FixtureSchedule,
        area_counts: List[AreaCount],
        plan_notes: List[PlanNote],
        panel_data: Optional[PanelData],
        rcp_snippets: List[Dict],
        emit,
        start_time: float,
        mode: str
    ) -> Dict:
        """Run strict/liability mode: Counter + Checker + Reconciler + Judge."""
        print(f"[TAKEOFF] Running {mode.upper()} mode pipeline")

        # Counter
        emit("Counter analyzing drawings and building fixture count...")
        counter_response = self.counter.generate_count(fixture_schedule, area_counts, plan_notes, panel_data)
        counter_output = counter_response.data
        emit(f"Counter: {counter_output.get('grand_total_fixtures', 0)} total fixtures")

        # Short-circuit: zero fixtures means blank/unreadable drawing
        if counter_output.get("grand_total_fixtures", 0) == 0:
            print(f"[TAKEOFF] WARNING: Counter found 0 fixtures — blank or unreadable drawing")
            return {
                "job_id": job_id, "verdict": "BLOCK", "confidence_score": 0.25,
                "confidence_band": "VERY_LOW", "grand_total": 0, "fixture_counts": [],
                "checker_attacks": [], "reconciler_responses": [], "violations": [],
                "flags": ["No fixtures detected. Check that snippets contain a fixture schedule and RCP data."],
                "mode": mode, "error": "No fixtures detected in provided snippets."
            }

        # Checker
        emit("Checker independently reviewing count...")
        checker_response = self.checker.generate_attacks(
            counter_output, fixture_schedule, area_counts, plan_notes, panel_data
        )
        checker_attacks = checker_response.data.get("attacks", [])
        emit(f"Checker found {len(checker_attacks)} issues ({checker_response.data.get('critical_count', 0)} critical)")

        # Reconciler
        emit(f"Reconciler addressing {len(checker_attacks)} attacks...")
        reconciler_response = self.reconciler.address_attacks(
            counter_output, checker_attacks, fixture_schedule, area_counts
        )
        reconciler_output = reconciler_response.data
        reconciler_responses_list = reconciler_output.get("responses", [])
        revised_total = reconciler_output.get("revised_grand_total", counter_output.get("grand_total_fixtures", 0))
        emit(f"Reconciler: revised total = {revised_total}")

        # Judge
        emit("Judge evaluating final takeoff against constitutional rules...")
        judge_result = self.judge.evaluate(
            counter_output, checker_attacks, reconciler_output, fixture_schedule, mode=mode
        )
        emit(f"Judge verdict: {judge_result.get('verdict')}")

        # Confidence
        fixture_counts_list = counter_output.get("fixture_counts", [])
        areas_covered = counter_output.get("areas_covered", [])

        confidence_result = calculate_confidence(
            fixture_counts=fixture_counts_list,
            areas_covered=areas_covered,
            rcp_snippets=rcp_snippets,
            fixture_schedule={"fixtures": fixture_schedule.fixtures},
            checker_attacks=checker_attacks,
            reconciler_responses=reconciler_responses_list,
            constitutional_violations=judge_result.get("violations", []),
            mode=mode,
            has_panel_schedule=panel_data is not None,
            has_plan_notes=len(plan_notes) > 0,
            notes_addressed=(
                len(plan_notes) == 0 or
                any(
                    note.text.lower()[:50] in (counter_response.reasoning or "").lower()
                    or any(
                        kw in (counter_response.reasoning or "").lower()
                        for kw in note.text.lower().split()
                        if len(kw) > 5
                    )
                    for note in plan_notes
                    if note.text
                )
            )
        )

        # Persist
        grand_total = reconciler_output.get("revised_grand_total", counter_output.get("grand_total_fixtures", 0))
        self.db.store_fixture_counts(job_id, fixture_counts_list)
        self.db.store_adversarial_log(job_id, checker_attacks, reconciler_responses_list)
        self.db.store_result(
            job_id, grand_total,
            confidence_result["score"], confidence_result["band"],
            confidence_result["features_json"],
            judge_result.get("violations", []),
            judge_result.get("flags", []),
            judge_result.get("verdict", "WARN")
        )

        return self._build_result(
            job_id, counter_output, checker_attacks, reconciler_output, reconciler_output,
            judge_result, confidence_result, fixture_schedule, mode
        )

    def _build_result(
        self,
        job_id: str,
        counter_output: dict,
        checker_attacks: List[Dict],
        reconciler_response,
        reconciler_output: Optional[dict],
        judge_result: dict,
        confidence_result: dict,
        fixture_schedule: FixtureSchedule,
        mode: str
    ) -> Dict:
        """Build the final result dict for API/CLI consumers."""
        # Use reconciler's revised counts if available
        if reconciler_output and reconciler_output.get("revised_grand_total"):
            grand_total = reconciler_output["revised_grand_total"]
            revised_counts = reconciler_output.get("revised_fixture_counts", {})
        else:
            grand_total = counter_output.get("grand_total_fixtures", 0)
            revised_counts = {}

        # Build final fixture count table for display
        fixture_table = []
        for fc in counter_output.get("fixture_counts", []):
            tag = fc.get("type_tag", "")
            revised = revised_counts.get(tag, {})
            final_total = revised.get("total", fc.get("total", 0)) if revised else fc.get("total", 0)
            delta = revised.get("delta", "0") if revised else "0"

            schedule_entry = fixture_schedule.fixtures.get(tag, {})
            desc = schedule_entry.get("description", fc.get("description", "")) if isinstance(schedule_entry, dict) else fc.get("description", "")

            fixture_table.append({
                "type_tag": tag,
                "description": desc,
                "total": final_total,
                "delta": delta,
                "difficulty": fc.get("difficulty", "S"),
                "accessories": fc.get("accessories", []),
                "flags": fc.get("flags", []),
                "counts_by_area": fc.get("counts_by_area", {})
            })

        # Adversarial log summary
        adv_log = []
        for attack in checker_attacks:
            resolution = None
            verdict_text = None
            if reconciler_output:
                for resp in reconciler_output.get("responses", []):
                    if resp.get("attack_id") == attack.get("attack_id"):
                        resolution = resp.get("explanation")
                        verdict_text = resp.get("verdict")
                        break
            adv_log.append({
                "attack_id": attack.get("attack_id"),
                "severity": attack.get("severity"),
                "category": attack.get("category"),
                "description": attack.get("description"),
                "suggested_correction": attack.get("suggested_correction"),
                "resolution": resolution,
                "verdict": verdict_text
            })

        return {
            "job_id": job_id,
            "mode": mode,
            "grand_total": grand_total,
            "fixture_table": fixture_table,
            "areas_covered": counter_output.get("areas_covered", []),
            "confidence": confidence_result["score"],
            "confidence_band": confidence_result["band"],
            "confidence_explanation": format_confidence_explanation(confidence_result),
            "verdict": judge_result.get("verdict"),
            "violations": judge_result.get("violations", []),
            "flags": judge_result.get("flags", []),
            "ruling_summary": judge_result.get("ruling_summary", ""),
            "adversarial_log": adv_log,
            "agent_counts": {
                "counter_types": len(counter_output.get("fixture_counts", [])),
                "checker_attacks": len(checker_attacks),
                "reconciler_responses": len(reconciler_output.get("responses", [])) if reconciler_output else 0
            }
        }
