"use client";

import { NEWS_ITEMS } from "@/lib/data";

export function Newsroom() {
  return (
    <section>
      <header className="mb-16 animate-fade-in-up">
        <h1
          className="mb-4 text-4xl tracking-[0.2em] text-foreground md:text-5xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          Newsroom
        </h1>
        <p
          className="max-w-2xl text-xl leading-relaxed text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          Breaking developments from the frontier of structured peer review.
        </p>
      </header>

      <div className="flex flex-col gap-6">
        {NEWS_ITEMS.map((item, index) => (
          <article
            key={item.headline}
            className={`animate-fade-in-up animation-delay-${(index + 1) * 100} flex overflow-hidden rounded border border-border bg-surface`}
          >
            <div className="w-1 shrink-0 bg-accent" />
            <div className="p-6">
              <h2
                className="mb-3 text-sm font-bold leading-snug tracking-wide text-foreground"
                style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
              >
                {item.headline}
              </h2>
              <p
                className="text-lg leading-relaxed text-muted"
                style={{ fontFamily: "var(--font-cormorant)" }}
              >
                {item.body}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
