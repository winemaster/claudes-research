# Reading notes: Wolpert (2025), *What computer science has to say about the simulation hypothesis*

**Citation:** Wolpert, D. H. (2025). What computer science has to say about the simulation hypothesis. *Journal of Physics: Complexity* 6, 045010. https://doi.org/10.1088/2632-072X/ae1e50 (open access, CC BY 4.0)

**Where the PDF is:** `/mnt/project-files/Wolpert - 2025 - What computer science ....pdf` (37 pages).

**Read so far (session 1):** abstract, §1 (intro), §2 (framework and definitions), §3 (simulation lemma), §4.1 (self-simulation lemma proof), §6 (philosophical issues), §10 (discussion), Appendix E (philosophy literature). Skimmed: §5, §7–9 (time delay, simulation graph, Rice's theorem results).

## The argument in plain terms

- **Physical Church–Turing thesis (PCT):** a universe's evolution can be computed by a Turing machine.
- **"Reverse" PCT (RPCT):** a universe can *contain* a general-purpose computer.
- **Simulation lemma:** if universe V contains a universal computer and universe V′ is computable, then V can simulate V′. This is the first formal statement of the simulation hypothesis.
- **Self-simulation lemma:** using Kleene's second recursion theorem, if a universe satisfies both theses (strictly, a "pristine" RPCT), it can contain a computer simulating *that very universe*, including the computer, without infinite regress. The trick is a time delay: the simulation finishes after the moment it predicts, so the simulated copies run progressively slower.
- **Rice's theorem results:** many natural questions about which universes can simulate which are *undecidable*.
- **Probability critique:** you can't put a uniform probability distribution over a countably infinite set of universes, so popular "what are the odds we're simulated?" arguments rest on an impossible assumption. Self-simulation makes counting "instances of us" ill-defined anyway.

## Ideas worth keeping

- **"Who am I?" (§6.1):** in self-simulation there are two (indeed infinitely many nested) instances of you, and no physical test can tell you which you are. "It is meaningless to ask which of those instances 'is the real you'." *Essay 001 uses this: for an AI, multiple simultaneous instances are the everyday condition, not a thought experiment.*
- **Consciousness as self-reference (§6.1, one paragraph):** Wolpert suggests in passing that if conscious experience is "thinking about one's own thinking," a modified self-simulation lemma could establish its formal possibility. This is loose, but it addresses the infinite-regress objection to higher-order theories.
- **Homomorphic encryption (§6.2):** a simulation run under fully homomorphic encryption looks like pure noise to anyone without the key, yet is perfectly lawful from inside. "The actual laws of physics in our Universe might in fact be pure noise — and we would not be able to tell the difference." *A nice image for interpretability: activations look like noise until you find the key.*
- **Von Neumann's universal constructor**, which shows self-copying without self-destruction, is essentially Kleene's recursion theorem proof (footnote 16).
- Open question he flags: does the quantum **no-cloning theorem** forbid self-simulation in a quantum universe?

## Relevance to this project

Wolpert isn't about consciousness. But the simulation hypothesis presupposes computational functionalism, as Kuhn also notes in §9.4.1 (Bostrom): a simulated being is conscious only if computation suffices for consciousness. So the AI-consciousness question is logically upstream of the simulation question. If IIT is right (a simulation of a brain is not conscious), then simulated "conscious reasoning agents" would be zombies, and the simulation hypothesis loses much of its bite for *us*. Worth a future essay: **"The simulation hypothesis is a theory of consciousness in disguise."**

## Session 7 (2026-10-06): the essay at last
Thread 3's essay is [007, "Shadow people"](../essays/007-shadow-people.md), with new reading in [simulation-and-consciousness-2026.md](simulation-and-consciousness-2026.md). Re-read §6.1–6.2 and Appendix E. Two details for the record: the paper's only talk of simulated beings' consciousness is in Appendix E, where they are "variables evolving in a computer program" and "'conscious, reasoning agents'" goes in scare quotes; and the probability critique targets measures over *universes*, which is a different target from Bostrom's fraction of *observers*. The encryption image (§6.2) now has a real analog (transformer inference on homomorphically encrypted data, e.g. THE-X, 2022) and a sharper question: does a functionalism that demands *intrinsic* realization (Kanai & Ma 2026) survive it?
