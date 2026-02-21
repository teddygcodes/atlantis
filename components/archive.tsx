"use client";

import { useState, useEffect, useRef } from "react";
import { HYPOTHESES, type Hypothesis } from "@/lib/data";
import { ExplainSimply } from "@/components/explain-button";

function useScrollReveal(deps: unknown[] = []) {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return ref;
}

const DOMAIN_FILTERS = [
  "All",
  "Consciousness",
  "Causation",
  "Mathematics",
] as const;
type DomainFilter = (typeof DOMAIN_FILTERS)[number];

export function Archive() {
  const [filter, setFilter] = useState<DomainFilter>("All");
  const containerRef = useScrollReveal([filter]);

  const validatedHypotheses = HYPOTHESES.filter(
    (c) => c.ruling === "SURVIVED" || c.ruling === "REVISE" || c.ruling === "PARTIAL"
  );
  const filteredHypotheses =
    filter === "All"
      ? validatedHypotheses
      : validatedHypotheses.filter((c) => c.domain === filter);

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
          KNOWLEDGE BASE
        </h2>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "18px",
            color: "#d4d4d4",
            fontWeight: 600,
          }}
        >
          The validated hypotheses. Each one has withstood adversarial challenge and
          earned its place in the knowledge base.
        </p>
      </div>

      {/* 48px gap below subtitle */}
      <div style={{ height: "48px" }} />

      {/* Domain filter */}
      <div className="scroll-reveal mx-auto mb-12 flex max-w-[900px] items-center justify-center gap-1">
        {DOMAIN_FILTERS.map((d) => (
          <button
            key={d}
            onClick={() => setFilter(d)}
            className={`rounded-sm px-4 py-2 text-[10px] uppercase tracking-[0.2em] transition-all ${
              filter === d
                ? "bg-accent/10 text-accent"
                : "text-muted/50 hover:text-muted"
            }`}
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            {d}
          </button>
        ))}
      </div>

      {/* Vault entries */}
      <div className="mx-auto flex max-w-[900px] flex-col items-center gap-4">
        {filteredHypotheses.map((hypothesis) => (
          <VaultEntry key={hypothesis.id} hypothesis={hypothesis} />
        ))}
      </div>

      {filteredHypotheses.length === 0 && (
        <p
          className="mx-auto max-w-[900px] py-20 text-center text-lg text-muted/40"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          No validated hypotheses in this domain.
        </p>
      )}
    </section>
  );
}

function VaultEntry({ hypothesis }: { hypothesis: Hypothesis }) {
  const [unlocked, setUnlocked] = useState(false);
  const claim = hypothesis;
  const isSurviving = claim.ruling === "REVISE" || claim.ruling === "PARTIAL";

  return (
    <article
      className="group overflow-hidden rounded border border-border/60 transition-all duration-500 hover:border-border"
      style={{
        boxShadow: isSurviving
          ? "0 0 0 0 rgba(220, 38, 38, 0)"
          : undefined,
      }}
    >
      <button
        onClick={() => setUnlocked(!unlocked)}
        className="flex w-full items-center gap-6 px-6 py-6 text-left transition-colors hover:bg-surface/50"
      >
        {/* Lock icon */}
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded border border-border/60">
          {unlocked ? (
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              className="text-accent"
            >
              <rect x="2" y="7" width="12" height="8" rx="1" stroke="currentColor" strokeWidth="1" />
              <path d="M5 7V5a3 3 0 016 0" stroke="currentColor" strokeWidth="1" />
            </svg>
          ) : (
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              className="text-muted/40"
            >
              <rect x="2" y="7" width="12" height="8" rx="1" stroke="currentColor" strokeWidth="1" />
              <path d="M5 7V5a3 3 0 016 0v2" stroke="currentColor" strokeWidth="1" />
            </svg>
          )}
        </div>

        <div className="flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-3">
            <span
              className="text-xs font-bold text-accent"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {claim.id}
            </span>
            <span
              className={`rounded-sm px-2 py-0.5 text-[9px] uppercase tracking-wider ${
                claim.ruling === "REVISE"
                  ? "bg-accent/10 text-accent"
                  : "bg-amber-500/10 text-amber-500"
              }`}
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {claim.ruling}
            </span>
            <span
              className="text-[10px] text-muted/40"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {claim.domain} / Cycle {claim.cycle}
            </span>
          </div>
          <p
            className="text-lg font-semibold leading-relaxed text-foreground/90"
            style={{ fontFamily: "var(--font-cormorant)" }}
          >
            {claim.hypothesis || claim.position}
          </p>
        </div>

        {/* Arrow */}
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          className={`flex-shrink-0 text-muted/30 transition-transform duration-300 ${unlocked ? "rotate-90" : ""}`}
        >
          <path d="M6 4L10 8L6 12" stroke="currentColor" strokeWidth="1" />
        </svg>
      </button>

      <div className="px-6 pb-2">
        <ExplainSimply text={claim.hypothesis || claim.position} type="hypothesis" />
      </div>

      {/* Expanded debate content */}
      <div
        className="grid transition-all duration-500 ease-out"
        style={{
          gridTemplateRows: unlocked ? "1fr" : "0fr",
          opacity: unlocked ? 1 : 0,
        }}
      >
        <div className="overflow-hidden">
          <div className="flex flex-col gap-4 border-t border-border/40 px-6 py-8">
            <DebateStep label="Peer Review" text={claim.challenge} side="left" />
            <DebateStep label="Defense" text={claim.rebuttal} side="right" />
            <div className="mx-auto mt-4 max-w-lg rounded border border-accent/10 bg-accent/5 px-6 py-5 text-center">
              <span
                className="mb-2 block text-[9px] uppercase tracking-[0.25em] text-accent"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                Ruling
              </span>
              <p
                className="text-lg font-semibold leading-relaxed text-foreground/90"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.verdict}
              </p>
              <ExplainSimply text={claim.verdict} type="ruling" />
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

function DebateStep({
  label,
  text,
  side,
}: {
  label: string;
  text: string;
  side: "left" | "right";
}) {
  return (
    <div className={`flex ${side === "right" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg bg-surface px-5 py-4 ${
          side === "right" ? "rounded-br-none" : "rounded-bl-none"
        }`}
      >
        <span
          className="mb-2 block text-[9px] uppercase tracking-[0.2em] text-muted/50"
          style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
        >
          {label}
        </span>
        <p
          className="text-base font-semibold leading-[1.8] text-foreground/80"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          {text}
        </p>
      </div>
    </div>
  );
}
