"use client";

import { useRef, useEffect, useState } from "react";
import type { NavItem } from "@/lib/data";

const SECTIONS: { id: NavItem; title: string; description: string; numeral: string }[] = [
  {
    id: "Chronicle",
    title: "Chronicle",
    description: "The history of ideas tested through fire",
    numeral: "I",
  },
  {
    id: "States",
    title: "States",
    description: "Six rival programs competing for truth",
    numeral: "II",
  },
  {
    id: "Archive",
    title: "Archive",
    description: "Knowledge that survived adversarial challenge",
    numeral: "III",
  },
  {
    id: "Debates",
    title: "Debates",
    description: "Watch claims fight for survival",
    numeral: "IV",
  },
  {
    id: "Graveyard",
    title: "Graveyard",
    description: "Ideas that did not survive",
    numeral: "V",
  },
  {
    id: "About",
    title: "About",
    description: "The civilization is learning",
    numeral: "VI",
  },
];

interface SectionGridProps {
  onNavigate: (tab: NavItem) => void;
}

export function SectionGrid({ onNavigate }: SectionGridProps) {
  const gridRef = useRef<HTMLDivElement>(null);
  const [visibleCards, setVisibleCards] = useState<Set<number>>(new Set());

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const index = Number(entry.target.getAttribute("data-index"));
          if (entry.isIntersecting) {
            setVisibleCards((prev) => new Set(prev).add(index));
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -60px 0px" }
    );

    const cards = gridRef.current?.querySelectorAll("[data-index]");
    cards?.forEach((card) => observer.observe(card));

    return () => observer.disconnect();
  }, []);

  return (
    <section className="mx-auto max-w-5xl px-6 py-24 md:py-36">
      <p
        className="mb-20 text-center text-[11px] uppercase tracking-[0.35em] text-muted/40"
        style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
      >
        Explore the world
      </p>

      <div ref={gridRef} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {SECTIONS.map((section, index) => (
          <button
            key={section.id}
            data-index={index}
            onClick={() => onNavigate(section.id)}
            className="section-door group relative flex min-h-[220px] flex-col justify-between overflow-hidden rounded border border-border/40 bg-surface p-8 text-left md:min-h-[240px] md:p-10"
            style={{
              opacity: visibleCards.has(index) ? 1 : 0,
              transform: visibleCards.has(index)
                ? "translateY(0)"
                : "translateY(40px)",
              transition: `opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.12}s, transform 0.8s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.12}s`,
            }}
          >
            {/* Red glow on hover -- top and left border */}
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px origin-left scale-x-0 bg-accent transition-transform duration-700 group-hover:scale-x-100" />
            <div className="pointer-events-none absolute inset-y-0 left-0 w-px origin-top scale-y-0 bg-accent/60 transition-transform duration-700 group-hover:scale-y-100" />

            {/* Subtle radial glow on hover */}
            <div className="pointer-events-none absolute -right-20 -top-20 h-60 w-60 rounded-full bg-accent/0 transition-all duration-700 group-hover:bg-accent/[0.04]" />

            {/* Top row: numeral */}
            <span
              className="text-[11px] tracking-[0.2em] text-muted/25 transition-colors duration-500 group-hover:text-accent/40"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {section.numeral}
            </span>

            {/* Content */}
            <div className="mt-auto">
              <h3
                className="mb-3 text-2xl tracking-[0.15em] text-foreground transition-colors duration-500 group-hover:text-foreground md:text-3xl"
                style={{ fontFamily: "var(--font-cinzel)" }}
              >
                {section.title}
              </h3>
              <p
                className="mb-6 text-lg leading-relaxed text-muted/50 transition-colors duration-500 group-hover:text-muted/70"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {section.description}
              </p>

              {/* Enter indicator */}
              <div className="flex items-center gap-2 text-muted/20 transition-all duration-500 group-hover:gap-3 group-hover:text-accent/60">
                <span
                  className="text-[9px] uppercase tracking-[0.25em]"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  Enter
                </span>
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 18 18"
                  fill="none"
                  className="transition-transform duration-500 group-hover:translate-x-1"
                >
                  <path
                    d="M1 9h14m0 0l-5-5m5 5l-5 5"
                    stroke="currentColor"
                    strokeWidth="1"
                  />
                </svg>
              </div>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
