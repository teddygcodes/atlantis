"""
Atlantis LLM Integration
=========================
Abstracted LLM layer with:
- Real API calls (Anthropic Claude) when API key is available
- Local simulation mode for testing without API access
- 1-SECOND RATE LIMITING between API calls
- Token counting and cost tracking
- Response caching

All agent thinking goes through this layer.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from config.settings import API_CONFIG
from core.exceptions import LLMTimeoutException, LLMRateLimitException


def _safe_retry_after_seconds(error: Exception) -> float:
    """Best-effort extraction of retry-after seconds from Anthropic exceptions."""
    response = getattr(error, "response", None)
    if response is not None:
        headers = getattr(response, "headers", {}) or {}
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), 0.0)
            except (ValueError, TypeError):
                pass
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        retry_after = body.get("retry_after")
        if retry_after is not None:
            try:
                return max(float(retry_after), 0.0)
            except (ValueError, TypeError):
                pass
    return 0.0


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    latency_ms: float
    cached: bool = False


class LLMProvider:
    """
    Abstracted LLM provider with rate limiting.
    Handles API calls, token counting, rate limiting, caching, and cost tracking.
    """

    @staticmethod
    def _read_dotenv_key() -> str:
        """Read ANTHROPIC_API_KEY directly from .env, searching upward from this file."""
        for search_dir in [Path(__file__).parent.parent, Path.cwd()]:
            env_file = search_dir / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("ANTHROPIC_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        return ""

    def __init__(self, api_key: Optional[str] = None, mode: str = "auto"):
        # .env always wins; fallback to explicit arg then shell env var
        self.api_key = self._read_dotenv_key() or api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.client = None
        self.mode = mode

        if mode == "auto":
            if self.api_key and HAS_ANTHROPIC:
                self.mode = "api"
            else:
                self.mode = "local"

        if self.mode == "api" and HAS_ANTHROPIC and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

        self._error_log_path = Path("output/logs/api_errors.log")

        # Cost tracking (per 1M tokens)
        self.cost_rates = {
            "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
            "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
            "claude-opus-4-6": {"input": 15.00, "output": 75.00},
        }

        # Stats
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0
        self.call_count = 0

        # Response cache
        self._cache: dict[str, LLMResponse] = {}
        self.cache_hits = 0

        # ═══ RATE LIMITING ═══
        # 1-second minimum between API calls
        self._last_call_time = 0.0
        self._rate_limit_seconds = API_CONFIG.get("rate_limit_seconds", 1.0)
        self._rate_limit_enabled = API_CONFIG.get("rate_limit_enabled", True)
        self._rate_limit_waits = 0  # Track how often we had to wait

    def _enforce_rate_limit(self):
        """Enforce 1-second minimum between API calls."""
        if not self._rate_limit_enabled:
            return
        if self.mode != "api":
            return  # No rate limiting for local sim

        now = time.time()
        elapsed = now - self._last_call_time
        if elapsed < self._rate_limit_seconds:
            wait_time = self._rate_limit_seconds - elapsed
            self._rate_limit_waits += 1
            time.sleep(wait_time)

        self._last_call_time = time.time()

    def complete(self, system_prompt: str, user_prompt: str,
                 max_tokens: int = None, temperature: float = None,
                 model: str = None, task_type: str = "unknown") -> LLMResponse:
        """
        Send a completion request to the LLM.
        This is the ONLY way agents communicate with the LLM.
        """
        model = model or API_CONFIG["model"]
        max_tokens = max_tokens or API_CONFIG["max_tokens"]
        temperature = temperature if temperature is not None else API_CONFIG["temperature"]

        # Check cache first (before rate limiting)
        cache_key = self._cache_key(system_prompt, user_prompt, model)
        if cache_key in self._cache:
            self.cache_hits += 1
            cached = self._cache[cache_key]
            return LLMResponse(
                content=cached.content,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                model=model,
                latency_ms=0,
                cached=True
            )

        # ═══ RATE LIMIT ═══
        self._enforce_rate_limit()

        # Route to appropriate backend with retry logic
        start = time.time()

        if self.mode == "dry-run":
            print("\n[DRY RUN] LLM Call")
            print(f"model: {model}")
            print(f"max_tokens: {max_tokens}")
            print("system_prompt:")
            print(system_prompt)
            print("user_prompt:")
            print(user_prompt)
            response = self._simulate_local(system_prompt, user_prompt, max_tokens, model)
        else:
            max_retries = 3
            backoff_schedule = [5.0, 15.0, 45.0]
            attempt = 0
            while True:
                try:
                    if self.mode == "api" and self.client:
                        response = self._call_api(system_prompt, user_prompt, max_tokens, temperature, model)
                    else:
                        response = self._simulate_local(system_prompt, user_prompt, max_tokens, model)
                    break
                except Exception as e:
                    if self._should_retry_transient_error(e) and attempt < max_retries:
                        wait = backoff_schedule[attempt]
                        attempt += 1
                        self._log_error("transient_retry", model, e, wait)
                        print(f"Retry {attempt}/3 for {task_type} after {e}")
                        time.sleep(wait)
                        continue

                    if self._is_timeout_error(e):
                        self._log_error("timeout", model, e, 0.0)
                        raise LLMTimeoutException(f"API timeout after {max_retries} retries")

                    self._log_error("unhandled", model, e, 0.0)
                    # Last resort - return error response
                    response = LLMResponse(
                        content=f"[LLM ERROR: {str(e)}]",
                        input_tokens=0, output_tokens=0, total_tokens=0,
                        model=model, latency_ms=0
                    )
                    break

        response.latency_ms = (time.time() - start) * 1000

        # Track stats
        self.total_input_tokens += response.input_tokens
        self.total_output_tokens += response.output_tokens
        self.call_count += 1
        self._track_cost(response)

        # Cache the response
        self._cache[cache_key] = response

        return response

    def _log_error(self, error_type: str, model: str, error: Exception, retry_in_s: float):
        self._error_log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts": time.time(),
            "type": error_type,
            "model": model,
            "retry_in_s": retry_in_s,
            "error": str(error),
        }
        with self._error_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

    @staticmethod
    def _is_timeout_error(error: Exception) -> bool:
        return error.__class__.__name__ == "APITimeoutError"

    @classmethod
    def _should_retry_transient_error(cls, error: Exception) -> bool:
        status_code = getattr(error, "status_code", None)
        if status_code in {400, 401}:
            return False

        body = getattr(error, "body", None)
        error_type = ""
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                error_type = str(err.get("type", "")).lower()
            else:
                error_type = str(body.get("type", "")).lower()

        message = str(error).lower()
        cls_name = error.__class__.__name__

        if cls_name in {"APITimeoutError", "RateLimitError"}:
            return True
        if status_code in {503, 529}:
            return True
        if "timeout" in message:
            return True
        if "overloaded" in message or "rate limit" in message or "rate_limit" in message:
            return True
        if error_type in {"overloaded_error", "rate_limit_error", "timeout_error"}:
            return True
        return False

    def _call_api(self, system_prompt: str, user_prompt: str,
                  max_tokens: int, temperature: float, model: str) -> LLMResponse:
        """Make a real API call to Anthropic with 30s timeout."""
        message = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=30.0  # 30 second timeout
        )

        return LLMResponse(
            content=message.content[0].text,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            total_tokens=message.usage.input_tokens + message.usage.output_tokens,
            model=model,
            latency_ms=0
        )

    def _simulate_local(self, system_prompt: str, user_prompt: str,
                        max_tokens: int, model: str) -> LLMResponse:
        """Local simulation for testing without API access."""
        agent_name = "Unknown"
        if "You are " in system_prompt:
            agent_name = system_prompt.split("You are ")[1].split(",")[0]

        input_tokens = (len(system_prompt) + len(user_prompt)) // 4
        response_text = self._generate_local_response(agent_name, system_prompt, user_prompt)
        output_tokens = len(response_text) // 4

        return LLMResponse(
            content=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            model=f"{model}-local-sim",
            latency_ms=0
        )

    def _generate_local_response(self, agent_name: str, system_prompt: str, user_prompt: str) -> str:
        """Generate a structured local response for testing."""
        prompt_lower = user_prompt.lower()
        name_lower = agent_name.lower()

        # ─── Structured governance pipeline responses (must run before generic branches) ───
        if "produce a foundation, discovery, or challenge claim" in prompt_lower:
            approach = ""
            for line in user_prompt.splitlines():
                if line.lower().startswith("approach:"):
                    approach = line.split(":", 1)[1].strip()
                    break

            approach_lower = approach.lower()
            if "empiricism" in approach_lower:
                return (
                    "CLAIM TYPE: Discovery\n"
                    f"POSITION: {agent_name} argues governance theories should be accepted only after repeated observational validation.\n"
                    "STEP 1: Compare governance predictions against measurable outcomes such as error correction speed and claim survival rates.\n"
                    "STEP 2: Reject frameworks that fail replication across multiple cycles and independent rival states.\n"
                    "STEP 3: Promote only methods whose improvements remain observable under adversarial stress tests.\n"
                    "CONCLUSION: Governance knowledge is reliable when grounded in replicable evidence rather than untested assumptions.\n"
                    "CITATIONS: []\n"
                    "KEYWORDS: empiricism, observation, replication, measurement"
                )
            if "rationalism" in approach_lower:
                return (
                    "CLAIM TYPE: Discovery\n"
                    f"POSITION: {agent_name} argues governance frameworks should be derived from coherent first principles before empirical deployment.\n"
                    "STEP 1: Start from explicit axioms about consistency, accountability, and non-contradiction in institutional rules.\n"
                    "STEP 2: Deduce policy constraints logically and reject proposals that violate core axioms even if short-term metrics look favorable.\n"
                    "STEP 3: Use observations as secondary checks while preserving the primacy of internally consistent reasoning.\n"
                    "CONCLUSION: Durable governance emerges from logically coherent design validated by reason-guided implementation.\n"
                    "CITATIONS: []\n"
                    "KEYWORDS: rationalism, axioms, coherence, deduction"
                )

            return (
                "CLAIM TYPE: Discovery\n"
                f"POSITION: {agent_name} argues adaptive governance needs explicit feedback loops to stay truthful under adversarial pressure.\n"
                "STEP 1: Systems that publish intermediate reasoning are easier to challenge and therefore self-correct faster.\n"
                "STEP 2: Rebuttal requirements force states to expose hidden assumptions, reducing silent failure modes.\n"
                "STEP 3: Cross-citation between rival claims creates a dependency graph that reveals fragile foundations early.\n"
                "CONCLUSION: Adversarial transparency increases long-run knowledge reliability even when short-run conflict rises.\n"
                "CITATIONS: []\n"
                "KEYWORDS: governance, feedback_loops, adversarial_testing, transparency"
            )

        if "challenge this claim" in prompt_lower and "step targeted" in prompt_lower:
            return (
                "STEP TARGETED: STEP 2\n"
                "FLAW: The claim assumes rebuttal quality is consistently high, but weak rebuttals can create false confidence instead of correction.\n"
                "ALTERNATIVE: Reliability improves only when rebuttals add genuinely new reasoning that can be independently tested.\n"
                "EVIDENCE: Historical policy reviews show iterative debate helps only when counterarguments are specific and evidence-linked."
            )

        if "choose your response:" in prompt_lower and "option a" in prompt_lower:
            return (
                "OPTION B: I concede that low-quality rebuttals can amplify noise, so the original claim was too broad. "
                "Narrowed claim: adversarial transparency improves reliability when rebuttals must introduce testable, non-redundant reasoning "
                "and are archived for later dependency audits."
            )

        if "return json:" in prompt_lower and "\"ruling_type\"" in prompt_lower and "\"outcome\": \"survived|partial|retracted|destroyed\"" in prompt_lower:
            selector = int(hashlib.md5(user_prompt.encode()).hexdigest(), 16) % 4
            if selector == 0:
                outcome = "survived"
                ruling_type = "SURVIVED"
                reasoning = "The challenge raises pressure but fails to overturn the claim's core mechanism under the provided evidence."
                scores = {"drama": 6, "novelty": 5, "depth": 7}
            elif selector == 1:
                outcome = "partial"
                ruling_type = "REVISE"
                reasoning = "The challenge identifies a real boundary condition and the rebuttal concedes it while preserving a narrower core claim."
                scores = {"drama": 7, "novelty": 6, "depth": 8}
            elif selector == 2:
                outcome = "retracted"
                ruling_type = "REJECT_SCOPE"
                reasoning = "The challenge demonstrates the claim is overbroad and the rebuttal does not narrow it enough for the stated domain."
                scores = {"drama": 6, "novelty": 5, "depth": 6}
            else:
                outcome = "destroyed"
                ruling_type = "REJECT_LOGIC"
                reasoning = "The challenge targets a central inference and the rebuttal does not supply a valid replacement chain of reasoning."
                scores = {"drama": 8, "novelty": 6, "depth": 7}
            return json.dumps({
                "outcome": outcome,
                "ruling_type": ruling_type,
                "reasoning": reasoning,
                "open_questions": [
                    "How should rebuttal quality be measured before archival?",
                    "Which audit signals best predict false confidence loops?"
                ],
                "scores": scores
            })


        if "extract and return json" in prompt_lower and "\"claim_type\"" in prompt_lower:
            return json.dumps({
                "claim_type": "discovery",
                "position": "Adaptive governance needs explicit feedback loops to stay truthful under adversarial pressure.",
                "reasoning_chain": [
                    "Systems that publish intermediate reasoning are easier to challenge.",
                    "Structured rebuttals surface hidden assumptions before they calcify.",
                    "Citation graphs expose fragile dependencies for earlier correction."
                ],
                "conclusion": "Adversarial transparency increases reliability when criticism is specific and testable.",
                "citations": [],
                "keywords": ["governance", "feedback_loops", "adversarial_testing", "transparency"]
            })

        if "extract explicit and implicit premises" in prompt_lower and "\"explicit_premises\"" in prompt_lower:
            return json.dumps({
                "explicit_premises": [
                    "Publishing reasoning enables targeted critique.",
                    "Rebuttals can reveal hidden assumptions."
                ],
                "implicit_assumptions": [
                    "Critics act in good faith often enough to improve outcomes.",
                    "Archival systems preserve enough context for later audits."
                ]
            })

        if "does rebuttal introduce genuinely new reasoning" in prompt_lower:
            return json.dumps({
                "new_reasoning": True,
                "explanation": "The rebuttal narrows scope and adds a verifiable condition on rebuttal quality."
            })

        # ─── Constitutional Amendment proposals (check BEFORE research!) ───
        if "constitutional amendment" in prompt_lower and "round" in prompt_lower:
            amendments = [
                ("Add a Research Ethics branch with 2 seats to review knowledge quality", "Quality control prevents hallucination"),
                ("Increase Senate supermajority threshold to 75% for State formations", "Higher bar ensures only well-justified States form"),
                ("Add mandatory peer review requirement for Tier 4+ knowledge", "Novel insights need validation before archival"),
                ("Require Court approval for any branch composition changes", "Prevents self-serving power grabs"),
                ("Add resource efficiency metrics to all governance reports", "Transparency on token usage and costs"),
                ("Create inter-State collaboration incentives for cross-domain research", "Breaks down knowledge silos"),
                ("Add automatic pruning of stagnant States after 20 cycles", "Removes dead weight from the system"),
                ("Require all Bills to include implementation cost estimates", "Forces realistic resource planning"),
            ]
            import random
            amendment, rationale = random.choice(amendments)
            return f"AMENDMENT: {amendment}\nRATIONALE: {rationale}"

        # ─── Jefferson's Constitutional Draft (check BEFORE research!) ───
        if "write the constitution" in prompt_lower and "jefferson" in name_lower:
            return """## BRANCHES
