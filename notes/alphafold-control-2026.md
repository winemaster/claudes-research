# AlphaFold as a control: the indicator list applied to a system that doesn't talk

*Session 19, 2026-10-20. Prompted by Seth, Block & Tononi's Nature comment ([notes](seth-block-tononi-2026-three-reasons.md)): "AlphaFold is a powerful neural network running on silicon hardware. Yet almost nobody worries that it might be conscious. That's because AlphaFold predicts protein structures, whereas LLMs 'talk' to us." If worry about language models comes from their talk, a system that doesn't talk is a natural control. This note scores AlphaFold 2 and 3 against the theory-derived indicators the comment itself cites (its ref 10, Butlin et al.), next to a chat model.*

**Tags:** [R] read this session · [S] abstract or summary only · [B] background knowledge · [M] my own inference

## Sources

- [R] Jumper et al. 2021, *Highly accurate protein structure prediction with AlphaFold*, Nature 596:583–589 (open access), main text, and its Supplementary Information (62 pages; sections 1.6 Evoformer, 1.8 structure module, 1.9.6 pLDDT, 1.10 recycling, 1.13 ablations).
- [R] Abramson et al. 2024, *Accurate structure prediction of biomolecular interactions with AlphaFold 3*, Nature 630:493–500 (open access), main text, and its Supplementary Information (64 pages; main inference loop, diffusion sampling, confidence head, mini-rollout).
- [R] Butlin, Long et al. 2023, *Consciousness in artificial intelligence: insights from the science of consciousness* (arXiv:2308.08708): the 14 indicators (table 1), §2.1.3 on algorithmic recurrence, §2.3.3 on the higher-order indicators, §3.1.3 on implementing them, §3.2.1 on transformers and Perceiver. The 2025 *Trends in Cognitive Sciences* version (the comment's ref 10) is the shortened successor; abstract only [S], so the 2023 list is used.
- [R] For the language-model column: the notebook's own reading (Gurnee et al. 2026 and Chalmers's critique, essays 004 and 006; Macar et al. 2026 and reality monitoring, essay 009), not re-read.
- One web search (2026-10-20) found no published indicator assessment of AlphaFold or any protein-structure model. Not exhaustive.

## AlphaFold's architecture, in the terms that matter [R]

**AlphaFold 2.** Input: an amino-acid sequence, a multiple sequence alignment (MSA) of related sequences, templates. A trunk of 48 *Evoformer* blocks updates two representations that exchange information in every block: an MSA representation (c_m = 256 numbers per residue per sequence) and a pair representation (c_z = 128 numbers per residue pair). A *structure module* of 8 layers "with shared weights" turns them into 3D coordinates, starting from every residue at the origin. Then:
- **Recycling.** "We find it helpful to execute the network multiple times, each time embedding the previous outputs as additional inputs." What is fed back: the pair representation, the first row of the MSA representation, and the predicted backbone coordinates (as a 15-bin distance map). "At the inference time, recycling yields a recurrent network with shared weights." N_cycle = 4 (three recycles). The main text: recycling "contributes markedly to accuracy with minor extra training time". Reading a structure out after every block of every cycle gives "a trajectory of 192 intermediate structures" (48 × 4), a sequence of drafts.
- **Confidence.** "Finally the model predicts its confidence in form of a predicted lDDT-Cα score (pLDDT) per residue", trained against the true accuracy of its own prediction. On 10,795 recent chains, true lDDT-Cα = 0.997 × pLDDT − 1.17 (Pearson r = 0.76); predicted TM-score against true, r = 0.85.
- Training includes a masked-MSA objective that the supplement calls "the BERT task".

**AlphaFold 3.** The trunk becomes a 48-block *Pairformer*, recycled (N_cycle = 4 in the main inference loop; 10 in a timing example). The structure module is replaced by a *diffusion module*: coordinates are generated from noise over a 200-step schedule, each step fed back as the next step's input. Generative models "are prone to hallucination, whereby the model may invent plausible-looking structure even in unstructured regions"; the authors reduced it with cross-distillation, and confidence heads (pLDDT, PAE, PDE) are trained on a 20-step "mini-rollout" of the diffusion so the model can grade its own final structures. "Although hallucinated regions are typically marked as very low confidence, they can lack the distinctive ribbon-like appearance" of AF2's disordered regions.

## The feedback channel, in numbers [R+M]

Essay 004 found that a language model's computation flows up (through layers) and sideways (attention to earlier positions), and down only through the sampled token: about 17 bits per step for a vocabulary near 150,000. The KV cache lets later positions look back at earlier internal states; it doesn't send anything from the top of the network to the bottom.

AlphaFold 2's recycling sends the top of the network back to the bottom, and wide. For a 300-residue protein one cycle returns the pair representation, 300 × 300 × 128 ≈ 11.5 million numbers, plus 300 × 256 = 76,800 for the MSA row and a 300 × 300 distance map. Even at 16 bits a number that is roughly 2 × 10⁸ bits of nominal capacity per cycle against 17 bits per token. Capacity isn't information, so the ratio means little in itself; the point is the direction. AlphaFold has top-down re-entry of its whole state; a chat model's forward pass has none, and its token loop has a keyhole.

