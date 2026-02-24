"use client";

import { useRef, useEffect } from "react";
import { Search } from "lucide-react";

interface SearchBarProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSubmit: () => void;
  isCompact: boolean;
  isLoading: boolean;
}

export function SearchBar({
  query,
  onQueryChange,
  onSubmit,
  isCompact,
  isLoading,
}: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isCompact) {
      inputRef.current?.focus();
    }
  }, [isCompact]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && query.trim() && !isLoading) {
      onSubmit();
    }
  };

  return (
    <div
      className="group relative flex w-full items-center overflow-hidden rounded-xl transition-all"
      style={{
        maxWidth: isCompact ? "640px" : "600px",
        border: isLoading
          ? "1.5px solid rgba(220, 38, 38, 0.4)"
          : "1.5px solid rgba(220, 38, 38, 0.2)",
        backgroundColor: "#0a0a0a",
        boxShadow: isLoading
          ? "0 0 24px rgba(220, 38, 38, 0.12)"
          : "0 4px 24px rgba(0, 0, 0, 0.35), 0 0 0 0.5px rgba(220, 38, 38, 0.08)",
      }}
    >
      <div className="flex h-12 flex-shrink-0 items-center justify-center pl-4">
        <Search
          size={16}
          style={{
            color: isLoading ? "#dc2626" : "#525252",
            transition: "color 0.3s ease",
          }}
        />
      </div>

      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything..."
        disabled={isLoading}
        className="h-12 flex-1 border-none bg-transparent px-3 outline-none placeholder:text-[#333]"
        style={{
          fontFamily: "var(--font-cormorant)",
          fontSize: isCompact ? "15px" : "17px",
          fontWeight: 500,
          color: "#e5e5e5",
        }}
        aria-label="Search query"
      />

      {query.trim() && !isLoading && (
        <button
          onClick={onSubmit}
          className="mr-2 flex h-8 items-center justify-center rounded-lg px-3 transition-all hover:opacity-80"
          style={{
            backgroundColor: "rgba(220, 38, 38, 0.15)",
            border: "1px solid rgba(220, 38, 38, 0.25)",
          }}
          aria-label="Submit search"
        >
          <span
            className="text-[10px] uppercase tracking-[0.2em]"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              color: "#dc2626",
            }}
          >
            Ask
          </span>
        </button>
      )}

      {isLoading && (
        <div className="mr-3 flex items-center">
          <span
            className="search-loading-dot h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: "#dc2626" }}
          />
        </div>
      )}
    </div>
  );
}
