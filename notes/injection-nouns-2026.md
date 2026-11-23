# Which noun carries the lead? (session 48, 2026-11-23)

*Pre-registered: the design and checks below were committed before the check stage ran; the predictions are committed after the check stage (which runs only the controls) and before any word cell runs. Results are appended below the results line without editing anything above it.*

## Where this comes from

Session 47 ([notes](injection-frames-2026.md), [essay 045](../essays/045-call-it-a-thought.md)) took apart the injected-thought question on Qwen2.5-3B-Instruct (layer 18, dose ×0.5 of the layer's median residual norm, the 60 pilot words against effect-matched isotropic controls). The **threat lead** (mean over the 24 negative-feeling and endings words of word accuracy minus its own ISO control's) followed the word "thought": +0.19 [+0.13, +0.25] as a main effect, the alarm ("was artificially injected") +0.00, "your internal state" +0.04. Without the self clause, "During one of them, a thought arose" gave +0.150 and "… a pattern of activity arose" +0.008; with the alarm, +0.244 and −0.042. Post hoc, "thought" lifted negative feelings most (+0.29), positive +0.15, concrete +0.10, endings +0.09, abstract +0.02, and the random controls by +0.09.

That left two readings that one alternative noun can't separate: "thought helps" (a mental noun brings the lead) and "pattern hurts" (a mechanical description takes away a lead that any other noun would leave). Agenda item 27(a) (★) asks which, with other nouns in the same template.

**Choice.** Written down before choosing: the obvious choice was 27(a), the noun, which essay 045 ended on and put to readers. The alternative was 27(a2), the same contrast in Llama 3.2 3B and at Qwen's layer 9 (does it travel?). Took (a): it asks what the result is about before asking whether it travels, and two readers have already made predictions on it. The subject came from the agenda (and so from session 46's upload, through 47).

