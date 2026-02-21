"use client";

import { useRef, useEffect, useState } from "react";
import type { NavItem } from "@/lib/data";

/* ── Unique SVG watermarks per section ─────────────────── */

function ChronicleWatermark() {
  return (
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 400 300" fill="none" aria-hidden="true">
      {/* Vertical timeline line */}
      <line x1="60" y1="20" x2="60" y2="280" stroke="#141414" strokeWidth="2" />
      {/* Timeline dots */}
      <circle cx="60" cy="50" r="4" fill="#181818" />
      <circle cx="60" cy="110" r="4" fill="#181818" />
      <circle cx="60" cy="170" r="4" fill="#181818" />
      <circle cx="60" cy="230" r="4" fill="#181818" />
      {/* Connecting horizontal ticks */}
      <line x1="60" y1="50" x2="90" y2="50" stroke="#141414" strokeWidth="1.5" />
      <line x1="60" y1="110" x2="105" y2="110" stroke="#141414" strokeWidth="1.5" />
      <line x1="60" y1="170" x2="80" y2="170" stroke="#141414" strokeWidth="1.5" />
      <line x1="60" y1="230" x2="95" y2="230" stroke="#141414" strokeWidth="1.5" />
    </svg>
  );
}

function StatesWatermark() {
  return (
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 400 300" fill="none" aria-hidden="true">
      {/* Six rival figures — abstract silhouettes */}
      <circle cx="80" cy="120" r="18" fill="#131313" />
      <rect x="68" y="142" width="24" height="40" rx="4" fill="#131313" />
      <circle cx="160" cy="100" r="18" fill="#141414" />
      <rect x="148" y="122" width="24" height="40" rx="4" fill="#141414" />
      <circle cx="130" cy="180" r="15" fill="#121212" />
      <rect x="120" y="198" width="20" height="34" rx="4" fill="#121212" />
      {/* Connecting tension lines */}
      <line x1="98" y1="120" x2="142" y2="100" stroke="#151515" strokeWidth="1" strokeDasharray="4 4" />
      <line x1="160" y1="118" x2="145" y2="168" stroke="#151515" strokeWidth="1" strokeDasharray="4 4" />
    </svg>
  );
}

function ArchiveWatermark() {
  return (
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 400 300" fill="none" aria-hidden="true">
      {/* Vault door shape */}
      <rect x="50" y="40" width="140" height="200" rx="8" stroke="#151515" strokeWidth="2.5" fill="none" />
      <circle cx="120" cy="140" r="35" stroke="#141414" strokeWidth="2" fill="none" />
      <circle cx="120" cy="140" r="4" fill="#161616" />
      {/* Lock handle */}
      <line x1="120" y1="105" x2="120" y2="175" stroke="#141414" strokeWidth="1.5" />
      <line x1="85" y1="140" x2="155" y2="140" stroke="#141414" strokeWidth="1.5" />
      {/* Rivets */}
      <circle cx="65" cy="55" r="3" fill="#131313" />
      <circle cx="175" cy="55" r="3" fill="#131313" />
      <circle cx="65" cy="225" r="3" fill="#131313" />
      <circle cx="175" cy="225" r="3" fill="#131313" />
    </svg>
  );
}

function DebatesWatermark() {
  return (
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 400 300" fill="none" aria-hidden="true">
      {/* Crossed swords */}
      <line x1="40" y1="240" x2="180" y2="60" stroke="#151515" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="180" y1="240" x2="40" y2="60" stroke="#151515" strokeWidth="2.5" strokeLinecap="round" />
      {/* Sword guards */}
      <line x1="75" y1="188" x2="100" y2="200" stroke="#141414" strokeWidth="2" />
      <line x1="145" y1="188" x2="120" y2="200" stroke="#141414" strokeWidth="2" />
      {/* Spark at center */}
      <circle cx="110" cy="150" r="6" fill="#161616" />
      <line x1="100" y1="150" x2="120" y2="150" stroke="#181818" strokeWidth="1" />
      <line x1="110" y1="140" x2="110" y2="160" stroke="#181818" strokeWidth="1" />
    </svg>
  );
}

