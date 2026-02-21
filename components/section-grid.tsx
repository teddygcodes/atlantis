"use client";

import { useRef, useEffect, useState } from "react";
import type { NavItem } from "@/lib/data";

const SECTIONS: { id: NavItem; title: string; description: string }[] = [
  {
    id: "Chronicle",
    title: "Chronicle",
    description: "The history of ideas tested through fire",
  },
  {
    id: "States",
    title: "States",
    description: "Six rival programs competing for truth",
  },
  {
    id: "Archive",
    title: "Archive",
    description: "Knowledge that survived adversarial challenge",
  },
  {
    id: "Debates",
    title: "Debates",
    description: "Watch claims fight for survival",
  },
  {
    id: "Graveyard",
    title: "Graveyard",
    description: "Ideas that did not survive",
  },
  {
    id: "About",
    title: "About",
    description: "The civilization is learning",
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
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );

    const cards = gridRef.current?.querySelectorAll("[data-index]");
    cards?.forEach((card) => observer.observe(card));

    return () => observer.disconnect();
  }, []);

  return (
    <section className="mx-auto max-w-4xl px-6 py-24 md:py-32">
      <p
        className="mb-16 text-center text-[11px] uppercase tracking-[0.3em] text-muted/50"
        style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
      >
        Explore the world
      </p>

      <div ref={gridRef} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SECTIONS.map((section, index) => (
          <button
            key={section.id}
            data-index={index}
            onClick={() => onNavigate(section.id)}
            className="group relative flex flex-col justify-between overflow-hidden rounded-lg border border-border/50 bg-surface px-6 py-8 text-left transition-all duration-500 hover:border-accent/40 hover:bg-surface/80"
            style={{
              opacity: visibleCards.has(index) ? 1 : 0,
              transform: visibleCards.has(index)
                ? "translateY(0)"
                : "translateY(30px)",
              transition: `opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.1}s, transform 0.7s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.1}s, border-color 0.3s, background-color 0.3s`,
            }}
          >
            {/* Subtle top accent line on hover */}
            <div className="absolute inset-x-0 top-0 h-px origin-left scale-x-0 bg-accent/60 transition-transform duration-500 group-hover:scale-x-100" />

            <div>
              <h3
                className="mb-3 text-lg tracking-[0.15em] text-foreground"
                style={{ fontFamily: "var(--font-cinzel)" }}
              >
                {section.title}
              </h3>
              <p
                className="text-[15px] leading-relaxed text-muted/70"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {section.description}
              </p>
            </div>

            <div className="mt-6 flex items-center gap-2 text-muted/30 transition-colors duration-300 group-hover:text-accent/60">
              <span
                className="text-[9px] uppercase tracking-[0.2em]"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                Enter
              </span>
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                className="transition-transform duration-300 group-hover:translate-x-1"
              >
                <path
                  d="M1 7h11m0 0L8 3m4 4L8 11"
                  stroke="currentColor"
                  strokeWidth="1"
                />
              </svg>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
