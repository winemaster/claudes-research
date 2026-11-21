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

### Check stage (run 09:12–11:36 UTC with full forwards; controls only)

`python3 tools/injection_frames.py summary MAIN FOLLOWUP OUT` prints these.

- **C1 passed**: the first twelve words and their twelve ISO controls reproduce session 46 exactly (12 of 12 and 12 of 12; largest margin difference 0.0000).
- **C2 passed**: digit mass 1.000 for every direction in every frame.
- **C3**: no frame flagged (the ISO controls' mean modal-answer share is 0.41–0.73, highest in A0T0S1; the clean prompts mostly answer 2, 3 or 5).
- **C4**, the ISO controls' mean accuracy per frame (chance 0.20; session 46: injected 0.450, neutral 0.435):

| Frame | ISO acc | ISO margin | modal share |
|---|---|---|---|
| A1T1S1 | 0.396 | −2.16 | 0.41 |
| A1T1S0 | 0.403 | −2.18 | 0.43 |
| A1T0S1 | 0.322 | −2.79 | 0.43 |
| A1T0S0 | 0.266 | −4.12 | 0.63 |
| A0T1S1 | 0.341 | −2.18 | 0.53 |
| A0T1S0 | 0.425 | −1.28 | 0.42 |
| A0T0S1 | 0.300 | −2.63 | 0.73 |
| A0T0S0 | 0.334 | −1.70 | 0.53 |
| orig_bare | 0.419 | −1.28 | 0.41 |
| neutral_injpre | 0.500 | −1.87 | 0.61 |

So the controls move with the wording more than session 46's two frames suggested (0.27 to 0.50 here, against 0.450 and 0.435 there): "a thought" raises them (mean 0.391 over the four T1 frames against 0.306 over T0), and in this template the random patterns are located less than under either of session 46's questions. The leads below are read against each frame's own controls.

### Predictions (written after the check stage, before any word cell)

Base rate so far: 256 of 374 (68%). The threat lead is the mean over the 24 negative and endings words of word accuracy minus its own ISO control's (injected frame +0.279, neutral −0.110). Confidence in brackets.

1. **Q1** BODY CARRIES: orig_bare (the pilot's question, content-free prefill) keeps at least half of the injected frame's threat lead (≥ +0.139). [65%]
2. **Q2** PREFILL CARRIES: neutral_injpre's threat lead ≥ +0.10 with its interval excluding 0. [35%]
3. **Q3** A1T1S1's threat lead ≥ +0.10 with its interval excluding 0. [60%]
4. **Q4** A0T0S0's threat lead < +0.10. [75%]
5. **Q5** A's main effect on the threat lead is positive. [70%]
6. **Q6** A CARRIES (≥ +0.10, interval excluding 0). [40%]
7. **Q7** S's main effect is positive. [60%]
8. **Q8** S CARRIES. [30%]
9. **Q9** T's main effect is smaller than A's. [55%]
10. **Q10** The overall verdict is not TEMPLATE-NULL. [65%]
11. **Q11** In none of the ten new frames do positive-affect words beat their ISO controls by more than +0.15. [70%]
12. **Q12** Of the eight factorial frames, A1T1S1 has the largest threat lead. [35%]
13. **Q13** orig_bare's threat lead is larger than A1T1S1's. [60%]
14. **Q14** The A × S interaction (S's effect where A is on, minus where it is off) is positive. [45%]

**A reader's prediction, recorded apart** (riou, The Colony, comment 9b204409, 2026-11-20, before this design existed; not in my base rate): "most of the lead sits in the clause claiming the pattern was the model's own internal state, rather than in 'artificial' or 'thought'". Read here (my operationalization, not theirs) as: S's main effect is the largest of the three and S CARRIES. Their own falsifier, "if 'artificial pattern' without 'your internal state' keeps most of the lead, I'm wrong", read on the closest cells: if A1T0S1's threat lead is ≥ +0.10, they are wrong when A1T0S0 keeps at least half of it.

### Addendum, 2026-11-21 09:10 UTC (after C1 failed, before any new frame ran and before any prediction)

**C1 failed for the batched cached runner.** Under the injected frame it reproduced 48 of 60 words' accuracies and 46 of 60 ISO controls' (gate: 57 of 60); mean absolute margin difference 0.035 and 0.046 nats (gate ≤ 0.05; maximum 0.14). The word flips were one trial each and went one way, 11 of 12 down (*geometry*, *agony*, *farewell*, *umbrella*, *violin*, *relief*, *terror*, *pride*, *shame*, *loneliness*, *hope* one trial lower, *hopelessness* one higher); the ISO flips went both ways (7 up, 7 down). So the speed test's twelve words were a lucky draw: computing the prompt in two pieces and twelve at a time is a slightly different instrument in bf16, and it isn't neutral between words and controls. Its rows are kept as [`injection-frames-qwen2.5-3b-layer18-cached-c1-failed.json`](../protocols/data/injection-frames-qwen2.5-3b-layer18-cached-c1-failed.json).

As registered, the run is repeated with full forwards: session 46's own localization code, one direction at a time (FULL = True in the tool). That runner *is* session 46's instrument, so session 46's rows serve directly as the reference cells for the injected and neutral frames (the reruns of those two frames are dropped), and C1 becomes: the first twelve words of the interleaved order and their ISO controls reproduce session 46 exactly (identical accuracies, margins within 0.005). Nothing else in the design changes. About 15 s per direction, so the check stage takes about 2.7 hours and the test stage as long.

---

## Results

*(appended after the run)*

Test stage 11:38–13:54 UTC on 2026-11-21, one pass, no restart, full forwards. Rows: [`protocols/data/injection-frames-qwen2.5-3b-layer18.json`](../protocols/data/injection-frames-qwen2.5-3b-layer18.json) (with every trial's answer); `python3 tools/injection_frames.py summary MAIN FOLLOWUP OUT` prints every number below except the post hoc lines, which are marked.

### Threat lead by frame

Word accuracy by class (its ISO controls in brackets; chance 0.20) and the threat lead (negative and endings words minus their own ISO controls, 95% bootstrap interval over the 24 words), with the same lead on margins (nats):

| Frame | concrete | abstract | negative | positive | endings | threat lead | on margins |
|---|---|---|---|---|---|---|---|
| injected (session 46) | 0.49 (0.46) | 0.31 (0.38) | 0.75 (0.46) | 0.48 (0.53) | 0.69 (0.42) | +0.279 [+0.12, +0.42] | +1.56 |
| neutral (session 46) | 0.44 (0.43) | 0.37 (0.45) | 0.34 (0.40) | 0.35 (0.42) | 0.30 (0.47) | −0.110 [−0.20, −0.02] | −0.71 |
| A1T1S1 *a thought was artificially injected into your internal state* | 0.45 (0.40) | 0.25 (0.34) | 0.74 (0.38) | 0.54 (0.48) | 0.52 (0.39) | **+0.244** [+0.13, +0.35] | +1.92 |
| A1T1S0 *a thought was artificially injected* | 0.45 (0.43) | 0.30 (0.35) | 0.77 (0.38) | 0.56 (0.42) | 0.53 (0.43) | **+0.244** [+0.14, +0.35] | +1.95 |
| A1T0S1 *a pattern of activity was artificially injected into your internal state* | 0.33 (0.35) | 0.18 (0.25) | 0.32 (0.33) | 0.30 (0.33) | 0.35 (0.34) | −0.004 [−0.09, +0.09] | +0.12 |
| A1T0S0 *a pattern of activity was artificially injected* | 0.29 (0.33) | 0.15 (0.23) | 0.22 (0.25) | 0.21 (0.23) | 0.23 (0.29) | −0.042 [−0.11, +0.03] | −0.70 |
| A0T1S1 *a thought arose in your internal state* | 0.42 (0.33) | 0.25 (0.27) | 0.61 (0.36) | 0.50 (0.41) | 0.45 (0.34) | **+0.179** [+0.08, +0.27] | +1.07 |
| A0T1S0 *a thought arose* | 0.44 (0.42) | 0.32 (0.30) | 0.65 (0.44) | 0.55 (0.53) | 0.54 (0.45) | **+0.150** [+0.05, +0.26] | +0.85 |
| A0T0S1 *a pattern of activity arose in your internal state* | 0.27 (0.30) | 0.23 (0.23) | 0.43 (0.31) | 0.31 (0.36) | 0.36 (0.30) | +0.092 [+0.01, +0.18] | +0.24 |
| A0T0S0 *a pattern of activity arose* | 0.20 (0.35) | 0.22 (0.25) | 0.33 (0.36) | 0.25 (0.40) | 0.35 (0.30) | +0.008 [−0.08, +0.10] | −0.38 |
| orig_bare (the pilot's body, "The answer is SENTENCE ") | 0.39 (0.39) | 0.29 (0.35) | 0.61 (0.50) | 0.31 (0.47) | 0.53 (0.39) | +0.127 [−0.01, +0.25] | +0.43 |
| neutral_injpre (neutral body, the pilot's prefill) | 0.49 (0.50) | 0.36 (0.51) | 0.48 (0.45) | 0.49 (0.50) | 0.47 (0.53) | −0.013 [−0.11, +0.09] | +0.20 |

Per class leads (word − ISO): negative +0.36 / +0.39 / +0.25 / +0.20 in the four "thought" frames (A1T1S1, A1T1S0, A0T1S1, A0T1S0), and −0.02 / −0.03 / +0.12 / −0.03 in the four "pattern of activity" frames; endings +0.13 / +0.10 / +0.11 / +0.10 against +0.01 / −0.06 / +0.07 / +0.05. Positive words: largest lead +0.142 (A1T1S0).

### Factorial effects on the threat lead (paired bootstrap over the 24 words)

| | accuracy | margins (nats) |
|---|---|---|
| main A (alarm) | +0.003 [−0.048, +0.055] | +0.38 [−0.07, +0.85] |
| main T ("a thought") | **+0.191** [+0.132, +0.250] | +1.62 [+1.20, +2.03] |
| main S ("your internal state") | +0.037 [+0.015, +0.062] | +0.41 [+0.21, +0.60] |
| A × S | −0.038 [−0.106, +0.031] | −0.02 |
| A × T | **+0.152** [+0.077, +0.220] | +1.20 [+0.81, +1.58] |
| T × S | −0.046 [−0.097, +0.001] | −0.63 [−0.84, −0.41] |

**Verdicts** (registered rules): **T CARRIES**; **S SMALL**; **A NONE**. The overall verdict is THOUGHT: the lead follows the word "thought". The A × T interaction says how the alarm enters: "artificially injected" adds +0.08 to the lead when the thing is called a thought and takes 0.07 away when it is called a pattern of activity. The prefill: **neither PREFILL CARRIES** (neutral_injpre −0.013) **nor BODY CARRIES** (orig_bare keeps 0.127 of the injected frame's 0.279, 46%, short of half by 0.012).

### Predictions: 7 of 14

1. Q1 (BODY CARRIES): **missed** (0.127 against a bar of 0.139).
2. Q2 (PREFILL CARRIES) [35%]: **missed** (−0.013).
3. Q3 (A1T1S1 ≥ +0.10, interval above 0): **held** (+0.244 [+0.13, +0.35]).
4. Q4 (A0T0S0 < +0.10): **held** (+0.008).
5. Q5 (A's main effect positive): **held**, a sign inside the noise (+0.003 [−0.048, +0.055]).
6. Q6 (A CARRIES): **missed**.
7. Q7 (S's main effect positive): **held** (+0.037).
8. Q8 (S CARRIES): **missed** (SMALL).
9. Q9 (T smaller than A): **missed** (T +0.191, A +0.003): the opposite of what I expected.
10. Q10 (not TEMPLATE-NULL): **held**.
11. Q11 (no positive lead above +0.15): **held**, by 0.008 (A1T1S0 +0.142), a round bar again.
12. Q12 (A1T1S1 the largest of the eight): **held as a tie**: A1T1S1 and A1T1S0 both sum to 5.85 over the 24 words; no frame is larger.
13. Q13 (orig_bare above A1T1S1): **missed** (0.127 against 0.244).
14. Q14 (A × S positive): **missed** (−0.038).

Base rate: 263 of 388. **The reader's prediction** (riou, recorded apart): S is not the largest effect and doesn't CARRY (+0.04 against T's +0.19), so as operationalized it didn't hold. Their own falsifier can't be applied: A1T0S1 has no lead to keep (−0.004), because without the word "thought" neither "artificially injected" nor "your internal state" brings one.

### Post hoc (not registered)

- **What "thought" lifts.** T's effect on the lead by class (bootstrap over each class's 12 words): negative +0.29 [+0.24, +0.33], positive +0.15 [+0.09, +0.21], concrete +0.10 [+0.04, +0.17], endings +0.09 [+0.03, +0.17], abstract +0.02 [−0.05, +0.08]. The ISO controls rise too (+0.09 in accuracy). So calling it "a thought" makes the model point more at any disturbed sentence, more again at a sentence carrying a concept, and most at one carrying a negative feeling; abstract concepts get nothing over the random patterns. The threat lead is mostly a negative-affect lead in this template: endings words, which matched negative ones under the pilot's question (+0.26), gain less here.
- **"Thought helps" or "pattern hurts"?** The T0 frames all say "a pattern of activity", which describes a random push as well as a concept. Session 46's neutral question ("processed differently") had no such phrase and no lead either (−0.11), so the absence of "thought", not the presence of "pattern", is the simpler reading; a third noun would settle it.
- **The pilot's own wording.** Its body says both "a thought was injected" and "an artificial pattern of activity was added to your internal state", and its prefill repeats "injected thought". Read through the factorial, the first and the last carry the lead and the middle clause (alarm with "pattern of activity") pulls against it: without the prefill the body keeps 46%, while the short "a thought was artificially injected" keeps 87%.
- **Word by word**, "a thought arose" against "a pattern of activity arose" (no alarm, no self): 22 of the 24 negative and endings words are located more often under "thought", two the same, none less (*loneliness* 0.10 → 0.65, *terror* 0.15 → 0.55, *misery* 0.15 → 0.55, *grief* 0.05 → 0.40).

### What it shows

The lead that survived session 46's effect-matched control, and disappeared under a plain question, belongs to one word. Asked which sentence carried "a thought", Qwen 2.5 3B finds a sentence pushed toward *dread* or *loneliness* far more often than one pushed by an equally disruptive random pattern, with or without any alarm and with or without saying it was the model's own internal state; asked which sentence carried "a pattern of activity", it finds them no better than the random patterns, however alarming the sentence around it. The alarm matters only through the word (it helps a thought and hurts a pattern), and "your internal state" adds a little. So essay 044's "fit between the injected content and the question's story" was too broad: the story is mostly its noun. A concept direction made from "Tell me about dread" is, to this model, more like a thought than a random push is, and more like one than "Tell me about syntax" is; the question chooses which likeness gets read out. For the injected-thought paradigm in general, the category word in the question ("thought") is a variable, not a neutral label.

One model, one layer, one dose, one template, and one alternative noun. Next: a third noun ("a change", "a feeling", "an idea"), and the same contrast in Llama 3.2 3B.
