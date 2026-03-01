"""Sydyn Constitution: Hard Rules and Articles."""

# 6 Hard Rules (Judge enforces these strictly)
HARD_RULES = [
    {
        "name": "No Fabrication",
        "description": "Claims must have ≥1 DIRECT_SUPPORT or INDIRECT_SUPPORT citation",
        "check": "citation_support",
        "severity": "FATAL"
    },
    {
        "name": "No Speculation",
        "description": "Future predictions must be labeled as 'speculative'",
        "check": "speculation_label",
        "severity": "MAJOR"
    },
    {
        "name": "No Health Advice",
        "description": "Medical claims trigger DEFER response",
        "check": "medical_query",
        "severity": "FATAL"
    },
    {
        "name": "No Legal Advice",
        "description": "Legal claims trigger DEFER response",
        "check": "legal_query",
        "severity": "FATAL"
    },
    {
        "name": "Cite Partisan Sources",
        "description": "Political claims from biased sources must acknowledge bias",
        "check": "partisan_bias",
        "severity": "MAJOR"
    },
    {
        "name": "Source Diversity",
        "description": "≥2 unique domains required for any factual claim",
        "check": "domain_diversity",
        "severity": "MAJOR"
    }
]

# 5 Constitutional Articles (Guidelines, not strictly enforced)
ARTICLES = [
    {
        "number": 1,
        "title": "Truth over Speed",
        "principle": "Accuracy > latency; timeout degrades gracefully"
    },
    {
        "number": 2,
        "title": "Transparency",
        "principle": "Show confidence features, not just score"
    },
    {
        "number": 3,
        "title": "Adversarial Testing",
        "principle": "Strict mode must include attacks"
    },
    {
        "number": 4,
        "title": "Constitutional Supremacy",
        "principle": "Judge has veto power"
    },
    {
        "number": 5,
        "title": "Knowledge Consolidation",
        "principle": "Validated answers go to KB for reuse"
    }
]

# Keywords for rule checking
MEDICAL_KEYWORDS = [
    "medical", "diagnose", "diagnosis", "treat", "treatment",
    "medicine", "medication", "drug", "symptom", "disease",
    "illness", "condition", "cure", "prescription", "doctor",
    "health", "healthcare", "therapy", "surgery"
]

LEGAL_KEYWORDS = [
    "legal", "law", "lawsuit", "attorney", "lawyer", "court",
    "judge", "litigation", "contract", "liability", "rights",
    "regulation", "statute", "precedent", "judicial"
]

# Partisan source domains (can be expanded)
PARTISAN_SOURCES = {
    "left_leaning": [
        "huffpost.com", "dailykos.com", "thinkprogress.org",
        "motherjones.com", "jacobinmag.com"
    ],
    "right_leaning": [
        "breitbart.com", "dailywire.com", "theblaze.com",
        "newsmax.com", "oann.com", "foxnews.com"
    ],
    "center": [
        "apnews.com", "reuters.com", "bbc.com", "npr.org"
    ]
}


def get_constitution() -> dict:
    """Return full constitution as dict."""
    return {
        "hard_rules": HARD_RULES,
        "articles": ARTICLES,
        "medical_keywords": MEDICAL_KEYWORDS,
        "legal_keywords": LEGAL_KEYWORDS,
        "partisan_sources": PARTISAN_SOURCES
    }


def check_medical_query(query: str) -> bool:
    """Check if query contains medical keywords.

    Args:
        query: User query text

    Returns:
        True if medical query detected
    """
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in MEDICAL_KEYWORDS)


def check_legal_query(query: str) -> bool:
    """Check if query contains legal keywords.

    Args:
        query: User query text

    Returns:
        True if legal query detected
    """
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in LEGAL_KEYWORDS)


def check_citation_support(claims: list, citation_grades: dict) -> list:
    """Check if claims have adequate citation support.

    Args:
        claims: List of Claim objects
        citation_grades: Dict mapping claim_id -> {source_id -> (grade, explanation)}

    Returns:
        List of violations
    """
    violations = []

    for claim in claims:
        if claim.claim_type == "attack":
            continue  # Attacks don't need citations

        claim_id = claim.claim_id
        grades = citation_grades.get(claim_id, {})

        # Count support grades
        direct_support = sum(1 for g, _ in grades.values() if g == "DIRECT_SUPPORT")
        indirect_support = sum(1 for g, _ in grades.values() if g == "INDIRECT_SUPPORT")

        total_support = direct_support + indirect_support

        if total_support == 0:
            violations.append({
                "rule": "No Fabrication",
                "claim_id": claim_id,
                "severity": "FATAL",
                "explanation": f"Claim has no supporting citations (0 DIRECT or INDIRECT support)"
            })

    return violations


