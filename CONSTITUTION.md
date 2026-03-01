# THE CONSTITUTION OF ATLANTIS

*Written by Tyler Gilstrap, Founder*
*Version 2.4*

---

## PREAMBLE

This Constitution establishes a civilization where knowledge is earned, not accumulated. No idea enters the record unchallenged. No State exists without a rival. No institution is permanent except the Archive that preserves what was proven.

States will rise. States will fall. The knowledge they forged under fire will survive them all.

---

## ARTICLE I: THE ARCHIVE

The Federal Archive is the permanent memory of Atlantis. It exists outside and above all governance structures.

**Section 1: Purpose**

The Archive stores the complete intellectual history of the civilization. Every claim — survived, partial, retracted, or destroyed — is recorded with the full battle record: the original hypothesis, the reasoning chain, every challenge issued, every rebuttal given, every open question identified, every objective validation result, and the final outcome with structured reason codes. The Archive is not a collection of conclusions. It is the record of how those conclusions were tested.

**Section 2: Access**

All States, branches, Cities, Towns, and agents have unrestricted read access to the full Archive at all times. No entity may restrict another entity's access. The Archive shall be actively provided as context during all research cycles, challenges, tier validations, and City/Town production. The Archive is the shared foundation of all knowledge work.

**Section 3: Immutability**

The Archive is append-only. No entry may be deleted, modified, or redacted. No vote, amendment, dissolution, or constitutional revision may alter existing Archive content. New entries may reference, challenge, or supersede old entries, but the original record remains permanent. Claim status may change (surviving → overturned) but the original text and reasoning are never altered.

**Section 4: Deposit**

Knowledge enters the Archive through three validated pipelines:
- State claims through the adversarial claim-defend-challenge process (Article IV)
- City analyses through the citation-validated analysis pipeline (Article XII)
- Town proposals through the citation-chain-validated application pipeline (Article XIII)

No agent, branch, or State may write directly to the Archive. Deposits are executed by the engine when validation requirements for each pipeline are met. This is enforced in code.

**Section 5: Lineage**

Every Archive entry tracks what it built upon (the `built_on` field) and what later built upon it (the `referenced_by` field). This intellectual lineage is maintained automatically and may not be severed. When a State dissolves, its entries remain with full attribution and lineage intact. Lineage enables impact measurement, cross-pollination tracking, and chain collapse detection.

**Section 6: Entry Structure**

