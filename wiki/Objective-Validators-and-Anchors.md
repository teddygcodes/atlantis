# Objective Validators and Anchors

## Two-Layer Validation

Before any LLM judge sees a claim, it passes through **two computational validation layers**:

```
Claim Text
    ↓
1. UNIVERSAL VALIDATORS (run on ALL claims, zero API cost)
    ↓ Citation validity, self-contradiction, circular reasoning,
    ↓ numeric consistency, reasoning depth
    ↓
2. DOMAIN ANCHORS (domain-specific factual checks)
    ↓ Math: SymPy computation
    ↓ Physics: Dimensional analysis
    ↓ Biology: Established facts
    ↓ ...
    ↓
3. ANCHOR RESULTS → JUDGE PROMPT
    ↓ "OBJECTIVE VALIDATION NOTES: [flags, warnings, info]"
    ↓ Judge sees anchor findings as evidence, not override
    ↓
4. JUDGE RULING
    ↓ survived | partial | retracted | destroyed
```

## Universal Validators

Run on **all claims** regardless of domain:

| Validator | Catches | Example |
|-----------|---------|---------|
| **Citation validity** | References to non-existent archive entries | Claim cites #999 but archive stops at #062 |
| **Self-contradiction** | Position negates its own conclusion | "X is always true... therefore X is false" |
| **Circular reasoning** | Conclusion restates position (>80% overlap) | "Markets are efficient because efficiency defines markets" |
| **Numeric consistency** | Percentages >100%, sums that don't add up | "60% Alpha, 50% Beta (total: 110%)" |
| **Reasoning depth** | Too few steps for State's tier | Tier 3 State submits 2-step claim (needs 4) |

**Output:** Flags (critical), Warnings (soft), Info (notes)

## Domain Anchors

Each domain has **computational validators** that check claims against external reality:

### Mathematics
**Anchor type:** SymPy symbolic computation
**What it checks:**
- Derivative correctness (`d/dx(x²) = 2x`, not `3x`)
- Arithmetic errors (`2+2 = 5` flagged)
- Algebraic simplification mistakes
- Integration errors

**Example catch:**
```
CLAIM: "The derivative of x² is 3x, therefore..."
ANCHOR: SymPy computed derivative = 2x
FLAG: "MATH ANCHOR: Claimed derivative is 3x but SymPy computes 2x"
```

**How it works:**
1. Extract mathematical expressions from claim text
2. Parse into SymPy symbolic form
3. Compute actual derivative/integral/simplification
4. Compare claimed result to computed result
5. Flag discrepancies

### Physics
**Anchor type:** Dimensional analysis + physical constants
**What it checks:**
- Speeds > speed of light (unless subject IS light/photons)
- Temperatures < absolute zero
- Wrong physical constants (Planck, Boltzmann, G)
- Dimensional inconsistencies (adding meters to seconds)

**Example catch:**
```
CLAIM: "Neutrinos traveling at 5×10⁹ m/s faster than light..."
ANCHOR: c = 3×10⁸ m/s (speed of light limit)
FLAG: "PHYSICS ANCHOR: Claimed speed 5×10⁹ m/s exceeds c = 3×10⁸ m/s"
```

**False negative fixed (v2.1):**
Original bug: Skipped check if word "light" appeared anywhere
Fix: Only skip if SUBJECT is light/photons (regex checks surrounding context)

### Biology
**Anchor type:** Established biological facts
**What it checks:**
- DNA base pairing (A-T, G-C)
- Lamarckian inheritance claims (inheritance of acquired traits)
- Prokaryotes with nuclei
- Mitochondria in prokaryotes

**Example:**
```
CLAIM: "Bacteria with membrane-bound nuclei..."
FLAG: "BIOLOGY ANCHOR: Prokaryotes (bacteria) do not have membrane-bound nuclei"
```

### Finance
**Anchor type:** Financial logic + probability constraints
**What it checks:**
- Compound interest calculations
- Negative probabilities
- Returns >100% without leverage explanation
- Arbitrage violations

### Technology
**Anchor type:** Computer science fundamentals
**What it checks:**
- P = NP claims (unproven, flag as speculative)
- Halting problem violations
- O(1) sorting claims
- Impossible complexity class reductions

