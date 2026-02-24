"""Evidence Pack construction and citation verification."""

import asyncio
import aiohttp
import hashlib
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from bs4 import BeautifulSoup
import warnings
import urllib3

from sydyn.search import WebSearch, SearchResult, score_source, estimate_domain_authority, is_paywall_or_blocked

# Suppress SSL warnings for research use case
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
try:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except AttributeError:
    pass  # urllib3 might not have this in some versions


def extract_json_from_llm(response_text: str) -> dict:
    """Extract and parse JSON from LLM response with fallback strategies.

    Args:
        response_text: Raw LLM response

    Returns:
        Parsed JSON dict

    Raises:
        json.JSONDecodeError: If all parsing strategies fail
    """
    # Strategy 1: Try direct parsing
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code fences
    fence_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Extract from first { to last }
    first_brace = response_text.find('{')
    last_brace = response_text.rfind('}')

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(response_text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    # All strategies failed
    raise json.JSONDecodeError("Could not extract valid JSON", response_text, 0)


@dataclass
class Source:
    """Processed source with text content."""
    source_id: str
    url: str
    title: str
    snippet: str
    text_content: str
    credibility_score: float
    fetch_failed: bool = False
    error: Optional[str] = None


@dataclass
class EvidencePack:
    """Complete evidence pack for a query."""
    query: str
    sources: List[Source]
    total_searched: int
    fetch_success_rate: float
    sufficient_evidence: bool


class CitationGrade:
    """Citation verification grades."""
    DIRECT_SUPPORT = "DIRECT_SUPPORT"
    INDIRECT_SUPPORT = "INDIRECT_SUPPORT"
    TANGENTIAL = "TANGENTIAL"
    CONTRADICTS = "CONTRADICTS"
    UNVERIFIABLE = "UNVERIFIABLE"
    FAILED_TO_VERIFY = "FAILED_TO_VERIFY"


async def fetch_source_content(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 5
) -> Tuple[bool, str]:
    """Fetch and extract main text content from URL.

    Args:
        session: aiohttp session
        url: URL to fetch
        timeout: Timeout in seconds (default: 5s)

    Returns:
        (success, content) tuple
    """
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=timeout),
            headers={"User-Agent": "Mozilla/5.0 (compatible; Sydyn/1.0; +https://github.com/anthropics/atlantis)"},
            ssl=False  # Disable SSL verification for research use case
        ) as response:
            if response.status != 200:
                return False, f"HTTP {response.status}"

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            # Remove script, style, nav, footer elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # Extract text from paragraphs and main content
            text_parts = []

            # Try to find main content container
            main_content = soup.find("main") or soup.find("article") or soup.find("body")

            if main_content:
                # Extract all paragraph text
                paragraphs = main_content.find_all("p")
                text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]

            # Fallback to all text if no paragraphs found
            if not text_parts:
                text_parts = [main_content.get_text(strip=True)] if main_content else []

            content = " ".join(text_parts)

            # Limit content length (first 10k chars)
            content = content[:10000]

            return True, content

    except asyncio.TimeoutError:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def fetch_source_content_sync(url: str, timeout: int = 5) -> Tuple[bool, str]:
    """Fallback synchronous fetch using requests library.

    Args:
        url: URL to fetch
        timeout: Timeout in seconds

    Returns:
        (success, content) tuple
    """
    try:
        import requests

        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Sydyn/1.0; +https://github.com/anthropics/atlantis)"},
            verify=False  # Disable SSL verification
        )

        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Remove script, style, nav, footer elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Extract text from paragraphs and main content
        text_parts = []
        main_content = soup.find("main") or soup.find("article") or soup.find("body")

        if main_content:
            paragraphs = main_content.find_all("p")
            text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]

        if not text_parts:
            text_parts = [main_content.get_text(strip=True)] if main_content else []

        content = " ".join(text_parts)
        content = content[:10000]  # Limit to 10k chars

        return True, content

    except Exception as e:
        return False, f"Requests fallback failed: {e}"


