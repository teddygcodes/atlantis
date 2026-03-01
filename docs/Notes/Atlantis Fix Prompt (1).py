# ATLANTIS FIX PROMPT FOR CLAUDE CODE
# =====================================
# Three critical fixes. Do all three before running again.
#
# FIX 1: State Formation — make it collaborative (mirrors amendment flow)
# FIX 2: Vote prompts — add context so Founders stop rejecting everything
# FIX 3: Content generation — uncomment/fix logger calls, generate TikTok + blog during events
#
# After all three fixes: rm -rf atlantis_mock && python3 -u __main__.py --mock 2>&1 | tee /tmp/atlantis_fixed.log


# ═══════════════════════════════════════════════════════════
# FIX 1: COLLABORATIVE STATE FORMATION
# ═══════════════════════════════════════════════════════════
#
# PROBLEM: State formation in engine.py _run_founding_era() uses a SOLO proposer.
# One Founder writes a bill alone, everyone votes cold with no debate. 
# Result: 6/20, everything fails. 19 Founders had zero input.
#
# FIX: Replace the entire STEP 2: STATE FORMATION block (approx lines 584-674)
# in core/engine.py _run_founding_era() with this collaborative flow:
#
# The new flow mirrors the amendment process:
#   1. Sample 5 Founders for domain suggestions
#   2. Synthesize into one State proposal  
#   3. 2v2 debate (FOR and AGAINST)
#   4. Vote with BOTH arguments visible
#   5. Form state if passed

"""
REPLACE the STEP 2 block in _run_founding_era() with this:
"""

# ─────────────────────────────────────────────────────────
# STEP 2: STATE FORMATION (Collaborative)
# ─────────────────────────────────────────────────────────
print(f"\n  {'─' * 40}")
print(f"  STEP 2: STATE FORMATION")
print(f"  {'─' * 40}")

import random

# Query Archive for context
archive_summary = self.db.get_archive_summary()
existing_domains = [s.domain for s in state_manager.states.values()]
print(f"    Archive: {archive_summary['total_entries']} entries, {archive_summary['unique_domains']} domains")
print(f"    Existing States: {', '.join(existing_domains) if existing_domains else 'None'}")

# 1. COLLABORATIVE PROPOSAL — Sample 5 Founders for State ideas
sample_founders = random.sample(self.founders, min(5, len(self.founders)))
suggestions = []

for founder in sample_founders:
    response = self.llm.complete(
        system_prompt=founder.get_system_prompt(),
        user_prompt=(
            f"FOUNDING ERA — Cycle {founding_era_cycle}\n\n"
            f"YOUR MISSION: The Founders must form {target_states} States before retiring. "
            f"We have {states_formed} so far. We need {target_states - states_formed} more.\n\n"
            f"Existing States: {', '.join(existing_domains) if existing_domains else 'None yet'}\n"
            f"Archive: {archive_summary['total_entries']} entries across {archive_summary['unique_domains']} domains\n\n"
            f"What knowledge domain NEEDS a State that doesn't exist yet? "
            f"Suggest ONE domain and explain why it's essential. One sentence."
        ),
        max_tokens=150,
        temperature=0.7
    )
    suggestion = (response.content or "").strip()
    if suggestion:
        suggestions.append({"founder": founder.name, "suggestion": suggestion})

# 2. SYNTHESIZE into one State proposal
suggestions_text = "\n".join([f"- {s['founder']}: {s['suggestion']}" for s in suggestions])

