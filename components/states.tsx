"use client";

import { useState } from "react";
import { STATES, type StateEntity } from "@/lib/data";
import { ChevronDown } from "lucide-react";

export function States() {
  return (
    <section>
      <header className="mb-16 animate-fade-in-up">
        <h1
          className="mb-4 text-4xl tracking-[0.2em] text-foreground md:text-5xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          States
        </h1>
        <p
          className="max-w-2xl text-xl leading-relaxed text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          Six entities. Three domains. Each one learning from its failures,
          adapting its arguments, fighting to survive.
        </p>
      </header>

      <div className="grid gap-6 md:grid-cols-2">
        {STATES.map((state, index) => (
          <StateCard
            key={state.name}
            state={state}
            index={index}
          />
        ))}
      </div>
    </section>
  );
}

function StateCard({ state, index }: { state: StateEntity; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const total = state.wins + state.partials + state.losses;
  const survivalPct =
    total > 0
      ? Math.round(((state.wins + state.partials) / total) * 100)
      : 0;

  return (
    <article
      className={`animate-fade-in-up animation-delay-${((index % 4) + 1) * 100} group cursor-pointer rounded border border-border bg-surface transition-colors hover:border-accent/30`}
      onClick={() => setExpanded(!expanded)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setExpanded(!expanded);
        }
      }}
      aria-expanded={expanded}
    >
      <div className="p-6">
        <div className="mb-3 flex items-start justify-between">
          <h3
            className="text-sm font-bold tracking-wide text-foreground"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            {state.name}
          </h3>
          <span
            className="rounded bg-accent/10 px-2 py-0.5 text-xs text-accent"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            {state.domain}
          </span>
        </div>

        <p
          className="mb-4 line-clamp-2 text-base leading-relaxed text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          {state.approach}
        </p>

        <div className="mb-3 flex items-center gap-4">
          <div
            className="flex items-center gap-3 text-xs"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            <span className="text-emerald-500">
              W {state.wins}
            </span>
            <span className="text-amber-500">
              P {state.partials}
            </span>
            <span className="text-red-400">
              L {state.losses}
            </span>
          </div>
          <div
            className="ml-auto text-xs text-muted"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            {survivalPct}% survival
          </div>
        </div>

        {/* Survival bar */}
        <div className="mb-2 h-1 w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full bg-accent transition-all duration-500"
            style={{ width: `${survivalPct}%` }}
          />
        </div>

        <div className="flex items-center justify-center pt-2">
          <ChevronDown
            className={`h-4 w-4 text-muted transition-transform duration-300 ${expanded ? "rotate-180" : ""}`}
          />
        </div>
      </div>

      {expanded && (
        <div className="border-t border-border bg-background px-6 py-5">
          <span
            className="mb-3 block text-xs tracking-[0.2em] text-accent"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            LEARNING ARC
          </span>
          <p
            className="text-base leading-relaxed text-muted"
            style={{ fontFamily: "var(--font-cormorant)" }}
          >
            {state.learningArc}
          </p>
        </div>
      )}
    </article>
  );
}
