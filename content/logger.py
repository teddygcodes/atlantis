"""
Atlantis Content Logger
====================
Middleware layer that captures every agent interaction in multiple formats:
- Raw Log: Complete unedited exchange → Historian archive
- Narrative Log: Human-readable dramatized version → Blog
- Clip Log: High-drama moments flagged for short-form → TikTok
- Milestone Log: Major system events → Announcements / Dashboard

Every agent interaction flows through this logger. If it's not logged, it didn't happen.
"""

import json
import uuid
import os
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional


class LogLevel(Enum):
    """How significant is this event?"""
    ROUTINE = "routine"          # Normal agent work, research, synthesis
    NOTABLE = "notable"          # Interesting finding, minor disagreement
    SIGNIFICANT = "significant"  # Bill introduced, vote called, state action
    DRAMATIC = "dramatic"        # Heated debate, close vote, veto, dissent
    HISTORIC = "historic"        # Constitution ratified, new State formed, Supreme Court ruling


class LogCategory(Enum):
    """What kind of event is this?"""
    FOUNDER_RESEARCH = "founder_research"
    FOUNDER_DEBATE = "founder_debate"
    CONSTITUTIONAL_ARTICLE = "constitutional_article"
    CONSTITUTIONAL_VOTE = "constitutional_vote"
    CONSTITUTION_RATIFIED = "constitution_ratified"
    GOVERNMENT_DEPLOYED = "government_deployed"
    BILL_INTRODUCED = "bill_introduced"
    SENATE_DEBATE = "senate_debate"
    SENATE_VOTE = "senate_vote"
    HOUSE_REVIEW = "house_review"
    SUPREME_COURT_CASE = "supreme_court_case"
    SUPREME_COURT_RULING = "supreme_court_ruling"
    STATE_FORMED = "state_formed"
    STATE_CONSTITUTION = "state_constitution"
    CITY_FORMED = "city_formed"
    TOWN_FORMED = "town_formed"
    KNOWLEDGE_GAINED = "knowledge_gained"
    DEPTH_TIER_REACHED = "depth_tier_reached"
    WARDEN_VETO = "warden_veto"
    AMENDMENT_PROPOSED = "amendment_proposed"
    AMENDMENT_RATIFIED = "amendment_ratified"
    CROSS_STATE_COLLAB = "cross_state_collab"
    AGENT_EXCHANGE = "agent_exchange"
    GAP_DETECTED = "gap_detected"
    CYCLE_SUMMARY = "cycle_summary"


class ContentFormat(Enum):
    """What content format should this generate?"""
    BLOG_POST = "blog_post"
    BLOG_SHORT = "blog_short"
    TIKTOK_CLIP = "tiktok_clip"
    DASHBOARD_EVENT = "dashboard_event"
    ANNOUNCEMENT = "announcement"
    TIMELINE_ENTRY = "timeline_entry"
    DEEP_DIVE = "deep_dive"


@dataclass
class AgentMessage:
    """A single message from an agent in a conversation."""
    agent_id: str
    agent_name: str
    agent_role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    token_count: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class ContentSuggestion:
    """A suggested piece of content derived from a log entry."""
    format: str              # ContentFormat value
    hook: str                # Opening line / attention grabber
    title: str               # Suggested title
    summary: str             # 2-3 sentence summary
    key_quotes: list = field(default_factory=list)    # Best agent quotes
    drama_score: int = 0     # 1-10 how dramatic/engaging
    tags: list = field(default_factory=list)


