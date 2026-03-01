/* Shared TypeScript types for the Takeoff workspace. */

export type SnippetLabel =
  | "fixture_schedule"
  | "rcp"
  | "panel_schedule"
  | "plan_notes"
  | "detail"
  | "site_plan";

export interface Snippet {
  id: string;
  label: SnippetLabel;
  subLabel?: string; // area name for RCPs
  pageNumber: number;
  bbox: { x: number; y: number; width: number; height: number };
  thumbnailDataUrl?: string; // base64 cropped image
}

export type TakeoffMode = "fast" | "strict" | "liability";

export type AppState =
  | "empty"
  | "loaded"
  | "snipping"
  | "ready"
  | "running"
  | "complete";

export interface FixtureRow {
  typeTag: string;
  description: string;
  total: number;
  revised: number;
  delta: number;
  difficulty: string;
  flags: string[];
  countsbyArea?: Record<string, number>;
}

export interface AdversarialEntry {
  attackId: string;
  severity: "critical" | "major" | "minor";
  category: string;
  description: string;
  resolution: "CONCEDED" | "DEFENDED" | "PARTIAL";
  explanation: string;
}

export interface ConfidenceFeatures {
  scheduleMatch: number;
  areaCoverage: number;
  adversarialResolved: number;
  constitutionalClean: number;
  crossReference: number;
  noteCompliance: number;
  reconcilerCoverage: number;
}

export interface Violation {
  rule: string;
  severity: string;
  explanation: string;
}

export type Verdict = "PASS" | "WARN" | "BLOCK";

export interface TakeoffResult {
  verdict: Verdict;
  grandTotal: number;
  confidence: number;
  confidenceBand: string;
  fixtureTable: FixtureRow[];
  areasCovered: string[];
  adversarialLog: AdversarialEntry[];
  confidenceFeatures: ConfidenceFeatures;
  violations: Violation[];
}

export interface PipelineStep {
  id: string;
  label: string;
  detail?: string;
  status: "pending" | "running" | "done" | "error";
}