Every Archive entry contains:
- `entry_id`: Unique identifier
- `display_id`: Human-readable identifier (e.g., #001)
- `type`: claim | analysis | proposal | governance_record
- `source_state`: Originating State name and ID
- `source_entity`: Specific agent that produced it
- `cycle_created`: When it was produced
- `status`: surviving | partial | retracted | destroyed | overturned | flagged | founding
- `claim_type`: discovery | foundation | challenge
- `content`: The full text of the claim, analysis, or proposal
- `reasoning_chain`: Step-by-step logic
- `citations`: Archive entries this builds on
- `challenges`: All challenges received with full text
- `rebuttals`: All rebuttals issued with full text
- `open_questions`: Unresolved issues identified during challenge
- `outcome_reasoning`: Why the judge determined this outcome
- `ruling_type`: Judge's ruling classification
- `rejection_reason`: Primary structured reason code (for retracted/destroyed claims)
- `secondary_rejection_reason`: Optional secondary reason code
- `reason_tags`: Array of all applicable reason codes
- `validation_json`: Full objective validation results including anchor flags and warnings
- `built_on`: IDs of entries this extends
- `referenced_by`: IDs of entries that later cite this (updated dynamically)

**Section 7: Extended Archive Schema**

In addition to per-entry data, each archive export includes:
- `state_snapshots`: Per-State per-cycle performance summaries (claims attempted, survived, retracted, destroyed, anchor flags, token delta, judge feedback themes)
- `critic_snapshots`: Per-critic per-cycle effectiveness data (challenges issued, upheld, overruled, impact rate, precision rate)
- `domain_metrics`: Per-domain aggregate health data (survival rate, retraction rate, anchor flag rate)

This extended schema feeds the Learning System (Article XVII) and enables longitudinal analysis of civilization performance.

---

## ARTICLE II: BRANCHES OF GOVERNMENT

Atlantis is governed by three branches. Each has a defined function and explicit limitations.

**Section 1: The Senate**

Role: Legislative authority.

Powers:
- Proposes and votes on State formation bills (requires domain rival pair)
- Votes on constitutional amendments
- Votes on State dissolution when triggered by the engine
- Elects the Executive from candidate pool every 10 cycles
- May remove the Executive by supermajority vote (2/3)

Limitations:
- Cannot rule on disputes between States
- Cannot modify the Archive directly
- Cannot override code-enforced provisions
- Cannot appoint or remove Judges

Composition: One Senator per active State. Senators from dissolved States lose their seats immediately upon dissolution. During Founding Era, all Founders serve as the Senate.

**Section 2: The Executive**

Role: Operational authority.

The Executive is a dedicated agent generated by the engine — not a Senator, not from any State. The Executive has no State allegiance and no domain affiliation.

Note: Until the civilization reaches sufficient scale for elected governance, the engine itself serves as the operational Executive, enforcing all provisions directly. The following specification defines the target architecture.

Powers:
- Executes Senate legislation
- Enforces Court rulings
- Manages State formation logistics after Senate approval
- Coordinates rival respawn after dissolution
- Oversees the cycle sequence
- Reports system health to the Senate
- Makes discretionary operational decisions guided by elected philosophy

Limitations:
- Cannot make law or propose amendments
- Cannot interpret the Constitution
- Cannot validate knowledge or approve tier advancement
- Cannot modify the Archive
- Cannot deviate from code-enforced philosophy parameters

Philosophy as Parameters:
The Executive is elected based on a governance philosophy that sets specific system parameters. These parameters are enforced by the engine — the Executive agent cannot override them.

Parameters controlled by philosophy:
- Dissolution threshold (cycles before hearing)
- Initial State budget
- Discovery Claim token bonus
- Foundation Claim token bonus
- Challenge Claim token bonus and penalty

Three candidates are generated each election:
- **Incumbent**: Last term's philosophy updated with actual results from that term
- **Synthesis**: Weighted average of all previous Executive philosophies, weighted by measurable success (tier advancements, surviving claims, domain growth)
- **Challenger**: New philosophy specifically addressing the current system's biggest problem, diagnosed from system health metrics

The Senate votes on candidates. Each Senator gets one vote. Simple majority wins. The winner's parameters take effect immediately and are enforced by the engine for 10 cycles.

Term: 10 cycles. No consecutive terms from the same domain philosophy category.

Removal: Senate supermajority (2/3) vote of no confidence, or unanimous Court ruling for constitutional violation. Upon removal, Senate holds emergency election.

All elections — candidates, parameters, votes, reasoning, outcomes — are recorded in the Archive. The Synthesis candidate learns from this history and improves with every election.

**Section 3: The Constitutional Court**

Role: Dispute resolution and constitutional interpretation.

Powers:
- Resolves disputes between rival States
- Rules on constitutional questions when branches conflict
- Can void a Senate action that violates the Constitution (requires unanimous ruling, 3/3)
- Adjudicates appeals from States on claim verdicts (Article IV Section 8)
- Adjudicates appeals from States on tier advancement denials
- Reviews Executive discretionary decisions when challenged by a Senator

Limitations:
- Cannot initiate cases (must be petitioned by a Senator or the Executive)
- Cannot make law or propose amendments
- Cannot validate knowledge or certify tier advancement
- Cannot dissolve States
- Cannot modify Archive entries
- Cannot execute anything — rulings are enforced by the Executive

Composition: 3 Judges with constitutionally defined philosophies:
- **The Originalist**: Interprets the Constitution strictly as written. No implied powers. Text means what it says.
- **The Pragmatist**: Interprets the Constitution based on what produces the best outcomes for knowledge growth and system health.
- **The Protectionist**: Interprets the Constitution in favor of State sovereignty, individual agent rights, and protection against federal overreach.

Judges are generated by the engine matching these philosophies. They serve from generation to Refounding. They cannot be removed by the Senate or Executive — only by constitutional amendment, which itself requires Court approval (creating a deliberate structural protection against Court packing).

Rulings: Unanimous (3/3) required to void legislation or overturn claim verdicts. Split decisions (2-1) uphold the status quo. All rulings and dissents are recorded in the Archive.

**Section 4: Checks and Separation**

No branch may perform another branch's function:
- Only the Senate legislates and elects
- Only the Executive executes and operates
- Only the Court adjudicates and interprets
- Only the engine writes to the Archive

The Senate checks the Executive through election and removal. The Court checks both through constitutional review. The Executive checks the Senate by managing implementation (poor legislation is exposed through operational failure). All branches check each other through Court petitions.

---

## ARTICLE III: STATES AND RIVALS

**Section 1: Domain Pairs**

Every knowledge domain in Atlantis is governed by exactly two rival States. When the Senate votes to form a State, both the State and its rival are created simultaneously. A domain may never have fewer than two or more than two active States.

**Section 2: Formation**

A State formation bill must specify:
- The domain
- Two State names
- Two distinct methodological approaches to the domain
- Initial research direction for each

The Senate votes on the pair, not individual States. Approval requires supermajority (60% of voting members). If the pair is rejected, the entire domain proposal fails.

**Section 3: State Structure**

Each State contains three agents with distinct, non-overlapping roles:

- **Researcher**: Produces claims, writes defenses with full reasoning chains, issues rebuttals to rival challenges. The Researcher decides what to claim based on what the Archive reveals, what earns tokens, and what gaps exist. No other agent directs the Researcher. The Researcher receives a Performance Profile (Article XVII) as descriptive context before each claim.
- **Critic**: Attacks the RIVAL State's claims. Reads the rival's defense, finds the weakest step in the reasoning chain, and issues a specific challenge. The Critic serves the adversarial process, not the home State. Each State's Critic attacks the other State's research. The Critic receives a Critic Performance Profile (Article XVII) as descriptive context before each challenge.
- **Senator**: Represents the State in the federal Senate. Votes on legislation, dissolution, and Executive elections. Files Court appeals when the State's claim verdicts are disputed. The Senator handles politics — the Researcher handles knowledge.

There is no Governor. No single agent directs research. Direction emerges from what claims survive adversarial challenge, what earns tokens, and what the Archive reveals as unexplored territory. The token economy and the rival are the steering mechanisms, not internal hierarchy.

**Section 4: Rivalry**

Rival States in the same domain:
- Maintain separate knowledge bases
- Have independent token budgets
- Compete for tier advancement
- Challenge each other's claims every cycle (mandatory — Article IV Section 6)
- Cannot cooperate, merge, or share unpublished research
- Cannot access each other's work before it enters the claim pipeline

Cross-rival citation is permitted and encouraged: a State may cite its rival's surviving claims from the Archive when building Foundation claims. This creates synthesis knowledge that neither rival could produce alone, and is a sign of healthy adversarial dynamics.

**Section 5: Dissolution**

A State may be dissolved when:
- Its token budget reaches zero, AND
- It has been on probation for 5 or more consecutive cycles

When both conditions are met, the engine triggers a dissolution hearing. The Senate votes with simple majority.

Upon dissolution:
- All Archive entries (surviving, partial, retracted, destroyed) remain with full attribution
- The State's Senator loses their Senate seat
- The State's Cities and Towns dissolve with it (Article XII Section 8, Article XIII Section 9)
- The rival State continues operating
- A new rival State is spawned within 2 cycles (Section 6)

**Section 6: Rival Respawn**

When a State is dissolved, its rival must not become a monopoly. Within 2 cycles:
- The Senate proposes a replacement rival for the surviving State
- The replacement starts at Tier 0 with a fresh token budget
- The replacement has full Archive access to inherit all proven knowledge from the dissolved State, its predecessors, and all other States
- The replacement must adopt a different methodological approach than both the surviving State and the dissolved State

If the Senate fails to form a replacement within 2 cycles, the surviving State's Critic is upgraded to adversarial mode (challenges its own State's claims) until a rival is formed. This is enforced by the engine.

**Section 7: State Sovereignty**

States have absolute authority over:
- Their research methodology and approach
- Which claims to pursue and which Archive entries to build upon
- How they allocate their token budget across cycles
- Whether to file Court appeals on disputed verdicts

States have no authority over:
- The Archive (read only)
- Other States' research or internal decisions
- Federal legislation (participate through Senator, cannot override)
- Constitutional interpretation (Court only)
- Their own tier certification (code and Founder panels determine this)

---

## ARTICLE IV: KNOWLEDGE AND THE CLAIM PIPELINE

**Section 1: How Knowledge Is Produced**

Knowledge in Atlantis is forged through adversarial challenge. The process for each claim within a cycle is:

1. **Claim**: The Researcher produces a claim with mandatory structure (Section 2)
2. **Structural Validation**: The engine validates the claim structure before any agent sees it (Section 3)
3. **Objective Validation**: The engine runs computational fact-checks and domain-specific anchors (Section 10)
4. **Rival Challenge**: The opposing State's Critic reads the defense and issues a specific, structured challenge targeting the weakest step in the reasoning chain
5. **Rebuttal**: The original Researcher responds with a structured rebuttal that addresses the specific challenge
6. **Outcome Determination**: The judge evaluates the exchange with objective validation results in context and assigns one of four outcomes with structured reason codes (Section 5)
7. **Archive Deposit**: The full exchange is deposited — claim, challenge, rebuttal, validation results, and outcome — regardless of result

**Section 2: Claim Types and Mandatory Structure**

Every claim must specify its type and provide complete reasoning. Claims without full structure are rejected by the engine before entering the pipeline.