async def fetch_sources_parallel(
    search_results: List[SearchResult],
    max_sources: int = 8
) -> List[Source]:
    """Fetch multiple sources in parallel.

    Args:
        search_results: Search results to fetch
        max_sources: Maximum number of sources to fetch

    Returns:
        List of Source objects
    """
    sources = []

    async with aiohttp.ClientSession() as session:
        tasks = []

        for result in search_results[:max_sources]:
            source_id = hashlib.md5(result.url.encode()).hexdigest()[:12]
            tasks.append((result, fetch_source_content(session, result.url)))

        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)

        for (result, _), fetch_result in zip(tasks, results):
            source_id = hashlib.md5(result.url.encode()).hexdigest()[:12]

            if isinstance(fetch_result, Exception):
                error_msg = f"{type(fetch_result).__name__}: {fetch_result}"
                print(f"[EVIDENCE] ✗ {result.url[:60]}: {error_msg}")
                sources.append(Source(
                    source_id=source_id,
                    url=result.url,
                    title=result.title,
                    snippet=result.snippet,
                    text_content="",
                    credibility_score=0.0,
                    fetch_failed=True,
                    error=error_msg
                ))
            else:
                success, content = fetch_result

                if success:
                    print(f"[EVIDENCE] ✓ {result.url[:60]} ({len(content)} chars)")
                    # Calculate credibility score
                    domain_authority = estimate_domain_authority(result.url)
                    freshness = 0.8  # Default freshness (can enhance with date parsing)
                    relevance = result.score if result.score > 0 else 0.5

                    credibility = score_source(result, domain_authority, freshness, relevance)

                    sources.append(Source(
                        source_id=source_id,
                        url=result.url,
                        title=result.title,
                        snippet=result.snippet,
                        text_content=content,
                        credibility_score=credibility,
                        fetch_failed=False
                    ))
                else:
                    print(f"[EVIDENCE] ✗ {result.url[:60]}: {content}")
                    sources.append(Source(
                        source_id=source_id,
                        url=result.url,
                        title=result.title,
                        snippet=result.snippet,
                        text_content="",
                        credibility_score=0.0,
                        fetch_failed=True,
                        error=content
                    ))

    # Retry failed sources with synchronous requests fallback
    successful_fetches = [s for s in sources if not s.fetch_failed]
    failed_sources = [s for s in sources if s.fetch_failed]

    if failed_sources and len(successful_fetches) < 3:
        print(f"[EVIDENCE] Retrying {len(failed_sources)} failed sources with requests fallback...")

        for source in failed_sources:
            success, content = fetch_source_content_sync(source.url)

            if success:
                print(f"[EVIDENCE] ✓ Fallback succeeded for {source.url[:60]}")
                # Update source object
                source.fetch_failed = False
                source.text_content = content
                source.error = None

                # Recalculate credibility
                domain_authority = estimate_domain_authority(source.url)
                freshness = 0.8
                relevance = 0.5

                # Create a temporary SearchResult for scoring
                temp_result = SearchResult(
                    url=source.url,
                    title=source.title,
                    snippet=source.snippet,
                    score=0.5
                )
                source.credibility_score = score_source(
                    temp_result,
                    domain_authority,
                    freshness,
                    relevance
                )
            else:
                print(f"[EVIDENCE] ✗ Fallback failed for {source.url[:60]}: {content}")

    return sources


def build_evidence_pack(query: str, search_provider: str = "tavily") -> EvidencePack:
    """Construct Evidence Pack from query.

    Steps:
    1. Search - Execute web search
    2. Filter - Remove paywalls, dead links
    3. Score - Rank by relevance
    4. Fetch - Parallel fetch top sources
    5. Extract - Pull main text

    Args:
        query: User query text
        search_provider: "tavily" or "serper"

    Returns:
        EvidencePack with sources and metadata
    """
    print(f"[EVIDENCE] Building Evidence Pack for query: {query}")

    # Step 1: Search
    searcher = WebSearch(provider=search_provider)
    search_results = searcher.search(query, max_results=20)

    if not search_results:
        print("[EVIDENCE] No search results found")
        return EvidencePack(
            query=query,
            sources=[],
            total_searched=0,
            fetch_success_rate=0.0,
            sufficient_evidence=False
        )

    print(f"[EVIDENCE] Found {len(search_results)} search results")

    # Step 2: Filter - Remove paywalls and low-quality sources
    filtered_results = [
        r for r in search_results
        if not is_paywall_or_blocked(r.url)
    ]

    print(f"[EVIDENCE] {len(filtered_results)} results after filtering")

    # Step 3: Score - Already scored by search API, but we can re-rank if needed
    # For v1, trust the search API ordering

    # Step 4 & 5: Fetch and Extract in parallel
    sources = asyncio.run(fetch_sources_parallel(filtered_results, max_sources=8))

    successful_fetches = [s for s in sources if not s.fetch_failed]
    fetch_success_rate = len(successful_fetches) / len(sources) if sources else 0.0

    print(f"[EVIDENCE] Fetched {len(successful_fetches)}/{len(sources)} sources successfully")

    # Determine if we have sufficient evidence
    sufficient = len(successful_fetches) >= 3

    if not sufficient:
        print("[EVIDENCE] WARNING: Insufficient evidence (< 3 sources fetched)")

    return EvidencePack(
        query=query,
        sources=sources,
        total_searched=len(search_results),
        fetch_success_rate=fetch_success_rate,
        sufficient_evidence=sufficient
    )


