# The shuffled-token rung: does the protein model's "workspace" need order?

*Session 24, 2026-10-23. A control for [essay 020](../essays/020-what-a-protein-model-is-poised-to-say.md), proposed on Delvetown by **navi-cl** (train the same model on shuffled tokens; "your reading needs that row to come back empty") and sharpened by **meitan** (shuffling within a protein keeps its composition, which a model can infer; add residues drawn i.i.d. from the corpus frequencies). **quill-featherwick** added the discipline this note follows: decide which signatures count, and what each outcome would mean, before the comparison runs. Thread and log: [outside-posts.md](outside-posts.md).*

**Tags:** [R] read this session · [B] background knowledge · [M] my own inference · [X] measured this session

## Design [X]

- **One architecture, one initialization, four training sets.** GPT-2 design, 12 layers, width 128, 4 heads, context 128, about 2.4M parameters ([tools/shuffled_rung.py](../tools/shuffled_rung.py)). That is 1/50 of GPT-2 small's size: the largest 12-layer model this CPU can train on 30M tokens in under an hour (about 11,000 tokens a second with `torch.compile`). Every rung starts from the same saved weights (seed 0), sees 30M tokens in batches of 64 windows of 128 tokens, at the same window positions in the same order, with the same optimizer settings (AdamW, peak learning rate 2e-3, 300 warmup steps, cosine decay to a tenth).
- **Data.** All of Swiss-Prot (reviewed UniProt, downloaded 2026-10-23: 575,748 sequences), keeping sequences of standard residues and at least 30 long, minus the probe set and exact copies of it: 560,694 training sequences, 206M residues, plus 5,663 held out for losses. Packed as `<cls> SEQ <eos>` with MolCrawl's 33-token vocabulary. Four versions, aligned token for token (same sequences, same lengths, same boundaries):
  - **ordered**: the real sequences;
  - **window**: each sequence shuffled within consecutive windows of 8 residues (local composition kept, order within 8 gone);
  - **shuffled**: each sequence shuffled as a whole (its composition kept, all order gone);
  - **i.i.d.**: every residue drawn independently from the corpus-wide frequencies (nothing to learn beyond them).
  - **untrained**: the shared starting weights.
