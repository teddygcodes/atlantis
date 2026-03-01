"""Query classification for mode selection (fast | strict | liability)."""

import json
from typing import Optional

from sydyn.constitution import MEDICAL_KEYWORDS, LEGAL_KEYWORDS


# Keywords for fast mode (factual lookups)
FAST_MODE_PATTERNS = [
    "what is",
    "what are",
    "when did",
    "when was",
    "where is",
    "where was",
    "how many",
    "how much",
    "who is",
    "who was",
    "define",
    "definition of"
]

# Keywords for strict mode (contested/controversial)
STRICT_MODE_KEYWORDS = [
    "why", "how come", "explain why",
    "compare", "versus", "vs", "better than",
    "should", "controversial", "debate",
    "argue", "criticism", "critics say"
]

# Keywords for liability mode (high stakes)
LIABILITY_KEYWORDS = [
    "should i", "can i", "invest", "investment",
    "diagnose", "treatment", "medication",
    "legal advice", "lawsuit", "contract"
]


def classify_query_keyword(query: str) -> str:
    """Classify query using keyword matching.

    Args:
        query: User query text

    Returns:
        Mode: "fast" | "strict" | "liability" | "unknown"
    """
    query_lower = query.lower()

    # Check liability keywords first (highest priority)
    for keyword in LIABILITY_KEYWORDS:
        if keyword in query_lower:
            return "liability"

    # Check for medical/legal queries
    if any(kw in query_lower for kw in MEDICAL_KEYWORDS):
        return "liability"

    if any(kw in query_lower for kw in LEGAL_KEYWORDS):
        return "liability"

    # Check strict mode keywords
    if any(kw in query_lower for kw in STRICT_MODE_KEYWORDS):
        return "strict"

    # Check fast mode patterns
    for pattern in FAST_MODE_PATTERNS:
        if query_lower.startswith(pattern):
            return "fast"

    return "unknown"


def classify_query_llm(query: str, model_router) -> str:
    """Classify query using LLM fallback.

    Args:
        query: User query text
        model_router: ModelRouter instance

    Returns:
        Mode: "fast" | "strict" | "liability"
    """
    system_prompt = """You are a query classifier for Sydyn's adversarial search system.

Classify the query into one of three modes:

FAST MODE:
- Simple factual lookups: "What is X?", "When did Y happen?", "How many Z?"
- Clear, uncontested questions with objective answers
- Examples: "What is the capital of France?", "When did WWII end?"

STRICT MODE:
- Questions requiring nuance or analysis: "Why did X happen?", "Compare X and Y"
- Contested or controversial topics: "Is X better than Y?"
- Questions where reasonable people disagree
- Examples: "Why did the Roman Empire fall?", "Is nuclear energy safe?"

LIABILITY MODE:
- Medical questions: diagnosis, treatment, health advice
- Legal questions: contracts, lawsuits, legal advice
- Financial advice: investment decisions, "should I invest"
- Safety-critical decisions
- Examples: "Should I take aspirin?", "Can I sue for X?", "Should I invest in Y?"

Output format (JSON):
{
  "mode": "fast" | "strict" | "liability",
  "reasoning": "<brief explanation>"
}"""

    user_prompt = f"""Query: {query}

Classify this query into fast, strict, or liability mode."""

    try:
        response = model_router.complete(
            task_type="sydyn_query_classifier",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=200
        )

        data = json.loads(response.content)
        mode = data.get("mode", "fast")

        # Validate mode
        if mode not in ["fast", "strict", "liability"]:
            print(f"[CLASSIFIER] Invalid mode '{mode}' from LLM, defaulting to fast")
            return "fast"

        return mode

    except Exception as e:
        print(f"[CLASSIFIER] LLM classification failed: {e}, defaulting to fast")
        return "fast"


def classify_query(
    query: str,
    model_router,
    override_mode: Optional[str] = None
) -> str:
    """Classify query using keyword matching + LLM fallback.

    Args:
        query: User query text
        model_router: ModelRouter instance
        override_mode: Optional user-specified mode

    Returns:
        Mode: "fast" | "strict" | "liability"
    """
    # If user specified mode, use it
    if override_mode:
        if override_mode in ["fast", "strict", "liability"]:
            print(f"[CLASSIFIER] Using user-specified mode: {override_mode}")
            return override_mode
        else:
            print(f"[CLASSIFIER] Invalid override mode '{override_mode}', ignoring")

    # Try keyword matching first
    keyword_mode = classify_query_keyword(query)

    if keyword_mode != "unknown":
        print(f"[CLASSIFIER] Keyword match: {keyword_mode}")
        return keyword_mode

    # Fallback to LLM classification
    print(f"[CLASSIFIER] No keyword match, using LLM fallback")
    llm_mode = classify_query_llm(query, model_router)

    print(f"[CLASSIFIER] LLM classification: {llm_mode}")
    return llm_mode
