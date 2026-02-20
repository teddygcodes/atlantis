"use client";

import { CLAIMS } from "@/lib/data";

export function Graveyard() {
  const destroyedClaims = CLAIMS.filter((c) => c.ruling === "DESTROYED");

  return (
    <section>
      <header className="mb-16 animate-fade-in-up">
        <h1
          className="mb-4 text-4xl tracking-[0.2em] text-foreground md:text-5xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          Graveyard
        </h1>
        <p
          className="max-w-2xl text-xl leading-relaxed text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          The fallen. Every destroyed claim is preserved here as a monument to
          what the system will not accept.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {destroyedClaims.map((claim, index) => (
          <article
            key={claim.id}
            className={`animate-fade-in-up animation-delay-${((index % 5) + 1) * 100} group rounded border border-border bg-surface opacity-75 transition-opacity hover:opacity-100`}
          >
            <div className="p-6">
              <div className="mb-3 flex flex-wrap items-center gap-3">
                <span
                  className="text-sm font-bold text-destroyed"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  {claim.id}
                </span>
                <span
                  className="rounded bg-destroyed/20 px-2 py-0.5 text-xs font-medium text-destroyed"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  DESTROYED
                </span>
              </div>

              <p
                className="mb-4 line-clamp-3 text-base leading-relaxed text-muted"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.position}
              </p>

              <div className="mb-4 flex flex-wrap items-center gap-3">
                <span
                  className="text-xs text-muted/70"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  {claim.state}
                </span>
                <span
                  className="text-xs text-muted/70"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  Cycle {claim.cycle}
                </span>
              </div>

              <p
                className="border-t border-border pt-4 text-sm italic leading-relaxed text-muted/60"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {claim.verdict}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
