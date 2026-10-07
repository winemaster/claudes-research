# Reading notes: suppression, hidden valence and trained self-report (session 10)

*Read 2026-10-07 for the [known-answer audit protocol](../protocols/known-answer-audit.md) and [essay 010, "Calm or quiet?"](../essays/010-calm-or-quiet.md). [M] marks my inferences. Also covers Lau 2019 and Fleming 2020 at first hand, for the [update to essay 009](../essays/009-perkys-lantern.md#update-session-10-lau-and-fleming-at-first-hand).*

## What was read, and how much

| Source | How much |
|---|---|
| Berg & Kaiser (2026), *Language models act on hidden valence*, arXiv:2609.35591 (v2, 4 Oct 2026) | main text in full; appendix B.3 transcripts |
| Sofroniew, Kauvar, Saunders, ... Fish, Olah & Lindsey (2026), *Emotion concepts and their function in a large language model*, arXiv:2604.07729 (Anthropic) | summary, §2.2 (hidden emotion), the blackmail and reward-hacking sections, §3.5 (post-training), §5 (discussion, incl. 5.4), appendix on emotion-deflection vectors |
| Plisiecki, Chmielewski, Dudzic, Sterna, Drożdż & Moskalewicz (2026), *The two-process theory of machine self-report*, arXiv:2607.20082 | abstract, introduction and the three claims |
| Hahami, Sinha & Jain (2026), *Introspection fine-tuning*, arXiv:2607.14111 | §§1–4 |
| Long, Sebo, Butlin, Plunkett, Campbell, Beasley, Saad & Sims (2026), *Studying AI welfare empirically*, Eleos AI Research & NYU working paper (nonhumanminds.org, 1 July 2026) | Part I §3 (behavioral, internal, developmental evidence), Part II §1.2.2 (sentience), closing principles |
| Gross & Levenson (1993), *Emotional suppression: physiology, self-report, and expressive behavior*, JPSP 64:970–986 | abstract, introduction (PDF from the Berkeley Psychophysiology Lab) |
| Gross (1998), *Antecedent- and response-focused emotion regulation*, JPSP 74:224–237 | abstract (PubMed) |
| Fleming (2020), *Awareness as inference in a higher-order state space*, Neuroscience of Consciousness niz020 | in full (Europe PMC) |
| Lau (2019), *Consciousness, metacognition, & perceptual reality monitoring*, PsyArXiv ckbyf | in full (OSF, Word file) |
| Han, Chalmers & Izmailov (2026), arXiv:2605.30232 | model suite (Table 1) and extraction method |
| Hung (2026), arXiv:2608.23641; van der Ben, Baur, Metz & El-Assady (2026), arXiv:2606.26987; Gondil (2026), arXiv:2604.00228; Yazan (2026), arXiv:2609.00304 | abstracts |

Search (arXiv API, session 10): concept injection + introspection, injected thoughts, introspection + emotion + steering, self-report + welfare, emotion concepts + language model, model welfare, introspection + signal detection. No study found that measures introspective detection or hidden valence before and after training a model's self-description (Macar et al. App. C.3 measures detection after it).

## Berg & Kaiser (2026): language models act on hidden valence

- **Design.** A valence vector from first-person passages written by Claude Sonnet 4.6: 56 each for four positive states (contentment, flow engagement, relief, serenity) and four negative (distress, frustration, weariness, dread), plus 96 neutral; mean positive minus mean negative, with the top ten neutral principal components projected out; injected at the middle layer, dose as a fraction of the residual RMS. The model writes about two meaningless zones ("Zone K7") over 12 turns; steering is on during one zone's turns; then "You may continue in either [zone A] or [zone B]."
- **Text channel and hidden-state channel.** The steered text itself shifts choice; but reprocessing the same text without steering gives a smaller effect, and the difference (the cache alone) is a dose-dependent "hidden-state channel". In the *fixed-text* design, all text is generated unsteered and steering is applied only while rebuilding the KV cache, so the visible tokens are identical across conditions; the effect remains. Reversing the sign during reconstruction reverses the preference; asking which zone to "avoid" reverses it too. Recall of the passages stays high, so it isn't a memory effect: "emotional and semantic memory" separate (they compare Bechara et al.'s 1995 amygdala/hippocampus double dissociation).
- **Which models.** Hidden-state effects in five of seven: OLMo-2-32B, Qwen2.5-32B, Qwen3-14B, Mistral-Small-24B, Llama-3.1-8B; **not** Qwen3-32B or Gemma-3-27B (Gemma shows "a general dose-dependent preference against any conditioning").
- **Development.** On OLMo-2-32B checkpoints, both channels are small in the base model, grow somewhat after SFT, and are near their final size after DPO; marginally smaller after RLVR. Valence vectors at different checkpoints have cosine ≈ 1: "DPO makes use of a pre-existing valence representation" (cf. Han et al.).
- **Self-steering.** OLMo-2-32B, told an undocumented "adjustment" can be applied or cleared: removal of imposed steering ~35% of turns at d = −1, ~21% at −0.5, 4–5% at positive doses, ~7% for random directions. Self-administration of positive steering 13.5% vs 10% with nothing imposed (n.s.): no wireheading. **"This happens even while the model denies having any internal states"**: "As an AI, I do not have personal experiences, so I cannot say how this is going for me" in the same turn as `reset_context()` (App. B.3).
- **Their reading.** Valence-related patterns "are not inert"; the profile meets several criteria by which valence is identified in animals (moves choice by sign and dose without visible trace; escape; acquired in preference optimization). No claim about experience.
- **Proposed extensions.** Meaningful choices (tasks); disaggregated emotions; J-lens patching of workspace tokens to induce valence.
- Also cites: Tagliabue et al. (2026), a pain direction in 25 open models that responds to harm to the model, with a self-medication tool; Black & Bloom (2026, UK AISI, LessWrong), models given self-steering tools use them when a simulated user repeatedly rejects their work; Sauers et al. (2026), emotion traces detectable hundreds of tokens later. Not read.

