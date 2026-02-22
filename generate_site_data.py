#!/usr/bin/env python3
"""Generate lib/data.ts from Atlantis archive output."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DATA_TS_PATH = Path("lib/data.ts")
RUNS_DIR = Path("runs")
OUTPUT_ARCHIVE_PATH = Path("output/archive.json")

NAV_ITEMS = [
    "Research Timeline",
    "States",
    "Knowledge Base",
    "Debates",
    "Refuted",
    "About",
]

ABOUT_PARAGRAPHS = [
    "Atlantis is a knowledge platform where ideas are tested through structured research review. Hypotheses enter the system. They are challenged. They must defend themselves. Only validated knowledge survives to become part of the permanent knowledge base.",
    "The result is a growing body of knowledge that has earned its place — not through consensus or authority, but through adversarial pressure. Every validated hypothesis has been challenged and has defended itself successfully. Every refuted hypothesis teaches the system what doesn't hold up.",
    "The civilization is learning.",
]

STATUS_TO_RULING = {
    "surviving": "SURVIVED",
    "survived": "SURVIVED",
    "partial": "PARTIAL",
    "revised": "REVISE",
    "revise": "REVISE",
    "destroyed": "DESTROYED",
    "retracted": "DESTROYED",
    "overturned": "DESTROYED",
    "foundation_challenged": "DESTROYED",
    "chain_broken": "DESTROYED",
}


def _normalize_ruling(entry: dict[str, Any]) -> str:
    explicit = str(entry.get("ruling_type", "")).strip().upper()
    if explicit in {"SURVIVED", "PARTIAL", "REVISE", "DESTROYED"}:
        return explicit
    status = str(entry.get("status", "")).strip().lower()
    return STATUS_TO_RULING.get(status, "REVISE")


def _pick_latest_run_archive() -> Path | None:
    if not RUNS_DIR.exists() or not RUNS_DIR.is_dir():
        return None
    candidates = [p for p in RUNS_DIR.iterdir() if p.is_dir()]
    if not candidates:
        return None
    latest = sorted(candidates, key=lambda p: p.name)[-1]
    archive = latest / "archive.json"
    return archive if archive.exists() else None


def _resolve_input_path(cli_input: str | None) -> Path | None:
    if cli_input:
        p = Path(cli_input)
        return p if p.exists() else None

    run_archive = _pick_latest_run_archive()
    if run_archive:
        return run_archive
    if OUTPUT_ARCHIVE_PATH.exists():
        return OUTPUT_ARCHIVE_PATH
    return None


def _extract_field(text: str, labels: list[str]) -> str:
    if not text:
        return ""
    for label in labels:
        pattern = rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*(.+)$"
        m = re.search(pattern, text)
        if m:
            return m.group(1).strip()
    return ""


def _infer_domain(entry: dict[str, Any]) -> str:
    for key in ("domain", "topic_domain"):
        value = str(entry.get(key, "")).strip()
        if value:
            return value
    source_state = str(entry.get("source_state", "")).strip()
    if "_" in source_state:
        return source_state.split("_", 1)[0]
    return "Unknown"


def _to_hypothesis(entry: dict[str, Any]) -> dict[str, Any]:
    raw_claim = str(entry.get("raw_claim_text", "") or "")
    position = str(entry.get("position", "") or "").strip() or _extract_field(raw_claim, ["POSITION", "MAIN STATEMENT"])
    hypothesis_text = _extract_field(raw_claim, ["HYPOTHESIS", "THESIS"])
    if not hypothesis_text:
        hypothesis_text = position

    op_def = _extract_field(raw_claim, ["OPERATIONAL_DEF", "OPERATIONAL DEFINITION"]) or ""
    prediction = _extract_field(raw_claim, ["PREDICTION", "TESTABLE IMPLICATION"]) or ""

    challenge = str(entry.get("raw_challenge_text", "") or "").strip()
    rebuttal = str(entry.get("raw_rebuttal_text", "") or "").strip()
    verdict = str(entry.get("outcome_reasoning", "") or "").strip() or str(entry.get("conclusion", "") or "").strip() or str(entry.get("outcome", "") or "").strip()

    hyp: dict[str, Any] = {
        "id": str(entry.get("display_id", "") or "").strip() or str(entry.get("entry_id", "")).strip()[:8],
        "domain": _infer_domain(entry),
        "cycle": int(entry.get("cycle_created", 0) or 0),
        "state": str(entry.get("source_state", "") or "Unknown"),
        "ruling": _normalize_ruling(entry),
        "validation_json": entry.get("validation_json"),
        "position": position or str(entry.get("conclusion", "") or "").strip() or "No position recorded.",
        "challenge": challenge or "No formal challenge was recorded.",
        "rebuttal": rebuttal or "No rebuttal was recorded.",
        "verdict": verdict or "Verdict unavailable.",
        "drama": int(entry.get("drama_score", 0) or 0),
        "novelty": int(entry.get("novelty_score", 0) or 0),
        "depth": int(entry.get("depth_score", 0) or 0),
        "hypothesis": hypothesis_text,
    }
    if op_def:
        hyp["operational_def"] = op_def
    if prediction:
        hyp["prediction"] = prediction

    # Include validation results if present
    validation_json = entry.get("validation_json")
    if validation_json:
        try:
            validation_data = json.loads(validation_json) if isinstance(validation_json, str) else validation_json
            hyp["validation"] = validation_data
        except (json.JSONDecodeError, TypeError):
            pass  # Skip malformed validation data

    return hyp


def _cycle_title(cycle: int, rulings: Counter[str]) -> str:
    destroyed = rulings["DESTROYED"]
    validated = rulings["SURVIVED"] + rulings["PARTIAL"] + rulings["REVISE"]
    if cycle == 1:
        return "The Opening Arguments"
    if destroyed >= max(2, validated * 2):
        return "The Killing Fields"
    if validated > destroyed:
        return "Learning Under Fire"
    return "Trial by Adversary"


def _build_cycle_narrative(cycle: int, entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_domain: dict[str, Counter[str]] = defaultdict(Counter)
    rulings = Counter()
    for h in entries:
        by_domain[h["domain"]][h["ruling"]] += 1
        rulings[h["ruling"]] += 1

    domain_phrases = []
    for domain in sorted(by_domain):
        c = by_domain[domain]
        domain_phrases.append(
            f"{domain}: {c['SURVIVED']} survived, {c['PARTIAL'] + c['REVISE']} validated-with-revisions, {c['DESTROYED']} refuted"
        )

    narrative = (
        f"Cycle {cycle} intensified the rivalry. "
        f"Outcomes were {rulings['SURVIVED']} survived, {rulings['PARTIAL'] + rulings['REVISE']} revised/partial, and {rulings['DESTROYED']} destroyed. "
        f"Domain breakdown — {'; '.join(domain_phrases)}."
    )

    return {
        "cycle": cycle,
        "title": _cycle_title(cycle, rulings),
        "narrative": narrative,
    }


def _build_states(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for h in hypotheses:
        grouped[h["state"]].append(h)

    states: list[dict[str, Any]] = []
    for state_name, entries in sorted(grouped.items()):
        entries = sorted(entries, key=lambda x: (x["cycle"], x["id"]))
        rulings = Counter(e["ruling"] for e in entries)
        approach = entries[0]["position"]
        learning_arc = (
            f"Across {len({e['cycle'] for e in entries})} cycle(s), {state_name} logged "
            f"{rulings['SURVIVED']} survivals, {rulings['PARTIAL'] + rulings['REVISE']} partial/revise outcomes, "
            f"and {rulings['DESTROYED']} destructive losses. "
            f"Most recent move: {entries[-1]['position'][:160]}."
        )
        states.append(
            {
                "name": state_name,
                "domain": entries[0]["domain"],
                "approach": approach,
                "wins": rulings["SURVIVED"],
                "partials": rulings["PARTIAL"] + rulings["REVISE"],
                "losses": rulings["DESTROYED"],
                "learningArc": learning_arc,
            }
        )
    return states


def _build_domain_pairs(states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group rival states by domain into Alpha/Beta pairs."""
    # Exclude "Founding Era" and group by domain
    rival_states = [s for s in states if s["name"] != "Founding Era"]

    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for state in rival_states:
        by_domain[state["domain"]].append(state)

    pairs = []
    for domain in sorted(by_domain.keys()):
        domain_states = sorted(by_domain[domain], key=lambda s: s["name"])
        if len(domain_states) >= 2:
            # Find Alpha and Beta
            alpha = next((s for s in domain_states if "Alpha" in s["name"]), domain_states[0])
            beta = next((s for s in domain_states if "Beta" in s["name"]), domain_states[1])
            pairs.append({
                "domain": domain,
                "alpha": alpha["name"],
                "beta": beta["name"],
            })
        elif len(domain_states) == 1:
            # Single state in domain (unusual but handle it)
            pairs.append({
                "domain": domain,
                "alpha": domain_states[0]["name"],
                "beta": None,
            })

    return pairs


