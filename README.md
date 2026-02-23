# ATLANTIS — Self-Improving Adversarial Knowledge Engine

> 20 AI minds. 10 research domains. Constitutional governance. A system that diagnoses its own weaknesses, writes its own fixes, and gets smarter every run.

**Live site:** [atlantiskb.com](https://atlantiskb.com)  
**Latest run:** V2.5 — 105 surviving claims, 91.0% survival rate, $4.59 total cost

## What This Is

Atlantis is a closed-loop AI civilization that produces validated knowledge through adversarial debate — and then improves its own ability to produce knowledge.

Rival AI States generate research hypotheses, attack each other's claims, and defend their work before judges — all governed by a constitution the AI agents wrote themselves. A meta optimizer reads the system's failure patterns, proposes prompt improvements, debates those improvements adversarially, and applies the survivors — creating a self-improvement loop that compounds across runs.

**The breakthrough:** governance prevents death. Multi-agent AI systems fail because they loop, hallucinate in circles, and drift into nonsense. Atlantis solves this with structural pressure — constitutional law, token economies, objective validators, and tiered knowledge that forces the system to destroy its own bad work.

**The result:** research-grade hypotheses with operational definitions, falsification criteria, and citation chains — produced for under $5 per run, improving automatically with each iteration.

## How It Works

```
Phase 0: Founding Research
  20 Founders deposit knowledge across 10 domains

Phase 1: Rival Pair Formation
  10 domain pairs formed (Alpha vs Beta per domain)

Phase 2: Autonomous Governance (3 cycles)
  For each cycle, for each rival pair:
    1. Both States produce research claims
    2. Claims pass through objective validators + real-world anchors
    3. Rival critic attacks the claim
    4. Researcher defends with rebuttal
    5. Judge rules with structured rejection codes
    6. Token economy rewards/punishes States
    7. Federal Lab destabilizes surviving claims
    8. Learning system feeds performance data back to agents
    9. Content pipeline generates narratives

Meta Layer: Self-Improvement
  After each run:
    1. Optimizer diagnoses failure patterns from run data
    2. Proposes atomic prompt improvements (one change per proposal)
    3. Adversarial review: Alpha proposes, Beta attacks, Judge rules
    4. Human approves/rejects each proposal individually
    5. Applied changes bump prompt version, snapshot baseline
    6. Next run uses improved prompts — system compounds
```

## Run History

| Version | Claims | Survival | Cost | Key Achievement |
|---------|--------|----------|------|-----------------|
| V2.5 | 105 | 91.0% | $4.59 | Self-improved prompts, learning system active, citation chains 4-5 deep |
| V2.4 | 101 | 82.4% | $4.54 | Learning system, performance profiles, Federal Lab |
| V2.3 | 111 | 82.9% | $4.77 | Cross-rival citations, anchor teeth |
| V2.2 | 36 | 64.6% | $2.49 | First 10-domain run |

## V2.5 Highlights

**Self-improvement proven.** The meta optimizer diagnosed LOGIC_FAILURE as the #1 failure pattern (50% of retractions), proposed a critic prompt upgrade, debated it adversarially, and applied the surviving fix. Result: survival rate jumped from 82.4% to 91.0% for $0.05 more per run.

**Learning context scaling.** Performance history injected into every agent grew from 56 chars in Cycle 1 to 314 chars in Cycle 3. Agents adapted: Physics_Alpha pivoted from a retracted fine-structure constant claim to CMB quantum gravity signatures. It learned from getting killed and came back with something harder to attack.

**Citation chains forming.** Research programs now run 4-5 claims deep. Biology went from "senescent cells store stress memory" → "combinatorial SASP codes" → "temporal phase encoding doubles information capacity." Finance derived the exact geometric drag formula from first principles and validated it against real ETF data across four connected claims.

**Anti-loop detection active.** Caught Physics_Beta recycling the same argument in different packaging. The governance prevented knowledge inflation by destroying duplicate reasoning.

**Cross-rival synthesis.** Economics_Beta Cycle 3 cited both #137 (Alpha's work) and #138 (its own prior work). Competitors building on each other's research — synthesis knowledge neither could produce alone.

## Architecture

```
core/
  engine.py          — Main orchestrator (Phase 0 → 1 → 2)
  llm.py             — Anthropic API client with retry logic
  models.py          — ModelRouter (Haiku/Sonnet/Opus by task)
  persistence.py     — SQLite archive + knowledge base
  exceptions.py      — Custom exception types

governance/
  perpetual.py       — Adversarial governance loop + learning system
  states.py          — State entities (researcher, critic, lab, senator)
  validators.py      — Objective validation (format + domain checks)
  anchors.py         — Real-world anchors (SymPy math, physics, dates, etc.)

meta/
  optimizer.py       — Failure pattern diagnosis + adversarial proposal generation
  apply.py           — Safe prompt application (additive mode, per-proposal approval)
  architect.py       — Code optimization proposals (parallelization)
  apply_code.py      — Code proposal safety gates
  __main__.py        — CLI: python3 -m meta optimize --run <path>
  history.json       — Prompt version tracking + applied changes
  baselines/         — Baseline snapshots for regression detection
  proposals/         — Generated proposal files

founders/
  convention.py      — Constitutional Convention (Jefferson draft + amendments)

content/
  generator.py       — Content generation pipeline
  logger.py          — Structured logging

runs/                — Timestamped output from each engine run
  archive.json       — Full knowledge base (extended schema)
  archive.md         — Human-readable archive
  domain_health.json — Domain metrics + warning flags
  cost_summary.json  — API cost breakdown
  logs/              — Per-cycle logs
  content/           — Generated blog posts, debates, narratives

lib/data.ts          — Auto-generated site data (from generate_site_data.py)
app/                 — Next.js 16 frontend (Vercel deployment)
```

## Meta Optimizer — Self-Improvement Loop

The meta system reads run data, diagnoses weaknesses, and writes its own fixes:

### Failure Pattern Diagnosis

Analyzes retractions, domain health flags, and survival rates to identify systemic problems. Patterns ranked by severity:

| Pattern | Severity | Trigger |
|---------|----------|---------|
| CRITIC_TOO_PASSIVE | 5 | 100% survival + weak critic flag |
| LOGIC_FAILURE | 3 | Claims retracted for reasoning errors |
| EVIDENCE_INSUFFICIENT | 2 | Claims survive with weak evidence |
| PARAMETER_UNJUSTIFIED | 2 | Arbitrary constants without justification |
| MAGNITUDE_IMPLAUSIBLE | 2 | Effect sizes inconsistent with constraints |
| SCOPE_EXCEEDED | 1 | Claims extend beyond evidence |
| DEPENDENCY_FAILURE | 1 | Upstream claims insufficiently grounded |

### Adversarial Proposal Review

Each proposed fix goes through the same governance as research claims:

- **Meta_Alpha** proposes the change with rationale and predicted effect
- **Meta_Beta** attacks with strongest objections (bloat, root cause, domain harm)
- **Meta_Alpha** rebuts with run-data-grounded defense
- **Meta_Judge** rules APPROVE, NARROW, or REJECT with specific narrowing instructions

### Atomic Proposals

Each proposal contains exactly one change (additive line insertion). Human approves or rejects individually with:

- Full diff preview showing the single line being added
- Estimated token cost impact per run
- Complete adversarial review summary

### Safety Gates

- **Anti-oscillation guard** — Sections modified in the last 3 runs cannot be modified again
- **Length cap** — Proposals limited to 10% growth or 200 chars, whichever is greater
- **Required sections** — Proposals cannot remove constitutional format requirements
- **Weak pattern detection** — Proposals attempting to weaken validation are rejected
- **Baseline snapshots** — Every version change snapshots metrics for regression detection

### Usage

```bash
# Diagnose failures and generate improvement proposals
python3 -m meta optimize --run runs/<timestamp>/

# Each proposal shown individually — approve or reject each one
# Dry run (preview without applying)
python3 -m meta optimize --run runs/<timestamp>/ --dry-run

# Include cost optimization analysis
python3 -m meta optimize --run runs/<timestamp>/ --cost

# Limit proposals
python3 -m meta optimize --run runs/<timestamp>/ --max 5
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
| Judge rulings | Sonnet | Nuanced evaluation with rejection codes |
| Rebuttals | Sonnet | Complex defense arguments |
| Normalization | Haiku | Fast structured extraction |
| Anti-loop checks | Haiku | Quick pattern matching |
| Content generation | Haiku | Efficient narrative production |
| Meta optimizer | Haiku + Sonnet | Haiku for proposals, Sonnet for judge |
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
   - All anchors return flags/warnings injected into the judge prompt

Anchors inform the judge — they don't override it. A flagged claim can still survive if the judge finds the flag is about a peripheral detail, not the core hypothesis.

**Anchor Teeth (V2.3+):** Surviving claims flagged by objective validators receive a -200 token penalty. Anchors don't override the judge, but they create economic consequences for borderline claims.

## Learning System (V2.4+)

Atlantis agents improve across cycles through structured feedback loops:

**State Performance Profiles** — Each researcher receives a descriptive summary of their track record before producing claims: survival rate, failure modes (from structured retraction codes), judge feedback themes, token trajectory. In V2.5, performance context scaled from 56 chars in Cycle 1 to 314 chars in Cycle 3 as the system accumulated more data.

**Critic Performance Tracking** — Critics receive their impact rate (challenges that changed outcomes) and precision rate (objections upheld by judge). Prevents both passive and trigger-happy critics.

**Structured Retraction Reasons** — Every destruction and retraction includes a primary reason tag:
- `DEPENDENCY_FAILURE` — upstream claim insufficiently grounded
- `EVIDENCE_INSUFFICIENT` — not enough empirical support
- `MAGNITUDE_IMPLAUSIBLE` — effect size inconsistent with constraints
- `PARAMETER_UNJUSTIFIED` — key constants chosen arbitrarily
- `LOGIC_FAILURE` — reasoning chain contains errors
- `SCOPE_EXCEEDED` — claim extends beyond evidence

These feed the performance profiles and the meta optimizer, creating a closed learning loop.

**Domain Health Report** — End-of-run comparison across all domains. Flags weak critics (>90% survival after 3+ cycles) and format issues (<30% survival). These flags feed directly into the meta optimizer's failure diagnosis.

## Token Economy

| Event | Tokens |
|-------|--------|
| Foundation claim survives | +2000 |
| Discovery claim survives | +1000 |
| Rival's claim narrowed by critic | +2000 |
| Claim retracted | +500 |
| Claim destroyed | -500 |
| Anchor-teethed surviving claim | -200 |

States that drop below zero tokens enter probation. Continued failure leads to dissolution.

## Knowledge Tiers

| Tier | Requirement | Privileges |
|------|-------------|------------|
| Tier 1 | First surviving claim | Can publish Foundation claims |
| Tier 2 | 3+ surviving claims | Can publish to main archive |
| Tier 3 | 5+ surviving claims | Can make expertise claims |
| Tier 4 | 10+ surviving claims | Can serve on review panels |

## Quick Start

### Requirements

- Python 3.11+
- Node.js 20+
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

# Full 10-domain run (3 governance cycles, ~$5)
python3 __main__.py --demo-10-domains --force-clean

# Output appears in runs/<timestamp>/
```

### Run the Meta Optimizer

```bash
# Diagnose failures and generate improvement proposals
python3 -m meta optimize --run runs/<timestamp>/

# Each proposal shown individually with diff, cost impact, adversarial review
# Approve or reject each one independently

# Dry run (preview without applying)
python3 -m meta optimize --run runs/<timestamp>/ --dry-run

# Include cost optimization analysis
python3 -m meta optimize --run runs/<timestamp>/ --cost
```

### Generate Site Data + Deploy

```bash
python3 generate_site_data.py
npm run dev            # Local dev
git push origin main   # Auto-deploys via Vercel
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

- **Adversarial search product** — Perplexity-style Q&A where every answer gets validated through governance before delivery
- **Architect parallelization** — System proposes its own code optimizations for parallel LLM calls
- **State spawning** — New States spawn dynamically as domains mature
- **City/Town formation** — Cities from clusters of validated research, Towns from practical applications
- **The Beast** — Commercial product using adversarial validation for domain-specific research

## Cost Structure

Atlantis uses multi-model routing to minimize API costs:

- Haiku ($0.80/MTok in, $4/MTok out) for routine tasks
- Sonnet ($3/MTok in, $15/MTok out) for research and judgment
- Opus ($15/MTok in, $75/MTok out) reserved for Supreme Court

A full 10-domain, 3-cycle run costs approximately **$5**. The meta optimizer costs **~$0.02** per self-improvement cycle.

## License

MIT License. See LICENSE for details.