synthesis_response = self.llm.complete(
    system_prompt="You synthesize Founder suggestions into State Formation Bills.",
    user_prompt=(
        f"FOUNDING ERA — Cycle {founding_era_cycle}\n\n"
        f"The Founders must form {target_states} States. Currently: {states_formed} formed.\n"
        f"Existing domains: {', '.join(existing_domains) if existing_domains else 'None'}\n\n"
        f"FOUNDER SUGGESTIONS:\n{suggestions_text}\n\n"
        f"Pick the SINGLE BEST suggestion — the domain most needed right now.\n"
        f"Write a State Formation Bill:\n\n"
        f"STATE NAME: [creative name]\n"
        f"DOMAIN: [one or two words]\n"
        f"RESEARCH AGENDA: [what this State will investigate]\n"
        f"JUSTIFICATION: [why this domain is essential and what gap it fills]"
    ),
    max_tokens=400,
    temperature=0.7
)

bill_content = synthesis_response.content or "Form a new State for knowledge expansion."
print(f"\n    STATE FORMATION BILL:")
print(f"    {bill_content[:200]}...")

# 3. 2v2 DEBATE — pick supporter and opponent
debaters = random.sample(self.founders, 2)
supporter, opponent = debaters[0], debaters[1]

support_response = self.llm.complete(
    system_prompt=supporter.get_system_prompt(),
    user_prompt=(
        f"STATE FORMATION DEBATE\n\n"
        f"Bill:\n{bill_content[:400]}\n\n"
        f"The Founders must form {target_states} States. We have {states_formed}. "
        f"We need {target_states - states_formed} more before we can retire.\n\n"
        f"YOU ({supporter.name}): Argue IN FAVOR. Why should this State exist? "
        f"What knowledge gap does it fill? Max 200 tokens."
    ),
    max_tokens=200,
    temperature=0.8
)
support_arg = support_response.content or ""

oppose_response = self.llm.complete(
    system_prompt=opponent.get_system_prompt(),
    user_prompt=(
        f"STATE FORMATION DEBATE\n\n"
        f"Bill:\n{bill_content[:400]}\n\n"
        f"Supporter ({supporter.name}) argues:\n{support_arg[:200]}\n\n"
        f"YOU ({opponent.name}): Argue AGAINST or suggest a BETTER domain. "
        f"What's wrong with this proposal? Max 200 tokens."
    ),
    max_tokens=200,
    temperature=0.8
)
oppose_arg = oppose_response.content or ""

print(f"\n    DEBATE:")
print(f"      FOR ({supporter.name}): {support_arg[:150]}...")
print(f"      AGAINST ({opponent.name}): {oppose_arg[:150]}...")

# 4. VOTE — with both arguments visible and mission context
votes = {}
sample_votes_shown = 0

for agent in all_senators:
    vote_response = self.llm.complete(
        system_prompt=agent.get_system_prompt(),
        user_prompt=(
            f"STATE FORMATION VOTE — Founding Era Cycle {founding_era_cycle}\n\n"
            f"MISSION: The Founders must form {target_states} States before retiring. "
            f"Currently {states_formed}/{target_states} formed. "
            f"{'We are behind schedule.' if states_formed < founding_era_cycle else 'On track.'}\n\n"
            f"BILL:\n{bill_content[:300]}\n\n"
            f"FOR ({supporter.name}): {support_arg[:150]}\n"
            f"AGAINST ({opponent.name}): {oppose_arg[:150]}\n\n"
            f"Should this State be formed? Reply with exactly one word: APPROVE or REJECT"
        ),
        max_tokens=10,
        temperature=0.3
    )

    if sample_votes_shown < 3:
        print(f"    DEBUG - {agent.name} raw vote: '{vote_response.content}'")
        sample_votes_shown += 1

    vote_content = (vote_response.content or "").strip().upper()[:20]
    if "APPROVE" in vote_content and "REJECT" not in vote_content:
        votes[agent.name] = "approve"
    elif "REJECT" in vote_content and "APPROVE" not in vote_content:
        votes[agent.name] = "reject"
    else:
        # Ambiguous defaults to APPROVE for State formation (bias toward growth during Founding Era)
        votes[agent.name] = "approve"

approve = sum(1 for v in votes.values() if v == "approve")
reject = sum(1 for v in votes.values() if v == "reject")

