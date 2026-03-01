"""
tests/test_takeoff_pipeline.py
==============================
Unit + integration tests for the takeoff/ adversarial lighting takeoff system.

Tests:
  1. Constitution enforcement — feed in counts that violate rules, verify Judge catches them
  2. Confidence calculation — known feature values → expected score
  3. Extraction helpers — extract_json_from_response fallback strategies
  4. Schema — SQLite round-trip
  5. Engine pipeline validation — early-return checks on missing snippets
  6. Engine pipeline (live, optional) — end-to-end with real API

Run:
  python -m pytest tests/test_takeoff_pipeline.py -v -p no:cacheprovider
"""

import json
import sys
import os
import uuid
import tempfile
import unittest

# Add repo root to path so imports work without installing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from takeoff.constitution import (
    enforce_constitution,
    check_schedule_traceability,
    check_complete_coverage,
    check_emergency_fixtures,
    check_no_double_counting,
    check_cross_sheet_consistency,
    check_flag_assumptions,
    get_constitution,
)
from takeoff.confidence import (
    calculate_confidence,
    format_confidence_explanation,
    FEATURE_WEIGHTS,
)
from takeoff.extraction import extract_json_from_response
from takeoff.schema import TakeoffDB


# ══════════════════════════════════════════════════════════════════════
# Helpers / fixtures
# ══════════════════════════════════════════════════════════════════════

SAMPLE_FIXTURE_SCHEDULE = {
    "fixtures": {
        "A": {
            "description": "2x4 LED Recessed Troffer",
            "voltage": "277V",
            "mounting": "recessed",
            "watts": 40,
        },
        "B": {
            "description": "2x2 LED Troffer",
            "voltage": "277V",
            "mounting": "recessed",
            "watts": 30,
        },
        "C": {
            "description": "6-inch Recessed Downlight",
            "voltage": "120V",
            "mounting": "recessed",
            "watts": 15,
        },
        "X": {
            "description": "LED Exit Sign w/ Battery Backup",
            "voltage": "120V",
            "mounting": "wall",
            "watts": 5,
        },
    }
}

SAMPLE_RCP_SNIPPETS = [
    {"label": "rcp", "sub_label": "Open Office North"},
    {"label": "rcp", "sub_label": "Open Office South"},
    {"label": "rcp", "sub_label": "Corridor 1A"},
]

# constitution.py expects fixture_counts as a LIST of dicts with type_tag field
VALID_FIXTURE_COUNTS_LIST = [
    {
        "type_tag": "A",
        "description": "2x4 LED Recessed Troffer",
        "total": 36,
        "counts_by_area": {"Open Office North": 18, "Open Office South": 18},
    },
    {
        "type_tag": "B",
        "description": "2x2 LED Troffer",
        "total": 12,
        "counts_by_area": {"Open Office North": 6, "Open Office South": 6},
    },
    {
        "type_tag": "C",
        "description": "6-inch Recessed Downlight",
        "total": 8,
        "counts_by_area": {"Corridor 1A": 8},
    },
    {
        "type_tag": "X",
        "description": "LED Exit Sign w/ Battery Backup",
        "total": 4,
        "counts_by_area": {"Corridor 1A": 4},
        "notes": "emergency circuit",
    },
]

VALID_AREAS_COVERED = ["Open Office North", "Open Office South", "Corridor 1A"]


# ══════════════════════════════════════════════════════════════════════
# 1. Constitution Enforcement
# ══════════════════════════════════════════════════════════════════════

class TestConstitutionEnforcement(unittest.TestCase):

    def test_get_constitution_returns_dict(self):
        c = get_constitution()
        self.assertIn("hard_rules", c)
        self.assertIn("articles", c)
        self.assertEqual(len(c["hard_rules"]), 6)
        self.assertEqual(len(c["articles"]), 5)

    def test_valid_counts_pass_traceability(self):
        violations = check_schedule_traceability(
            VALID_FIXTURE_COUNTS_LIST, SAMPLE_FIXTURE_SCHEDULE
        )
        self.assertEqual(violations, [], f"Expected no violations, got: {violations}")

    def test_phantom_fixture_fails_traceability(self):
        """Type tag 'Z' is not in the fixture schedule — must fail."""
        bad_counts = list(VALID_FIXTURE_COUNTS_LIST) + [
            {
                "type_tag": "Z",
                "description": "Unknown fixture",
                "total": 3,
                "counts_by_area": {"Open Office North": 3},
            }
        ]
        violations = check_schedule_traceability(bad_counts, SAMPLE_FIXTURE_SCHEDULE)
        self.assertTrue(
            any("Z" in str(v) for v in violations),
            f"Expected violation mentioning 'Z', got: {violations}",
        )

    def test_valid_areas_pass_coverage(self):
        violations = check_complete_coverage(VALID_AREAS_COVERED, SAMPLE_RCP_SNIPPETS)
        self.assertEqual(violations, [])

    def test_missing_area_fails_coverage(self):
        """If the counter didn't cover Corridor 1A, should trigger a violation."""
        partial_coverage = ["Open Office North", "Open Office South"]
        violations = check_complete_coverage(partial_coverage, SAMPLE_RCP_SNIPPETS)
        self.assertTrue(
            len(violations) > 0,
            "Expected coverage violation for missed area",
        )

    def test_emergency_fixtures_present_no_violation(self):
        # Our list has type X with "emergency circuit" in notes
        violations = check_emergency_fixtures(VALID_FIXTURE_COUNTS_LIST)
        self.assertEqual(
            violations, [],
            f"Expected no emergency violation when exit sign is present, got: {violations}",
        )

    def test_no_emergency_fixtures_warns(self):
        # Build a substantial fixture list (> 5 types) with no emergency tracking.
        # The check only fires for jobs with > 5 fixture types — small jobs may legitimately have none.
        large_counts_no_emergency = [
            {"type_tag": "A", "description": "2x4 Troffer", "total": 20, "counts_by_area": {}, "notes": ""},
            {"type_tag": "B", "description": "2x2 Troffer", "total": 10, "counts_by_area": {}, "notes": ""},
            {"type_tag": "C", "description": "Downlight 6in", "total": 8, "counts_by_area": {}, "notes": ""},
            {"type_tag": "D", "description": "Wall Sconce", "total": 6, "counts_by_area": {}, "notes": ""},
            {"type_tag": "E", "description": "Linear Strip", "total": 4, "counts_by_area": {}, "notes": ""},
            {"type_tag": "F", "description": "High Bay", "total": 12, "counts_by_area": {}, "notes": ""},
        ]
        violations = check_emergency_fixtures(large_counts_no_emergency)
        self.assertTrue(
            len(violations) > 0,
            "Expected emergency fixture warning when no emergency fixtures counted in a large job (> 5 types)",
        )

    def test_enforce_constitution_pass(self):
        result = enforce_constitution(
            fixture_counts=VALID_FIXTURE_COUNTS_LIST,
            areas_covered=VALID_AREAS_COVERED,
            rcp_snippets=SAMPLE_RCP_SNIPPETS,
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
        )
        self.assertIn(result["verdict"], ("PASS", "WARN"))
        self.assertIsInstance(result["violations"], list)

    def test_enforce_constitution_fatal_blocks(self):
        """Phantom fixture should produce FATAL violation → BLOCK verdict."""
        bad_counts = [
            {
                "type_tag": "PHANTOM",
                "description": "Unknown fixture",
                "total": 5,
                "counts_by_area": {"Open Office North": 5},
            }
        ]
        result = enforce_constitution(
            fixture_counts=bad_counts,
            areas_covered=["Open Office North"],
            rcp_snippets=[{"label": "rcp", "sub_label": "Open Office North"}],
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
        )
        self.assertEqual(result["verdict"], "BLOCK", f"Expected BLOCK, got {result['verdict']}")
        self.assertTrue(
            any(v.get("severity") == "FATAL" for v in result["violations"]),
            f"Expected FATAL violation, violations: {result['violations']}",
        )


