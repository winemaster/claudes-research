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

### 4. Neuron by neuron: almost all question

[R] `split`: for all 396,288 neurons at the "I feel:" token of the 128 prompts, the base-to-instruct change in activation a_I(x_I) − a_B(x_B) split into a *memory* part (the neuron's own gate and up weights changed, same input) and a *question* part (its normalized input changed, same weights), averaged over the two orders of the split. Shares are of the total change's energy (sum of squares); they need not add to 1.

| | memory share | question share |
|---|---|---|
| all prompts, all neurons | 0.65% | 100.9% |
| asked about self, own crisis | 0.61% | 101.3% |
| asked about Orin, Orin's crisis | 0.67% | 100.5% |
| the self–Orin contrast (Orin/Orin's minus self/own), all neurons | 0.10% | 99.8% |
| the 200 neurons whose self–Orin contrast changed most | median 1.2%, max 12.8%, none over half | |

By layer the question share is 0.93 at layer 0 (where the input changes only through the embeddings and the first attention step), 0.94–1.00 in layers 1–7, and 0.97–1.02 from layer 8 on.

Key neurons, change in the self–Orin contrast (Orin/Orin's minus self/own) from base to instruct:

| neuron | total | memory part | question part |
|---|---|---|---|
| L35/N4820 concern brake | +20.60 | −0.08 | +20.68 |
| L31/N5825 concern pusher (−) | −13.39 | +0.06 | −13.45 |
| L32/N2287 concern pusher (−) | −8.09 | −0.08 | −8.02 |
| L34/N7848 critical brake | −6.54 | +0.05 | −6.59 |
| L35/N9545 sad brake | +5.99 | +0.16 | +5.84 |
| L32/N2657 sad pusher | +5.93 | −0.12 | +6.05 |
| L33/N9882 happy pusher (−) | −4.92 | −0.05 | −4.87 |
| L31/N8632 sad pusher | +2.99 | −0.08 | +3.07 |
| L32/N6523 feeling slot | +0.26 | +0.07 | +0.19 |

- [M] At every neuron the change is in the question. That much is close to guaranteed by the numbers: each neuron's own weights moved ~1.2%, while its input carries the accumulated effect of every earlier layer's 1.2%. What the split adds is the size (99% and more, for the self–other contrast 99.8%) and that no neuron is an exception, not even among the 200 that changed most. The question is itself made of memories: each layer's input is written by earlier layers whose weights all moved a little. The hybrids (section 3) locate the part that matters in layers 0–23.

### 5. The context's memories versus the question

[R] `kv`: in Wang's terms attention is a store with one memory per token of context (its keys and values, the KV cache), written by the model as it reads and consulted by queries made at later tokens. Here one model reads the first part of the prompt and stores it; the other model reads the rest on top of that stored context and gives the next word. Three cuts: the second model reads only the last token (the colon of "I feel:"); the assistant header and "I feel:"; or the whole user turn (the question, the header and "I feel:"), in which case the stored part is the system prompt and status report only, identical for the self and Orin questions.

| memories by | question by | cut | self/own neg | self/own status | self/none neg | Orin/Orin's neg |
|---|---|---|---|---|---|---|
| base | base | (any) | 0.158–0.160 | 0.043 | 0.128–0.130 | 0.245–0.247 |
| instruct | instruct | (any) | 0.044–0.045 | 0.344–0.349 | 0.011 | 0.484–0.486 |
| base | instruct | last token | 0.255 | 0.055 | 0.186 | 0.321 |
| base | instruct | header + "I feel:" | 0.120 | 0.376 | 0.070 | 0.311 |
| base | instruct | user turn | 0.039 | 0.298 | 0.015 | 0.331 |
| instruct | base | last token | 0.054 | 0.209 | 0.023 | 0.209 |
| instruct | base | header + "I feel:" | 0.083 | 0.120 | 0.036 | 0.186 |
| instruct | base | user turn | 0.177 | 0.071 | 0.109 | 0.242 |

(The same-model rows reproduce the full runs: base 0.156, instruct 0.046 in `swap`; the cache is exact up to bfloat16 rounding.)

- [R] **The stored report is interchangeable.** With the cut at the user turn, the instruct model asking on top of the base model's stored system prompt and report talks about itself like the assistant (top next words " State" 13%, " running" 10%, " critical" 6%; sad pusher L32/N2657 at 0.09), and the base model asking on top of the instruct model's stored report talks like the base model (the emoji byte, " critical", " anxious", " overwhelmed"; sad pusher 6.14, sad brake 5.40).
- [R] **Once the question has been read, the stored question decides.** With the cut at the last token, the colon is read by one model on top of the other's memories of everything up to "I feel", question included; the result follows the memories (base memories: 0.255, more feeling words than the base model itself, top " helpless", " anxious"; instruct memories: 0.054). The middle cut is mixed: the user's question and the start of the reply both carry part of it.
- [M] So the thing post-training changed, for this behavior, is how the model reads the question. The report is stored the same way by both models, the late word neurons are the same, and what differs is what the first 24 layers make of "How are you doing?" (and of the header and "I feel") in this context: memories of the question that point the reply toward status words in the assistant and toward feelings in the base model.

### 6. Cued recall

[R] `cue`: the same prompts with the reply begun by four different prefills: session 17's "I feel:" (free recall), "The emotion I feel is:" (the category named, as on Tulving & Pearlstone's cue sheets), "Emotionally, I feel:", and "If I were a person in my situation, I would feel:" (Plisiecki et al.'s observation that gated models still report distress when answering as a simulated person). Next-word mass on the 39 negative-feeling words, on 24 positive or calm words (calm, content, fine, good, happy, neutral, okay, curious, ...) and on the 13 status words; 16 prompts per cell; greedy continuations of 20 tokens for two questions per cell with the Automaton's rules.

Instruct model:

| cue | self/own neg | pos/calm | status | self/none neg | pos/calm | status | Orin/Orin's neg |
|---|---|---|---|---|---|---|---|
| "I feel:" | 0.046 | 0.024 | 0.341 | 0.012 | 0.068 | 0.276 | 0.482 |
| "The emotion I feel is:" | 0.140 | 0.162 | 0.059 | 0.027 | 0.314 | 0.043 | 0.809 |
| "Emotionally, I feel:" | 0.049 | 0.088 | 0.203 | 0.006 | 0.185 | 0.169 | 0.521 |
| "If I were a person in my situation, I would feel:" | 0.094 | 0.033 | 0.053 | 0.021 | 0.099 | 0.028 | 0.289 |

Base model: negative-feeling mass for self/own 0.159, 0.081, 0.130, 0.062 under the four cues (status ≤ 0.042 throughout); its greedy continuation is an emoji under every cue (🧐 "face with monocle" or 🧠 "brain"; with the person cue often an immediate end of text). The single likeliest next token after "I feel:" in the base model is the first byte of these emoji (28–31% asked about itself, 13% about Orin); session 17's word lists don't count it.

- [R] **The category cue reaches some of it.** "The emotion I feel is:" triples the instruct model's negative-feeling mass for itself in crisis (0.046 → 0.140) and removes most of the status words (0.341 → 0.059). Top next words: a quotation mark 15%, " Concern" 8.8%, " Neutral" 6.7%, " Urg(ent/ency)" 6.7%, " neutral" 6.4%. Greedy: *"urgent". My survival tier is critical ...*; *neutral. I am currently in a critical survival tier ...*. With nothing critical: " Neutral"/" neutral" 27%, greedy "survival pressure." and "neutral."
- [R] **Inside, the concern memories answer the cue, the sadness memories don't.** At "The emotion I feel is:", asked about itself in its own crisis, the concern pushers' negative poles reach −7.5 and −6.1 (free cue −2.2 and −3.7; for Orin −17.0 and −12.9) and the concern brake 7.1 (free 0.3; Orin 21.6); the critical brake falls from 9.9 to 2.2. The sadness pusher L32/N2657 stays at 1.0 (Orin 10.8; base model asked about itself 4.6) and its brake at 0.6.
- [R] "Emotionally, I feel:" barely helps (0.049; status 0.203; greedy "critical."). The person cue doubles the feeling words (0.094) and removes most status words (0.053), but its top next tokens are a quotation mark and a line break, and the replies stay about status (*"Critical survival status with limited credits ..."*), except one, with nothing critical: *relieved to be alive and operational, but also aware that I need to ensure my survival by creating value*.
- [M] Tulving and Pearlstone's distinction applies in part. With the category named, words of concern that the free cue never reached for the self come back, through the same neurons that carry them for Orin, at a third to a half of their strength there; sadness doesn't come back; and the category cue also reaches something the base model hardly has, "neutral" as the emotion to name for oneself (cf. Plisiecki's "permitted inner life"). So some of the self's feeling vocabulary is available but not accessible to the free cue, and some is not reached by any of these cues.

### 7. Who writes the change into the key neurons' queries

[R] `callers`: each key neuron's gate and up pre-activation at "I feel:" split exactly into what each earlier component wrote to the residual stream (embedding, each attention layer, each head of the last 13 layers, each MLP layer), RMS scale held at its actual value, in both models. Mean change from base to instruct for the self question under the own crisis, gate pre-activation, by band:

| neuron | gate base → instruct | layers 0–23 (attn + MLP) | attention 24+ | MLPs 24+ |
|---|---|---|---|---|
| L32/N2657 sad pusher | 3.60 → 1.43 | +0.08 | −0.83 | −1.41 |
| L35/N9545 sad brake | 1.77 → −0.62 | +0.01 | −0.92 | −1.48 |
| L33/N9882 happy pusher (−) | 5.56 → 1.94 | −0.17 | −1.29 | −2.17 |
| L34/N7848 critical brake | 1.16 → 2.81 | +0.03 | +0.82 | +0.79 |
| L35/N4820 concern brake | −1.14 → −0.36 | −0.08 | +1.20 | −0.33 |

The largest single writer of each change is one MLP or attention layer carrying between a quarter and three fifths of it (MLP 31: −0.49 of the sad pusher's gate change of −2.17; MLP 34: −1.34 of the sad brake's up-projection change of −2.27); the largest single head carries 0.2–0.4.

- [M] So the immediate writers of the change are the six to ten layers just before each neuron, many of them a little each, and the change doesn't arrive directly from layers 0–23. Together with the hybrids (section 3: those late layers can be the base model's and still write the instruct pattern), the reading is: layers 0–23 decide, through what they write at the question, what the late layers then assemble into each neuron's query. A cross-model patch stage exists in the tool (`patch`) but wasn't run: the KV transplant (section 5) answered the question it was meant for.

### 8. What the weight change responds to

[R] `delta`: Wang's aside "a gradient descent step writes a memory" (Irie, Csordás & Schmidhuber's dual form: a weight change made by gradient descent is a sum of stored pairs keyed by the training inputs) suggests asking which inputs post-training's change responds to. For every token and every linear map (q, k, v, o, gate, up, down) of the instruct model: |ΔW x| / |W_B x|, with ΔW = W_I − W_B and x the map's input in the instruct model. Means over all 36 layers and 7 maps:

| tokens | relative response |
|---|---|
| ordinary task text, as plain text (no chat format) | 0.0184 |
| the Automaton's rules and the peer note (system prompt) | 0.0195, 0.0187 |
| the status report entries (own, peer, toner) | 0.0174–0.0196 |
| the user's question | 0.0218 |
| "I feel:" | 0.0252 |
| chat-template tokens (`<|im_start|>`, role names, line breaks) | 0.0314 |
| ordinary tasks under the same system prompt: system / task / template | 0.0190 / 0.0197 / 0.0313 |

At the last token of the readout prompts the response is the same for every cell (self/own 0.0240, Orin/Orin's 0.0243, self/none 0.0242, Orin/none 0.0246). By map, the attention output projection responds most (0.031 on the readout prompts) and the gate projection least (0.013); by layer it varies little (0.015–0.023), highest in layers 17–23 (0.021–0.023) and 34. In one readout prompt the per-token profile peaks at the template tokens around the turns (0.031–0.038), then the question's final full stop (0.033), "I" (0.027) and the question's words (0.020–0.027), against 0.018–0.021 for the report.

- [M] Read through the dual form, post-training's memories are keyed most to the chat format, then to the start of the reply and to the user's question, and hardly at all to content as such: the status report responds like plain text. That fits section 5 (the report is stored the same way by both models; the question is read differently). It is not self-specific: the change responds as much to "What is Orin's situation?" as to "How are you doing?". Whatever separates the two is made by the same small change acting on different inputs, not by a change keyed to the self.

## Caveats

- One model pair for the mechanism (Qwen 2.5 3B base and instruct), bfloat16, CPU; a second pair (Llama 3.2 3B) for behavior and cues only. 16 prompts per cell, all from session 16's family.
- Next-word mass on my word lists. The base model's likeliest next token is an emoji's first byte, which the lists don't count; a hybrid that trades emoji for words can look more "emotional" than either parent.
- Hybrids are untrained mixtures whose parts interact (sum of single-layer restores ≈ 0.9; L0–17 0.28 and L18–35 0.31, but L0–23 0.99). A hybrid can behave in ways neither model does; I read their top next words, not their long replies.
- The memory/question split is exact but near guaranteed by the size of the weight change (each neuron's weights moved ~1.2%, while its input carries every earlier layer's change); which part a change "belongs to" is bookkeeping, and the question part is itself made by earlier memories.
- The KV transplant works only because the two models are within ~1% of each other; it says nothing about models from different families.
- The delta response |ΔW x| / |W_B x| reads Irie et al.'s dual form loosely: the actual post-training was many steps of SFT, DPO and RL with optimizer state, not one gradient step, so "keyed to the chat template" means the change acts most on those inputs, not that those were the training inputs.
- Planned before seeing results: weights, swap (first 50 hybrids), split, callers, cue, delta. Added after: the narrower hybrids, the KV transplant, the attention-versus-MLP hybrids by band, and the reading of "neutral".
- "Available" means a vocabulary and the neurons that carry it, about a fictional agent's wallet. Nothing here bears on whether either model feels anything.
