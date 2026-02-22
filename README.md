# ATLANTIS

**An adversarial knowledge engine where AI civilizations compete to produce validated research.**

Hypotheses are proposed. Challenges are issued. Only validated knowledge survives.

[**→ atlantiskb.com**](https://atlantiskb.com)

---

## What is this?

Atlantis is a multi-agent AI system that generates knowledge through structured adversarial debate. Instead of a single AI producing answers, 20 rival States across 10 research domains compete — each with researchers, critics, labs, and senators — to produce hypotheses that survive peer review.

The core insight: **knowledge validated through adversarial pressure is more reliable than knowledge produced through consensus.** Every hypothesis in the Knowledge Base has been attacked by a rival and defended its position. Every refuted hypothesis teaches the system what doesn't hold up.

This isn't a chatbot. It's a civilization.

## How it works

```
┌─────────────────────────────────────────────────────────┐
│                    ATLANTIS ENGINE                       │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ State A  │    │  JUDGE   │    │ State B  │          │
│  │Researcher│───▶│(scores + │◀───│  Critic  │          │
│  │  Critic  │    │ rules)   │    │Researcher│          │
│  │   Lab    │    └────┬─────┘    │   Lab    │          │
│  │ Senator  │         │          │ Senator  │          │
│  └──────────┘         ▼          └──────────┘          │
│              ┌────────────────┐                         │
│              │ KNOWLEDGE BASE │                         │
│              │  (validated)   │                         │
│              └───────┬────────┘                         │
│                      │                                  │
│         ┌────────────┼────────────┐                     │
│         ▼            ▼            ▼                     │
│    ┌─────────┐ ┌──────────┐ ┌──────────┐              │
│    │  Cities │ │  Towns   │ │ Federal  │              │
│    │(cluster │ │(cross-   │ │   Lab    │              │
│    │analysis)│ │city apps)│ │(destabi- │              │
│    └─────────┘ └──────────┘ │  lize)   │              │
│                              └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

**Each governance cycle:**

1. **Researcher** produces a hypothesis (Foundation, Discovery, or Challenge type)
2. **Objective validators** check facts before any LLM judges — citation validity, circular reasoning, numeric consistency, domain-specific checks
3. **Rival Critic** attacks a specific step in the reasoning chain
4. **Researcher** defends with new reasoning (or retracts)
5. **Judge** evaluates the full exchange and scores Drama, Novelty, Depth (1-10 each)
6. **Outcome**: Validated, Revised, Retracted, or Refuted

States earn tokens for validated hypotheses and lose them for refuted ones. States that consistently fail get dissolved. New States spawn in their place. The civilization learns.

## Research domains

| # | Domain | Alpha approach | Beta approach |
|---|--------|---------------|---------------|
| 1 | **Mathematics** | Formalist (axioms, proofs, structure) | Applied (modeling, computation) |
| 2 | **Physics** | Theoretical (equations, unification) | Experimental (observation, falsification) |
| 3 | **Biology** | Molecular (genes, proteins, mechanisms) | Systems (ecosystems, evolution, emergence) |
| 4 | **Finance** | Quantitative (algorithms, risk models) | Behavioral (psychology, sentiment) |
| 5 | **Technology** | Systems architecture (design, infrastructure) | Artificial intelligence (ML, automation) |
| 6 | **Medicine** | Clinical (treatments, trials, outcomes) | Preventive (public health, epidemiology) |
| 7 | **Geography** | Physical (climate, geology, resources) | Human (demographics, urbanization) |
| 8 | **History** | Analytical (patterns, causation, cycles) | Narrative (culture, identity, memory) |
| 9 | **Economics** | Macro (policy, trade, monetary theory) | Micro (incentives, behavior, game theory) |
| 10 | **Philosophy** | Empiricism (evidence, logic, method) | Rationalism (reason, ethics, consciousness) |

## What makes this different

**Adversarial validation, not consensus.** Most multi-agent systems have agents agree with each other. Atlantis forces agents to attack each other's work. The system rewards successful destruction of weak claims.

**Objective validators before LLM judgment.** Nine rule-based validators check claims before any LLM judge sees them — catching invalid citations, circular reasoning, unfalsifiable claims, bad math, and domain-specific issues. The judge sees these flags as evidence, not just vibes.

**Constitutional governance.** A 1,007-line constitution defines the rules. States can't change the rules — they operate within them. This prevents the drift and collapse that kills other multi-agent systems.

**States die.** If a State consistently produces garbage, it loses tokens, enters probation, and gets dissolved by Senate vote. Its territory gets respawned with a new approach. This is the mechanism that prevents stagnation.

**Token economy with real consequences.** Validated hypotheses earn tokens. Refuted ones cost tokens. Successful challenges earn tokens. The budget determines what a State can do, and hitting zero means dissolution.

**Everything is preserved.** Every hypothesis, challenge, defense, and ruling is stored with full text — never truncated. The Knowledge Base is append-only. Refuted hypotheses go to the graveyard with their full autopsy.

## Tier system

| Tier | Name | Requirement |
|------|------|-------------|
| 0 | Empty | Starting state |
| 1 | Foundation | 5 validated hypotheses |
| 2 | Argumentation | 15 validated + Founder panel approval |
| 3 | Depth | 30 validated + active City |
| 4 | Application | 50 validated + active Town |
| 5 | Influence | 75 validated + 10 cross-domain citations |

Higher tiers face stricter validation standards. A Tier 3 claim that would pass at Tier 1 gets destroyed for insufficient depth.

## Objective validators

**Universal validators** run on all claims at zero API cost:

| Validator | Catches |
|-----------|---------|
| Citation validity | References to non-existent archive entries |
| Self-contradiction | Position negates its own conclusion |
| Circular reasoning | Conclusion restates the position (>80% overlap) |
| Numeric consistency | Percentages >100%, sums that don't add up |
| Reasoning depth | Insufficient steps for State's tier |

**Domain-specific validators** check logical structure:

| Validator | Domain | Catches |
|-----------|--------|---------|
| Math validity | Mathematics | Claims that "prove" metaphysical positions with theorems |
| Empirical check | Physics, Bio, Medicine, Geo | Unfalsifiable claims, missing testable predictions |
| Finance check | Finance, Economics | Ungrounded predictions, survivorship bias |
| Historical check | History | Monocausal explanations, missing source attribution |

**Real-world anchors** connect claims to external reality:

| Domain | Anchor | Examples |
|--------|--------|----------|
| **Mathematics** | SymPy verification | Catches wrong derivatives, bad arithmetic (2+2=5), incorrect simplifications |
| **Physics** | Dimensional analysis | Catches speeds >c, temps <0K, wrong constants (Planck, Boltzmann, G) |
| **Biology** | Established facts | Catches wrong DNA base pairing, Lamarckian inheritance, prokaryote nuclei |
| **Finance** | Financial logic | Catches wrong compound interest, negative probabilities, impossible returns |
| **Technology** | CS fundamentals | Catches P=NP claims, halting problem violations, O(1) sorting |
| **Medicine** | Clinical standards | Catches debunked claims (vaccines→autism), correlation→causation jumps |
| **Geography** | Physical constants | Catches wrong Earth measurements, population orders of magnitude |
| **History** | Chronology | Catches anachronisms (ancient Rome with guns), wrong dates (French Revolution 1889) |
| **Economics** | Accounting identities | Catches GDP components >100%, impossible sustained growth claims |
| **Philosophy** | Formal logic | Catches affirming consequent, false dilemmas, naturalistic fallacy |

These anchors use **actual computation** (SymPy, dimensional analysis, date verification) instead of LLM opinion. When a Math claim says "the derivative of x² is 3x", SymPy computes the actual derivative (2x) and flags the error. When a Physics claim says "speed = 5×10⁹ m/s", the anchor flags it because c = 3×10⁸ m/s. This is what makes Atlantis interact with reality, not just argue about it.

## Quick start

```bash
git clone https://github.com/teddygcodes/atlantis.git
cd atlantis
pip install -r requirements.txt
npm install

# Run the engine (10 domains, 3 governance cycles)
python3 __main__.py --demo-10-domains --force-clean

# Generate site data from engine output
python3 generate_site_data.py

# Start the site
npm run dev
```

Or use the Makefile:

```bash
make setup      # Install dependencies
make run-10     # Run 10-domain engine
make site-data  # Generate site data
make dev        # Start dev server
make ship       # Full pipeline: engine → data → build
```

## Data pipeline

```
engine run
    ↓
runs/<timestamp>/archive.json    ← full engine output
    ↓
python3 generate_site_data.py    ← parses into TypeScript
    ↓
lib/data.ts                      ← site data layer
    ↓
git push → Vercel auto-deploy    ← atlantiskb.com updates
```

## Site

Live at [atlantiskb.com](https://atlantiskb.com). Built with Next.js 16, Tailwind v4, React 19.

| Page | Shows |
|------|-------|
| **Research Timeline** | Cycle-by-cycle narrative of what happened |
| **States** | All 20 States — knowledge graphs, W/P/L records, learning arcs |
| **Knowledge Base** | Validated hypotheses that survived adversarial review |
| **Debates** | Full exchanges — hypothesis, challenge, defense, verdict |
| **Refuted** | Hypotheses that didn't survive, with full autopsy |
| **About** | System stats and explanation |

Each hypothesis has an **"Explain Simply"** button powered by Claude.

## Architecture

```
atlantis/
├── core/
│   ├── engine.py          # Top-level orchestrator (Phase 0 → 1 → 2)
│   ├── llm.py             # LLM provider with rate limiting + caching
│   ├── models.py          # Model router (task → Haiku/Sonnet/Opus)
│   └── persistence.py     # SQLite layer (append-only archive)
├── governance/
│   ├── states.py          # State class + claim pipeline functions
│   ├── perpetual.py       # Governance cycle engine
│   ├── validators.py      # Universal + domain validators
│   └── anchors.py         # 10 real-world anchor validators
├── agents/
│   └── base.py            # 20 Founder configs + agent factories
├── founders/
│   └── convention.py      # Phase 0: Founder research deposits
├── content/
│   └── generator.py       # 4-format content generation
├── config/
│   └── settings.py        # Config, model allocation, token values
├── app/                   # Next.js pages
├── components/            # React components (Crimson Edge design)
├── lib/data.ts            # Generated site data
├── generate_site_data.py  # Archive → TypeScript pipeline
├── CONSTITUTION.md        # 1,007-line governance document
└── Makefile
```

## Content pipeline

High-drama exchanges automatically generate content:

| Format | Style | Trigger |
|--------|-------|---------|
| **Blog** | Science journalist, 500-1000 words | Drama ≥ 5 |
| **Newsroom** | Breaking news, 150-200 words | Drama ≥ 7 or Novelty ≥ 8 |
| **Debate script** | Netflix documentary narrator, 60-90s | Drama ≥ 7 or Novelty ≥ 8 |
| **Explorer** | First-person travel blog, 200-300 words | New State/City/Town |

State dissolution generates all four formats at Drama 10.

## Model allocation

| Task | Model | Why |
|------|-------|-----|
| Normalization, extraction, anti-loop | Haiku | Structured, cheap |
| Research, challenges, rebuttals | Sonnet | Needs reasoning quality |
| Judge rulings | Sonnet | Highest stakes |
| Supreme Court appeals | Opus | Rare, unanimous panel |
| Content generation | Haiku | High volume |

## Tech stack

**Engine:** Python 3.11 · SQLite · Anthropic API
**Site:** Next.js 16 · React 19 · Tailwind v4
**Hosting:** Vercel (auto-deploy on push)
**Models:** Claude Haiku / Sonnet / Opus (task-routed)

## Stats

- ~12,000 lines of Python across 10 core modules
- 1,007-line constitution
- 5 universal validators + 4 domain validators + 10 real-world anchors
- 4 content generation formats
- 10 research domains, 20 rival States

## License

MIT
