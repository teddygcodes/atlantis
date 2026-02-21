"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { CLAIMS, type Claim } from "@/lib/data";

interface GraphNode {
  id: string;
  claim: Claim;
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  isLocal: boolean; // belongs to this state
}

interface GraphEdge {
  source: string;
  target: string;
}

/**
 * Build citation edges: claims in the same domain across different cycles
 * cite each other (evolving arguments). Claims from the same state in
 * sequential cycles have strong connections. Cross-state same-domain claims
 * have weaker connections (adversarial references).
 */
function buildGraph(
  stateName: string,
  stateClaims: Claim[]
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  if (stateClaims.length === 0) return { nodes: [], edges: [] };

  const domain = stateClaims[0].domain;
  // All claims in the same domain
  const domainClaims = CLAIMS.filter((c) => c.domain === domain);
  // Other-state claims in the same domain
  const otherClaims = domainClaims.filter((c) => c.state !== stateName);

  const allClaims = [...stateClaims, ...otherClaims];
  const nodes: GraphNode[] = allClaims.map((claim, i) => ({
    id: claim.id,
    claim,
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    radius: claim.state === stateName ? 24 : 16,
    isLocal: claim.state === stateName,
  }));

  const edges: GraphEdge[] = [];

  // Same-state sequential cycle connections (strong evolution links)
  for (let i = 0; i < stateClaims.length; i++) {
    for (let j = i + 1; j < stateClaims.length; j++) {
      if (Math.abs(stateClaims[i].cycle - stateClaims[j].cycle) === 1) {
        edges.push({ source: stateClaims[i].id, target: stateClaims[j].id });
      }
    }
  }

  // Cross-state same-cycle connections (adversarial references)
  for (const local of stateClaims) {
    for (const other of otherClaims) {
      if (local.cycle === other.cycle) {
        edges.push({ source: local.id, target: other.id });
      }
    }
  }

  // Cross-state adjacent-cycle references
  for (const local of stateClaims) {
    for (const other of otherClaims) {
      if (Math.abs(local.cycle - other.cycle) === 1) {
        edges.push({ source: local.id, target: other.id });
      }
    }
  }

  return { nodes, edges };
}

function useForceSimulation(
  initialNodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number
) {
  const nodesRef = useRef<GraphNode[]>([]);
  const [tick, setTick] = useState(0);
  const animRef = useRef<number>(0);

  useEffect(() => {
    if (width === 0 || height === 0) return;

    // Initialize positions in a circle
    const cx = width / 2;
    const cy = height / 2;
    const r = Math.min(width, height) * 0.3;
    nodesRef.current = initialNodes.map((n, i) => ({
      ...n,
      x: cx + r * Math.cos((2 * Math.PI * i) / initialNodes.length + Math.random() * 0.3),
      y: cy + r * Math.sin((2 * Math.PI * i) / initialNodes.length + Math.random() * 0.3),
      vx: 0,
      vy: 0,
    }));

    let iterations = 0;
    const maxIterations = 200;

    function simulate() {
      const nodes = nodesRef.current;
      const alpha = Math.max(0.001, 1 - iterations / maxIterations);

      // Repulsion between all nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (800 * alpha) / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          nodes[i].vx -= fx;
          nodes[i].vy -= fy;
          nodes[j].vx += fx;
          nodes[j].vy += fy;
        }
      }

      // Attraction along edges
      const nodeMap = new Map(nodes.map((n) => [n.id, n]));
      for (const edge of edges) {
        const s = nodeMap.get(edge.source);
        const t = nodeMap.get(edge.target);
        if (!s || !t) continue;
        const dx = t.x - s.x;
        const dy = t.y - s.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const idealDist = s.isLocal && t.isLocal ? 100 : 140;
        const force = (dist - idealDist) * 0.03 * alpha;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        s.vx += fx;
        s.vy += fy;
        t.vx -= fx;
        t.vy -= fy;
      }

      // Center gravity
      for (const node of nodes) {
        node.vx += (cx - node.x) * 0.01 * alpha;
        node.vy += (cy - node.y) * 0.01 * alpha;
      }

      // Apply velocities with damping
      for (const node of nodes) {
        node.vx *= 0.6;
        node.vy *= 0.6;
        node.x += node.vx;
        node.y += node.vy;
        // Clamp to bounds
        node.x = Math.max(node.radius + 10, Math.min(width - node.radius - 10, node.x));
        node.y = Math.max(node.radius + 10, Math.min(height - node.radius - 10, node.y));
      }

      iterations++;
      setTick((t) => t + 1);

      if (iterations < maxIterations) {
        animRef.current = requestAnimationFrame(simulate);
      }
    }

    animRef.current = requestAnimationFrame(simulate);
    return () => cancelAnimationFrame(animRef.current);
  }, [initialNodes, edges, width, height]);

  return { nodes: nodesRef.current, tick };
}

