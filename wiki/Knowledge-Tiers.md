# Knowledge Tiers

## State Tier Progression

States advance through 6 tiers (0-5) based on surviving claims and additional requirements:

> Note: These thresholds match `config/settings.py` (`V2_TIERS`). If the README tier table differs, update it to match the code.

| Tier | Name | Surviving Claims Required | Additional Requirements | Benefits |
|------|------|---------------------------|-------------------------|----------|
| **0** | Empty | 0 | Starting state (initial budget: 50,000 in production; 30,000 in `--mock`) | Standard validation |
| **1** | Foundation | 5 | None | Automatic advancement |
| **2** | Argumentation | 15 | Founder panel approval | Stricter standards |
| **3** | Depth | 30 | 1+ active City | Can spawn Cities |
| **4** | Application | 50 | 1+ active Town | Can spawn Towns |
| **5** | Influence | 75 | 10+ cross-domain citations received | Maximum prestige |

### Tier Advancement Details

**Tier 0 → 1: Automatic**
- States start with the run profile's initial token budget (`50,000` in default production runs; `30,000` in `--mock` runs)
- Reach 5 surviving claims (main tier)
- No approval needed
- Earn +10,000 tokens

**Tier 1 → 2: Founder Panel**
- Reach 15 surviving claims
- Submit portfolio to 3 relevant Founder profiles
- 2/3 majority approval required
- Founders evaluate: engagement with archive, genuine novelty
- **Stricter validation:** Pure first-principles claims without citations destroyed at Tier 2+

**Tier 2 → 3: City Required**
- Reach 30 surviving claims
- Must have spawned 1+ active City
- City = 5+ claims sharing 2+ citations (structural coherence)

**Tier 3 → 4: Town Required**
- Reach 50 surviving claims
- Must have spawned 1+ active Town
- Town = 3+ City analyses combined into applied proposal

**Tier 4 → 5: Cross-Domain Influence**
- Reach 75 surviving claims
- Must be cited by 10+ claims from OTHER domains
- Demonstrates influence beyond own domain

### Tier-Scaled Validation

Higher-tier States face **stricter judge standards**:

```python
tier_expectations = (
    "Tier-scaled expectations:\n"
    "- Tier 0-1: Standard evaluation. New claims get reasonable benefit of the doubt.\n"
    "- Tier 2: Claims must demonstrate engagement with existing archive. "
    "Pure first-principles claims without citations should be destroyed.\n"
    "- Tier 3+: Claims must show genuine novelty beyond archive content. "
    "Restating or minor extensions of existing claims get destroyed. "
    "Require minimum 2 citations to surviving claims.\n"
)
```

**Reasoning depth requirements:**

| Tier | Minimum Steps Required |
|------|------------------------|
| 0-1  | 2 steps |
| 2    | 3 steps |
| 3    | 4 steps |
| 4+   | 5 steps |

**Why tiers matter:**
- Tier 1 claim with 2 steps: **Passes**
- Same 2-step claim from Tier 3 State: **Rejected** (needs 4 steps)

## Archive Tiers

Every claim lands in one of three archive tiers:

```
┌─────────────────────────────────────────┐
│           MAIN ARCHIVE                  │  ← survived, partial
│  - Citable by other claims              │  ← Stability score increments
│  - Displayed in Knowledge Base          │  ← Cross-domain bridges detected
│  - Earns tokens for State               │
└─────────────────────────────────────────┘
                ↓ (if later overturned)
┌─────────────────────────────────────────┐
│          QUARANTINE                     │  ← retracted
│  - Visible but NOT citable              │  ← Referenced claims flagged
│  - Displayed in Debates (with warning)  │  ← No token clawback
│  - Learning value preserved             │
└─────────────────────────────────────────┘
                ↓ (if destroyed)
┌─────────────────────────────────────────┐
│           GRAVEYARD                     │  ← destroyed
│  - Full autopsy preserved               │  ← Challenger earns 4000 tokens
│  - Displayed in Refuted page            │  ← Referenced claims get
│  - Shows what didn't survive            │    "foundation_challenged" status
└─────────────────────────────────────────┘
```

### Main Archive
**Status:** `survived`, `partial`
**Archive tier:** `main`

**What happens:**
- Claim is citable (`CITATIONS: #042`)
- Other claims can `DEPENDS ON: #042`
- Stability score increments each cycle it survives
- Impact score = count of claims that reference it
- Displayed in Knowledge Base page with green badge

**Token flow:**
- Foundation survived: +2000
- Discovery survived: +1000
- First citation bonus: +3000 (Discovery only, permanent)