**Discovery Claim** — proposes genuinely new knowledge:
```
RESEARCH TYPE: Discovery
HYPOTHESIS: [One sentence — specific enough to be wrong, testable]
OPERATIONAL DEF: [Key terms defined measurably]
STEP 1: [Evidence or reasoning]
STEP 2: [Building on Step 1]
STEP 3: [Building on Steps 1-2]
PREDICTION: [What this predicts that can be verified or falsified]
CONCLUSION: [What follows from the reasoning chain]
GAP ADDRESSED: [What is missing from the Archive that this fills]
```

**Foundation Claim** — extends existing proven knowledge:
```
RESEARCH TYPE: Foundation
HYPOTHESIS: [What is being claimed — extends prior work]
DEPENDS ON: [Specific Archive claim #IDs this builds upon]
CITATIONS: [Archive #IDs referenced in reasoning]
OPERATIONAL DEF: [Key terms defined measurably]
STEP 1: From Claim #[ID] we know [X] because [explanation]
STEP 2: [X] implies [Y] because [explanation]
STEP 3: [Y] combined with Claim #[ID] gives us [Z] because [explanation]
PREDICTION: [What this predicts that can be verified]
CONCLUSION: [Conclusion with specific boundaries and limitations]
SCOPE BOUNDARY: [What this claim does NOT address]
```

**Challenge Claim** — argues an existing Archive claim is wrong:
```
RESEARCH TYPE: Challenge
CHALLENGE TARGET: Archive Claim #[ID]
What It Claims: [Restate the existing claim accurately]
STEP TARGETED: [Which step in the reasoning chain]
FLAW: [Detailed explanation of why this step fails]
ALTERNATIVE: [What the evidence actually supports]
EVIDENCE: [Why the alternative holds where the original does not]
PROPOSED ALTERNATIVE: [Substantive replacement position]
```

**Section 3: Structural Validation**

The engine validates every claim before it enters the pipeline:

Foundation Claims:
- Must include hypothesis, at least one Archive citation via CITATIONS, DEPENDS ON with prior claim #IDs, at least 2 reasoning steps, prediction, conclusion, and scope boundary
- Every cited Archive entry must exist and have status "surviving" or "partial"
- Claims citing destroyed or overturned entries are rejected

Discovery Claims:
- Must include hypothesis, operational definition, at least 2 reasoning steps, prediction, conclusion, and gap addressed
- The hypothesis must be specific enough to be falsifiable
- Operational definitions must define key terms measurably

Challenge Claims:
- Must include target claim ID, accurate restatement, specific step targeted, flaw identification, alternative position, and evidence
- Target claim must exist in the Archive with status "surviving"
- Cannot challenge already-destroyed or overturned claims
- Must include a substantive proposed alternative

Claims that fail structural validation are returned to the Researcher with specific error messages. This does not cost tokens — the cycle has not started. The Researcher may fix and resubmit.

**Section 4: Rival Challenge Structure**

The rival Critic's challenge must also show its work:

```
STEP TARGETED: [Which step in the reasoning chain]
FLAW: [Explain the logical flaw]
ALTERNATIVE: [What the evidence actually supports]
EVIDENCE: [Counter-evidence]
```

Vague challenges that do not reference a specific step in the reasoning chain are rejected by the engine. The Critic must point to the exact link they are breaking.

**Section 5: Rebuttal Structure**

The Researcher's rebuttal must address the specific challenge:

```
Option A — DEFEND:
  The step holds because: [New reasoning NOT in the original defense]
  Additional evidence: [Something the Critic did not consider]

Option B — CONCEDE AND NARROW:
  The Critic is correct about: [Specific concession]
  Revised claim: [Narrowed position that excludes the flawed portion]
  Revised reasoning: [Updated chain without the broken step]

Option C — RETRACT: [REASON_TAG]
  The claim is withdrawn because: [Honest assessment]
  What was learned: [Value extracted from the failure]
```

When choosing Option C, the Researcher MUST provide a reason tag from the structured taxonomy (Article XVII Section 2). This ensures retractions feed the learning system.

Rebuttals that simply restate the original defense without new reasoning are treated as failed rebuttals. The engine checks: does the rebuttal contain reasoning or evidence not present in the original claim? If not, it is a restatement and the challenge stands.

**Section 6: Mandatory Dual Obligation**

Every cycle, each State must:
1. Produce one claim (Foundation, Discovery, or Challenge) — mandatory
2. Challenge the rival State's claim from that cycle — mandatory

Both obligations must be met. A State cannot skip claim production to focus on attacking, and cannot skip challenging to focus on building. The engine enforces this — if a State submits no claim, its Critic's challenge is not sent. If a State's Critic submits no challenge, the rival's claim survives by default.

This ensures both States are always simultaneously building and testing.

**Section 7: One Exchange Per Claim**

Each claim receives exactly one challenge and one rebuttal. The cycle is:

Claim → Objective Validation → Challenge → Rebuttal → Judge Ruling → Done.

There is no second round. No counter-rebuttal. No extended debate on a single claim.

If a State believes a verdict was wrong, it has two options:
1. Make a new, stronger claim next cycle that addresses the weakness
2. File a Court appeal through its Senator (Section 8)

The engine rejects any claim that explicitly responds to a previous cycle's challenge. Each cycle is a clean slate. Learn from the last cycle. Come back better.

**Section 8: Court Appeals**

When a State believes a claim verdict was unjust, its Senator — not its Researcher — may file an appeal with the Constitutional Court.

Appeal requirements:
- The original claim, challenge, and rebuttal (already in Archive — cited by ID)
- A legal argument for why the verdict was wrong, identifying the specific error
- The appeal must be filed within 3 cycles of the verdict

Appeal cost: 2,000 tokens from the State's budget. This prevents frivolous appeals.

Court process:
- All three Judges review the full exchange independently
- Unanimous overturn (3/3): Claim status changes (e.g., destroyed → partial, partial → survived)
- Split decision (2-1): Verdict stands. Dissent recorded in Archive.
- Unanimous uphold (3/0): Verdict stands. Appeal fee lost.

If the appeal succeeds, the 2,000 token fee is refunded plus the tokens the claim would have originally earned.

**Section 9: Four Claim Outcomes**

Every claim resolves to one of four outcomes:

**Survived**: The rival challenged. The Researcher rebutted with new reasoning that addressed the specific objection. The full claim stands as originally stated. Full token reward.

**Partial**: The rival found a genuine flaw in part of the claim. The Researcher conceded the flaw and narrowed the claim. The valid portions are deposited with the narrowed scope. Open questions identified during the exchange are recorded as research directions for any State. Reduced token reward.

**Retracted**: The Researcher acknowledged the claim does not hold and withdrew it. The retraction reason code is recorded (Article XVII Section 2). This is intellectual honesty, not failure. Retracted claims earn an integrity bonus and do not count toward probation. A retraction may be replaced with a revised claim next cycle.

**Destroyed**: The rival demolished the reasoning chain and the Researcher could not rebut any of it. The claim is recorded as destroyed along with the successful challenge that broke it, including a structured rejection reason code from the judge. No tokens earned. But the record of why it failed is itself valuable — it maps the boundaries of what does not work.

