# ATLANTIS

Adversarial search engine. 4 AI agents research, attack, and judge answers before showing them to you.

**Site:** [atlantiskb.com](https://atlantiskb.com)

## How It Works

You ask a question. The system searches the web, builds an evidence pack, and runs it through a pipeline:

1. **Researcher** drafts claims from the evidence
2. **Adversary** attacks those claims
3. **Critic** evaluates the attacks (in Strict mode)
4. **Judge** rules under 6 hard rules — no fabrication, no speculation, no health/legal advice without flagging it, cite partisan sources, require source diversity

Every citation gets verified against the actual source. Confidence is scored from features, not vibes. The full audit trail is visible.

## Modes

- **Fast** — 3 agents, ~30s, simple factual questions
- **Strict** — 4 agents, ~60s, contested or complex topics
- **Liability** — 4 agents with safety caps, health/legal/financial queries

The system picks the mode automatically.

## Quick Start

```bash
git clone https://github.com/teddygcodes/atlantis.git
cd atlantis
pip install -r sydyn/requirements.txt
export ANTHROPIC_API_KEY=your-key
export TAVILY_API_KEY=your-key

# Ask a question
python3 -m sydyn "What is the speed of light?"

# Run the API server
uvicorn sydyn.api:app --host 0.0.0.0 --port 8000
```

## Stack

Python, FastAPI, Next.js, Tailwind, Anthropic Claude API, Tavily Search API, SQLite, Vercel, Railway.

## Background

The Atlantis engine (V1–V2) was the research system that proved the architecture — 20 AI States across 10 domains generating and attacking hypotheses under constitutional governance. Sydyn is the search product built on top of that work.

## License

MIT
