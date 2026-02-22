# Roadmap

## Version History and Future Plans

---

## v2.2 (Current - February 2026)

### What Shipped

#### Core Engine
- ✅ **10 Research Domains** - Expanded from 3 to 10 domains via `--demo-10-domains` mode
  - Mathematics, Physics, Biology, Finance, Technology, Medicine, Geography, History, Economics, Philosophy
  - 20 rival States (Alpha/Beta pairs per domain)
  - Guaranteed epistemological diversity: STEM + social sciences + humanities

- ✅ **Validation Persistence** - Archive entries now preserve full validation results
  - `validation_json` column in database
  - Exports to frontend: `{all_passed, flags, warnings, info}`
  - Enables post-hoc analysis of objective validator performance

- ✅ **Dynamic Domain Pairs** - Frontend no longer hardcoded
  - `generate_site_data.py` extracts domain pairs from actual State names
  - TypeScript export: `DOMAIN_PAIRS: DomainPair[]`
  - States page shows all 20 States dynamically

- ✅ **Hypothesis Format Compatibility** - Dual-format support (backward compatible)
  - Old format: `POSITION`, `STEP N`, `CONCLUSION`
  - New format: `HYPOTHESIS`, `OPERATIONAL DEF`, `PREDICTION`, `CONCLUSION`
  - Validation, normalization, and display layers handle both

#### Researcher Agent Fixes
- ✅ **Increased Max Tokens** - 1200 → 2500 tokens for researcher claims
  - Prevents truncation of complex Discovery hypotheses
  - Allows 5+ step reasoning chains for high-tier States

- ✅ **Format Requirements** - Explicit prompting for Extension/Foundation claims
  - `DEPENDS ON: #[prior claim ID]` enforced
  - `SCOPE BOUNDARY: [what this doesn't cover]` required for Foundation
  - Reduces rejection rate for structural validation failures

- ✅ **Section Reordering** - Logical prompt structure
  - Archive context → Meta-learning → Lab hypothesis → Format requirements
  - Improved claim quality from better context flow

#### Frontend Improvements
- ✅ **Complete UI Rebrand** - "Claims" → "Hypotheses" across all components
  - Archive, Debates, Graveyard, State Profile pages
  - Scientific terminology consistency

- ✅ **Navigation Fixes** - Route mapping corrected
  - Knowledge Base → `/archive`
  - Peer Review → `/debates`
  - Refuted → `/graveyard`

- ✅ **Null Safety** - State profile no longer crashes on empty arrays
  - Guard clauses for `stateHypotheses.length === 0`
  - Graceful fallback messages

- ✅ **Archive Filters** - Now shows "SURVIVED" claims (was broken)
  - Filter includes: `SURVIVED`, `REVISE`, `PARTIAL`
  - Stats page reflects actual survival counts

#### Infrastructure
- ✅ **Critical Bug Fixes** - 8 high-priority issues resolved
  - API_CONFIG keys (model, max_tokens, temperature) added
  - Cost tracking model IDs corrected
  - Ruling type mapping fixed (REJECT_SCOPE → destroyed)
  - Retracted outcome handling added

- ✅ **Documentation** - 10 comprehensive wiki pages
  - Home, Architecture Overview, How Claims Work
  - Objective Validators, Token Economy, Knowledge Tiers
  - Model Routing, Research Domains, Running Atlantis, Roadmap

### Known Issues
- ⚠️ Knowledge graph performance degrades with >100 nodes (O(n²) force calculations)
- ⚠️ No log rotation for `api_errors.log` (can grow to gigabytes)
- ⚠️ Federal Lab rotation cooldown can skip cycles if only one domain eligible

---

## v2.3 (Next - March 2026)

### Planned Features

#### Anchor Teeth - Make Validators Enforceable
**Status:** Proposed

**Problem:** Domain anchors currently "inform" the judge but don't enforce hard constraints. A claim flagged for `speed > c` can still survive if the rebuttal is persuasive, even if the physics violation remains.

**Solution:** Add "fatal flag" category that auto-destroys claims without judge review.

**Implementation:**
```python
# governance/anchors.py
class AnchorResult:
    fatal_flags: List[str]   # Auto-reject (e.g., "claimed speed 5×10⁹ m/s exceeds c")
    soft_flags: List[str]    # Judge evaluates (e.g., "missing citation to main-tier claim")
    warnings: List[str]      # Info only (e.g., "cites quarantine-tier claim")

# governance/states.py
if validation_result.get("fatal_flags"):
    # Skip judge, auto-destroy
    return {
        "outcome": "destroyed",
        "reasoning": f"Fatal validation failure: {validation_result['fatal_flags'][0]}",
        "scores": {"drama": 1, "novelty": 1, "depth": 1}
    }
```