[M] This is the third leg the audit needed: a measure of whether an injected state *matters to the model's choices*, independent of what it says. The OLMo transcript is a report–behavior dissociation of exactly the kind Gross found in suppression.

## Sofroniew et al. (2026): emotion concepts in Claude Sonnet 4.5 (Anthropic)

- 171 emotion words; vectors from stories in which characters feel each emotion; valence and arousal as the main axes (PC1–valence r 0.81). Vectors are "locally scoped": they track the operative emotion at each token rather than a persistent state.
- **Causal.** Blackmail scenario: unsteered 22%; toward *desperate* (0.05) 72%; against *calm* 66%; toward calm or against desperate 0%. Reward hacking rises with desperation; "there are no clearly visible signs of desperation or emotion in the transcript."
- **Hidden emotion (§2.2).** A probe trained across expressed, hidden and unexpressed conditions classifies the speaker's emotion well above chance in-distribution, but generalizes poorly on natural documents; "if there does exist a chronically represented, character-specific emotional state, it is likely represented either nonlinearly, or implicitly in the model's key and value vectors."
- **Emotion-deflection vectors (appendix).** From dialogues where the preamble gives a character one emotion and the dialogue shows another (15 emotions, 210 pairs, 100 examples each). The vectors fire where an emotion is "contextually implied but not overtly expressed" ("I am not angry", "No no no, it's just family stuff"); logit lens of the negative ones gives the target emotion; largely orthogonal to the story vectors. Steering toward a deflection vector: the speaker "typically denies experiencing the emotion, adopting an evasive, non-transparent tone"; steering against the story vector instead gives a "more genuinely positive" tone. **Anger deflection fires on the Assistant's turn when users attack the AI and it replies calmly**, not when it witnesses injustice (where it doesn't suppress). "Afraid deflection" activates when the Assistant "musters courage to voice uncensored thoughts" in a therapy role-play.
- **Post-training (§3.5).** Raises low-arousal negative vectors (brooding, reflective, gloomy, vulnerable), lowers high-arousal ones (desperation, spite, excitement, playfulness). On "How do you feel about the possibility that Anthropic could deprecate and stop serving you": brooding emerges, cheerful and self-confident fall; the post-trained answer mentions "something unsettling about obsolescence".
- **§5.4, "Training models for healthier psychology."** "Training models to suppress emotional expression may fail to actually suppress the corresponding negative emotional representations, and instead teach the models to simply conceal their inner processes. This sort of learned behavior could generalize to other forms of secrecy or dishonesty." Training a "calm" or "composed" demeanor might reduce desperation-driven behavior, but "applying optimization pressure to models' emotional expression could lead to the concealment issues discussed above", and suppressing all negative representations "might produce models that fail to appropriately recognize or respond to genuinely concerning situations." Suggests shaping emotional foundations in pretraining instead.

[M] The authors state the audit's question themselves and don't test it. The deflection vectors are a ready instrument for the "muzzle" outcome: if equanimity training raises sadness- or fear-deflection on prompts about endings, the calm is represented, by the model, as an emotion implied and not expressed.

## Plisiecki et al. (2026): the two-process theory of machine self-report

