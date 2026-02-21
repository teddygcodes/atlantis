"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { HYPOTHESES, type Hypothesis } from "@/lib/data";

interface GraphNode {
  id: string;
  claim: Hypothesis;
  x: number;
  y: number;
  radius: number;
  isLocal: boolean;
}

interface GraphEdge {
  source: string;
  target: string;
  isLocal: boolean;
}

/**
 * Build graph data from state claims and related domain claims.
 * Run force layout synchronously to produce a stable, non-shaking result.
 */
function buildAndLayoutGraph(
  stateName: string,
  stateClaims: Hypothesis[],
  width: number,
  height: number
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  if (stateClaims.length === 0 || width === 0 || height === 0)
    return { nodes: [], edges: [] };

  const domain = stateClaims[0].domain;
  const otherClaims = HYPOTHESES.filter(
    (c) => c.domain === domain && c.state !== stateName
  );
  const allClaims = [...stateClaims, ...otherClaims];

  // Build edges
  const edges: GraphEdge[] = [];

  // Same-state sequential cycle connections
  for (let i = 0; i < stateClaims.length; i++) {
    for (let j = i + 1; j < stateClaims.length; j++) {
      if (Math.abs(stateClaims[i].cycle - stateClaims[j].cycle) === 1) {
        edges.push({
          source: stateClaims[i].id,
          target: stateClaims[j].id,
          isLocal: true,
        });
      }
    }
  }

  // Cross-state same-cycle connections
  for (const local of stateClaims) {
    for (const other of otherClaims) {
      if (local.cycle === other.cycle) {
        edges.push({ source: local.id, target: other.id, isLocal: false });
      }
    }
  }

  // Initialize positions in a circle (deterministic - no Math.random)
  const cx = width / 2;
  const cy = height / 2;
  const r = Math.min(width, height) * 0.28;

  // Simple deterministic hash for slight position jitter
  function hashOffset(id: string, axis: number): number {
    let h = 0;
    for (let i = 0; i < id.length; i++) {
      h = ((h << 5) - h + id.charCodeAt(i) + axis * 31) | 0;
    }
    return ((h % 20) - 10);
  }

  const nodes: GraphNode[] = allClaims.map((claim, i) => ({
    id: claim.id,
    claim,
    x:
      cx +
      r * Math.cos((2 * Math.PI * i) / allClaims.length) +
      hashOffset(claim.id, 0),
    y:
      cy +
      r * Math.sin((2 * Math.PI * i) / allClaims.length) +
      hashOffset(claim.id, 1),
    radius: claim.state === stateName ? 26 : 16,
    isLocal: claim.state === stateName,
  }));

  // Run force simulation synchronously to completion
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const iterations = 300;

  for (let iter = 0; iter < iterations; iter++) {
    const alpha = 1 - iter / iterations;
    const decay = alpha * alpha; // quadratic decay for fast settling

    // Repulsion
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x;
        const dy = nodes[j].y - nodes[i].y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const minDist = nodes[i].radius + nodes[j].radius + 40;
        if (dist < minDist) {
          const force = ((minDist - dist) / dist) * 0.5 * decay;
          const fx = dx * force;
          const fy = dy * force;
          nodes[i].x -= fx;
          nodes[i].y -= fy;
          nodes[j].x += fx;
          nodes[j].y += fy;
        }
      }
    }

    // Attraction along edges
    for (const edge of edges) {
      const s = nodeMap.get(edge.source);
      const t = nodeMap.get(edge.target);
      if (!s || !t) continue;
      const dx = t.x - s.x;
      const dy = t.y - s.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const idealDist = edge.isLocal ? 100 : 150;
      const force = (dist - idealDist) * 0.02 * decay;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      s.x += fx;
      s.y += fy;
      t.x -= fx;
      t.y -= fy;
    }

    // Center gravity
    for (const node of nodes) {
      node.x += (cx - node.x) * 0.02 * decay;
      node.y += (cy - node.y) * 0.02 * decay;
    }
  }

  // Clamp to bounds
  const pad = 40;
  for (const node of nodes) {
    node.x = Math.max(pad + node.radius, Math.min(width - pad - node.radius, node.x));
    node.y = Math.max(pad + node.radius, Math.min(height - pad - node.radius, node.y));
  }

  return { nodes, edges };
}

