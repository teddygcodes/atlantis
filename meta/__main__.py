"""CLI entrypoint for Atlantis meta self-correction system."""

from __future__ import annotations

import argparse
from pathlib import Path

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env", override=True)
except ImportError:
    pass  # dotenv not installed, assume env vars set manually

from .apply import _apply_proposal_file, process_proposal_file
from .apply_code import apply_code, _compare as compare_code
from .architect import run_architect
from .optimizer import MetaOptimizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Atlantis meta prompt self-correction")
    sub = parser.add_subparsers(dest="command", required=True)

    optimize = sub.add_parser("optimize", help="Analyze runs and generate proposal JSON")
    optimize.add_argument("--run", help="Run directory to analyze (defaults to latest)")
    optimize.add_argument("--cost", action="store_true", help="Include cost optimization analysis")
    optimize.add_argument("--dry-run", action="store_true", help="Show proposals without applying")
    optimize.add_argument("--max", type=int, default=None, help="Limit to top N proposals (default: unlimited)")
    optimize.add_argument(
        "--llm-mode",
        default="auto",
        choices=["auto", "api", "local", "dry-run"],
        help="LLM provider mode",
    )

    apply_cmd = sub.add_parser("apply", help="Apply approved proposal sections")
    apply_cmd.add_argument("proposal", help="Path to proposal JSON")
    apply_cmd.add_argument("--yes", action="store_true", help="Apply without confirmation prompts")
    apply_cmd.add_argument("--minor-bump", action="store_true", help="Bump minor version (vX.Y.0) when proposals are applied")

    architect_cmd = sub.add_parser("architect", help="Generate governance parallelization proposal")
    architect_cmd.add_argument("--run", help="Run directory to analyze (defaults to latest)")
    architect_cmd.add_argument("--dry-run", action="store_true", help="Use deterministic mock outputs")
    architect_cmd.add_argument(
        "--llm-mode",
        default="auto",
        choices=["auto", "api", "local", "dry-run"],
        help="LLM provider mode",
    )

    apply_code_cmd = sub.add_parser("apply-code", help="Apply code proposal with strict gates")
    apply_code_cmd.add_argument("proposal", nargs="?", help="Path to proposal JSON")
    apply_code_cmd.add_argument("--yes", action="store_true", help="Apply without confirmation prompts")
    apply_code_cmd.add_argument("--compare", action="store_true", help="Compare run with baseline")
    apply_code_cmd.add_argument("--baseline", help="Baseline JSON path")
    apply_code_cmd.add_argument("--run", help="Run directory path")

    args = parser.parse_args()

    if args.command == "optimize":
        optimizer = MetaOptimizer(llm_mode=args.llm_mode)
        out = optimizer.run(run_path=args.run, cost_mode=False, max_proposals=args.max)
        print(f"Wrote proposal file: {out}")

        if args.cost:
            cost_out = optimizer.run(run_path=args.run, cost_mode=True, max_proposals=args.max)
            print(f"Wrote cost proposal file: {cost_out}")

        process_proposal_file(out, dry_run=args.dry_run)
        return

    if args.command == "apply":
        proposal_path = Path(args.proposal)
        if args.yes:
            print("Note: --yes flag not yet supported in apply mode")
        _apply_proposal_file(proposal_path, minor_bump=args.minor_bump)
        return

    if args.command == "architect":
        out = run_architect(run=args.run, dry_run=args.dry_run, llm_mode=args.llm_mode)
        print(f"Wrote architect proposal file: {out}")
        return

    if args.command == "apply-code":
        if args.compare:
            if not args.baseline or not args.run:
                parser.error("apply-code --compare requires --baseline and --run")
            code = compare_code(Path(args.baseline), Path(args.run))
            raise SystemExit(code)
        if not args.proposal:
            parser.error("apply-code requires a proposal path unless --compare is set")
        code = apply_code(Path(args.proposal), yes=args.yes)
        raise SystemExit(code)


if __name__ == "__main__":
    main()
