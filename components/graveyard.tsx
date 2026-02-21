"use client";

import { useEffect, useRef, useState } from "react";
import { CLAIMS, type Claim } from "@/lib/data";

export function Graveyard() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -60px 0px" }
    );
    el.querySelectorAll(".scroll-reveal, .tombstone").forEach((child) =>
      observer.observe(child)
    );
    return () => observer.disconnect();
  }, []);

  const destroyedClaims = CLAIMS.filter((c) => c.ruling === "DESTROYED");

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
          THE GRAVEYARD
        </h2>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "16px",
            color: "#e5e5e5",
          }}
        >
          The fallen. Every destroyed claim is preserved here as a monument to
          what the system will not accept.
        </p>
      </div>

      <div style={{ height: "48px" }} />

      {/* Tombstones */}
      <div className="mx-auto flex max-w-[900px] flex-col gap-12">
        {destroyedClaims.map((claim) => (
          <Tombstone
            key={claim.id}
            claim={claim}
            isExpanded={expandedId === claim.id}
            onToggle={() =>
              setExpandedId(expandedId === claim.id ? null : claim.id)
            }
          />
        ))}
      </div>

      {/* End marker */}
      <div className="mt-20 flex justify-center">
        <div className="h-px w-12 bg-destroyed/20" />
      </div>
    </section>
  );
}

function Tombstone({
  claim,
  isExpanded,
  onToggle,
}: {
  claim: Claim;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <article
      className="tombstone flex flex-col items-center text-center opacity-0 transition-all duration-700"
    >
      {/* Clickable tombstone */}
      <button
        onClick={onToggle}
        className="w-full max-w-md cursor-pointer rounded-t-[80px] border border-border/30 bg-surface/20 px-8 py-10 pb-8 transition-all duration-300 hover:border-destroyed/40 hover:bg-surface/30 focus:outline-none"
      >
        {/* Cross / marker */}
        <div className="mb-6 flex justify-center">
          <svg
            width="20"
            height="28"
            viewBox="0 0 20 28"
            fill="none"
            className="text-destroyed/40"
          >
            <path d="M10 0v28M4 8h12" stroke="currentColor" strokeWidth="1" />
          </svg>
        </div>

        {/* Claim ID */}
        <span
          className="mb-4 block text-sm tracking-[0.2em] text-accent"
          style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
        >
          {claim.id}
        </span>

        {/* Epitaph */}
        <p
          className="mb-6 text-lg italic leading-relaxed text-foreground/80"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          &ldquo;{getEpitaph(claim.verdict)}&rdquo;
        </p>

        {/* Meta */}
        <div className="flex items-center justify-center gap-3">
          <span
            className="text-[9px] uppercase tracking-[0.2em] text-foreground/50"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            {claim.state.replace("_", " ")}
          </span>
          <span className="text-foreground/30">|</span>
          <span
            className="text-[9px] uppercase tracking-[0.2em] text-foreground/50"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            Cycle {claim.cycle}
          </span>
        </div>

        {/* Expand hint */}
        <div className="mt-4">
          <span
            className="text-[10px] uppercase tracking-[0.15em] text-foreground/30"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            {isExpanded ? "Click to close" : "Click to exhume"}
          </span>
        </div>
      </button>

      {/* Base */}
      <div className="h-3 w-full max-w-md border-x border-b border-border/20 bg-surface/10" />
      <div className="h-2 w-[calc(100%-16px)] max-w-[calc(28rem-16px)] border-x border-b border-border/10 bg-surface/5" />

      {/* Expanded details */}
      <div
        className="overflow-hidden transition-all duration-500 ease-in-out"
        style={{
          maxHeight: isExpanded ? "800px" : "0px",
          opacity: isExpanded ? 1 : 0,
        }}
      >
        <div className="mx-auto mt-6 w-full max-w-lg space-y-6 rounded-lg border border-border/20 bg-surface/10 px-8 py-8 text-center">
          {/* The original position */}
          <div>
            <span
              className="mb-2 block text-xs uppercase tracking-[0.2em] text-foreground/40"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              The Claim
            </span>
            <p
              className="text-lg leading-[1.8] text-foreground/90"
              style={{ fontFamily: "var(--font-cormorant)" }}
            >
              {claim.position}
            </p>
          </div>

          <div className="mx-auto h-px w-16 bg-border/20" />

          {/* The challenge that brought it down */}
          <div>
            <span
              className="mb-2 block text-xs uppercase tracking-[0.2em] text-red-400/70"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              Challenge
            </span>
            <p
              className="text-base leading-[1.8] text-foreground/80"
              style={{ fontFamily: "var(--font-cormorant)" }}
            >
              {claim.challenge}
            </p>
          </div>

          <div className="mx-auto h-px w-16 bg-border/20" />

          {/* The failed rebuttal */}
          <div>
            <span
              className="mb-2 block text-xs uppercase tracking-[0.2em] text-emerald-500/50"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              Rebuttal
            </span>
            <p
              className="text-base leading-[1.8] text-foreground/80"
              style={{ fontFamily: "var(--font-cormorant)" }}
            >
              {claim.rebuttal}
            </p>
          </div>

          <div className="mx-auto h-px w-16 bg-border/20" />

          {/* The verdict */}
          <div>
            <span
              className="mb-2 block text-xs uppercase tracking-[0.2em] text-destroyed"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              Verdict
            </span>
            <p
              className="text-base leading-[1.8] text-foreground/70"
              style={{ fontFamily: "var(--font-cormorant)" }}
            >
              {claim.verdict}
            </p>
          </div>

          {/* Scores */}
          <div className="flex items-center justify-center gap-6 pt-2">
            {[
              { label: "Drama", value: claim.drama },
              { label: "Novelty", value: claim.novelty },
              { label: "Depth", value: claim.depth },
            ].map((metric) => (
              <div key={metric.label} className="flex flex-col items-center">
                <span
                  className="text-lg text-foreground/80"
                  style={{ fontFamily: "var(--font-cinzel)" }}
                >
                  {metric.value}
                </span>
                <span
                  className="text-[9px] uppercase tracking-wider text-foreground/40"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  {metric.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </article>
  );
}

function getEpitaph(verdict: string): string {
  const firstSentence = verdict.split(". ")[0];
  return firstSentence.replace(/^Destroyed\.\s*/i, "").trim();
}
