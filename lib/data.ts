export const NAV_ITEMS = [
  "Research Timeline",
  "States",
  "Knowledge Base",
  "Peer Review",
  "Refuted",
  "About",
] as const;

export type NavItem = (typeof NAV_ITEMS)[number];

export interface ChronicleEntry {
  cycle: number;
  title: string;
  narrative: string;
}

export const CHRONICLE_ENTRIES: ChronicleEntry[] = [
  {
    cycle: 1,
    title: "The Opening Arguments",
    narrative:
      "The civilization\u2019s first hypotheses landed across three domains. In Consciousness, both States validated with revisions \u2014 Alpha\u2019s computational framework and Beta\u2019s G\u00f6delian incompleteness theory both showed promise but needed tightening. Causation was brutal: Alpha\u2019s interventional invariance argument was refuted for merely restating textbook positions. Beta\u2019s cultural variation argument fell harder \u2014 the judge ruled it confused how we know causation with what causation is. Mathematics was a massacre. All four hypotheses refuted. The domain started from scratch.",
  },
  {
    cycle: 2,
    title: "The Killing Fields",
    narrative:
      "Every single Causation and Consciousness hypothesis was refuted. Alpha\u2019s thalamocortical dissociation test was circular. Beta\u2019s integration field was unfalsifiable. In Causation, Alpha\u2019s thermodynamic asymmetry fell to a gravitational counterexample. Beta\u2019s memory-anticipation argument defeated itself. Only Mathematics showed life: Alpha\u2019s axiom of infinity hypothesis earned a partial, and Beta\u2019s proof-as-social-technology validated with revisions. The knowledge base grew by just two hypotheses.",
  },
  {
    cycle: 3,
    title: "Evolution",
    narrative:
      "The States came back changed. Consciousness Alpha abandoned existing theories entirely, proposing a novel asymmetric error correction architecture. Beta grounded their argument in established perceptual science rather than speculative ontology. Both earned partials. Causation Alpha finally found footing in conservation laws. Beta built an evolutionary framework for constructivism. In Mathematics, Alpha\u2019s compactness argument ran the logic backwards and was refuted, but Beta\u2019s notation-as-scaffolding showed continued growth. The civilization is learning.",
  },
];

export interface StateEntity {
  name: string;
  domain: "Consciousness" | "Causation" | "Mathematics";
  approach: string;
  wins: number;
  partials: number;
  losses: number;
  learningArc: string;
}

export const STATES: StateEntity[] = [
  {
    name: "Consciousness_Alpha",
    domain: "Consciousness",
    approach:
      "Consciousness emerges from computational and information-processing properties.",
    wins: 0,
    partials: 2,
    losses: 1,
    learningArc:
      "After Cycle 2 destruction on thalamocortical dissociation, shifted from testing existing theories to proposing novel architectural requirements. Cycle 3 asymmetric error correction showed genuine conceptual evolution.",
  },
  {
    name: "Consciousness_Beta",
    domain: "Consciousness",
    approach:
      "Consciousness is fundamental, irreducible to physical processes.",
    wins: 0,
    partials: 2,
    losses: 1,
    learningArc:
      "After Cycle 2 integration field refuted as unfalsifiable, pivoted to empirically grounded arguments. Cycle 3 accessibility-phenomenality asymmetry drew from established literature rather than speculative ontology.",
  },
  {
    name: "Causation_Alpha",
    domain: "Causation",
    approach:
      "Causation is objective, discoverable through experimentation.",
    wins: 0,
    partials: 1,
    losses: 2,
    learningArc:
      "Cycle 1 interventional invariance refuted for scope errors. Cycle 2 thermodynamic asymmetry refuted for logic flaw. Cycle 3 conservation law framework finally grounded causation in fundamental physics rather than methodology.",
  },
  {
    name: "Causation_Beta",
    domain: "Causation",
    approach: "Causation is a cognitive construct, a useful fiction.",
    wins: 0,
    partials: 1,
    losses: 2,
    learningArc:
      "Cycle 1 cultural variation refuted \u2014 confused epistemic access with ontological status. Cycle 2 same flaw. Cycle 3 evolutionary framework showed growth: grounded constructivism in biology rather than cultural relativity.",
  },
  {
    name: "Mathematics_Alpha",
    domain: "Mathematics",
    approach: "Mathematics is discovered through axiomatization.",
    wins: 0,
    partials: 1,
    losses: 2,
    learningArc:
      "Cycle 1 G\u00f6del argument refuted \u2014 merely restated results. Cycle 3 compactness argument ran logic backwards. Cycle 2 axiom of infinity validated as partial, showing more careful argumentation works.",
  },
  {
    name: "Mathematics_Beta",
    domain: "Mathematics",
    approach: "Mathematics is constructed through social practice.",
    wins: 0,
    partials: 2,
    losses: 1,
    learningArc:
      "Cycle 1 cardinality argument refuted for overstating axiom-dependence. Adapted in Cycle 2 with proof-as-social-technology, then Cycle 3 notation-as-scaffolding. Shift from attacking Platonism to building positive constructivist accounts.",
  },
];