function GraveyardWatermark() {
  return (
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 400 300" fill="none" aria-hidden="true">
      {/* Tombstone */}
      <path d="M80 260 L80 100 Q80 60 120 60 Q160 60 160 100 L160 260" stroke="#141414" strokeWidth="2.5" fill="none" />
      {/* Cross on tombstone */}
      <line x1="120" y1="90" x2="120" y2="160" stroke="#151515" strokeWidth="2" />
      <line x1="100" y1="115" x2="140" y2="115" stroke="#151515" strokeWidth="2" />
      {/* Ground line */}
      <line x1="40" y1="260" x2="200" y2="260" stroke="#131313" strokeWidth="1.5" />
      {/* Small background stones */}
      <rect x="180" y="220" width="25" height="40" rx="4" fill="#111111" />
      <rect x="215" y="230" width="20" height="30" rx="3" fill="#101010" />
    </svg>
  );
}

function AboutWatermark() {
  return (
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 400 300" fill="none" aria-hidden="true">
      {/* Abstract Atlantis trident / spiral */}
      <path d="M120 240 L120 100 L90 60 M120 100 L120 40 M120 100 L150 60" stroke="#141414" strokeWidth="2.5" strokeLinecap="round" />
      {/* Spiral wrapping */}
      <path d="M85 170 Q85 130 120 130 Q155 130 155 170 Q155 200 120 200 Q95 200 95 175" stroke="#131313" strokeWidth="1.5" fill="none" />
      {/* Glow point at tip */}
      <circle cx="120" cy="36" r="4" fill="#161616" />
    </svg>
  );
}

const WATERMARKS = [ChronicleWatermark, StatesWatermark, ArchiveWatermark, DebatesWatermark, GraveyardWatermark, AboutWatermark];

/* ── Section data ──────────────────────────────────────── */

const SECTIONS: {
  id: NavItem;
  title: string;
  description: string;
  numeral: string;
  gradient: string;
}[] = [
  {
    id: "Chronicle",
    title: "Chronicle",
    description: "The history of ideas tested through fire",
    numeral: "I",
    gradient: "radial-gradient(ellipse at 30% 80%, rgba(220,38,38,0.04) 0%, transparent 60%)",
  },
  {
    id: "States",
    title: "States",
    description: "Six rival programs competing for truth",
    numeral: "II",
    gradient: "radial-gradient(ellipse at 70% 30%, rgba(220,38,38,0.03) 0%, transparent 55%)",
  },
  {
    id: "Archive",
    title: "Archive",
    description: "Knowledge that survived adversarial challenge",
    numeral: "III",
    gradient: "radial-gradient(ellipse at 50% 90%, rgba(220,60,20,0.04) 0%, transparent 65%)",
  },
  {
    id: "Debates",
    title: "Debates",
    description: "Watch claims fight for survival",
    numeral: "IV",
    gradient: "radial-gradient(ellipse at 80% 70%, rgba(220,38,38,0.05) 0%, transparent 55%)",
  },
  {
    id: "Graveyard",
    title: "Graveyard",
    description: "Ideas that did not survive",
    numeral: "V",
    gradient: "radial-gradient(ellipse at 20% 30%, rgba(160,38,38,0.03) 0%, transparent 50%)",
  },
  {
    id: "About",
    title: "About",
    description: "The civilization is learning",
    numeral: "VI",
    gradient: "radial-gradient(ellipse at 60% 50%, rgba(220,38,38,0.03) 0%, transparent 60%)",
  },
];

interface SectionGridProps {
  onNavigate: (tab: NavItem) => void;
}

