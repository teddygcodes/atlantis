"""Timeout handling and graceful degradation."""

import time
from typing import Optional


class TimeoutManager:
    """Manages latency budgets and graceful degradation."""

    # Latency budgets from plan
    TARGET_LATENCY = 55.0  # seconds
    HARD_TIMEOUT = 90.0    # seconds

    # Degradation thresholds
    LEVEL_1_THRESHOLD = 60.0  # Skip Critic
    LEVEL_2_THRESHOLD = 75.0  # Skip Adversary + Critic
    LEVEL_3_THRESHOLD = 90.0  # Evidence-only

    def __init__(self):
        """Initialize timeout manager."""
        self.start_time = None
        self.degradation_level = None

    def start(self):
        """Start timing."""
        self.start_time = time.time()
        self.degradation_level = None

    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def remaining(self, target: Optional[float] = None) -> float:
        """Get remaining time before timeout.

        Args:
            target: Optional target time (defaults to TARGET_LATENCY)

        Returns:
            Remaining seconds
        """
        if target is None:
            target = self.TARGET_LATENCY

        elapsed = self.elapsed()
        return max(0.0, target - elapsed)

    def should_skip_critic(self) -> bool:
        """Check if Critic should be skipped due to timeout.

        Returns:
            True if elapsed > LEVEL_1_THRESHOLD
        """
        elapsed = self.elapsed()

        if elapsed > self.LEVEL_1_THRESHOLD:
            if self.degradation_level is None:
                print(f"[TIMEOUT] Level 1 degradation at {elapsed:.1f}s - skipping Critic")
                self.degradation_level = "no_critic"
            return True

        return False

    def should_skip_adversary(self) -> bool:
        """Check if Adversary should be skipped due to timeout.

        Returns:
            True if elapsed > LEVEL_2_THRESHOLD
        """
        elapsed = self.elapsed()

        if elapsed > self.LEVEL_2_THRESHOLD:
            if self.degradation_level != "no_adversary":
                print(f"[TIMEOUT] Level 2 degradation at {elapsed:.1f}s - skipping Adversary + Critic")
                self.degradation_level = "no_adversary"
            return True

        return False

    def should_return_evidence_only(self) -> bool:
        """Check if should return evidence-only response.

        Returns:
            True if elapsed > LEVEL_3_THRESHOLD
        """
        elapsed = self.elapsed()

        if elapsed > self.LEVEL_3_THRESHOLD:
            if self.degradation_level != "evidence_only":
                print(f"[TIMEOUT] Level 3 degradation at {elapsed:.1f}s - evidence-only response")
                self.degradation_level = "evidence_only"
            return True

        return False

    def get_degradation_level(self) -> Optional[str]:
        """Get current degradation level.

        Returns:
            "no_critic" | "no_adversary" | "evidence_only" | None
        """
        return self.degradation_level

    def get_timeout_message(self) -> str:
        """Get user-facing timeout message.

        Returns:
            Message explaining degradation
        """
        level = self.degradation_level

        if level == "no_critic":
            return "⚠️  Adversarial review incomplete due to timeout"

        elif level == "no_adversary":
            return "⚠️  Adversarial testing skipped due to timeout"

        elif level == "evidence_only":
            return "⚠️  Query too complex for real-time answer. Evidence summary provided. Retry with simpler phrasing."

        return ""

    def format_summary(self) -> str:
        """Format timing summary for output.

        Returns:
            Summary string
        """
        elapsed = self.elapsed()

        if self.degradation_level:
            return (
                f"Completed in {elapsed:.1f}s (timeout occurred, "
                f"degraded to {self.degradation_level})"
            )
        elif elapsed > self.TARGET_LATENCY:
            return f"Completed in {elapsed:.1f}s (exceeded target of {self.TARGET_LATENCY:.0f}s)"
        else:
            return f"Completed in {elapsed:.1f}s"


def build_evidence_only_response(evidence_pack) -> str:
    """Build evidence-only response when timeout occurs.

    Args:
        evidence_pack: EvidencePack object

    Returns:
        Evidence summary text
    """
    lines = [
        "EVIDENCE SUMMARY",
        "=" * 50,
        "",
        f"Query: {evidence_pack.query}",
        f"Sources found: {evidence_pack.total_searched}",
        f"Sources fetched: {len([s for s in evidence_pack.sources if not s.fetch_failed])}",
        "",
        "TOP SOURCES:",
        ""
    ]

    for i, source in enumerate(evidence_pack.sources[:5]):
        if not source.fetch_failed:
            lines.append(f"{i+1}. {source.title}")
            lines.append(f"   {source.url}")
            lines.append(f"   Credibility: {source.credibility_score:.2f}")
            lines.append(f"   {source.snippet[:150]}...")
            lines.append("")

    lines.append("")
    lines.append("⚠️  Full analysis timed out. These sources may help answer your query.")
    lines.append("Try rephrasing with a more specific question.")

    return "\n".join(lines)
