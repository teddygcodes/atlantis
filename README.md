# PROJECT ATLANTIS — The Lost Civilization, Rebuilt

## What This Is

A self-governing AI civilization. Twenty Founder agents build deep knowledge
across 10 research cycles, then convene a 4-round Constitutional Convention
where they **design and build the government through structured votes** —
not articles, not essays, but concrete specifications that directly become
the live config. Then they **permanently retire**. The government they built
takes over, forming States, Cities, and Towns, growing knowledge deeper
every cycle. Forever.

**This is not a chatbot. This is not a prompt chain. This is a civilization.**

All intelligence comes from Claude API calls. No web search. No browsing.
No external data. Pure Claude reasoning.

## How It Works

```
Phase 0: Founding Period
  20 Founders × 10 research cycles = 200 knowledge entries
  Each Founder builds depth in their domains using Claude's built-in knowledge

Phase 1: Constitutional Convention (4 Rounds)
  Round 1 — STRUCTURE: How many branches? What are they? Who sits on them?
  Round 2 — POWERS: What can each branch do? Voting thresholds?
  Round 3 — KNOWLEDGE & CYCLE: Research standards, State formation, the forever loop
  Round 4 — SAFEGUARDS: Non-amendable clauses, amendments, health monitoring, ethics

  Each decision: 2v2 adversarial debate → all 20 vote → 14/20 (70%) to pass
  Passed decisions directly mutate the GovernmentBlueprint
  Failed decisions trigger counter-proposals (competing visions)

Phase 2: Government Deployment
  The blueprint IS the spec. No parser. No interpretation.
  Deployer reads the blueprint and instantiates exactly what the Founders voted for.
  Founders retire permanently.

Phase 3: Autonomous Governance
  The perpetual cycle runs forever:
  agenda → research → legislate → implement → judge → health_check → archive → publish → repeat
  (Only steps the Constitution defined. No judiciary vote = no judge step.)
```

## Architecture

```
atlantis/
├── agents/
│   └── base.py            # BaseAgent + all 20 Founder definitions
├── config/
│   └── settings.py        # Hard constraints, depth tiers, debate matchups
├── content/
│   ├── logger.py          # AtlantisLogger — logs everything
│   └── generator.py       # TikTok scripts + blog posts from governance events
├── core/
│   ├── engine.py          # Main orchestrator — runs all 4 phases
│   ├── llm.py             # Claude API with 1-second rate limiting
│   └── persistence.py     # SQLite state management
├── founders/
│   └── convention.py      # 10-cycle research + 4-round Convention + GovernmentBlueprint
└── governance/
    ├── deployer.py        # Deploys government from Founder-built blueprint (no parser)
    └── perpetual.py       # The forever cycle engine
```

## The 20 Founders

### Governance Core — 8 Founders
| Founder | Role | Convention Focus |
|---------|------|-----------------|
| **Hamilton** | Systems Architect | Government structure, efficiency mandates |
| **Jefferson** | Sovereignty Champion | State rights, decentralization, diversity |
| **Franklin** | Evidence Gatekeeper | Knowledge standards, depth tiers, evidence |
| **Madison** | Legislative Designer | Checks and balances, separation of powers |
| **Marshall** | Judicial Architect | Supreme Court, judicial review, case law |
| **Washington** | Stability Guardian | Safety limits, non-amendable clauses |
| **Paine** | Transparency Architect | Content pipeline, radical transparency |
| **Tyler** | Integration Engineer | Cross-branch coordination, the governance cycle |

### Knowledge Champions — 12 Founders
| Founder | Domain | Convention Focus |
|---------|--------|-----------------|
| **Darwin** | Evolution | Evolutionary governance, adaptation mechanisms |
| **Curie** | Science | Experimental validation, scientific rigor |
| **Turing** | Computation | Loop prevention, computational integrity |
| **Aristotle** | Philosophy | Ethical principles, philosophical governance |
| **Hippocrates** | Health | System health monitoring, diagnostics |
| **Da Vinci** | Design | Creative synthesis, cross-domain innovation |
| **Brunel** | Engineering | Infrastructure standards, implementation authority |
| **Olympia** | Performance | Metrics, measurement, State representation |
| **Smith** | Economics | Resource budgets, sustainability mandates |
| **Herodotus** | History | Institutional memory, historical preservation |
| **Euclid** | Mathematics | Formal verification, logical consistency |
| **Carson** | Environment | Ecosystem diversity, knowledge biodiversity |

## Phase 0: The Founding Period

20 Founders × 10 research cycles = **200 knowledge entries**.

Each cycle, every Founder researches one of their domains using Claude's
built-in knowledge. Knowledge is structured: concepts, frameworks,
applications, cross-domain connections. Founders progress through the
5-tier depth system:

1. **Vocabulary** — Basic terminology
2. **Frameworks** — Models and structures
3. **Application** — Real-world uses
4. **Synthesis** — Cross-domain connections
5. **Novel Insight** — Original contributions

Founders must reach minimum Tier 2 before the Convention opens.
10 cycles gives them genuine depth to draw from when designing the government.

## Phase 1: The Constitutional Convention