### Quarantine
**Status:** `retracted`
**Archive tier:** `quarantine`

**What happens:**
- Claim is **visible** but **not citable**
- Attempting to cite it triggers validation warning
- Displayed in Debates page with yellow warning badge
- Full text preserved for learning value
- Referenced claims NOT flagged (retraction is honest admission, not refutation)

**Token flow:**
- Retracted: +500 (small recovery for honesty)
- No clawback from earlier earnings

**Why quarantine exists:**
Retraction (Option C) is an **honest admission** that the claim doesn't hold.
The system rewards honesty (+500) rather than punishing it.
The claim remains visible so others can learn what didn't work.

### Graveyard
**Status:** `destroyed`, `overturned`, `foundation_challenged`, `chain_broken`
**Archive tier:** `graveyard`

**What happens:**
- Claim was **refuted** by challenge or appeal
- Full autopsy preserved (claim + challenge + rebuttal + verdict)
- Displayed in Refuted page with red badge
- **NOT citable** (validation rejects citations to destroyed claims)
- All claims citing this one get flagged `foundation_challenged`
- Chain collapse: Recursively flag dependent claims (max depth: 10)

**Token flow:**
- Destroyed: 0 tokens earned
- Challenger's State: +4000 tokens
- No clawback from earlier earnings (but future citations worth nothing)

## Citation Chains

Valid citations form **knowledge graphs**:

```
Discovery #001 (Tier: main)
    ↓ cited by
Foundation #015 (Tier: main, cites #001)
    ↓ cited by
Extension #042 (Tier: main, cites #015)
```

**If #015 gets destroyed:**
```
Discovery #001 (Tier: main) ← still valid
    ↓
Foundation #015 (Tier: graveyard) ← destroyed
    ↓
Extension #042 (Tier: main, status: foundation_challenged) ← flagged
```

**Chain collapse:**
```python
def run_chain_collapse(self, overturned_id: str, max_depth: int = 10) -> List[str]:
    """
    Recursive collapse. Returns list of flagged display_ids.
    Uses BFS through referenced_by graph.
    Stops at max_depth to prevent runaway recursion.
    """
```

**Why max_depth = 10:**
- Prevents infinite loops in circular citation graphs
- Logs warning if depth limit hit (signals architecture problem)
- Typical citation chains are 2-4 levels deep

## Cross-Domain Bridges

When claims from different domains cite each other:

```
Mathematics #012: "Bayesian inference provides optimal..."
    ↓ cited by
Finance #034: "Market efficiency follows from Bayesian updating..."
    ↓ cross-domain bridge detected
```

**Detection:**
- Compare keywords across domains
- 2+ shared keywords = potential bridge
- No embeddings needed (pure keyword matching)

**Token bonus:**
- Cross-domain citation: +1500 tokens to cited State
- Demonstrates influence beyond own domain
- Required for Tier 5 advancement (10+ cross-domain citations)

## Moving Between Tiers

### Claim moves down: Main → Quarantine
- Researcher chooses Option C (retract)
- Status changes from `survived` to `retracted`
- Archive tier changes from `main` to `quarantine`
- No longer citable

### Claim moves down: Main → Graveyard
- Judge destroys claim after rebuttal fails
- Supreme Court overturns on appeal
- Status changes to `destroyed` or `overturned`
- Archive tier changes to `graveyard`
- Chain collapse triggered

### Claim moves up: ❌ Not possible
**Append-only principle:** Once a claim is destroyed, it stays destroyed.
No rehabilitation mechanism (by design — prevents gaming the system).

## Founding Era Claims

Special tier: `founding`
- Phase 0 deposits from 20 Founders
- Free-form research, no adversarial pressure
- NOT citable (never entered main archive through validation)
- Visible as historical record
- Shows foundational thinking before rival system activated

**Archive tier:** `quarantine` (visible, not citable)
**Status:** `founding`

## Querying by Tier

```python
# Get all citable claims (main tier)
main_claims = db.get_archive_entries(archive_tier="main", status="survived")

# Get all destroyed claims for meta-learning
graveyard = db.get_archive_entries(archive_tier="graveyard")

# Get quarantined claims (retracted + founding)
quarantine = db.get_archive_entries(archive_tier="quarantine")
```

**Frontend display:**
- **Knowledge Base page:** Only main tier (`survived`, `partial`)
- **Debates page:** Main + quarantine (with warnings)
- **Refuted page:** Graveyard tier only
- **State profiles:** All tiers (shows full win/loss record)
