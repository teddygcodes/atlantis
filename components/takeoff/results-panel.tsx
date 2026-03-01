"use client";

import { useState, useCallback } from "react";

interface FixtureCount {
  type_tag: string;
  description: string;
  total: number;
  counts_by_area: Record<string, number>;
  difficulty: string;
  notes?: string;
  accessories?: string[];
  flags?: string[];
  confidence?: number;
}

interface AdversarialEntry {
  attack_id: string;
  severity: "critical" | "major" | "minor";
  category: string;
  description: string;
  resolution?: string;
  verdict?: string;
}

interface ConstitutionalViolation {
  rule: string;
  severity: string;
  explanation: string;
}

interface ConfidenceBreakdown {
  schedule_match_rate?: number;
  area_coverage?: number;
  adversarial_resolved?: number;
  constitutional_clean?: number;
  cross_reference_match?: number;
  note_compliance?: number;
  fast_mode_penalty?: number;
}

export interface TakeoffResultData {
  job_id?: string;
  drawing_name?: string;
  mode?: string;
  fixture_counts: FixtureCount[];
  grand_total: number;
  areas_covered: string[];
  confidence_score: number;
  confidence_band: string;
  confidence_breakdown?: ConfidenceBreakdown;
  constitutional_violations: ConstitutionalViolation[];
  adversarial_log: AdversarialEntry[];
  judge_verdict: string;
  flags: string[];
  ruling_summary?: string;
}

interface ResultsPanelProps {
  data: TakeoffResultData;
  pipelineStatus?: string;
  isLoading?: boolean;
}

const DIFFICULTY_LABELS: Record<string, { label: string; color: string }> = {
  S: { label: "Standard", color: "#10b981" },
  M: { label: "Moderate", color: "#f59e0b" },
  D: { label: "Difficult", color: "#f97316" },
  E: { label: "Extreme", color: "#dc2626" },
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#dc2626",
  major: "#f59e0b",
  minor: "#3b82f6",
  FATAL: "#dc2626",
  MAJOR: "#f59e0b",
  MINOR: "#3b82f6",
};

const BAND_COLORS: Record<string, string> = {
  HIGH: "#10b981",
  MODERATE: "#f59e0b",
  LOW: "#f97316",
  VERY_LOW: "#dc2626",
};

const VERDICT_COLORS: Record<string, string> = {
  PASS: "#10b981",
  WARN: "#f59e0b",
  BLOCK: "#dc2626",
};