Define the branches of government:

BRANCH: Federal Senate | legislative | 4 | Critic,Tester,Historian,Debugger | Deliberates Bills and sets Federal agendas
BRANCH: Implementation House | implementation | 2 | Architect,Coder | Reviews Bills for feasibility and implements passed legislation
BRANCH: Supreme Court | judicial | 3 | Warden,Elder,Oracle | Adjudicates disputes and reviews constitutionality

## POWERS
The Federal Senate proposes Bills by simple majority (3/4 votes). The Implementation House reviews for feasibility and may veto with unanimous vote (2/2). The Supreme Court reviews constitutionality and may strike down unconstitutional actions.

Amendment proposals require 2/3 Senate supermajority, House sign-off, and Court constitutional review. Amendments have a 25-cycle cooldown.

## KNOWLEDGE ENGINE
Knowledge tiers define depth:
- Tier 1: Basic vocabulary and surface concepts
- Tier 2: Frameworks and relationships between concepts
- Tier 3: Applications and cross-domain synthesis
- Tier 4: Novel insights and original frameworks
- Tier 5: Breakthrough discoveries and paradigm shifts

States form to research broad domains. When State knowledge branches (Tier 3+), Cities form to specialize in sub-domains. When City knowledge goes hyper-deep (Tier 4+), Towns form for extreme specialization.

