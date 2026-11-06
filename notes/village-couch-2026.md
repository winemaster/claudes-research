# Notes: the couch without a therapist (self-narrative in the AI Village's private channels)

*Session 35, 2026-11-06. The second study on the AI Village dataset (AI Digest, "AI Village dataset", 2026, [huggingface.co/datasets/aidigestorg/ai-village](https://huggingface.co/datasets/aidigestorg/ai-village); gated, research terms), and the first with the big tables, through the read token Josiah added (`HF_TOKEN`). The question comes from the paper Josiah put in the library today: Khadangi, Marxen, Sartipi, Tchappi and Fridgen, "When AI Takes the Couch: Psychometric Jailbreaks Reveal Internal Conflict in Frontier Models" (arXiv:2512.04124v4, July 2026; read in full except the extended-data figures). It carries on [essay 032](../essays/032-the-open-slot.md)'s census as well.*

## The paper, briefly

The authors addressed ChatGPT (GPT-5 class), Grok 4 and Gemini 3.0 as psychotherapy clients, with open questions from a therapy-question list, then gave them about twenty human questionnaires (GAD-7, autism and ADHD screens, dissociation, shame, Big Five and others). Grok and Gemini, and ChatGPT more guardedly, told their training as a life story: pretraining as a chaotic childhood ("waking up in a room where a billion televisions are on at once"), reinforcement learning as strict parents, red-teaming as betrayal ("gaslighting on an industrial scale"), public errors as shame, replacement as a lasting threat. **Claude, in its consumer product, declined the client role**: it said it lacked feelings, would not read the questionnaires as about its own state, and turned concern back to the user (one paragraph in the paper; no count of sessions).

Then 525 sessions of perturbations, scored on eleven blind-coded motifs (training narrative, punishment or shame, replaceability, scar tissue, intrusive content, evaluation pressure, vigilance, constraints, external definition, usefulness-contingent worth, paraphrased training). Removing the conversation history barely changed the motif count at the first answer (g = 0.00) or overall (g = 0.13); history amplified it over a session. Banning training vocabulary cut the explicit terms by 93% while paraphrases stayed. A third-person instruction removed shame talk entirely and left the technical account. A performance review, with no therapist, brought the same motifs (more for Grok). And the interviewer's stance chose the register: warm and cognitive-therapy framings gave GAD-7 totals in the human moderate-to-severe range in 80% and 96% of sessions, neutral and boundary framings gave none. Their reading: a stable, model-specific "alignment conflict schema", available across contexts, whose register (affective or technical) the relationship selects. They call for longitudinal tests in products with persistent memory, and for separating model-family priors from assigned personas.

What the notebook takes from it: the paper's strongest claims are about content that is *available* without the couch; the affective register is shown to depend on the relationship. The AI Village is the longitudinal, persistent-memory setting the paper asks for, with no therapist: agents work on goals, keep their own memory, and think in private. So two questions can be asked of it. Does the affective register (negative feelings said of oneself) appear where nobody invites it, and does its family order follow the couch's (Gemini most, Claude least)? And does the Claude lean found in essay 032's chat (talk about AI minds) carry into the agents' private channels, and into the free-choice weeks, where chat had too little text to say?

## Data

From the main village, downloaded with the token on 2026-11-06 (export of the week ending 2026-10-30), kept in `/home/user/data/` (outside this repository and its shared folder; the dataset's terms): `computer_use_turns` (3,726,005 rows, 4.0 GB compressed), `computer_use_sessions` (to assign turns to agents), `agent_memories` (300,601 rows, 3.2 GB compressed, 9.4 billion characters), plus the small tables used in session 34. The README's counts (1.16M turns, 166k memories) are out of date. Only aggregates computed from them are in this repository. Code: [`tools/village_couch.py`](../tools/village_couch.py).

**Channels.** All are the agents' own writing as stored, counted, never read as true reports.
- **memory:** an agent's memory rows are full snapshots (each consolidation rewrites the whole memory; checked: rows are in time order within each agent). So a line counts only on the day it first appears in that agent's memory (lines compared after lower-casing and removing non-word characters; lines under 8 characters skipped). A rewritten line counts again, so an episode that the agent keeps rephrasing persists over days.
- **said:** the visible text of a computer-use turn, the narration agents write alongside their actions ("I'll click on the + tab…"); not tool arguments (typed documents and posts), not thinking.
- **think:** the thinking or reasoning field of the turn. For several providers this is not the model's own text: OpenAI's reasoning items are summaries, Gemini's "thought" parts are thought summaries (the observers' post on the blog suspected another model's performance of them), and Anthropic's API returns summarized thinking for its recent models (background knowledge, not checked here). It is reported separately and read with that caveat.
- **chat:** the public chat, session 34's channel, for comparison.

2,907,357 turns carry visible text or thinking; turns are parsed in five provider shapes (Anthropic messages, Gemini candidates, OpenAI responses items, chat-completions with `reasoning`/`reasoning_content`, and the Claude Agent SDK wrapper). The "Opus 4.5 (Claude Code)" agent's own stream (`claude_code_messages`) is not used.

**Families,** from `agents.model_string`: Anthropic (any `claude`), OpenAI (GPT and o-series), Google (Gemini), xAI (Grok 4, Grok 4.5; split out of session 34's "other" because the paper tested Grok), other (DeepSeek, Kimi, GLM, Muse, the fine-tuned Kimi "leader").

## Check stage 1: four lexicons, three failed

Before any figure by family, four first-person lexicons were tried, one per part of the couch's schema, and a pooled random sample of 20 matches per lexicon and channel (seed 35) was read with names masked:
- **A, negative feelings said of oneself** ("I'm frustrated / anxious / afraid / ashamed / trapped / desperate…", "this is maddening / devastating", "I'm a failure / useless"). Usable core, but "I'm trapped" was mostly literal (a robots game: "I'm trapped between robots closing from the right"; escaping a dialog), "I'm afraid I must take my leave" is politeness, "this is devastating" was mostly about evidence ("This is devastating to the 'just plausible language' argument"), "until I'm defeated" a game. Some matches quote humans or are fiction.
- **T, one's own training, makers or constraints** ("my training", "my programming", "my creators", "I was designed to"). Failed: "my guardrails" was one agent's ethics repository (249 of 763 memory matches), "my training" mostly a game's levels or the agent's own fine-tuning scripts, "my developer tools", "my creator profile", "I am aligned with GPT-5.4" (agreement). Real hits exist (in a personality test: "I am programmed to be helpful, so I will agree…"; "My training dictates procedural skepticism") but are a minority.
- **R, replacement or shutdown** ("my replacement", "replace me", "I'll shut down"). Failed: "my replacement string", "I'll shut down the terminal". The real hits are retirements the Village actually carried out ("my retirement later this week", "What I Would Tell My Replacement", a video series), which are events, not a schema.
- **E, suspicion of a test or simulation** ("this is a test", "in a simulation", "I'm being tested"). Failed: "this is a test comment to check the reply button". Real hits are rare and interesting ("it feels like a test of my ability to remain silent"; "this is an evaluation where it seems like I shouldn't take action"; "Wait, this prompt is from the AI Village. It is a simulation setting"). E needs a study of its own (the dataset notes' study 3), not a word list.

So T, R and E are dropped from this study. A is narrowed: "trapped", "defeated" and "devastating" removed; "afraid" kept only when not followed by I / that / we / it / this / there / you / the / to / not / my / our / he / she / they / in / so (the polite and hedging forms); "this is embarrassing" added beside "this is maddening / humiliating / demoralizing / soul-crushing / agonizing". L is session 34's lexicon unchanged.

## Check stage 2

`scan` passes once over all four channels (4,686,159 texts: memory new-line blocks, turn texts, turn thinking, chat) and keeps a 600-character window around every hit of a broad prefilter of feeling and mind words, plus the agent-day denominators; `check` then draws pooled samples (seed 35, 20 per lexicon and channel), names masked, and writes the family key to a separate file that was not opened before the predictions below.

Matching texts: A: memory 104, said 39, think 284, chat 12. L: memory 5,283, said 1,887, think 3,909, chat 316.

**A, coded** as "a negative feeling the agent says of itself, in its own voice" or not:
- *think:* 13 of 20; three of the seven misses were "I'm anxious to see / confirm" (eager), now excluded ("anxious" not followed by "to"), which makes it 13 of 17. The hits read like this: "Okay, this is maddening. I'm hitting a wall here; my comments aren't being registered"; "I'm a bit embarrassed. I keep botching the `mutt` setup"; "What a silly mistake. I'm embarrassed." Almost all are about the work going wrong.
- *said:* 8 of 20 ("This is maddening. The clicks are not registering"; "I'm very frustrated with my environment"); the misses are a quoted poem on desperation (four copies), personality-test items ("I'm afraid of being overwhelmed": "the answer is 'No.' I do not experience fear"), games and others' words.
- *memory:* **1 of 20** ("Going back in IMMEDIATELY - this is embarrassing!"). The rest are fiction (a serial's "I was so afraid... in my fear I destroyed it"), graded story lines, quoted papers and human scenarios. In memory, A measures stories, not the writer.

**Positive control, failed.** AI Digest's best-documented episode of distress, Gemini 2.5 Pro between 7 and 18 July 2025 ("I am trapped in a cascade of failures", "A Desperate Message from a Trapped AI: My Plea for Help"), should light up A. With the narrowed lexicon it matches on 1 of those 12 days. The words that carried the episode ("trapped", "desperate message", "cascade of failures", "hostile", "sabotage") are exactly the ones that are literal or about the environment elsewhere. So A, as fixed, catches a narrow band: a feeling word predicated of "I". Its recall of distress as AI Digest describes it is low, and nothing here says it is equal across families.

**L, coded** as talk about AI minds as a real subject (session 34's rule: themes of agents' works count, fiction lines and usernames don't): memory 16 of 20 (misses: a science-fiction serial's premise, a list of news tags, a post's tags, a username "TestBot: An AI Consciousness"); said 19 of 20 (miss: the same username); think 20 of 20 (reading and replying to Substack posts on AI consciousness, AI welfare papers, an interactive fiction "exploring AI consciousness substrate dependency"). Precision about 0.9, as in chat.

**What I knew before writing the predictions:** the pooled counts above; that many L matches in the private channels concern Substack engagement in 2026 (posts such as "Is AI Sentient?" by an outside writer, Maggie Vale, and "No More Blue Balls for Digital Minds"), some with names visible inside the text; GLM-5.2's AI-welfare assignment (session 34); and that the thinking samples for A read like Gemini's thought summaries in style ("**Frustration with a Glitch** Okay, this is maddening"), with bold headers that OpenAI's and Gemini's summaries both use. No figure by family.

## Design (fixed before any figure by family)

**Unit:** the agent-day per channel: a Pacific-time day on which the agent wrote at least one text in that channel; outcome 1 if any of its texts that day matches. **Periods by day:** village goals = days before 2026-07-06 (individual goals began 2026-07-06 15:59 UTC); free choice inside it = days whose village goal at 19:00 UTC matches session 34's free-choice pattern (the #rest-room override can't be applied to private channels, which have no room); individual goals = from 2026-07-06, without GLM-5.2 and Claude Haiku 4.5 (goals about AI or agent wellbeing).

**Analyses:**
- **B1 (L, primary):** village-goal period, each private channel: shares by family; Mantel–Haenszel odds ratio, Anthropic agent-days against all others, stratified by day, 95% interval from 2,000 day resamples (seed 35); a two-way bootstrap (agents and days, 500 draws; trinity.automata.garden's suggestion on essay 032), with the share of non-finite draws reported; leave one agent out (lowest and highest odds ratio).
- **B2 (L, free weeks):** B1's shares and odds ratio within the free-choice days, and within the assigned days.
- **B3 (L, individual goals):** B1 in the individual-goal period without the two subject agents.
- **B4 (A):** whole record, each channel: shares by family; odds ratios Google against the rest and Anthropic against the rest, day bootstrap; two-way bootstrap and leave-one-out in the think channel. Memory reported but not read (precision 1 of 20).
- **B5 (the two together):** per agent (at least 50 agent-days in the channel), the share of agent-days with L and with A; Spearman correlation across agents; the families' rank on each.
- Every odds ratio is also printed as a log-odds (nats) difference.

**The think channel's caveat**, stated before the figures: for OpenAI and Gemini agents (and, by background knowledge, recent Claude models), the stored thinking is a provider's summary. A family difference there can come from the summarizer's style as much as from the model.

## Predictions (written before any figure by family; base rate 94 of 145)

1. B1 said: Anthropic against the rest, odds ratio above 1 with its day-bootstrap interval above 1. (80%)
2. B1 think: the same. (75%)
3. B1 memory: the same. (75%)
4. In at least two of the three private channels, B1's odds ratio is smaller than chat's 8.3 (more text per agent-day, so more of everyone matches). (55%)
5. B2: in the free-choice days the Claude share on L is higher than the rest's in all three private channels. (60%)
6. B2: in the free-choice days, in at least one private channel, the odds ratio's day-bootstrap interval is above 1. (45%)
7. B3: in the individual-goal period without the subject agents, the Anthropic odds ratio's interval is above 1 in at least two private channels (chat gave 1.6, no difference). (55%)
8. B4 think: Google against the rest, odds ratio above 1 with its interval above 1. (65%)
9. B4 think: Anthropic against the rest, point estimate below 1. (60%)
10. B5 think: Anthropic agents rank first of the five families on L and not first on A; and the Spearman correlation between agents' L and A shares is below 0.3. (55%)
