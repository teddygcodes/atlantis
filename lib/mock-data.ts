import type {
  Snippet,
  TakeoffResult,
  PipelineStep,
} from "./types";

/* ── Mock Snippets ───────────────────────────────────────────────────── */

export const MOCK_SNIPPETS: Snippet[] = [
  {
    id: "s1",
    label: "fixture_schedule",
    pageNumber: 2,
    bbox: { x: 120, y: 40, width: 680, height: 300 },
  },
  {
    id: "s2",
    label: "rcp",
    subLabel: "Open Office North",
    pageNumber: 4,
    bbox: { x: 50, y: 80, width: 900, height: 600 },
  },
  {
    id: "s3",
    label: "rcp",
    subLabel: "Open Office South",
    pageNumber: 5,
    bbox: { x: 50, y: 80, width: 900, height: 600 },
  },
  {
    id: "s4",
    label: "rcp",
    subLabel: "Corridor 1A",
    pageNumber: 6,
    bbox: { x: 100, y: 120, width: 700, height: 400 },
  },
  {
    id: "s5",
    label: "panel_schedule",
    pageNumber: 8,
    bbox: { x: 60, y: 200, width: 500, height: 350 },
  },
];

/* ── Mock Results ────────────────────────────────────────────────────── */

export const MOCK_RESULT: TakeoffResult = {
  verdict: "WARN",
  grandTotal: 94,
  confidence: 0.82,
  confidenceBand: "MODERATE",
  fixtureTable: [
    {
      typeTag: "A",
      description: "2x4 LED Recessed Troffer, 4000K",
      total: 48,
      revised: 48,
      delta: 0,
      difficulty: "S",
      flags: [],
      countsbyArea: { "Open Office North": 24, "Open Office South": 18, "Corridor 1A": 6 },
    },
    {
      typeTag: "B",
      description: "2x2 LED Troffer, 3500K",
      total: 12,
      revised: 14,
      delta: 2,
      difficulty: "S",
      flags: ["Checker found 2 additional in break room"],
      countsbyArea: { "Open Office North": 6, "Open Office South": 8 },
    },
    {
      typeTag: "C",
      description: '6" LED Recessed Downlight, 3000K',
      total: 24,
      revised: 24,
      delta: 0,
      difficulty: "M",
      flags: [],
      countsbyArea: { "Open Office North": 8, "Open Office South": 8, "Corridor 1A": 8 },
    },
    {
      typeTag: "D",
      description: "Wall Sconce, 2700K",
      total: 6,
      revised: 6,
      delta: 0,
      difficulty: "S",
      flags: [],
      countsbyArea: { "Corridor 1A": 6 },
    },
    {
      typeTag: "X",
      description: "LED Exit Sign w/ Battery Backup",
      total: 8,
      revised: 8,
      delta: 0,
      difficulty: "S",
      flags: [],
      countsbyArea: { "Open Office North": 2, "Open Office South": 2, "Corridor 1A": 4 },
    },
    {
      typeTag: "EM",
      description: "Emergency Battery Unit (Bug-Eye)",
      total: 4,
      revised: 4,
      delta: 0,
      difficulty: "S",
      flags: [],
      countsbyArea: { "Open Office North": 1, "Open Office South": 1, "Corridor 1A": 2 },
    },
  ],
  areasCovered: ["Open Office North", "Open Office South", "Corridor 1A"],
  adversarialLog: [
    {
      attackId: "ATK-001",
      severity: "major",
      category: "missed_fixtures",
      description:
        "Counter reported 12 Type B fixtures but RCP snippet for Open Office South shows 14. Two fixtures near the break room kitchenette appear to have been missed.",
      resolution: "CONCEDED",
      explanation:
        "Checker is correct -- two Type B downlights in the kitchenette alcove were not counted. Revised count: 14.",
    },
    {
      attackId: "ATK-002",
      severity: "minor",
      category: "missing_accessory",
      description:
        "Type C downlights in Corridor 1A do not list flex whips in accessories. Standard practice requires 6' flex whips for recessed corridor fixtures.",
      resolution: "CONCEDED",
      explanation: "Flex whips added to Type C accessories list.",
    },
    {
      attackId: "ATK-003",
      severity: "minor",
      category: "cross_reference",
      description:
        "Panel schedule total load (4,200 VA) vs. computed fixture wattage (3,890W) -- 7.9% discrepancy. Within 15% threshold but worth noting.",
      resolution: "DEFENDED",
      explanation:
        "Discrepancy is within constitutional 15% threshold. Panel schedule may include receptacle loads on shared circuits.",
    },
    {
      attackId: "ATK-004",
      severity: "major",
      category: "missed_note",
      description:
        "Plan note states 'Provide occupancy sensor in each private office.' Counter did not flag sensor requirements for Type A fixtures in office areas.",
      resolution: "PARTIAL",
      explanation:
        "Sensors are accessories, not fixtures -- added to Type A accessory list. However, sensor count depends on office room count which is not explicit in RCP snippets.",
    },
  ],
  confidenceFeatures: {
    scheduleMatch: 1.0,
    areaCoverage: 1.0,
    adversarialResolved: 0.75,
    constitutionalClean: 0.85,
    crossReference: 0.92,
    noteCompliance: 0.8,
    reconcilerCoverage: 1.0,
  },
  violations: [
    {
      rule: "Flag Assumptions",
      severity: "MINOR",
      explanation:
        "Sensor count for private offices flagged as assumption -- exact office room count not determinable from RCP snippets provided.",
    },
  ],
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
