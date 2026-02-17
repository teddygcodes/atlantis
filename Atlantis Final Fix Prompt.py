"""
ATLANTIS FINAL FIX PROMPT — State Research Parsing + Structural Safeguards
==========================================================================

The system is 95% working. Archive deposits 56 entries, States form with
correct names, votes pass. ONE BUG REMAINS plus structural safeguards needed.

REMAINING BUG: State research returns "Tier 0, 0 concepts" because the 
State._parse_findings() method in governance/states.py (line 1068) was NOT 
updated to strip bold markdown. Claude returns **CONCEPTS:** but the regex 
only matches CONCEPTS: — same root cause as the archive bug.

There are THREE copies of _parse_findings() in governance/states.py:
  - Town._parse_findings() around line 295
  - City._parse_findings() around line 583  
  - State._parse_findings() around line 1068

ALL THREE must be updated. Replace each one with the version below.

Also add the _extract_items() helper function at module level (after imports,
before the first class definition, around line 23).

AFTER fixing parsing, apply the structural safeguards (E1-E5).

==========================================================================
FIX ORDER:
  1. Add _extract_items() helper at module level in governance/states.py
  2. Replace ALL THREE _parse_findings() methods in governance/states.py
  3. Add debug print of raw research content before parsing (temporary)
  4. Add constitutional versioning to core/persistence.py
  5. Add max_states=50 to config/settings.py HARD_CONSTRAINTS
  6. Add amendment cooling period (3 cycles between passed amendments)
  7. Add quality_score to archive deposits in core/persistence.py
  8. Make tier calculation cumulative in all three entity classes

Then run:
  rm -rf atlantis_mock && python3 -u __main__.py --mock 2>&1 | tee /tmp/atlantis_master.log

==========================================================================
"""

# ════════════════════════════════════════════════════════════
# FIX 1: Add _extract_items() helper to governance/states.py
# Location: After imports (around line 22), before first class
# ════════════════════════════════════════════════════════════

# Add this function at module level in governance/states.py,
# right after the imports and before the first @dataclass:

"""
def _extract_items(raw_text):
    '''Extract items from a section — handles comma, bullet, and numbered formats.'''
    items = []
    lines = raw_text.split('\\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith(('- ', '* ', '• ')):
            item = line.lstrip('-*• ').strip()
            if item and len(item) > 2:
                items.append(item[:100])
        elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            item = line.lstrip('0123456789.): ').strip()
            if item and len(item) > 2:
                items.append(item[:100])
        elif ',' in line:
            for part in line.split(','):
                part = part.strip()
                if part and len(part) > 2:
                    items.append(part[:100])
        elif line and len(line) > 2:
            items.append(line[:100])
    return list(dict.fromkeys(items))
"""


# ════════════════════════════════════════════════════════════
# FIX 2: Replace ALL THREE _parse_findings() methods
# Location: Town (~line 295), City (~line 583), State (~line 1068)
# Replace each one with this IDENTICAL method:
# ════════════════════════════════════════════════════════════

"""
Replace ALL THREE _parse_findings() methods with this version.
The key change is line 2: content.replace("**", "") which strips
bold markdown that Claude always uses in responses.

    def _parse_findings(self, content: str) -> Dict:
        '''Parse research findings. Handles bold markdown, bullets, numbers, commas.'''
        import re
        
        findings = {
            "concepts": [],
            "frameworks": [],
            "applications": [],
            "synthesis": "",
            "evidence": ""
        }
        
        if not content:
            return findings
        
        # CRITICAL: Strip bold markdown — Claude returns **CONCEPTS:** not CONCEPTS:
        clean = content.replace("**", "")
        
        concepts_match = re.search(
            r'CONCEPTS?:\s*(.*?)(?=\n\s*(?:FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if concepts_match:
            findings["concepts"] = _extract_items(concepts_match.group(1).strip())
        
        frameworks_match = re.search(
            r'FRAMEWORKS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if frameworks_match:
            findings["frameworks"] = _extract_items(frameworks_match.group(1).strip())
        
        applications_match = re.search(
            r'APPLICATIONS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if applications_match:
            findings["applications"] = _extract_items(applications_match.group(1).strip())
        
        synthesis_match = re.search(
            r'SYNTHESIS:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if synthesis_match:
            findings["synthesis"] = synthesis_match.group(1).strip()[:500]
        
        evidence_match = re.search(
            r'EVIDENCE:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if evidence_match:
            findings["evidence"] = evidence_match.group(1).strip()[:500]
        
        # Fallback: extract something if nothing parsed
        if not findings["concepts"] and not findings["frameworks"]:
            lines = [l.strip() for l in content.split('\\n') if len(l.strip()) > 10]
            if lines:
                findings["concepts"] = [w.strip('.,;:*-# ') for w in lines[0].split(',') if len(w.strip()) > 3][:10]
                findings["synthesis"] = content[:500]
        
        return findings
"""