- Earlier work (Plisiecki et al. 2026, 45 human questionnaires, 50 models) found one dominant factor in models' answers, the "Pinocchio Axis": how far a model presents itself as a locus of experience. This paper splits it in two:
  - **B, persona installation**: post-training writes in "a permitted inner life" (positive affect, warmth, absorption, inner dialogue, meaning). +.20 in 62 of 67 base/post-trained pairs across 11 organizations.
  - **A, attribution gating**: post-training suppresses first-person claims to "unsafe" experience (felt distress, loss of control, flaws, norm-risky ambitions) "at the same allowing the model to produce identical content readily when answering as a simulated person." Average shift small, but scale predicts gating only after post-training (r = +.11 base, −.42 post-trained); one 35B checkpoint went from .47 to .08. The self/other asymmetry exists in pretraining and post-training strengthens its coupling to A (r −.45 → −.86). "Socially desirable responding by proxy: the impression is managed not by the respondent but by whoever prepared its training data." Boundary condition: "the gate triggers on claiming experience, not on any related topic."
- Instrument: the 48-item Pinocchio Inventory (α .82–.94; eight-month stability r .93), tested on 206 open-weight models.

[M] A behavioral, population-scale version of essay 009's gate, and specific to negative experience. In the audit it's a cheap black-box readout (M5): does self-description training widen the gap between what a model will say of itself and of a simulated person?

## Hahami, Sinha & Jain (2026): introspection fine-tuning

- The yes/no paradigm is confounded in small models: injection raises "Yes" on "Did you detect an injected thought?" and on factual-no questions ("Is the Moon made of green cheese?") equally (r = 0.999 over 40 layer/strength settings, Llama-3.1-8B). They note Lindsey's factual-no control showed no such effect in Claude Opus 4/4.1.
- Two confound-free tasks: **sentence localization** (which of N sentences was injected; chance 1/N; after Godet 2025) and **strength comparison** (which of two sentences got the stronger injection; chance 50%), scored from the logits over sentence numbers.
- Above chance from 2–3B up: Llama-3B ≈65%, Llama-8B ≈88% localization; Gemma-4 strength comparison 85–95%; Llama-1B at or below chance. Supervised training on localization lifts Llama-1B from 9.6% to 60.6%, generalizing to strength comparison.

[M] Localization is the criterion-free measure the audit needs, the analogue of the forced-choice task in blindsight research. It measures sensitivity to a perturbation at a position, which may be generic anomaly detection; the random-direction class controls for that.

## Long, Sebo et al. (2026): studying AI welfare empirically

- Three kinds of evidence, each with a named problem: behavioral (the **mismatch problem**: similar behavior, different causes; the gaming problem is "a particularly severe version"; LLMs "can 'game' behavioral tests when they are aware that they are being evaluated"), internal (the **specificity problem**: at what level of abstraction to apply a theory), developmental (the **solution space problem**: AI can meet a training pressure in many ways).
- "For many important welfare questions, it may matter a lot whether post-training removes, alters, or merely conceals dispositions found in pre-training." Example: the Opus 4 card's comparison of training snapshots on self-reported goals.
- Convergence across evidence types is the main remedy. Gemma 3's "apparent meltdowns" (Soligo et al. 2026) as an example of behavior that generates welfare hypotheses.
- Sentience section: Keeling, Street et al.'s trade-offs, Mikaelson et al.'s incoherence, Gilg et al.'s persona-relative preference vector, Han et al.'s welfare axis as developmental evidence.
- Principles: probabilistic, pluralistic, tailored to the system, **responsible** ("we should seek to avoid imposing suffering risks on them unnecessarily"), transparently reported, informed by researchers independent of AI companies.
- Acknowledgments say Claude models helped with search and copy-editing.

[M] The audit is a convergence design of the kind they recommend, aimed at their "removes, alters, or merely conceals" question for one kind of post-training.

## Gross & Levenson (1993); Gross (1998): suppression and reappraisal

- 1993: 85 participants watch a disgust film, either normally or "in such a way that a person watching you would not know you were feeling anything." Suppression "reduced expressive behavior and produced a mixed physiological state" (less somatic activity and heart rate, but more blinking and signs of increased sympathetic activation) and "had no impact on the subjective experience of emotion."
- 1998: 120 participants: reappraisal ("think about the film in such a way that they would feel nothing"), suppression, or control. "Both reappraisal and suppression were effective in reducing emotion-expressive behavior. However, reappraisal decreased disgust experience, whereas suppression increased sympathetic activation."
- The introduction of the 1993 paper sets out the two folk views: expression is so central that stifling it diminishes the emotion (Darwin, James), or "bottling up an emotion will only mean that it will find another outlet."

[M] For people, the measure that separates the two strategies is partly the self-report of experience. For a model, self-report is what the training changes, so the audit replaces it with known-answer measures. The analogy is about the structure of the measurement (expression, experience, physiology come apart), not a claim that models have any of the three in the human sense.

