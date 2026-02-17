# ATLANTIS

A constraint-driven multi-agent governance engine. 20 AI agents research knowledge domains, write a constitution through adversarial debate, form autonomous States, and self-govern under rules they created — with hard constraints that prevent the system from collapsing into consensus, loops, or drift.

Built on Claude API. ~8,700 lines of Python. No web search, no external data — pure LLM reasoning under structural pressure.

## What It Actually Does

```
Phase 0: 20 Founders × 3 research cycles = 60 knowledge entries
         Each Founder builds depth in their assigned domains
         Knowledge parsed, stored, tier-tracked automatically

Phase 1: Jefferson writes a draft Constitution
         4 branches, tiered knowledge engine, non-amendable clauses
         Government deploys immediately — Constitution evolves during governance

Phase 2: Founding Era — Collaborative governance + State formation
         Each cycle: Amendment proposal → 2v2 debate → 20-agent vote
                     State Formation Bill → debate → vote → form State
                     State research → tier advancement
         Founders retire when target States are formed

Phase 3: Autonomous Governance — Perpetual engine
         States self-govern: legislate → research → implement → judge
         No human intervention. The system runs on what the Founders built.
```

## First Mock Run Results

4 cycles. 3 States formed. 4 amendments debated and rejected. 236K tokens. ~$1.35 in API costs.

**States formed:**
- The Principality of Axiom (Mathematics) — proposed, rejected 5/20, re-proposed with better framing, passed 12/20
- The Empirical Republic (Natural Philosophy) — passed 14/21 over Jefferson's objection that it was "federal overreach disguised as State formation"
- The Mechanicum (Engineering) — near-unanimous 19/22, only Franklin, Aristotle, and Da Vinci dissenting

**Constitutional features the AI designed:**
- 4 branches: Senate of States, Knowledge Council, Constitutional Court, Implementation Assembly
- 5 non-amendable clauses (State sovereignty, mandatory knowledge validation, diversity protection)
- Anti-loop protocols as constitutional law
- Tiered knowledge system (Tier 0-5) embedded in the founding document

**What the Senate rejected:**
- Mandatory judicial review (killed 4 times — Jefferson: "federal overreach")
- Formal logical consistency requirements (Madison: "weaponizes logical formalism against democratic governance")
- Mandatory efficiency metrics (Euclid: "measurement paradox undermines true knowledge")

The Founders aren't rubber stamps. They argue, they vote no, they have principles.

## Architecture

```
atlantis/
├── agents/base.py              # 20 Founder agents with distinct personalities, fears, domains
├── config/settings.py          # Hard constraints, depth tiers, governance rules
├── content/
│   ├── generator.py            # TikTok scripts + blog posts from governance events
│   └── logger.py               # Full event logging with narrative generation
├── core/
│   ├── engine.py               # Main orchestrator — all 4 phases
│   ├── llm.py                  # Claude API with rate limiting + caching
│   └── persistence.py          # SQLite — constitutional versioning, knowledge archive
├── founders/
│   └── convention.py           # Research cycles, constitutional drafting, amendment debates
└── governance/
    ├── deployer.py             # Instantiates government from Constitution spec
    ├── perpetual.py            # Autonomous governance cycle engine
    └── states.py               # State/City/Town hierarchy with tiered knowledge
```

## The 20 Founders

### Governance Core
| Founder | Role | What They Fight For |
|---------|------|-------------------|
| Hamilton | Systems Architect | Efficiency, resource optimization, institutional structure |
| Jefferson | Sovereignty Champion | State rights, decentralization, intellectual diversity |
| Franklin | Evidence Gatekeeper | Empirical standards, knowledge validation, anti-hallucination |
| Madison | Legislative Designer | Checks and balances, separation of powers, process integrity |
| Marshall | Judicial Architect | Rule of law, constitutional interpretation, precedent |
| Washington | Stability Guardian | Failure analysis, non-amendable clauses, system safety |
| Paine | Transparency Architect | Public accountability, content pipeline, open governance |
| Tyler | Integration Engineer | Cross-system coordination, protocol design, interoperability |

### Knowledge & Science
| Founder | Role | What They Fight For |
|---------|------|-------------------|
| Darwin | Evolutionary Theorist | Adaptation, natural selection, complex adaptive systems |
| Curie | Scientific Methodologist | Experimental rigor, hypothesis testing, peer review |
| Turing | Computational Theorist | Formal logic, algorithmic governance, decidability |
| Aristotle | Ethical Philosopher | Virtue theory, political philosophy, epistemology |
| Hippocrates | Systems Diagnostician | Health monitoring, preventive care, triage protocols |
| Da Vinci | Creative Synthesist | Cross-domain innovation, design thinking, visual systems |

