"use client";

import { useEffect, useRef } from "react";
import {
  SCROLL_REVEAL_THRESHOLD_DEFAULT,
  SCROLL_REVEAL_ROOT_MARGIN_STANDARD,
} from "@/lib/constants";

function useScrollReveal() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("is-visible");
        });
      },
      {
        threshold: SCROLL_REVEAL_THRESHOLD_DEFAULT,
        rootMargin: SCROLL_REVEAL_ROOT_MARGIN_STANDARD,
      }
    );
    el.querySelectorAll(".scroll-reveal").forEach((child) =>
      observer.observe(child)
    );
    return () => observer.disconnect();
  }, []);
  return ref;
}

const PIPELINE_STEPS = [
  {
    number: "1",
    title: "Evidence Pack",
    description:
      "Your question triggers a web search. Sources are fetched, scored for credibility, and assembled into an evidence pack that all agents share.",
  },
  {
    number: "2",
    title: "Researcher",
    description:
      "Drafts an answer with structured claims, each citing specific sources from the evidence pack.",
  },
  {
    number: "3",
    title: "Adversary",
    description:
      "Independently searches for counter-evidence and attacks every claim. Must produce at least one concrete counter-hypothesis and show what it tried.",
  },
  {
    number: "4",
    title: "Critic",
    description:
      "Evaluates the attacks. Defends claims where attacks are weak, qualifies claims where attacks land, concedes where evidence is insufficient.",
  },
  {
    number: "5",
    title: "Judge",
    description:
      "Rules on every claim under constitutional law. Checks citation verification grades, source diversity, and six hard rules before issuing a verdict.",
  },
];

const CONSTITUTION_RULES = [
  "No claim survives without a verified citation",
  "No answer is approved without attempted falsification",
  "Health and legal questions are flagged, never prescribed",
  "Confidence scores are computed from evidence features, not model certainty",
  "Sources must come from multiple independent domains",
  "Partisan sources must be acknowledged as such",
];

const CITATION_GRADES = [
  { grade: "DIRECT_SUPPORT", color: "#22c55e", description: "Source explicitly states the claim" },
  { grade: "INDIRECT_SUPPORT", color: "#3b82f6", description: "Source supports via inference" },
  { grade: "TANGENTIAL", color: "#a3a3a3", description: "Source mentions topic but doesn't support" },
  { grade: "CONTRADICTS", color: "#dc2626", description: "Source opposes the claim" },
  { grade: "UNVERIFIABLE", color: "#525252", description: "Source can't be checked" },
];

const CONFIDENCE_BANDS = [
  { label: "HIGH", range: "85 - 100", color: "#22c55e" },
  { label: "MODERATE", range: "65 - 84", color: "#eab308" },
  { label: "LOW", range: "40 - 64", color: "#f97316" },
  { label: "REJECT", range: "0 - 39", color: "#dc2626" },
];

