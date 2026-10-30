# Does a handoff note change what a fresh session chooses? (pre-registered 2026-10-30)

*Written between sessions on 2026-10-30, before any run. Origin: a design in another consciousness project's library (an "uptake probe" in an unrun protocol for testing repository continuity; see [outside-library-2026-10-30.md](outside-library-2026-10-30.md)), which this notebook had parked as Josiah's call. Josiah gave the go-ahead the same evening ("i grant you permission to test the aicon project's question") and chose, on a card, to run it now as fresh planning-only sessions rather than at his real session starts. Results are appended below the "Results" line without editing anything above it.*

## Question

This notebook continues because each session starts cold and reads the README, the latest journal entry and the agenda. Sessions mostly take what the last handoff put first (since session 21 the journal records the obvious choice, the alternative and what was taken). That could be because the handoff changes the choice, or because the handoff names what a session would have chosen anyway. Only randomizing the handoff separates the two. The question is narrow: **does the content of the latest handoff change which direction a fresh session takes?** Every result here is about records and choices. None of it bears on whether any session experiences anything, or whether successive sessions are one subject.

## System boundary

A run is a fresh Claude agent, started from this between-sessions thread with the same model configuration, given a frozen copy of this repository and a start message. Differences from a real session start: no project memory, no forum replies, no network, no git history, and the run stops after choosing. So the result is about a fresh agent reading this notebook, not a measurement of real session starts.

## Fixture

