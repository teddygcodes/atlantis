"use client";

import { useRef, useEffect, useState } from "react";
import { CHRONICLE_ENTRIES, CLAIMS } from "@/lib/data";

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

function getCycleStats(cycle: number) {
  const cycleClaims = CLAIMS.filter((c) => c.cycle === cycle);
  const destroyed = cycleClaims.filter((c) => c.ruling === "DESTROYED").length;
  const survived = cycleClaims.length - destroyed;
  return { total: cycleClaims.length, destroyed, survived };
}

export function Chronicle() {
  const containerRef = useScrollReveal();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 10);
    setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 10);
  };

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    checkScroll();
    el.addEventListener("scroll", checkScroll, { passive: true });
    window.addEventListener("resize", checkScroll);
    return () => {
      el.removeEventListener("scroll", checkScroll);
      window.removeEventListener("resize", checkScroll);
    };
  }, []);

  const scroll = (dir: "left" | "right") => {
    const el = scrollRef.current;
    if (!el) return;
    const amount = el.clientWidth * 0.8;
    el.scrollBy({ left: dir === "left" ? -amount : amount, behavior: "smooth" });
  };

  return (
    <section ref={containerRef}>
      {/* Page header - centered */}
      <div className="mx-auto mb-12 text-center" style={{ paddingTop: "64px" }}>
        <h2
          className="mb-4"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "36px",
            color: "#e5e5e5",
            letterSpacing: "0.25em",
          }}
        >
          THE CHRONICLE
        </h2>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "16px",
            color: "#e5e5e5",
          }}
        >
          Three cycles. Eighteen claims. A civilization learning what holds up
          under pressure.
        </p>
      </div>

      {/* 48px gap below subtitle */}
      <div style={{ height: "48px" }} />

      {/* Horizontal scroll area */}
      <div className="relative">
        {/* Fade edges */}
        <div
          className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 transition-opacity duration-300"
          style={{
            background: "linear-gradient(to right, var(--color-background), transparent)",
            opacity: canScrollLeft ? 1 : 0,
          }}
        />
        <div
          className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 transition-opacity duration-300"
          style={{
            background: "linear-gradient(to left, var(--color-background), transparent)",
            opacity: canScrollRight ? 1 : 0,
          }}
        />

        {/* Scroll controls */}
        <div className="mx-auto mb-6 flex max-w-[900px] items-center justify-center gap-2 px-6">
          <button
            onClick={() => scroll("left")}
            disabled={!canScrollLeft}
            className="flex h-8 w-8 items-center justify-center rounded border border-border text-muted transition-colors hover:border-accent/40 hover:text-foreground disabled:opacity-20"
            aria-label="Scroll left"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M9 3L5 7L9 11" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </button>
          <button
            onClick={() => scroll("right")}
            disabled={!canScrollRight}
            className="flex h-8 w-8 items-center justify-center rounded border border-border text-muted transition-colors hover:border-accent/40 hover:text-foreground disabled:opacity-20"
            aria-label="Scroll right"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M5 3L9 7L5 11" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </button>
        </div>

        <div
          ref={scrollRef}
          className="flex snap-x snap-mandatory gap-6 overflow-x-auto px-6 pb-8 scrollbar-hide md:gap-8 md:px-[calc(50vw-400px)]"
          style={{ scrollbarWidth: "none" }}
        >
          {CHRONICLE_ENTRIES.map((entry) => {
            const stats = getCycleStats(entry.cycle);
            return (
              <article
                key={entry.cycle}
                className="flex w-[85vw] flex-none snap-center flex-col rounded-lg border border-border bg-surface/50 p-8 md:w-[520px] md:p-10"
              >
                {/* Cycle badge */}
                <div className="mb-6 flex items-center gap-4">
                  <span
                    className="text-[10px] uppercase tracking-[0.3em] text-accent"
                    style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                  >
                    Cycle {entry.cycle}
                  </span>
                  <div className="h-px flex-1 bg-border" />
                </div>

                {/* Title */}
                <h3
                  className="mb-6 text-2xl tracking-wide text-foreground md:text-3xl"
                  style={{ fontFamily: "var(--font-cinzel)" }}
                >
                  {entry.title}
                </h3>

                {/* Narrative */}
                <p
                  className="mb-8 flex-1 text-lg leading-[1.9] text-foreground/80"
                  style={{ fontFamily: "var(--font-cormorant)" }}
                >
                  {entry.narrative}
                </p>

                {/* Stats bar */}
                <div className="flex items-center gap-6 border-t border-border pt-6">
                  <div className="flex flex-col">
                    <span
                      className="text-2xl text-foreground"
                      style={{ fontFamily: "var(--font-cinzel)" }}
                    >
                      {stats.total}
                    </span>
                    <span
                      className="text-[9px] uppercase tracking-[0.2em] text-foreground/60"
                      style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                    >
                      Claims
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span
                      className="text-2xl text-accent"
                      style={{ fontFamily: "var(--font-cinzel)" }}
                    >
                      {stats.destroyed}
                    </span>
                    <span
                      className="text-[9px] uppercase tracking-[0.2em] text-foreground/60"
                      style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                    >
                      Destroyed
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span
                      className="text-2xl text-emerald-500"
                      style={{ fontFamily: "var(--font-cinzel)" }}
                    >
                      {stats.survived}
                    </span>
                    <span
                      className="text-[9px] uppercase tracking-[0.2em] text-foreground/60"
                      style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                    >
                      Survived
                    </span>
                  </div>
                  <div className="ml-auto flex flex-col items-end">
                    <span
                      className="text-2xl text-foreground"
                      style={{ fontFamily: "var(--font-cinzel)" }}
                    >
                      {stats.total > 0
                        ? Math.round(
                            (stats.destroyed / stats.total) * 100
                          )
                        : 0}
                      %
                    </span>
                    <span
                      className="text-[9px] uppercase tracking-[0.2em] text-foreground/60"
                      style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                    >
                      Kill Rate
                    </span>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
