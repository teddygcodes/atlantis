"""
Project Atlantis V2 — System Configuration
==========================================
V2 is an adversarial knowledge engine. Rival States attack each other.
Knowledge enters the Archive only if it survives adversarial challenge.
Full text of every exchange is preserved. States can and should die.
"""

# ═══════════════════════════════════════
# SYSTEM IDENTITY
# ═══════════════════════════════════════
SYSTEM_NAME = "ATLANTIS"
VERSION = "2.0.0"
DESCRIPTION = "The Lost Civilization, Rebuilt — Adversarial Knowledge Engine"

# ═══════════════════════════════════════
# V2 TIER SYSTEM (based on SURVIVING CLAIMS, not concept counts)
# ═══════════════════════════════════════
V2_TIERS = {
    0: {"name": "Empty", "surviving_claims": 0},
    1: {"name": "Foundation", "surviving_claims": 5},
    2: {"name": "Argumentation", "surviving_claims": 15,
        "validation": "founder_panel"},
    3: {"name": "Depth", "surviving_claims": 30,
        "requires": "active_city"},
    4: {"name": "Application", "surviving_claims": 50,
        "requires": "active_town"},
    5: {"name": "Influence", "surviving_claims": 75,
        "requires": "10_cross_domain_citations_received"},
}

TIER_NAMES = {tier: info["name"] for tier, info in V2_TIERS.items()}

# ═══════════════════════════════════════
# MOCK CONFIG (for testing)
# ═══════════════════════════════════════
MOCK_CONFIG = {
    "founding_era_target_pairs": 3,        # 6 States
    "phase0_research_cycles": 3,           # Founder research cycles
    "founding_era_max_cycles": 10,         # Max cycles to form pairs
    "governance_cycles": 5,                # Phase 2 cycles (0 = indefinite)
    "initial_token_budget": 30000,         # Per State
    "cycle_cost": 2000,                    # Per cycle per State
    "federal_lab_activation_cycle": 5,     # When Federal Lab starts
    "federal_lab_min_claims": 10,          # Or when this many surviving claims
    "abstraction_pass_interval": 5,        # Every N cycles
    "abstraction_max_claims_per_domain": 20,
    "chain_collapse_max_depth": 10,        # BFS recursion limit
}

# ═══════════════════════════════════════
# PRODUCTION CONFIG
# ═══════════════════════════════════════
PRODUCTION_CONFIG = {
    "founding_era_target_pairs": 3,        # TEMP: 3 for testing (restore to 10)
    "phase0_research_cycles": 1,
    "founding_era_max_cycles": 5,
    "governance_cycles": 3,                # TEMP: 3 for testing (restore to 0 for indefinite)
    "initial_token_budget": 50000,
    "cycle_cost": 3000,
    "federal_lab_activation_cycle": 5,
    "federal_lab_min_claims": 10,
    "abstraction_pass_interval": 5,
    "abstraction_max_claims_per_domain": 20,
    "chain_collapse_max_depth": 10,
}

# ═══════════════════════════════════════
# MODEL ALLOCATION
# ═══════════════════════════════════════
JUDGE_MODEL = "claude"  # Future: "gpt", "gemini", "multi"

MODEL_ALLOCATION = {
    # Haiku: structured extraction, pattern matching, content, free-form research (cheap + fast)
    "founder_research": "haiku",
    "founder_vote": "haiku",
    "normalization": "haiku",
    "premise_decomposition": "haiku",
    "rebuttal_newness": "haiku",
    "anti_loop": "haiku",
    "reclassification": "haiku",
    "bridge_extraction": "haiku",
    "content_generation": "haiku",
    # Sonnet: core reasoning (claims, challenges, rebuttals)
    "researcher_claims": "sonnet",
    "critic_challenges": "sonnet",
    "researcher_rebuttals": "sonnet",
    "court_judges": "sonnet",
    "founder_panels": "sonnet",
    "federal_lab": "sonnet",
    "executive_election": "sonnet",
    # Sonnet/Opus: judge is the quality gate — use strongest available
    "judge": "sonnet",
}

MODEL_IDS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-5-20250929",
    "opus": "claude-opus-4-6",
}

