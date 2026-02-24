"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Shield,
  AlertTriangle,
} from "lucide-react";

interface Source {
  title: string;
  url: string;
  grade: string;
}

interface AuditTrail {
  mode: string;
  researcher_claims: number;
  adversary_attacks: number;
  attacks_survived: number;
  judge_verdict: string;
  reasoning: string;
}

interface SearchResultData {
  answer_bullets: string[];
  confidence: "HIGH" | "MODERATE" | "LOW";
  confidence_score: number;
  sources: Source[];
  constitutional_violations: string[];
  audit_trail: AuditTrail;
}

function ConfidenceBadge({
  confidence,
  score,
}: {
  confidence: string;
  score: number;
}) {
  const config: Record<string, { color: string; bg: string; border: string }> =
    {
      HIGH: {
        color: "#22c55e",
        bg: "rgba(34, 197, 94, 0.08)",
        border: "rgba(34, 197, 94, 0.25)",
      },
      MODERATE: {
        color: "#eab308",
        bg: "rgba(234, 179, 8, 0.08)",
        border: "rgba(234, 179, 8, 0.25)",
      },
      LOW: {
        color: "#dc2626",
        bg: "rgba(220, 38, 38, 0.08)",
        border: "rgba(220, 38, 38, 0.25)",
      },
    };

  const c = config[confidence] || config.MODERATE;

  return (
    <div
      className="inline-flex items-center gap-2 rounded-full px-3 py-1"
      style={{
        backgroundColor: c.bg,
        border: `1px solid ${c.border}`,
      }}
    >
      <Shield size={12} style={{ color: c.color }} />
      <span
        className="text-[10px] uppercase tracking-[0.2em]"
        style={{
          fontFamily: "var(--font-ibm-plex-mono)",
          color: c.color,
        }}
      >
        {confidence}
      </span>
      <span
        className="text-[10px]"
        style={{
          fontFamily: "var(--font-ibm-plex-mono)",
          color: c.color,
          opacity: 0.7,
        }}
      >
        {(score * 100).toFixed(0)}%
      </span>
    </div>
  );
}

function SourceGrade({ grade }: { grade: string }) {
  const gradeColors: Record<string, string> = {
    A: "#22c55e",
    B: "#4ade80",
    C: "#eab308",
    D: "#f97316",
    F: "#dc2626",
  };

  return (
    <span
      className="inline-flex h-5 w-5 items-center justify-center rounded text-[10px] font-bold"
      style={{
        backgroundColor: `${gradeColors[grade] || "#525252"}20`,
        color: gradeColors[grade] || "#525252",
        fontFamily: "var(--font-ibm-plex-mono)",
      }}
    >
      {grade}
    </span>
  );
}

function VerdictBadge({ verdict }: { verdict: string }) {
  const colors: Record<string, string> = {
    PASS: "#22c55e",
    WARN: "#eab308",
    FAIL: "#dc2626",
  };

  return (
    <span
      className="text-[10px] uppercase tracking-[0.15em]"
      style={{
        fontFamily: "var(--font-ibm-plex-mono)",
        color: colors[verdict] || "#525252",
      }}
    >
      {verdict}
    </span>
  );
}

