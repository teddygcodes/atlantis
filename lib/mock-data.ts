import type { Snippet, TakeoffResult, PipelineStep, MockPage } from "./types";

/* ── Mock Pages (simulated PDF) ──────────────────────────────────────── */

export const MOCK_PAGES: MockPage[] = [
  { number: 1, title: "Title Sheet" },
  { number: 2, title: "Fixture Schedule" },
  { number: 3, title: "Site Plan" },
  { number: 4, title: "Open Office North RCP" },
  { number: 5, title: "Open Office South RCP" },
  { number: 6, title: "Corridor 1A RCP" },
  { number: 7, title: "Detail Drawings" },
  { number: 8, title: "Panel Schedule LP-1" },
  { number: 9, title: "Electrical Notes" },
  { number: 10, title: "Single Line Diagram" },
  { number: 11, title: "Emergency Lighting" },
  { number: 12, title: "Controls Diagram" },
];

/* ── Mock Snippets ───────────────────────────────────────────────────── */

export const MOCK_SNIPPETS: Snippet[] = [
  {
    id: "s1",
    label: "fixture_schedule",
    sub_label: "Fixture Schedule",
    page_number: 2,
    bbox: { x: 120, y: 40, width: 680, height: 300 },
  },
  {
    id: "s2",
    label: "rcp",
    sub_label: "Open Office North",
    page_number: 4,
    bbox: { x: 50, y: 80, width: 900, height: 600 },
  },
  {
    id: "s3",
    label: "rcp",
    sub_label: "Open Office South",
    page_number: 5,
    bbox: { x: 50, y: 80, width: 900, height: 600 },
  },
  {
    id: "s4",
    label: "rcp",
    sub_label: "Corridor 1A",
    page_number: 6,
    bbox: { x: 100, y: 120, width: 700, height: 400 },
  },
  {
    id: "s5",
    label: "panel_schedule",
    sub_label: "Panel Schedule LP-1",
    page_number: 8,
    bbox: { x: 60, y: 200, width: 500, height: 350 },
  },
];

/* ── Mock Results ────────────────────────────────────────────────────── */

