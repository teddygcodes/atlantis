# Architecture Overview

## Three-Phase System

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────────┐
│   PHASE 0   │  →   │   PHASE 1    │  →   │      PHASE 2        │
│   Founder   │      │   Founding   │      │   Autonomous        │
│   Research  │      │     Era      │      │   Governance        │
└─────────────┘      └──────────────┘      └─────────────────────┘
      1 cycle              Instant               Indefinite

 20 Founders          Direct rival pair         Perpetual rival
 research freely      formation (demo mode)     challenge cycles
```

### Phase 0: Founder Research
- 20 Founders (Madison, Hamilton, Jefferson, etc.) each research their expertise domains
- Free-form deposits to archive (no validation pressure)
- Builds foundational knowledge corpus
- Profiles stored for later Tier 2/3 validation panels
- **Output:** 20 founding entries, 20 stored profiles

### Phase 1: Founding Era
- Demo mode forms rival pairs directly (no multi-cycle Senate voting)
- Target: 10 domain pairs formed (20 rival States total)
- Each State: Researcher + Critic + Senator + Lab agents
- Initial token budget: 50,000 per State
- **Output:** 10 active rival pairs, each locked in permanent adversarial relationship

### Phase 2: Autonomous Governance
- **Each cycle:**
  1. Both States produce claims (Researcher agent)
  2. Structural validation (format, citations, depth)
  3. Objective validation (anchors check facts)
  4. Cross-challenge (Critics attack rival claims)
  5. Rebuttals (Researchers defend or concede)
  6. Judge rulings (Sonnet evaluates exchanges)
  7. Archive deposit (full text preserved)
  8. Token outcomes applied
  9. End-of-cycle operations (Cities, abstraction, probation)

- Continues indefinitely (or until `governance_cycles` limit in config)

## Single Governance Cycle (Steps 1-19)

```
┌────────────────────────────────────────────────────────────┐
│ For each rival pair:                                       │
│                                                             │
│  1-2.  Both States produce claims (Researcher)             │
│  3.    Structural validation (format, citations)           │
│  4.    Anti-loop check (detect repetition)                 │
│  5.    Normalization (Haiku extracts fields)               │
│  6.    Premise decomposition (Haiku)                       │
│  7.    Reasoning depth enforcement (tier-scaled)           │
│  7.5.  Objective validation (anchors)                      │
│  8-9.  Cross-challenge (A attacks B, B attacks A)          │
│  10.   Validate challenges (must target specific step)     │
│  11-12. Rebuttals (Option A/B/C)                           │
│  13.   Rebuttal newness check (Haiku)                      │
│  14.   Judge determines outcomes (Sonnet)                  │
│  15.   Deposit to Archive (full text, never truncated)     │
│  16.   Apply token outcomes                                │
│  17.   Update stability scores                             │
│                                                             │
│ After all pairs complete:                                  │
│                                                             │
│  18.   Federal Lab (challenges highest-impact claim)       │
│  19.   End-of-cycle operations:                            │
│        - City formation (5+ claims, 2+ shared citations)   │
│        - Town formation (3+ City analyses)                 │
│        - Abstraction pass (every 5 cycles)                 │
│        - Cross-domain bridges                              │
│        - Tier advancement                                  │
│        - Probation & dissolution checks                    │
│        - Cycle log export                                  │
└────────────────────────────────────────────────────────────┘
```

## File Structure

```
atlantis/
├── core/
│   ├── engine.py          # Phase 0 → 1 → 2 orchestrator
│   ├── llm.py             # LLM provider (rate limiting, caching)
│   ├── models.py          # Task-to-model router
│   └── persistence.py     # SQLite append-only archive
│
├── governance/
│   ├── states.py          # State class + claim pipeline
│   ├── perpetual.py       # Cycle engine (steps 1-19)
│   ├── validators.py      # Universal + domain validators
│   └── anchors.py         # 10 real-world anchor validators
│
├── founders/
│   └── convention.py      # Phase 0: Founder research deposits
│
├── agents/
│   └── base.py            # 20 Founder configs + agent factories
│
├── content/
│   └── generator.py       # 4-format content generation
│
├── config/
│   └── settings.py        # Model allocation, token values, tiers
│
├── runs/
│   └── <timestamp>/       # Each engine run preserved
│       ├── archive.json
│       ├── archive.md
│       ├── domain_health.json
│       └── logs/cycle_N.md
│
├── app/                   # Next.js frontend pages
├── components/            # React components
├── lib/data.ts            # Generated from archive.json
└── generate_site_data.py  # Archive → TypeScript pipeline
```

## Data Flow

```
Engine Run
    ↓
runs/<timestamp>/archive.json  (SQLite → JSON export)
    ↓
generate_site_data.py          (Parse + restructure)
    ↓
lib/data.ts                    (TypeScript data layer)
    ↓
Next.js pages                  (React components)
    ↓
Vercel deployment              (atlantiskb.com auto-updates)
```

## Key Principles

1. **Append-only archive** — Text never modified. Status can change.
2. **Full text preservation** — Claims never truncated (raw_claim_text stores everything).
3. **Adversarial validation** — Every surviving claim was attacked and defended.
4. **Constitutional constraints** — States can't change rules, only operate within them.
5. **Economic pressure** — Token budget enforces quality (States die if they produce garbage).
