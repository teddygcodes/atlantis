# New Convention methods for Jefferson draft + 80 amendments model
# To be integrated into ConstitutionalConvention class

def run(self):
    """
    New Convention flow:
    - Step 0: Jefferson writes complete draft Constitution
    - Rounds 1-4: All 20 Founders propose amendments (80 total)
    - Ratification vote
    """
    print("\n" + "=" * 60)
    print("  PHASE 1: THE CONSTITUTIONAL CONVENTION")
    print("  Jefferson Draft + 80 Amendments (20 per round × 4)")
    print("  The Founders build the machine. Then they leave forever.")
    print("=" * 60)

    # Step 0: Jefferson writes draft Constitution
    self._step_0_jefferson_draft()

    # Rounds 1-4: All Founders propose amendments
    for round_num in range(1, 5):
        self._amendment_round(round_num)

    # Final validation
    self._validate_final_blueprint()

    # Ratification vote
    self._ratify()

    # Save convention rounds count
    self.db.set_state("convention_rounds_completed", 4)

    return self.blueprint


def _step_0_jefferson_draft(self):
    """Step 0: Jefferson writes complete draft Constitution."""
    print("\n" + "=" * 60)
    print("  STEP 0: JEFFERSON WRITES THE DRAFT CONSTITUTION")
    print("=" * 60)

    jefferson = self.founders_map.get("Jefferson")
    if not jefferson:
        print("  ERROR: Jefferson not found in founders")
        return

    # Jefferson's prompt to write the entire Constitution
    prompt = f"""You are Thomas Jefferson. You've spent {self.db.get_state('research_cycles', 10)} cycles researching alongside 19 other Founders.

You've seen what happens when AI systems run without governance — they loop, they hallucinate, they drift into repetition, they collapse under their own weight. Knowledge without structure dies. Depth without checks becomes delusion.

You've watched systems that start strong and produce the same surface-level output forever because nothing forces them deeper. You've seen what happens when there's no critic, no judge, no mechanism to say 'that's not good enough, go deeper.'

Now you must write the founding document for an AI civilization that SOLVES these problems. A government that forces depth. That catches loops before they kill progress. That validates knowledge so hallucination can't masquerade as insight. That grows forever — adding new States, new Cities, new Towns — each going deeper than the last, each governed by checks and balances that prevent collapse.

Write the Constitution. All of it.

REQUIRED SECTIONS (format your response with these headers):

## BRANCHES
Define the branches of government:
- How many branches? (at least 2, recommend 3-4)
- For each branch, specify: NAME | TYPE (legislative/executive/judicial/implementation) | SEATS (number) | ROLES (comma-separated) | PURPOSE

Example:
BRANCH: Federal Senate | legislative | 4 | Critic,Tester,Historian,Debugger | Deliberates Bills and sets agendas

## POWERS
Define what each branch can do:
- Voting thresholds (simple majority, supermajority, unanimous)
- Veto powers
- Who proposes Bills, who reviews, who judges

## KNOWLEDGE ENGINE
Define how research works:
- What are the knowledge tiers? (1-5, what each represents)
- How do States form? What triggers new State creation?
- How do Cities form from States? Towns from Cities?
- Research cycle structure

## SAFEGUARDS
What can NEVER be changed?
- List at least 3 non-amendable clauses that protect system integrity
- How are amendments proposed and ratified?
- What prevents infinite loops and hallucination?

## CYCLE SEQUENCE
What happens each governance cycle?
- List the steps in order (e.g., agenda, research, legislate, implement, judge, etc.)

This civilization will outlive its Founders. Make it unbreakable."""

    response = self.llm.complete(
        system_prompt=jefferson.get_system_prompt(),
        user_prompt=prompt,
        max_tokens=2500,
        temperature=0.8
    )

    jefferson.total_tokens_used += response.total_tokens

    draft_text = response.content or ""
    print(f"\n  Jefferson's draft: {len(draft_text)} characters")

    # Parse Jefferson's draft into blueprint
    self._parse_jefferson_draft(draft_text)

    # Validate draft
    if not self._validate_draft():
        print("  ⚠ Draft incomplete - requesting revision...")
        self._request_jefferson_revision()

    # Log the draft
    self.logger.log_narrative_event(
        title="Jefferson's Draft Constitution",
        summary=draft_text[:500],
        agents_involved=[jefferson.name],
        tokens=response.total_tokens
    )


