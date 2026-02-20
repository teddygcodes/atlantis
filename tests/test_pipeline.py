import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uuid
from types import SimpleNamespace

import pytest

from core.persistence import PersistenceLayer
from governance.perpetual import PerpetualEngine
from governance.states import (
    ArchiveEntry,
    check_anti_loop,
    determine_outcome,
    normalize_claim,
    run_science_gate,
    validate_claim,
)


class StubModels:
    def __init__(self, content: str):
        self.content = content

    def complete(self, **kwargs):
        return SimpleNamespace(content=self.content)


class SequenceStubModels:
    def __init__(self, contents):
        self.contents = list(contents)
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        content = self.contents.pop(0) if self.contents else "{}"
        return SimpleNamespace(content=content)


@pytest.fixture
def db(tmp_path):
    return PersistenceLayer(str(tmp_path / "atlantis.db"))


def _make_entry(db: PersistenceLayer, **overrides):
    display_id = overrides.pop("display_id", db.next_display_id())
    payload = {
        "entry_id": str(uuid.uuid4()),
        "display_id": display_id,
        "entry_type": "claim",
        "source_state": "TestState",
        "source_entity": "Test Researcher",
        "cycle_created": 1,
        "status": "surviving",
        "claim_type": "discovery",
        "raw_claim_text": "base claim",
    }
    payload.update(overrides)
    entry = ArchiveEntry(**payload)
    db.save_archive_entry(entry)
    return display_id


def test_display_id_sequential(db):
    ids = [db.next_display_id() for _ in range(10)]
    assert ids == [f"#{i:03d}" for i in range(1, 11)]


def test_token_floor_zero(db):
    db.save_state_budget("Axiom", "physics", "empirical", budget=5, rival_name="Rival", cycle=1)
    db.update_state_budget("Axiom", -20)
    row = db.get_state_budget_row("Axiom")
    assert row is not None
    assert row["token_budget"] == 0


def test_archive_entry_full_text(db):
    raw_text = "This claim text should be preserved exactly.\nLine 2 with symbols: <>[]{}"
    did = _make_entry(db, raw_claim_text=raw_text)
    loaded = db.get_archive_entry(did)
    assert loaded is not None
    assert loaded["raw_claim_text"] == raw_text


def test_chain_collapse(db):
    a = _make_entry(db, status="destroyed", citations=[], referenced_by=["#002"])
    b = _make_entry(db, display_id="#002", citations=[a], referenced_by=["#003"])
    c = _make_entry(db, display_id="#003", citations=[b])

    flagged = db.run_chain_collapse(a)

    b_row = db.get_archive_entry(b)
    c_row = db.get_archive_entry(c)
    assert b in flagged
    assert c in flagged
    assert b_row is not None and b_row["status"] == "foundation_challenged"
    assert c_row is not None and c_row["status"] == "foundation_challenged"


def test_founding_deposit(db):
    did = _make_entry(db, status="founding", raw_claim_text="Unstructured founding note")
    loaded = db.get_archive_entry(did)
    assert loaded is not None
    assert loaded["status"] == "founding"
    assert loaded["raw_claim_text"] == "Unstructured founding note"


def test_claim_validation_foundation(db):
    _make_entry(db, status="surviving")
    claim = """CLAIM TYPE: Foundation\nPOSITION: Gravity causes acceleration.\nSTEP 1: Masses attract each other.\nCONCLUSION: Therefore acceleration occurs."""
    is_valid, errors = validate_claim(claim, StubModels("{}"), db)
    assert not is_valid
    assert any("citation" in err.lower() for err in errors)


def test_claim_validation_discovery(db):
    claim = """CLAIM TYPE: Discovery
POSITION: Layered anodes improve cycle life, operationally defined as >=10% more retained capacity after 500 cycles measured by standardized charge/discharge tests.
STEP 1: If layered anodes are used, then dendrite-related failure rates should decrease in controlled cycling experiments (testable implication).
GAP ADDRESSED: Prior claims do not specify a measurable threshold for improved cycle life.
ESTIMATE: 12% cycle-life gain under identical test protocols. ASSUMPTIONS: same electrolyte chemistry and temperature window.
CONCLUSION: Therefore cycle life improves."""
    is_valid, errors = validate_claim(claim, StubModels("{}"), db)
    assert is_valid
    assert errors == []



