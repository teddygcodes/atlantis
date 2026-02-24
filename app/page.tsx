"use client";

import { useState, useCallback, useRef, useEffect } from "react";
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

interface ConversationEntry {
  id: string;
  query: string;
  result: SearchResultData | null;
  error: string | null;
  isLoading: boolean;
  pipelineStatus: string;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const hasSearched = conversation.length > 0;

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [conversation]);

  const handleSearch = useCallback(async () => {
    if (!query.trim() || isLoading) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const entryId = Date.now().toString();
    const currentQuery = query.trim();

    // Add new conversation entry
    const newEntry: ConversationEntry = {
      id: entryId,
      query: currentQuery,
      result: null,
      error: null,
      isLoading: true,
      pipelineStatus: "",
    };

    setConversation((prev) => [...prev, newEntry]);
    setQuery("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: currentQuery }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error("Search request failed");

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
              setConversation((prev) =>
                prev.map((e) =>
                  e.id === entryId
                    ? { ...e, pipelineStatus: data.message }
                    : e
                )
              );
            } else if (data.type === "result") {
              setConversation((prev) =>
                prev.map((e) =>
                  e.id === entryId
                    ? {
                        ...e,
                        result: data.data,
                        isLoading: false,
                        pipelineStatus: "",
                      }
                    : e
                )
              );
            } else if (data.type === "error") {
              setConversation((prev) =>
                prev.map((e) =>
                  e.id === entryId
                    ? { ...e, error: data.message, isLoading: false }
                    : e
                )
              );
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        setConversation((prev) =>
          prev.map((e) =>
            e.id === entryId
              ? {
                  ...e,
                  error: err.message || "Something went wrong",
                  isLoading: false,
                }
              : e
          )
        );
      }
    } finally {
      setIsLoading(false);
    }
  }, [query, isLoading]);

  return (
    <div className="relative flex h-dvh flex-col overflow-hidden">
      <ParticleField />

      {/* About link - top right, always visible */}
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

      {/* ===== LANDING STATE: centered title + search ===== */}
      {!hasSearched && (
        <main className="relative z-10 flex flex-1 flex-col items-center justify-center">
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

          <div className="flex w-full justify-center px-6">
            <SearchBar
              query={query}
              onQueryChange={setQuery}
              onSubmit={handleSearch}
              isCompact={false}
              isLoading={false}
              placeholder="Ask anything..."
            />
          </div>

          <p
            className="hero-wave-line-1 mt-3 text-center"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              fontSize: "12px",
              color: "#444",
            }}
          >
            Powered by Sydyn
          </p>
        </main>
      )}

      {/* ===== CHAT STATE: header, scrollable conversation, bottom input ===== */}
      {hasSearched && (
        <>
          {/* Compact header */}
          <header className="relative z-10 flex items-center justify-center pb-2 pt-5">
            <button
              onClick={() => {
                setConversation([]);
                setQuery("");
              }}
              className="transition-opacity hover:opacity-70"
            >
              <h1
                className="search-title-enter tracking-[0.2em] text-foreground"
                style={{
                  fontFamily: "var(--font-cinzel)",
                  fontSize: "22px",
                  cursor: "pointer",
                }}
              >
                ATLANTIS
              </h1>
            </button>
          </header>

          {/* Scrollable conversation area */}
          <div
            ref={scrollRef}
            className="relative z-10 flex-1 overflow-y-auto"
            style={{
              scrollbarWidth: "thin",
              scrollbarColor: "#1a1a1a transparent",
            }}
          >
            <div className="mx-auto flex w-full max-w-2xl flex-col px-6 py-4">
              {conversation.map((entry, index) => (
                <div key={entry.id}>
                  {/* Divider between entries */}
                  {index > 0 && (
                    <div
                      className="my-8 h-px w-full"
                      style={{ backgroundColor: "#1a1a1a" }}
                    />
                  )}

                  {/* User query bubble */}
                  <div className="mb-5 flex justify-end">
                    <div
                      className="rounded-xl px-4 py-2.5"
                      style={{
                        backgroundColor: "rgba(220, 38, 38, 0.08)",
                        border: "1px solid rgba(220, 38, 38, 0.15)",
                        maxWidth: "85%",
                      }}
                    >
                      <p
                        className="leading-relaxed"
                        style={{
                          fontFamily: "var(--font-cormorant)",
                          fontSize: "16px",
                          fontWeight: 500,
                          color: "#d4d4d4",
                        }}
                      >
                        {entry.query}
                      </p>
                    </div>
                  </div>

                  {/* Pipeline status (during loading) */}
                  {entry.isLoading && entry.pipelineStatus && (
                    <div className="mb-4">
                      <PipelineStatus currentStatus={entry.pipelineStatus} />
                    </div>
                  )}

                  {/* Loading without pipeline status */}
                  {entry.isLoading && !entry.pipelineStatus && (
                    <div className="mb-4 flex items-center gap-2">
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
                  {entry.error && (
                    <p
                      className="mb-4 text-center text-sm"
                      style={{
                        fontFamily: "var(--font-ibm-plex-mono)",
                        color: "#dc2626",
                        fontSize: "12px",
                      }}
                    >
                      {entry.error}
                    </p>
                  )}

                  {/* Results */}
                  {entry.result && <SearchResults data={entry.result} />}
                </div>
              ))}

              {/* Scroll anchor */}
              <div ref={bottomRef} className="h-1" />
            </div>
          </div>

          {/* Bottom search bar - pinned */}
          <div
            className="relative z-10 flex w-full justify-center px-6 pb-5 pt-3"
            style={{
              background:
                "linear-gradient(to top, #000000 60%, transparent 100%)",
            }}
          >
            <SearchBar
              query={query}
              onQueryChange={setQuery}
              onSubmit={handleSearch}
              isCompact={true}
              isLoading={isLoading}
              placeholder="Ask a follow-up..."
            />
          </div>
        </>
      )}
    </div>
  );
}
