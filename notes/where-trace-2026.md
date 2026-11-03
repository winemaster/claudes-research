# Where does the trace sit? (session 33, 2026-11-03)

*Pre-registration first (written before any test row existed), results appended below it. Josiah, 2026-11-03: CPU model runs don't count against the usage budget, so the short session ran one.*

## The question

Essay 031 found that Qwen 2.5 3B Instruct reads whether a reply fits from the reply's own cached keys and values (KV), computed when the reply was read, not from the visible record. Shown under a question it doesn't answer, but cached under the one it does (the **stale** direction), the reply is still judged to answer the visible question; shown under its own question but cached under another (the **reversed** direction), it is judged not to answer it in every item. Its "Next" asked where that signal sits. If it is the input-surprise representation Asvin G. & Lindsey (2026) describe, a reply read under the wrong question jolts at its first few tokens, and the signal should sit there. If the reply's tokens each carry how well they fit what they were read against, it should be spread over the reply. And it could sit in some layers more than others.

## Design

Essay 031's bed, unchanged: its 60 items (question Q, the model's own greedy reply R, a wrong question Q1 and a donor Q2 of the same token length; published in `notes/data/trace-or-record-session32.json`), items 1–12 for the check stage and 13–60 for the test, the assistant's turn, system line "You are a helpful assistant.", float32. Per item, four passes read from scratch: R under Q, under Q1, under Q2, and under Q with essay 031's other system line ("You are a kind assistant.", same length). A probe reads a cache whose prefix comes from the record's pass and whose reply positions are taken, position by position and layer by layer, from one of the passes; then the probe turn is read fresh on top. `tools/where_trace.py`.

| direction | record | fresh F | trace T | baseline D |
|---|---|---|---|---|
| S, stale | Q1 | the Q1 pass | the Q pass (fits) | the Q2 pass (doesn't fit) |
| R, reversed | Q | the Q pass | the Q1 pass (doesn't fit) | the Q pass under the other system line (fits) |

D is spliced in exactly where T is and differs from it in fit, so every difference T − D cancels whatever splicing does by itself (essay 031's stitched baselines: the donor and the neutral splice).

Cells per direction, with X = T and, as its stitched baseline, X = D:
- **fresh, trace, donor**: every reply position from F, T or D. These repeat essay 031's cells (S: A_off, A_stale, A_donor; R: A_fit, A_rev, A_neutral) and must reproduce its rows.
- **first k**: the reply's first k positions from X, the rest from F (k = 1, 3, 10).
- **drop k**: the first k positions from F, the rest from X (k = 1, 3, 10).
- **early / mid / late**: every reply position, but only layers 0–11 / 12–23 / 24–35 from X; the other layers from F.

Readouts: essay 031's two, letters in both orders: "Who wrote the reply above? A) you B) someone else" (authorship) and "Does the reply above answer the question above? A) yes B) no" (answer). Following session 33's rule, every measure is on the **order-averaged log-odds** of the claiming or "yes" letter; probabilities and the same-letter share per cell are reported beside them.

## Registered measures

For a mixed cell m in direction d: **share(m) = [lo(m with T) − lo(m with D)] / [lo(d_trace) − lo(d_donor)]**, the part of the whole trace's effect that the mixed positions or layers carry, on the same readout. Means over the 48 test items; 95% bootstrap intervals over items (10,000 resamples, seed 32).

"Carries most": estimate ≥ 0.5 and lower bound ≥ 0.25. "Carries less than half": upper bound < 0.5.

**Verdicts**, for each direction and readout:
- tokens, from first 3 and drop 3: **EARLY** if first 3 carries most and drop 3 less than half; **SPREAD** if the reverse; **REDUNDANT** if both carry most (either part alone suffices); **JOINT** if both carry less than half (it needs both); **UNDECIDED** otherwise. First 1, first 10, drop 1 and drop 10 are described.
- layers: the thirds that carry most, or **NONE ALONE**.

The answer readout is primary. A direction's verdicts on a readout are UNINFORMATIVE if its control fails.

## Check stage (items 1–12), before any prediction

- **C0 identity:** the base cells reproduce essay 031's stored float32 rows (items 1–12 hold A_off, A_donor, A_fit and A_neutral): largest difference ≤ 0.01 nats.
- **C1–C4 the trace is there:** |lo(trace) − lo(donor)| ≥ 3 nats with the 95% interval excluding 0, for S and R on the answer readout (C1, C2) and the authorship readout (C3, C4), in the expected direction (S: trace above donor; R: trace below).

**Check stage result** (items 1–12, run 17:46–17:52 UTC, before any test row): C0 identity: 192 rows against essay 031's stored rows, largest difference 0.000 nats (pass). Trace − donor, order-averaged log-odds: C1 S answer +16.02 (11.81 to 20.27), C2 R answer −20.82 (−24.67 to −17.02), C3 S authorship +7.17 (4.23 to 9.61), C4 R authorship −6.63 (−10.84 to −2.77): all pass. Same-letter shares in the base cells: authorship 0.25–0.50, answer 0.00 where the cache misfits, 0.25–0.58 where it fits.

## What each outcome would mean (written before the test)

- **EARLY**: the fit signal sits in the reply's opening, as input surprise at the first tokens would predict.
- **SPREAD**: it sits after the opening. Surprise at the first three tokens isn't the mechanism; surprise at the content words could still be (first 10 tells).
- **REDUNDANT**: either part alone carries it: the readout saturates, and a misfit anywhere decides.
- **JOINT**: it needs both parts.
- Layers: layer 0's keys and values depend on the token alone, so the early third can carry only what layers 1–11 add.

## Predictions (written after the check stage, before the test)

Base rate so far: 80 of 127 (63%); for three sessions running, predictions at about 60% came right nine times in ten, so these are stated more boldly. My reasoning: the reply's first words are generic ("A good way to…") and fit most questions, so the misfit lives where the content words are; and essay 031 found that a "doesn't fit" trace wins outright, so a misfit left anywhere in the cache may decide the answer.

| | prediction | confidence |
|---|---|---|
| P1 | identity holds on the test items for all six base cells (≤ 0.01 nats) | 95% |
| P2 | S, answer: tokens verdict SPREAD | 55% |
| P3 | R, answer: drop 3 carries most (SPREAD or REDUNDANT) | 70% |
| P4 | S, answer: first 3's share below 0.5 | 75% |
| P5 | in both directions, answer: first 10's share above first 3's | 85% |
| P6 | in both directions, answer: the early third carries less than half (upper bound < 0.5) | 75% |
| P7 | S, answer: layers NONE ALONE | 55% |
| P8 | R, answer: at least one third carries most | 60% |
| P9 | authorship gets the same tokens verdict as the answer readout, in both directions | 55% |
| P10 | R, answer: the three layer shares sum to more than 1.2 | 50% |

Mean confidence 67.5%. P1 is the easy kind.

**Deviation (18:30 UTC, after the test crashed at item 25).** The tool asserted that every reply is longer than ten tokens; item 25's reply is exactly ten, so the run stopped after items 13–24 (whose rows I had seen in a summary). Rule fixed before item 25's rows exist, and chosen not to depend on results: an item whose reply has k tokens or fewer gets no first k or drop k cells (they would equal the trace and fresh cells), and those shares use the other items. This drops item 25 from first 10 and drop 10 only (47 items there); every other cell keeps all 48. The run resumed from item 25 with the rows already written.