# ════════════════════════════════════════════════════════════
# FIX 3: Add debug print in State.run_research_cycle()
# Location: governance/states.py, State.run_research_cycle()
# After research_response = llm.complete(...) and before 
# findings = self._parse_findings(...)
# ════════════════════════════════════════════════════════════

"""
In the State class run_research_cycle() method, after the research LLM call
and before _parse_findings, add:

    # DEBUG: Show first 200 chars of research response
    print(f"    DEBUG research response: {(research_response.content or '')[:200]}")

This helps verify the bold markdown stripping is working.
Remove this debug line after confirming the fix works.
"""


# ════════════════════════════════════════════════════════════
# FIX 4: Constitutional Versioning
# Location: core/persistence.py — add methods to AtlantisDB
# Location: core/engine.py — save v1.0 after Jefferson's draft
# ════════════════════════════════════════════════════════════

"""
In core/persistence.py, add these methods to AtlantisDB class:

    def save_constitution_version(self, version, constitution_text, 
                                   amendments=None, ratified_by=None):
        '''Save immutable constitutional version snapshot.'''
        import json
        from datetime import datetime, timezone
        
        self.execute(
            "INSERT INTO constitutions (constitution_type, version, articles_json, ratified_by_json, ratified_at, is_current) VALUES (?, ?, ?, ?, ?, ?)",
            ("federal", version, constitution_text,
             json.dumps(ratified_by or []),
             datetime.now(timezone.utc).isoformat(), 1)
        )
        self.execute(
            "UPDATE constitutions SET is_current = 0 WHERE constitution_type = 'federal' AND version < ?",
            (version,)
        )
    
    def get_constitution_version(self, version=None):
        '''Get specific version or current constitution.'''
        if version:
            row = self.fetchone(
                "SELECT * FROM constitutions WHERE constitution_type = 'federal' AND version = ?",
                (version,)
            )
        else:
            row = self.fetchone(
                "SELECT * FROM constitutions WHERE constitution_type = 'federal' AND is_current = 1"
            )
        return dict(row) if row else None
    
    def get_constitution_history(self):
        '''Get all versions for audit trail.'''
        rows = self.fetchall(
            "SELECT version, ratified_at, ratified_by_json FROM constitutions WHERE constitution_type = 'federal' ORDER BY version"
        )
        return [dict(r) for r in rows]


In core/engine.py, after Jefferson's draft is accepted in _run_convention():

    # Save v1.0 — Jefferson's original (immutable)
    if hasattr(convention, 'draft_text') and convention.draft_text:
        self.db.save_constitution_version(
            version=1,
            constitution_text=convention.draft_text,
            ratified_by=["Jefferson"],
        )
        self.constitution_version = 1
        print(f"  ✓ Constitution v1.0 saved (immutable)")

After each successful amendment in _run_founding_era():

    if amendment_result.get("status") == "passed":
        self.constitution_version = getattr(self, 'constitution_version', 1) + 1
        self.db.save_constitution_version(
            version=self.constitution_version,
            constitution_text=str(self.blueprint.to_dict()),
            amendments=[amendment_result.get("text", "")],
            ratified_by=amendment_result.get("yes_voters", []),
        )
        print(f"  ✓ Constitution v{self.constitution_version} saved")
"""


# ════════════════════════════════════════════════════════════
# FIX 5: Hard Spawn Cap
# Location: config/settings.py HARD_CONSTRAINTS
# Location: governance/states.py StateManager.form_state()
# ════════════════════════════════════════════════════════════

"""
In config/settings.py, change the comment and add max_states:

    "max_states": 50,  # Hard cap — prevents spawn explosion
    "max_cities_per_state": 15,
    "max_towns_per_city": 10,

In governance/states.py StateManager.form_state(), add at the top
of the method before any other logic:

    if len(self.states) >= HARD_CONSTRAINTS.get("max_states", 50):
        print(f"    ✗ Maximum States reached ({HARD_CONSTRAINTS['max_states']})")
        return None
"""


# ════════════════════════════════════════════════════════════
# FIX 6: Amendment Cooling Period
# Location: core/engine.py _run_founding_era() STEP 1
# ════════════════════════════════════════════════════════════

