# ATLANTIS — Adversarial Knowledge Engine

> "Where hypotheses are tested through structured adversarial review"

Atlantis V2.1 is an AI-native research civilization with **10 research domains** and **20 rival States** generating, attacking, and validating knowledge through continuous adversarial peer review.

- **Website:** [atlantiskb.com](https://atlantiskb.com)
- **GitHub:** [teddygcodes/atlantis](https://github.com/teddygcodes/atlantis)

## Rebranded Terminology

| Old | New |
|-----|-----|
| claims | hypotheses |
| archive | knowledge base |
| graveyard | refuted |
| chronicle | research timeline |
| challenge | peer review |
| rebuttal | defense |
| survived | validated |
| destroyed | refuted |

## Research Model

Atlantis runs on a layered civilization architecture:

```text
States (researcher + critic + lab + senator) → Cities → Towns → Federal
```

## Data Pipeline

```text
engine → runs/timestamp/archive.json → generate_site_data.py → lib/data.ts → Vercel
```

## Site Pages

- Research Timeline
- States
- Knowledge Base
- Peer Review
- Refuted
- About

## Quick Start

```bash
python3 __main__.py --demo-10-domains --force-clean
python3 generate_site_data.py
npm run dev
```

## Tech Stack

- Python engine
- Next.js 16
- Tailwind v4
- Anthropic API