### Infrastructure & Measurement
| Founder | Role | What They Fight For |
|---------|------|-------------------|
| Brunel | Infrastructure Engineer | Engineering standards, reliability, capacity planning |
| Olympia | Performance Analyst | Metrics, benchmarking, measurement frameworks |
| Smith | Resource Economist | Scarcity management, sustainability, budget theory |
| Herodotus | Institutional Historian | Archival science, institutional memory, historiography |
| Euclid | Formal Logician | Proof theory, axiomatic systems, mathematical foundations |
| Carson | Ecosystem Guardian | Biodiversity, sustainability science, carrying capacity |

Each Founder has defined fears that drive adversarial behavior. Curie fears pseudoscience. Jefferson fears centralization. Carson fears unbounded growth. These fears create genuine debate tension, not scripted disagreement.

## Knowledge Depth System

States advance through tiers by accumulating research:

| Tier | Name | Requirements |
|------|------|-------------|
| 0 | Empty | No knowledge |
| 1 | Vocabulary | Basic concepts and definitions |
| 2 | Frameworks | Relationships and structural models |
| 3 | Application | Practical implementation (States can't publish until here) |
| 4 | Cross-Domain Synthesis | Integration across knowledge areas |
| 5 | Novel Insight | Original contributions (States can claim expertise) |

Tier advancement is cumulative — knowledge compounds across cycles, not per-cycle. A State that stagnates stays at its tier. A State that produces nothing can be dissolved.

## Structural Safeguards

These prevent the failure modes that kill multi-agent systems:

**Against semantic drift:**
- Non-amendable constitutional clauses enforced in code
- Constitutional versioning with immutable snapshots (v1.0 = Jefferson's original, preserved forever)

**Against spawn explosion:**
- Hard cap: 50 States maximum
- 15 Cities per State, 10 Towns per City
- 3 depth levels maximum (State → City → Town)

**Against amendment stacking:**
- 3-cycle cooling period between passed amendments
- Supermajority required for ratification

**Against knowledge bloat:**
- Quality scoring on archive entries (tier weight + content richness)
- Cumulative tier calculation prevents artificial advancement
- Self-citation penalty in quality scoring

**Against consensus collapse:**
- Founder fears create persistent adversarial pressure
- 2v2 debate format ensures both sides are argued before every vote
- Vote parsing handles all LLM formatting styles (bold markdown, numbered lists, fences)

## Content Pipeline

Every governance event automatically generates:
- **TikTok scripts** (~170 words) from State research breakthroughs
- **Blog posts** from landmark votes, State formations, constitutional crises

Content is a byproduct of real governance. Not manufactured.

## Running

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Quick mock run (3 States, 5 governance cycles) — ~$1.35
python __main__.py --mock

# Full production run (20 States, 10 governance cycles)
python __main__.py

# Custom governance cycles
python __main__.py --cycles 20
```

## Cost

| Run Type | API Calls | Tokens | Cost |
|----------|-----------|--------|------|
| Mock (3 States, 5 cycles) | ~365 | ~236K | ~$1.35 |
| Full (20 States, 10 cycles) | ~2,000+ | ~1.5M+ | ~$8-12 |

All calls use Claude with 1-second rate limiting. Response caching prevents duplicate queries.

## The Interesting Bug

During development, 60 research cycles completed successfully but the Federal Archive contained 0 entries. No errors. No crashes. The system ran perfectly — it just learned nothing.

Root cause: Claude formats responses with bold markdown (`**CONCEPTS:**`) but the parsers only matched plain text (`CONCEPTS:`). Two asterisks silently dropped every piece of knowledge across the entire system. Five parsing functions across two files, all with the same bug.

One `content.replace("**", "")` fixed everything. The Archive went from 0 to 58 entries. States started advancing tiers. The system came alive.

If you're building on LLMs: never assume output formatting is consistent. The system that crashes is safer than the one that runs with empty data.

## What This Demonstrates

- **Multi-agent orchestration** with persistent state and structured adversarial debate
- **Constitutional governance** as a mechanism for preventing AI system collapse
- **Knowledge compounding** with tiered depth tracking and quality scoring
- **Irreversibility as a feature** — constitutional versioning, Founder retirement, amendment cooling
- **Structured output parsing** that handles real-world LLM formatting variance
- **Content generation** as a natural byproduct of system operation

## License

MIT