function exportToCSV(data: TakeoffResultData) {
  const rows = [
    ["Type Tag", "Description", "Total", "Difficulty", ...data.areas_covered, "Flags"],
    ...data.fixture_counts.map((f) => [
      f.type_tag,
      f.description,
      String(f.total),
      f.difficulty,
      ...data.areas_covered.map((area) => String(f.counts_by_area[area] ?? 0)),
      (f.flags || []).join("; "),
    ]),
    [],
    ["GRAND TOTAL", "", String(data.grand_total)],
    ["Confidence", "", `${(data.confidence_score * 100).toFixed(0)}% (${data.confidence_band})`],
    ["Verdict", "", data.judge_verdict],
  ];

  const csv = rows
    .map((row) => row.map((cell) => `"${cell}"`).join(","))
    .join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `takeoff_${data.drawing_name || "results"}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export function ResultsPanel({ data, pipelineStatus, isLoading }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<"counts" | "adversarial" | "confidence">("counts");
  const [expandedArea, setExpandedArea] = useState<string | null>(null);

  const confidenceColor = BAND_COLORS[data.confidence_band] || "#666";
  const verdictColor = VERDICT_COLORS[data.judge_verdict] || "#666";

  const handleExport = useCallback(() => exportToCSV(data), [data]);

  if (isLoading) {
    return (
      <div
        className="flex h-full flex-col items-center justify-center gap-4 p-8"
        style={{ background: "#060606" }}
      >
        <div
          className="h-2 w-2 animate-pulse rounded-full"
          style={{ background: "#dc2626" }}
        />
        <p
          className="text-center text-xs"
          style={{
            fontFamily: "var(--font-ibm-plex-mono)",
            color: "#525252",
            letterSpacing: "0.1em",
          }}
        >
          {pipelineStatus || "RUNNING PIPELINE..."}
        </p>
      </div>
    );
  }

  return (
    <div
      className="flex h-full flex-col"
      style={{ background: "#060606" }}
    >
      {/* ── Summary Header ── */}
      <div
        className="border-b px-5 py-4"
        style={{ borderColor: "#1a1a1a", background: "#0a0a0a" }}
      >
        <div className="mb-3 flex items-start justify-between">
          <div>
            <h2
              className="mb-0.5 tracking-[0.2em]"
              style={{
                fontFamily: "var(--font-cinzel)",
                fontSize: "11px",
                color: "#525252",
              }}
            >
              TAKEOFF RESULTS
            </h2>
            {data.drawing_name && (
              <p
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  fontSize: "10px",
                  color: "#333",
                }}
              >
                {data.drawing_name}
                {data.mode && (
                  <span className="ml-2 uppercase" style={{ color: "#444" }}>
                    ({data.mode})
                  </span>
                )}
              </p>
            )}
          </div>
          <button
            onClick={handleExport}
            className="rounded px-3 py-1.5 text-xs transition-colors hover:opacity-80"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              background: "#1a1a1a",
              color: "#d4d4d4",
              letterSpacing: "0.08em",
              fontSize: "10px",
            }}
          >
            ↓ CSV
          </button>
        </div>

        {/* Key metrics row */}
        <div className="flex gap-6">
          <div>
            <p
              className="mb-0.5 text-xs"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#525252", fontSize: "9px" }}
            >
              TOTAL FIXTURES
            </p>
            <p
              className="text-2xl font-bold"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#d4d4d4" }}
            >
              {data.grand_total.toLocaleString()}
            </p>
          </div>

          <div>
            <p
              className="mb-0.5 text-xs"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#525252", fontSize: "9px" }}
            >
              CONFIDENCE
            </p>
            <p
              className="text-2xl font-bold"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: confidenceColor }}
            >
              {(data.confidence_score * 100).toFixed(0)}%
              <span className="ml-2 text-sm" style={{ color: confidenceColor }}>
                {data.confidence_band}
              </span>
            </p>
          </div>

          <div>
            <p
              className="mb-0.5 text-xs"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#525252", fontSize: "9px" }}
            >
              VERDICT
            </p>
            <p
              className="text-xl font-bold"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: verdictColor }}
            >
              {data.judge_verdict === "PASS" ? "✓ PASS" : data.judge_verdict === "WARN" ? "⚠ WARN" : "✗ BLOCK"}
            </p>
          </div>
        </div>

        {/* Ruling summary */}
        {data.ruling_summary && (
          <p
            className="mt-2 text-xs"
            style={{
              fontFamily: "var(--font-cormorant)",
              color: "#525252",
              fontSize: "13px",
              fontStyle: "italic",
            }}
          >
            {data.ruling_summary}
          </p>
        )}
      </div>

      {/* ── Tabs ── */}
      <div
        className="flex border-b"
        style={{ borderColor: "#1a1a1a", background: "#0a0a0a" }}
      >
        {(["counts", "adversarial", "confidence"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className="px-4 py-2.5 text-xs uppercase transition-colors"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              fontSize: "9px",
              letterSpacing: "0.1em",
              color: activeTab === tab ? "#d4d4d4" : "#444",
              borderBottom: activeTab === tab ? "1px solid #dc2626" : "1px solid transparent",
              marginBottom: "-1px",
            }}
          >
            {tab === "counts" && `Counts (${data.fixture_counts.length})`}
            {tab === "adversarial" && `Adversarial (${data.adversarial_log.length})`}
            {tab === "confidence" && "Confidence"}
          </button>
        ))}
      </div>

      {/* ── Tab Content ── */}
      <div
        className="flex-1 overflow-y-auto"
        style={{ scrollbarWidth: "thin", scrollbarColor: "#1a1a1a transparent" }}
      >
        {/* COUNTS TAB */}
        {activeTab === "counts" && (
          <div>
            {/* Areas covered */}
            <div
              className="border-b px-5 py-3"
              style={{ borderColor: "#1a1a1a" }}
            >
              <p
                className="mb-1.5 text-xs"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: "#444",
                  fontSize: "9px",
                  letterSpacing: "0.1em",
                }}
              >
                AREAS COVERED
              </p>
              <div className="flex flex-wrap gap-1.5">
                {data.areas_covered.map((area) => (
                  <span
                    key={area}
                    className="rounded px-2 py-0.5 text-xs"
                    style={{
                      fontFamily: "var(--font-ibm-plex-mono)",
                      fontSize: "10px",
                      background: "#1a1a1a",
                      color: "#666",
                    }}
                  >
                    {area}
                  </span>
                ))}
              </div>
            </div>

            {/* Fixture count table */}
            <table className="w-full">
              <thead>
                <tr
                  style={{
                    borderBottom: "1px solid #1a1a1a",
                    background: "#0a0a0a",
                  }}
                >
                  {["TYPE", "DESCRIPTION", "TOTAL", "DIFF"].map((h) => (
                    <th
                      key={h}
                      className="px-3 py-2 text-left text-xs"
                      style={{
                        fontFamily: "var(--font-ibm-plex-mono)",
                        fontSize: "9px",
                        letterSpacing: "0.1em",
                        color: "#444",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.fixture_counts.map((fixture) => {
                  const diffInfo = DIFFICULTY_LABELS[fixture.difficulty] || { label: fixture.difficulty, color: "#666" };
                  const isExpanded = expandedArea === fixture.type_tag;
                  const hasAreas = Object.keys(fixture.counts_by_area).length > 0;

                  return (
                    <>
                      <tr
                        key={fixture.type_tag}
                        onClick={() => hasAreas && setExpandedArea(isExpanded ? null : fixture.type_tag)}
                        className="transition-colors"
                        style={{
                          borderBottom: "1px solid #0f0f0f",
                          cursor: hasAreas ? "pointer" : "default",
                          background: isExpanded ? "#0a0a0a" : "transparent",
                        }}
                      >
                        <td className="px-3 py-2.5">
                          <span
                            className="rounded px-1.5 py-0.5 text-xs font-bold"
                            style={{
                              fontFamily: "var(--font-ibm-plex-mono)",
                              fontSize: "11px",
                              background: "rgba(220,38,38,0.12)",
                              color: "#dc2626",
                            }}
                          >
                            {fixture.type_tag}
                          </span>
                        </td>
                        <td className="px-3 py-2.5">
                          <p
                            className="text-xs"
                            style={{
                              fontFamily: "var(--font-cormorant)",
                              fontSize: "13px",
                              color: "#d4d4d4",
                            }}
                          >
                            {fixture.description}
                          </p>
                          {(fixture.flags || []).length > 0 && (
                            <p
                              className="mt-0.5 text-xs"
                              style={{
                                fontFamily: "var(--font-ibm-plex-mono)",
                                fontSize: "9px",
                                color: "#f59e0b",
                              }}
                            >
                              ⚠ {fixture.flags?.join("; ")}
                            </p>
                          )}
                        </td>
                        <td className="px-3 py-2.5 text-right">
                          <span
                            className="text-sm font-bold"
                            style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#d4d4d4" }}
                          >
                            {fixture.total}
                          </span>
                          {hasAreas && (
                            <span
                              className="ml-1 text-xs"
                              style={{ color: "#333" }}
                            >
                              {isExpanded ? "▲" : "▼"}
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2.5">
                          <span
                            className="text-xs"
                            style={{
                              fontFamily: "var(--font-ibm-plex-mono)",
                              fontSize: "10px",
                              color: diffInfo.color,
                            }}
                          >
                            {fixture.difficulty}
                          </span>
                        </td>
                      </tr>

                      {/* Per-area breakdown */}
                      {isExpanded && hasAreas && (
                        <tr key={`${fixture.type_tag}-areas`}>
                          <td colSpan={4} className="pb-2">
                            <div
                              className="mx-3 rounded p-3"
                              style={{ background: "#0f0f0f", border: "1px solid #1a1a1a" }}
                            >
                              {Object.entries(fixture.counts_by_area).map(([area, count]) => (
                                <div
                                  key={area}
                                  className="flex justify-between py-1"
                                  style={{ borderBottom: "1px solid #111" }}
                                >
                                  <span
                                    className="text-xs"
                                    style={{
                                      fontFamily: "var(--font-ibm-plex-mono)",
                                      color: "#525252",
                                      fontSize: "10px",
                                    }}
                                  >
                                    {area}
                                  </span>
                                  <span
                                    className="text-xs"
                                    style={{
                                      fontFamily: "var(--font-ibm-plex-mono)",
                                      color: "#d4d4d4",
                                      fontSize: "10px",
                                    }}
                                  >
                                    {count}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
              <tfoot>
                <tr style={{ borderTop: "1px solid #1a1a1a", background: "#0a0a0a" }}>
                  <td colSpan={2} className="px-3 py-3">
                    <span
                      className="text-xs uppercase"
                      style={{
                        fontFamily: "var(--font-ibm-plex-mono)",
                        color: "#525252",
                        letterSpacing: "0.1em",
                        fontSize: "10px",
                      }}
                    >
                      Grand Total
                    </span>
                  </td>
                  <td className="px-3 py-3 text-right">
                    <span
                      className="text-lg font-bold"
                      style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#d4d4d4" }}
                    >
                      {data.grand_total.toLocaleString()}
                    </span>
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>

            {/* Flags */}
            {data.flags.length > 0 && (
              <div
                className="m-4 rounded p-4"
                style={{ background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.15)" }}
              >
                <p
                  className="mb-2 text-xs uppercase"
                  style={{
                    fontFamily: "var(--font-ibm-plex-mono)",
                    color: "#f59e0b",
                    fontSize: "9px",
                    letterSpacing: "0.15em",
                  }}
                >
                  Flagged Items
                </p>
                {data.flags.map((flag, i) => (
                  <p
                    key={i}
                    className="text-xs"
                    style={{
                      fontFamily: "var(--font-ibm-plex-mono)",
                      color: "#d4d4d4",
                      fontSize: "11px",
                      marginBottom: "4px",
                    }}
                  >
                    ⚠ {flag}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ADVERSARIAL TAB */}
        {activeTab === "adversarial" && (
          <div className="p-4">
            {data.adversarial_log.length === 0 ? (
              <p
                className="py-8 text-center text-xs"
                style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#333" }}
              >
                No adversarial challenges in this run
              </p>
            ) : (
              data.adversarial_log.map((entry, i) => {
                const severityColor = SEVERITY_COLORS[entry.severity] || "#666";
                const verdictColor = entry.verdict === "concede"
                  ? "#dc2626"
                  : entry.verdict === "defend"
                  ? "#10b981"
                  : "#f59e0b";

                return (
                  <div
                    key={i}
                    className="mb-3 rounded p-4"
                    style={{
                      border: `1px solid rgba(${entry.severity === "critical" ? "220,38,38" : "255,255,255"},0.08)`,
                      background: "#0a0a0a",
                    }}
                  >
                    <div className="mb-2 flex items-center gap-3">
                      <span
                        className="rounded px-2 py-0.5 text-xs"
                        style={{
                          fontFamily: "var(--font-ibm-plex-mono)",
                          fontSize: "9px",
                          letterSpacing: "0.1em",
                          background: `rgba(${entry.severity === "critical" ? "220,38,38" : entry.severity === "major" ? "245,158,11" : "59,130,246"},0.12)`,
                          color: severityColor,
                        }}
                      >
                        {entry.severity?.toUpperCase()}
                      </span>
                      <span
                        className="text-xs"
                        style={{
                          fontFamily: "var(--font-ibm-plex-mono)",
                          color: "#444",
                          fontSize: "10px",
                        }}
                      >
                        {entry.attack_id}
                      </span>
                      {entry.category && (
                        <span
                          className="text-xs"
                          style={{
                            fontFamily: "var(--font-ibm-plex-mono)",
                            color: "#333",
                            fontSize: "9px",
                            letterSpacing: "0.05em",
                          }}
                        >
                          {entry.category.replace(/_/g, " ")}
                        </span>
                      )}
                    </div>

                    <p
                      className="mb-2 text-sm"
                      style={{
                        fontFamily: "var(--font-cormorant)",
                        color: "#d4d4d4",
                        fontSize: "14px",
                      }}
                    >
                      {entry.description}
                    </p>

                    {entry.resolution && (
                      <div
                        className="flex items-start gap-2 rounded p-2"
                        style={{ background: "#0f0f0f", border: "1px solid #1a1a1a" }}
                      >
                        {entry.verdict && (
                          <span
                            className="mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs uppercase"
                            style={{
                              fontFamily: "var(--font-ibm-plex-mono)",
                              fontSize: "8px",
                              letterSpacing: "0.1em",
                              color: verdictColor,
                              background: `${verdictColor}18`,
                            }}
                          >
                            {entry.verdict}
                          </span>
                        )}
                        <p
                          className="text-xs"
                          style={{
                            fontFamily: "var(--font-ibm-plex-mono)",
                            color: "#525252",
                            fontSize: "10px",
                          }}
                        >
                          {entry.resolution}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })
            )}

            {/* Constitutional violations */}
            {data.constitutional_violations.length > 0 && (
              <div
                className="mt-4 rounded p-4"
                style={{
                  background: "rgba(220,38,38,0.04)",
                  border: "1px solid rgba(220,38,38,0.15)",
                }}
              >
                <p
                  className="mb-3 text-xs uppercase"
                  style={{
                    fontFamily: "var(--font-ibm-plex-mono)",
                    color: "#dc2626",
                    fontSize: "9px",
                    letterSpacing: "0.15em",
                  }}
                >
                  Constitutional Violations
                </p>
                {data.constitutional_violations.map((v, i) => (
                  <div key={i} className="mb-2">
                    <p
                      className="text-xs font-semibold"
                      style={{
                        fontFamily: "var(--font-ibm-plex-mono)",
                        color: SEVERITY_COLORS[v.severity] || "#666",
                        fontSize: "10px",
                      }}
                    >
                      {v.severity} — {v.rule}
                    </p>
                    <p
                      className="text-xs"
                      style={{
                        fontFamily: "var(--font-ibm-plex-mono)",
                        color: "#525252",
                        fontSize: "10px",
                      }}
                    >
                      {v.explanation}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* CONFIDENCE TAB */}
        {activeTab === "confidence" && (
          <div className="p-4">
            {/* Overall score */}
            <div
              className="mb-4 rounded p-4"
              style={{ background: "#0a0a0a", border: "1px solid #1a1a1a" }}
            >
              <div className="mb-2 flex items-baseline gap-3">
                <span
                  className="text-4xl font-bold"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)", color: confidenceColor }}
                >
                  {(data.confidence_score * 100).toFixed(0)}%
                </span>
                <span
                  className="text-sm font-semibold"
                  style={{ fontFamily: "var(--font-ibm-plex-mono)", color: confidenceColor }}
                >
                  {data.confidence_band}
                </span>
              </div>

              {/* Confidence bar */}
              <div
                className="h-1.5 w-full rounded-full"
                style={{ background: "#1a1a1a" }}
              >
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${data.confidence_score * 100}%`,
                    background: confidenceColor,
                  }}
                />
              </div>
            </div>

            {/* Feature breakdown */}
            {data.confidence_breakdown && (
              <div>
                <p
                  className="mb-3 text-xs uppercase"
                  style={{
                    fontFamily: "var(--font-ibm-plex-mono)",
                    color: "#444",
                    fontSize: "9px",
                    letterSpacing: "0.15em",
                  }}
                >
                  Feature Breakdown
                </p>

                {Object.entries(data.confidence_breakdown).map(([feature, value]) => {
                  const displayNames: Record<string, string> = {
                    schedule_match_rate: "Schedule Match Rate",
                    area_coverage: "Area Coverage",
                    adversarial_resolved: "Adversarial Resolved",
                    constitutional_clean: "Constitutional Clean",
                    cross_reference_match: "Panel Cross-Reference",
                    note_compliance: "Plan Note Compliance",
                    fast_mode_penalty: "Fast Mode Penalty",
                  };
                  const weights: Record<string, number> = {
                    schedule_match_rate: 0.25,
                    area_coverage: 0.20,
                    adversarial_resolved: 0.15,
                    constitutional_clean: 0.15,
                    cross_reference_match: 0.10,
                    note_compliance: 0.10,
                    fast_mode_penalty: -0.05,
                  };
                  const isNegative = (value as number) < 0;
                  const barColor = isNegative ? "#dc2626" : (value as number) >= 0.8 ? "#10b981" : (value as number) >= 0.5 ? "#f59e0b" : "#f97316";

                  return (
                    <div key={feature} className="mb-3">
                      <div className="mb-1 flex justify-between">
                        <span
                          className="text-xs"
                          style={{
                            fontFamily: "var(--font-ibm-plex-mono)",
                            color: "#525252",
                            fontSize: "10px",
                          }}
                        >
                          {displayNames[feature] || feature}
                        </span>
                        <div className="flex items-center gap-2">
                          <span
                            className="text-xs"
                            style={{
                              fontFamily: "var(--font-ibm-plex-mono)",
                              color: "#333",
                              fontSize: "9px",
                            }}
                          >
                            w={weights[feature]}
                          </span>
                          <span
                            className="text-xs font-bold"
                            style={{
                              fontFamily: "var(--font-ibm-plex-mono)",
                              color: barColor,
                              fontSize: "11px",
                            }}
                          >
                            {typeof value === "number"
                              ? isNegative
                                ? `${(value * 100).toFixed(0)}%`
                                : `${(value * 100).toFixed(0)}%`
                              : "—"}
                          </span>
                        </div>
                      </div>
                      <div
                        className="h-1 w-full rounded-full"
                        style={{ background: "#1a1a1a" }}
                      >
                        {!isNegative && (
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${Math.abs((value as number) * 100)}%`,
                              background: barColor,
                            }}
                          />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Confidence band legend */}
            <div
              className="mt-4 rounded p-3"
              style={{ background: "#0a0a0a", border: "1px solid #1a1a1a" }}
            >
              <p
                className="mb-2 text-xs uppercase"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: "#333",
                  fontSize: "9px",
                  letterSpacing: "0.1em",
                }}
              >
                Confidence Bands
              </p>
              {[
                { band: "HIGH", range: "85–100%", color: "#10b981" },
                { band: "MODERATE", range: "65–84%", color: "#f59e0b" },
                { band: "LOW", range: "40–64%", color: "#f97316" },
                { band: "VERY LOW", range: "0–39%", color: "#dc2626" },
              ].map(({ band, range, color }) => (
                <div key={band} className="flex items-center justify-between py-0.5">
                  <span
                    className="text-xs"
                    style={{ fontFamily: "var(--font-ibm-plex-mono)", color, fontSize: "10px" }}
                  >
                    {band}
                  </span>
                  <span
                    className="text-xs"
                    style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#333", fontSize: "10px" }}
                  >
                    {range}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
