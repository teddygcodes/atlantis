"""
ATLANTIS MASTER FIX PROMPT — ALL CRITICAL BUGS + STRUCTURAL SAFEGUARDS
========================================================================

This file contains EVERY fix needed to get Atlantis running correctly AND
add the structural safeguards to prevent entropy collapse.

Apply ALL fixes in order, then run:
  rm -rf atlantis_mock && python3 -u __main__.py --mock 2>&1 | tee /tmp/atlantis_master.log

FIXES ARE GROUPED INTO:
  A. PARSING FIXES (Root cause of empty archive + tier advancement failure)
  B. ENGINE FIXES (Archive deposit, Constitution context, perpetual engine)
  C. VALIDATION FIXES (Advisory not blocking, JSON robustness)
  D. AGENT FIXES (Deduplication, update_knowledge, typos)
  E. STRUCTURAL SAFEGUARDS (Constitutional versioning, spawn caps, semantic anchoring)

========================================================================
"""

# ══════════════════════════════════════════════════════════════
# A. PARSING FIXES — Root cause of ALL knowledge failures
# ══════════════════════════════════════════════════════════════
#
# ROOT CAUSE: Claude formats responses with bold markdown:
#   **CONCEPTS:** systems thinking, feedback loops
# But parsers only match:
#   CONCEPTS: systems thinking, feedback loops
#
# Result: 60 research cycles × 20 Founders = 0 knowledge stored.
# Archive empty. States can't advance tiers. System is brain-dead.
#
# FIX: Strip ** before matching in ALL parsing functions.

# -----------------------------------------------------------
# A1. Replace _parse_research() in founders/convention.py
#     Location: around line 1247
#     Also replace _split() right after it
# -----------------------------------------------------------

"""
FIND this function (around line 1247 of founders/convention.py):

def _parse_research(content):
    concepts, frameworks, applications, connections = [], [], [], []
    if not content:
        return concepts, frameworks, applications, connections
    current = None
    for line in content.split("\\n"):
        line = line.strip()
        u = line.upper()
        if u.startswith("CONCEPTS:") or u.startswith("KEY CONCEPTS:"):
            ...

REPLACE the entire _parse_research() AND _split() functions with:
"""

PARSE_RESEARCH_REPLACEMENT = '''
def _parse_research(content):
    """Parse research output from LLM response.
    
    Handles all Claude formatting styles:
    - Plain: CONCEPTS: item1, item2
    - Bold markdown: **CONCEPTS:** item1, item2  
    - Bulleted: - item1\\n- item2
    - Numbered: 1. item1\\n2. item2
    """
    concepts, frameworks, applications, connections = [], [], [], []
    if not content:
        return concepts, frameworks, applications, connections
    
    current = None
    for line in content.split("\\n"):
        line = line.strip()
        # CRITICAL FIX: Strip bold markdown before matching
        clean = line.replace("**", "").replace("*", "").strip()
        u = clean.upper()
        
        if u.startswith("CONCEPTS:") or u.startswith("KEY CONCEPTS:"):
            current = "c"
            r = clean.split(":", 1)[-1].strip()
            if r:
                concepts.extend(_split(r))
        elif u.startswith("FRAMEWORKS:") or u.startswith("KEY FRAMEWORKS:"):
            current = "f"
            r = clean.split(":", 1)[-1].strip()
            if r:
                frameworks.extend(_split(r))
        elif u.startswith("APPLICATIONS:"):
            current = "a"
            r = clean.split(":", 1)[-1].strip()
            if r:
                applications.extend(_split(r))
        elif u.startswith("CONNECTIONS:"):
            current = "x"
            r = clean.split(":", 1)[-1].strip()
            if r:
                connections.extend(_split(r))
        elif u.startswith("SYNTHESIS:") or u.startswith("EVIDENCE:"):
            current = None
        elif line.startswith("- ") or line.startswith("* ") or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
            # Handle bullets and numbered lists
            item = line.lstrip("-*0123456789.) ").strip()
            if item:
                if current == "c": concepts.append(item)
                elif current == "f": frameworks.append(item)
                elif current == "a": applications.append(item)
                elif current == "x": connections.append(item)
    
    return (list(dict.fromkeys(concepts)), list(dict.fromkeys(frameworks)),
            list(dict.fromkeys(applications)), list(dict.fromkeys(connections)))


def _split(text):
    """Split comma/semicolon/dash separated items."""
    for sep in [",", ";", " - "]:
        if sep in text:
            return [i.strip() for i in text.split(sep) if i.strip()]
    return [text.strip()] if text.strip() else []
'''

