"use client";

import { useState, useCallback, useRef } from "react";
import { DrawingViewer } from "@/components/takeoff/drawing-viewer";
import { SnippetTray } from "@/components/takeoff/snippet-tray";
import { ResultsPanel } from "@/components/takeoff/results-panel";
import { LabelModal } from "@/components/takeoff/label-modal";
import type { Snippet, TakeoffResult, PipelineStep, AppState } from "@/lib/types";
import { MOCK_PAGES, MOCK_RESULT, PIPELINE_STEPS, PIPELINE_MESSAGES } from "@/lib/mock-data";

export default function TakeoffPage() {
  /* ── State ─────────────────────────────────────────────────────── */
  const [appState, setAppState] = useState<AppState>("empty");
  const [pdfLoaded, setPdfLoaded] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [snippets, setSnippets] = useState<Snippet[]>([]);
  const [snipMode, setSnipMode] = useState(false);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [pendingBbox, setPendingBbox] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
  const [result, setResult] = useState<TakeoffResult | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[] | null>(null);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [snippetFlash, setSnippetFlash] = useState<string | null>(null);
  const [pdfFilename, setPdfFilename] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pageCount = MOCK_PAGES.length;

  /* ── Handlers ──────────────────────────────────────────────────── */

  const handleUpload = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPdfLoaded(true);
      setPdfFilename(file.name);
      setCurrentPage(1);
      setAppState("loaded");
    }
  }, []);

  const handleToggleSnip = useCallback(() => {
    setSnipMode((prev) => !prev);
    setAppState((prev) => (prev === "snipping" ? "loaded" : "snipping"));
  }, []);

  const handleSnipComplete = useCallback(
    (bbox: { x: number; y: number; width: number; height: number }) => {
      setPendingBbox(bbox);
      setShowLabelModal(true);
    },
    []
  );

  const handleLabelSave = useCallback(
    (label: string, subLabel: string) => {
      if (!pendingBbox) return;
      const newSnippet: Snippet = {
        id: `s-${Date.now()}`,
        label: label as Snippet["label"],
        sub_label: subLabel,
        page_number: currentPage,
        bbox: pendingBbox,
      };
      setSnippets((prev) => [...prev, newSnippet]);
      setPendingBbox(null);
      setShowLabelModal(false);
      setSnipMode(false);
      setAppState("ready");
    },
    [pendingBbox, currentPage]
  );

  const handleLabelCancel = useCallback(() => {
    setPendingBbox(null);
    setShowLabelModal(false);
  }, []);

  const handleDeleteSnippet = useCallback((id: string) => {
    setSnippets((prev) => prev.filter((s) => s.id !== id));
  }, []);

  const handleRelabelSnippet = useCallback(
    (id: string, label: string, subLabel: string) => {
      setSnippets((prev) =>
        prev.map((s) =>
          s.id === id ? { ...s, label: label as Snippet["label"], sub_label: subLabel } : s
        )
      );
    },
    []
  );

  const handleHighlightSnippet = useCallback(
    (snippet: Snippet | null) => {
      if (snippet) {
        setCurrentPage(snippet.page_number);
        setSnippetFlash(snippet.id);
        setTimeout(() => setSnippetFlash(null), 1500);
      } else {
        setSnippetFlash(null);
      }
    },
    []
  );

  /* ── Simulated Pipeline ────────────────────────────────────────── */
  const handleRunTakeoff = useCallback((_mode: string) => {
    setAppState("running");
    setPipelineRunning(true);
    setShowResults(false);
    setResult(null);

    const steps: PipelineStep[] = PIPELINE_STEPS.map((s) => ({ ...s }));
    setPipelineSteps(steps);

    let stepIndex = 0;
    const interval = setInterval(() => {
      if (stepIndex < steps.length) {
        // Mark current as running
        steps[stepIndex] = { ...steps[stepIndex], status: "running" };
        setPipelineSteps([...steps]);
      }

      if (stepIndex > 0) {
        // Mark previous as done
        steps[stepIndex - 1] = { ...steps[stepIndex - 1], status: "done" };
        setPipelineSteps([...steps]);
      }

      stepIndex++;

      if (stepIndex > steps.length) {
        clearInterval(interval);
        // All done
        steps[steps.length - 1] = { ...steps[steps.length - 1], status: "done" };
        setPipelineSteps([...steps]);

        setTimeout(() => {
          setPipelineRunning(false);
          setPipelineSteps(null);
          setResult(MOCK_RESULT);
          setShowResults(true);
          setAppState("complete");
        }, 600);
      }
    }, 1200);
  }, []);

  const handleCloseResults = useCallback(() => {
    setShowResults(false);
  }, []);

  /* ── Render ────────────────────────────────────────────────────── */
  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-canvas">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Header Bar */}
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-border bg-background px-4">
        <div className="flex items-center gap-3">
          {/* Red diamond icon */}
          <div className="flex h-7 w-7 items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L22 12L12 22L2 12L12 2Z" fill="#DC2626" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-foreground">TAKEOFF</span>
          <span className="hidden text-sm text-muted-foreground sm:inline">
            Adversarial Lighting Takeoff
          </span>
        </div>

        <div className="flex items-center gap-3">
          {pdfLoaded && pdfFilename && (
            <span className="hidden text-xs text-muted-foreground md:inline">
              {pdfFilename} {"\u00B7"} {pageCount} pages {"\u00B7"}{" "}
              <button onClick={handleUpload} className="text-accent hover:underline">
                Change
              </button>
            </span>
          )}
          <button
            onClick={handleUpload}
            className="flex items-center gap-2 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-accent-hover"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" x2="12" y1="3" y2="15" />
            </svg>
            Upload PDF
          </button>
        </div>
      </header>

      {/* Main workspace */}
      <div className="flex flex-1 overflow-hidden">
        {/* Drawing viewer (page sidebar + toolbar + canvas) */}
        <div className={`flex flex-1 flex-col overflow-hidden ${showResults ? "" : ""}`}>
          <div className={`flex flex-1 overflow-hidden ${showResults ? "h-[55%]" : "h-full"}`}>
            <DrawingViewer
              pageCount={pageCount}
              currentPage={currentPage}
              onPageChange={setCurrentPage}
              snippets={snippets}
              snipMode={snipMode}
              onToggleSnip={handleToggleSnip}
              onSnipComplete={handleSnipComplete}
              onUpload={handleUpload}
              pdfLoaded={pdfLoaded}
              pipelineSteps={pipelineSteps}
              pipelineRunning={pipelineRunning}
              snippetFlash={snippetFlash}
            />
          </div>

          {/* Results panel - slides up from bottom */}
          {showResults && result && (
            <div
              className="shrink-0 border-t border-border"
              style={{ height: "45vh" }}
            >
              <ResultsPanel
                data={result}
                onClose={handleCloseResults}
              />
            </div>
          )}
        </div>

        {/* Snippet tray - right side */}
        <div className="w-[300px] shrink-0">
          <SnippetTray
            snippets={snippets}
            onDeleteSnippet={handleDeleteSnippet}
            onRelabelSnippet={handleRelabelSnippet}
            onHighlightSnippet={handleHighlightSnippet}
            onRunTakeoff={handleRunTakeoff}
            isRunning={pipelineRunning}
            hasPdf={pdfLoaded}
          />
        </div>
      </div>

      {/* Label Modal */}
      {showLabelModal && (
        <LabelModal onSave={handleLabelSave} onCancel={handleLabelCancel} />
      )}
    </div>
  );
}
