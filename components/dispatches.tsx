"use client";

import { useState } from "react";
import { DISPATCHES, type Dispatch } from "@/lib/data";

export function Dispatches() {
  const [selectedArticle, setSelectedArticle] = useState<Dispatch | null>(null);

  if (selectedArticle) {
    return (
      <ArticleView
        article={selectedArticle}
        onBack={() => setSelectedArticle(null)}
      />
    );
  }

  return (
    <section className="mx-auto max-w-3xl">
      <header className="mb-16 animate-fade-in-up">
        <h1
          className="mb-4 text-4xl tracking-[0.2em] text-foreground md:text-5xl"
          style={{ fontFamily: "var(--font-cinzel)" }}
        >
          Dispatches
        </h1>
        <p
          className="text-xl leading-relaxed text-muted"
          style={{ fontFamily: "var(--font-cormorant)" }}
        >
          Long-form analysis of what the debates reveal about knowledge,
          argumentation, and the structure of ideas.
        </p>
      </header>

      <div className="flex flex-col gap-8">
        {DISPATCHES.map((dispatch, index) => (
          <article
            key={dispatch.title}
            className={`animate-fade-in-up animation-delay-${(index + 1) * 100} group cursor-pointer border-b border-border pb-8 transition-colors last:border-b-0`}
            onClick={() => setSelectedArticle(dispatch)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setSelectedArticle(dispatch);
              }
            }}
          >
            <span
              className="mb-3 inline-block text-xs tracking-[0.2em] text-accent"
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {dispatch.domain.toUpperCase()} &middot; CYCLE {dispatch.cycle}
            </span>

            <h2
              className="mb-3 text-2xl leading-snug tracking-wide text-foreground transition-colors group-hover:text-accent md:text-3xl"
              style={{ fontFamily: "var(--font-cinzel)" }}
            >
              {dispatch.title}
            </h2>

            <p
              className="text-lg leading-relaxed text-muted"
              style={{ fontFamily: "var(--font-cormorant)" }}
            >
              {dispatch.excerpt}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ArticleView({
  article,
  onBack,
}: {
  article: Dispatch;
  onBack: () => void;
}) {
  return (
    <article className="mx-auto max-w-3xl animate-fade-in-up">
      <button
        onClick={onBack}
        className="mb-8 text-sm text-muted transition-colors hover:text-foreground"
        style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
      >
        &larr; Back to Dispatches
      </button>

      <span
        className="mb-4 inline-block text-xs tracking-[0.2em] text-accent"
        style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
      >
        {article.domain.toUpperCase()} &middot; CYCLE {article.cycle}
      </span>

      <h1
        className="mb-10 text-3xl leading-snug tracking-wide text-foreground md:text-4xl"
        style={{ fontFamily: "var(--font-cinzel)" }}
      >
        {article.title}
      </h1>

      <div className="flex flex-col gap-6">
        {article.body.split("\n\n").map((paragraph, i) => (
          <p
            key={i}
            className="text-xl leading-relaxed text-foreground/85"
            style={{ fontFamily: "var(--font-cormorant)" }}
          >
            {paragraph}
          </p>
        ))}
      </div>
    </article>
  );
}
