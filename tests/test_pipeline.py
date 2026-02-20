import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uuid
from types import SimpleNamespace

import pytest

from core.persistence import PersistenceLayer
from governance.perpetual import PerpetualEngine
from governance.states import ArchiveEntry, check_anti_loop, normalize_claim, validate_claim


class StubModels:
    def __init__(self, content: str):
        self.content = content

    def complete(self, **kwargs):
        return SimpleNamespace(content=self.content)


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
    claim = """CLAIM TYPE: Discovery\nPOSITION: I propose a new battery architecture.\nSTEP 1: Because layered anodes reduce dendrite growth.\nCONCLUSION: Therefore cycle life improves."""
    is_valid, errors = validate_claim(claim, StubModels("{}"), db)
    assert is_valid
    assert errors == []



def test_claim_validation_discovery_no_citations_with_survivors(db):
    _make_entry(db, status="survived")
    claim = """CLAIM TYPE: Discovery\nPOSITION: I propose a new battery architecture.\nSTEP 1: Because layered anodes reduce dendrite growth.\nCONCLUSION: Therefore cycle life improves."""
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