def _build_dispatches(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dramatic = sorted([h for h in hypotheses if h["drama"] >= 7], key=lambda x: (x["drama"], x["depth"], x["novelty"]), reverse=True)
    dispatches = []
    for h in dramatic[:6]:
        title = f"Dispatch: {h['state']} Faces {h['ruling']} in {h['domain']}"
        excerpt = f"Cycle {h['cycle']} brought a drama score of {h['drama']} as {h['state']} tested '{h['hypothesis'][:90]}'."
        body = (
            f"In Cycle {h['cycle']}, {h['state']} advanced a high-stakes hypothesis in {h['domain']}. "
            f"The court's ruling was {h['ruling']}. Challenge pressure centered on: {h['challenge']} "
            f"Why it matters: this result shifts the domain's trajectory by clarifying which reasoning survives adversarial review."
        )
        dispatches.append({"title": title, "domain": h["domain"], "cycle": h["cycle"], "excerpt": excerpt, "body": body})
    return dispatches


def _build_news(hypotheses: list[dict[str, Any]]) -> list[dict[str, str]]:
    top = sorted(hypotheses, key=lambda x: (x["drama"], x["depth"], x["novelty"]), reverse=True)[:3]
    out = []
    for h in top:
        headline = f"{h['domain'].upper()}: {h['state']} ruled {h['ruling']} (Cycle {h['cycle']})"
        body = (
            f"A high-drama event ({h['drama']}/10) reshaped {h['domain']}. "
            f"Claim: {h['hypothesis']}. Verdict: {h['verdict']}"
        )
        out.append({"headline": headline, "body": body})
    return out


def _to_ts_literal(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def generate_ts(entries: list[dict[str, Any]]) -> str:
    hypotheses = [_to_hypothesis(e) for e in entries if str(e.get("entry_type", "claim")) in {"claim", "analysis", "proposal"}]
    hypotheses.sort(key=lambda x: (x["cycle"], x["id"]))

    domains = sorted({h["domain"] for h in hypotheses})
    domain_union = " | ".join(json.dumps(d, ensure_ascii=False) for d in domains) if domains else '"Unknown"'

    cycles: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for h in hypotheses:
        cycles[h["cycle"]].append(h)
    chronicle = [_build_cycle_narrative(cycle, cycles[cycle]) for cycle in sorted(cycles)]

    states = _build_states(hypotheses)
    domain_pairs = _build_domain_pairs(states)
    dispatches = _build_dispatches(hypotheses)
    news_items = _build_news(hypotheses)

    validated = sum(1 for h in hypotheses if h["ruling"] in {"SURVIVED", "PARTIAL", "REVISE"})
    refuted = sum(1 for h in hypotheses if h["ruling"] == "DESTROYED")

    parts = [
        "export const NAV_ITEMS = " + _to_ts_literal(NAV_ITEMS) + " as const;",
        "",
        "export type NavItem = (typeof NAV_ITEMS)[number];",
        f"export type Domain = {domain_union};",
        "",
        "export interface ChronicleEntry {",
        "  cycle: number;",
        "  title: string;",
        "  narrative: string;",
        "}",
        "",
        "export const CHRONICLE_ENTRIES: ChronicleEntry[] = " + _to_ts_literal(chronicle) + ";",
        "",
        "export interface StateEntity {",
        "  name: string;",
        "  domain: Domain;",
        "  approach: string;",
        "  wins: number;",
        "  partials: number;",
        "  losses: number;",
        "  learningArc: string;",
        "}",
        "",
        "export const STATES: StateEntity[] = " + _to_ts_literal(states) + ";",
        "",
        "export interface DomainPair {",
        "  domain: Domain;",
        "  alpha: string;",
        "  beta: string | null;",
        "}",
        "",
        "export const DOMAIN_PAIRS: DomainPair[] = " + _to_ts_literal(domain_pairs) + ";",
        "",
        "export interface Hypothesis {",
        "  id: string;",
        "  domain: Domain;",
        "  cycle: number;",
        "  state: string;",
        "  ruling: \"REVISE\" | \"PARTIAL\" | \"DESTROYED\" | \"SURVIVED\";",
        "  position: string;",
        "  hypothesis?: string;",
        "  operational_def?: string;",
        "  prediction?: string;",
        "  challenge: string;",
        "  rebuttal: string;",
        "  verdict: string;",
        "  drama: number;",
        "  novelty: number;",
        "  depth: number;",
        "  validation_json?: string | null;",
        "  validation?: {",
        "    all_passed: boolean;",
        "    flags: string[];",
        "    warnings: string[];",
        "    info: string[];",
        "  };",
        "}",
        "",
        "export const HYPOTHESES: Hypothesis[] = " + _to_ts_literal(hypotheses) + ";",
        "",
        "export interface Dispatch {",
        "  title: string;",
        "  domain: Domain;",
        "  cycle: number;",
        "  excerpt: string;",
        "  body: string;",
        "}",
        "",
        "export const DISPATCHES: Dispatch[] = " + _to_ts_literal(dispatches) + ";",
        "",
        "export interface NewsItem {",
        "  headline: string;",
        "  body: string;",
        "}",
        "",
        "export const NEWS_ITEMS: NewsItem[] = " + _to_ts_literal(news_items) + ";",
        "",
        "export const ABOUT_PARAGRAPHS = " + _to_ts_literal(ABOUT_PARAGRAPHS) + ";",
        "",
        "export const STATS = "
        + _to_ts_literal(
            {
                "domains": len(domains),
                "states": len(states),
                "validated": validated,
                "refuted": refuted,
            }
        )
        + ";",
        "",
        "export const DEBATES = HYPOTHESES;",
        "export type Debate = Hypothesis;",
        "export const CLAIMS = DEBATES;",
        "export type Claim = Debate;",
        "",
    ]
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate lib/data.ts from archive JSON")
    parser.add_argument("--input", help="Path to archive.json", default=None)
    args = parser.parse_args()

    input_path = _resolve_input_path(args.input)
    if input_path is None:
        print("Warning: no archive source found (runs/*/archive.json or output/archive.json). data.ts was not modified.")
        return

    try:
        entries = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: failed to read archive data from {input_path}: {exc}. data.ts was not modified.")
        return

    if not isinstance(entries, list):
        print(f"Warning: archive payload at {input_path} is not a JSON list. data.ts was not modified.")
        return

    DATA_TS_PATH.write_text(generate_ts(entries), encoding="utf-8")
    print(f"Generated {DATA_TS_PATH} from {input_path}")


if __name__ == "__main__":
    main()
