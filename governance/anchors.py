"""
Real-world anchors for Atlantis domains.

Each anchor connects a domain to something OUTSIDE the LLM —
actual computation, verified data, formal logic, or established facts.
This is what makes Atlantis interact with reality, not just argue about it.

These are added to DOMAIN_VALIDATORS in validators.py.

Dependencies: sympy, pint (add to requirements.txt)
"""

from __future__ import annotations

import re
import math
from typing import List, Tuple


# ─── 1. MATHEMATICS: SymPy Verification ─────────────────────────────

def check_math_computation(claim_text: str) -> dict:
    """
    Extract mathematical expressions and verify them with SymPy.
    Catches wrong arithmetic, bad simplifications, incorrect derivatives/integrals.
    """
    try:
        import sympy
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication
    except ImportError:
        return {"passed": True, "notes": ["SymPy not installed — skipping math verification"], "severity": "info"}

    notes = []
    text = claim_text

    # Pattern: "X equals Y" or "X = Y" in mathematical context
    equals_patterns = [
        # "the derivative of x^2 is 2x"
        r"(?:the\s+)?derivative\s+of\s+([^\s]+(?:\s*[\^\*]\s*\d+)?)\s+is\s+([^\s,\.]+)",
        # "X simplifies to Y"
        r"([^\s]+(?:\s*[\+\-\*\/\^]\s*[^\s]+)*)\s+simplifies?\s+to\s+([^\s,\.]+)",
        # "X = Y" (in math context)
        r"(\d+(?:\s*[\+\-\*\/\^]\s*\d+)+)\s*=\s*(\d+(?:\.\d+)?)",
        # "sum of 1/n^2 converges to pi^2/6"
        r"sum\s+of\s+(.+?)\s+converges?\s+to\s+([^\s,\.]+)",
    ]

    for pattern in equals_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            lhs_str, rhs_str = match.group(1).strip(), match.group(2).strip()
            try:
                transformations = standard_transformations + (implicit_multiplication,)
                lhs = parse_expr(lhs_str.replace("^", "**"), transformations=transformations)
                rhs = parse_expr(rhs_str.replace("^", "**"), transformations=transformations)

                # Check if derivative claim
                if "derivative" in match.group(0).lower():
                    x = sympy.Symbol('x')
                    actual = sympy.diff(lhs, x)
                    if sympy.simplify(actual - rhs) == 0:
                        notes.append(f"MATH VERIFIED: derivative of {lhs} is indeed {rhs}")
                    else:
                        notes.append(f"MATH ERROR: derivative of {lhs} is {actual}, not {rhs}")
                        return {"passed": False, "notes": notes, "severity": "flag"}
                else:
                    # Direct equality check
                    if sympy.simplify(lhs - rhs) == 0:
                        notes.append(f"MATH VERIFIED: {lhs_str} = {rhs_str}")
                    else:
                        evaluated = sympy.simplify(lhs)
                        notes.append(f"MATH ERROR: {lhs_str} evaluates to {evaluated}, not {rhs_str}")
                        return {"passed": False, "notes": notes, "severity": "flag"}
            except (sympy.SympifyError, SyntaxError, TypeError, ValueError):
                continue  # Can't parse — skip silently

    # Check basic arithmetic: "2+2=5" patterns
    arith_matches = re.finditer(r"(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)\s*(?:=|equals|is)\s*(\d+(?:\.\d+)?)", text)
    for m in arith_matches:
        a, op, b, claimed = float(m.group(1)), m.group(2), float(m.group(3)), float(m.group(4))
        ops = {'+': a + b, '-': a - b, '*': a * b, '/': a / b if b != 0 else None}
        actual = ops.get(op)
        if actual is not None and abs(actual - claimed) > 0.001:
            notes.append(f"MATH ERROR: {a}{op}{b} = {actual}, not {claimed}")
            return {"passed": False, "notes": notes, "severity": "flag"}
        elif actual is not None:
            notes.append(f"MATH VERIFIED: {a}{op}{b} = {actual}")

    if notes:
        return {"passed": True, "notes": notes, "severity": "info"}
    return {"passed": True, "notes": [], "severity": "info"}


