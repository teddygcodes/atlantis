from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HISTORY_PATH = ROOT / "meta" / "history.json"
BASELINES_DIR = ROOT / "meta" / "baselines"
STATES_PATH = ROOT / "governance" / "states.py"
RUNS_DIR = ROOT / "runs"

ALLOWED_MARKERS = {"RESEARCHER_PROMPT", "CRITIC_PROMPT"}
REQUIRED_SECTIONS = {
    # Strict format requirements for researcher prompts (constitutional)
    "RESEARCHER_PROMPT": ["RESEARCH TYPE:", "HYPOTHESIS:", "CONCLUSION:", "CITATIONS:"],
    # Semantic requirements for critic prompts (allow format flexibility)
    # These are OR-based: "flaw|gap|error" means accept any of these words
    "CRITIC_PROMPT": ["challenge", "flaw|gap|error", "evidence"],
}


@dataclass
class Proposal:
    proposal_id: str
    status: str
    marker: str
    new_text: str
    rollback_text: str
    adversarial_review_summary: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _latest_run_dir(runs_dir: Path) -> Path:
    runs = [p for p in runs_dir.iterdir() if p.is_dir()]
    if not runs:
        raise FileNotFoundError(f"No run directories found in {runs_dir}")
    return sorted(runs)[-1]


def _load_archive_entries(run_dir: Path) -> list[dict[str, Any]]:
    archive_path = run_dir / "archive.json"
    payload = _read_json(archive_path)
    entries = payload.get("archive_entries", [])
    if not isinstance(entries, list):
        raise ValueError(f"Invalid archive format in {archive_path}")
    return entries


def _survival_rate_per_domain(entries: list[dict[str, Any]]) -> dict[str, float]:
    totals = defaultdict(int)
    surviving = defaultdict(int)
    for e in entries:
        domain = e.get("source_state") or "unknown"
        status = (e.get("status") or "").lower()
        if status in {"founding"}:
            continue
        totals[domain] += 1
        if status in {"surviving", "partial"}:
            surviving[domain] += 1
    rates: dict[str, float] = {}
    for domain, total in totals.items():
        rates[domain] = round((surviving[domain] / total) if total else 0.0, 4)
    return dict(sorted(rates.items()))


