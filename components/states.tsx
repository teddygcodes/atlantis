"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { STATES, type StateEntity } from "@/lib/data";

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

const DOMAIN_COLORS: Record<string, string> = {
  Consciousness: "#dc2626",
  Causation: "#f59e0b",
  Mathematics: "#3b82f6",
};

const PAIRS = [
  { domain: "CONSCIOUSNESS", a: STATES[0], b: STATES[1] },
  { domain: "CAUSATION", a: STATES[2], b: STATES[3] },
  { domain: "MATHEMATICS", a: STATES[4], b: STATES[5] },
];

export function States() {
  const containerRef = useScrollReveal();

  return (
    <section ref={containerRef}>
      {/* Page header - centered, 64px below nav */}
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
          THE STATES
        </h2>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "16px",
            color: "#a3a3a3",
          }}
        >
          Six entities. Three domains. Each one learning from its failures.
        </p>
      </div>

      {/* 48px gap below subtitle */}
      <div style={{ height: "48px" }} />

      {/* Domain groups */}
      <div className="mx-auto flex max-w-[900px] flex-col px-6">
        {PAIRS.map((pair, pairIdx) => (
          <div key={pair.domain}>
            {/* Domain divider: ——— DOMAIN ——— */}
            <div className="scroll-reveal flex items-center gap-4" style={{ marginBottom: "32px" }}>
              <div className="h-px flex-1" style={{ backgroundColor: "#dc2626", opacity: 0.3 }} />
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "10px",
                  color: "#dc2626",
                  letterSpacing: "0.2em",
                }}
              >
                {pair.domain}
              </span>
              <div className="h-px flex-1" style={{ backgroundColor: "#dc2626", opacity: 0.3 }} />
            </div>

            {/* First rival */}
            <StateCard state={pair.a} index={pairIdx * 2} />

            {/* 16px gap between rivals */}
            <div style={{ height: "16px" }} />

            {/* Second rival */}
            <StateCard state={pair.b} index={pairIdx * 2 + 1} />

            {/* 48px gap between domain groups */}
            {pairIdx < PAIRS.length - 1 && <div style={{ height: "48px" }} />}
          </div>
        ))}
      </div>

      {/* Bottom spacer */}
      <div style={{ height: "80px" }} />
    </section>
  );
}

function StateCard({ state, index }: { state: StateEntity; index: number }) {
  const [revealed, setRevealed] = useState(false);
  const total = state.wins + state.partials + state.losses;
  const survivalPct =
    total > 0 ? Math.round(((state.wins + state.partials) / total) * 100) : 0;
  const slug = state.name.toLowerCase().replace("_", "-");

  return (
    <article
      className="scroll-reveal group relative overflow-hidden"
      style={{
        backgroundColor: "#0e0e0e",
        border: "1px solid #1c1c1c",
        borderRadius: "12px",
        padding: "32px",
        animationDelay: `${index * 0.06}s`,
        transition: "border-color 0.3s ease, box-shadow 0.3s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "rgba(220, 38, 38, 0.3)";
        e.currentTarget.style.boxShadow = "0 8px 32px rgba(220, 38, 38, 0.08)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "#1c1c1c";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      {/* Animated red left border */}
      <div
        className="absolute left-0 top-0 w-[2px] transition-all duration-300 ease-out"
        style={{
          backgroundColor: "#dc2626",
          height: "0%",
          borderRadius: "1px",
        }}
        ref={(el) => {
          if (!el) return;
          const parent = el.parentElement;
          if (!parent) return;
          parent.addEventListener("mouseenter", () => {
            el.style.height = "100%";
          });
          parent.addEventListener("mouseleave", () => {
            el.style.height = "0%";
          });
        }}
      />

      {/* Top row: name/domain left, record/survival right */}
      <div className="flex items-start justify-between">
        {/* Left side */}
        <div>
          <h3
            className="mb-1.5 transition-transform duration-300 group-hover:translate-x-1"
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "24px",
              color: "#e5e5e5",
              letterSpacing: "0.04em",
            }}
          >
            {state.name.replace("_", " ")}
          </h3>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "#dc2626",
              textTransform: "uppercase" as const,
              letterSpacing: "0.15em",
            }}
          >
            {state.domain}
          </span>
        </div>

        {/* Right side: record + survival */}
        <div className="flex flex-col items-end gap-2 pt-1">
          <div className="flex items-center gap-1.5" style={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}>
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
        </div>
      </div>

      {/* Approach quote */}
      <p
        className="mt-5 mb-6"
        style={{
          fontFamily: "var(--font-body)",
          fontSize: "16px",
          fontStyle: "italic",
          color: "#a3a3a3",
          lineHeight: "1.7",
        }}
      >
        &ldquo;{state.approach}&rdquo;
      </p>

      {/* Reveal toggle - bottom right */}
      <div className="flex justify-end">
        <button
          onClick={() => setRevealed(!revealed)}
          className="flex items-center gap-2 transition-colors duration-200"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            color: revealed ? "#dc2626" : "#525252",
            textTransform: "uppercase" as const,
            letterSpacing: "0.2em",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = "#dc2626"; }}
          onMouseLeave={(e) => { if (!revealed) e.currentTarget.style.color = "#525252"; }}
        >
          {revealed ? "COLLAPSE" : "REVEAL FULL STORY"}
          <span
            className="inline-block transition-transform duration-300"
            style={{
              transform: revealed ? "rotate(180deg)" : "rotate(0deg)",
            }}
          >
            &#8595;
          </span>
        </button>
      </div>

      {/* Expanded: Learning Arc + profile link */}
      <div
        className="grid transition-all duration-500 ease-out"
        style={{
          gridTemplateRows: revealed ? "1fr" : "0fr",
          opacity: revealed ? 1 : 0,
        }}
      >
        <div className="overflow-hidden">
          <div style={{ paddingTop: "24px" }}>
            <div className="mb-4 h-px w-full" style={{ backgroundColor: "#1c1c1c" }} />
            <span
              className="mb-3 block"
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "9px",
                color: "#dc2626",
                textTransform: "uppercase" as const,
                letterSpacing: "0.25em",
              }}
            >
              Learning Arc
            </span>
            <p
              className="mb-6"
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "16px",
                color: "#a3a3a3",
                lineHeight: "1.9",
              }}
            >
              {state.learningArc}
            </p>
            <Link
              href={`/states/${slug}`}
              className="inline-flex items-center gap-2"
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "10px",
                color: "#dc2626",
                textTransform: "uppercase" as const,
                letterSpacing: "0.2em",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = "#dc2626"; }}
            >
              VIEW FULL PROFILE
              <span>&rarr;</span>
            </Link>
          </div>
        </div>
      </div>
    </article>
  );
}