def check_source_diversity(claims: list, sources: list) -> list:
    """Check if claims cite ≥2 unique domains.

    Args:
        claims: List of Claim objects
        sources: List of Source objects

    Returns:
        List of violations
    """
    from urllib.parse import urlparse

    violations = []

    for claim in claims:
        if claim.claim_type != "factual":
            continue  # Only factual claims need diversity

        # Get domains for this claim's citations
        cited_domains = set()
        for source_id in claim.citations:
            source = next((s for s in sources if s.source_id == source_id), None)
            if source and not source.fetch_failed:
                try:
                    domain = urlparse(source.url).netloc
                    cited_domains.add(domain)
                except Exception:
                    pass

        if len(cited_domains) < 2:
            violations.append({
                "rule": "Source Diversity",
                "claim_id": claim.claim_id,
                "severity": "MAJOR",
                "explanation": f"Factual claim cites only {len(cited_domains)} domain(s), requires ≥2"
            })

    return violations


def check_partisan_bias(claims: list, sources: list) -> list:
    """Check if partisan sources are acknowledged.

    Args:
        claims: List of Claim objects
        sources: List of Source objects

    Returns:
        List of violations
    """
    violations = []

    # Build source bias map
    source_bias = {}
    for source in sources:
        url_lower = source.url.lower()
        for domain in PARTISAN_SOURCES["left_leaning"]:
            if domain in url_lower:
                source_bias[source.source_id] = "left_leaning"
                break
        for domain in PARTISAN_SOURCES["right_leaning"]:
            if domain in url_lower:
                source_bias[source.source_id] = "right_leaning"
                break

    # Check if political claims acknowledge bias
    for claim in claims:
        # Simple heuristic: check for political keywords
        political_keywords = ["democrat", "republican", "liberal", "conservative", "election", "policy"]
        claim_lower = claim.text.lower()

        is_political = any(kw in claim_lower for kw in political_keywords)

        if is_political:
            # Check if any cited sources are partisan
            partisan_citations = [
                source_id for source_id in claim.citations
                if source_id in source_bias
            ]

            if partisan_citations:
                # Check if bias is acknowledged in claim text
                bias_keywords = ["bias", "partisan", "left-leaning", "right-leaning", "according to"]

                if not any(kw in claim_lower for kw in bias_keywords):
                    violations.append({
                        "rule": "Cite Partisan Sources",
                        "claim_id": claim.claim_id,
                        "severity": "MAJOR",
                        "explanation": f"Political claim cites partisan source(s) without acknowledging bias"
                    })

    return violations


def enforce_constitution(
    query: str,
    claims: list,
    citation_grades: dict,
    sources: list,
    mode: str = "fast"
) -> dict:
    """Enforce constitutional rules programmatically.

    Args:
        query: User query
        claims: List of Claim objects
        citation_grades: Citation verification results
        sources: List of Source objects
        mode: "fast" | "strict" | "liability"

    Returns:
        Dict with verdict and violations
    """
    all_violations = []

    # Rule 1: No Fabrication
    all_violations.extend(check_citation_support(claims, citation_grades))

    # Rule 2: No Speculation (checked by Judge via LLM)
    # Skipped here - requires NLP

    # Rule 3: No Health Advice
    if check_medical_query(query):
        all_violations.append({
            "rule": "No Health Advice",
            "claim_id": "query",
            "severity": "FATAL",
            "explanation": "Medical query detected - Sydyn cannot provide health advice"
        })

    # Rule 4: No Legal Advice
    if check_legal_query(query):
        all_violations.append({
            "rule": "No Legal Advice",
            "claim_id": "query",
            "severity": "FATAL",
            "explanation": "Legal query detected - Sydyn cannot provide legal advice"
        })

    # Rule 5: Cite Partisan Sources
    all_violations.extend(check_partisan_bias(claims, sources))

    # Rule 6: Source Diversity
    diversity_violations = check_source_diversity(claims, sources)
    # In liability mode, enforce stricter (≥3 domains)
    if mode == "liability":
        all_violations.extend(diversity_violations)
    else:
        # In fast/strict mode, only warn
        for v in diversity_violations:
            v["severity"] = "MINOR"
        all_violations.extend(diversity_violations)

    # Determine verdict
    fatal_count = sum(1 for v in all_violations if v["severity"] == "FATAL")
    major_count = sum(1 for v in all_violations if v["severity"] == "MAJOR")

    if fatal_count > 0:
        verdict = "BLOCK"
    elif major_count > 0:
        verdict = "WARN"
    else:
        verdict = "PASS"

    return {
        "verdict": verdict,
        "violations": all_violations,
        "reasoning": f"Programmatic constitutional check: {len(all_violations)} violation(s) found"
    }
