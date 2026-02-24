"""Web search wrapper for Tavily and Serper APIs."""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import requests


@dataclass
class SearchResult:
    """Single search result."""
    url: str
    title: str
    snippet: str
    score: float = 0.0  # Relevance score from search API


class WebSearch:
    """Web search interface supporting multiple APIs."""

    def __init__(self, provider: str = "tavily"):
        """Initialize search provider.

        Args:
            provider: "tavily" or "serper"
        """
        self.provider = provider.lower()

        if self.provider == "tavily":
            self.api_key = os.getenv("TAVILY_API_KEY")
            if not self.api_key:
                raise ValueError("TAVILY_API_KEY environment variable not set")
            self.endpoint = "https://api.tavily.com/search"

        elif self.provider == "serper":
            self.api_key = os.getenv("SERPER_API_KEY")
            if not self.api_key:
                raise ValueError("SERPER_API_KEY environment variable not set")
            self.endpoint = "https://google.serper.dev/search"

        else:
            raise ValueError(f"Unsupported search provider: {provider}")

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        """Execute web search and return results.

        Args:
            query: Search query text
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        try:
            if self.provider == "tavily":
                return self._search_tavily(query, max_results)
            elif self.provider == "serper":
                return self._search_serper(query, max_results)
            else:
                return []
        except Exception as e:
            print(f"[SEARCH] Error during web search: {e}")
            return []

    def _search_tavily(self, query: str, max_results: int) -> List[SearchResult]:
        """Execute Tavily search."""
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("results", []):
            results.append(SearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                snippet=item.get("content", ""),
                score=item.get("score", 0.5)
            ))

        return results

    def _search_serper(self, query: str, max_results: int) -> List[SearchResult]:
        """Execute Serper (Google) search."""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": max_results
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        results = []

        # Serper returns both "organic" and "knowledgeGraph" results
        for item in data.get("organic", []):
            results.append(SearchResult(
                url=item.get("link", ""),
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                score=0.5  # Serper doesn't provide relevance scores
            ))

        return results


def score_source(
    result: SearchResult,
    domain_authority: float,
    freshness: float,
    relevance: float
) -> float:
    """Calculate composite score for a search result.

    Args:
        result: Search result to score
        domain_authority: Domain authority score (0-1)
        freshness: Content freshness score (0-1)
        relevance: Query relevance score (0-1)

    Returns:
        Weighted composite score (0-1)
    """
    # Weights from plan: domain authority (0.4) + freshness (0.3) + relevance (0.3)
    weights = {"authority": 0.4, "freshness": 0.3, "relevance": 0.3}

    score = (
        weights["authority"] * domain_authority +
        weights["freshness"] * freshness +
        weights["relevance"] * relevance
    )

    return min(1.0, max(0.0, score))


def estimate_domain_authority(url: str) -> float:
    """Estimate domain authority based on URL.

    Simple heuristic for v1 - can be enhanced with actual domain authority APIs.

    Args:
        url: Source URL

    Returns:
        Authority score (0-1)
    """
    # High-authority domains (can be expanded)
    high_authority = [
        ".gov", ".edu", "wikipedia.org", "britannica.com",
        "nature.com", "science.org", "nih.gov", "cdc.gov",
        "who.int", "un.org", "nist.gov", "ieee.org"
    ]

    # Medium-authority domains
    medium_authority = [
        ".org", "reuters.com", "ap.org", "bbc.com",
        "nytimes.com", "wsj.com", "economist.com"
    ]

    url_lower = url.lower()

    for domain in high_authority:
        if domain in url_lower:
            return 0.9

    for domain in medium_authority:
        if domain in url_lower:
            return 0.7

    # Default to medium-low for unknown domains
    return 0.5


def is_paywall_or_blocked(url: str) -> bool:
    """Check if URL is likely behind paywall or blocked.

    Args:
        url: Source URL

    Returns:
        True if likely blocked/paywalled
    """
    # Common paywalled or problematic domains
    blocked_patterns = [
        "paywalled", "subscription", "login.php",
        "paywall", "subscriber-only"
    ]

    url_lower = url.lower()

    for pattern in blocked_patterns:
        if pattern in url_lower:
            return True

    return False
