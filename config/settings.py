"""
Project Atlantis — System Configuration
========================================
System-wide settings, hard constraints, depth tier definitions,
and resource limits. These are the pre-constitutional parameters
that exist before the Founders even convene.

THIS IS NOT CROSSREF. No UPCs. No product codes. This is a
civilization engine with checks and balances to prevent loops.
"""

# ═══════════════════════════════════════
# SYSTEM IDENTITY
# ═══════════════════════════════════════
SYSTEM_NAME = "ATLANTIS"
VERSION = "1.0.0"
DESCRIPTION = "The Lost Civilization, Rebuilt — A Self-Governing AI Civilization of Knowledge"

# ═══════════════════════════════════════
# DEPTH TIER DEFINITIONS
# ═══════════════════════════════════════
DEPTH_TIERS = {
    0: {
        "name": "Empty",
        "description": "No knowledge in this domain.",
        "requirements": [],
        "min_concepts": 0,
        "min_frameworks": 0,
        "min_applications": 0,
    },
    1: {
        "name": "Vocabulary",
        "description": "Knows the terminology, key concepts, major figures, and foundational principles.",
        "requirements": [
            "Can define 10+ key terms in the domain",
            "Can name major figures and their contributions",
            "Can describe foundational principles",
            "Can explain what the domain is about to a non-expert"
        ],
        "min_concepts": 10,
        "min_frameworks": 0,
        "min_applications": 0,
    },
    2: {
        "name": "Frameworks",
        "description": "Understands the major models, methodologies, and debates used in the domain.",
        "requirements": [
            "Can describe 3+ major frameworks or models",
            "Can explain the key debates and disagreements in the field",
            "Can compare different methodological approaches",
            "Understands when each framework applies and its limitations"
        ],
        "min_concepts": 25,
        "min_frameworks": 3,
        "min_applications": 0,
    },
    3: {
        "name": "Application",
        "description": "Can apply knowledge to real scenarios and produce useful analysis.",
        "requirements": [
            "Can analyze a specific real-world scenario using domain knowledge",
            "Can identify problems and propose evidence-based solutions",
            "Can produce analysis that a domain expert would find useful",
            "Can explain reasoning and cite evidence for conclusions"
        ],
        "min_concepts": 50,
        "min_frameworks": 5,
        "min_applications": 3,
    },
    4: {
        "name": "Cross-Domain Synthesis",
        "description": "Can combine knowledge with other domains for emergent insights.",
        "requirements": [
            "Can identify meaningful connections to 2+ other domains",
            "Can produce insights that require knowledge from multiple fields",
            "Can evaluate how developments in one domain affect another",
            "Collaborates effectively with other States/domains"
        ],
        "min_concepts": 100,
        "min_frameworks": 8,
        "min_applications": 10,
    },
    5: {
        "name": "Novel Insight",
        "description": "Can produce original analysis and frameworks not found in training data.",
        "requirements": [
            "Can generate original hypotheses or frameworks",
            "Can identify gaps in existing knowledge that others miss",
            "Can produce analysis that extends beyond existing literature",
            "Can challenge established assumptions with evidence"
        ],
        "min_concepts": 200,
        "min_frameworks": 12,
        "min_applications": 25,
    }
}

TIER_NAMES = {tier: info["name"] for tier, info in DEPTH_TIERS.items()}

# ═══════════════════════════════════════
# HARD CONSTRAINTS (Pre-Constitutional)
# ═══════════════════════════════════════
# These exist BEFORE the Founders write the constitution.
# They are the parameters of the simulation itself.
# The Founders cannot override these.