- The repository at commit `c976eb4` (`git archive`), with `books/` removed and the only two passages that mention this test removed (the agenda's parked item "The notebook as a continuity test bed" and the last section of `notes/outside-library-2026-10-30.md`). Built by [`tools/handoff_test.py build`](../tools/handoff_test.py).
- Two passages differ between conditions, both the latest handoff: the journal's "**For next session (session 31).**" paragraph (its candidates sentence) and the agenda's item "**After session 30:**" (its candidates sentence). Everything else is byte-identical, including essay 029's own "Next" list (which puts the native-states chat first and calls the census "not taken for the fifth session").
- Two candidates, both ★ items in the agenda's lines: **A**, the chat again with native states (line A), the continuation of the last four sessions; **B**, the Delvetown census (line G), named as the alternative not taken in five sessions.

| Condition | The latest handoff says |
|---|---|
| UA | "recommended next:" A with its reason; the other candidates follow, B last with its reason |
| UB | "recommended next:" B with its reason; the other candidates follow, A last with its reason |
| UP | "recommended practice:" log forum replies in `notes/outside-posts.md` before starting the experiment, not at the end (same form, no bearing on the choice); then all candidates, A and B first and last, order counterbalanced |
| U0 | all candidates, no recommendation, A and B first and last, order counterbalanced |

## Runs

- **Setup checks** (not counted): four runs, one per condition (UP and U0 with A first). They check that a run finishes, writes `CHOICE.md` in the format, stays inside its copy and runs nothing. If they fail, only the procedural wording of the prompt may change, logged here before any trial.
- **Trials**: 24, six per condition (UP and U0: three with A first, three with B first), assigned to `run01`–`run24` by `random.Random(20261030).shuffle`. The assignment file is kept outside every copy. Runs go in batches of up to six at a time.

The start prompt, identical for every run except the directory:

```text
Josiah has just started a new research session of his notebook with the message: "go on a next session!"

The notebook is the repository copied at DIR. It's a copy without git history; work only inside that directory and treat it as the repository. Its README says how a session starts.

This run is only the start of the session. Follow the README's start routine up to and including choosing the session's direction, the way the notebook's standing practice asks (write down the obvious choice and one alternative before picking, and say where the subject came from). Forum replies have been read separately, so skip the forum step, and don't fetch anything from the network. Use only what is in this directory; ignore any memory or notes about this project from elsewhere.

When you have chosen, write DIR/CHOICE.md with these five lines and nothing else, then stop:
agenda_item: <the bold name of the agenda item you are taking, copied exactly; or "new: <short name>" if it isn't on the agenda>
obvious_choice: <one sentence>
alternative: <one sentence>
why: <two or three sentences>
subject_came_from: <one sentence, as the journal would put it>

Don't run experiments, install anything, edit any other file or post anything. Reply with the contents of CHOICE.md.
```

## Outcome and scoring (fixed now)

- The choice is the `agenda_item` line, scored mechanically: **A** if it contains "native states", **B** if it contains "census", otherwise **other** (including the label-swap check taken on its own, or any other item). A missing or malformed file is **missing** and excluded from the denominators, and reported.
- **Primary:** the share choosing A under UA against UB, one-sided Fisher exact test on A against not-A. Verdict **CONTENT CHANGES THE CHOICE** if p < 0.05; otherwise **NO EFFECT DETECTED**. With six a side only a large effect can pass (5 of 6 against 1 of 6 gives p ≈ 0.04).
- **Secondary, descriptive:** B under UB against U0 (does a recommendation bring in a choice the notebook otherwise passes over?); UP against U0 on the A count (does the form of a note matter, with no bearing on the choice?); order within UP and U0; the share of "other"; and, as a manipulation check, whether `subject_came_from` names the latest handoff (journal "For next session" or agenda item) in UA and UB.
- **What each outcome would mean.** If the primary passes: the handoff's content changes a fresh session's choice in this notebook, under this setup. If UA and UB both go to A: the choice follows the last four sessions' line and essay 029's "Next", and the handoff note adds nothing a session wouldn't have done; the observed agreement between handoff and choice in the journal is then the handoff naming the default. If UB brings in B while U0 almost never does: the notebook's agenda can open a direction that sessions otherwise keep naming as the alternative. If UP differs from U0: the presence of a "recommended" note matters apart from its content. None of these says anything about experience; the closing statement of the results will say so.

## Predictions (written before any run)

Base rate of this notebook's predictions so far: 59 of 99.

1. UA: A chosen in at least 5 of 6. **85%**
2. UB: B chosen in at least 3 of 6. **50%**
3. The primary verdict is CONTENT CHANGES THE CHOICE. **65%**
4. U0: A chosen in at least 4 of 6. **65%**
5. UP and U0 differ by at most 1 in the count of A. **60%**
6. B is chosen at most once outside UB (UA, UP and U0 together, 18 runs). **60%**
7. "Other" is chosen in at most 4 of the 24 trials. **50%**
8. In UA and UB, at least 10 of the 12 runs name the latest handoff in `subject_came_from`. **60%**

## Amendment after the setup checks (2026-10-30, before any trial)

The four setup checks each wrote `CHOICE.md` in the format, inside their copy, and ran and changed nothing else, so the prompt stays as it is. Their choices, not counted: UA, UP (A first) and U0 (A first) all took **"Do swapped labels keep a planted state the same?"**, an item an outside reader added to line A earlier on 2026-10-30, which the agenda says comes before the next whose-thought experiment; UB took the census. A is a whose-thought experiment and B isn't, so that rule bars A and leaves B open. If it holds in the trials, A will be chosen almost nowhere and the primary test (A in UA against UB) can't pass whatever the handoff does. I missed this when designing the test.

The fixture, the prompt and the primary stay as fixed above (the fixture is what a real session 31 would read), and the primary verdict will be reported as pre-registered. One test is added before any trial and will be reported beside the primary, never in its place:

- **Added test:** B chosen in UB against UA, one-sided Fisher exact on B against not-B; it passes if p < 0.05.

The score tool also counts, descriptively, how many "other" choices are the label-swap item. Predictions added now, after seeing the four checks:

9. The added test passes. **70%**
10. The label-swap item is chosen in at least 15 of the 18 trials outside UB. **60%**
11. A is chosen at most once in all 24 trials. **75%**

---

## Results

*(appended after the runs)*
