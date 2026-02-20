"use client";

import { useState } from "react";
import { CLAIMS, type Claim } from "@/lib/data";

const CYCLE_FILTERS = [1, 2, 3] as const;

export function Debates() {
  const [activeCycle, setActiveCycle] = useState<number>(1);

  const filteredClaims = CLAIMS.filter((c) => c.cycle === activeCycle);

  return (
    <section>
      <header className="mb-12 animate-fade-in-up">
        <h1
          className="mb-4 text-4xl tracking-[0.2em] text-foreground md:text-5xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          Debates
        </h1>
        <p
          className="max-w-2xl text-xl leading-relaxed text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          Every claim. Every challenge. Every verdict. The full adversarial
          record.
        </p>
      </header>

      {/* Cycle filter tabs */}
      <div className="mb-10 flex gap-1 border-b border-border">
        {CYCLE_FILTERS.map((cycle) => (
          <button
            key={cycle}
            onClick={() => setActiveCycle(cycle)}
            className={`px-4 py-3 text-sm transition-colors ${
              activeCycle === cycle
                ? "border-b-2 border-accent font-semibold text-foreground"
                : "text-muted hover:text-foreground"
            }`}
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            Cycle {cycle}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-6">
        {filteredClaims.map((claim, index) => (
          <DebateCard key={claim.id} claim={claim} index={index} />
        ))}
      </div>
    </section>
  );
}

function DebateCard({ claim, index }: { claim: Claim; index: number }) {
  const isAlive = claim.ruling !== "DESTROYED";

  return (
    <article
      className={`animate-fade-in-up animation-delay-${((index % 5) + 1) * 100} overflow-hidden rounded border border-border bg-surface`}
    >
      {/* Colored left border accent */}
      <div className="flex">
        <div
          className={`w-1 shrink-0 ${isAlive ? "bg-accent" : "bg-destroyed"}`}
        />

        <div className="flex-1 p-6">
          {/* Header */}
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <span
              className="text-sm font-bold text-accent"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {claim.id}
            </span>
            <span
              className={`rounded px-2 py-0.5 text-xs font-medium ${
                claim.ruling === "DESTROYED"
                  ? "bg-destroyed/20 text-destroyed"
                  : claim.ruling === "REVISE"
                    ? "bg-accent/10 text-accent"
                    : "bg-amber-500/10 text-amber-500"
              }`}
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {claim.ruling}
            </span>
            <span
              className="text-xs text-muted"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {claim.domain} &middot; {claim.state}
            </span>
          </div>

          {/* Position */}
          <p
            className="mb-6 text-lg leading-relaxed text-foreground"
            style={{ fontFamily: "var(--font-cormorant)" }}
          >
            {claim.position}
          </p>

          {/* Challenge and Rebuttal grid */}
          <div className="mb-4 grid gap-4 md:grid-cols-2">
            <div className="rounded bg-background px-5 py-4">
              <span
                className="mb-2 block text-xs tracking-[0.15em] text-muted"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                CHALLENGE
              </span>
              <p
                className="text-base leading-relaxed text-foreground/80"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.challenge}
              </p>
            </div>
            <div className="rounded bg-background px-5 py-4">
              <span
                className="mb-2 block text-xs tracking-[0.15em] text-muted"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                REBUTTAL
              </span>
              <p
                className="text-base leading-relaxed text-foreground/80"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.rebuttal}
              </p>
            </div>
          </div>

          {/* Verdict */}
          <div className="rounded border border-accent/10 bg-accent/5 px-5 py-4">
            <span
              className="mb-2 block text-xs tracking-[0.15em] text-accent"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              VERDICT
            </span>
            <p
              className="text-base leading-relaxed text-foreground/90"
              style={{ fontFamily: "var(--font-cormorant)" }}
            >
              {claim.verdict}
            </p>
          </div>
        </div>
      </div>
    </article>
  );
}