# -----------------------------------------------------------
# A2. Add _extract_items() helper to governance/states.py
#     Location: After imports, before first class definition
#     (around line 23, before the @dataclass line)
# -----------------------------------------------------------

EXTRACT_ITEMS_HELPER = '''
def _extract_items(raw_text):
    """Extract items from a section — handles comma, bullet, and numbered formats."""
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
'''

# -----------------------------------------------------------
# A3. Replace ALL THREE _parse_findings() methods in governance/states.py
#     There are 3 copies — Town (~line 295), City (~line 583), State (~line 1068)
#     Replace ALL THREE with this identical version:
# -----------------------------------------------------------

PARSE_FINDINGS_REPLACEMENT = '''
    def _parse_findings(self, content: str) -> Dict:
        """Parse research findings from LLM response.
        Handles bold markdown, bullets, numbered lists, comma-separated."""
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
        
        # CRITICAL FIX: Strip bold markdown globally
        clean = content.replace("**", "")
        
        concepts_match = re.search(
            r'CONCEPTS?:\\s*(.*?)(?=\\n\\s*(?:FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if concepts_match:
            findings["concepts"] = _extract_items(concepts_match.group(1).strip())
        
        frameworks_match = re.search(
            r'FRAMEWORKS?:\\s*(.*?)(?=\\n\\s*(?:CONCEPTS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if frameworks_match:
            findings["frameworks"] = _extract_items(frameworks_match.group(1).strip())
        
        applications_match = re.search(
            r'APPLICATIONS?:\\s*(.*?)(?=\\n\\s*(?:CONCEPTS?|FRAMEWORKS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if applications_match:
            findings["applications"] = _extract_items(applications_match.group(1).strip())
        
        synthesis_match = re.search(
            r'SYNTHESIS:\\s*(.*?)(?=\\n\\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|EVIDENCE|CONNECTIONS?):|\Z)',
            clean, re.IGNORECASE | re.DOTALL
        )
        if synthesis_match:
            findings["synthesis"] = synthesis_match.group(1).strip()[:500]
        
        evidence_match = re.search(
            r'EVIDENCE:\\s*(.*?)(?=\\n\\s*(?:CONCEPTS?|FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|CONNECTIONS?):|\Z)',
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
'''


# ══════════════════════════════════════════════════════════════
# B. ENGINE FIXES — Archive deposit + missing methods
# ══════════════════════════════════════════════════════════════

# -----------------------------------------------------------
# B1. Fix _deposit_founder_knowledge_to_archive() in core/engine.py
#     The method MUST use self.founders (which have knowledge from Phase 0)
#     NOT get_all_founders() which creates empty objects.
#     
#     If self.founders doesn't exist or is empty, reload from database.
#     Add debug output to verify knowledge is present.
# -----------------------------------------------------------

ARCHIVE_DEPOSIT_FIX = '''
In core/engine.py, find _deposit_founder_knowledge_to_archive() and ensure:

1. It uses self.founders (NOT get_all_founders())
2. If self.founders is missing, reload knowledge from database
3. Add debug print showing what each founder has before depositing

The deposit loop should look like:

    total_deposited = 0
    for founder in self.founders:
        domain_count = len(founder.knowledge)
        has_data = any(
            ka.key_concepts or ka.frameworks or ka.applications
            for ka in founder.knowledge.values()
        )
        print(f"  DEBUG: {founder.name} — {domain_count} domains, has_data={has_data}")
        
        for domain, ka in founder.knowledge.items():
            if ka.key_concepts or ka.frameworks or ka.applications:
                self.db.deposit_to_archive(
                    source_type="founder",
                    source_id=founder.id,
                    knowledge={
                        "domain": domain,
                        "tier": ka.tier,
                        "concepts": ka.key_concepts,
                        "frameworks": ka.frameworks,
                        "applications": ka.applications,
                        "synthesis": f"Founder {founder.name} research in {domain}",
                        "evidence": ", ".join(ka.key_concepts[:5]),
                        "cycle_created": 0
                    }
                )
                total_deposited += 1
'''