export function KnowledgeGraph({
  stateName,
  stateClaims,
}: {
  stateName: string;
  stateClaims: Claim[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: 400,
        });
      }
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const { nodes: graphNodes, edges: graphEdges } = buildGraph(
    stateName,
    stateClaims
  );

  const hasCitations = graphEdges.length > 0;

  const { nodes } = useForceSimulation(
    graphNodes,
    graphEdges,
    dimensions.width,
    dimensions.height
  );

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  const nodeColor = useCallback((node: GraphNode) => {
    if (!node.isLocal) return "#404040";
    return node.claim.ruling === "DESTROYED" ? "#525252" : "#dc2626";
  }, []);

  const nodeStroke = useCallback((node: GraphNode) => {
    if (!node.isLocal) return "#2a2a2a";
    return node.claim.ruling === "DESTROYED" ? "#404040" : "#991b1b";
  }, []);

  return (
    <div ref={containerRef} className="w-full">
      <div
        style={{
          backgroundColor: "#0e0e0e",
          border: "1px solid #1c1c1c",
          borderRadius: "12px",
          overflow: "hidden",
          position: "relative",
          height: "400px",
        }}
      >
        {!hasCitations ? (
          <div className="flex h-full items-center justify-center px-8">
            <p
              className="max-w-md text-center"
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "16px",
                fontWeight: 600,
                color: "#525252",
                fontStyle: "italic",
                lineHeight: "1.8",
              }}
            >
              No citation network yet. Knowledge graphs form as claims begin
              referencing each other across cycles.
            </p>
          </div>
        ) : (
          <svg
            width={dimensions.width}
            height={dimensions.height}
            style={{ display: "block" }}
          >
            {/* Edges */}
            {graphEdges.map((edge, i) => {
              const s = nodeMap.get(edge.source);
              const t = nodeMap.get(edge.target);
              if (!s || !t) return null;
              const isLocal = s.isLocal && t.isLocal;
              return (
                <line
                  key={`edge-${i}`}
                  x1={s.x}
                  y1={s.y}
                  x2={t.x}
                  y2={t.y}
                  stroke={isLocal ? "#dc2626" : "#2a2a2a"}
                  strokeWidth={isLocal ? 1.5 : 0.8}
                  strokeOpacity={isLocal ? 0.5 : 0.3}
                />
              );
            })}

            {/* Nodes */}
            {nodes.map((node) => (
              <g
                key={node.id}
                onMouseEnter={() => setHoveredNode(node)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: "pointer" }}
              >
                {/* Glow for local nodes */}
                {node.isLocal && node.claim.ruling !== "DESTROYED" && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={node.radius + 6}
                    fill="none"
                    stroke="#dc2626"
                    strokeWidth={1}
                    strokeOpacity={0.15}
                  />
                )}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.radius}
                  fill={nodeColor(node)}
                  stroke={nodeStroke(node)}
                  strokeWidth={1.5}
                  opacity={node.isLocal ? 1 : 0.5}
                />
                <text
                  x={node.x}
                  y={node.y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={node.isLocal ? "#f5f5f5" : "#737373"}
                  fontSize={node.isLocal ? "10px" : "8px"}
                  fontFamily="var(--font-mono)"
                  fontWeight={600}
                  letterSpacing="0.05em"
                >
                  {node.claim.id}
                </text>
              </g>
            ))}
          </svg>
        )}

        {/* Tooltip */}
        {hoveredNode && (
          <div
            style={{
              position: "absolute",
              left: Math.min(
                hoveredNode.x + 20,
                dimensions.width - 280
              ),
              top: Math.min(hoveredNode.y - 10, dimensions.height - 120),
              backgroundColor: "#171717",
              border: "1px solid #2a2a2a",
              borderRadius: "8px",
              padding: "12px 16px",
              maxWidth: "260px",
              pointerEvents: "none",
              zIndex: 10,
            }}
          >
            <div className="mb-2 flex items-center gap-3">
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "10px",
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
                  fontSize: "9px",
                  color: hoveredNode.claim.ruling === "DESTROYED" ? "#dc2626" : "#a3a3a3",
                  letterSpacing: "0.1em",
                }}
              >
                {hoveredNode.claim.ruling}
              </span>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "9px",
                  color: "#525252",
                  letterSpacing: "0.1em",
                }}
              >
                CYCLE {hoveredNode.claim.cycle}
              </span>
            </div>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "13px",
                fontWeight: 600,
                color: "#d4d4d4",
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
                  fontSize: "9px",
                  color: "#525252",
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
            bottom: "12px",
            left: "16px",
            display: "flex",
            gap: "16px",
            alignItems: "center",
          }}
        >
          <div className="flex items-center gap-2">
            <div
              style={{
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                backgroundColor: "#dc2626",
              }}
            />
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "9px",
                color: "#525252",
                letterSpacing: "0.1em",
              }}
            >
              SURVIVING
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div
              style={{
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                backgroundColor: "#525252",
              }}
            />
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "9px",
                color: "#525252",
                letterSpacing: "0.1em",
              }}
            >
              DESTROYED
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: "#404040",
                opacity: 0.5,
              }}
            />
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "9px",
                color: "#525252",
                letterSpacing: "0.1em",
              }}
            >
              OTHER STATE
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
