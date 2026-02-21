"use client";

import { useState, useEffect, useRef } from "react";
import { HYPOTHESES, type Hypothesis } from "@/lib/data";
import { ExplainSimply } from "@/components/explain-simply";

const CYCLE_FILTERS = [1, 2, 3] as const;

export function Debates() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeCycle, setActiveCycle] = useState<number>(1);

  // Re-observe .scroll-reveal elements whenever the cycle changes
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("is-visible");
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -60px 0px" }
    );
    el.querySelectorAll(".scroll-reveal").forEach((child) =>
      observer.observe(child)
    );
    return () => observer.disconnect();
  }, [activeCycle]);

  const filteredHypotheses = HYPOTHESES.filter((c) => c.cycle === activeCycle);
  return (
    <section ref={containerRef} className="text-center">
      {/* Page header - centered */}
      <div className="scroll-reveal mx-auto mb-6 text-center" style={{ paddingTop: "24px" }}>
        <h2
          className="mb-4"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "36px",
            color: "#e5e5e5",
            letterSpacing: "0.25em",
          }}
        >
          THE DEBATES
        </h2>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "18px",
            fontWeight: 600,
            color: "#d4d4d4",
          }}
        >
          Every hypothesis. Every challenge. Every verdict. Watch the adversarial
          review process unfold.
        </p>
      </div>

      {/* Cycle selector - lifted up closer to header */}
      <div className="scroll-reveal mx-auto mb-10 mt-2 flex max-w-[900px] items-center justify-center gap-3">
        {CYCLE_FILTERS.map((cycle) => (
          <button
            key={cycle}
            onClick={() => setActiveCycle(cycle)}
            className={`rounded-md px-6 py-3 text-sm uppercase tracking-[0.2em] transition-all ${
              activeCycle === cycle
                ? "bg-accent/10 text-accent"
                : "text-foreground/50 hover:text-foreground"
            }`}
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            Cycle {cycle}
          </button>
        ))}
      </div>

      {/* Debate cards */}
      <div className="mx-auto flex max-w-[900px] flex-col gap-16">
        {filteredHypotheses.map((hypothesis) => (
          <MatchCard key={hypothesis.id} claim={hypothesis} />
        ))}
      </div>
    </section>
  );
}

function MatchCard({ claim }: { claim: Hypothesis }) {
  const [step, setStep] = useState(0);
  const isAlive = claim.ruling !== "DESTROYED";

  const advanceStep = () => {
    if (step < 3) setStep(step + 1);
    else setStep(0);
  };

  return (
    <article className="scroll-reveal">
      {/* Match header */}
      <div className="mb-8 flex flex-wrap items-center justify-center gap-5">
        <span
          className="text-sm font-bold text-accent"
          style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
        >
          {claim.id}
        </span>
        <span
          className="text-xs text-foreground/70"
          style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
        >
          {claim.domain}
        </span>
        <span
          className="text-xs text-foreground/70"
          style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
        >
          {claim.state.replace("_", " ")}
        </span>
        <span
          className={`rounded-sm px-3 py-1 text-[11px] uppercase tracking-wider ${
            claim.ruling === "DESTROYED"
              ? "bg-destroyed/20 text-destroyed"
              : claim.ruling === "REVISE"
                ? "bg-accent/10 text-accent"
                : "bg-amber-500/10 text-amber-500"
          }`}
          style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
        >
          {claim.ruling}
        </span>
      </div>

      {/* The match arena */}
      <div
        className="cursor-pointer rounded-lg border border-border/60 bg-surface/30 p-8 transition-colors hover:border-border md:p-12"
        onClick={advanceStep}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            advanceStep();
          }
        }}
        aria-label="Advance debate step"
      >
        {/* Step 0: The hypothesis */}
        <div
          className="transition-all duration-500"
          style={{ opacity: step >= 0 ? 1 : 0 }}
        >
          <div className="mb-8 text-center">
            <span
              className="mb-4 block text-xs uppercase tracking-[0.25em] text-foreground/60"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              The Hypothesis
            </span>
            <p
              className="text-2xl font-bold leading-[1.8] text-foreground"
              style={{ fontFamily: "var(--font-cormorant)" }}
            >
              {claim.hypothesis || claim.position}
            </p>
            <ExplainSimply text={claim.hypothesis || claim.position} type="hypothesis" />
          </div>
        </div>

        {/* Step 1+: Challenge */}
        {step >= 1 && (
          <div className="mt-8 debate-animate-in">
            <div className="rounded-lg border border-border/40 bg-background px-8 py-6 text-center">
              <span
                className="mb-3 block text-xs uppercase tracking-[0.2em] text-red-400"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                Peer Review
              </span>
              <p
                className="text-xl font-semibold leading-[1.8] text-foreground/90"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.challenge}
              </p>
              <ExplainSimply text={claim.challenge} type="peer review" />
            </div>
          </div>
        )}

        {/* Step 2+: Rebuttal */}
        {step >= 2 && (
          <div className="mt-6 debate-animate-in">
            <div className="rounded-lg border border-border/40 bg-background px-8 py-6 text-center">
              <span
                className="mb-3 block text-xs uppercase tracking-[0.2em] text-emerald-500"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                Defense
              </span>
              <p
                className="text-xl font-semibold leading-[1.8] text-foreground/90"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.rebuttal}
              </p>
              <ExplainSimply text={claim.rebuttal} type="defense" />
            </div>
          </div>
        )}

        {/* Step 3: Verdict drops center */}
        {step >= 3 && (
          <div className="mt-10 flex justify-center debate-animate-in">
            <div
              className="max-w-lg rounded border px-8 py-6 text-center"
              style={{
                borderColor: isAlive
                  ? "rgba(220, 38, 38, 0.2)"
                  : "rgba(82, 82, 82, 0.3)",
                backgroundColor: isAlive
                  ? "rgba(220, 38, 38, 0.05)"
                  : "rgba(82, 82, 82, 0.05)",
              }}
            >
              <span
                className="mb-3 block text-xs uppercase tracking-[0.25em]"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: isAlive ? "#dc2626" : "#525252",
                }}
              >
                Ruling
              </span>
              <p
                className="text-xl font-semibold leading-[1.8] text-foreground/90"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.verdict}
              </p>
              <ExplainSimply text={claim.verdict} type="ruling" />
            </div>
          </div>
        )}

        {/* Click hint */}
        {step < 3 && (
          <div className="mt-8 text-center">
            <span
              className="text-xs uppercase tracking-[0.2em] text-foreground/50"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              Click to {step === 0 ? "review" : step === 1 ? "defend" : "judge"}
            </span>
          </div>
        )}
        {step >= 3 && (
          <div className="mt-8 text-center">
            <span
              className="text-xs uppercase tracking-[0.2em] text-foreground/50"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              Click to reset
            </span>
          </div>
        )}
      </div>

      {/* Score bar */}
      <div className="mt-6 flex items-center justify-center gap-6">
        <div className="flex items-center gap-5">
          {[
            { label: "Drama", value: claim.drama },
            { label: "Novelty", value: claim.novelty },
            { label: "Depth", value: claim.depth },
          ].map((metric) => (
            <div key={metric.label} className="flex items-center gap-1.5">
              <span
                className="text-[11px] uppercase tracking-wider text-foreground/60"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                {metric.label}
              </span>
              <div className="flex gap-px">
                {Array.from({ length: 10 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-1 w-1.5 rounded-sm"
                    style={{
                      backgroundColor:
                        i < metric.value
                          ? "rgba(220, 38, 38, 0.6)"
                          : "rgba(255, 255, 255, 0.05)",
                    }}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}
