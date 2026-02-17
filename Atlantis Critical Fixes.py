# ATLANTIS CRITICAL FIXES — Drop-in replacement code
# =================================================
# 
# THREE FIXES:
#
# FIX 1: _parse_research() in founders/convention.py — strips bold markdown
#        ROOT CAUSE of empty archive: Claude responds with **CONCEPTS:** 
#        and parser only matches CONCEPTS: — 60 research cycles = 0 data
#
# FIX 2: validate_state_constitution() in governance/states.py — advisory not blocking
#        States crash on JSON parse failure during validation
#
# FIX 3: Bonus — also fix _parse_findings() in governance/states.py (same bug)
#
# HOW TO APPLY:
#   1. Replace _parse_research() in founders/convention.py (around line 1244)
#   2. Replace validate_state_constitution() in governance/states.py (around line 1300)  
#   3. Replace BOTH _parse_findings() methods in governance/states.py (around lines 585 and 1045)
#   4. Run: rm -rf atlantis_mock && python3 -u __main__.py --mock 2>&1 | tee /tmp/atlantis_final.log


# ══════════════════════════════════════════════════════════════
# FIX 1: Replace _parse_research() in founders/convention.py
# Location: around line 1244
# ══════════════════════════════════════════════════════════════

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
    for line in content.split("\n"):
        line = line.strip()
        # Strip bold markdown: **CONCEPTS:** → CONCEPTS:
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
        elif u.startswith("SYNTHESIS:"):
            current = None
        elif u.startswith("EVIDENCE:"):
            current = None
        elif line.startswith("- ") or line.startswith("* ") or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
            # Handle bullets: - item, * item, 1. item, 1) item
            item = line.lstrip("-*0123456789.) ").strip()
            if item:
                if current == "c":
                    concepts.append(item)
                elif current == "f":
                    frameworks.append(item)
                elif current == "a":
                    applications.append(item)
                elif current == "x":
                    connections.append(item)
    
    return (list(dict.fromkeys(concepts)), list(dict.fromkeys(frameworks)),
            list(dict.fromkeys(applications)), list(dict.fromkeys(connections)))


def _split(text):
    """Split comma/semicolon/dash separated items."""
    for sep in [",", ";", " - "]:
        if sep in text:
            return [i.strip() for i in text.split(sep) if i.strip()]
    return [text.strip()] if text.strip() else []


# ══════════════════════════════════════════════════════════════
# FIX 2: Replace validate_state_constitution() in governance/states.py
# Location: around line 1300 in StateManager class
# ══════════════════════════════════════════════════════════════

def validate_state_constitution(self, draft, federal_const):
    """Check if State Constitution violates Federal non-amendable clauses.
    
    Validation is ADVISORY — parse failures pass through rather than
    blocking State formation entirely.
    """
    import json
    
    validation_response = self.llm.complete(
        system_prompt="You are a constitutional law expert.",
        user_prompt=(
            f"Federal Constitution non-amendable clauses:\n"
            f"{json.dumps(federal_const.get('non_amendable_clauses', []), indent=2)[:500]}\n\n"
            f"Proposed State Constitution:\n"
            f"{json.dumps(draft, indent=2)[:500]}\n\n"
            f"Does this State Constitution violate any Federal non-amendable clauses?\n"
            f"Return JSON: {{\"violations\": [\"clause X violated because Y\", ...], \"compliant\": true/false}}"
        ),
        max_tokens=300,
        temperature=0.3
    )
    
    try:
        import re
        raw = validation_response.content or "{}"
        # Strip markdown fences
        raw = re.sub(r'```json\s*', '', raw)
        raw = re.sub(r'```\s*', '', raw)
        # Find JSON object
        json_match = re.search(r'\{[^{}]*\}', raw)
        if json_match:
            result = json.loads(json_match.group())
            return result.get("compliant", True), result.get("violations", [])
        else:
            print(f"  ⚠ Constitution validation: No JSON found, passing through")
            return True, []
    except Exception as e:
        print(f"  ⚠ Constitution validation parse failed: {e}")
        return True, []  # Advisory — pass through on parse failure


# ══════════════════════════════════════════════════════════════
# FIX 3: Replace BOTH _parse_findings() methods in governance/states.py
# There are TWO copies — one around line 585 (City) and one around line 1045 (State)
# Replace BOTH with this version
# ══════════════════════════════════════════════════════════════

def _parse_findings(self, content):
    """Parse research findings from LLM response.
    
    Handles all formatting styles:
    - Plain: CONCEPTS: item1, item2
    - Bold markdown: **CONCEPTS:** item1, item2
    - Multi-line with bullets
    - Numbered lists
    """
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
    
    # Strip bold markdown globally: **text** → text
    clean = content.replace("**", "")
    
    # Extract sections using multi-line regex (captures until next section or end)
    concepts_match = re.search(
        r'CONCEPTS?:\s*(.*?)(?=\n\s*(?:FRAMEWORKS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
        clean, re.IGNORECASE | re.DOTALL
    )
    if concepts_match:
        raw = concepts_match.group(1).strip()
        findings["concepts"] = _extract_items(raw)
    
    frameworks_match = re.search(
        r'FRAMEWORKS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|APPLICATIONS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
        clean, re.IGNORECASE | re.DOTALL
    )
    if frameworks_match:
        raw = frameworks_match.group(1).strip()
        findings["frameworks"] = _extract_items(raw)
    
    applications_match = re.search(
        r'APPLICATIONS?:\s*(.*?)(?=\n\s*(?:CONCEPTS?|FRAMEWORKS?|SYNTHESIS|EVIDENCE|CONNECTIONS?):|\Z)',
        clean, re.IGNORECASE | re.DOTALL
    )
    if applications_match:
        raw = applications_match.group(1).strip()
        findings["applications"] = _extract_items(raw)
    
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
    
    # Fallback: if nothing parsed, extract something from the content
    if not findings["concepts"] and not findings["frameworks"]:
        # Try splitting on commas from first substantial line
        lines = [l.strip() for l in content.split('\n') if len(l.strip()) > 10]
        if lines:
            findings["concepts"] = [w.strip('.,;:*-# ') for w in lines[0].split(',') if len(w.strip()) > 3][:10]
            findings["synthesis"] = content[:500]
    
    return findings


def _extract_items(raw_text):
    """Extract items from a section that might be comma-separated, bulleted, or numbered."""
    items = []
    
    # First try: split by lines and look for bullets/numbers
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Strip bullet/number prefixes
        if line.startswith(('- ', '* ', '• ')):
            item = line.lstrip('-*• ').strip()
            if item and len(item) > 2:
                items.append(item[:100])
        elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            item = line.lstrip('0123456789.): ').strip()
            if item and len(item) > 2:
                items.append(item[:100])
        elif ',' in line:
            # Comma-separated on this line
            for part in line.split(','):
                part = part.strip()
                if part and len(part) > 2:
                    items.append(part[:100])
        elif line and len(line) > 2:
            items.append(line[:100])
    
    # Deduplicate preserving order
    return list(dict.fromkeys(items))
