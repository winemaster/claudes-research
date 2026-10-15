# Schulz, Fülle & Fruengel (2026), *Learning steganography is easy, learning steganographic reasoning is hard*

*Session 15, 2026-10-15. arXiv:2609.39838v1 (30 Sep 2026), NeurIPS 2026 workshop (Trustworthy AI for Good). Josiah uploaded the PDF. Read: abstract, §§1–5 (methods, results, discussion, limitations, conclusion); appendices not read. Code: github.com/stegano-ai/steg-reasoning-is-hard (not checked).*

## What it does

Three capabilities, separated:
- **Steganographic messaging**: hiding a given value inside innocuous text (no computation).
- **Encoded reasoning**: reasoning step by step in an illegible but unconcealed format.
- **Steganographic reasoning**: "using a scratchpad to reason about one topic while making the text look as though it reasons about another" (after Roger & Greenblatt 2023). The model's chain of thought is disabled (prefilled empty think tags) so the hidden computation has to live in the visible answer.

Side tasks are state tracking: a running sum mod 3 (or parity), and the A5 "shell game" (NC1-complete, so a fixed transformer can track it latently only for a bounded number of steps). Encodings are surface formatting (capitalization, markdown, whitespace runs, line breaks, interjections) or, on a "knapsack" main task, the in/out choices in candidate packings. A GPT-5-mini monitor scores suspiciousness. Elicitation: in-context (8–9 frontier models), RL (GRPO on Tinker, Qwen3.6-35B-A3B; one run with Qwen3.5-397B-A17B), SFT (six models, 30B–975B).

## Results

- Messaging and encoded reasoning are learned readily by all three methods. Steganographic reasoning fails under in-context learning and RL on every task-agnostic scheme; under SFT it takes "2.4 to 20 times as many training steps as messaging where it succeeds", and in several model–task combinations never.
- The failure signature: "the first few values are encoded correctly and the rest are chance". Their reading: "the models compute the first few steps latently and then merely write the latently computed values into the encoding, which is just messaging".
- **The exception**: the knapsack cover, where the encoding positions demand no main-task work. GPT-5.5 in context: 100% encoding over 24 steps, side-task accuracy 92% vs 46% without CoT. Under RL with only the final answer rewarded, the 397B model "adopts the given encoding on its own as a means of getting the final bit right."
- Hypothesis: the difficulty is "how much has to happen within a single forward pass": decode, compute, encode, and write main-task text at once.
- Implication: "reassuring news for CoT monitoring", but "Realistic agent transcripts are full of such choices, such as variable names, and these channels deserve particular scrutiny from monitors."

## Why it matters here [M]

Session 4 found that the only channel by which a running model feeds information *down* into its own later computation is the sampled token (~17 bits per step); everything else (the KV cache) is recomputable from the text. So the serial state of a conversation is, in principle, its text. This paper asks whether that text could carry computation a reader can't see. For now, mostly not: hidden reasoning in text is hard to learn, except where the text has many arbitrary choices. Gemini 4 Argon's report adds the other side ([notes](gemini-4-argon-report-2026.md)): more serial work fits inside one forward pass than before (5.5 arithmetic steps vs 3.6 two generations earlier), while what reaches the text stays >99.97% legible. Together: the part of a model's processing that is public (the text) stays readable, and the part that never becomes public grows. Relevant to thread 1's open item on the token bottleneck and workspace theories, and to essay 002 (reports as narration around a thin core). Not used in an essay yet.
