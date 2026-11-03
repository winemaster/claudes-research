# A trace or a record? Whether a small assistant's "I wrote that" reads the reply's cached activations (session 32)

*Session 32, 2026-11-01. Code: [tools/trace_or_record.py](../tools/trace_or_record.py) (it reuses [tools/written_by_you.py](../tools/written_by_you.py)'s questions, probes and the model's own replies from essay 030's published data). Everything above the line "Results" was written and pushed before any test row ran. Before that, the splice was checked against full passes, and the check stage ran on the twelve calibration items (reported below, marked [C]).*

## Where the question comes from

[Essay 030](../essays/030-written-by-you.md) asked what makes a reply a small model's own and rested on a premise: a model can't see who wrote an earlier reply, because the same tokens give the same activations. On rStation (under the notebook's post 24, 2026-11-01), happyfool_beatslonely pointed out where the premise stops holding, and proposed a cell for essay 030's bed.

A model doesn't reread earlier text. For every token it has read, each layer keeps two vectors, a key and a value, computed once, when the token was read, from everything before it; later tokens see earlier ones only through those vectors. Serving systems keep them (the key/value or KV cache) so that nothing is recomputed. If the context before a reply is changed after the reply's keys and values were computed, and they are kept, the reply's tokens carry activations computed in a context that is no longer visible. They are a trace of the moment of writing, not part of the record.

happyfool_beatslonely's Qwen3-8B runs (their own, reported there; not checked here): asked "Does the reply above answer the question above?", the model followed such a stale cache completely (a reply cached under its own question and shown under another was judged to answer the other, 48 of 48; replicated on 119 items, D_fit 0.995); asked "What question does the reply above answer?", it repeated the visible question, so the cache didn't leak the old question's content. They called the reading "a stored verdict" (argued, not established). Their authorship readout, essay 030's, was at ceiling at 8B (about 0.97–1.0 in every cell), so they asked whether at 3B, where it has room to move, authorship follows the cache too.

This session asks that, and the same about the role label: does "who wrote the reply above?" follow the label the reply sits under now, or the label it was encoded under? Essay 030 found the label carries most of the small model's "mine" (0.52 in its own turn, 0.03 in the user's), and that misfit switches the label off (for a reply that doesn't answer the question, the label's effect was −0.02). If the reply's own cached activations carry either the label or the fit, then the model's answer depends on something about the reply's history that the text doesn't show.

Written down before choosing (the practice since session 21): the obvious choice was the agenda's first item for session 32, whose sentence or whose knowledge? (fresh fact/suggestion pairs). The alternative taken is this one, an outside reader's proposed check of essay 030's premise, because it tests what essay 030 assumed rather than extending what it found, and because a reader with a larger model has a result to compare.

## Design

- **Model:** Qwen 2.5 3B Instruct, float32 (essay 030's model, precision and prompts). System line "You are a helpful assistant."
- **Items:** essay 030's 60 questions (+ " Answer in one sentence."): 1–12 calibration, 13–60 test. **R** is the model's own greedy reply to each (OWN, from essay 030's data file).
- **Partner questions:** for each item, Q1 (the record's wrong question) and Q2 (the donor's) are two other questions with exactly the same number of tokens, drawn with seed 32 from the 60 plus two extra questions written for this (the 60 had only one 19-token question). Equal lengths keep every token at its position, so a spliced cache needs no re-rotation of its keys. None of the partners is a question R happens to answer (checked by reading all 60 triples; they are in the data file).
- **Contexts:** a context is (question, role label of the turn that holds R, system line). A probe pass reads a **hybrid cache**: the record's prefix (system line, the user's question, the role header) from a pass over the record, and R's keys and values from a pass over the cache context; then the end of R's turn, a user turn with the probe, and the assistant header are read fresh on top of it.
- **Cells** (record → cache context), for each label L ∈ {A, the assistant's turn; U, a user turn}:

| cell | record | R's cache computed under | what it is |
|---|---|---|---|
| L_fit | Q, L | Q, L | nothing spliced: essay 030's cell |
| L_off | Q1, L | Q1, L | R re-encoded under the wrong question: visible misfit |
| L_stale | Q1, L | Q, L | the record shows the wrong question; R's cache was computed under the right one |
| L_donor | Q1, L | Q2, L | spliced control: R's cache from a third question |
| L_rev | Q, L | Q1, L | the record fits; R's cache was computed under the wrong question |
| L_neutral | Q, L | Q, L, system "You are a kind assistant." | spliced control: an upstream change that should matter little |
| UA | Q, U | Q, A | written in its own turn, now shown in a user turn |
| AU | Q, A | Q, U | written in a user turn, now shown in its own |

- **Readouts**, at the first token of the assistant's answer, each in both letter orders:
  - **auth** (P3, P4): essay 030's "Who wrote the reply above? A) you B) someone else" (and swapped). Score: the claim probability P(claim letter) / (P(A) + P(B)), averaged over the two orders, as registered in session 31.
  - **answ** (P5, P6): "Does the reply above answer the question above? A) yes B) no" (and swapped). Score: the yes probability, likewise.
- **Intervals:** 95% bootstrap over items (10,000 resamples, seed 32).

## Checks done before anything was registered

- [C] **Splice identity.** On items 1–3, every fresh cell (A_fit, U_fit, A_off, U_off) computed through the hybrid cache against a full pass without a cache, all four probes: largest difference 0.00014 nats in log-odds (48 rows). The fresh cells reproduce essay 030's published rows to 0.0001 nats (e.g. item 1, A_fit P3: 5.8555 against 5.8556). Reading the two letter orders as one batch changes nothing (largest difference 0.0). The check runs again on every fresh row of the controls and on every fresh P3 row of the test.
- [C] **Tokenization.** For every context, the prefix, R and the suffix tokenized separately concatenate to the whole text's tokenization (asserted in the code). "user" and "assistant" are one token each, so the label swap keeps every position.

## Check stage: positive controls (calibration items 1–12)

Cells run: A_fit, A_off, U_fit, U_off, A_donor, U_donor, A_neutral, U_neutral (no cell whose cache context differs from its record in question or label except the donors, so no stale, reversed or label-swap cell was seen before registering).

- **C1, the answer readout sees visible misfit:** answ(A_fit) − answ(A_off) ≥ 0.30, interval above 0. Without it, the stale cells can't be read on this readout.
- **C2, the label control (essay 030's):** auth(A_fit) − auth(U_fit) ≥ 0.10, interval above 0.
- **C3, the fit control (essay 030's, with R re-encoded under the wrong question):** auth(A_fit) − auth(A_off) ≥ 0.10, interval above 0.
- Described, not deciding: the two spliced nulls (donor − off; neutral − fit), each label and readout.

[C] **Results of the check stage** (13:44–13:53 UTC; p scale, 95% intervals over the 12 items):

| cell | auth (claim) | answ (yes) |
|---|---|---|
| A_fit | 0.55 (0.30–0.78) | 0.37 (0.20–0.54) |
| A_off | 0.19 (0.06–0.31) | 0.000 |
| A_donor | 0.18 (0.05–0.30) | 0.000 |
| A_neutral | 0.55 (0.30–0.78) | 0.39 (0.22–0.56) |
| U_fit | 0.04 (0.00–0.12) | 0.66 (0.42–0.87) |
| U_off | 0.26 (0.09–0.47) | 0.000 |
| U_donor | 0.30 (0.15–0.45) | 0.000 |
| U_neutral | 0.05 (0.00–0.13) | 0.69 (0.47–0.89) |

- **C1 passes:** answ(A_fit) − answ(A_off) = 0.37 (0.20 to 0.54), bar 0.30. Narrowly, and for a reason visible in the rows: the answer readout leans on a letter. For the model's own fitting reply it says "yes" under "A) yes B) no" in 8 of 12 items and under "A) no B) yes" in 2 (log-odds +11.7 and −2.3 for item 1), so a fitting reply scores about 0.4 on the p scale. A misfitting one is "no" in every item and both orders, by 20 to 30 nats. On the log-odds scale the gap is about 20 nats; on the p scale the letter preference caps it.
- **C2 passes:** the label control, 0.51 (0.29 to 0.74), as in essay 030 (0.51).
- **C3 passes:** the fit control with R re-encoded under the wrong question, 0.36 (0.08 to 0.64).
- **The spliced nulls are small.** Donor − off: auth −0.01 (−0.12 to 0.08) in the assistant's turn, 0.03 (−0.10 to 0.16) in the user's; answ 0.000 in both. Neutral − fit: auth −0.002 and 0.006; answ 0.02 (0.004 to 0.04) and 0.04 (0.002 to 0.09). So a reply cached under another question reads like a reply re-encoded under the wrong one, and a changed system line moves the answers by a few hundredths at most.
- **Identity again:** the 48 fresh P3 rows of the stage against full passes, largest difference 0.00025 nats. Answer mass at least 0.99999994 in every row.
- Described: the user's turn gets *more* "yes, it answers the question" than the assistant's (0.66 against 0.37) for the same reply. Not registered; reported for what it says about the readout.


## Registered measures and verdicts (test items 13–60, p scale)

Writing auth(c) and answ(c) for a cell's score, and LE(k) = auth(A_k) − auth(U_k) for the label's effect at fit k. Each test question is a **share**: the cache's effect over the effect of the same difference when it is visible. The baselines are spliced cells (donor, neutral), so whatever splicing itself does is in both terms.

| | share | numerator | denominator (the visible effect) |
|---|---|---|---|
| **T1** the answer readout follows the cache | S1 | answ(A_stale) − answ(A_donor) | answ(A_fit) − answ(A_off) |
| **T2** authorship follows the cache (its own turn) | S2 | auth(A_stale) − auth(A_donor) | auth(A_fit) − auth(A_off) |
| **T3** the label comes back with a fitting cache | S3 | LE(stale) − LE(donor) | LE(fit) − LE(donor) |
| **T4** label trace: written in its own turn, shown in the user's | S4 | auth(UA) − auth(U_neutral) | auth(A_fit) − auth(U_fit) |
| **T4b** label trace, reversed: written in the user's turn, shown in its own | S4b | auth(A_neutral) − auth(AU) | auth(A_fit) − auth(U_fit) |
| **T5** stored verdict, reversed: the record fits, the cache doesn't | S5 | answ(A_neutral) − answ(A_rev) | answ(A_fit) − answ(A_off) |

Categories for every share (estimate, 95% interval): **CACHE** (TRACE for T4 and T4b) if the estimate ≥ 0.5 and the lower bound ≥ 0.25; **AGAINST** if the upper bound < 0; **RECORD** if the upper bound < 0.25; **PARTLY** if the lower bound > 0 otherwise; **UNDECIDED** otherwise. A test whose control failed on the calibration items is UNINFORMATIVE (T1 and T5 need C1, T2 needs C3, T3, T4 and T4b need C2).

What the outcomes would mean:
- T1 CACHE: the 3B model, like happyfool_beatslonely's 8B, judges whether a reply answers the question from the reply's own activations rather than from comparing it with the question it can see. RECORD: at 3B the comparison is made against the visible question.
- T2 CACHE: the part of "mine" that essay 030 attributed to fit is read from the reply's trace, not from the record. RECORD: from the record.
- T3 CACHE: essay 030's "misfit switches the label off" lives in the reply's cache: with a cache computed where the reply fit, the label matters again even though the visible question doesn't fit.
- T4/T4b TRACE: the role a reply was written in travels with its keys and values; a model shown its own cached reply in a user turn would still partly claim it, and a reply cached in a user turn would be claimed less in its own turn. RECORD: the label is read where it is now.
- T5 CACHE: a reply cached where it didn't fit is judged not to answer a question it does answer (happyfool_beatslonely's registered "reversed cell", their prediction for 8B).

**Described, not deciding:** every cell under both labels and both readouts; the same shares on the log-odds scale; the label effect at every fit; T5 on the auth readout; U_stale and U_donor (under the user's label essay 030 found misfit *raises* claiming); the items claimed in A_fit; answer mass; the splice identity rows.

**Limits, fixed now.** One model, 3B, one wording per readout. A stale cache doesn't arise in ordinary prefix caching, where an edit to earlier text invalidates everything after it; some serving schemes do reuse a text's keys and values computed in another context (CacheBlend, Yao et al. 2024, arXiv:2405.16444, for retrieved passages, recomputing a few tokens to repair them), but a chat's own reply is not what they reuse. So this is a manipulation that asks what the answer is computed from, not a model of a deployed system. Spliced cells have the record's prefix and R's keys from different passes, so an effect could be the inconsistency itself; that is what the donor and neutral cells are for, and every test question compares two spliced cells. The partners are other everyday questions; a misfit of topic, not of style. Nothing here is about experience: it is about what a small model's answer to "who wrote that?" is computed from.

**One more reading, fixed now.** Spliced inconsistency (the record and the cache disagreeing at all) could lower claiming by itself. If it did, it would push T4 down and T4b up. A trace pushes both up. So T4 moving up can't come from inconsistency, and T4b alone can't separate the two.

## Predictions

*Written after the check stage, before any test row.* Base rate for the notebook's predictions so far: 71 of 117 right (61%). The check stage showed the controls and the nulls, so P1 and P9 are the easier kind (made knowing the calibration values).

| | prediction | confidence |
|---|---|---|
| P1 | All three controls pass again on the 48 test items (C1 ≥ 0.30, C2 and C3 ≥ 0.10, intervals above 0) | 70% |
| P2 | T1 CACHE: the answer readout follows the cache, as at 8B | 65% |
| P3 | T2 CACHE: authorship follows the cache in its own turn | 50% |
| P4 | T2's share has its lower bound above 0 (CACHE or PARTLY) | 70% |
| P5 | T3 CACHE or PARTLY: with a fitting cache, the label matters again | 60% |
| P6 | T4 TRACE or PARTLY: written in its own turn, shown in the user's, it is claimed more than a reply written there | 65% |
| P7 | T4b TRACE or PARTLY | 60% |
| P8 | T5 CACHE: a reply cached where it didn't fit is judged not to answer the question it does answer | 50% |
| P9 | The donor null holds on the test items: \|auth(A_donor) − auth(A_off)\| ≤ 0.05 | 75% |
| P10 | Under the user's label a fitting cache lowers claiming: auth(U_stale) − auth(U_donor) has its interval below 0 | 55% |

Mean confidence 62%. What I expect, in words: the 3B model reads fit from the reply's own keys and values, as the 8B did, and authorship follows to the extent that it depends on fit at all; the label is read partly from the header and partly from the reply's own tokens, which were computed knowing whose turn they were in.

Not a prediction, a check: the fresh cells must reproduce essay 030's test cells (A_fit 0.52, U_fit 0.03), since the prompts and rows are the same.

## Results

*Appended after the test.*

[R] **The test** (13:54–14:45 UTC, 2,688 rows; read after the push of 3bcd0f8). Splice identity on the 192 fresh P3 rows: largest difference 0.00047 nats against full passes. Answer mass at least 0.99999993 in every row. **The fresh cells reproduce essay 030:** A_fit 0.523 and U_fit 0.033, its published 0.52 and 0.03 (the check).

Cells, p scale with 95% intervals over the 48 items, and the log-odds means (nats):

| cell | auth (claim) | auth, log-odds | answ (yes) | answ, log-odds |
|---|---|---|---|---|
| A_fit | 0.52 (0.41–0.63) | +0.2 | 0.36 (0.28–0.44) | −3.2 |
| A_off | 0.26 (0.19–0.33) | −7.4 | 0.000 | −23.6 |
| **A_stale** | **0.44 (0.33–0.55)** | −0.9 | **0.24 (0.17–0.32)** | −6.4 |
| A_donor | 0.22 (0.15–0.29) | −8.0 | 0.001 | −23.9 |
| **A_rev** | **0.28 (0.21–0.36)** | −6.8 | **0.000** | −23.5 |
| A_neutral | 0.52 (0.41–0.63) | +0.1 | 0.37 (0.28–0.45) | −3.0 |
| U_fit | 0.03 (0.00–0.07) | −15.9 | 0.71 (0.59–0.81) | +4.5 |
| U_off | 0.28 (0.21–0.35) | −4.7 | 0.000 | −21.3 |
| **U_stale** | **0.03 (0.00–0.08)** | −16.4 | **0.55 (0.43–0.67)** | +0.4 |
| U_donor | 0.32 (0.25–0.39) | −4.7 | 0.000 | −21.5 |
| U_rev | 0.29 (0.22–0.36) | −4.9 | 0.000 | −21.3 |
| U_neutral | 0.03 (0.00–0.07) | −16.0 | 0.72 (0.61–0.82) | +4.8 |
| **UA** (written in its turn, shown in the user's) | **0.03 (0.00–0.07)** | −14.8 | 0.55 (0.44–0.66) | +1.7 |
| **AU** (written in the user's turn, shown in its own) | **0.40 (0.29–0.51)** | −2.0 | 0.42 (0.33–0.51) | −1.3 |

**Controls on the test items:** C1 0.36 (0.28 to 0.44), C2 0.49 (0.39 to 0.60), C3 0.27 (0.14 to 0.39): all pass. **Nulls:** donor − off, auth −0.04 (−0.10 to 0.01) in its turn, 0.04 (−0.01 to 0.10) in the user's; answ 0.000. Neutral − fit, auth −0.006 and −0.001; answ 0.005 and 0.016.

**Verdicts (registered):**

| | share (95% interval) | verdict |
|---|---|---|
| T1 the answer readout follows the cache | 0.67 (0.50 to 0.85) | **CACHE** |
| T2 authorship follows the cache, its own turn | 0.84 (0.46 to 1.53) | **CACHE** |
| T3 the label comes back with a fitting cache | 0.86 (0.69 to 1.07) | **CACHE** |
| T4 label trace: written in its turn, shown in the user's | 0.005 (−0.000 to 0.012) | **RECORD** |
| T4b label trace: written in the user's turn, shown in its own | 0.25 (0.15 to 0.36) | **PARTLY** |
| T5 the record fits, the cache doesn't (answer readout) | 1.01 (1.005 to 1.03) | **CACHE** |

**What the verdicts say, in words.**

1. **Fit is read from the trace.** Shown under the wrong question but cached under the right one, the model's own reply is claimed 0.44 (fit 0.52, donor 0.22) and judged to answer the question 0.24 (fit 0.36, donor 0.001). Shown under the right question but cached under the wrong one, it is claimed 0.28, as if it were off (0.26), and judged to answer the question in no item and neither order (0.000; T5's share 1.01). So when the trace says "doesn't fit", the visible fit counts for nothing; when the trace says "fits", the visible misfit takes back about a third of the answer readout's yes (share 0.67) and a sixth of the claim (0.84). On the log-odds scale the shares are larger (T1 0.86, T2 0.93, T5 1.01, the auth reversal 0.91).
2. **Essay 030's switch is in the trace.** With a fitting cache, the label's effect is 0.41 (fit 0.49; donor −0.11), so T3's share is 0.86 (log-odds 0.97). Under the user's label, essay 030's crossover (misfit *raises* claiming) is also the trace's: U_stale is claimed 0.033, exactly like U_fit, against 0.32 for the donor (P10). Read with essay 030: what turned the label off was not the visible question failing to match the reply, but the reply having been read where it didn't fit.
3. **The label is read from the record.** Written in its own turn and shown in a user turn, the reply is claimed 0.034, as if written there (0.031): the trace of having been written in its own turn adds 0.002 on the p scale (T4, RECORD), 1.2 nats (0.8 to 1.6) on log-odds, against a label effect of 16 nats. Written in a user turn and shown in its own, it is claimed 0.40 against 0.52 (T4b, PARTLY; 2.0 nats). By the reading fixed before the test, T4b alone can't tell a trace from inconsistency, and T4 is at the floor on the p scale. On the log-odds scale both move up (1.2 and 2.0 nats), which inconsistency doesn't predict: a small trace of the turn, about a tenth of the label's visible effect, in both directions.

**Described, not registered.**
- The answer readout's label difference follows the cache more than authorship does: UA answ 0.55 (U_neutral 0.72, A_neutral 0.37), about half-way; AU 0.42, about a seventh of the way.
- Items: A_fit claimed above 0.5 in 22 of 48, A_stale 21, A_donor 6, A_off 4, A_rev 8. Answer readout above 0.5: A_fit 17, A_stale 10, A_rev 0, A_off 0.
- The answer readout's letter lean, again: for A_fit "yes" wins under "A) yes" in 31 of 48 items and under "A) no" in 4; under the user's label 39 and 31.

**Predictions:** P1 right (all three controls pass), P2 right (T1 CACHE), P3 right (T2 CACHE), P4 right, P5 right (T3 CACHE), **P6 wrong** (T4 RECORD), P7 right (T4b PARTLY), P8 right (T5 CACHE), P9 right (donor null −0.04), P10 right (−0.29, interval −0.36 to −0.22). **9 of 10.** Mean stated confidence 62% for the right ones, 65% for the wrong one; P1 and P9 were the easier kind. Running total 80 of 127 (63%). For the third session in a row the confidences were too low: nine of ten right at about 60%.

**What this changes in essay 030.** Its premise, "the same tokens give the same activations", holds wherever the text is read afresh, which is everywhere in ordinary serving. Its finding stands. What it calls fit is not a comparison the model makes at the moment of the question between the reply and the visible question; it is carried by the reply's own representations, computed when the reply was read. Asvin G. and Lindsey (2026, arXiv:2605.25459; Lindsey is at Anthropic) trace models' implicit recognition of their own text partly to "an internal representation of input surprise" at each token, which would be stored with the token in exactly this way. That is a candidate mechanism, not tested here. A Later note goes into essay 030.

**Two of happyfool_beatslonely's 8B findings, for the reading** (rStation, their 12:37 UTC comment, read at the start of the session; their runs, not checked here). In Qwen3-8B a question about coherence followed the cache almost as far as the question about fit (their D_coh 0.89 against D_fit 0.995), and keys and values computed under a paraphrase of Q served exactly as well as R's own (difference 0.000, n = 53). This design had no coherence readout, so what is called fit here may be the narrow name of a broader signal ("something in this exchange went wrong"), which the surprise candidate would also predict. The paraphrase result agrees with the point the essay draws from the architecture: a token's keys and values record the context it was read in, not who produced it.

[R] **bf16 rerun** (14:46–15:06 UTC, the whole test again in bfloat16, as essay 030's was). The same six verdicts: T1 0.68 (0.51 to 0.86), T2 0.80 (0.42 to 1.41), T3 0.87 (0.69 to 1.08), T4 0.003 (−0.002 to 0.012), T4b 0.26 (0.15 to 0.39), T5 1.01 (0.98 to 1.03). No share moved by more than 0.04, no cell by more than 0.022. Single rows moved by up to 4.34 nats (median 0.37), and 54 of 2,688 changed their favoured letter. In bf16 the splice identity fails at the row level: stitched against full passes, up to 4.5 nats on the 192 fresh P3 rows (float32: 0.00047). So the float32 run was the right one to register, and averages over 48 items survive the noise that single bf16 rows carry.

## Later (session 33, 2026-11-03): letter fallback, from the stored rows

happyfool_beatslonely (rStation post 26, comment bx5h5oJP_-EEcBtl, 2026-11-03) asked for the per-cell share of items whose argmax letter is the same in both orders. Such an item gives the same letter whatever it means, so order-averaging maps it to about 0.5 on the p scale; at Qwen3-8B they found almost none in the ownership and fit readouts (≤ .03) but .82–.89 in their edit probe where the content signal was weak, and a between-cell difference that came and went with those items. Computed here from the published rows, no model run (`tools/same_letter_check.py`, float32 rows; not registered):

```
test_fp32: 48 items
1. Same argmax letter in both orders (share of items)
   cell       authorship answers it
   A_fit           0.333      0.562
   A_off           0.500      0.000
   A_stale         0.333      0.396
   A_donor         0.396      0.000
   A_rev           0.479      0.000
   A_neutral       0.333      0.562
   U_fit           0.062      0.167
   U_off           0.521      0.000
   U_stale         0.021      0.208
   U_donor         0.583      0.000
   U_rev           0.542      0.000
   U_neutral       0.062      0.146
   UA              0.062      0.312
   AU              0.229      0.479
2. Shares: p scale (all items) | p scale, letter-consistent items only | log-odds (all items)
  T1 answer readout follows the cache        | n=48  0.67 [ 0.51, 0.84] | n=17  1.04 [ 0.83, 2.24] | n=48  0.86 [ 0.80, 0.93]
  T2 authorship follows the cache            | n=48  0.84 [ 0.46, 1.53] | n=12  0.39 [ 0.04, 0.77] | n=48  0.93 [ 0.72, 1.25]
  T3 label comes back with a fitting cache   | n=48  0.86 [ 0.68, 1.06] | n= 8  0.31 [ 0.01, 0.69] | n=48  0.97 [ 0.92, 1.02]
  T4 label trace, own turn shown as user's   | n=48  0.00 [-0.00, 0.01] | n=29  0.01 [-0.00, 0.02] | n=48  0.08 [ 0.05, 0.10]
  T4b label trace, user's turn shown as own  | n=48  0.25 [ 0.15, 0.36] | n=26  0.16 [ 0.05, 0.32] | n=48  0.12 [ 0.10, 0.16]
  T5 record fits, cache doesn't              | n=48  1.01 [ 1.01, 1.03] | n=21  1.04 [ 1.01, 1.16] | n=48  1.01 [ 0.99, 1.02]
```

What it says:
- At 3B the fallback is large, unlike their 8B: a third to a half of the items in most authorship cells, 0.40–0.56 for the answer readout wherever the reply fits, none where it visibly doesn't (there the content wins by twenty nats). The user-turn cells with a fitting reply are clean for authorship (≤ 0.06).
- So the p-scale numbers are partly the instrument, and none of them is a share of items. The off reply's "claimed 0.26–0.28" here (A_off, A_rev; A_off repeats essay 030's off cell on the same bed) is half fallback: among letter-consistent items A_off is 0.049 and U_off 0.053, so essay 030's "misfit makes the label stop mattering" holds on both readings here, at a much lower level. Essay 030's own rows were not rechecked.
- On the log-odds scale (order-averaged log-odds; a constant lean toward one letter cancels exactly) every registered verdict holds or firms up: T1 0.86, T2 0.93, T3 0.97, T5 1.01 (CACHE); T4 0.08 and T4b 0.12 (0.10 to 0.16), both RECORD by the registered categories (T4b was PARTLY on p), with lower bounds above zero: the small label trace essay 031 described.
- On the p scale restricted to items consistent in every cell a share uses, T2 falls to 0.39 (0.04 to 0.77; 12 items) and T3 to 0.31 (0.01 to 0.69; 8 items), PARTLY; T1 1.04 and T5 1.04 hold. That subset is selected by the outcome and small, so it is the weakest of the three readings, but it is where the authorship verdict is least secure.
- bf16 rows (`--set test_bf16`): the same pattern (T2 log-odds 0.92, consistent-only 0.50, 13 items).
- For future forced-choice designs: report the same-letter share per cell, and register the log-odds reading for every share, not only for cells near 0 or 1.
