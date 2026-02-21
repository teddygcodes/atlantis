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

const DOMAIN_FILTERS = [
  "All",
  "Consciousness",
  "Causation",
  "Mathematics",
] as const;
type DomainFilter = (typeof DOMAIN_FILTERS)[number];

export function Archive() {
  const containerRef = useScrollReveal();
  const [filter, setFilter] = useState<DomainFilter>("All");

  const survivingClaims = CLAIMS.filter(
    (c) => c.ruling === "REVISE" || c.ruling === "PARTIAL"
  );
  const filteredClaims =
    filter === "All"
      ? survivingClaims
      : survivingClaims.filter((c) => c.domain === filter);

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
          THE ARCHIVE
        </h2>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "16px",
            color: "#a3a3a3",
          }}
        >
          The surviving claims. Each one has withstood adversarial challenge and
          earned its place in the vault.
        </p>
      </div>

      {/* 48px gap below subtitle */}
      <div style={{ height: "48px" }} />

      {/* Domain filter */}
      <div className="scroll-reveal mx-auto mb-12 flex max-w-[900px] items-center gap-1">
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
      <div className="mx-auto flex max-w-[900px] flex-col gap-4">
        {filteredClaims.map((claim) => (
          <VaultEntry key={claim.id} claim={claim} />
        ))}
      </div>

      {filteredClaims.length === 0 && (
        <p
          className="mx-auto max-w-[900px] py-20 text-center text-lg text-muted/40"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          No surviving claims in this domain.
        </p>
      )}
    </section>
  );
}

function VaultEntry({ claim }: { claim: Claim }) {
  const [unlocked, setUnlocked] = useState(false);
  const isSurviving = claim.ruling === "REVISE" || claim.ruling === "PARTIAL";

  return (
    <article
      className="scroll-reveal group overflow-hidden rounded border border-border/60 transition-all duration-500 hover:border-border"
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
            className="text-lg leading-relaxed text-foreground/80"
            style={{ fontFamily: "var(--font-cormorant)" }}
          >
            {claim.position}
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
            <DebateStep label="Challenge" text={claim.challenge} side="left" />
            <DebateStep label="Rebuttal" text={claim.rebuttal} side="right" />
            <div className="mx-auto mt-4 max-w-lg rounded border border-accent/10 bg-accent/5 px-6 py-5 text-center">
              <span
                className="mb-2 block text-[9px] uppercase tracking-[0.25em] text-accent"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                Verdict
              </span>
              <p
                className="text-lg leading-relaxed text-foreground/80"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.verdict}
              </p>
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
          className="text-base leading-[1.8] text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          {text}
        </p>
      </div>
    </div>
  );
}
