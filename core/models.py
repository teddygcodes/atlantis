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

    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        mode = "local" if mock_mode else "auto"
        self._provider = LLMProvider(api_key=api_key, mode=mode)
        self._mock_mode = mock_mode

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

        return self._provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model_id,
        )

    def get_stats(self) -> dict:
        """Return LLM usage stats (tokens, cost, cache hits, etc.)."""
        return self._provider.get_stats()

    @property
    def is_mock(self) -> bool:
        return self._mock_mode
