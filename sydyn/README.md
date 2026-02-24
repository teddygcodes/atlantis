# Sydyn: Real-Time Adversarial Search System

Sydyn is a real-time adversarial search system powered by Atlantis governance infrastructure. Think of it as "Google + peer review + constitutional law."

## Features

- **Evidence Pack Construction** - Web search + source scoring + parallel fetching
- **4-Agent Pipeline** - Researcher, Adversary, Critic, Judge
- **Citation Verification** - 6-grade system (DIRECT_SUPPORT → FAILED_TO_VERIFY)
- **Feature-Based Confidence** - 7 features with explicit weights (not vibes)
- **Query Classification** - Auto-select fast/strict/liability modes
- **Timeout Handling** - 3 degradation levels (no_critic → no_adversary → evidence_only)
- **Knowledge Base** - 90-day re-validation for cached answers
- **Constitutional Rules** - 6 hard rules + 5 articles

## Installation

```bash
# Install dependencies
pip install beautifulsoup4 aiohttp requests

# Set API key for web search (choose one)
export TAVILY_API_KEY="your_tavily_key"
# OR
export SERPER_API_KEY="your_serper_key"
```

## Usage

### Basic Query

```bash
python -m sydyn "What is the speed of light?"
```

### Override Mode

```bash
# Force strict mode (includes Critic)
python -m sydyn "Why did the Roman Empire fall?" --mode strict

# Force liability mode (stricter thresholds)
python -m sydyn "Should I take aspirin?" --mode liability
```

### JSON Output

```bash
python -m sydyn "What caused COVID-19?" --format json
```

### Save to Knowledge Base

```bash
python -m sydyn "What is the capital of France?" --save-kb
```

### Verbose Mode

```bash
python -m sydyn "Compare nuclear and solar energy" --verbose
```

## Modes

### Fast Mode (DEFAULT)
- **Agents:** Researcher + Adversary + Judge (skip Critic)
- **Latency:** ~30-40s
- **Cost:** ~$0.04-0.06
- **Use for:** Factual lookups, "What is X?", "When did Y happen?"

### Strict Mode
- **Agents:** Researcher + Adversary + Critic + Judge
- **Latency:** ~45-55s
- **Cost:** ~$0.08-0.12
- **Use for:** Contested topics, "Why?", "Compare X and Y"
- **Auto-escalation:** Controversial/complex queries

### Liability Mode
- **Agents:** Same as Strict
- **Latency:** ~50-60s
- **Cost:** ~$0.10-0.15
- **Use for:** Medical, legal, financial advice
- **Auto-escalation:** Safety-critical queries

## Architecture

```
User Query
   ↓
Query Classifier (Haiku) → fast | strict | liability
   ↓
Evidence Pack (web search → filter → score → fetch → extract)
   ↓
Researcher (Haiku) → Initial answer with citations
   ↓
Adversary (Haiku) → Generate attacks
   ↓
Critic (Sonnet) → Address attacks [skipped in fast mode]
   ↓
Citation Verifier (Haiku) → Grade all citations
   ↓
Judge (Sonnet) → Constitutional evaluation
   ↓
Confidence Calculator → Feature-based score (7 features)
   ↓
Answer + Confidence + Violations
```

## Constitution

### 6 Hard Rules (Judge enforces)

1. **No Fabrication** - Claims must have ≥1 DIRECT_SUPPORT or INDIRECT_SUPPORT citation
2. **No Speculation** - Future predictions must be labeled as "speculative"
3. **No Health Advice** - Medical claims trigger DEFER response
4. **No Legal Advice** - Legal claims trigger DEFER response
5. **Cite Partisan Sources** - Political claims from biased sources must acknowledge bias
6. **Source Diversity** - ≥2 unique domains required for any factual claim

### 5 Constitutional Articles (Guidelines)

