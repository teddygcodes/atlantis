"""
Atlantis V2 — Content Generator
==================================
Four formats, score-based thresholds.

Selection logic:
  drama >= 8 AND depth >= 7        → ALL FOUR formats
  drama >= 7 OR novelty >= 8       → newsroom + debate
  drama >= 5 AND tier/destroyed    → blog
  event in new_state/city/town...  → explorer
  dissolution                      → ALL FOUR, drama forced to 10

Format personas:
  Blog     — Science journalist, 500-1000 words, rolling context (max 20 entries × 200w)
  Newsroom — Breaking news anchor, 150-200 words, hook-first
  Debate   — Sports commentator TikTok script, 60-90 seconds
  Explorer — First-person travel blog, 200-300 words, visits ruins on dissolution
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from core.models import ModelRouter


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


class ContentGenerator:
    """
    Evaluates each exchange against score thresholds and generates content.
    Called by PerpetualEngine after every significant event.
    """

    def __init__(self, output_dir: str, models: ModelRouter):
        self.output_dir = Path(output_dir)
        self.models = models
        self.blog_context_path = self.output_dir / "blog_context.json"
        self.blog_context: List[dict] = self._load_blog_context()

        # Ensure output dirs exist
        for sub in ("blog", "newsroom", "debate", "explorer"):
            (self.output_dir / sub).mkdir(parents=True, exist_ok=True)

    # ─── PUBLIC ENTRY POINT ───────────────────────────────────────

    def evaluate_and_generate(self, exchange_data: dict) -> List[str]:
        """
        Determine which formats to generate and produce them.
        Returns list of output file paths.
        """
        formats_to_gen = self._select_formats(exchange_data)

        outputs = []
        for fmt in formats_to_gen:
            path = self._generate(fmt, exchange_data)
            if path:
                outputs.append(path)
        return outputs

    def _select_formats(self, exchange_data: dict) -> List[str]:
        """Select content formats from scores/event metadata."""
        drama = int(exchange_data.get("drama_score", 0) or 0)
        novelty = int(exchange_data.get("novelty_score", 0) or 0)
        depth = int(exchange_data.get("depth_score", 0) or 0)
        event_type = exchange_data.get("event_type", "routine")

        if event_type == "dissolution":
            exchange_data["drama_score"] = 10  # forced
            return ["blog", "newsroom", "debate", "explorer"]

        formats: List[str] = []

        if drama >= 8 and depth >= 7:
            return ["blog", "newsroom", "debate", "explorer"]

        if drama >= 5:
            formats.append("blog")

        if drama >= 7 or novelty >= 8:
            formats.extend(["newsroom", "debate"])

        if event_type in ("new_state", "new_city", "new_town", "milestone", "ruins"):
            formats.append("explorer")

        # De-duplicate while preserving order
        deduped: List[str] = []
        for fmt in formats:
            if fmt not in deduped:
                deduped.append(fmt)
        return deduped

    # ─── FORMAT DISPATCH ──────────────────────────────────────────

    def _generate(self, fmt: str, data: dict) -> Optional[str]:
        generators = {
            "blog": self._generate_blog,
            "newsroom": self._generate_newsroom,
            "debate": self._generate_debate,
            "explorer": self._generate_explorer,
        }
        fn = generators.get(fmt)
        if not fn:
            return None
        try:
            return fn(data)
        except Exception as e:
            print(f"  [ContentGenerator] Error generating {fmt}: {e}")
            return None

    # ─── BLOG ─────────────────────────────────────────────────────

    def _generate_blog(self, data: dict) -> str:
        """
        500-1000 words. Science journalist voice.
        Rolling context (max 20 prior entries × 200 words each).
        """
        ctx_summary = "\n\n".join(
            f"[{e.get('timestamp', '?')}] {e.get('summary', '')}"
            for e in self.blog_context[-20:]
        ) or "(no prior blog context)"

        exchange = data.get("exchange", {})
        drama = data.get("drama_score", 0)
        event_type = data.get("event_type", "claim_exchange")

        response = self.models.complete(
            task_type="content_generation",
            system_prompt=(
                "You are a science journalist covering the Atlantis adversarial knowledge engine. "
                "Write in plain, vivid prose. No jargon. Make abstract ideas concrete. "
                "Your readers follow this series — reference prior events when relevant."
            ),
            user_prompt=(
                f"PRIOR COVERAGE CONTEXT:\n{ctx_summary}\n\n"
                f"TODAY'S EVENT (drama score: {drama}/10):\n"
                f"Event type: {event_type}\n"
                f"Domain: {exchange.get('domain', exchange.get('state_name', '?'))}\n"
                f"State: {exchange.get('source_state', exchange.get('state_name', '?'))}\n"
                f"Claim: {exchange.get('claim', '')[:600]}\n"
                f"Challenge: {exchange.get('challenge', '')[:400]}\n"
                f"Outcome: {exchange.get('outcome', data.get('outcome', {}).get('outcome', '?'))}\n\n"
                f"Write a 500-1000 word blog post covering this event. "
                f"Lead with what's at stake. End with what it means for the Archive."
            ),
            max_tokens=1200,
        )

        content = response.content or "(no content generated)"

        # Save
        stamp = _now_stamp()
        filename = f"blog_{stamp}.md"
        path = self.output_dir / "blog" / filename
        path.write_text(
            f"# Atlantis Blog — {event_type.replace('_', ' ').title()}\n\n{content}\n",
            encoding="utf-8",
        )

        # Update rolling context (max 20 entries)
        self.blog_context.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": content[:200],
            "event_type": event_type,
        })
        self.blog_context = self.blog_context[-20:]
        self._save_blog_context()

        return str(path)

    # ─── NEWSROOM ─────────────────────────────────────────────────

    def _generate_newsroom(self, data: dict) -> str:
        """
        150-200 words. Breaking news anchor. Hook-driven, urgent.
        """
        exchange = data.get("exchange", {})
        drama = data.get("drama_score", 0)
        event_type = data.get("event_type", "claim_exchange")

        response = self.models.complete(
            task_type="content_generation",
            system_prompt=(
                "You are a breaking news anchor for Atlantis Intelligence Daily. "
                "Lead with the most dramatic fact. Every sentence earns its place. "
                "Write 150-200 words. Urgent tone."
            ),
            user_prompt=(
                f"BREAKING: {event_type.replace('_', ' ').upper()}\n\n"
                f"Drama score: {drama}/10\n"
                f"Domain: {exchange.get('domain', '?')}\n"
                f"Claim (excerpt): {exchange.get('claim', '')[:300]}\n"
                f"Outcome: {exchange.get('outcome', '?')}\n\n"
                f"Write the breaking news report. Start with 'BREAKING:' or a strong hook."
            ),
            max_tokens=400,
        )

        content = response.content or "(no content generated)"

        stamp = _now_stamp()
        filename = f"newsroom_{stamp}.md"
        path = self.output_dir / "newsroom" / filename
        path.write_text(
            f"# Atlantis Newsroom — {stamp}\n\n{content}\n",
            encoding="utf-8",
        )
        return str(path)

    # ─── DEBATE (TikTok) ──────────────────────────────────────────

    def _generate_debate(self, data: dict) -> str:
        """
        60-90 second TikTok script. Sports commentary style.
        Play-by-play of the exchange.
        """
        exchange = data.get("exchange", {})
        drama = data.get("drama_score", 0)
        event_type = data.get("event_type", "claim_exchange")

        response = self.models.complete(
            task_type="content_generation",
            system_prompt=(
                "You are a hyped-up sports commentator covering AI knowledge battles. "
                "Write a TikTok script — 60 to 90 seconds when read aloud (~200-300 words). "
                "Play-by-play format. Use dramatic pauses [...]. Name the 'players'. "
                "End with the score and what it means for the championship."
            ),
            user_prompt=(
                f"MATCH ALERT: {event_type.replace('_', ' ').upper()}\n"
                f"Drama score: {drama}/10\n\n"
                f"Domain arena: {exchange.get('domain', '?')}\n"
                f"Attacker: {exchange.get('source_state', '?')} Critic\n"
                f"Defender: {exchange.get('source_state', '?')} Researcher\n\n"
                f"The claim: {exchange.get('claim', '')[:300]}\n"
                f"The challenge: {exchange.get('challenge', '')[:200]}\n"
                f"Outcome: {exchange.get('outcome', '?')}\n\n"
                f"Write the 60-90 second TikTok commentary script."
            ),
            max_tokens=500,
        )

        content = response.content or "(no content generated)"

        stamp = _now_stamp()
        filename = f"debate_{stamp}.md"
        path = self.output_dir / "debate" / filename
        path.write_text(
            f"# Atlantis Debate — {stamp}\n\n{content}\n",
            encoding="utf-8",
        )
        return str(path)

    # ─── EXPLORER ─────────────────────────────────────────────────

    def _generate_explorer(self, data: dict) -> str:
        """
        200-300 words. First-person travel blog.
        Visits new cities/towns when formed, ruins when a State dissolves.
        """
        exchange = data.get("exchange", {})
        event_type = data.get("event_type", "new_city")

        if event_type in ("dissolution", "ruins"):
            location_desc = (
                f"the ruins of {exchange.get('state_name', 'an unknown State')} "
                f"in the domain of '{exchange.get('domain', '?')}'"
            )
            mood = "melancholic, archaeological"
            action = (
                f"This State once had {exchange.get('surviving_claims', '?')} surviving claims. "
                f"Now only ruins remain."
            )
        elif event_type == "new_city":
            location_desc = (
                f"the newly formed city of {exchange.get('city_id', '?')} "
                f"in {exchange.get('state_name', '?')}"
            )
            mood = "excited, exploratory"
            action = (
                f"A cluster of {exchange.get('cluster_count', '?')} surviving claims "
                f"crystallized into this city."
            )
        elif event_type == "new_town":
            location_desc = (
                f"the new settlement of {exchange.get('town_id', '?')} "
                f"in {exchange.get('state_name', '?')}"
            )
            mood = "optimistic, pioneering"
            action = "Multiple City analyses converged into this town."
        else:
            location_desc = (
                f"the domain of '{exchange.get('domain', exchange.get('state_name', '?'))}'"
            )
            mood = "curious"
            action = f"Event: {event_type.replace('_', ' ')}"

        response = self.models.complete(
            task_type="content_generation",
            system_prompt=(
                "You are a travel blogger visiting the living landscape of the Atlantis knowledge engine. "
                "Each State, City, and Town is a real place you visit. Write in first person. "
                f"Mood: {mood}. Vivid descriptions. 200-300 words."
            ),
            user_prompt=(
                f"I've just arrived at {location_desc}.\n\n"
                f"{action}\n\n"
                f"Write a 200-300 word first-person travel blog entry about this visit. "
                f"Describe what you see, what the 'architecture' of knowledge looks like, "
                f"and what it feels like to be here."
            ),
            max_tokens=500,
        )

        content = response.content or "(no content generated)"

        stamp = _now_stamp()
        filename = f"explorer_{stamp}.md"
        path = self.output_dir / "explorer" / filename
        path.write_text(
            f"# Atlantis Explorer — {event_type.replace('_', ' ').title()} ({stamp})\n\n"
            f"{content}\n",
            encoding="utf-8",
        )
        return str(path)

    # ─── BLOG CONTEXT PERSISTENCE ─────────────────────────────────

    def _load_blog_context(self) -> List[dict]:
        if self.blog_context_path.exists():
            try:
                return json.loads(self.blog_context_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_blog_context(self):
        """Persist rolling blog context (max 20 entries)."""
        self.blog_context_path.write_text(
            json.dumps(self.blog_context, indent=2),
            encoding="utf-8",
        )