### Medicine
**Anchor type:** Clinical standards + debunked claims
**What it checks:**
- Vaccines → autism link (debunked)
- Correlation → causation jumps without RCT evidence
- Unverified treatment efficacy claims

### Geography
**Anchor type:** Physical constants + demographics
**What it checks:**
- Earth radius/circumference errors
- Population orders of magnitude (e.g., claiming 70 billion people)
- Continental drift rates

### History
**Anchor type:** Chronology + date verification
**What it checks:**
- Anachronisms (ancient Rome with guns)
- Wrong dates (French Revolution in 1889 instead of 1789)
- Impossible causation chains (effect before cause)

### Economics
**Anchor type:** Accounting identities
**What it checks:**
- GDP components summing >100%
- Impossible sustained growth claims (10% GDP growth for 100 years)
- Budget constraint violations

### Philosophy
**Anchor type:** Formal logic
**What it checks:**
- Affirming the consequent (If P→Q and Q, then P)
- False dilemmas (Only A or B when C exists)
- Naturalistic fallacy (Is → Ought)

## How Anchors Flow to Judge

**1. Anchor execution (Step 7.5 in governance cycle):**
```python
a_validation = run_objective_validation(
    claim_text=a_raw,
    domain=pair.domain,
    cited_ids=a_norm.get("citations", []),
    archive_ids=archive_ids,
    state_tier=sa.tier,
)
```

**2. Result structure:**
```json
{
  "all_passed": false,
  "flags": [
    "PHYSICS ANCHOR: Claimed speed 5e9 m/s exceeds c = 3e8 m/s"
  ],
  "warnings": [
    "CITATION WARNING: Cited #042 is in quarantine tier"
  ],
  "info": [
    "Operational definition detected: 'measured by tracking...'"
  ]
}
```

**3. Injected into judge prompt:**
```
OBJECTIVE VALIDATION NOTES:
FLAGS (critical issues):
- PHYSICS ANCHOR: Claimed speed 5e9 m/s exceeds c = 3e8 m/s

WARNINGS (soft failures):
- CITATION WARNING: Cited #042 is in quarantine tier

INFO:
- Operational definition detected
```

**4. Judge sees and considers:**
Judge prompt includes:
```
These notes are EVIDENCE, not verdicts. Weigh them appropriately.
A flagged claim CAN still survive if the rebuttal addresses the issue.
```

## Key Principle: Anchors Inform, Don't Override

**Anchors are not automatic rejections.** They provide **evidence** that the judge weighs:

- **Flag raised, claim survives:** Researcher's rebuttal successfully explains the issue
- **Flag raised, claim destroyed:** Rebuttal fails to address anchor finding
- **No flags, claim destroyed:** Judge finds logical flaws not caught by anchors

**Why this design:**
- Anchors catch objective errors (math, physics constants)
- Judge evaluates subjective merit (novelty, reasoning quality)
- Human oversight: User can audit anchor findings in `validation_json` field

## Anchor Validation in Archive

Since v2.2, validation results are **persisted** with each claim:

```typescript
{
  "display_id": "#023",
  "validation": {
    "all_passed": false,
    "flags": ["PHYSICS ANCHOR: ..."],
    "warnings": [],
    "info": []
  }
}
```

**Frontend can display:**
- ✅ All validators passed
- ⚠️ Warnings present
- ❌ Flags raised
- Badge showing which anchor caught the issue

## Adding New Anchors

To add a domain anchor:

1. **Define check function** in `governance/anchors.py`:
   ```python
   def check_chemistry_valence(claim_text: str) -> dict:
       """Check valence electron configurations."""
       # Extract chemical formulas
       # Verify electron counts
       return {"passed": bool, "notes": [str], "severity": "flag"|"warning"|"info"}
   ```

2. **Register in DOMAIN_ANCHORS:**
   ```python
   DOMAIN_ANCHORS = {
       "Chemistry": [_with_metadata(check_chemistry_valence)],
   }
   ```

3. **Test with known violations:**
   ```python
   result = check_chemistry_valence("Carbon with 7 valence electrons...")
   assert not result["passed"]
   assert "valence" in result["notes"][0].lower()
   ```

**Cost:** Zero API cost (pure computation). Anchors run before any LLM calls.