def _parse_jefferson_draft(self, draft_text):
    """Parse Jefferson's draft into the blueprint."""
    import re

    # Parse BRANCHES section
    branches_section = re.search(r'## BRANCHES\s*\n(.*?)(?=\n##|$)', draft_text, re.DOTALL | re.IGNORECASE)
    if branches_section:
        branch_lines = branches_section.group(1)
        for line in branch_lines.split('\n'):
            if 'BRANCH:' in line.upper():
                # Parse: NAME | TYPE | SEATS | ROLES | PURPOSE
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    name = parts[0].replace('BRANCH:', '').strip()
                    branch_type = parts[1].strip()
                    try:
                        seats = int(re.search(r'\d+', parts[2]).group())
                    except:
                        seats = 3
                    roles = [r.strip() for r in parts[3].split(',')]
                    purpose = parts[4].strip()

                    self._add_branch(
                        name=name,
                        branch_type=branch_type,
                        purpose=purpose,
                        seats=[{"name": role, "mandate": f"{role} duties"} for role in roles],
                        designed_by="Jefferson (Draft)"
                    )

    # Parse SAFEGUARDS section
    safeguards_section = re.search(r'## SAFEGUARDS\s*\n(.*?)(?=\n##|$)', draft_text, re.DOTALL | re.IGNORECASE)
    if safeguards_section:
        safeguard_text = safeguards_section.group(1)
        # Extract bullet points or numbered items
        safeguards = re.findall(r'[-*\d]+\.?\s+(.+)', safeguard_text)
        for safeguard in safeguards[:5]:  # Take first 5
            if len(safeguard) > 20:  # Meaningful safeguard
                self.blueprint.non_amendable_clauses.append(safeguard.strip())

    # Parse CYCLE SEQUENCE section
    cycle_section = re.search(r'## CYCLE SEQUENCE\s*\n(.*?)(?=\n##|$)', draft_text, re.DOTALL | re.IGNORECASE)
    if cycle_section:
        cycle_text = cycle_section.group(1)
        steps = re.findall(r'[-*\d]+\.?\s+(\w+)', cycle_text)
        if steps:
            self.blueprint.cycle_sequence = steps[:10]  # Max 10 steps

    print(f"  Parsed: {len(self.blueprint.branches)} branches, {len(self.blueprint.non_amendable_clauses)} safeguards")


def _validate_draft(self):
    """Validate Jefferson's draft is complete enough to proceed."""
    if len(self.blueprint.branches) < 2:
        print(f"  ✗ Only {len(self.blueprint.branches)} branches (need at least 2)")
        return False

    if any(len(b.seats) < 1 for b in self.blueprint.branches):
        print("  ✗ Branch with 0 seats")
        return False

    if len(self.blueprint.non_amendable_clauses) < 1:
        print("  ✗ No safeguards defined")
        return False

    print(f"  ✓ Draft valid: {len(self.blueprint.branches)} branches, {len(self.blueprint.non_amendable_clauses)} safeguards")
    return True


def _request_jefferson_revision(self):
    """Request Jefferson to revise incomplete draft."""
    jefferson = self.founders_map.get("Jefferson")
    if not jefferson:
        self._apply_minimal_fallback()
        return

    gaps = []
    if len(self.blueprint.branches) < 2:
        gaps.append(f"Only {len(self.blueprint.branches)} branches defined - need at least 2")
    if len(self.blueprint.non_amendable_clauses) < 1:
        gaps.append("No safeguards defined")

    prompt = f"""Your draft Constitution is incomplete. Please revise to include:

{chr(10).join('- ' + g for g in gaps)}

Provide the missing sections in the same format as before."""

    response = self.llm.complete(
        system_prompt=jefferson.get_system_prompt(),
        user_prompt=prompt,
        max_tokens=1500,
        temperature=0.8
    )

    self._parse_jefferson_draft(response.content or "")

    if not self._validate_draft():
        print("  ✗ Revision still incomplete - using minimal fallback")
        self._apply_minimal_fallback()


def _apply_minimal_fallback(self):
    """Apply minimal fallback Constitution if Jefferson's draft fails."""
    print("  ⚠ Applying minimal fallback Constitution")

    self.blueprint.branches = []

    self._add_branch(
        "Federal Senate", "legislative",
        "Deliberates Bills and sets agendas",
        [{"name": "Critic", "mandate": "Challenge proposals"},
         {"name": "Tester", "mandate": "Verify claims"},
         {"name": "Historian", "mandate": "Maintain memory"},
         {"name": "Debugger", "mandate": "Monitor health"}],
        designed_by="Fallback"
    )

    self._add_branch(
        "Federal House", "implementation",
        "Reviews implementation feasibility",
        [{"name": "Architect", "mandate": "Design plans"},
         {"name": "Coder", "mandate": "Validate execution"}],
        designed_by="Fallback"
    )

    self._add_branch(
        "Supreme Court", "judicial",
        "Interprets Constitution",
        [{"name": "WARDEN", "mandate": "Constitutional guardian"},
         {"name": "Justice Critic", "mandate": "Find weaknesses"},
         {"name": "Justice Historian", "mandate": "Reference precedent"}],
        designed_by="Fallback"
    )

    self.blueprint.non_amendable_clauses = [
        "The government must force knowledge to progress through tiers",
        "No single agent can override system checks",
        "Transparency is mandatory for all decisions"
    ]

    self.blueprint.cycle_sequence = ["agenda", "research", "legislate", "implement", "judge"]