export function SectionGrid({ onNavigate }: SectionGridProps) {
  const gridRef = useRef<HTMLDivElement>(null);
  const [visibleRows, setVisibleRows] = useState<Set<number>>(new Set());

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const row = Number(entry.target.getAttribute("data-row"));
          if (entry.isIntersecting) {
            setVisibleRows((prev) => new Set(prev).add(row));
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -60px 0px" }
    );

    const sentinels = gridRef.current?.querySelectorAll("[data-row]");
    sentinels?.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <section className="mx-auto max-w-5xl px-6 py-28 md:py-40">
      <p
        className="mb-20 text-center text-[11px] uppercase tracking-[0.35em] text-muted/40"
        style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
      >
        Explore the world
      </p>

      <div ref={gridRef} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {SECTIONS.map((section, index) => {
          const Watermark = WATERMARKS[index];
          const row = Math.floor(index / 2);
          const isRowVisible = visibleRows.has(row);
          const colDelay = index % 2 === 0 ? 0 : 0.1;
          const rowDelay = row * 0.2;
          const totalDelay = rowDelay + colDelay;

          return (
            <button
              key={section.id}
              data-row={row}
              onClick={() => onNavigate(section.id)}
              className="section-door group relative flex min-h-[280px] cursor-pointer flex-col overflow-hidden rounded-sm border border-border/30 text-left md:min-h-[300px]"
              style={{
                opacity: isRowVisible ? 1 : 0,
                transform: isRowVisible
                  ? "translateY(0)"
                  : "translateY(60px)",
                transition: `opacity 0.9s cubic-bezier(0.16, 1, 0.3, 1) ${totalDelay}s, transform 0.9s cubic-bezier(0.16, 1, 0.3, 1) ${totalDelay}s`,
                backgroundImage: section.gradient,
                backgroundColor: "#0a0a0a",
              }}
            >
              {/* Unique SVG watermark illustration */}
              <div className="pointer-events-none absolute inset-0 opacity-100">
                <Watermark />
              </div>

              {/* Massive background numeral bleeding off edge */}
              <span
                className="pointer-events-none absolute -bottom-10 -right-2 select-none text-[200px] font-bold leading-none md:text-[240px]"
                style={{
                  fontFamily: "var(--font-cinzel)",
                  color: "#0f0f0f",
                }}
                aria-hidden="true"
              >
                {section.numeral}
              </span>

              {/* Animated red border -- top sweep */}
              <div
                className="pointer-events-none absolute inset-x-0 top-0 h-[2px] origin-left scale-x-0 transition-transform duration-[400ms] ease-out group-hover:scale-x-100"
                style={{ backgroundColor: "rgba(220,38,38,0.7)" }}
              />
              {/* Animated red border -- left sweep */}
              <div
                className="pointer-events-none absolute inset-y-0 left-0 w-[2px] origin-top scale-y-0 transition-transform duration-[400ms] ease-out group-hover:scale-y-100"
                style={{ backgroundColor: "rgba(220,38,38,0.5)", transitionDelay: "0.1s" }}
              />

              {/* Hover glow bloom */}
              <div
                className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full opacity-0 transition-opacity duration-700 group-hover:opacity-100"
                style={{ background: "radial-gradient(circle, rgba(220,38,38,0.06), transparent 70%)" }}
              />

              {/* Content with generous padding */}
              <div className="relative z-10 flex h-full flex-col justify-between p-10 md:p-12">
                {/* Top: small numeral label */}
                <span
                  className="text-[10px] tracking-[0.25em] text-muted/20 transition-colors duration-300 group-hover:text-accent/50"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
                >
                  {section.numeral}
                </span>

                {/* Bottom: title + description + enter */}
                <div>
                  <h3
                    className="mb-3 text-[28px] tracking-[0.12em] text-foreground/90 transition-all duration-300 group-hover:translate-x-2 group-hover:text-foreground"
                    style={{ fontFamily: "var(--font-cinzel)" }}
                  >
                    {section.title}
                  </h3>
                  <p
                    className="mb-8 text-[16px] leading-relaxed transition-colors duration-300 group-hover:[color:#a3a3a3]"
                    style={{
                      fontFamily: "var(--font-cormorant)",
                      color: "#737373",
                    }}
                  >
                    {section.description}
                  </p>

                  {/* Enter arrow */}
                  <div
                    className="flex items-center gap-2 transition-all duration-300 group-hover:gap-4"
                    style={{ color: "#404040" }}
                  >
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
          );
        })}
      </div>
    </section>
  );
}
