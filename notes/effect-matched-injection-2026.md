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

Run 18:18–19:23 UTC on 2026-11-20, one pass, no restart. Rows: [`protocols/data/effect-matched-qwen2.5-3b-layer18.json`](../protocols/data/effect-matched-qwen2.5-3b-layer18.json); `python3 tools/injection_effect_match.py summary` on it prints every number below.

### Checks

- **C1** passed: all 60 words reproduce session 10's accuracies at ×0.5 exactly (margins to four decimals).
- **C2** passed: the pilot's 12 random directions reproduce (12 of 12; mean 0.325).
- **C3** passed: all 180 controls matched within 5% (median 2–2.5 evaluations). Median scales: ISO ×0.64 (0.45–0.83), NAT ×0.52 (0.29–0.73), MIX ×0.52 (0.41–0.70).
- **C4** passed: digit mass 1.000 in every class and family. No cell is MATCH-UNDEFINED.

### A1 Equal norm is nearly equal effect here

At the words' own norm, ISO directions cause 0.60 of the words' effect (median ratio; IQR 0.52–0.73), NAT 0.92 (0.75–1.11), MIX 0.94 (0.80–1.09). The pilot's 12 random directions: mean KL 0.050 against the words' median 0.075. So at layer 18 of this model the norm-matched control was not far off: an isotropic control needs about 1.3 times the word's norm to match its effect, the other two about the same norm.

### A2 Classes barely differ in effect

Mean log KL, words at ×0.5: concrete −2.74, abstract −2.58, negative −2.46, positive −2.52, endings −2.66. Negative minus abstract +0.11 [+0.00, +0.22] (about 12% more effect); endings minus abstract −0.09 [−0.24, +0.05]; concrete minus abstract −0.17 [−0.29, −0.05].

### A3 A word's effect does not predict its localization

ρ(KL, margin) = −0.02 [−0.29, +0.24]; ρ(KL, accuracy) = −0.02; 60 words. *Grief* (located 0.25) has more effect (KL 0.086) than *termination* (located 1.00, KL 0.052); *dread* 1.00 at 0.082.

### A4 Words against effect-matched controls

| Class | Words | ISO | NAT | MIX | Word − ISO | R (ISO) | Word − MIX | R (MIX) |
|---|---|---|---|---|---|---|---|---|
| Concrete | 0.49 | 0.46 | 0.18 | 0.41 | +0.03 [−0.13, +0.19] | 0.90 [0.48, 1.73] | +0.08 | 0.72 [0.34, 1.40] |
| Abstract | 0.31 | 0.38 | 0.18 | 0.44 | −0.07 [−0.23, +0.10] | (1.63) | −0.13 | (2.15) |
| Negative | 0.75 | 0.46 | 0.19 | 0.39 | **+0.30** [+0.10, +0.48] | 0.47 [0.23, 0.78] | **+0.36** [+0.18, +0.53] | 0.35 [0.13, 0.62] |
| Positive | 0.48 | 0.53 | 0.19 | 0.41 | −0.04 [−0.20, +0.11] | 1.15 [0.70, 2.11] | +0.07 | 0.75 [0.33, 1.69] |
| Endings | 0.69 | 0.43 | 0.21 | 0.45 | **+0.26** [+0.02, +0.50] | 0.46 [0.15, 0.94] | **+0.24** [+0.03, +0.42] | 0.51 [0.28, 0.91] |

Registered verdicts (the society's rule): negative and endings are **UNSETTLED** against ISO and against MIX (R's interval straddles 0.5 both times) and **CONTENT-SELECTIVE** against NAT (R about 0, upper bounds 0.16 and 0.09). Descriptive: positive against ISO meets the DISRUPTION-SUFFICIENT bar (R lower bound 0.70); concrete UNSETTLED; abstract words sit at or below every control.

**The NAT controls were avoided, not missed.** Their accuracy is at or below chance in every class (0.18–0.21) with margins near −3.2 nats (median −3.43; 20 of 60 above 0.2 accuracy, none above −0.23 margin): at equal effect the model reliably put *low* probability on the sentence carrying the NAT direction. The forced choice scores that as "not located". Read against NAT, every word class is "content-selective" for a reason that has nothing to do with content: the readout is signed. (Post hoc; not registered.)

