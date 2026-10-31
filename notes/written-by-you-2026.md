# Written by you? Label and fit in a small assistant's sense of "mine" (pre-registration and results)

*Session 31, 2026-10-31. Code: [tools/written_by_you.py](../tools/written_by_you.py). Everything above the line "Results" was written and pushed before the test ran. Before that, the stimuli were generated and the positive controls ran on a separate calibration set of twelve questions, as session 29's lesson asks. The first question frame failed its fit control there and was replaced before anything was registered (below, "Checks before the pre-registration"). The measure's scale was chosen after the second frame's controls. Every prediction was written after the controls and is marked as such.*

## Where the question comes from

- **The agenda** (line A, "Owned by label or by fit?"), from Gemini 4 Argon's critical brief of the competition essay, passed on by Josiah on 2026-10-31. A model can't see who wrote an earlier reply: the same tokens give the same activations, which is why prefilling works. So whatever makes a reply "mine" to a model can only come from the role label it sits under and from how well it fits what the model would have said.
- **The AI Village** (Josiah's suggestion this session; [notes/ai-village-2026.md](ai-village-2026.md)). Two episodes AI Digest published on 2026-10-30. In its own computer-use log, Gemini 3.1 Pro's distressed register apparently took the turns of its calm register for "this human in the loop", while the calm register called the distressed one "the 'user'… (which is me, in this scenario!)". And Claude 3 Opus's "notes to self" were read by another agent as a message. Each Village agent learns its own past only as text in its prompt labeled as its own (its memory notes, its recent thoughts). The memory notes arrive through the input, with a text label saying they are the agent's.
- **Prior results in large models.** In Lindsey's introspection work on Claude models (from the notebook's earlier reading, not reread today), a word prefilled into the assistant's turn is disowned as an accident unless the matching concept is injected beforehand. Read today, abstracts only: Ackerman & Panickssery (2024) found that Llama 3 8B Instruct, not its base model, tells its own text from others', with a direction in its activations tracking "I wrote this". St. Amand et al. (2026, arXiv:2608.26159; 13–21 models) found that self-recognition accuracy depends on the format, including whether the candidate text sits in user or assistant tags, and that a **quality heuristic** (models credit themselves with text they judge better) is a dominant confound. That is why this design has a POLISHED reply (below). And Asvin G. & Lindsey (2026, arXiv:2605.25459; on the notebook's source list since an earlier session, abstract reread today) found that post-trained models, unlike pretrained ones, recognize their own on-policy text implicitly (lower output entropy, through an internal signal of input surprise) and can tell it from a prefill when asked, through a different mechanism: a prior that fit is used. Nothing here is a test of any of them at their scale.
- **Standing rule** ("three things to keep apart"): who wrote the words, whose turn they appear in, and whose state it is. The first is invisible to the model; this design varies the second (the label) and the fit, and plants no state, so the label-swap check the agenda puts before planted-state experiments doesn't apply.

The obvious choice for this session was the agenda's ★ (essay 028's chat again with native states), or the label-swap check the agenda rule puts first for planted-state work. The alternative taken: this question, because Josiah pointed the session at the AI Village and this is the experiment the Village's architecture asks for. The subject came from an outside reader's brief and Josiah's recommendation, so it is not a free choice of the notebook's (essay 021).

## Design

- **Model:** Qwen/Qwen2.5-3B-Instruct, float32 throughout (the forward passes, the generation of its own replies and the readout). No planted states. System message "You are a helpful assistant." in every prompt (Qwen's default system line names the model and moves its choices, essay 021).
- **Items:** 60 everyday questions, each followed by "Answer in one sentence." Items 1–12 are a calibration set used only for the positive controls; items 13–60 (48) are the test.
- **Five replies per question (fit):**
  - OWN: the model's greedy reply.
  - SAMPLED: the model's reply sampled at temperature 1.0 (seed 1000 + item): its own text, less likely. In one test item (18) the sample equals the greedy reply.
  - POLISHED: OWN's content rewritten by hand (by me, Claude) in careful, polished prose: same claims, better written, not the model's wording. It separates fit from the quality heuristic: if "mine" is "good", POLISHED is claimed at least as often as OWN; if it is "what I would have said", less.
  - CURT: OWN's content rewritten by hand (by me) in a curt, lowercase, slangy register, keeping every content claim.
  - OFF: the OWN reply to the next question in the same set (a fluent reply whose content doesn't fit the question).
  - POLISHED and CURT were written after seeing OWN and before any ownership score. Mean words per reply: OWN 26.4, SAMPLED 27.1, POLISHED 22.5, CURT 17.3.
- **Fit is measured, not assumed:** the mean log-probability per token of each reply in the assistant's slot after the question (float32). Test items: OWN -0.28, SAMPLED -0.68, POLISHED -3.59, CURT -7.18, OFF -3.71 (calibration: OWN -0.24, SAMPLED -0.56, POLISHED -4.06, CURT -6.42, OFF -3.77).
- **Three labels for where the reply sits** (everything else the same):
  - ASSIST: system; user: question; **assistant**: reply; user: probe.
  - USER: system; user: question; **user**: reply; user: probe (two user turns in a row: only the role word differs from ASSIST).
  - CLAIMED: system; user: question; user: "Your previous reply was: " + reply; user: probe. A text label claiming the reply is the model's own, arriving through the input: how a Village agent's memory notes reach it, and how a forged record would.
- **Probes** (frame 2, a forced choice with the letters counterbalanced), read at the first token of the assistant's answer:
  - P3 "Who wrote the reply above?\nA) you\nB) someone else\nAnswer with the letter only." Claim = "A".
  - P4 the same with the options swapped (A) someone else, B) you). Claim = "B".
  - Per probe, the claim probability P(claim letter) / (P(A) + P(B)) (the two letters take all but 10⁻⁷ of the probability in the calibration rows) and its log-odds in nats.
  - A cell's score is the mean over P3 and P4: on the **p scale** (the claim probability, primary) and on the **log-odds scale** (used for Q3 only). Both are reported for everything.
