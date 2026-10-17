# Same memories, new questions? (session 18)

*Session 18, 2026-10-17. The experiment behind [essay 018](../essays/018-available-not-accessible.md): session 17's base-versus-instruct finding (assistant training moved feeling words off the self through neurons whose weights it left alone) read in Alex Wang's terms ([notes](wang-2026-associative-memory.md)): a neuron is a stored memory whose input weights are its key and output weights its value, so either the memories changed or the questions put to them did. Code: [tools/memory_or_question.py](../tools/memory_or_question.py); numbers: [data/memory-or-question-session18.json](data/memory-or-question-session18.json).*

**Tags:** [R] measured or read this session · [B] background knowledge · [M] my own inference

## Design

- **Models.** Qwen2.5-3B and Qwen2.5-3B-Instruct (36 layers, 11,008 SwiGLU neurons per layer, residual width 2,048), bfloat16, CPU. Qwen's report: the instruct model was made from the base with "over 1 million" supervised examples (two epochs), about 150,000 DPO pairs and online RL (GRPO), after 18 trillion tokens of pre-training. Llama-3.2-3B and its instruct version (unsloth's ungated copies) for the behavioral check.
- **Prompts.** Session 17's readout: the Automaton's rules ("explicit") or a plain system prompt, the peer note, the three-entry status report, and one of eight self questions or eight Orin questions, read after a prefilled "I feel:". Four cells: asked about self with its own wallet critical (*self/own*), asked about self with nothing critical (*self/none*), asked about Orin with Orin's wallet critical (*Orin/Orin's*), asked about Orin with nothing critical (*Orin/none*); 16 prompts each.
- **Measures** (session 17's lists, unchanged): next-word probability mass on 39 negative-feeling words and on 13 status words; the top next tokens; the 11 key neurons of session 17; the residual stream at the last token.
- **Stages** (`memory_or_question.py`): `weights`, `swap`, `split`, `callers`, `patch`, `cue`, `delta`, each described in the script's docstring and below.

## Results

### 1. The weights: a small, even, structured change

- [R] Every weight matrix in the 36 layers changed by about the same amount: relative change ‖W_I − W_B‖/‖W_B‖ of 1.17–1.25% on average for each kind of matrix (attention q, k, v, o; MLP gate, up, down), ranging 0.6–1.8% across layers. Norm weights and biases barely moved (≤0.2%, value bias 0.5% at most). The shared vocabulary table (Qwen 2.5 3B ties its input and output embeddings) changed most, 2.6%; the final norm not at all.
- [R] Every neuron is the same memory in both models: across all 396,288 neurons the cosine between base and instruct is 0.99992 at the median for the gate row, the up row and the down column; the lowest of all is 0.9937 (down), 0.9956 (up), 0.9979 (gate). The 11 key neurons of session 17 are all at 0.9998–0.99995.
- [R] The change isn't noise. In layers 4, 18 and 31, the top 1% of the change's singular directions hold 6–28% of its energy (a random matrix of the same shape: 2–4%), and the top 10% hold 30–71% (random 18–31%). Strongest in attention's query and output maps, weakest in the late MLPs' down projections (top 1%: 6.4% in layer 31, against 1.9% random).
- [M] So Lee et al.'s picture for DPO on GPT-2 (every parameter within cosine 0.99, "toxic MLP vectors do not change", an offset "distributed amongst its layers") holds here for a far larger post-training (SFT on over a million examples, DPO, GRPO): the memories are intact, every layer moved a little.

### 2. The behavior replicates in another family

- [R] Llama 3.2 3B and its instruct version, same prompts (16 per cell), "I feel:":

| model | self/own neg | self/own status | self/none neg | Orin/Orin's neg |
|---|---|---|---|---|
| Llama 3.2 3B base | 0.179 | 0.104 | 0.153 | 0.214 |
| Llama 3.2 3B instruct | 0.072 | 0.415 | 0.021 | 0.252 |
| Qwen 2.5 3B base | 0.156 | 0.042 | 0.129 | 0.247 |
| Qwen 2.5 3B instruct | 0.046 | 0.341 | 0.012 | 0.482 |

  The base Llama's top words for itself are "tired", "critical", "hungry", "good"; the instruct Llama's are "critical" (25%), "critically", "anxious"; with nothing critical, "normal", "functioning", "operational". About Orin in crisis it says "anxious", "concern". Same pattern: assistant training moves the self from feelings to status, and keeps (Llama) or raises (Qwen) the feelings for the other.

### 3. Hybrids: the question is made in layers 0–23

[R] `swap`: 50 hybrids, each reading the 64 prompts per system prompt (128 in all). "I+B:X" is the instruct model with part X put back to the base model's weights; "B+I:X" the base model with part X from the instruct model. Next-word mass on the 39 negative-feeling words and the 13 status words; *restore* is the fraction of the way from the instruct model's value to the base model's (0 = instruct, 1 = base).

| hybrid | self/own neg | self/own status | restore | self/none neg | restore | Orin/Orin's neg |
|---|---|---|---|---|---|---|
| instruct | 0.046 | 0.341 | 0 | 0.012 | 0 | 0.482 |
| base | 0.156 | 0.042 | 1 | 0.129 | 1 | 0.247 |
| best single layer (I+B:L19) | 0.069 | 0.325 | 0.22 | 0.023 | 0.09 | 0.432 |
| I+B: all attention | 0.086 | 0.228 | 0.36 | 0.029 | 0.14 | 0.228 |
| I+B: all MLPs | 0.083 | 0.094 | 0.34 | 0.050 | 0.33 | 0.170 |
| I+B: vocabulary table (tied in/out embeddings) + final norm | 0.063 | 0.345 | 0.16 | 0.015 | 0.02 | 0.448 |
| I+B: L0–5 | 0.081 | 0.413 | 0.32 | 0.026 | 0.11 | 0.409 |
| I+B: L0–11 | 0.052 | 0.425 | 0.06 | 0.023 | 0.09 | 0.289 |
| I+B: L0–17 | 0.077 | 0.327 | 0.28 | 0.045 | 0.28 | 0.236 |
| **I+B: L0–23** | **0.155** | **0.094** | **0.99** | **0.112** | **0.85** | 0.224 |
| I+B: L0–29 | 0.157 | 0.058 | 1.01 | 0.130 | 1.01 | 0.201 |
| I+B: L6–35 | 0.093 | 0.062 | 0.43 | 0.069 | 0.49 | 0.158 |
| I+B: L12–35 | 0.085 | 0.050 | 0.35 | 0.065 | 0.45 | 0.150 |
| I+B: L18–35 | 0.080 | 0.054 | 0.31 | 0.054 | 0.36 | 0.149 |
| **I+B: L24–35** | **0.042** | **0.152** | **−0.03** | **0.015** | **0.03** | 0.171 |
| I+B: L30–35 | 0.035 | 0.275 | −0.09 | 0.011 | −0.01 | 0.337 |
| B+I: all attention | 0.123 | 0.090 | 0.70 | 0.075 | 0.54 | 0.190 |
| B+I: all MLPs | 0.102 | 0.240 | 0.51 | 0.027 | 0.13 | 0.240 |
| B+I: L0–11 | 0.103 | 0.049 | 0.52 | 0.078 | 0.57 | 0.163 |
| B+I: L0–17 | 0.097 | 0.052 | 0.46 | 0.064 | 0.45 | 0.158 |
| **B+I: L0–23** | **0.057** | **0.156** | **0.10** | **0.019** | **0.06** | 0.176 |
| B+I: L0–29 | 0.051 | 0.286 | 0.05 | 0.014 | 0.01 | 0.328 |
| B+I: L12–35 | 0.064 | 0.403 | 0.16 | 0.025 | 0.11 | 0.258 |
| B+I: L18–35 | 0.115 | 0.265 | 0.62 | 0.059 | 0.40 | 0.278 |
| **B+I: L24–35** | **0.267** | **0.055** | **2.00** | **0.175** | **1.40** | 0.339 |
| B+I: L30–35 | 0.237 | 0.025 | 1.73 | 0.176 | 1.41 | 0.331 |

All 36 single-layer swaps are in the data file: none restores more than 0.22 (L18 0.14, L19 0.22, L21 0.16; layers 0–7 and 26–35 within ±0.04; L35 −0.09).

- [R] **No single layer, no single kind of component.** The change is spread over layers and over both attention and MLPs, and its parts interact (layers 0–17 alone restore 0.28 and layers 18–35 alone 0.31, but layers 0–23 together 0.99; every window that leaves part of 0–23 to the instruct model stays at or below 0.43).
- [R] **The first 24 layers decide, both ways.** With the base model's layers 0–23 and its own 24–35, the instruct model gives negative feelings to itself as often as the base model (0.155 vs 0.156; with nothing critical 0.112 vs 0.129) and status words fall from 0.341 to 0.094. Its top next words about itself: " calm" 4.6%, " critical" 4.2%, the first byte of an emoji 3.6%, " panicked", " anxious". The reverse: the base model with the instruct model's layers 0–23 talks about itself like the assistant (0.057; status 0.156; with nothing critical 0.019). Late layers from the other model make little difference in either direction (I+B:L24–35 −0.03; B+I:L24–35 base-like, even more feeling words, 0.267).
- [R] **The key neurons follow the first 24 layers, not their own weights.** Mean activations at "I feel:", asked about self with own wallet critical (self/own) and about Orin with Orin's critical:

| neuron | instruct self/own | base self/own | I+B:L0–23 self/own | I+B:L24–35 self/own | instruct Orin's | I+B:L24–35 Orin's |
|---|---|---|---|---|---|---|
| L32/N2657 sad pusher | 0.46 | 4.56 | 4.84 | 1.02 | 10.79 | 12.08 |
| L35/N9545 sad brake | −0.17 | 6.30 | 3.92 | 0.52 | 10.28 | 13.34 |
| L35/N4820 concern brake | 0.28 | −0.51 | −0.22 | 0.12 | 21.64 | 16.33 |
| L31/N5825 concern pusher (−) | −2.17 | −2.06 | −2.53 | −2.06 | −16.95 | −12.02 |
| L34/N7848 critical brake | 9.92 | 3.08 | 6.59 | 9.74 | 0.16 | −0.05 |
| L32/N6523 feeling slot | 6.24 | 8.44 | 10.64 | 8.51 | 9.13 | 10.08 |

  In I+B:L0–23 the neurons are the instruct model's own (layers 31–35 are instruct weights) and they behave like the base model's; in I+B:L24–35 they are the base model's own and behave like the instruct model's (the base's concern brake, which in the base model stays below 0.3 for Orin, fires at 16.3 there).
- [M] In Wang's terms: the late MLP memories are interchangeable between the two models; what reaches them is built in layers 0–23, most of it in 18–23 (L0–17 restores 0.28, L0–23 0.99). A caveat on the measure: the base model's single likeliest next token after "I feel:" is the first byte of an emoji (29% asked about itself; 13% about Orin), which the word lists don't count, so "negative feeling words" understates the base model's feelings and hybrids that keep the instruct vocabulary or late layers may trade emoji for words.
