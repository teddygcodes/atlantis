# Model Routing

## Task-to-Model Allocation

Atlantis routes different tasks to different Claude models based on complexity and cost:

| Task Type | Model | Why | Cost/1M Input | Cost/1M Output |
|-----------|-------|-----|---------------|----------------|
| **normalization** | Haiku 4.5 | Structured extraction, cheap | $0.80 | $4.00 |
| **premise_decomposition** | Haiku 4.5 | Simple decomposition | $0.80 | $4.00 |
| **rebuttal_newness** | Haiku 4.5 | Binary check (new reasoning?) | $0.80 | $4.00 |
| **anti_loop** | Haiku 4.5 | Detect repetition | $0.80 | $4.00 |
| **reclassification** | Haiku 4.5 | Discovery → Foundation check | $0.80 | $4.00 |
| **bridge_extraction** | Haiku 4.5 | Cross-domain keyword matching | $0.80 | $4.00 |
| **content_generation** | Haiku 4.5 | Blog/news/dispatch writing | $0.80 | $4.00 |
| **science_gate** | Haiku 4.5 | Numeric assertion scan | $0.80 | $4.00 |
| **researcher_claims** | Sonnet 4.5 | Needs reasoning quality | $3.00 | $15.00 |
| **critic_challenges** | Sonnet 4.5 | Attack must be precise | $3.00 | $15.00 |
| **researcher_rebuttals** | Sonnet 4.5 | Defense requires depth | $3.00 | $15.00 |
| **judge** | Sonnet 4.5 | Highest stakes evaluation | $3.00 | $15.00 |
| **court_judges** | Sonnet 4.5 | Appeal review | $3.00 | $15.00 |
| **founder_panels** | Sonnet 4.5 | Tier advancement evaluation | $3.00 | $15.00 |
| **federal_lab** | Sonnet 4.5 | Radical hypothesis generation | $3.00 | $15.00 |
| **founder_research** | Haiku 4.5 | Phase 0 free-form deposits | $0.80 | $4.00 |

## Model Capabilities

### Claude Haiku 4.5
- **Speed:** ~1s per call
- **Use case:** Structured extraction, binary checks, content generation
- **Strengths:** Fast, cheap, reliable for templated tasks
- **Limits:** Max 4096 tokens output (fine for normalization)

**Example tasks:**
- Extract `{hypothesis, steps, citations, keywords}` from raw claim
- Check if rebuttal introduces new reasoning (yes/no)
- Detect if last 3 claims repeat same argument
- Generate 500-word blog post from exchange

### Claude Sonnet 4.5
- **Speed:** ~4-6s per call
- **Use case:** Research, challenges, rebuttals, judging
- **Strengths:** Strong reasoning, nuanced evaluation, depth
- **Limits:** More expensive, slower than Haiku

**Example tasks:**
- Produce 1500-token research hypothesis with 5-step reasoning chain
- Attack rival's claim by targeting specific logical flaw
- Defend claim with novel counter-evidence
- Judge exchange: survived/partial/destroyed + drama/novelty/depth scores

### Claude Opus 4.6
- **Speed:** ~8-12s per call
- **Use case:** Supreme Court appeals (future feature)
- **Strengths:** Highest reasoning quality, unanimous panel decisions
- **Limits:** Most expensive, rarely used

**When Opus activates:**
- Supreme Court appeals (3 judges, unanimous to overturn)
- Currently not implemented in v2.2

## Cost Optimization Strategy

### Principle: Use cheapest model that can accomplish the task

**Bad:** Use Sonnet for all tasks
```
100 calls × $3.00 input = $300 (unnecessary)
```

**Good:** Route by complexity
```
60 Haiku calls × $0.80 = $48
40 Sonnet calls × $3.00 = $120
Total: $168 (44% savings)
```

### Phase 0 Optimization (v2.2)

**Before:**
```
Phase 0: 100 Sonnet calls × 4-6s each = 8-10 minutes
Cost: ~$0.30
```

**After:**
```
Phase 0: 100 Haiku calls × ~1s each = ~2 minutes
Cost: ~$0.002
```

**Change:**
```python
# config/settings.py
MODEL_ALLOCATION = {
    "founder_research": "haiku",  # was: "researcher_claims" (Sonnet)
}
```

**Result:** 150x cost reduction, 5x speed improvement for Phase 0

### Per-Cycle Cost Breakdown (10 rival pairs)

**Assumptions:**
- 10 pairs × 2 claims = 20 claims per cycle
- Each claim: 1500 input tokens, 800 output tokens
- Each exchange: normalization + decomposition + challenge + rebuttal + judge

**Haiku costs:**
```
20 normalizations × (1500 input + 600 output) = $0.10
20 decompositions × (1500 input + 500 output) = $0.09
20 newness checks × (1000 input + 200 output) = $0.02
20 anti-loop checks × (1200 input + 200 output) = $0.02
Total Haiku: $0.23/cycle
```