def test_claim_validation_discovery_no_citations_with_survivors(db):
    _make_entry(db, status="survived")
    claim = """CLAIM TYPE: Discovery
POSITION: Layered anodes improve cycle life, operationally defined as >=10% more retained capacity after 500 cycles measured by standardized charge/discharge tests.
STEP 1: If layered anodes are used, then dendrite-related failure rates should decrease in controlled cycling experiments (falsifiable).
GAP ADDRESSED: Prior claims do not specify a measurable threshold for improved cycle life.
EVIDENCE CLASS: preliminary bench test.
CONCLUSION: Therefore cycle life improves."""
    is_valid, errors = validate_claim(claim, StubModels("{}"), db)
    assert is_valid
    assert errors == []


def test_claim_validation_foundation_requires_structural_fields(db):
    main_id = _make_entry(db, status="surviving")
    claim = f"""CLAIM TYPE: Foundation
POSITION: Existing archive evidence supports a stable mechanism.
STEP 1: Prior measurements align with this synthesis.
CITATIONS: {main_id}
DEPENDS ON: {main_id}
SCOPE BOUNDARY: This claim does not address long-term deployment risks.
CONCLUSION: The mechanism has credible support in the archive."""
    is_valid, errors = validate_claim(claim, StubModels("{}"), db)
    assert is_valid
    assert errors == []


def test_claim_validation_challenge_requires_target_step_and_alternative(db):
    claim = """CLAIM TYPE: Challenge
CHALLENGE TARGET: #001
STEP 2 is attacked because it assumes linear scaling.
PROPOSED ALTERNATIVE: Use a saturation model with bounded response under high load.
CONCLUSION: The alternative better fits known constraints."""
    is_valid, errors = validate_claim(claim, StubModels("{}"), db)
    assert is_valid
    assert errors == []

def test_normalize_claim():
    models = StubModels('{"claim_type": "discovery", "position": "P", "reasoning_chain": ["A", "B"], "conclusion": "C", "citations": [], "keywords": ["k"]}')
    out = normalize_claim(
        "I propose a new mechanism because signal timing matters. Therefore systems stabilize.",
        models,
    )
    assert out["claim_type"] == "discovery"
    assert out["position"]
    assert isinstance(out["reasoning_chain"], list)
    assert out["reasoning_chain"]


def test_anti_loop():
    models = StubModels('{"is_loop": true, "explanation": "same argument repeated"}')
    out = check_anti_loop(["A", "A", "A"], models)
    assert out["is_loop"] is True


def test_credibility_score(db):
    db.save_state_budget("Axiom", "physics", "empirical", budget=100, rival_name="Rival", cycle=1)
    db.increment_pipeline_claims("Axiom", survived=True)
    db.increment_pipeline_claims("Axiom", survived=True)
    db.increment_pipeline_claims("Axiom", survived=True)
    db.increment_pipeline_claims("Axiom", survived=False)
    db.increment_pipeline_claims("Axiom", survived=False)

    assert db.get_state_credibility("Axiom") == 0.6


def test_archive_tier_assignment_and_status_updates(db):
    main_id = _make_entry(db, status="surviving")
    quarantine_id = _make_entry(db, status="founding")
    graveyard_id = _make_entry(db, status="destroyed")

    assert db.get_archive_entry(main_id)["archive_tier"] == "main"
    assert db.get_archive_entry(quarantine_id)["archive_tier"] == "quarantine"
    assert db.get_archive_entry(graveyard_id)["archive_tier"] == "graveyard"

    db.update_entry_status(main_id, "retracted")
    assert db.get_archive_entry(main_id)["archive_tier"] == "graveyard"


def test_researcher_context_main_only_and_meta_uses_graveyard(db, tmp_path):
    _make_entry(db, display_id="#001", status="surviving", raw_claim_text="Main claim")
    _make_entry(db, display_id="#002", status="partial", raw_claim_text="Partial claim")
    _make_entry(db, display_id="#003", status="destroyed", raw_claim_text="Failed claim", outcome_reasoning="bad logic")

    fake_engine = SimpleNamespace(db=db, cycle=7, output_dir=tmp_path)

    citable_context = PerpetualEngine._build_archive_context(fake_engine, domain="", state_name="TestState")
    meta = PerpetualEngine._get_meta_learning(fake_engine, state_name="TestState")

    assert "#001" in citable_context
    assert "#002" not in citable_context
    assert "#003" not in citable_context
    assert "#003" in meta


def test_export_archive_grouped_by_tier(db, tmp_path):
    _make_entry(db, display_id="#001", status="surviving", raw_claim_text="Main")
    _make_entry(db, display_id="#002", status="partial", raw_claim_text="Quarantine")
    _make_entry(db, display_id="#003", status="retracted", raw_claim_text="Graveyard")

    fake_engine = SimpleNamespace(db=db, cycle=3, output_dir=tmp_path)
    PerpetualEngine._export_archive(fake_engine)

    archive_md = (tmp_path / "archive.md").read_text(encoding="utf-8")
    assert "## Main Archive (Surviving)" in archive_md
    assert "## Quarantine (Partial/Under Review)" in archive_md
    assert "## Graveyard (Destroyed/Retracted)" in archive_md


