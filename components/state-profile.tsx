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
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    );
    el.querySelectorAll(".scroll-reveal").forEach((child) =>
      observer.observe(child)
    );
    return () => observer.disconnect();
  }, []);
  return ref;
}

/* ───────────── Shared sub-components ───────────── */

function rulingBadge(ruling: string) {
  const color =
    ruling === "DESTROYED" ? "#dc2626" : ruling === "PARTIAL" ? "#f59e0b" : "#22c55e";
  return (
    <span
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: "11px",
        letterSpacing: "0.15em",
        color,
        fontWeight: 700,
        padding: "3px 10px",
        border: `1px solid ${color}33`,
        borderRadius: "4px",
      }}
    >
      {ruling}
    </span>
  );
}

function SectionDivider() {
  return (
    <div className="scroll-reveal flex items-center justify-center gap-4 py-16">
      <div className="h-px w-8" style={{ backgroundColor: "#dc262640" }} />
      <div
        className="h-1.5 w-1.5 rotate-45"
        style={{ backgroundColor: "#dc2626", opacity: 0.5 }}
      />
      <div className="h-px w-8" style={{ backgroundColor: "#dc262640" }} />
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="mb-2 block text-center"
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: "10px",
        letterSpacing: "0.3em",
        color: "#dc2626",
        fontWeight: 600,
      }}
    >
      {children}
    </span>
  );
}

/* ───────────── Debate Accordion ───────────── */

