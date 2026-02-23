"""Generate prompt-improvement proposals from Atlantis run artifacts."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import MODEL_IDS
from core.llm import LLMProvider

SEVERITY = {
    "LOGIC_FAILURE": 3,
    "EVIDENCE_INSUFFICIENT": 2,
    "PARAMETER_UNJUSTIFIED": 2,
    "MAGNITUDE_IMPLAUSIBLE": 2,
    "SCOPE_EXCEEDED": 1,
    "DEPENDENCY_FAILURE": 1,
    "CRITIC_TOO_PASSIVE": 5,
}

MAX_PROPOSALS = 10

PROMPT_MARKERS = {
    "RESEARCHER_PROMPT": ("# === RESEARCHER_PROMPT_START ===", "# === RESEARCHER_PROMPT_END ==="),
    "CRITIC_PROMPT": ("# === CRITIC_PROMPT_START ===", "# === CRITIC_PROMPT_END ==="),
}


def _next_version(current: str) -> str:
    parts = current.lstrip("v").split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return "v" + ".".join(parts)


@dataclass
class FailurePattern:
    pattern: str
    score: float
    frequency: int
    affected_domains: list[str]
    affected_states: list[str]


class MetaOptimizer:
    def __init__(
        self,
        runs_dir: Path | str = "runs",
        states_file: Path | str = "governance/states.py",
        history_file: Path | str = "meta/history.json",
        proposals_dir: Path | str = "meta/proposals",
        llm_mode: str = "auto",
    ):
        self.runs_dir = Path(runs_dir)
        self.states_file = Path(states_file)
        self.history_file = Path(history_file)
        self.proposals_dir = Path(proposals_dir)
        self.llm = LLMProvider(mode=llm_mode)
        print(f"[OPTIMIZER] LLM initialized in mode: {self.llm.mode}")
        if self.llm.mode == "local":
            print("[OPTIMIZER] WARNING: Running in local simulation mode - set ANTHROPIC_API_KEY to use real API")

    def run(self, run_path: str | None = None, cost_mode: bool = False) -> Path:
        run_dir = self._resolve_run(run_path)
        archive = self._load_archive(run_dir)
        history = self._load_history()

        if cost_mode:
            payload = self._run_cost_optimization(run_dir, archive)
            self.proposals_dir.mkdir(parents=True, exist_ok=True)
            out = self.proposals_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_cost_proposal.json"
            out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return out

        top_patterns = self._rank_failures(archive, run_dir)[:MAX_PROPOSALS]
        prompt_text = self.states_file.read_text(encoding="utf-8")

        proposals = []
        for rank, pattern in enumerate(top_patterns, start=1):
            target_section = "CRITIC_PROMPT" if pattern.pattern in {"LOGIC_FAILURE", "CRITIC_TOO_PASSIVE"} else "RESEARCHER_PROMPT"
            current_excerpt = self._extract_prompt(prompt_text, target_section)
            proposal = self._draft_proposal(run_dir, pattern, rank, target_section, current_excerpt)
            if self._is_oscillating(proposal, history):
                proposal["status"] = "REJECTED"
                proposal["adversarial_review"]["meta_judge_ruling"] += (
                    "\nRejected by anti-oscillation guard due to recent contradictory edits."
                )
                proposal["adversarial_review"]["ruling"] = "REJECTED"
            proposals.append(proposal)

        payload = {
            "run_analyzed": str(run_dir),
            "prompt_version": _next_version(self._prompt_version()),
            "failure_patterns": [self._pattern_json(p, i + 1, archive) for i, p in enumerate(top_patterns)],
            "proposals": proposals,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "llm_cost_usd_estimate": round(self.llm.get_stats().get("total_cost_usd", 0.0), 6),
        }

        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        out = self.proposals_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_proposal.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return out

    def _run_cost_optimization(self, run_dir: Path, archive: dict[str, Any]) -> dict[str, Any]:
        cost_summary = self._load_cost_summary(run_dir)
        previous_run = self._previous_run(run_dir)
        previous_cost_summary = self._load_cost_summary(previous_run) if previous_run else {}
        previous_archive = self._load_archive(previous_run) if previous_run else {}

        savings_candidates = []
        savings_candidates.extend(self._detect_prompt_bloat(run_dir, archive, cost_summary, previous_archive, previous_cost_summary))
        savings_candidates.extend(self._detect_model_tier_opportunities(cost_summary))
        savings_candidates.extend(self._detect_redundant_validation(run_dir, archive, cost_summary))
        savings_candidates.extend(self._detect_token_budget_waste(run_dir, cost_summary))

        proposals = [self._draft_cost_proposal(run_dir, i + 1, candidate) for i, candidate in enumerate(savings_candidates[:10])]

        return {
            "analysis_mode": "cost_optimization",
            "run_analyzed": str(run_dir),
            "baseline_run": str(previous_run) if previous_run else None,
            "prompt_version": _next_version(self._prompt_version()),
            "summary": {
                "proposal_count": len(proposals),
                "estimated_total_savings_per_run_usd": round(sum(p["cost_delta"]["estimated_savings_per_run_usd"] for p in proposals), 6),
            },
            "proposals": proposals,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "llm_cost_usd_estimate": round(self.llm.get_stats().get("total_cost_usd", 0.0), 6),
        }

    def _resolve_run(self, run_path: str | None) -> Path:
        if run_path:
            return Path(run_path)
        candidates = sorted([p for p in self.runs_dir.iterdir() if p.is_dir()])
        if not candidates:
            raise FileNotFoundError("No run directories found under runs/")
        return candidates[-1]

    @staticmethod
    def _load_archive(run_dir: Path) -> dict[str, Any]:
        return json.loads((run_dir / "archive.json").read_text(encoding="utf-8"))

    @staticmethod
    def _load_domain_health(run_dir: Path) -> dict[str, Any]:
        path = run_dir / "domain_health.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_history(self) -> dict[str, Any]:
        if not self.history_file.exists():
            return {"events": []}
        return json.loads(self.history_file.read_text(encoding="utf-8"))

    @staticmethod
    def _load_cost_summary(run_dir: Path | None) -> dict[str, Any]:
        if not run_dir:
            return {}
        path = run_dir / "cost_summary.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _previous_run(self, run_dir: Path) -> Path | None:
        candidates = sorted([p for p in self.runs_dir.iterdir() if p.is_dir()])
        try:
            idx = candidates.index(run_dir)
        except ValueError:
            return None
        if idx <= 0:
            return None
        return candidates[idx - 1]

    def _draft_cost_proposal(self, run_dir: Path, rank: int, candidate: dict[str, Any]) -> dict[str, Any]:
        alpha_prompt = self._alpha_cost_prompt(run_dir, candidate)
        alpha = self._call_llm(alpha_prompt, MODEL_IDS["haiku"], 1000)

        beta_prompt = (
            "You are Meta_Beta. Attack this cost savings proposal with strongest quality-risk objections.\n"
            f"Proposal:\n{alpha}\n"
            "Argue why quality, recall, or safety will regress if this change ships."
        )
        beta = self._call_llm(beta_prompt, MODEL_IDS["haiku"], 700)

        rebut_prompt = (
            "You are Meta_Alpha. Rebut each objection with run-data grounded defense.\n"
            f"Original proposal:\n{alpha}\n\nObjections:\n{beta}"
        )
        rebuttal = self._call_llm(rebut_prompt, MODEL_IDS["haiku"], 800)

        judge_prompt = (
            "You are Meta_Judge. Decide APPROVE, NARROW, or REJECT.\n"
            "Prioritize net savings but reject if quality risk is too high.\n"
            f"Proposal:\n{alpha}\n\nObjection:\n{beta}\n\nRebuttal:\n{rebuttal}"
        )
        judge = self._call_llm(judge_prompt, MODEL_IDS["sonnet"], 800)
        ruling = self._extract_ruling(judge)
        status = {"APPROVE": "APPROVED", "NARROW": "NARROWED", "REJECT": "REJECTED"}.get(ruling, "NARROWED")

        return {
            "proposal_id": f"cost_{rank}",
            "category": candidate["category"],
            "component": candidate["component"],
            "status": status,
            "approval": "PENDING_HUMAN",
            "evidence": candidate["evidence"],
            "proposal": candidate["proposal"],
            "cost_delta": candidate["cost_delta"],
            "risk_assessment": candidate["risk_assessment"],
            "adversarial_review": {
                "meta_beta_objection": beta,
                "meta_alpha_rebuttal": rebuttal,
                "meta_judge_ruling": judge,
                "ruling": status,
            },
        }

    def _alpha_cost_prompt(self, run_dir: Path, candidate: dict[str, Any]) -> str:
        return (
            "You are Meta_Alpha performing COST OPTIMIZATION for Atlantis.\n"
            f"Run: {run_dir}\n"
            f"Category: {candidate['category']}\n"
            f"Component: {candidate['component']}\n"
            f"Evidence: {json.dumps(candidate['evidence'])}\n"
            f"Current cost per run: ${candidate['cost_delta']['current_cost_per_run_usd']:.6f}\n"
            f"Proposed cost per run: ${candidate['cost_delta']['proposed_cost_per_run_usd']:.6f}\n"
            f"Estimated savings per run: ${candidate['cost_delta']['estimated_savings_per_run_usd']:.6f}\n"
            f"Risk: {candidate['risk_assessment']}\n"
            "Write a concise implementation proposal and why quality should remain acceptable."
        )

    @staticmethod
    def _survival_rate(archive: dict[str, Any]) -> float:
        entries = archive.get("archive_entries", []) if isinstance(archive, dict) else []
        considered = [e for e in entries if (e.get("status") or "").lower() != "founding"]
        if not considered:
            return 0.0
        survived = sum(1 for e in considered if (e.get("status") or "").lower() in {"survived", "partial"})
        return survived / len(considered)

    def _detect_prompt_bloat(
        self,
        run_dir: Path,
        archive: dict[str, Any],
        cost_summary: dict[str, Any],
        previous_archive: dict[str, Any],
        previous_cost_summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not previous_cost_summary:
            return []
        curr_tasks = cost_summary.get("cost_by_task_type", {})
        prev_tasks = previous_cost_summary.get("cost_by_task_type", {})
        survival_delta = self._survival_rate(archive) - self._survival_rate(previous_archive)
        proposals = []
        for task, curr in curr_tasks.items():
            prev = prev_tasks.get(task)
            if not prev:
                continue
            curr_calls = max(int(curr.get("calls", 0)), 1)
            prev_calls = max(int(prev.get("calls", 0)), 1)
            curr_avg_in = float(curr.get("input_tokens", 0)) / curr_calls
            prev_avg_in = float(prev.get("input_tokens", 0)) / prev_calls
            if prev_avg_in <= 0:
                continue
            growth = (curr_avg_in - prev_avg_in) / prev_avg_in
            if growth <= 0.20 or survival_delta > 0.01:
                continue
            current_cost = float(curr.get("cost_usd", 0.0))
            proposed_cost = current_cost * 0.85
            proposals.append(
                {
                    "category": "PROMPT_BLOAT",
                    "component": task,
                    "evidence": {
                        "avg_input_tokens_previous": round(prev_avg_in, 2),
                        "avg_input_tokens_current": round(curr_avg_in, 2),
                        "token_growth_pct": round(growth * 100, 2),
                        "overall_survival_delta_pct": round(survival_delta * 100, 2),
                    },
                    "proposal": "Compress repeated instructions and move static rubric text into shorter canonical bullets.",
                    "cost_delta": {
                        "current_cost_per_run_usd": round(current_cost, 6),
                        "proposed_cost_per_run_usd": round(proposed_cost, 6),
                        "estimated_savings_per_run_usd": round(current_cost - proposed_cost, 6),
                    },
                    "risk_assessment": "Compression may remove nuance and reduce edge-case handling in adversarial prompts.",
                }
            )
        return proposals

    def _detect_model_tier_opportunities(self, cost_summary: dict[str, Any]) -> list[dict[str, Any]]:
        tasks = cost_summary.get("cost_by_task_type", {})
        sonnet_tasks = {k: v for k, v in tasks.items() if MODEL_IDS.get("sonnet") and k in {"researcher_claims", "critic_challenges", "researcher_rebuttals", "federal_lab", "judge"}}
        proposals = []
        for task, bucket in sonnet_tasks.items():
            calls = max(int(bucket.get("calls", 0)), 1)
            avg_output = float(bucket.get("output_tokens", 0)) / calls
            if avg_output > 450:
                continue
            current_cost = float(bucket.get("cost_usd", 0.0))
            proposed_cost = current_cost * 0.35
            proposals.append(
                {
                    "category": "MODEL_TIER_OPPORTUNITY",
                    "component": task,
                    "evidence": {
                        "current_tier": "sonnet",
                        "proposed_tier": "haiku",
                        "calls": calls,
                        "avg_output_tokens": round(avg_output, 2),
                    },
                    "proposal": f"Route {task} to Haiku for low-complexity cases; keep Sonnet fallback when confidence is low.",
                    "cost_delta": {
                        "current_cost_per_run_usd": round(current_cost, 6),
                        "proposed_cost_per_run_usd": round(proposed_cost, 6),
                        "estimated_savings_per_run_usd": round(current_cost - proposed_cost, 6),
                    },
                    "risk_assessment": "Haiku downgrade may reduce reasoning depth on hard samples unless fallback routing is enforced.",
                }
            )
        return proposals[:3]

    def _detect_redundant_validation(
        self,
        run_dir: Path,
        archive: dict[str, Any],
        cost_summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        tasks = cost_summary.get("cost_by_task_type", {})
        entries = archive.get("archive_entries", [])
        rejection_text = "\n".join(
            str(e.get("rejection_reason") or "") + " " + str(e.get("retraction_reason") or "")
            for e in entries
        ).lower()
        validation_keywords = {
            "anti_loop": ["loop", "circular"],
            "rebuttal_newness": ["duplicate", "newness", "novelty"],
            "premise_decomposition": ["premise", "decomposition"],
            "science_gate": ["science gate", "scientific"],
            "normalization": ["normalize", "format"],
        }
        proposals = []
        for task, keys in validation_keywords.items():
            bucket = tasks.get(task)
            if not bucket or int(bucket.get("calls", 0)) < 20:
                continue
            catches = sum(rejection_text.count(k) for k in keys)
            if catches != 0:
                continue
            current_cost = float(bucket.get("cost_usd", 0.0))
            proposed_cost = current_cost * 0.25
            proposals.append(
                {
                    "category": "REDUNDANT_VALIDATION",
                    "component": task,
                    "evidence": {
                        "run": str(run_dir),
                        "calls": int(bucket.get("calls", 0)),
                        "estimated_rejections_caught": catches,
                        "estimated_rejection_rate": 0.0,
                    },
                    "proposal": f"Consolidate {task} into adjacent validation stage and execute only on high-risk samples.",
                    "cost_delta": {
                        "current_cost_per_run_usd": round(current_cost, 6),
                        "proposed_cost_per_run_usd": round(proposed_cost, 6),
                        "estimated_savings_per_run_usd": round(current_cost - proposed_cost, 6),
                    },
                    "risk_assessment": "Hidden failure modes may reappear if this validator is removed entirely; keep periodic audit sampling.",
                }
            )
        return proposals

    def _detect_token_budget_waste(self, run_dir: Path, cost_summary: dict[str, Any]) -> list[dict[str, Any]]:
        tasks = cost_summary.get("cost_by_task_type", {})
        token_limits = self._extract_task_token_limits(run_dir)
        proposals = []
        for task, bucket in tasks.items():
            max_tokens = token_limits.get(task)
            if not max_tokens:
                continue
            calls = max(int(bucket.get("calls", 0)), 1)
            avg_output = float(bucket.get("output_tokens", 0)) / calls
            utilization = avg_output / max_tokens
            current_cost = float(bucket.get("cost_usd", 0.0))
            if utilization >= 0.95:
                proposed_cost = current_cost * 0.9
                proposal_text = "Increase max_tokens slightly and compress prompt headers to reduce truncation retries."
                risk = "More tokens can increase spend if truncation diagnosis is wrong."
            elif utilization < 0.50:
                proposed_cost = current_cost * 0.92
                proposal_text = "Reduce max_tokens allocation for this state/task to better match observed output usage."
                risk = "Tighter caps may clip rare high-complexity outputs."
            else:
                continue
            proposals.append(
                {
                    "category": "TOKEN_BUDGET_WASTE",
                    "component": task,
                    "evidence": {
                        "calls": calls,
                        "avg_output_tokens": round(avg_output, 2),
                        "max_tokens": max_tokens,
                        "budget_utilization_pct": round(utilization * 100, 2),
                    },
                    "proposal": proposal_text,
                    "cost_delta": {
                        "current_cost_per_run_usd": round(current_cost, 6),
                        "proposed_cost_per_run_usd": round(proposed_cost, 6),
                        "estimated_savings_per_run_usd": round(current_cost - proposed_cost, 6),
                    },
                    "risk_assessment": risk,
                }
            )
        return proposals

    def _extract_task_token_limits(self, run_dir: Path) -> dict[str, int]:
        states_path = run_dir.parent.parent / "governance" / "states.py"
        if not states_path.exists():
            states_path = Path("governance/states.py")
        text = states_path.read_text(encoding="utf-8")
        pattern = re.compile(r'task_type\s*=\s*"([a-z_]+)"[\s\S]{0,240}?max_tokens\s*=\s*(\d+)')
        out: dict[str, int] = {}
        for task, tok in pattern.findall(text):
            out[task] = max(out.get(task, 0), int(tok))
        return out

    def _rank_failures(self, archive: dict[str, Any], run_dir: Path) -> list[FailurePattern]:
        entries = archive.get("archive_entries", [])
        domain_survival = {
            d.get("domain"): max(float(d.get("survival_rate", 0.0)), 0.01)
            for d in archive.get("domain_metrics", [])
        }
        domain_health = self._load_domain_health(run_dir)

        counts = Counter()
        domains_by_reason: dict[str, set[str]] = defaultdict(set)
        states_by_reason: dict[str, set[str]] = defaultdict(set)
        score_acc = defaultdict(float)

        for e in entries:
            reason_tags = e.get("reason_tags") or []
            if isinstance(reason_tags, str):
                reason_tags = [reason_tags]
            if not reason_tags and e.get("retraction_reason"):
                reason_tags = [e.get("retraction_reason")]
            domain = self._domain_from_state(e.get("source_state", ""))
            for tag in reason_tags:
                tag = str(tag).strip().upper()
                if tag not in SEVERITY:
                    continue
                counts[tag] += 1
                domains_by_reason[tag].add(domain)
                states_by_reason[tag].add(e.get("source_state", ""))
                weight = 1.0 / domain_survival.get(domain, 0.1)
                score_acc[tag] += SEVERITY[tag] * weight

        passive_domains = []
        for domain, metrics in domain_health.items():
            if not isinstance(metrics, dict):
                continue
            flags = metrics.get("flags") or {}
            survival = float(metrics.get("survival_rate", 0.0))
            weak_critic = bool(flags.get("weak_critic_warning"))
            if survival >= 0.999 and weak_critic:
                passive_domains.append(domain)

        if passive_domains:
            tag = "CRITIC_TOO_PASSIVE"
            counts[tag] = len(passive_domains)
            domains_by_reason[tag].update(passive_domains)
            passive_states = {
                e.get("source_state", "")
                for e in entries
                if self._domain_from_state(e.get("source_state", "")) in passive_domains
            }
            states_by_reason[tag].update(s for s in passive_states if s)
            score_acc[tag] += SEVERITY[tag] * len(passive_domains) * 2

        ranked = [
            FailurePattern(
                pattern=k,
                score=round(v, 3),
                frequency=counts[k],
                affected_domains=sorted(d for d in domains_by_reason[k] if d),
                affected_states=sorted(s for s in states_by_reason[k] if s),
            )
            for k, v in score_acc.items()
        ]
        ranked.sort(key=lambda p: p.score, reverse=True)
        return ranked[:MAX_PROPOSALS]

    def _draft_proposal(
        self,
        run_dir: Path,
        pattern: FailurePattern,
        rank: int,
        target_section: str,
        current_excerpt: str,
    ) -> dict[str, Any]:
        alpha_prompt = self._alpha_prompt(pattern, target_section, current_excerpt)
        alpha = self._call_llm(alpha_prompt, MODEL_IDS["haiku"], 1200)

        beta_prompt = (
            "You are Meta_Beta. Attack this proposal with the strongest objections.\n"
            f"Proposal:\n{alpha}\n"
            "Address bloat, symptom-vs-root-cause, novelty suppression, data support, domain harm, over-constraint."
        )
        beta = self._call_llm(beta_prompt, MODEL_IDS["haiku"], 800)

        rebut_prompt = (
            "You are Meta_Alpha. Rebut each objection with run-data-grounded defense.\n"
            f"Original proposal:\n{alpha}\n\nObjections:\n{beta}"
        )
        rebuttal = self._call_llm(rebut_prompt, MODEL_IDS["haiku"], 900)

        judge_prompt = (
            "You are Meta_Judge. Decide APPROVE, NARROW, or REJECT with reasoning.\n"
            "If NARROW, include exact narrowing instructions.\n"
            f"Proposal:\n{alpha}\n\nObjection:\n{beta}\n\nRebuttal:\n{rebuttal}"
        )
        judge = self._call_llm(judge_prompt, MODEL_IDS["sonnet"], 900)

        parsed = self._parse_alpha(alpha)
        ruling = self._extract_ruling(judge)
        proposed_text = parsed.get("proposed_change", current_excerpt)

        # Validate that the proposed change is actually different
        if proposed_text.strip() == current_excerpt.strip():
            print(f"[OPTIMIZER] WARNING: Proposal {rank} has identical current and proposed text for {target_section}")
            print(f"[OPTIMIZER] Pattern: {pattern.pattern}, attempting to force change...")
            # Try to extract any suggested changes from the alpha response text
            if "add text requiring" in alpha.lower() or "add:" in alpha.lower():
                print(f"[OPTIMIZER] Alpha response suggests changes but didn't modify proposed_change field")
                print(f"[OPTIMIZER] Alpha excerpt: {alpha[:500]}...")

        if len(proposed_text) > int(len(current_excerpt) * 1.1):
            ruling = "NARROWED"
            proposed_text = proposed_text[: int(len(current_excerpt) * 1.1)]

        status_map = {"APPROVE": "APPROVED", "NARROW": "NARROWED", "REJECT": "REJECTED"}
        status = status_map.get(ruling, "NARROWED")

        return {
            "status": status,
            "target_file": "governance/states.py",
            "target_section": target_section,
            "current_excerpt": current_excerpt,
            "current_length": len(current_excerpt),
            "proposed_change": proposed_text,
            "proposed_length": len(proposed_text),
            "rationale": parsed.get("rationale", "Generated from weighted failure analysis."),
            "predicted_effect": parsed.get("predicted_effect", "Improve survival for targeted failure pattern."),
            "risk": parsed.get("risk", "May overfit to recent run characteristics."),
            "trade_off": parsed.get("trade_off", "Higher structure may reduce stylistic variance."),
            "rollback_plan": "Revert to previous prompt text",
            "adversarial_review": {
                "meta_beta_objection": beta,
                "meta_alpha_rebuttal": rebuttal,
                "meta_judge_ruling": judge,
                "ruling": status,
            },
        }

    def _alpha_prompt(self, pattern: FailurePattern, target_section: str, current_excerpt: str) -> str:
        # Pattern-specific guidance
        pattern_guidance = {
            "LOGIC_FAILURE": (
                "Claims have logical gaps or non-sequiturs. Add text requiring:\n"
                "- 'Verify each logical step follows necessarily from the previous one'\n"
                "- 'Identify and reject claims with missing inferential steps'\n"
                "- 'Ensure conclusions are entailed by premises, not merely compatible'"
            ),
            "EVIDENCE_INSUFFICIENT": (
                "Claims lack adequate supporting evidence. Add text requiring:\n"
                "- 'Every empirical claim must cite specific data sources'\n"
                "- 'Reject assertions that lack measurable evidence or replication pathway'\n"
                "- 'Demand quantitative support for all magnitude claims'"
            ),
            "PARAMETER_UNJUSTIFIED": (
                "Numerical parameters lack justification. Add text requiring:\n"
                "- 'All thresholds and constants must have explicit derivations'\n"
                "- 'Explain why each parameter value was chosen over alternatives'\n"
                "- 'Link parameter choices to empirical constraints or theoretical bounds'"
            ),
            "MAGNITUDE_IMPLAUSIBLE": (
                "Claims contain implausible numerical magnitudes. Add text requiring:\n"
                "- 'Sanity-check all quantitative claims against known reference values'\n"
                "- 'Flag magnitude claims that exceed domain-typical ranges by >2x'\n"
                "- 'Require explicit justification for extraordinary magnitude claims'"
            ),
            "SCOPE_EXCEEDED": (
                "Claims overgeneralize beyond supporting evidence. Add text requiring:\n"
                "- 'Explicitly bound the scope of each claim to tested conditions'\n"
                "- 'Challenge generalizations that extend beyond available data'\n"
                "- 'Require domain-specific caveats for cross-domain applications'"
            ),
            "DEPENDENCY_FAILURE": (
                "Claims cite retracted or weak dependencies. Add text requiring:\n"
                "- 'Verify all cited claims have survived adversarial review'\n"
                "- 'Check citation chains for retracted or partial-status dependencies'\n"
                "- 'Reject claims that rest on unvalidated foundations'"
            ),
            "CRITIC_TOO_PASSIVE": (
                "Entire domains show 100% survival while weak-critic flags are active. Add text requiring:\n"
                "- 'Actively seek falsification opportunities for each claim, not just surface checks'\n"
                "- 'Challenge at least one core assumption with a domain-specific counterexample attempt'\n"
                "- 'Escalate uncertain claims to retraction unless evidence clears explicit confidence thresholds'\n"
                "- 'When no weaknesses are found, explain the stress tests attempted and why they failed to falsify'"
            ),
        }

        guidance = pattern_guidance.get(pattern.pattern, "Add validation text to prevent this failure pattern.")

        return (
            "You are Meta_Alpha, a prompt optimization agent. Your task is to MODIFY the current prompt text "
            "to address a specific failure pattern.\n\n"

            f"FAILURE PATTERN: {pattern.pattern}\n"
            f"Severity score: {pattern.score} | Frequency: {pattern.frequency} occurrences\n"
            f"Affected domains: {', '.join(pattern.affected_domains)}\n"
            f"Affected states: {', '.join(pattern.affected_states[:3])}{'...' if len(pattern.affected_states) > 3 else ''}\n\n"

            f"HOW TO FIX {pattern.pattern}:\n{guidance}\n\n"

            f"TARGET SECTION: {target_section}\n\n"

            "INSTRUCTIONS:\n"
            "1. Read the CURRENT_EXCERPT below (the current prompt text)\n"
            "2. Identify where to add/modify text to prevent this failure pattern\n"
            "3. Generate a MODIFIED version of the excerpt with specific validation requirements added\n"
            "4. The proposed_change must be DIFFERENT from the current excerpt - add concrete validation text\n"
            "5. Keep changes focused and minimal - replace weak phrasing or add specific checks\n"
            "6. Do NOT just append text - integrate changes into the existing structure\n"
            "7. Preserve the overall structure and formatting of the prompt\n\n"

            "Return JSON with these exact keys:\n"
            "{\n"
            '  "proposed_change": "THE FULL MODIFIED PROMPT TEXT (must differ from current_excerpt)",\n'
            '  "rationale": "Why this change addresses the failure pattern",\n'
            '  "predicted_effect": "Expected impact on claim survival rates",\n'
            '  "risk": "Potential downsides or unintended consequences",\n'
            '  "trade_off": "What we might lose by adding this validation"\n'
            "}\n\n"

            f"CURRENT_EXCERPT:\n{current_excerpt}\n\n"

            "Now generate the JSON with a MODIFIED proposed_change that addresses the failure pattern:"
        )

    @staticmethod
    def _parse_alpha(alpha_text: str) -> dict[str, Any]:
        start = alpha_text.find("{")
        end = alpha_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(alpha_text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {}

    @staticmethod
    def _extract_ruling(judge_text: str) -> str:
        upper = judge_text.upper()
        if "REJECT" in upper:
            return "REJECT"
        if "NARROW" in upper:
            return "NARROW"
        if "APPROVE" in upper:
            return "APPROVE"
        return "NARROW"

    def _extract_prompt(self, full_text: str, section: str) -> str:
        start_marker, end_marker = PROMPT_MARKERS[section]
        pattern = re.compile(
            rf"{re.escape(start_marker)}(.*?){re.escape(end_marker)}",
            re.DOTALL,
        )
        match = pattern.search(full_text)
        if not match:
            raise ValueError(f"Unable to locate markers for {section}")
        return match.group(1).strip("\n")

    def _pattern_json(self, pattern: FailurePattern, rank: int, archive: dict[str, Any]) -> dict[str, Any]:
        total = max(sum(1 for e in archive.get("archive_entries", []) if e.get("status") in {"destroyed", "retracted"}), 1)
        pct = f"{round((pattern.frequency / total) * 100)}% of retractions"
        return {
            "rank": rank,
            "pattern": pattern.pattern,
            "frequency": pct,
            "score": pattern.score,
            "affected_domains": pattern.affected_domains,
            "affected_states": pattern.affected_states,
        }

    def _is_oscillating(self, proposal: dict[str, Any], history: dict[str, Any]) -> bool:
        events = history.get("events", [])[-6:]
        target = proposal["target_section"]
        for ev in events:
            if ev.get("target_section") == target and ev.get("status") in {"applied", "reverted"}:
                if ev.get("hash_before") == self._hash_text(proposal["proposed_change"]):
                    return True
        return False

    @staticmethod
    def _hash_text(text: str) -> str:
        import hashlib

        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _domain_from_state(state_name: str) -> str:
        if not state_name:
            return ""
        return state_name.split("_")[0]

    def _call_llm(self, prompt: str, model: str, max_tokens: int) -> str:
        try:
            response = self.llm.complete(
                system_prompt="You are an internal Atlantis meta-optimization agent.",
                user_prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=0.3,
                task_type="meta_optimizer",
            )
            content = response.content or ""
            if not content:
                print(f"[OPTIMIZER] WARNING: Empty LLM response for model {model}")
            return content
        except Exception as e:
            print(f"[OPTIMIZER] ERROR: LLM call failed - {type(e).__name__}: {e}")
            print(f"[OPTIMIZER] Model: {model}, Mode: {self.llm.mode}")
            raise

    @staticmethod
    def _prompt_version() -> str:
        history_path = Path("meta/history.json")
        if history_path.exists():
            history = json.loads(history_path.read_text(encoding="utf-8"))
            return str(history.get("current_prompt_version") or history.get("current_version") or "v0.0.0")
        return "v0.0.0"
