"""Apply architect code proposals with strict mechanical safety gates."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .apply import _load_archive_entries, _read_json, _write_json

ROOT = Path(__file__).resolve().parents[1]
PERPETUAL_PATH = ROOT / "governance" / "perpetual.py"
HISTORY_PATH = ROOT / "meta" / "history.json"
BASELINES_DIR = ROOT / "meta" / "baselines"
WHITELIST_IMPORTS = {"concurrent.futures", "threading"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _line_delta(current_code: str, proposed_code: str) -> int:
    return len(list(difflib.unified_diff(current_code.splitlines(), proposed_code.splitlines(), lineterm="")))


def _extract_imports(code: str) -> set[str]:
    imports = set()
    for line in code.splitlines():
        s = line.strip()
        if s.startswith("import "):
            imports.add(s.replace("import", "").strip().split(" as ")[0])
        elif s.startswith("from "):
            imports.add(s.split()[1])
    return imports


def _find_changed_paths(code_text: str) -> list[str]:
    suspicious = []
    patterns = ["core.persistence", "persistence", "archive.json", "db.", "write(", "insert", "update"]
    lowered = code_text.lower()
    for p in patterns:
        if p in lowered:
            suspicious.append(p)
    return suspicious


def _safe_entries(thread_safety_analysis: dict[str, Any]) -> bool:
    for item in thread_safety_analysis.get("shared_objects_accessed", []):
        if not item.get("safe", False):
            return False
    return True


def _show_full_diff_and_review(current_text: str, proposed_code: str, proposal: dict[str, Any]) -> None:
    print("\n=== Full Diff (display) ===")
    diff = difflib.unified_diff(
        current_text.splitlines(),
        proposed_code.splitlines(),
        fromfile="governance/perpetual.py (current)",
        tofile="governance/perpetual.py (proposed)",
        lineterm="",
    )
    print("\n".join(diff))
    print("\n=== Adversarial Review ===")
    print(json.dumps(proposal.get("adversarial_review", {}), indent=2))


def _snapshot_baseline(run_dir: Path) -> Path:
    entries = _load_archive_entries(run_dir)
    baseline = {
        "created_at": _now(),
        "run": run_dir.name,
        "event_counts": _event_counts(entries),
        "required_archive_fields": _required_archive_fields(entries),
        "ordering_ok": _ordering_ok(entries),
    }
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    out = BASELINES_DIR / "perpetual_code_baseline.json"
    _write_json(out, baseline)
    return out


def _event_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    keys = ["claim", "challenge", "rebuttal", "judge"]
    counts = {k: 0 for k in keys}
    for e in entries:
        text = json.dumps(e).lower()
        for k in keys:
            if k in text:
                counts[k] += 1
    return counts


def _required_archive_fields(entries: list[dict[str, Any]]) -> bool:
    required = {"display_id", "source_state", "status"}
    for e in entries:
        if not required.issubset(set(e.keys())):
            return False
    return True


def _ordering_ok(entries: list[dict[str, Any]]) -> bool:
    triples = []
    for e in entries:
        cycle = e.get("cycle", 0)
        pair = str(e.get("source_state", ""))
        phase = str(e.get("status", ""))
        triples.append((cycle, pair, phase))
    return triples == sorted(triples, key=lambda x: (x[0], x[1], x[2]))


def _compare(baseline_path: Path, run_dir: Path) -> int:
    baseline = _read_json(baseline_path)
    entries = _load_archive_entries(run_dir)
    current = {
        "event_counts": _event_counts(entries),
        "required_archive_fields": _required_archive_fields(entries),
        "ordering_ok": _ordering_ok(entries),
    }
    print("=== Code Baseline Comparison ===")
    print(f"Baseline: {baseline_path}")
    print(f"Run:      {run_dir}")
    print(json.dumps({"baseline": baseline, "current": current}, indent=2))

    mismatch = baseline.get("event_counts") != current["event_counts"]
    mismatch = mismatch or baseline.get("required_archive_fields") != current["required_archive_fields"]
    mismatch = mismatch or not current["ordering_ok"]
    return 2 if mismatch else 0


def apply_code(proposal_path: Path, yes: bool = False) -> int:
    proposal = _read_json(proposal_path)
    if proposal.get("target_file") != "governance/perpetual.py":
        raise ValueError("apply-code currently supports only governance/perpetual.py")

    current_text = PERPETUAL_PATH.read_text(encoding="utf-8")
    proposed_code = str(proposal.get("proposed_code", ""))
    if not proposed_code:
        raise ValueError("proposal missing proposed_code")

    # PRE-APPLY GATES
    pre_errors = []
    tmp_path = ROOT / "meta" / ".tmp_proposed_perpetual.py"
    tmp_path.write_text(proposed_code, encoding="utf-8")
    rc, out = _run(["python", "-m", "py_compile", str(tmp_path)])
    if rc != 0:
        pre_errors.append(f"py_compile failed: {out}")

    if _line_delta(current_text, proposed_code) >= 50:
        pre_errors.append("Diff size must be < 50 lines")

    imports = _extract_imports(proposed_code) - _extract_imports(current_text)
    disallowed = [i for i in imports if i not in WHITELIST_IMPORTS]
    if disallowed:
        pre_errors.append(f"Disallowed new imports: {disallowed}")

    if _find_changed_paths(proposed_code):
        pre_errors.append("Potential persistence/DB path changes detected")

    if not _safe_entries(proposal.get("thread_safety_analysis", {})):
        pre_errors.append("Thread safety analysis contains safe: false entry")

    _show_full_diff_and_review(current_text, proposed_code, proposal)

    if pre_errors:
        for err in pre_errors:
            print(f"PRE-APPLY FAIL: {err}")
        tmp_path.unlink(missing_ok=True)
        return 1

    if not yes:
        confirm = input("\nApply these code changes? (y/n): ").strip().lower()
        if confirm != "y":
            tmp_path.unlink(missing_ok=True)
            print("Aborted.")
            return 1

    latest_run = sorted([p for p in (ROOT / "runs").iterdir() if p.is_dir()])[-1]
    baseline_path = _snapshot_baseline(latest_run)
    backup_path = ROOT / "meta" / "baselines" / "perpetual.pre_apply.py"
    shutil.copy2(PERPETUAL_PATH, backup_path)
    PERPETUAL_PATH.write_text(proposed_code, encoding="utf-8")

    # POST-APPLY GATES
    post_errors = []
    rc, out = _run(["python", "-m", "py_compile", str(PERPETUAL_PATH)])
    if rc != 0:
        post_errors.append(f"py_compile governance/perpetual.py failed: {out}")

    rc, out = _run(["python3", "-m", "meta", "architect", "--dry-run"])
    if rc != 0:
        post_errors.append(f"dry-run failed: {out}")

    rc, out = _run(["python3", "__main__.py", "--demo-10-domains", "--force-clean", "--cycles", "1"])
    if rc != 0:
        post_errors.append(f"live smoke test failed: {out[:400]}")

    cmp_code = _compare(baseline_path, latest_run)
    if cmp_code != 0:
        post_errors.append("baseline invariants comparison failed")

    tmp_path.unlink(missing_ok=True)

    if post_errors:
        shutil.copy2(backup_path, PERPETUAL_PATH)
        history = _read_json(HISTORY_PATH) if HISTORY_PATH.exists() else {"events": []}
        history.setdefault("events", []).append(
            {
                "ts": _now(),
                "type": "apply_code_failed",
                "proposal": str(proposal_path),
                "reasons": post_errors,
                "rollback": "git checkout governance/perpetual.py",
            }
        )
        _write_json(HISTORY_PATH, history)
        for err in post_errors:
            print(f"POST-APPLY FAIL: {err}")
        return 2

    print("apply-code completed successfully")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply architect code proposal with strict gates")
    parser.add_argument("proposal", nargs="?", type=Path, help="Path to architect proposal JSON")
    parser.add_argument("--yes", action="store_true", help="Apply without prompt")
    parser.add_argument("--compare", action="store_true", help="Compare run against baseline")
    parser.add_argument("--baseline", type=Path, help="Path to baseline json")
    parser.add_argument("--run", type=Path, help="Path to run directory")
    args = parser.parse_args()

    if args.compare:
        if not args.baseline or not args.run:
            parser.error("--compare requires --baseline and --run")
        return _compare(args.baseline, args.run)

    if not args.proposal:
        parser.error("proposal path is required unless using --compare")
    return apply_code(args.proposal, yes=args.yes)


if __name__ == "__main__":
    raise SystemExit(main())