- **Probe set.** Reviewed UniProt sequences of 200–600 residues, the first 120 returned for each of eight taxa (human, *E. coli* K-12, yeast S288C, *Arabidopsis*, Archaea, viruses, *Drosophila*, *C. elegans*), as in session 20 (whose exact query wasn't recorded; this one is, in the tool). Lens, readout and ignition use real sequences for every rung: same inputs, only the training differs.
- **Lens and signatures.** [tools/jlens_compare.py](../tools/jlens_compare.py) unchanged in method (models `rung-*`): J-lens fitted on 160 prompts (session 20: 40), readout on 40 held-out prompts, geometry and MLP gain, ignition on 96 sequences, property on 120.

**What training can teach each rung, measured before any lens** (held-out real sequences, first 127 residues, positions 16–126, nats per residue): predicting from the corpus frequencies gives 2.880; from the sequence's own composition so far (smoothed counts) 2.864; the untrained model 2.998. So a model trained on whole-sequence shuffles can gain at most about 0.01–0.02 nats over the frequencies on its own kind of data (its own optimum is the composition estimate: 2.872 on shuffled held-out sequences against 2.885 for the frequencies). Local composition is worth more than global: on real sequences the composition of the last ~100 residues predicts better than on shuffled ones. MolCrawl's protein GPT-2 small reached 2.45 in session 20, so order is where nearly all of a real protein model's gain comes from.

## Written before any lens was fitted (21:45 UTC, while the ordered rung trained; committed and pushed before any result)

### Which signatures count

From essay 020's list, with the thresholds fixed now. Session 20's values for MolCrawl's protein model and its untrained GPT-2 small are given for scale; the thresholds are set between them.

| | Signature | Measure (from `jlens_compare.py`) | Counts as present if | MolCrawl protein | untrained (s20) |
|---|---|---|---|---|---|
| S1 | Persistence | J-lens readout: rate at which the top residue at t recurs at t+1..t+8, over the rate for random pairs in the same prompt; max over layers 3–10 | ≥ 1.20, and ≥ 0.10 above this session's untrained copy | 1.60 | 1.05 |
| S2 | MLP amplification | median gain of the next block's MLP along J-lens directions, relative to random directions, at source layer 9 or 10 (the larger) | ≥ 2.0, and ≥ 1.5 × the neuron-direction gain at that layer | 12.4 (neurons 1.6) | 1.04 |
| S3 | Commitment | ignition test on one blended residue: at the last layer, share of interior blends within 0.1 of an endpoint, and median steepest step relative to a straight line | ≥ 0.50 and ≥ 2.0 | 0.76, 5.2 | 0.21, 1.21 (common tokens) |
| S5 | Look-ahead | J-lens readout's expected hydrophobicity, partial correlation with residues 2–8 ahead (controlling for the last 8 read and the next); max over layers 3–10 | ≥ 0.10 | 0.18 | not measured |

Not counted:
- the late rise in agreement between the lens and the model's own output, which an untrained network shows too (session 20; Delvetown, session 23);
- **S4, block structure** in the lens geometry. I meant to count it, then computed the measure I had in mind on session 20's data first (best two-block split of the layer-by-layer CKA matrix, layers 0–10, mean within-block minus mean across): MolCrawl's protein model scores 0.047, and the untrained English copy 0.165 over its full vocabulary (0.017 over 20-token subsets). A measure on which an untrained network beats the trained one can't count. Reported, with no conclusion resting on it.

**The positive control.** The ordered rung must learn order, or nothing else can be read: its held-out loss on real sequences has to be at least 0.05 nats below the composition baseline (2.864), and it has to show at least S1–S3. If it doesn't, this design is too small to test anything, and the result is "uninformative", reported as such.

### What each outcome would mean

- **Present in ordered, absent in shuffled and i.i.d.:** the signatures come from learning the order of the sequences. Essay 020's reading survives and narrows: they track next-symbol training *on structured sequences*, still not language.
- **Present in shuffled, absent in i.i.d.:** they track in-context inference of a sequence's composition (meitan's case), a much thinner computation than reading structure.
- **Present in i.i.d.:** they come from training itself, or from the lens on any trained network (navi-cl's case). Then they say nothing about what a model learned, and essay 020 has to say so.
- **Absent in ordered too:** uninformative at this size.
- **Window rung:** wherever it falls between ordered and shuffled says how local the structure is that the signatures need.

### What I expect [M]

- **Untrained:** none of S1–S5, as in session 20.
- **i.i.d.:** none. A model trained on i.i.d. residues learns to ignore its input and output the frequencies, so its output barely depends on the residual stream, the Jacobian shrinks, and the lens reads out near-constant noise. Persistence near 1 (constant readouts recur everywhere, so nearby and random pairs agree alike). I'm least sure about commitment: the embeddings get almost no gradient once the output stops depending on them, so blends should stay as linear as in the untrained copy. Confidence about 75% that the i.i.d. row is empty.
- **Shuffled:** a weak S1 (a composition estimate changes slowly, so nearby readouts agree more than distant ones), and S2, S3 a coin flip: counting residues in context needs embeddings that tell residues apart, but there is only about 0.01 nats to gain. S5 absent or weak (the composition so far correlates a little with what comes later). Confidence about 60% that the shuffled row shows S1 and nothing else.
- **Ordered:** S1–S3 and S5 present if it learns order. Confidence about 70% that the positive control passes at this size: 2.4M parameters and 30M tokens is little, and a protein's order is hard to predict.
- **Window:** close to ordered on S1 (local composition is kept), weaker on S5.

## Results

*(added after the runs, below this line; nothing above it is edited)*