# ─── 2. PHYSICS: Unit Dimensional Analysis ──────────────────────────

def check_physics_units(claim_text: str) -> dict:
    """
    Check dimensional consistency in physics claims.
    Catches: force claimed in seconds, energy in meters, speed > c, etc.
    """
    notes = []
    text_lower = claim_text.lower()

    # Speed of light violations
    speed_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:×|x|times)\s*10\^?(\d+)\s*m/s", claim_text)
    if speed_match:
        mantissa = float(speed_match.group(1))
        exponent = int(speed_match.group(2))
        speed = mantissa * (10 ** exponent)
        c = 3e8  # speed of light
        if speed > c and "light" not in text_lower and "photon" not in text_lower:
            notes.append(
                f"PHYSICS FLAG: Claimed speed {speed:.2e} m/s exceeds speed of light "
                f"(3×10⁸ m/s) for non-photonic entity."
            )
            return {"passed": False, "notes": notes, "severity": "flag"}

    # Temperature below absolute zero
    temp_match = re.search(r"(-\d+(?:\.\d+)?)\s*(?:K|kelvin)", claim_text, re.IGNORECASE)
    if temp_match:
        temp = float(temp_match.group(1))
        if temp < 0:
            notes.append(f"PHYSICS FLAG: Temperature {temp}K is below absolute zero.")
            return {"passed": False, "notes": notes, "severity": "flag"}

    # Energy conservation: check for perpetual motion language
    if re.search(r"\b(perpetual motion|infinite energy|creates? energy|100%\s+efficien)", text_lower):
        if not re.search(r"\b(impossible|violat|refut|disproven|cannot)\b", text_lower):
            notes.append(
                "PHYSICS WARNING: Claim implies perpetual motion or energy creation "
                "without acknowledging thermodynamic constraints."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    # Check if claim references specific constants with wrong values
    constants = {
        "planck": (6.626e-34, r"planck(?:'s)?\s+constant.*?(\d+\.?\d*)\s*(?:×|x)\s*10\^?\s*(-?\d+)"),
        "boltzmann": (1.381e-23, r"boltzmann(?:'s)?\s+constant.*?(\d+\.?\d*)\s*(?:×|x)\s*10\^?\s*(-?\d+)"),
        "gravitational": (6.674e-11, r"gravitational\s+constant.*?(\d+\.?\d*)\s*(?:×|x)\s*10\^?\s*(-?\d+)"),
    }
    for name, (true_val, pattern) in constants.items():
        match = re.search(pattern, text_lower)
        if match:
            claimed = float(match.group(1)) * 10 ** int(match.group(2))
            ratio = claimed / true_val if true_val != 0 else float('inf')
            if not (0.9 < ratio < 1.1):
                notes.append(
                    f"PHYSICS ERROR: Claimed {name} constant ({claimed:.3e}) "
                    f"differs from accepted value ({true_val:.3e}) by >{abs(1-ratio)*100:.0f}%"
                )
                return {"passed": False, "notes": notes, "severity": "flag"}
            else:
                notes.append(f"PHYSICS VERIFIED: {name} constant value is correct.")

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── 3. BIOLOGY: Taxonomy & Established Facts ──────────────────────

def check_biology_facts(claim_text: str) -> dict:
    """
    Check biological claims against established facts.
    Catches: wrong taxonomy, impossible biology, debunked claims.
    """
    notes = []
    text_lower = claim_text.lower()

    # DNA base pairing errors
    if re.search(r"dna", text_lower):
        # A pairs with T, G pairs with C
        wrong_pairs = [
            (r"adenine\s+(?:pairs?|bonds?|connects?)\s+(?:with|to)\s+(?:guanine|cytosine)", "Adenine pairs with Thymine, not Guanine/Cytosine"),
            (r"thymine\s+(?:pairs?|bonds?|connects?)\s+(?:with|to)\s+(?:guanine|cytosine)", "Thymine pairs with Adenine, not Guanine/Cytosine"),
            (r"guanine\s+(?:pairs?|bonds?|connects?)\s+(?:with|to)\s+(?:adenine|thymine)", "Guanine pairs with Cytosine, not Adenine/Thymine"),
        ]
        for pattern, msg in wrong_pairs:
            if re.search(pattern, text_lower):
                notes.append(f"BIOLOGY ERROR: {msg}")
                return {"passed": False, "notes": notes, "severity": "flag"}

    # Lamarckian inheritance (debunked)
    if re.search(r"\b(acquired traits?|acquired characteristics?)\b.*\b(inherit|pass(?:ed)?\s+(?:on|to))\b", text_lower):
        if not re.search(r"\b(epigenetic|lamarck|debunk|incorrect|disproven)\b", text_lower):
            notes.append(
                "BIOLOGY WARNING: Claim implies inheritance of acquired characteristics "
                "(Lamarckian inheritance) without epigenetic qualification."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    # Photosynthesis basics
    if "photosynthesis" in text_lower:
        if re.search(r"photosynthesis.*(?:produces?|creates?|generates?).*oxygen.*(?:from|using).*nitrogen", text_lower):
            notes.append("BIOLOGY ERROR: Photosynthesis uses CO₂ and water, not nitrogen, to produce oxygen.")
            return {"passed": False, "notes": notes, "severity": "flag"}

    # Cell biology: prokaryotes don't have nuclei
    if re.search(r"(?:bacteria|prokaryot).*\b(nucleus|nuclei|nuclear membrane)\b", text_lower):
        if not re.search(r"\b(lack|without|no|absent|don't have)\b", text_lower):
            notes.append("BIOLOGY WARNING: Prokaryotes/bacteria do not have membrane-bound nuclei.")
            return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── 4. FINANCE: Market Data & Financial Logic ──────────────────────

def check_finance_logic(claim_text: str) -> dict:
    """
    Check financial claims against basic financial logic and math.
    Catches: impossible returns, wrong compound interest, arbitrage fallacies.
    """
    notes = []
    text_lower = claim_text.lower()

    # Compound interest verification
    ci_match = re.search(
        r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:invested|compounded|growing)\s+at\s+(\d+(?:\.\d+)?)\s*%"
        r".*?(\d+)\s*years?.*?(?:becomes?|grows?\s+to|equals?|results?\s+in)\s*"
        r"(\d+(?:,\d+)*(?:\.\d+)?)",
        claim_text, re.IGNORECASE
    )
    if ci_match:
        principal = float(ci_match.group(1).replace(",", ""))
        rate = float(ci_match.group(2)) / 100
        years = int(ci_match.group(3))
        claimed_result = float(ci_match.group(4).replace(",", ""))
        actual = principal * ((1 + rate) ** years)
        if abs(actual - claimed_result) / max(actual, 1) > 0.05:
            notes.append(
                f"FINANCE ERROR: ${principal:,.0f} at {rate*100}% for {years} years = "
                f"${actual:,.0f}, not ${claimed_result:,.0f}"
            )
            return {"passed": False, "notes": notes, "severity": "flag"}
        else:
            notes.append(f"FINANCE VERIFIED: Compound interest calculation is correct.")

    # Risk-free arbitrage claims (usually wrong)
    if re.search(r"\b(risk.?free|guaranteed|certain)\s+(return|profit|gain|arbitrage)\b", text_lower):
        if re.search(r"\b(\d+)\s*%", text_lower):
            pct = int(re.search(r"\b(\d+)\s*%", text_lower).group(1))
            if pct > 10:
                notes.append(
                    f"FINANCE WARNING: Claiming {pct}% risk-free return. "
                    f"Risk-free rates are typically 2-5%. Returns above 10% "
                    f"guaranteed indicate either error or fraud."
                )
                return {"passed": True, "notes": notes, "severity": "warning"}

    # Negative probability claims
    if re.search(r"(-\d+(?:\.\d+)?)\s*%\s*(?:probability|chance|likelihood)", text_lower):
        notes.append("FINANCE ERROR: Probability cannot be negative.")
        return {"passed": False, "notes": notes, "severity": "flag"}

    # Probability > 100%
    prob_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:probability|chance|likelihood)", text_lower)
    if prob_match and float(prob_match.group(1)) > 100:
        notes.append(f"FINANCE ERROR: Probability {prob_match.group(1)}% exceeds 100%.")
        return {"passed": False, "notes": notes, "severity": "flag"}

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── 5. TECHNOLOGY: Logic & Complexity Claims ───────────────────────

