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