export function KnowledgeGraph({
  stateName,
  stateClaims,
}: {
  stateName: string;
  stateClaims: Hypothesis[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const graphHeight = 420;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setWidth(entry.contentRect.width);
      }
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const { nodes, edges } = useMemo(
    () => buildAndLayoutGraph(stateName, stateClaims, width, graphHeight),
    [stateName, stateClaims, width]
  );

  const hasCitations = edges.length > 0;
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  return (
    <div ref={containerRef} className="w-full">
      <div
        style={{
          backgroundColor: "#0e0e0e",
          border: "1px solid #1c1c1c",
          borderRadius: "12px",
          overflow: "hidden",
          position: "relative",
          height: `${graphHeight}px`,
        }}
      >
        {!hasCitations ? (
          <div className="flex h-full items-center justify-center px-8">
            <p
              className="max-w-md text-center"
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "17px",
                fontWeight: 600,
                color: "#737373",
                fontStyle: "italic",
                lineHeight: "1.8",
              }}
            >
              No citation network yet. Knowledge graphs form as claims begin
              referencing each other across cycles.
            </p>
          </div>
        ) : width > 0 ? (
          <svg
            width={width}
            height={graphHeight}
            style={{ display: "block" }}
          >
            {/* Edges */}
            {edges.map((edge, i) => {
              const s = nodeMap.get(edge.source);
              const t = nodeMap.get(edge.target);
              if (!s || !t) return null;
              return (
                <line
                  key={`edge-${i}`}
                  x1={s.x}
                  y1={s.y}
                  x2={t.x}
                  y2={t.y}
                  stroke={edge.isLocal ? "#dc2626" : "#333"}
                  strokeWidth={edge.isLocal ? 2 : 1}
                  strokeOpacity={edge.isLocal ? 0.6 : 0.25}
                />
              );
            })}

            {/* Nodes */}
            {nodes.map((node) => {
              const color =
                !node.isLocal
                  ? "#404040"
                  : node.claim.ruling === "DESTROYED"
                    ? "#525252"
                    : "#dc2626";
              const strokeColor =
                !node.isLocal
                  ? "#2a2a2a"
                  : node.claim.ruling === "DESTROYED"
                    ? "#404040"
                    : "#991b1b";
              const isHovered = hoveredNode?.id === node.id;

              return (
                <g
                  key={node.id}
                  onMouseEnter={() => setHoveredNode(node)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{ cursor: "pointer" }}
                >
                  {/* Glow for local surviving nodes */}
                  {node.isLocal && node.claim.ruling !== "DESTROYED" && (
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={node.radius + 8}
                      fill="none"
                      stroke="#dc2626"
                      strokeWidth={isHovered ? 2 : 1}
                      strokeOpacity={isHovered ? 0.4 : 0.15}
                    />
                  )}
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={isHovered ? node.radius + 3 : node.radius}
                    fill={color}
                    stroke={strokeColor}
                    strokeWidth={2}
                    opacity={node.isLocal ? 1 : 0.5}
                    style={{ transition: "r 0.15s ease" }}
                  />
                  <text
                    x={node.x}
                    y={node.y}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill={node.isLocal ? "#f5f5f5" : "#737373"}
                    fontSize={node.isLocal ? "11px" : "9px"}
                    fontFamily="var(--font-mono)"
                    fontWeight={700}
                    letterSpacing="0.05em"
                  >
                    {node.claim.id}
                  </text>
                </g>
              );
            })}
          </svg>
        ) : null}

        {/* Tooltip */}
        {hoveredNode && (
          <div
            style={{
              position: "absolute",
              left: `${Math.min(hoveredNode.x + 20, (width || 400) - 290)}px`,
              top: `${Math.min(hoveredNode.y - 10, graphHeight - 130)}px`,
              backgroundColor: "#171717",
              border: "1px solid #2a2a2a",
              borderRadius: "8px",
              padding: "14px 18px",
              maxWidth: "270px",
              pointerEvents: "none",
              zIndex: 10,
            }}
          >
            <div className="mb-2 flex items-center gap-3">
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  color: "#dc2626",
                  letterSpacing: "0.1em",
                  fontWeight: 700,
                }}
              >
                {hoveredNode.claim.id}
              </span>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "10px",
                  color:
                    hoveredNode.claim.ruling === "DESTROYED"
                      ? "#dc2626"
                      : "#d4d4d4",
                  letterSpacing: "0.1em",
                }}
              >
                {hoveredNode.claim.ruling}
              </span>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "10px",
                  color: "#737373",
                  letterSpacing: "0.1em",
                }}
              >
                CYCLE {hoveredNode.claim.cycle}
              </span>
            </div>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "14px",
                fontWeight: 600,
                color: "#e5e5e5",
                lineHeight: "1.6",
              }}
            >
              {hoveredNode.claim.position.length > 150
                ? hoveredNode.claim.position.slice(0, 150) + "..."
                : hoveredNode.claim.position}
            </p>
            {!hoveredNode.isLocal && (
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "10px",
                  color: "#737373",
                  marginTop: "6px",
                  display: "block",
                }}
              >
                {hoveredNode.claim.state.replace("_", " ")}
              </span>
            )}
          </div>
        )}

        {/* Legend */}
        <div
          style={{
            position: "absolute",
            bottom: "14px",
            left: "18px",
            display: "flex",
            gap: "18px",
            alignItems: "center",
          }}
        >
          {[
            { color: "#dc2626", label: "VALIDATED" },
            { color: "#525252", label: "REFUTED" },
            { color: "#404040", label: "OTHER STATE", size: 8, opacity: 0.5 },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <div
                style={{
                  width: `${item.size || 10}px`,
                  height: `${item.size || 10}px`,
                  borderRadius: "50%",
                  backgroundColor: item.color,
                  opacity: item.opacity || 1,
                }}
              />
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "10px",
                  color: "#737373",
                  letterSpacing: "0.1em",
                }}
              >
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
