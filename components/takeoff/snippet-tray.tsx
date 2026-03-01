"use client";

import { useState, useCallback } from "react";
import type { SnippetData } from "./drawing-viewer";

interface SnippetTrayProps {
  snippets: SnippetData[];
  onDeleteSnippet: (id: string) => void;
  onRelabelSnippet: (id: string, label: string, subLabel: string) => void;
  onHighlightSnippet: (snippet: SnippetData | null) => void;
  onRunTakeoff: (mode: string) => void;
  isRunning: boolean;
}

const LABEL_COLORS: Record<string, { bg: string; text: string }> = {
  fixture_schedule: { bg: "rgba(16,185,129,0.12)", text: "#10b981" },
  rcp: { bg: "rgba(220,38,38,0.12)", text: "#dc2626" },
  panel_schedule: { bg: "rgba(59,130,246,0.12)", text: "#3b82f6" },
  plan_notes: { bg: "rgba(245,158,11,0.12)", text: "#f59e0b" },
  detail: { bg: "rgba(139,92,246,0.12)", text: "#8b5cf6" },
  site_plan: { bg: "rgba(20,184,166,0.12)", text: "#14b8a6" },
};

const LABEL_DISPLAY: Record<string, string> = {
  fixture_schedule: "FIXTURE SCHEDULE",
  rcp: "RCP",
  panel_schedule: "PANEL SCHEDULE",
  plan_notes: "PLAN NOTES",
  detail: "DETAIL",
  site_plan: "SITE PLAN",
};

const SNIPPET_LABEL_OPTIONS = [
  { value: "fixture_schedule", label: "Fixture Schedule" },
  { value: "rcp", label: "RCP" },
  { value: "panel_schedule", label: "Panel Schedule" },
  { value: "plan_notes", label: "Plan Notes" },
  { value: "detail", label: "Detail" },
  { value: "site_plan", label: "Site Plan" },
];

function getReadinessStatus(snippets: SnippetData[]): {
  ready: boolean;
  message: string;
  counts: Record<string, number>;
} {
  const counts: Record<string, number> = {};
  for (const s of snippets) {
    counts[s.label] = (counts[s.label] || 0) + 1;
  }
  const hasSchedule = (counts["fixture_schedule"] || 0) >= 1;
  const hasRcp = (counts["rcp"] || 0) >= 1;

  const parts: string[] = [];
  if (counts["fixture_schedule"]) parts.push(`${counts["fixture_schedule"]} Fixture Schedule`);
  if (counts["rcp"]) parts.push(`${counts["rcp"]} RCP${counts["rcp"] > 1 ? "s" : ""}`);
  if (counts["panel_schedule"]) parts.push(`${counts["panel_schedule"]} Panel Schedule`);
  if (counts["plan_notes"]) parts.push(`${counts["plan_notes"]} Plan Notes`);
  if (counts["detail"]) parts.push(`${counts["detail"]} Detail${counts["detail"] > 1 ? "s" : ""}`);
  if (counts["site_plan"]) parts.push(`${counts["site_plan"]} Site Plan`);

  if (!hasSchedule && !hasRcp) {
    return { ready: false, message: "Need 1 Fixture Schedule + 1 RCP to run", counts };
  }
  if (!hasSchedule) {
    return { ready: false, message: "Need 1 Fixture Schedule snippet", counts };
  }
  if (!hasRcp) {
    return { ready: false, message: "Need at least 1 RCP snippet", counts };
  }

  return {
    ready: true,
    message: parts.join(", ") + " — Ready",
    counts,
  };
}

