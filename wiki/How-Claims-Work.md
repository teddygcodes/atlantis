# How Claims Work

> **Note:** In the frontend UI, claims are displayed as **"hypotheses."** Internally, the engine and codebase still use **claim** terminology.

## Claim Lifecycle

```
1. GENERATION
   ↓ Researcher agent produces claim (max_tokens: 2500)

2. STRUCTURAL VALIDATION
   ↓ Must have: type, hypothesis/position, steps, conclusion
   ↓ Discovery: GAP ADDRESSED required
   ↓ Foundation: CITATIONS + DEPENDS ON required
   ↓ Extension: DEPENDS ON + SCOPE BOUNDARY required

3. ANTI-LOOP CHECK
   ↓ Haiku detects if last 3 claims repeat same argument

4. NORMALIZATION
   ↓ Haiku extracts structured fields (hypothesis, steps, citations, keywords)

5. OBJECTIVE VALIDATION
   ↓ Domain anchors check factual claims (math, physics constants, etc.)

6. CHALLENGE
   ↓ Rival Critic targets specific reasoning step

7. REBUTTAL
   ↓ Option A: Defend with new reasoning
   ↓ Option B: Concede and narrow claim scope
   ↓ Option C: Retract entirely

8. RULING
   ↓ Judge evaluates: survived | partial | retracted | destroyed
   ↓ Scores: drama (1-10), novelty (1-10), depth (1-10)

9. ARCHIVE
   ↓ Main tier: survived, partial (citable)
   ↓ Quarantine: retracted (visible, not citable)
   ↓ Graveyard: destroyed (autopsy preserved)
```

## Research Types

### Discovery
**Purpose:** First-principles reasoning, no citations required
**Use case:** Archive has no citable claims yet, or covering genuinely new ground

**Required sections:**
```
RESEARCH TYPE: Discovery
HYPOTHESIS: [one sentence — testable prediction]
OPERATIONAL DEF: [key terms defined measurably]
STEP 1: [evidence/reasoning]
STEP 2: [evidence/reasoning]
(add steps as needed)
PREDICTION: [what this predicts that can be verified]
CONCLUSION: [one sentence summary]
GAP ADDRESSED: [what new ground this covers]
KEYWORDS: [3-5 terms]
```

**Example:**
```
RESEARCH TYPE: Discovery

HYPOTHESIS: DNA polymerase error rates in multicellular eukaryotes are
maintained within a narrow optimal range (10^-9 to 10^-10 per base pair
per replication) not solely for minimizing mutation accumulation, but
because this rate optimizes evolvability...
```

### Foundation
**Purpose:** Build on existing validated claims with citations
**Use case:** Extending Archive knowledge with evidence-based reasoning

**Required sections:**
```
RESEARCH TYPE: Foundation
HYPOTHESIS: [statement]
OPERATIONAL DEF: [definitions]
DEPENDS ON: #[prior claim ID]
STEP 1: [reasoning]
STEP 2: [reasoning]
CONCLUSION: [summary]
SCOPE BOUNDARY: [what this claim does NOT cover]
CITATIONS: #[archive IDs]
KEYWORDS: [3-5 terms]
```

**Validation:** Must cite at least one surviving main-tier claim

### Extension
**Purpose:** Narrow or modify an existing claim
**Use case:** Refining a previous hypothesis based on new evidence

**Required sections:**
```
RESEARCH TYPE: Extension
HYPOTHESIS: [refined statement]
DEPENDS ON: #[prior claim ID]
STEP 1: [how this extends the original]
STEP 2: [new evidence]
CONCLUSION: [summary]
SCOPE BOUNDARY: [what this extension does NOT cover]
KEYWORDS: [3-5 terms]
```

## Rejection Reasons

Claims can be rejected (no token cost) before reaching the judge:

| Rejection Type | Cause | Fix |
|----------------|-------|-----|
| **Format failure** | Missing required sections (HYPOTHESIS, STEPS, CONCLUSION) | Add all required headers |
| **Truncation** | Claim cut off before GAP ADDRESSED | Increase max_tokens (now 2500) |
| **Depth too shallow** | Fewer steps than tier requires (Tier 0-1: 2 steps, Tier 2: 3, Tier 3: 4, Tier 4+: 5) | Add more reasoning steps |
| **Anti-loop triggered** | Last 3 claims repeat same argument | Produce genuinely new position |
| **Missing citations** | Foundation claim with no valid #IDs | Cite existing main-tier claims |
| **Invalid citations** | References non-existent or quarantine claims | Only cite surviving main-tier |
| **Missing dependencies** | Extension/Foundation without DEPENDS ON | Add DEPENDS ON: #ID |

## What Happens After Ruling

### Survived
- **Archive tier:** Main (citable)
- **Tokens earned:** 2000 (Foundation) or 1000 (Discovery)
- **Stability score:** +1 per cycle survived
- **Impact score:** Increases as other claims cite it
- **First citation bonus:** Discovery claims earn 3000 tokens when first cited (permanent, not clawed back)

### Partial (Option B: Concede and Narrow)
- **Archive tier:** Main (citable, but scope narrowed)
- **Tokens earned:** 1200 (Foundation) or 600 (Discovery)
- **Status:** "partial" — shows claim was challenged and refined

### Retracted (Option C or judge-forced)
- **Archive tier:** Quarantine (visible but not citable)
- **Tokens earned:** 500 (small recovery for honest retraction)
- **Learning value:** Teaches what doesn't hold up

### Destroyed
- **Archive tier:** Graveyard (full autopsy preserved)
- **Tokens earned:** 0
- **Challenger reward:** Critic's State earns 3000 tokens
- **Impact:** All claims citing this one get flagged "foundation_challenged"

## Probation Mechanics

States enter probation if they produce **3 consecutive cycles** without survived/partial outcomes:
- Retracted claims reset probation counter: **NO** (only survived/partial reset it)
- Option C under fire counts toward probation: **YES** (choosing retract = probation cycle)
- Probation → Dissolution: Token budget hits 0 AND 5+ consecutive probation cycles

**Why this matters:** Economic pressure forces quality. States that consistently produce weak claims die.
