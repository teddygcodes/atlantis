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
MARKER_CALLS_PER_RUN = {
    "RESEARCHER_PROMPT": 60,
    "CRITIC_PROMPT": 60,
}
MARKER_MODEL_TIER = {
    "RESEARCHER_PROMPT": "sonnet",
    "CRITIC_PROMPT": "sonnet",
}
INPUT_PRICE_PER_MTOK_USD = {
    "haiku": 0.25,
    "sonnet": 3.00,
}
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
    # Additive mode fields (optional)
    mode: str = "replace"  # "replace" or "additive"
    after_line: str | None = None  # For additive: line to insert after
    addition: str | None = None  # For additive: the one line to add


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


def _apply_block(text: str, marker: str, proposal: Proposal) -> str:
    start, end, old_block = _extract_block(text, marker)

    if proposal.mode == "additive":
        # Additive mode: find anchor line and insert new line after it
        if not proposal.after_line or not proposal.addition:
            raise ValueError(f"Additive proposal missing after_line or addition")

        # Find the anchor line in the old block
        lines = old_block.splitlines(keepends=True)
        anchor_found = False
        new_lines = []

        for line in lines:
            new_lines.append(line)
            # Check if this line contains the anchor text (fuzzy match)
            if proposal.after_line.strip() in line.strip():
                # Insert the new line after this one
                # Preserve indentation from the anchor line
                indent = len(line) - len(line.lstrip())
                new_line_with_indent = " " * indent + proposal.addition.strip() + "\n"
                new_lines.append(new_line_with_indent)
                anchor_found = True
                break

        if not anchor_found:
            raise ValueError(f"Anchor line not found in {marker}: {proposal.after_line[:60]}...")

        # Add remaining lines after the insertion point
        if anchor_found:
            anchor_idx = lines.index(next(l for l in lines if proposal.after_line.strip() in l.strip()))
            new_lines.extend(lines[anchor_idx + 1:])

        new_block = "".join(new_lines)
        # For additive mode, skip length check (single line additions are always small)
        return text[:start] + new_block + text[end:]

    else:
        # Replace mode: validate and replace entire block
        new_text = proposal.new_text
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


def _next_version(current: str) -> str:
    parts = current.lstrip("v").split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return "v" + ".".join(parts)


def _next_minor_version(current: str) -> str:
    m = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", current.strip())
    if not m:
        raise ValueError(f"Invalid prompt version '{current}', expected vX.Y.Z")
    major, minor, _patch = map(int, m.groups())
    return f"v{major}.{minor + 1}.0"


def _read_history() -> dict[str, Any]:
    if not HISTORY_PATH.exists():
        return {"current_prompt_version": "v2.4.0", "runs": []}
    return _read_json(HISTORY_PATH)


def _check_anti_oscillation(history: dict[str, Any], sections: list[str]) -> None:
    """Check if section was modified too recently (prevents rapid back-and-forth changes).

    TODO: Make this more granular - allow changes to different lines in same section.
    Currently blocks entire section if modified in last run. Future: track line-level changes.
    """
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
        # Block if modified in the immediately previous run (reduced from 3 to 1)
        if last_idx is not None and (current_idx - last_idx) < 2:
            raise ValueError(
                f"Anti-oscillation: '{section}' was modified in the last run (v{history.get('current_prompt_version', 'unknown')})"
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

        # Detect mode: additive or replace
        mode = p.get("mode", "replace")
        after_line = p.get("after_line")
        addition = p.get("addition")

        # For additive mode, validate required fields
        if mode == "additive":
            if not after_line or not addition:
                raise ValueError(f"Proposal {i} in additive mode missing after_line or addition")
            # In additive mode, new_text is the addition, rollback_text stays as current_excerpt
            new_text = addition
        else:
            # Replace mode: old format uses "new_text", new format uses "proposed_change"
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
                mode=mode,
                after_line=after_line,
                addition=addition,
            )
        )

    if len(proposals) > 10:
        raise ValueError("Maximum 10 non-rejected proposals are allowed per analysis")
    return proposals


def _show_proposal_diff_and_review(current_text: str, proposal: Proposal, index: int, total: int) -> None:
    _, _, old_block = _extract_block(current_text, proposal.marker)

    print(f"\n=== Proposal {index}/{total}: {proposal.proposal_id} ({proposal.marker}) ===")

    if proposal.mode == "additive":
        # Show additive proposal as a clean single-line insertion
        print(f"MODE: Additive (single line addition)")
        print(f"\nAfter line: {proposal.after_line[:80]}...")
        print(f"Adding:     + {proposal.addition}")

        # Show context (3 lines before and after the anchor)
        lines = old_block.splitlines()
        for i, line in enumerate(lines):
            if proposal.after_line.strip() in line.strip():
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                print(f"\nContext:")
                for j in range(context_start, context_end):
                    prefix = "  " if j != i else "→ "
                    print(f"{prefix}{lines[j]}")
                if i + 1 < len(lines):
                    print(f"+ {proposal.addition}")
                break

        # Token estimate for additive mode (just the one line)
        token_delta = _estimate_input_tokens(proposal.addition)
    else:
        # Show full diff for replace mode
        preview_new = _normalize_new_text(proposal.new_text)
        diff = difflib.unified_diff(
            old_block.splitlines(),
            preview_new.splitlines(),
            fromfile=f"{proposal.marker}:old",
            tofile=f"{proposal.marker}:new",
            lineterm="",
        )
        print("\n".join(diff) or "(no textual change)")
        old_tokens = _estimate_input_tokens(old_block)
        new_tokens = _estimate_input_tokens(preview_new)
        token_delta = new_tokens - old_tokens

    cost_delta = _estimated_cost_impact_per_run(proposal.marker, token_delta)
    print(
        "\nEstimated cost impact: "
        f"{token_delta:+d} tokens/call, "
        f"~${cost_delta:.3f}/run"
    )
    print(f"Adversarial review summary: {proposal.adversarial_review_summary}")

