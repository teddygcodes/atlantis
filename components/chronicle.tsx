"use client";

import { CHRONICLE_ENTRIES } from "@/lib/data";

export function Chronicle() {
  return (
    <section>
      <header className="mb-16 animate-fade-in-up">
        <h1
          className="mb-4 text-4xl tracking-[0.2em] text-foreground md:text-5xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          Chronicle
        </h1>
        <p
          className="max-w-2xl text-xl leading-relaxed text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          A record of what happened. Each cycle brings new claims, new
          challenges, and new ruins.
        </p>
      </header>

      <div className="relative ml-4 md:ml-8">
        {/* Timeline line */}
        <div className="absolute left-0 top-0 h-full w-px bg-accent" />

        <div className="flex flex-col gap-16">
          {CHRONICLE_ENTRIES.map((entry, index) => (
            <article
              key={entry.cycle}
              className={`animate-fade-in-up relative pl-10 md:pl-14 animation-delay-${(index + 1) * 100}`}
            >
              {/* Timeline marker */}
              <div className="absolute left-0 top-1 flex -translate-x-1/2 items-center justify-center">
                <div className="h-3 w-3 rounded-full border-2 border-accent bg-background" />
              </div>

              <span
                className="mb-2 inline-block text-xs tracking-[0.25em] text-accent"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                CYCLE {entry.cycle}
              </span>

              <h2
                className="mb-4 text-2xl tracking-wide text-foreground md:text-3xl"
                style={{ fontFamily: "var(--font-cinzel)" }}
              >
                {entry.title}
              </h2>

              <p
                className="max-w-3xl text-lg leading-relaxed text-muted"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {entry.narrative}
              </p>
            </article>
          ))}
        </div>

        {/* Timeline end marker */}
        <div className="absolute bottom-0 left-0 -translate-x-1/2">
          <div className="h-2 w-2 rotate-45 bg-accent" />
        </div>
      </div>
    </section>
  );
}
