"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import { CLAIMS } from "@/lib/data";

export function Graveyard() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          } else {
            // Dim tombstones as they scroll past
            const rect = entry.boundingClientRect;
            if (rect.top < 0) {
              entry.target.classList.add("tombstone-past");
            }
          }
        });
      },
      { threshold: 0.2, rootMargin: "0px 0px -80px 0px" }
    );
    el.querySelectorAll(".tombstone").forEach((child) =>
      observer.observe(child)
    );
    return () => observer.disconnect();
  }, []);

  const destroyedClaims = CLAIMS.filter((c) => c.ruling === "DESTROYED");

  return (
    <section ref={containerRef}>
      {/* Header */}
      <div className="scroll-reveal mx-auto mb-20 flex max-w-[800px] items-start gap-8">
        <Image
          src="/images/logo.png"
          alt="Atlantis logo"
          width={80}
          height={80}
          className="mt-1 flex-shrink-0 object-contain"
          style={{ width: "80px", height: "auto" }}
        />
        <div>
          <h2
            className="mb-4 tracking-[0.25em] text-foreground"
            style={{ fontFamily: "var(--font-cinzel)", fontSize: "36px" }}
          >
            THE GRAVEYARD
          </h2>
          <p
            className="text-xl leading-[1.9] text-muted/60"
            style={{ fontFamily: "var(--font-cormorant)" }}
          >
            The fallen. Every destroyed claim is preserved here as a monument to
            what the system will not accept.
          </p>
        </div>
      </div>

      {/* Tombstones */}
      <div className="mx-auto flex max-w-[600px] flex-col gap-12">
        {destroyedClaims.map((claim) => (
          <article
            key={claim.id}
            className="tombstone flex flex-col items-center text-center opacity-0 transition-all duration-700"
          >
            {/* Tombstone shape */}
            <div className="w-full max-w-md rounded-t-[80px] border border-border/30 bg-surface/20 px-8 py-10 pb-8">
              {/* Cross / marker */}
              <div className="mb-6 flex justify-center">
                <svg
                  width="20"
                  height="28"
                  viewBox="0 0 20 28"
                  fill="none"
                  className="text-destroyed/40"
                >
                  <path d="M10 0v28M4 8h12" stroke="currentColor" strokeWidth="1" />
                </svg>
              </div>

              {/* Claim ID */}
              <span
                className="mb-4 block text-sm tracking-[0.2em] text-destroyed/60"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                {claim.id}
              </span>

              {/* Epitaph: the one-line reason it died */}
              <p
                className="mb-6 text-lg italic leading-relaxed text-muted/40"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                &ldquo;{getEpitaph(claim.verdict)}&rdquo;
              </p>

              {/* Meta */}
              <div className="flex items-center justify-center gap-3">
                <span
                  className="text-[9px] uppercase tracking-[0.2em] text-muted/25"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  {claim.state.replace("_", " ")}
                </span>
                <span className="text-muted/15">|</span>
                <span
                  className="text-[9px] uppercase tracking-[0.2em] text-muted/25"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  Cycle {claim.cycle}
                </span>
              </div>
            </div>

            {/* Base */}
            <div className="h-3 w-full max-w-md border-x border-b border-border/20 bg-surface/10" />
            <div className="h-2 w-[calc(100%-16px)] max-w-[calc(28rem-16px)] border-x border-b border-border/10 bg-surface/5" />
          </article>
        ))}
      </div>

      {/* End marker */}
      <div className="mt-20 flex justify-center">
        <div className="h-px w-12 bg-destroyed/20" />
      </div>
    </section>
  );
}

function getEpitaph(verdict: string): string {
  // Extract the first sentence as the epitaph
  const firstSentence = verdict.split(". ")[0];
  return firstSentence.replace(/^Destroyed\.\s*/i, "").trim();
}