export function SnippetTray({
  snippets,
  onDeleteSnippet,
  onRelabelSnippet,
  onHighlightSnippet,
  onRunTakeoff,
  isRunning,
}: SnippetTrayProps) {
  const [mode, setMode] = useState("strict");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [editSubLabel, setEditSubLabel] = useState("");

  const { ready, message, counts } = getReadinessStatus(snippets);

  const startEdit = useCallback((snippet: SnippetData) => {
    setEditingId(snippet.id);
    setEditLabel(snippet.label);
    setEditSubLabel(snippet.sub_label);
  }, []);

  const confirmEdit = useCallback(
    (id: string) => {
      onRelabelSnippet(id, editLabel, editSubLabel);
      setEditingId(null);
    },
    [editLabel, editSubLabel, onRelabelSnippet]
  );

  // Group snippets by label
  const grouped = snippets.reduce<Record<string, SnippetData[]>>((acc, s) => {
    if (!acc[s.label]) acc[s.label] = [];
    acc[s.label].push(s);
    return acc;
  }, {});

  const labelOrder = ["fixture_schedule", "rcp", "panel_schedule", "plan_notes", "detail", "site_plan"];

  return (
    <div
      className="flex h-full flex-col"
      style={{ background: "#060606", borderLeft: "1px solid #1a1a1a" }}
    >
      {/* Header */}
      <div
        className="border-b px-4 py-3"
        style={{ borderColor: "#1a1a1a", background: "#0a0a0a" }}
      >
        <h2
          className="mb-1 tracking-[0.2em]"
          style={{
            fontFamily: "var(--font-cinzel)",
            fontSize: "11px",
            color: "#525252",
          }}
        >
          SNIPPET TRAY
        </h2>
        <p
          className="text-xs"
          style={{
            fontFamily: "var(--font-ibm-plex-mono)",
            color: ready ? "#10b981" : "#666",
            fontSize: "10px",
          }}
        >
          {snippets.length === 0 ? "No snippets captured yet" : message}
        </p>
      </div>

      {/* Snippets list */}
      <div
        className="flex-1 overflow-y-auto"
        style={{ scrollbarWidth: "thin", scrollbarColor: "#1a1a1a transparent" }}
      >
        {snippets.length === 0 ? (
          <div className="flex h-full items-center justify-center p-6">
            <p
              className="text-center text-xs"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#333" }}
            >
              Use the ✂ SNIP tool to capture
              <br />
              regions from the drawing
            </p>
          </div>
        ) : (
          <div className="p-3">
            {labelOrder.map((labelKey) => {
              const group = grouped[labelKey];
              if (!group) return null;
              const color = LABEL_COLORS[labelKey] || { bg: "rgba(255,255,255,0.05)", text: "#666" };
              return (
                <div key={labelKey} className="mb-4">
                  <div
                    className="mb-2 flex items-center gap-2 px-1"
                  >
                    <span
                      className="rounded px-2 py-0.5 text-xs"
                      style={{
                        fontFamily: "var(--font-ibm-plex-mono)",
                        fontSize: "9px",
                        letterSpacing: "0.1em",
                        background: color.bg,
                        color: color.text,
                      }}
                    >
                      {LABEL_DISPLAY[labelKey]}
                    </span>
                    <span
                      className="text-xs"
                      style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#444", fontSize: "10px" }}
                    >
                      {group.length}
                    </span>
                  </div>

                  {group.map((snippet) => (
                    <div
                      key={snippet.id}
                      className="mb-2 rounded"
                      style={{ border: "1px solid #1a1a1a", background: "#0a0a0a" }}
                    >
                      {editingId === snippet.id ? (
                        // Edit mode
                        <div className="p-3">
                          <select
                            value={editLabel}
                            onChange={(e) => setEditLabel(e.target.value)}
                            className="mb-2 w-full rounded px-2 py-1 text-xs"
                            style={{
                              background: "#111",
                              border: "1px solid #1a1a1a",
                              color: "#d4d4d4",
                              fontFamily: "var(--font-ibm-plex-mono)",
                              fontSize: "11px",
                            }}
                          >
                            {SNIPPET_LABEL_OPTIONS.map((opt) => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                          <input
                            type="text"
                            value={editSubLabel}
                            onChange={(e) => setEditSubLabel(e.target.value)}
                            placeholder="Area name (optional)"
                            className="mb-2 w-full rounded px-2 py-1 text-xs"
                            style={{
                              background: "#111",
                              border: "1px solid #1a1a1a",
                              color: "#d4d4d4",
                              fontFamily: "var(--font-ibm-plex-mono)",
                              fontSize: "11px",
                            }}
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => confirmEdit(snippet.id)}
                              className="flex-1 rounded py-1 text-xs"
                              style={{
                                fontFamily: "var(--font-ibm-plex-mono)",
                                background: "#dc2626",
                                color: "#fff",
                                fontSize: "10px",
                              }}
                            >
                              SAVE
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="rounded px-2 py-1 text-xs"
                              style={{
                                fontFamily: "var(--font-ibm-plex-mono)",
                                background: "transparent",
                                color: "#525252",
                                border: "1px solid #1a1a1a",
                                fontSize: "10px",
                              }}
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      ) : (
                        // Display mode
                        <div
                          className="flex cursor-pointer items-start gap-2 p-2"
                          onMouseEnter={() => onHighlightSnippet(snippet)}
                          onMouseLeave={() => onHighlightSnippet(null)}
                        >
                          {/* Thumbnail */}
                          <div
                            className="flex-shrink-0 overflow-hidden rounded"
                            style={{ width: "52px", height: "38px", border: "1px solid #1a1a1a" }}
                          >
                            <img
                              src={snippet.image_data}
                              alt={snippet.label}
                              className="h-full w-full object-cover"
                            />
                          </div>

                          {/* Info */}
                          <div className="min-w-0 flex-1">
                            <p
                              className="truncate text-xs"
                              style={{
                                fontFamily: "var(--font-ibm-plex-mono)",
                                color: "#d4d4d4",
                                fontSize: "10px",
                              }}
                            >
                              {snippet.sub_label || LABEL_DISPLAY[snippet.label]}
                            </p>
                            <p
                              style={{
                                fontFamily: "var(--font-ibm-plex-mono)",
                                color: "#444",
                                fontSize: "9px",
                              }}
                            >
                              p.{snippet.page_number}
                            </p>
                          </div>

                          {/* Actions */}
                          <div className="flex gap-1">
                            <button
                              onClick={() => startEdit(snippet)}
                              className="rounded p-1 text-xs transition-colors hover:text-white"
                              style={{ color: "#444" }}
                              title="Relabel"
                            >
                              ✎
                            </button>
                            <button
                              onClick={() => onDeleteSnippet(snippet.id)}
                              className="rounded p-1 text-xs transition-colors hover:text-red-500"
                              style={{ color: "#444" }}
                              title="Delete"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Run Takeoff footer */}
      <div
        className="border-t p-4"
        style={{ borderColor: "#1a1a1a", background: "#0a0a0a" }}
      >
        {/* Mode selector */}
        <div className="mb-3 flex gap-1">
          {["fast", "strict", "liability"].map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className="flex-1 rounded py-1.5 text-xs uppercase transition-colors"
              style={{
                fontFamily: "var(--font-ibm-plex-mono)",
                fontSize: "9px",
                letterSpacing: "0.1em",
                background: mode === m ? "#1a1a1a" : "transparent",
                color: mode === m ? "#d4d4d4" : "#444",
                border: `1px solid ${mode === m ? "#333" : "#1a1a1a"}`,
              }}
            >
              {m}
            </button>
          ))}
        </div>

        <button
          onClick={() => ready && !isRunning && onRunTakeoff(mode)}
          disabled={!ready || isRunning}
          className="w-full rounded py-2.5 text-xs font-medium uppercase transition-all"
          style={{
            fontFamily: "var(--font-ibm-plex-mono)",
            letterSpacing: "0.15em",
            background: ready && !isRunning ? "#dc2626" : "#1a1a1a",
            color: ready && !isRunning ? "#fff" : "#444",
            cursor: ready && !isRunning ? "pointer" : "not-allowed",
          }}
        >
          {isRunning ? "RUNNING TAKEOFF..." : "RUN TAKEOFF"}
        </button>

        {!ready && snippets.length > 0 && (
          <p
            className="mt-2 text-center text-xs"
            style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#444", fontSize: "10px" }}
          >
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
