"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { STATES, HYPOTHESES, type StateEntity, type Hypothesis } from "@/lib/data";
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

function DebateCard({ claim, index }: { claim: Hypothesis; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="scroll-reveal w-full max-w-2xl"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-center transition-colors duration-300"
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
              color: "#a3a3a3",
              letterSpacing: "0.1em",
            }}
          >
            CYCLE {claim.cycle}
          </span>
          {rulingBadge(claim.ruling)}
        </div>

        {/* Hypothesis text */}
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "18px",
            fontWeight: 600,
            color: claim.ruling === "DESTROYED" ? "#a3a3a3" : "#f5f5f5",
            lineHeight: "1.8",
            textDecoration: claim.ruling === "DESTROYED" ? "line-through" : "none",
            textDecorationColor: "#dc262640",
            textAlign: "center",
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
            className="mx-4 mb-2 flex flex-col gap-8 rounded-b-xl px-6 pb-8 pt-6 text-center md:mx-8 md:px-10"
            style={{
              backgroundColor: "#0a0a0a",
              borderLeft: "1px solid #1c1c1c",
              borderRight: "1px solid #1c1c1c",
              borderBottom: "1px solid #1c1c1c",
            }}
          >
            {/* Challenge */}
            <div>
              <SectionLabel>CHALLENGE</SectionLabel>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "17px",
                  fontWeight: 600,
                  color: "#e5e5e5",
                  lineHeight: "1.9",
                  textAlign: "center",
                }}
              >
                {claim.challenge}
              </p>
            </div>

            <div className="mx-auto h-px w-16" style={{ backgroundColor: "#1c1c1c" }} />

            {/* Rebuttal */}
            <div>
              <SectionLabel>REBUTTAL</SectionLabel>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "17px",
                  fontWeight: 600,
                  color: "#e5e5e5",
                  lineHeight: "1.9",
                  textAlign: "center",
                }}
              >
                {claim.rebuttal}
              </p>
            </div>

            <div className="mx-auto h-px w-16" style={{ backgroundColor: "#1c1c1c" }} />

            {/* Verdict */}
            <div>
              <SectionLabel>VERDICT</SectionLabel>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "17px",
                  fontWeight: 600,
                  color: "#f5f5f5",
                  lineHeight: "1.9",
                  textAlign: "center",
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
                      color: "#a3a3a3",
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
        <p style={{ fontFamily: "var(--font-body)", fontSize: "22px", color: "#a3a3a3" }}>
          State not found.
        </p>
      </div>
    );
  }

  const stateHypotheses = HYPOTHESES.filter((c) => c.state === state.name);
  const validatedHypotheses = stateHypotheses.filter(
    (c) => c.ruling === "REVISE" || c.ruling === "PARTIAL"
  );
  const refutedHypotheses = stateHypotheses.filter((c) => c.ruling === "DESTROYED");
  const latestHypothesis = stateHypotheses.reduce(
    (a, b) => (a.cycle > b.cycle ? a : b),
    stateHypotheses[0]
  );

  const total = state.wins + state.partials + state.losses;
  const survivalPct =
    total > 0 ? Math.round(((state.wins + state.partials) / total) * 100) : 0;

  let tier = "IRON";
  if (survivalPct >= 80) tier = "GOLD";
  else if (survivalPct >= 60) tier = "SILVER";
  else if (survivalPct >= 40) tier = "BRONZE";

  const hypothesesByCycle = [1, 2, 3].map((cycle) =>
    stateHypotheses.filter((c) => c.cycle === cycle)
  );

  return (
    <div style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
    <section ref={containerRef} style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", width: "100%" }}>
      {/* ── HERO ZONE ── */}
      <div className="scroll-reveal mb-6 text-center">
        <Link
          href="/states"
          className="inline-flex items-center gap-2 transition-opacity duration-200 hover:opacity-60"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            color: "#a3a3a3",
            letterSpacing: "0.2em",
          }}
        >
          &larr; ALL STATES
        </Link>
      </div>

      {/* State identity */}
      <div className="scroll-reveal mb-6" style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            color: "#dc2626",
            letterSpacing: "0.3em",
            marginBottom: "16px",
            textAlign: "center",
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
            textAlign: "center",
            width: "100%",
          }}
        >
          {state.name.replace("_", " ")}
        </h1>
      </div>

      {/* Approach quote */}
      <div className="scroll-reveal mb-8" style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "20px",
            fontWeight: 600,
            fontStyle: "italic",
            color: "#a3a3a3",
            lineHeight: "1.8",
            textAlign: "center",
            maxWidth: "36rem",
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
                color: "#a3a3a3",
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
              color: "#a3a3a3",
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
                    : "#a3a3a3",
            fontWeight: 700,
          }}
        >
          {tier}
        </span>
      </div>

      <SectionDivider />

      {/* ── CURRENT RESEARCH ── */}
      <div className="scroll-reveal mb-0" style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", width: "100%" }}>
        <SectionLabel>CURRENT FOCUS</SectionLabel>
        <h2
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "24px",
            color: "#f5f5f5",
            letterSpacing: "0.15em",
            marginBottom: "24px",
            textAlign: "center",
          }}
        >
          Active Research
        </h2>
        <div
          style={{
            backgroundColor: "#0e0e0e",
            border: "1px solid #dc262625",
            borderRadius: "12px",
            padding: "32px",
            maxWidth: "42rem",
            width: "100%",
            textAlign: "center",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "12px", marginBottom: "12px" }}>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "12px",
                color: "#dc2626",
                fontWeight: 700,
                letterSpacing: "0.1em",
              }}
            >
              {latestHypothesis.id}
            </span>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                color: "#8a8a8a",
                letterSpacing: "0.1em",
              }}
            >
              CYCLE {latestHypothesis.cycle}
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "20px",
              fontWeight: 600,
              color: "#f5f5f5",
              lineHeight: "1.8",
              textAlign: "center",
            }}
          >
            {latestHypothesis.position}
          </p>
        </div>
      </div>

      <SectionDivider />

      {/* ── KNOWLEDGE GRAPH ── */}
      <div className="scroll-reveal mb-0" style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <SectionLabel>NETWORK</SectionLabel>
        <h2
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "24px",
            color: "#f5f5f5",
            letterSpacing: "0.15em",
            marginBottom: "32px",
            textAlign: "center",
          }}
        >
          Knowledge Graph
        </h2>
        <KnowledgeGraph stateName={state.name} stateClaims={stateHypotheses} />
      </div>

      <SectionDivider />

      {/* ── LEARNING ARC ── */}
      <div className="scroll-reveal mb-0" style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <SectionLabel>EVOLUTION</SectionLabel>
        <h2
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "24px",
            color: "#f5f5f5",
            letterSpacing: "0.15em",
            marginBottom: "40px",
            textAlign: "center",
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

          {hypothesesByCycle.map((cycleHypotheses, idx) => {
            if (cycleHypotheses.length === 0) return null;
            const claim = cycleHypotheses[0];
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
                        color: claim.ruling === "DESTROYED" ? "#a3a3a3" : "#fff",
                        fontWeight: 700,
                      }}
                    >
                      {idx + 1}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="mx-auto w-full pt-14 text-center">
                  <div className="mb-2 flex items-center justify-center gap-3">
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "11px",
                        color: "#a3a3a3",
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
                      color: claim.ruling === "DESTROYED" ? "#b3b3b3" : "#e5e5e5",
                      lineHeight: "1.8",
                      textDecoration:
                        claim.ruling === "DESTROYED" ? "line-through" : "none",
                      textDecorationColor: "#dc262640",
                      textAlign: "center",
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
        <div className="mx-auto mt-12 max-w-2xl text-center">
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "18px",
              fontWeight: 600,
              color: "#d4d4d4",
              lineHeight: "1.9",
              fontStyle: "italic",
              textAlign: "center",
            }}
          >
            {state.learningArc}
          </p>
        </div>
      </div>

      <SectionDivider />

      {/* ── DEBATES ── */}
      <div className="mb-0" style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div className="scroll-reveal" style={{ textAlign: "center", width: "100%" }}>
          <SectionLabel>ADVERSARIAL RECORD</SectionLabel>
          <h2
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "24px",
              color: "#f5f5f5",
              letterSpacing: "0.15em",
              marginBottom: "40px",
              textAlign: "center",
            }}
          >
            Debates
          </h2>
        </div>

        <div className="flex flex-col items-center gap-4">
          {stateHypotheses.map((hypothesis, i) => (
            <DebateCard key={hypothesis.id} claim={hypothesis} index={i} />
          ))}
        </div>
      </div>

      <SectionDivider />

      {/* ── SURVIVING KNOWLEDGE ── */}
      <div className="mb-0" style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div className="scroll-reveal" style={{ textAlign: "center", width: "100%" }}>
          <SectionLabel>KNOWLEDGE BASE</SectionLabel>
          <h2
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "24px",
              color: "#f5f5f5",
              letterSpacing: "0.15em",
              marginBottom: "40px",
              textAlign: "center",
            }}
          >
            Validated Hypotheses
          </h2>
        </div>

        {validatedHypotheses.length === 0 ? (
          <p
            className="scroll-reveal"
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "18px",
              fontWeight: 600,
              color: "#8a8a8a",
              fontStyle: "italic",
            }}
          >
            No validated hypotheses yet.
          </p>
        ) : (
          <div className="flex flex-col items-center gap-6">
            {validatedHypotheses.map((claim, i) => (
              <div
                key={claim.id}
                className="scroll-reveal mx-auto w-full max-w-2xl rounded-xl px-8 py-6 text-center"
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
                    textAlign: "center",
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
      <div className="mb-0" style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div className="scroll-reveal" style={{ textAlign: "center", width: "100%" }}>
          <SectionLabel>REFUTED</SectionLabel>
          <h2
            style={{
              fontFamily: "var(--font-serif)",
              marginBottom: "40px",
              textAlign: "center",
              fontSize: "24px",
              color: "#a3a3a3",
              letterSpacing: "0.15em",
            }}
          >
            Refuted Hypotheses
          </h2>
        </div>

        {refutedHypotheses.length === 0 ? (
          <p
            className="scroll-reveal"
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "18px",
              fontWeight: 600,
              color: "#8a8a8a",
              fontStyle: "italic",
            }}
          >
            No refuted hypotheses.
          </p>
        ) : (
          <div className="flex flex-col items-center gap-6">
            {refutedHypotheses.map((claim, i) => (
              <div
                key={claim.id}
                className="scroll-reveal mx-auto w-full max-w-2xl rounded-xl px-8 py-6 text-center"
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
                      color: "#8a8a8a",
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
                    color: "#b3b3b3",
                    lineHeight: "1.8",
                    textDecoration: "line-through",
                    textDecorationColor: "#dc262640",
                    textAlign: "center",
                  }}
                >
                  {claim.position}
                </p>
                <p
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "15px",
                    fontWeight: 600,
                    color: "#8a8a8a",
                    lineHeight: "1.8",
                    fontStyle: "italic",
                    textAlign: "center",
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
    </div>
  );
}