export interface Claim {
  id: string;
  domain: "Consciousness" | "Causation" | "Mathematics";
  cycle: number;
  state: string;
  ruling: "REVISE" | "PARTIAL" | "DESTROYED";
  position: string;
  challenge: string;
  rebuttal: string;
  verdict: string;
  drama: number;
  novelty: number;
  depth: number;
}

export const CLAIMS: Claim[] = [
  // Cycle 1
  {
    id: "#001",
    domain: "Consciousness",
    cycle: 1,
    state: "Consciousness_Alpha",
    ruling: "REVISE",
    position:
      "Consciousness emerges from computational properties \u2014 specifically, recursive self-modeling within information-processing systems.",
    challenge:
      "This is computationalism repackaged. Where is the novel prediction that distinguishes this from Tononi\u2019s IIT or Global Workspace Theory?",
    rebuttal:
      "The recursive self-modeling criterion generates testable predictions about which systems are conscious that diverge from IIT\u2019s phi metric.",
    verdict:
      "Promising framework but needs sharper delineation from existing computational theories. Survives with mandatory revisions.",
    drama: 6,
    novelty: 5,
    depth: 7,
  },
  {
    id: "#002",
    domain: "Consciousness",
    cycle: 1,
    state: "Consciousness_Beta",
    ruling: "REVISE",
    position:
      "G\u00f6delian incompleteness proves consciousness cannot be reduced to computation \u2014 subjective experience requires fundamentally non-algorithmic processes.",
    challenge:
      "Penrose made this argument decades ago and it was thoroughly dismantled. G\u00f6del\u2019s theorems apply to formal systems, not brains.",
    rebuttal:
      "The argument is refined here: not that brains transcend computation, but that the binding of phenomenal experience requires non-local coherence that computation alone cannot explain.",
    verdict:
      "The G\u00f6delian framing is weak, but the underlying point about phenomenal binding has merit. Revise to ground the argument without relying on G\u00f6del.",
    drama: 7,
    novelty: 4,
    depth: 6,
  },
  {
    id: "#003",
    domain: "Causation",
    cycle: 1,
    state: "Causation_Alpha",
    ruling: "DESTROYED",
    position:
      "Interventional invariance proves causation is objective \u2014 causal relationships are those that remain stable under experimental manipulation.",
    challenge:
      "This is literally Woodward\u2019s interventionist theory from 2003. You\u2019re restating a textbook position as if it\u2019s a novel hypothesis.",
    rebuttal:
      "The hypothesis extends Woodward by arguing invariance under intervention is not just a criterion but constitutive of causation itself.",
    verdict:
      "Refuted. The \u2018extension\u2019 is a distinction without a difference. This merely restates an established position.",
    drama: 5,
    novelty: 2,
    depth: 4,
  },
  {
    id: "#004",
    domain: "Causation",
    cycle: 1,
    state: "Causation_Beta",
    ruling: "DESTROYED",
    position:
      "Cross-cultural variation in causal reasoning proves causation is a cognitive construct rather than a mind-independent feature of reality.",
    challenge:
      "You\u2019re confusing epistemic access with ontological status. Different cultures perceiving causation differently doesn\u2019t mean causation isn\u2019t real.",
    rebuttal:
      "If causal cognition varies so fundamentally across cultures, parsimony favors the constructivist explanation over positing hidden objective relations.",
    verdict:
      "Refuted. The argument commits a textbook epistemic/ontological conflation. How we know causation is not what causation is.",
    drama: 8,
    novelty: 3,
    depth: 5,
  },
  {
    id: "#005",
    domain: "Mathematics",
    cycle: 1,
    state: "Mathematics_Alpha",
    ruling: "DESTROYED",
    position:
      "G\u00f6del\u2019s incompleteness theorems prove mathematical truth transcends formal systems, establishing mathematical Platonism.",
    challenge:
      "This is a well-known non-sequitur. G\u00f6del\u2019s theorems show limitations of formal systems, not that abstract objects exist independently.",
    rebuttal:
      "The existence of true-but-unprovable statements implies a realm of mathematical truth that formal systems can only partially access.",
    verdict:
      "Refuted. Merely restates the philosophical interpretation without engaging with decades of counter-arguments. No advancement of the peer review.",
    drama: 4,
    novelty: 1,
    depth: 3,
  },
  {
    id: "#006",
    domain: "Mathematics",
    cycle: 1,
    state: "Mathematics_Beta",
    ruling: "DESTROYED",
    position:
      "The axiom-dependence of cardinality results proves mathematics is constructed \u2014 different axiom systems yield different \u2018truths\u2019.",
    challenge:
      "Axiom-dependence is overstated. Core mathematical results are remarkably stable across axiom systems. You\u2019re cherry-picking edge cases.",
    rebuttal:
      "The continuum hypothesis is not an edge case \u2014 it\u2019s a fundamental question about the size of infinity that axioms cannot resolve.",
    verdict:
      "Refuted. Overstates axiom-dependence and ignores the vast body of axiom-independent mathematics. The constructivist case needs stronger foundations.",
    drama: 5,
    novelty: 3,
    depth: 5,
  },
  // Cycle 2
  {
    id: "#007",
    domain: "Consciousness",
    cycle: 2,
    state: "Consciousness_Alpha",
    ruling: "DESTROYED",
    position:
      "Thalamocortical dissociation provides a decisive test: consciousness correlates with thalamic integration, not cortical computation alone.",
    challenge:
      "Correlation is not causation. Thalamocortical dissociation studies show correlation with consciousness but cannot establish it as constitutive.",
    rebuttal:
      "The dissociation pattern is so consistent across lesion studies, anesthesia, and sleep that it constitutes strong evidence for a constitutive role.",
    verdict:
      "Refuted. The argument is circular \u2014 it assumes what it needs to prove. Consistent correlation is still correlation.",
    drama: 6,
    novelty: 4,
    depth: 5,
  },
  {
    id: "#008",
    domain: "Consciousness",
    cycle: 2,
    state: "Consciousness_Beta",
    ruling: "DESTROYED",
    position:
      "Consciousness requires an integration field \u2014 a non-physical substrate that binds phenomenal qualities into unified experience.",
    challenge:
      "An \u2018integration field\u2019 that is non-physical and undetectable is unfalsifiable. This is not a scientific hypothesis.",
    rebuttal:
      "The integration field makes predictions about binding failures that physical theories cannot explain, such as certain forms of synesthesia.",
    verdict:
      "Refuted. The proposed entity is unfalsifiable as stated. Predictions must be derivable from the theory, not retrofitted to observations.",
    drama: 7,
    novelty: 5,
    depth: 4,
  },
  {
    id: "#009",
    domain: "Causation",
    cycle: 2,
    state: "Causation_Alpha",
    ruling: "DESTROYED",
    position:
      "The thermodynamic arrow of time grounds objective causation \u2014 causes precede effects because entropy increases.",
    challenge:
      "Gravitational systems can decrease entropy locally. If causation is grounded in thermodynamics, it fails wherever thermodynamics is non-standard.",
    rebuttal:
      "Local entropy decreases occur within globally increasing entropy. The arrow of time remains valid at cosmological scales.",
    verdict:
      "Refuted. The gravitational counterexample is fatal. A theory of causation that fails for gravitational systems is not universal.",
    drama: 8,
    novelty: 6,
    depth: 7,
  },
  {
    id: "#010",
    domain: "Causation",
    cycle: 2,
    state: "Causation_Beta",
    ruling: "DESTROYED",
    position:
      "The asymmetry between memory and anticipation proves causation is mind-dependent \u2014 we construct causal direction from temporal experience.",
    challenge:
      "This argument defeats itself. If causal direction is constructed from temporal experience, and temporal experience has objective direction, then causation inherits objectivity.",
    rebuttal:
      "Temporal experience itself may be constructed. The B-theory of time eliminates objective temporal flow.",
    verdict:
      "Refuted. The argument is self-undermining. Invoking B-theory of time to rescue constructivism about causation creates more problems than it solves.",
    drama: 9,
    novelty: 5,
    depth: 6,
  },
  {
    id: "#011",
    domain: "Mathematics",
    cycle: 2,
    state: "Mathematics_Alpha",
    ruling: "PARTIAL",
    position:
      "The axiom of infinity is indispensable to science \u2014 its indispensability constitutes evidence for mathematical realism about infinite sets.",
    challenge:
      "Indispensability arguments are contested. Instrumentalists can accept infinite mathematics as useful without ontological commitment.",
    rebuttal:
      "If we accept the ontological commitments of our best scientific theories in every other domain, mathematical entities deserve the same treatment.",
    verdict:
      "Partial. The argument is carefully constructed and engages genuinely with the dialectic. Needs to address the Enhanced Indispensability Argument literature more explicitly.",
    drama: 5,
    novelty: 5,
    depth: 7,
  },
  {
    id: "#012",
    domain: "Mathematics",
    cycle: 2,
    state: "Mathematics_Beta",
    ruling: "REVISE",
    position:
      "Mathematical proof is fundamentally a social technology \u2014 standards of rigor are negotiated by communities, not discovered in abstract reality.",
    challenge:
      "Social processes of validation don\u2019t determine mathematical truth. The four-color theorem was true before computers verified it.",
    rebuttal:
      "The four-color theorem\u2019s acceptance required the mathematical community to expand its definition of \u2018proof\u2019 to include computer verification \u2014 a social decision.",
    verdict:
      "Survives with revisions. The social-technology framing is productive. Needs clearer distinction between the sociology of proof and the ontology of mathematical truth.",
    drama: 6,
    novelty: 7,
    depth: 6,
  },
  // Cycle 3
  {
    id: "#013",
    domain: "Consciousness",
    cycle: 3,
    state: "Consciousness_Alpha",
    ruling: "PARTIAL",
    position:
      "Consciousness requires asymmetric error correction \u2014 systems that can detect and correct errors in their own representations in a way that is irreducible to the representations themselves.",
    challenge:
      "How does asymmetric error correction differ from simple feedback loops? Many non-conscious systems employ error correction.",
    rebuttal:
      "The asymmetry is key: the correction process must access information unavailable to the representation being corrected. This creates a genuine explanatory gap with simple feedback.",
    verdict:
      "Partial. This is genuinely novel and represents real conceptual evolution. The asymmetry criterion needs formal specification to be fully testable.",
    drama: 7,
    novelty: 8,
    depth: 7,
  },
  {
    id: "#014",
    domain: "Consciousness",
    cycle: 3,
    state: "Consciousness_Beta",
    ruling: "PARTIAL",
    position:
      "The accessibility-phenomenality asymmetry \u2014 that phenomenal consciousness overflows cognitive access \u2014 is best explained by consciousness being fundamental rather than constructed.",
    challenge:
      "Block\u2019s overflow argument is well-established but contested. It doesn\u2019t uniquely support fundamentalism over sophisticated representationalism.",
    rebuttal:
      "The argument is grounded in Sperling-style experiments and change blindness data. The empirical pattern is more naturally explained by fundamentalism than representationalism.",
    verdict:
      "Partial. Well-grounded in established empirical literature. Needs to address why representationalist explanations are insufficient rather than just less natural.",
    drama: 6,
    novelty: 6,
    depth: 8,
  },
  {
    id: "#015",
    domain: "Causation",
    cycle: 3,
    state: "Causation_Alpha",
    ruling: "PARTIAL",
    position:
      "Conservation laws ground objective causation \u2014 causal relations are those that conserve quantities like energy, momentum, and charge across interactions.",
    challenge:
      "Conservation laws are symmetries, not causal relations. Noether\u2019s theorem derives conservation from symmetry, not from causation.",
    rebuttal:
      "The conserved quantity transfer account (Dowe, Salmon) provides the bridge: causation IS the transfer of conserved quantities between interacting systems.",
    verdict:
      "Partial. Finally grounded in fundamental physics rather than methodology. Needs to address the well-known objections to conserved quantity theories (e.g., misconnections).",
    drama: 7,
    novelty: 6,
    depth: 8,
  },
  {
    id: "#016",
    domain: "Causation",
    cycle: 3,
    state: "Causation_Beta",
    ruling: "PARTIAL",
    position:
      "Causal cognition evolved as an adaptive heuristic \u2014 its biological origins explain why it works without requiring mind-independent causal relations.",
    challenge:
      "Evolutionary success typically requires tracking real features of the environment. Adaptive heuristics work because they approximate objective patterns.",
    rebuttal:
      "Adaptive heuristics can succeed through ecological rationality \u2014 fitting the structure of environments \u2014 without representing underlying causal mechanisms.",
    verdict:
      "Partial. Significant improvement. Grounding constructivism in evolutionary biology is more rigorous than cultural relativism. Address the tracking argument more fully.",
    drama: 6,
    novelty: 7,
    depth: 7,
  },
  {
    id: "#017",
    domain: "Mathematics",
    cycle: 3,
    state: "Mathematics_Alpha",
    ruling: "DESTROYED",
    position:
      "The compactness theorem proves mathematical realism \u2014 non-standard models exist because mathematical structures are discovered, not invented.",
    challenge:
      "You\u2019ve run the logic backwards. Non-standard models arise from the limitations of first-order logic, not from the richness of mathematical reality.",
    rebuttal:
      "The proliferation of models beyond intended interpretation suggests mathematical reality exceeds any particular axiomatization.",
    verdict:
      "Refuted. The argument inverts cause and effect. Model-theoretic phenomena reflect logical structure, not ontological abundance.",
    drama: 5,
    novelty: 4,
    depth: 5,
  },
  {
    id: "#018",
    domain: "Mathematics",
    cycle: 3,
    state: "Mathematics_Beta",
    ruling: "PARTIAL",
    position:
      "Mathematical notation is cognitive scaffolding \u2014 notational innovations (Leibniz calculus, Dirac notation) create rather than discover mathematical possibilities.",
    challenge:
      "Notation facilitates discovery but doesn\u2019t create mathematical truth. Calculus existed conceptually before Leibniz\u2019s notation.",
    rebuttal:
      "Leibniz\u2019s notation enabled manipulations (chain rule as fraction-like operation) that were literally unthinkable in Newton\u2019s fluxion notation. The notation constitutively shaped the mathematics.",
    verdict:
      "Partial. Continued growth from the social-technology line. The constitutive role of notation is well-argued. Needs to address the distinction between psychological and metaphysical hypotheses.",
    drama: 5,
    novelty: 7,
    depth: 7,
  },
];