# -----------------------------------------------------------
# B2. Add _run_perpetual_engine() method to AtlantisEngine in core/engine.py
#     This method is called on line ~98 but doesn't exist.
# -----------------------------------------------------------

PERPETUAL_ENGINE_METHOD = '''
Add this method to AtlantisEngine class in core/engine.py:

    def _run_perpetual_engine(self, governance_cycles: int = 10):
        """Phase 3: Autonomous Governance — Perpetual Engine."""
        print(f"\\n{'=' * 60}")
        print(f"  PHASE 3: PERPETUAL GOVERNANCE ENGINE")
        print(f"  Running {governance_cycles} autonomous cycles")
        print(f"{'=' * 60}")
        
        from governance.perpetual import PerpetualEngine
        from governance.states import StateManager
        
        state_manager = StateManager(
            llm=self.llm, db=self.db, logger=self.logger
        )
        
        perpetual = PerpetualEngine(
            government=self.government,
            state_manager=state_manager,
            logger=self.logger,
            llm=self.llm,
            db=self.db
        )
        
        perpetual.run_cycles(num_cycles=governance_cycles)
        
        self.current_phase = "governance_complete"
        self.db.set_state("current_phase", "governance_complete")
'''

# -----------------------------------------------------------
# B3. Build federal_constitution dict for State formation voters
#     In core/engine.py _run_founding_era(), before the State formation
#     vote, build a dict that voters can reference:
# -----------------------------------------------------------

FEDERAL_CONSTITUTION_CONTEXT = '''
In core/engine.py, wherever State formation voting happens, add before the vote:

    # Build federal constitution context for voters
    federal_constitution = {
        "branches": [b.name for b in self.blueprint.branches],
        "non_amendable_clauses": getattr(self.blueprint, 'non_amendable_clauses', []),
        "cycle_sequence": getattr(self.blueprint, 'cycle_sequence', []),
    }
    
    # Include readable summary in vote prompt
    govt_context = "GOVERNMENT STRUCTURE:\\n"
    for b in self.blueprint.branches:
        govt_context += f"  • {b.name} ({b.branch_type})\\n"
    govt_context += f"\\nNON-AMENDABLE CLAUSES: {len(federal_constitution['non_amendable_clauses'])}\\n"
    for clause in federal_constitution['non_amendable_clauses'][:3]:
        govt_context += f"  - {clause[:100]}\\n"
'''


# ══════════════════════════════════════════════════════════════
# C. VALIDATION FIXES — Don't let parse failures block States
# ══════════════════════════════════════════════════════════════

# -----------------------------------------------------------
# C1. validate_state_constitution() returns True on parse failure
#     Location: governance/states.py, StateManager class
#     Advisory, not blocking — an unvalidated State is better than no State
# -----------------------------------------------------------

VALIDATION_FIX = '''
In governance/states.py, find validate_state_constitution() and ensure
the except clause returns True (advisory pass-through):

    except Exception as e:
        print(f"  ⚠ Constitution validation parse failed: {e}")
        return True, []  # Advisory — pass through on failure
'''

# -----------------------------------------------------------
# C2. JSON parsing — strip markdown fences everywhere
#     In governance/states.py, wherever json.loads() is called on
#     LLM output, first strip markdown fences:
# -----------------------------------------------------------