"""
In core/engine.py _run_founding_era(), in the STEP 1 amendment section,
add before calling propose_collaborative_amendment():

    # Amendment cooling period — prevent amendment stacking
    min_gap = 3  # Minimum cycles between passed amendments
    cycles_since_last = cycle - getattr(self, '_last_amendment_passed_cycle', -999)
    if cycles_since_last < min_gap:
        print(f"  Amendment cooling period: {cycles_since_last}/{min_gap} cycles since last passed")
        amendment_result = {"status": "cooling_period"}
    else:
        # Normal amendment flow
        amendment_result = propose_collaborative_amendment(...)
        if amendment_result.get("status") == "passed":
            self._last_amendment_passed_cycle = cycle
"""


# ════════════════════════════════════════════════════════════
# FIX 7: Knowledge Quality Scoring  
# Location: core/persistence.py deposit_to_archive()
# ════════════════════════════════════════════════════════════

"""
In core/persistence.py, modify deposit_to_archive() to calculate
a quality score:

    tier = knowledge.get("tier", 0)
    concepts = knowledge.get("concepts", [])
    frameworks = knowledge.get("frameworks", [])
    
    # Quality score: tier weight + content richness
    quality_score = (tier * 20) + len(concepts) + (len(frameworks) * 3)

Add quality_score to the INSERT statement and the federal_archive table.
If the column doesn't exist, add it with:

    ALTER TABLE federal_archive ADD COLUMN quality_score INTEGER DEFAULT 0;

(Wrap in try/except since ALTER TABLE fails if column already exists)
"""


# ════════════════════════════════════════════════════════════
# FIX 8: Cumulative Tier Calculation
# Location: governance/states.py — all three entity classes
# In run_research_cycle() for Town, City, and State
# ════════════════════════════════════════════════════════════

"""
In each entity's run_research_cycle() method, AFTER adding the new
findings to knowledge_entries and BEFORE calculating the tier, 
replace the per-cycle tier calculation with cumulative:

    # Calculate tier from ALL knowledge entries (cumulative)
    all_concepts = []
    all_frameworks = []
    all_applications = []
    for entry in self.knowledge_entries:
        if hasattr(entry, 'concepts'):
            all_concepts.extend(entry.concepts)
        if hasattr(entry, 'frameworks'):
            all_frameworks.extend(entry.frameworks)
        if hasattr(entry, 'applications'):
            all_applications.extend(entry.applications)
    
    # Deduplicate
    all_concepts = list(dict.fromkeys(all_concepts))
    all_frameworks = list(dict.fromkeys(all_frameworks))
    all_applications = list(dict.fromkeys(all_applications))
    
    cumulative = {
        "concepts": all_concepts,
        "frameworks": all_frameworks,
        "applications": all_applications
    }
    new_tier = self._calculate_tier(cumulative)
    
    if new_tier > self.tier:
        old_tier = self.tier
        self.tier = new_tier
        print(f"    ⚡ TIER ADVANCEMENT: {self.name} → Tier {new_tier}!")
"""


# ════════════════════════════════════════════════════════════
# VERIFICATION CHECKLIST
# ════════════════════════════════════════════════════════════

"""
After applying all fixes, run:
  rm -rf atlantis_mock && python3 -u __main__.py --mock 2>&1 | tee /tmp/atlantis_master.log

Verify in the output:
  ✅ Phase 0: Founders reach Tier 1 ("* Hamilton reached Tier 1 in systems_theory!")
  ✅ Archive: "Deposited 56+ knowledge entries from 20 Founders" (NOT 0)
  ✅ Archive: "20 entries, 20 domains" shown in Founding Era
  ✅ State formed: Correct name like "The Axiom Forge" (not "State of State Formation")
  ✅ State research: "Research complete: Tier X, Y concepts" where Y > 0 (NOT 0)
  ✅ Tier advancement: "⚡ TIER ADVANCEMENT" messages during State research
  ✅ Constitution v1.0 saved after Jefferson's draft
  ✅ Constitution validation: "⚠ Constitution validation parse failed" (advisory pass-through)
  ✅ No crashes, no AttributeError, no silent failures
  
If State research still shows 0 concepts:
  - Check the DEBUG research response line — does it contain **CONCEPTS:** with asterisks?
  - If yes, the replace("**", "") isn't being applied — verify the _parse_findings was replaced
  - If no, the LLM isn't returning structured format — check the research prompt
"""