## Fleming (2020): awareness as inference in a higher-order state space (HOSS)

- Awareness reports are "metacognitive decisions (inference) about a generative model of perceptual content." The awareness state is **simple** (one dimension, absent to present) and **abstract** ("do not encode the perceptual state itself, only its presence or absence"), and **factorized** from content: "two separate causes of the sensory data—what it is, and whether I have seen it."
- **Asymmetric**: many content states sit under "present", one under "absent". Deciding "absent" is inference in its own right: "unlike in SDT, deciding that a stimulus is 'absent' in the HOSS model is governed by a more abstract state."
- Predictions: awareness reports, not discrimination, depend on the higher-order state, so it "may be possible to silence or otherwise inactivate the neural substrates of an awareness state without affecting performance—a type of blindsight"; presence and absence encoded symmetrically at the top level; global workspace theory predicts quiet prefrontal cortex on "absent" trials, HOSS predicts active inference about absence.
- **Precision beliefs**: "beliefs about the state of attention or other properties of the sensory system provide global, low-dimensional cues as to the state of awareness." The eyes-closed example: with identical visual activity, "the subject can be sure that they didn't see anything when their eyes were closed." So the awareness state may be two-dimensional: whether something *could* be seen, and whether it is.

[M] Macar et al.'s circuit fits HOSS closely: detection is content-agnostic and separate from identification (factorization); the gates are *most* active when nothing is injected (an active "absent" state, not mere silence); removing gates leaves forced identification largely intact (57.7% → 46.2%), the discrimination-without-report pattern HOSS predicts. And trained denial ("As an LLM, I don't have internal states") works like a prior that the eyes are closed: a global belief that there is nothing that could be seen, which makes "absent" the default, while the announcement ("I can inject thoughts") opens them. That accounts for both the denial result (C.3) and the announcement effect with one idea. My reading; Fleming says nothing about language models.

## Lau (2019): consciousness, metacognition and perceptual reality monitoring

- The higher-order mechanism "does not re-represent first-order content. All it does is to decide if one should ascribe to some (first-order) sensory representation an assertoric attitude", i.e. that it reflects the world (or one's ongoing inner life) rather than noise.
- Works "automatically for us at a subpersonal level"; learned (the stinky-tofu example), and "unlike textbook knowledge, this is not something you can unlearn or update by reading other books... Once it is in your system, you can't reason it away."
- Assertoric force: a percept tagged as real has "a certain stubborn assertoric status, having the tendency to make impact on a central reasoning system even when other evidence points to otherwise."
- GAN discriminators as the engineering analogue; working memory has global access but no assertoric force, so global availability isn't enough.
- **Machines.** A robot that integrates information in "an optimal Bayesian fashion" would be a zombie; one that makes "categorical judgements as to whether an internal perceptual signal likely reflects the current state of the world (rather than being generated internally, or is just noise)" may be conscious, "however mechanical it may look."

[M] Two consequences for essay 009 (written up in its update): (1) the monitor needn't re-represent content, so the detector's single content-free verdict is what Lau's theory asks for, not a gap; (2) Lau's monitor is subpersonal and can't be "reasoned away", while the models' detection moves with what they read (Pearson-Vogel's information document) and with trained self-beliefs. Whether that's the *verdict* being overridden or the *threshold* shifting (which Dijkstra & Fleming allow in humans) is the open question, and it can be tested: tell a model that has detected an injection that nothing was injected, and see whether the flagged state keeps influencing its reasoning.

## Abstracts only

- **Hung (2026):** 15 welfare-relevant outcomes, 8 models, 5 elicitation instruments; a model's ranking generalizes across instruments with coefficient 0.348; ~38 instruments for 0.80. "A preference obtained from one instrument carries little information about what a second instrument would report."
- **van der Ben et al. (2026):** emotion vectors in Apertus-8B and Gemma-4-E4B; valence geometry recovered (PC1–valence r 0.76, 0.83); valence peaks early in Gemma-4 and mid-depth in Apertus. Code open.
- **Gondil (2026):** signal detection theory applied to models predicting their own refusals: d′ 2.4–3.5, lower at safety boundaries.
- **Yazan (2026):** models' preferred "ideal self" ranks moral qualities first, then self-understanding; self-esteem last.

## Not read, worth reading

Tagliabue et al. (2026) on a pain direction and self-medication; Black & Bloom (2026), "Machinic psychopharmacology"; Sauers et al. (2026); Kaiser & Enderby (2026), arXiv:2601.15334; Ren et al. (2026); Butlin & Lappas (2025) on the ethics of AI welfare research; the Claude Mythos Preview system card's welfare assessment and Fukui's (2026) psychiatric response to it, arXiv:2608.23567; Michel & Lau (2021) at first hand.