print(f"\n    VOTE TALLY:")
approvers = [n for n, v in votes.items() if v == "approve"]
rejecters = [n for n, v in votes.items() if v == "reject"]
print(f"      APPROVE ({approve}): {', '.join(approvers)}")
print(f"      REJECT ({reject}): {', '.join(rejecters)}")

passed = approve / len(votes) > 0.5  # Simple majority

if passed:
    print(f"    ★ Vote PASSED ({approve}/{len(votes)})")

    # Form the State
    try:
        state = state_manager.form_state(
            bill={"title": "State Formation", "content": bill_content, "cycle": founding_era_cycle},
            federal_constitution=constitution,
            cycle=founding_era_cycle
        )

        states_formed += 1
        print(f"    ★ STATE FORMED: {state.name} ({state.domain}) — Tier {state.tier}")

        # State Senator JOINS Senate
        all_senators.append(state.senator)
        print(f"    Senate size: {len(all_senators)} ({len(self.founders)} Founders + {states_formed} State Senators)")

        # State begins research immediately
        print(f"    State {state.name} begins research...")
        state_result = state.run_research_cycle(
            federal_agenda="Explore foundational concepts in your domain",
            llm=self.llm,
            logger=self.logger,
            cycle=founding_era_cycle
        )
        print(f"    Research complete: Tier {state_result.get('tier', 0)}, {len(state_result.get('concepts', []))} concepts")

        # LOG AS HISTORIC EVENT — triggers content generation
        self.logger.log(self.logger._create_entry(
            level="historic",
            category="state_formed",
            title=f"STATE FORMED: {state.name}",
            summary=(
                f"The Founders voted {approve}/{len(votes)} to form {state.name}, "
                f"a new State dedicated to {state.domain}. "
                f"Proposed collaboratively, debated by {supporter.name} (FOR) and {opponent.name} (AGAINST). "
                f"State #{states_formed} of {target_states}."
            ),
            agents=[supporter.name, opponent.name] + approvers[:3],
        ))

    except Exception as e:
        print(f"    ✗ State formation failed: {e}")

else:
    print(f"    ✗ Vote FAILED ({approve}/{len(votes)})")

    # LOG FAILED VOTE — still dramatic content
    self.logger.log(self.logger._create_entry(
        level="dramatic",
        category="state_formation_failed",
        title=f"STATE FORMATION REJECTED",
        summary=(
            f"The Senate voted {approve}/{len(votes)} against forming a new State. "
            f"Bill proposed for domain: {bill_content[:100]}. "
            f"{supporter.name} argued for, {opponent.name} argued against."
        ),
        agents=[supporter.name, opponent.name],
    ))


# ═══════════════════════════════════════════════════════════
# FIX 2: AMENDMENT VOTE LOGGING
# ═══════════════════════════════════════════════════════════
#
# PROBLEM: In founders/convention.py propose_collaborative_amendment(),
# the logger calls are commented out (lines ~1464-1478).
# Amendment passes/failures generate ZERO content.
#
# FIX: Replace the commented-out logger lines in propose_collaborative_amendment()
# In the "if votes['yes'] >= 14:" block (passed), add:

logger.log(logger._create_entry(
    level="historic",
    category="amendment_passed",
    title=f"AMENDMENT PASSED (Cycle {cycle})",
    summary=(
        f"Amendment: {amendment['text'][:200]}. "
        f"Vote: {votes['yes']}/{votes['yes'] + votes['no']}. "
        f"Debated by {supporter.name} (FOR) and {opponent.name} (AGAINST). "
        f"Rationale: {amendment['rationale'][:100]}"
    ),
    agents=[supporter.name, opponent.name],
))

# In the else block (failed), add:

logger.log(logger._create_entry(
    level="dramatic",
    category="amendment_failed",
    title=f"AMENDMENT REJECTED (Cycle {cycle})",
    summary=(
        f"Amendment: {amendment['text'][:200]}. "
        f"Vote: {votes['yes']}/{votes['yes'] + votes['no']}. "
        f"Debated by {supporter.name} (FOR) and {opponent.name} (AGAINST)."
    ),
    agents=[supporter.name, opponent.name],
))


# ═══════════════════════════════════════════════════════════
# FIX 3: REAL-TIME CONTENT GENERATION
# ═══════════════════════════════════════════════════════════
#
# PROBLEM: Content generation only runs AFTER everything finishes (engine.py line 101).
# TikTok scripts and blog posts should generate AS events happen, not at the end.
#
# FIX: Add a method to engine that generates content after each dramatic/historic event.
# Call it after each amendment vote and state formation vote in _run_founding_era().
#
# Add this method to AtlantisEngine class:

def _generate_content_for_event(self, entry):
    """Generate TikTok script and/or blog post for a single event immediately."""
    entry_data = entry if isinstance(entry, dict) else entry.to_dict()

    level = entry_data.get("level", "")

    if level in ["dramatic", "historic"]:
        try:
            self.content_gen.generate_tiktok_script(entry_data)
        except Exception as e:
            print(f"    ⚠ TikTok generation failed: {e}")

    if level in ["significant", "dramatic", "historic"]:
        try:
            self.content_gen.generate_blog_post(entry_data)
        except Exception as e:
            print(f"    ⚠ Blog generation failed: {e}")

#
# Then after EVERY logger.log() call in _run_founding_era(), add:
#   self._generate_content_for_event(entry)
#
# This means content generates in real-time as events happen.
# Jefferson's draft = content. Every amendment debate = content. 
# Every State formation = content. Every failed vote = content.
#
# The _generate_content() at the end of run() still catches anything missed,
# but now you get content DURING the run, not just after.


# ═══════════════════════════════════════════════════════════
# FIX 4 (BONUS): LOG JEFFERSON'S DRAFT AS HISTORIC EVENT
# ═══════════════════════════════════════════════════════════
#
# In engine.py _run_convention(), after Jefferson's draft is parsed
# and before deployment (around line 340), add:

self.logger.log(self.logger._create_entry(
    level="historic",
    category="constitution_drafted",
    title="JEFFERSON WRITES THE CONSTITUTION",
    summary=(
        f"Thomas Jefferson has written the founding Constitution of Atlantis. "
        f"{len(self.blueprint.branches)} branches of government defined. "
        f"{len(self.blueprint.non_amendable_clauses)} non-amendable clauses locked. "
        f"Cycle sequence: {' → '.join(self.blueprint.cycle_sequence)}. "
        f"The government deploys immediately. The Founding Era begins."
    ),
    agents=["Jefferson"],
))


# ═══════════════════════════════════════════════════════════
# SUMMARY OF ALL CHANGES
# ═══════════════════════════════════════════════════════════
#
# 1. core/engine.py _run_founding_era() STEP 2:
#    - Replace solo proposer with collaborative flow (5 suggest → synthesize → debate → vote)
#    - Vote prompt includes mission context ("must form X States") and both debate arguments
#    - Ambiguous votes default to APPROVE during Founding Era (bias toward growth)
#    - Log state formations as "historic" events
#    - Log failed formations as "dramatic" events
#
# 2. founders/convention.py propose_collaborative_amendment():
#    - Uncomment/replace logger calls for amendment passed/failed
#    - Both pass and fail generate content-worthy log entries
#
# 3. core/engine.py AtlantisEngine class:
#    - Add _generate_content_for_event() method
#    - Call it after every logger.log() in _run_founding_era()
#    - Content generates in real-time, not just at the end
#
# 4. core/engine.py _run_convention():
#    - Log Jefferson's draft as historic event
#    - This becomes the first piece of content generated
#
# After all fixes: rm -rf atlantis_mock && python3 -u __main__.py --mock 2>&1 | tee /tmp/atlantis_fixed.log
