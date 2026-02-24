"use client";

import { useRef, useEffect } from "react";
import { Search } from "lucide-react";

interface SearchBarProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSubmit: () => void;
  isCompact: boolean;
  isLoading: boolean;
  placeholder?: string;
}

export function SearchBar({
  query,
  onQueryChange,
  onSubmit,
  isCompact,
  isLoading,
  placeholder = "Ask anything...",
}: SearchBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isLoading) {
      textareaRef.current?.focus();
    }
  }, [isLoading]);

  // Auto-resize textarea to fit content
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "0px";
      el.style.height = Math.min(el.scrollHeight, 160) + "px";
    }
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && query.trim() && !isLoading) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div
      className="group relative flex w-full items-start overflow-hidden rounded-xl transition-all"
      style={{
        maxWidth: isCompact ? "640px" : "600px",
        border: isLoading
          ? "1.5px solid rgba(220, 38, 38, 0.7)"
          : "1.5px solid rgba(220, 38, 38, 0.45)",
        backgroundColor: "#0a0a0a",
        boxShadow: isLoading
          ? "0 0 28px rgba(220, 38, 38, 0.2)"
          : "0 4px 24px rgba(0, 0, 0, 0.35), 0 0 12px rgba(220, 38, 38, 0.1)",
      }}
    >
      <div className="flex flex-shrink-0 items-start justify-center pl-4 pt-3.5">
        <Search
          size={16}
          style={{
            color: isLoading ? "#dc2626" : "#525252",
            transition: "color 0.3s ease",
          }}
        />
      </div>

      <textarea
        ref={textareaRef}
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading}
        rows={1}
        className="flex-1 resize-none border-none bg-transparent px-3 py-3 outline-none placeholder:text-[#333]"
        style={{
          fontFamily: "var(--font-cormorant)",
          fontSize: isCompact ? "15px" : "17px",
          fontWeight: 500,
          color: "#e5e5e5",
          lineHeight: "1.5",
          maxHeight: "160px",
          overflow: "auto",
        }}
        aria-label="Search query"
      />

      {query.trim() && !isLoading && (
        <button
          onClick={onSubmit}
          className="mr-2 mt-2 flex h-8 flex-shrink-0 items-center justify-center rounded-lg px-3 transition-all hover:opacity-80"
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
        <div className="mr-3 mt-3.5 flex flex-shrink-0 items-center">
          <span
            className="search-loading-dot h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: "#dc2626" }}
          />
        </div>
      )}
    </div>
  );
}
