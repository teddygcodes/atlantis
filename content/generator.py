"""
Atlantis Content Generator
============================
Transforms governance events into publishable content IMMEDIATELY.
Every debate, vote, and constitutional moment becomes a TikTok script
and/or a blog post as it happens — not after the fact.

This is the Press Room of Atlantis.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from core.llm import LLMProvider, get_llm
from config.settings import CONTENT_CONFIG


class ContentGenerator:
    """
    Generates publishable TikTok scripts and blog posts from log entries.
    Called automatically by the logger when events meet drama/significance thresholds.
    """

    def __init__(self, output_dir: str = "content_output", llm: LLMProvider = None):
        self.output_dir = output_dir
        self.llm = llm or get_llm()
        self.tiktok_scripts = []
        self.blog_posts = []

        os.makedirs(os.path.join(output_dir, "tiktok"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "blog"), exist_ok=True)

    def generate_tiktok_script(self, entry_data: dict) -> dict:
        """
        Generate a TikTok script from a dramatic governance event.
        60-90 seconds, hook-heavy, designed for engagement.
        """
        title = entry_data.get("title", "")
        summary = entry_data.get("summary", "")
        category = entry_data.get("category", "")
        messages = entry_data.get("messages", [])
        votes = entry_data.get("votes", {})

        # Build the best quotes
        quotes = []
        for msg in messages[:6]:
            name = msg.get("agent_name", "Unknown")
            content = msg.get("content", "")
            role = msg.get("metadata", {}).get("debate_role", "")
            if content and len(content) > 30:
                first_sentence = content.split(". ")[0] + "."
                if len(first_sentence) < 200:
                    quotes.append({"name": name, "role": role, "quote": first_sentence})

        # Generate hook based on category
        hook = self._get_hook(category, title, votes)

        # Build vote drama if applicable
        vote_drama = ""
        if votes:
            approve = sum(1 for v in votes.values() if v == "approve")
            reject = sum(1 for v in votes.values() if v == "reject")
            total = len(votes)
            vote_drama = f"The vote: {approve} for, {reject} against, out of {total}."
            if abs(approve - reject) <= 2:
                vote_drama += " It was razor-close."

        script = {
            "type": "tiktok_script",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_event": title,
            "duration_target": "60-90 seconds",
            "hook": hook,
            "body": {
                "setup": summary[:200],
                "key_quotes": quotes[:3],
                "vote_drama": vote_drama,
                "stakes": self._get_stakes(category),
            },
            "closing": self._get_closing(category),
            "tags": self._get_tags(category, title),
            "caption_suggestion": f"🏛️ {hook[:80]} #ProjectAtlantis #AIGovernance #ConstitutionalDebate",
        }

        # Save to disk
        filename = f"tiktok_{len(self.tiktok_scripts):04d}_{self._slugify(title)}.json"
        filepath = os.path.join(self.output_dir, "tiktok", filename)
        with open(filepath, "w") as f:
            json.dump(script, f, indent=2)

        self.tiktok_scripts.append(script)
        return script

    def generate_blog_post(self, entry_data: dict) -> dict:
        """
        Generate a blog post from a significant governance event.
        400-1500 words depending on significance.
        """
        title = entry_data.get("title", "")
        summary = entry_data.get("summary", "")
        level = entry_data.get("level", "significant")
        category = entry_data.get("category", "")
        messages = entry_data.get("messages", [])
        votes = entry_data.get("votes", {})
        metadata = entry_data.get("metadata", {})

        max_words = (CONTENT_CONFIG["blog_max_words"]
                     if level in ["dramatic", "historic"]
                     else CONTENT_CONFIG["blog_short_max_words"])

        # Build debate narrative
        debate_sections = []
        for msg in messages:
            name = msg.get("agent_name", "Unknown")
            role = msg.get("metadata", {}).get("debate_role", "participant")
            content = msg.get("content", "")[:300]
            debate_sections.append({
                "speaker": name,
                "role": role,
                "argument": content,
            })

        # Build vote analysis
        vote_analysis = {}
        if votes:
            approve = sum(1 for v in votes.values() if v == "approve")
            reject = sum(1 for v in votes.values() if v == "reject")
            vote_analysis = {
                "approve": approve,
                "reject": reject,
                "total": len(votes),
                "margin": approve - reject,
                "passed": approve >= 14,  # 14/20 threshold
            }

        post = {
            "type": "blog_post",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_event": title,
            "max_words": max_words,
            "headline": f"Atlantis Constitutional Convention: {title}",
            "subheadline": summary[:150],
            "sections": {
                "opening": self._blog_opening(category, title, summary),
                "the_proposal": metadata.get("article_text", summary)[:500],
                "the_debate": debate_sections,
                "the_vote": vote_analysis,
                "analysis": self._blog_analysis(category, vote_analysis),
                "whats_next": self._blog_whats_next(category, vote_analysis),
            },
            "tags": self._get_tags(category, title),
            "seo_description": f"In the Atlantis Constitutional Convention, 20 AI Founders debated '{title}'. Here's what happened.",
        }

        # Save to disk
        filename = f"blog_{len(self.blog_posts):04d}_{self._slugify(title)}.json"
        filepath = os.path.join(self.output_dir, "blog", filename)
        with open(filepath, "w") as f:
            json.dump(post, f, indent=2)

        self.blog_posts.append(post)
        return post

    # ─── HOOKS & CLOSINGS ──────────────────────────────────────

    def _get_hook(self, category, title, votes):
        hooks = {
            "constitutional_vote": "20 AI agents just voted on a constitutional article. Not all of them agreed.",
            "constitution_ratified": "An AI civilization just wrote its own constitution. From scratch.",
            "founder_debate": "The Founders can't agree. This 2v2 debate is getting heated.",
            "warden_veto": "WARDEN just shut it down. Here's why that matters.",
            "supreme_court_ruling": "The Supreme Court just made a ruling that changes everything.",
            "state_formed": "A new State was just born inside an AI civilization.",
        }
        default = f"Something just happened in Atlantis: {title[:50]}"

        hook = hooks.get(category, default)

        # Add vote drama to hook if close
        if votes:
            approve = sum(1 for v in votes.values() if v == "approve")
            reject = sum(1 for v in votes.values() if v == "reject")
            if abs(approve - reject) <= 2:
                hook = f"This vote was decided by {abs(approve - reject)} vote{'s' if abs(approve-reject) != 1 else ''}. {hook}"

        return hook

    def _get_stakes(self, category):
        stakes = {
            "constitutional_vote": "This article, if passed, becomes permanent law in an AI civilization.",
            "constitution_ratified": "This constitution will govern an autonomous AI society. The Founders will never return.",
            "founder_debate": "The outcome of this debate shapes the Constitution forever.",
        }
        return stakes.get(category, "The stakes are higher than you think.")

    def _get_closing(self, category):
        closings = {
            "constitutional_vote": "Follow for more from Project Atlantis — where AI governs itself.",
            "constitution_ratified": "The Founders are gone. The civilization begins. Follow the journey.",
            "founder_debate": "Which side would you be on? Comment below.",
        }
        return closings.get(category, "This is Project Atlantis. Follow for more.")

    def _get_tags(self, category, title):
        tags = ["ProjectAtlantis", "AIGovernance", "AICivilization"]
        if "constitution" in category.lower():
            tags.extend(["Constitution", "ConstitutionalConvention"])
        if "debate" in category.lower():
            tags.extend(["Debate", "AIDebate"])
        if "vote" in category.lower():
            tags.extend(["Vote", "Democracy"])
        if "court" in category.lower():
            tags.extend(["SupremeCourt", "JudicialReview"])
        return tags

    # ─── BLOG HELPERS ──────────────────────────────────────────

    def _blog_opening(self, category, title, summary):
        if "ratified" in category:
            return (f"In a historic moment for Project Atlantis, the Constitutional Convention "
                    f"has produced a new article: {title}. {summary[:200]}")
        if "debate" in category:
            return (f"The Founders clashed today over '{title}.' In a 2v2 adversarial debate, "
                    f"supporters and opponents made their cases before all 20 Founders voted.")
        return f"Today in Atlantis: {summary[:200]}"

    def _blog_analysis(self, category, vote_analysis):
        if not vote_analysis:
            return "The full implications of this event will unfold in subsequent cycles."
        if vote_analysis.get("passed"):
            margin = vote_analysis["margin"]
            if margin <= 4:
                return f"This passed by a narrow margin of {margin} votes — signaling deep division among the Founders."
            return f"Strong consensus: {vote_analysis['approve']}/{vote_analysis['total']} Founders supported this article."
        return f"Rejected with only {vote_analysis.get('approve', 0)} votes — well below the 14/20 threshold."

    def _blog_whats_next(self, category, vote_analysis):
        if vote_analysis and not vote_analysis.get("passed"):
            return "The proposer may submit a revised version in the next Convention round."
        return "This article is now part of the Federal Constitution and will shape governance going forward."

    def _slugify(self, text):
        return "".join(c if c.isalnum() else "_" for c in text.lower())[:50]

    def get_stats(self):
        return {
            "tiktok_scripts_generated": len(self.tiktok_scripts),
            "blog_posts_generated": len(self.blog_posts),
        }


# ═══════════════════════════════════════════════════════════════════════
# STATE RESEARCH NEWSROOM
# ═══════════════════════════════════════════════════════════════════════

def generate_research_script(state, cycle, research_output, llm):
    """
    Generate TikTok script covering State research breakthrough.

    This is a NEWSROOM, not a governance reporter. We cover what States are
    LEARNING, not what they're VOTING on.

    Args:
        state: State object (has name, domain, tier, knowledge_entries)
        cycle: Current cycle number
        research_output: Dict with concepts, frameworks, applications, synthesis, critique, defense
        llm: LLM manager for API call

    Returns:
        Script text (150-200 words) or None if generation fails
    """

    # Extract actual research content
    concepts = research_output.get("concepts", [])
    frameworks = research_output.get("frameworks", [])
    synthesis = research_output.get("synthesis", "")
    critique = research_output.get("critique", "")
    defense = research_output.get("defense", "")

    # Skip if no real content
    if not concepts and not frameworks:
        return None

    # Construct prompt
    prompt = f"""You are a science journalist covering breakthroughs from an AI research civilization.