**Sonnet costs:**
```
20 researcher claims × (1000 input + 1500 output) = $0.36
20 critic challenges × (2000 input + 800 output) = $0.18
20 researcher rebuttals × (2500 input + 800 output) = $0.19
20 judge rulings × (3500 input + 600 output) = $0.29
Total Sonnet: $1.02/cycle
```

**Total per cycle:** $1.25
**3 cycles:** $3.75
**Actual first run (Phases 0-2):** $2.49 (below estimate due to fewer calls)

## Model Router Implementation

**`core/models.py`:**
```python
class ModelRouter:
    def __init__(self, api_key: str, mock_mode: bool = False):
        self._clients: dict[str, LLMProvider] = {}

    def get(self, task_type: str) -> LLMProvider:
        """Return LLMProvider for given task type."""
        model_tier = MODEL_ALLOCATION.get(task_type, "sonnet")
        return self._get_client(model_tier)

    def _get_client(self, tier: str) -> LLMProvider:
        if tier not in self._clients:
            model_id = {
                "haiku": "claude-haiku-4-5-20251001",
                "sonnet": "claude-sonnet-4-5-20250929",
                "opus": "claude-opus-4-6",
            }[tier]
            self._clients[tier] = LLMProvider(model=model_id)
        return self._clients[tier]

    def complete(self, task_type: str, system_prompt: str, user_prompt: str, max_tokens: int):
        """Route to appropriate model based on task_type."""
        llm = self.get(task_type)
        return llm.complete(system_prompt, user_prompt, max_tokens)
```

**Usage:**
```python
# Automatically routes to Haiku
response = self.models.complete(
    task_type="normalization",
    system_prompt="Extract fields from claim",
    user_prompt=claim_text,
    max_tokens=600,
)

# Automatically routes to Sonnet
response = self.models.complete(
    task_type="researcher_claims",
    system_prompt=researcher_config.system_prompt,
    user_prompt=research_context,
    max_tokens=2500,
)
```

## Swapping Models

To change model allocation, edit **one location**:

```python
# config/settings.py
MODEL_ALLOCATION = {
    "judge": "opus",  # Upgrade judge from Sonnet to Opus
}
```

**No code changes needed.** ModelRouter reads this config at runtime.

## Mock Mode (Zero Cost Testing)

For development/testing without API calls:

```bash
python3 __main__.py --mock
```

**`core/llm.py`:**
```python
class LLMProvider:
    def __init__(self, api_key: str, mock_mode: bool = False):
        self.mock = mock_mode

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int):
        if self.mock:
            return LLMResponse(
                content="MOCK: This is a fake response for testing",
                input_tokens=100,
                output_tokens=50,
            )
        # Real API call
        ...
```

**Use case:** Test pipeline logic without spending API credits.

## Cost Tracking

**`core/llm.py`:**
```python
def calculate_cost(self, response) -> float:
    rates = self.cost_rates.get(response.model)
    if not rates:
        return 0.0
    input_cost = (response.usage.input_tokens / 1_000_000) * rates["input"]
    output_cost = (response.usage.output_tokens / 1_000_000) * rates["output"]
    return input_cost + output_cost
```

**Tracked per call:**
- Input tokens × input rate
- Output tokens × output rate
- Running total in `self.total_cost_usd`

**Exported to:**
```json
// runs/<timestamp>/cost_summary.json
{
  "total_cost_usd": 2.49,
  "by_model": {
    "claude-haiku-4-5-20251001": 0.23,
    "claude-sonnet-4-5-20250929": 2.26
  },
  "by_task": {
    "researcher_claims": 0.89,
    "judge": 0.67,
    "critic_challenges": 0.42,
    ...
  }
}
```

## Future Optimizations

### Multi-model judging (v3.0)
Instead of single Sonnet judge:
```python
JUDGE_MODEL = "multi"  # Claude + GPT-4 + Gemini
```

- 3 independent judges vote
- Majority ruling wins
- Reduces single-model bias
- Cost: 3x judge calls (~$0.90/cycle vs $0.30)

### Prompt caching (built-in)
LLMProvider already implements 15-minute cache:
```python
def _cache_key(self, system: str, user: str, model: str) -> str:
    system_hash = hashlib.md5(system.encode()).hexdigest()
    user_hash = hashlib.md5(user.encode()).hexdigest()
    return f"{model}:{system_hash}:{user_hash}"
```

**Benefit:** Identical prompts within 15 minutes = instant response, zero cost

### Batch processing (future)
Anthropic Batch API (50% discount, 24-hour delivery):
- Generate all 20 researcher claims in batch
- Process overnight
- Sacrifice real-time for 50% savings
- Best for non-interactive runs (archive building)