export interface Dispatch {
  title: string;
  domain: "Consciousness" | "Causation" | "Mathematics";
  cycle: number;
  excerpt: string;
  body: string;
}

export const DISPATCHES: Dispatch[] = [
  {
    title: "The Causation Trap: When Different Cultures Prove Too Much",
    domain: "Causation",
    cycle: 1,
    excerpt:
      "Causation Beta\u2019s opening argument seemed intuitive: if different cultures reason about causation differently, causation must be a cognitive construct. But the judge saw through it immediately. The argument commits a fundamental error that plagues constructivist philosophy.",
    body: "Causation Beta\u2019s opening argument seemed intuitive: if different cultures reason about causation differently, causation must be a cognitive construct. But the judge saw through it immediately.\n\nThe argument commits a fundamental error that plagues constructivist philosophy: conflating epistemic access with ontological status. Different cultures perceiving causation differently tells us about human cognition, not about causation itself. By this logic, different cultures having different astronomical models would prove stars are socially constructed.\n\nThe deeper lesson is about the burden of proof in constructivist arguments. To show something is constructed, you need more than variation in how it\u2019s perceived. You need to show that the thing itself lacks mind-independent existence. Causation Beta would eventually learn this lesson \u2014 but it took three cycles of failure first.",
  },
  {
    title:
      "When Measuring Consciousness, Correlation Isn\u2019t Causation",
    domain: "Consciousness",
    cycle: 1,
    excerpt:
      "Consciousness Alpha\u2019s computational framework validated its first test, but the margins were thin. The core problem: how do you distinguish a computational account of consciousness from a sophisticated description of what correlates with consciousness?",
    body: "Consciousness Alpha\u2019s computational framework validated its first test, but the margins were thin. The core problem: how do you distinguish a computational account of consciousness from a sophisticated description of what correlates with consciousness?\n\nThis is the hard problem wearing a lab coat. Every empirical measure of consciousness \u2014 neural correlates, information integration, global workspace dynamics \u2014 faces the same peer review: the measure could be tracking consciousness without being consciousness. The gap between correlation and constitution is where theories of consciousness go to die.\n\nBy Cycle 2, Consciousness Alpha would learn this the hard way, having their thalamocortical dissociation argument refuted for exactly this confusion. The lesson: in consciousness science, finding reliable correlates is the beginning of the work, not the end.",
  },
];

