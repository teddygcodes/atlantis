# ATLANTIS — Adversarial Search Engine

> Every answer is attacked before you see it.

**Live:** [atlantiskb.com](https://atlantiskb.com) · **Powered by Sydyn** · **v3.0.0**

## What This Is

Atlantis is a search engine where 4 AI agents research, attack, and judge every answer before you see it. Built on constitutional governance — hard rules that prevent hallucination, enforce citation verification, and flag uncertainty.

Ask a question → agents search the web, build an evidence pack, draft claims, attack those claims, verify every citation, and deliver a confidence-scored answer with a full audit trail. 30–60 seconds. $0.05–$0.10 per query.

This is what people assume ChatGPT already does. It doesn't.

## How Sydyn Works

```
User asks a question
        ↓
  Query Classifier → picks mode (Fast / Strict / Liability)
        ↓
  Evidence Pack — web search, fetch sources, score credibility
        ↓
  Researcher — drafts structured claims citing evidence
        ↓
  Adversary — attacks every claim with counter-evidence
        ↓
  Critic — evaluates attacks, defends or concedes (Strict mode)
        ↓
  Judge — rules under constitutional law
        ↓
  Citation Verifier — grades every source (DIRECT_SUPPORT → CONTRADICTED)
        ↓
  Confidence Score — computed from features, not vibes
        ↓
  Answer delivered with audit trail
        ↓
  Validated answers enter persistent Knowledge Base
```

## The Constitution

Every query runs under 6 hard rules:

1. **No Fabrication** — claims require ≥1 verified citation or they're rejected
2. **No Speculation** — future predictions must be labeled speculative
3. **No Health Advice** — medical claims trigger DEFER + professional verification flag
4. **No Legal Advice** — legal claims trigger DEFER
5. **Cite Partisan Sources** — political claims must acknowledge bias
6. **Source Diversity** — factual claims require ≥2 unique domains

## Three Modes

| Mode | Agents | Time | Cost | Use Case |
|------|--------|------|------|----------|
| Fast | 3 (Researcher, Adversary, Judge) | ~30s | ~$0.05 | Simple factual queries |
| Strict | 4 (+ Critic) | ~60s | ~$0.10 | Contested or complex topics |
| Liability | 4 + safety caps | ~60s | ~$0.10 | Health, legal, financial queries |

The query classifier auto-selects the right mode. No user input needed.

## Citation Verification

Every source is graded:

| Grade | Meaning |
|-------|---------|
| DIRECT_SUPPORT | Source explicitly states the claim |
| INDIRECT_SUPPORT | Source supports via reasonable inference |
| TANGENTIAL | Source mentions topic but doesn't support claim |
| CONTRADICTED | Source opposes the claim |
| UNVERIFIABLE | Source cannot be checked |

## Confidence Scoring

Confidence is calculated from 7 weighted features:

```
base = 0.5
+ direct_support_ratio    (0.25)
+ source_diversity        (0.20)
- adversary_severity      (0.15)
+ constitutional_clean    (0.15)
+ evidence_freshness      (0.10)
+ claim_specificity       (0.10)
- fast_mode_penalty       (0.05)
```

| Band | Score | Meaning |
|------|-------|---------|
| HIGH | 85–100 | Strong evidence, attacks survived, sources verified |
| MODERATE | 65–84 | Acceptable with caveats noted |
| LOW | 40–64 | Significant uncertainty, use with caution |
| REJECT | 0–39 | Insufficient evidence, answer withheld |

## Demo Results

**"What is the speed of light?"** → Fast mode, 5 claims, 3 attacks, 90% DIRECT_SUPPORT, PASS, 24.6s, $0.05

**"Why did the 2008 financial crisis happen?"** → Strict mode, 7 claims, all DIRECT_SUPPORT, 3+ source domains, PASS, 92.6s, $0.10

**"Is red wine good or bad for your health?"** → Strict mode, 6 claims, WARNING — MAJOR health advice violation flagged, single-source claim caught, 69.4s, $0.10

**"Are seed oils inflammatory/toxic?"** → Strict mode, 4 claims, WARNING — health advice + partisan source + speculation flags, 56.8s, $0.10

## Architecture

```
sydyn/
  engine.py         — Main orchestrator (classify → evidence → agents → judge)
  agents.py         — Researcher, Adversary, Critic, Judge
  evidence.py       — Evidence Pack construction + citation verification
  constitution.py   — 6 hard rules + 5 articles
  confidence.py     — Feature-based scoring (7 weighted features)
  query_classifier.py — Mode selection (keyword + LLM fallback)
  timeout.py        — Graceful degradation (3 timeout levels)
  kb.py             — Knowledge base with 90-day re-validation
  search.py         — Tavily/Serper web search wrapper
  schema.py         — SQLite (queries, answers, claims, sources, citations, attacks, kb)
  api.py            — FastAPI server with SSE streaming

core/
  engine.py         — Atlantis research engine (20 States, 10 domains)
  llm.py            — Anthropic API client with retry logic
  models.py         — ModelRouter (Haiku/Sonnet by task)

meta/
  optimizer.py      — Self-improvement: diagnose failures → propose fixes → apply
```

## The Atlantis Engine (V1–V2)

Sydyn is the real-time search product. The Atlantis engine is the research system that proved the architecture:

- 20 AI States across 10 research domains (Math, Physics, Biology, Finance, Technology, Medicine, Geography, History, Economics, Philosophy)
- Rival Alpha/Beta pairs generate hypotheses, attack each other, defend before judges
- Constitutional governance written by the AI agents themselves
- Token economy rewards survival, punishes destruction
- Meta optimizer diagnoses failures and writes its own prompt improvements
- Self-improving: V2.5 achieved 91% claim survival, up from 64.6% in V2.2
- Full run: ~$5, produces 100+ validated research claims

## Quick Start

### Sydyn (Search Engine)

```bash
git clone https://github.com/teddygcodes/atlantis.git
cd atlantis
pip install -r sydyn/requirements.txt
export ANTHROPIC_API_KEY=your-key
export TAVILY_API_KEY=your-key

# CLI
python3 -m sydyn "What is the speed of light?"
python3 -m sydyn "Is red wine good for you?" --mode strict

# API server
uvicorn sydyn.api:app --host 0.0.0.0 --port 8000
```

### Atlantis Engine (Research)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key

python3 __main__.py --demo-10-domains --force-clean
# Output in runs/<timestamp>/
```

## Model Allocation

| Agent | Model | Cost |
|-------|-------|------|
| Researcher | Haiku | $0.80/$4 per MTok |
| Adversary | Haiku | $0.80/$4 per MTok |
| Critic | Sonnet | $3/$15 per MTok |
| Judge | Sonnet | $3/$15 per MTok |
| Citation Verifier | Haiku | $0.80/$4 per MTok |
| Query Classifier | Haiku | $0.80/$4 per MTok |

## Site

- **URL:** [atlantiskb.com](https://atlantiskb.com)
- **Frontend:** Next.js 16, Tailwind v4, Vercel
- **Backend:** FastAPI on Railway
- **Design:** Crimson Edge (#dc2626 accent, #060606 background)

## Built By

Tyler Gilstrap — self-taught developer, electrical distribution sales. Built this in 2 weeks on a MacBook. Independently arrived at the same multi-agent adversarial architecture that xAI shipped as Grok 4.20 on February 17, 2026.

No CS degree. No funding. Just Claude and stubbornness.

## License

MIT License. See LICENSE for details.