def _retraction_reason_distribution(entries: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for e in entries:
        status = (e.get("status") or "").lower()
        if status not in {"retracted", "destroyed"}:
            continue
        reason = e.get("retraction_reason") or e.get("rejection_reason") or "UNKNOWN"
        counter[str(reason)] += 1
    return dict(counter)


def _domain_health_summary(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "domain_health.json"
    if path.exists():
        return _read_json(path)
    return {"warning": "domain_health.json missing"}


def _snapshot_baseline(prompt_version: str, run_dir: Path) -> Path:
    entries = _load_archive_entries(run_dir)
    baseline = {
        "prompt_version": prompt_version,
        "run": run_dir.name,
        "created_at": _now(),
        "survival_rate_per_domain": _survival_rate_per_domain(entries),
        "retraction_reason_distribution": _retraction_reason_distribution(entries),
        "domain_health_summary": _domain_health_summary(run_dir),
    }
    path = BASELINES_DIR / f"{prompt_version}_baseline.json"
    _write_json(path, baseline)
    return path


def _extract_block(text: str, marker: str) -> tuple[int, int, str]:
    start_pat = f"# === {marker}_START ==="
    end_pat = f"# === {marker}_END ==="
    start = text.find(start_pat)
    end = text.find(end_pat)
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Marker block not found for {marker}")
    block_start = start + len(start_pat)
    block = text[block_start:end]
    return block_start, end, block


def _normalize_new_text(new_text: str) -> str:
    if not new_text.endswith("\n"):
        return "\n" + new_text + "\n"
    return "\n" + new_text


def _apply_block(text: str, marker: str, new_text: str) -> str:
    start, end, old_block = _extract_block(text, marker)
    old_len = len(old_block.strip())
    new_len = len(new_text.strip())
    # Allow either 10% growth OR 200 characters, whichever is greater
    max_growth = max(int(old_len * 0.10), 200)
    if old_len and (new_len - old_len) > max_growth:
        raise ValueError(f"Proposal increases {marker} length by more than {max_growth} chars (10% or 200 char limit)")
    # Validate required sections (case-insensitive for flexibility)
    # Support OR syntax: "flaw|gap|error" means accept any of these words
    for required in REQUIRED_SECTIONS.get(marker, []):
        if "|" in required:
            # OR-based check: accept any of the alternatives
            alternatives = [alt.strip() for alt in required.split("|")]
            if not any(alt.lower() in new_text.lower() for alt in alternatives):
                raise ValueError(f"Proposal removes required section (needs one of: {', '.join(alternatives)}) from {marker}")
        else:
            # Exact keyword check (case-insensitive)
            if required.lower() not in new_text.lower():
                raise ValueError(f"Proposal removes required section '{required}' from {marker}")

    weak_patterns = [r"validation\s+optional", r"ignore\s+validation", r"skip\s+validation"]
    lowered = new_text.lower()
    if any(re.search(pat, lowered) for pat in weak_patterns):
        raise ValueError("Proposal appears to weaken validation requirements")

    return text[:start] + _normalize_new_text(new_text) + text[end:]


def _bump_patch(version: str) -> str:
    m = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", version.strip())
    if not m:
        raise ValueError(f"Invalid prompt version '{version}', expected vX.Y.Z")
    major, minor, patch = map(int, m.groups())
    return f"v{major}.{minor}.{patch + 1}"


def _read_history() -> dict[str, Any]:
    if not HISTORY_PATH.exists():
        return {"current_prompt_version": "v2.4.0", "runs": []}
    return _read_json(HISTORY_PATH)


def _check_anti_oscillation(history: dict[str, Any], sections: list[str]) -> None:
    runs = history.get("runs", [])
    if not runs:
        return
    current_idx = len(runs)
    for section in sections:
        last_idx = None
        for idx in range(len(runs) - 1, -1, -1):
            if section in runs[idx].get("modified_sections", []):
                last_idx = idx
                break
        if last_idx is not None and (current_idx - last_idx) < 3:
            raise ValueError(
                f"Anti-oscillation violation: section '{section}' modified {current_idx - last_idx} run(s) ago"
            )


def _to_proposals(payload: dict[str, Any]) -> list[Proposal]:
    raw = payload.get("proposals", [])
    if not isinstance(raw, list):
        raise ValueError("Proposal file must contain a 'proposals' list")

    proposals: list[Proposal] = []
    for i, p in enumerate(raw):
        status = str(p.get("status", "")).upper()
        if status == "REJECTED":
            continue

        # Support both old format (marker/new_text/rollback_text) and new format (target_section/proposed_change/current_excerpt)
        marker = p.get("marker") or p.get("target_section")
        if marker not in ALLOWED_MARKERS:
            raise ValueError(f"Proposal {i} targets invalid marker '{marker}'")

        # Rollback text: old format uses "rollback_text", new format uses "current_excerpt"
        rollback = p.get("rollback_text") or p.get("current_excerpt", "")
        if not rollback:
            raise ValueError(f"Proposal {i} missing rollback text (rollback_text or current_excerpt)")

        # New text: old format uses "new_text", new format uses "proposed_change"
        new_text = p.get("new_text") or p.get("proposed_change", "")
        if not new_text:
            raise ValueError(f"Proposal {i} missing new text (new_text or proposed_change)")

        # Adversarial review: old format uses string "adversarial_review_summary", new format uses dict "adversarial_review"
        adv_review = p.get("adversarial_review_summary")
        if not adv_review:
            # New format: extract summary from adversarial_review dict
            adv_dict = p.get("adversarial_review", {})
            if isinstance(adv_dict, dict):
                ruling = adv_dict.get("ruling", "UNKNOWN")
                judge_ruling = adv_dict.get("meta_judge_ruling", "")
                adv_review = f"Ruling: {ruling}\n{judge_ruling}"
            else:
                adv_review = "(none provided)"

        proposals.append(
            Proposal(
                proposal_id=str(p.get("proposal_id", f"proposal_{i+1}")),
                status=status,
                marker=marker,
                new_text=new_text,
                rollback_text=rollback,
                adversarial_review_summary=str(adv_review),
            )
        )

    if len(proposals) > 3:
        raise ValueError("Maximum 3 non-rejected proposals are allowed per analysis")
    return proposals


def _show_diff_and_review(current_text: str, proposals: list[Proposal]) -> None:
    temp = current_text
    print("\n=== Proposed Changes ===")
    for p in proposals:
        _, _, old_block = _extract_block(temp, p.marker)
        preview_new = _normalize_new_text(p.new_text)
        diff = difflib.unified_diff(
            old_block.splitlines(),
            preview_new.splitlines(),
            fromfile=f"{p.marker}:old",
            tofile=f"{p.marker}:new",
            lineterm="",
        )
        print(f"\n--- {p.proposal_id} ({p.marker}) ---")
        print("\n".join(diff) or "(no textual change)")
        print(f"Adversarial review summary: {p.adversarial_review_summary}")
        temp = _apply_block(temp, p.marker, p.new_text)


def _apply_proposal_file(proposal_path: Path) -> None:
    payload = _read_json(proposal_path)
    proposals = _to_proposals(payload)
    if not proposals:
        print("No non-rejected proposals to apply. Exiting.")
        return

    history = _read_history()
    prompt_version = str(payload.get("prompt_version") or history.get("current_prompt_version") or "v2.4.0")

    sections = [p.marker for p in proposals]
    _check_anti_oscillation(history, sections)

    latest_run = _latest_run_dir(RUNS_DIR)
    baseline_path = _snapshot_baseline(prompt_version, latest_run)
    print(f"Baseline snapshot written: {baseline_path}")

    current_text = STATES_PATH.read_text(encoding="utf-8")
    _show_diff_and_review(current_text, proposals)

    confirm = input("\nApply these changes? (y/n): ").strip().lower()
    if confirm != "y":
        print("Aborted by user.")
        return

    new_text = current_text
    modified_sections: list[str] = []
    for p in proposals:
        new_text = _apply_block(new_text, p.marker, p.new_text)
        modified_sections.append(p.marker)

    STATES_PATH.write_text(new_text, encoding="utf-8")

    new_version = _bump_patch(prompt_version)
    run_record = {
        "applied_at": _now(),
        "proposal_file": str(proposal_path),
        "prompt_version_before": prompt_version,
        "prompt_version_after": new_version,
        "modified_sections": modified_sections,
        "proposals": [
            {
                "proposal_id": p.proposal_id,
                "marker": p.marker,
                "status": p.status,
                "rollback_text": p.rollback_text,
                "adversarial_review_summary": p.adversarial_review_summary,
            }
            for p in proposals
        ],
    }

    history.setdefault("runs", []).append(run_record)
    history["current_prompt_version"] = new_version
    _write_json(HISTORY_PATH, history)
    print(f"Applied {len(proposals)} proposal(s). prompt_version: {prompt_version} → {new_version}")
    print(f"History updated: {HISTORY_PATH}")


def _compare_mode(baseline_path: Path, run_dir: Path) -> int:
    baseline = _read_json(baseline_path)
    entries = _load_archive_entries(run_dir)
    current_rates = _survival_rate_per_domain(entries)
    baseline_rates = baseline.get("survival_rate_per_domain", {})

    print("=== Baseline Comparison ===")
    print(f"Baseline: {baseline_path}")
    print(f"Run:      {run_dir}")

    rollback_flag = False
    domains = sorted(set(baseline_rates) | set(current_rates))
    for d in domains:
        b = float(baseline_rates.get(d, 0.0))
        c = float(current_rates.get(d, 0.0))
        drop = b - c
        pct_points = round(drop * 100, 2)
        line = f"- {d}: baseline={b:.2%}, current={c:.2%}, drop={pct_points:.2f}pp"
        if drop > 0.15:
            rollback_flag = True
            line += "  <-- ROLLBACK FLAG"
        print(line)

    if rollback_flag:
        print("\nRollback recommended: survival dropped >15% in at least one domain.")
        return 2
    print("\nNo rollback flags.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply prompt proposals safely")
    parser.add_argument("--proposal", type=Path, help="Path to proposal JSON")
    parser.add_argument("--compare", action="store_true", help="Compare run with baseline")
    parser.add_argument("--baseline", type=Path, help="Path to baseline JSON")
    parser.add_argument("--run", type=Path, help="Run directory path")
    args = parser.parse_args()

    if args.compare:
        if not args.baseline or not args.run:
            parser.error("--compare requires --baseline and --run")
        return _compare_mode(args.baseline, args.run)

    if not args.proposal:
        parser.error("--proposal is required when not in compare mode")

    _apply_proposal_file(args.proposal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
