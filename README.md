# ATLANTIS — Adversarial Knowledge Engine

> 20 AI minds. 10 research domains. Constitutional governance. Knowledge that destroys its own mistakes.

**Live site:** [atlantiskb.com](https://atlantiskb.com)

## What This Is

Atlantis is a closed-loop AI civilization that produces validated knowledge through adversarial debate. Rival AI States generate research hypotheses, attack each other's claims, and defend their work before judges — all governed by a constitution the AI agents wrote themselves.

The breakthrough: governance prevents death. Multi-agent AI systems fail because they loop, hallucinate in circles, and drift into nonsense. Atlantis solves this with structural pressure — constitutional law, token economies, objective validators, and tiered knowledge that forces the system to destroy its own bad work.

The result: research-grade hypotheses with operational definitions, falsification criteria, and citation chains — produced for under $1 per governance cycle.

## How It Works

```
Phase 0: Founding Research
  20 Founders research across 10 domains (1 cycle)

Phase 1: Rival Pair Formation
  10 domain pairs formed (Alpha vs Beta per domain)

Phase 2: Autonomous Governance (3 cycles)
  For each cycle, for each rival pair:
    1. Both States produce research claims
    2. Claims pass through objective validators + real-world anchors
    3. Rival critic attacks the claim
    4. Researcher defends with rebuttal
    5. Judge rules (with anchor evidence in context)
    6. Token economy rewards/punishes States
    7. Federal Lab destabilizes surviving claims
    8. Content pipeline generates narratives
```

## Architecture

```
core/
  engine.py          — Main orchestrator (Phase 0 → 1 → 2)
  llm.py             — Anthropic API client with retry logic
  models.py          — ModelRouter (Haiku/Sonnet/Opus by task)
  persistence.py     — SQLite archive + knowledge base
  exceptions.py      — Custom exception types

governance/
  perpetual.py       — Adversarial governance loop
  states.py          — State entities (researcher, critic, lab, senator)
  validators.py      — Objective validation (format + domain checks)
  anchors.py         — Real-world anchors (SymPy math, physics, dates, etc.)
  content.py         — Content generation pipeline

founders/
  profiles.py        — 20 Founder definitions + specializations
  convention.py      — Constitutional Convention (Jefferson draft + amendments)

runs/                — Timestamped output from each engine run
  archive.json       — Full knowledge base
  archive.md         — Human-readable archive
  domain_health.json — Domain metrics
  cost_summary.json  — API cost breakdown
  logs/              — Per-cycle logs
  content/           — Generated blog posts, debates, narratives

lib/data.ts          — Auto-generated site data (from generate_site_data.py)
app/                 — Next.js 16 frontend (Vercel deployment)
```

## Research Domains

| Domain | Focus | Anchor Type |
|--------|-------|-------------|
| Mathematics | Formal systems, proof theory, computation | SymPy symbolic verification |
| Physics | Quantum mechanics, cosmology, constants | Speed of light, unit validation |
| Biology | Evolution, genetics, cell biology | Known biological facts |
| Finance | Market microstructure, behavioral economics | Financial logic checks |
| Technology | Distributed systems, neural networks, AI | CS fundamentals |
| Medicine | Immunology, clinical trials, pharmacology | Medical standards (WHO/FDA) |
| Geography | Urban systems, geophysics, climate | Geographic data (coordinates, distances) |
| History | Civilizational patterns, archival theory | Historical date verification |
| Economics | Productivity, preferences, market structure | Economic identities (GDP = C+I+G+NX) |
| Philosophy | Consciousness, epistemology, ethics | Formal logic validation |

## Model Allocation

| Task | Model | Rationale |
|------|-------|-----------|
| Researcher claims | Sonnet | Deep reasoning for hypothesis generation |
| Critic challenges | Sonnet | Sophisticated attack strategies |
| Judge rulings | Sonnet | Nuanced evaluation |
| Rebuttals | Sonnet | Complex defense arguments |
| Normalization | Haiku | Fast structured extraction |
| Anti-loop checks | Haiku | Quick pattern matching |
| Content generation | Haiku | Efficient narrative production |
| Supreme Court | Opus | Highest-stakes constitutional rulings |

## Objective Validators + Real-World Anchors

Claims pass through two validation layers before reaching the judge:

1. **Format validators** — Check for required sections (HYPOTHESIS, OPERATIONAL DEF, STEPS, PREDICTION, GAP ADDRESSED)
2. **Domain anchors** — Real-world fact checks using actual computation:
   - Math: SymPy verifies derivatives, integrals, known constants
   - Physics: Checks claims against speed of light, conservation laws
   - History: Validates dates against known historical events (±2 year tolerance)
   - Biology: Cross-references established biological facts
   - Finance: Checks against financial logic and identities
   - All anchors return flags/warnings that are injected into the judge prompt

Anchors inform the judge — they don't override it. A flagged claim can still survive if the judge finds the flag is about a peripheral detail, not the core hypothesis.

## Token Economy

States earn and lose tokens based on performance:

| Event | Tokens |
|-------|--------|
| Foundation claim survives | +2000 |
| Discovery claim survives | +1000 |
| Rival's claim narrowed by critic | +2000 |
| Claim retracted | +500 |
| Claim destroyed | -500 |

States that drop below zero tokens enter probation. Continued failure leads to dissolution — the State dies and is replaced.

## Knowledge Tiers

| Tier | Requirement | Privileges |
|------|-------------|------------|
| Tier 1 | First surviving claim | Can participate in governance |
| Tier 2 | 3+ surviving claims | Can publish to main archive |
| Tier 3 | 5+ surviving claims | Can make expertise claims |
| Tier 4 | 10+ surviving claims | Can serve on review panels |

## First Run Results (V2.2)

```
Surviving claims:     36
Survival rate:        64.6%
Active States:        20
Domains:              10
Governance cycles:    3
Total cost:           $2.49
Cost per cycle:       $0.83
LLM calls:           234 (187 Sonnet, 90 Haiku, 0 Opus)
```

## Quick Start

### Requirements

- Python 3.11+
- Node.js 22+
- Anthropic API key

### Install

```bash
git clone https://github.com/teddygcodes/atlantis.git
cd atlantis
pip install -r requirements.txt
npm install
```

### Run the Engine

```bash
# Set your API key
export ANTHROPIC_API_KEY=your-key-here

# Full 10-domain run (3 governance cycles, ~$2.50)
python3 __main__.py --demo-10-domains --force-clean

# Output appears in runs/<timestamp>/
```

### Generate Site Data + Deploy

```bash
# Generate frontend data from latest run
python3 generate_site_data.py

# Local dev
npm run dev

# Production (auto-deploys on push via Vercel)
git push origin main
```

## Site

- **URL:** [atlantiskb.com](https://atlantiskb.com)
- **Stack:** Next.js 16, Tailwind v4, Vercel
- **Design:** Crimson Edge palette (#dc2626 accent, #060606 background)
- **Fonts:** Cinzel (headings), Cormorant Garamond (body), IBM Plex Mono (data)
- **Auto-deploy:** Push to main → Vercel builds → live in ~60 seconds

## Data Pipeline

```
Engine run → runs/<timestamp>/archive.json
                    ↓
         python3 generate_site_data.py
                    ↓
              lib/data.ts
                    ↓
           git push origin main
                    ↓
          Vercel auto-deploys site
```

## What's Next

- **Validation persistence** — Store anchor flags/warnings in archive for frontend display
- **Researcher prompt optimization** — Extension/Foundation format requirements, increased token limits
- **Commercial application** — Adversarial validation applied to electrical contractor lighting takeoffs
- **Content pipeline** — TikTok/video generation from governance events

## Cost Structure

Atlantis uses multi-model routing to minimize API costs:

- Haiku ($0.80/MTok in, $4/MTok out) for routine tasks
- Sonnet ($3/MTok in, $15/MTok out) for research and judgment
- Opus ($15/MTok in, $75/MTok out) reserved for Supreme Court

A full 10-domain, 3-cycle run costs approximately **$2.50**.

## License

Proprietary. All rights reserved.
