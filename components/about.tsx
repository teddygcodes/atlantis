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
    <section ref={containerRef} className="mx-auto max-w-[800px]">
      {/* Header */}
      <div className="scroll-reveal mb-20 flex items-start gap-8">
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
            ABOUT ATLANTIS
          </h2>
          <p
            className="text-xl leading-[1.9] text-muted"
            style={{ fontFamily: "var(--font-cormorant)" }}
          >
            The civilization is learning.
          </p>
        </div>
      </div>

      {/* Paragraphs */}
      <div className="mb-24 flex flex-col gap-12">
        {ABOUT_PARAGRAPHS.map((paragraph, index) => (
          <p
            key={index}
            className={`scroll-reveal text-center text-xl leading-[1.9] ${
              index === ABOUT_PARAGRAPHS.length - 1
                ? "font-semibold text-foreground"
                : "text-muted"
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
    </section>
  );
}