export const MOCK_RESULT: TakeoffResult = {
  drawing_name: "Office TI - Phase 2",
  mode: "strict",
  judge_verdict: "WARN",
  grand_total: 92,
  revised_total: 94,
  confidence_score: 0.82,
  confidence_band: "MODERATE",
  fixture_counts: [
    {
      type_tag: "A",
      description: "2x4 LED Recessed Troffer, 4000K",
      total: 48,
      revised: 48,
      delta: 0,
      difficulty: "S",
      flags: [],
      counts_by_area: { "Open Office North": 24, "Open Office South": 18, "Corridor 1A": 6 },
    },
    {
      type_tag: "B",
      description: "2x2 LED Troffer, 3500K",
      total: 12,
      revised: 14,
      delta: 2,
      difficulty: "S",
      flags: ["Checker found 2 additional in break room"],
      counts_by_area: { "Open Office North": 6, "Open Office South": 8 },
    },
    {
      type_tag: "C",
      description: '6" LED Recessed Downlight, 3000K',
      total: 24,
      revised: 24,
      delta: 0,
      difficulty: "M",
      flags: [],
      counts_by_area: { "Open Office North": 8, "Open Office South": 8, "Corridor 1A": 8 },
    },
    {
      type_tag: "D",
      description: "Wall Sconce, 2700K",
      total: 6,
      revised: 6,
      delta: 0,
      difficulty: "S",
      flags: [],
      counts_by_area: { "Corridor 1A": 6 },
    },
    {
      type_tag: "X",
      description: "LED Exit Sign w/ Battery Backup",
      total: 8,
      revised: 8,
      delta: 0,
      difficulty: "S",
      flags: [],
      counts_by_area: { "Open Office North": 2, "Open Office South": 2, "Corridor 1A": 4 },
    },
    {
      type_tag: "EM",
      description: "Emergency Battery Unit (Bug-Eye)",
      total: 4,
      revised: 4,
      delta: 0,
      difficulty: "S",
      flags: [],
      counts_by_area: { "Open Office North": 1, "Open Office South": 1, "Corridor 1A": 2 },
    },
  ],
  areas_covered: ["Open Office North", "Open Office South", "Corridor 1A"],
  adversarial_log: [
    {
      attack_id: "ATK-001",
      severity: "major",
      category: "missed_fixtures",
      description:
        "Counter reported 12 Type B fixtures but RCP snippet for Open Office South shows 14. Two fixtures near the break room kitchenette appear to have been missed.",
      resolution: "CONCEDED",
      explanation:
        "Checker is correct \u2014 two Type B downlights in the kitchenette alcove were not counted. Revised count: 14.",
    },
    {
      attack_id: "ATK-002",
      severity: "minor",
      category: "missing_accessory",
      description:
        "Type C downlights in Corridor 1A do not list flex whips in accessories. Standard practice requires 6\u2019 flex whips for recessed corridor fixtures.",
      resolution: "CONCEDED",
      explanation: "Flex whips added to Type C accessories list.",
    },
    {
      attack_id: "ATK-003",
      severity: "minor",
      category: "cross_reference",
      description:
        "Panel schedule total load (4,200 VA) vs. computed fixture wattage (3,890W) \u2014 7.9% discrepancy. Within 15% threshold but worth noting.",
      resolution: "DEFENDED",
      explanation:
        "Discrepancy is within constitutional 15% threshold. Panel schedule may include receptacle loads on shared circuits.",
    },
    {
      attack_id: "ATK-004",
      severity: "major",
      category: "missed_note",
      description:
        "Plan note states \u2018Provide occupancy sensor in each private office.\u2019 Counter did not flag sensor requirements for Type A fixtures in office areas.",
      resolution: "PARTIAL",
      explanation:
        "Sensors are accessories, not fixtures \u2014 added to Type A accessory list. However, sensor count depends on office room count which is not explicit in RCP snippets.",
    },
  ],
  confidence_breakdown: {
    schedule_match: 1.0,
    area_coverage: 1.0,
    adversarial_resolved: 0.75,
    constitutional_clean: 0.85,
    cross_reference: 0.92,
    note_compliance: 0.8,
    reconciler_coverage: 1.0,
  },
  constitutional_violations: [
    {
      rule: "Flag Assumptions",
      severity: "MINOR",
      explanation:
        "Sensor count for private offices flagged as assumption \u2014 exact office room count not determinable from RCP snippets provided.",
    },
  ],
  ruling_summary:
    "Takeoff approved with warnings. Two additional fixtures found by adversarial checker. Confidence moderate due to unresolved sensor count assumption.",
};

/* ── Pipeline Steps ──────────────────────────────────────────────────── */

export const PIPELINE_STEPS: PipelineStep[] = [
  { id: "extract", label: "Extracting fixture schedule", status: "pending" },
  { id: "count", label: "Counting fixtures", detail: "3 areas", status: "pending" },
  { id: "check", label: "Checker reviewing counts", status: "pending" },
  { id: "reconcile", label: "Reconciler resolving disputes", status: "pending" },
  { id: "judge", label: "Judge ruling", status: "pending" },
  { id: "confidence", label: "Calculating confidence", status: "pending" },
];

/* ── Pipeline messages shown at each step ────────────────────────────── */

export const PIPELINE_MESSAGES: Record<string, string> = {
  extract: "Extracting fixture types and quantities from schedule...",
  count: "Counting fixtures across Open Office North, Open Office South, Corridor 1A...",
  check: "Checker independently reviewing counts for accuracy...",
  reconcile: "Reconciler resolving disputes between Counter and Checker...",
  judge: "Judge issuing final ruling on takeoff quality...",
  confidence: "Computing weighted confidence score across all features...",
};