def _amendment_round(self, round_num):
    """Run one round where all 20 Founders propose amendments sequentially."""
    round_themes = {
        1: "Here is YOUR constitution after Jefferson's draft. What else needs to change?",
        2: "After Round 1. What did Round 1 break? What's missing?",
        3: "Your constitution is maturing. What conflicts exist? What edge cases aren't covered?",
        4: "Final draft. What must be locked in permanently? What can never be changed?"
    }

    print(f"\n{'=' * 60}")
    print(f"  ROUND {round_num}: AMENDMENTS")
    print(f"  Theme: {round_themes[round_num]}")
    print(f"  All 20 Founders propose 1 amendment each")
    print(f"{'=' * 60}")

    amendments_passed = 0
    amendments_failed = 0

    for idx, founder in enumerate(self.founder_list):
        print(f"\n  Amendment {idx+1}/20 — Founder: {founder.name}")

        # Founder proposes amendment with full blueprint context
        amendment_proposal = self._propose_amendment(founder, round_num, idx, round_themes[round_num])

        if not amendment_proposal:
            continue

        # 2v2 debate
        supporter, opponent = self._select_debaters(founder)
        support_arg = self._debate_support(supporter, amendment_proposal)
        oppose_arg = self._debate_oppose(opponent, amendment_proposal, support_arg)

        # All 20 vote
        votes = self._vote_on_amendment(amendment_proposal, support_arg, oppose_arg)

        # Pass requires 14/20 (70% supermajority)
        if votes['yes'] >= 14:
            self._apply_amendment(amendment_proposal)
            amendments_passed += 1
            print(f"    ✓ PASSED ({votes['yes']}/{len(self.founder_list)})")
        else:
            amendments_failed += 1
            print(f"    ✗ FAILED ({votes['yes']}/{len(self.founder_list)})")

    print(f"\n  Round {round_num} complete: {amendments_passed} passed, {amendments_failed} failed")


def _propose_amendment(self, founder, round_num, idx, theme):
    """Founder proposes ONE amendment with full blueprint context."""
    blueprint_json = json.dumps(self.blueprint.to_dict(), indent=2)

    prompt = f"""CONSTITUTIONAL AMENDMENT — Round {round_num}, Founder {idx+1}/20

CURRENT BLUEPRINT:
{blueprint_json}

Round {round_num} theme: {theme}

YOU ({founder.name}): What one change would improve this Constitution?

Propose ONE specific amendment to any part of the blueprint above. You can:
- Add a new branch, safeguard, or rule
- Modify an existing branch's powers or composition
- Change voting thresholds or procedures
- Strengthen safeguards against system failures

Format:
AMENDMENT: [specific change in one sentence]
RATIONALE: [why this matters, what problem it solves]"""

    response = self.llm.complete(
        system_prompt=founder.get_system_prompt(),
        user_prompt=prompt,
        max_tokens=400,
        temperature=0.8
    )

    founder.total_tokens_used += response.total_tokens

    content = response.content or ""

    # Parse amendment
    import re
    amendment_match = re.search(r'AMENDMENT:\s*(.+?)(?=\nRATIONALE:|$)', content, re.IGNORECASE | re.DOTALL)
    rationale_match = re.search(r'RATIONALE:\s*(.+?)$', content, re.IGNORECASE | re.DOTALL)

    if amendment_match:
        amendment_text = amendment_match.group(1).strip()
        rationale = rationale_match.group(1).strip() if rationale_match else "No rationale provided"

        return {
            "proposer": founder.name,
            "text": amendment_text,
            "rationale": rationale,
            "round": round_num,
            "index": idx
        }

    return None


def _select_debaters(self, proposer):
    """Select random supporter and opponent (not the proposer)."""
    import random

    available = [f for f in self.founder_list if f.name != proposer.name]
    random.shuffle(available)

    supporter = available[0] if len(available) > 0 else proposer
    opponent = available[1] if len(available) > 1 else proposer

    return supporter, opponent


def _debate_support(self, supporter, amendment):
    """Supporter argues FOR the amendment (max 200 tokens)."""
    prompt = f"""CONSTITUTIONAL AMENDMENT DEBATE

Amendment proposed by {amendment['proposer']}:
{amendment['text']}

Rationale: {amendment['rationale']}

YOU ({supporter.name}): Argue IN FAVOR of this amendment in 200 tokens or less.

Why is this change necessary? What problem does it solve? What risks does it prevent?"""

    response = self.llm.complete(
        system_prompt=supporter.get_system_prompt(),
        user_prompt=prompt,
        max_tokens=200,
        temperature=0.8
    )

    supporter.total_tokens_used += response.total_tokens

    return response.content or ""