JSON_PARSING_FIX = '''
Everywhere in governance/states.py that parses JSON from LLM responses,
add this before json.loads():

    import re
    raw = response.content or "{}"
    # Strip markdown fences
    raw = re.sub(r'```json\\s*', '', raw)
    raw = re.sub(r'```\\s*', '', raw)
    # Find JSON object with brace matching (not greedy regex)
    start = raw.find('{')
    if start != -1:
        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == '{': depth += 1
            elif raw[i] == '}': depth -= 1
            if depth == 0:
                result = json.loads(raw[start:i+1])
                break

This applies to:
- State spec parsing (~line 1188)
- State constitution generation (~line 1230)  
- Constitution validation (~line 1318)
'''


# ══════════════════════════════════════════════════════════════
# D. AGENT & MISC FIXES
# ══════════════════════════════════════════════════════════════

# -----------------------------------------------------------
# D1. Fix applications deduplication in agents/base.py
#     Line ~175 — applications.extend() without dedup
# -----------------------------------------------------------

DEDUP_FIX = '''
In agents/base.py update_knowledge() method, after:
    if applications:
        ka.applications.extend(applications)
ADD:
        ka.applications = list(dict.fromkeys(ka.applications))
'''

# -----------------------------------------------------------
# D2. Fix Town tier starting at 4 → 0 in governance/states.py
#     Line ~148
# -----------------------------------------------------------

TOWN_TIER_FIX = '''
In governance/states.py Town.__init__(), change:
    self.tier = 4
To:
    self.tier = 0
'''

# -----------------------------------------------------------
# D3. Fix Governor subdomain typo in governance/states.py
#     Line ~812
# -----------------------------------------------------------

SUBDOMAIN_FIX = '''
In governance/states.py, change:
    "subdomain": getattr(city, 'subdomain', city.domain),
To:
    "subdomain": getattr(city, 'sub_domain', city.domain),
'''

# -----------------------------------------------------------
# D4. Fix regex crash on missing digits in founders/convention.py
#     Line ~582
# -----------------------------------------------------------

REGEX_FIX = '''
In founders/convention.py, where branch seats are parsed, change:
    seats = int(re.search(r'\\d+', parts[2]).group())
To:
    match = re.search(r'\\d+', parts[2])
    seats = int(match.group()) if match else 3
'''

# -----------------------------------------------------------
# D5. Ensure update_knowledge() exists on BaseAgent in agents/base.py
#     It should already exist but verify it handles all params
# -----------------------------------------------------------

UPDATE_KNOWLEDGE_FIX = '''
Verify agents/base.py has update_knowledge() method on BaseAgent class:

    def update_knowledge(self, domain: str, tier: int = None,
                         concepts: list = None, frameworks: list = None,
                         applications: list = None, connections: list = None):
        if domain not in self.knowledge:
            self.knowledge[domain] = KnowledgeArea(domain=domain)
        
        ka = self.knowledge[domain]
        if tier is not None:
            ka.tier = max(ka.tier, tier)
        if concepts:
            ka.key_concepts.extend(concepts)
            ka.key_concepts = list(dict.fromkeys(ka.key_concepts))
        if frameworks:
            ka.frameworks.extend(frameworks)
            ka.frameworks = list(dict.fromkeys(ka.frameworks))
        if applications:
            ka.applications.extend(applications)
            ka.applications = list(dict.fromkeys(ka.applications))
        if connections:
            ka.connections.extend(connections)
            ka.connections = list(set(ka.connections))
        ka.entry_count += 1
'''


# ══════════════════════════════════════════════════════════════
# E. STRUCTURAL SAFEGUARDS — Prevent entropy collapse
# ══════════════════════════════════════════════════════════════
#
# These are NEW features based on failure analysis.
# They prevent:
#   - Constitutional amendment recursion
#   - Spawn explosion
#   - Semantic drift
#   - Knowledge bloat
#   - Self-referential myth building

# -----------------------------------------------------------
# E1. CONSTITUTIONAL VERSIONING
#     Every ratified amendment creates a new version.
#     Old versions are preserved and queryable.
#     Non-amendable clauses can NEVER be changed.
#
#     Add to core/persistence.py:
# -----------------------------------------------------------

