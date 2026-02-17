# Atlantis

**Adversarial multi-agent governance engine with constitutional constraints**

Atlantis is a multi-agent AI system where 20 Founding agents research knowledge domains, write a constitution through structured debate, form self-governing States, and produce content from governance events — all under constitutional constraints that prevent the system from collapsing.

The system ran end-to-end for **$2.11** across **512 API calls** without a single crash.

---

## What It Does

Atlantis simulates a complete civilization lifecycle:

1. **Phase 0 — Founding Research**: 20 AI Founders research across knowledge domains, building baseline knowledge
2. **Phase 1 — Constitutional Convention**: Jefferson drafts a Constitution with branches, powers, checks, and non-amendable clauses
3. **Phase 2 — Founding Era**: Founders debate amendments (all 5 rejected), propose and vote on State formation, States begin independent research
4. **Phase 3 — Autonomous Governance**: Founders retire. States govern themselves under the Constitution they inherited. Judge → Research → Legislate every cycle.

Every phase produces TikTok scripts and blog posts automatically from real governance events.

---

## Real Results (Mock Run — February 2026)

### The Constitution
Jefferson wrote a 4,631-character Constitution with:
- 4 branches of government (Senate, Knowledge Council, Constitutional Court, Implementation Assembly)
- 5 non-amendable clauses protecting State sovereignty and knowledge validation
- Anti-loop protocols embedded as constitutional law
- Tiered knowledge system (Tier 0-5) as foundational policy
- Constitution v1.0 saved immutably

### Amendments: 5 Proposed, 0 Passed
The Senate rejected every amendment. Not because the system is broken — because the agents genuinely disagreed:

| Amendment | Vote | Key Opposition |
|-----------|------|----------------|
| Explicit judicial review | 2/20 | Jefferson: "federal overreach" |
| Mandatory formal verification | 3/20 | Madison: "weaponizes logical formalism against democratic governance" |
| Mandatory efficiency metrics | 3/20 | Euclid: "measurement paradox undermines true knowledge" |
| Standardized communication | 6/20 | Franklin: "evidence-free bureaucracy trap" |
| Constitutional verification protocol | 7/20 | Brunel: "verification bottleneck paralyzes evolution" |

### States Formed: 3 (of 5 proposed)

| State | Domain | Vote | Notable |
|-------|--------|------|---------|
| The Axiom Republic | Mathematics | 13/20 | Rejected first attempt 5/20, passed on resubmission |
| The Empirical Republic | Natural Philosophy | 14/21 | Jefferson voted REJECT: "federal overreach disguised as State formation" |
| The Forge of Praxis | Engineering | 19/22 | Near-unanimous. Both existing State Senators voted APPROVE |

**Rejected proposals:**
- The Republic of Principia (Physics) — **0/21**. Unanimous rejection. Washington: "Physics underpins every domain — creating a monopoly is a single point of failure"
- The Lyceum of First Principles (Philosophy) — **5/21**. Hamilton: "Philosophy generates infinite token consumption with zero measurable output"

### Tier Advancement
The Empirical Republic reached **Tier 2** during autonomous governance — the first confirmed tier advancement in the project's history. Research topic at breakthrough: "Causal Closure — the principle that every physical event has sufficient physical cause."

### Non-Deterministic
Two separate runs produced genuinely different civilizations:

| | Run 1 | Run 2 |
|---|-------|-------|
| Math State | The Principality of Axiom | The Axiom Republic |
| Science State | The Empirical Republic | The Empirical Republic |
| Engineering State | The Mechanicum | The Forge of Praxis |
| Constitution | 4 branches, bicameral | 4 branches, different structure |
| Amendments passed | 0/4 | 0/5 |

Same domains emerged. Different names, different constitutions, different political dynamics.

---

## Architecture

```
atlantis/
├── core/
│   ├── engine.py          # Phase orchestration, cycle management
│   ├── persistence.py     # SQLite database, Federal Archive, state management
│   └── llm.py             # LLM provider (Claude API + mock mode)
├── founders/
│   └── convention.py      # 20 Founders, Constitutional Convention, debates
├── governance/
│   ├── states.py          # States, Cities, Towns, tier system, research cycles
│   ├── deployer.py        # Government deployment from constitutional blueprint
│   └── perpetual.py       # Autonomous governance engine (Phase 3)
├── agents/
│   └── base.py            # Base agent class, knowledge tracking
├── content/
│   ├── generator.py       # TikTok/blog content from governance events
│   └── logger.py          # Event logging with significance levels
├── config/
│   └── settings.py        # All configuration, tier thresholds, constraints
└── __main__.py            # Entry point
```

### Key Design Decisions

**Governance prevents collapse.** The core innovation is using constitutional constraints to prevent the failure modes that kill multi-agent systems: infinite loops, hallucination drift, authority concentration, and semantic decay.

**Tiered knowledge validation.** States can't publish until Tier 3, can't claim expertise until Tier 4. Knowledge is earned through research cycles, not self-declared.

**Constitutional versioning.** Every amendment changes the version. The original v1.0 is immutable. The system can track how governance evolved over time.

**Token budget tracking.** Every API call is tracked per agent. Designed for model optimization: Haiku for routine tasks, Sonnet for governance, Opus for deep reasoning.