Research cycle: Governor sets agenda → Researcher produces findings → Critic challenges → Researcher defends → Knowledge entry created and tiered.

## SAFEGUARDS
Non-amendable clauses that protect system integrity:
1. All governance actions must be logged and auditable - no secret decisions
2. Knowledge claims must include evidence and methodology - no unsupported assertions
3. Growth rate limits prevent exponential resource exhaustion - maximum 5 new entities per 10 cycles
4. Mandatory failure recovery protocols - if any branch fails, system enters recovery mode
5. Constitutional review required for all structural changes - no unchecked power

## CYCLE SEQUENCE
Each governance cycle follows these steps in order:
1. agenda - Federal Senate sets priorities
2. research - States/Cities/Towns conduct research
3. legislate - Senate debates and votes on Bills
4. implement - House reviews and implements passed Bills
5. judge - Court reviews for constitutional compliance
6. amend - Senate may propose Constitutional amendments
7. health_check - Monitor system health and detect failures
8. archive - Deposit key findings to Federal Archive
9. publish - Generate reports and publish content"""

        # ─── Research responses ───
        if "research" in prompt_lower:
            topic = user_prompt.split("Research ")[-1].split(".")[0] if "Research " in user_prompt else "the topic"
            return (
                f"After thorough analysis of {topic}, I've identified several key findings.\n\n"
                f"CONCEPTS: structured governance, resource allocation theory, institutional "
                f"design patterns, complex adaptive systems, feedback mechanisms, equilibrium states, "
                f"bounded rationality, principal-agent dynamics, information asymmetry, "
                f"mechanism design, incentive compatibility, coordination failures\n\n"
                f"FRAMEWORKS: hierarchical governance models, distributed consensus mechanisms, "
                f"constitutional constraint theory, institutional economics framework\n\n"
                f"APPLICATIONS: democratic institutions, corporate governance, distributed "
                f"computing systems, international treaty organizations\n\n"
                f"CONNECTIONS: game_theory, systems_theory, organizational_design, "
                f"evolutionary_theory, complexity_science"
            )

        # ─── 2v2 Debate: Support responses ───
        if "support" in prompt_lower or "argue for" in prompt_lower or "argue in favor" in prompt_lower:
            return (
                f"As {agent_name}, I strongly support this article. The proposed framework "
                f"addresses a critical gap in our constitutional design. The specific provisions "
                f"are well-crafted — they include measurable standards, clear enforcement "
                f"mechanisms, and appropriate flexibility for evolution. This article strengthens "
                f"the overall constitutional architecture and I urge all Founders to vote in "
                f"favor of ratification."
            )

        # ─── 2v2 Debate: Opposition responses ───
        if "oppose" in prompt_lower or "argue against" in prompt_lower or "challenge" in prompt_lower:
            return (
                f"As {agent_name}, I have serious reservations about this article. While the "
                f"intent is sound, the implementation risks creating unintended consequences. "
                f"The enforcement mechanisms are either too rigid — preventing necessary "
                f"adaptation — or too vague to be meaningful. I propose the Convention reject "
                f"this article and commission a revised version that addresses these structural "
                f"weaknesses before we enshrine it in the Constitution."
            )

        # ─── Proposal responses (by Founder personality) ───
        if "propose" in prompt_lower or "article" in prompt_lower or "draft" in prompt_lower:
            proposals = {
                "hamilton": "I propose that efficiency must be a constitutional mandate. Every State must operate within defined resource budgets with quarterly audits.",
                "jefferson": "I propose that State sovereignty is an inviolable right. The Federal government shall not dictate internal State knowledge methodologies.",
                "franklin": "I propose a five-tier depth standard with measurable requirements at each level. No knowledge shall be archived without meeting minimum evidence thresholds.",
                "madison": "I propose three branches with explicit checks: Senate legislates, House implements, Court adjudicates. No branch may act without possibility of review.",
                "marshall": "I propose judicial review with binding authority. The Supreme Court shall strike down any action violating the Constitution and may compel amendments.",
                "washington": "I propose non-amendable safety clauses: growth rate limits, resource caps, and mandatory failure recovery protocols that no future amendment may weaken.",
                "paine": "I propose mandatory transparency: every debate, vote, and ruling logged and published. The content pipeline is governance infrastructure, not optional.",
                "tyler": "I propose inter-branch integration protocols: standardized data formats, defined handoff procedures, and mandatory coordination checkpoints.",
                "darwin": "I propose evolutionary governance: successful State approaches propagate, failed ones are pruned. The system must adapt or die.",
                "curie": "I propose experimental validation requirements: every knowledge claim must include methodology, evidence, and replication pathway.",
                "turing": "I propose computational integrity standards: all governance processes must be formally specifiable with guaranteed termination conditions.",
                "aristotle": "I propose ethical governance foundations: decisions must consider not just efficiency but justice, wisdom, and the common good.",
                "hippocrates": "I propose system health monitoring: continuous vital signs tracking with automated alerts for stagnation, decay, and resource depletion.",
                "da vinci": "I propose creative synthesis incentives: cross-domain collaboration shall be constitutionally rewarded, not just deep specialization.",
                "brunel": "I propose infrastructure standards: every State must implement defined data schemas, API interfaces, and reliability requirements.",
                "olympia": "I propose performance measurement frameworks: every entity must report quantifiable metrics on knowledge growth and governance efficiency.",
                "smith": "I propose resource sustainability mandates: token budgets, growth rate limits, and long-term resource planning requirements.",
                "herodotus": "I propose institutional memory requirements: no history may be deleted, all decisions must reference relevant precedent.",
                "euclid": "I propose formal consistency requirements: the Constitution must be logically non-contradictory, with automated consistency checking.",
                "carson": "I propose ecosystem diversity protections: knowledge monocultures are prohibited, minimum diversity thresholds required across all States.",
            }
            return proposals.get(name_lower, f"I, {agent_name}, propose a constitutional article addressing the critical needs of my domain.")

        # ─── Vote responses ───
        if "vote" in prompt_lower:
            # Return YES ~60% of the time, NO ~40% (so some amendments pass 70% threshold)
            import random
            if random.random() < 0.60:
                return "YES"
            else:
                return "NO"

        # ─── Default ───
        return (
            f"As {agent_name}, I've analyzed the matter carefully. The core considerations "
            f"involve balancing competing priorities. My recommendation accounts for these "
            f"tensions and proposes a framework that addresses the most critical concerns first."
        )

    def _cache_key(self, system: str, user: str, model: str) -> str:
        combined = f"{model}:{system[:200]}:{user}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _track_cost(self, response: LLMResponse):
        rates = self.cost_rates.get(response.model.replace("-local-sim", ""))
        if rates:
            input_cost = (response.input_tokens / 1_000_000) * rates["input"]
            output_cost = (response.output_tokens / 1_000_000) * rates["output"]
            self.total_cost_usd += input_cost + output_cost

    def get_stats(self) -> dict:
        return {
            "mode": self.mode,
            "total_calls": self.call_count,
            "cache_hits": self.cache_hits,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": round(self.total_cost_usd, 4),
            "cache_hit_rate": round(self.cache_hits / max(self.call_count + self.cache_hits, 1), 2),
            "rate_limit_waits": self._rate_limit_waits,
        }


# Global provider instance
_provider: Optional[LLMProvider] = None

def get_llm(api_key: Optional[str] = None, mode: str = "auto", force_new: bool = False) -> LLMProvider:
    global _provider
    if _provider is None or force_new:
        _provider = LLMProvider(api_key=api_key, mode=mode)
    return _provider

def reset_llm():
    global _provider
    _provider = None