# ═══════════════════════════════════════
# TOKEN ECONOMY
# ═══════════════════════════════════════
TOKEN_VALUES = {
    "foundation_survived": 2000,
    "foundation_partial": 1200,
    "discovery_survived": 1000,
    "discovery_first_cited": 3000,       # Permanent — not clawed back if citing claim overturned
    "discovery_partial": 600,
    "challenge_succeeded": 4000,
    "challenge_failed": -1000,            # Clamped to 0 floor
    "retracted": 500,
    "destroyed": 0,
    "rival_destroyed_by_critic": 1000,
    "rival_narrowed_by_critic": 800,
    "city_published": 1000,
    "city_cited_by_town": 1500,
    "city_cross_domain": 2000,
    "town_published": 500,
    "town_human_accepted": 5000,         # FUTURE — requires human review interface
    "town_cross_domain": 3000,
    "tier_advancement": 10000,
    "cross_domain_citation": 1500,
    "domain_milestone": 2000,            # Awarded to WEAKER rival at 25/50/100 surviving
}

# ═══════════════════════════════════════
# GOVERNANCE RULES
# ═══════════════════════════════════════
SENATE_MIN_QUORUM = 3               # Senate suspended if fewer than 3 active States
SENATE_PAIR_SUPERMAJORITY = 0.60    # 60% to form a rival pair
SENATE_SIMPLE_MAJORITY = 0.51       # For dissolution votes
COURT_OVERTURN_THRESHOLD = 3        # Unanimous (3/3) to overturn; 2-1 upholds status quo

WARMUP_CYCLES = 3                   # Cycles both States skip cross-challenge after replacement
PROBATION_TRIGGER = 3               # Consecutive cycles with 0 surviving/partial → probation
DISSOLUTION_TRIGGER = 5             # Budget=0 AND this many consecutive probation cycles

# Retracted (proactive) does NOT reset probation
# Retracted (Option C under fire) DOES count toward probation
PROBATION_RESET_OUTCOMES = ["survived", "partial"]
OPTION_C_UNDER_FIRE_COUNTS_PROBATION = True

APPEAL_COST_TOKENS = 2000           # Deducted from State budget



# ═══════════════════════════════════════
# EXECUTIVE ELECTIONS
# ═══════════════════════════════════════
EXECUTIVE_ELECTION_INTERVAL = 10
EXECUTIVE_TERM_CYCLES = 10
EXECUTIVE_PLATFORM_ADJUSTABLE_KEYS = [
    "cycle_cost",
    "token_values",
    "tier_thresholds",
]

# ═══════════════════════════════════════
# SCORING RUBRIC (included in judge prompt)
# ═══════════════════════════════════════
SCORING_RUBRIC = """
Drama (1-10):
  1-3: Routine exchange, no real tension
  4-6: Genuine disagreement, outcome uncertain mid-read
  7-8: Claim nearly destroyed or barely survived
  9-10: Paradigm confrontation, system-wide implications

Novelty (1-10):
  1-3: Incremental extension of existing knowledge
  4-6: New angle on known territory
  7-8: Genuinely new ground, no prior claims in area
  9-10: Cross-domain breakthrough or fundamental challenge

Depth (1-10):
  1-3: Surface reasoning, 2 steps, obvious conclusions
  4-6: Solid chain, 3-4 steps, some implicit work
  7-8: Deep reasoning, 5+ steps, hidden assumptions exposed
  9-10: Multi-layered argument with recursive dependencies
"""

# ═══════════════════════════════════════
# REASONING DEPTH MINIMUMS BY TIER
# ═══════════════════════════════════════
REASONING_DEPTH_BY_TIER = {
    0: 2, 1: 2,   # Tier 0-1: 2 steps minimum
    2: 3,          # Tier 2: 3 steps
    3: 4,          # Tier 3: 4 steps
    4: 5, 5: 5,   # Tier 4+: 5 steps
}

# ═══════════════════════════════════════
# CONTENT SELECTION THRESHOLDS
# ═══════════════════════════════════════
CONTENT_THRESHOLDS = {
    "all_four": {"drama_min": 8, "depth_min": 7},
    "newsroom_debate": {"drama_min": 7, "novelty_min": 8},   # drama OR novelty
    "blog": {"drama_min": 5, "event_types": ["tier_advancement", "destroyed"]},
    "explorer": {"event_types": ["new_state", "new_city", "new_town", "milestone", "ruins"]},
    "dissolution": "all_four_drama_10",    # ALL FOUR, drama=10 automatic
}