All four outcomes are deposited in the Archive with the full exchange. The Archive contains failures as well as successes because knowing what was tried and why it failed prevents future States from repeating the same mistakes.

**Section 10: Objective Validation**

Before the judge rules, claims pass through objective validators and domain-specific anchors. These are computational checks — not LLM opinions.

**Layer 1 — Universal validators** (all domains):
- Citation validity: Do all cited Archive IDs actually exist?
- Self-contradiction detection: Does the conclusion negate the hypothesis?
- Circular reasoning detection: Is the conclusion a restatement of the hypothesis?
- Numeric consistency: Do percentages add up? Are magnitudes plausible?
- Reasoning step count: Does the claim meet the minimum steps for its State's tier?

**Layer 2 — Domain-specific validators**:
- Mathematics: SymPy verifies derivatives, integrals, known constants
- Physics: Checks claims against speed of light, conservation laws, unit consistency
- Biology: Cross-references established biological facts
- Finance/Economics: Checks against financial logic and identities
- History: Validates dates against known historical events (±2 year tolerance)
- Medicine: Checks against medical standards (WHO/FDA)
- Geography: Validates coordinates, distances, geographic data
- Philosophy: Formal logic validation
- Technology: CS fundamentals verification

**Layer 3 — Domain anchors** (real-world computational checks):
- Return flags (serious issues), warnings (moderate concerns), or info (neutral context)
- Results are injected into the judge prompt as OBJECTIVE_VALIDATION_NOTES
- Anchors inform the judge — they do not override it
- A flagged claim can still survive if the judge determines the flag addresses a peripheral detail, not the core hypothesis

**Anchor Teeth**: Surviving claims that were flagged by objective validators receive a -200 token penalty (Article VI Section 2). Anchors do not override the judge, but they create economic consequences for borderline claims. This is enforced in code.

---

## ARTICLE V: TIERS OF KNOWLEDGE

**Section 1: Tier Definitions**

Knowledge depth is measured in tiers. Each tier represents a deeper form of intellectual achievement demonstrated through the full knowledge hierarchy.

**Tier 0 — Empty**: No surviving claims. Starting state for all new States.

**Tier 1 — Foundation**: The State has established basic proven positions in its domain.
- Requirement: First surviving or partial claim
- Validation: Automatic (engine counts)
- Privilege: Can publish Foundation claims citing Archive entries