---

## The Bold Markdown Bug

The root cause of the project's biggest failure was two characters: `**`

Claude returns research with bold markdown formatting: `**CONCEPTS:**`. The parser expected plain text: `CONCEPTS:`. Every research cycle produced valid knowledge that was silently discarded because the regex couldn't match through bold markers.

**Result:** 60 research cycles. Zero knowledge retained. 20 Founders researching for nothing. The Federal Archive empty. State formation votes failing because voters had no knowledge context.

**Fix:** One line per parser:
```python
content = content.replace("**", "")
```

Applied to 8 parsing functions across 3 files. Archive went from 0 entries to 57. The entire system came alive.

This is the kind of bug that doesn't show up in unit tests. It's a formatting mismatch between two AI systems — the one generating output and the one parsing it. If you're building multi-agent systems, check your parsers against actual LLM output, not expected output.

---

## The 20 Founders

| Founder | Domain | Role |
|---------|--------|------|
| Hamilton | Systems Theory | Resource optimization, economic structure |
| Jefferson | Political Philosophy | State sovereignty, individual rights |
| Franklin | Epistemology | Evidence standards, scientific methodology |
| Madison | Constitutional Law | Structural checks, power balance |
| Marshall | Jurisprudence | Legal interpretation, precedent |
| Washington | Leadership Theory | Executive restraint, voluntary power transfer |
| Paine | Transparency | Open governance, accountability |
| Tyler | Political Economy | State rights, economic independence |
| Darwin | Evolutionary Theory | Adaptation, selection pressure |
| Curie | Scientific Method | Experimental design, hypothesis testing |
| Turing | Computation Theory | Formal logic, algorithmic governance |
| Aristotle | Classical Philosophy | Epistemology, virtue ethics |
| Hippocrates | Medical Ethics | Evidence-based practice, harm prevention |
| Da Vinci | Design Thinking | Cross-domain innovation, systems design |
| Brunel | Infrastructure | Engineering standards, practical application |
| Olympia | Athletics Philosophy | Performance metrics, competitive fairness |
| Smith | Economics | Market dynamics, resource allocation |
| Herodotus | Historical Analysis | Pattern recognition, civilizational cycles |
| Euclid | Formal Logic | Proof theory, mathematical foundations |
| Carson | Environmental Science | Ecological systems, sustainability |

---

## Cost Breakdown

| Phase | API Calls | Tokens | Est. Cost |
|-------|-----------|--------|-----------|
| Phase 0 (Research) | ~120 | ~80K | $0.48 |
| Phase 1 (Convention) | ~30 | ~25K | $0.15 |
| Phase 2 (Founding Era) | ~250 | ~170K | $1.02 |
| Phase 3 (Governance) | ~112 | ~79K | $0.46 |
| **Total** | **512** | **354,181** | **$2.11** |

An entire AI civilization for the cost of a cup of coffee.

---

## Running It

```bash
# Clone
git clone https://github.com/teddygcodes/atlantis.git
cd atlantis

# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Run in mock mode (no API calls, tests full pipeline)
python3 -u __main__.py --mock

# Run with real API calls
python3 -u __main__.py
```

**Requirements:**
- Python 3.10+
- `anthropic` Python package (`pip install anthropic`)
- An Anthropic API key (for real runs)

---

## What's Next (v2)

The current system produces knowledge through research cycles. v2 redesigns knowledge production around adversarial debate:

- **Rival States**: Every domain has two competing States with different methodologies
- **Claim-Defend-Challenge Pipeline**: States make argued claims with full reasoning chains, defend against rival challenges. Only what survives enters the Archive.
- **Show Your Work**: Every claim requires step-by-step reasoning. Rivals attack specific steps. Any agent can follow the logic regardless of domain expertise.
- **Three Claim Types**: Foundation (build on Archive), Discovery (genuinely new knowledge), Challenge (overturn existing claims)
- **Cities and Towns**: Cities analyze what surviving claims mean. Towns build practical applications. The full hierarchy — argue, analyze, apply — produces output a human can evaluate.
- **Executive Branch**: Elected philosophy agent with code-enforced parameters. Senate votes on governance configurations, not personalities.
- **Constitutional Court**: Three Judges with fixed philosophies (Originalist, Pragmatist, Protectionist). Permanent until civilizational collapse.
- **Collapse and Refounding**: When the system fails, the Archive survives. New civilizations inherit everything and build on it.
- **The Beast**: Commercial product. Point Atlantis at any domain, receive adversarially tested analysis with full reasoning chains.

Full v2 Constitution (1,007 lines, 16 Articles) is written and ready for implementation.

---

## Evolution

This is the 5th iteration:
- HYDRA V1-V4: Four previous attempts, each teaching critical lessons about multi-agent failure modes
- **Atlantis V1**: Complete rebuild from architectural principles. First version to run end-to-end.

Every failure taught something. Governance prevents loops. Tiered validation prevents hallucination. Structured debate prevents drift. Constitutional constraints prevent collapse.

---

## Author

**Tyler Gilstrap** — [@teddygcodes](https://github.com/teddygcodes)

Built with Claude (Anthropic) for strategic architecture and Claude Code for implementation.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
