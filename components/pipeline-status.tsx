"use client";

const STAGE_ORDER = [
  "Searching sources...",
  "Researcher drafting...",
  "Adversary attacking...",
  "Judge reviewing...",
];

export function PipelineStatus({ currentStatus }: { currentStatus: string }) {
  const currentIndex = STAGE_ORDER.indexOf(currentStatus);

  return (
    <div className="flex w-full max-w-2xl flex-col gap-2">
      {STAGE_ORDER.map((stage, i) => {
        const isActive = stage === currentStatus;
        const isComplete = i < currentIndex;
        const isPending = i > currentIndex;

        return (
          <div
            key={stage}
            className="flex items-center gap-3 transition-all"
            style={{
              opacity: isPending ? 0.25 : isComplete ? 0.5 : 1,
            }}
          >
            {/* Status indicator */}
            <div className="relative flex h-4 w-4 items-center justify-center">
              {isActive && (
                <span
                  className="pipeline-pulse absolute h-4 w-4 rounded-full"
                  style={{ backgroundColor: "rgba(220, 38, 38, 0.3)" }}
                />
              )}
              <span
                className="relative h-1.5 w-1.5 rounded-full"
                style={{
                  backgroundColor: isActive
                    ? "#dc2626"
                    : isComplete
                      ? "#525252"
                      : "#1a1a1a",
                }}
              />
            </div>

            {/* Stage label */}
            <span
              className="text-[11px] tracking-[0.15em]"
              style={{
                fontFamily: "var(--font-ibm-plex-mono)",
                color: isActive
                  ? "#dc2626"
                  : isComplete
                    ? "#525252"
                    : "#1a1a1a",
              }}
            >
              {stage}
            </span>

            {/* Checkmark for completed stages */}
            {isComplete && (
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
