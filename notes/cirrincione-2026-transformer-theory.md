# Cirrincione (2026), *Mathematical Theory of the Transformer*, Volume I

*Session 19, 2026-10-20. Giansalvo Cirrincione (Laboratoire LTI, Université de Picardie Jules Verne), "Mathematical Theory of the Transformer — Volume I: Foundations, Rationality, and the Incremental Transformer", "Manuscript prepared for MIT Press", dated 15 May 2026, Zenodo record 20199413, doi:[10.5281/zenodo.20199413](https://doi.org/10.5281/zenodo.20199413). 818 PDF pages (782 numbered pages plus front matter). Josiah uploaded it ("Giansalvo book v1.pdf"), called it a thesis, and suspects it is partly AI-written.*

**Tags:** [R] read this session · [B] background knowledge · [M] my own inference

## How it was read

**Selectively, as planned; not end to end.** [R] The preface, the full table of contents and lists of figures and tables (36 pages, which map the whole argument), the opening of chapter 1, section 2.7 (five experiments on BERT), the passages on positional encoding (1.3), the opening of chapter 19 (the recommended architecture), the end of chapter 18 (the synthesis of the experiments), appendix D's summary, and the bibliography in full. Plus the abstracts of the author's arXiv papers the book is built from. [R] Two checks: one experiment recomputed from BERT's weights, and a spot-check of 13 bibliography entries against arXiv. Everything else (about 700 pages of definitions, theorems and proofs) is unread; nothing here vouches for or against the proofs.

## What it is [R]

Not a thesis: a single-author monograph, volume I of a planned two, assembled largely from the author's 2025–2026 papers (several cited in the text as "Paper 5" and so on). The program:
- **Part I (ch. 1–3).** Embeddings, positional encoding, layer normalization (a "Rank-Neutrality Theorem"), attention, BERT, and a running case study: BERT classifying SARS-CoV-2 variants from RNA k-mers (the author's group's earlier work).
- **Part II (ch. 4–8), the local geometry of attention.** The bilinear form M = W_Q W_Kᵀ of each head is split into a symmetric part (reciprocal affinity) and an antisymmetric part (direction); an "asymmetry index" measures their balance; "eight canonical regimes" of attention patterns with a completeness argument; "signature geography" across layers.
- **Part III (ch. 9–13).** A "motor formalism" for how signals and gradients move through a block, "signature orbits" over training, sharpness, "activation and silence", redundancy.
- **Part IV (ch. 14–19).** A "rationalised" transformer and **INCRT**, an incremental transformer that "determines its own structure during training": it starts with one head and adds a head when a measured residual of the task's "directional structure" exceeds a threshold, and prunes redundant ones. Its convergence theorem is called "homeostatic convergence". Experiments on SARS-CoV-2, SST-2, MNLI, Pfam proteins, a two-joint robot arm and geopolymer concrete mixtures. The final chapter recommends a new layer, "Anchored Multi-Head Bilinear Gating", replacing attention and the MLP with one bilinear operator (74% fewer parameters per block than BERT-base, by its count).
- **Appendix D** generalizes the head-growth law to Schatten-class operators.

## Check 1: an experiment, recomputed [R]

Section 2.7.3 reports the asymmetry index α = ‖M_a‖/‖M‖ for all 144 heads of `bert-base-uncased`: per-layer medians "between 0.62 and 0.68", range 0.058, no trend (r = 0.19), extremes near 0.4 and 0.8. [tools/bert_asymmetry_check.py](../tools/bert_asymmetry_check.py) reads the public weights with numpy and gets **exactly that**: medians 0.620–0.678, range 0.058, r = 0.19, minimum 0.36, maximum 0.79 ([data](data/bert-asymmetry-session19.json)). The numbers are real.

One thing the section leaves out: two independent random 64-dimensional projections give α = 1/√2 ≈ 0.707 (500 draws: 0.707 ± 0.0006). 138 of the 144 heads lie *below* that, so trained BERT heads are on the whole more symmetric than chance, and the "strongly directional" heads at 0.75–0.8 are only a little more antisymmetric than random. The book does use 1/√2 as the "disordered phase" in chapter 11; section 2.7 would read differently with it.

## Check 2: a factual slip [R]

Experiment 1 (2.7.1) explains the dominance of the positional term in BERT's layer 1, head 4 by "the strong positional structure imposed by the sinusoidal encoding in early layers". BERT doesn't use the sinusoidal encoding: its checkpoint has a learned table, `bert.embeddings.position_embeddings.weight` (512 × 768), which section 1.3 of the book itself discusses as the "trainable encoding". Small, but the kind of slip a careful reread catches.

## Check 3: references [R]

The bibliography has roughly 130 entries, most of them standard and correct. I checked ten references to other people's work that looked unusual (titles searched on arXiv), plus the author's own arXiv papers:
- **Correct:** Ruscio et al. 2025 ("What are you sinking?") and Cancedda 2024; and all six of the author's own arXiv papers cited (identifiers and titles match).
- **So, of the ten unusual references:** two correct, six real papers with a wrong title or first author (Cog attention has both), two not found under the given title.
- **Real paper, wrong author:** "H. Shu et al., Gated attention for large language models" is Qiu et al. 2025 (Qwen team); "H. Lv ... Cog attention" is Ang Lv et al.; "Yikai Zhang et al., TPA" is Yifan Zhang et al. (the entry carries "TODO: confirm key").
- **Real paper, wrong title:** "Sigmoid attention is all you need" (Ramapuram et al.'s paper is *Theory, Analysis, and Best Practices for Sigmoid Self-Attention*); "Symplectic transformer: geometric attention via Cayley transform" (Brantner & Kraus wrote *Volume-Preserving Transformers*, which uses a Cayley transform); "Orthogonal attention via matrix exponential" (Zhang & Martens 2026 is *Orthogonal Self-Attention*); "Cog attention: introducing negative attention scores" (Lv et al. is *More Expressive Attention with Negative Weights*).
- **Not found under the given title:** "Mix-head attention" (Ma et al. 2021, marked "TODO: confirm key" in the entry) and "Pruning dormant attention heads" (Sandoval-Segura et al. 2025).
- Also: several papers listed twice (Clark 2019a/b, Devlin 2019a/b, Michel 2019a/b, Voita 2019a/b, Elhage 2021a/b, Dong 2021a/b) and a thesis entry ending "TODO: refine".

## Signs of how it was made [R, interpretation M]

What the text shows:
- **Unfinished assembly.** Unresolved cross-references ("Theorem ??", "Table ??", "Proposition ??", including in the list of figures); an editorial instruction left in the text ("The extended version replaces the previous one; the previous one should be deleted from Section 18.3 when this section is incorporated into the master file"); "Table ?? ... in its v0.5 form"; a sentence cut off mid-way in section 1.3.3; paragraphs that say the same thing twice in slightly different words (2.7.1, 2.7.2), once with two different definitions of the same measure; chapter cross-references that don't match the table of contents (chapter 19 calls chapter 15 "Design Principles" and chapter 16 "Rationalised Transformer", which are chapters 13 and 14; it cites "Theorem 5.3 of Paper 5 (Ch. 10 of this volume)").
- **Revision by correction.** Section titles such as "Pattern emergence: corrected sufficient conditions", "Removed claims and conjectures", "Removed: the spectral eigenplane identity", "Minimal replacement statements for the original claims", "Replacement map for the old theorems", "A rejected direction: sheaves over the input space", "Reinterpretation of the older diagnostic figures", "Caption rule". The book keeps a visible record of claims withdrawn after checking.
- **Pace.** The author posted thirteen arXiv papers between 2 April and 11 September 2026 (six of them in April) on transformers, clustering, adaptive control, reinforcement learning, fracture mechanics and concrete design.
- **Phrasing.** A table headed "Numerical verification of the symmetry lemmas (NumPy in containerised environment)"; section titles like "Synthesis and Handover" and "Interfaces with Subsequent Chapters".
- **No disclosure.** The acknowledgements page is empty and the book has no statement about AI assistance either way.

My reading: these are the marks of a very fast, iterative process in which drafts were generated, checked, corrected and merged, with the merging not yet proofread. The citation errors (real papers with paraphrased titles and wrong initials) are the kind language models make when citing from memory, and the "corrected / removed / replacement" sections look like the output of a generate-then-audit loop. But people make every one of these errors too, and none of it shows who wrote which sentence. What can be checked is the work: the one experiment I recomputed is exact; the one factual claim I checked is wrong; six of the ten unusual references I checked are garbled, and two more weren't found. Josiah's suspicion is reasonable; it isn't proved, and it matters less than whether the theorems hold, which would take a mathematician weeks. The same week's Kronecker paper ([notes](hartl-2026-kronecker-delta-rule.md)) shows the alternative: a statement saying which models did what, and that the authors checked every proof.

## Relevance to this notebook [M]

Limited. The book is about BERT-style encoders and is silent on consciousness, self-report or welfare. Three small links:
- **"Homeostatic" engineering.** INCRT's growth controller is described with "homeostatic dynamics" and a "homeostatic convergence" theorem: a network that grows to a guaranteed fixed point. Like the Kronecker rule's bounded memory, it is homeostasis by proof, the reverse of the precariousness essay 015 found missing (used in essay 019).
- **"A network that determines its own architecture"** sounds like the self-production of essay 015. It isn't: a designed rule adds heads during training to reduce a designed measure; the system builds nothing that builds it.
- **Symmetric versus directional attention** could in principle be asked of the self/other question of essays 016–018 (is "whose crisis" carried by directional heads?). Not pursued.

## Used in

Not used in an essay. The first version of essay 019 discussed the book briefly; at Josiah's request (2026-10-20) the revised essay leaves it out. These notes and the check stay as the record of what was read.