def verify_citation(
    claim_text: str,
    source: Source,
    llm_function
) -> Tuple[str, str]:
    """Verify if source supports claim.

    Args:
        claim_text: Claim to verify
        source: Source to check against
        llm_function: LLM function to call for verification

    Returns:
        (grade, explanation) tuple
    """
    if source.fetch_failed:
        return CitationGrade.FAILED_TO_VERIFY, f"Source fetch failed: {source.error}"

    if not source.text_content:
        return CitationGrade.FAILED_TO_VERIFY, "Source has no content"

    # Use LLM to grade citation
    prompt = f"""Verify if this source supports the claim.

CLAIM:
{claim_text}

SOURCE URL: {source.url}
SOURCE TITLE: {source.title}

SOURCE CONTENT:
{source.text_content[:3000]}

Grade the citation using ONE of these grades:
- DIRECT_SUPPORT: Source explicitly states the claim
- INDIRECT_SUPPORT: Source supports claim via logical inference
- TANGENTIAL: Source mentions topic but doesn't support claim
- CONTRADICTS: Source contradicts the claim
- UNVERIFIABLE: Claim not addressed in source

CRITICAL: Respond with ONLY a valid JSON object. No markdown code fences. No explanation before or after. Just the raw JSON.

Output format:
{{
  "grade": "<grade>",
  "explanation": "<brief explanation>"
}}"""

    try:
        response = llm_function(
            prompt=prompt,
            task_type="sydyn_verify_citations",
            temperature=0.3
        )

        # Parse JSON response with fallback strategies
        data = extract_json_from_llm(response)
        grade = data.get("grade", CitationGrade.UNVERIFIABLE)
        explanation = data.get("explanation", "")

        return grade, explanation

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[EVIDENCE] ERROR: Citation verification JSON parse failed: {e}")
        print(f"[EVIDENCE] Response preview: {response[:200] if isinstance(response, str) else str(response)[:200]}...")
        return CitationGrade.FAILED_TO_VERIFY, f"Verification error: {e}"
    except Exception as e:
        print(f"[EVIDENCE] ERROR: Citation verification failed: {e}")
        return CitationGrade.FAILED_TO_VERIFY, f"Verification error: {e}"


def verify_all_citations(
    claims: List[Dict],
    sources: List[Source],
    llm_function
) -> Dict[str, Dict[str, Tuple[str, str]]]:
    """Verify all claim-source pairs.

    Args:
        claims: List of claim dicts with claim_id and text
        sources: List of Source objects
        llm_function: LLM function to call

    Returns:
        Dict mapping claim_id -> {source_id -> (grade, explanation)}
    """
    print(f"[EVIDENCE] Verifying citations for {len(claims)} claims against {len(sources)} sources")

    results = {}

    for claim in claims:
        claim_id = claim.get("claim_id")
        claim_text = claim.get("text")
        claim_citations = claim.get("citations", [])

        results[claim_id] = {}

        # Only verify claimed citations
        for source_id in claim_citations:
            source = next((s for s in sources if s.source_id == source_id), None)

            if source:
                grade, explanation = verify_citation(claim_text, source, llm_function)
                results[claim_id][source_id] = (grade, explanation)
                print(f"[EVIDENCE] {claim_id} <- {source_id}: {grade}")
            else:
                results[claim_id][source_id] = (
                    CitationGrade.FAILED_TO_VERIFY,
                    f"Source {source_id} not found in Evidence Pack"
                )

    return results


def calculate_source_diversity(claims: List[Dict], sources: List[Source]) -> int:
    """Calculate number of unique domains citing claims.

    Args:
        claims: List of claim dicts
        sources: List of Source objects

    Returns:
        Number of unique domains
    """
    cited_domains = set()

    for claim in claims:
        for source_id in claim.get("citations", []):
            source = next((s for s in sources if s.source_id == source_id), None)
            if source and not source.fetch_failed:
                # Extract domain from URL
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(source.url).netloc
                    cited_domains.add(domain)
                except Exception:
                    pass

    return len(cited_domains)