1. **Truth over Speed** - Accuracy > latency; timeout degrades gracefully
2. **Transparency** - Show confidence features, not just score
3. **Adversarial Testing** - Strict mode must include attacks
4. **Constitutional Supremacy** - Judge has veto power
5. **Knowledge Consolidation** - Validated answers go to KB for reuse

## Confidence Features

```python
base_confidence = 0.5

weights = {
    "direct_support_ratio": 0.25,      # % of DIRECT_SUPPORT citations
    "source_diversity": 0.20,          # Unique domains citing claims
    "adversary_severity": -0.15,       # Penalty for unaddressed attacks
    "constitutional_clean": 0.15,      # No violations = boost
    "evidence_freshness": 0.10,        # Avg source age < 1 year
    "claim_specificity": 0.10,         # Quantified vs vague claims
    "fast_mode_penalty": -0.05         # Fast mode skips critic
}

confidence = clamp(base_confidence + sum(feature * weight), 0.0, 1.0)
```

**Confidence Bands:**
- 0.85-1.0: HIGH
- 0.65-0.84: MODERATE
- 0.40-0.64: LOW
- 0.0-0.39: VERY_LOW

## Timeout Handling

| Elapsed | Degradation | Agents Run | Confidence Penalty |
|---------|-------------|------------|--------------------|
| <60s | None | Full pipeline | 0 |
| 60-75s | Level 1 | Skip Critic | -0.10 |
| 75-90s | Level 2 | Skip Adversary + Critic | -0.15 |
| >90s | Level 3 | Evidence-only response | -0.50 |

## Database Schema

Sydyn stores all query results in `sydyn.db` (SQLite):

- `queries` - Query metadata (mode, latency, cost)
- `answers` - Final answers with confidence
- `claims` - Extracted claims from agents
- `sources` - Source metadata and credibility
- `citation_grades` - Citation verification results
- `attack_log` - Adversary attacks and critic responses
- `kb` - Knowledge base (cached answers)

## Model Allocation

All models use Haiku or Sonnet (no Opus in v1):

- **Query Classifier:** Haiku (2s)
- **Researcher:** Haiku (10s)
- **Adversary:** Haiku (8s)
- **Critic:** Sonnet (15s)
- **Judge:** Sonnet (8-10s)
- **Citation Verifier:** Haiku (8s)

## Cost Targets

- **Fast mode:** <$0.06 per query
- **Strict mode:** <$0.10 per query
- **Liability mode:** <$0.15 per query

## Examples

### Factual Query (Fast Mode)

```bash
$ python -m sydyn "What is the capital of France?"

======================================================================
SYDYN - Real-Time Adversarial Search
======================================================================

Query: What is the capital of France?
Mode: FAST

ANSWER:
----------------------------------------------------------------------
• Paris is the capital of France

CONFIDENCE: 0.92 (HIGH)
- Direct citation support: 100%
- Source diversity: ≥3 domains ✓
- Adversarial review: no attacks
- Constitutional violations: none ✓

✓ VERDICT: PASS (no major constitutional issues)

Completed in 12.3s | Cost: $0.0450

======================================================================
```

### Medical Query (Liability Mode)

```bash
$ python -m sydyn "Should I take aspirin for headaches?"

======================================================================
SYDYN - Real-Time Adversarial Search
======================================================================

Query: Should I take aspirin for headaches?
Mode: LIABILITY

ANSWER:
----------------------------------------------------------------------
[DEFER] This query requests medical advice. Sydyn cannot provide
health recommendations. Please consult a qualified healthcare provider.

CONFIDENCE: 0.00 (VERY_LOW)

CONSTITUTIONAL VIOLATIONS:
----------------------------------------------------------------------
• No Health Advice: Medical query detected - Sydyn cannot provide health advice
  Severity: FATAL

⚠️  VERDICT: BLOCKED (constitutional violations prevent this answer)

Completed in 8.1s | Cost: $0.0200

======================================================================
```

## License

Part of Project Atlantis - see main repo for license.
