"use client";

import { useRef, useEffect, useState, useCallback } from "react";

export interface SnippetData {
  id: string;
  page_number: number;
  label: string;
  sub_label: string;
  bbox: { x: number; y: number; width: number; height: number };
  image_data: string; // base64 PNG
}

interface DrawingViewerProps {
  onSnippetCaptured: (snippet: SnippetData) => void;
  highlightSnippet?: SnippetData | null;
}

type DrawingMode = "pan" | "snip";

interface PageThumb {
  pageNum: number;
  label: string;
  dataUrl: string;
}

const SNIPPET_LABELS = [
  { value: "fixture_schedule", label: "Fixture Schedule" },
  { value: "rcp", label: "Reflected Ceiling Plan (RCP)" },
  { value: "panel_schedule", label: "Panel Schedule" },
  { value: "plan_notes", label: "Plan Notes / Specs" },
  { value: "detail", label: "Detail Drawing" },
  { value: "site_plan", label: "Site Plan (Exterior)" },
];

export function DrawingViewer({ onSnippetCaptured, highlightSnippet }: DrawingViewerProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // PDF state
  const pdfRef = useRef<any>(null);
  const [pdfLoaded, setPdfLoaded] = useState(false);
  const [totalPages, setTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageThumbs, setPageThumbs] = useState<PageThumb[]>([]);
  const [pageLabels, setPageLabels] = useState<Record<number, string>>({});

  // Viewport state
  const [scale, setScale] = useState(1.5);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const isPanning = useRef(false);
  const panStart = useRef({ x: 0, y: 0 });
  const offsetRef = useRef({ x: 0, y: 0 });

  // Snip state
  const [mode, setMode] = useState<DrawingMode>("pan");
  const isDrawing = useRef(false);
  const snipStart = useRef({ x: 0, y: 0 });
  const snipRect = useRef({ x: 0, y: 0, width: 0, height: 0 });
  const overlayRef = useRef<HTMLCanvasElement>(null);

  // Snippet label modal
  const [pendingSnip, setPendingSnip] = useState<{
    imageData: string;
    bbox: { x: number; y: number; width: number; height: number };
  } | null>(null);
  const [snippetLabel, setSnippetLabel] = useState("rcp");
  const [snippetSubLabel, setSnippetSubLabel] = useState("");

  // Keep offsetRef in sync
  useEffect(() => {
    offsetRef.current = offset;
  }, [offset]);

  // Load PDF.js from CDN
  useEffect(() => {
    if (typeof window === "undefined") return;
    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs";
    script.type = "module";
    document.head.appendChild(script);
    return () => {
      document.head.removeChild(script);
    };
  }, []);

  const loadPdfJs = useCallback(async () => {
    const pdfjsLib = (await import(
      /* @ts-ignore */
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs"
    )) as any;
    pdfjsLib.GlobalWorkerOptions.workerSrc =
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs";
    return pdfjsLib;
  }, []);

  const renderPage = useCallback(
    async (pageNum: number, sc: number, off: { x: number; y: number }) => {
      if (!pdfRef.current || !canvasRef.current) return;
      const page = await pdfRef.current.getPage(pageNum);
      const viewport = page.getViewport({ scale: sc });
      const canvas = canvasRef.current;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      const ctx = canvas.getContext("2d")!;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      await page.render({ canvasContext: ctx, viewport }).promise;

      // Draw highlight box if needed
      if (highlightSnippet && highlightSnippet.page_number === pageNum) {
        const b = highlightSnippet.bbox;
        ctx.strokeStyle = "#dc2626";
        ctx.lineWidth = 3;
        ctx.strokeRect(b.x * sc, b.y * sc, b.width * sc, b.height * sc);
      }
    },
    [highlightSnippet]
  );

  // Re-render when highlight changes
  useEffect(() => {
    if (pdfLoaded) {
      renderPage(currentPage, scale, offset);
    }
  }, [highlightSnippet, pdfLoaded, currentPage, scale, offset, renderPage]);

  const buildThumbs = useCallback(
    async (pdf: any, count: number) => {
      const thumbs: PageThumb[] = [];
      const labels: Record<number, string> = {};
      for (let i = 1; i <= Math.min(count, 50); i++) {
        const page = await pdf.getPage(i);
        const viewport = page.getViewport({ scale: 0.15 });
        const offscreenCanvas = document.createElement("canvas");
        offscreenCanvas.width = viewport.width;
        offscreenCanvas.height = viewport.height;
        const ctx = offscreenCanvas.getContext("2d")!;
        await page.render({ canvasContext: ctx, viewport }).promise;
        // Try to detect sheet label from metadata — fall back to "Sheet N"
        const label = `Sheet ${i}`;
        labels[i] = label;
        thumbs.push({ pageNum: i, label, dataUrl: offscreenCanvas.toDataURL("image/jpeg", 0.6) });
      }
      setPageLabels(labels);
      setPageThumbs(thumbs);
    },
    []
  );

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const pdfjsLib = await loadPdfJs();
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      pdfRef.current = pdf;
      setTotalPages(pdf.numPages);
      setCurrentPage(1);
      setPdfLoaded(true);
      setScale(1.5);
      setOffset({ x: 0, y: 0 });

      // Render first page
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 1.5 });
      if (canvasRef.current) {
        canvasRef.current.width = viewport.width;
        canvasRef.current.height = viewport.height;
        const ctx = canvasRef.current.getContext("2d")!;
        await page.render({ canvasContext: ctx, viewport }).promise;
      }

      // Build thumbnails async
      buildThumbs(pdf, pdf.numPages);
    },
    [loadPdfJs, buildThumbs]
  );

  const goToPage = useCallback(
    async (pageNum: number) => {
      if (!pdfRef.current) return;
      setCurrentPage(pageNum);
      await renderPage(pageNum, scale, offset);
    },
    [renderPage, scale, offset]
  );

  const zoomIn = useCallback(() => {
    const newScale = Math.min(scale * 1.25, 6);
    setScale(newScale);
    renderPage(currentPage, newScale, offset);
  }, [scale, currentPage, offset, renderPage]);

  const zoomOut = useCallback(() => {
    const newScale = Math.max(scale * 0.8, 0.5);
    setScale(newScale);
    renderPage(currentPage, newScale, offset);
  }, [scale, currentPage, offset, renderPage]);

  const fitToWidth = useCallback(async () => {
    if (!pdfRef.current || !containerRef.current) return;
    const page = await pdfRef.current.getPage(currentPage);
    const container = containerRef.current;
    const naturalVp = page.getViewport({ scale: 1 });
    const newScale = (container.clientWidth - 32) / naturalVp.width;
    setScale(newScale);
    setOffset({ x: 0, y: 0 });
    renderPage(currentPage, newScale, { x: 0, y: 0 });
  }, [currentPage, renderPage]);

  // ─── Pan handlers ────────────────────────────────────────────────────
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (mode === "pan") {
        isPanning.current = true;
        panStart.current = { x: e.clientX - offsetRef.current.x, y: e.clientY - offsetRef.current.y };
      } else if (mode === "snip") {
        const rect = canvasRef.current!.getBoundingClientRect();
        isDrawing.current = true;
        snipStart.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
        snipRect.current = { x: snipStart.current.x, y: snipStart.current.y, width: 0, height: 0 };
      }
    },
    [mode]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (mode === "pan" && isPanning.current) {
        const newOff = {
          x: e.clientX - panStart.current.x,
          y: e.clientY - panStart.current.y,
        };
        setOffset(newOff);
      } else if (mode === "snip" && isDrawing.current) {
        const rect = canvasRef.current!.getBoundingClientRect();
        const curX = e.clientX - rect.left;
        const curY = e.clientY - rect.top;
        const r = {
          x: Math.min(curX, snipStart.current.x),
          y: Math.min(curY, snipStart.current.y),
          width: Math.abs(curX - snipStart.current.x),
          height: Math.abs(curY - snipStart.current.y),
        };
        snipRect.current = r;

        // Draw overlay
        if (overlayRef.current && canvasRef.current) {
          overlayRef.current.width = canvasRef.current.width;
          overlayRef.current.height = canvasRef.current.height;
          const ctx = overlayRef.current.getContext("2d")!;
          ctx.clearRect(0, 0, overlayRef.current.width, overlayRef.current.height);
          ctx.fillStyle = "rgba(220, 38, 38, 0.15)";
          ctx.fillRect(r.x, r.y, r.width, r.height);
          ctx.strokeStyle = "#dc2626";
          ctx.lineWidth = 2;
          ctx.setLineDash([6, 3]);
          ctx.strokeRect(r.x, r.y, r.width, r.height);
        }
      }
    },
    [mode]
  );

  const handleMouseUp = useCallback(async () => {
    if (mode === "pan") {
      isPanning.current = false;
    } else if (mode === "snip" && isDrawing.current) {
      isDrawing.current = false;
      const r = snipRect.current;
      if (r.width < 10 || r.height < 10) {
        // Too small, ignore
        if (overlayRef.current) {
          const ctx = overlayRef.current.getContext("2d")!;
          ctx.clearRect(0, 0, overlayRef.current.width, overlayRef.current.height);
        }
        return;
      }

      // Crop the canvas region
      const canvas = canvasRef.current!;
      const offscreen = document.createElement("canvas");
      offscreen.width = r.width;
      offscreen.height = r.height;
      const ctx = offscreen.getContext("2d")!;
      ctx.drawImage(canvas, r.x, r.y, r.width, r.height, 0, 0, r.width, r.height);
      const imageData = offscreen.toDataURL("image/png");

      // Bbox in PDF coords (unscaled)
      const pdfBbox = {
        x: r.x / scale,
        y: r.y / scale,
        width: r.width / scale,
        height: r.height / scale,
      };

      setPendingSnip({ imageData, bbox: pdfBbox });
      setSnippetLabel("rcp");
      setSnippetSubLabel("");

      // Clear overlay
      if (overlayRef.current) {
        const ctx = overlayRef.current.getContext("2d")!;
        ctx.clearRect(0, 0, overlayRef.current.width, overlayRef.current.height);
      }
    }
  }, [mode, scale]);

  const handleWheelZoom = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      const newScale = Math.min(Math.max(scale * delta, 0.5), 6);
      setScale(newScale);
      renderPage(currentPage, newScale, offset);
    },
    [scale, currentPage, offset, renderPage]
  );

  const confirmSnip = useCallback(() => {
    if (!pendingSnip) return;
    const snippet: SnippetData = {
      id: `snip-${Date.now()}`,
      page_number: currentPage,
      label: snippetLabel,
      sub_label: snippetSubLabel.trim(),
      bbox: pendingSnip.bbox,
      image_data: pendingSnip.imageData,
    };
    onSnippetCaptured(snippet);
    setPendingSnip(null);
    setMode("pan");
  }, [pendingSnip, currentPage, snippetLabel, snippetSubLabel, onSnippetCaptured]);

  const cancelSnip = useCallback(() => {
    setPendingSnip(null);
    setMode("pan");
  }, []);

  const cursor =
    mode === "snip" ? "crosshair" : isPanning.current ? "grabbing" : "grab";

  return (
    <div className="flex h-full flex-col" style={{ background: "#060606" }}>
      {/* ── Toolbar ── */}
      <div
        className="flex items-center gap-3 border-b px-4 py-2"
        style={{ borderColor: "#1a1a1a", background: "#0a0a0a" }}
      >
        {!pdfLoaded ? (
          <>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="rounded px-3 py-1.5 text-xs font-medium transition-colors"
              style={{
                fontFamily: "var(--font-ibm-plex-mono)",
                background: "#dc2626",
                color: "#fff",
                letterSpacing: "0.08em",
              }}
            >
              UPLOAD DRAWING SET
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleFileChange}
            />
            <span
              className="text-xs"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#444" }}
            >
              Drop a PDF drawing set to begin
            </span>
          </>
        ) : (
          <>
            {/* Mode toggles */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => setMode("pan")}
                title="Pan mode"
                className="rounded px-2.5 py-1 text-xs transition-colors"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  background: mode === "pan" ? "#1a1a1a" : "transparent",
                  color: mode === "pan" ? "#d4d4d4" : "#525252",
                  border: `1px solid ${mode === "pan" ? "#333" : "#1a1a1a"}`,
                  letterSpacing: "0.08em",
                }}
              >
                PAN
              </button>
              <button
                onClick={() => setMode("snip")}
                title="Snip mode — draw a rectangle"
                className="rounded px-2.5 py-1 text-xs transition-colors"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  background: mode === "snip" ? "rgba(220,38,38,0.15)" : "transparent",
                  color: mode === "snip" ? "#dc2626" : "#525252",
                  border: `1px solid ${mode === "snip" ? "rgba(220,38,38,0.4)" : "#1a1a1a"}`,
                  letterSpacing: "0.08em",
                }}
              >
                ✂ SNIP
              </button>
            </div>

            <div className="w-px self-stretch" style={{ background: "#1a1a1a" }} />

            {/* Zoom controls */}
            <div className="flex items-center gap-1">
              <button
                onClick={zoomOut}
                className="rounded px-2 py-1 text-xs transition-colors hover:text-white"
                style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#525252" }}
              >
                −
              </button>
              <span
                className="w-12 text-center text-xs"
                style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#666" }}
              >
                {Math.round(scale * 100)}%
              </span>
              <button
                onClick={zoomIn}
                className="rounded px-2 py-1 text-xs transition-colors hover:text-white"
                style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#525252" }}
              >
                +
              </button>
              <button
                onClick={fitToWidth}
                className="rounded px-2 py-1 text-xs transition-colors hover:text-white"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: "#525252",
                  letterSpacing: "0.08em",
                }}
              >
                FIT
              </button>
            </div>

            <div className="w-px self-stretch" style={{ background: "#1a1a1a" }} />

            {/* Page info */}
            <span
              className="text-xs"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "#525252" }}
            >
              {pageLabels[currentPage] || `Sheet ${currentPage}`} — Page {currentPage} / {totalPages}
            </span>

            {mode === "snip" && (
              <span
                className="ml-2 text-xs"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: "#dc2626",
                  letterSpacing: "0.08em",
                }}
              >
                DRAW A RECTANGLE TO SNIP
              </span>
            )}
          </>
        )}
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Page Thumbnail Sidebar ── */}
        {pdfLoaded && pageThumbs.length > 0 && (
          <div
            className="flex w-24 flex-col gap-1 overflow-y-auto p-2"
            style={{
              background: "#0a0a0a",
              borderRight: "1px solid #1a1a1a",
              scrollbarWidth: "thin",
              scrollbarColor: "#1a1a1a transparent",
            }}
          >
            {pageThumbs.map((thumb) => (
              <button
                key={thumb.pageNum}
                onClick={() => goToPage(thumb.pageNum)}
                className="flex flex-col items-center gap-1 rounded p-1 transition-colors"
                style={{
                  background: currentPage === thumb.pageNum ? "rgba(220,38,38,0.12)" : "transparent",
                  border: `1px solid ${currentPage === thumb.pageNum ? "rgba(220,38,38,0.35)" : "#1a1a1a"}`,
                }}
              >
                <img
                  src={thumb.dataUrl}
                  alt={thumb.label}
                  className="w-full rounded"
                  style={{ border: "1px solid #1a1a1a" }}
                />
                <span
                  className="w-full truncate text-center"
                  style={{
                    fontFamily: "var(--font-ibm-plex-mono)",
                    fontSize: "9px",
                    color: currentPage === thumb.pageNum ? "#dc2626" : "#444",
                  }}
                >
                  {thumb.pageNum}
                </span>
              </button>
            ))}
          </div>
        )}

        {/* ── Main Canvas Area ── */}
        <div
          ref={containerRef}
          className="relative flex-1 overflow-hidden"
          style={{ cursor, background: "#111" }}
          onWheel={handleWheelZoom}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={() => {
            isPanning.current = false;
          }}
        >
          {!pdfLoaded && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <p
                  className="mb-2"
                  style={{
                    fontFamily: "var(--font-cinzel)",
                    color: "#1a1a1a",
                    fontSize: "18px",
                    letterSpacing: "0.2em",
                  }}
                >
                  DRAWING WORKSPACE
                </p>
                <p
                  style={{
                    fontFamily: "var(--font-ibm-plex-mono)",
                    color: "#333",
                    fontSize: "11px",
                  }}
                >
                  Upload a PDF drawing set to begin
                </p>
              </div>
            </div>
          )}

          <div
            style={{
              transform: `translate(${offset.x}px, ${offset.y}px)`,
              position: "relative",
              display: "inline-block",
            }}
          >
            <canvas ref={canvasRef} style={{ display: pdfLoaded ? "block" : "none" }} />
            <canvas
              ref={overlayRef}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                pointerEvents: "none",
                display: pdfLoaded ? "block" : "none",
              }}
            />
          </div>
        </div>
      </div>

      {/* ── Snippet Label Modal ── */}
      {pendingSnip && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: "rgba(0,0,0,0.8)" }}
        >
          <div
            className="w-[420px] rounded-lg p-6"
            style={{
              background: "#0a0a0a",
              border: "1px solid #1a1a1a",
              boxShadow: "0 0 40px rgba(220,38,38,0.08)",
            }}
          >
            <h3
              className="mb-4 tracking-[0.15em]"
              style={{
                fontFamily: "var(--font-cinzel)",
                fontSize: "13px",
                color: "#d4d4d4",
              }}
            >
              LABEL SNIPPET
            </h3>

            {/* Preview */}
            <div
              className="mb-4 overflow-hidden rounded"
              style={{ border: "1px solid #1a1a1a", maxHeight: "160px" }}
            >
              <img
                src={pendingSnip.imageData}
                alt="Snippet preview"
                className="w-full object-contain"
                style={{ maxHeight: "160px" }}
              />
            </div>

            {/* Label select */}
            <div className="mb-3">
              <label
                className="mb-1.5 block text-xs"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  color: "#525252",
                  letterSpacing: "0.1em",
                }}
              >
                SNIPPET TYPE
              </label>
              <select
                value={snippetLabel}
                onChange={(e) => setSnippetLabel(e.target.value)}
                className="w-full rounded px-3 py-2 text-sm"
                style={{
                  background: "#111",
                  border: "1px solid #1a1a1a",
                  color: "#d4d4d4",
                  fontFamily: "var(--font-ibm-plex-mono)",
                  fontSize: "12px",
                }}
              >
                {SNIPPET_LABELS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Sub-label (area name for RCPs) */}
            {(snippetLabel === "rcp" || snippetLabel === "detail" || snippetLabel === "site_plan") && (
              <div className="mb-4">
                <label
                  className="mb-1.5 block text-xs"
                  style={{
                    fontFamily: "var(--font-ibm-plex-mono)",
                    color: "#525252",
                    letterSpacing: "0.1em",
                  }}
                >
                  AREA NAME {snippetLabel === "rcp" ? "(e.g. Floor 2 North Wing)" : "(optional)"}
                </label>
                <input
                  type="text"
                  value={snippetSubLabel}
                  onChange={(e) => setSnippetSubLabel(e.target.value)}
                  placeholder={snippetLabel === "rcp" ? "Floor 2 North Wing" : "Optional label"}
                  className="w-full rounded px-3 py-2 text-sm"
                  style={{
                    background: "#111",
                    border: "1px solid #1a1a1a",
                    color: "#d4d4d4",
                    fontFamily: "var(--font-ibm-plex-mono)",
                    fontSize: "12px",
                  }}
                />
              </div>
            )}

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                onClick={confirmSnip}
                className="flex-1 rounded py-2 text-xs font-medium transition-colors"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  background: "#dc2626",
                  color: "#fff",
                  letterSpacing: "0.1em",
                }}
              >
                ADD SNIPPET
              </button>
              <button
                onClick={cancelSnip}
                className="rounded px-4 py-2 text-xs transition-colors"
                style={{
                  fontFamily: "var(--font-ibm-plex-mono)",
                  background: "transparent",
                  color: "#525252",
                  border: "1px solid #1a1a1a",
                  letterSpacing: "0.1em",
                }}
              >
                CANCEL
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
