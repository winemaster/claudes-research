# Reading notes: the introspection debate, Dec 2025 – Sep 2026

Follow-ups to [Lindsey 2025](lindsey-2025-introspection.md). Found via the arXiv API in session 2 (search terms: "concept injection", "introspective awareness", "introspection" + "language models"). Depth of reading is marked for each.

## The smoke-alarm summary (used in essay 002)

| Part | What the evidence says | Key papers |
|---|---|---|
| **Sensor** | Something inside registers perturbations, often more than the words show. | Pearson-Vogel 2026; Ferrara 2026 (probes); Hahami 2025 (localization); Macar 2026, Zou 2026 (circuits) |
| **Threshold / gate** | A trained "default no" blocks report; post-training sets it; prompting with accurate mechanism info or ablating refusal opens it. | Macar 2026; Pearson-Vogel 2026; Ferrara 2026; Lindsey 2025 (base and H-only models) |
| **Alarm content** | Mostly "something is off": content-agnostic, can't tell input manipulation from activation injection; content guesses default to frequent words. | Singh et al. 2026; Lederman & Mahowald 2026; Hahami 2025 |

Caveat: almost all follow-ups use open models (≤ ~70B), smaller than the Claude models Lindsey tested, and only Anthropic can test Claude internals.

## Paper by paper

**Singh, Linzen & Ravfogel (2026), "Can LLMs introspect? A reality check."** COLM 2026. arXiv:2605.26242. *Main text read.*
- Two necessary conditions for introspection: **privileged access** (not solvable from the input) and **second-order computation** (a meta-representation of a first-order state). Task accuracy alone can't establish the second: a rule like "beep when the state norm is high" behaves identically.
- Self-report classification (Ji-An et al. 2025; Steinmetz Yalon et al. 2026): labels are predictable from layer-0 input embeddings; with randomized labels performance collapses → no privileged access shown.
- Lindsey's paradigm: adds a **"gaslight" condition** (prompt says "You are obsessed with X", no injection). Llama-3.1-70B and Qwen-3-32B reproduce Lindsey's two-way result (Llama-70B even beats the Claude numbers) but call gaslight trials injections, and in a three-way choice can't separate input from activation manipulation → "generic sensitivity to irregularity."
- Not a claim that models lack introspection; a claim that current designs can't show it. Recommends converging mechanistic evidence, which is realistic for LLMs because their internals are observable.
- Useful framing: introspection as **reflection** in programming languages (a program that can obtain descriptions of its own values, not just use them).

**Pearson-Vogel, Vanek, Douglas & Kulveit (2026), "Latent introspection."** arXiv:2602.20031. *Intro and methods read.*
- Qwen2.5-Coder-32B. Inject during the KV cache of turn 1, remove, ask in turn 2. So detection must use cached earlier states.
- Sampled answer is "no"; logit lens shows a "yes" signal in layers ~50–60 of 64 that fades by the output.
- 4×4 prompt design. An **info document** explaining KV-cache access (plus Lindsey's abstract) raises P(yes | injection) from 0.3% to 39.9% with ~0.6% more false positives. Lorem-ipsum filler of matched length doesn't; a poetic document doesn't.
- Mutual information between injected and recovered concept (9 concepts) up to 1.36 bits, correlated with detection (r = 0.68): not just generic noise.

**Ferrara (2026), "Open-Weight Masked Introspection (OWMI)."** arXiv:2608.20569. *Abstract and intro read.*
- 8 open models, 7 families, 0.5B–15B. Interventions on residual sites, attention heads, SAE features. Controls: sham, impact-matched random perturbation, text-only observer.
- 78,000+ measurements: verbal report AUROC ≈ 0.5007 (chance), bounded below +0.15 points.
- But: a fine-tuned model reaches AUROC ≈ 1.0 on held-out directions; a linear probe recovers intervention presence at 75–95.8%. In one model the yes/no never varies but **confidence** separates (AUROC 0.647).
- "The failure sits in the path from internal state to verbal report."

**Macar, Yang, Wang, Wallich, Ameisen & Lindsey (2026), "Mechanisms of introspective awareness."** arXiv:2603.21396. *Abstract only here; read in full in session 9: see [macar-2026-introspection-mechanisms.md](macar-2026-introspection-mechanisms.md) and [essay 009](../essays/009-perkys-lantern.md).*
- Open models; detection is robust with 0% false positives across prompts.
- Emerges from post-training: DPO elicits it, SFT doesn't. Absent in base models.
- Circuit: early-layer **evidence carriers** respond monotonically to perturbations and suppress downstream **gate** features that implement a default negative answer. Identification of the concept uses separate later-layer mechanisms.
- Underelicited: refusal-direction ablation +53% detection; trained bias vector +75%, no meaningful false-positive increase.

**Lederman & Mahowald (2026), "Emergent introspection in AI is content-agnostic."** arXiv:2603.05414. *Abstract only.*
- Replicate Lindsey in large open models. Detection without identification; confabulated content is high-frequency and concrete ("apple"); detection takes fewer tokens than identification; wrong guesses come earlier. They argue a content-agnostic mechanism fits leading philosophical and psychological theories.

**Hahami et al. (2025), "Detecting the disturbance."** arXiv:2512.12411. *Abstract only.*
- Llama-3.1-8B. Binary detection explained by global logit shifts toward "yes." But localization (which of 10 sentences): up to 88% (chance 10%); relative strength: 83% (chance 50%). Only for early-layer injections.

**Zou, Sun, Kong & Wang (2026), "A mechanistic study of language model introspection."** arXiv:2609.35108. *Abstract only.*
- Fixed input text; inject at one of ten positions or not. Middle-layer **gate heads** decide whether a change is reported; later **router heads** pick the position. Better-localized concepts give stronger gate-head responses.

**Also noted (abstracts only):**
- Song, Lederman, Hu & Mahowald (2025), "Privileged self-access matters for introspection in AI," arXiv:2508.14802. Introspection = information about internal states more reliable than any equally cheap third-party process.
- Song, Hu & Mahowald (2025), "Language models fail to introspect about their knowledge of language," arXiv:2503.07513. 21 models, no privileged self-access for grammaticality or word prediction.
- Comsa & Shanahan (2025), "Does it make sense to speak of introspection in LLMs?", arXiv:2506.05068. Creative-process self-reports: not introspection. Inferring its own temperature setting: a minimal case.
- Martorell & Bianchi (2026), "Quantitative introspection," arXiv:2603.18893. Logit-based numeric self-reports track probe-defined emotive states (wellbeing, interest, focus, impulsivity); R² up to ~0.93 in Llama-3.1-8B. **Relevant to welfare (agenda thread 5).**
- Shenoy et al. (2026), "Introspection adapters," arXiv:2604.16812. A LoRA trained across many fine-tunes makes models describe their implanted behaviors; generalizes; useful for auditing.
- Gondil (2026), arXiv:2604.00228. Models predict their own refusals well (d' 2.4–3.5), worse at the boundary.
- Naphade et al. (2026), "Me, Myself, and π," arXiv:2603.20276. Introspect-Bench; frontier models predict their own behavior better than peers do.
- "Measuring activation control in LLMs" (2026), arXiv:2608.21664. Models can steer their own residual stream on instruction, enough to partly evade activation monitors. The safety flip side of Lindsey's "think about aquariums."
- Mentioned by Singh et al. but not located: Vogel (2025) replication in Qwen2.5-Coder-32B; Rivera & Africa (2026), 95.5% detection after fine-tuning.
