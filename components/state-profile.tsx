"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { STATES, CLAIMS, type StateEntity, type Claim } from "@/lib/data";
import { KnowledgeGraph } from "@/components/knowledge-graph";

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

function rulingColor(ruling: string): string {
  return ruling === "DESTROYED" ? "#dc2626" : "#d4d4d4";
}

function SectionHeading({ title }: { title: string }) {
  return (
    <div className="scroll-reveal mb-8 text-center">
      <h3
        className="mb-3"
        style={{
          fontFamily: "var(--font-serif)",
          fontSize: "22px",
          color: "#f5f5f5",
          letterSpacing: "0.2em",
        }}
      >
        {title}
      </h3>
      <div className="mx-auto h-px w-12" style={{ backgroundColor: "#dc2626", opacity: 0.5 }} />
    </div>
  );
}

function DarkCard({
  children,
  className = "",
  dimmed = false,
}: {
  children: React.ReactNode;
  className?: string;
  dimmed?: boolean;
}) {
  return (
    <div
      className={className}
      style={{
        backgroundColor: dimmed ? "#0a0a0a" : "#0e0e0e",
        border: "1px solid #1c1c1c",
        borderRadius: "12px",
        padding: "28px",
        opacity: dimmed ? 0.8 : 1,
      }}
    >
      {children}
    </div>
  );
}

function DebateCard({ claim }: { claim: Claim }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <DarkCard className="scroll-reveal" dimmed={claim.ruling === "DESTROYED"}>
      {/* Top row */}
      <div className="mb-4 flex flex-wrap items-center justify-center gap-4">
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            color: "#d4d4d4",
            letterSpacing: "0.1em",
            fontWeight: 600,
          }}
        >
          {claim.id}
        </span>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            color: "#a3a3a3",
            letterSpacing: "0.1em",
          }}
        >
          CYCLE {claim.cycle}
        </span>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            letterSpacing: "0.1em",
            color: rulingColor(claim.ruling),
            fontWeight: 600,
          }}
        >
          {claim.ruling}
        </span>
      </div>

      {/* Position text */}
      <p
        className="mb-5 text-center"
        style={{
          fontFamily: "var(--font-body)",
          fontSize: "17px",
          fontWeight: 600,
          color: claim.ruling === "DESTROYED" ? "#a3a3a3" : "#e5e5e5",
          lineHeight: "1.8",
          fontStyle: claim.ruling === "DESTROYED" ? "italic" : "normal",
        }}
      >
        {claim.position}
      </p>

      {/* Expand toggle */}
      <div className="text-center">
        <button
          onClick={() => setExpanded(!expanded)}
          className="inline-flex items-center gap-2"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            color: expanded ? "#dc2626" : "#a3a3a3",
            textTransform: "uppercase" as const,
            letterSpacing: "0.2em",
            background: "none",
            border: "none",
            cursor: "pointer",
            transition: "color 0.2s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "#dc2626";
          }}
          onMouseLeave={(e) => {
            if (!expanded) e.currentTarget.style.color = "#a3a3a3";
          }}
        >
          {expanded ? "COLLAPSE" : "VIEW DEBATE"}
          <span
            className="inline-block transition-transform duration-300"
            style={{ transform: expanded ? "rotate(180deg)" : "rotate(0deg)" }}
          >
            &#8595;
          </span>
        </button>
      </div>

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
            <div className="mb-5 text-center">
              <span
                className="mb-2 block"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  color: "#d4d4d4",
                  letterSpacing: "0.25em",
                  textTransform: "uppercase" as const,
                }}
              >
                Challenge
              </span>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "16px",
                  fontWeight: 600,
                  color: "#e5e5e5",
                  lineHeight: "1.8",
                }}
              >
                {claim.challenge}
              </p>
            </div>

            {/* Rebuttal */}
            <div className="mb-5 text-center">
              <span
                className="mb-2 block"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  color: "#d4d4d4",
                  letterSpacing: "0.25em",
                  textTransform: "uppercase" as const,
                }}
              >
                Rebuttal
              </span>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "16px",
                  fontWeight: 600,
                  color: "#e5e5e5",
                  lineHeight: "1.8",
                }}
              >
                {claim.rebuttal}
              </p>
            </div>

            {/* Verdict */}
            <div className="text-center">
              <span
                className="mb-2 block"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  color: "#d4d4d4",
                  letterSpacing: "0.25em",
                  textTransform: "uppercase" as const,
                }}
              >
                Verdict &middot;{" "}
                <span style={{ color: rulingColor(claim.ruling) }}>
                  {claim.ruling}
                </span>
              </span>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "16px",
                  fontWeight: 600,
                  color: "#f5f5f5",
                  lineHeight: "1.8",
                }}
              >
                {claim.verdict}
              </p>
            </div>
          </div>
        </div>
      </div>
    </DarkCard>
  );
}

