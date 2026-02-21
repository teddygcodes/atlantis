"use client";

import { useState, useEffect, useRef } from "react";
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

export function States() {
  const containerRef = useScrollReveal();

  return (
    <section ref={containerRef}>
      {/* Header */}
      <div className="scroll-reveal mx-auto mb-20 text-center">
        <h2
          className="mb-4 text-3xl tracking-[0.25em] text-foreground md:text-4xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          THE STATES
        </h2>
        <p
          className="text-lg text-muted"
          style={{ fontFamily: "var(--font-cormorant)", fontSize: "18px", color: "#a3a3a3" }}
        >
          Six entities. Three domains. Each one learning from its failures.
        </p>
      </div>

      {/* 2-column card grid */}
      <div className="mx-auto grid max-w-[900px] grid-cols-1 gap-5 md:grid-cols-2">
        {STATES.map((state, index) => (
          <StateCard key={state.name} state={state} index={index} />
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

  return (
    <article
      className="scroll-reveal group relative overflow-hidden rounded-xl border transition-all duration-300"
      style={{
        backgroundColor: "#0e0e0e",
        borderColor: "#1c1c1c",
        animationDelay: `${index * 0.1}s`,
      }}
    >
      {/* Red left border on hover */}
      <div
        className="absolute left-0 top-0 h-0 w-[2px] transition-all duration-300 ease-out group-hover:h-full"
        style={{ backgroundColor: "#dc2626" }}
      />

      <div className="p-8">
        {/* Name + domain */}
        <div className="mb-5">
          <h3
            className="mb-2 transition-transform duration-300 group-hover:translate-x-1"
            style={{
              fontFamily: "var(--font-cinzel)",
              fontSize: "22px",
              color: "#e5e5e5",
            }}
          >
            {state.name.replace("_", " ")}
          </h3>
          <span
            className="text-[11px] uppercase tracking-[0.2em]"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              color: domainColor,
            }}
          >
            {state.domain}
          </span>
        </div>

        {/* Approach as quote */}
        <p
          className="mb-6 italic leading-relaxed"
          style={{
            fontFamily: "var(--font-cormorant)",
            fontSize: "15px",
            color: "#a3a3a3",
          }}
        >
          &ldquo;{state.approach}&rdquo;
        </p>

        {/* Record + survival */}
        <div className="mb-6 flex items-center justify-between">
          <div
            className="flex items-center gap-1.5 text-xs"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            <span className="text-[#a3a3a3]">W</span>
            <span className="text-emerald-500">{state.wins}</span>
            <span className="text-[#404040]">/</span>
            <span className="text-[#a3a3a3]">P</span>
            <span className="text-amber-500">{state.partials}</span>
            <span className="text-[#404040]">/</span>
            <span className="text-[#a3a3a3]">L</span>
            <span className="text-[#737373]">{state.losses}</span>
          </div>
          <span
            className="text-sm font-medium"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              color: "#dc2626",
            }}
          >
            {survivalPct}%
          </span>
        </div>

        {/* Reveal toggle */}
        <button
          onClick={() => setRevealed(!revealed)}
          className="text-[10px] uppercase tracking-[0.25em] transition-colors duration-200 hover:text-foreground"
          style={{
            fontFamily: "var(--font-ibm-plex-mono)",
            color: "#525252",
          }}
        >
          {revealed ? "Hide story" : "Reveal full story"}
        </button>

        {/* Expanded learning arc */}
        <div
          className="grid transition-all duration-500 ease-out"
          style={{
            gridTemplateRows: revealed ? "1fr" : "0fr",
            opacity: revealed ? 1 : 0,
          }}
        >
          <div className="overflow-hidden">
            <div className="pt-6">
              <div
                className="mb-3 h-px w-full"
                style={{ backgroundColor: "#1c1c1c" }}
              />
              <span
                className="mb-3 block text-[9px] uppercase tracking-[0.25em]"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: "#dc2626",
                }}
              >
                Learning Arc
              </span>
              <p
                className="leading-[1.9]"
                style={{
                  fontFamily: "var(--font-cormorant)",
                  fontSize: "16px",
                  color: "#a3a3a3",
                }}
              >
                {state.learningArc}
              </p>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
