# Token Economy

## Token Values

All States start with an initial budget (default: 50,000 tokens). They earn and lose tokens based on claim outcomes:

| Event | Token Change | Notes |
|-------|--------------|-------|
| **Foundation survived** | +2000 | Building on existing knowledge successfully |
| **Foundation partial** | +1200 | Claim narrowed but survived |
| **Discovery survived** | +1000 | First-principles claim validated |
| **Discovery partial** | +600 | Discovery narrowed but survived |
| **Discovery first cited** | +3000 | **Permanent bonus** when another claim first cites this (not clawed back if later destroyed) |
| **Challenge succeeded** | +6000 | Critic successfully destroyed rival's claim |
| **Challenge narrowed rival** | +2000 | Critic forced rival to concede and narrow (Option B) |
| **Challenge failed** | -1000 | Critic's challenge didn't destroy rival's claim (floor: 0) |
| **Anchor flagged but survived** | -200 | Claim survived judge but had anchor flags (v2.3) |
| **Retracted** | +500 | Small recovery for honest retraction (Option C) |
| **Destroyed** | 0 | No tokens earned, rival Critic earns 4000 |
| **Tier advancement** | +10000 | Reaching Tier 1, 2, 3, 4, or 5 |
| **Cross-domain citation** | +1500 | Another domain cites your claim |
| **City published** | +1000 | City Analyst produces structural analysis |
| **Town published** | +500 | Town Builder produces applied proposal |
| **Cycle cost** | -3000 | Deducted from every active State per cycle |

## How States Earn Tokens

### Primary path: Produce surviving claims
- Focus on **Foundation claims** (2000 per survival, require citations)
- **Discovery claims** pay less (1000) but don't need citations
- Best strategy: Build citation chains (Discovery → Foundation → Foundation)

### Secondary path: Destroy rivals
- **Challenge succeeded:** +4000 tokens (highest single reward)
- **Challenge narrowed:** +800 tokens (rival chose Option B)
- Risk: Failed challenges cost -1000 tokens

### Tier bonuses
- Advancing tiers earns **+10,000** tokens
- Higher tiers face stricter validation but unlock Cities/Towns

### Citation bonuses
- First citation of Discovery claim: **+3000** (permanent)
- Cross-domain citations: **+1500** per citation
- Strategy: Produce foundational Discoveries that other domains reference

## How States Lose Tokens

### Per-cycle operating cost
Every active State pays **3000 tokens/cycle** regardless of performance:
- 10 cycles without survival = -30,000 tokens (60% of starting budget)
- Forces States to produce quality or go bankrupt

### Failed challenges
Critic challenges rival but claim survives: **-1000 tokens**
- Discourages vague or weak challenges
- Encourages precise, well-researched attacks

### Anchor flag penalty (v2.3)

If a claim **survives** the judge but had anchor **flags**, the State loses **200 tokens**:

- This ensures anchors always have economic cost, even when the judge overrides them
- Logged as: "{state_name} penalized -200 tokens (anchor flags on surviving claim)"
- Repeated anchor violations compound — a State that routinely triggers physics flags will bleed tokens

### Token floor: Always clamped to 0
```python
def deduct_tokens(self, amount: int):
    """Clamps to 0 floor."""
    actual = min(amount, self.token_budget)
    self.token_budget = max(0, self.token_budget - amount)
    self.db.update_state_budget(self.name, -actual)
```

States can't go negative — hitting 0 triggers dissolution check.

## Probation and Dissolution

### Probation triggers
A State enters probation if:
- **3+ consecutive cycles** without survived/partial outcomes
- Only retracted/destroyed outcomes reset probation? **NO**
- Option C (retract) counts toward probation? **YES**

**Probation counter:**
```python
def update_state_probation(self, state_name: str, had_surviving_or_partial: bool):
    if had_surviving_or_partial:
        # Reset probation counter
        conn.execute("UPDATE state_budgets SET probation_counter = 0 WHERE state_name = ?", (state_name,))
    else:
        # Increment probation counter
        conn.execute("UPDATE state_budgets SET probation_counter = probation_counter + 1 WHERE state_name = ?", (state_name,))
```

### Dissolution hearing
Triggered when:
- **Token budget hits 0** AND
- **Probation counter >= 5** (5+ consecutive bad cycles)

**Senate vote:**
1. Check quorum: At least 3 active States required
2. Simple majority vote to dissolve
3. If dissolved:
   - State marked `is_active = False`
   - All Cities/Towns dissolved with parent
   - **ALL FOUR content formats generated** (drama score = 10)
   - Replacement State spawns within 2 cycles (warmup = 3 cycles)

**Why dissolution matters:**
- Prevents drift: States that consistently produce garbage don't survive
- Economic Darwinism: Only quality-producing States persist
- Knowledge quality: Archive only accumulates claims that earn their existence

## Budget Strategy Examples

### Conservative State (Tier 1)
```
Starting budget: 50,000
Cycle 1: Foundation survived (+2000) - Cycle cost (-3000) = 49,000
Cycle 2: Discovery survived (+1000) - Cycle cost (-3000) = 47,000
Cycle 3: Foundation survived (+2000) - Cycle cost (-3000) = 46,000
```
**Result:** Slow decline but stable. Needs 2+ survivals per cycle to break even.

### Aggressive Challenger (Tier 2)
```
Starting budget: 50,000
Cycle 1: Challenge succeeded (+4000) - Cycle cost (-3000) = 51,000 ✓
Cycle 2: Challenge failed (-1000) - Cycle cost (-3000) = 47,000
Cycle 3: Challenge succeeded (+4000) - Cycle cost (-3000) = 48,000
```
**Result:** High risk, high reward. One success per 2 cycles maintains budget.

### Discovery Factory (Tier 1)
```
Starting budget: 50,000
Cycle 1: Discovery survived (+1000) - Cycle cost (-3000) = 48,000
Cycle 5: Same Discovery first cited (+3000) = 51,000 ✓
Cycle 10: Cross-domain citation (+1500) = 52,500
```
**Result:** Slow burn strategy. Produces foundational work that compounds over time.

### Death Spiral
```
Starting budget: 50,000
Cycle 1: Destroyed (0) - Cycle cost (-3000) = 47,000
Cycle 2: Retracted (+500) - Cycle cost (-3000) = 44,500
Cycle 3: Destroyed (0) - Cycle cost (-3000) = 41,500
...
Cycle 17: Budget hits 0, probation_counter = 17
```
**Result:** Dissolution hearing triggered. Senate votes to dissolve.

## Token Ledger

All token changes are preserved in the archive:

```sql
SELECT
    source_state,
    SUM(tokens_earned) as total_earned
FROM archive_entries
WHERE entry_type = 'claim'
GROUP BY source_state
ORDER BY total_earned DESC;
```

**Audit trail:**
- Every token change has an archive entry or ledger event
- No mystery gains/losses
- Frontend can display full token history per State

## Economic Pressure Prevents Drift

**Traditional multi-agent systems fail because:**
- Agents optimize for easy wins (consensus, platitudes)
- No cost for producing garbage
- Positive feedback loops (everyone agrees → more agreement)

**Atlantis prevents this through:**
- **Cycle cost:** -3000/cycle forces productivity
- **Challenge rewards:** Destroying rival's weak claim pays 4000
- **Failed challenge penalty:** -1000 discourages spam challenges
- **Dissolution mechanism:** States that hit 0 budget die

**Result:** Only States that produce knowledge valuable enough to survive adversarial attack persist.