**Benefits:**
- Reduces API costs (skip judge LLM call for obvious violations)
- Enforces computational correctness (math errors can't survive via rhetoric)
- Clearer distinction: anchors verify facts, judges evaluate reasoning

**Risk:** Over-aggressive fatal flags could reject valid edge cases. Requires careful anchor design and escape hatch for "but this is a special case because..." explanations.

---

#### Researcher Prompt Enhancement - Context Windowing
**Status:** In Development

**Problem:** Researcher agents see only last 3-5 destroyed claims for meta-learning. Misses long-term patterns like "all my physics claims violate dimensional analysis."

**Solution:** Structured context with:
1. **Success patterns** - Last 3 survived claims from this State
2. **Failure patterns** - Last 5 destroyed claims with grouped rejection reasons
3. **Domain trends** - Current DMI phase and what it means for standards

**Example Prompt Addition:**
```
YOUR SUCCESS PATTERNS:
#042 (survived): Foundation claim citing 3 main-tier claims, 4-step reasoning
#038 (survived): Discovery with operational definition and 5-step chain
Pattern: Claims with operational definitions and 4+ steps survive Tier 2 validation

YOUR FAILURE PATTERNS:
#051 (destroyed): REJECT_CITATION - cited quarantine-tier claim #017
#049 (destroyed): REJECT_SCOPE - claimed universality without evidence
#045 (destroyed): REJECT_LOGIC - circular reasoning detected
Pattern: 60% of your rejections are citation/scope issues, not reasoning depth

DOMAIN HEALTH (Physics):
Current Phase: Argumentation (survival rate 55%)
Trend: Standards tightening, judges expect 3+ citations and 4+ steps
Recommendation: Build on existing foundation rather than first-principles claims
```

**Implementation:** Add `_get_success_patterns()` and `_get_failure_patterns()` methods to pull structured insights from archive.

---

#### Content Pipeline - Automated TikTok Scripts
**Status:** Proposed

**Vision:** Governance events (destroyed claims, dissolutions, tier advancements) automatically generate short-form video scripts optimized for TikTok/YouTube Shorts.

**Format Types (from v2.2):**
1. **Blog** (500-1000 words) - Science journalist style
2. **Newsroom** (150-200 words) - Breaking news
3. **Debate** (60-90s TikTok script) - Sports commentary play-by-play ← **EXPAND THIS**
4. **Explorer** (200-300 words) - First-person travel blog

**New:** Video Generation Pipeline
```
High-Drama Event (drama ≥ 8)
    ↓
Content Generator writes 60s script
    ↓
TTS (ElevenLabs API): Convert to voiceover
    ↓
Video Assembly (FFmpeg): Text overlays + B-roll stock footage
    ↓
Upload to TikTok API (auto-post with hashtags)
```

**Example Script (from actual v2.2 run):**
```
[COLD OPEN]
Physics just had a PARADIGM FIGHT.

[SETUP - 0:05]
Mathematics_Alpha claimed: "Dark energy is emergent spacetime encoded as quantum error-correction."

Sounds crazy. But the math checked out.

[CONFLICT - 0:15]
Physics_Beta challenged: "This violates the holographic principle. Information density exceeds Bekenstein bound."

Mathematics_Alpha rebutted: "Holographic bound applies to BULK spacetime, not the boundary theory where entanglement lives."

[CLIMAX - 0:30]
Judge ruled: PARTIAL.

The claim survives... but narrowed. Only applies to AdS/CFT correspondence, not general spacetime.

[RESOLUTION - 0:45]
Why this matters: If spacetime IS error-correction, black holes aren't destroying information—they're PROTECTING it.

That's not just physics.
That's the universe debugging itself.

[CTA - 0:55]
Follow for more intellectual cage matches.
Next: Can behavioral finance predict the next crash?

#Physics #QuantumMechanics #DarkEnergy #ScienceTok
```

**Challenges:**
- TTS quality (needs emotion, pacing, emphasis)
- B-roll sourcing (copyright-free physics animations?)
- Moderation (some destroyed claims might be inflammatory)

---

#### Supreme Court (Opus 4.6 Judges)
**Status:** Designed, Not Implemented

**From CONSTITUTION.md §6.2:**
> "A special Supreme Court convenes for appeals with extraordinary implications.
> Three Opus judges. Unanimous (3/3) vote required to overturn.
> Activated when: appeal involves paradigm shift OR chain collapse affects 10+ claims."

**Trigger Conditions:**
```python
def check_supreme_court_eligibility(appeal_data: dict) -> bool:
    # Condition 1: Paradigm shift flag (drama >= 9 AND novelty >= 9)
    if appeal_data["drama"] >= 9 and appeal_data["novelty"] >= 9:
        return True

    # Condition 2: Chain collapse risk
    if len(appeal_data["dependent_claims"]) >= 10:
        return True

    return False
```

**Cost:** 3 Opus judges = ~$45 per appeal (vs $3 for Sonnet judge). Reserved for rare, high-stakes cases.

**Implementation Blockers:**
- Opus 4.6 API access (currently available)
- Prompt design for unanimous consensus (how to structure 3-judge deliberation?)
- Test cases (need real governance history to validate triggers)

---

## v3.0 (Future - 2026 Q3)

### The Beast - Commercial Application Integration

**Vision:** Atlantis's adversarial validation system applied to real-world commercial estimation problems, starting with electrical lighting design.

**Use Case: Lighting Takeoffs**

Current process:
1. Estimator receives architectural plans (PDF)
2. Manually counts fixtures, calculates labor hours
3. Submits bid ($50K-$500K projects)
4. 20-30% error rate (missed fixtures, wrong labor multipliers)

**Atlantis Integration:**
```
PDF Plans
    ↓
[Researcher Agent A]: Extract fixture counts using vision model
    ↓
[Researcher Agent B]: Calculate labor hours using NEC code + local rates
    ↓
[Critic Agent]: Challenge both (missed rooms? wrong fixture types?)
    ↓
[Judge Agent]: Validate final takeoff
    ↓
Confidence Score: 95% ± $2,500
```

**Why Adversarial Helps:**
- **Researcher A** (optimistic): "This is a 2-gang box, 0.5 labor hours"
- **Critic** (skeptical): "Plans show GFCI required, that's 0.8 labor hours + $45 device cost"
- **Judge**: "Critic correct. NEC 210.8 requires GFCI in wet locations. Adjust estimate."

**Architecture Changes Needed:**

1. **Domain-Specific Anchors**
   ```python
   # governance/anchors.py - new domain
   def check_nec_compliance(claim_text: str, plans_metadata: dict) -> dict:
       """Validate electrical code compliance."""
       # Extract claimed circuit breaker size
       # Check against NEC Table 310.16 for wire gauge
       # Flag if undersized
   ```

2. **Vision Model Integration**
   ```python
   # core/vision.py - NEW FILE
   class VisionProvider:
       def extract_fixture_schedule(self, pdf_path: str) -> List[dict]:
           """Use Claude Vision to parse fixture schedule from plans."""
   ```

3. **Cost Estimation Domain**
   ```python
   COMMERCIAL_DOMAINS = {
       "Lighting_Design": {
           "approach_a": "fixture-centric (count first, labor second)",
           "approach_b": "labor-centric (hours first, materials second)",
           "anchor_type": "nec_compliance",
       },
       "Electrical_Estimation": {
           "approach_a": "top-down ($/sqft benchmarks)",
           "approach_b": "bottom-up (per-device pricing)",
           "anchor_type": "pricing_database",
       },
   }
   ```

4. **Confidence Scoring**
   ```python
   # New metric: estimation uncertainty
   class TakeoffEntry(ArchiveEntry):
       confidence_interval: tuple[float, float]  # ($47,500, $52,500)
       risk_factors: List[str]  # ["underground feed depth unknown", "permit costs TBD"]
   ```

**Revenue Model:**
- SaaS: $500/month per estimator seat
- Pay-per-takeoff: $50-$200 per project (based on size)
- API: $0.10 per fixture analyzed

**Target Market:**
- Electrical contractors (10K+ companies in US)
- MEP engineering firms
- General contractors (subcontractor validation)

**Challenges:**
- **Regulatory:** NEC compliance liability (who's responsible if estimate is wrong?)
- **Data:** Need large dataset of plans + actual costs for training
- **UX:** Estimators won't use CLI - needs web interface
- **Trust:** Adoption requires proving accuracy > human estimators (95%+ on test set)

---

### Content Pipeline v2 - Full Video Generation

**From v2.3's TikTok scripts →** Full autonomous video production:

**Pipeline:**
```
Governance Event (drama ≥ 8)
    ↓
[Script Generator]: 60s TikTok script (Haiku LLM)
    ↓
[Voiceover]: Text-to-speech (ElevenLabs API)
    ↓
[Visual Assets]: Stock footage search (Pexels API) + AI-generated diagrams (DALL-E)
    ↓
[Video Assembly]: FFmpeg compositing (text overlays, transitions, captions)
    ↓
[Auto-Upload]: TikTok/YouTube Shorts APIs
    ↓
[Analytics]: Track views, engagement, virality
```

**Content Types:**

1. **Intellectual Cage Matches** (drama ≥ 8)
   - Format: Split-screen "versus" style
   - Voiceover: Hype commentator (sports announcer energy)
   - B-roll: Abstract physics/biology animations

2. **Knowledge Autopsies** (destroyed claims)
   - Format: CSI-style investigation
   - Voiceover: Calm, analytical narrator
   - B-roll: Slow-motion "explosion" effects for claim destruction

3. **State Obituaries** (dissolutions)
   - Format: Documentary tribute
   - Voiceover: Somber reflection
   - B-roll: "Ruins explorer" footage (from Explorer content format)

4. **Milestone Celebrations** (tier advancements, first citations)
   - Format: Celebration montage
   - Voiceover: Triumphant, inspirational
   - B-roll: Upward graphs, confetti effects

**Monetization:**
- Ad revenue from TikTok Creator Fund / YouTube Partner
- Sponsorships (educational platforms, research tools)
- Affiliate links (textbooks, courses on featured topics)

**Success Metrics:**
- 10M+ views/month across platforms
- 1% click-through to Atlantis website
- 100K+ followers by end of 2026

---

## Experimental Features (Research)

### Multi-Model Judging (Ensemble Validation)
**Idea:** Instead of single Sonnet judge, use 3 independent models:
- Claude Sonnet 4.5
- GPT-4o
- Gemini 1.5 Pro

Majority vote determines outcome. Reduces single-model bias.

**Cost:** 3x judge calls (~$0.90/cycle vs $0.30)
**Benefit:** More robust rulings, less vulnerable to model-specific quirks

---

### Human-in-the-Loop Validation
**Idea:** High-stakes appeals (drama ≥ 9) require human expert review before finalization.

**UI:** Web dashboard showing:
- Original claim, challenge, rebuttal
- Judge's proposed ruling
- Validation flags, anchor warnings
- "Approve" or "Override" buttons

**Use Case:** Before destroying a claim with 10+ dependents, human expert verifies the chain collapse is justified.

**Challenge:** Sourcing domain experts, compensating them, maintaining speed

---

### Reinforcement Learning for Researchers
**Idea:** Researcher agents learn from survival patterns via RL.

**Reward Signal:**
- +10 for survived claim
- +5 for partial
- -5 for destroyed
- -10 for rejection before judge

**Training Loop:**
1. Agent generates claim
2. Pipeline runs (validation → challenge → rebuttal → judge)
3. Outcome determines reward
4. Agent updates policy (prompt engineering via RL)

**Hypothesis:** Over 100+ cycles, agents learn to:
- Cite more frequently (reduces REJECT_CITATION)
- Add operational definitions (reduces missing_operational_definition)
- Increase reasoning depth (survives judge scrutiny)

**Challenge:** Prompt optimization is slow (each cycle = 20 minutes), RL requires 1000+ iterations

---

## Community Requests

### Feature Voting (Top 5)
1. **Export to Obsidian** - Archive entries as linked markdown notes
2. **Mobile App** - iOS/Android for reading debates on-the-go
3. **RSS Feed** - Subscribe to high-drama governance events
4. **LaTeX Support** - Render math equations in claims
5. **Collaborative Mode** - Multiple humans can submit claims as States

Vote at: https://github.com/yourusername/atlantis/discussions

---

## Version Numbering

- **v2.x** - Adversarial governance engine (current architecture)
- **v3.x** - Commercial applications (The Beast + industry integrations)
- **v4.x** - Full autonomy (self-improving Constitution, RL-trained agents)

**Semantic Versioning:**
- Major (2 → 3): Breaking changes, new architecture
- Minor (2.2 → 2.3): New features, backward compatible
- Patch (2.2.0 → 2.2.1): Bug fixes only

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- How to propose features
- Pull request guidelines
- Roadmap prioritization process

**Roadmap Updates:** Reviewed quarterly based on user feedback and technical feasibility.
