"use client";

import { useState, useEffect, useRef } from "react";

interface PipelineStatusProps {
  currentStatus: string;
}

export function PipelineStatus({ currentStatus }: PipelineStatusProps) {
  const [history, setHistory] = useState<string[]>([]);
  const prevStatus = useRef("");

  // Accumulate status messages as they arrive
  useEffect(() => {
    if (currentStatus && currentStatus !== prevStatus.current) {
      prevStatus.current = currentStatus;
      setHistory((prev) => [...prev, currentStatus]);
    }
  }, [currentStatus]);

  if (history.length === 0 && !currentStatus) return null;

  return (
    <div className="flex w-full flex-col gap-1.5">
      {history.map((message, i) => {
        const isLatest = i === history.length - 1;

        return (
          <div
            key={`${i}-${message}`}
            className="flex items-center gap-3 transition-all"
            style={{
              opacity: isLatest ? 1 : 0.35,
            }}
          >
            {/* Status indicator dot */}
            <div className="relative flex h-4 w-4 flex-shrink-0 items-center justify-center">
              {isLatest && (
                <span
                  className="pipeline-pulse absolute h-4 w-4 rounded-full"
                  style={{ backgroundColor: "rgba(220, 38, 38, 0.3)" }}
                />
              )}
              <span
                className="relative h-1.5 w-1.5 rounded-full"
                style={{
                  backgroundColor: isLatest ? "#dc2626" : "#525252",
                }}
              />
            </div>

            {/* Status message */}
            <span
              className="text-[11px] tracking-[0.1em]"
              style={{
                fontFamily: "var(--font-ibm-plex-mono)",
                color: isLatest ? "#dc2626" : "#525252",
              }}
            >
              {message}
            </span>

            {/* Checkmark for completed steps */}
            {!isLatest && (
              <svg
                width="10"
                height="8"
                viewBox="0 0 10 8"
                fill="none"
                style={{ color: "#525252" }}
              >
                <path
                  d="M1 4l3 3 5-6"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </div>
        );
      })}
    </div>
  );
}