export function StateProfile({ slug }: { slug: string }) {
  const containerRef = useScrollReveal();

  const state = STATES.find(
    (s) => s.name.toLowerCase().replace("_", "-") === slug
  );

  if (!state) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p style={{ fontFamily: "var(--font-body)", fontSize: "20px", color: "#a3a3a3" }}>
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
  const latestClaim = stateClaims.reduce(
    (a, b) => (a.cycle > b.cycle ? a : b),
    stateClaims[0]
  );

  const total = state.wins + state.partials + state.losses;
  const survivalPct =
    total > 0 ? Math.round(((state.wins + state.partials) / total) * 100) : 0;

  let tier = "IRON";
  if (survivalPct >= 80) tier = "GOLD";
  else if (survivalPct >= 60) tier = "SILVER";
  else if (survivalPct >= 40) tier = "BRONZE";

  const claimsByCycle = [1, 2, 3].map((cycle) =>
    stateClaims.filter((c) => c.cycle === cycle)
  );

  return (
    <section ref={containerRef}>
      {/* Back breadcrumb */}
      <div className="scroll-reveal mb-10 text-center">
        <Link
          href="/states"
          className="inline-flex items-center gap-2 transition-colors duration-200 hover:opacity-70"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            color: "#dc2626",
            letterSpacing: "0.15em",
          }}
        >
          &larr; STATES
        </Link>
      </div>

      {/* Header - centered */}
      <div className="scroll-reveal mb-16 text-center">
        <h1
          className="mb-3"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "36px",
            color: "#f5f5f5",
            letterSpacing: "0.15em",
          }}
        >
          {state.name.replace("_", " ")}
        </h1>

        <span
          className="mb-5 inline-block"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            color: "#dc2626",
            letterSpacing: "0.2em",
            textTransform: "uppercase" as const,
          }}
        >
          {state.domain}
        </span>

        <p
          className="mx-auto mb-6 max-w-2xl"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "19px",
            fontWeight: 600,
            fontStyle: "italic",
            color: "#d4d4d4",
            lineHeight: "1.8",
          }}
        >
          &ldquo;{state.approach}&rdquo;
        </p>

        {/* Stats row - centered */}
        <div className="flex flex-wrap items-center justify-center gap-8">
          <div
            className="flex items-center gap-1.5"
            style={{ fontFamily: "var(--font-mono)", fontSize: "14px" }}
          >
            <span style={{ color: "#d4d4d4" }}>W</span>
            <span style={{ color: "#f5f5f5", fontWeight: 700 }}>{state.wins}</span>
            <span style={{ color: "#2a2a2a" }}>/</span>
            <span style={{ color: "#d4d4d4" }}>P</span>
            <span style={{ color: "#f5f5f5", fontWeight: 700 }}>{state.partials}</span>
            <span style={{ color: "#2a2a2a" }}>/</span>
            <span style={{ color: "#d4d4d4" }}>L</span>
            <span style={{ color: "#f5f5f5", fontWeight: 700 }}>{state.losses}</span>
          </div>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "14px",
              color: "#dc2626",
              fontWeight: 700,
            }}
          >
            {survivalPct}% survival
          </span>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              letterSpacing: "0.15em",
              color: "#d4d4d4",
              border: "1px solid #333",
              padding: "4px 12px",
              borderRadius: "4px",
            }}
          >
            {tier} TIER
          </span>
        </div>
      </div>

      {/* Divider */}
      <div className="mx-auto mb-16 h-px max-w-xs" style={{ backgroundColor: "#1c1c1c" }} />

      {/* 1. LEARNING ARC */}
      <div className="mb-20">
        <SectionHeading title="LEARNING ARC" />
        <DarkCard className="scroll-reveal">
          <div className="flex flex-col gap-6">
            {claimsByCycle.map((cycleClaims, idx) => {
              if (cycleClaims.length === 0) return null;
              const claim = cycleClaims[0];
              return (
                <div key={idx} className="text-center">
                  <div className="mb-2 flex items-center justify-center gap-4">
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "12px",
                        color: "#d4d4d4",
                        letterSpacing: "0.2em",
                      }}
                    >
                      CYCLE {idx + 1}
                    </span>
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "12px",
                        letterSpacing: "0.1em",
                        color: rulingColor(claim.ruling),
                        fontWeight: 600,
                      }}
                    >
                      {claim.ruling}
                    </span>
                  </div>
                  <p
                    style={{
                      fontFamily: "var(--font-body)",
                      fontSize: "17px",
                      fontWeight: 600,
                      color: "#e5e5e5",
                      lineHeight: "1.8",
                    }}
                  >
                    {claim.position}
                  </p>
                  {idx < claimsByCycle.filter((c) => c.length > 0).length - 1 && (
                    <div
                      className="mx-auto mt-6"
                      style={{ height: "1px", maxWidth: "120px", backgroundColor: "#1c1c1c" }}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {/* Narrative */}
          <div className="mt-8 pt-6 text-center" style={{ borderTop: "1px solid #1c1c1c" }}>
            <span
              className="mb-3 block"
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                color: "#d4d4d4",
                letterSpacing: "0.25em",
                textTransform: "uppercase" as const,
              }}
            >
              Narrative
            </span>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "17px",
                fontWeight: 600,
                color: "#e5e5e5",
                lineHeight: "1.9",
              }}
            >
              {state.learningArc}
            </p>
          </div>
        </DarkCard>
      </div>

      {/* 2. ACTIVE RESEARCH */}
      <div className="mb-20">
        <SectionHeading title="ACTIVE RESEARCH" />
        <DarkCard className="scroll-reveal text-center">
          <div className="mb-3 flex items-center justify-center gap-3">
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "12px",
                color: "#dc2626",
                letterSpacing: "0.15em",
                textTransform: "uppercase" as const,
              }}
            >
              {state.domain}
            </span>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "12px",
                color: "#a3a3a3",
              }}
            >
              {latestClaim.id} &middot; Cycle {latestClaim.cycle}
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "18px",
              fontWeight: 600,
              color: "#f5f5f5",
              lineHeight: "1.8",
            }}
          >
            {latestClaim.position}
          </p>
        </DarkCard>
      </div>

      {/* 3. KNOWLEDGE GRAPH */}
      <div className="mb-20">
        <SectionHeading title="KNOWLEDGE GRAPH" />
        <div className="scroll-reveal">
          <KnowledgeGraph stateName={state.name} stateClaims={stateClaims} />
        </div>
      </div>

      {/* 4. DEBATES */}
      <div className="mb-20">
        <SectionHeading title="DEBATES" />
        <div className="flex flex-col gap-6">
          {claimsByCycle.map((cycleClaims, cycleIdx) => {
            if (cycleClaims.length === 0) return null;
            return (
              <div key={cycleIdx}>
                <span
                  className="scroll-reveal mb-4 block text-center"
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    color: "#d4d4d4",
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

      {/* 5. KNOWLEDGE (surviving claims) */}
      <div className="mb-20">
        <SectionHeading title="KNOWLEDGE" />
        {survivingClaims.length === 0 ? (
          <p
            className="scroll-reveal text-center"
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "17px",
              fontWeight: 600,
              color: "#737373",
              fontStyle: "italic",
            }}
          >
            No surviving claims yet.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            {survivingClaims.map((claim) => (
              <DarkCard key={claim.id} className="scroll-reveal text-center">
                <div className="mb-3 flex items-center justify-center gap-3">
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "12px",
                      color: "#d4d4d4",
                      letterSpacing: "0.1em",
                      fontWeight: 600,
                    }}
                  >
                    {claim.id}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "12px",
                      color: "#a3a3a3",
                      letterSpacing: "0.1em",
                    }}
                  >
                    CYCLE {claim.cycle}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "12px",
                      letterSpacing: "0.1em",
                      color: "#d4d4d4",
                    }}
                  >
                    {claim.ruling}
                  </span>
                </div>
                <p
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "17px",
                    fontWeight: 600,
                    color: "#e5e5e5",
                    lineHeight: "1.8",
                  }}
                >
                  {claim.position}
                </p>
              </DarkCard>
            ))}
          </div>
        )}
      </div>

      {/* 6. GRAVEYARD (destroyed claims) */}
      <div className="mb-20">
        <SectionHeading title="GRAVEYARD" />
        {destroyedClaims.length === 0 ? (
          <p
            className="scroll-reveal text-center"
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "17px",
              fontWeight: 600,
              color: "#737373",
              fontStyle: "italic",
            }}
          >
            No destroyed claims.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            {destroyedClaims.map((claim) => (
              <DarkCard key={claim.id} className="scroll-reveal text-center" dimmed>
                <div className="mb-3 flex items-center justify-center gap-3">
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "12px",
                      color: "#a3a3a3",
                      letterSpacing: "0.1em",
                      fontWeight: 600,
                    }}
                  >
                    {claim.id}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "12px",
                      color: "#a3a3a3",
                      letterSpacing: "0.1em",
                    }}
                  >
                    CYCLE {claim.cycle}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "12px",
                      letterSpacing: "0.1em",
                      color: "#dc2626",
                      fontWeight: 600,
                    }}
                  >
                    DESTROYED
                  </span>
                </div>
                <p
                  className="mb-4"
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "17px",
                    fontWeight: 600,
                    color: "#a3a3a3",
                    lineHeight: "1.8",
                  }}
                >
                  {claim.position}
                </p>
                <p
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "16px",
                    fontWeight: 600,
                    color: "#737373",
                    lineHeight: "1.8",
                    fontStyle: "italic",
                  }}
                >
                  {claim.verdict}
                </p>
              </DarkCard>
            ))}
          </div>
        )}
      </div>

      {/* 7. CITIES & TOWNS */}
      <div className="mb-20">
        <SectionHeading title="CITIES & TOWNS" />
        <div className="scroll-reveal flex flex-col gap-6 md:flex-row">
          <DarkCard className="flex-1 text-center">
            <span
              className="mb-3 block"
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                color: "#a3a3a3",
                letterSpacing: "0.2em",
                textTransform: "uppercase" as const,
              }}
            >
              Cities
            </span>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "17px",
                fontWeight: 600,
                color: "#737373",
                fontStyle: "italic",
              }}
            >
              No cities formed yet.
            </p>
          </DarkCard>
          <DarkCard className="flex-1 text-center">
            <span
              className="mb-3 block"
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                color: "#a3a3a3",
                letterSpacing: "0.2em",
                textTransform: "uppercase" as const,
              }}
            >
              Towns
            </span>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "17px",
                fontWeight: 600,
                color: "#737373",
                fontStyle: "italic",
              }}
            >
              No towns formed yet.
            </p>
          </DarkCard>
        </div>
      </div>

      <div style={{ height: "40px" }} />
    </section>
  );
}
