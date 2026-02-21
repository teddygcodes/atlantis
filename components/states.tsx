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

// Group states into rival pairs by domain
const PAIRS = [
  { domain: "Consciousness", a: STATES[0], b: STATES[1] },
  { domain: "Causation", a: STATES[2], b: STATES[3] },
  { domain: "Mathematics", a: STATES[4], b: STATES[5] },
];

export function States() {
  const containerRef = useScrollReveal();

  return (
    <section ref={containerRef}>
      {/* Header */}
      <div className="scroll-reveal mx-auto mb-24 text-center">
        <h2
          className="mb-5 tracking-[0.25em] text-foreground"
          style={{ fontFamily: "var(--font-cinzel)", fontSize: "36px" }}
        >
          THE STATES
        </h2>
        <p
          className="text-lg"
          style={{
            fontFamily: "var(--font-cormorant)",
            fontSize: "19px",
            color: "#a3a3a3",
          }}
        >
          Six entities. Three domains. Each one learning from its failures.
        </p>
      </div>

      {/* State pairs */}
      <div className="mx-auto flex max-w-[900px] flex-col gap-16">
        {PAIRS.map((pair, pairIdx) => (
          <div key={pair.domain} className="flex flex-col gap-6">
            {/* Domain label */}
            <div className="scroll-reveal mb-2 text-center">
              <span
                className="text-[10px] uppercase tracking-[0.35em]"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: DOMAIN_COLORS[pair.domain],
                }}
              >
                {pair.domain} Domain
              </span>
            </div>

            <StateCard state={pair.a} index={pairIdx * 2} />

            {/* Red rival divider */}
            <div className="flex items-center gap-4 px-8">
              <div className="h-px flex-1" style={{ backgroundColor: "rgba(220, 38, 38, 0.2)" }} />
              <span
                className="text-[9px] uppercase tracking-[0.3em]"
                style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "rgba(220, 38, 38, 0.4)" }}
              >
                vs
              </span>
              <div className="h-px flex-1" style={{ backgroundColor: "rgba(220, 38, 38, 0.2)" }} />
            </div>

            <StateCard state={pair.b} index={pairIdx * 2 + 1} />

            {/* Separator between domain pairs */}
            {pairIdx < PAIRS.length - 1 && (
              <div className="mt-10 h-px w-full" style={{ backgroundColor: "#1a1a1a" }} />
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function StateCard({ state, index }: { state: StateEntity; index: number }) {
  const [revealed, setRevealed] = useState(false);
  const total = state.wins + state.partials + state.losses;
  const survivalPct =
    total > 0 ? Math.round(((state.wins + state.partials) / total) * 100) : 0;
  const domainColor = DOMAIN_COLORS[state.domain] || "#dc2626";
  const slug = state.name.toLowerCase().replace("_", "-");

  return (
    <article
      className="scroll-reveal section-door group relative overflow-hidden rounded-xl border"
      style={{
        backgroundColor: "#0e0e0e",
        borderColor: "#1c1c1c",
        animationDelay: `${index * 0.08}s`,
      }}
    >
      {/* Red left border on hover */}
      <div
        className="absolute left-0 top-0 h-0 w-[2px] transition-all duration-300 ease-out group-hover:h-full"
        style={{ backgroundColor: "#dc2626" }}
      />

      <div className="p-8">
        {/* Top row: name + stats */}
        <div className="mb-5 flex items-start justify-between">
          <div>
            <h3
              className="mb-1.5 transition-transform duration-300 group-hover:translate-x-1"
              style={{
                fontFamily: "var(--font-cinzel)",
                fontSize: "28px",
                color: "#e5e5e5",
                letterSpacing: "0.05em",
              }}
            >
              {state.name.replace("_", " ")}
            </h3>
            <span
              className="text-[10px] uppercase tracking-[0.2em]"
              style={{
                fontFamily: "var(--font-ibm-plex-mono)",
                color: domainColor,
              }}
            >
              {state.domain}
            </span>
          </div>

          {/* Record + survival on right */}
          <div className="flex flex-col items-end gap-1.5 pt-1">
            <div
              className="flex items-center gap-1.5 text-xs"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              <span style={{ color: "#737373" }}>W</span>
              <span className="text-emerald-500">{state.wins}</span>
              <span style={{ color: "#2a2a2a" }}>/</span>
              <span style={{ color: "#737373" }}>P</span>
              <span className="text-amber-500">{state.partials}</span>
              <span style={{ color: "#2a2a2a" }}>/</span>
              <span style={{ color: "#737373" }}>L</span>
              <span style={{ color: "#525252" }}>{state.losses}</span>
            </div>
            <span
              className="text-sm font-medium"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#dc2626" }}
            >
              {survivalPct}% survival
            </span>
          </div>
        </div>

        {/* Approach quote */}
        <p
          className="mb-6 italic leading-relaxed"
          style={{
            fontFamily: "var(--font-cormorant)",
            fontSize: "17px",
            color: "#a3a3a3",
            lineHeight: "1.7",
          }}
        >
          &ldquo;{state.approach}&rdquo;
        </p>

        {/* Reveal toggle */}
        <div className="flex justify-end">
          <button
            onClick={() => setRevealed(!revealed)}
            className="flex items-center gap-2 text-[10px] uppercase tracking-[0.25em] transition-colors duration-200 hover:text-foreground"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              color: revealed ? "#dc2626" : "#525252",
            }}
          >
            {revealed ? "Collapse" : "Reveal full story"}
            <span
              className="inline-block transition-transform duration-300"
              style={{ transform: revealed ? "rotate(180deg)" : "rotate(0deg)" }}
            >
              &#8595;
            </span>
          </button>
        </div>

        {/* Expanded content */}
        <div
          className="grid transition-all duration-500 ease-out"
          style={{
            gridTemplateRows: revealed ? "1fr" : "0fr",
            opacity: revealed ? 1 : 0,
          }}
        >
          <div className="overflow-hidden">
            <div className="pt-6">
              <div className="mb-4 h-px w-full" style={{ backgroundColor: "#1c1c1c" }} />
              <span
                className="mb-3 block text-[9px] uppercase tracking-[0.25em]"
                style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#dc2626" }}
              >
                Learning Arc
              </span>
              <p
                className="mb-6 leading-[1.9]"
                style={{
                  fontFamily: "var(--font-cormorant)",
                  fontSize: "17px",
                  color: "#a3a3a3",
                }}
              >
                {state.learningArc}
              </p>
              <Link
                href={`/states/${slug}`}
                className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.25em] transition-colors duration-200 hover:text-foreground"
                style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#dc2626" }}
              >
                View full profile
                <span className="transition-transform duration-200 hover:translate-x-1">&rarr;</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
