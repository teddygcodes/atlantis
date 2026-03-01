"""Takeoff-only model router — self-contained, no core/ dependency.

Slim extraction from core/models.py with only the takeoff task types
and routing logic needed for the adversarial pipeline.
"""

import logging
import os
from typing import Optional

from takeoff.llm import LLMProvider, LLMResponse
from takeoff.settings import MODEL_ALLOCATION, MODEL_IDS, API_CONFIG

logger = logging.getLogger(__name__)

# ─── Task-specific temperatures ───────────────────────────────────────────────

TASK_TEMPERATURES = {
    "takeoff_counter": 0.3,
    "takeoff_checker": 0.5,
    "takeoff_reconciler": 0.3,
    "takeoff_judge": 0.2,
    "takeoff_test": 0.0,
}


class ModelRouter:
    """Routes takeoff tasks to the appropriate model and temperature."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._provider = LLMProvider(api_key=self.api_key, mode="api")

        # Stats
        self._total_calls = 0
        self._total_cost_usd = 0.0

    def _get_model_for_task(self, task_type: str) -> str:
        """Get the model ID for a given task type."""
        tier = MODEL_ALLOCATION.get(task_type, "sonnet")
        return MODEL_IDS.get(tier, MODEL_IDS["sonnet"])

    def _get_temperature_for_task(self, task_type: str) -> float:
        """Get the temperature for a given task type."""
        return TASK_TEMPERATURES.get(task_type, API_CONFIG.get("temperature", 0.4))

    def complete(
        self,
        task_type: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """Route a completion request to the appropriate model.

        Args:
            task_type: The takeoff task type (e.g. "takeoff_counter")
            system_prompt: System message
            user_prompt: User message
            max_tokens: Maximum tokens to generate
            temperature: Override temperature (uses task default if None)

        Returns:
            LLMResponse with the completion
        """
        model = self._get_model_for_task(task_type)
        temp = temperature if temperature is not None else self._get_temperature_for_task(task_type)

        response = self._provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temp,
            model=model,
            task_type=task_type,
        )

        self._total_calls += 1
        self._total_cost_usd += response.cost_usd

        return response

    def get_stats(self) -> dict:
        """Return model router statistics."""
        return {
            "model_router_calls": self._total_calls,
            "model_router_cost_usd": round(self._total_cost_usd, 6),
            "provider_calls": self._provider.call_count,
            "provider_cost_usd": round(self._provider.total_cost_usd, 6),
            "provider_input_tokens": self._provider.total_input_tokens,
            "provider_output_tokens": self._provider.total_output_tokens,
        }
