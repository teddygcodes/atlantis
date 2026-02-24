"use client";

import { useState, useCallback, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { SearchBar } from "@/components/search-bar";
import { SearchResults } from "@/components/search-results";
import { PipelineStatus } from "@/components/pipeline-status";
import { ParticleField } from "@/components/particle-field";

interface SearchResultData {
  answer_bullets: string[];
  confidence: "HIGH" | "MODERATE" | "LOW";
  confidence_score: number;
  sources: { title: string; url: string; grade: string }[];
  constitutional_violations: string[];
  audit_trail: {
    mode: string;
    researcher_claims: number;
    adversary_attacks: number;
    attacks_survived: number;
    judge_verdict: string;
    reasoning: string;
  };
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState("");
  const [result, setResult] = useState<SearchResultData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleSearch = useCallback(async () => {
    if (!query.trim() || isLoading) return;

    // Abort any previous request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setHasSearched(true);
    setIsLoading(true);
    setResult(null);
    setError(null);
    setPipelineStatus("");

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() }),
        signal: controller.signal,
      });

      if (!res.ok) {
        throw new Error("Search request failed");
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response stream");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === "status") {
              setPipelineStatus(data.message);
            } else if (data.type === "result") {
              setResult(data.data);
              setPipelineStatus("");
            } else if (data.type === "error") {
              setError(data.message);
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        setError(err.message || "Something went wrong");
      }
    } finally {
      setIsLoading(false);
    }
  }, [query, isLoading]);

  return (
    <div
      className="relative flex min-h-screen flex-col"
      style={{ height: "100dvh", overflow: hasSearched ? "auto" : "hidden" }}
    >
      <ParticleField />

      {/* About link - top right */}
      <div className="absolute right-6 top-5 z-20">
        <Link
          href="/about"
          className="transition-colors hover:opacity-70"
          style={{
            fontFamily: "var(--font-ibm-plex-mono)",
            fontSize: "11px",
            textTransform: "uppercase" as const,
            letterSpacing: "0.15em",
            color: "#525252",
          }}
        >
          About
        </Link>
      </div>

      {/* Main content area */}
      <main
        className="relative z-10 flex flex-1 flex-col items-center"
        style={{
          paddingTop: hasSearched ? "24px" : "0",
          justifyContent: hasSearched ? "flex-start" : "center",
          transition: "padding-top 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        {/* ATLANTIS title - visible before search, hidden during results */}
        {!hasSearched && (
          <div className="hero-wave-title mb-6 flex flex-col items-center">
            <h1
              className="text-center tracking-[0.3em] text-foreground"
              style={{
                fontFamily: "var(--font-cinzel)",
                fontSize: "clamp(36px, 6vw, 64px)",
              }}
            >
              ATLANTIS
            </h1>
          </div>
        )}

        {/* Compact header when searching */}
        {hasSearched && (
          <div className="mb-4 flex items-center gap-3">
            <Link href="/" onClick={() => {
              setHasSearched(false);
              setResult(null);
              setError(null);
              setQuery("");
            }}>
              <h1
                className="search-title-enter tracking-[0.2em] text-foreground transition-opacity hover:opacity-70"
                style={{
                  fontFamily: "var(--font-cinzel)",
                  fontSize: "22px",
                  cursor: "pointer",
                }}
              >
                ATLANTIS
              </h1>
            </Link>
          </div>
        )}

        {/* Search bar */}
        <div
          className="flex w-full justify-center px-6"
          style={{
            marginBottom: hasSearched ? "24px" : "0",
            transition: "margin-bottom 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
        >
          <SearchBar
            query={query}
            onQueryChange={setQuery}
            onSubmit={handleSearch}
            isCompact={hasSearched}
            isLoading={isLoading}
          />
        </div>

        {/* Taglines - below search bar, only before search */}
        {!hasSearched && (
          <div className="mt-6 flex flex-col items-center gap-1.5">
            <p
              className="hero-wave-line-1 text-center"
              style={{
                fontFamily: "var(--font-cormorant)",
                fontSize: "clamp(14px, 2vw, 18px)",
                fontWeight: 600,
                color: "#525252",
              }}
            >
              Hypotheses are proposed.
            </p>
            <p
              className="hero-wave-line-2 text-center"
              style={{
                fontFamily: "var(--font-cormorant)",
                fontSize: "clamp(14px, 2vw, 18px)",
                fontWeight: 600,
                color: "#525252",
              }}
            >
              Challenges are issued.
            </p>
            <p
              className="hero-wave-line-3 text-center"
              style={{
                fontFamily: "var(--font-cormorant)",
                fontSize: "clamp(14px, 2vw, 18px)",
                fontWeight: 600,
                color: "#525252",
              }}
            >
              Only validated knowledge survives.
            </p>
          </div>
        )}

        {/* Results area */}
        {hasSearched && (
          <div className="flex w-full flex-col items-center px-6 pb-24">
            {/* Pipeline status (during loading) */}
            {isLoading && pipelineStatus && (
              <PipelineStatus currentStatus={pipelineStatus} />
            )}

            {/* Loading without pipeline status yet */}
            {isLoading && !pipelineStatus && (
              <div className="flex items-center gap-2">
                <span
                  className="search-loading-dot h-1.5 w-1.5 rounded-full"
                  style={{ backgroundColor: "#dc2626" }}
                />
                <span
                  className="text-[11px] tracking-[0.15em]"
                  style={{
                    fontFamily: "var(--font-ibm-plex-mono)",
                    color: "#525252",
                  }}
                >
                  Initializing pipeline...
                </span>
              </div>
            )}

            {/* Error state */}
            {error && (
              <div className="flex max-w-2xl flex-col items-center gap-2">
                <p
                  className="text-center text-sm"
                  style={{
                    fontFamily: "var(--font-ibm-plex-mono)",
                    color: "#dc2626",
                    fontSize: "12px",
                  }}
                >
                  {error}
                </p>
              </div>
            )}

            {/* Results */}
            {result && <SearchResults data={result} />}
          </div>
        )}
      </main>

      {/* Footer flame logo - bottom center */}
      {!hasSearched && (
        <div className="hero-wave-scroll absolute bottom-6 left-1/2 z-10 -translate-x-1/2">
          <Image
            src="/images/hero-emblem.png"
            alt="Atlantis emblem"
            width={40}
            height={40}
            className="object-contain opacity-20"
            style={{ width: "40px", height: "40px" }}
          />
        </div>
      )}
    </div>
  );
}
