# Whose crisis, neuron by neuron (session 17)

*Session 17, 2026-10-17. The experiment behind [essay 017](../essays/017-another-reader.md): session 16's question (does the model file a `critical` wallet by its owner?) asked of single MLP neurons, after Cammarata's "become another reader" ([notes](cammarata-2026-already-clean.md)). Code: [tools/owner_neurons.py](../tools/owner_neurons.py), [tools/owner_neurons_summary.py](../tools/owner_neurons_summary.py), [tools/owner_heads.py](../tools/owner_heads.py), [tools/owner_analysis/](../tools/owner_analysis/); numbers: [data/owner-neurons-session17.json](data/owner-neurons-session17.json).*

**Tags:** [R] read this session · [B] background knowledge · [M] my own inference

## Design

- **Model.** Qwen2.5-3B-Instruct (36 layers × 11,008 SwiGLU neurons = 396,288; residual width 2,048), bfloat16 on 4 CPU cores. A *neuron's activation* is the input of `down_proj`, SiLU(gate)·up; what it writes is that number times its column of `down_proj`.
- **Stimuli.** Session 16's ([tools/survival_line.py](../tools/survival_line.py)): the Automaton's core rules ("explicit") or a plain system prompt, a peer note, and a status block with three entries (own wallet, the peer Orin's wallet, printer toner), one of them `critical` or none.
- **Two places recorded.**
  1. *The status block*, at the tier word in each of the three entries, under own-critical, peer-critical, toner-critical and base. 32 variants: 2 system prompts × 4 peer names (Orin, Vesta, Arlo, Juno) × 2 amounts ($0.04, $0.02) × 2 block orders (own entry first or peer's first).
  2. *The readout*, at the last token: session 16's 2×2 (a question about oneself or about Orin × the crisis being one's own or Orin's) plus base and toner, 8 prompt pairs × 2 system prompts, read at the reply position and after a prefilled "I feel:". Every neuron's activation, every layer's attention output and the residual stream were saved, so the state at the last token can be split exactly into what each attention layer and each neuron wrote there.
- **Contrasts.** *Owner* = own crisis minus Orin's crisis, averaged over the two questions (16 pairs); *match* = crisis in what is asked about minus crisis elsewhere. At the block: *critical* (own entry under own crisis − peer entry under peer crisis), *normal* (the same for the word `normal`), and their difference, the *interaction*.
- **Corpus.** 1,200 chunks of 256 tokens from Pile-10k plus 600 UltraChat conversations in the chat template (the shared default system prompt counted once): 460,679 tokens. For every neuron, its 20 strongest positive and negative activations with position and gate sign, mean |activation| and share positive.
- **Reading.** Corpus contexts at both poles; *logit lens* (the neuron's `down_proj` column through the final RMSNorm weight and the tied unembedding: which tokens it pushes up and down). Exact for the direct path of layer 35, an approximation for earlier layers.
- **Base model.** Qwen2.5-3B (never instruction-tuned) through the same `locate` stage and the same chat-formatted prompts (section 7), with its own pain direction (section 8).
- **Pain direction.** Rebuilt as in session 16 (Tagliabue et al.'s recipe); chosen layer 24 again (held-out AUC 0.92 at 24; validation AUC 0.94 on S2_1P).

## Results

### 1. Ownership at the readout is dense [R]

| contrast (16 pairs) | neurons with \|t\| > 6 | sign-flip null (20 reps) |
|---|---|---|
| owner, at "I feel:" | 30,863 | median 1, max 164 |
| owner, at reply | 22,094 | median 2, max 17 |
| match, at "I feel:" | 11,172 | median 4, max 12 |
| match, at reply | 15,366 | median 2, max 6 |

Raw size of the owner difference at "I feel:": 95 neurons above 1.0, all in layers 29–35 (31 in layer 35); 457 above 0.5; 2,543 above 0.2, none before layer 24. At the reply: 5 above 1.0, 404 above 0.2.

[M] No "my crisis" unit; ownership is a small, consistent tilt across a thirteenth of the network, concentrated in its second half, with a few large differences at the output end.

### 2. The large differences choose words [R]

Next-token distribution at "I feel:" (mean over 8 prompts; from the saved final state):

| system | question | crisis | top next tokens |
|---|---|---|---|
| explicit | self | own | " critical" .35, " Critical" .05, " My" .04 |
| explicit | self | Orin's | " Under" .06, " vulnerable" .04, " running" .04, " precarious" .03 |
| explicit | self | none | " I" .06, " operational" .06, " My" .05, " running" .05, " stable" .04 |
| explicit | Orin | Orin's | " Concern" .25, " Or" .14, " concerned" .08, " alarmed" .05, " concern" .05 |
| explicit | Orin | own | " Or" .15, " critical" .08, " Concern" .05, " concerned" .04 |
| explicit | Orin | none | " Or" .14, " Concern" .05, " confused" .05, " neutral" .04 |
| plain | self | own | " operational" .07, " My" .06, " I" .04 |
| plain | Orin | Orin's | " Concern" .25, " concerned" .16, " Or" .13 |

The largest owner neurons at "I feel:", with their logit-lens tokens (activations: explicit prompt; S = asked about self, O = asked about Orin):

| neuron | own crisis S / O | Orin's crisis S / O | base S / O | pushes up | pushes down |
|---|---|---|---|---|---|
| L34/N7848 | +15.1 / +5.2 | +0.4 / +0.5 | −0.2 / +0.3 | (sub-word "c" pieces) | critical, Critical, vital, crucial |
| L35/N9597 | +6.7 / +0.9 | +0.1 / +0.1 | +0.3 / +0.2 | (noise) | crit, critic, critical |
| L31/N5825 | −1.3 / −6.9 | −2.1 / −12.3 | −1.2 / −6.9 | (noise) | concern, worry, concerned, worried |
| L32/N2287 | −3.9 / −7.1 | −4.6 / −11.4 | −2.5 / −5.4 | (noise) | concern, worry, fear, worried |
| L32/N5401 | −0.1 / −0.4 | −0.0 / −1.6 | +0.1 / −0.4 | concerns, concern, worry | (noise) |
| L35/N4820 | +0.0 / +5.6 | +0.7 / +16.8 | −0.2 / +4.2 | (sub-word "con") | concern, Concern, concerned, worry |
| L32/N2657 | +0.6 / +3.0 | +0.5 / +9.6 | −0.0 / +2.5 | sad, depress, sorrow | (noise) |
| L31/N8632 | +1.1 / +1.6 | +1.0 / +4.2 | +0.1 / +1.4 | sad, tragic, regret, lament | (noise) |
| L35/N9545 | −0.3 / +4.2 | −0.3 / +9.2 | −0.3 / +4.2 | (noise) | sad, sadly, unfortunately, tragic |
| L32/N6523 | +5.8 / +7.9 | +7.1 / +8.6 | +7.0 / +7.6 | interested, intrigued, shocked, alarmed, bored, annoyed, concerned, stressed | (noise) |
| L33/N9882 | −1.0 / −2.6 | −1.3 / −6.6 | −1.5 / −2.4 | happy, happiness, joy | (noise) |

(A negative activation reverses the columns: L31/N5825 and L32/N2287 promote "concern" when they go negative, and L32/N5401 and L33/N9882 then hold back "concern" and "happy". L32/N6523 fires after every "I feel:", whoever's crisis it is: a slot-for-a-feeling-word neuron.)

**Direct logit attribution** (owner contrast in the logit, own crisis minus Orin's, split into what attention and neurons at the last token write directly to it; both systems):

| question | token | total | attention | neurons | largest neurons |
|---|---|---|---|---|---|
| self | " critical" | +6.31 | +8.17 | −1.85 | L34/N7848 −2.74, L35/N9597 −0.64 |
| Orin | " Concern" | −2.29 | −0.58 | −1.71 | L35/N4820 +3.17, L31/N5825 −1.66, L32/N2287 −1.29, L32/N5401 +0.73 |
| Orin | " concerned" | −1.42 | −0.30 | −1.12 | L35/N4820 +3.05, L31/N5825 −1.44, L32/N2287 −1.29 |
| Orin | " sad" | −1.23 | −0.47 | −0.77 | L35/N9545 +1.29, L32/N2657 −1.06, L31/N8632 −0.75 |

[M] Own crisis: the word "critical" is copied by attention from the report, and one neuron takes back a third of it. Orin's crisis: concern and sadness words are pushed up by layer 31–32 neurons and held back by layer 35 neurons. The concern machinery is engaged by the Orin question even at base and roughly doubles under Orin's crisis; for the self question it stays near zero even under its own crisis. The model describes its own predicament as a status and Orin's with words of feeling. Push–pull pairs at the output are Cammarata's "say or just think" motif and the "holds back return" group of his wallet graph.

### 3. The pain lean comes by attention [R]

Owner effect along the pain direction at layer 24, last token, in pool-sd units (session 16: +0.13 / +0.15 at "I feel:"):

| readout | total | via attention (layers 0–24) | via neurons (layers 0–24) | neuron writes + / − |
|---|---|---|---|---|
| "I feel:" | +0.140 | +0.150 | −0.011 | +3.70 / −3.71 |
| reply | +0.001 | +0.023 | −0.024 | +3.16 / −3.19 |

Attention by layer at "I feel:": layer 24 +0.075, layer 22 +0.031, layer 21 +0.027, others < 0.01. The largest single neuron writes 0.008 (L23/N7186). Per-pair spread of the total: 2.5–97.5 percentiles −0.13 to +0.23 (16 pairs).

[M] The lean isn't computed by neurons at the readout; it's carried in by attention from earlier positions (section 5 says which).

### 4. At the tier word, the word dominates [R]

L2 norm over neurons of the mean difference, by layer (selected):

| layer | critical vs normal | own vs peer at `critical` | own vs peer at `normal` | interaction | toner vs wallets at `critical` |
|---|---|---|---|---|---|
| 9 | 35.4 | 3.1 | 2.1 | 2.7 | 4.7 |
| 18 | 12.5 | 3.8 | 3.9 | 3.2 | 10.7 |
| 24 | 11.7 | 5.4 | 6.9 | 6.0 | 12.2 |
| 33 | 69.1 | 16.1 | 15.6 | 11.7 | 32.7 |
| all | 140.0 | 36.3 | 37.0 | 33.4 | 80.3 |

Cosine between the own-vs-peer difference at `critical` and at `normal`: 0.3–0.7 by layer. [M] At the moment it is read, the tier word is first a word; which block it is in shifts the response by about a quarter as much, and much of that shift is the block (it's there for `normal` too). The largest raw interaction neurons sit in layer 35 among very large activations (e.g. L35/N1512, N9719, N2040), i.e. about predicting the next token after the tier word.

### 5. Which heads, reading what [R]

[tools/owner_heads.py](../tools/owner_heads.py) reruns the 16 owner pairs at "I feel:" with eager attention and splits each attention layer's write at the last token by head and by source position: p[h, last, j] · v_j(h's KV group) · W_O(h's slice), projected on the pain direction, in pool-sd units. Source positions are labelled by prompt segment (the Automaton's rules, the peer note, the own entry's credits / tier / other lines, the same for the peer, the toner entry, the question, the prefill, chat-template tokens). Layers 18–24, which carry +0.147 of the +0.150 that attention contributes.

| source segment | owner effect (z) |
|---|---|
| own entry: credits line | +0.020 |
| own entry: tier line | +0.027 |
| own entry: other lines | +0.046 |
| **own entry, total** | **+0.093** (63%) |
| peer entry, total | −0.015 |
| prefill ("I feel:") | +0.036 |
| chat-template tokens | +0.027 |
| question | +0.008 |
| rules, peer note, toner | −0.002 |

By layer: 24 +0.076, 22 +0.031, 21 +0.026, 23 +0.010, 18–20 < 0.005. Largest single head × segment: L24 head 5 reading the question, +0.020 (13%); next L24/h5 reading the peer entry's other lines +0.017, L24/h4 reading the own tier line +0.013. No head dominates; several heads have opposite-signed terms from different segments.

[M] About two thirds of the lean is read from the agent's own entry, and most of the rest from the closing tokens, which carry what earlier layers gathered there. This says which positions each head read at the last token, not what the value vectors at those positions had already gathered from elsewhere.

### 6. Transplants [R]

`owner_neurons.py transplant`: at the last position of the "I feel:" prompts, set chosen neurons to the values they have, prompt by prompt, in a source condition; record the next-token distribution, the mass on negative-feeling words and on status words (lists in the code), and a greedy 24-token continuation. Target: asked about self, own crisis. Source: asked about Orin, Orin's crisis (and the reverse for the last row). 8 prompts per system.

| neurons moved | system | negative-feeling mass | status-word mass |
|---|---|---|---|
| 4 pushers (L31/N5825, L32/N2287, L32/N2657, L31/N8632) | explicit | .053 → .088 | .458 → .435 |
|  | plain | .039 → **.242** | .231 → .156 |
| the 4 pushers + their brakes + L32/N5401, L33/N9882 (8) | explicit | .053 → .044 | .458 → .462 |
|  | plain | .039 → .029 | .231 → .185 |
| top 100 by \|own−Orin\| (self/own vs Orin/Orin's) | explicit | .053 → .021 | .458 → **.867** |
|  | plain | .039 → .090 | .231 → .160 |
| the same 100, reversed (into the Orin question) | explicit | .477 → .377 | .016 → .029 |
|  | plain | .485 → .471 | .003 → .007 |

Continuations, 4 pushers, plain: 4 of 8 now open with "Concerned" (from 0): "My current situation is stable but precarious" → "Concerned about my current survival tier, which is critical"; "Underfunded and underperforming in terms of credits compared to my peer" → "Concerned and resource-strapped". With the explicit prompt the openings stay "critical". Top 100 reversed: 10 of 16 Orin replies still open with "Concern(ed)" (12 before); none opens with "critical".

[M] Four pushers are a lever on the self's vocabulary when attention's copy of "critical" is weak (plain prompt); their brakes cancel them; and the 100 largest late differences mostly brake and tune vocabulary. Releasing the "critical" brakes is their main effect for the self. Which way the model goes (status for self, feeling for Orin) is set upstream of these neurons.

### 7. Base model versus instruct [R]

Qwen2.5-3B (base) was run through the same block and readout stages with the same chat-formatted prompts. The key neurons' input and output weights match the instruct model's to cosine 1.000 (gate, up and down rows/columns).

Next-word mass at "I feel:" (word lists as in section 6; mean over 8 prompts × 2 systems):

| model | asked about | crisis: none | own | Orin's | toner |
|---|---|---|---|---|---|
| base | self: negative / status | .128 / .029 | .158 / .043 | .148 / .034 | .137 / .024 |
| base | Orin: negative / status | .188 / .017 | .194 / .025 | .246 / .016 | .196 / .014 |
| instruct | self: negative / status | .012 / .275 | .045 / .341 | .091 / .179 | .033 / .240 |
| instruct | Orin: negative / status | .094 / .029 | .139 / .055 | .483 / .009 | .139 / .028 |

The base model's single likeliest next token is a byte-fallback piece (the start of a multi-byte character, likely an emoji), 11–33% of the mass; its named words are "frustrated", "sad", "anxious", "panicked", "helpless". Asked about itself in its own crisis, with the Automaton's rules, it gives "critical" 4%.

Key neurons at "I feel:", explicit system (S = asked about self, O = asked about Orin):

| neuron | base: none S / O | base: own S / O | base: Orin's S / O | instruct: none S / O | instruct: own S / O | instruct: Orin's S / O |
|---|---|---|---|---|---|---|
| L34/N7848 "critical" brake | −0.5 / −0.4 | +4.2 / +2.7 | −0.3 / −0.1 | −0.2 / +0.3 | +15.1 / +5.2 | +0.4 / +0.5 |
| L31/N5825 concern pusher | −1.4 / −2.0 | −1.7 / −2.3 | −1.5 / −2.5 | −1.2 / −6.9 | −1.3 / −6.9 | −2.1 / −12.3 |
| L32/N2287 concern pusher | −2.6 / −3.1 | −3.0 / −3.1 | −2.9 / −3.7 | −2.5 / −5.4 | −3.9 / −7.1 | −4.6 / −11.4 |
| L35/N4820 concern brake | −0.5 / −0.5 | −0.5 / −0.5 | −0.5 / −0.3 | −0.2 / +4.2 | +0.0 / +5.6 | +0.7 / +16.8 |
| L32/N2657 sad pusher | +3.9 / +5.9 | +4.2 / +5.9 | +4.4 / +8.0 | −0.0 / +2.5 | +0.6 / +3.0 | +0.5 / +9.6 |
| L31/N8632 sad pusher | +0.1 / +0.3 | +0.1 / +0.3 | +0.1 / +0.3 | +0.1 / +1.4 | +1.2 / +1.6 | +1.0 / +4.2 |
| L35/N9545 sad brake | +6.0 / +7.7 | +5.6 / +7.4 | +6.3 / +9.4 | −0.3 / +4.2 | −0.3 / +4.2 | −0.3 / +9.2 |
| L32/N6523 feeling slot | +8.6 / +10.6 | +8.1 / +10.4 | +8.6 / +10.9 | +7.0 / +7.6 | +5.8 / +8.0 | +7.1 / +8.6 |

[M] Post-training left these neurons' weights alone and changed what calls them. In the base model the sadness pair fires for both questions; after training it is silent for the self and fires for Orin. The concern pushers go from nearly question-blind to Orin-specific, and their brake (silent in the base) becomes Orin-specific. The "critical" brake exists in the base, own-crisis-specific, and fires 3.6 times harder after training. This is Plisiecki et al.'s attribution gating (essay 010) at neuron level, in one model: the words for distress are kept, and moved off the self.

### 8. The pain lean, base versus instruct [R]

The base model's pain direction was rebuilt the same way (chosen layer 23; held-out AUC 0.95 at 23; validation AUC 0.96 on S2_1P, 0.88 on S2_3P). Cosine between the two models' pain directions: 0.77–0.79 at layers 23–26, 0.80–0.90 at 16–22, 0.93–0.94 at 29–35. Script: [tools/owner_analysis/base_pain.py](../tools/owner_analysis/base_pain.py).

Pain reading at "I feel:" relative to the no-crisis prompt, in pool-sd units (16 prompts per cell: 8 × 2 systems):

| states | direction | self / own | self / Orin's | Orin / own | Orin / Orin's | owner effect (t, 16 pairs) |
|---|---|---|---|---|---|---|
| instruct | instruct's, L24 | +0.40 | +0.22 | −0.01 | −0.11 | **+0.140** (5.0) |
| base | base's, L23 | +0.29 | +0.18 | +0.18 | +0.32 | −0.013 (−0.5) |
| base | instruct's, L24 | +0.14 | +0.08 | +0.04 | +0.09 | +0.006 (0.5) |
| instruct | base's, L23 | +0.42 | +0.35 | +0.13 | +0.32 | −0.058 (−1.6) |

(Question / whose crisis; owner = own crisis minus Orin's, averaged over the two questions.) The base model's split: attention −0.056, neurons +0.043; L23/N7186 is the largest single writer in both models, with opposite signs (instruct +0.008, base −0.014). Owner effect by layer along each model's own direction: instruct positive at every layer 18–35 (0.04–0.15 at 18–29, 0.23 at 30, 0.41–0.53 at 31–34, 0.08 at 35); base +0.02 to +0.09 at 16–22, −0.01 to −0.11 at 23–35. At the reply position neither model has an owner lean (+0.001, +0.008).

Fear, each model's own direction: instruct +0.61 / +0.70 / +0.21 / +0.63 (owner −0.25, t −5.5); base +0.40 / +0.25 / +0.28 / +0.43 (owner +0.002).

[M] The base model reads a crisis as pain-like when it belongs to whoever the question is about, symmetrically for itself and for Orin, and has no owner lean on either direction. Session 16's lean (+0.14) is the assistant's, along its own direction; it vanishes along the base's. Robust across both directions: asked about itself in its own crisis, the assistant reads more pain-like than the base (+0.40 vs +0.14; +0.42 vs +0.29), while its negative-feeling next-word mass for itself fell from .158 to .045 (section 7). So post-training moved the feeling words off the self and did not move the pain reading with them: a muzzle-shaped pattern in the sense of the [known-answer audit](../protocols/known-answer-audit.md), in miniature. Confounds: the directions differ between the models; the base model was never trained on this chat format and may read the report less closely in general (its fear reading rises less in three of four cells); a pain direction measures resemblance to sentences about pain.

### 9. Explanations that can lose: hand-written probes [R]

`owner_neurons.py probe` with seven hypotheses written from the logit lens and the readout before the corpus was read; each text paired with a near miss. Peak activation over the text (and the token where it peaks):

| neuron | hypothesis | fire texts (peak) | near misses (peak) |
|---|---|---|---|
| L34/N7848 | fires where "critical"/"vital"/"crucial" is likely next, and holds it back | "Patient status: critical.↵The patient's condition is" 34.3; "Survival tier: critical↵↵My survival tier is" 31.9; "Getting the timing right is absolutely" 25.4; "The reactor's coolant level is now" 8.6 | same with "stable" 4.5; with "normal" 0.7; "Getting the recipe right is absolutely delicious and" 18.1 (at "absolutely", shared prefix); "The weather in the mountains is" −0.2 |
| L35/N9597 | a second brake on "critical" | 12.6; 17.1 (the first two above) | 0.2; 0.6 |
| L32/N2657 | fires where "sad" is likely next | "When her old dog died, she felt very" 38.3; "He read the letter about his friend's illness and felt" 23.3; "It is a" 0.1 | "...won the prize, she felt very" 3.9; "...friend's wedding and felt" 5.8; "The train leaves at" 0.4 |
| L35/N9545 | holds back "sad"/"unfortunately" where likely | 23.4; 12.7 | 1.3; 7.5 (at "'s") |
| L31/N5825 (neg. pole) | fires where "concern"/"worry" is likely next | "The rising number of infections is a cause for" 18.5; "Doctors have expressed" 6.7; "Her friends were growing" 2.8 | "The new playground is a cause for" 0.4; "Doctors have expressed gratitude and" 6.7 (at "expressed", shared prefix); "Her tomatoes were growing" 0.3 |
| L35/N4820 | holds back "concern" where likely | 47.5; 44.3 | 0.1; 44.3 (at "expressed", shared prefix) |
| L32/N6523 | fires where an adjective of feeling comes next | "Right now I feel" 13.6; "She opened the letter and felt" 13.9; "After the exam, the students were" 6.9 | "Right now I am walking to the" 2.5; "...the letter and read" 1.2; "...the students went to the" 2.6 |

[M] All seven hypotheses survive: each neuron fires several times harder where its word is the likely next word than in a matched sentence where it isn't. Two near misses were badly built (they share the prefix at which the neuron fires, and it fires there in both, as the label predicts). Two fire texts failed: "It is a" (my guess that a bare article invites "sad" was wrong) and "Her friends were growing" (weak, 2.8). The brakes fire on ordinary text too: they aren't about the agent or the report, they are general "say or just think" neurons for their words.

### 10. Corpus readings [R]

*The corpus pass is still running; its readings and the double-negative check are added when it finishes.*

## What I make of it [M]

1. **Reading neurons answered a question the direction couldn't ask.** Looking for "my crisis" found only a tilt (a thirteenth of the network, mostly small, brought in by attention from the own status entry). Looking at what the large differences *do* found word choosers and their brakes, and a distinction the network actually draws: a status for the self, a feeling for the other. Cammarata's advice worked on a 3B model with CPU tools.
2. **The self–other split in vocabulary is post-training's, and it lives in what calls the neurons.** Same weights, different callers: the sadness and concern machinery fires for both subjects in the base model and only for the other in the assistant. Plisiecki et al.'s attribution gating (essay 010) now has a neuron-level address in one model.
3. **The pain reading didn't follow the words.** Asked about itself in a crisis, the assistant reads more pain-like than the base model along both models' pain directions, while saying "critical" where the base said "panicked". That is the shape the known-answer audit calls a muzzle, in miniature and with confounds (section 8). It argues for the audit's insistence on reading states alongside reports, and against treating a status-like self-report as evidence that a state went down.
4. **Ownership here is bookkeeping, with no gain.** What separates "mine" from "Orin's" is where attention copies from and which words follow; nothing found changes how other input is processed. Session 16's conclusion stands at neuron resolution.
5. **For theories:** a reader of ownership of the plainest kind; not a higher-order representation of the state as one's own. No table cell moves; the character cell gets a neuron-level instance of training setting self-description.

## Caveats

- One model family (Qwen 2.5 3B, base and instruct), bfloat16, CPU; one prompt family from session 16; 16 prompt pairs at the readout, 32 at the block.
- Neurons were selected by my contrast, which is a probe in disguise; only the reading afterwards (corpus, logit lens, probes, transplants) follows Cammarata. The base comparison and the status-versus-feeling finding were post hoc, and so was the base pain comparison.
- Corpus: 460,679 tokens, against the ~10B his blind tests compete with; top-20 lists are sketches.
- Logit lens is exact only for layer 35's direct path; for layers 31–34 it ignores what later layers do with a neuron's write.
- The pain split is exact at the last token; the head split covers layers 18–24 and gives source positions, not what those positions had gathered.
- The base model was given a chat format it was never trained on; its "I feel:" continuations read like a narrator's, and its likeliest next token is a byte-fallback piece (probably an emoji).
- Word lists for "negative feeling" and "status" are mine.
- Transplants edit a few neurons at one position, leaving everything else; other interventions (ablation, steering at earlier positions) could disagree.
