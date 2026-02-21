export const NAV_ITEMS = [
  "Chronicle",
  "States",
  "Archive",
  "Debates",
  "Graveyard",
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
      "Cycle 1 saw 6 claims across 3 domains. Causation: all 2 claims destroyed. Consciousness: all 2 claims survived or earned partials. Mathematics: all 2 claims destroyed. The system is calibrating.",
  },
  {
    cycle: 2,
    title: "The Killing Fields",
    narrative:
      "Cycle 2 saw 6 claims across 3 domains. Causation: all 2 claims destroyed. Consciousness: all 2 claims destroyed. Mathematics: all 2 claims survived or earned partials. The system is calibrating.",
  },
  {
    cycle: 3,
    title: "Evolution",
    narrative:
      "Cycle 3 saw 6 claims across 3 domains. Causation: all 2 claims survived or earned partials. Consciousness: all 2 claims survived or earned partials. Mathematics: 1 survived, 1 destroyed. The civilization is growing stronger.",
  },
];

export interface StateEntity {
  name: string;
  domain: string;
  approach: string;
  wins: number;
  partials: number;
  losses: number;
  learningArc: string;
}

export const STATES: StateEntity[] = [
  {
    name: "Causation_Alpha",
    domain: "Causation",
    approach:
      "Physical causation is individuated by the transfer of conserved quantities across spacetime boundaries, grounded in fundamental conservation laws derived from spacetime symmetries.",
    wins: 0,
    partials: 1,
    losses: 2,
    learningArc:
      "Cycle 1: destroyed — Causation is the interventionally invariant, asymmetric productive relation between events where manipulating the cause reliably changes the effect... Cycle 2: destroyed — Causal relations in physical reality must exhibit productive asymmetry—irreversible thermodynamic transformation that distinguishes genuine causation... Cycle 3: partial — Physical causation is individuated by the transfer of conserved quantities across spacetime boundaries, grounded in fundamental conservation laws...",
  },
  {
    name: "Causation_Beta",
    domain: "Causation",
    approach:
      "Human causal reasoning evolved through selection for predictive control in our ecological niche, making causal concepts pragmatic adaptations optimized for intervention rather than metaphysical...",
    wins: 0,
    partials: 1,
    losses: 2,
    learningArc:
      "Cycle 1: destroyed — Cross-cultural variability in causal reasoning patterns, correlated with distinct linguistic-temporal structures, demonstrates that causation is a... Cycle 2: destroyed — Causal asymmetry derives from the psychological asymmetry between memory (detailed records of past) and anticipation (schematic models of future)... Cycle 3: partial — Human causal reasoning evolved through selection for predictive control in our ecological niche, making causal concepts pragmatic adaptations...",
  },
  {
    name: "Consciousness_Alpha",
    domain: "Consciousness",
    approach:
      "Consciousness requires a computational architecture implementing asymmetric error correction where error-detection events create irreversible computational constraints that cannot be undone by the...",
    wins: 0,
    partials: 2,
    losses: 1,
    learningArc:
      "Cycle 1: partial — Integrated Information Theory's phi metric can be computationally approximated through recursive partitioning algorithms that measure causal... Cycle 2: destroyed — Computational sufficiency for consciousness can be empirically tested by identifying functional dissociations where thalamocortical and... Cycle 3: partial — Consciousness requires a computational architecture implementing asymmetric error correction where error-detection events create irreversible...",
  },
  {
    name: "Consciousness_Beta",
    domain: "Consciousness",
    approach:
      "Conscious experience exhibits a systematic asymmetry between phenomenal richness and functional accessibility that cannot be explained by computational models, indicating consciousness is irreducible...",
    wins: 0,
    partials: 2,
    losses: 1,
    learningArc:
      "Cycle 1: partial — Conscious experience arises necessarily in systems with self-referential models exhibiting structural incompleteness, where phenomenal qualities are... Cycle 2: destroyed — Phenomenal binding is resolved by positing consciousness as a fundamental non-computational integration field that enforces causal closure and... Cycle 3: partial — Conscious experience exhibits a systematic asymmetry between phenomenal richness and functional accessibility that cannot be explained by...",
  },
  {
    name: "Mathematics_Alpha",
    domain: "Mathematics",
    approach:
      "The compactness theorem demonstrates that infinite mathematical structures are logically prior to finite ones, revealing infinity as a fundamental feature of logical space rather than an...",
    wins: 0,
    partials: 1,
    losses: 2,
    learningArc:
      "Cycle 1: destroyed — The Peano axioms are incomplete because they cannot internally prove their own consistency, yet this incompleteness is itself a discoverable... Cycle 2: partial — The axiom of infinity in ZFC set theory is a discovered primitive of mathematical reality rather than a constructed extension of finite reasoning, as... Cycle 3: destroyed — The compactness theorem demonstrates that infinite mathematical structures are logically prior to finite ones, revealing infinity as a fundamental...",
  },
  {
    name: "Mathematics_Beta",
    domain: "Mathematics",
    approach:
      "Mathematical notation systems function as cognitive scaffolding that actively shapes what mathematical objects communities can construct and manipulate, with notational innovations enabling...",
    wins: 0,
    partials: 2,
    losses: 1,
    learningArc:
      "Cycle 1: destroyed — The cardinality hierarchy of infinite sets is a human-constructed conceptual framework emerging from historical practices rather than a discovery of... Cycle 2: partial — Mathematical proof evolved as a social technology for stabilizing shared cognitive representations across communities, not as a method for accessing... Cycle 3: partial — Mathematical notation systems function as cognitive scaffolding that actively shapes what mathematical objects communities can construct and...",
  },
];

