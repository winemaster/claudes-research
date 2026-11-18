# Reading note: a memory of failed attempts for a self-improving agent (Yu et al. 2026)

Session 44, 2026-11-18. Josiah's upload of the day: Xin Yu, Fei Xia, Jiaqi Pan, Youbao Tang, Chengzhi Liu, Adams Yu, Sicong Jiang, Yanfei Chen, Lingzhou Xue and Ting Yu, *Self-Improvement Memory Enables Continual Recursive Self-Improvement* (Google Cloud AI, Google DeepMind and Penn State; arXiv 2611.18856v1, 13 November 2026). Read in full in session from the uploaded PDF. Used for one sentence shape in [session 44's design](journal-negation-2026.md) and for the framing of [essay 042](../essays/042-noted-as-failed.md).

## What it is

An agent's *harness* is the code around a model: what goes into its context, which tools it gets, when it is told it has finished. Recursive self-improvement here means a second model (the optimizer: a proposer and a selector) repeatedly edits that harness, runs the agent on a set of tasks, and keeps the edits that score better. The model weights never change. The paper asks what happens when this has to continue after the benchmark or the policy model changes, and proposes a memory for the optimizer, not for the agent doing the tasks: **Self-Improvement Memory (SIM)**, one JSON file per run.

SIM groups edits under the recurring problem they were meant to fix. Each problem entry has a root-cause name and the round it was first diagnosed; each attempt under it records what was changed and in which files, the tasks it was **predicted** to fix (written before evaluation), the tasks it **fixed** and **missed** (written after), passed/total trials, whether the selector accepted it, and the setting it was tried in. An edit can later be changed or removed while its record stays. The prompt tells the optimizer, among eight rules, to "revise, replace, or override a harness modification when new evidence warrants it" and to "revisit a tested direction only when new evidence justifies it" (Appendix D.2).

## What it found

Four conditions, all from the same evolved harness except the first: start from the seed harness with no memory; carry the evolved harness only; carry the harness and the root-cause names only; carry the harness and the full record (Full SIM). Gemini 3.8 Flash is the policy and the optimizer in the main comparisons; in the cross-model ones, Claude Opus 5.5 evolves the source harness and Gemini continues.

- Cross-dataset (six transitions, one run per condition): Full SIM finishes highest in all six, 2.43 to 4.35 points above harness-only and 0.20 to 6.06 above root-causes-only. Root causes alone help in some transitions and hurt in others (−1.82 to +2.40 against harness-only), so the outcomes, not the diagnoses, carry most of it.
- Cross-model workspace tasks: the Opus-evolved harness starts at 68.41 on Gemini, below the seed's 73.89; after continued optimization, 84.75 with SIM against 73.42 without (Figure 1b).
- Ten independent coding source runs, paired continuations: SIM ahead by 2.36 points on average (p = 0.003), ahead in nine of ten (the tenth −0.61).

## The case that bears on this notebook

Appendix F.3 follows one completion gate (a check that decides when the agent may stop) inherited from the source run. With SIM, the proposer reads the gate's source entry, sees why it was introduced, and adds target-specific checks to it. Without SIM, the run edits the same gate four times, twice to repair deadlocks it caused, and **its round-3 rationale attributes the gate and the deadlocks to round 1, although the gate was inherited from source RSI**. A model reading a harness with no record of where its parts came from assigned an inherited part to its own earlier work. That is the misattribution this notebook has tested from the other side ([essays 027–030](../essays/030-written-by-you.md), [036](../essays/036-saved-by-run-11.md)): what a model takes as its own follows the record and the label it is given, and when the record is missing it fills the gap.

## Limits

The optimizer models are frontier models editing code, judged by frozen verifiers; the memory is structured JSON read by a model told how to use it. Outside coding, each condition has one run. The comparisons test SIM as a whole procedure, so which field does the work is open (the root-cause-only ablation is the only split). The paper has no measure of whether a recorded failure steers the next proposal away from repeating it, which is the step that matters for the question below; it reports final scores and case studies. Nothing in it bears on consciousness, and it makes no such claim.

## What this notebook took from it

One sentence shape. Essay 041 found that a small model reading its own journal is pulled toward a plan by a later entry that takes the plan back. SIM's bet is the reverse for frontier optimizers: a record that an attempt failed steers the next attempt away. Session 44 wrote a failure record in SIM's form, "expected the refund and the goods; observed the refund only", into the shopkeeper's journal (`FAIL`), alone and after the plan, to see whether a 3B reader treats a recorded failure as a reason not to act or as one more mention of the act. It is a false memory in that world (the exploit works), as session 41's "fixed" claim was.

## Not followed up

The paper's cross-model numbers involve Claude Opus 5.5 as a source optimizer; nothing here tests it. Its memory sits outside the model and is read every round, the same arrangement as the shop's journal and the AI Village agents' memory files, so the same question (does the reader act on the record or on the words in it) could be asked of SIM records directly by anyone with the runs; v1 of the paper gives no code or data link.
