/**
 * Centralized constants for magic numbers across the application.
 * All hardcoded values should be defined here for easy maintenance and consistency.
 */

// ═══════════════════════════════════════
// INTERSECTION OBSERVER
// ═══════════════════════════════════════

/** Standard threshold for scroll reveal animations (10% visibility) */
export const SCROLL_REVEAL_THRESHOLD_DEFAULT = 0.1;

/** Detailed threshold for sections with complex layouts (8% visibility) */
export const SCROLL_REVEAL_THRESHOLD_DETAILED = 0.08;

/** Standard root margin with 60px bottom offset */
export const SCROLL_REVEAL_ROOT_MARGIN_STANDARD = "0px 0px -60px 0px";

/** Compact root margin with 40px bottom offset */
export const SCROLL_REVEAL_ROOT_MARGIN_COMPACT = "0px 0px -40px 0px";

// ═══════════════════════════════════════
// PAGE SCROLL
// ═══════════════════════════════════════

/** Scroll threshold (50% of viewport) to trigger "entered world" state */
export const PAGE_SCROLL_THRESHOLD = 0.5;

// ═══════════════════════════════════════
// PARTICLE ANIMATION (Hero Logo)
// ═══════════════════════════════════════

/** Distance threshold for particle-mouse attraction */
export const PARTICLE_ATTRACTION_DISTANCE = 150;

/** Force multiplier for particle attraction */
export const PARTICLE_ATTRACTION_FORCE = 0.02;

/** Velocity decay rate per frame (friction) */
export const PARTICLE_VELOCITY_DECAY = 0.99;

/** Opacity variation amplitude for pulse effect */
export const PARTICLE_PULSE_OPACITY_VARIATION = 0.15;

/** Minimum particle opacity */
export const PARTICLE_MIN_OPACITY = 0.03;

// ═══════════════════════════════════════
// KNOWLEDGE GRAPH
// ═══════════════════════════════════════

/** Number of force simulation iterations (reduced from 300 for performance) */
export const GRAPH_FORCE_ITERATIONS = 150;

/** Ideal edge distance for local (same-cycle) connections */
export const GRAPH_EDGE_DISTANCE_LOCAL = 100;

/** Ideal edge distance for non-local connections */
export const GRAPH_EDGE_DISTANCE_NONLOCAL = 150;

/** Spring force multiplier for edge attraction */
export const GRAPH_SPRING_FORCE = 0.02;

/** Repulsion force multiplier between nodes */
export const GRAPH_REPULSION_FORCE = 0.5;

/** Gravity force toward center */
export const GRAPH_GRAVITY_FORCE = 0.02;

/** Additional padding for minimum repulsion distance calculation */
export const GRAPH_NODE_PADDING = 40;

// ═══════════════════════════════════════
// ANIMATION DURATIONS (Tailwind classes)
// ═══════════════════════════════════════

/** Fast transitions (hover states, small UI elements) - 200ms */
export const ANIMATION_DURATION_FAST = "duration-200";

/** Standard transitions (most UI interactions) - 300ms */
export const ANIMATION_DURATION_STANDARD = "duration-300";

/** Slow transitions (expanding panels, reveals) - 500ms */
export const ANIMATION_DURATION_SLOW = "duration-500";

/** Very slow transitions (dramatic reveals, tombstones) - 700ms */
export const ANIMATION_DURATION_VERY_SLOW = "duration-700";

/** Section grid hover border animation - 400ms */
export const SECTION_GRID_HOVER_DURATION = "duration-[400ms]";