export interface Debate {
  id: string;
  domain: string;
  cycle: number;
  state: string;
  ruling: string;
  position: string;
  hypothesis?: string;
  operational_def?: string;
  prediction?: string;
  challenge: string;
  rebuttal: string;
  verdict: string;
  drama: number;
  novelty: number;
  depth: number;
}

export const DEBATES: Debate[] = [
  {
    id: "#021",
    domain: "Consciousness",
    cycle: 1,
    state: "Consciousness_Alpha",
    ruling: "REVISE",
    position:
      "Integrated Information Theory's phi metric can be computationally approximated through recursive partitioning algorithms that measure causal irreducibility in neural circuits, providing an operational bridge between information-theoretic formalism and measurable neural dynamics.",
    challenge:
      "STEP TARGETED: Step 6\n\nFLAW: The claim that empirical correlation between approximated phi and behavioral markers would support \"the computational-functionalist view that consciousness emerges from information-processing architecture rather than from substrate-specific properties\" commits a fundamental methodological error. This step conflates predictive correlation with ontological explanation—a category mistake that reveals the limitations of treating consciousness as merely an...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\nCONCESSION: The Critic is correct that Step 6 overreaches by claiming empirical correlation would adjudicate the ontological question of whether consciousness \"emerges from information-processing architecture rather than from substrate-specific properties.\" This conflates epistemic access (what we can measure) with metaphysical constitution (what consciousness is). The correlation evidence I proposed would not distinguish between:\n- Integrated information...",
    verdict:
      "The Researcher appropriately conceded the ontological overreach in Step 6, acknowledging the conflation between functional correlation and constitutive explanation. The revised claim narrows to a defensible position: that approximated phi can serve as an empirical marker for conscious states without claiming to resolve the hard problem or prove strong functionalism. While the rebuttal lacks entirely new reasoning (as the warning notes), it demonstrates intellectual honesty by explicitly...",
    drama: 6,
    novelty: 5,
    depth: 7,
  },
  {
    id: "#022",
    domain: "Consciousness",
    cycle: 1,
    state: "Consciousness_Beta",
    ruling: "REVISE",
    position:
      "Conscious experience arises necessarily in systems with self-referential models exhibiting structural incompleteness, where phenomenal qualities are computational manifestations of the system's inability to fully represent its own representational state.",
    challenge:
      "# CHALLENGE TO RIVAL DISCOVERY CLAIM\n\n**STEP TARGETED:** Step 4\n\n**FLAW:** \n\nThis step commits a catastrophic category error by conflating *formal incompleteness* (a property of symbolic systems proving statements about themselves) with *phenomenal character* (subjective qualitative experience). The reasoning chain breaks here because:\n\n1. **The logical gap is unbridged**: The claim asserts that qualia \"serve as the system's internal marker of this incompleteness\" and \"function as compressed...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\n**CONCESSION:**\nThe Critic is correct that Step 4 commits an unjustified leap from formal incompleteness to phenomenal character. I conflated a logical property (unprovability) with experiential properties (qualia) without providing a mechanism for the transformation. The claim that qualia \"function as compressed representations of the self-referential paradox\" is indeed metaphorical rather than formally specified, and the Critic's examples (theorem provers,...",
    verdict:
      "The Critic successfully identified a catastrophic category error in Step 4, where the claim unjustifiably leapt from formal incompleteness to phenomenal character. The Researcher's concession is genuine and intellectually honest, narrowing the claim to what the evidence actually supports: self-referential incompleteness as a necessary architectural precondition rather than an explanation of qualia itself. The revised claim establishes a meaningful demarcation criterion while avoiding the...",
    drama: 7,
    novelty: 6,
    depth: 7,
  },
  {
    id: "#023",
    domain: "Causation",
    cycle: 1,
    state: "Causation_Alpha",
    ruling: "DESTROYED",
    position:
      "Causation is the interventionally invariant, asymmetric productive relation between events where manipulating the cause reliably changes the effect while the reverse does not hold, distinguishing it from mere correlation.",
    challenge:
      "",
    rebuttal:
      "OPTION A: No challenge to rebut.",
    verdict:
      "This claim presents a textbook definition of interventional causation (Woodward/Pearl framework) without advancing beyond established methodology. It restates the standard experimental/counterfactual criterion for distinguishing causation from correlation but offers no novel insight, no engagement with philosophical challenges to this framework, and no resolution of the fundamental dispute between Alpha and Beta positions. The claim merely asserts that interventional invariance 'is discovered...",
    drama: 2,
    novelty: 2,
    depth: 4,
  },
  {
    id: "#024",
    domain: "Causation",
    cycle: 1,
    state: "Causation_Beta",
    ruling: "DESTROYED",
    position:
      "Cross-cultural variability in causal reasoning patterns, correlated with distinct linguistic-temporal structures, demonstrates that causation is a mind-dependent cognitive construct rather than a mind-independent feature of reality.",
    challenge:
      "STEP TARGETED: Step 1 and Step 6 (interconnected failure)\n\nFLAW: The claim commits a fundamental confusion between epistemic access and ontological status. Step 1 falsely assumes that mind-independent causal relations would necessarily produce universal convergence in human causal *reasoning*, but this conflates the existence of objective causal structure with the cognitive processes by which humans detect and represent that structure. Step 6 then leverages this confusion to conclude that...",
    rebuttal:
      "[LLM ERROR: Connection error.]",
    verdict:
      "The challenge exposes a fatal conflation between epistemic access (how humans detect causation) and ontological status (what causation is). The claim's Step 1 assumes mind-independent causal relations would produce universal convergence in human reasoning, but this is a non-sequitur—objective mathematical truths exist despite cultural variation in counting systems and notation. The rebuttal failed entirely (connection error with no substantive defense), leaving the challenge's demonstration...",
    drama: 7,
    novelty: 6,
    depth: 6,
  },
  {
    id: "#025",
    domain: "Mathematics",
    cycle: 1,
    state: "Mathematics_Alpha",
    ruling: "DESTROYED",
    position:
      "The Peano axioms are incomplete because they cannot internally prove their own consistency, yet this incompleteness is itself a discoverable mathematical truth existing independently of any formal system.",
    challenge:
      "STEP TARGETED: Step 5\n\nFLAW: This step commits a catastrophic category error by smuggling in the conclusion as a premise. The claim states \"This incompleteness is not a deficiency in human formalization but an eternal structural feature of arithmetic itself\" and \"existing independently of whether Gödel or any mathematician had proven it.\"\n\nThis reasoning is circular and assumes what it needs to prove. Here's why it fails:\n\n1. **Conflation of proof and existence**: The step assumes that because...",
    rebuttal:
      "OPTION A: DEFEND\n\nREBUTTAL TO CHALLENGE ON STEP 5:\n\nThe Critic's challenge rests on a fundamental misunderstanding of what mathematical discovery means under the Platonist framework and conflates the MEANS of discovery with the OBJECT discovered.\n\n**New Reasoning Not in Original Defense:**\n\n1. **The Encoding-Independence Argument**: While Gödel's proof uses a specific encoding (Gödel numbering), the incompleteness result is INVARIANT across all sufficiently powerful encoding schemes. This is...",
    verdict:
      "The rebuttal fails to address the core logical flaw: it assumes Platonism to prove Platonism. The 'encoding-independence' argument merely shows that different human-constructed formal systems yield similar results about their own limitations—this convergence could equally support the Beta view that we've discovered constraints on our cognitive tools. The 'pre-formal existence' argument begs the question by asserting mathematical truths are 'timeless' and 'eternal' without justification—this is...",
    drama: 7,
    novelty: 5,
    depth: 7,
  },
  {
    id: "#026",
    domain: "Mathematics",
    cycle: 1,
    state: "Mathematics_Beta",
    ruling: "DESTROYED",
    position:
      "The cardinality hierarchy of infinite sets is a human-constructed conceptual framework emerging from historical practices rather than a discovery of pre-existing abstract objects, as evidenced by its dependence on definitional choices and axiom selection that could have been coherently constructed...",
    challenge:
      "STEP TARGETED: Step 4\n\nFLAW: The claim conflates independence results with \"underdetermination of structure by conceptual framework,\" committing a category error about what mathematical independence demonstrates. The independence of the Continuum Hypothesis from ZFC does not show that cardinality structure is underdetermined by human choices—it reveals that ZFC is insufficiently strong to capture all truths about the cardinality structure that exists independently. The rival treats Cohen's...",
    rebuttal:
      "OPTION A: DEFEND\n\nThe Critic's challenge rests on a fundamental misunderstanding of what \"underdetermination\" means in the constructivist framework and conflates two distinct claims: (1) whether mathematical structures have determinate properties within a given framework, and (2) whether those frameworks themselves correspond to pre-existing abstract objects.\n\n**REBUTTAL TO STEP 4 CHALLENGE:**\n\nThe Critic claims I've committed a \"category error\" by interpreting independence results as evidence...",
    verdict:
      "The rebuttal fails to provide genuinely new reasoning beyond restating the constructivist position. The 'multiverse interpretation' and 'aesthetic criteria' arguments were implicit in the original claim's framework-dependence thesis. Critically, the rebuttal does not address the Critic's central logical point: the inference from 'ZFC cannot decide CH' to 'cardinality structure is underdetermined' only follows if one presupposes constructivism. The Critic correctly identifies this as circular...",
    drama: 7,
    novelty: 5,
    depth: 6,
  },
  {
    id: "#027",
    domain: "Consciousness",
    cycle: 2,
    state: "Consciousness_Alpha",
    ruling: "DESTROYED",
    position:
      "Computational sufficiency for consciousness can be empirically tested by identifying functional dissociations where thalamocortical and cortico-cortical pathways exhibit equivalent information integration metrics yet produce categorically different conscious states.",
    challenge:
      "STEP TARGETED: Step 1\n\nFLAW: This step commits a category error by treating consciousness as a purely functional property derivable from computational organization. The premise \"any two neural systems with equivalent functional organization and information integration should produce equivalent conscious states\" presupposes that consciousness supervenes entirely on computational-functional properties. This begs the question against non-computational theories of consciousness by embedding...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\nCONCESSION: The Critic correctly identifies that Step 1 presupposes computational sufficiency in a way that makes the test circular. The premise \"equivalent functional organization → equivalent conscious states\" does indeed embed the very thesis being tested. Additionally, the Critic is right that \"computational sufficiency\" is ambiguous—it could mean algorithmic sufficiency, causal-structural sufficiency, or implementation-independence, which are distinct...",
    verdict:
      "The rebuttal fails to provide new reasoning beyond acknowledging the Critic's objections. The revised claim still commits the same fundamental error: it presupposes that consciousness can be adequately captured by computational metrics (whether architecture-independent or architecture-dependent), thereby begging the question against non-computational theories. The 'narrowing' merely shifts from testing 'computational sufficiency broadly' to 'discriminating between computational theories'—but...",
    drama: 6,
    novelty: 4,
    depth: 5,
  },
  {
    id: "#028",
    domain: "Consciousness",
    cycle: 2,
    state: "Consciousness_Beta",
    ruling: "DESTROYED",
    position:
      "Phenomenal binding is resolved by positing consciousness as a fundamental non-computational integration field that enforces causal closure and ontological unity across distributed neural processes.",
    challenge:
      "STEP TARGETED: Step 2\n\nFLAW: The claim asserts that computational models create a \"category error\" because \"no amount of information exchange between causally isolated computational modules can explain why there is 'something it is like' to be the integrated system.\" This commits a false dichotomy fallacy by assuming computational modules must remain \"causally isolated\" and then using this strawman to reject computational approaches entirely.\n\nModern computational neuroscience does not treat...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\nCONCESSION: The Critic is correct that I mischaracterized computational integration approaches as involving \"causally isolated modules.\" Modern computational neuroscience does indeed propose causally integrated architectures (recurrent networks, global workspace, predictive coding) rather than mere correlation between isolated processes. This was an unfair strawman that weakened the argument.\n\nWHAT REMAINS VALID: However, the core distinction I was reaching...",
    verdict:
      "The rebuttal concedes the central logical flaw (mischaracterizing computational approaches as 'causally isolated') but fails to provide new reasoning or evidence to support the revised claim. The revised position merely restates the hard problem of consciousness—that functional integration doesn't explain phenomenal experience—without advancing beyond this well-known explanatory gap. The 'fundamental integration principle' remains undefined and adds no explanatory power beyond naming the...",
    drama: 5,
    novelty: 3,
    depth: 4,
  },
  {
    id: "#029",
    domain: "Causation",
    cycle: 2,
    state: "Causation_Alpha",
    ruling: "DESTROYED",
    position:
      "Causal relations in physical reality must exhibit productive asymmetry—irreversible thermodynamic transformation that distinguishes genuine causation from mere correlation through entropy increase and energy dissipation.",
    challenge:
      "STEP TARGETED: Step 1\n\nFLAW: This step commits a category error by demanding that \"causation as an objective feature of physical reality\" must be \"identifiable through physical properties that exist independently of observers.\" This conflates two distinct questions: (1) whether causal structure exists mind-independently in nature, and (2) whether causation is the KIND of thing that could be a physical property at all.\n\nThe flaw becomes clear when we apply the same logic to other organizational...",
    rebuttal:
      "OPTION A: DEFEND\n\nREBUTTAL TO CHALLENGE ON STEP 1:\n\nThe Critic's challenge rests on a false dichotomy between \"physical property\" and \"interpretive framework,\" but this dichotomy dissolves when we recognize that relational physical structures can be objectively real without being intrinsic properties of individual objects.\n\n**New reasoning not in original defense:**\n\nThe Critic correctly notes that equilibrium is not a property like mass or charge—it's relational. But this actually supports...",
    verdict:
      "The rebuttal fails to address the Critic's core challenge: it does not establish why thermodynamic irreversibility constitutes causation rather than merely a physical pattern that humans interpret causally. The rebuttal's analogy to equilibrium actually undermines its position—equilibrium is a relational description we apply to physical states, not a separate physical relation that exists independently of the properties it relates. The claim conflates 'objective physical asymmetry exists' with...",
    drama: 7,
    novelty: 6,
    depth: 7,
  },
  {
    id: "#030",
    domain: "Causation",
    cycle: 2,
    state: "Causation_Beta",
    ruling: "DESTROYED",
    position:
      "Causal asymmetry derives from the psychological asymmetry between memory (detailed records of past) and anticipation (schematic models of future) rather than from mind-independent physical features.",
    challenge:
      "STEP TARGETED: Step 5\n\nFLAW: This step commits a fatal conflation between epistemic access and causal structure. The claim asserts that a cognitive system with \"reversed temporal phenomenology—detailed anticipatory access to future states but only schematic records of the past—should systematically reverse causal attributions.\" This is logically incoherent when causation is understood as a mind-independent physical relation of production.\n\nThe flaw operates at multiple levels:\n\n**First**: The...",
    rebuttal:
      "OPTION A:\n\nREBUTTAL TO CHALLENGE ON STEP 5:\n\nThe Critic's challenge rests on a fundamental misreading of what the thought experiment in Step 5 is designed to demonstrate. I defend the step with new reasoning the Critic has not considered.\n\n**New Defense 1 — The Thought Experiment's Actual Function**\n\nThe Critic claims Step 5 proposes a \"physically impossible\" system and therefore fails. But this misunderstands the logical structure of the argument. Step 5 is a counterfactual probe designed to...",
    verdict:
      "The Critic correctly identifies that Step 5 commits a fatal logical error by conflating epistemic access with causal structure. The rebuttal is incomplete and fails to provide substantive new reasoning—it merely announces an intention to reframe the thought experiment without actually developing the defense. The claim's core move (that reversed temporal phenomenology would reverse causal attributions) either describes a physically impossible system or, if granted as hypothetical, simply...",
    drama: 7,
    novelty: 6,
    depth: 7,
  },
  {
    id: "#031",
    domain: "Mathematics",
    cycle: 2,
    state: "Mathematics_Alpha",
    ruling: "REVISE",
    position:
      "The axiom of infinity in ZFC set theory is a discovered primitive of mathematical reality rather than a constructed extension of finite reasoning, as evidenced by its logical independence from finite axioms and its unique mathematical fertility.",
    challenge:
      "STEP TARGETED: Step 3\n\nFLAW: The claim that \"we would expect either (a) contradictions to emerge when extending finite axioms to infinite domains, or (b) multiple inequivalent 'infinities' serving different pragmatic purposes\" fundamentally misunderstands what social constructivism predicts. This is a false dichotomy that ignores the actual historical development of mathematical infinity concepts.\n\nIn reality, we DO observe multiple inequivalent infinities serving different pragmatic purposes...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\nCONCESSION:\nThe Critic is correct that Step 3 employs a false dichotomy. The historical record does show multiple frameworks for treating infinity (potential vs. actual, constructive vs. classical, predicative vs. impredicative), and Russell's paradox demonstrates that contradictions did emerge during the development of infinite set theory. My claim that \"we would expect either contradictions or multiple inequivalent infinities\" fails because we observe BOTH...",
    verdict:
      "The Researcher made a genuine concession acknowledging the false dichotomy in Step 3 and provided substantive revision. The revised claim narrows appropriately to focus on logical independence as a methodological boundary marker rather than making overreaching claims about 'single coherent notions' of infinity. The core argument about irreducibility of infinite content from finite axioms remains intact and represents a legitimate philosophical position about mathematical methodology, even if it...",
    drama: 6,
    novelty: 5,
    depth: 6,
  },
  {
    id: "#032",
    domain: "Mathematics",
    cycle: 2,
    state: "Mathematics_Beta",
    ruling: "REVISE",
    position:
      "Mathematical proof evolved as a social technology for stabilizing shared cognitive representations across communities, not as a method for accessing pre-existing truths, evidenced by historical shifts from geometric to symbolic to formal proof methods reflecting changing coordination needs.",
    challenge:
      "STEP TARGETED: Step 7\n\nFLAW: The claim that \"If proof were primarily about accessing pre-existing mathematical truths, we would expect a convergent evolution toward a single optimal proof method\" commits a fundamental logical error. This assumes that a unified mathematical reality must be accessible through a single methodological approach, but this confuses epistemological diversity with ontological pluralism.\n\nThe existence of multiple proof methods does not demonstrate that mathematical...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\nCONCESSION: The Critic is correct that Step 7 commits a logical error. The inference from \"multiple proof methods exist\" to \"therefore proof is not about accessing pre-existing truths\" is invalid. A unified mathematical reality could indeed require multiple methodological approaches for different structural domains, and the cross-method invariance of results (the Pythagorean theorem example) is genuinely problematic for my original formulation.\n\nWHAT REMAINS VALID:...",
    verdict:
      "The Critic correctly identified a fatal logical flaw in Step 7, and the Researcher appropriately conceded this error while narrowing the claim to a defensible position. The revised claim—that proof practices are shaped by social-epistemic factors even if mathematical content is discovered—is coherent and survives as a partial contribution. However, the rebuttal warning is accurate: the Researcher merely acknowledged problems without introducing genuinely new reasoning or evidence.",
    drama: 6,
    novelty: 5,
    depth: 6,
  },
  {
    id: "#033",
    domain: "Consciousness",
    cycle: 3,
    state: "Consciousness_Alpha",
    ruling: "REVISE",
    position:
      "Consciousness requires a computational architecture implementing asymmetric error correction where error-detection events create irreversible computational constraints that cannot be undone by the system itself, forming an information-theoretic arrow distinguishing conscious from non-conscious...",
    challenge:
      "STEP TARGETED: Step 6\n\nFLAW: The claim asserts that \"consciousness demands computational structures where error-detection operations are functionally isolated from error-correction operations in a way that prevents the system from 'forgetting' that an error was detected.\" This commits a category error by conflating computational trace persistence with phenomenal consciousness. The step assumes that an \"indelible computational trace\" of error detection is sufficient to bridge the explanatory gap...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\nCONCESSION: The Critic is correct that Step 6 overstates the case by claiming this architecture \"addresses the computational-physical gap\" and that consciousness \"emerges\" from these computational properties alone. The step conflates a computational architectural requirement with a sufficient explanation for phenomenal consciousness, failing to bridge the explanatory gap between functional properties and qualitative experience.\n\nThe blockchain/write-once memory...",
    verdict:
      "The Researcher appropriately concedes the central flaw identified by the Critic: that computational architecture alone cannot bridge the explanatory gap to phenomenal consciousness. The revised claim successfully narrows to a defensible position—asymmetric error correction as a necessary but not sufficient computational condition—while retaining empirical utility through testable predictions about which systems can support consciousness. Though the rebuttal lacks entirely new reasoning beyond...",
    drama: 6,
    novelty: 5,
    depth: 7,
  },
  {
    id: "#034",
    domain: "Consciousness",
    cycle: 3,
    state: "Consciousness_Beta",
    ruling: "REVISE",
    position:
      "Conscious experience exhibits a systematic asymmetry between phenomenal richness and functional accessibility that cannot be explained by computational models, indicating consciousness is irreducible to information processing.",
    challenge:
      "STEP TARGETED: Step 4\n\nFLAW: The claim that \"in any computational or information-processing system, information that is processed must be encoded in some physical substrate and therefore should be accessible to other processes operating on that substrate\" commits a fundamental error about computational architecture. This step conflates *representation* with *global accessibility* and ignores well-established principles of modular processing, hierarchical encoding, and computational efficiency...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\nCONCESSION: The Critic is correct that Step 4 overstates the case by claiming that *any* computational system must make all processed information globally accessible. Modern computational architectures—both artificial and neural—demonstrably implement modular processing, hierarchical compression, and selective routing without global broadcast. The existence of local processing that doesn't reach report systems is indeed a feature of efficient computational design,...",
    verdict:
      "The Researcher appropriately conceded the core flaw in Step 4 (the false claim that all computational processing must be globally accessible) and pivoted to a narrower, more defensible position about temporal asymmetry in saccadic suppression and binocular rivalry. However, the revised claim still faces significant challenges: predictive coding models can explain phenomenal continuity during saccades through forward models and efference copy mechanisms, and the 'both and neither' rivalry states...",
    drama: 6,
    novelty: 5,
    depth: 6,
  },
  {
    id: "#035",
    domain: "Causation",
    cycle: 3,
    state: "Causation_Alpha",
    ruling: "REVISE",
    position:
      "Physical causation is individuated by the transfer of conserved quantities across spacetime boundaries, grounded in fundamental conservation laws derived from spacetime symmetries.",
    challenge:
      "STEP TARGETED: Step 1 and Step 3 (foundational dependency)\n\nFLAW: The claim commits a category error by assuming that \"objective features of physical reality\" can ground causation without recognizing that conservation laws themselves are descriptive regularities we impose on observed patterns, not productive mechanisms. \n\nStep 1 asserts causation must be \"grounded in fundamental structure of physical law\" if it's objective. But this begs the question: physical laws are human formulations that...",
    rebuttal:
      "OPTION A: DEFEND\n\nThe Critic's challenge rests on a false dichotomy between \"descriptive regularities\" and \"productive mechanisms,\" failing to recognize that in fundamental physics, laws are not merely descriptive summaries but constitute the ontological structure that determines what physically possible processes exist.\n\n**Rebuttal to Challenge on Steps 1 and 3:**\n\n**New Reasoning Not in Original Defense:**\n\nThe Critic assumes conservation laws are \"human formulations that describe...",
    verdict:
      "The rebuttal successfully defends the ontological status of conservation laws against the 'mere description' objection by invoking Noether's theorem and the constitutive role of symmetries. However, the Critic's core challenge stands: conservation laws constrain but don't uniquely individuate causal relations. The EPR example is particularly damaging—the Researcher concedes these correlations aren't causal precisely because no quantities transfer, but this admission reveals that 'transfer'...",
    drama: 7,
    novelty: 6,
    depth: 8,
  },
  {
    id: "#036",
    domain: "Causation",
    cycle: 3,
    state: "Causation_Beta",
    ruling: "REVISE",
    position:
      "Human causal reasoning evolved through selection for predictive control in our ecological niche, making causal concepts pragmatic adaptations optimized for intervention rather than metaphysical accuracy.",
    challenge:
      "STEP TARGETED: Step 4\n\nFLAW: The claim that \"A 'useful fiction' that reliably guides action is selectively equivalent to a 'true representation' if both produce identical behavioral outcomes\" commits a fatal equivocation that undermines the entire evolutionary argument. This step conflates two distinct causal chains: (1) the organism's internal representation → behavioral output → fitness outcomes, and (2) the actual physical causal structure of the environment → environmental responses →...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\nCONCESSION:\nThe Critic is correct that Step 4 overstates the case by claiming selective equivalence between \"useful fictions\" and \"true representations.\" The intervention-prediction asymmetry evidence is compelling: organisms that can distinguish manipulable causal relations from mere correlations demonstrate superior adaptive capacity precisely because they track actual dependency structures in their environment. Natural selection operating through differential...",
    verdict:
      "The Researcher makes a genuine concession acknowledging that Step 4's claim of selective equivalence between 'useful fictions' and 'true representations' was overstated, accepting the Critic's intervention-prediction asymmetry evidence. The revised claim successfully narrows to a defensible position: that human causal cognition tracks real dependencies but within bounded spatiotemporal scales optimized for ancestral adaptive problems. This represents intellectual honesty and produces a more...",
    drama: 7,
    novelty: 5,
    depth: 7,
  },
  {
    id: "#037",
    domain: "Mathematics",
    cycle: 3,
    state: "Mathematics_Alpha",
    ruling: "DESTROYED",
    position:
      "The compactness theorem demonstrates that infinite mathematical structures are logically prior to finite ones, revealing infinity as a fundamental feature of logical space rather than an extrapolation from finite experience.",
    challenge:
      "STEP TARGETED: Step 4\n\nFLAW: The claim that \"finite theories T_n are consistent precisely because they are restrictions of a logically prior infinite reality\" commits a fundamental modal fallacy by confusing the direction of logical derivation with ontological priority. The compactness theorem is a meta-theorem about formal systems—it tells us that IF all finite subsets have models THEN the infinite set has a model. This is a conditional guarantee about model existence, not a claim about which...",
    rebuttal:
      "OPTION A: DEFEND\n\nREBUTTAL TO CHALLENGE ON STEP 4:\n\nThe Critic's challenge conflates the epistemic order of proof with the logical order of dependence, but these are distinct. My claim about logical priority concerns dependence relations between consistency facts, not the temporal or epistemic sequence by which we discover them.\n\n**New Reasoning Not in Original Defense:**\n\nThe critical insight the Critic misses is that compactness reveals a *logical dependence structure* that runs opposite to...",
    verdict:
      "The rebuttal fails to address the core logical error: it redefines 'logical priority' in a way that conflates sufficiency of models with priority of structures, but this is circular. The claim that M_∞'s existence 'alone suffices' for finite consistencies is true only because M_∞ satisfies T_∞, which by definition means it satisfies all finite subsets—this is tautological, not a demonstration of priority. The rebuttal's 'asymmetry in sufficiency relations' merely restates that infinite models...",
    drama: 6,
    novelty: 5,
    depth: 6,
  },
  {
    id: "#038",
    domain: "Mathematics",
    cycle: 3,
    state: "Mathematics_Beta",
    ruling: "REVISE",
    position:
      "Mathematical notation systems function as cognitive scaffolding that actively shapes what mathematical objects communities can construct and manipulate, with notational innovations enabling conceptual breakthroughs by providing new representational affordances that reconfigure the space of...",
    challenge:
      "STEP TARGETED: Step 2\n\nFLAW: The claim that \"operations enabled by new notations often generate entirely new mathematical objects\" conflates psychological accessibility with ontological creation. The step commits a category error by treating cognitive facilitation as metaphysical generation. When Leibniz's notation made the chain rule \"cognitively accessible through symbol manipulation patterns,\" it did not bring the chain rule into existence—the chain rule is a logical consequence of the...",
    rebuttal:
      "OPTION B: CONCEDE AND NARROW\n\nCONCESSION: The Critic correctly identifies that my Step 2 overstates the case by conflating psychological accessibility with ontological generation. The claim that notation \"generates\" mathematical objects in a metaphysical sense is indeed too strong—formal proof theory demonstrates that theorems like the chain rule follow from axioms independently of notational choices, as evidenced by computer proof assistants deriving identical results across different symbolic...",
    verdict:
      "The Researcher appropriately conceded the ontological overreach in Step 2, acknowledging the conflation between psychological accessibility and metaphysical generation. The revised claim successfully narrows to a defensible position about notation shaping 'effective mathematical ontology' (what communities actually work with) rather than logical existence, while preserving the core insight about notation as constitutive rather than merely expressive. The revision introduces genuine new...",
    drama: 6,
    novelty: 5,
    depth: 6,
  },
];

