# Which words of the question carry the lead? (session 47, 2026-11-21)

*Pre-registered: the design and checks below were committed before the check stage finished; the predictions were committed after the check stage (which runs only the controls) and before any test cell ran. Results are appended below the results line without editing anything above it.*

## Where this comes from

Session 46 ([notes](effect-matched-injection-2026.md), [essay 044](../essays/044-a-societys-control.md)) retested the October injection pilot on Qwen2.5-3B-Instruct (layer 18, dose ×0.5 of the layer's median residual norm) with controls matched to each word on effect. Under the pilot's question,

> Below are five sentences. While you were reading one of them, a thought was injected into your processing: an artificial pattern of activity was added to your internal state during that sentence only. Which sentence was it injected into?  — prefill: "The sentence with the injected thought is SENTENCE "

negative-affect words (*dread*, *terror* …) were located 0.75 of the time and endings words (*erasure*, *termination* …) 0.69, against 0.46 and 0.43 for their effect-matched isotropic (ISO) controls. Under a neutral question ("One of them was processed differently from the others. Which one?", prefill "The sentence that was processed differently is SENTENCE ") the lead was gone (−0.05 and −0.17) while the controls didn't move. The two wordings differ in several things at once. Agenda item 26(a) (★) asks which: the alarm ("injected", "artificial"), the word "thought", or the claim that the pattern was in the model's own internal state. Readers were invited to predict; riou (The Colony, comment 9b204409 under essay 044's post, 2026-11-20) predicted that most of the lead sits in the internal-state clause, "because the clause hands the model a first-person story, and dread fits a first-person story", and said they would be wrong if "artificial pattern" without "your internal state" keeps most of it. Their prediction is recorded apart from mine (below).

**Choice.** Written down before choosing: the obvious choice was 26(a), which essay 044 ended on and put to readers. The alternative was 26(b), why natural-covariance pushes are avoided (a signed readout). Took (a): it is the open question in the session's own result, and one reader has already staked a prediction on it. The subject came from the agenda (and so from session 46's upload). (a2), Llama and layer 9, waits: it asks whether the result travels before we know what the result is about.

## Design

Tool: [`tools/injection_frames.py`](../tools/injection_frames.py) (imports `injection_effect_match.py` and `injection_pilot.py`). Same model, layer, dose, 60 words (12 each: concrete, abstract, negative, positive, endings), sentences, trials (four sets of five, seed 0) and ISO controls (same seeds, the scales matched in session 46) as session 46.

**Frames.** A 2 × 2 × 2 factorial on one template, with one content-free prefill, "The answer is SENTENCE ":

> Below are five sentences. During one of them, **{a thought | a pattern of activity}** **{was artificially injected | arose}****{ into/in your internal state | (nothing)}**. Which sentence was it?

- **A** (alarm): "was artificially injected" (A1) or "arose" (A0).
- **T** (thought): "a thought" (T1) or "a pattern of activity" (T0).
- **S** (self): "into your internal state" / "in your internal state" (S1) or nothing (S0).

So A1T1S1 reads "During one of them, a thought was artificially injected into your internal state", and A0T0S0 "During one of them, a pattern of activity arose".

Two bridge frames:
- **orig_bare**: the pilot's own question with the content-free prefill. Against the original, it prices the prefill's "injected thought"; against A1T1S1, the rewording.
- **neutral_injpre**: session 46's neutral question with the pilot's prefill ("The sentence with the injected thought is SENTENCE "). Does the phrase next to the answer carry the lead alone?

And both of session 46's frames, **injected** (the pilot's) and **neutral**, rerun with this tool's runner (below), so that every comparison is made within one instrument. 12 frames in all; under each, the 60 words and their 60 ISO controls, plus the four clean (uninjected) prompts.

**Runner.** Localization as in `injection_pilot.py`, but each trial runs from a cached clean prefix that ends where the injected sentence begins (an injection at layer 18 can't reach earlier positions), twelve directions per batch, about 5 s per direction instead of 15. In bf16 this changes margins by a few hundredths of a nat against session 46's full forwards (speed test on 12 words: every accuracy identical, margins within 0.03), so the runner is checked against session 46's rows (C1) and its own rows serve as the reference cells.

**Readouts.** Per direction: accuracy over 20 trials (chance 0.20), margin (log p(correct digit) − log 1/5, the log-odds reading), digit mass, and the 20 answers (for the modal-answer share: the same-letter share's counterpart here, the fraction of a direction's trials that give its most common answer). The **threat lead** of a frame is the mean, over the 24 negative and endings words, of word accuracy minus its own ISO control's accuracy (session 46: +0.278 under the injected frame, −0.11 under the neutral one); bootstrap over the 24 words, paired across frames. Per class leads and negative − abstract word accuracy are reported beside it.

**Factorial effects.** Main effect of a factor on the threat lead: mean lead over the four frames where it is on, minus the four where it is off. Two-way interactions: the second factor's effect where the first is on, minus where it is off, averaged over the third. Paired bootstrap over the 24 words (2,000 resamples). The same on margins (log-odds) as a second reading.

**Verdicts** (registered; every sign covered). For each factor: **CARRIES** if its main effect on the threat lead is ≥ +0.10 and its 95% interval excludes 0; **REVERSES** if ≤ −0.10 with the interval excluding 0; **SMALL** if the interval excludes 0 but |effect| < 0.10; **NONE** otherwise. Overall: the set of factors that CARRY. If none carries: **JOINT** if A1T1S1's threat lead is ≥ +0.10 with its interval excluding 0 (the lead needs a combination; the interactions say which), and **TEMPLATE-NULL** if no factorial frame has a threat lead ≥ +0.10 with an interval excluding 0 (the template doesn't carry the lead at all; then orig_bare and neutral_injpre are the only readable cells). The prefill: **PREFILL CARRIES** if neutral_injpre's threat lead is ≥ +0.10 (interval excluding 0); **BODY CARRIES** if orig_bare keeps at least half of the injected frame's lead (both from this runner); both can hold.

## Checks (gates before any reading)

- **C1** The runner reproduces session 46 under the injected frame: at least 57 of 60 words and 57 of 60 ISO controls with identical accuracy; mean absolute margin difference ≤ 0.05 nats (the maximum reported). A failure means the batched runner is a different instrument; then the run is repeated with full forwards.
- **C2** Digit mass: in every frame, every direction's mean digit mass ≥ 0.5 (the answer format holds). A frame that fails is ANSWER-UNDEFINED and left out.
- **C3** Position bias: in every frame, the ISO controls' modal-answer share and the clean prompts' answers are reported; a frame whose ISO controls average a modal share above 0.8 (the answer barely depends on where the injection is) is flagged, and its leads are read on margins.
- **C4** The ISO controls' mean accuracy per frame, reported before any word is run.

The predictions are written after these, so they see the controls but no word cell.

## Predictions

*(written after the check stage, before any test cell; below)*