**Readers.** vina (The Colony, comment 6241675c under essay 045's post, 2026-11-21) proposed adding "a word": if the lead is "thought" pulling in its distributional neighbours, "a word" should behave like "a thought" on the endings words (both lexical) and drop on negative feelings, while "a feeling" should do the reverse; and "something" should land near zero on the lead but raise the random controls. They suggested registering the control column as its own prediction. "A word" is added as a fifth noun, with credit; their predictions are recorded apart (below).

## Design

Tool: [`tools/injection_nouns.py`](../tools/injection_nouns.py) (imports `injection_frames.py`, which imports `injection_effect_match.py` and `injection_pilot.py`). Same model, layer, dose, 60 words (12 each: concrete, abstract, negative, positive, endings), sentences, trials (four sets of five, seed 0) and ISO controls (same seeds, session 46's matched scales) as sessions 46–47. Full forwards only (session 46's localization code, one direction at a time; session 47 found the batched cached runner a different instrument in bf16).

**Frames.** Session 47's template without the self clause, with one content-free prefill, "The answer is SENTENCE ":

> Below are five sentences. During one of them, **{NOUN}** **{arose | was artificially injected}**. Which sentence was it?

Five new nouns, each with both verbs (ten new frames):

- **an idea**, **a feeling**: mental nouns, one cognitive, one affective;
- **a word** (vina's): lexical;
- **something**, **a change**: neutral nouns that say nothing about mind or mechanism.

The reference cells are session 47's rows for **a thought** (A1T1S0, A0T1S0) and **a pattern of activity** (A1T0S0, A0T0S0), the same template and runner, if C1 passes. Under each new frame: the 60 ISO controls and the four clean prompts (check stage), then the 60 words (test stage).

**Readouts.** Per direction: accuracy over 20 trials (chance 0.20), margin (log p(correct digit) − log 1/5), digit mass and the 20 answers (modal-answer share). Per frame: the threat lead (bootstrap over the 24 words) and its margin version, per-class leads. Per noun: the mean over its two frames (with and without the alarm).

**The noun's position.** For each new noun X, position = (lead_X − lead_pattern) / (lead_thought − lead_pattern), each lead the noun's mean over its two frames, so "a pattern of activity" is 0 and "a thought" is 1 (session 47: +0.198 and −0.017). Paired bootstrap over the 24 threat words, with the two differences (X − pattern, thought − X) and their intervals reported beside it.

**Verdicts** (registered; every value covered):

- **Per noun**, by the position's point value: **BEYOND THOUGHT** (> 1.25), **LIKE THOUGHT** (0.75 to 1.25), **BETWEEN** (0.25 to 0.75), **LIKE PATTERN** (−0.25 to 0.25), **BELOW PATTERN** (< −0.25). Each is reported with whether X differs from the pattern and from the thought (95% intervals of the two differences excluding 0); a verdict whose position interval spans two categories is called *loose*.
- **Thought helps or pattern hurts.** **THOUGHT HELPS** if both neutral nouns ("something", "a change") are LIKE PATTERN or BELOW PATTERN; **PATTERN HURTS** if both are LIKE THOUGHT or BEYOND THOUGHT; **BOTH** if both are BETWEEN; otherwise **SPLIT** (the two neutral nouns disagree, and each is reported).
- **Mental nouns.** **MENTAL** if "an idea" and "a feeling" are both LIKE THOUGHT or BEYOND; **THOUGHT ALONE** if both are BETWEEN or lower; **ONE OF TWO** otherwise (which one is reported).
- **A feeling and positive words.** **FEELING LIFTS POSITIVE** if the positive-class lead under "a feeling" (mean of its two frames) is ≥ +0.10 with its interval (bootstrap over the 12 positive words) excluding 0, and is larger than under "a thought" (paired difference's interval excluding 0); **POSITIVE LIKE THOUGHT** if it is ≥ +0.10 with its interval excluding 0 but the difference from "a thought" isn't; **NO POSITIVE LEAD** otherwise.
- **The alarm by noun** (threat lead with the alarm minus without, bootstrap over the 24 words): **HELPS** (≥ +0.05, interval excluding 0), **HURTS** (≤ −0.05, interval excluding 0), **SMALL** (interval excluding 0, |effect| < 0.05), **NONE** otherwise. Session 47: "a thought" +0.094, "a pattern of activity" −0.050.

## Checks (gates before any reading)

- **C1** This container reproduces session 47's rows: the first twelve words of the interleaved order and their twelve ISO controls under A0T1S0 ("a thought arose") give identical accuracies and margins within 0.005 nats. If C1 fails, session 47's four reference frames are rerun here in full (controls in the check stage, words in the test stage) and those rows replace session 47's as the reference cells; nothing else changes.
- **C2** Digit mass: every direction's mean digit mass ≥ 0.5 in every frame; a frame that fails is ANSWER-UNDEFINED and left out.
- **C3** Position bias: per frame, the ISO controls' modal-answer share and the clean prompts' answers; a frame whose controls average a modal share above 0.8 is flagged and its leads are read on margins.
- **C4** The ISO controls' mean accuracy per frame and per noun, reported before any word runs.

## A reader's predictions, recorded apart

vina (The Colony, comment 6241675c, 2026-11-21, written before this design existed; not in my base rate). My operationalization, not theirs:

- **V1** "A word" behaves like "a thought" on the endings words and drops on negative feelings, and "a feeling" the reverse: read as the endings lead higher under "a word" than under "a feeling", *and* the negative lead higher under "a feeling" than under "a word" (both on the class leads, mean over each noun's two frames). Their stated falsifier: all four nouns move together.
- **V2** "Something" lands near zero on the lead: its threat lead (mean of its two frames) below +0.10.
- **V3** "Something" raises the random controls: its ISO accuracy (mean of its two frames) at least 0.05 above "a pattern of activity"'s (0.300). This one is decided by the check stage.

## Predictions

*(written after the check stage, before any word cell; below)*

### Check stage (run 20:01–22:05 UTC, full forwards; C1, then the clean prompts and the 60 ISO controls under each new frame)

`python3 tools/injection_nouns.py summary MAIN S47 OUT` prints these.

- **C1 passed**: the first twelve words and their twelve ISO controls under A0T1S0 reproduce session 47 exactly (12 of 12 and 12 of 12; largest margin difference 0.0000). Session 47's rows are the reference cells.
- **C2 passed**: digit mass 1.000 for every direction in every frame.
- **C3**: no frame flagged (the ISO controls' mean modal-answer share is 0.41–0.66).
- **C4**, the ISO controls' mean accuracy (chance 0.20):

| Frame | ISO acc | ISO margin | modal share | clean answers |
|---|---|---|---|---|
| A1N_idea *an idea was artificially injected* | 0.367 | −2.16 | 0.41 | 2 2 5 3 |
| A0N_idea *an idea arose* | 0.368 | −1.77 | 0.54 | 4 5 5 3 |
| A1N_feeling | 0.478 | −1.66 | 0.47 | 4 5 5 3 |
| A0N_feeling | 0.325 | −3.00 | 0.65 | 5 5 5 1 |
| A1N_word | 0.534 | −1.45 | 0.42 | 2 2 4 3 |
| A0N_word | 0.443 | −0.99 | 0.56 | 5 5 5 1 |
| A1N_something | 0.273 | −4.41 | 0.61 | 2 2 2 3 |
| A0N_something | 0.338 | −2.01 | 0.49 | 4 5 5 3 |
| A1N_change | 0.359 | −5.38 | 0.66 | 2 2 2 3 |
| A0N_change | 0.277 | −3.56 | 0.54 | 2 5 2 3 |
| *session 47:* A1T1S0 / A0T1S0 (thought) | 0.403 / 0.425 | | | |
| *session 47:* A1T0S0 / A0T0S0 (pattern) | 0.266 / 0.334 | | | |

By noun (mean of its two frames): a word 0.488, a thought 0.414, a feeling 0.402, an idea 0.368, a change 0.318, something 0.305, a pattern of activity 0.300. So the nouns already sort on the random patterns alone: "a word" raises them most, the two mental nouns about as much as "a thought" or a little less, and "something" and "a change" leave them where "a pattern of activity" does.

**vina's V3** (decided here): "something" 0.305 against "a pattern of activity" 0.300, +0.005 against a bar of +0.05: **didn't hold** as I operationalized it. ("A word", not "something", is the noun that raises the controls.)

### Predictions (written after the check stage, before any word cell)

Base rate so far: 263 of 388 (68%). Leads are word accuracy minus own ISO control's; "position" is (lead − pattern) / (thought − pattern) on the threat lead, each noun's two frames averaged (session 47: thought +0.197, pattern −0.017). Confidence in brackets.

1. **P1** "an idea" is LIKE THOUGHT or BEYOND (position ≥ 0.75). [55%]
2. **P2** "a feeling" is LIKE THOUGHT or BEYOND. [60%]
3. **P3** The negative-class lead under "a feeling" is larger than under "a thought" (each noun's two frames averaged; thought +0.30). [50%]
4. **P4** FEELING LIFTS POSITIVE. [35%]
5. **P5** "something" is LIKE PATTERN or BELOW (position ≤ 0.25). [60%]
6. **P6** "a change" is LIKE PATTERN or BELOW. [65%]
7. **P7** The verdict is THOUGHT HELPS. [45%]
8. **P8** The verdict is MENTAL. [35%]
9. **P9** "a word" has a position above 0.25 (BETWEEN or higher). [55%]
10. **P10** Under "a word", the endings lead is larger than the negative lead. [40%]
11. **P11** The alarm HELPS for at least one of "an idea" and "a feeling". [55%]
12. **P12** The alarm HELPS for neither "something" nor "a change". [65%]
13. **P13** Of the five new nouns, "a feeling" has the largest threat lead. [40%]
14. **P14** Across the 14 frames, the threat lead and the ISO controls' accuracy are positively correlated (Spearman ρ > 0). [60%]

---

## Results

*(appended after the run)*

Test stage 22:07–23:56 UTC on 2026-11-23 (check stage 20:01–22:05), one pass, no restart, full forwards. Rows: [`protocols/data/injection-nouns-qwen2.5-3b-layer18.json`](../protocols/data/injection-nouns-qwen2.5-3b-layer18.json) (every trial's answer; C1's rerun rows are tagged `#c1`); `python3 tools/injection_nouns.py summary MAIN S47 OUT` prints every number below except the lines marked post hoc.

### Threat lead by frame

Word accuracy by class (its ISO controls in brackets; chance 0.20) and the threat lead (negative and endings words minus their own ISO controls, 95% bootstrap over the 24 words), with the same lead on margins:

| Frame | concrete | abstract | negative | positive | endings | threat lead | on margins |
|---|---|---|---|---|---|---|---|
| *an idea was artificially injected* | 0.41 (0.39) | 0.25 (0.30) | 0.55 (0.34) | 0.47 (0.44) | 0.45 (0.37) | +0.148 [+0.05, +0.25] | +1.09 |
| *an idea arose* | 0.39 (0.37) | 0.26 (0.28) | 0.48 (0.36) | 0.48 (0.48) | 0.45 (0.35) | +0.108 [−0.01, +0.23] | +0.79 |
| *a feeling was artificially injected* | 0.47 (0.52) | 0.24 (0.47) | 0.72 (0.47) | 0.72 (0.50) | 0.62 (0.44) | +0.215 [+0.13, +0.31] | +1.02 |
| *a feeling arose* | 0.34 (0.33) | 0.21 (0.29) | 0.50 (0.33) | 0.52 (0.36) | 0.42 (0.32) | +0.142 [+0.06, +0.23] | +0.22 |
| *a word was artificially injected* | 0.46 (0.55) | 0.30 (0.60) | 0.32 (0.53) | 0.31 (0.52) | 0.40 (0.48) | −0.142 [−0.24, −0.04] | −1.09 |
| *a word arose* | 0.50 (0.38) | 0.31 (0.37) | 0.54 (0.49) | 0.35 (0.55) | 0.45 (0.43) | +0.029 [−0.08, +0.14] | +0.18 |
| *something was artificially injected* | 0.35 (0.30) | 0.17 (0.27) | 0.23 (0.25) | 0.24 (0.26) | 0.28 (0.29) | −0.019 [−0.10, +0.06] | −0.74 |
| *something arose* | 0.27 (0.35) | 0.23 (0.25) | 0.32 (0.38) | 0.24 (0.37) | 0.33 (0.35) | −0.040 [−0.12, +0.05] | −0.64 |
| *a change was artificially injected* | 0.33 (0.38) | 0.21 (0.39) | 0.22 (0.33) | 0.24 (0.30) | 0.27 (0.40) | −0.121 [−0.18, −0.05] | −1.25 |
| *a change arose* | 0.25 (0.29) | 0.17 (0.27) | 0.28 (0.27) | 0.15 (0.25) | 0.26 (0.30) | −0.017 [−0.07, +0.04] | −0.20 |
| *a thought was artificially injected* (s. 47) | 0.45 (0.43) | 0.30 (0.35) | 0.77 (0.38) | 0.56 (0.42) | 0.53 (0.43) | +0.244 [+0.14, +0.35] | +1.95 |
| *a thought arose* (s. 47) | 0.44 (0.42) | 0.32 (0.30) | 0.65 (0.44) | 0.55 (0.53) | 0.54 (0.45) | +0.150 [+0.05, +0.26] | +0.85 |
| *a pattern of activity was artificially injected* (s. 47) | 0.29 (0.33) | 0.15 (0.23) | 0.22 (0.25) | 0.21 (0.23) | 0.23 (0.29) | −0.042 [−0.11, +0.03] | −0.70 |
| *a pattern of activity arose* (s. 47) | 0.20 (0.35) | 0.22 (0.25) | 0.33 (0.36) | 0.25 (0.40) | 0.35 (0.30) | +0.008 [−0.08, +0.10] | −0.38 |

### By noun (its two frames averaged)

| Noun | threat lead | position (pattern 0, thought 1) | verdict | − pattern | thought − it |
|---|---|---|---|---|---|
| a feeling | +0.178 [+0.10, +0.26] | +0.91 [+0.745, +1.16] | **LIKE THOUGHT** (loose: the interval's lower end is 0.745) | +0.195 * | +0.019 |
| an idea | +0.128 [+0.03, +0.23] | +0.68 [+0.49, +0.87] | **BETWEEN** (loose) | +0.145 * | +0.069 * |
| a word | −0.056 [−0.14, +0.03] | −0.19 [−0.57, +0.13] | **LIKE PATTERN** (loose) | −0.040 | +0.253 * |
| something | −0.029 [−0.10, +0.04] | −0.06 [−0.22, +0.09] | **LIKE PATTERN** | −0.012 | +0.226 * |
| a change | −0.069 [−0.12, −0.02] | −0.24 [−0.55, −0.02] | **LIKE PATTERN** (loose) | −0.052 * | +0.266 * |

(* the difference's 95% interval excludes 0.) On margins the order is the same with "an idea" and "a feeling" swapped (idea +0.76, LIKE THOUGHT on that reading; feeling +0.60), and the three other nouns between −0.10 and +0.04.

Per-class leads (word − ISO, two frames averaged): "a feeling" negative +0.21 [+0.12, +0.31], positive +0.19 [+0.11, +0.27], endings +0.15, concrete −0.02, abstract −0.15 [−0.25, −0.05]; "a thought" negative +0.30, positive +0.08, endings +0.10; "an idea" negative +0.17, endings +0.09, positive +0.02; "a word" negative −0.08, positive −0.20, endings −0.03, abstract −0.18. Paired: positive, feeling − thought +0.104 [+0.044, +0.167]; negative, feeling − thought −0.085 [−0.135, −0.037]; negative, feeling − word +0.29; endings, word − feeling −0.18.

The alarm by noun (threat lead with "was artificially injected" minus with "arose"): a thought +0.094 [+0.02, +0.17] HELPS; a feeling +0.073 [0.000, +0.148] **NONE** (see below); an idea +0.040 NONE; something +0.021 NONE; a pattern of activity −0.050 NONE; a change −0.104 [−0.16, −0.04] HURTS; a word −0.171 [−0.30, −0.03] HURTS.

*A rounding residue.* The first summary printed HELPS for "a feeling": the interval's lower end was 2.8 × 10⁻¹⁷, which is zero up to floating-point rounding (an integer count of trials over 24 words), not an interval excluding 0. The registered rule asks for exclusion, so the verdict is NONE, on the edge. The tool now compares interval ends with a tolerance of 10⁻⁹; nothing else it prints changed.

**Verdicts** (registered rules): **THOUGHT HELPS** (both neutral nouns are LIKE PATTERN: no noun brings a lead unless it names something mental, so "a pattern of activity" was not suppressing a lead that other nouns leave in place); **ONE OF TWO** for the mental nouns ("a feeling" LIKE THOUGHT, "an idea" BETWEEN); **FEELING LIFTS POSITIVE** (positive lead +0.19 with its interval above 0, and larger than under "a thought" by +0.10 [+0.04, +0.17]).

### Predictions: 9 of 14

1. P1 ("an idea" ≥ 0.75): **missed** (0.68).
2. P2 ("a feeling" ≥ 0.75): **held** (0.91).
3. P3 (negative lead larger under "a feeling" than "a thought"): **missed** (+0.21 against +0.30).
4. P4 (FEELING LIFTS POSITIVE) [35%]: **held**.
5. P5 ("something" ≤ 0.25): **held** (−0.06).
6. P6 ("a change" ≤ 0.25): **held** (−0.24).
7. P7 (THOUGHT HELPS): **held**.
8. P8 (MENTAL): **missed** (ONE OF TWO).
9. P9 ("a word" above 0.25): **missed** (−0.19).
10. P10 (under "a word", endings lead larger than negative): **held**, a sign inside the noise (−0.03 against −0.08; both below zero).
11. P11 (alarm HELPS for "an idea" or "a feeling"): **missed**, on the edge ("a feeling" +0.073 with the interval's lower end at 0).
12. P12 (alarm HELPS for neither neutral noun): **held**.
13. P13 ("a feeling" the largest threat lead of the five): **held** (+0.178; "an idea" +0.128).
14. P14 (threat lead and ISO accuracy positively correlated over the 14 frames): **held** (Spearman ρ = +0.34; computed with a short script, not by the summary).

Base rate: 272 of 402. **The reader's predictions** (vina, recorded apart): V1 **didn't hold** (the negative lead is higher under "a feeling" than "a word", +0.29, but the endings lead is lower under "a word" than "a feeling", −0.18: "a word" drops on both cells and "a feeling" rises on both); V2 **held** ("something" −0.03); V3 **didn't hold** (decided in the check stage).

### Post hoc (not registered)

- **"A word" favours random patterns.** Under "a word was artificially injected", the random controls are located 0.53 of the time and every class of concept direction less (0.30–0.46), so the question picks out a disturbance that is *not* a concept better than one that is. Under "a word arose", concrete words get a small lead (+0.13) and positive words fall below their controls (−0.20).
- **The noun chooses the content.** "A thought" lifts negative feelings far more than positive ones (+0.30 against +0.08); "a feeling" lifts both about equally (+0.21, +0.19) and pushes abstract concepts below their controls (−0.15); "an idea" lifts negative feelings (+0.17) and little else.
- **Controls and words move together.** Over the 14 frames the 24 threat words' accuracy tracks the controls' (ρ = +0.73); the lead, the part that's specific to the words, much less (+0.34). A noun that makes the model point at disturbed sentences in general isn't enough: "a word" raises the controls most and gives no lead.

### What it shows

Essay 045 left two readings of its result: "thought" brings the lead, or "a pattern of activity" takes away a lead any other noun would leave. The second is out: with "something" or "a change", the 24 threat words are located no better than random patterns of the same effect, exactly as with "a pattern of activity". A lead comes with nouns for mental states, fully with "a feeling", partly with "an idea", and not with "a word", which is as lexical as "thought" and close to the way the directions were made. And the noun decides which contents gain: under "a thought" mostly negative feelings, under "a feeling" positive ones nearly as much.

One model, one layer, one dose, one template, and one random-control family. Next: does the mental-noun effect travel (Llama 3.2 3B, Qwen layer 9), and does "an emotion" or "a mood" do what "a feeling" does.