def _estimate_input_tokens(text: str) -> int:
    """Approximate token count using the provider's char-to-token heuristic."""
    return len(text) // 4


def _estimated_cost_impact_per_run(marker: str, token_delta_per_call: int) -> float:
    calls_per_run = MARKER_CALLS_PER_RUN.get(marker, 0)
    model_tier = MARKER_MODEL_TIER.get(marker, "sonnet")
    input_price_per_mtok = INPUT_PRICE_PER_MTOK_USD.get(model_tier, INPUT_PRICE_PER_MTOK_USD["sonnet"])
    return (token_delta_per_call * calls_per_run / 1_000_000) * input_price_per_mtok


def process_proposal_file(proposal_path: Path, dry_run: bool = False, *, minor_bump: bool = False) -> dict[str, int | bool | str]:
    payload = _read_json(proposal_path)
    proposals = _to_proposals(payload)
    if not proposals:
        print("No non-rejected proposals to apply. Exiting.")
        return {"accepted": 0, "denied": 0, "version_changed": False, "new_version": "unchanged"}

    history = _read_history()
    prompt_version = str(history.get("current_prompt_version") or "v2.4.0")
    proposal_version = payload.get("prompt_version")

    base_text = STATES_PATH.read_text(encoding="utf-8")
    new_text = base_text
    modified_sections: list[str] = []
    accepted_proposals: list[Proposal] = []
    denied_proposals: list[dict[str, str]] = []

    for idx, p in enumerate(proposals, start=1):
        _show_proposal_diff_and_review(new_text, p, idx, len(proposals))
        if dry_run:
            continue

        # Check anti-oscillation BEFORE asking user to approve
        # Never waste user's time approving something that will be rejected
        try:
            _check_anti_oscillation(history, [p.marker])
        except ValueError as e:
            denied_proposals.append({"proposal_id": p.proposal_id, "reason": str(e)})
            print(f"\n⚠️  [BLOCKED] {e}")
            print(f"Skipping proposal {idx} (not asking for approval)\n")
            continue

        confirm = input(f"\nApply proposal {idx} of {len(proposals)}? (y/n): ").strip().lower()
        if confirm != "y":
            denied_proposals.append({"proposal_id": p.proposal_id, "reason": "user_rejected"})
            continue

        try:
            new_text = _apply_block(new_text, p.marker, p)
        except ValueError as e:
            denied_proposals.append({"proposal_id": p.proposal_id, "reason": str(e)})
            print(f"Error applying {p.proposal_id}: {e}")
            continue

        accepted_proposals.append(p)
        modified_sections.append(p.marker)

    if dry_run:
        print("Dry run enabled: proposals were displayed but not applied.")
        return {"accepted": 0, "denied": len(proposals), "version_changed": False, "new_version": prompt_version}

    if accepted_proposals:
        STATES_PATH.write_text(new_text, encoding="utf-8")

    if accepted_proposals:
        if minor_bump:
            new_version = _next_minor_version(prompt_version)
        elif proposal_version:
            new_version = str(proposal_version)
        else:
            new_version = _next_version(prompt_version)
    else:
        new_version = prompt_version
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
                "applied": True,
            }
            for p in accepted_proposals
        ]
        + [
            {
                "proposal_id": p.proposal_id,
                "marker": p.marker,
                "status": p.status,
                "rollback_text": p.rollback_text,
                "adversarial_review_summary": p.adversarial_review_summary,
                "applied": False,
                "rejection_reason": next(d["reason"] for d in denied_proposals if d["proposal_id"] == p.proposal_id),
            }
            for p in proposals
            if any(d["proposal_id"] == p.proposal_id for d in denied_proposals)
        ],
    }

    history.setdefault("runs", []).append(run_record)
    history["current_prompt_version"] = new_version
    _write_json(HISTORY_PATH, history)

    if accepted_proposals and new_version != prompt_version:
        latest_run = _latest_run_dir(RUNS_DIR)
        baseline_path = _snapshot_baseline(new_version, latest_run)
        print(f"Baseline snapshot written: {baseline_path}")
    print(
        f"Applied {len(accepted_proposals)} proposal(s); denied {len(denied_proposals)} proposal(s). "
        f"prompt_version: {prompt_version} → {new_version}"
    )
    print(f"History updated: {HISTORY_PATH}")
    return {"accepted": len(accepted_proposals), "denied": len(denied_proposals), "version_changed": new_version != prompt_version, "new_version": new_version}


def _apply_proposal_file(proposal_path: Path) -> None:
    process_proposal_file(proposal_path, dry_run=False)


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
    parser.add_argument("--minor-bump", action="store_true", help="Bump minor version (vX.Y.0) when proposals are applied")
    args = parser.parse_args()

    if args.compare:
        if not args.baseline or not args.run:
            parser.error("--compare requires --baseline and --run")
        return _compare_mode(args.baseline, args.run)

    if not args.proposal:
        parser.error("--proposal is required when not in compare mode")

    _apply_proposal_file(args.proposal, minor_bump=args.minor_bump)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