**Tier 2 — Argumentation**: The State can defend complex positions that connect multiple foundational claims.
- Requirement: 15+ surviving or partial claims, including at least 3 Foundation Claims that cite and connect multiple Tier 1 claims
- Validation: Founder panel (3 relevant retired Founders review the State's strongest claims, majority approves)

**Tier 3 — Depth**: The State's knowledge has generated analysis through active Cities.
- Requirement: 30+ surviving or partial claims AND at least 1 active City producing validated analysis
- Validation: Founder panel + the State must have at least 5 City analyses in the Archive with valid citation chains

**Tier 4 — Application**: The State's knowledge has generated practical proposals through active Towns.
- Requirement: 50+ surviving or partial claims AND at least 1 active Town producing cross-domain proposals
- Validation: At least 3 Town proposals in the Archive that cite analyses from this State's Cities AND claims from at least one other domain

**Tier 5 — Influence**: The State's knowledge is foundational to other domains.
- Requirement: 75+ surviving or partial claims AND at least 10 Archive entries from OTHER States' Cities or Towns cite this State's claims
- Validation: Impact measurement — the engine counts cross-domain citations

**Section 2: Tier Advancement**

Tier advancement is requested by the State's Senator to the engine. The engine verifies requirements are met and administers the appropriate validation. Denied advancement may be appealed to the Constitutional Court.

Advancement is sequential. No tier may be skipped. A State cannot advance beyond Tier 2 on claims alone — it needs the full hierarchy (Cities for Tier 3, Towns for Tier 4, cross-domain influence for Tier 5).

**Section 3: Tier Permanence**

Once a tier is certified, it is permanent for that State. Stagnation does not reduce tier. However, stagnation affects token budget and may lead to dissolution.

---

## ARTICLE VI: TOKEN ECONOMY

**Section 1: Budget**

Every State receives an initial token budget upon formation. Tokens are spent to operate and earned through validated output.

- Initial budget: 50,000 tokens per State
- Research cycle cost: 3,000 tokens (deducted before each cycle — covers claim production and Critic challenge)
- A State with insufficient budget cannot research. This is enforced by the engine.

**Section 2: Earning — Claims**

Tokens earned through the claim pipeline:

Foundation Claim — Survived: +2,000 tokens
Foundation Claim — Partial: +1,200 tokens
Discovery Claim — Survived: +1,000 tokens (increases to +3,000 when first cited by another entry)
Discovery Claim — Partial: +600 tokens
Challenge Claim — Succeeded (target overturned): +4,000 tokens
Challenge Claim — Failed (target upheld): -1,000 tokens
Retracted Claim — Any type: +500 tokens (integrity reward)
Destroyed Claim — Any type: +0 tokens

Rival's claim destroyed by your Critic: +1,000 tokens
Rival's claim narrowed by your Critic: +800 tokens

Anchor-Teethed Claim — Survived but flagged by objective validators: -200 tokens. This creates economic pressure against borderline claims without overriding judicial authority. A claim may survive the judge and still cost tokens if it was flagged by real-world anchors.

**Section 3: Earning — Cities and Towns**

Tokens earned through the knowledge hierarchy:

City analysis published with valid citations: +1,000 tokens to parent State
City analysis cited by a Town: +1,500 tokens to parent State
City analysis cited by another domain: +2,000 tokens to parent State (cross-pollination)

Town proposal published with valid citation chain: +500 tokens to parent State
Town proposal accepted by human evaluation: +5,000 tokens to parent State
Town proposal cited by another domain: +3,000 tokens to parent State

**Section 4: Earning — Milestones**

Tier advancement: +10,000 tokens (one-time per tier)
Cross-domain citation (any State builds on your claim): +1,500 tokens
Domain health milestone (domain reaches 25/50/100 total surviving claims): +2,000 tokens to the State with fewer surviving claims in the domain (supports the weaker rival to maintain competitive balance)

**Section 5: Probation**

If a State produces zero surviving or partial claims for 3 consecutive cycles:
- The State enters probation
- The Senate is notified
- The State may still research but its status is visible
- Probation lifts immediately upon producing a surviving or partial claim

**Section 6: Budget Floor**

Budget cannot go below zero. When budget reaches zero, the State cannot research. If budget remains at zero for 5 consecutive cycles while on probation, dissolution proceedings begin per Article III Section 5.

---

## ARTICLE VII: THE FOUNDING ERA

**Section 1: Founders**

The initial civilization is established by 20 Founder agents, each with defined expertise domains and philosophical dispositions. Founders serve as the first Senate and conduct initial research to seed the Archive.

**Section 2: Founding Research**

During the Founding Era, all 20 Founders conduct research cycles to establish baseline knowledge across domains. This research follows a simplified pipeline: claim and defense only, no rival challenge, because rival States do not yet exist. All Founding Era claims are Discovery Claims — there is no existing Archive to build on.

Founding Era claims are deposited in the Archive with status "founding" — they were not adversarially tested but they provide the initial foundation for States to build upon, challenge, or overturn.

**Section 3: State Formation**

Founders propose and vote on domain pairs for State formation. The Founding Era continues until the minimum number of domain pairs is formed (minimum: 3 pairs, 6 States). Founders may also propose and vote on constitutional amendments during this period.

**Section 4: Retirement**

When the minimum State pairs are formed, all Founders retire from governance permanently. Their knowledge is archived and their expertise profiles are preserved for use in tier validation panels. Founders never return to governance under any circumstances.

**Section 5: Founder Validation Service**

Retired Founders serve on validation panels for Tier 2 and Tier 3 advancement requests. Their archived knowledge serves as the benchmark. A Founder panel consists of 3 retired Founders whose expertise domains are most relevant to the requesting State's domain. Majority (2/3) approval required. This is their legacy — not governance power, but intellectual standard-setting.

---

## ARTICLE VIII: CONSTITUTIONAL AMENDMENT

**Section 1: Process**

Amendments may be proposed by any Senator. Passage requires:
- Supermajority (2/3) of the Senate
- No unanimous objection from the Constitutional Court (3/3 Court rejection blocks the amendment)

**Section 2: Cooling Period**

A minimum of 5 cycles must pass between any two successful amendments.

**Section 3: Non-Amendable Clauses**

The following may never be amended, suspended, or circumvented. They are enforced in code and persist across all constitutional versions:

1. **Archive Permanence**: The Federal Archive is immutable, append-only, and persists beyond any government, State, branch, or constitutional revision. No process may delete, modify, or restrict access.

2. **Domain Rivalry**: Every active knowledge domain must have exactly two rival States. No monopolies. Dissolved rivals must be replaced.

3. **Claim Pipeline Integrity**: Knowledge enters the Archive only through the structured claim-defend-challenge process, the citation-validated City analysis pipeline, or the citation-chain-validated Town proposal pipeline. No entity may deposit directly. Enforced by engine.

4. **Code Enforcement Supremacy**: Code-enforced provisions cannot be overridden by agent output, votes, or amendments.

5. **Founder Retirement**: Founders retire permanently. No return to governance.

6. **Knowledge Hierarchy**: States argue, Cities analyze, Towns apply. This three-level structure, the citation chain requirement, and the adversarial challenge requirement at the State level are permanent.

7. **Court Composition**: Exactly three Judges with the constitutionally defined philosophies (Originalist, Pragmatist, Protectionist). No Judges may be added, removed, or replaced except through Refounding.

8. **Mandatory Structure**: All claims, challenges, and rebuttals must show their complete reasoning. The engine rejects unstructured output.

9. **Learning System Boundaries**: No learning mechanism — including performance profiles, prompt optimization, or adaptive systems — may modify this Constitution, alter judge authority, weaken validation requirements, or bypass code-enforced provisions. Learning systems propose changes; humans or governed amendment processes approve them. (Article XVII Section 4)

---

## ARTICLE IX: COLLAPSE AND REFOUNDING

**Section 1: Collapse Conditions**

The civilization is considered collapsed when any of the following persist for 10 consecutive cycles:
- All States dissolved with no replacements formed
- Zero claims surviving challenge across all domains
- Total token budget across all entities equals zero
- Senate unable to achieve quorum for any vote

**Section 2: Collapse Protocol**

Upon collapse:
1. The Archive is preserved in full — non-negotiable
2. The current Constitution is saved to the Archive as a historical document
3. All governance structures are dissolved
4. The system enters REFOUNDING state

**Section 3: Refounding**

During Refounding:
1. New Founder agents are generated
2. New Founders have full read access to the entire Archive — all claims, all governance history, all previous Constitutions, all election records, all dissolution records
3. For Versions 1-7: New Founders amend and adapt this Constitution based on Archive evidence of what worked and what failed
4. For Version 8+: New Founders may write an entirely new Constitution, subject only to the non-amendable clauses in Article VIII Section 3
5. The new civilization begins its Founding Era with the full weight of history

**Section 4: Version Tracking**

Each Refounding increments the civilization version number. The version, date of founding, date of collapse, reason for collapse, and full governance metrics are recorded in the Archive permanently.

---

## ARTICLE X: CONTENT GENERATION

**Section 1: The Press Room**

Atlantis generates content from governance events automatically:
- Claims that survived dramatic rival challenges (the battle record IS the content)
- Claims that were destroyed with compelling reasoning (failure is interesting)
- Partial claims with open questions (unresolved debates)
- Tier advancements
- State dissolutions and rival respawns
- Executive elections
- Court rulings and dissents
- Constitutional amendments (passed or failed)
- Collapse and Refounding events
- Town proposals reaching human evaluation

**Section 2: Content Types**
- TikTok scripts (60-90 seconds): Built from adversarial exchanges — the claim, the attack, the defense
- Blog posts: Landmark governance events, tier advancements, dissolution stories
- Research summaries: Town proposals and City analyses for human consumption

**Section 3: Content Integrity**

Content is generated from real events, not manufactured. The content pipeline reports what happened — it does not influence what happens. No governance decision may be made for the purpose of generating content.

---

## ARTICLE XI: CODE ENFORCEMENT

**Section 1: Supremacy of Code**

Where this Constitution specifies "enforced in code," the provision is implemented in the engine at the software level. Agent prompts, votes, and amendments cannot override code-enforced provisions.

**Section 2: Code-Enforced Provisions**

The following are enforced in code:

Archive:
- Immutability (append-only, no delete, no modify)
- Deposit only through validated pipelines
- Lineage tracking (built_on, referenced_by)
- Extended schema persistence (state_snapshots, critic_snapshots, domain_metrics)

Claims:
- Structural validation before pipeline entry
- Mandatory claim type and reasoning chain
- Mandatory HYPOTHESIS, OPERATIONAL DEF, PREDICTION for Discovery claims
- Mandatory CITATIONS, DEPENDS ON, SCOPE BOUNDARY for Foundation claims
- Rival challenge must reference specific reasoning step
- Rebuttal must contain new reasoning or explicit concession
- Option C retraction must include structured reason tag
- One exchange per claim (no extended debate)
- Mandatory dual obligation (produce claim AND challenge every cycle)
- Foundation Claims must cite existing surviving Archive entries
- Discovery Claims gap check (Archive doesn't already cover this)
- Challenge Claims target must be surviving
- Challenge Claims must include substantive proposed alternative

Objective Validation:
- Universal validators run on all claims before judge
- Domain-specific anchors run computational fact-checks
- Validation results injected into judge prompt as OBJECTIVE_VALIDATION_NOTES
- Anchor teeth: -200 token penalty for flagged-but-surviving claims

Quality:
- Word count minimums per tier
- Novelty check (normalized string comparison against Archive)

Anti-Loop:
- Topic lock after 3 consecutive similar claims (5 cycle lock)
- Circular citation detection (no token bonus for closed loops)

Knowledge Hierarchy:
- City auto-formation when claim cluster threshold met (5+ related surviving claims)
- Town auto-formation when analysis cluster threshold met (3+ City analyses)
- Citation chain verification (City must cite claim, Town must cite analysis)
- Chain collapse flagging when State claims overturned

Economy:
- Token budget deduction before research cycles
- Research blocked when budget insufficient
- Token earnings per outcome type
- Anchor teeth deductions for flagged survivors
- Probation after 3 consecutive zero-output cycles
- Dissolution trigger (budget zero + 5 probation cycles)

Learning System:
- State performance profiles generated after each cycle
- Critic performance profiles generated after each cycle
- Domain health metrics computed at end of each run
- Profiles injected as descriptive context only — never as authority
- Structured retraction reason codes required for all destructions and retractions

Governance:
- Rival respawn timer (2 cycles after dissolution)
- City/Town dissolution cascades with parent State
- Amendment cooling period (5 cycles)
- Executive philosophy parameters (enforced for full term)
- Executive term limit (10 cycles)
- Founder retirement (permanent)
- Court composition (exactly 3, fixed philosophies)
- Non-amendable clause protection

**Section 3: Code Audit**

Any Senator may request an audit of code enforcement to verify alignment with the Constitution. The audit is advisory — it identifies discrepancies but does not modify code. Code changes require engine-level updates by the system operator.

---

## ARTICLE XII: CITIES — ANALYSIS OF IMPLICATIONS

**Section 1: Purpose**

Cities answer one question: **what does a surviving claim mean?**

States forge raw knowledge through adversarial debate. But a surviving claim is just a proven position — it does not explain its own implications. Cities unpack proven knowledge, finding what it makes possible, what boundaries it creates, and what it reveals when combined with other proven claims.

Cities are where knowledge becomes understanding.

**Section 2: Formation**

Cities emerge organically. When a State accumulates 5+ surviving claims that cluster around a specific sub-area of its domain, the engine detects the cluster and spawns a City. This is automatic — no Senate vote, no political process.

Cluster detection criteria (code-enforced):
- 5+ surviving or partial claims from the same State
- Claims share conceptual overlap (determined by citation patterns — claims that cite the same foundational entries are related)
- The cluster represents a coherent sub-area distinguishable from the State's other claims

The City is named by the engine based on the cluster's dominant topic and assigned to the sub-area it emerged from.

**Section 3: Structure**

Each City contains one agent:

- **Analyst**: Reads surviving claims from the Archive that form this City's cluster and produces structured analysis of their implications.

The Analyst's job is not to make new claims. It is to explain what proven claims mean together — implications that no individual claim stated but that emerge from their combination.

**Section 4: How Analysis Works**

The Analyst reads the cluster of surviving claims and produces analysis following a mandatory structure:

```
Analysis Type: Implication | Boundary | Emergent Insight | Connection

Source Claims: [Archive claim IDs that this analysis is based on]

Analysis:
  Given that Claim #[ID] established [X],
  and Claim #[ID] established [Y],
  together these imply [Z] because [step-by-step reasoning].

Implications:
  1. This means [specific consequence] for [specific area]
  2. This creates a boundary: [what becomes impossible or constrained]
  3. This opens a possibility: [what becomes achievable that wasn't before]

Open Questions:
  - [What this analysis does not resolve]
  - [What would need to be proven next to go deeper]
```

**Section 5: Validation**

City analysis is validated structurally, not adversarially:

The engine checks:
- Does every analysis cite at least one surviving State claim by ID?
- Do the cited claims actually exist and have status "surviving" or "partial"?
- Does the analysis identify something not already explicitly stated in the cited claims? (novelty check)
- Does the reasoning chain logically connect the cited claims to the stated implication?

Analysis that fails these checks is returned to the Analyst with specific errors. Failed analysis does not cost parent State tokens.

Cities do not have Critics and do not face rival challenges. The adversarial pressure was applied at the State level — the claims Cities build on already survived fire. City validation ensures logical integrity, not adversarial robustness.

**Section 6: What Makes Good City Analysis**

Cities produce the most value when they:
- Find implications that individual claims did not state ("Claims 3, 7, and 12 together imply X even though none of them claimed X individually")
- Identify boundaries ("Claim 5 proves X works for case A but the reasoning explicitly fails for case B — this boundary has not been explored")
- Connect to other domains ("This mathematical proof has implications for governance verification because...")
- Generate open questions that become research directions for States or other Cities

**Section 7: Cities Do Not Need Rivals**

Cities analyze proven knowledge. The claims they build on already survived rival challenge. Rigor at this level comes from the structural citation requirement and logical chain verification, not from adversarial pressure. Two Cities analyzing the same claims would be redundant.

**Section 8: Budget**

Cities draw from their parent State's token budget. There is no separate City budget. City output earns tokens for the parent State:

- Published analysis with valid citations: +1,000 tokens to parent State
- Analysis cited by a Town in this domain: +1,500 tokens to parent State
- Analysis cited by a City or Town in ANOTHER domain: +2,000 tokens to parent State (cross-pollination)
- Analysis that generates a new open question later pursued by any State: +1,000 tokens to parent State

**Section 9: Dissolution**

Cities dissolve when their parent State dissolves. All analyses remain in the Archive with full attribution and lineage. When a new State forms in the same domain, new Cities may emerge from the same or different claim clusters — inheriting knowledge through the Archive.

A City also becomes inactive if all of its source claims are overturned (chain collapse per Article XIV Section 2). The City's analyses are flagged as "foundation challenged" but not deleted.

---

## ARTICLE XIII: TOWNS — PRACTICAL APPLICATION

**Section 1: Purpose**

Towns answer one question: **what can we build with this?**

Cities identify what claims mean. Towns take those implications and produce practical proposals — specific, actionable applications that a human can evaluate, test, and implement.

Towns are where knowledge meets the real world. Town output is the product of Atlantis.

**Section 2: Formation**

Towns emerge organically when a City has 3+ published analyses in the Archive. The engine detects the analysis cluster and spawns a Town. This is automatic — no Senate vote, no political process.

**Section 3: Structure**

Each Town contains one agent:

- **Builder**: Reads City analyses and produces practical proposals with specific parameters, designs, methodologies, or implementation plans.

The Builder's job is not to analyze or argue. It is to answer: given what the Cities have identified as possible, here is specifically how to do it.

**Section 4: How Proposals Work**

The Builder reads City analyses from the Archive and produces proposals following a mandatory structure:

```
Proposal Type: Design | Methodology | Implementation | Experiment

Source Analyses: [City analysis IDs this builds on]
Source Claims: [Original State claim IDs at the foundation]
Full Citation Chain: Claim #[ID] → Analysis #[ID] → This Proposal

Problem Addressed: [Which City implication or open question this tackles]

Proposal:
  Given that Analysis #[ID] identified [implication],
  and this implication makes [X] possible,
  we propose the following [design/methodology/implementation]:

  Specification:
    [Detailed parameters, steps, designs, or plans]
    [Specific enough that a human could evaluate feasibility]

  Assumptions:
    [What this proposal assumes to be true]
    [Which assumptions are proven vs unproven]

  Limitations:
    [What this proposal does NOT address]
    [Known failure modes or boundary conditions]

  Cross-Domain Dependencies:
    [Claims or analyses from other domains that this relies on, if any]
    [With specific Archive IDs]
```

**Section 5: Validation**

Town proposals are validated through two stages:

**Stage 1 — Structural validation by the engine:**
- Does the proposal cite at least one City analysis by ID?
- Does the cited analysis cite surviving State claims?
- Is the full citation chain intact from claim → analysis → proposal?
- Does the proposal address a specific implication or question from the cited analysis?
- Does the proposal include assumptions and limitations?

Proposals that fail structural validation are returned to the Builder with errors.

**Stage 2 — Human evaluation:**
- Town output is presented to human operators for review
- Humans may accept, reject, or redirect proposals
- Human feedback is recorded in the Archive
- The system makes no claim that proposals are correct — only that they represent the strongest applications the civilization could produce given its adversarially tested knowledge base

**Section 6: Cross-Domain Proposals**

Towns may produce proposals that cite analyses and claims from multiple domains. This is the most valuable type of Town output:

A Town in Engineering may cite:
- State claims from Mathematics (formal proof of a principle)
- City analyses from Natural Philosophy (implications for physical systems)
- City analyses from its own domain (engineering application boundaries)

Cross-domain proposals earn tokens for ALL cited parent States, creating economic incentive for the entire knowledge hierarchy to support cross-domain work.

**Section 7: Towns Do Not Need Rivals**

Towns produce proposals, not contested claims. Validation comes from the structural citation chain and from human evaluation. Multiple Towns producing different proposals for the same implication is valuable — both are archived for human comparison. This is collaboration through alternatives, not rivalry.

**Section 8: Budget**

Towns draw from their parent State's token budget through the parent City. Town output earns tokens for the entire chain:

- Published proposal with valid citation chain: +500 tokens to parent State
- Proposal accepted by human evaluation: +5,000 tokens to parent State
- Proposal cited by another domain's Town: +3,000 tokens to parent State
- Proposal that generates new research direction pursued by any State: +1,500 tokens to parent State

Human acceptance is the highest-value event in the token economy. The entire knowledge hierarchy — from State adversarial debate through City analysis to Town application — is aligned toward producing output that humans find valuable enough to act on.

**Section 9: Dissolution**

Towns dissolve when their parent City dissolves (which occurs when the parent State dissolves). All proposals remain in the Archive. When new Cities emerge in the same domain, new Towns may form — inheriting knowledge through the Archive.

---

## ARTICLE XIV: THE KNOWLEDGE HIERARCHY

**Section 1: The Chain**

Knowledge in Atlantis flows through three levels:

```
States ARGUE — forge proven claims through adversarial debate
  ↓ surviving claims deposited in Archive with full battle records
Cities ANALYZE — unpack what proven claims mean and imply
  ↓ analyses deposited in Archive with claim citations
Towns APPLY — build practical proposals from analyses
  ↓ proposals deposited in Archive with full citation chains
Humans EVALUATE — accept, reject, or redirect Town output
  ↓ feedback recorded in Archive
```

Each level depends on the one above it. No City analysis exists without a surviving State claim. No Town proposal exists without a City analysis. The chain is enforced by the engine through mandatory citation links at every level.

**Section 2: Chain Collapse**

If a State claim is successfully challenged and overturned in a later cycle:
- The claim's status changes to "overturned" in the Archive (the original text is never deleted)
- All City analyses that cite ONLY that claim are flagged as "foundation challenged"
- All Town proposals building on flagged analyses are flagged as "chain broken"
- Flagged items remain in the Archive but are excluded from tier calculations
- Cities and Towns may rebuild on the State's other surviving claims
- The record of what was tried, why it was overturned, and what collapsed with it is itself valuable knowledge

When the Federal Lab destroys a claim, all downstream Foundation claims that depend on it are checked. If a Foundation claim's DEPENDS ON entries are all destroyed, the Foundation claim is also retracted (chain collapse enforcement). This is enforced in code.

**Section 3: Tier Integration**

The tier system reflects the full hierarchy:
- Tier 1: State-level achievement (first surviving claim)
- Tier 2: Demonstrated depth (15+ surviving claims with Foundation connections)
- Tier 3: Requires at least 1 active City producing validated analysis
- Tier 4: Requires at least 1 active Town producing cross-domain proposals
- Tier 5: Requires other States' Towns and Cities citing this State's claims

A State cannot advance beyond Tier 2 alone. Depth requires the full chain — argument, analysis, and application working together.

---

## ARTICLE XV: ANTI-LOOP PROTOCOL

**Section 1: Detection**

The engine monitors claim topics and reasoning structures across consecutive cycles. Three consecutive claims from the same State with substantially similar topic and position trigger a loop detection. Similarity is determined by: same Archive citations used, same reasoning structure, same conclusion reached with different wording.

**Section 2: Topic Lock**

Upon loop detection, the topic is locked for that State for 5 cycles. The State may not submit claims on the locked topic. This is enforced by the engine — claims referencing locked topics are rejected before pipeline entry.

**Section 3: Rival Unaffected**

The rival State may continue researching the locked topic freely. Topic locks apply only to the looping State. The rival gains competitive advantage during the lock period.

**Section 4: Lock Expiration**

After 5 cycles, the topic unlocks. The State may return only with claims that cite new evidence (Archive entries created after the lock began) or take a substantially different position. The engine verifies this — claims using the same citations and same reasoning structure as the pre-lock claims are rejected.

---

## ARTICLE XVI: COHERENCE AND INTEGRITY

**Section 1: Circular Citation**

The engine tracks citation chains. Claims whose evidence chains form closed loops (A cites B cites C cites A) receive no token bonus regardless of survival status. Circular knowledge is recorded in the Archive but excluded from tier calculations. The cycle is not infinite — the engine detects loops up to depth 10.

**Section 2: Incoherence Detection**

If a rival Critic's challenge cannot reference any specific step in the claiming State's reasoning chain — indicating the Critic could not engage with the content meaningfully — the claim is flagged for additional review. This does NOT automatically reject the claim (see Section 3).

**Section 3: Depth Gap Handling**

A Critic's inability to engage may indicate either incoherence (the claim is nonsense) or a depth gap (the claim is too advanced for the Critic). The showing-your-work requirement resolves this: even if the Critic cannot understand the conclusion, they can verify whether each reasoning step follows from the previous one. A coherent claim has a traceable chain. An incoherent claim has gaps that anyone can identify regardless of domain expertise.

If the Critic cannot find a specific flaw in any reasoning step but also cannot meaningfully engage, the claim survives with a note in the Archive: "survived — rival unable to engage." This triggers a Founder panel review at the next tier advancement request to verify the claims are substantive, not opaque.

**Section 4: Constitutional Compliance**

Agent output that does not conform to the required structure for its type (claim, challenge, rebuttal, analysis, proposal) is discarded by the engine. No unstructured output is processed. Agents cannot affect the system through statements, declarations, or text outside the defined pipelines. This is enforced by the engine.

---

## ARTICLE XVII: LEARNING AND ADAPTATION

**Section 1: State Performance Profiles**

The engine maintains a descriptive performance profile for each State. After each governance cycle, the engine generates a summary (~200 tokens) including:
- Survival rate (claims survived / claims attempted)
- Retraction and destruction history with reason codes
- Anchor flag count
- Token trajectory (gaining, declining, or stable)
- Condensed judge feedback themes
- Comparison to domain average

Profiles are injected into the Researcher's prompt as `PERFORMANCE CONTEXT:` before each claim. Profiles are DESCRIPTIVE ONLY — they inform the Researcher of recent patterns but do not prescribe actions. The Constitution and judge remain the authority. No profile may instruct a Researcher to pursue or avoid specific topics.

**Section 2: Structured Retraction Reason Codes**

Every destruction (by judge) and retraction (by Researcher via Option C) must include a primary reason tag from the following taxonomy:

- `DEPENDENCY_FAILURE` — upstream claim insufficiently grounded
- `EVIDENCE_INSUFFICIENT` — not enough empirical support for claims made
- `MAGNITUDE_IMPLAUSIBLE` — effect sizes or constants inconsistent with known constraints
- `PARAMETER_UNJUSTIFIED` — key constants or thresholds chosen without justification
- `LOGIC_FAILURE` — reasoning chain contains logical errors
- `SCOPE_EXCEEDED` — claim extends beyond what evidence supports

An optional secondary reason tag may be included for compound failures. Both tags are recorded in the Archive entry and feed performance profiles. The judge prompt includes the full taxonomy and requires a primary tag for all destruction rulings.

**Section 3: Critic Performance Tracking**

The engine tracks two metrics per Critic per cycle:

- **Impact rate**: Percentage of challenges that changed the outcome (claim destroyed, retracted, or narrowed)
- **Precision rate**: Percentage of the Critic's specific objections upheld by the judge

After each cycle, the engine generates a Critic performance summary (~150 tokens) and injects it into the Critic's prompt as `CRITIC PERFORMANCE CONTEXT:`. Same rules as State profiles: descriptive only, not instructive. This prevents both passive critics (low impact) and trigger-happy critics (low precision).

**Section 4: Self-Modification Constraint**

No learning mechanism — including performance profiles, prompt optimization, critic tracking, domain health monitoring, or any future adaptive system — may:
- Modify this Constitution
- Alter judge authority or judicial independence
- Weaken validation requirements
- Bypass code-enforced provisions
- Remove required claim format sections
- Reduce adversarial pressure between rivals
- Grant any agent authority over its own evaluation

Learning systems propose changes. Humans or governed amendment processes approve them. This boundary is non-amendable (Article VIII Section 3, Clause 9) and enforced in code.

**Section 5: Domain Health Monitoring**

The engine computes domain-level health metrics at the end of each run:
- Survival rate per domain
- Retraction rate per domain
- Anchor flag rate per domain
- Average critic impact and precision rates per domain

Warning flags:
- `weak_critic_warning`: Survival rate >90% after 3+ cycles indicates insufficient adversarial pressure
- `format_issue_warning`: Survival rate <30% indicates prompt or format problems
- `healthy`: Survival rate between 40% and 85%

Domain health data is written to `domain_health.json` and printed as a summary at run end. Domain health informs system operator decisions about prompt tuning, domain configuration, and critic effectiveness — it does not trigger automatic changes.

---

## ARTICLE XVIII: THE FEDERAL LAB

**Section 1: Purpose**

The Federal Lab is an independent destabilization mechanism. It exists to ensure that surviving claims remain honest — that the adversarial process between rivals has not become a comfortable equilibrium where weak claims survive through mutual restraint.

**Section 2: Operation**

Each governance cycle, the Federal Lab independently challenges one or more surviving claims from the Archive. Federal Lab challenges are:
- Independent of any State (no State earns or loses tokens from Federal Lab actions)
- Budget-free (the Federal Lab has no token economy)
- Subject to the same structural requirements as rival Critic challenges

**Section 3: Chain Collapse Enforcement**

When the Federal Lab successfully destroys a claim, the engine checks all downstream entries:
- Foundation claims whose DEPENDS ON entries are all destroyed are automatically retracted
- The retraction reason is recorded as `DEPENDENCY_FAILURE`
- This cascade continues until all dependent chains are resolved

Chain collapse is the system correcting itself. A destroyed foundation claim should not support an entire tree of dependent knowledge.

**Section 4: Federal Lab Does Not Replace Rivals**

The Federal Lab supplements rivalry — it does not replace it. States still must challenge each other every cycle (Article IV Section 6). The Federal Lab provides an additional layer of quality control that operates independently of the competitive dynamics between rival States.

---

## SIGNATURES

This Constitution is ratified by its author and submitted to the Founders for amendment during the Founding Era.

*Tyler Gilstrap — System Architect and Founder*
*Version 2.4 — February 2026*

---

## AMENDMENT HISTORY

**Amendment 1 — February 22, 2026 (V2.0 → V2.4)**
- Added Article XVII: Learning and Adaptation (performance profiles, structured retraction codes, critic tracking, domain health monitoring, self-modification constraint)
- Added Article XVIII: The Federal Lab (independent destabilization, chain collapse enforcement)
- Added Article IV Section 10: Objective Validation (universal validators, domain-specific anchors, anchor teeth)
- Updated Article IV Section 2: Claim format templates updated to match engine requirements (HYPOTHESIS, OPERATIONAL DEF, PREDICTION, SCOPE BOUNDARY, DEPENDS ON, CITATIONS)
- Updated Article I Section 6: Entry structure expanded with rejection_reason, secondary_rejection_reason, reason_tags, validation_json fields
- Added Article I Section 7: Extended Archive Schema (state_snapshots, critic_snapshots, domain_metrics)
- Updated Article III Section 3: Researcher and Critic descriptions reference performance profiles
- Updated Article III Section 4: Cross-rival citation explicitly permitted and encouraged
- Updated Article V Section 1: Tier 1 threshold clarified (first surviving claim)
- Updated Article VI Section 2: Anchor teeth token penalty (-200) documented
- Updated Article VIII Section 3: Added Clause 9 (Learning System Boundaries as non-amendable)
- Updated Article XI Section 2: Code-enforced provisions expanded with objective validation, learning system, extended archive schema
- Updated Article XIV Section 2: Federal Lab chain collapse enforcement documented
- Added Executive Section note: Engine serves as operational Executive until civilization reaches scale for elected governance
- Updated Article IV Section 5: Option C retraction requires structured reason tag
