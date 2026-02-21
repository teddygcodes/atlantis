"use client";

import { useState, useCallback } from "react";

const cache = new Map<string, string>();

export function ExplainSimply({
  text,
  type = "academic text",
}: {
  text: string;
  type?: string;
}) {
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const handleClick = useCallback(
    async (e: React.MouseEvent | React.KeyboardEvent) => {
      e.stopPropagation();
      e.preventDefault();

      if (open) {
        setOpen(false);
        return;
      }

      setOpen(true);

      const cacheKey = `${type}::${text}`;
      if (cache.has(cacheKey)) {
        setExplanation(cache.get(cacheKey)!);
        return;
      }

      setLoading(true);
      try {
        const res = await fetch("/api/explain", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, type }),
        });
        const data = await res.json();
        if (!res.ok || !data.explanation) {
          throw new Error(data.error || "Failed");
        }
        cache.set(cacheKey, data.explanation);
        setExplanation(data.explanation);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        console.error("[v0] ExplainSimply client error:", msg);
        setExplanation(`Error: ${msg}`);
      } finally {
        setLoading(false);
      }
    },
    [open, text, type]
  );

  return (
    <div
      style={{ textAlign: "left", width: "100%" }}
      onClick={(e) => e.stopPropagation()}
    >
      <span
        role="button"
        tabIndex={0}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") handleClick(e);
        }}
        style={{
          fontFamily: "var(--font-ibm-plex-mono)",
          fontSize: "10px",
          color: "#dc2626",
          letterSpacing: "0.08em",
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "4px 0",
          marginTop: "8px",
          display: "inline-block",
          transition: "opacity 0.2s, text-decoration 0.2s",
          textDecoration: "none",
          opacity: 0.8,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.textDecoration = "underline";
          e.currentTarget.style.opacity = "1";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.textDecoration = "none";
          e.currentTarget.style.opacity = "0.8";
        }}
      >
        {open ? "HIDE EXPLANATION" : "WHAT DOES THIS MEAN?"}
      </span>

      {open && (
        <div
          style={{
            marginTop: "10px",
            padding: "16px 20px",
            backgroundColor: "#0e0e0e",
            border: "1px solid #1c1c1c",
            borderLeft: "4px solid #dc2626",
            borderRadius: "4px",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              fontSize: "9px",
              color: "#dc2626",
              letterSpacing: "0.2em",
              display: "block",
              marginBottom: "8px",
            }}
          >
            IN PLAIN ENGLISH:
          </span>

          {loading ? (
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div
                style={{
                  width: "12px",
                  height: "12px",
                  border: "1.5px solid #dc262640",
                  borderTopColor: "#dc2626",
                  borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }}
              />
              <span
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  fontSize: "10px",
                  color: "#525252",
                  letterSpacing: "0.1em",
                }}
              >
                THINKING...
              </span>
            </div>
          ) : (
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "16px",
                fontStyle: "italic",
                color: "#a3a3a3",
                lineHeight: "1.7",
                margin: 0,
                fontWeight: 500,
              }}
            >
              {explanation}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
