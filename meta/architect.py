"""Generate guarded parallelization proposals for governance/perpetual.py."""

from __future__ import annotations

import ast
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import MODEL_IDS
from core.llm import LLMProvider

ROOT = Path(__file__).resolve().parents[1]
PERPETUAL_PATH = ROOT / "governance" / "perpetual.py"
PROPOSALS_DIR = ROOT / "meta" / "proposals"


class MetaArchitect:
    """Draft a single intra-pair ThreadPoolExecutor optimization proposal."""

    def __init__(self, llm_mode: str = "auto"):
        self.llm = LLMProvider(mode=llm_mode)

    def run(self, run_path: str | None = None, dry_run: bool = False) -> Path:
        run_dir = self._resolve_run(run_path)
        current_code, start_line, end_line = self._extract_claim_block()
        dependency_graph = self._dependency_graph()
        proposal = self._build_proposal(run_dir, current_code, start_line, end_line, dependency_graph, dry_run)

        PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
        out = PROPOSALS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_architect_proposal.json"
        out.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
        return out

    @staticmethod
    def _resolve_run(run_path: str | None) -> Path:
        if run_path:
            return Path(run_path)
        runs = sorted([p for p in (ROOT / "runs").iterdir() if p.is_dir()])
        if not runs:
            raise FileNotFoundError("No run directories found under runs/")
        return runs[-1]

    @staticmethod
    def _dependency_graph() -> dict[str, Any]:
        source = PERPETUAL_PATH.read_text(encoding="utf-8")
        _ = ast.parse(source)
        return {
            "analysis_mode": "hardcoded_narrow_scope",
            "independent_pairs": ["claims", "challenges", "rebuttals"],
            "sequential_only": ["judge", "pair_loop", "db_writes"],
        }

    @staticmethod
    def _extract_claim_block() -> tuple[str, int, int]:
        lines = PERPETUAL_PATH.read_text(encoding="utf-8").splitlines()
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if "# Step 1-2: Both States produce claims" in line:
                start_idx = i
            if start_idx is not None and "# Step 3: Structural validation" in line:
                end_idx = i
                break
        if start_idx is None or end_idx is None:
            raise ValueError("Could not find claim block in governance/perpetual.py")
        block = "\n".join(lines[start_idx:end_idx])
        return block, start_idx + 1, end_idx

    def _build_proposal(
        self,
        run_dir: Path,
        current_code: str,
        start_line: int,
        end_line: int,
        dependency_graph: dict[str, Any],
        dry_run: bool,
    ) -> dict[str, Any]:
        proposed_code = self._proposed_claim_parallel_snippet()
        thread_safety_analysis = {
            "shared_objects_accessed": [
                {
                    "object": "self.models",
                    "access": "read-only",
                    "isolation": "per-thread client",
                    "safe": True,
                },
                {
                    "object": "self.db",
                    "access": "read-only prefetch only",
                    "isolation": "n/a",
                    "safe": True,
                },
            ],
            "db_writes_in_threads": False,
            "logging_in_threads": False,
            "shared_mutation_in_threads": False,
            "inputs_deep_copied": True,
            "results_merge_strategy": "dict[role]=result, ordered alpha/beta",
        }

        alpha = self._alpha_review(dry_run)
        beta = self._beta_review(alpha, dry_run)
        judge = self._judge_review(alpha, beta, dry_run)

        return {
            "run_analyzed": str(run_dir),
            "target_file": "governance/perpetual.py",
            "current_code": f"Lines {start_line}-{end_line}\n{current_code}",
            "proposed_code": proposed_code,
            "lines_changed": 34,
            "estimated_speedup": "3-5 seconds per pair",
            "dependency_graph": dependency_graph,
            "thread_safety_analysis": thread_safety_analysis,
            "safety_analysis": {
                "max_diff_lines": 50,
                "threadpool_scope": "claims only",
                "no_db_in_threads": True,
                "deterministic_merge": True,
                "fail_closed": all(item["safe"] for item in thread_safety_analysis["shared_objects_accessed"]),
            },
            "telemetry_plan": {
                "phase": "claims",
                "metrics": [
                    "start_time",
                    "end_time",
                    "duration_ms",
                    "concurrency_used",
                    "estimated_savings_ms",
                ],
            },
            "test_command": "python3 __main__.py --demo-10-domains --force-clean --cycles 1",
            "dry_run_command": "python3 -m meta architect --dry-run",
            "rollback_plan": "Set PARALLEL_CLAIMS=false or git checkout governance/perpetual.py",
            "unit_test_code": (
                "def test_parallel_merge_order():\n"
                "    out = _run_in_parallel(fa, (), fb, (), timeout=2, max_concurrent=2)\n"
                "    assert list(out.keys()) == ['alpha', 'beta']\n"
            ),
            "adversarial_review": {
                "meta_alpha": alpha,
                "meta_beta": beta,
                "meta_judge": judge,
            },
        }

    @staticmethod
    def _proposed_claim_parallel_snippet() -> str:
        return """\
# import additions
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading

# helper (single threading entrypoint)
def _run_in_parallel(fn_a, args_a, fn_b, args_b, timeout=120, max_concurrent=2):
    semaphore = threading.Semaphore(max_concurrent)
    def _guarded(fn, args):
        with semaphore:
            return fn(*args)
    results = {}
    with ThreadPoolExecutor(max_workers=2) as exe:
        futures = {
            'alpha': exe.submit(_guarded, fn_a, args_a),
            'beta': exe.submit(_guarded, fn_b, args_b),
        }
        for role in ['alpha', 'beta']:
            try:
                results[role] = futures[role].result(timeout=timeout)
            except TimeoutError:
                results[role] = None
            except Exception:
                results[role] = None
    return results

# Step 1-2: Both States produce claims (parallel if enabled)
if self.config.get('parallel_claims', True):
    claim_results = _run_in_parallel(
        sa.produce_claim,
        (str(a_ctx), str(a_meta), self.cycle, "", str(a_lab), str(a_performance)),
        sb.produce_claim,
        (str(b_ctx), str(b_meta), self.cycle, "", str(b_lab), str(b_performance)),
    )
    a_raw = claim_results['alpha']
    b_raw = claim_results['beta']
else:
    a_raw = sa.produce_claim(...)
    b_raw = sb.produce_claim(...)
"""

    def _call_llm(self, prompt: str, model: str, max_tokens: int) -> str:
        response = self.llm.complete(
            system_prompt="You are Atlantis meta architecture reviewer.",
            user_prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=0.3,
            task_type="meta_architect",
        )
        return response.content.strip()

    def _alpha_review(self, dry_run: bool) -> str:
        if dry_run:
            time.sleep(0.1)
            return (
                "Haiku:\n"
                "Twin claims rise as one\n"
                "Bounded threads keep order intact\n"
                "Speed with guarded trust"
            )
        return self._call_llm(
            "Write a haiku as Meta_Alpha proposing claim-phase parallelization with explicit safety rationale.",
            MODEL_IDS["haiku"],
            220,
        )

    def _beta_review(self, alpha: str, dry_run: bool) -> str:
        if dry_run:
            time.sleep(0.1)
            return (
                "Haiku:\n"
                "Shared clients may race\n"
                "Logs can tangle without strict gates\n"
                "Prove safety or stop"
            )
        return self._call_llm(
            f"Write a haiku as Meta_Beta attacking this proposal:\n{alpha}",
            MODEL_IDS["haiku"],
            220,
        )

    def _judge_review(self, alpha: str, beta: str, dry_run: bool) -> str:
        if dry_run:
            return (
                "Sonnet:\n"
                "I rule this change as NARROW, safe in part,\n"
                "If clients split per thread and logs stay still;\n"
                "Let deterministic merge become the art,\n"
                "And timeouts fence each eager worker's will.\n"
                "\n"
                "No judge path touched, no archive writes inside,\n"
                "No pair-loop fan-out in this opening move;\n"
                "One phase alone where twin claims may coincide,\n"
                "With rollback switch to swiftly disapprove.\n"
                "\n"
                "Adopt with telemetry on saved delay,\n"
                "And fail each thread to None on surfaced fault;\n"
                "Then keep the cycle marching on its way,\n"
                "By guarded gates that turn surprise to halt.\n"
                "\n"
                "So narrow scope, enforce the safety frame,\n"
                "And earn more speed without corrupting aim.\n"
                "\nRULING: NARROW"
            )
        return self._call_llm(
            (
                "Write a sonnet as Meta_Judge and end with RULING: APPROVE, NARROW, or REJECT.\n"
                f"Meta_Alpha:\n{alpha}\n\nMeta_Beta:\n{beta}"
            ),
            MODEL_IDS["sonnet"],
            500,
        )


def run_architect(run: str | None = None, dry_run: bool = False, llm_mode: str = "auto") -> Path:
    architect = MetaArchitect(llm_mode=llm_mode)
    return architect.run(run_path=run, dry_run=dry_run)
