"use client";

import { useRef, useEffect, useState } from "react";
import Link from "next/link";
import type { NavItem } from "@/lib/data";

const SECTIONS: {
  id: NavItem;
  title: string;
  description: string;
  href: string;
}[] = [
  {
    id: "Chronicle",
    title: "Research Timeline",
    description: "what happened when ideas were put to the test",
    href: "/chronicle",
  },
  {
    id: "States",
    title: "States",
    description: "meet the minds that were validated",
    href: "/states",
  },
  {
    id: "Archive",
    title: "Knowledge Base",
    description: "the knowledge that earned its place",
    href: "/archive",
  },
  {
    id: "Debates",
    title: "Peer Review",
    description: "watch the adversarial review process",
    href: "/debates",
  },
  {
    id: "Graveyard",
    title: "Refuted",
    description: "not every hypothesis holds up",
    href: "/graveyard",
  },
];

export function SectionGrid() {
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
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    );

    const sentinels = gridRef.current?.querySelectorAll("[data-row]");
    sentinels?.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  const rowMap = [0, 1, 1, 2, 2];

  return (
    <section className="mx-auto max-w-5xl px-6 py-28 md:py-40">
      <p
        className="mb-20 text-center text-[11px] uppercase tracking-[0.35em] animate-fade-in-up"
        style={{
          fontFamily: "var(--font-ibm-plex-mono)",
          color: "#737373",
        }}
      >
        Explore the world
      </p>

      <div ref={gridRef} className="flex flex-col gap-4">
        {renderTile(SECTIONS[0], 0)}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {renderTile(SECTIONS[1], 1)}
          {renderTile(SECTIONS[2], 2)}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {renderTile(SECTIONS[3], 3)}
          {renderTile(SECTIONS[4], 4)}
        </div>
      </div>
    </section>
  );

  function renderTile(section: (typeof SECTIONS)[number], index: number) {
    const row = rowMap[index];
    const isVisible = visibleRows.has(row);
    const colDelay = index === 2 || index === 4 ? 0.1 : 0;
    const rowDelay = row * 0.2;
    const totalDelay = rowDelay + colDelay;
    const isChronicle = index === 0;

    return (
      <Link
        key={section.id}
        href={section.href}
        data-row={row}
        className="section-door group relative flex cursor-pointer items-center justify-center overflow-hidden border text-center"
        style={{
          minHeight: isChronicle ? "280px" : "260px",
          borderColor: "rgba(255,255,255,0.06)",
          backgroundColor: "#0a0a0a",
          borderRadius: "12px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? "translateY(0)" : "translateY(50px)",
          transition: `opacity 0.9s cubic-bezier(0.16, 1, 0.3, 1) ${totalDelay}s, transform 0.9s cubic-bezier(0.16, 1, 0.3, 1) ${totalDelay}s, box-shadow 0.3s ease, border-color 0.3s ease`,
        }}
      >
        {/* Animated red left border */}
        <div
          className="pointer-events-none absolute inset-y-0 left-0 w-[2px] origin-top scale-y-0 transition-transform duration-[400ms] ease-out group-hover:scale-y-100"
          style={{
            backgroundColor: "rgba(220,38,38,0.6)",
            borderRadius: "12px 0 0 12px",
          }}
        />

        {/* Animated red top border */}
        <div
          className="pointer-events-none absolute inset-x-0 top-0 h-[2px] origin-left scale-x-0 transition-transform duration-[400ms] ease-out group-hover:scale-x-100"
          style={{
            backgroundColor: "rgba(220,38,38,0.5)",
            transitionDelay: "0.08s",
            borderRadius: "12px 12px 0 0",
          }}
        />

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center px-10 py-10 md:px-12 md:py-12">
          <h3
            className={`mb-4 tracking-[0.12em] text-foreground/90 transition-all duration-300 group-hover:text-foreground ${
              isChronicle
                ? "text-[28px] md:text-[36px]"
                : "text-[24px] md:text-[28px]"
            }`}
            style={{ fontFamily: "var(--font-cinzel)" }}
          >
            {section.title}
          </h3>

          <p
            className="mb-8 max-w-md text-[16px] italic transition-colors duration-300 group-hover:[color:#a3a3a3]"
            style={{
              fontFamily: "var(--font-cormorant)",
              color: "#737373",
              lineHeight: "1.6",
            }}
          >
            {section.description}
          </p>

          <div className="flex items-center gap-2 transition-all duration-300 group-hover:gap-4">
            <span
              className="text-[9px] uppercase tracking-[0.3em] transition-colors duration-300 group-hover:text-[#dc2626]/70"
              style={{
                fontFamily: "var(--font-ibm-plex-mono)",
                color: "#333333",
              }}
            >
              Enter
            </span>
            <svg
              width="20"
              height="12"
              viewBox="0 0 20 12"
              fill="none"
              className="transition-all duration-300 group-hover:translate-x-2 group-hover:text-[#dc2626]/70"
              style={{ color: "#333333" }}
            >
              <path
                d="M0 6h16m0 0l-4-4.5m4 4.5l-4 4.5"
                stroke="currentColor"
                strokeWidth="1"
              />
            </svg>
          </div>
        </div>
      </Link>
    );
  }
}