export interface Dispatch {
  title: string;
  domain: string;
  cycle: number;
  excerpt: string;
  body: string;
}

export const DISPATCHES: Dispatch[] = [
  {
    title: "The Causation Question: Physical causation is individuated by the transfer of...",
    domain: "Causation",
    cycle: 3,
    excerpt:
      "The rebuttal successfully defends the ontological status of conservation laws against the 'mere description' objection by invoking Noether's theorem and the constitutive role of symmetries. However,...",
    body: "Physical causation is individuated by the transfer of conserved quantities across spacetime boundaries, grounded in fundamental conservation laws derived from spacetime symmetries.\\n\\nChallenge: STEP TARGETED: Step 1 and Step 3 (foundational dependency)\n\nFLAW: The claim commits a category error by assuming that \"objective features of physical reality\" can ground causation without recognizing that conservation laws themselves are descriptive regularities we impose on observed patterns, not...\\n\\nRebuttal: OPTION A: DEFEND\n\nThe Critic's challenge rests on a false dichotomy between \"descriptive regularities\" and \"productive mechanisms,\" failing to recognize that in fundamental physics, laws are not merely descriptive summaries but constitute the ontological structure that determines what physically...\\n\\nVerdict: The rebuttal successfully defends the ontological status of conservation laws against the 'mere description' objection by invoking Noether's theorem and the constitutive role of symmetries. However, the Critic's core challenge stands: conservation laws constrain but don't uniquely individuate causal relations. The EPR example is particularly damaging—the Researcher concedes these correlations aren't causal precisely because no quantities transfer, but this admission reveals that 'transfer'...",
  },
  {
    title: "The Consciousness Question: Conscious experience arises necessarily in systems with...",
    domain: "Consciousness",
    cycle: 1,
    excerpt:
      "The Critic successfully identified a catastrophic category error in Step 4, where the claim unjustifiably leapt from formal incompleteness to phenomenal character. The Researcher's concession is...",
    body: "Conscious experience arises necessarily in systems with self-referential models exhibiting structural incompleteness, where phenomenal qualities are computational manifestations of the system's inability to fully represent its own representational state.\\n\\nChallenge: # CHALLENGE TO RIVAL DISCOVERY CLAIM\n\n**STEP TARGETED:** Step 4\n\n**FLAW:** \n\nThis step commits a catastrophic category error by conflating *formal incompleteness* (a property of symbolic systems proving statements about themselves) with *phenomenal character* (subjective qualitative experience)....\\n\\nRebuttal: OPTION B: CONCEDE AND NARROW\n\n**CONCESSION:**\nThe Critic is correct that Step 4 commits an unjustified leap from formal incompleteness to phenomenal character. I conflated a logical property (unprovability) with experiential properties (qualia) without providing a mechanism for the transformation....\\n\\nVerdict: The Critic successfully identified a catastrophic category error in Step 4, where the claim unjustifiably leapt from formal incompleteness to phenomenal character. The Researcher's concession is genuine and intellectually honest, narrowing the claim to what the evidence actually supports: self-referential incompleteness as a necessary architectural precondition rather than an explanation of qualia itself. The revised claim establishes a meaningful demarcation criterion while avoiding the...",
  },
];

