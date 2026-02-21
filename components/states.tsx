"use client";

import { useEffect, useRef } from "react";
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
            fontSize: "18px",
            fontWeight: 600,
            color: "#d4d4d4",
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
  const total = state.wins + state.partials + state.losses;
  const survivalPct =
    total > 0 ? Math.round(((state.wins + state.partials) / total) * 100) : 0;
  const slug = state.name.toLowerCase().replace("_", "-");

  return (
    <Link
      href={`/states/${slug}`}
      className="scroll-reveal group relative block cursor-pointer overflow-hidden"
      style={{
        backgroundColor: "#0e0e0e",
        border: "1px solid #1c1c1c",
        borderRadius: "12px",
        padding: "32px",
        animationDelay: `${index * 0.06}s`,
        transition: "border-color 0.3s ease, box-shadow 0.3s ease",
        textDecoration: "none",
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
      {/* State name */}
      <div className="text-center">
        <h3
          className="mb-2"
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
            fontSize: "11px",
            color: "#dc2626",
            textTransform: "uppercase" as const,
            letterSpacing: "0.15em",
          }}
        >
          {state.domain}
        </span>
      </div>

      {/* Record + survival - centered */}
      <div className="mt-5 flex flex-col items-center gap-2">
        <div className="flex items-center gap-2" style={{ fontFamily: "var(--font-mono)", fontSize: "13px" }}>
          <span style={{ color: "#a3a3a3" }}>W</span>
          <span style={{ color: "#22c55e" }}>{state.wins}</span>
          <span style={{ color: "#4a4a4a" }}>/</span>
          <span style={{ color: "#a3a3a3" }}>P</span>
          <span style={{ color: "#f59e0b" }}>{state.partials}</span>
          <span style={{ color: "#4a4a4a" }}>/</span>
          <span style={{ color: "#a3a3a3" }}>L</span>
          <span style={{ color: "#b3b3b3" }}>{state.losses}</span>
        </div>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "14px",
            color: "#dc2626",
            fontWeight: 500,
          }}
        >
          {survivalPct}% survival
        </span>
      </div>

      {/* Approach quote - centered */}
      <p
        className="mt-5 mb-6 text-center"
        style={{
          fontFamily: "var(--font-body)",
          fontSize: "17px",
          fontWeight: 600,
          fontStyle: "italic",
          color: "#d4d4d4",
          lineHeight: "1.7",
        }}
      >
        &ldquo;{state.approach}&rdquo;
      </p>

      {/* View State link - centered */}
      <div className="flex justify-center">
        <span
          className="inline-flex items-center gap-2 transition-colors duration-200 group-hover:text-red-500"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            color: "#a3a3a3",
            textTransform: "uppercase" as const,
            letterSpacing: "0.2em",
          }}
        >
          VIEW STATE
          <span className="transition-transform duration-300 group-hover:translate-x-1">&rarr;</span>
        </span>
      </div>
    </Link>
  );
}
