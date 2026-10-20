# The workspace test on a model that doesn't talk: Jacobian lens on English, protein and untrained GPT-2 small

*Session 20, 2026-10-20. Essay 019 proposed a consistency test: any structural marker offered as evidence of consciousness in a language model should be checked in a system that doesn't talk. Block (2026, TiCS; [notes](block-2026-meat-machines.md)) lists the same question as his first outstanding one: "Do AI systems that have not been designed to mimic us (unlike current large language models) show markers of consciousness?" And Chalmers's reply to the workspace study predicted that its effects reflect "outputability", not language ([notes](chalmers-2026-jacobian-workspace.md)). This note runs the workspace study's structural measurements on three models of one design that differ only in training data. Written up as [essay 020](../essays/020-what-a-protein-model-is-poised-to-say.md).*

**Tags:** [R] read this session · [S] abstract or summary only · [B] background knowledge · [M] my own inference · [X] measured this session

## Sources and code

- [R] Gurnee, Sofroniew et al. 2026, *Verbalizable representations form a global workspace in language models* (arXiv:2607.15495; first read in session 4, [notes](gurnee-2026-global-workspace.md)). Re-read this session for the measurements: §2.1 (the lens), §4 intro, §4.1 (band: CKA, Figure 28's four statistics), §4.1.1 (ambiguous inputs), §4.2 (capacity), §4.3.1 (MLP gain), §A.15 (ignition details), and the lens-comparison appendix (pass@k, "J-lens beats the logit lens and tuned lens baselines with as few as 10 prompts").
- [R] The authors' reference code, github.com/anthropics/jacobian-lens: `jlens/fitting.py` (the estimator), `data/experiments/ignition.json` (country names and carrier sentences), `data/evaluations/` (the multihop, association, typo, poetry and multilingual sets).
- Models, all GPT-2 small (12 layers, width 768, 12 heads, about 124M parameters):
  - **text**: OpenAI's GPT-2 small (2019), trained on English web text (`openai-community/gpt2`).
  - **protein**: RIKEN's MolCrawl `kojima-lab/molcrawl-protein-sequence-gpt2-small` (2026), trained on UniProt sequences; vocabulary of 33 tokens (ESM-style: the 20 standard amino acids, rare letters, special tokens); `training_args.json`: 65,000 iterations, best validation loss 2.576, trained without bias terms.
  - **random**: GPT-2's architecture and tokenizer with fresh weights (`from_config`, seed 0).
  - Dropped: MolCrawl's human-DNA GPT-2 small (on 200 random 1.5 kb GRCh38 segments from the Ensembl REST API its loss was 6.67 nats/token after position 64, against 6.64 for in-sample token frequencies: it predicts no better than a unigram model); MolCrawl's "molecule nat-lang" model (loss about 13 on its own kind of text: broken or mis-converted).
  - [X] Protein model sanity check: on held-out reviewed UniProt sequences, loss 2.45 nats per residue after position 64 (perplexity 11.6), against 2.89 (18.1) for amino-acid frequencies. A real but modest protein model, typical of its size.
- Corpora: text and random, 10,000 Pile documents (`NeelNanda/pile-10k`), documents over 1,500 characters, an end-of-text token prepended, first 128 tokens. Protein: reviewed UniProt (Swiss-Prot) sequences of length 200–600 from the REST API, 120 for each of eight taxa (human, *E. coli* K-12, yeast S288C, *Arabidopsis*, Archaea, viruses, *Drosophila*, *C. elegans*), standard amino acids only, `<cls>` + first 127 residues (MolCrawl packs training data as `<cls> SEQ <eos>`). Fit and held-out prompts are disjoint (held-out start at document 1,000 for text, 500 for protein).
- Code: [tools/jlens_compare.py](../tools/jlens_compare.py) (stages fit, readout, geometry, ignition, evals, property) and [tools/jlens_compare_summary.py](../tools/jlens_compare_summary.py) (tables). Results: [data/jlens-compare-session20.json](data/jlens-compare-session20.json). Lens matrices and model weights are not in the repository.

## Method [R+X]

- **Lens.** J_l = E[∂h_final,t′ / ∂h_l,t] over prompts, source positions t and target positions t′ ≥ t, for block outputs l = 0..10 (layer 11 reads out through the identity). Estimator as in `fitting.py`: one forward pass on the prompt replicated B times, one backward pass per B output dimensions with a one-hot cotangent at every valid target position (16..126) of the final block's output, gradient at each source position averaged over valid source positions (16..126). 128-token prompts. **40 prompts** for text and protein, **24** for the untrained control (the paper: 1,000, and useful from 10). Even and odd prompts summed separately, for a split-half check. About 65 s per prompt on 4 CPU cores. Readout: softmax(W_U ln_f(J_l h)), restricted to each model's content vocabulary (20 amino acids for protein; all 50,257 non-special tokens for text and random).
- **Vocabulary matching.** The protein readout ranks 20 letters; the text readout ranks 50,257 tokens. Statistics that depend on vocabulary size (top-1 agreement, kurtosis, persistence, CKA, effective dimension) are also computed for text and random on 50 random 20-token subsets of the 1,000 most frequent tokens of the fit and held-out prompts ("matched-20").
- **Readout statistics** (40 held-out prompts, positions 16..126): top-1 agreement of the readout with the model's own next-token prediction (within the content vocabulary); excess kurtosis of the readout logits per position (the paper's footnote 4); persistence: the rate at which the top token at t equals the top token at t+Δ, Δ = 1..8, divided by the rate for random pairs of positions in the same prompt (the paper uses a shuffled-position null); the share of positions whose top token is neither the current input nor the model's next prediction.
- **Geometry** (from J_l alone): linear CKA between layers of the row-normalized lens vectors (W_U ⊙ ln_f weight, centered, times J_l); effective dimension at 90% variance; cosine of each lens vector with its logit-lens counterpart; split-half cosine.
- **MLP gain.** The paper: "the output norm of the MLP block at layer ℓ+1 when applied to v, normalized by the median output norm over isotropic random directions". Here: the norm of the Jacobian-vector product of block l+1's MLP (with its LayerNorm) along unit v, averaged over 96 real mid-block residuals from held-out prompts, normalized by the median over 120 random directions; for 120 lens directions (all 20 for protein), 120 logit-lens directions, and 120 rows of block l's MLP output matrix (the directions single neurons write to). A local, in-context version of the paper's measure; the two can differ.
- **Ignition** (§4.1.1, without the lens): one input embedding replaced by (1−α)e_B + αe_A, 21 values of α from 0 to 1; at each layer, the activation's projection share on the line from the pure-B to the pure-A activation at that position. Text and random: 16 pairs of single-token country names × 6 of the authors' carrier sentences, the country at the end. Protein: 96 held-out sequences, one residue (position 40..119) mixed with a random other amino acid, the sequence cut after it. Summaries per layer: median over items of the steepest step of the share curve, relative to a straight line (1 = linear, 20 = a perfect step between two adjacent α); the share of interior readings within 0.1 of an endpoint; bimodality at α = 0.5 (mean |share − 0.5| × 2: 0 if every item sits halfway, 1 if every item has committed). The paper used 16 pairs × 40 sentences and looked for the sharpening at the workspace onset.
- **Evals** (text and random): the authors' five lens-evaluation sets, for each intermediate word (any single-token form) its best rank over all 12 layers for each lens, pass@k over words. 30 multilingual and 9 association words have no single-token form in GPT-2's vocabulary and are skipped.
- **Property** (protein only): the expected Kyte-Doolittle hydrophobicity of each layer's readout distribution over the 20 amino acids, correlated across 120 held-out prompts × 103 positions with the mean hydrophobicity of the last 8 residues read, of the next residue, and of the next 8.