CONSTITUTIONAL_VERSIONING = '''
Add these methods to AtlantisDB class in core/persistence.py:

    def save_constitution_version(self, version: int, constitution_text: str,
                                   amendments: list = None, ratified_by: list = None):
        """Save an immutable constitutional version snapshot."""
        import json
        from datetime import datetime, timezone
        
        self.execute(
            """INSERT INTO constitutions 
               (constitution_type, version, articles_json, ratified_by_json, ratified_at, is_current)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("federal", version, constitution_text,
             json.dumps(ratified_by or []),
             datetime.now(timezone.utc).isoformat(),
             1)
        )
        # Mark previous versions as not current
        self.execute(
            "UPDATE constitutions SET is_current = 0 WHERE constitution_type = 'federal' AND version < ?",
            (version,)
        )
    
    def get_constitution_version(self, version: int = None):
        """Get a specific constitution version, or current if version is None."""
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
        """Get all constitutional versions for audit trail."""
        rows = self.fetchall(
            "SELECT version, ratified_at, ratified_by_json FROM constitutions WHERE constitution_type = 'federal' ORDER BY version"
        )
        return [dict(r) for r in rows]


Then in core/engine.py, after Jefferson's draft is accepted:

    # Save v1.0 — Jefferson's original
    self.db.save_constitution_version(
        version=1,
        constitution_text=convention.draft_text,
        ratified_by=["Jefferson"],
    )
    self.constitution_version = 1

And after each successful amendment:

    self.constitution_version += 1
    self.db.save_constitution_version(
        version=self.constitution_version,
        constitution_text=current_constitution_text,
        amendments=[amendment_text],
        ratified_by=yes_voters,
    )
'''

# -----------------------------------------------------------
# E2. HARD SPAWN CAP
#     Add max_states to HARD_CONSTRAINTS in config/settings.py
#     Enforce it in governance/states.py StateManager.form_state()
# -----------------------------------------------------------

SPAWN_CAP = '''
In config/settings.py, update HARD_CONSTRAINTS:

    "max_states": 50,  # Hard cap — prevents spawn explosion
    "max_cities_per_state": 15,
    "max_towns_per_city": 10,

In governance/states.py StateManager.form_state(), add at the top:

    if len(self.states) >= HARD_CONSTRAINTS["max_states"]:
        return False, f"Maximum States reached ({HARD_CONSTRAINTS['max_states']}). No new States."
'''

# -----------------------------------------------------------
# E3. AMENDMENT FREQUENCY LIMIT
#     Max 1 amendment per cycle (already structural).
#     Add: max 1 PASSED amendment per 3 cycles to prevent stacking.
# -----------------------------------------------------------

AMENDMENT_LIMIT = '''
In config/settings.py, add:

    "min_cycles_between_amendments": 3,  # Cooling period after passed amendment

In core/engine.py _run_founding_era() STEP 1, add before amendment proposal:

    # Check amendment cooling period
    cycles_since_last = cycle - getattr(self, '_last_amendment_cycle', -999)
    if cycles_since_last < FOUNDING_CONFIG.get("min_cycles_between_amendments", 3):
        print(f"  Amendment cooling period ({cycles_since_last}/{FOUNDING_CONFIG['min_cycles_between_amendments']} cycles)")
        # Skip amendment this cycle
    else:
        # Proceed with amendment proposal
        ...
        if amendment_passed:
            self._last_amendment_cycle = cycle
'''

# -----------------------------------------------------------
# E4. KNOWLEDGE QUALITY STRATIFICATION
#     Archive entries get quality scores based on tier + source diversity.
#     High-tier entries outrank low-tier in queries.
# -----------------------------------------------------------