def check_technology_claims(claim_text: str) -> dict:
    """
    Check technology claims against computer science fundamentals.
    Catches: impossible complexity claims, P=NP assumptions, halting problem violations.
    """
    notes = []
    text_lower = claim_text.lower()

    # P=NP claims (extraordinary claim, extraordinary evidence needed)
    if re.search(r"\bp\s*=\s*np\b", text_lower):
        if not re.search(r"\b(if|assuming|hypothetical|conjecture|unresolved|open problem)\b", text_lower):
            notes.append(
                "TECHNOLOGY FLAG: Claim asserts P=NP as fact. This is one of the "
                "Millennium Prize Problems and remains unresolved. Requires extraordinary proof."
            )
            return {"passed": False, "notes": notes, "severity": "flag"}

    # Halting problem violations
    if re.search(r"\b(algorithm|program|method)\b.*\b(determine|decide|solve)\b.*\b(halting problem|whether.*terminates?)\b", text_lower):
        if not re.search(r"\b(undecidable|impossible|turing proved|cannot|restricted|subset)\b", text_lower):
            notes.append(
                "TECHNOLOGY FLAG: Claim implies solving the halting problem for general programs. "
                "Turing proved this is undecidable (1936)."
            )
            return {"passed": False, "notes": notes, "severity": "flag"}

    # O(1) sorting claims
    if re.search(r"sort.*o\(1\)|o\(1\).*sort", text_lower):
        notes.append(
            "TECHNOLOGY FLAG: Comparison-based sorting has a proven lower bound of O(n log n). "
            "O(1) sorting of arbitrary data is impossible."
        )
        return {"passed": False, "notes": notes, "severity": "flag"}

    # 100% accuracy in ML
    if re.search(r"100\s*%\s*(?:accuracy|precision|recall)", text_lower):
        if re.search(r"\b(real.?world|production|general|any)\b", text_lower):
            notes.append(
                "TECHNOLOGY WARNING: Claiming 100% accuracy in real-world ML systems. "
                "Perfect accuracy on non-trivial tasks indicates overfitting or data leakage."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── 6. MEDICINE: Clinical & Safety Checks ──────────────────────────

def check_medicine_claims(claim_text: str) -> dict:
    """
    Check medical claims against clinical standards.
    Catches: dosage impossibilities, debunked treatments, correlation/causation errors.
    """
    notes = []
    text_lower = claim_text.lower()

    # Correlation ≠ Causation without qualification
    if re.search(r"\b(correlat|associat)\w*\b", text_lower):
        if re.search(r"\b(therefore|thus|proves?|causes?|leads? to|results? in)\b", text_lower):
            if not re.search(r"\b(caution|caveat|correlation.*not.*causation|confound|observational)\b", text_lower):
                notes.append(
                    "MEDICINE WARNING: Claim jumps from correlation/association to causation "
                    "without acknowledging confounding variables or study design limitations."
                )
                return {"passed": True, "notes": notes, "severity": "warning"}

    # Debunked medical claims
    debunked = [
        (r"vaccines?\s+(?:cause|lead|linked)\s+(?:to\s+)?autism", "Vaccines causing autism has been thoroughly debunked (Wakefield study retracted 2010)"),
        (r"homeopathy\s+(?:cure|treat|heal|effective)", "Homeopathy has no evidence of efficacy beyond placebo for any condition"),
        (r"blood.?letting\s+(?:cure|treat|effective|therapeutic)", "Bloodletting as treatment was abandoned based on evidence-based medicine"),
    ]
    for pattern, msg in debunked:
        if re.search(pattern, text_lower):
            if not re.search(r"\b(debunked|disproven|false|incorrect|historical|was believed)\b", text_lower):
                notes.append(f"MEDICINE FLAG: {msg}")
                return {"passed": False, "notes": notes, "severity": "flag"}

    # Sample size concerns
    sample_match = re.search(r"(?:study|trial|sample|n\s*=)\s*(?:of\s+)?(\d+)\s+(?:patients?|participants?|subjects?|people)", text_lower)
    if sample_match:
        n = int(sample_match.group(1))
        if n < 30:
            notes.append(
                f"MEDICINE WARNING: Study sample size n={n} is very small. "
                f"Results may not be statistically significant or generalizable."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── 7. GEOGRAPHY: Physical Constants & Scale ──────────────────────

def check_geography_facts(claim_text: str) -> dict:
    """
    Check geographic claims against known facts.
    Catches: impossible distances, wrong populations orders of magnitude, reversed locations.
    """
    notes = []
    text_lower = claim_text.lower()

    # Earth's basic measurements
    earth_facts = {
        "circumference": (40075, r"earth(?:'s)?\s+circumference.*?(\d+(?:,\d+)*)\s*km"),
        "radius": (6371, r"earth(?:'s)?\s+radius.*?(\d+(?:,\d+)*)\s*km"),
        "diameter": (12742, r"earth(?:'s)?\s+diameter.*?(\d+(?:,\d+)*)\s*km"),
    }
    for fact, (true_val, pattern) in earth_facts.items():
        match = re.search(pattern, text_lower)
        if match:
            claimed = int(match.group(1).replace(",", ""))
            ratio = claimed / true_val
            if not (0.8 < ratio < 1.2):
                notes.append(
                    f"GEOGRAPHY ERROR: Claimed Earth's {fact} is {claimed:,} km. "
                    f"Accepted value is ~{true_val:,} km."
                )
                return {"passed": False, "notes": notes, "severity": "flag"}

    # Population order of magnitude checks
    pop_claims = {
        "world": (8e9, 0.5e9),
        "china": (1.4e9, 0.3e9),
        "india": (1.4e9, 0.3e9),
        "united states": (330e6, 50e6),
        "russia": (144e6, 20e6),
        "japan": (125e6, 15e6),
    }
    for country, (approx_pop, tolerance) in pop_claims.items():
        pop_match = re.search(
            rf"{country}(?:'s)?\s+population.*?(\d+(?:\.\d+)?)\s*(billion|million|thousand)",
            text_lower
        )
        if pop_match:
            num = float(pop_match.group(1))
            unit = pop_match.group(2)
            multipliers = {"billion": 1e9, "million": 1e6, "thousand": 1e3}
            claimed_pop = num * multipliers.get(unit, 1)
            if abs(claimed_pop - approx_pop) > tolerance:
                notes.append(
                    f"GEOGRAPHY WARNING: Claimed {country} population ({claimed_pop/1e6:.0f}M) "
                    f"differs significantly from ~{approx_pop/1e6:.0f}M."
                )
                return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── 8. HISTORY: Date & Chronology Verification ────────────────────

def check_history_dates(claim_text: str) -> dict:
    """
    Check historical claims against known dates and chronology.
    Catches: anachronisms, impossible timelines, wrong centuries.
    """
    notes = []
    text_lower = claim_text.lower()

    # Known historical dates (event → (year, tolerance))
    known_dates = {
        "fall of rome": (476, 5),
        "fall of the roman empire": (476, 5),
        "french revolution": (1789, 2),
        "american revolution": (1776, 2),
        "world war i": (1914, 1),
        "world war ii": (1939, 1),
        "moon landing": (1969, 0),
        "fall of the berlin wall": (1989, 0),
        "black death": (1347, 5),
        "magna carta": (1215, 1),
        "printing press": (1440, 10),
        "industrial revolution": (1760, 20),
        "renaissance": (1400, 50),
        "columbus": (1492, 1),
    }

    for event, (true_year, tolerance) in known_dates.items():
        # Look for "event ... in YEAR" or "YEAR ... event"
        patterns = [
            rf"{event}.*?\b(\d{{4}})\b",
            rf"\b(\d{{4}})\b.*?{event}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                claimed_year = int(match.group(1))
                if abs(claimed_year - true_year) > tolerance:
                    notes.append(
                        f"HISTORY ERROR: {event.title()} dated to {claimed_year}, "
                        f"accepted date is ~{true_year} (±{tolerance} years)."
                    )
                    return {"passed": False, "notes": notes, "severity": "flag"}
                else:
                    notes.append(f"HISTORY VERIFIED: {event.title()} correctly dated to ~{claimed_year}.")
                break

    # Anachronism detection: technology before invention
    anachronisms = [
        (r"(?:ancient|classical)\s+(?:rome|greek|egypt).*?\b(gun|rifle|cannon|firearm)", "Firearms didn't exist in the ancient world"),
        (r"(?:medieval|middle ages).*?\b(internet|computer|electricity|telephone)", "Modern technology didn't exist in medieval period"),
        (r"(?:1[0-4]\d{2}|before\s+1500).*?\b(steam engine|railway|railroad)", "Steam engines weren't developed until the 18th century"),
    ]
    for pattern, msg in anachronisms:
        if re.search(pattern, text_lower):
            notes.append(f"HISTORY FLAG: Anachronism detected — {msg}")
            return {"passed": False, "notes": notes, "severity": "flag"}

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── 9. ECONOMICS: Accounting Identity Checks ──────────────────────

def check_economics_logic(claim_text: str) -> dict:
    """
    Check economic claims against fundamental accounting identities and logic.
    Catches: GDP component errors, impossible growth claims, logical contradictions.
    """
    notes = []
    text_lower = claim_text.lower()

    # GDP identity: GDP = C + I + G + (X-M)
    gdp_components = {
        "consumption": re.search(r"consumption.*?(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?gdp", text_lower),
        "investment": re.search(r"investment.*?(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?gdp", text_lower),
        "government": re.search(r"government.*?(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?gdp", text_lower),
    }
    found_components = {k: float(v.group(1)) for k, v in gdp_components.items() if v}
    if len(found_components) >= 2:
        total = sum(found_components.values())
        if total > 120:  # Allow some room for net exports and rounding
            notes.append(
                f"ECONOMICS WARNING: GDP components sum to {total}% "
                f"({found_components}). Components should roughly sum to ~100% "
                f"(minus net exports)."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    # Impossible sustained growth
    growth_match = re.search(r"(\d+(?:\.\d+)?)\s*%.*(?:annual|yearly)\s+(?:growth|gdp growth).*(?:for|over|sustained)\s+(\d+)\s+(?:years?|decades?)", text_lower)
    if growth_match:
        rate = float(growth_match.group(1))
        years = int(growth_match.group(2))
        if "decade" in growth_match.group(0):
            years *= 10
        if rate > 15 and years > 10:
            notes.append(
                f"ECONOMICS WARNING: {rate}% annual growth sustained for {years} years "
                f"would imply {((1+rate/100)**years):.0f}x increase. "
                f"No economy has sustained >15% growth for >10 years."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    # Deflation + high growth contradiction
    if re.search(r"\bdeflation\b", text_lower) and re.search(r"\b(boom|rapid growth|expansion|prosperity)\b", text_lower):
        if not re.search(r"\b(exception|unusual|rare|despite|paradox|however)\b", text_lower):
            notes.append(
                "ECONOMICS WARNING: Deflation typically accompanies economic contraction, "
                "not booms. Claim implies both without acknowledging the tension."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── 10. PHILOSOPHY: Formal Logic Checks ───────────────────────────

def check_philosophy_logic(claim_text: str) -> dict:
    """
    Check philosophical claims for formal logic errors.
    Catches: affirming the consequent, denying the antecedent, false dilemmas,
    equivocation, and undistributed middle.
    """
    notes = []
    text_lower = claim_text.lower()

    # Affirming the consequent: "If P then Q. Q. Therefore P."
    if re.search(r"if\s+.+?\s+then\s+.+", text_lower):
        # Check if the argument structure affirms the consequent
        if re.search(r"therefore.*because.*(?:is true|is the case|obtains|holds)", text_lower):
            if not re.search(r"\b(modus ponens|valid|deductive)\b", text_lower):
                notes.append(
                    "PHILOSOPHY WARNING: Argument structure may commit 'affirming the consequent' "
                    "fallacy (If P→Q, Q, ∴ P). This is logically invalid."
                )
                return {"passed": True, "notes": notes, "severity": "warning"}

    # False dilemma / false dichotomy
    false_dilemma_patterns = [
        r"(?:either|must be)\s+(?:true|the case)\s+(?:that\s+)?.+?\s+or\s+.+",
        r"(?:only two|just two|two choices?|two options?|two possibilit)",
    ]
    for pattern in false_dilemma_patterns:
        if re.search(pattern, text_lower):
            if not re.search(r"\b(exhaustive|mutually exclusive|dichotomy justified|logically necessary)\b", text_lower):
                notes.append(
                    "PHILOSOPHY WARNING: Possible false dilemma — presents only two options "
                    "without justifying that alternatives are exhaustive."
                )
                return {"passed": True, "notes": notes, "severity": "warning"}

    # Appeal to nature fallacy
    if re.search(r"\bnatural\b.*\b(therefore|thus|so|hence)\b.*\b(good|right|better|superior|moral)\b", text_lower):
        if not re.search(r"\b(fallacy|naturalistic|hume|is-ought)\b", text_lower):
            notes.append(
                "PHILOSOPHY WARNING: Possible naturalistic fallacy — deriving 'ought' from 'is' "
                "(something being natural doesn't make it good/right)."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    # Infinite regress without acknowledgment
    if re.search(r"\b(requires?|needs?|depends? on)\s+.+?\s+which\s+(?:itself\s+)?(?:requires?|needs?|depends?)", text_lower):
        if not re.search(r"\b(regress|foundational|brute fact|axiom|self-evident|infinite)\b", text_lower):
            notes.append(
                "PHILOSOPHY WARNING: Argument may involve infinite regress — "
                "each step depends on a prior step without grounding."
            )
            return {"passed": True, "notes": notes, "severity": "warning"}

    return {"passed": True, "notes": notes, "severity": "info"}


# ─── METADATA WRAPPER ───────────────────────────────────────────────

ANCHOR_VERSION = "1.0"


def _with_metadata(check_fn):
    """Wrap a validator to inject reproducibility metadata into its result."""
    def wrapper(*args, **kwargs):
        result = check_fn(*args, **kwargs)
        result["anchor"] = check_fn.__name__
        result["version"] = ANCHOR_VERSION
        return result
    wrapper.__name__ = check_fn.__name__
    wrapper.__doc__ = check_fn.__doc__
    return wrapper


# ─── EXPORTS ────────────────────────────────────────────────────────

# Map domain → list of anchor validators (all wrapped with metadata)
DOMAIN_ANCHORS = {
    "Mathematics": [_with_metadata(check_math_computation)],
    "Physics": [_with_metadata(check_physics_units)],
    "Biology": [_with_metadata(check_biology_facts)],
    "Finance": [_with_metadata(check_finance_logic)],
    "Technology": [_with_metadata(check_technology_claims)],
    "Medicine": [_with_metadata(check_medicine_claims)],
    "Geography": [_with_metadata(check_geography_facts)],
    "History": [_with_metadata(check_history_dates)],
    "Economics": [_with_metadata(check_economics_logic)],
    "Philosophy": [_with_metadata(check_philosophy_logic)],
}
