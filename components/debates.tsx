"use client";

import { useState, useEffect, useRef } from "react";
import { CLAIMS, type Claim } from "@/lib/data";

function useScrollReveal() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
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
  }, []);
  return ref;
}

const CYCLE_FILTERS = [1, 2, 3] as const;

export function Debates() {
  const containerRef = useScrollReveal();
  const [activeCycle, setActiveCycle] = useState<number>(1);

  const filteredClaims = CLAIMS.filter((c) => c.cycle === activeCycle);

  return (
    <section ref={containerRef}>
      {/* Page header - centered */}
      <div className="scroll-reveal mx-auto mb-12 text-center" style={{ paddingTop: "64px" }}>
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
            fontSize: "16px",
            color: "#a3a3a3",
          }}
        >
          Every claim. Every challenge. Every verdict. Watch the adversarial
          process unfold.
        </p>
      </div>

      {/* 48px gap below subtitle */}
      <div style={{ height: "48px" }} />

      {/* Cycle selector */}
      <div className="scroll-reveal mx-auto mb-16 flex max-w-[900px] items-center justify-center gap-1">
        {CYCLE_FILTERS.map((cycle) => (
          <button
            key={cycle}
            onClick={() => setActiveCycle(cycle)}
            className={`rounded-sm px-4 py-2 text-[10px] uppercase tracking-[0.2em] transition-all ${
              activeCycle === cycle
                ? "bg-accent/10 text-accent"
                : "text-muted/50 hover:text-muted"
            }`}
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            Cycle {cycle}
          </button>
        ))}
      </div>

      {/* Debate cards */}
      <div className="mx-auto flex max-w-[900px] flex-col gap-16">
        {filteredClaims.map((claim) => (
          <MatchCard key={claim.id} claim={claim} />
        ))}
      </div>
    </section>
  );
}

function MatchCard({ claim }: { claim: Claim }) {
  const [step, setStep] = useState(0);
  const isAlive = claim.ruling !== "DESTROYED";

  const advanceStep = () => {
    if (step < 3) setStep(step + 1);
    else setStep(0);
  };

  return (
    <article className="scroll-reveal">
      {/* Match header */}
      <div className="mb-6 flex flex-wrap items-center justify-center gap-4">
        <span
          className="text-xs font-bold text-accent"
          style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
        >
          {claim.id}
        </span>
        <span
          className="text-[10px] text-muted/40"
          style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
        >
          {claim.domain}
        </span>
        <span
          className="text-[10px] text-muted/40"
          style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
        >
          {claim.state.replace("_", " ")}
        </span>
        <span
          className={`rounded-sm px-2 py-0.5 text-[9px] uppercase tracking-wider ${
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
        className="cursor-pointer rounded-lg border border-border/60 bg-surface/30 p-6 transition-colors hover:border-border md:p-8"
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
        {/* Step 0: The claim */}
        <div
          className="transition-all duration-500"
          style={{ opacity: step >= 0 ? 1 : 0 }}
        >
          <div className="mb-6 text-center">
            <span
              className="mb-3 block text-[9px] uppercase tracking-[0.25em] text-muted/40"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              The Claim
            </span>
            <p
              className="mx-auto max-w-2xl text-xl leading-[1.8] text-foreground"
              style={{ fontFamily: "var(--font-cormorant)" }}
            >
              {claim.position}
            </p>
          </div>
        </div>

        {/* Step 1+: Challenge */}
        {step >= 1 && (
          <div className="mt-6 flex justify-center debate-animate-in">
            <div className="max-w-[80%] rounded-lg border border-border/40 bg-background px-5 py-4 text-center">
              <span
                className="mb-2 block text-[9px] uppercase tracking-[0.2em] text-red-400"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                Challenge
              </span>
              <p
                className="text-base leading-[1.8] text-muted"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.challenge}
              </p>
            </div>
          </div>
        )}

        {/* Step 2+: Rebuttal */}
        {step >= 2 && (
          <div className="mt-4 flex justify-center debate-animate-in">
            <div className="max-w-[80%] rounded-lg border border-border/40 bg-background px-5 py-4 text-center">
              <span
                className="mb-2 block text-[9px] uppercase tracking-[0.2em] text-emerald-500"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                Rebuttal
              </span>
              <p
                className="text-base leading-[1.8] text-muted"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.rebuttal}
              </p>
            </div>
          </div>
        )}

        {/* Step 3: Verdict drops center */}
        {step >= 3 && (
          <div className="mt-8 flex justify-center debate-animate-in">
            <div
              className="max-w-lg rounded border px-6 py-5 text-center"
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
                className="mb-2 block text-[9px] uppercase tracking-[0.25em]"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: isAlive ? "#dc2626" : "#525252",
                }}
              >
                Verdict
              </span>
              <p
                className="text-lg leading-[1.8] text-foreground/90"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.verdict}
              </p>
            </div>
          </div>
        )}

        {/* Click hint */}
        {step < 3 && (
          <div className="mt-6 text-center">
            <span
              className="text-[9px] uppercase tracking-[0.2em] text-muted/30"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              Click to {step === 0 ? "challenge" : step === 1 ? "rebut" : "judge"}
            </span>
          </div>
        )}
        {step >= 3 && (
          <div className="mt-6 text-center">
            <span
              className="text-[9px] uppercase tracking-[0.2em] text-muted/30"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              Click to reset
            </span>
          </div>
        )}
      </div>

      {/* Score bar */}
      <div className="mt-4 flex items-center justify-center gap-4">
        <div className="flex items-center gap-3">
          {[
            { label: "Drama", value: claim.drama },
            { label: "Novelty", value: claim.novelty },
            { label: "Depth", value: claim.depth },
          ].map((metric) => (
            <div key={metric.label} className="flex items-center gap-1.5">
              <span
                className="text-[9px] uppercase tracking-wider text-muted/30"
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
