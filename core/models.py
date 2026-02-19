"""
Atlantis V2 — Model Router
===========================
Maps task types to appropriate model IDs and temperatures.
Single config point: change MODEL_ALLOCATION in settings.py to swap models.

All model calls go through ModelRouter.complete() so model selection
is centralized and swappable without touching agent code.
"""

from typing import Optional
from core.llm import LLMProvider, LLMResponse
from config.settings import MODEL_ALLOCATION, MODEL_IDS, API_CONFIG


class ModelRouter:
    """
    Routes task types to appropriate LLM model + temperature.
    Wraps a single LLMProvider (shared rate limiting, caching, cost tracking).
    """

    # Per-task temperatures
    TASK_TEMPERATURES = {
        # Zero temp for deterministic structured extraction
        "normalization": 0.0,
        "premise_decomposition": 0.0,
        "rebuttal_newness": 0.0,
        "anti_loop": 0.0,
        "reclassification": 0.0,
        "bridge_extraction": 0.0,
        # Low temp for consistent judging
        "judge": 0.2,
        "court_judges": 0.3,
        "founder_panels": 0.3,
        # Standard research temp
        "researcher_claims": 0.7,
        "critic_challenges": 0.7,
        "researcher_rebuttals": 0.7,
        "federal_lab": 0.7,
        # Higher temp for creative content
        "content_generation": 0.8,
    }

    # Approximate Anthropic prices (USD / 1M tokens)
    MODEL_PRICING = {
        "haiku": {"input": 0.25, "output": 1.25},
        "sonnet": {"input": 3.00, "output": 15.00},
        "opus": {"input": 15.00, "output": 75.00},
    }

    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False, dry_run: bool = False):
        mode = "local" if mock_mode else ("dry-run" if dry_run else "auto")
        self._provider = LLMProvider(api_key=api_key, mode=mode)
        self._mock_mode = mock_mode
        self._cost_by_model_tier = {
            tier: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
            for tier in self.MODEL_PRICING
        }

    @classmethod
    def validate_model_allocation(cls) -> list[dict]:
        """Return model allocation validation records for each task type."""
        known_models = set(MODEL_IDS.values())
        validation = []
        for task_type, tier in sorted(MODEL_ALLOCATION.items()):
            model_id = MODEL_IDS.get(tier)
            is_valid = bool(model_id and model_id in known_models and model_id.startswith("claude-"))
            validation.append(
                {
                    "task_type": task_type,
                    "tier": tier,
                    "model_id": model_id,
                    "valid": is_valid,
                }
            )
        return validation

    def complete(
        self,
        task_type: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """
        Make an LLM call for the given task type.
        Automatically selects the right model and temperature.
        """
        model_tier = MODEL_ALLOCATION.get(task_type, "sonnet")
        model_id = MODEL_IDS.get(model_tier, MODEL_IDS["sonnet"])
        temperature = self.TASK_TEMPERATURES.get(task_type, API_CONFIG["temperature_research"])

        response = self._provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model_id,
        )

        pricing = self.MODEL_PRICING.get(model_tier)
        if pricing:
            input_cost = (response.input_tokens / 1_000_000) * pricing["input"]
            output_cost = (response.output_tokens / 1_000_000) * pricing["output"]
            bucket = self._cost_by_model_tier[model_tier]
            bucket["calls"] += 1
            bucket["input_tokens"] += response.input_tokens
            bucket["output_tokens"] += response.output_tokens
            bucket["cost_usd"] += input_cost + output_cost

        return response

    def get_stats(self) -> dict:
        """Return LLM usage stats (tokens, cost, cache hits, etc.)."""
        stats = self._provider.get_stats()
        total_cost = 0.0
        cost_by_model = {}
        for tier, values in self._cost_by_model_tier.items():
            cost_by_model[tier] = {
                **values,
                "cost_usd": round(values["cost_usd"], 6),
            }
            total_cost += values["cost_usd"]
        stats["model_router_cost_usd"] = round(total_cost, 6)
        stats["cost_by_model_tier"] = cost_by_model
        return stats

    def print_cost_summary(self):
        """Print per-model and total estimated cost summary."""
        stats = self.get_stats()
        print("\n  ModelRouter Cost Summary")
        print("  " + "-" * 48)
        for tier, values in stats["cost_by_model_tier"].items():
            print(
                f"  {tier:<6} calls={values['calls']:<4} "
                f"in={values['input_tokens']:<8} out={values['output_tokens']:<8} "
                f"cost=${values['cost_usd']:.6f}"
            )
        print(f"  TOTAL estimated cost: ${stats['model_router_cost_usd']:.6f}")

    @property
    def is_mock(self) -> bool:
        return self._mock_mode