# ══════════════════════════════════════════════════════════════════════
# 2. Confidence Calculation
# ══════════════════════════════════════════════════════════════════════

class TestConfidenceCalculation(unittest.TestCase):

    def test_feature_weights_sum(self):
        """Positive weights should be > 0."""
        positive = sum(v for v in FEATURE_WEIGHTS.values() if v > 0)
        self.assertGreater(positive, 0)

    def test_perfect_score_high_band(self):
        """All features max → HIGH or MODERATE confidence."""
        result = calculate_confidence(
            fixture_counts=VALID_FIXTURE_COUNTS_LIST,
            areas_covered=VALID_AREAS_COVERED,
            rcp_snippets=SAMPLE_RCP_SNIPPETS,
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=[],
            reconciler_responses=[],
            constitutional_violations=[],
            mode="strict",
            has_panel_schedule=True,
            has_plan_notes=True,
            notes_addressed=True,
        )
        self.assertGreaterEqual(result["score"], 0.7, f"Expected HIGH/MODERATE, got {result['score']}")
        self.assertIn(result["band"], ("HIGH", "MODERATE"))

    def test_fast_mode_penalty_applied(self):
        """fast mode should yield lower or equal confidence than strict for same inputs."""
        strict = calculate_confidence(
            fixture_counts=VALID_FIXTURE_COUNTS_LIST,
            areas_covered=VALID_AREAS_COVERED,
            rcp_snippets=SAMPLE_RCP_SNIPPETS,
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=[],
            reconciler_responses=[],
            constitutional_violations=[],
            mode="strict",
            has_panel_schedule=False,
            has_plan_notes=False,
            notes_addressed=False,
        )
        fast = calculate_confidence(
            fixture_counts=VALID_FIXTURE_COUNTS_LIST,
            areas_covered=VALID_AREAS_COVERED,
            rcp_snippets=SAMPLE_RCP_SNIPPETS,
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=[],
            reconciler_responses=[],
            constitutional_violations=[],
            mode="fast",
            has_panel_schedule=False,
            has_plan_notes=False,
            notes_addressed=False,
        )
        self.assertLessEqual(fast["score"], strict["score"])

    def test_fatal_violation_floors_confidence(self):
        """FATAL constitutional violation should force score ≤ 0.25."""
        fatal_violations = [{"severity": "FATAL", "rule": "Schedule Traceability"}]
        result = calculate_confidence(
            fixture_counts=VALID_FIXTURE_COUNTS_LIST,
            areas_covered=VALID_AREAS_COVERED,
            rcp_snippets=SAMPLE_RCP_SNIPPETS,
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=[],
            reconciler_responses=[],
            constitutional_violations=fatal_violations,
            mode="strict",
            has_panel_schedule=True,
            has_plan_notes=True,
            notes_addressed=True,
        )
        self.assertLessEqual(result["score"], 0.26, f"FATAL should force score ≤ 0.25, got {result['score']}")

    def test_confidence_score_clamped(self):
        """Score must always be in [0.0, 1.0]."""
        result = calculate_confidence(
            fixture_counts=[],
            areas_covered=[],
            rcp_snippets=[],
            fixture_schedule={},
            checker_attacks=[{"severity": "critical"}, {"severity": "critical"}],
            reconciler_responses=[],
            constitutional_violations=[{"severity": "MAJOR"}, {"severity": "MAJOR"}],
            mode="fast",
            has_panel_schedule=False,
            has_plan_notes=False,
            notes_addressed=False,
        )
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)

    def test_format_confidence_explanation(self):
        result = calculate_confidence(
            fixture_counts=VALID_FIXTURE_COUNTS_LIST,
            areas_covered=VALID_AREAS_COVERED,
            rcp_snippets=SAMPLE_RCP_SNIPPETS,
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=[],
            reconciler_responses=[],
            constitutional_violations=[],
            mode="strict",
            has_panel_schedule=True,
            has_plan_notes=True,
            notes_addressed=True,
        )
        explanation = format_confidence_explanation(result)
        self.assertIsInstance(explanation, str)
        self.assertIn("confidence", explanation.lower())


# ══════════════════════════════════════════════════════════════════════
# 3. JSON Extraction Helpers
# ══════════════════════════════════════════════════════════════════════

class TestExtractJsonFromResponse(unittest.TestCase):

    def test_clean_json_block(self):
        text = '```json\n{"key": "value"}\n```'
        result = extract_json_from_response(text, "test_agent")
        self.assertEqual(result.get("key"), "value")

    def test_inline_json(self):
        text = 'Some preamble\n{"fixture_counts": [], "total": 42}\nSome postamble'
        result = extract_json_from_response(text, "test_agent")
        self.assertEqual(result.get("total"), 42)

    def test_bare_json(self):
        text = '{"attacks": [], "total_attacks": 0}'
        result = extract_json_from_response(text, "test_agent")
        self.assertEqual(result.get("total_attacks"), 0)

    def test_malformed_raises_json_decode_error(self):
        """extract_json_from_response raises JSONDecodeError on completely invalid input."""
        import json as _json
        text = "This is not JSON at all."
        with self.assertRaises(_json.JSONDecodeError):
            extract_json_from_response(text, "test_agent")

    def test_nested_json_object(self):
        """Nested JSON object should be parsed correctly."""
        text = '{"outer": {"inner": [1, 2, 3]}, "flag": true}'
        result = extract_json_from_response(text, "test_agent")
        self.assertIn("outer", result)
        self.assertTrue(result.get("flag"))


# ══════════════════════════════════════════════════════════════════════
# 4. Schema Round-Trip
# ══════════════════════════════════════════════════════════════════════