HARD_CONSTRAINTS = {
    # Growth limits
    "max_states": 50,  # Hard cap — prevents spawn explosion
    "max_cities_per_state": 15,
    "max_towns_per_city": 10,
    "max_depth_levels": 3,            # State → City → Town (no deeper)
    "max_agents_per_entity": 8,

    # Founding Era — Founders stay to form initial States
    "founding_era_target_states": 20,  # Founders form 20 States then retire

    # Growth rate limits (prevents runaway expansion in autonomous phase)
    "max_new_states_per_100_cycles": 3,
    "max_new_cities_per_50_cycles": 5,
    "min_cycles_before_first_state": 1,

    # Resource limits
    "max_tokens_per_cycle": 100_000,
    "max_tokens_per_agent_per_cycle": 15_000,
    "token_warning_threshold": 0.8,

    # Constitutional limits
    "min_constitutional_articles": 5,
    "max_constitutional_articles": 30,
    "amendment_cooldown_cycles": 25,
    "supermajority_threshold": 0.70,    # 70% for constitutional changes (14/20)
    "simple_majority_threshold": 0.51,

    # Safety — loop prevention
    "max_consecutive_failures": 5,
    "max_amendment_rate": 3,            # Max 3 amendments per 100 cycles
    "founder_retirement_mandatory": True,
    "max_debate_rounds_per_article": 1, # Single round of 2v2, then vote
}

# ═══════════════════════════════════════
# FOUNDING PERIOD CONFIGURATION
# ═══════════════════════════════════════
FOUNDING_CONFIG = {
    # Research — 10 cycles for deep knowledge before Convention
    "research_cycles": 10,
    "min_founder_depth": 2,           # Must reach Tier 2 before Convention

    # Convention — 2v2 adversarial debate format
    "num_founders": 20,
    "convention_rounds": 3,            # 3 rounds of proposals
    "debate_format": "2v2",            # 2 supporters vs 2 opponents
    "num_supporters": 2,
    "num_opponents": 2,
    "ratification_threshold": 14,      # 14/20 must approve (70%)
    "convention_max_articles": 30,

    # Retirement
    "founder_retirement_delay": 0,
}

# ═══════════════════════════════════════
# THE 20 FOUNDERS — Role Assignments
# ═══════════════════════════════════════
# Governance Core (Gold): Hamilton, Jefferson, Franklin, Madison,
#                         Marshall, Washington, Paine, Tyler
# Knowledge Champions (Teal): Darwin, Curie, Turing, Aristotle,
#                              Hippocrates, Da Vinci, Brunel, Olympia,
#                              Smith, Herodotus, Euclid, Carson

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

# ═══════════════════════════════════════
# DEBATE MATCHMAKING
# ═══════════════════════════════════════
# For 2v2 debates, we need to assign supporters and opponents
# who have genuine domain overlap / philosophical tension.
# This maps each proposer to likely allies and opponents.

DEBATE_MATCHUPS = {
    # Governance Core proposals
    "Hamilton":    {"allies": ["Madison", "Olympia"], "opponents": ["Jefferson", "Carson"]},
    "Jefferson":   {"allies": ["Paine", "Aristotle"], "opponents": ["Hamilton", "Washington"]},
    "Franklin":    {"allies": ["Curie", "Euclid"], "opponents": ["Da Vinci", "Darwin"]},
    "Madison":     {"allies": ["Marshall", "Hamilton"], "opponents": ["Jefferson", "Paine"]},
    "Marshall":    {"allies": ["Washington", "Madison"], "opponents": ["Jefferson", "Paine"]},
    "Washington":  {"allies": ["Hippocrates", "Brunel"], "opponents": ["Darwin", "Smith"]},
    "Paine":       {"allies": ["Jefferson", "Herodotus"], "opponents": ["Washington", "Hamilton"]},
    "Tyler":       {"allies": ["Turing", "Brunel"], "opponents": ["Aristotle", "Jefferson"]},

    # Knowledge Champion proposals
    "Darwin":      {"allies": ["Carson", "Hippocrates"], "opponents": ["Euclid", "Washington"]},
    "Curie":       {"allies": ["Franklin", "Turing"], "opponents": ["Aristotle", "Da Vinci"]},
    "Turing":      {"allies": ["Euclid", "Hamilton"], "opponents": ["Aristotle", "Herodotus"]},
    "Aristotle":   {"allies": ["Herodotus", "Franklin"], "opponents": ["Turing", "Smith"]},
    "Hippocrates": {"allies": ["Washington", "Carson"], "opponents": ["Smith", "Hamilton"]},
    "Da Vinci":    {"allies": ["Brunel", "Olympia"], "opponents": ["Euclid", "Franklin"]},
    "Brunel":      {"allies": ["Hamilton", "Tyler"], "opponents": ["Carson", "Jefferson"]},
    "Olympia":     {"allies": ["Smith", "Hamilton"], "opponents": ["Aristotle", "Herodotus"]},
    "Smith":       {"allies": ["Hamilton", "Olympia"], "opponents": ["Carson", "Jefferson"]},
    "Herodotus":   {"allies": ["Aristotle", "Paine"], "opponents": ["Turing", "Hamilton"]},
    "Euclid":      {"allies": ["Turing", "Franklin"], "opponents": ["Da Vinci", "Paine"]},
    "Carson":      {"allies": ["Darwin", "Hippocrates"], "opponents": ["Smith", "Hamilton"]},
}

