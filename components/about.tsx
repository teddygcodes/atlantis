"use client";

import { ABOUT_PARAGRAPHS, STATS } from "@/lib/data";

export function About() {
  return (
    <section className="mx-auto max-w-[800px]">
      <div className="mb-20 flex flex-col gap-10">
        {ABOUT_PARAGRAPHS.map((paragraph, index) => (
          <p
            key={index}
            className={`animate-fade-in-up animation-delay-${(index + 1) * 100} text-center text-lg leading-[1.8] text-foreground/85 md:text-xl ${
              index === ABOUT_PARAGRAPHS.length - 1
                ? "font-semibold text-foreground"
                : ""
            }`}
            style={{ fontFamily: "var(--font-cormorant)" }}
          >
            {paragraph}
          </p>
        ))}
      </div>

      <div className="animate-fade-in-up animation-delay-400 border-t border-border pt-12">
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
                className="text-xs tracking-[0.2em] text-muted"
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
