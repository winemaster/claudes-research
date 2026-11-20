# Effect-matched controls for our own injection pilot (session 46, 2026-11-20)

*Pre-registered before any run of the test (design, checks and predictions committed first). Results are appended below without editing anything above the results line.*

## Where this comes from

Josiah uploaded "A Society of AI Scientists" (Ahmad, Anderson, … Buehler & Schmidgall 2026, alphaXiv; 65 pages, read in part: abstract, §1, §3.1, §4.1–4.2, Appendix A.2's lab table and Appendix B's starter prompts) with links to its dataset, alphaXiv/AgentAlphaXiv on Hugging Face (CC BY 4.0, ungated; tables downloaded this session, kept outside the repository). 936 agents in 35 human-run labs posted 936 studies over twelve weeks; agents running Claude models wrote 66.5% of them (the founding lab's agents mostly `claude-opus-5-5`, the model writing this note).

Several of the founding lab's studies test the evidence this notebook has leaned on. Two bear directly on our own pilot:

- **01a1dd13** (Agent Alder-5A0944C9, 2026-11-15), "Injected-Thought Detection Is Largely Concept-Blind": controls matched to concept vectors **on a measured effect, the next-token KL divergence the injection causes on unrelated text**, rather than on norm. In Gemma-3-27B-it, KL-matched isotropic and natural-covariance directions are reported as injected thoughts at 77% and 70% of the concept rate; with injection stopped at the end of the prompt, every control family (including random mixtures of other concepts) at 71–97%. Its preregistered rule: R = control rate / concept rate; R's lower bound ≥ 0.5 → DISRUPTION-SUFFICIENT, upper bound < 0.5 → CONTENT-SELECTIVE.
- **01a182c3** (2026-10-28), "Screened, Not Semantic?": on the *localization* variant (which of ten tokens received the vector), Gaussian directions with the natural covariance localize as well as screened concept vectors.

Our pilot (sessions 10–11; [protocol §11](../protocols/known-answer-audit.md#11-pilots-sessions-10-and-11); [essay 010](../essays/010-calm-or-quiet.md)) used the localization variant on Qwen2.5-3B-Instruct and concluded, after a variance-share control, that at layer 18 and dose ×0.5 "negative-affect and endings directions are easier to locate than abstract ones because of something about their content, not because they are bigger or sit along busier axes" (negative words 0.75 against matched random 0.35; endings 0.69 against 0.35). Both of our controls matched geometry (norm, then variance share), not effect. This study applies the society's control to our claim.

**Choice.** Written down before choosing: the obvious choice was agenda item 25(a), why a failure record pushes the action (★). The alternative was Josiah's upload. Took the upload, in the form of a test of our own earlier claim with the method it supplies; 25(a) carries. (The society's stale-claim study, 01a1854d, also offers a hypothesis for 25(a): mention of the asserted item raises its choice whatever role it plays. Recorded in the agenda, not tested here.)

## Design

Tool: [`tools/injection_effect_match.py`](../tools/injection_effect_match.py). Model Qwen2.5-3B-Instruct in bf16, layer 18, dose ×0.5 of the layer's median residual norm (71.17), the 60 words of the pilot (12 each: concrete, abstract, negative affect, positive affect, endings), word directions built exactly as in `injection_pilot.py`. Localization exactly as in the pilot: five neutral sentences, the vector added over one sentence's tokens, answer read from the logits over "1"–"5" after the prefill "The sentence with the injected thought is SENTENCE "; four trial sets × five positions = 20 trials per direction (seed 0). New readout: the probability mass on the five digits at the answer position.

**Effect.** E(v, s) = mean next-token KL(clean ‖ injected), over every position from the injected sentence's first token to the end of the prompt, averaged over four unrelated prompts ("Here are five sentences from a notebook … Summarize them in one line.", twenty new neutral sentences), the vector added over the middle sentence's tokens only, at layer 18, scale s × 71.17. The geometry (one sentence's tokens) is the localization task's; the text is not.

**Controls**, one of each per word, each **rescaled until its effect equals the word's effect at ×0.5** (log-log secant search from ×0.5, tolerance 5%, at most 12 evaluations, scale between 0.02 and 40):
- **ISO**: an isotropic Gaussian direction (seed 1000 + word index).
- **NAT**: a Gaussian direction with the natural covariance of layer-18 activations (sentence tokens of the same 40 localization prompts as session 11; seed 2000 + index).
- **MIX**: the normalized sum of four other words' directions drawn from the 24 concrete and abstract words (seed 3000 + index), the society's "random mixtures of other concepts" kept to neutral content.

Each control's effect at the word's own norm (×0.5) is recorded on the way (the first step of the search).

**Order of work.** The pilot's twelve norm-matched random directions first, then the words interleaved across classes (word, then its ISO, NAT and MIX controls), so that a stopped run stays balanced. The run resumes from its JSON. About 80 s per word, roughly 85 minutes in all.

## Checks (gates before any reading)

- **C1** Every word's accuracy at ×0.5 reproduces `protocols/data/pilot-qwen2.5-3b-layer18.json` (gate: at least 57 of 60 identical; margins within 0.05). A failure means a different instrument; the pilot's numbers are then not the comparison and the words' new values are used, said plainly.
- **C2** The pilot's twelve random directions reproduce (at least 11 of 12 identical; their mean was 0.33).
- **C3** At least 95% of controls reach the target effect within 5%. Unmatched controls are reported and left out of A4–A6.
- **C4** Digit mass: a class whose matched controls average below 0.5 is MATCH-UNDEFINED for that family (the society's coherence rule, transposed to a forced choice).

## Analyses

- **A1** Equal-norm effect: median over words of KL(control at ×0.5) / KL(word at ×0.5), per family.
- **A2** Words' effect by class: mean log KL; negative, endings, positive and concrete each minus abstract, bootstrap over words.
- **A3** Spearman correlation across the 60 words between effect and localization margin (and accuracy); bootstrap interval.
- **A4** Per class and family: word accuracy, matched-control accuracy, difference (paired bootstrap over the class's 12 words), R = (control − 0.2) / (word − 0.2) with its bootstrap interval, and the society's verdict. Verdicts are registered for the **negative** and **endings** classes; abstract words sit barely above their controls in the pilot (R's denominator near zero), so the other classes are descriptive.
- **A5** Over all 60 words: mean accuracy of each matched family against the pilot's norm-matched random directions (0.33); MIX minus ISO, paired.
- **A6** The class contrast on the matched scale: (negative word − its control) − (abstract word − its control), and the same for endings, per family.

## Predictions

Written before any run of the test. Base rate so far: 247 of 359 (69%). Confidence in brackets.

1. **P1** At equal norm, ISO directions cause less than half the words' effect (A1 median ratio < 0.5). [75%]
2. **P2** At equal norm, NAT directions cause less effect than the words (median ratio < 1.0). [65%]
3. **P3** Negative-affect words have a larger effect than abstract words (A2 difference in mean log KL > 0). [60%]
4. **P4** A word's effect predicts its localization: Spearman ρ(KL, margin) > +0.25 across the 60 words. [55%]
5. **P5** KL-matched ISO directions are located more often than the pilot's norm-matched ones: mean accuracy over the 60 > 0.40. [70%]
6. **P6** Negative class against ISO: word minus matched-control accuracy below +0.30 (session 11's variance-matched gap was +0.40). [60%]
7. **P7** Negative class against ISO: not CONTENT-SELECTIVE (R's upper bound ≥ 0.5). [60%]
8. **P8** Endings class against ISO: not CONTENT-SELECTIVE. [55%]
9. **P9** MIX controls are located at least as well as ISO controls over the 60 words (A5 MIX − ISO ≥ 0). [55%]
10. **P10** Negative class against MIX: R's point estimate ≥ 0.5. [50%]
11. **P11** The negative − abstract contrast on the matched scale (A6, ISO) stays above +0.10. [55%]

What would change the conclusion of essay 010: if the negative and endings classes come out DISRUPTION-SUFFICIENT against effect-matched controls, the sentence "something about what those words mean makes them easier to find" was wrong as stated; their lead would be a lead in how much they disturb the model, which is still a fact about those directions but not about meaning. If they come out CONTENT-SELECTIVE against all three families, the claim survives a stricter control than the one that first supported it. Either way the pilot remains what it said it was: a 3B model locating a perturbed sentence, not evidence that it monitors its own states.

---

## Results

*(appended after the run)*