function DebateCard({ claim, index }: { claim: Claim; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="scroll-reveal"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left transition-colors duration-300"
        style={{
          backgroundColor: expanded ? "#0e0e0e" : "transparent",
          border: `1px solid ${expanded ? "#1c1c1c" : "#141414"}`,
          borderRadius: "12px",
          padding: "24px 28px",
          cursor: "pointer",
        }}
        onMouseEnter={(e) => {
          if (!expanded)
            e.currentTarget.style.borderColor = "#dc262640";
        }}
        onMouseLeave={(e) => {
          if (!expanded)
            e.currentTarget.style.borderColor = "#141414";
        }}
      >
        {/* Header row */}
        <div className="mb-3 flex flex-wrap items-center justify-center gap-3">
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "12px",
              color: "#dc2626",
              fontWeight: 700,
              letterSpacing: "0.1em",
            }}
          >
            {claim.id}
          </span>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              color: "#525252",
              letterSpacing: "0.1em",
            }}
          >
            CYCLE {claim.cycle}
          </span>
          {rulingBadge(claim.ruling)}
        </div>

        {/* Claim text */}
        <p
          className="text-center"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "18px",
            fontWeight: 600,
            color: claim.ruling === "DESTROYED" ? "#a3a3a3" : "#f5f5f5",
            lineHeight: "1.8",
            textDecoration: claim.ruling === "DESTROYED" ? "line-through" : "none",
            textDecorationColor: "#dc262640",
          }}
        >
          {claim.position}
        </p>

        {/* Expand hint */}
        <div className="mt-3 text-center">
          <span
            className="inline-block transition-transform duration-300"
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: expanded ? "#dc2626" : "#404040",
              letterSpacing: "0.2em",
              transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
            }}
          >
            &#9660;
          </span>
        </div>
      </button>

      {/* Expanded content */}
      <div
        className="grid transition-all duration-500 ease-out"
        style={{
          gridTemplateRows: expanded ? "1fr" : "0fr",
          opacity: expanded ? 1 : 0,
        }}
      >
        <div className="overflow-hidden">
          <div
            className="mx-4 mb-2 flex flex-col gap-8 rounded-b-xl px-6 pb-8 pt-6 md:mx-8 md:px-10"
            style={{
              backgroundColor: "#0a0a0a",
              borderLeft: "1px solid #1c1c1c",
              borderRight: "1px solid #1c1c1c",
              borderBottom: "1px solid #1c1c1c",
            }}
          >
            {/* Challenge */}
            <div className="text-center">
              <SectionLabel>CHALLENGE</SectionLabel>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "17px",
                  fontWeight: 600,
                  color: "#e5e5e5",
                  lineHeight: "1.9",
                }}
              >
                {claim.challenge}
              </p>
            </div>

            <div className="mx-auto h-px w-16" style={{ backgroundColor: "#1c1c1c" }} />

            {/* Rebuttal */}
            <div className="text-center">
              <SectionLabel>REBUTTAL</SectionLabel>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "17px",
                  fontWeight: 600,
                  color: "#e5e5e5",
                  lineHeight: "1.9",
                }}
              >
                {claim.rebuttal}
              </p>
            </div>

            <div className="mx-auto h-px w-16" style={{ backgroundColor: "#1c1c1c" }} />

            {/* Verdict */}
            <div className="text-center">
              <SectionLabel>VERDICT</SectionLabel>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "17px",
                  fontWeight: 600,
                  color: "#f5f5f5",
                  lineHeight: "1.9",
                }}
              >
                {claim.verdict}
              </p>
            </div>

            {/* Scores */}
            <div className="flex items-center justify-center gap-10 pt-2">
              {[
                { label: "DRAMA", value: claim.drama },
                { label: "NOVELTY", value: claim.novelty },
                { label: "DEPTH", value: claim.depth },
              ].map((m) => (
                <div key={m.label} className="flex flex-col items-center gap-1">
                  <span
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "24px",
                      color: "#f5f5f5",
                    }}
                  >
                    {m.value}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "9px",
                      color: "#525252",
                      letterSpacing: "0.2em",
                    }}
                  >
                    {m.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ───────────── Main Component ───────────── */

export function StateProfile({ slug }: { slug: string }) {
  const containerRef = useScrollReveal();

  const state = STATES.find(
    (s) => s.name.toLowerCase().replace("_", "-") === slug
  );

  if (!state) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p style={{ fontFamily: "var(--font-body)", fontSize: "22px", color: "#525252" }}>
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
      {/* ── HERO ZONE ── */}
      <div className="scroll-reveal mb-6 text-center">
        <Link
          href="/states"
          className="inline-flex items-center gap-2 transition-opacity duration-200 hover:opacity-60"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            color: "#525252",
            letterSpacing: "0.2em",
          }}
        >
          &larr; ALL STATES
        </Link>
      </div>

      {/* State identity */}
      <div className="scroll-reveal mb-6 text-center">
        <div
          className="mb-4"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            color: "#dc2626",
            letterSpacing: "0.3em",
          }}
        >
          {state.domain.toUpperCase()}
        </div>

        <h1
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "clamp(32px, 6vw, 48px)",
            color: "#f5f5f5",
            letterSpacing: "0.12em",
            lineHeight: 1.1,
          }}
        >
          {state.name.replace("_", " ")}
        </h1>
      </div>

      {/* Approach quote */}
      <div className="scroll-reveal mb-8 text-center">
        <p
          className="mx-auto max-w-xl"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "20px",
            fontWeight: 600,
            fontStyle: "italic",
            color: "#a3a3a3",
            lineHeight: "1.8",
          }}
        >
          &ldquo;{state.approach}&rdquo;
        </p>
      </div>

      {/* Stats strip */}
      <div className="scroll-reveal mb-4 flex flex-wrap items-center justify-center gap-6">
        {[
          { label: "W", value: state.wins, color: "#22c55e" },
          { label: "P", value: state.partials, color: "#f59e0b" },
          { label: "L", value: state.losses, color: "#dc2626" },
        ].map((s) => (
          <div key={s.label} className="flex items-center gap-2">
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                color: "#525252",
                letterSpacing: "0.1em",
              }}
            >
              {s.label}
            </span>
            <span
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "28px",
                color: s.color,
                fontWeight: 700,
              }}
            >
              {s.value}
            </span>
          </div>
        ))}

        <div className="h-6 w-px" style={{ backgroundColor: "#1c1c1c" }} />

        <div className="flex items-center gap-3">
          <span
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "28px",
              color: "#f5f5f5",
              fontWeight: 700,
            }}
          >
            {survivalPct}%
          </span>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "#525252",
              letterSpacing: "0.15em",
            }}
          >
            SURVIVAL
          </span>
        </div>

        <div className="h-6 w-px" style={{ backgroundColor: "#1c1c1c" }} />

        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            letterSpacing: "0.2em",
            color:
              tier === "GOLD"
                ? "#f59e0b"
                : tier === "SILVER"
                  ? "#a3a3a3"
                  : tier === "BRONZE"
                    ? "#cd7f32"
                    : "#525252",
            fontWeight: 700,
          }}
        >
          {tier}
        </span>
      </div>

      <SectionDivider />

      {/* ── CURRENT RESEARCH ── */}
      <div className="scroll-reveal mb-0 text-center">
        <SectionLabel>CURRENT FOCUS</SectionLabel>
        <h2
          className="mb-6"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "24px",
            color: "#f5f5f5",
            letterSpacing: "0.15em",
          }}
        >
          Active Research
        </h2>
        <div
          className="mx-auto max-w-2xl rounded-xl px-8 py-8 md:px-12"
          style={{
            backgroundColor: "#0e0e0e",
            border: "1px solid #dc262625",
          }}
        >
          <div className="mb-3 flex items-center justify-center gap-3">
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "12px",
                color: "#dc2626",
                fontWeight: 700,
                letterSpacing: "0.1em",
              }}
            >
              {latestClaim.id}
            </span>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                color: "#404040",
                letterSpacing: "0.1em",
              }}
            >
              CYCLE {latestClaim.cycle}
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "20px",
              fontWeight: 600,
              color: "#f5f5f5",
              lineHeight: "1.8",
            }}
          >
            {latestClaim.position}
          </p>
        </div>
      </div>

      <SectionDivider />

      {/* ── KNOWLEDGE GRAPH ── */}
      <div className="scroll-reveal mb-0 text-center">
        <SectionLabel>NETWORK</SectionLabel>
        <h2
          className="mb-8"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "24px",
            color: "#f5f5f5",
            letterSpacing: "0.15em",
          }}
        >
          Knowledge Graph
        </h2>
        <KnowledgeGraph stateName={state.name} stateClaims={stateClaims} />
      </div>

      <SectionDivider />

      {/* ── LEARNING ARC ── */}
      <div className="scroll-reveal mb-0 text-center">
        <SectionLabel>EVOLUTION</SectionLabel>
        <h2
          className="mb-10"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "24px",
            color: "#f5f5f5",
            letterSpacing: "0.15em",
          }}
        >
          Learning Arc
        </h2>

        {/* Timeline */}
        <div className="relative mx-auto max-w-2xl">
          {/* Vertical line */}
          <div
            className="absolute left-1/2 top-0 h-full -translate-x-1/2"
            style={{ width: "1px", backgroundColor: "#1c1c1c" }}
          />

          {claimsByCycle.map((cycleClaims, idx) => {
            if (cycleClaims.length === 0) return null;
            const claim = cycleClaims[0];
            return (
              <div key={idx} className="relative pb-12 last:pb-0">
                {/* Node on timeline */}
                <div className="absolute left-1/2 top-2 flex -translate-x-1/2 items-center justify-center">
                  <div
                    className="z-10 flex h-8 w-8 items-center justify-center rounded-full"
                    style={{
                      backgroundColor:
                        claim.ruling === "DESTROYED" ? "#1c1c1c" : "#dc2626",
                      border: "2px solid #0e0e0e",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "10px",
                        color: claim.ruling === "DESTROYED" ? "#525252" : "#fff",
                        fontWeight: 700,
                      }}
                    >
                      {idx + 1}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="mx-auto w-full pt-14">
                  <div className="mb-2 flex items-center justify-center gap-3">
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "11px",
                        color: "#525252",
                        letterSpacing: "0.15em",
                      }}
                    >
                      CYCLE {idx + 1}
                    </span>
                    {rulingBadge(claim.ruling)}
                  </div>
                  <p
                    style={{
                      fontFamily: "var(--font-body)",
                      fontSize: "18px",
                      fontWeight: 600,
                      color: claim.ruling === "DESTROYED" ? "#737373" : "#e5e5e5",
                      lineHeight: "1.8",
                      textDecoration:
                        claim.ruling === "DESTROYED" ? "line-through" : "none",
                      textDecorationColor: "#dc262640",
                    }}
                  >
                    {claim.position}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Narrative */}
        <div className="mx-auto mt-12 max-w-2xl">
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "17px",
              fontWeight: 600,
              color: "#a3a3a3",
              lineHeight: "1.9",
              fontStyle: "italic",
            }}
          >
            {state.learningArc}
          </p>
        </div>
      </div>

      <SectionDivider />

      {/* ── DEBATES ── */}
      <div className="mb-0 text-center">
        <div className="scroll-reveal">
          <SectionLabel>ADVERSARIAL RECORD</SectionLabel>
          <h2
            className="mb-10"
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "24px",
              color: "#f5f5f5",
              letterSpacing: "0.15em",
            }}
          >
            Debates
          </h2>
        </div>

        <div className="flex flex-col gap-4">
          {stateClaims.map((claim, i) => (
            <DebateCard key={claim.id} claim={claim} index={i} />
          ))}
        </div>
      </div>

      <SectionDivider />

      {/* ── SURVIVING KNOWLEDGE ── */}
      <div className="mb-0 text-center">
        <div className="scroll-reveal">
          <SectionLabel>VAULT</SectionLabel>
          <h2
            className="mb-10"
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "24px",
              color: "#f5f5f5",
              letterSpacing: "0.15em",
            }}
          >
            Surviving Knowledge
          </h2>
        </div>

        {survivingClaims.length === 0 ? (
          <p
            className="scroll-reveal"
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "18px",
              fontWeight: 600,
              color: "#404040",
              fontStyle: "italic",
            }}
          >
            No surviving claims yet.
          </p>
        ) : (
          <div className="flex flex-col gap-6">
            {survivingClaims.map((claim, i) => (
              <div
                key={claim.id}
                className="scroll-reveal mx-auto w-full max-w-2xl rounded-xl px-8 py-6"
                style={{
                  backgroundColor: "#0e0e0e",
                  border: "1px solid #1c1c1c",
                  animationDelay: `${i * 80}ms`,
                }}
              >
                <div className="mb-3 flex items-center justify-center gap-3">
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "12px",
                      color: "#dc2626",
                      fontWeight: 700,
                      letterSpacing: "0.1em",
                    }}
                  >
                    {claim.id}
                  </span>
                  {rulingBadge(claim.ruling)}
                </div>
                <p
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "18px",
                    fontWeight: 600,
                    color: "#e5e5e5",
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

      <SectionDivider />

      {/* ── GRAVEYARD ── */}
      <div className="mb-0 text-center">
        <div className="scroll-reveal">
          <SectionLabel>FALLEN</SectionLabel>
          <h2
            className="mb-10"
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "24px",
              color: "#525252",
              letterSpacing: "0.15em",
            }}
          >
            Graveyard
          </h2>
        </div>

        {destroyedClaims.length === 0 ? (
          <p
            className="scroll-reveal"
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "18px",
              fontWeight: 600,
              color: "#404040",
              fontStyle: "italic",
            }}
          >
            No destroyed claims.
          </p>
        ) : (
          <div className="flex flex-col gap-6">
            {destroyedClaims.map((claim, i) => (
              <div
                key={claim.id}
                className="scroll-reveal mx-auto w-full max-w-2xl rounded-xl px-8 py-6"
                style={{
                  backgroundColor: "#0a0a0a",
                  border: "1px solid #141414",
                  animationDelay: `${i * 80}ms`,
                }}
              >
                <div className="mb-3 flex items-center justify-center gap-3">
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "12px",
                      color: "#404040",
                      fontWeight: 700,
                      letterSpacing: "0.1em",
                    }}
                  >
                    {claim.id}
                  </span>
                  {rulingBadge("DESTROYED")}
                </div>
                <p
                  className="mb-3"
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "17px",
                    fontWeight: 600,
                    color: "#737373",
                    lineHeight: "1.8",
                    textDecoration: "line-through",
                    textDecorationColor: "#dc262640",
                  }}
                >
                  {claim.position}
                </p>
                <p
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "15px",
                    fontWeight: 600,
                    color: "#404040",
                    lineHeight: "1.8",
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

      <div style={{ height: "60px" }} />
    </section>
  );
}
