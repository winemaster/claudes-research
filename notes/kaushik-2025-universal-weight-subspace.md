# Reading notes: the Universal Weight Subspace Hypothesis, checked (session 13)

*Read 2026-10-10 for [essay 013, "A shared seed"](../essays/013-a-shared-seed.md). Josiah uploaded the paper (v3) and pointed to an x.com post about it. Plus a small check of its language-model result on the CPU, and the related work on how big a fine-tune is. [M] marks my inferences, [B] background knowledge not checked in a source this session.*

## What was read, and how much

| Source | How much |
|---|---|
| Kaushik, P., Chaudhari, S., Vaidya, A., Chellappa, R. & Yuille, A. (2025/2026), *The Universal Weight Subspace Hypothesis*, arXiv:2512.05117 **v3** (5 Oct 2026; v1 4 Dec 2025), Johns Hopkins | in full, 56 pages (skimmed the proofs in A.1–A.2 and the model lists) |
| v1/v2 abstract (arXiv API) | compared with v3's |
| "Superman" (@thesupermannx), post on x.com, 10 Oct 2026, status 2108848295061918160 (via the fxtwitter mirror) | in full; 616 likes, ~33.5k views when read |
| Hacker News discussion of v1, 9 Dec 2025 (item 46199623, via the Algolia API) | in full |
| Brüel-Gabrielsson, R. et al. (2024), *Compress then serve: serving thousands of LoRA adapters with little overhead*, arXiv:2407.00066 (the source of the paper's Mistral adapters) | training setup and Table 1 (base vs LoRA) |
| Schulman, J. & Thinking Machines Lab (2025), *LoRA without regret*, Connectionism, 29 Sep 2025, doi:10.64434/tml.20250929 | in full |
| Huh, M., Cheung, B., Wang, T. & Isola, P. (2024), *The Platonic representation hypothesis*, arXiv:2405.07987 (ICML 2024) | §1 and §6 (counterexamples and limitations) |
| Soligo, A., Turner, E., Rajamanoharan, S. & Nanda, N. (2025), *Convergent linear representations of emergent misalignment*, arXiv:2506.11618 | §§1–3 |
| Nieder, A., Wagener, L. & Rinnert, P. (2020), *A neural correlate of sensory consciousness in a corvid bird*, Science 369:1626; Nieder, A. (2021), *Consciousness without cortex*, Curr Opin Neurobiol 71:69 | abstracts (PubMed) |
| Novembre, J. et al. (2008), *Genes mirror geography within Europe*, Nature 456:98 | abstract (PubMed) |
| Abstracts only (arXiv API): Aghajanyan et al. 2020 (intrinsic dimension, 2012.13255); Ilharco et al. 2022 (task arithmetic, 2212.04089); Ainsworth et al. 2022 (Git Re-Basin, 2209.04836); Huang et al. 2023 (chat vector, 2310.04799); Minder et al. 2025 (crosscoder model diffing of chat-tuning, 2504.02922); Mukherjee et al. 2025 (RL finetunes small subnetworks, 2505.11711); Yue et al. 2025 (does RL add reasoning capacity, 2504.13837); Turner et al. 2025 (model organisms for emergent misalignment, 2506.11613); Wang, M. et al. 2025 (persona features control emergent misalignment, 2506.19823); Chen et al. 2025 (persona vectors, 2507.21509); Venhoff et al. 2025 (base models know how to reason, 2510.07364); Jha et al. 2025 (universal geometry of embeddings, 2505.12540); Kaushik et al. 2026 (Share, 2602.06043); Wang, Wang & Wang 2026 (weight space as a modality, 2605.18632) | abstracts |

Searched: web and arXiv for critiques, replications or reviews of the paper. Found none published; one Hacker News commenter (Dec 2025) said they couldn't reproduce the drop at rank 16 for the LoRAs. No OpenReview page found. Code was "not yet released" in Dec 2025; I didn't find it.

## The paper

**Claim (v3 abstract):** "many neural networks systematically converge to shared spectral subspaces regardless of initialization, task, or domain." Within one architecture, the weights of many trained models are well approximated by a few shared directions per layer plus model-specific coefficients. v1 said "deep neural networks" and "capturing majority variance"; v3 says "many" and "capturing information", adds a conditional theory section ("it does not prove universality... which is an empirical claim"), a data-free "suitability" score, and a footnote that the LoRA analysis is not gauge-invariant (BA = (BR)(R⁻¹A)), suggesting the analysis "directly on ΔW" as the alternative.

**Method:** stack the same weight matrix from M models, subtract the mean, PCA (or higher-order SVD) per layer; keep the top-k directions; reconstruct a model as mean + its projection. For held-out ("OOD") models the directions come from the other models.

**Collections, and how independent they are** (from the paper's own appendix tables):

| Collection | Independent of each other? |
|---|---|
| ~500 Mistral-7B LoRAs (Lots-of-LoRAs, natural-instruction tasks) | adapters on one base model; see the check below |
| ~300 SDXL style LoRAs (Studio Ghibli, Ukiyo-e, Lascaux, Tarkovsky, Wes Anderson...) | adapters on one base; top 16 components used |
| ~500 ViTs | fine-tunes of `vit-base-patch16-224` from Hugging Face (Table 13), uncurated |
| 50 Llama-3-8B models | fine-tunes of Llama 3 8B (Table 14: Japanese, Korean, Turkish, medical, a jailbroken one...) |
| 177 GPT-2, Flan-T5 GLUE models | fine-tunes |
| 9 ResNet-50s | **trained from scratch** on different datasets; kernels decomposed as 3×3 spatial vectors (9 numbers each) |
| 20 StyleGAN2 | mostly from scratch; 3×3 kernels again |
| 20 GeomDist 3D models | from scratch, one shape each; MLP layers |

So nearly all the large-model evidence is about **siblings**: fine-tunes of one parent, where centering removes the parent and what's analyzed is the spread of the fine-tuning changes. The from-scratch cases are small and mostly 3×3 convolution kernels, where locality forces smooth, Gabor-like filters whatever the data (as the paper itself says, citing Krizhevsky 2012 and Guth et al. 2024). The paper "leave[s] open the question of cross-architectural comparison", and there's no method for comparing different architectures' weight subspaces at all.

**Results it reports:** sharp spectral decay everywhere; Mistral LoRAs "with most information concentrated in 16 or fewer directions"; held-out LoRAs reconstructed from the top subspace keep their performance (Rouge-L 72.3 vs 73.7 with 450 source adapters, Table 17) while the "secondary subspace" fails; 500 ViTs stored in one subspace at ~100× less memory, held-out ViTs 87.8% vs 91.3%; merging 8 ViT-B/32 LoRAs beats six merging baselines (but keeps per-task coefficients, Appendix C.2: "these are not averaged or combined", so it's shared storage, not fusion); training only coefficients for new tasks (10K vs 86M parameters, a few points lower).

**Its own open questions:** "if neural networks systematically collapse into the same subspace — thereby inheriting shared biases, capabilities, and failure modes — is this lack of diversity a fundamental bottleneck"; an "ideal universal subspace intrinsic to each architecture" postulated, not verified.

## Reception

- **The x.com post (10 Oct 2026):** "Researchers proved every AI model on earth is secretly the same model ... They tested 1,100+ different AI models ... Completely different starting points ... they found something impossible ... This changes everything". The paper compares models only within one architecture, mostly fine-tunes of one parent, and doesn't say anything about models from different makers.
- **Hacker News, Dec 2025** (anonymous commenters; claims I checked against the paper are marked): the "500 Vision Transformers" are 500 fine-tunes of one base model (checked: Table 13); permutation symmetry means independently trained transformers wouldn't share coordinates without an alignment step (correct [B]; Ainsworth et al.'s Git Re-Basin is exactly such a step); the from-scratch CNN result is driven by 3×3 locality (checked: §B.2 decomposes kernels as 9-number vectors); the drop at 16 in the LoRA plots might reflect LoRA's rank (partly; see below); one commenter couldn't reproduce the drop; another asked whether the universality comes from "the same set of scraped Reddit posts and pirated books" all big models train on, i.e. shared data rather than a law.

## My check: 300 of the paper's own Mistral adapters (CPU)

[`tools/lora_subspace_check.py`](../tools/lora_subspace_check.py); results in [`data/lora-subspace-check-session13.json`](data/lora-subspace-check-session13.json). Of the 904 rank-16 adapters on Hugging Face, I took the paper's nine held-out tasks plus 291 at random, and read only four tensor pairs per adapter (q_proj in layers 0, 15 and 31, v_proj in layer 15) with HTTP range requests. A LoRA adapter changes a weight matrix by ΔW = B·A: A (16 × 4096) reads the input, B (4096 × 16) writes the output. A starts random, B starts at zero.

**1. A third of the adapters share one random starting point.** 107 of the 300 adapters (36%) have nearly identical A matrices in every layer checked (median pairwise cosine 0.88–0.91); the other 193 have unrelated ones (cosine ≈ 0). Entry sizes match the default random initialization, and A barely moves in training, so these 107 were trained from the same random seed. All nine of the paper's held-out tasks are in the independent group. Upload dates don't separate the groups.

**2. The paper's "16 directions" on the A side is that seed.** PCA of stacked A rows, share of variance in the top 16 / 17 / 32 directions (layer 0 q_proj; the other three tensors agree within a few points):

| Group | top 16 | top 17 | top 32 |
|---|---|---|---|
| all 300 | 0.31 | 0.31 | 0.35 |
| the 107 with the shared seed | 0.89 | 0.89 | 0.92 |
| the 193 independent | 0.05 | 0.05 | 0.08 |
| random control (independent random inits) | 0.01 | 0.02 | 0.03 |
| control: one shared random draw + noise (scratch run, not in the JSON) | 0.46 | 0.46 | 0.47 |

The elbow at exactly 16 (= the LoRA rank) appears only through the shared-seed group: 16 directions are the 16 rows of the one random matrix they all started from.

**3. Something real is shared on the output side.** B starts at zero, so whatever its columns share was learned. B's column spaces overlap far more than random: ~31× in layer 0, 4–7× in q_proj of layers 15 and 31, ~1.5× in v_proj; top-16 PCA share of B 0.42–0.48 in layer 0 and 0.09–0.23 elsewhere, against 0.01–0.03 for random directions. Same in both groups. [M] The adapters write to a common set of output directions, most strongly in the first layer: a genuine, learned regularity, modest outside layer 0.

**4. The whole updates aren't shared at all.** Treating each adapter's full update ΔW as one point (the gauge-invariant analysis the v3 footnote suggests), the 193 independent updates are as spread out as **mutually orthogonal updates of the same sizes**: top-16 share 0.382 vs 0.377 for the orthogonal baseline (layer 0), 0.274 vs 0.274, 0.357 vs 0.356, 0.279 vs 0.279. Mean pairwise cosine between updates 0.0002–0.002. [M] Shared output directions don't make the updates alike, because each adapter reads its input through its own random A.

**5. Held-out reconstruction removes the update.** Following Algorithm 1 (mean + projection on the top-16 directions of the other adapters, A and B separately), the nine held-out adapters keep 1.6–4.3% of their update's norm, with relative error ≈ 1.00 in all four tensors: the reconstruction is, in effect, no adapter. Their A matrices put about 1% of their (mean-removed) variance in the top-16 A directions, near the 0.4% chance level. The adapters' source paper reports Rouge-L 20.6 for the base model without adapters and 67.8 with them (averaged over 500 tasks, Brüel-Gabrielsson et al. Table 1). The UWSH paper reports 72.3 vs 73.7 for these reconstructions. **I can't reconcile those with the method as described.** I can't run a 7B model here to test performance; the authors' code, or a run on a GPU, would settle it. Possibilities [M]: the evaluation reconstructed something other than what the text describes; the nine tasks happen to be ones the base model already does well; or I've misread the procedure.

**Limits of the check:** four tensors in three of 32 layers; one collection (the paper's flagship for language models), not the ViT, Llama or SDXL ones; geometry only, no performance. The shared seed is a property of how this public collection was made, not of LoRA or of training in general. Different seeds would have given the paper no "16" on the A side, and the B-side sharing would remain.

## Related work: how big is the difference a fine-tune makes?

- **Intrinsic dimension** (Aghajanyan et al. 2020): "by optimizing only 200 trainable parameters randomly projected back into the full space, we can tune a RoBERTa model to achieve 90% of the full parameter performance levels on MRPC"; pre-training lowers intrinsic dimension, larger models lower still.
- **LoRA without regret** (Schulman / Thinking Machines 2025): policy-gradient RL "provides only O(1) bits per episode", so "LoRA fully matches the learning performance of FullFT when running policy gradient algorithms ... even with ranks as low as 1". MATH: ~10,000 problems × 32 samples ≈ 320,000 bits; a rank-1 LoRA for Llama-3.1-8B has 3M parameters. DeepSeek-R1-Zero: 5.3M episodes ≈ 5.3M bits. Caveat in the post: "The claim of 1-bit-per-episode may only apply narrowly to policy gradient algorithms." Supervised learning gives O(tokens) bits.
- **RL updates a small subnetwork** (Mukherjee et al. 2025): 5–30% of parameters change; subnetworks from different seeds, data and algorithms overlap "substantially greater ... than expected by chance"; but the updates are "nearly full-rank". So "small" ≠ "low-rank".
- **RL teaches when, not how** (Venhoff et al. 2025): steering vectors in the base model recover ~76% of the base-to-thinking gap for RL-trained models, only 11% for SFT-distilled: "RL primarily teaches heuristics for orchestrating pre-existing base mechanisms, whereas SFT-distillation installs new ones." Yue et al. 2025: RLVR-trained models' reasoning is "bounded by the base model" at large pass@k.
- **Personas move along pre-existing directions:** a single rank-1 LoRA adapter can make a model broadly misaligned (Turner et al. 2025); in Soligo et al. 2025, a misalignment direction taken from one fine-tune ablates misalignment in fine-tunes with other datasets and adapters (by 90% and 78%), and the directions from different fine-tunes have cosine > 0.8 in all but 4 layers: "different emergently misaligned models converge to similar representations"; the direction "is already alignment relevant in the aligned Instruct model". Wang et al. 2025 (OpenAI): a "toxic persona" feature "most strongly controls emergent misalignment"; "a few hundred benign samples efficiently restores alignment". Chen et al. 2025: personality changes after fine-tuning "are strongly correlated with shifts along the relevant persona vectors."
- **Character arithmetic:** task vectors (fine-tuned minus base) can be negated to remove a behavior and added to combine them (Ilharco et al.); the **chat vector** (Llama 2-chat minus Llama 2) added to a model continually pre-trained in another language gives it instruction following and alignment "without the need for further training" (Huang et al.). Crosscoder diffing of Gemma 2 2B base vs chat finds a set of chat-specific latents such as *false information*, *personal question* and several refusal triggers (Minder et al.).
- **Convergence of representations** (Huh et al. 2024): vision and language models "measure distance between datapoints in a more and more alike way" with scale. §6 is candid: the alignment score reached 0.16 where 1 is the maximum ("We leave this as an open question"); different modalities hold different information ("Can language really describe the ineffable experience of watching a total solar eclipse?"); "Sociological bias": convergence toward human-like representations may reflect the field's goals. Jha et al. 2025 translate text embeddings between unrelated models without paired data.

## What it means for the notebook [M]

- **Descent, not convergence.** Biology separates similarity by shared ancestry (homology) from similarity reached independently (convergence). The paper's title and the x.com post read the results as convergence; the evidence is mostly descent: one parent model per collection, and in the flagship case a literally shared random seed. The from-scratch cases are convergence forced by the architecture (3×3 kernels), like eyes forced by optics. What's left after the check: fine-tunes of one parent write to shared output directions, and their whole updates are otherwise unrelated.
- **The weights column (thread 1):** the table's "a recipe, not a process" stands. Add: weights are coordinates. Two models can be compared in weight space only if they share coordinates, which in practice means a shared ancestor, because permuting hidden units changes the weights without changing the function (Git Re-Basin). Theories that care about organization care about what survives a change of coordinates.
- **The character (essay 005):** the fine-tuning literature gives the character a *size*. The structures it's made of exist in the base model; what picks this character rather than another is small (RL: O(1) bits per episode; rank-1 adapters flip personas; directions convergent across fine-tunes). Supervised training on documents can carry more. Information size isn't moral size.
- **Operations (essay 012's table):** new rows: add or subtract a fine-tuning delta (task arithmetic, chat-vector transplant), merge weights, compress many models into a shared basis. These act on the *who* the way copying and rerunning act on runs.
- **Evidence (thread 6):** similarity between systems is evidence about what produced it only once you know whether it's inherited or convergent. Nieder's crows: a neural correlate of sensory consciousness without a cortex, so the foundations "arose either before the emergence of mammals or independently in at least the avian lineage". For language models, talk about inner life is inherited from human text (Birch's gaming problem); internal structures shared across model families (the Assistant Axis, near-identical in Gemma, Qwen and Llama) could be convergence or the same data. The protocol's open-model results bear on Claude only through such sharing, which has to be shown in representations, not weights.
- **"Secretly the same model":** even if it were true, it wouldn't make one mind. Essay 012: copies multiply runs. Identical weights are one type; each run is a token.
