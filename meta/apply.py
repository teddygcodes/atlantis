"""Apply approved/narrowed prompt proposals between prompt markers only."""

from __future__ import annotations

import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .optimizer import PROMPT_MARKERS


class ProposalApplier:
    def __init__(
        self,
        states_file: Path | str = "governance/states.py",
        history_file: Path | str = "meta/history.json",
        baselines_dir: Path | str = "meta/baselines",
    ):
        self.states_file = Path(states_file)
        self.history_file = Path(history_file)
        self.baselines_dir = Path(baselines_dir)

    def apply(self, proposal_json: str, auto_confirm: bool = False) -> int:
        payload = json.loads(Path(proposal_json).read_text(encoding="utf-8"))
        states_text = self.states_file.read_text(encoding="utf-8")
        changed = 0

        for p in payload.get("proposals", []):
            if p.get("status") not in {"APPROVED", "NARROWED"}:
                continue
            section = p["target_section"]
            start_marker, end_marker = PROMPT_MARKERS[section]
            old = p["current_excerpt"]
            new = p["proposed_change"]
            diff = "\n".join(
                difflib.unified_diff(
                    old.splitlines(),
                    new.splitlines(),
                    fromfile=f"{section}:current",
                    tofile=f"{section}:proposed",
                    lineterm="",
                )
            )
            print(diff)
            if not auto_confirm:
                answer = input("Apply this change? [y/N]: ").strip().lower()
                if answer != "y":
                    continue

            baseline = self._snapshot_baseline(states_text, section)
            states_text = self._replace_section(states_text, start_marker, end_marker, new)
            self._append_history(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "proposal_file": proposal_json,
                    "target_section": section,
                    "status": "applied",
                    "baseline": str(baseline),
                    "hash_before": self._hash(old),
                    "hash_after": self._hash(new),
                }
            )
            changed += 1

        if changed:
            self.states_file.write_text(states_text, encoding="utf-8")
        return changed

    def _snapshot_baseline(self, states_text: str, section: str) -> Path:
        self.baselines_dir.mkdir(parents=True, exist_ok=True)
        out = self.baselines_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{section}.txt"
        out.write_text(states_text, encoding="utf-8")
        return out

    @staticmethod
    def _replace_section(full_text: str, start_marker: str, end_marker: str, replacement: str) -> str:
        start = full_text.index(start_marker) + len(start_marker)
        end = full_text.index(end_marker, start)
        return full_text[:start] + "\n" + replacement + "\n" + full_text[end:]

    def _append_history(self, event: dict) -> None:
        if self.history_file.exists():
            history = json.loads(self.history_file.read_text(encoding="utf-8"))
        else:
            history = {"events": []}
        history.setdefault("events", []).append(event)
        self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
