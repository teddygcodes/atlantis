"use client";

import { useState } from "react";
import { CLAIMS, type Claim } from "@/lib/data";
import { ChevronDown } from "lucide-react";

const DOMAIN_FILTERS = ["All", "Consciousness", "Causation", "Mathematics"] as const;
type DomainFilter = (typeof DOMAIN_FILTERS)[number];

export function Archive() {
  const [filter, setFilter] = useState<DomainFilter>("All");

  const survivingClaims = CLAIMS.filter(
    (c) => c.ruling === "REVISE" || c.ruling === "PARTIAL"
  );

  const filteredClaims =
    filter === "All"
      ? survivingClaims
      : survivingClaims.filter((c) => c.domain === filter);

  return (
    <section>
      <header className="mb-12 animate-fade-in-up">
        <h1
          className="mb-4 text-4xl tracking-[0.2em] text-foreground md:text-5xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          Archive
        </h1>
        <p
          className="max-w-2xl text-xl leading-relaxed text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          The surviving claims. Each one has withstood adversarial challenge and
          earned its place.
        </p>
      </header>

      {/* Domain filter tabs */}
      <div className="mb-10 flex gap-1 border-b border-border">
        {DOMAIN_FILTERS.map((d) => (
          <button
            key={d}
            onClick={() => setFilter(d)}
            className={`px-4 py-3 text-sm transition-colors ${
              filter === d
                ? "border-b-2 border-accent font-semibold text-foreground"
                : "text-muted hover:text-foreground"
            }`}
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            {d}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-4">
        {filteredClaims.map((claim, index) => (
          <ArchiveCard key={claim.id} claim={claim} index={index} />
        ))}
      </div>

      {filteredClaims.length === 0 && (
        <p
          className="py-20 text-center text-lg text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          No surviving claims in this domain.
        </p>
      )}
    </section>
  );
}

function ArchiveCard({ claim, index }: { claim: Claim; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article
      className={`animate-fade-in-up animation-delay-${((index % 5) + 1) * 100} rounded border border-border bg-surface transition-colors hover:border-accent/20`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-5 text-left"
        aria-expanded={expanded}
      >
        <div className="mb-3 flex flex-wrap items-center gap-3">
          <span
            className="text-sm font-bold text-accent"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            {claim.id}
          </span>
          <span
            className={`rounded px-2 py-0.5 text-xs font-medium ${
              claim.ruling === "REVISE"
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
            {claim.domain} &middot; Cycle {claim.cycle}
          </span>
        </div>

        <p
          className="mb-4 text-lg leading-relaxed text-foreground"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          {claim.position}
        </p>

        <div className="flex items-center gap-6">
          <div
            className="flex items-center gap-4 text-xs text-muted"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
          >
            <span>Drama {claim.drama}</span>
            <span>Novelty {claim.novelty}</span>
            <span>Depth {claim.depth}</span>
          </div>
          <ChevronDown
            className={`ml-auto h-4 w-4 text-muted transition-transform duration-300 ${expanded ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      {expanded && (
        <div className="flex flex-col gap-3 border-t border-border px-6 py-5">
          <DebateSection label="Challenge" text={claim.challenge} />
          <DebateSection label="Rebuttal" text={claim.rebuttal} />
          <DebateSection label="Verdict" text={claim.verdict} variant="verdict" />
        </div>
      )}
    </article>
  );
}

function DebateSection({
  label,
  text,
  variant,
}: {
  label: string;
  text: string;
  variant?: "verdict";
}) {
  return (
    <div
      className={`rounded px-5 py-4 ${
        variant === "verdict" ? "bg-accent/5 border border-accent/10" : "bg-background"
      }`}
    >
      <span
        className="mb-2 block text-xs tracking-[0.15em] text-muted"
        style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
      >
        {label.toUpperCase()}
      </span>
      <p
        className="text-base leading-relaxed text-foreground/80"
        style={{ fontFamily: "var(--font-cormorant)" }}
      >
        {text}
      </p>
    </div>
  );
}