def test_science_gate_classifies_and_extracts_unverified():
    models = StubModels('{"assertions":[{"text":"500 years","classification":"UNVERIFIED","source_or_assumption":""},{"text":"12%","classification":"ESTIMATE","source_or_assumption":"assumes fixed temp"}]}')
    out = run_science_gate("Over 500 years it rises 12%.", {"position": "x"}, models)
    assert out["unverified_assertions"] == ["500 years"]


def test_determine_outcome_includes_numeric_skepticism_note():
    models = SequenceStubModels(['{"outcome":"survived","ruling_type":"SURVIVED","reasoning":"ok","open_questions":[],"scores":{"drama":5,"novelty":5,"depth":5}}'])
    determine_outcome(
        claim_text="The effect is 47%",
        challenge_text="Challenge",
        rebuttal_text="Rebuttal",
        newness_result={"new_reasoning": True},
        domain="physics",
        state_approaches={"A": "empirical", "B": "formal"},
        models=models,
        unverified_numeric_assertions=["47%"],
    )
    prompt = models.calls[0]["user_prompt"]
    assert "This claim contains unverified numeric assertions" in prompt
    assert "47%" in prompt


def test_archive_persists_unverified_numerics_json(db):
    did = _make_entry(db, unverified_numerics=["47%", "500 years"])
    loaded = db.get_archive_entry(did)
    assert loaded is not None
    assert loaded["unverified_numerics"] == ["47%", "500 years"]


def test_unverified_numeric_challenge_bonus_applies_to_drama():
    engine = PerpetualEngine.__new__(PerpetualEngine)
    outcome = {"outcome": "partial", "scores": {"drama": 6, "novelty": 4, "depth": 4}}
    PerpetualEngine._apply_unverified_numeric_drama_bonus(
        engine,
        outcome,
        "STEP TARGETED: the 47% increase is unsupported",
        {"unverified_assertions": ["47% increase"]},
    )
    assert outcome["scores"]["drama"] == 7


def test_state_budget_tracks_rejections_and_first_survival_cycle(db):
    db.save_state_budget("Axiom", "physics", "empirical", budget=100, rival_name="Rival", cycle=3)

    db.increment_pipeline_claims("Axiom", survived=False, ruling_type="REJECT_LOGIC", cycle=4)
    db.increment_pipeline_claims("Axiom", survived=False, ruling_type="REJECT_FACT", cycle=5)
    db.increment_pipeline_claims("Axiom", survived=True, ruling_type="SURVIVED", cycle=6)

    row = db.get_state_budget_row("Axiom")
    assert row is not None
    assert row["cycles_to_first_survival"] == 4
    assert row["total_rejections_by_type"] == {"REJECT_LOGIC": 1, "REJECT_FACT": 1}


def test_domain_health_includes_revision_efficiency_metrics(db, tmp_path):
    db.save_state_budget("A", "physics", "empirical", budget=100, rival_name="B", cycle=1)
    db.save_state_budget("B", "physics", "formal", budget=100, rival_name="A", cycle=1)

    db.increment_pipeline_claims("A", survived=False, ruling_type="REJECT_LOGIC", cycle=1)
    db.increment_pipeline_claims("A", survived=True, ruling_type="SURVIVED", cycle=2)
    db.increment_pipeline_claims("B", survived=False, ruling_type="REJECT_FACT", cycle=1)

    _make_entry(
        db,
        source_state="A",
        position="shared topic",
        status="destroyed",
        ruling_type="REJECT_LOGIC",
    )
    _make_entry(
        db,
        source_state="A",
        position="shared topic",
        status="surviving",
        ruling_type="SURVIVED",
    )
    _make_entry(
        db,
        source_state="B",
        position="other topic",
        status="destroyed",
        ruling_type="REJECT_FACT",
    )

    engine = PerpetualEngine.__new__(PerpetualEngine)
    engine.db = db
    engine.cycle = 2
    metrics = PerpetualEngine._compute_domain_health(engine, "physics")

    assert metrics["cycles_to_first_survival"] == 2.0
    assert metrics["revision_depth"] == 2.0
    assert metrics["failure_distribution"] == {"REJECT_LOGIC": 1, "REJECT_FACT": 1}
    assert metrics["survival_rate"] == pytest.approx(1 / 3, 0.001)
