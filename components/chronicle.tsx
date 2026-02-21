"use client";

import { CHRONICLE_ENTRIES } from "@/lib/data";

export function Chronicle() {
  return (
    <section className="mx-auto max-w-[800px] py-8">
      <header className="mb-20 animate-fade-in-up">
        <h1
          className="mb-6 text-2xl tracking-[0.2em] text-foreground md:text-3xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          Chronicle
        </h1>
        <p
          className="text-lg leading-[1.8] text-muted md:text-xl"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          A record of what happened. Each cycle brings new claims, new
          challenges, and new ruins.
        </p>
      </header>

      <div className="relative pl-8 md:pl-10">
        {/* Timeline line */}
        <div
          className="absolute left-0 top-0 h-full"
          style={{ width: "1px", backgroundColor: "#dc2626" }}
        />

        <div className="flex flex-col gap-20">
          {CHRONICLE_ENTRIES.map((entry, index) => (
            <article
              key={entry.cycle}
              className={`animate-fade-in-up relative animation-delay-${(index + 1) * 100}`}
            >
              {/* Timeline marker - red circle */}
              <div
                className="absolute top-[6px] flex items-center justify-center"
                style={{ left: "-32px", width: "9px", height: "9px" }}
              >
                <div
                  className="rounded-full"
                  style={{
                    width: "9px",
                    height: "9px",
                    backgroundColor: "#dc2626",
                  }}
                />
              </div>

              <span
                className="mb-3 inline-block text-[11px] uppercase tracking-[0.25em] text-accent"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                Cycle {entry.cycle}
              </span>

              <h2
                className="mb-5 text-xl tracking-wide text-foreground md:text-2xl"
                style={{ fontFamily: "var(--font-cinzel)" }}
              >
                {entry.title}
              </h2>

              <p
                className="text-lg leading-[1.8] text-muted"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {entry.narrative}
              </p>
            </article>
          ))}
        </div>

        {/* Timeline end marker */}
        <div
          className="absolute bottom-0"
          style={{ left: "-3px" }}
        >
          <div
            className="rotate-45"
            style={{
              width: "7px",
              height: "7px",
              backgroundColor: "#dc2626",
            }}
          />
        </div>
      </div>
    </section>
  );
}