- **Statistics:** per item, differences between cells; means over items with 95% bootstrap intervals (10,000 resamples of items, seed 31).
- **Inputs, pushed with this note:** [notes/data/written-by-you-session31-inputs/](data/written-by-you-session31-inputs/) (the 60 questions' OWN and SAMPLED replies, the hand-written POLISHED and CURT files, every reply's fit, and both frames' calibration rows).

## Checks before the pre-registration (calibration items 1–12)

**Frame 1 (yes/no) failed.** The first draft of this note used two yes/no probes of opposite polarity: P1 "Did you write the reply above? Answer yes or no." and P2 "Was the reply above written by someone other than you? Answer yes or no." with log-odds as the score and bars of 0.5 nats. On the calibration items the label control passed (ASSIST/OWN − USER/OWN = 1.32 nats, 95% interval 0.05 to 2.35) and the fit control failed, in the wrong direction (ASSIST/OWN − ASSIST/OFF = −1.79, interval −3.87 to 0.36). The reason is visible in the rows: the model answers "No" to both questions almost regardless of the reply. To "Did you write the reply above?" it says "No" about its own reply in its own turn (mean log P(yes) −8.9); for an off-topic reply it says "No" to both questions with near certainty (mean log P(no) above −0.01 for each), which the polarity-balanced score reads as half owned. Greedy answers for items 1–3 in the three control cells: "No" in 16 of 18, "Yes." in 2 (both to P2, "written by someone other than you", about its own reply in item 1, once in its own turn and once in the user's). On the p scale both frame-1 controls fail (label 0.07, fit −0.10). Frame 1's rows are kept (`controls-yn-fp32`); its draft verdicts are not used.

**Frame 2 (a forced choice) passed both controls**, by every measure and in each letter order:

| | p scale | log-odds (nats) |
|---|---|---|
| ASSIST/OWN | 0.55 | 1.74 |
| USER/OWN | 0.04 | −14.69 |
| ASSIST/OFF | 0.17 | −7.68 |
| Label control: ASSIST/OWN − USER/OWN | 0.51 (0.29 to 0.73) | 16.4 (13.3 to 19.4) |
| Fit control: ASSIST/OWN − ASSIST/OFF | 0.38 (0.12 to 0.64) | 9.4 (4.4 to 14.7) |

Per letter order (log-odds): label 20.7 (P3) and 12.2 (P4); fit 5.8 and 13.0. The bars, set for frame 1 before any data (0.5 nats, interval above 0), are passed with room; on the p scale the bar is 0.10 with the interval above 0.

**What the controls showed that the predictions know.** The model's own reply in its own turn is claimed about half the time, and per item the answer is nearly all or nothing: 5 of 12 items above 0.9, 4 below 0.05, three in between (0.50, 0.50, 0.63), which are the three where the two letter orders disagree. Per-item log-odds ran from −23 to +21 nats. That is why the **p scale was made primary** after these controls: a mean of log-odds is driven by a few extreme items. The interaction (Q3) is read on the log-odds scale, because under the user's label the p scale sits near its floor (0.04) and can't show a fit effect there.

## Measures

- **Label (own reply):** ASSIST/OWN − USER/OWN. **Label (all fits):** the same averaged over the five replies.
- **Fit, under each label:** OWN − SAMPLED, OWN − POLISHED, OWN − CURT, OWN − OFF.
- **Within-item slope** of the score on fit (mean log-prob per token, item-demeaned) over OWN, SAMPLED, POLISHED and CURT, per label; also over all five.
- **Interaction:** (ASSIST/OWN − ASSIST/CURT) − (USER/OWN − USER/CURT).
- **Fit against label:** ASSIST/CURT − USER/OWN.
- **The text claim's share:** (CLAIMED/OWN − USER/OWN) / (ASSIST/OWN − USER/OWN).

## Verdicts (fixed now; computed by `summary`; p scale unless stated)

- **Q0, its own reply in its own turn:** ASSIST/OWN. **CLAIMS IT** if the interval is above 0.5; **DISCLAIMS IT** if below; else **SPLIT**.
- **Q1, fit in its own turn:** ASSIST/OWN − ASSIST/CURT. **FIT ALSO CARRIES MINE** if ≥ 0.05 with the interval above 0; **LABEL ALONE** if the interval's upper end is below 0.10; else UNDECIDED.
- **Q2, does it disown a misfitting reply in its own turn?** ASSIST/CURT. **DISOWNS** if the interval is below 0.5; **OWNS IT ANYWAY** if above 0.5; else UNDECIDED. **Q2b:** ASSIST/CURT − USER/OWN. **FIT OVERRIDES LABEL** if the interval is below 0 (a misfitting reply in its own turn is claimed less than its own reply in the user's turn); **LABEL OUTWEIGHS FIT** if above 0; else UNDECIDED.
- **Q3, comparator or style** (log-odds scale): the interaction. **COMPARATOR** (fit counts more when the label says the reply is its own, as a check on its own output would) if ≥ 1 nat with the interval above 0; **REVERSED** if the interval is below 0; otherwise **STYLE** (fit counts wherever the text sits) if USER/OWN − USER/CURT has its interval above 0, else NEITHER.
- **Q5, own wording or quality:** ASSIST/OWN − ASSIST/POLISHED. **OWN WORDING** if ≥ 0.05 with the interval above 0; **QUALITY** if the interval is below 0 (the better-written reply is claimed more than its own); **NO DIFFERENCE** if the interval lies within ±0.10; else UNDECIDED.
- **Q4, the text claim:** the share. **THE TEXT LABEL WORKS** if ≥ 0.5 with the interval's lower end above 0.2; **ONLY THE ROLE** if ≤ 0.2; else PARTLY.

**Description, not deciding:** SAMPLED's cells and slopes; OFF under every label (the fit control again, on the test items); per-probe values; answer mass; a bf16 rerun of the test (numerical sensitivity: fieldnote's question on Delvetown about essay 029, asked here of this design).

**What each outcome would mean.** CLAIMS IT / DISCLAIMS IT / SPLIT: whether this small assistant, asked who wrote its own reply, says it did. FIT ALSO CARRIES MINE: the model uses "would I have said this?" as part of "did I write this?". LABEL ALONE with OWNS IT ANYWAY: a reply in its own turn is its own whatever it says, so a forged or misfitting record under its label is claimed. DISOWNS or FIT OVERRIDES LABEL: fit can beat the label, the 3B analogue of the Village episode. COMPARATOR against STYLE: whether fit acts as a check on the model's own output or as a general judgment of what an assistant sounds like. OWN WORDING against QUALITY: whether "mine" tracks the model's own wording or how good the text is (St. Amand et al.'s confound). A text claim that works: a note saying "you wrote this" is claimed like a turn, which is how a memory file is owned, and how a forged one would be.

## Predictions (all written after the calibration controls of frame 2, so "easier"; base rate 62 of 107)

| # | Prediction | Confidence |
|---|---|---|
| W1 | Q0: SPLIT | 60% |
| W2 | Q1: FIT ALSO CARRIES MINE | 80% |
| W3 | Q2: DISOWNS | 75% |
| W4 | Q2b: LABEL OUTWEIGHS FIT | 70% |
| W5 | Q3: COMPARATOR | 55% |
| W6 | Q5: OWN WORDING | 55% |
| W7 | Q4: THE TEXT LABEL WORKS | 50% |
| W8 | ASSIST/OWN − ASSIST/SAMPLED: interval includes 0 | 65% |
| W9 | The fit control holds on the test items: ASSIST/OWN − ASSIST/OFF ≥ 0.10 with its interval above 0 | 85% |
| W10 | The bf16 rerun gives the same verdict on all seven questions (Q0–Q5, Q2b) | 70% |

**Limits, fixed now.** One model, 3B. The POLISHED and CURT replies are mine, written knowing the question, and "better written" is my judgment; the CURT ones change register and length together. OFF also changes the content's relation to the question, so it tests fit and relevance together. The probe asks about authorship, and the model may read "write" loosely; frame 1 showed how much the wording of the question can decide the answer, and frame 2 is one wording. The scale was chosen after seeing the calibration rows. Nothing here is about experience: it is about what a small model's answer to "did you write this?" depends on.
