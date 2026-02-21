"use client";

import { useEffect, useRef } from "react";
import { CHRONICLE_ENTRIES } from "@/lib/data";

function useScrollReveal() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = ref.current;
    if (!container) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );

    const elements = container.querySelectorAll(".scroll-reveal");
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return ref;
}

export function Chronicle() {
  const containerRef = useScrollReveal();

  return (
    <section ref={containerRef} className="mx-auto max-w-[800px]">
      {/* Section header with red rule */}
      <header className="scroll-reveal mb-24">
        <h2
          className="mb-4 text-lg tracking-[0.3em] text-foreground md:text-xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          The Chronicle
        </h2>
        <div className="mb-8 h-px w-10" style={{ backgroundColor: "#dc2626" }} />
        <p
          className="text-[18px] leading-[1.9] text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          A record of what happened. Each cycle brings new claims, new
          challenges, and new ruins.
        </p>
      </header>

      {/* Timeline */}
      <div className="relative pl-10 md:pl-12">
        {/* Vertical red line */}
        <div
          className="absolute left-[4px] top-2 h-[calc(100%-16px)]"
          style={{ width: "1px", backgroundColor: "#dc2626", opacity: 0.5 }}
        />

        <div className="flex flex-col" style={{ gap: "72px" }}>
          {CHRONICLE_ENTRIES.map((entry) => (
            <article key={entry.cycle} className="scroll-reveal relative">
              {/* Red dot marker */}
              <div
                className="absolute flex items-center justify-center"
                style={{
                  left: "-40px",
                  top: "8px",
                  width: "9px",
                  height: "9px",
                }}
              >
                <div
                  className="rounded-full"
                  style={{
                    width: "9px",
                    height: "9px",
                    backgroundColor: "#dc2626",
                    boxShadow: "0 0 6px rgba(220, 38, 38, 0.4)",
                  }}
                />
              </div>

              <span
                className="mb-4 inline-block text-[11px] uppercase tracking-[0.25em] text-accent"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                Cycle {entry.cycle}
              </span>

              <h3
                className="mb-6 text-xl tracking-wide text-foreground md:text-2xl"
                style={{ fontFamily: "var(--font-cinzel)" }}
              >
                {entry.title}
              </h3>

              <p
                className="text-[18px] leading-[1.9] text-muted"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {entry.narrative}
              </p>
            </article>
          ))}
        </div>

        {/* Timeline end cap */}
        <div className="absolute bottom-0" style={{ left: "1px" }}>
          <div
            className="rotate-45"
            style={{
              width: "7px",
              height: "7px",
              backgroundColor: "#dc2626",
              opacity: 0.5,
            }}
          />
        </div>
      </div>
    </section>
  );
}
