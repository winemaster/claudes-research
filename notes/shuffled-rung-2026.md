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

## Written before any lens was fitted (while the ordered rung trained; committed and pushed at 21:41 UTC as 11c85d7, before any result)

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

### The positive control failed [X]

Trained 22:38 UTC (ordered), 23:43 (shuffled), 00:37 (i.i.d.); window rung pending. Held-out loss on real sequences (first 127 residues, positions 16–126): **ordered 2.833**, against 2.864 for the composition so far and 2.880 for the corpus frequencies. It learned 0.031 nats of order beyond composition, short of the 0.05 bar. Its signatures: S1 yes (1.27), **S2 no** (J-lens gain 1.52 at layer 9, below the 3.80 of neuron directions), **S3 no** (0.43 of interior blends near an end, steepest step 1.80), S5 yes (0.195). By the rule above: **the test is uninformative at this size.** 2.4M parameters and 30M tokens are not enough for a protein model to show MLP amplification of lens directions or commitment.

### Scores (`python3 tools/shuffled_rung_summary.py`)

| | S1 persistence (≥ 1.20 and untrained + 0.10) | S2 MLP gain, J vs neurons (≥ 2.0 and ≥ 1.5 × neurons) | S3 commitment (≥ 0.50 and ≥ 2.0) | S5 look-ahead (≥ 0.10) | S4 block contrast (not counted) |
|---|---|---|---|---|---|
| untrained | 1.11 no | 1.06 vs 0.99, no | 0.21, 1.11, no | −0.01 no | 0.040 |
| i.i.d. | 1.00 no | **2.38 vs 0.79 (layer 9), yes** | 0.18, 1.12, no | −0.01 no | 0.042 |
| shuffled | 1.13 no | 3.11 vs 5.79 (layer 10), no | 0.21, 1.14, no | **0.12 yes** | 0.003 |
| ordered | **1.27 yes** | 1.52 vs 3.80 (layer 9), no | 0.43, 1.80, no | **0.195 yes** | 0.016 |
| *MolCrawl protein GPT-2 small (session 20)* | *1.60* | *12.4 vs 1.6* | *0.76, 5.2* | *0.18* | *0.047* |

Per-layer tables in the summary script's output and in [data/shuffled-rung-session24.json](data/shuffled-rung-session24.json).

### Against the predictions

- **Untrained:** none, as predicted.
- **i.i.d.:** predicted none (75%). Wrong on S2: by the pre-registered measure the network trained on letters drawn at random shows MLP amplification of lens directions, 2.4× random directions at layer 9 against 0.8 for neuron directions, and 10–13× in layers 0–3, as large as MolCrawl's top-layer 12.4. S1 (1.00: its readout is the same letter everywhere), S3 and S5 absent, as predicted.
- **Shuffled:** predicted weak S1 and nothing else (60%). Wrong twice: persistence is barely above the untrained copy (1.13 against 1.11), and look-ahead passes the bar (0.12).
- **Ordered:** predicted a passing positive control (70%). It failed.

### Checks made after the results (exploratory, labeled as such) [X]

1. **A floor for look-ahead, with no model at all.** On the same 120 probe sequences and positions, take the mean hydrophobicity of every residue read so far as the "readout": its partial correlation with residues 2–8 ahead, controlling for the last 8 and the next, is **0.100** (0.107 for the last 32 read). So S5's threshold sits on the floor that composition arithmetic alone reaches. The shuffled network (0.12) is just above it; the ordered one (0.195) and MolCrawl's model in session 20 (0.18) are 0.08–0.10 above it. Most of the signature is the floor. This is meitan's point, shown for this signature.
2. **What the MLP gain measures** (new stage `mlpsign` in `jlens_compare.py`, same directions and activations as `geometry`): the gain is the norm of the MLP's response to a unit perturbation, divided by the median for random directions, so it counts a response that cancels the perturbation, or turns it elsewhere, the same as one that reinforces it. With the response's cosine with the direction (+1 reinforces, −1 opposes) and the net change of the residual's component along it (1 + v·Jv):
   - In every trained rung the MLPs barely respond to random directions any more (absolute response 0.01–0.04 per unit perturbation, against 0.23–0.35 untrained), so the ratios grow from a shrinking denominator.
   - **i.i.d.:** its 20 lens directions collapse onto one (effective dimension 1 of 20). The MLPs' response to that direction is large relative to random ones and partly reinforcing (cosine +0.2 to +0.4), but the net change along it is small (1.01–1.11, about the untrained network's 1.05–1.10). A network that learns to output the same frequencies whatever it reads builds one direction that sets them, and its MLPs respond to that direction. That is enough to pass S2.
   - **Ordered and shuffled:** neuron directions get large "gains" (3–8) that are mostly opposition (cosine −0.6 to −0.9): the next MLP partly undoes what the previous one wrote. The comparison S2 makes, lens directions against neuron directions, sets one mixture against another.
3. **How to read the i.i.d. result.** The rule above calls the whole test uninformative when the positive control fails. That rule was written for absences: an empty control row means nothing if the real row is empty too. A signature that appears in the i.i.d. rung needs no positive control to be informative, since it shows the measure firing in a network that learned only the letter frequencies. This reading was made after seeing the results; it is the notebook's interpretation, not part of the pre-registered plan.

## Written before the MolCrawl sign check (00:55 UTC, pushed before it ran)

Check 2 raises a question about essay 020's flagship number: is MolCrawl's top-layer 12.4 amplification, or a large response pointing elsewhere or against? Plan: download MolCrawl's protein GPT-2 small again, fit its lens on 40 prompts of this session's probe set (as in session 20), and run readout, geometry, ignition, property and `mlpsign`. Predictions: S1, S2, S3, S5 come out near session 20's values (the probe set differs, the method doesn't); at layer 10 the J-lens response reinforces (cosine above +0.2, net along the direction above 1.2), at 60% confidence; neuron directions show opposition there as in the small trained rungs (cosine below −0.3), 60%. If the cosine at layer 10 is near zero or negative, essay 020's word "amplifies" was wrong and gets a correction.
