"""CLI entrypoint for Atlantis meta self-correction system."""

from __future__ import annotations

import argparse

from .apply import ProposalApplier
from .optimizer import MetaOptimizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Atlantis meta prompt self-correction")
    sub = parser.add_subparsers(dest="command", required=True)

    optimize = sub.add_parser("optimize", help="Analyze runs and generate proposal JSON")
    optimize.add_argument("--run", help="Run directory to analyze (defaults to latest)")
    optimize.add_argument(
        "--llm-mode",
        default="auto",
        choices=["auto", "api", "local", "dry-run"],
        help="LLM provider mode",
    )

    apply_cmd = sub.add_parser("apply", help="Apply approved proposal sections")
    apply_cmd.add_argument("proposal", help="Path to proposal JSON")
    apply_cmd.add_argument("--yes", action="store_true", help="Apply without confirmation prompts")

    args = parser.parse_args()

    if args.command == "optimize":
        optimizer = MetaOptimizer(llm_mode=args.llm_mode)
        out = optimizer.run(run_path=args.run)
        print(f"Wrote proposal file: {out}")
        return

    if args.command == "apply":
        applier = ProposalApplier()
        changed = applier.apply(args.proposal, auto_confirm=args.yes)
        print(f"Applied {changed} proposal(s)")


if __name__ == "__main__":
    main()
