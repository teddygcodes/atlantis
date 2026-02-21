"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import { ABOUT_PARAGRAPHS, STATS } from "@/lib/data";

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

export function About() {
  const containerRef = useScrollReveal();

  return (
    <section ref={containerRef} className="mx-auto max-w-[900px]">
      {/* Page header - centered */}
      <div className="scroll-reveal mx-auto mb-12 text-center" style={{ paddingTop: "64px" }}>
        <h2
          className="mb-4"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "36px",
            color: "#e5e5e5",
            letterSpacing: "0.25em",
          }}
        >
          ABOUT ATLANTIS
        </h2>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "18px",
            fontWeight: 600,
            color: "#d4d4d4",
          }}
        >
          The civilization is learning.
        </p>
      </div>

      {/* 48px gap below subtitle */}
      <div style={{ height: "48px" }} />

      {/* Paragraphs */}
      <div className="mb-24 flex flex-col gap-12">
        {ABOUT_PARAGRAPHS.map((paragraph, index) => (
          <p
            key={index}
            className={`scroll-reveal text-center text-xl font-semibold leading-[1.9] ${
              index === ABOUT_PARAGRAPHS.length - 1
                ? "font-bold text-foreground"
                : "text-foreground/80"
            }`}
            style={{ fontFamily: "var(--font-cormorant)" }}
          >
            {paragraph}
          </p>
        ))}
      </div>

      {/* Stats */}
      <div className="scroll-reveal border-t border-border pt-16">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {[
            { label: "DOMAINS", value: STATS.domains },
            { label: "STATES", value: STATS.states },
            { label: "SURVIVING", value: STATS.surviving },
            { label: "DESTROYED", value: STATS.destroyed },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div
                className="mb-2 text-3xl text-foreground"
                style={{ fontFamily: "var(--font-cinzel)" }}
              >
                {stat.value}
              </div>
              <div
                className="text-[9px] tracking-[0.25em] text-muted/50"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom logo */}
      <div className="scroll-reveal mt-32 flex justify-center pb-8">
        <Image
          src="/images/atlantis-logo-full.png"
          alt="Atlantis logo"
          width={600}
          height={600}
          className="object-contain opacity-50"
          style={{ width: "auto", height: "auto", maxWidth: "360px" }}
        />
      </div>
    </section>
  );
}
