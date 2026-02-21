"use client";

import { useRef, useEffect, useState } from "react";
import type { NavItem } from "@/lib/data";

const SECTIONS: {
  id: NavItem;
  title: string;
  description: string;
  numeral: string;
  gradient: string;
  accentHue: string;
}[] = [
  {
    id: "Chronicle",
    title: "Chronicle",
    description: "The history of ideas tested through fire",
    numeral: "I",
    gradient: "radial-gradient(ellipse at 20% 80%, rgba(220,38,38,0.04) 0%, transparent 60%)",
    accentHue: "rgba(220,38,38,0.06)",
  },
  {
    id: "States",
    title: "States",
    description: "Six rival programs competing for truth",
    numeral: "II",
    gradient: "radial-gradient(ellipse at 80% 20%, rgba(220,38,38,0.03) 0%, transparent 55%)",
    accentHue: "rgba(180,38,38,0.05)",
  },
  {
    id: "Archive",
    title: "Archive",
    description: "Knowledge that survived adversarial challenge",
    numeral: "III",
    gradient: "radial-gradient(ellipse at 50% 100%, rgba(220,60,20,0.04) 0%, transparent 65%)",
    accentHue: "rgba(220,60,20,0.05)",
  },
  {
    id: "Debates",
    title: "Debates",
    description: "Watch claims fight for survival",
    numeral: "IV",
    gradient: "radial-gradient(ellipse at 80% 80%, rgba(220,38,38,0.05) 0%, transparent 55%)",
    accentHue: "rgba(200,30,30,0.06)",
  },
  {
    id: "Graveyard",
    title: "Graveyard",
    description: "Ideas that did not survive",
    numeral: "V",
    gradient: "radial-gradient(ellipse at 20% 20%, rgba(160,38,38,0.03) 0%, transparent 50%)",
    accentHue: "rgba(160,38,38,0.04)",
  },
  {
    id: "About",
    title: "About",
    description: "The civilization is learning",
    numeral: "VI",
    gradient: "radial-gradient(ellipse at 60% 50%, rgba(220,38,38,0.03) 0%, transparent 60%)",
    accentHue: "rgba(220,38,38,0.04)",
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
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    );

    const cards = gridRef.current?.querySelectorAll("[data-index]");
    cards?.forEach((card) => observer.observe(card));

    return () => observer.disconnect();
  }, []);

  return (
    <section className="mx-auto max-w-5xl px-6 py-28 md:py-40">
      <p
        className="mb-24 text-center text-[11px] uppercase tracking-[0.35em] text-muted/40"
        style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
      >
        Explore the world
      </p>

      <div ref={gridRef} className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        {SECTIONS.map((section, index) => (
          <button
            key={section.id}
            data-index={index}
            onClick={() => onNavigate(section.id)}
            className="section-door group relative flex min-h-[260px] cursor-pointer flex-col overflow-hidden rounded-sm border border-border/30 text-left md:min-h-[280px]"
            style={{
              opacity: visibleCards.has(index) ? 1 : 0,
              transform: visibleCards.has(index)
                ? "translateY(0)"
                : "translateY(50px)",
              transition: `opacity 0.9s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.1}s, transform 0.9s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.1}s`,
              backgroundImage: section.gradient,
              backgroundColor: "#0a0a0a",
            }}
          >
            {/* Large background numeral for depth */}
            <span
              className="pointer-events-none absolute -bottom-6 right-4 select-none text-[160px] font-bold leading-none md:text-[200px]"
              style={{
                fontFamily: "var(--font-cinzel)",
                color: "#111111",
              }}
              aria-hidden="true"
            >
              {section.numeral}
            </span>

            {/* Animated red border -- top */}
            <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] origin-left scale-x-0 transition-transform duration-500 ease-out group-hover:scale-x-100" style={{ backgroundColor: "rgba(220,38,38,0.7)" }} />
            {/* Animated red border -- left */}
            <div className="pointer-events-none absolute inset-y-0 left-0 w-[2px] origin-top scale-y-0 transition-transform duration-500 ease-out group-hover:scale-y-100" style={{ backgroundColor: "rgba(220,38,38,0.5)" }} />

            {/* Hover glow in corner */}
            <div
              className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full opacity-0 transition-opacity duration-700 group-hover:opacity-100"
              style={{ background: `radial-gradient(circle, ${section.accentHue}, transparent 70%)` }}
            />

            {/* Content container with generous padding */}
            <div className="relative z-10 flex h-full flex-col justify-between p-10 md:p-12">
              {/* Top row: small numeral label */}
              <span
                className="text-[10px] tracking-[0.25em] text-muted/20 transition-colors duration-300 group-hover:text-accent/50"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                {section.numeral}
              </span>

              {/* Bottom content */}
              <div>
                <h3
                  className="mb-3 text-[28px] tracking-[0.12em] text-foreground/90 transition-all duration-300 group-hover:translate-x-1.5 group-hover:text-foreground"
                  style={{ fontFamily: "var(--font-cinzel)" }}
                >
                  {section.title}
                </h3>
                <p
                  className="mb-8 text-[16px] leading-relaxed transition-colors duration-300"
                  style={{
                    fontFamily: "var(--font-cormorant)",
                    color: "#737373",
                  }}
                >
                  <span className="group-hover:hidden">{section.description}</span>
                  <span className="hidden group-hover:inline" style={{ color: "#a3a3a3" }}>{section.description}</span>
                </p>

                {/* Enter with arrow */}
                <div className="flex items-center gap-2 transition-all duration-300 group-hover:gap-4" style={{ color: "#404040" }}>
                  <span
                    className="text-[9px] uppercase tracking-[0.3em] transition-colors duration-300 group-hover:text-accent/70"
                    style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                  >
                    Enter
                  </span>
                  <svg
                    width="20"
                    height="12"
                    viewBox="0 0 20 12"
                    fill="none"
                    className="transition-all duration-300 group-hover:translate-x-2 group-hover:text-accent/70"
                  >
                    <path
                      d="M0 6h16m0 0l-4-4.5m4 4.5l-4 4.5"
                      stroke="currentColor"
                      strokeWidth="1"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