# ═══════════════════════════════════════
# V1 DATA DETECTION
# ═══════════════════════════════════════
V1_DATA_PATHS = [
    "atlantis_mock/",
    "atlantis_data/",
    "test_dir/",
    "test_debug/",
    "phase_cache.json",
    "phase2_cache.json",
    "founding_era_checkpoint.json",
]

# ═══════════════════════════════════════
# OUTPUT DIRECTORY STRUCTURE
# ═══════════════════════════════════════
OUTPUT_DIRS = [
    "output/content/blog",
    "output/content/newsroom",
    "output/content/debate",
    "output/content/explorer",
    "output/logs",
]

OUTPUT_FILES = {
    "archive_md": "output/archive.md",
    "archive_json": "output/archive.json",
    "domain_health": "output/domain_health.json",
    "blog_context": "output/content/blog_context.json",
    "database": "output/atlantis.db",
}

# ═══════════════════════════════════════
# THE 20 FOUNDERS — Groups and Debate Matchups
# ═══════════════════════════════════════
FOUNDER_GROUPS = {
    "governance_core": [
        "Hamilton", "Jefferson", "Franklin", "Madison",
        "Marshall", "Washington", "Paine", "Tyler"
    ],
    "knowledge_champions": [
        "Darwin", "Curie", "Turing", "Aristotle",
        "Hippocrates", "Da Vinci", "Brunel", "Olympia",
        "Smith", "Herodotus", "Euclid", "Carson"
    ]
}

DEBATE_MATCHUPS = {
    "Hamilton":    {"allies": ["Madison", "Olympia"],    "opponents": ["Jefferson", "Carson"]},
    "Jefferson":   {"allies": ["Paine", "Aristotle"],    "opponents": ["Hamilton", "Washington"]},
    "Franklin":    {"allies": ["Curie", "Euclid"],       "opponents": ["Da Vinci", "Darwin"]},
    "Madison":     {"allies": ["Marshall", "Hamilton"],  "opponents": ["Jefferson", "Paine"]},
    "Marshall":    {"allies": ["Washington", "Madison"], "opponents": ["Jefferson", "Paine"]},
    "Washington":  {"allies": ["Hippocrates", "Brunel"], "opponents": ["Darwin", "Smith"]},
    "Paine":       {"allies": ["Jefferson", "Herodotus"],"opponents": ["Washington", "Hamilton"]},
    "Tyler":       {"allies": ["Turing", "Brunel"],      "opponents": ["Aristotle", "Jefferson"]},
    "Darwin":      {"allies": ["Carson", "Hippocrates"], "opponents": ["Euclid", "Washington"]},
    "Curie":       {"allies": ["Franklin", "Turing"],    "opponents": ["Aristotle", "Da Vinci"]},
    "Turing":      {"allies": ["Euclid", "Hamilton"],    "opponents": ["Aristotle", "Herodotus"]},
    "Aristotle":   {"allies": ["Herodotus", "Franklin"], "opponents": ["Turing", "Smith"]},
    "Hippocrates": {"allies": ["Washington", "Carson"],  "opponents": ["Smith", "Hamilton"]},
    "Da Vinci":    {"allies": ["Brunel", "Olympia"],     "opponents": ["Euclid", "Franklin"]},
    "Brunel":      {"allies": ["Hamilton", "Tyler"],     "opponents": ["Carson", "Jefferson"]},
    "Olympia":     {"allies": ["Smith", "Hamilton"],     "opponents": ["Aristotle", "Herodotus"]},
    "Smith":       {"allies": ["Hamilton", "Olympia"],   "opponents": ["Carson", "Jefferson"]},
    "Herodotus":   {"allies": ["Aristotle", "Paine"],    "opponents": ["Turing", "Hamilton"]},
    "Euclid":      {"allies": ["Turing", "Franklin"],    "opponents": ["Da Vinci", "Paine"]},
    "Carson":      {"allies": ["Darwin", "Hippocrates"], "opponents": ["Smith", "Hamilton"]},
}

# ═══════════════════════════════════════
# API CONFIGURATION
# ═══════════════════════════════════════
API_CONFIG = {
    "rate_limit_seconds": 0.1,
    "rate_limit_enabled": True,
    "temperature_research": 0.7,
    "temperature_judge": 0.2,        # Lower temp for consistent judging
    "temperature_content": 0.8,      # Higher temp for creative content
    "temperature_extraction": 0.0,   # Zero temp for structured extraction (Haiku calls)
}