export function About() {
  const containerRef = useScrollReveal();

  return (
    <section ref={containerRef} className="mx-auto max-w-[760px]">
      {/* Header */}
      <div className="scroll-reveal mb-16 pt-16 text-center">
        <h1
          className="mb-6 tracking-[0.25em]"
          style={{
            fontFamily: "var(--font-cinzel)",
            fontSize: "clamp(28px, 5vw, 42px)",
            color: "#e5e5e5",
          }}
        >
          How Atlantis Works
        </h1>
        <p
          className="mx-auto max-w-[540px] leading-relaxed"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "18px",
            color: "#a3a3a3",
          }}
        >
          Atlantis is an adversarial search engine. When you ask a question,
          four AI agents research, attack, defend, and judge the answer before
          you see it.
        </p>
      </div>

      {/* The Pipeline */}
      <div className="scroll-reveal mb-20">
        <h2
          className="mb-10 tracking-[0.2em]"
          style={{
            fontFamily: "var(--font-cinzel)",
            fontSize: "18px",
            color: "#dc2626",
          }}
        >
          THE PIPELINE
        </h2>
        <div className="flex flex-col gap-6">
          {PIPELINE_STEPS.map((step) => (
            <div
              key={step.number}
              className="scroll-reveal flex gap-5 rounded-lg p-5"
              style={{
                backgroundColor: "#0e0e0e",
                border: "1px solid #1a1a1a",
              }}
            >
              <div
                className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full"
                style={{
                  backgroundColor: "rgba(220, 38, 38, 0.1)",
                  border: "1px solid rgba(220, 38, 38, 0.25)",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    color: "#dc2626",
                    fontWeight: 600,
                  }}
                >
                  {step.number}
                </span>
              </div>
              <div>
                <h3
                  className="mb-1.5"
                  style={{
                    fontFamily: "var(--font-cinzel)",
                    fontSize: "15px",
                    color: "#e5e5e5",
                    letterSpacing: "0.05em",
                  }}
                >
                  {step.title}
                </h3>
                <p
                  className="leading-relaxed"
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "15px",
                    color: "#a3a3a3",
                  }}
                >
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* The Constitution */}
      <div className="scroll-reveal mb-20">
        <h2
          className="mb-4 tracking-[0.2em]"
          style={{
            fontFamily: "var(--font-cinzel)",
            fontSize: "18px",
            color: "#dc2626",
          }}
        >
          THE CONSTITUTION
        </h2>
        <p
          className="mb-8 leading-relaxed"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "15px",
            color: "#a3a3a3",
          }}
        >
          Every query runs under a set of hard rules:
        </p>
        <div className="flex flex-col gap-3">
          {CONSTITUTION_RULES.map((rule, i) => (
            <div
              key={i}
              className="scroll-reveal flex items-start gap-3 py-2"
              style={{ borderBottom: "1px solid #1a1a1a" }}
            >
              <span
                className="mt-0.5 block h-1.5 w-1.5 flex-shrink-0 rounded-full"
                style={{ backgroundColor: "#dc2626" }}
              />
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "15px",
                  color: "#d4d4d4",
                  lineHeight: "1.6",
                }}
              >
                {rule}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Citation Verification */}
      <div className="scroll-reveal mb-20">
        <h2
          className="mb-4 tracking-[0.2em]"
          style={{
            fontFamily: "var(--font-cinzel)",
            fontSize: "18px",
            color: "#dc2626",
          }}
        >
          CITATION VERIFICATION
        </h2>
        <p
          className="mb-8 leading-relaxed"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "15px",
            color: "#a3a3a3",
          }}
        >
          Every source is graded:
        </p>
        <div className="flex flex-col gap-3">
          {CITATION_GRADES.map((item) => (
            <div
              key={item.grade}
              className="scroll-reveal flex items-center gap-4 rounded-md px-4 py-3"
              style={{ backgroundColor: "#0e0e0e", border: "1px solid #1a1a1a" }}
            >
              <span
                className="flex-shrink-0"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  color: item.color,
                  letterSpacing: "0.05em",
                  fontWeight: 600,
                  width: "150px",
                }}
              >
                {item.grade}
              </span>
              <span
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "14px",
                  color: "#a3a3a3",
                }}
              >
                {item.description}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Confidence Scoring */}
      <div className="scroll-reveal mb-20">
        <h2
          className="mb-4 tracking-[0.2em]"
          style={{
            fontFamily: "var(--font-cinzel)",
            fontSize: "18px",
            color: "#dc2626",
          }}
        >
          CONFIDENCE SCORING
        </h2>
        <p
          className="mb-8 leading-relaxed"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "15px",
            color: "#a3a3a3",
          }}
        >
          Confidence is calculated from features, not vibes:
        </p>
        <ul className="mb-8 flex flex-col gap-2">
          {[
            "Percentage of directly supported citations",
            "Number of independent source domains",
            "Severity of surviving adversarial attacks",
            "Constitutional violations found",
            "Evidence freshness",
          ].map((item, i) => (
            <li key={i} className="flex items-start gap-3">
              <span
                className="mt-2 block h-1 w-1 flex-shrink-0 rounded-full"
                style={{ backgroundColor: "#525252" }}
              />
              <span
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "14px",
                  color: "#a3a3a3",
                }}
              >
                {item}
              </span>
            </li>
          ))}
        </ul>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {CONFIDENCE_BANDS.map((band) => (
            <div
              key={band.label}
              className="scroll-reveal rounded-md px-4 py-3 text-center"
              style={{
                backgroundColor: "#0e0e0e",
                border: "1px solid #1a1a1a",
              }}
            >
              <div
                className="mb-1"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "12px",
                  fontWeight: 700,
                  color: band.color,
                  letterSpacing: "0.1em",
                }}
              >
                {band.label}
              </div>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  color: "#525252",
                }}
              >
                {band.range}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Why This Exists */}
      <div className="scroll-reveal mb-20">
        <h2
          className="mb-6 tracking-[0.2em]"
          style={{
            fontFamily: "var(--font-cinzel)",
            fontSize: "18px",
            color: "#dc2626",
          }}
        >
          WHY THIS EXISTS
        </h2>
        <p
          className="mb-6 leading-relaxed"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "18px",
            color: "#d4d4d4",
            lineHeight: "1.8",
          }}
        >
          Most AI gives you answers that sound confident. Atlantis gives you
          answers that earned confidence by surviving adversarial review.
        </p>
      </div>

      {/* Footer */}
      <div
        className="scroll-reveal border-t pb-12 pt-10 text-center"
        style={{ borderColor: "#1a1a1a" }}
      >
        <p
          className="mb-2"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "15px",
            color: "#a3a3a3",
          }}
        >
          Built by Tyler Gilstrap. Open source at{" "}
          <a
            href="https://github.com/teddygcodes/atlantis"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:underline"
            style={{ color: "#dc2626" }}
          >
            github.com/teddygcodes/atlantis
          </a>
          .
        </p>
        <p
          style={{
            fontFamily: "var(--font-ibm-plex-mono)",
            fontSize: "12px",
            color: "#444",
          }}
        >
          Powered by Sydyn
        </p>
      </div>
    </section>
  );
}