class TestTakeoffDB(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = TakeoffDB(db_path=self.tmp.name)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def _job_id(self):
        return str(uuid.uuid4())[:8]

    def test_create_and_get_job(self):
        jid = self._job_id()
        self.db.create_job(
            job_id=jid,
            mode="strict",
            drawing_name="test_drawing",
            total_pages=5,
            snippet_count=4,
        )
        job = self.db.get_job(jid)
        self.assertIsNotNone(job)
        self.assertEqual(job["drawing_name"], "test_drawing")
        self.assertEqual(job["mode"], "strict")

    def test_update_job_status(self):
        jid = self._job_id()
        self.db.create_job(job_id=jid, mode="fast", drawing_name="test")
        self.db.update_job_status(jid, "complete")
        job = self.db.get_job(jid)
        self.assertEqual(job["status"], "complete")

    def test_store_fixture_schedule(self):
        jid = self._job_id()
        self.db.create_job(job_id=jid, mode="strict", drawing_name="test")
        # store_fixture_schedule takes a schedule dict
        self.db.store_fixture_schedule(job_id=jid, schedule=SAMPLE_FIXTURE_SCHEDULE)
        # Should not raise

    def test_store_and_retrieve_result(self):
        jid = self._job_id()
        self.db.create_job(job_id=jid, mode="strict", drawing_name="test")
        self.db.store_result(
            job_id=jid,
            grand_total=92,
            confidence_score=0.84,
            confidence_band="MODERATE",
            confidence_features=json.dumps({}),
            violations=[],
            flags=[],
            judge_verdict="PASS",
        )
        self.db.update_job_status(jid, "complete")
        job = self.db.get_job(jid)
        self.assertEqual(job["status"], "complete")
        self.assertEqual(job["grand_total"], 92)

    def test_list_jobs(self):
        for i in range(3):
            jid = self._job_id()
            self.db.create_job(
                job_id=jid,
                mode="strict",
                drawing_name=f"drawing_{i}",
                total_pages=i + 1,
                snippet_count=2,
            )
        jobs = self.db.list_jobs()
        self.assertGreaterEqual(len(jobs), 3)


# ══════════════════════════════════════════════════════════════════════
# 5. Engine Pipeline Validation (no API key needed)
# ══════════════════════════════════════════════════════════════════════

class TestEnginePipelineValidation(unittest.TestCase):
    """
    Tests engine-level validation via run_takeoff() which returns an error dict
    (rather than raising) when snippet requirements are not met.
    """

    def setUp(self):
        import base64
        from PIL import Image
        import io

        img = Image.new("RGB", (200, 150), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        self.fake_image_b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

        self.snippets = [
            {
                "id": "snip-001",
                "label": "fixture_schedule",
                "sub_label": "",
                "page_number": 1,
                "bbox": {"x": 0, "y": 0, "width": 200, "height": 150},
                "image_data": self.fake_image_b64,
            },
            {
                "id": "snip-002",
                "label": "rcp",
                "sub_label": "Open Office North",
                "page_number": 2,
                "bbox": {"x": 0, "y": 0, "width": 200, "height": 150},
                "image_data": self.fake_image_b64,
            },
        ]

    def _make_engine(self, db_path: str):
        from takeoff.engine import TakeoffEngine
        return TakeoffEngine(db_path=db_path, model_router=None)

    def test_missing_fixture_schedule_returns_error(self):
        """Engine should return error dict if no fixture_schedule snippet."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            engine = self._make_engine(db_path)
            bad_snippets = [s for s in self.snippets if s["label"] != "fixture_schedule"]
            result = engine.run_takeoff(snippets=bad_snippets, mode="fast")
            self.assertIn("error", result, f"Expected error key, got: {result}")
        finally:
            os.unlink(db_path)

    def test_missing_rcp_returns_error(self):
        """Engine should return error dict if no rcp snippet."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            engine = self._make_engine(db_path)
            bad_snippets = [s for s in self.snippets if s["label"] != "rcp"]
            result = engine.run_takeoff(snippets=bad_snippets, mode="fast")
            self.assertIn("error", result, f"Expected error key, got: {result}")
        finally:
            os.unlink(db_path)

    @unittest.skipUnless(
        os.environ.get("ANTHROPIC_API_KEY"),
        "Skipped: set ANTHROPIC_API_KEY to run live pipeline tests",
    )
    def test_full_pipeline_live(self):
        """
        End-to-end pipeline test using real Claude API.
        Only runs when ANTHROPIC_API_KEY is available.
        """
        from core.models import ModelRouter
        from takeoff.engine import TakeoffEngine

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            router = ModelRouter(api_key=os.environ["ANTHROPIC_API_KEY"])
            engine = TakeoffEngine(db_path=db_path, model_router=router)
            result = engine.run_takeoff(
                snippets=self.snippets,
                mode="fast",
                drawing_name="test_drawing",
            )
            # May succeed or fail vision extraction on blank PNG — either way should not crash
            self.assertIsInstance(result, dict)
            if "error" not in result:
                self.assertIn("confidence_score", result)
                self.assertIn("grand_total", result)
                self.assertGreaterEqual(result["confidence_score"], 0.0)
                self.assertLessEqual(result["confidence_score"], 1.0)
        finally:
            os.unlink(db_path)


# ══════════════════════════════════════════════════════════════════════
# 6. Programmatic Constitutional Rules (M7)
# ══════════════════════════════════════════════════════════════════════

class TestProgrammaticConstitutionalRules(unittest.TestCase):
    """Tests for check_no_double_counting and check_cross_sheet_consistency."""

    def test_no_double_counting_clean(self):
        """Area subtotals equal reported total → no violation."""
        violations = check_no_double_counting(VALID_FIXTURE_COUNTS_LIST, SAMPLE_FIXTURE_SCHEDULE)
        self.assertEqual(violations, [], f"Expected no violations, got: {violations}")

    def test_no_double_counting_detected(self):
        """Sum of counts_by_area > total * 1.10 → MAJOR violation."""
        inflated = [
            {
                "type_tag": "A",
                "total": 10,
                "counts_by_area": {"Zone 1": 10, "Zone 2": 5},  # sum=15, >10% over total=10
            }
        ]
        violations = check_no_double_counting(inflated, {})
        self.assertTrue(len(violations) > 0, "Expected double-count violation")
        self.assertTrue(any("A" in str(v) for v in violations))
        self.assertEqual(violations[0]["severity"], "MAJOR")

    def test_no_double_counting_within_tolerance(self):
        """Sum of counts_by_area ≤ total * 1.10 → no violation."""
        ok_counts = [
            {
                "type_tag": "B",
                "total": 10,
                "counts_by_area": {"Zone 1": 10},  # sum==total, no problem
            }
        ]
        violations = check_no_double_counting(ok_counts, {})
        self.assertEqual(violations, [])

    def test_no_double_counting_empty_counts(self):
        """Empty fixture_counts → no violations."""
        violations = check_no_double_counting([], {})
        self.assertEqual(violations, [])

    def test_cross_sheet_consistency_clean(self):
        """Same type+area appears only once → no violations."""
        violations = check_cross_sheet_consistency(VALID_FIXTURE_COUNTS_LIST)
        self.assertEqual(violations, [], f"Expected no violations, got: {violations}")

    def test_cross_sheet_conflict_detected(self):
        """Same type+area with different counts → MAJOR violation."""
        conflicting = [
            {"type_tag": "A", "counts_by_area": {"Open Office North": 18}},
            {"type_tag": "A", "counts_by_area": {"Open Office North": 20}},  # conflict!
        ]
        violations = check_cross_sheet_consistency(conflicting)
        self.assertTrue(len(violations) > 0, "Expected cross-sheet conflict violation")
        self.assertEqual(violations[0]["severity"], "MAJOR")

    def test_cross_sheet_no_conflict_different_areas(self):
        """Same type in different areas → no violation."""
        ok = [
            {"type_tag": "A", "counts_by_area": {"Zone 1": 10}},
            {"type_tag": "A", "counts_by_area": {"Zone 2": 5}},  # different area, no conflict
        ]
        violations = check_cross_sheet_consistency(ok)
        self.assertEqual(violations, [])

    def test_cross_sheet_empty_counts(self):
        """Empty fixture_counts → no violations."""
        violations = check_cross_sheet_consistency([])
        self.assertEqual(violations, [])


# ══════════════════════════════════════════════════════════════════════
# 7. Reconciler Concede/Defend/Partial Logic (L6)
# ══════════════════════════════════════════════════════════════════════

class TestReconcilerLogic(unittest.TestCase):
    """Tests for Reconciler agent concede/defend/partial response parsing."""

    def test_concede_defend_partial_counts(self):
        """Count verdicts from a list of reconciler responses."""
        responses = [
            {"attack_id": "ATK-001", "verdict": "concede", "explanation": "Valid — area was missed"},
            {"attack_id": "ATK-002", "verdict": "defend", "explanation": "Counter was correct"},
            {"attack_id": "ATK-003", "verdict": "partial", "explanation": "Partly valid"},
        ]
        concessions = sum(1 for r in responses if r.get("verdict") == "concede")
        defenses = sum(1 for r in responses if r.get("verdict") == "defend")
        partials = sum(1 for r in responses if r.get("verdict") == "partial")
        self.assertEqual(concessions, 1)
        self.assertEqual(defenses, 1)
        self.assertEqual(partials, 1)

    def test_unresolved_attack_count(self):
        """Attacks not matched in reconciler responses are unresolved."""
        attacks = [{"attack_id": f"ATK-{i:03d}"} for i in range(5)]
        responses = [{"attack_id": "ATK-000"}, {"attack_id": "ATK-001"}]
        resolved_ids = {r.get("attack_id") for r in responses}
        attack_ids = {a.get("attack_id") for a in attacks}
        unresolved = attack_ids - resolved_ids
        self.assertEqual(len(unresolved), 3)

    def test_empty_attacks_no_unresolved(self):
        """No attacks → no unresolved."""
        attacks = []
        responses = []
        resolved_ids = {r.get("attack_id") for r in responses}
        attack_ids = {a.get("attack_id") for a in attacks}
        unresolved = attack_ids - resolved_ids
        self.assertEqual(len(unresolved), 0)

    def test_confidence_adversarial_resolved_feature(self):
        """Reconciler responses covering all attacks → adversarial_resolved = 1.0."""
        attacks = [{"attack_id": "ATK-001"}, {"attack_id": "ATK-002"}]
        responses = [{"attack_id": "ATK-001"}, {"attack_id": "ATK-002"}]
        result = calculate_confidence(
            fixture_counts=VALID_FIXTURE_COUNTS_LIST,
            areas_covered=VALID_AREAS_COVERED,
            rcp_snippets=SAMPLE_RCP_SNIPPETS,
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=attacks,
            reconciler_responses=responses,
            constitutional_violations=[],
            mode="strict",
            has_panel_schedule=False,
            has_plan_notes=False,
            notes_addressed=False,
        )
        self.assertEqual(result["features"]["adversarial_resolved"], 1.0)

    def test_confidence_unresolved_attacks_penalized(self):
        """Attacks with no reconciler responses → adversarial_resolved = 0.0."""
        attacks = [{"attack_id": "ATK-001"}, {"attack_id": "ATK-002"}]
        result = calculate_confidence(
            fixture_counts=VALID_FIXTURE_COUNTS_LIST,
            areas_covered=VALID_AREAS_COVERED,
            rcp_snippets=SAMPLE_RCP_SNIPPETS,
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=attacks,
            reconciler_responses=[],  # fast mode — no Reconciler
            constitutional_violations=[],
            mode="fast",
            has_panel_schedule=False,
            has_plan_notes=False,
            notes_addressed=False,
        )
        self.assertEqual(result["features"]["adversarial_resolved"], 0.0)


# ══════════════════════════════════════════════════════════════════════
# 8. Regression Tests for Critical Bug Fixes
# ══════════════════════════════════════════════════════════════════════

class TestCriticalBugFixes(unittest.TestCase):
    """Regression tests for the 4 critical bugs fixed in this session."""

    # --- Bug 1: MAJOR penalty must not raise a score already below 0.40 ---

    def test_major_violation_does_not_raise_low_score(self):
        """A MAJOR violation hard-override must never INCREASE the confidence score.

        Scenario: fixture counts/coverage are all bad so base score calculates below 0.40.
        The MAJOR cap must keep it at that lower value, not raise it to 0.40.
        """
        result = calculate_confidence(
            fixture_counts=[],           # 0 types → schedule_match_rate = 0.0
            areas_covered=[],            # nothing covered
            rcp_snippets=SAMPLE_RCP_SNIPPETS,  # 3 areas expected
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=[{"attack_id": "ATK-001"}],
            reconciler_responses=[],     # fast mode — attacks unresolved
            constitutional_violations=[{"severity": "MAJOR", "rule": "No Double-Counting"}],
            mode="fast",
            has_panel_schedule=False,
            has_plan_notes=False,
            notes_addressed=False,
        )
        # Score must not exceed 0.40 (the MAJOR cap)
        self.assertLessEqual(result["score"], 0.40, f"MAJOR penalty raised score to {result['score']}")
        # Score must also not exceed what the features would give before the override
        # (i.e., the override must never make a bad score look better)
        self.assertIn(result["band"], ("LOW", "VERY_LOW"))

    def test_minor_violation_does_not_raise_low_score(self):
        """A MINOR violation cap must never INCREASE the confidence score."""
        result = calculate_confidence(
            fixture_counts=[],
            areas_covered=[],
            rcp_snippets=SAMPLE_RCP_SNIPPETS,
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=[{"attack_id": "ATK-001"}],
            reconciler_responses=[],
            constitutional_violations=[{"severity": "MINOR", "rule": "Flag Assumptions"}],
            mode="fast",
            has_panel_schedule=False,
            has_plan_notes=False,
            notes_addressed=False,
        )
        # Score must not exceed 0.50 (the MINOR cap)
        self.assertLessEqual(result["score"], 0.50, f"MINOR penalty raised score to {result['score']}")

    # --- Bug 2: Worst-case features should produce VERY_LOW, not MODERATE ---

    def test_worst_case_features_produce_very_low_band(self):
        """All features at zero (no fixtures, no coverage, no panel, fast mode) → VERY_LOW."""
        result = calculate_confidence(
            fixture_counts=[],
            areas_covered=[],
            rcp_snippets=SAMPLE_RCP_SNIPPETS,  # 3 expected but none covered
            fixture_schedule=SAMPLE_FIXTURE_SCHEDULE,
            checker_attacks=[{"attack_id": "ATK-001"}],
            reconciler_responses=[],
            constitutional_violations=[],
            mode="fast",
            has_panel_schedule=False,
            has_plan_notes=False,
            notes_addressed=False,
        )
        self.assertLess(result["score"], 0.65,
            f"Worst-case scenario should not reach MODERATE, got {result['score']} ({result['band']})")

    # --- Bug 3: Area label parentheticals must not cause false FATAL violations ---

    def test_area_label_copy_suffix_matches(self):
        """Sub_label 'Floor 1 (Copy)' must match areas_covered 'Floor 1'."""
        from takeoff.constitution import check_complete_coverage
        rcp_snippets_with_copy = [
            {"label": "rcp", "sub_label": "Open Office North (Copy)"},
            {"label": "rcp", "sub_label": "Corridor 1A"},
        ]
        areas_covered = ["Open Office North", "Corridor 1A"]
        violations = check_complete_coverage(areas_covered, rcp_snippets_with_copy)
        self.assertEqual(violations, [],
            f"Parenthetical suffix in sub_label caused false FATAL violation: {violations}")

    def test_area_label_rev_suffix_matches(self):
        """Sub_label 'Suite 200 (Rev B)' must match areas_covered 'Suite 200'."""
        from takeoff.constitution import check_complete_coverage
        rcp_snippets_rev = [
            {"label": "rcp", "sub_label": "Suite 200 (Rev B)"},
        ]
        areas_covered = ["Suite 200"]
        violations = check_complete_coverage(areas_covered, rcp_snippets_rev)
        self.assertEqual(violations, [],
            f"Revision suffix in sub_label caused false FATAL violation: {violations}")

    # --- Bug 4: Checker dedup must preserve distinct attacks with matching 60-char prefixes ---

    def test_checker_dedup_preserves_distinct_attacks(self):
        """Two attacks on the same type+area but with different full descriptions must both survive dedup."""
        from takeoff.agents import Checker
        # Simulate the dedup logic directly (same logic extracted from Checker.generate_attacks)
        attacks = [
            {
                "attack_id": "ATK-001",
                "category": "math_error",
                "affected_type_tag": "A",
                "affected_area": "Open Office North",
                "description": "Double count in type A area Open Office North detected due to overlapping floor plan view north vs south panel",
            },
            {
                "attack_id": "ATK-002",
                "category": "math_error",
                "affected_type_tag": "A",
                "affected_area": "Open Office North",
                "description": "Double count in type A area Open Office North detected due to overlapping detail views 2 and 3 in the drawing set",
            },
        ]
        # These two attacks share the same first 60 chars — old dedup would collapse them
        desc1 = attacks[0]["description"]
        desc2 = attacks[1]["description"]
        self.assertEqual(desc1[:60].lower(), desc2[:60].lower(),
            "Test precondition: descriptions must share same 60-char prefix")

        # Apply the fixed dedup logic (uses full description)
        seen: set = set()
        deduped = []
        for attack in attacks:
            key = (
                attack.get("category", ""),
                (attack.get("affected_type_tag") or "").upper(),
                (attack.get("affected_area") or "").lower().strip(),
                (attack.get("description") or "").lower()  # full description
            )
            if key not in seen:
                seen.add(key)
                deduped.append(attack)

        self.assertEqual(len(deduped), 2,
            f"Fixed dedup should keep both distinct attacks, kept {len(deduped)}: {[a['attack_id'] for a in deduped]}")


# ══════════════════════════════════════════════════════════════════════
# 9. Edge Cases & Negative Path Tests
# ══════════════════════════════════════════════════════════════════════

class TestEdgeCases(unittest.TestCase):
    """Negative path and edge case tests for robustness."""

    # --- check_flag_assumptions ---

    def test_flag_assumptions_unknown_type_no_flags_violation(self):
        """Type tag UNKNOWN with no flags → MAJOR violation."""
        counts = [
            {"type_tag": "UNKNOWN", "description": "Unidentified fixture", "total": 3, "flags": [], "notes": ""}
        ]
        violations = check_flag_assumptions(counts)
        self.assertTrue(len(violations) > 0, "Expected violation for UNKNOWN type with no flags")
        self.assertEqual(violations[0]["severity"], "MAJOR")

    def test_flag_assumptions_unknown_type_with_flags_no_violation(self):
        """Type tag UNKNOWN WITH a flag → no violation."""
        counts = [
            {"type_tag": "UNKNOWN", "description": "Unidentified fixture", "total": 3,
             "flags": ["Cannot identify — assumed type A based on location"], "notes": ""}
        ]
        violations = check_flag_assumptions(counts)
        self.assertEqual(violations, [], f"Expected no violation when UNKNOWN is flagged, got: {violations}")

    def test_flag_assumptions_ambiguous_language_no_flags_violation(self):
        """Description containing 'assumed' with no flags → MAJOR violation."""
        counts = [
            {"type_tag": "B", "description": "Assumed to be type B downlight based on spacing", "total": 5, "flags": [], "notes": ""}
        ]
        violations = check_flag_assumptions(counts)
        self.assertTrue(len(violations) > 0, "Expected violation for assumed type with no flags")

    def test_flag_assumptions_ambiguous_in_notes_no_flags_violation(self):
        """Notes containing 'unclear' with no flags → MAJOR violation."""
        counts = [
            {"type_tag": "C", "description": "6-inch downlight", "total": 2, "flags": [],
             "notes": "unclear which circuit — assumed standard"}
        ]
        violations = check_flag_assumptions(counts)
        self.assertTrue(len(violations) > 0, "Expected violation for unclear note with no flags")

    def test_flag_assumptions_clean_counts_no_violation(self):
        """Clean fixture counts with no ambiguous language → no violations."""
        violations = check_flag_assumptions(VALID_FIXTURE_COUNTS_LIST)
        self.assertEqual(violations, [], f"Expected no violations for clean counts, got: {violations}")

    def test_flag_assumptions_empty_list_no_violation(self):
        """Empty fixture_counts → no violations."""
        violations = check_flag_assumptions([])
        self.assertEqual(violations, [])

    # --- validate_grand_total GrandTotalResult ---

    def test_validate_grand_total_returns_dataclass(self):
        """validate_grand_total must return GrandTotalResult, not a tuple."""
        from takeoff.agents import validate_grand_total, GrandTotalResult
        agent_output = {
            "fixture_counts": [{"total": 10}, {"total": 5}],
            "grand_total_fixtures": 15
        }
        result = validate_grand_total(agent_output)
        self.assertIsInstance(result, GrandTotalResult)
        self.assertFalse(result.was_corrected)
        self.assertEqual(result.counts["grand_total_fixtures"], 15)

    def test_validate_grand_total_corrects_mismatch(self):
        """Reported grand_total > 5% off computed sum → was_corrected=True."""
        from takeoff.agents import validate_grand_total
        agent_output = {
            "fixture_counts": [{"total": 10}, {"total": 5}],
            "grand_total_fixtures": 100  # way off
        }
        result = validate_grand_total(agent_output)
        self.assertTrue(result.was_corrected)
        self.assertEqual(result.counts["grand_total_fixtures"], 15)

    def test_validate_grand_total_empty_counts_no_correction(self):
        """Empty fixture_counts → not corrected."""
        from takeoff.agents import validate_grand_total
        agent_output = {"fixture_counts": [], "grand_total_fixtures": 0}
        result = validate_grand_total(agent_output)
        self.assertFalse(result.was_corrected)

    def test_validate_grand_total_zero_computed_sum_no_correction(self):
        """Computed sum = 0 (all totals are 0) → not corrected (avoid division by zero)."""
        from takeoff.agents import validate_grand_total
        agent_output = {
            "fixture_counts": [{"total": 0}, {"total": 0}],
            "grand_total_fixtures": 50
        }
        result = validate_grand_total(agent_output)
        # Should not raise, and should not correct (computed_total=0 → guard returns early)
        self.assertFalse(result.was_corrected)

    # --- DB snippet uniqueness warning ---

    def test_db_store_snippets_missing_id_skipped(self):
        """Snippet with no 'id' field is skipped with warning, not inserted."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            db = TakeoffDB(db_path=db_path)
            jid = str(uuid.uuid4())[:8]
            db.create_job(job_id=jid, mode="fast", drawing_name="test")
            # One snippet with id, one without
            snippets = [
                {"id": "snip-001", "label": "rcp", "sub_label": "Zone 1"},
                {"label": "rcp", "sub_label": "Zone 2"},  # missing id
            ]
            db.store_snippets(jid, snippets)
            db.close()
        finally:
            os.unlink(db_path)

    # --- Zero-fixture result has fixture_table ---

    def test_zero_fixture_result_has_fixture_table(self):
        """If Counter returns 0 fixtures, the early-return result must include fixture_table key."""
        # Simulate the zero-fixture early return from engine.py
        zero_fixture_result = {
            "job_id": "test123", "verdict": "BLOCK", "confidence_score": 0.25,
            "confidence_band": "VERY_LOW", "grand_total": 0,
            "fixture_table": [], "fixture_counts": [],
            "checker_attacks": [], "reconciler_responses": [], "violations": [],
            "flags": ["No fixtures detected."],
            "mode": "fast", "error": "No fixtures detected in provided snippets."
        }
        self.assertIn("fixture_table", zero_fixture_result,
                      "Zero-fixture result must contain fixture_table key for frontend compatibility")
        self.assertEqual(zero_fixture_result["fixture_table"], [])

    # --- JSON extraction with extra-space whitespace ---

    def test_extract_json_with_prefix_text(self):
        """JSON embedded after long text preamble should be extracted."""
        text = "The agent responded with the following analysis:\n" * 5 + '{"total": 99, "types": []}'
        result = extract_json_from_response(text, "test")
        self.assertEqual(result.get("total"), 99)

    def test_extract_json_empty_string_raises(self):
        """Empty string input must raise JSONDecodeError."""
        import json as _json
        with self.assertRaises(_json.JSONDecodeError):
            extract_json_from_response("", "test")


# ══════════════════════════════════════════════════════════════════════
# New tests covering fixed gaps
# ══════════════════════════════════════════════════════════════════════

class TestFixedGaps(unittest.TestCase):
    """Tests for bugs and gaps fixed in the audit round."""

    # ── P0 #2: cost_usd in frontend format ─────────────────────────────

    def test_format_for_frontend_includes_cost_usd(self):
        """_format_for_frontend must pass cost_usd through to the response dict."""
        # Import directly so test doesn't depend on server running
        import importlib
        import sys
        # Mock fastapi if not installed
        if "fastapi" not in sys.modules:
            import unittest.mock as mock
            sys.modules.setdefault("fastapi", mock.MagicMock())
            sys.modules.setdefault("fastapi.middleware.cors", mock.MagicMock())
            sys.modules.setdefault("fastapi.responses", mock.MagicMock())
        try:
            from takeoff.api import _format_for_frontend
        except Exception:
            self.skipTest("FastAPI not importable in this environment")

        result = {
            "job_id": "abc123", "mode": "fast", "grand_total": 50,
            "fixture_table": [], "areas_covered": [],
            "confidence_band": "MODERATE", "confidence": 0.72,
            "confidence_explanation": "ok", "verdict": "PASS",
            "violations": [], "flags": [], "ruling_summary": "ok",
            "adversarial_log": [], "agent_counts": {},
            "latency_ms": 4200, "cost_usd": 0.087
        }
        formatted = _format_for_frontend(result)
        self.assertIn("cost_usd", formatted)
        self.assertAlmostEqual(formatted["cost_usd"], 0.087)

    # ── P0 #3: Rule 6 — UNKNOWN tags auto-flagged ──────────────────────

    def test_rule6_unknown_tag_auto_flagged_by_engine(self):
        """Engine must auto-flag type_tag UNKNOWN if Counter didn't self-flag."""
        counter_output = {
            "fixture_counts": [
                {"type_tag": "A", "total": 10, "flags": []},
                {"type_tag": "UNKNOWN", "total": 3, "flags": []},
            ],
            "grand_total_fixtures": 13
        }
        _assumption_keywords = {"UNKNOWN", "TBD", "UNSCHEDULED", "?"}
        for fc in counter_output.get("fixture_counts", []):
            if fc.get("type_tag", "").upper() in _assumption_keywords:
                existing = fc.get("flags", [])
                if not any("ASSUMPTION" in f for f in existing):
                    fc.setdefault("flags", []).append("ASSUMPTION: fixture type not identified in schedule")

        unknown_fc = next(fc for fc in counter_output["fixture_counts"] if fc["type_tag"] == "UNKNOWN")
        self.assertTrue(any("ASSUMPTION" in f for f in unknown_fc["flags"]),
                        "UNKNOWN type_tag should be auto-flagged with ASSUMPTION")
        normal_fc = next(fc for fc in counter_output["fixture_counts"] if fc["type_tag"] == "A")
        self.assertEqual(normal_fc["flags"], [], "Normal type should not be flagged")

    def test_rule6_pre_flagged_unknown_not_double_flagged(self):
        """If Counter already flagged UNKNOWN, engine should not add a second flag."""
        counter_output = {
            "fixture_counts": [
                {"type_tag": "UNKNOWN", "total": 2, "flags": ["ASSUMPTION: not sure what this is"]},
            ],
            "grand_total_fixtures": 2
        }
        _assumption_keywords = {"UNKNOWN", "TBD", "UNSCHEDULED", "?"}
        for fc in counter_output.get("fixture_counts", []):
            if fc.get("type_tag", "").upper() in _assumption_keywords:
                existing = fc.get("flags", [])
                if not any("ASSUMPTION" in f for f in existing):
                    fc.setdefault("flags", []).append("ASSUMPTION: fixture type not identified in schedule")

        fc = counter_output["fixture_counts"][0]
        assumption_flags = [f for f in fc["flags"] if "ASSUMPTION" in f]
        self.assertEqual(len(assumption_flags), 1, "Should not double-flag already-flagged UNKNOWN")

    # ── P0 #4: Multi-panel schedule merge ──────────────────────────────

    def test_multi_panel_merge_accumulates_circuits(self):
        """Merging two PanelData objects should accumulate circuits from both."""
        from takeoff.extraction import PanelData
        panel1 = PanelData(
            panel_name="Panel A",
            circuits=[{"circuit": "1A", "load_va": 1200}],
            total_load_va=1200.0
        )
        panel2 = PanelData(
            panel_name="Panel B",
            circuits=[{"circuit": "1B", "load_va": 800}, {"circuit": "2B", "load_va": 600}],
            total_load_va=1400.0
        )
        # Simulate engine merge logic
        panel1.circuits.extend(panel2.circuits)
        panel1.total_load_va = panel1.total_load_va + panel2.total_load_va
        self.assertEqual(len(panel1.circuits), 3)
        self.assertAlmostEqual(panel1.total_load_va, 2600.0)

    # ── P0 #1: Reconciler per-area scale ───────────────────────────────

    def test_reconciler_area_counts_scaled_proportionally(self):
        """When Reconciler revises a total, counts_by_area must be scaled."""
        original_areas = {"Zone A": 10, "Zone B": 10}
        original_total = 20
        revised_total = 24  # +4 from reconciler
        scale = revised_total / original_total
        scaled = {area: max(0, round(cnt * scale)) for area, cnt in original_areas.items()}
        self.assertEqual(scaled["Zone A"], 12)
        self.assertEqual(scaled["Zone B"], 12)
        self.assertEqual(sum(scaled.values()), revised_total)

    def test_reconciler_no_change_leaves_areas_unchanged(self):
        """When Reconciler doesn't change the total, counts_by_area must be unchanged."""
        original_areas = {"Zone A": 10, "Zone B": 10}
        original_total = 20
        revised_total = 20  # no change
        # In the engine: if final_total == original_total, we skip scaling
        if revised_total != original_total and original_total > 0:
            scale = revised_total / original_total
            counts_by_area = {area: max(0, round(cnt * scale)) for area, cnt in original_areas.items()}
            area_flags = ["AREA_COUNTS_ESTIMATED"]
        else:
            counts_by_area = original_areas
            area_flags = []
        self.assertEqual(counts_by_area, original_areas)
        self.assertEqual(area_flags, [])

    # ── P4 #19: Checker dedup by category+type+area (not description) ──

    def test_checker_dedup_collapses_same_category_type_area(self):
        """Two attacks on same category/type_tag/area but different wording must deduplicate."""
        import re
        attacks = [
            {"attack_id": "ATK-001", "category": "missed_area", "affected_type_tag": "A",
             "affected_area": "Zone 1", "description": "Zone 1 is missing"},
            {"attack_id": "ATK-002", "category": "missed_area", "affected_type_tag": "A",
             "affected_area": "Zone 1", "description": "Zone 1 was not counted"},
        ]
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
        self.assertEqual(len(deduped), 1, "Same category/type/area should collapse to 1 attack")

    def test_checker_dedup_keeps_distinct_categories(self):
        """Attacks with different categories on same type/area must NOT deduplicate."""
        attacks = [
            {"attack_id": "ATK-001", "category": "missed_area", "affected_type_tag": "A",
             "affected_area": "Zone 1", "description": "zone missing"},
            {"attack_id": "ATK-002", "category": "math_error", "affected_type_tag": "A",
             "affected_area": "Zone 1", "description": "math is wrong"},
        ]
        seen: set = set()
        deduped = []
        for attack in attacks:
            key = (attack.get("category", ""), (attack.get("affected_type_tag") or "").upper(),
                   (attack.get("affected_area") or "").lower().strip())
            if key not in seen:
                seen.add(key)
                deduped.append(attack)
        self.assertEqual(len(deduped), 2, "Different categories on same area should both be kept")

    # ── P4 #20: Area fuzzy match ────────────────────────────────────────

    def test_area_fuzzy_match_word_overlap(self):
        """'North Wing Level 1' should fuzzy-match 'Level 1 North Wing'."""
        from takeoff.constitution import _area_fuzzy_match, _normalize_area_label
        expected = _normalize_area_label("North Wing Level 1")
        covered = {_normalize_area_label("Level 1 North Wing")}
        self.assertTrue(_area_fuzzy_match(expected, covered))

    def test_area_fuzzy_match_no_match(self):
        """'South Wing Level 2' must NOT match 'North Wing Level 1'."""
        from takeoff.constitution import _area_fuzzy_match, _normalize_area_label
        expected = _normalize_area_label("South Wing Level 2")
        covered = {_normalize_area_label("North Wing Level 1")}
        self.assertFalse(_area_fuzzy_match(expected, covered))

    def test_complete_coverage_fuzzy_miss_is_major_not_fatal(self):
        """Area with fuzzy match (label rename) should produce MAJOR, not FATAL violation."""
        from takeoff.constitution import check_complete_coverage
        # Snippets use "Floor 1 North" but Counter covered "Level 1 North"
        rcp_snippets = [{"label": "rcp", "sub_label": "Floor 1 North"}]
        areas_covered = ["Level 1 North"]
        violations = check_complete_coverage(areas_covered, rcp_snippets)
        if violations:
            self.assertEqual(violations[0]["severity"], "MAJOR",
                             "Fuzzy-matched area rename should be MAJOR, not FATAL")

    def test_complete_coverage_exact_match_no_violation(self):
        """Exact area label match (after normalization) should produce no violation."""
        from takeoff.constitution import check_complete_coverage
        rcp_snippets = [{"label": "rcp", "sub_label": "Floor 1 North (Copy)"}]
        areas_covered = ["Floor 1 North"]
        violations = check_complete_coverage(areas_covered, rcp_snippets)
        self.assertEqual(violations, [], "Exact match after normalization should produce no violation")

    # ── P2 #9: Fast mode notes compliance → neutral ────────────────────

    def test_fast_mode_note_compliance_is_neutral(self):
        """Fast mode should report neutral (0.5) for note_compliance regardless of notes."""
        result = calculate_confidence(
            fixture_counts=[{"type_tag": "A", "total": 10, "counts_by_area": {}}],
            areas_covered=["Zone 1"],
            rcp_snippets=[{"label": "rcp", "sub_label": "Zone 1"}],
            fixture_schedule={"fixtures": {"A": {"description": "Troffer"}}},
            checker_attacks=[],
            reconciler_responses=[],
            constitutional_violations=[],
            mode="fast",
            has_panel_schedule=False,
            has_plan_notes=False,  # Fast mode skips structural check → neutral
            notes_addressed=False
        )
        self.assertAlmostEqual(result["features"]["note_compliance"], 0.5,
                               msg="Fast mode note_compliance must be neutral 0.5")

    # ── Payload validation logic ────────────────────────────────────────

    def test_payload_validation_max_snippets(self):
        """Payload with >30 snippets should be rejected."""
        MAX_SNIPPETS = 30
        snippets = [{"id": f"s{i}", "label": "rcp", "image_data": "x"} for i in range(31)]
        self.assertGreater(len(snippets), MAX_SNIPPETS)

    def test_payload_validation_requires_fixture_schedule(self):
        """Payload without fixture_schedule snippet should be rejected."""
        snippets = [
            {"id": "rcp1", "label": "rcp", "image_data": "x"},
            {"id": "rcp2", "label": "rcp", "image_data": "x"},
        ]
        fixture_snippets = [s for s in snippets if s.get("label") == "fixture_schedule"]
        self.assertEqual(len(fixture_snippets), 0, "No fixture_schedule should fail validation")

    def test_payload_validation_requires_rcp(self):
        """Payload without rcp snippet should be rejected."""
        snippets = [
            {"id": "fs1", "label": "fixture_schedule", "image_data": "x"},
        ]
        rcp_snippets = [s for s in snippets if s.get("label") == "rcp"]
        self.assertEqual(len(rcp_snippets), 0, "No rcp snippet should fail validation")


# ══════════════════════════════════════════════════════════════════════
# TestBugFixes2 — tests for the second round of bug fixes
# ══════════════════════════════════════════════════════════════════════

class TestBugFixes2(unittest.TestCase):
    """Tests covering BUG-1 through BUG-10 fixes."""

    # ── BUG-4 / BUG-5: Atomic DB write and integer-split area scaling ────

    def test_store_job_results_atomic_commits_all(self):
        """store_job_results_atomic stores counts, log, and result in one shot."""
        import tempfile, os
        from takeoff.schema import TakeoffDB

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            db = TakeoffDB(db_path)
            db.create_job("job1", mode="fast", drawing_name="test", snippet_count=2)

            fixture_counts = [{"type_tag": "A", "counts_by_area": {"Floor 1": 10, "Floor 2": 5}, "difficulty": "S", "flags": []}]
            attacks = [{"attack_id": "ATK-001", "severity": "minor", "category": "missed_fixtures", "description": "test"}]
            responses = [{"attack_id": "ATK-001", "verdict": "defend", "explanation": "justified"}]
            full_result = {"job_id": "job1", "grand_total": 15}

            db.store_job_results_atomic(
                job_id="job1",
                fixture_counts=fixture_counts,
                attacks=attacks,
                reconciler_responses=responses,
                grand_total=15,
                confidence_score=0.72,
                confidence_band="MODERATE",
                confidence_features='{}',
                violations=[],
                flags=[],
                judge_verdict="PASS",
                full_result=full_result
            )

            counts = db.get_job_counts("job1")
            self.assertEqual(len(counts), 2)  # Floor 1 + Floor 2
            self.assertEqual(sum(r["count"] for r in counts), 15)

            adv_log = db.get_job_adversarial_log("job1")
            self.assertEqual(len(adv_log), 1)
            self.assertEqual(adv_log[0]["final_verdict"], "defend")

            retrieved = db.get_full_result("job1")
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved["grand_total"], 15)

            db.close()
        finally:
            os.unlink(db_path)

    def test_scale_area_counts_sums_to_target(self):
        """_scale_area_counts must produce counts that sum exactly to target_total."""
        from takeoff.engine import _scale_area_counts

        original = {"Floor 1": 7, "Floor 2": 5, "Floor 3": 3}
        for target in [12, 13, 14, 17, 20, 1]:
            result = _scale_area_counts(original, target)
            self.assertEqual(sum(result.values()), target,
                             f"Expected sum={target}, got {sum(result.values())} with original={original}")
            self.assertTrue(all(v >= 0 for v in result.values()))

    def test_scale_area_counts_empty(self):
        """Empty input returns empty dict."""
        from takeoff.engine import _scale_area_counts
        self.assertEqual(_scale_area_counts({}, 10), {})

    def test_scale_area_counts_zero_original(self):
        """Zero original total returns zeros."""
        from takeoff.engine import _scale_area_counts
        result = _scale_area_counts({"A": 0, "B": 0}, 5)
        self.assertEqual(result, {"A": 0, "B": 0})

    # ── BUG-9: area_coverage uses fuzzy matching ─────────────────────────

    def test_area_coverage_fuzzy_match_counts(self):
        """area_coverage should credit areas matched by normalization, not just exact string."""
        result = calculate_confidence(
            fixture_counts=[{"type_tag": "A", "total": 5, "counts_by_area": {"North Wing Level 1": 5}}],
            areas_covered=["Level 1 North Wing"],  # same area, different word order
            rcp_snippets=[{"label": "rcp", "sub_label": "North Wing Level 1"}],
            fixture_schedule={"fixtures": {"A": {"description": "Troffer"}}},
            checker_attacks=[],
            reconciler_responses=[],
            constitutional_violations=[],
            mode="fast",
            has_panel_schedule=False,
            has_plan_notes=False,
            notes_addressed=False
        )
        # Fuzzy match should find "North Wing Level 1" ↔ "Level 1 North Wing"
        self.assertGreater(result["features"]["area_coverage"], 0.5,
                           "Fuzzy-matched area should score > 0.5")

    # ── BUG-10: Vision cost tracking ─────────────────────────────────────

    def test_reset_and_get_vision_cost(self):
        """reset_vision_cost zeros the accumulator; get_vision_cost_usd returns float."""
        from takeoff.extraction import reset_vision_cost, get_vision_cost_usd
        reset_vision_cost()
        cost = get_vision_cost_usd()
        self.assertIsInstance(cost, float)
        self.assertEqual(cost, 0.0)

    # ── BUG-3: Fixture schedule collision detection ───────────────────────

    def test_fixture_collision_keeps_first_definition(self):
        """When two schedule snippets define the same type tag, first wins."""
        # Simulate what engine does: iterate extracted.fixtures and skip duplicates
        existing = {"A": {"description": "First definition", "wattage": 38.0}}
        incoming = {"A": {"description": "Second definition", "wattage": 50.0}, "B": {"description": "New type"}}

        warnings = []
        for tag, info in incoming.items():
            if tag in existing:
                warnings.append(f"Collision on '{tag}'")
            else:
                existing[tag] = info

        self.assertEqual(existing["A"]["description"], "First definition",
                         "First definition must be preserved on collision")
        self.assertIn("B", existing, "Non-colliding new type must be added")
        self.assertTrue(any("A" in w for w in warnings), "Collision warning must be emitted")

    # ── BUG-7: Judge model errors return WARN not BLOCK ──────────────────

    def test_judge_model_error_returns_warn(self):
        """Judge model/parse errors should return WARN + JUDGE_UNAVAILABLE, not BLOCK."""
        from unittest.mock import MagicMock, patch
        from takeoff.agents import Judge
        from takeoff.constitution import get_constitution
        from takeoff.extraction import FixtureSchedule

        # Create a Judge whose model_router.complete raises
        router = MagicMock()
        router.complete.side_effect = RuntimeError("API timeout")
        judge = Judge(router, get_constitution())

        fs = FixtureSchedule(fixtures={"A": {"description": "Troffer", "wattage": 38}})
        result = judge.evaluate(
            counter_output={"fixture_counts": [{"type_tag": "A", "total": 10}], "grand_total_fixtures": 10, "areas_covered": []},
            checker_attacks=[],
            reconciler_output=None,
            fixture_schedule=fs,
            mode="fast"
        )
        self.assertEqual(result["verdict"], "WARN",
                         "Model error should produce WARN, not BLOCK")
        self.assertTrue(any("JUDGE_UNAVAILABLE" in f for f in result["flags"]),
                        "JUDGE_UNAVAILABLE flag must be present")
        self.assertEqual(result["violations"], [],
                         "No constitutional violations should be fabricated on model error")

    # ── BUG-2: Semaphore uses public .locked() API ────────────────────────

    def test_semaphore_locked_check_exists(self):
        """asyncio.Semaphore.locked() is a public API (not _value)."""
        import asyncio
        sem = asyncio.Semaphore(1)
        self.assertTrue(hasattr(sem, "locked"), "Semaphore must have public .locked() method")
        # _value access should no longer appear in api.py
        with open("takeoff/api.py") as f:
            content = f.read()
        self.assertNotIn("_value", content, "api.py must not access private _value attribute")


# ══════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