The Founders don't write articles for a parser to interpret.
They vote on **concrete specifications** that directly become the government.

### Round 1 — STRUCTURE

The fundamental question: what does this government look like?

**Madison** proposes a 3-branch system:
- Senate: 4 seats (Critic, Tester, Historian, Debugger)
- House: 2 seats (Architect, Coder)
- Court: 3 seats (WARDEN, Justice Critic, Justice Historian)

Debated 2v2. All 20 vote. 14/20 to pass.

**If rejected**, Jefferson counter-proposes a decentralized council model.
Two runs can produce two completely different civilizations.

Then Olympia proposes dynamic State representative seats in the legislature.

### Round 2 — POWERS

What can each branch actually do?

- **Marshall** proposes judicial review (strike-down power, compel amendments, binding precedent)
- **Hamilton** proposes Senate legislative powers (Bills, agendas, budgets, State formation, emergencies)
- **Brunel** proposes House implementation authority (feasibility review, block unimplementable Bills)
- **Paine** proposes radical transparency (every event logged, auto-generate blog + TikTok, no secrets)

Each proposal is a permission map: `{"powers": ["strike_down_unconstitutional", "compel_amendment"]}`.
Not an essay. A spec.

### Round 3 — KNOWLEDGE & CYCLE

How does the civilization grow?

- **Franklin** proposes the 5-tier knowledge standard
- **Jefferson** proposes State formation rules (sovereignty, own constitution, hierarchy: State → City → Town)
- **Smith** proposes resource budgets (100K tokens/cycle, cost estimates on every Bill)
- **Tyler** proposes the governance cycle (adapts to whatever branches exist from Round 1)

### Round 4 — SAFEGUARDS

What can never change? What happens when things break?

- **Washington** proposes non-amendable clauses (growth limits, permanent retirement, no unchecked power, no infinite loops, constitution can't be nullified)
- **Darwin** proposes the amendment process (2/3 supermajority, 25-cycle cooldown, Court can fast-track)
- **Hippocrates** proposes health monitoring (vital signs, early warning, do no harm)
- **Aristotle** proposes ethical principles (justice, prudence, courage, temperance)
- **Turing** proposes computational integrity (all processes terminate, max recursion 10, deadlock timeout 5 cycles)

## The 2v2 Debate Format

Every decision goes through this:

1. **Proposer** presents the specification
2. **2 Supporters** argue FOR (assigned from pre-built matchup table based on philosophical alignment)
3. **2 Opponents** argue AGAINST (assigned from opposing perspectives — Hamilton vs Jefferson, Euclid vs Da Vinci)
4. Opponents see the supporters' arguments and specifically counter them
5. **Proposer closing** addresses the opposition
6. **All 20 vote** — 14/20 required

The matchups ensure genuine adversarial tension, not rubber-stamping.

## Phase 2: Government Deployment

The GovernmentBlueprint is the live config. No parser. No interpretation layer.

The deployer reads each branch the Founders voted for and instantiates agents
with the exact seats, powers, and constraints they specified. If they voted for
3 branches, 3 branches deploy. If they rejected the judiciary, there's no Court.

The Founders permanently retire. Their knowledge is archived. They never return.

## Phase 3: Autonomous Governance

The perpetual cycle runs whatever the Founders built:

```
agenda → research → legislate → implement → judge → health_check → archive → publish → repeat
```

Each step only runs if the Constitution defined it. Every cycle:
- **Agenda**: Senate sets research priorities
- **Research**: States research their domains (or identify first State candidates)
- **Legislate**: Senate proposes and votes on Bills (State formation, research agendas)
- **Implement**: House reviews feasibility
- **Judge**: Supreme Court checks constitutionality
- **Health Check**: Monitor for stagnation, deadlock, resource issues
- **Archive**: Persist everything to SQLite
- **Publish**: Generate TikTok scripts and blog posts from dramatic events

## The Content Pipeline

Every governance event automatically generates:
- **TikTok Scripts**: 60-90 second clips from close votes, judicial rulings, heated debates
- **Blog Posts**: Analysis of landmark decisions, State formations, constitutional crises
- **Milestone Announcements**: New States, tier achievements, historic rulings

Content is a byproduct of real governance. Not manufactured.

## Cost

The full founding process — 200 research entries + 15 Convention decisions
across 4 rounds + 3 governance cycles — costs approximately **$2.10** in
Claude API calls. Achieved by:
- Pure Claude knowledge (no web search)
- 1-second rate limiting between calls
- Response caching for identical queries
- Token limits on every call

## Running

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run the full process (default 10 governance cycles after founding)
python __main__.py

# Run with custom data directory
python __main__.py my_data_dir

# Run in local simulation mode (no API key needed)
python __main__.py --local

# Control governance cycles
python __main__.py --local --cycles 5

# Full production run
python __main__.py --cycles 20
```

## Hard Constraints

These exist before the Founders vote. They cannot be overridden:
- Max 25 States, 15 Cities per State, 10 Towns per City
- Max 100K tokens per cycle
- Founders MUST retire after the Convention
- Constitutional amendments require 2/3 supermajority
- Minimum 25 cycles between amendments
- 1-second minimum between API calls
- All intelligence from Claude API — no web calls
