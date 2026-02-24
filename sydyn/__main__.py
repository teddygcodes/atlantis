"""Sydyn CLI entry point.

Usage:
    python -m sydyn "What caused the 2008 financial crisis?"
    python -m sydyn "Should I take aspirin?" --mode liability
    python -m sydyn "Why is X better than Y?" --verbose --save-kb
"""

import argparse
import json
import sys
import os

# Load environment variables FIRST (critical for API keys)
# Use override=True to ensure .env values take precedence over shell environment
from dotenv import load_dotenv
load_dotenv(override=True)

from sydyn.engine import SydynEngine


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sydyn - Real-Time Adversarial Search System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m sydyn "What is the speed of light?"
  python -m sydyn "Why did the Roman Empire fall?" --mode strict
  python -m sydyn "Should I take aspirin?" --mode liability
  python -m sydyn "What caused COVID-19?" --verbose --save-kb --format json
        """
    )

    parser.add_argument(
        "query",
        type=str,
        help="Query text to answer"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["fast", "strict", "liability"],
        default=None,
        help="Override auto-classification (default: auto-classify)"
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed agent reasoning"
    )

    parser.add_argument(
        "--save-kb",
        action="store_true",
        help="Store validated answer in knowledge base"
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="sydyn.db",
        help="Path to SQLite database (default: sydyn.db)"
    )

    parser.add_argument(
        "--search-provider",
        type=str,
        choices=["tavily", "serper"],
        default="tavily",
        help="Web search provider (default: tavily)"
    )

    args = parser.parse_args()

    # Verify API keys before running (prevents wasting search credits)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("[ERROR] ANTHROPIC_API_KEY not found in environment", file=sys.stderr)
        print("[ERROR] Make sure you have a .env file with ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        sys.exit(1)

    # Test API key with a minimal call
    print("[SYDYN] Verifying Anthropic API key...")
    try:
        from core.llm import LLMProvider
        test_provider = LLMProvider(api_key=anthropic_key, mode="api")
        test_response = test_provider.complete(
            system_prompt="You are a test assistant.",
            user_prompt="Reply with just 'OK'",
            max_tokens=10,
            temperature=0.0,
            model="claude-haiku-4-5-20251001",
            task_type="sydyn_test"
        )

        # Check if response contains an error
        if "[LLM ERROR" in test_response.content:
            print(f"[ERROR] API call failed: {test_response.content}", file=sys.stderr)
            print("[ERROR] Your ANTHROPIC_API_KEY may be invalid, expired, or lack access to Claude models", file=sys.stderr)
            sys.exit(1)

        # Check for expected response
        if "OK" not in test_response.content and "ok" not in test_response.content.lower():
            print(f"[WARN] Unexpected test response: {test_response.content[:50]}", file=sys.stderr)

        print("[SYDYN] ✓ API key verified\n")
    except Exception as e:
        print(f"[ERROR] Anthropic API key verification failed: {e}", file=sys.stderr)
        print(f"[ERROR] Error type: {type(e).__name__}", file=sys.stderr)
        if hasattr(e, 'status_code'):
            print(f"[ERROR] Status code: {e.status_code}", file=sys.stderr)
        print("[ERROR] Make sure your API key is valid and has access to Claude models", file=sys.stderr)
        sys.exit(1)

    # Initialize engine
    try:
        engine = SydynEngine(
            db_path=args.db_path,
            search_provider=args.search_provider
        )
    except Exception as e:
        print(f"[ERROR] Failed to initialize Sydyn engine: {e}", file=sys.stderr)
        print(f"[ERROR] Make sure you have set TAVILY_API_KEY or SERPER_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    # Execute query
    try:
        result = engine.query(
            query_text=args.query,
            mode=args.mode,
            save_kb=args.save_kb
        )
    except Exception as e:
        print(f"[ERROR] Query failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Output result
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        format_text_output(result, verbose=args.verbose)


def format_text_output(result: dict, verbose: bool = False):
    """Format result as human-readable text.

    Args:
        result: Query result dict
        verbose: Show detailed reasoning
    """
    print()
    print("=" * 70)
    print(f"SYDYN - Real-Time Adversarial Search")
    print("=" * 70)
    print()

    print(f"Query: {result.get('query', 'N/A')}")
    print(f"Mode: {result.get('mode', 'N/A').upper()}")
    print()

    # Cached indicator
    if result.get("cached"):
        print("✓ Answer retrieved from knowledge base (instant)")
        print()

    # Answer
    print("ANSWER:")
    print("-" * 70)
    print(result.get("answer", "No answer generated"))
    print()

    # Confidence
    if "confidence_explanation" in result:
        print(result["confidence_explanation"])
    else:
        confidence = result.get("confidence", 0.0)
        confidence_band = result.get("confidence_band", "UNKNOWN")
        print(f"CONFIDENCE: {confidence:.2f} ({confidence_band})")

    print()

    # Violations
    violations = result.get("violations", [])
    if violations:
        print("CONSTITUTIONAL VIOLATIONS:")
        print("-" * 70)
        for v in violations:
            print(f"• {v.get('rule', 'Unknown')}: {v.get('explanation', 'N/A')}")
            print(f"  Severity: {v.get('severity', 'UNKNOWN')}")
        print()

    # Verdict
    verdict = result.get("verdict", "UNKNOWN")
    if verdict == "BLOCK":
        print("⚠️  VERDICT: BLOCKED (constitutional violations prevent this answer)")
    elif verdict == "WARN":
        print("⚠️  VERDICT: WARNING (answer acceptable with caveats)")
    elif verdict == "PASS":
        print("✓ VERDICT: PASS (no major constitutional issues)")

    print()

    # Timeout warning
    if result.get("timeout"):
        degradation = result.get("degradation_level", "unknown")
        print(f"⚠️  Timeout occurred - degraded to {degradation}")
        print()

    # Metadata
    latency_ms = result.get("latency_ms", 0)
    cost_usd = result.get("cost_usd", 0.0)
    print(f"Completed in {latency_ms / 1000:.1f}s | Cost: ${cost_usd:.4f}")
    print()

    print("=" * 70)


if __name__ == "__main__":
    main()
