"use client";

import { ABOUT_PARAGRAPHS, STATS } from "@/lib/data";

export function About() {
  return (
    <section className="mx-auto max-w-[800px]">
      <div className="mb-24 flex flex-col gap-12">
        {ABOUT_PARAGRAPHS.map((paragraph, index) => (
          <p
            key={index}
            className={`animate-fade-in-up animation-delay-${(index + 1) * 100} text-center text-[18px] leading-[1.9] ${
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

      <div className="animate-fade-in-up animation-delay-400 border-t border-border pt-16">
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
                className="text-[10px] tracking-[0.25em] text-muted"
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