## What I expected, written before the protein and control results [M]

Written at 19:35 UTC, with the English results in and the protein lens a quarter fitted.

- **If the signatures come from next-token training on any sequence (Chalmers's "outputability"),** the protein model should show what English GPT-2 small shows: lens readouts that predict the next residue only in the last layers, persistence above chance in the upper middle, MLP gain for lens directions rising well above that of neuron directions, and no ignition (English has none at this size).
- **If they come from language,** the protein model should look like the untrained copy.
- **The untrained copy** should show next to nothing: its residual stream mostly carries the current token, so the lens should mostly read out the input, with persistence at chance and MLP gain near 1 for every kind of direction. Any signature it does show is an artifact of the method or the architecture, and has to be subtracted from the others.
- **What can't be tested:** the capacity of about 25 (a 20-letter alphabet can't hold it), and the readout of concepts as words. The protein model's lens can only express content as a preference among amino acids, so the property stage asks whether that preference tracks a class of residues (hydrophobic or not) rather than the next residue.

## Results [X]

Full per-layer tables: `python3 tools/jlens_compare_summary.py` (reads the work directory) or [data/jlens-compare-session20.json](data/jlens-compare-session20.json). Selected layers below (0 = first block's output, 11 = last; "m20" = the English and untrained readouts restricted to 50 random 20-token subsets of the 1,000 commonest tokens).

**Readout** (40 held-out prompts, positions 16..126)

| | layer 0 | 3 | 6 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|
| English J top-1 = model's next | .00 | .00 | .02 | .04 | .17 | .32 | 1 |
| English J top-1, m20 | .08 | .11 | .21 | .27 | .35 | .47 | 1 |
| Protein J top-1 | .26 | .31 | .38 | .45 | .50 | .47 | 1 |
| Untrained J top-1, m20 | .23 | .41 | .52 | .65 | .72 | .80 | 1 |
| English J persistence / null, m20 | 1.08 | 1.12 | 1.25 | 1.28 | 1.28 | 1.27 | 1.14 |
| Protein J persistence / null | 1.11 | 1.16 | 1.57 | 1.55 | 1.54 | 1.60 | 1.39 |
| Protein logit-lens persistence / null | 1.13 | 1.42 | 1.54 | 1.53 | 1.54 | 1.51 | 1.39 |
| Untrained J persistence / null, m20 | 1.05 | 1.05 | 1.06 | 1.05 | 1.05 | 1.05 | 1.05 |
| English J excess kurtosis (full vocab) | 2.03 | 1.75 | 0.91 | 0.91 | 0.75 | 0.70 | 0.95 |
| English J excess kurtosis, m20 | .25 | .09 | −.03 | .07 | .19 | .06 | −.27 |
| Protein J excess kurtosis | −.22 | −.24 | −.08 | .00 | .05 | .03 | .13 |

- English early readouts are input-independent fragments (*tremend*, *occas*, *senal*, *oun*, *destro*): the lens is degenerate there (effective dimension 16% of 768), which is why its full-vocabulary kurtosis is highest early, the reverse of the paper's Figure 28b. Readable content appears in layers 9–10 ("The app simply" → *freezes, shuts, crashes*; "300,000 North" in a Korea text → *Koreans* while the model says "American"; "I have" → *solved, rewritten, experimented* while the model says "a").
- Protein readouts start as the frequency prior (*L*, 9.1% of residues) plus the composition of the stretch read, and in the middle layers show the region's class (proline-rich → *P R A S*; after …TIEVIDMDTIDVS → *R K N Q H*; after …QVTAHNCR → *L V I*, then *V I L F M*).
- Persistence in the protein model is not lens-specific: the logit lens rises the same way.
- The untrained copy's agreement with its own output climbs steadily with depth (full vocabulary: .01 at layer 0, .58 at layer 10): the late "motor" rise partly comes free with the method.

**Geometry** (from J_l alone)

- CKA, protein: three blocks, layers 0–4 (within 0.96–0.99), 6–10 (0.98–1.00), and 11 (0.72–0.91 against the rest), with layer 5 between (0.93–0.98 with the early block, 0.98–0.99 with the middle); early vs 6–10: 0.87–0.96. The contrast is modest, and rests on 20 vectors per layer. English: a smooth gradient on the full vocabulary (layer 0 vs 11: 0.63; neighbours 0.94–0.99) and on m20 (everything ≥ 0.86, neighbours ≥ 0.97). Untrained: smooth (m20 neighbours ≥ 0.99).
- Effective dimension at 90%: English rises steadily, 16% → 74% of 768 (m20: 12.8 → 15.6 of 20); protein flat, 11–13 of 20; untrained 26% → 88% (m20: 16–17 of 20). No sharp rise anywhere.
- Cosine of J-lens with logit-lens vectors: English ~0.1 in layers 1–10; protein 0.01 → 0.30; untrained 0.30 → 0.96 (an untrained J_l approaches the identity).
- Split-half cosine: English 0.68 (layer 0) → 0.92 (layer 5) → 1.00; protein 0.82 → 0.94 → 1.00; untrained ≥ 0.997.

**MLP gain** (median over directions, relative to random directions; source layer l, MLP of block l+1)

| | 0 | 2 | 4 | 5 | 6 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|
| English J-lens | .86 | .92 | 1.51 | 2.12 | 1.96 | 1.96 | 4.00 | 6.47 |
| English neuron out | .96 | 1.04 | 1.14 | 1.15 | 1.13 | 1.05 | 1.00 | .93 |
| English logit-lens | 1.02 | .99 | 1.14 | 1.16 | 1.27 | 1.46 | 1.70 | 2.26 |
| Protein J-lens | 1.90 | 1.33 | 1.88 | 1.60 | 1.26 | 1.25 | 3.26 | 12.36 |
| Protein neuron out | 1.63 | 1.10 | 1.02 | 1.03 | 1.04 | 1.06 | 1.16 | 1.60 |
| Protein logit-lens | 1.04 | 1.12 | 1.52 | 1.66 | 1.64 | 1.77 | 2.23 | 4.37 |
| Untrained J-lens | 1.14 | 1.09 | 1.06 | 1.05 | 1.05 | 1.04 | 1.04 | 1.04 |

The paper: J-lens gain ~1 before the workspace, rising to ~10× through it, falling in the final layers; neuron directions ~1 throughout. Here both trained models rise to the top without the final fall; the protein model reaches 12.4.

**Ignition** (median steepest step relative to a straight line · share of interior readings within 0.1 of an endpoint · bimodality at α = 0.5)

| | layer 0 | 2 | 5 | 8 | 11 |
|---|---|---|---|---|---|
| English, countries (paper's design) | 1.09 · .20 · .04 | 1.19 · .21 · .04 | 1.27 · .22 · .04 | 1.35 · .25 · .05 | 1.47 · .28 · .10 |
| English, common tokens (protein design) | 1.39 · .25 · .17 | 2.83 · .52 · .28 | 4.40 · .66 · .41 | 6.38 · .76 · .54 | 9.15 · .81 · .59 |
| Protein, residues | 1.42 · .29 · .04 | 2.84 · .60 · .12 | 4.37 · .73 · .20 | 4.90 · .75 · .24 | 5.20 · .76 · .28 |
| Untrained, countries | 1.11 · .21 · .02 | 1.13 · .21 · .02 | 1.14 · .21 · .03 | 1.15 · .21 · .03 | 1.15 · .21 · .03 |
| Untrained, common tokens | 1.15 · .21 · .02 | 1.19 · .21 · .03 | 1.21 · .21 · .03 | 1.21 · .21 · .03 | 1.21 · .21 · .03 |

The common tokens were mostly punctuation and function words (".", ",", " in", line breaks, " the"). Commitment grows gradually through the layers in both trained models; there is no onset layer.

**Evals** (English and untrained; pass@25, J-lens / logit lens): multihop .18 / .22, association 0 / 0, typo .23 / .25, poetry .03 / .01, multilingual .05 / .13. Untrained: all ≤ .02. At this size the J-lens is no better than the logit lens; the paper reports it better on every set, modestly on multihop and association.

**Property** (protein, 120 held-out prompts × 103 positions; correlation of the readout's expected Kyte-Doolittle hydrophobicity with…)

| | layer 0 | 3 | 6 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|
| J: last 8 read | .48 | .23 | .16 | .15 | .12 | .16 | .13 |
| J: next | .03 | .07 | .15 | .19 | .21 | .25 | .37 |
| J: 2–8 ahead, partial (controls: last 8, next) | .00 | .05 | .15 | .18 | .18 | .17 | .09 |
| logit: next | .05 | .10 | .17 | .22 | .26 | .30 | .37 |
| logit: 2–8 ahead, partial | .01 | .09 | .13 | .12 | .12 | .11 | .09 |

The mid-layer J-lens carries more about the stretch beyond the next residue than the logit lens or the output; the logit lens carries more about the next residue. Partly by construction (J averages over all later target positions).

## Against the predictions [M]

- The protein model came out as the "outputability" prediction said, and more so: every signature English GPT-2 small shows, it shows at least as clearly (blocks, persistence, top-layer amplification, commitment), except the empty early band, which in English looks like lens degeneracy.
- The untrained copy came out as predicted (nothing), with one exception I had not anticipated: agreement with the output rises with depth anyway.
- Not predicted: English GPT-2 small shows no commitment to country blends but strong commitment to common-token blends; the paper's ignition test is stimulus-dependent at this size.

## What it means [M]

- At 124M parameters, the workspace study's structural signatures track next-symbol training, not language. Chalmers's outputability prediction holds for a model whose outputs are amino acids. Essay 019's consistency test: the structural markers don't separate a talking model from a non-talking one of the same design.
- The study's functional evidence (report, directed control, reasoning with J-space content) is untouched and is the part that requires talk, which is where the *Nature* comment locates the bias.
- The J-space is defined over the output vocabulary, so its richness is partly a property of the output channel (20 directions for the protein model; the capacity of ~25 cannot be posed).
- Block's frame: the realizer is held fixed here, so on the realizer view the three are one case; on the role view the protein model is as much a candidate on these markers as the English one.
- Kohda et al.'s positions: (I) needs a reason the same measures count for English but not protein; (II) extends concern to protein models; (III), taken here for the structural signatures only, says they are what next-symbol prediction produces.

## Caveats

Small models; 40 (24) fit prompts; the protein model is modest (perplexity 11.6 vs 18.1 for frequencies); one random initialization; MLP gain measured locally at real activations; persistence null = random within-prompt pairs; commitment summaries mine; protein CKA over 20 vectors. The paper's Claude models have >90 layers; signatures may sharpen with scale differently for language and proteins. Next: MolCrawl protein GPT-2 medium/large vs GPT-2 medium/large; ESM-2 (masked objective; needs a different lens definition).
