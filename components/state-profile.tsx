"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { STATES, CLAIMS, type StateEntity, type Claim } from "@/lib/data";

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
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );
    el.querySelectorAll(".scroll-reveal").forEach((child) =>
      observer.observe(child)
    );
    return () => observer.disconnect();
  }, []);
  return ref;
}

const RULING_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  REVISE: { bg: "rgba(245, 158, 11, 0.1)", text: "#f59e0b", label: "REVISE" },
  PARTIAL: { bg: "rgba(34, 197, 94, 0.1)", text: "#22c55e", label: "PARTIAL" },
  DESTROYED: { bg: "rgba(220, 38, 38, 0.1)", text: "#dc2626", label: "DESTROYED" },
};

function SectionHeading({ title }: { title: string }) {
  return (
    <div className="scroll-reveal mb-8">
      <h3
        className="mb-3"
        style={{
          fontFamily: "var(--font-serif)",
          fontSize: "20px",
          color: "#e5e5e5",
          letterSpacing: "0.2em",
        }}
      >
        {title}
      </h3>
      <div className="h-px w-12" style={{ backgroundColor: "#dc2626", opacity: 0.5 }} />
    </div>
  );
}

function DebateCard({ claim }: { claim: Claim }) {
  const [expanded, setExpanded] = useState(false);
  const ruling = RULING_STYLES[claim.ruling];

  return (
    <div
      className="scroll-reveal"
      style={{
        backgroundColor: claim.ruling === "DESTROYED" ? "#0a0a0a" : "#0e0e0e",
        border: "1px solid #1c1c1c",
        borderRadius: "12px",
        padding: "24px",
        opacity: claim.ruling === "DESTROYED" ? 0.7 : 1,
      }}
    >
      {/* Top row: claim id + cycle + ruling badge */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "#525252",
              letterSpacing: "0.1em",
            }}
          >
            {claim.id}
          </span>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "#525252",
              letterSpacing: "0.1em",
            }}
          >
            CYCLE {claim.cycle}
          </span>
        </div>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            letterSpacing: "0.1em",
            color: ruling.text,
            backgroundColor: ruling.bg,
            padding: "3px 10px",
            borderRadius: "4px",
          }}
        >
          {ruling.label}
        </span>
      </div>

      {/* Position text */}
      <p
        className="mb-4"
        style={{
          fontFamily: "var(--font-body)",
          fontSize: "16px",
          color: claim.ruling === "DESTROYED" ? "#737373" : "#a3a3a3",
          lineHeight: "1.7",
          fontStyle: claim.ruling === "DESTROYED" ? "italic" : "normal",
        }}
      >
        {claim.position}
      </p>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2"
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "10px",
          color: expanded ? "#dc2626" : "#525252",
          textTransform: "uppercase" as const,
          letterSpacing: "0.2em",
          background: "none",
          border: "none",
          cursor: "pointer",
        }}
        onMouseEnter={(e) => { e.currentTarget.style.color = "#dc2626"; }}
        onMouseLeave={(e) => { if (!expanded) e.currentTarget.style.color = "#525252"; }}
      >
        {expanded ? "COLLAPSE" : "VIEW DEBATE"}
        <span
          className="inline-block transition-transform duration-300"
          style={{ transform: expanded ? "rotate(180deg)" : "rotate(0deg)" }}
        >
          &#8595;
        </span>
      </button>

      {/* Expanded debate */}
      <div
        className="grid transition-all duration-500 ease-out"
        style={{
          gridTemplateRows: expanded ? "1fr" : "0fr",
          opacity: expanded ? 1 : 0,
        }}
      >
        <div className="overflow-hidden">
          <div style={{ paddingTop: "20px" }}>
            <div className="mb-5 h-px" style={{ backgroundColor: "#1c1c1c" }} />

            {/* Challenge */}
            <div className="mb-5">
              <span
                className="mb-2 block"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "9px",
                  color: "#dc2626",
                  letterSpacing: "0.25em",
                  textTransform: "uppercase" as const,
                }}
              >
                Challenge
              </span>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "15px",
                  color: "#a3a3a3",
                  lineHeight: "1.8",
                }}
              >
                {claim.challenge}
              </p>
            </div>

            {/* Rebuttal */}
            <div className="mb-5">
              <span
                className="mb-2 block"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "9px",
                  color: "#f59e0b",
                  letterSpacing: "0.25em",
                  textTransform: "uppercase" as const,
                }}
              >
                Rebuttal
              </span>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "15px",
                  color: "#a3a3a3",
                  lineHeight: "1.8",
                }}
              >
                {claim.rebuttal}
              </p>
            </div>

            {/* Verdict */}
            <div>
              <span
                className="mb-2 block"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "9px",
                  color: ruling.text,
                  letterSpacing: "0.25em",
                  textTransform: "uppercase" as const,
                }}
              >
                Verdict
              </span>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "15px",
                  color: "#e5e5e5",
                  lineHeight: "1.8",
                  fontStyle: claim.ruling === "DESTROYED" ? "italic" : "normal",
                }}
              >
                {claim.verdict}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function StateProfile({ slug }: { slug: string }) {
  const containerRef = useScrollReveal();

  // Find the state by slug
  const state = STATES.find(
    (s) => s.name.toLowerCase().replace("_", "-") === slug
  );

  if (!state) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p style={{ fontFamily: "var(--font-body)", fontSize: "20px", color: "#737373" }}>
          State not found.
        </p>
      </div>
    );
  }

  const stateClaims = CLAIMS.filter((c) => c.state === state.name);
  const survivingClaims = stateClaims.filter(
    (c) => c.ruling === "REVISE" || c.ruling === "PARTIAL"
  );
  const destroyedClaims = stateClaims.filter((c) => c.ruling === "DESTROYED");
  const latestClaim = stateClaims.reduce((a, b) => (a.cycle > b.cycle ? a : b), stateClaims[0]);

  const total = state.wins + state.partials + state.losses;
  const survivalPct =
    total > 0 ? Math.round(((state.wins + state.partials) / total) * 100) : 0;

  // Tier calculation
  let tier = "IRON";
  if (survivalPct >= 80) tier = "GOLD";
  else if (survivalPct >= 60) tier = "SILVER";
  else if (survivalPct >= 40) tier = "BRONZE";

  // Group claims by cycle for the Debates section
  const claimsByCycle = [1, 2, 3].map((cycle) =>
    stateClaims.filter((c) => c.cycle === cycle)
  );

  return (
    <section ref={containerRef}>
      {/* Back breadcrumb */}
      <div className="scroll-reveal mb-10">
        <Link
          href="/states"
          className="inline-flex items-center gap-2 transition-colors duration-200"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            color: "#dc2626",
            letterSpacing: "0.15em",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = "#dc2626"; }}
        >
          &larr; States
        </Link>
      </div>

      {/* Header */}
      <div className="scroll-reveal mb-16">
        <h1
          className="mb-3"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "36px",
            color: "#e5e5e5",
            letterSpacing: "0.15em",
          }}
        >
          {state.name.replace("_", " ")}
        </h1>

        <span
          className="mb-5 inline-block"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            color: "#dc2626",
            letterSpacing: "0.2em",
            textTransform: "uppercase" as const,
          }}
        >
          {state.domain}
        </span>

        <p
          className="mb-6 max-w-2xl"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "18px",
            fontStyle: "italic",
            color: "#a3a3a3",
            lineHeight: "1.8",
          }}
        >
          &ldquo;{state.approach}&rdquo;
        </p>

        {/* Stats row */}
        <div className="flex flex-wrap items-center gap-8">
          <div className="flex items-center gap-1.5" style={{ fontFamily: "var(--font-mono)", fontSize: "13px" }}>
            <span style={{ color: "#525252" }}>W</span>
            <span style={{ color: "#22c55e" }}>{state.wins}</span>
            <span style={{ color: "#2a2a2a" }}>/</span>
            <span style={{ color: "#525252" }}>P</span>
            <span style={{ color: "#f59e0b" }}>{state.partials}</span>
            <span style={{ color: "#2a2a2a" }}>/</span>
            <span style={{ color: "#525252" }}>L</span>
            <span style={{ color: "#737373" }}>{state.losses}</span>
          </div>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "13px",
              color: "#dc2626",
              fontWeight: 500,
            }}
          >
            {survivalPct}% survival
          </span>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              letterSpacing: "0.15em",
              color: "#525252",
              border: "1px solid #1c1c1c",
              padding: "3px 10px",
              borderRadius: "4px",
            }}
          >
            {tier} TIER
          </span>
        </div>
      </div>

      {/* Divider */}
      <div className="mb-16 h-px" style={{ backgroundColor: "#1c1c1c" }} />

      {/* 1. LEARNING ARC */}
      <div className="mb-20">
        <SectionHeading title="LEARNING ARC" />
        <div className="scroll-reveal flex flex-col gap-6">
          {claimsByCycle.map((cycleClaims, idx) => {
            if (cycleClaims.length === 0) return null;
            const claim = cycleClaims[0];
            const ruling = RULING_STYLES[claim.ruling];
            return (
              <div key={idx} className="flex gap-5">
                <div className="flex flex-col items-center">
                  <div
                    className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full"
                    style={{ backgroundColor: "rgba(220, 38, 38, 0.1)", border: "1px solid rgba(220, 38, 38, 0.25)" }}
                  >
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "#dc2626" }}>
                      {idx + 1}
                    </span>
                  </div>
                  {idx < 2 && (
                    <div className="flex-1" style={{ width: "1px", backgroundColor: "rgba(220, 38, 38, 0.15)", minHeight: "40px" }} />
                  )}
                </div>
                <div className="pb-2">
                  <div className="mb-2 flex items-center gap-3">
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "10px",
                        color: "#525252",
                        letterSpacing: "0.15em",
                      }}
                    >
                      CYCLE {idx + 1}
                    </span>
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "9px",
                        letterSpacing: "0.1em",
                        color: ruling.text,
                        backgroundColor: ruling.bg,
                        padding: "2px 8px",
                        borderRadius: "3px",
                      }}
                    >
                      {ruling.label}
                    </span>
                  </div>
                  <p
                    style={{
                      fontFamily: "var(--font-body)",
                      fontSize: "16px",
                      color: "#a3a3a3",
                      lineHeight: "1.8",
                    }}
                  >
                    {claim.position}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Full learning arc narrative */}
        <div
          className="scroll-reveal mt-8"
          style={{
            backgroundColor: "#0e0e0e",
            border: "1px solid #1c1c1c",
            borderRadius: "12px",
            padding: "24px",
          }}
        >
          <span
            className="mb-3 block"
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "9px",
              color: "#dc2626",
              letterSpacing: "0.25em",
              textTransform: "uppercase" as const,
            }}
          >
            Narrative
          </span>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "16px",
              color: "#a3a3a3",
              lineHeight: "1.9",
            }}
          >
            {state.learningArc}
          </p>
        </div>
      </div>

      {/* 2. ACTIVE RESEARCH */}
      <div className="mb-20">
        <SectionHeading title="ACTIVE RESEARCH" />
        <div
          className="scroll-reveal"
          style={{
            backgroundColor: "#0e0e0e",
            border: "1px solid #1c1c1c",
            borderRadius: "12px",
            padding: "24px",
          }}
        >
          <div className="mb-3 flex items-center gap-3">
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "10px",
                color: "#dc2626",
                letterSpacing: "0.15em",
                textTransform: "uppercase" as const,
              }}
            >
              {state.domain}
            </span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "#525252" }}>
              {latestClaim.id} &middot; Cycle {latestClaim.cycle}
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "17px",
              color: "#e5e5e5",
              lineHeight: "1.8",
            }}
          >
            {latestClaim.position}
          </p>
        </div>
      </div>

      {/* 3. DEBATES */}
      <div className="mb-20">
        <SectionHeading title="DEBATES" />
        <div className="flex flex-col gap-6">
          {claimsByCycle.map((cycleClaims, cycleIdx) => {
            if (cycleClaims.length === 0) return null;
            return (
              <div key={cycleIdx}>
                <span
                  className="scroll-reveal mb-4 block"
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "10px",
                    color: "#525252",
                    letterSpacing: "0.2em",
                  }}
                >
                  CYCLE {cycleIdx + 1}
                </span>
                <div className="flex flex-col gap-4">
                  {cycleClaims.map((claim) => (
                    <DebateCard key={claim.id} claim={claim} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. KNOWLEDGE (surviving claims) */}
      <div className="mb-20">
        <SectionHeading title="KNOWLEDGE" />
        {survivingClaims.length === 0 ? (
          <p
            className="scroll-reveal"
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "16px",
              color: "#525252",
              fontStyle: "italic",
            }}
          >
            No surviving claims yet.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            {survivingClaims.map((claim) => (
              <div
                key={claim.id}
                className="scroll-reveal"
                style={{
                  backgroundColor: "#0e0e0e",
                  border: "1px solid #1c1c1c",
                  borderRadius: "12px",
                  padding: "24px",
                }}
              >
                <div className="mb-3 flex items-center gap-3">
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "#525252", letterSpacing: "0.1em" }}>
                    {claim.id}
                  </span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "#525252", letterSpacing: "0.1em" }}>
                    CYCLE {claim.cycle}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "9px",
                      letterSpacing: "0.1em",
                      color: RULING_STYLES[claim.ruling].text,
                      backgroundColor: RULING_STYLES[claim.ruling].bg,
                      padding: "2px 8px",
                      borderRadius: "3px",
                    }}
                  >
                    {RULING_STYLES[claim.ruling].label}
                  </span>
                </div>
                <p
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "16px",
                    color: "#a3a3a3",
                    lineHeight: "1.8",
                  }}
                >
                  {claim.position}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5. GRAVEYARD (destroyed claims) */}
      <div className="mb-20">
        <SectionHeading title="GRAVEYARD" />
        {destroyedClaims.length === 0 ? (
          <p
            className="scroll-reveal"
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "16px",
              color: "#525252",
              fontStyle: "italic",
            }}
          >
            No destroyed claims.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            {destroyedClaims.map((claim) => (
              <div
                key={claim.id}
                className="scroll-reveal"
                style={{
                  backgroundColor: "#0a0a0a",
                  border: "1px solid #151515",
                  borderRadius: "12px",
                  padding: "24px",
                  opacity: 0.7,
                }}
              >
                <div className="mb-3 flex items-center gap-3">
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "#525252", letterSpacing: "0.1em" }}>
                    {claim.id}
                  </span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "#525252", letterSpacing: "0.1em" }}>
                    CYCLE {claim.cycle}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "9px",
                      letterSpacing: "0.1em",
                      color: "#dc2626",
                      backgroundColor: "rgba(220, 38, 38, 0.1)",
                      padding: "2px 8px",
                      borderRadius: "3px",
                    }}
                  >
                    DESTROYED
                  </span>
                </div>
                <p
                  className="mb-4"
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "16px",
                    color: "#737373",
                    lineHeight: "1.7",
                  }}
                >
                  {claim.position}
                </p>
                <p
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "15px",
                    color: "#525252",
                    lineHeight: "1.7",
                    fontStyle: "italic",
                  }}
                >
                  {claim.verdict}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 6. CITIES & TOWNS */}
      <div className="mb-20">
        <SectionHeading title="CITIES & TOWNS" />
        <div className="scroll-reveal flex flex-col gap-6 md:flex-row">
          <div
            className="flex-1"
            style={{
              backgroundColor: "#0e0e0e",
              border: "1px solid #1c1c1c",
              borderRadius: "12px",
              padding: "24px",
            }}
          >
            <span
              className="mb-3 block"
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "10px",
                color: "#525252",
                letterSpacing: "0.2em",
                textTransform: "uppercase" as const,
              }}
            >
              Cities
            </span>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "16px",
                color: "#525252",
                fontStyle: "italic",
              }}
            >
              No cities formed yet.
            </p>
          </div>
          <div
            className="flex-1"
            style={{
              backgroundColor: "#0e0e0e",
              border: "1px solid #1c1c1c",
              borderRadius: "12px",
              padding: "24px",
            }}
          >
            <span
              className="mb-3 block"
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "10px",
                color: "#525252",
                letterSpacing: "0.2em",
                textTransform: "uppercase" as const,
              }}
            >
              Towns
            </span>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "16px",
                color: "#525252",
                fontStyle: "italic",
              }}
            >
              No towns formed yet.
            </p>
          </div>
        </div>
      </div>

      {/* Bottom spacer */}
      <div style={{ height: "40px" }} />
    </section>
  );
}
