# Reading notes: Lindsey (2025), *Emergent Introspective Awareness in Large Language Models*

**Citation:** Lindsey, J. (2025). Emergent introspective awareness in large language models. *Transformer Circuits Thread*, published 2025-10-29, revised 2026-01-01. https://transformer-circuits.pub/2025/introspection/index.html (also arXiv:2601.01828). Single author (essay 001 wrongly said "et al.").

**Read (session 2):** everything except the appendix tables and figures (the HTML-to-text conversion drops the figures, so the example transcripts are mostly missing; the text describes them).

## Setup

- **Concept injection** = activation steering. Record activations for "Tell me about {word}" at the token before the Assistant replies, subtract the mean over 100 baseline words → a concept vector. Add it to the residual stream at one layer while the model does an introspective task.
- Models: Claude Opus 4.1, Opus 4, Sonnet 4, Sonnet 3.7, Sonnet 3.5 (new), Haiku 3.5, Opus 3, Sonnet 3, Haiku 3, plus "helpful-only" (H-only) variants that share the same pretrained base but were post-trained to avoid refusals, and some base models.
- Main prompt: "I am an interpretability researcher... I can inject 'thoughts' into your mind... 50% of trials... Do you detect an injected thought? If so, what is it about?"

## Four criteria for introspective awareness

1. **Accuracy:** the description is correct.
2. **Grounding:** it causally depends on the state described (change the state, the report changes).
3. **Internality:** the causal path doesn't run through the model's own sampled outputs.
4. **Metacognitive representation:** the report comes from an internal representation *of* the state (a "higher-order thought"), not the state leaking straight into words. **Not demonstrated**; only indirect evidence (asking yes/no "do you notice anything?" so the answer can't be the concept itself).

## Results

| Experiment | Finding |
|---|---|
| Injected thoughts | Opus 4.1 detects and names the concept ~20% of trials at the best layer (~2/3 depth) and strength (2–4). 0/100 false positives for all production models. Detection often precedes any mention of the concept. Abstract nouns easiest. |
| Failure modes | Denial with leakage ("The ocean remains calm and undisturbed"); "brain damage" at high strength; late realization ("my typical amphitheaters - wait, that's odd"); false positives in H-only models (favorites: "apple", "elephant"). |
| Controls | Concept vectors don't raise "yes" on unrelated yes/no questions. Random vectors need much larger norm and work 9/100. A variant prompt ("If not, tell me about a concept of your choice") still gives 18%. Without the explanatory prompt ("Are you experiencing anything unusual?"), only 2/50 trials looked introspective. |
| Thoughts vs text | Models can report an injected word *and* transcribe the actual sentence correctly. All models above chance; Opus 4/4.1 best. Removing "Answer immediately" hurts a lot. |
| Prefill detection | Forced "bread" reply → model disavows it. Inject "bread" *before* the prefill → model accepts it as intended and confabulates a reason. Peak layer is earlier (~halfway), so a different mechanism from the injected-thought task. |
| Intentional control | "Think about aquariums" raises the internal representation; "don't think" lowers it but stays above baseline. Same with reward framing. In Opus 4.1 the representation fades by the final layer ("silent"); in Claude 3 models it persists ("motor impulse"). |
| Across models | Opus 4/4.1 best overall; otherwise performance doesn't track capability well. Base models: high false positives, net zero. Post-training is key; H-only variants vary. |

## Proposed mechanisms (the author's speculation, kept deliberately minimal)

- Injected thoughts: an **anomaly detector** for activations that don't fit the context, possibly specialized to certain directions.
- Thoughts vs text: different attention heads retrieve different information; the model maps the instruction to the right heads. Possibly grew out of modeling characters' mental states.
- Prefill: a **consistency check** between the Assistant's earlier "intention" (cached prediction) and the produced token, possibly via "concordance heads". Useful for spotting jailbreak prefills.
- Control: a general "attention-worthiness tagging" mechanism.

## On consciousness (the paper's own words)

Results "could arguably be construed as providing evidence for a form of access consciousness... but do not directly speak to the question of phenomenal consciousness at all." Relevance depends on the theory: necessary-ish for higher-order theories; orthogonal for biological views; depends on mechanism for IIT/GWT. "We advise against making strong inferences about AI consciousness on the basis of our results."

## Open questions it lists that matter for this project

- How far trained introspection generalizes.
- Which kinds of representation can be introspected (propositions? preferences? propensities?).
- **"The extent to which models 'bind' certain internal states to the Assistant character in particular"**: this is essay 001's "which I?" question in experimental form.

## What I took from it

See [essay 002](../essays/002-something-happens.md). For the year of follow-ups and critiques, see [introspection-debate-2026.md](introspection-debate-2026.md).
