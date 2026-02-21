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
      { threshold: 0.1, rootMargin: "0px 0px -60px 0px" }
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

const DOMAIN_ICONS: Record<string, string> = {
  Consciousness: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z",
  Causation: "M12 2L2 19h20L12 2zm0 3.5L18.5 17H5.5L12 5.5z",
  Mathematics: "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z",
};

function getInitials(name: string) {
  const parts = name.split("_");
  return parts.map((p) => p[0]).join("");
}

export function States() {
  const containerRef = useScrollReveal();

  return (
    <section ref={containerRef}>
      {/* Header */}
      <div className="scroll-reveal mx-auto mb-20 max-w-[800px]">
        <div className="mb-6 flex items-center gap-4">
          <h2
            className="text-sm uppercase tracking-[0.3em] text-foreground"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            The States
          </h2>
          <div className="h-px flex-1 bg-accent/20" />
        </div>
        <p
          className="text-xl leading-[1.9] text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          Six entities. Three domains. Each one learning from its failures,
          adapting its arguments, fighting to survive.
        </p>
      </div>

      {/* Portrait grid */}
      <div className="mx-auto max-w-[1000px] flex flex-col gap-0">
        {STATES.map((state, index) => (
          <StatePortrait key={state.name} state={state} index={index} />
        ))}
      </div>
    </section>
  );
}

function StatePortrait({
  state,
  index,
}: {
  state: StateEntity;
  index: number;
}) {
  const [revealed, setRevealed] = useState(false);
  const total = state.wins + state.partials + state.losses;
  const survivalPct =
    total > 0 ? Math.round(((state.wins + state.partials) / total) * 100) : 0;
  const color = DOMAIN_COLORS[state.domain] || "#dc2626";
  const isEven = index % 2 === 0;

  return (
    <article
      className="scroll-reveal group border-b border-border/50 py-12 first:pt-0 last:border-b-0 md:py-16"
    >
      <div
        className={`flex flex-col gap-8 md:flex-row md:items-start md:gap-16 ${
          isEven ? "" : "md:flex-row-reverse"
        }`}
      >
        {/* Portrait / Avatar area */}
        <div className="flex flex-col items-center gap-4 md:w-48 md:flex-shrink-0">
          <div
            className="flex h-24 w-24 items-center justify-center rounded-full border transition-all duration-500 group-hover:shadow-[0_0_30px_rgba(220,38,38,0.1)]"
            style={{ borderColor: `${color}30` }}
          >
            <span
              className="text-2xl tracking-wider"
              style={{
                fontFamily: "var(--font-cinzel)",
                color,
              }}
            >
              {getInitials(state.name)}
            </span>
          </div>
          <div
            className="text-[9px] uppercase tracking-[0.2em]"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              color,
            }}
          >
            {state.domain}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1">
          <h3
            className="mb-4 text-2xl tracking-wide text-foreground md:text-3xl"
            style={{ fontFamily: "var(--font-cinzel)" }}
          >
            {state.name.replace("_", " ")}
          </h3>

          {/* Approach as a quote */}
          <blockquote
            className="mb-8 border-l-2 pl-6 text-xl italic leading-[1.9] text-muted"
            style={{
              fontFamily: "var(--font-cormorant)",
              borderColor: `${color}40`,
            }}
          >
            &ldquo;{state.approach}&rdquo;
          </blockquote>

          {/* Stats row */}
          <div className="mb-6 flex items-center gap-6">
            <div
              className="flex items-center gap-2 text-xs"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              <span className="text-emerald-500">W {state.wins}</span>
              <span className="text-muted/30">/</span>
              <span className="text-amber-500">P {state.partials}</span>
              <span className="text-muted/30">/</span>
              <span className="text-red-400">L {state.losses}</span>
            </div>
            <div className="h-px flex-1 bg-border" />
            <span
              className="text-xs text-muted/60"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {survivalPct}% survival
            </span>
          </div>

          {/* Survival bar */}
          <div className="mb-8 h-px w-full overflow-hidden bg-border">
            <div
              className="h-full transition-all duration-1000"
              style={{ width: `${survivalPct}%`, backgroundColor: color }}
            />
          </div>

          {/* Reveal toggle */}
          <button
            onClick={() => setRevealed(!revealed)}
            className="text-[10px] uppercase tracking-[0.25em] text-muted/50 transition-colors hover:text-foreground"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            {revealed ? "Hide story" : "Reveal full story"}
          </button>

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
                <span
                  className="mb-3 block text-[9px] uppercase tracking-[0.25em] text-accent"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  Learning Arc
                </span>
                <p
                  className="text-lg leading-[1.9] text-muted"
                  style={{ fontFamily: "var(--font-cormorant)" }}
                >
                  {state.learningArc}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