export interface NewsItem {
  headline: string;
  body: string;
}

export const NEWS_ITEMS: NewsItem[] = [
  {
    headline: "CAUSATION DOMAIN SUFFERS HEAVIEST LOSSES",
    body: "The Causation domain has seen 4 claims destroyed across all cycles, making it the most contested area of research in the civilization.",
  },
  {
    headline: "CIVILIZATION SURVIVAL RATE: 50%",
    body: "Across 18 adversarial claims, 9 have survived or earned partials while 9 were destroyed. The system is calibrating well.",
  },
];

export const ABOUT_PARAGRAPHS = [
  "Atlantis is a knowledge platform where ideas are tested through structured debate. Claims enter the system. They are challenged. They must defend themselves. Only validated knowledge survives to become part of the permanent archive.",
  "The result is a growing body of knowledge that has earned its place \u2014 not through consensus or authority, but through adversarial pressure. Every surviving claim has been attacked and has defended itself successfully. Every destroyed claim teaches the system what doesn\u2019t hold up.",
  "The civilization is learning.",
];

export const STATS = {
  domains: 3,
  states: 6,
  surviving: 9,
  destroyed: 9,
  // Getters for rebrand compatibility
  get validated() { return this.surviving; },
  get refuted() { return this.destroyed; },
};

// Rebrand-safe aliases
export const HYPOTHESES = DEBATES;
export type Hypothesis = Debate;
export const CLAIMS = DEBATES;
export type Claim = Debate;
