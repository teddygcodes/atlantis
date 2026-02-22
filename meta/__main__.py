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

from .apply import _apply_proposal_file
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
        proposal_path = Path(args.proposal)
        if args.yes:
            # For auto-confirm, we'd need to modify _apply_proposal_file to skip the prompt
            # For now, just call it normally (it will still prompt)
            print("Note: --yes flag not yet supported in apply mode")
        _apply_proposal_file(proposal_path)


if __name__ == "__main__":
    main()