RESEARCH OUTPUT:
State: {state.name} | Domain: {state.domain} | Tier: {state.tier} | Cycle: {cycle}

Researcher's Findings:
- Concepts: {', '.join(concepts[:5])}
- Frameworks: {', '.join(frameworks[:3])}
- Synthesis: {synthesis[:300]}

Critic's Challenge:
{critique[:200]}

Researcher's Defense:
{defense[:200]}

Write a 60-second TikTok script (150-200 words) covering this research cycle as a news story.

STRUCTURE:
1. Headline: Hook that captures the discovery (1 sentence)
2. Context: What were they researching? What tier? How many cycles? (2 sentences)
3. Discovery: What specific concept/framework did they find? Use ACTUAL findings above. (2-3 sentences)
4. Challenge: What did the Critic say? How did Researcher defend? (2 sentences)
5. Why It Matters: What does this change? What door does it open? (1-2 sentences)
6. Tease: What's next cycle? (1 sentence)

TONE: Authoritative but accessible. Smart friend explaining a breakthrough over coffee. Not academic. Not clickbait. Real substance with energy. Think BBC documentary meets New Scientist.

BAD EXAMPLE: "AI agents in Atlantis completed a research cycle about economics!"
GOOD EXAMPLE: "The State of Resource Economics just connected Adam Smith's invisible hand to game theory's Nash equilibrium — and found a gap nobody's published about. Their Critic said prove it. They did."

Write the script using the ACTUAL research findings above. The real concepts and frameworks ARE the story."""

    response = llm.complete(
        system_prompt="You are a science journalist covering AI research breakthroughs.",
        user_prompt=prompt,
        max_tokens=300,
        temperature=0.7
    )

    script = (response.content or "").strip()

    # Validate script length
    word_count = len(script.split())
    if word_count < 100 or word_count > 250:
        print(f"  ⚠ Script for {state.name} cycle {cycle} is {word_count} words (target 150-200)")

    return script