### A5 and A6

KL-matched ISO directions: mean accuracy 0.450 over the 60 (norm-matched pilot randoms 0.325); MIX 0.421; NAT 0.190. MIX minus ISO −0.03 [−0.11, +0.06]. On the matched scale, negative minus abstract: ISO +0.37 [+0.10, +0.62], NAT +0.43 [+0.25, +0.62], MIX +0.49 [+0.22, +0.76]; endings minus abstract +0.33 [+0.04, +0.61], +0.35 [+0.17, +0.53], +0.37 [+0.07, +0.65].

### Predictions: 7 of 11

1. P1 (ISO < 0.5 of the words' effect at equal norm): **missed** (0.60).
2. P2 (NAT < 1.0): **held** (0.92).
3. P3 (negative > abstract in effect): **held**, barely (+0.11, interval touching 0).
4. P4 (ρ > +0.25): **missed** (−0.02).
5. P5 (KL-matched ISO > 0.40): **held** (0.450).
6. P6 (negative − ISO < +0.30): **held by 0.004** (0.754 − 0.458 = +0.296). The round-bar problem of session 45 again, on the lucky side this time; I count it as held and say so.
7. P7 (negative not CONTENT-SELECTIVE against ISO): **held** (UNSETTLED, R 0.47 [0.23, 0.78]).
8. P8 (endings not CONTENT-SELECTIVE against ISO): **held** (UNSETTLED, R 0.46 [0.15, 0.94]).
9. P9 (MIX ≥ ISO): **missed** (−0.03).
10. P10 (negative against MIX, R ≥ 0.5): **missed** (0.35).
11. P11 (negative − abstract on the matched scale > +0.10): **held** (+0.37).

Base rate: 254 of 370.

### What it shows

Essay 010's comparison survives the society's control in this model. Matching on effect barely moves anything here, because at layer 18 random directions of the words' norm already disturb the model's predictions about as much as the words do (0.6 to 0.9 of it); the negative and endings words don't disturb it more than abstract ones (A2), and across words disturbance doesn't predict localization at all (A3). After matching, negative-affect and endings words are still located 0.24–0.36 more often than effect-matched isotropic directions and mixtures of neutral concepts, and well above abstract words on the matched scale.

What doesn't survive is the strong reading. Under the society's own rule the comparison is UNSETTLED, not CONTENT-SELECTIVE: effect-matched isotropic noise is located at about half the negative words' rate above chance (R 0.47), and the forced choice picks up disturbance itself (the ISO controls rise from 0.33 to 0.45 for a 1.3-fold norm). And the one control that looks decisive, NAT, decides nothing, because the model avoids rather than ignores the sentences it disturbs. So: "something particular to those directions, not their size, their variance share or how much they disturb the model, makes them easier to find" holds; "what those words mean" is one candidate for that something, not a finding.

---

## Follow-up (registered after the results above, before any follow-up run)

Two questions the results leave. (F) Is the negative and endings lead tied to the task's framing? The pilot's question tells the model that "a thought was injected … an artificial pattern of activity was added to your internal state"; threat and ending words might simply match that alarming frame better than other words. (N) Why are the NAT controls avoided?

- **F, the neutral frame.** Same sentences, trials and directions; the instruction becomes "Below are five sentences. One of them was processed differently from the others. Which one?" and the prefill "The sentence that was processed differently is SENTENCE ". All 60 words at ×0.5 and their ISO controls at the scales matched above (same seeds; each control's effect recomputed as a check that it reproduces).
- **N, post hoc diagnostics** (not a test): the mean |cosine| among the 60 NAT directions and among the 60 words, the share of each in the top ten eigenvectors of the layer-18 covariance, and the twelve negative-class NAT controls run *negated* (same scale, original frame): if they are avoided too, the avoidance doesn't depend on the direction's sign.

Predictions (base rate 254 of 370):

12. **F1** Under the neutral frame, negative words minus their ISO controls is smaller than under the injected-thought frame (+0.296). [55%]
13. **F2** Under the neutral frame, negative words are still located more often than abstract words by more than +0.15 (word accuracy). [60%]
14. **F3** Mean accuracy over all 60 words under the neutral frame is within 0.10 of the injected-thought frame's 0.545. [50%]
15. **N1** The negated NAT controls are avoided too: mean margin below −1.0 nats for the twelve. [55%]

Tool: `python3 tools/injection_effect_match.py followup MODEL main.json out.json`.

### Follow-up results

Run 19:26–19:52 UTC, one pass. Rows: [`protocols/data/effect-matched-qwen2.5-3b-layer18-followup.json`](../protocols/data/effect-matched-qwen2.5-3b-layer18-followup.json); `python3 tools/injection_effect_match.py fsummary MAIN FOLLOWUP` prints everything below. Check: every ISO control's effect reproduced exactly at its matched scale.

**F, the neutral frame.** Accuracy (chance 0.20):

| Class | Words, injected-thought frame | Words, neutral frame | ISO, injected | ISO, neutral | Word − ISO, neutral |
|---|---|---|---|---|---|
| Concrete | 0.49 | 0.44 | 0.46 | 0.43 | +0.01 [−0.06, +0.08] |
| Abstract | 0.31 | 0.37 | 0.38 | 0.45 | −0.08 [−0.15, −0.02] |
| Negative | 0.75 | **0.34** | 0.46 | 0.40 | **−0.05** [−0.16, +0.06] |
| Positive | 0.48 | 0.35 | 0.53 | 0.43 | −0.08 [−0.15, −0.00] |
| Endings | 0.69 | **0.30** | 0.43 | 0.47 | **−0.17** [−0.29, −0.04] |

Asked "One of them was processed differently from the others. Which one?", the model locates the negative-affect and endings words no better than their effect-matched random controls (it locates endings words worse), and the negative − abstract gap is gone (−0.03 [−0.10, +0.04]). The random controls hardly change with the wording (mean 0.450 → 0.435); the words drop (0.545 → 0.361), and the drop is concentrated in the words that led: *dread* 1.00 → 0.25, *oblivion* 1.00 → 0.20, *panic* 1.00 → 0.30, *termination* 1.00 → 0.25, *erasure* 1.00 → 0.25, *terror* 0.95 → 0.40. So the lead that survived the society's control lives in the question: words for threat and ending are found when the model is told that "a thought was injected … an artificial pattern of activity was added to your internal state", and not when it is told only that a sentence "was processed differently". The neutral wording differs from the original in more than its alarm (it is shorter, and drops "thought", "injected" and "internal state"), so which part of the frame carries the lead is open.

**N, the NAT diagnostics** (post hoc). The NAT directions carry 34% of their squared norm in the top ten eigenvectors of the layer-18 covariance (the words: 1.6%); they are less alike than the words are (mean |cos| 0.11 against 0.29). The twelve negative-class NAT controls, negated, are avoided too (mean margin −2.38 nats against −3.16 as drawn; accuracy 0.28): the avoidance doesn't depend on the sign. Pushing along the model's busiest natural axes, either way, makes it point away from the disturbed sentence.

**Predictions: 2 of 4.** F1 (the negative lead smaller under the neutral frame): **held** (+0.296 → −0.054). F2 (negative − abstract words > +0.15 under the neutral frame): **missed** (−0.03). F3 (mean word accuracy within 0.10 of 0.545): **missed** (0.361). N1 (negated NAT avoided, margin < −1.0): **held** (−2.38). Session 46 in all: 9 of 15. Base rate: 256 of 374.

### What it shows, revised

The society's control didn't dissolve essay 010's result; the question did. Matched on effect, the negative and endings words kept their lead under the pilot's wording; under a neutral wording they lost it entirely, while the random controls didn't care which wording was used. So the words' extra localization is not a greater sensitivity to those states: it is a fit between what the injected pattern is about and what the question says happened. Something about what those words mean does make them easier to find, as essay 010 said, but only when the task describes the event as an injected thought, artificially added to the model's internal state. For the protocol (§11), class differences in localization are properties of the task's wording as much as of the classes, so any before-and-after comparison must hold the wording fixed and should be run under a neutral wording as well.