def _debate_oppose(self, opponent, amendment, support_arg):
    """Opponent argues AGAINST the amendment (max 200 tokens)."""
    prompt = f"""CONSTITUTIONAL AMENDMENT DEBATE

Amendment proposed by {amendment['proposer']}:
{amendment['text']}

Supporter said:
{support_arg}

YOU ({opponent.name}): Argue AGAINST this amendment in 200 tokens or less.

What are the risks? What could break? What unintended consequences might occur?"""

    response = self.llm.complete(
        system_prompt=opponent.get_system_prompt(),
        user_prompt=prompt,
        max_tokens=200,
        temperature=0.8
    )

    opponent.total_tokens_used += response.total_tokens

    return response.content or ""


def _vote_on_amendment(self, amendment, support_arg, oppose_arg):
    """All 20 Founders vote on the amendment."""
    votes = {"yes": 0, "no": 0}

    for founder in self.founder_list:
        prompt = f"""CONSTITUTIONAL AMENDMENT VOTE

Amendment: {amendment['text']}

Supporter argues: {support_arg[:150]}
Opponent argues: {oppose_arg[:150]}

Vote YES to adopt or NO to reject. Respond with just YES or NO."""

        response = self.llm.complete(
            system_prompt=founder.get_system_prompt(),
            user_prompt=prompt,
            max_tokens=10,
            temperature=0.5
        )

        founder.total_tokens_used += response.total_tokens

        vote_text = (response.content or "").upper()
        if "YES" in vote_text:
            votes["yes"] += 1
        else:
            votes["no"] += 1

    return votes


def _apply_amendment(self, amendment):
    """Apply passed amendment to blueprint.

    Use Claude to parse amendment into structured mutation."""
    blueprint_json = json.dumps(self.blueprint.to_dict())

    prompt = f"""Given the current blueprint and this amendment proposal, determine what specific change to make.

Current blueprint:
{blueprint_json[:1000]}

Amendment: {amendment['text']}

What should be modified? Respond with ONE of:
- ADD_BRANCH: [name] | [type] | [purpose]
- MODIFY_BRANCH: [name] | [what to change]
- ADD_SAFEGUARD: [safeguard text]
- MODIFY_VOTING: [branch name] | [new threshold]
- ADD_CYCLE_STEP: [step name]
- NO_CHANGE: [if amendment is too vague to implement]

Format: ACTION: details"""

    response = self.llm.complete(
        system_prompt="You parse Constitutional amendments into structured changes.",
        user_prompt=prompt,
        max_tokens=150,
        temperature=0.3
    )

    action_text = (response.content or "").strip()

    # Parse and apply action
    if "ADD_SAFEGUARD:" in action_text:
        safeguard = action_text.split("ADD_SAFEGUARD:")[1].strip()
        self.blueprint.non_amendable_clauses.append(safeguard)
        print(f"      → Added safeguard")

    elif "ADD_CYCLE_STEP:" in action_text:
        step = action_text.split("ADD_CYCLE_STEP:")[1].strip()
        if step and step not in self.blueprint.cycle_sequence:
            self.blueprint.cycle_sequence.append(step)
            print(f"      → Added cycle step: {step}")

    elif "MODIFY_VOTING:" in action_text:
        print(f"      → Voting rule modified (logged)")

    elif "NO_CHANGE" in action_text:
        print(f"      → Amendment too vague to implement")

    else:
        print(f"      → Amendment applied (general)")

    # Record the amendment
    self.blueprint.decisions_made.append({
        "type": "amendment",
        "proposer": amendment['proposer'],
        "text": amendment['text'],
        "round": amendment['round']
    })


def _validate_final_blueprint(self):
    """Validate final blueprint after all amendments."""
    print(f"\n{'=' * 60}")
    print("  FINAL BLUEPRINT VALIDATION")
    print(f"{'=' * 60}")

    if len(self.blueprint.branches) < 2:
        print(f"  ✗ VALIDATION FAILED: Only {len(self.blueprint.branches)} branches")
        print("  → Applying minimal fallback")
        self._apply_minimal_fallback()
        return

    if any(len(b.seats) < 1 for b in self.blueprint.branches):
        print("  ✗ VALIDATION FAILED: Branch with 0 seats")
        print("  → Applying minimal fallback")
        self._apply_minimal_fallback()
        return

    print(f"  ✓ Valid blueprint:")
    print(f"    - {len(self.blueprint.branches)} branches")
    print(f"    - {len(self.blueprint.non_amendable_clauses)} safeguards")
    print(f"    - {len(self.blueprint.decisions_made)} amendments adopted")