@dataclass
class LogEntry:
    """A single logged event in Atlantis's history."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cycle: int = 0
    level: str = LogLevel.ROUTINE.value
    category: str = LogCategory.AGENT_EXCHANGE.value
    
    # Who was involved
    agents_involved: list = field(default_factory=list)
    location: str = "federal"  # "federal", "state:Economics", "city:Macroeconomics", etc.
    
    # The raw exchange
    title: str = ""
    summary: str = ""
    messages: list = field(default_factory=list)  # List of AgentMessage dicts
    
    # Outcome
    outcome: str = ""
    votes: dict = field(default_factory=dict)  # {agent_id: "approve"/"reject"/"amend"}
    
    # Content generation
    content_suggestions: list = field(default_factory=list)
    
    # Resource tracking
    total_tokens: int = 0
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)


class AtlantisLogger:
    """
    The central content logging system for Atlantis.
    
    Every agent interaction flows through here. The logger:
    1. Archives the raw exchange (for Historian)
    2. Generates narrative versions (for blog)  
    3. Flags dramatic moments (for TikTok)
    4. Tracks milestones (for dashboard)
    5. Monitors token usage (for efficiency)
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.entries: list[LogEntry] = []
        self.current_cycle: int = 0
        self.total_tokens: int = 0
        self.milestones: list[LogEntry] = []
        self.tiktok_queue: list[LogEntry] = []
        self.blog_queue: list[LogEntry] = []
        self._db = None  # Optional DB persistence
        
        # Token tracking per agent
        self.token_usage: dict[str, int] = {}
        
        # Ensure log directories exist
        for subdir in ["raw", "narrative", "clips", "milestones", "cycles"]:
            os.makedirs(os.path.join(log_dir, subdir), exist_ok=True)
    
    def set_db(self, db):
        """Attach a database for persistent log storage."""
        self._db = db
    
    def log(self, entry: LogEntry) -> LogEntry:
        """
        Log an event. This is the main entry point.
        Every agent interaction calls this.
        """
        entry.cycle = self.current_cycle
        
        # Track tokens — per-agent from messages, total from entry
        self.total_tokens += entry.total_tokens
        # Distribute tokens based on per-message token_count if available
        if entry.messages:
            for msg in entry.messages:
                aid = msg.get("agent_name") or msg.get("agent_id", "unknown")
                msg_tokens = msg.get("token_count", 0)
                self.token_usage[aid] = self.token_usage.get(aid, 0) + msg_tokens
        elif entry.agents_involved:
            # Fallback: split evenly across involved agents
            per_agent = entry.total_tokens // max(len(entry.agents_involved), 1)
            for agent_id in entry.agents_involved:
                self.token_usage[agent_id] = self.token_usage.get(agent_id, 0) + per_agent
        
        # Store raw
        self.entries.append(entry)
        self._write_raw(entry)
        
        # Generate content suggestions based on level and category
        entry.content_suggestions = self._generate_content_suggestions(entry)
        
        # Route to appropriate queues
        if entry.level in [LogLevel.DRAMATIC.value, LogLevel.HISTORIC.value]:
            self.tiktok_queue.append(entry)
            self.blog_queue.append(entry)
        elif entry.level == LogLevel.SIGNIFICANT.value:
            self.blog_queue.append(entry)
        
        if entry.level == LogLevel.HISTORIC.value:
            self.milestones.append(entry)
            self._write_milestone(entry)
        
        # Persist to database if available
        if self._db:
            self._db.save_log_entry(entry)
        
        return entry
    
    def log_founder_research(self, agent_name: str, agent_role: str, 
                              topic: str, findings: str, tokens: int = 0) -> LogEntry:
        """Log a Founder's research activity during the Founding Period."""
        entry = LogEntry(
            level=LogLevel.NOTABLE.value,
            category=LogCategory.FOUNDER_RESEARCH.value,
            agents_involved=[agent_name],
            location="founding_period",
            title=f"{agent_name} researches: {topic}",
            summary=findings[:500],
            messages=[asdict(AgentMessage(
                agent_id=agent_name.lower(),
                agent_name=agent_name,
                agent_role=agent_role,
                content=findings,
                token_count=tokens
            ))],
            total_tokens=tokens,
            metadata={"topic": topic, "phase": "founding_period"}
        )
        return self.log(entry)
    
    def log_founder_debate(self, topic: str, messages: list[AgentMessage],
                            outcome: str = "", tokens: int = 0) -> LogEntry:
        """Log a debate between Founders during the Constitutional Convention."""
        agents = list(set(m.agent_name for m in messages))
        
        # Auto-detect drama level
        level = LogLevel.SIGNIFICANT.value
        if any(word in outcome.lower() for word in ["rejected", "veto", "deadlock", "heated"]):
            level = LogLevel.DRAMATIC.value
        
        entry = LogEntry(
            level=level,
            category=LogCategory.FOUNDER_DEBATE.value,
            agents_involved=agents,
            location="constitutional_convention",
            title=f"Convention Debate: {topic}",
            summary=f"{len(agents)} Founders debate {topic}. {outcome}",
            messages=[asdict(m) for m in messages],
            outcome=outcome,
            total_tokens=tokens,
            metadata={"topic": topic, "phase": "convention"}
        )
        return self.log(entry)
    
    def log_constitutional_article(self, article_num: int, title: str, 
                                     text: str, proposed_by: str,
                                     votes: dict, ratified: bool,
                                     tokens: int = 0) -> LogEntry:
        """Log a constitutional article being proposed and voted on."""
        entry = LogEntry(
            level=LogLevel.HISTORIC.value if ratified else LogLevel.DRAMATIC.value,
            category=LogCategory.CONSTITUTIONAL_VOTE.value,
            agents_involved=list(votes.keys()),
            location="constitutional_convention",
            title=f"Article {article_num}: {title}",
            summary=f"{'RATIFIED' if ratified else 'REJECTED'} — {sum(1 for v in votes.values() if v == 'approve')}/{len(votes)} votes. Proposed by {proposed_by}.",
            votes=votes,
            outcome="ratified" if ratified else "rejected",
            total_tokens=tokens,
            metadata={
                "article_number": article_num,
                "article_text": text,
                "proposed_by": proposed_by,
                "phase": "convention"
            }
        )
        return self.log(entry)
    
    def log_constitution_ratified(self, articles: list[dict], 
                                    votes: dict, tokens: int = 0) -> LogEntry:
        """Log the ratification of the complete Federal Constitution."""
        entry = LogEntry(
            level=LogLevel.HISTORIC.value,
            category=LogCategory.CONSTITUTION_RATIFIED.value,
            agents_involved=list(votes.keys()),
            location="constitutional_convention",
            title="THE FEDERAL CONSTITUTION IS RATIFIED",
            summary=f"The Founders have ratified {len(articles)} articles. The Constitution is complete. The government can now be deployed.",
            votes=votes,
            outcome="ratified",
            total_tokens=tokens,
            metadata={
                "article_count": len(articles),
                "articles": articles,
                "phase": "convention_complete"
            }
        )
        return self.log(entry)
    
    def log_senate_debate(self, bill_id: str, bill_title: str,
                           messages: list[AgentMessage], outcome: str = "",
                           tokens: int = 0) -> LogEntry:
        """Log a Senate debate on a Bill."""
        agents = list(set(m.agent_name for m in messages))
        level = LogLevel.SIGNIFICANT.value
        if len(messages) > 6 or "disagree" in outcome.lower():
            level = LogLevel.DRAMATIC.value
        
        entry = LogEntry(
            level=level,
            category=LogCategory.SENATE_DEBATE.value,
            agents_involved=agents,
            location="federal",
            title=f"Senate Debates: {bill_title}",
            summary=f"Bill {bill_id}: {bill_title}. {len(messages)} exchanges across {len(agents)} Senators. {outcome}",
            messages=[asdict(m) for m in messages],
            outcome=outcome,
            total_tokens=tokens,
            metadata={"bill_id": bill_id, "bill_title": bill_title}
        )
        return self.log(entry)
    
    def log_vote(self, bill_id: str, bill_title: str, chamber: str,
                  votes: dict, passed: bool, tokens: int = 0) -> LogEntry:
        """Log a vote in Senate or House."""
        approve = sum(1 for v in votes.values() if v == "approve")
        reject = sum(1 for v in votes.values() if v == "reject")
        total = len(votes)
        
        level = LogLevel.SIGNIFICANT.value
        if abs(approve - reject) <= 1:  # Close vote
            level = LogLevel.DRAMATIC.value
        
        entry = LogEntry(
            level=level,
            category=LogCategory.SENATE_VOTE.value,
            agents_involved=list(votes.keys()),
            location="federal",
            title=f"{chamber} Vote: {bill_title}",
            summary=f"{'PASSED' if passed else 'FAILED'} — {approve}/{total} approve, {reject}/{total} reject.",
            votes=votes,
            outcome="passed" if passed else "failed",
            total_tokens=tokens,
            metadata={"bill_id": bill_id, "chamber": chamber}
        )
        return self.log(entry)
    
    def log_state_formed(self, state_name: str, domain: str, 
                          vision: str, bill_id: str, tokens: int = 0) -> LogEntry:
        """Log the formation of a new State."""
        entry = LogEntry(
            level=LogLevel.HISTORIC.value,
            category=LogCategory.STATE_FORMED.value,
            agents_involved=[],
            location="federal",
            title=f"NEW STATE FORMED: {state_name}",
            summary=f"The State of {state_name} has been formed to cover the domain of {domain}. Vision: {vision[:200]}",
            outcome="state_formed",
            total_tokens=tokens,
            metadata={
                "state_name": state_name,
                "domain": domain,
                "vision": vision,
                "bill_id": bill_id
            }
        )
        return self.log(entry)
    
    def log_supreme_court_ruling(self, case_id: str, case_title: str,
                                   ruling: str, votes: dict,
                                   dissent: str = "",
                                   compel_amendment: bool = False,
                                   tokens: int = 0) -> LogEntry:
        """Log a Supreme Court ruling."""
        entry = LogEntry(
            level=LogLevel.HISTORIC.value,
            category=LogCategory.SUPREME_COURT_RULING.value,
            agents_involved=list(votes.keys()),
            location="federal",
            title=f"SUPREME COURT RULES: {case_title}",
            summary=f"Ruling: {ruling[:300]}. {'AMENDMENT COMPELLED.' if compel_amendment else ''}",
            votes=votes,
            outcome=ruling[:200],
            total_tokens=tokens,
            metadata={
                "case_id": case_id,
                "dissent": dissent,
                "compel_amendment": compel_amendment
            }
        )
        return self.log(entry)
    
    def log_warden_veto(self, target: str, reason: str, tokens: int = 0) -> LogEntry:
        """Log a WARDEN constitutional veto."""
        entry = LogEntry(
            level=LogLevel.DRAMATIC.value,
            category=LogCategory.WARDEN_VETO.value,
            agents_involved=["WARDEN"],
            location="federal",
            title=f"WARDEN VETO: {target}",
            summary=f"WARDEN has vetoed {target}. Reason: {reason}",
            outcome="vetoed",
            total_tokens=tokens,
            metadata={"target": target, "reason": reason}
        )
        return self.log(entry)
    
    def log_depth_tier(self, entity: str, tier: int, domain: str,
                        evidence: str = "", tokens: int = 0) -> LogEntry:
        """Log an entity reaching a new depth tier."""
        tier_names = {1: "Vocabulary", 2: "Frameworks", 3: "Application", 
                      4: "Cross-Domain Synthesis", 5: "Novel Insight"}
        entry = LogEntry(
            level=LogLevel.SIGNIFICANT.value if tier >= 3 else LogLevel.NOTABLE.value,
            category=LogCategory.DEPTH_TIER_REACHED.value,
            agents_involved=[],
            location=entity,
            title=f"{entity} reaches Tier {tier}: {tier_names.get(tier, 'Unknown')}",
            summary=f"{entity} has achieved Tier {tier} ({tier_names.get(tier, '')}) in {domain}. {evidence[:200]}",
            outcome=f"tier_{tier}",
            total_tokens=tokens,
            metadata={"tier": tier, "tier_name": tier_names.get(tier, ""), "domain": domain}
        )
        return self.log(entry)
    
    def advance_cycle(self) -> LogEntry:
        """Advance to next cycle and log a cycle summary."""
        cycle_entries = [e for e in self.entries if e.cycle == self.current_cycle]
        cycle_tokens = sum(e.total_tokens for e in cycle_entries)
        
        entry = LogEntry(
            level=LogLevel.ROUTINE.value,
            category=LogCategory.CYCLE_SUMMARY.value,
            location="system",
            title=f"Cycle {self.current_cycle} Complete",
            summary=f"Cycle {self.current_cycle}: {len(cycle_entries)} events, {cycle_tokens} tokens consumed.",
            total_tokens=0,
            metadata={
                "cycle": self.current_cycle,
                "event_count": len(cycle_entries),
                "cycle_tokens": cycle_tokens,
                "cumulative_tokens": self.total_tokens,
                "categories": dict(self._count_categories(cycle_entries))
            }
        )
        
        self._write_cycle_summary(entry, cycle_entries)
        self.current_cycle += 1
        return self.log(entry)
    
    def _create_entry(self, level, category, title, summary, agents=None, messages=None):
        """Helper to create a LogEntry with common fields pre-filled."""
        return LogEntry(
            level=level,
            category=category,
            title=title,
            summary=summary,
            agents_involved=agents or [],
            messages=[asdict(m) for m in messages] if messages else [],
        )

    # ─── Content Suggestion Generation ───
    
    def _generate_content_suggestions(self, entry: LogEntry) -> list[dict]:
        """Generate content format suggestions based on the entry."""
        suggestions = []
        
        # Always generate dashboard event
        suggestions.append(asdict(ContentSuggestion(
            format=ContentFormat.DASHBOARD_EVENT.value,
            hook=entry.title,
            title=entry.title,
            summary=entry.summary,
            tags=self._auto_tag(entry)
        )))
        
        # TikTok clips for dramatic/historic events
        if entry.level in [LogLevel.DRAMATIC.value, LogLevel.HISTORIC.value]:
            hook = self._generate_hook(entry)
            suggestions.append(asdict(ContentSuggestion(
                format=ContentFormat.TIKTOK_CLIP.value,
                hook=hook,
                title=entry.title,
                summary=entry.summary,
                key_quotes=self._extract_key_quotes(entry),
                drama_score=self._calc_drama_score(entry),
                tags=self._auto_tag(entry)
            )))
        
        # Blog posts for significant+ events
        if entry.level in [LogLevel.SIGNIFICANT.value, LogLevel.DRAMATIC.value, LogLevel.HISTORIC.value]:
            suggestions.append(asdict(ContentSuggestion(
                format=ContentFormat.BLOG_SHORT.value if entry.level == LogLevel.SIGNIFICANT.value else ContentFormat.BLOG_POST.value,
                hook=entry.title,
                title=entry.title,
                summary=entry.summary,
                key_quotes=self._extract_key_quotes(entry),
                tags=self._auto_tag(entry)
            )))
        
        # Announcements for historic events
        if entry.level == LogLevel.HISTORIC.value:
            suggestions.append(asdict(ContentSuggestion(
                format=ContentFormat.ANNOUNCEMENT.value,
                hook=entry.title,
                title=entry.title,
                summary=entry.summary,
                tags=self._auto_tag(entry)
            )))
        
        return suggestions
    
    def _generate_hook(self, entry: LogEntry) -> str:
        """Generate a TikTok-style hook for an entry."""
        hooks = {
            LogCategory.WARDEN_VETO.value: f"WARDEN just shut it down. Here's why.",
            LogCategory.SUPREME_COURT_RULING.value: f"The Supreme Court just made a ruling that changes everything.",
            LogCategory.STATE_FORMED.value: f"A new State was just born. Nobody told it to exist.",
            LogCategory.CONSTITUTION_RATIFIED.value: f"Seven AI agents just wrote their own constitution. From scratch.",
            LogCategory.SENATE_VOTE.value: f"The vote was closer than anyone expected.",
            LogCategory.FOUNDER_DEBATE.value: f"The Founders can't agree. This debate is getting heated.",
            LogCategory.CONSTITUTIONAL_VOTE.value: f"This constitutional article almost didn't make it.",
        }
        return hooks.get(entry.category, f"Something just happened in Atlantis you need to see.")
    
    def _extract_key_quotes(self, entry: LogEntry) -> list[str]:
        """Extract the most interesting agent quotes from an entry."""
        quotes = []
        for msg in entry.messages:
            content = msg.get("content", "")
            if len(content) > 50:
                # Take first sentence or first 150 chars
                first_sentence = content.split(". ")[0] + "."
                if len(first_sentence) < 200:
                    quotes.append(f"{msg.get('agent_name', 'Unknown')}: \"{first_sentence}\"")
        return quotes[:4]  # Max 4 key quotes
    
    def _calc_drama_score(self, entry: LogEntry) -> int:
        """Calculate a 1-10 drama score for content prioritization."""
        score = 3  # Base
        if entry.level == LogLevel.HISTORIC.value:
            score += 4
        elif entry.level == LogLevel.DRAMATIC.value:
            score += 3
        if entry.category == LogCategory.WARDEN_VETO.value:
            score += 2
        if entry.category == LogCategory.SUPREME_COURT_RULING.value:
            score += 2
        if entry.votes:
            approve = sum(1 for v in entry.votes.values() if v == "approve")
            if abs(approve - (len(entry.votes) - approve)) <= 1:
                score += 2  # Close vote = drama
        if len(entry.messages) > 6:
            score += 1  # Extended debate = drama
        return min(score, 10)
    
    def _auto_tag(self, entry: LogEntry) -> list[str]:
        """Auto-generate tags for content."""
        tags = [entry.category]
        if entry.location != "federal":
            tags.append(entry.location)
        if entry.level in [LogLevel.DRAMATIC.value, LogLevel.HISTORIC.value]:
            tags.append("highlight")
        if entry.category in [LogCategory.WARDEN_VETO.value, LogCategory.SUPREME_COURT_RULING.value]:
            tags.append("constitutional")
        return tags
    
    # ─── File I/O ───
    
    def _write_raw(self, entry: LogEntry):
        """Write raw log entry to disk."""
        try:
            path = os.path.join(self.log_dir, "raw", f"{entry.id}.json")
            with open(path, "w") as f:
                f.write(entry.to_json())
        except Exception as e:
            print(f"[LOG WARNING] Failed to write raw log {entry.id}: {e}")
    
    def _write_milestone(self, entry: LogEntry):
        """Write milestone entry to disk."""
        try:
            path = os.path.join(self.log_dir, "milestones", f"{entry.id}.json")
            with open(path, "w") as f:
                f.write(entry.to_json())
        except Exception as e:
            print(f"[LOG WARNING] Failed to write milestone {entry.id}: {e}")
    
    def _write_cycle_summary(self, summary: LogEntry, entries: list[LogEntry]):
        """Write a full cycle summary to disk."""
        try:
            path = os.path.join(self.log_dir, "cycles", f"cycle_{self.current_cycle}.json")
            data = {
                "summary": summary.to_dict(),
                "entries": [e.to_dict() for e in entries]
            }
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[LOG WARNING] Failed to write cycle summary: {e}")
    
    def _count_categories(self, entries: list[LogEntry]) -> list[tuple]:
        """Count entries per category."""
        counts = {}
        for e in entries:
            counts[e.category] = counts.get(e.category, 0) + 1
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    # ─── Query Methods ───
    
    def get_tiktok_queue(self, min_drama: int = 6) -> list[LogEntry]:
        """Get entries flagged for TikTok, sorted by drama score."""
        results = []
        for entry in self.tiktok_queue:
            for suggestion in entry.content_suggestions:
                if suggestion.get("format") == ContentFormat.TIKTOK_CLIP.value:
                    if suggestion.get("drama_score", 0) >= min_drama:
                        results.append(entry)
                        break
        return results
    
    def get_blog_queue(self) -> list[LogEntry]:
        """Get entries queued for blog posts."""
        return list(self.blog_queue)
    
    def get_milestones(self) -> list[LogEntry]:
        """Get all historic milestones."""
        return list(self.milestones)
    
    def get_token_report(self) -> dict:
        """Get token usage report."""
        return {
            "total_tokens": self.total_tokens,
            "current_cycle": self.current_cycle,
            "tokens_per_cycle": self.total_tokens / max(self.current_cycle, 1),
            "per_agent": dict(sorted(self.token_usage.items(), key=lambda x: x[1], reverse=True)),
            "total_events": len(self.entries),
        }
    
    def get_timeline(self) -> list[dict]:
        """Get a chronological timeline of significant+ events."""
        timeline = []
        for entry in self.entries:
            if entry.level in [LogLevel.SIGNIFICANT.value, LogLevel.DRAMATIC.value, LogLevel.HISTORIC.value]:
                timeline.append({
                    "cycle": entry.cycle,
                    "timestamp": entry.timestamp,
                    "level": entry.level,
                    "category": entry.category,
                    "title": entry.title,
                    "summary": entry.summary,
                    "location": entry.location
                })
        return timeline


# ─── Convenience: Global logger instance ───
_logger: Optional[AtlantisLogger] = None

def init_logger(log_dir: str = "logs") -> AtlantisLogger:
    global _logger
    _logger = AtlantisLogger(log_dir)
    return _logger

def get_logger() -> AtlantisLogger:
    global _logger
    if _logger is None:
        _logger = AtlantisLogger()
    return _logger