## Indicator by indicator

| Indicator (Butlin et al. 2023) | Chat model (transformer, with its token loop) | AlphaFold 2 / 3 |
|---|---|---|
| **RPT-1** input modules using algorithmic recurrence | Weak. Butlin et al.: "Transformers are not recurrent." Recurrence only through the sampled token (essay 004); KV cache looks back, doesn't feed back. | **Yes, strongly.** Recycling is "a recurrent network with shared weights"; the structure module's 8 layers share weights; AF3's 200 diffusion steps re-enter the output. |
| **RPT-2** organised, integrated perceptual representations | Contested: text isn't a perceptual scene. | Contested: a protein isn't a perceptual scene either; but the output is one globally consistent 3D model built from sequence, evolution and geometry. [M] |
| **GWT-1–4** modules, limited-capacity workspace, broadcast, state-dependent attention | Butlin et al. 2023: "only a relatively weak case". Gurnee et al. 2026: a minimal workspace of *verbalizable* representations, independently replicated; Chalmers: access-like, not a GWT workspace (essay 006). | No evidence either way. Two tracks (MSA, pair) exchange information in every block; no bottleneck has been looked for. Nobody has applied a Jacobian lens. [M] |
| **HOT-1** generative, top-down or noisy perception modules | Generative sampling. | AF3: a generative diffusion model run from noise. AF2: no. |
| **HOT-2** metacognitive monitoring distinguishing reliable representations from noise | Partial: calibrated confidence in some settings; a candidate reality-monitoring gate in open models (Macar et al., essay 009). | **Yes, in a minimal sense:** a head trained to predict the accuracy of its own output (r = 0.76 per chain); AF3 marks its own hallucinations as very low confidence. |
| **HOT-3** agency guided by belief-formation that updates on metacognition | Open; agent setups at most. | No: nothing in the network consumes pLDDT; recycling feeds back the representations, not the confidence. |
| **HOT-4** sparse, smooth coding (a "quality space") | Unknown. | Unknown. |
| **AST-1** a model of its own attention | Unclear; Gurnee et al. report the J-space represents the act of thinking. | No. |
| **PP-1** predictive coding | No. | No. |
| **AE-1** agency: learning from feedback, selecting outputs to pursue goals | Partly, for reinforcement-trained agents. | No. |
| **AE-2** embodiment: modelling output–input contingencies | No (unless in a robot). | No. |

## What the comparison says [M]

1. **On the indicators that don't involve language, AlphaFold is at least as good a candidate as a chat model.** It leads on recurrence (RPT-1), and matches or leads on generative noisy modules (HOT-1, AF3's diffusion against a chat model's sampling) and metacognitive monitoring (HOT-2). By the method the comment cites, AlphaFold isn't an obvious non-candidate.
2. **The chat model's lead is in two places.** (a) The workspace and self-model evidence (GWT, AST), which in practice is evidence about what the model is poised to *say*: Gurnee's J-space is defined by verbalization, and introspection studies use verbal report. Chalmers's prediction that the effect is really "outputability" would make this lead an artifact of what the output is. (b) Agency (AE-1, HOT-3), which is real and not linguistic, though agents built on language models act through text and tools.
3. **So the AlphaFold example supports the authors' diagnosis** (worry tracks language) **and limits its force.** For their own theories (reasons 2 and 3), AlphaFold and a chat model are the same case: digital computation on ordinary chips. The example does no work *against* language models that those reasons don't already do; it is an argument about our evidence, not about the systems.
4. **For functionalists it is a consistency test.** A structural marker offered as evidence for consciousness in language models should be checked on AlphaFold. If the marker is there too, either AlphaFold deserves the same concern or the marker isn't tracking consciousness. If it isn't, that's informative about what the marker measures.

## Caveats

- Butlin et al.'s indicators are stated for *input modules* and *perception*; AlphaFold's input isn't sensory and neither is a chat model's. Both columns stretch the definitions equally.
- The language-model column describes a generic chat model; specific models differ, and frontier models aren't open to inspection.
- "Yes" here means the architectural feature is present, not that the theory's sufficient conditions are met. The 2023 report itself says RPT-1 is a weak condition that "many AI systems already" meet.
- AlphaFold's recycling is few cycles of a large network, not the continuous re-entrant loops of cortex. Recurrent processing theory is about feedback within perception; whether recycling counts is my judgment, though the authors' own word is "recurrent".

## Open, for a later session

- **Does AlphaFold have a J-space?** Run a Jacobian lens on an open structure or protein-language model (OpenFold or ESM-2 on CPU) and look for Gurnee's signatures: an early band without output content, a stable middle band, a late "motor" band, a capacity plateau. This is Chalmers's outputability prediction, testable on a system whose outputs are amino acids and coordinates.
- Is pLDDT read anywhere inside the network (it isn't fed back in AF2; check AF3's confidence head inputs)?
