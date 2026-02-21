#!/usr/bin/env python3
"""
Generate lib/data.ts from the latest Atlantis engine run.

Usage:
    python generate_site_data.py                    # reads from output/archive.json
    python generate_site_data.py path/to/archive.json  # reads from specific file

Outputs: lib/data.ts (overwrites existing)
"""

import json
import sys
import os
from collections import defaultdict
from pathlib import Path


def load_archive(path: str = None) -> list:
    if path is None:
        # Try output/ symlink first, then find latest run
        candidates = [
            "output/archive.json",
            "runs/latest/archive.json",
        ]
        for c in candidates:
            if os.path.exists(c):
                path = c
                break
        if path is None:
            # Find the most recent runs/ folder
            runs_dir = Path("runs")
            if runs_dir.exists():
                run_dirs = sorted(runs_dir.iterdir(), reverse=True)
                for d in run_dirs:
                    candidate = d / "archive.json"
                    if candidate.exists():
                        path = str(candidate)
                        break
        if path is None:
            print("ERROR: No archive.json found. Run the engine first.")
            sys.exit(1)

    with open(path) as f:
        return json.load(f)


def escape_ts(s: str) -> str:
    """Escape a string for TypeScript template literal."""
    if not s:
        return ""
    return (
        s.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


def truncate(s: str, max_len: int = 300) -> str:
    if not s or len(s) <= max_len:
        return s or ""
    return s[:max_len].rsplit(" ", 1)[0] + "..."


def get_adversarial_claims(archive: list) -> list:
    """Get only Phase 2 adversarial claims (not founding era)."""
    return [
        e for e in archive
        if e.get("source_state", "") not in ("Founding Era", "")
        and e.get("source_state") is not None
        and "_" in e.get("source_state", "")
    ]


def get_domain(state_name: str) -> str:
    """Extract domain from state name like 'Consciousness_Alpha'."""
    parts = state_name.rsplit("_", 1)
    return parts[0] if len(parts) == 2 else state_name


def compute_states(claims: list) -> list:
    """Build state records from claims."""
    state_data = defaultdict(lambda: {
        "wins": 0, "partials": 0, "losses": 0,
        "claims": [], "approach": "", "learning_events": []
    })

    for c in claims:
        state = c.get("source_state", "")
        if not state:
            continue

        sd = state_data[state]
        sd["claims"].append(c)

        status = c.get("status", "")
        ruling = c.get("ruling_type", "")
        outcome = c.get("outcome", "")

        if status == "survived" or outcome == "survived":
            sd["wins"] += 1
        elif status == "partial" or outcome == "partial" or "REVISE" in ruling:
            sd["partials"] += 1
        elif status == "destroyed" or outcome == "destroyed" or "REJECT" in ruling:
            sd["losses"] += 1

        # Track learning events
        cycle = c.get("cycle_created", 0)
        position = truncate(c.get("position", ""), 150)
        if outcome == "destroyed" or status == "destroyed" or "REJECT" in ruling:
            sd["learning_events"].append(f"Cycle {cycle}: destroyed — {position}")
        elif status == "partial" or outcome == "partial":
            sd["learning_events"].append(f"Cycle {cycle}: partial — {position}")
        elif status == "survived" or outcome == "survived":
            sd["learning_events"].append(f"Cycle {cycle}: survived — {position}")

        # Use latest claim's position as approach
        if not sd["approach"] or cycle >= max(
            (cl.get("cycle_created", 0) for cl in sd["claims"]), default=0
        ):
            sd["approach"] = truncate(c.get("position", ""), 200)

    states = []
    for name, sd in sorted(state_data.items()):
        domain = get_domain(name)
        total = sd["wins"] + sd["partials"] + sd["losses"]
        survival = round((sd["wins"] + sd["partials"]) / total * 100) if total > 0 else 0

        # Build learning arc from events
        learning_arc = " ".join(sd["learning_events"][-3:]) if sd["learning_events"] else "No data yet."

        states.append({
            "name": name,
            "domain": domain,
            "approach": sd["approach"],
            "wins": sd["wins"],
            "partials": sd["partials"],
            "losses": sd["losses"],
            "survival": survival,
            "learningArc": learning_arc,
        })

    return states


def compute_chronicle(claims: list) -> list:
    """Build chronicle entries from claims grouped by cycle."""
    cycles = defaultdict(list)
    for c in claims:
        cycle = c.get("cycle_created", 0)
        if cycle > 0:
            cycles[cycle].append(c)

    titles = [
        "The Opening Arguments",
        "The Killing Fields",
        "Evolution",
        "Deepening",
        "The Reckoning",
        "New Foundations",
        "Convergence",
        "The Crucible",
        "Breakthrough",
        "The Long Game",
    ]

    entries = []
    for cycle_num in sorted(cycles.keys()):
        cycle_claims = cycles[cycle_num]
        total = len(cycle_claims)
        destroyed = sum(
            1 for c in cycle_claims
            if c.get("status") == "destroyed"
            or c.get("outcome") == "destroyed"
            or "REJECT" in c.get("ruling_type", "")
        )
        survived = sum(
            1 for c in cycle_claims
            if c.get("status") == "survived"
            or c.get("outcome") == "survived"
        )
        partial = sum(
            1 for c in cycle_claims
            if c.get("status") == "partial"
            or c.get("outcome") == "partial"
            or c.get("ruling_type", "") == "REVISE"
        )

        # Group by domain
        domains = defaultdict(list)
        for c in cycle_claims:
            domain = get_domain(c.get("source_state", "Unknown"))
            domains[domain].append(c)

        # Build narrative
        parts = []
        for domain, dclaims in sorted(domains.items()):
            d_destroyed = sum(
                1 for c in dclaims
                if c.get("status") == "destroyed"
                or c.get("outcome") == "destroyed"
                or "REJECT" in c.get("ruling_type", "")
            )
            d_survived = len(dclaims) - d_destroyed
            if d_destroyed == len(dclaims):
                parts.append(f"{domain}: all {len(dclaims)} claims destroyed.")
            elif d_destroyed == 0:
                parts.append(f"{domain}: all {len(dclaims)} claims survived or earned partials.")
            else:
                parts.append(f"{domain}: {d_survived} survived, {d_destroyed} destroyed.")

        narrative = f"Cycle {cycle_num} saw {total} claims across {len(domains)} domains. " + " ".join(parts)

        if destroyed > total * 0.7:
            narrative += " A brutal cycle."
        elif destroyed < total * 0.3:
            narrative += " The civilization is growing stronger."
        else:
            narrative += " The system is calibrating."

        title = titles[cycle_num - 1] if cycle_num <= len(titles) else f"Cycle {cycle_num}"

        entries.append({
            "cycle": cycle_num,
            "title": title,
            "narrative": narrative,
        })

    return entries


def compute_debates(claims: list) -> list:
    """Build debate entries from adversarial claims."""
    debates = []
    for c in claims:
        ruling_type = c.get("ruling_type", "")
        status = c.get("status", "")
        outcome = c.get("outcome", "")

        # Determine ruling label
        if "REJECT" in ruling_type or status == "destroyed" or outcome == "destroyed":
            ruling = "DESTROYED"
        elif ruling_type == "REVISE" or status == "partial" or outcome == "partial":
            ruling = "REVISE"
        elif status == "survived" or outcome == "survived":
            ruling = "SURVIVED"
        else:
            ruling = "PENDING"

        debates.append({
            "id": c.get("display_id", ""),
            "domain": get_domain(c.get("source_state", "")),
            "cycle": c.get("cycle_created", 0),
            "state": c.get("source_state", ""),
            "ruling": ruling,
            "position": truncate(c.get("position", ""), 300),
            "challenge": truncate(c.get("raw_challenge_text", ""), 500),
            "rebuttal": truncate(c.get("raw_rebuttal_text", ""), 500),
            "verdict": truncate(c.get("outcome_reasoning", ""), 500),
            "drama": c.get("drama_score", 0),
            "novelty": c.get("novelty_score", 0),
            "depth": c.get("depth_score", 0),
        })

    return sorted(debates, key=lambda d: (d["cycle"], d["id"]))


def compute_stats(claims: list) -> dict:
    domains = set()
    states = set()
    surviving = 0
    destroyed = 0

    for c in claims:
        state = c.get("source_state", "")
        if state:
            states.add(state)
            domains.add(get_domain(state))

        status = c.get("status", "")
        outcome = c.get("outcome", "")
        ruling = c.get("ruling_type", "")

        if status == "survived" or outcome == "survived":
            surviving += 1
        elif status == "partial" or outcome == "partial" or ruling == "REVISE":
            surviving += 1
        elif status == "destroyed" or outcome == "destroyed" or "REJECT" in ruling:
            destroyed += 1

    return {
        "domains": len(domains),
        "states": len(states),
        "surviving": surviving,
        "destroyed": destroyed,
    }


def generate_ts(archive: list) -> str:
    claims = get_adversarial_claims(archive)

    if not claims:
        print("WARNING: No adversarial claims found. Using all non-founding claims.")
        claims = [e for e in archive if e.get("source_state") != "Founding Era"]

    chronicle = compute_chronicle(claims)
    states = compute_states(claims)
    debates = compute_debates(claims)
    stats = compute_stats(claims)

    # Build graveyard from destroyed claims
    graveyard = [d for d in debates if d["ruling"] == "DESTROYED"]
    # Archive = surviving only
    archive_entries = [d for d in debates if d["ruling"] in ("SURVIVED", "REVISE")]

    lines = []

    # NAV
    lines.append('export const NAV_ITEMS = [')
    lines.append('  "Chronicle",')
    lines.append('  "States",')
    lines.append('  "Archive",')
    lines.append('  "Debates",')
    lines.append('  "Graveyard",')
    lines.append('  "About",')
    lines.append('] as const;')
    lines.append('')
    lines.append('export type NavItem = (typeof NAV_ITEMS)[number];')
    lines.append('')

    # Chronicle
    lines.append('export interface ChronicleEntry {')
    lines.append('  cycle: number;')
    lines.append('  title: string;')
    lines.append('  narrative: string;')
    lines.append('}')
    lines.append('')
    lines.append('export const CHRONICLE_ENTRIES: ChronicleEntry[] = [')
    for entry in chronicle:
        lines.append('  {')
        lines.append(f'    cycle: {entry["cycle"]},')
        lines.append(f'    title: "{escape_ts(entry["title"])}",')
        lines.append(f'    narrative:')
        lines.append(f'      "{escape_ts(entry["narrative"])}",')
        lines.append('  },')
    lines.append('];')
    lines.append('')

    # States
    lines.append('export interface StateEntity {')
    lines.append('  name: string;')
    lines.append('  domain: string;')
    lines.append('  approach: string;')
    lines.append('  wins: number;')
    lines.append('  partials: number;')
    lines.append('  losses: number;')
    lines.append('  learningArc: string;')
    lines.append('}')
    lines.append('')
    lines.append('export const STATES: StateEntity[] = [')
    for s in states:
        lines.append('  {')
        lines.append(f'    name: "{escape_ts(s["name"])}",')
        lines.append(f'    domain: "{escape_ts(s["domain"])}",')
        lines.append(f'    approach:')
        lines.append(f'      "{escape_ts(s["approach"])}",')
        lines.append(f'    wins: {s["wins"]},')
        lines.append(f'    partials: {s["partials"]},')
        lines.append(f'    losses: {s["losses"]},')
        lines.append(f'    learningArc:')
        lines.append(f'      "{escape_ts(s["learningArc"])}",')
        lines.append('  },')
    lines.append('];')
    lines.append('')

    # Debates
    lines.append('export interface Debate {')
    lines.append('  id: string;')
    lines.append('  domain: string;')
    lines.append('  cycle: number;')
    lines.append('  state: string;')
    lines.append('  ruling: string;')
    lines.append('  position: string;')
    lines.append('  challenge: string;')
    lines.append('  rebuttal: string;')
    lines.append('  verdict: string;')
    lines.append('  drama: number;')
    lines.append('  novelty: number;')
    lines.append('  depth: number;')
    lines.append('}')
    lines.append('')
    lines.append('export const DEBATES: Debate[] = [')
    for d in debates:
        lines.append('  {')
        lines.append(f'    id: "{escape_ts(d["id"])}",')
        lines.append(f'    domain: "{escape_ts(d["domain"])}",')
        lines.append(f'    cycle: {d["cycle"]},')
        lines.append(f'    state: "{escape_ts(d["state"])}",')
        lines.append(f'    ruling: "{escape_ts(d["ruling"])}",')
        lines.append(f'    position:')
        lines.append(f'      "{escape_ts(d["position"])}",')
        lines.append(f'    challenge:')
        lines.append(f'      "{escape_ts(d["challenge"])}",')
        lines.append(f'    rebuttal:')
        lines.append(f'      "{escape_ts(d["rebuttal"])}",')
        lines.append(f'    verdict:')
        lines.append(f'      "{escape_ts(d["verdict"])}",')
        lines.append(f'    drama: {d["drama"]},')
        lines.append(f'    novelty: {d["novelty"]},')
        lines.append(f'    depth: {d["depth"]},')
        lines.append('  },')
    lines.append('];')
    lines.append('')

    # Dispatches (generate from highest-scoring debates)
    top_debates = sorted(debates, key=lambda d: d["drama"] + d["novelty"] + d["depth"], reverse=True)[:2]
    lines.append('export interface Dispatch {')
    lines.append('  title: string;')
    lines.append('  domain: string;')
    lines.append('  cycle: number;')
    lines.append('  excerpt: string;')
    lines.append('  body: string;')
    lines.append('}')
    lines.append('')
    lines.append('export const DISPATCHES: Dispatch[] = [')
    for d in top_debates:
        title = f"The {d['domain']} Question: {truncate(d['position'], 60)}"
        excerpt = truncate(d["verdict"], 200)
        body = f"{d['position']}\\n\\nChallenge: {truncate(d['challenge'], 300)}\\n\\nRebuttal: {truncate(d['rebuttal'], 300)}\\n\\nVerdict: {d['verdict']}"
        lines.append('  {')
        lines.append(f'    title: "{escape_ts(title)}",')
        lines.append(f'    domain: "{escape_ts(d["domain"])}",')
        lines.append(f'    cycle: {d["cycle"]},')
        lines.append(f'    excerpt:')
        lines.append(f'      "{escape_ts(excerpt)}",')
        lines.append(f'    body: "{escape_ts(body)}",')
        lines.append('  },')
    lines.append('];')
    lines.append('')

    # News items (auto-generate from notable events)
    lines.append('export interface NewsItem {')
    lines.append('  headline: string;')
    lines.append('  body: string;')
    lines.append('}')
    lines.append('')
    lines.append('export const NEWS_ITEMS: NewsItem[] = [')

    # Find most destroyed domain
    domain_destroyed = defaultdict(int)
    for d in debates:
        if d["ruling"] == "DESTROYED":
            domain_destroyed[d["domain"]] += 1
    if domain_destroyed:
        worst_domain = max(domain_destroyed, key=domain_destroyed.get)
        lines.append('  {')
        lines.append(f'    headline: "{worst_domain.upper()} DOMAIN SUFFERS HEAVIEST LOSSES",')
        lines.append(f'    body: "The {worst_domain} domain has seen {domain_destroyed[worst_domain]} claims destroyed across all cycles, making it the most contested area of research in the civilization.",')
        lines.append('  },')

    # Find any state with all losses
    for s in states:
        if s["wins"] == 0 and s["partials"] == 0 and s["losses"] > 0:
            lines.append('  {')
            lines.append(f'    headline: "{escape_ts(s["name"].upper())} FACES EXISTENTIAL CRISIS",')
            lines.append(f'    body: "{escape_ts(s["name"])} has failed to produce a single surviving claim across {s["losses"]} attempts. The State faces potential dissolution if performance does not improve.",')
            lines.append('  },')
            break

    # Overall survival rate
    total = stats["surviving"] + stats["destroyed"]
    rate = round(stats["surviving"] / total * 100) if total > 0 else 0
    lines.append('  {')
    lines.append(f'    headline: "CIVILIZATION SURVIVAL RATE: {rate}%",')
    lines.append(f'    body: "Across {total} adversarial claims, {stats["surviving"]} have survived or earned partials while {stats["destroyed"]} were destroyed. The system is {"calibrating well" if 35 <= rate <= 65 else "running hot" if rate > 65 else "under severe pressure"}.",')
    lines.append('  },')
    lines.append('];')
    lines.append('')

    # About
    lines.append('export const ABOUT_PARAGRAPHS = [')
    lines.append('  "Atlantis is a knowledge platform where ideas are tested through structured debate. Claims enter the system. They are challenged. They must defend themselves. Only validated knowledge survives to become part of the permanent archive.",')
    lines.append('  "The result is a growing body of knowledge that has earned its place \\u2014 not through consensus or authority, but through adversarial pressure. Every surviving claim has been attacked and has defended itself successfully. Every destroyed claim teaches the system what doesn\\u2019t hold up.",')
    lines.append('  "The civilization is learning.",')
    lines.append('];')
    lines.append('')

    # Stats
    lines.append('export const STATS = {')
    lines.append(f'  domains: {stats["domains"]},')
    lines.append(f'  states: {stats["states"]},')
    lines.append(f'  surviving: {stats["surviving"]},')
    lines.append(f'  destroyed: {stats["destroyed"]},')
    lines.append('  // Getters for rebrand compatibility')
    lines.append('  get validated() { return this.surviving; },')
    lines.append('  get refuted() { return this.destroyed; },')
    lines.append('};')
    lines.append('')

    # Aliases for rebrand compatibility
    lines.append('// Rebrand-safe aliases')
    lines.append('export const HYPOTHESES = DEBATES;')
    lines.append('export type Hypothesis = Debate;')
    lines.append('export const CLAIMS = DEBATES;')
    lines.append('export type Claim = Debate;')
    lines.append('')

    return "\n".join(lines)


if __name__ == "__main__":
    archive_path = sys.argv[1] if len(sys.argv) > 1 else None
    archive = load_archive(archive_path)

    print(f"Loaded {len(archive)} archive entries")

    ts_content = generate_ts(archive)

    output_path = "lib/data.ts"
    with open(output_path, "w") as f:
        f.write(ts_content)

    claims = get_adversarial_claims(archive)
    stats = compute_stats(claims)
    print(f"Generated {output_path}:")
    print(f"  {stats['domains']} domains, {stats['states']} states")
    print(f"  {stats['surviving']} surviving, {stats['destroyed']} destroyed")
    print(f"  {len(compute_chronicle(claims))} chronicle entries")
    print(f"  {len(compute_debates(claims))} debates")
    print(f"  Site data is now LIVE")