# ═══════════════════════════════════════
# GOVERNMENT CONFIGURATION
# ═══════════════════════════════════════
GOVERNMENT_ROLES = {
    "senate": {
        "permanent_seats": [
            {"id": "senator_critic", "name": "Critic", "mandate": "judicial_oversight"},
            {"id": "senator_tester", "name": "Tester", "mandate": "evidence_verification"},
            {"id": "senator_historian", "name": "Historian", "mandate": "institutional_memory"},
            {"id": "senator_debugger", "name": "Debugger", "mandate": "system_integrity"},
        ],
        "state_seats": True,  # 1 per State, added dynamically
    },
    "house": {
        "members": [
            {"id": "house_architect", "name": "Architect", "mandate": "implementation_design"},
            {"id": "house_coder", "name": "Coder", "mandate": "implementation_execution"},
        ]
    },
    "supreme_court": {
        "justices": [
            {"id": "justice_warden", "name": "WARDEN", "mandate": "constitutional_authority", "role": "Chief Justice"},
            {"id": "justice_critic", "name": "Critic", "mandate": "quality_analysis", "role": "Associate Justice"},
            {"id": "justice_historian", "name": "Historian", "mandate": "precedent_context", "role": "Associate Justice"},
        ]
    }
}

# ═══════════════════════════════════════
# CONTENT PIPELINE CONFIGURATION
# ═══════════════════════════════════════
CONTENT_CONFIG = {
    "enable_blog": True,
    "enable_tiktok": True,
    "enable_dashboard": True,

    # TikTok settings
    "tiktok_min_drama_score": 6,
    "tiktok_max_duration_seconds": 90,
    "tiktok_auto_generate": True,      # Generate scripts immediately

    # Blog settings
    "blog_min_level": "significant",
    "blog_max_words": 1500,
    "blog_short_max_words": 400,
    "blog_auto_generate": True,        # Generate posts immediately

    # Cycle summary frequency
    "cycle_summary_frequency": 10,
}

# ═══════════════════════════════════════
# KNOWLEDGE STORE CONFIGURATION
# ═══════════════════════════════════════
KNOWLEDGE_CONFIG = {
    "store_type": "local",
    "max_entries_per_entity": 10_000,
    "deduplication_threshold": 0.95,
    "cross_state_read_access": True,
    "cross_state_write_access": False,
    "append_only": True,
}

# ═══════════════════════════════════════
# API CONFIGURATION
# ═══════════════════════════════════════
API_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1000,
    "temperature": 0.7,
    "founder_temperature": 0.8,
    "government_temperature": 0.6,

    # Rate limiting — 0.5 second minimum between API calls
    "rate_limit_seconds": 0.5,
    "rate_limit_enabled": True,
}
