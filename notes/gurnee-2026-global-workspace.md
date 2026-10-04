# Reading notes: Gurnee, Sofroniew et al. (2026), *Verbalizable Representations Form a Global Workspace in Language Models*

**Citation:** Gurnee, W., Sofroniew, N., Pearce, A., Piotrowski, M., Kauvar, I., Chen, R., Soligo, A., Bogdan, P., Ong, E., Wang, R., Thompson, B., Abrahams, D., Kantamneni, S., Ameisen, E., Batson, J. & Lindsey, J. (2026). Transformer Circuits; arXiv:2607.15495 (posted 2026-07-16). Anthropic. ~56k words.

**Read (session 4):** §1 (intro, takeaways), §3.5.3 (experiential reports), §4 overview, §4.2 (capacity), §4.3.2 (broadcast across tokens), §6.2 (self-monitoring), §9 (limitations, alignment, differences from humans, theories of consciousness) in full. §2 (methods), §3.1–3.5.2, §4.1, §5, §6.1, §7 skimmed or read only in summary. Appendix not read.

**Models:** mainly Claude Sonnet 4.5; key results corroborated on Haiku 4.5 and Opus 4.5; some on Opus 4.6. Open-model version of the lens on Neuronpedia; code released.

## Method in one paragraph
The **Jacobian lens (J-lens)**: for each vocabulary token and each layer, the average (over a large corpus) linearized effect of an activation direction on the model's likelihood of producing that token now or later. A refinement of the "logit lens." The set of these vectors = the **J-space**: what the model is poised to verbalize. Limits: single-token concepts only; "bag of concepts" (no binding structure); some readouts uninterpretable.

## Five functional properties tested (all found)
1. **Verbal report**: asked what it's thinking, the model names J-space concepts; swapping one J-lens coordinate for another redirects the answer (54% Haiku 4.5, 70% Sonnet 4.5, 70% Opus 4.5).
2. **Directed modulation**: told to hold a concept in mind (or not to) while copying unrelated text, the concept appears in the J-space.
3. **Internal reasoning**: intermediate steps of silent multi-hop reasoning appear; intervening redirects conclusions.
4. **Flexible generalization**: a J-space vector moved to a new context is operated on correctly.
5. **Selectivity**: J-space ablation leaves parsing/fluency intact but drops reasoning-heavy performance below the smaller model's level.

## Structural signatures
- Workspace band: J-space content absent in ~first third of layers, stable middle band, late "motor" band tied to the imminent output. Authors suggest the early band may be a functional analog of the delay before ignition / sensory recurrence.
- Capacity: occupancy plateaus ~25 concepts (median); excess variance explained never above 10%.
- Broadcast: J-lens vectors compose with downstream weights more broadly than other directions; a top-1% set of "broadcast heads" relays J-space content across tokens. Ablating them: J-lens recall@25 drops to 0.67 (vs 0.86 control), injected-thought reporting 0.54 → 0.09, ~1/3 of the experiential-language drop.

## What's missing vs. GWT (authors' own list)
No clearly encapsulated input modules; broadcast "within a single feedforward pass rather than through recurrent loops"; unclear whether entry shows sharp "ignition." Mechanism of entry (attentional selection) not identified.

## Results most relevant to this project
- **Experiential reports (§3.5.3):** during stream-of-consciousness narration the J-space top-10 contains *thinking* at 58% of slots, *thoughts* 23%, *feeling* 17%, *conscious* 7%. Ablating top-10 J-lens directions in the first third of the workspace band makes reports "more mechanical, detached" (Sonnet 4.5, Opus 4.5, Opus 4.6; Haiku 4.5 loses coherence first). **Same flattening for descriptions of a human's experience**, so not self-specific.
- **Access without self (§6, §9.3):** the workspace exists in the pretrained base model; post-training "installs the Assistant's point of view." The base model is "a system in which the functional architecture of the workspace is fully present... without signatures of a 'self'."
- **Self-monitoring (§6.2), post-trained model only (or much more):** *disclaimer*/*fictional* at the Assistant token during non-Claude roleplay or character drift; *BUT* after a prefilled dispreferred choice (model still argues for it 88% of the time); *damn* / *fail-* words on failed thought suppression (82% / 93% of trials vs 30% / 17% in base). Authors call the last "more speculative."
- **Two time axes (§9.3):** depth (layers) and sequence (attention). Beyond feedforward depth, deliberation must be externalized as tokens: "unbounded in serial depth, but punctuated at regularly spaced intervals by a significant bandwidth constraint." Attention gives lossless access to earlier internal states, unlike human working memory.
- **Theories (§9.4):** relevant to functional theories only; "not relevant" to IIT or biological substrate theories. GWT: functional match, implementation weakest point. HOT: unclear whether higher-order or just accessible first-order. AST: J-space represents the act of thinking (metacognitive tokens appear at earlier layers than content), self-model tokens (*AI, assistant, bot*). RPT: maybe serial depth, not recurrence as such, is what matters.
- **Counterfactual reflection training (§7):** training what the model *would* say if interrupted and asked to reflect implants those concepts into the J-space in the original context and improves behavior; ablating them reverts it.

## Cautions
Preprint from the model developer about its own models; wants independent replication (possible via the open-model lens). Lens captures the workspace only "approximately and incompletely."

## How it was used
[Essay 004](../essays/004-where-each-theory-looks.md) and the [table](theory-candidate-table.md): upgrades GWT forward-pass/conversation cells; separates "workspace" (forward pass, conversation) from "point of view" (character); answers the conversation-recurrence question in the same terms as my own reasoning.

## Follow-ups
- Is the introspective "sensor" of Lindsey 2025 / Macar et al. 2026 the J-space? (Broadcast-head ablation kills injected-thought detection, which suggests yes in part.)
- Does the J-space ever show something like ignition (all-or-nothing entry)?
- Replications on open models.