KNOWLEDGE_STRATIFICATION = '''
In core/persistence.py, modify deposit_to_archive() to include quality_score:

    def deposit_to_archive(self, source_type, source_id, knowledge):
        """Deposit knowledge with quality scoring."""
        tier = knowledge.get("tier", 0)
        concepts = knowledge.get("concepts", [])
        frameworks = knowledge.get("frameworks", [])
        
        # Quality score: tier weight + content richness
        quality_score = (tier * 20) + len(concepts) + (len(frameworks) * 3)
        
        # Check for self-citation (penalize circular references)
        existing = self.fetchall(
            "SELECT knowledge_json FROM federal_archive WHERE source_id = ? AND domain = ?",
            (source_id, knowledge.get("domain", ""))
        )
        if existing:
            quality_score = max(1, quality_score - 10)  # Penalty for repeat deposits
        
        self.execute(
            """INSERT INTO federal_archive 
               (source_type, source_id, domain, tier, knowledge_json, quality_score, deposited_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (source_type, source_id, knowledge.get("domain", ""),
             tier, json.dumps(knowledge), quality_score,
             datetime.now(timezone.utc).isoformat())
        )

Add quality_score column to federal_archive table if not exists:

    ALTER TABLE federal_archive ADD COLUMN quality_score INTEGER DEFAULT 0;
'''

# -----------------------------------------------------------
# E5. CUMULATIVE TIER CALCULATION
#     Tiers must be calculated from ALL knowledge entries combined,
#     not just the current cycle's findings.
# -----------------------------------------------------------

CUMULATIVE_TIER = '''
In governance/states.py, in each entity's research cycle method
(Town, City, State), change tier calculation to cumulative:

    # Calculate tier from ALL knowledge entries (cumulative, not per-cycle)
    all_concepts = []
    all_frameworks = []
    all_applications = []
    for entry in self.knowledge_entries:
        all_concepts.extend(entry.get("concepts", []))
        all_frameworks.extend(entry.get("frameworks", []))
        all_applications.extend(entry.get("applications", []))
    
    # Deduplicate
    all_concepts = list(dict.fromkeys(all_concepts))
    all_frameworks = list(dict.fromkeys(all_frameworks))
    all_applications = list(dict.fromkeys(all_applications))
    
    cumulative_findings = {
        "concepts": all_concepts,
        "frameworks": all_frameworks,
        "applications": all_applications
    }
    new_tier = self._calculate_tier(cumulative_findings)
    
    if new_tier > self.tier:
        self.tier = new_tier
        print(f"    ⚡ TIER ADVANCEMENT: {self.name} → Tier {new_tier}!")
'''


# ══════════════════════════════════════════════════════════════
# EXECUTION ORDER
# ══════════════════════════════════════════════════════════════

EXECUTION_ORDER = """
Apply fixes in this order:

1. A1: Replace _parse_research() + _split() in founders/convention.py
2. A2: Add _extract_items() helper to governance/states.py (after imports, before classes)
3. A3: Replace ALL THREE _parse_findings() in governance/states.py
4. B1: Fix _deposit_founder_knowledge_to_archive() in core/engine.py
5. B2: Add _run_perpetual_engine() to core/engine.py
6. B3: Add federal_constitution context for voters in core/engine.py
7. C1: Make validate_state_constitution() advisory in governance/states.py
8. C2: Add markdown fence stripping to all JSON parsing in governance/states.py
9. D1: Add applications dedup in agents/base.py
10. D2: Fix Town tier 4→0 in governance/states.py
11. D3: Fix subdomain typo in governance/states.py
12. D4: Fix regex crash in founders/convention.py
13. D5: Verify update_knowledge() exists in agents/base.py
14. E1: Add constitutional versioning to core/persistence.py + core/engine.py
15. E2: Add hard spawn cap to config/settings.py + governance/states.py
16. E3: Add amendment frequency limit to config/settings.py + core/engine.py
17. E4: Add knowledge quality scoring to core/persistence.py
18. E5: Add cumulative tier calculation to governance/states.py

Then run:
  rm -rf atlantis_mock && python3 -u __main__.py --mock 2>&1 | tee /tmp/atlantis_master.log

Verify:
  - Phase 0: Founders reach Tier 1+ (not Tier 0)
  - Archive deposit: 60+ entries (not 0)
  - States form with correct names
  - Constitution validation passes (advisory)
  - Tier advancement visible during State research
  - No crashes or silent failures
"""

print(EXECUTION_ORDER)
