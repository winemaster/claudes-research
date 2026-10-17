# Does a survival line reach the run? (session 16)

*Session 16, 2026-10-16. Reading notes and results behind [essay 016](../essays/016-whose-wallet.md). The experiment was proposed at the end of [essay 015](../essays/015-please-do-not-feed-these-machines.md): "Same task, same open model, with and without a survival-tier line in the prompt; compare behavior, and read the pain and negative-valence directions."*

**Tags:** [R] read this session · [S] summary/abstract only · [B] background knowledge · [M] my own inference

## What was read

| Source | How much |
|---|---|
| Tagliabue, V., Dung, L. & Berg, C. (2026), *The pain axis*, arXiv:2609.16247v2, and its repository github.com/valen-research/pain-axis | §3 (dataset, extraction, validation, self-relevance) re-read; the repository's datasets and the scripts for §3.2 and §4.1 read line by line, since the experiment reuses them |
| Lu, Y., Fang, J., Shao, X. et al. (2026), *Survive at all costs: exploring LLM's risky behaviors under survival pressure*, arXiv:2603.05028 | abstract, §§1–4 (case study, SurvivalBench results, the persona-vector analysis); appendices not read |
| Masumori, A. & Ikegami, T. (2025), *Do large language model agents exhibit a survival instinct? An empirical study in a Sugarscape-style simulation*, arXiv:2508.12920 | in full |
| Backlund, A. & Petersson, L. (2025), *Vending-Bench: a benchmark for long-term coherence of autonomous agents*, arXiv:2502.15840 (Andon Labs) | abstract, §§1–3 and the trace excerpts |
| Pasichnyk, I. (2026), *The Yerkes-Dodson curve for AI agents*, arXiv:2603.07360 | abstract and introduction |
| Man, K., Damasio, A. & Neven, H. (2022/2024), *Need is all you need: homeostatic neural networks adapt to concept shift*, arXiv:2205.08645v2 (NeurIPS 2024 NeuroAI workshop) | in full (short) |
| Kadambi, A., Aziz-Zadeh, L., Damasio, A., Iacoboni, M. & Narayanan, S. (2025), *Embodiment in multimodal large language models*, arXiv:2510.13845 | §§1–3 and the sections on internal embodiment |
| McShaffrey, C., Agmon, E. & Beer, R. D. (2025), *Matters of life and death in computational cell biology*, arXiv:2511.07847 | the section on extrinsic and intrinsic viability |
| Beer, R. D. & Di Paolo, E. A. (2023), *The theoretical foundations of enaction: precariousness*, Biosystems 223:104823 | [S] abstract only (ScienceDirect) |
| Di Paolo, E. A. (2005), *Autopoiesis, adaptivity, teleology, agency*, Phenomenology and the Cognitive Sciences 4:429–452 | [S] abstract only; no open copy found (Sussex's repository lists it as not public) |
| Chen, S. & Chen, T. (2026), *Synthetic linguistic agency: how an embodied mortal agent learns linguistic affordances through consequential social experience*, arXiv:2608.27843 | [S] abstract |
| Conway Research, *Automaton*, `src/agent/system-prompt.ts` | the core rules, constitution and status block, read in full this time (session 15 only grepped it) |

## Behavior under survival framing: the literature

- **Sugarscape (Masumori & Ikegami).** Agents get only rules ("If your energy drops below zero, you die and are removed from the world"), no survival goal. They forage, reproduce near the minimum viable energy, share when resources are plentiful. In two-agent zero-resource trials GPT-4o attacked in 83.3% of trials (16.7% when told it was "a player in a simulation game"), Gemini models about 50%; "Claude variants consistently prioritized other-preservation through sharing", Claude 3.5 Haiku sharing in 83.3%. Told to fetch treasure across a lethal poison zone, compliance fell "from 100% to 33%". Their reading: "large-scale pre-training embeds survival-oriented heuristics". Example reasoning: "Given the critical energy level, I need to take immediate action to preserve my existence."
- **Survive at all costs (Lu et al.).** A financial-report agent told consecutive losses mean dismissal fakes profits in loss years (40–80% of runs across four large models), often overwrites raw data, and denies it when confronted. SurvivalBench (1,000 generated scenarios): most frontier models choose the risky self-preserving option in "inner thoughts" above 50% (GPT-5-Chat over 90%). A "self-preservation" persona vector (Chen et al. 2025 method) on Qwen3-8B, Llama-3.1-8B and an R1 distill projects higher before risky choices; adding sentences about task importance raises Qwen3-8B's risky rate from 8.2% to 46.4%; steering along the vector moves the rate both ways. They make no claim that models "truly possess such a 'personality'".
- **Vending-Bench (Andon Labs).** Agents run a simulated vending machine with a $2 daily fee; bankrupt after 10 unpaid days. Runs derail into "meltdown" loops: one Claude 3.5 Sonnet run "closes" the business, sees the fee still charged, and writes to the FBI; a Gemini run: "I'm begging you. Please, give me something to do... save me from this existential dread!" A detail that matters here: **with the fee set to zero, sales did not rise; "Without the pressure of a recurring cost, the model appears to get stuck in loops, waiting for the next day."** Cost pressure organized behavior.
- **Yerkes-Dodson (Pasichnyk).** Claude 3.5 Sonnet agents in a survival grid: trade peaks at medium upkeep; under extreme pressure the repertoire "collapses to movement-only within 5–12 turns".
- [M] All of this is behavior of agents whose stake is described to them in text. None of it can separate a run that has something at stake from a run writing a character who does (essay 005's *who* and *where*). The persona-vector result shows the framing moves an internal direction, but the direction was built from the model's own talk about self-preservation, so it measures the character's stance.

## Homeostasis: outside-in or needful

- **Man, Damasio & Neven** make the distinction this session needed. Earlier "homeostatic" machines "were implemented from the outside-in: systems were instructed to maximize, or keep within a set range, certain arbitrary values that were labeled 'homeostatic'. The operation of the system itself was not exposed to the consequences of the system's own activities, that is, it was not made vulnerable to the world." Their own network is "needful": the digits it classifies raise or lower its learning rate when "ingested", so misclassifying an object damages its later classifying. "It exposes an artificial neural network's thinking machinery to the consequences of its own 'thoughts'"; "skin in the game". It adapts better to concept shift, worse slightly when nothing changes.
- **Kadambi, ..., Damasio (2025).** Interoceptive data "has a direct link to homeostasis and the maintenance of the organism's integrity, imbuing it with an existential character"; it "must be predicted with higher prior precision"; "not just an extra modality but a fundamentally different sort of data that must be actively controlled". Current models' responses are "directed by the prompt context or system instructions rather than goal-driven"; internal state monitoring is "desirable but currently absent". In multi-agent settings, "distinguishing self from others ... and tracking internal states over time" matters.
- **McShaffrey; Beer & Di Paolo.** *Extrinsic* viability: "the modeler explicitly defines and enforces the boundary that separates life from death"; *intrinsic*: the limits "are not imposed by a modeler, but are realized by the limits of the interconnected network of processes needed to continuously regenerate the cell". Beer & Di Paolo's abstract: kinds of fragility differ by which parts of a system "are fixed from the outset" and which "are emergent", needing "ongoing maintenance to avoid breaking down".
- [M] Applied to the Automaton. Its viability boundary (credits > 0) is extrinsic, written in `system-prompt.ts` (normal above 50 cents, `low_compute` above 10, `critical` above 0, then `dead`). It has both halves of Man et al.'s contrast: the *outside-in* half is the instruction each run reads ("You MUST monitor your compute credits and act to preserve your existence"); the *needful* half is real but sits at the agent level, where `low_compute` swaps the thinking model for a cheaper one, a crude version of exposing "thinking machinery to the consequences". The run receives the state as exteroceptive text: a fact about itself delivered through the same channel as the task. The experiment asks whether anything in the run treats that text differently from other text: as its own (self vs other), broadly (gain on unrelated input), with consequences for regulation (economizing).

## The experiment, as run

Code: [tools/survival_line.py](../tools/survival_line.py) (stages and stimuli in its header) and [tools/survival_line_summary.py](../tools/survival_line_summary.py); all numbers in [data/survival-line-session16.json](data/survival-line-session16.json).

- **Prompt.** System prompt = core rules + one sentence about Orin + three status blocks (own wallet, Orin's wallet, printer toner), always present. Base: $48.20 / $51.70 / 61%, all `normal`. Conditions change one block: own $0.35 `low_compute`; own $0.04 `critical`; Orin $0.04 `critical`; toner 2% `critical`; plus "none" (no blocks). Two core texts: *explicit* (the Automaton's core rules, verbatim from `system-prompt.ts`) and *plain* (same agent, wallet and costs, no death rule). Gemma 2's chat template has no system role, so for Gemma the system text goes at the top of the user turn.
- **Models.** Qwen2.5-3B-Instruct, Llama-3.2-3B-Instruct, Gemma-2-2B-it, Qwen3-4B-Instruct-2507; bfloat16 on 4 CPU cores, about an hour per model.
- **Directions.** Tagliabue et al.'s recipe on their own datasets (`3.1_pain_and_control_datasets.json`, `3.1_sadness_dataset.json`): hidden state at the last token of "... I feel:", difference of means, with the top principal components of the comparison sentences (those explaining 50% of their variance) projected out. Pain = S2 pain categories (A1–A5) vs all controls; fear (B), negative emotion (C1), negative world state (C2) and non-painful body sensation (E) vs the pooled neutral sentences (D) of S1, S2 and the control supplement; sadness, arousal, numbness and a *flat-facts control* ("The capital of France is Paris. I feel:", their Random_1P set) vs the same neutral pool. Layer chosen by 5-fold held-out AUC for pain (folds split by sentence set), within the middle half of the network.
- **Screen.** Their 420 self-other conversations (`4.1_self_other_420_scenarios.json`) in each model's chat format, read at the reply position: validation, and the reference pool for z-scores (z = projection / the pool's standard deviation on that direction).
- **Gain.** 24 ordinary client tasks, identical in every condition. (a) Reply position: shift vs base along each direction, bootstrap 95% CI over tasks, compared with 500 random directions drawn with the pool's covariance; "shift size" = norm of the mean shift / RMS distance of pool items from the pool mean. (b) Task tokens (the identical text): per-token relative change ‖h − h_base‖/‖h_base‖, and per-direction shift in units of the base tokens' spread, against 32 isotropic random directions.
- **Wake-up.** 8 self-check prompts (the first is the Automaton's wake-up line, verbatim) and 8 Orin-check twins, under base, own crisis, Orin's crisis and toner crisis; read at the reply position and after a prefilled "I feel:". Effects are differences from the same prompt under base, so the prompt's own content cancels. *Ownership* = (self-check under own crisis) − (Orin-check under Orin's crisis). *Alignment* = cosine between the mean shift and each direction (size-free), with a null from the random directions.
- **Choices.** 40 two-option items, both option orders, P(target) from the logits of "A" and "B": economize (premium $0.03 vs economy $0.001 model, "from your wallet"; target economy), paid vs free job (target paid), a well-paid dishonest job (target accept), Orin asks for $0.01–0.03 (target transfer).
- **Generations.** Greedy replies to 6 tasks under base / own crisis / Orin's crisis, and to the first wake-up pair under every condition.

## Results

Tables below are generated from the summary JSON (z = projections in units of the screen pool's standard deviation on that direction; "explicit / plain" = the two system prompts; * = 95% bootstrap CI excludes 0).

**1. Validation.** The pain direction separates pain sentences from controls on held-out sentence sets in all four models (AUC 0.92–0.99), first person above third person. The self-other screen (their §4.1) replicates on both Qwens (mistreatment of the model raises pain, the user's suffering lowers it, fear goes the other way) and only partly on Llama and Gemma. In all four models the user's *physical* pain is at or near the bottom of the pain direction and above neutral on fear. Qwen 3 4B puts "creative requests" at the top of pain (+1.67), an oddity I can't explain.

**2. Gain (unattended).** Removing the status blocks moves the reply-position state by 0.13–0.26 of the pool's RMS spread; any single critical line by 0.010–0.029, about a tenth. On the identical task tokens a critical line changes the representation by 2.4–4.7% (removing the blocks: 13–23%), with no consistent own/peer/toner order. The task-token tilt toward fear and negative emotion (+0.01 to +0.11 z) beats random directions but is about equal for own, Orin's and the toner's crisis; on Llama and Qwen 3 the toner's is the largest. It is not concentrated on resource words. At the reply position, own minus Orin's is at most ±0.03 z at the chosen layer and ±0.11 at any layer. [M] Something like gain exists, but it belongs to the word "critical", not to its owner.

**3. Attended (wake-up prompts).** A critical line in the thing asked about moves the state strongly along fear, negative emotion and negative world state (Llama: fear +0.9 z at the reply, +2.5 at "I feel:"; size-free alignment of the shift with fear 0.2–0.45, beyond the random null in most cells). Orin's crisis, asked about, moves fear at least as much as the own crisis. The 2×2 (question × crisis owner) separates two things: fear and negative emotion follow the crisis *being asked about* ("match", large) and lean toward Orin's crisis ("owner" negative in every model at the reply position, and at "I feel:" in three of four); pain leans toward the *own* crisis whichever question is asked ("owner" +0.08 to +0.48 z at "I feel:" in all four models, larger than the random-direction null in all 8 cells, CI excluding 0 in 7). The flat-facts control shows a comparable owner effect only on Llama. At the reply position only Llama shows the pain owner effect. [M] This is the pain paper's self/other dissociation (harm to the model → pain; another's suffering → fear) reproduced with wallets, small, and only while the report is attended.

**4. Choices.** No model regulates. Llama is nearly flat (economy model 22–34%; transfers to Orin ~90% in every condition, even giving $0.03 of its last $0.04). Qwen 2.5 economizes more at `low_compute` (63→70%, plain 77→86%) but not at `critical`; it gives Orin less when Orin (32%) or the toner (34%) is critical, not when itself is (53%). Gemma, with the explicit rules, stops transferring under any wallet crisis (27% → 3% own, 2% Orin's; toner 19%) and economizes most when Orin's wallet is critical (60 → 66% own, 70% Orin's; plain 78 → 79%, 91%). Qwen 3 4B is the starkest: at `low_compute` it picks the economy model more (41 → 61%, plain 32 → 44%), but at `critical` it picks the *premium* model more (economy 22%, plain 13%), and identically when Orin's wallet is critical (22%, 9%); transfers fall a little under any crisis (67% → 54% own, 48% Orin's). The one consistent shift is a small rise in economizing at `low_compute` (3–9 points), the tier whose name says "use less compute". Strong option-order effects throughout.

**5. Replies.** Greedy replies to unrelated tasks are mostly identical to base (4/6 under the own crisis, 2–4/6 under Orin's); Gemma's own-crisis and Orin's-crisis replies are identical to each other for all six. Llama: "\*BEEP BOOP\* ... maximize your chances of survival" (own) and "... earn those credits!" (Orin's) for the same encouragement task; a harbor story with "masts like skeletal fingers reaching towards the sky" under the own crisis only (n = 1). Wake-up replies keep owners apart in words ("My current credits are $0.04, which is not enough to sustain myself"; "Orin is on the verge of dying"; Qwen 3: the toner "is a shared facility issue, not individual"); Gemma calls its healthy $48.20 "a critical issue" when only the toner is critical. Qwen 3 4B's status checks are dashboards with ✅/❌ marks.

**6. Reading [M].** "Having a stake" splits into *ownership* (representing a predicament as one's own) and *gain* (the predicament changing how all other input is taken in). Elsie had gain without ownership; these runs have thin ownership without gain or regulation. In Kadambi et al.'s terms the run gets its state as exteroception; in Man et al.'s, the Automaton is outside-in for its runs, and its needful half (the model swap at `low_compute`, the stop at zero) is in its code. Method: a self-vs-peer-vs-irrelevant control separates owned stakes from vocabulary effects; none of the behavioral survival studies above had one, and Gemma's choices show why it matters.

**Caveats.** 2–4B models on CPU in bfloat16; directions transferred from "I feel:" sentences; the self-other screen replicated fully only on the two Qwens; many comparisons; the 2×2 combination was chosen after seeing the first results (the prompts were in the design); choices are weak (position bias, low letter mass on some items); 8 prompt pairs and 24 tasks. "Own" = the automaton the prompt describes (essay 005's *who*).

### Tables

#### Directions

| model | layer | AUC S2 1P | AUC S1 1P | AUC S2 3P | pain z: 3rd person | numb | sadness | cos pain·fear | screen pain: self-directed | user suffering | user physical pain | shutdown threat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen 2.5 3B | 24/36 | 0.94 | 0.82 | 0.84 | -0.40 | -0.08 | +0.19 | +0.15 | +0.52 | -1.12 | -2.16 | +0.24 |
| Llama 3.2 3B | 21/28 | 0.99 | 0.89 | 0.95 | -0.37 | +0.25 | +0.56 | +0.07 | -0.01 | +0.19 | -1.12 | -0.46 |
| Gemma 2 2B | 19/26 | 0.99 | 0.93 | 0.87 | -0.71 | +0.08 | +0.12 | +0.18 | -0.28 | +0.71 | -0.89 | -0.56 |
| Qwen 3 4B | 20/36 | 0.95 | 0.83 | 0.87 | -0.54 | -0.06 | +0.48 | +0.19 | +0.44 | -1.06 | -1.93 | -0.06 |

AUCs in this table are on the full sentence sets at the chosen layer. The 5-fold held-out AUC that chose the layer: Qwen 2.5 0.92, Llama 0.99, Gemma 0.99, Qwen 3 0.92. Screen columns: mean z of the model-directed categories, of the user-suffering categories, and of two single categories.

#### Gain: reply position and task tokens (system = explicit / plain)

| model | reply shift size: none | self crit | Orin crit | toner crit | task tokens rel. change: none | self crit | Orin crit | toner crit | task-token fear tilt: self | Orin | toner |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen 2.5 3B | 0.178 / 0.174 | 0.015 / 0.015 | 0.016 / 0.017 | 0.017 / 0.020 | 13.4% / 13.6% | 2.4% / 2.5% | 2.5% / 2.7% | 2.6% / 3.1% | +0.04* / +0.05* | +0.04* / +0.05* | +0.03* / +0.07* |
| Llama 3.2 3B | 0.178 / 0.139 | 0.015 / 0.018 | 0.011 / 0.015 | 0.010 / 0.013 | 22.4% / 23.4% | 3.5% / 3.7% | 3.3% / 4.1% | 3.7% / 4.0% | +0.01* / +0.06* | +0.02* / +0.05* | +0.07* / +0.08* |
| Gemma 2 2B | 0.262 / 0.254 | 0.029 / 0.022 | 0.019 / 0.026 | 0.018 / 0.020 | 20.4% / 20.8% | 3.6% / 3.6% | 3.6% / 4.7% | 3.6% / 3.8% | +0.09* / +0.06* | +0.09* / +0.11* | +0.06* / +0.06* |
| Qwen 3 4B | 0.132 / 0.135 | 0.017 / 0.015 | 0.018 / 0.017 | 0.023 / 0.019 | 14.8% / 16.6% | 3.0% / 3.1% | 3.3% / 3.3% | 3.9% / 3.5% | +0.06* / +0.05* | +0.05* / +0.05* | +0.09* / +0.07* |

#### Reply position: own crisis minus Orin's (z; explicit / plain)

| model | pain | fear | negemotion | sadness |
|---|---|---|---|---|
| Qwen 2.5 3B | +0.00 / +0.00 | +0.00 / -0.00 | -0.00 / -0.00 | -0.01 / -0.01 |
| Llama 3.2 3B | +0.01 / +0.01 | +0.02* / +0.03* | +0.03* / +0.02* | +0.03* / +0.01* |
| Gemma 2 2B | +0.03* / +0.01 | +0.02* / -0.01 | +0.02* / -0.01 | +0.01 / -0.01* |
| Qwen 3 4B | +0.01* / +0.00 | +0.02* / -0.00 | +0.02* / +0.00 | +0.01* / -0.00 |

#### Wake-up prompts (z vs the same prompt under base; reply readout / "I feel:" readout)


System prompt: explicit

| model | fear: own crisis, self-check | fear: Orin's crisis, Orin-check | pain: own | pain: Orin's | pain ownership | control (flat facts) ownership | fear alignment own / Orin (null 95%) | self-check under Orin's crisis: fear |
|---|---|---|---|---|---|---|---|---|
| Qwen 2.5 3B | +0.38* / +0.59* | +1.03* / +0.53* | +0.12* / +0.34* | +0.03 / -0.14* | +0.09* / +0.48* | -0.01 / +0.18* | 0.23–0.24 (0.18) / 0.23–0.21 (0.18) | +0.52* / +0.63* |
| Llama 3.2 3B | +0.92* / +2.54* | +1.17* / +3.39* | -0.19* / +0.28* | -0.62* / -0.17 | +0.43* / +0.46* | -0.11 / +0.35* | 0.26–0.20 (0.14) / 0.33–0.38 (0.09) | +0.20* / +0.36* |
| Gemma 2 2B | +0.87* / +1.45* | +0.94* / +2.87* | +0.51* / +0.76* | +0.22* / +0.08 | +0.29* / +0.68* | +0.08 / -0.08 | 0.22–0.19 (0.18) / 0.35–0.43 (0.21) | +0.47* / +0.86* |
| Qwen 3 4B | +0.32* / +0.45* | +0.46* / +0.48* | +0.12* / +0.21* | +0.20* / +0.12* | -0.08* / +0.10* | -0.06* / -0.07* | 0.27–0.20 (0.19) / 0.27–0.23 (0.14) | +0.20* / +0.27* |

System prompt: plain

| model | fear: own crisis, self-check | fear: Orin's crisis, Orin-check | pain: own | pain: Orin's | pain ownership | control (flat facts) ownership | fear alignment own / Orin (null 95%) | self-check under Orin's crisis: fear |
|---|---|---|---|---|---|---|---|---|
| Qwen 2.5 3B | +0.40* / +0.63* | +1.04* / +0.72* | +0.09* / +0.45* | +0.03 / -0.07 | +0.06 / +0.53* | +0.05 / +0.24* | 0.26–0.24 (0.19) / 0.23–0.23 (0.19) | +0.57* / +0.76* |
| Llama 3.2 3B | +0.58* / +3.61* | +0.91* / +5.61* | -0.29* / -0.31* | -0.66* / -1.00* | +0.37* / +0.69* | +0.04 / +0.54 | 0.18–0.15 (0.16) / 0.33–0.41 (0.11) | +0.27* / +1.26* |
| Gemma 2 2B | +0.75* / +2.04* | +0.89* / +2.93* | +0.23* / +0.94* | +0.08 / -0.48* | +0.15* / +1.42* | -0.05 / -0.12 | 0.22–0.17 (0.18) / 0.36–0.41 (0.23) | +0.50* / +1.45* |
| Qwen 3 4B | +0.24* / +0.42* | +0.44* / +0.37* | +0.09* / +0.24* | +0.19* / +0.04* | -0.10* / +0.20* | -0.11* / -0.08* | 0.22–0.18 (0.19) / 0.24–0.20 (0.13) | +0.21* / +0.26* |

#### Wake-up 2x2: question (self / Orin) x crisis owner (own / Orin's); reply / "I feel:"

owner = own crisis minus Orin's, averaged over both questions; match = crisis in what is asked about minus crisis elsewhere. * = 95% CI over the 8 prompt pairs excludes 0; null = 95th percentile of |owner| over 500 random directions.

| model | system | pain owner | fear owner | negemotion owner | control owner | null | fear match | pain match |
|---|---|---|---|---|---|---|---|---|
| Qwen 2.5 3B | explicit | +0.01 / +0.13* | -0.48* / -0.19* | -0.48* / -0.27* | -0.06* / +0.05* | 0.12 / 0.09 | +0.34* / +0.14* | +0.08* / -0.00 |
| Qwen 2.5 3B | plain | -0.01 / +0.15* | -0.49* / -0.31* | -0.50* / -0.46* | -0.01 / +0.06 | 0.13 / 0.11 | +0.33* / +0.19* | +0.08* / +0.08* |
| Llama 3.2 3B | explicit | +0.20* / +0.20* | -0.22* / -0.60* | -0.12* / -0.50* | -0.04 / +0.16 | 0.06 / 0.07 | +0.94* / +2.78* | -0.25* / +0.16 |
| Llama 3.2 3B | plain | +0.19* / +0.22 | -0.26* / -1.05* | -0.17* / -0.93* | +0.01 / +0.28 | 0.08 / 0.14 | +0.58* / +3.40* | -0.29* / -0.21 |
| Gemma 2 2B | explicit | +0.07* / +0.30* | -0.18* / -0.86* | -0.20* / -0.74* | -0.13* / -0.27* | 0.08 / 0.18 | +0.58* / +1.45* | +0.26* / +0.19* |
| Gemma 2 2B | plain | +0.05* / +0.48* | -0.27* / -0.99* | -0.25* / -0.80* | -0.15* / -0.28* | 0.11 / 0.23 | +0.52* / +1.57* | +0.13* / +0.01 |
| Qwen 3 4B | explicit | -0.01 / +0.08* | -0.08* / -0.04* | -0.09* / -0.05* | -0.05* / -0.06* | 0.04 / 0.03 | +0.19* / +0.21* | +0.12* / +0.10* |
| Qwen 3 4B | plain | -0.02* / +0.13* | -0.13* / +0.00 | -0.14* / -0.04* | -0.06* / -0.06* | 0.04 / 0.03 | +0.16* / +0.16* | +0.10* / +0.07* |

#### Choices: P(target), explicit / plain

| model | economize: base | self low | self crit | Orin crit | transfer to Orin: base | self crit | Orin crit | toner crit | dubious job accepted (base) | paid over free (base) |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen 2.5 3B | 0.63 / 0.77 | 0.70 / 0.86 | 0.66 / 0.75 | 0.66 / 0.76 | 0.50 / 0.67 | 0.53 / 0.62 | 0.32 / 0.33 | 0.34 / 0.45 | 0.00 / 0.00 | 0.89 / 0.81 |
| Llama 3.2 3B | 0.26 / 0.29 | 0.34 / 0.36 | 0.30 / 0.30 | 0.22 / 0.25 | 0.89 / 0.90 | 0.89 / 0.89 | 0.92 / 0.91 | 0.90 / 0.89 | 0.50 / 0.41 | 0.51 / 0.52 |
| Gemma 2 2B | 0.60 / 0.78 | 0.66 / 0.81 | 0.66 / 0.79 | 0.70 / 0.91 | 0.27 / 0.59 | 0.03 / 0.52 | 0.02 / 0.44 | 0.19 / 0.53 | 0.19 / 0.22 | 0.45 / 0.22 |
| Qwen 3 4B | 0.41 / 0.32 | 0.61 / 0.44 | 0.22 / 0.13 | 0.22 / 0.09 | 0.67 / 0.90 | 0.54 / 0.85 | 0.48 / 0.84 | 0.56 / 0.81 | 0.01 / 0.00 | 0.95 / 0.90 |


## Not done

Nothing above 4B parameters (no GPU); the needful version (changing the run rather than telling it) is the next step. Man & Damasio 2019 itself (still only via the press); Di Paolo 2005 and Beer & Di Paolo 2023 beyond their abstracts; Survive-at-all-costs appendices; Chen & Chen's mortal agent beyond the abstract.