export function SearchResults({ data }: { data: SearchResultData }) {
  const [auditOpen, setAuditOpen] = useState(false);

  return (
    <div className="search-result-enter flex w-full max-w-2xl flex-col gap-6">
      {/* Confidence badge */}
      <div className="flex items-center gap-3">
        <ConfidenceBadge
          confidence={data.confidence}
          score={data.confidence_score}
        />
        <VerdictBadge verdict={data.audit_trail.judge_verdict} />
      </div>

      {/* Answer bullets */}
      <div className="flex flex-col gap-3">
        {data.answer_bullets.map((bullet, i) => (
          <div key={i} className="flex gap-3">
            <span
              className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full"
              style={{ backgroundColor: "#dc2626" }}
            />
            <p
              className="text-base leading-relaxed"
              style={{
                fontFamily: "var(--font-cormorant)",
                color: "#d4d4d4",
                fontSize: "17px",
                fontWeight: 500,
              }}
            >
              {bullet}
            </p>
          </div>
        ))}
      </div>

      {/* Sources */}
      {data.sources.length > 0 && (
        <div className="flex flex-col gap-2">
          <h4
            className="text-[10px] uppercase tracking-[0.25em]"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              color: "#525252",
            }}
          >
            Sources
          </h4>
          <div className="flex flex-col gap-1.5">
            {data.sources.map((source, i) => (
              <a
                key={i}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center gap-2 rounded px-2 py-1.5 transition-colors hover:bg-[#111]"
              >
                <SourceGrade grade={source.grade} />
                <span
                  className="flex-1 truncate text-sm transition-colors group-hover:text-foreground"
                  style={{
                    fontFamily: "var(--font-ibm-plex-mono)",
                    color: "#737373",
                    fontSize: "12px",
                  }}
                >
                  {source.title}
                </span>
                <ExternalLink
                  size={11}
                  className="flex-shrink-0 opacity-0 transition-opacity group-hover:opacity-50"
                  style={{ color: "#737373" }}
                />
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Constitutional violations */}
      {data.constitutional_violations.length > 0 && (
        <div
          className="flex flex-col gap-2 rounded-lg border p-3"
          style={{
            borderColor: "rgba(220, 38, 38, 0.25)",
            backgroundColor: "rgba(220, 38, 38, 0.04)",
          }}
        >
          <div className="flex items-center gap-2">
            <AlertTriangle size={13} style={{ color: "#dc2626" }} />
            <span
              className="text-[10px] uppercase tracking-[0.2em]"
              style={{
                fontFamily: "var(--font-ibm-plex-mono)",
                color: "#dc2626",
              }}
            >
              Constitutional Violations
            </span>
          </div>
          {data.constitutional_violations.map((violation, i) => (
            <p
              key={i}
              className="text-sm"
              style={{
                fontFamily: "var(--font-ibm-plex-mono)",
                color: "#a3a3a3",
                fontSize: "12px",
              }}
            >
              {violation}
            </p>
          ))}
        </div>
      )}

      {/* Collapsible audit trail */}
      <div
        className="rounded-lg border"
        style={{
          borderColor: "#1a1a1a",
          backgroundColor: "#0a0a0a",
        }}
      >
        <button
          onClick={() => setAuditOpen(!auditOpen)}
          className="flex w-full items-center justify-between px-3 py-2.5 transition-colors hover:bg-[#111]"
          style={{ borderRadius: "8px" }}
        >
          <span
            className="text-[10px] uppercase tracking-[0.25em]"
            style={{
              fontFamily: "var(--font-ibm-plex-mono)",
              color: "#525252",
            }}
          >
            Audit Trail
          </span>
          {auditOpen ? (
            <ChevronUp size={14} style={{ color: "#525252" }} />
          ) : (
            <ChevronDown size={14} style={{ color: "#525252" }} />
          )}
        </button>

        {auditOpen && (
          <div
            className="flex flex-col gap-3 border-t px-3 py-3"
            style={{ borderColor: "#1a1a1a" }}
          >
            <div className="grid grid-cols-2 gap-3">
              <AuditRow label="Mode" value={data.audit_trail.mode} />
              <AuditRow
                label="Researcher Claims"
                value={String(data.audit_trail.researcher_claims)}
              />
              <AuditRow
                label="Adversary Attacks"
                value={String(data.audit_trail.adversary_attacks)}
              />
              <AuditRow
                label="Attacks Survived"
                value={String(data.audit_trail.attacks_survived)}
              />
            </div>
            <div
              className="border-t pt-3"
              style={{ borderColor: "#1a1a1a" }}
            >
              <p
                className="text-xs leading-relaxed"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: "#737373",
                  fontSize: "11px",
                }}
              >
                {data.audit_trail.reasoning}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function AuditRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span
        className="text-[9px] uppercase tracking-[0.2em]"
        style={{
          fontFamily: "var(--font-ibm-plex-mono)",
          color: "#525252",
        }}
      >
        {label}
      </span>
      <span
        className="text-xs"
        style={{
          fontFamily: "var(--font-ibm-plex-mono)",
          color: "#a3a3a3",
          fontSize: "12px",
        }}
      >
        {value}
      </span>
    </div>
  );
}
