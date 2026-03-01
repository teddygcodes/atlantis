# Atlantis Demo Guide

## 1) Atlantis in 60 seconds
Atlantis is a simulation that stress-tests ideas like a competitive civilization of researchers. Instead of accepting one answer, Atlantis makes rival "States" propose claims, challenge each other step-by-step, rebut attacks, and then pass through a judge that scores what survives.

In plain terms: it is a structured "argument engine" for knowledge. You give it a constitutional framework and a run mode, and it produces:
- cycle-by-cycle debate logs,
- an archive of claims,
- domain health metrics (survival and maturity), and
- publication-ready content (blog/newsroom/debate outputs).

The goal is not quiet consensus. The goal is better ideas through adversarial pressure, traceability, and explicit reasoning.

## 2) How to run Atlantis

```bash
git clone <YOUR_REPO_URL>
cd atlantis
export OPENAI_API_KEY="your_api_key_here"
python3 -m atlantis --mock
```

Notes:
- `--mock` runs Atlantis in deterministic/mock mode suitable for demos.
- For this demo build, we also used `--force-clean` to clear prior output artifacts before regenerating.

## 3) Full claim battle excerpt (from cycle logs)
Source: `output/logs/cycle_1.md`, Exchange A (`#061`).

### Claim (with reasoning chain)
```text
CLAIM TYPE: Discovery
POSITION: Philosophy_Alpha Researcher argues adaptive governance needs explicit feedback loops to stay truthful under adversarial pressure.
STEP 1: Systems that publish intermediate reasoning are easier to challenge and therefore self-correct faster.
STEP 2: Rebuttal requirements force states to expose hidden assumptions, reducing silent failure modes.
STEP 3: Cross-citation between rival claims creates a dependency graph that reveals fragile foundations early.
CONCLUSION: Adversarial transparency increases long-run knowledge reliability even when short-run conflict rises.
CITATIONS: []
KEYWORDS: governance, feedback_loops, adversarial_testing, transparency
```

### Challenge (targeted step)
```text
STEP TARGETED: STEP 2
FLAW: The claim assumes rebuttal quality is consistently high, but weak rebuttals can create false confidence instead of correction.
ALTERNATIVE: Reliability improves only when rebuttals add genuinely new reasoning that can be independently tested.
EVIDENCE: Historical policy reviews show iterative debate helps only when counterarguments are specific and evidence-linked.
```

### Rebuttal
```text
OPTION B: I concede that low-quality rebuttals can amplify noise, so the original claim was too broad. Narrowed claim: adversarial transparency improves reliability when rebuttals must introduce testable, non-redundant reasoning and are archived for later dependency audits.
```

### Judge outcome + reasoning
```text
Outcome: partial
Judge reasoning: The challenge identifies a real boundary condition and the rebuttal concedes it while preserving a narrower core claim.
```

### Scores
```text
drama=7, novelty=6, depth=8
```

## 4) Metrics summary (from `domain_health.json`)

| Domain | Surviving | Survival Rate | Compression | Maturity Phase |
|---|---:|---:|---:|---|
| Philosophy of Knowledge | 5 / 11 | 0.455 | 0.2 | Stabilizing Foundation |

## 5) `archive.md` sample (first 3 entries)
From `output/archive.md`:

1. **#001 [FOUNDING]** — Source State: Founding Era, Entity: Hamilton, Claim Type: discovery, Cycle: 1
2. **#002 [FOUNDING]** — Source State: Founding Era, Entity: Jefferson, Claim Type: discovery, Cycle: 1
3. **#003 [FOUNDING]** — Source State: Founding Era, Entity: Franklin, Claim Type: discovery, Cycle: 1

These entries each include full claim text, score block, and citations section.

## 6) What the content system produces
After a run, Atlantis writes content artifacts under `output/content/`:

- `output/content/blog/`
  - Example: `blog_20260219_083805.md`
- `output/content/newsroom/`
  - Example: `newsroom_20260219_083805.md`
- `output/content/debate/`
  - Example: `debate_20260219_083805.md`
- `output/content/blog_context.json`
  - Shared context metadata used by content generation.

In short: one run yields both machine-readable governance outputs and human-readable publication formats.