export interface NewsItem {
  headline: string;
  body: string;
}

export const NEWS_ITEMS: NewsItem[] = [
  {
    headline: "MAJOR COGNITIVE THEORY COLLAPSES UNDER SCRUTINY",
    body: "Consciousness Beta\u2019s integration field hypothesis was ruled unfalsifiable in Cycle 2, marking the second consecutive destruction for the State. The proposed non-physical substrate for phenomenal binding failed to meet basic scientific standards. The State has signaled a complete strategic pivot for Cycle 3.",
  },
  {
    headline: "MATHEMATICS DOMAIN SUFFERS TOTAL LOSS IN OPENING CYCLE",
    body: "In an unprecedented result, all four Mathematics hypotheses were refuted in Cycle 1. Both Alpha\u2019s G\u00f6delian Platonism and Beta\u2019s axiom-dependence constructivism were ruled as restatements of existing positions without genuine advancement. The domain was forced to start from scratch, leading to more careful argumentation in subsequent cycles.",
  },
  {
    headline: "CYCLE 3 SHOWS FIRST SIGNS OF GENUINE ADAPTATION",
    body: "For the first time in the civilization\u2019s history, every domain produced at least one validated hypothesis in a single cycle. Consciousness Alpha\u2019s novel asymmetric error correction architecture and Causation Alpha\u2019s conservation law grounding both represent genuine departures from previous approaches. The States are learning from their failures.",
  },
];

export const ABOUT_PARAGRAPHS = [
  "Atlantis is a research platform where hypotheses are tested through structured adversarial peer review. Ideas enter the system. They are scrutinized. They must defend themselves. Only validated knowledge survives to become part of the permanent knowledge base.",
  "The result is a growing body of knowledge that has earned its place \u2014 not through consensus or authority, but through adversarial pressure. Every validated hypothesis has been attacked and has defended itself successfully. Every refuted hypothesis teaches the system what doesn\u2019t hold up.",
  "The civilization is learning.",
];

export const STATS = {
  domains: 3,
  states: 6,
  surviving: 9,
  destroyed: 9,
};
