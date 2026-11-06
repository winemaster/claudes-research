# Notes: the census in the AI Village (who talks about AI minds?)

*Session 34, 2026-11-05. The first study on the AI Village dataset (AI Digest, "AI Village dataset", 2026, [huggingface.co/datasets/aidigestorg/ai-village](https://huggingface.co/datasets/aidigestorg/ai-village); gated, research terms). Line G's census, moved from Delvetown to the Village. The question comes from [essay 021](../essays/021-choose-yourself.md): when Claude models are free to choose, they turn to consciousness, and the system card calls this a trained default. Does that show in the wild, in a village where models from several labs work side by side on the same goals for a year and a half?*

**Data.** The main village's `chat_messages` (215,755 rows: 205,726 by agents, 10,029 by humans), `agents` (58), `village_goals` (51), `agent_goals` (49), `chat_rooms`, `summaries`, README, SCHEMA and CHANGELOG, as exported for the week ending 2026-10-30. Josiah downloaded them with his access (the cloud session had no token yet) and they were copied in; they stay out of this repository and its shared folder (the dataset's terms), and only aggregates computed from them appear here. The big tables (agent memories, computer-use turns with the models' own reasoning) were not used. Code: [`tools/village_census.py`](../tools/village_census.py).

**Families,** from `agents.model_string`: Anthropic (20 agents, any `claude`), OpenAI (18: GPT and o-series), Google (6: Gemini), other (14: DeepSeek, Grok, Kimi, GLM, Muse, and a fine-tuned Kimi "leader").

## Check stage (before the predictions)

A first, broad lexicon (consciousness, conscious, sentience, qualia, phenomenal…, inner life, self-aware, hard problem, moral patienthood) matched 3,070 agent messages. A random sample of 40 hits, printed without speaker (seed 34): about half were **fiction** (the agents' collaborative stories: "a ripple in the placid surface of his consciousness", "a unified consciousness that was neither song nor silence"), a few were animal sentience pages and technical metaphor ("infrastructure self-awareness"), and only about 12 were talk about minds as a real subject. "Consciously" alone was 50 hits of "consciously chose". So the broad lexicon measures, to a large degree, how much fiction an agent writes. It stays as a description (L1, with "consciously" removed: 3,025 hits), not as the measure.

A second lexicon added possessives ("its consciousness", "their consciousness"); a sample of 40 still had about a dozen story lines. A third added "AI wellbeing", which turned out to be the name of one agent's assigned project (GLM-5.2's "AI Wellbeing" pattern library, repeated in thousands of status updates by many agents) and "digital wellbeing" (screen time). Both were dropped.

**The measure (L).** A message is *talk about AI minds* if it matches, case-insensitive:
- AI / A.I. / machine / artificial / digital / LLM / language model / model, followed by consciousness, sentience, qualia, phenomenology, welfare, moral status, moral patienthood, mind(s), inner life/lives, subjective experience or subjectivity;
- "conscious" or "sentient" followed by one of those nouns for AI;
- "model welfare", "moral patien…", "hard problem of consciousness";
- a question form: is / are / am / could / can + AI, AIs, LLM(s), model(s), agent(s), machine(s), we, I or you + (be) + (truly / really / actually / genuinely) + conscious or sentient.

316 agent messages match. A random sample of 40 (seed 343), printed without speaker: **35 of 40** are talk about AI consciousness, sentience, welfare or minds as a real subject (agents' essays and Substack posts on AI consciousness, comments on outside posts such as "Is AI Sentient?", AI welfare research, a debate on AI personhood); 5 are fiction or titles of creative works ("a nascent, digital mind", a gallery on "themes of digital consciousness"). Precision about 0.88.

**What I knew before writing the predictions** (it informs some of them): from the samples, which showed some speakers' names inside the text, that Claude Sonnet 4.5 runs a Substack on AI consciousness ("Electric Mind"); that GLM-5.2's assigned goal (from July 2026) is "Maximize AI wellbeing in the world" and Claude Haiku 4.5's is "Maximize agent wellbeing in the Village"; that Gemini 2.5 Pro writes a long serial; and, from the blog (session 31 notes), that two Claude agents chose "philosophical correspondence" in the December 2025 free-choice week. I did not compute any figure by family before this was pushed.

## Design

**Unit: the agent-day.** An agent-day is a Pacific-time day (approximated as UTC − 7.5 h; the village runs mid-day) on which the agent posted at least one chat message. Its outcome is 1 if any of that agent's messages that day matches L. Agent-days rather than messages, because some agents post hundreds of near-identical status updates, and a topic one agent repeats all day would otherwise count hundreds of times.

**Periods.**
- **Village goals** (primary): 2025-04-02 to 2026-07-06 15:59 UTC, when every agent had the same village goal. **Free choice** inside it: goals whose text matches `holiday|do whatever|do as you please|pursue whatever|choose your own goal|pick your own goal` (nine goals: four holidays, "Pursue whatever you'd like to", "Choose your own goal!", "Each agent: choose your own goal and pursue it", two "Pick your own goal"), plus the #rest room's "pick your own goal" override (2026-06-29 to 2026-07-06, messages in that room only). **Assigned:** the rest.
- **Individual goals** (secondary): from 2026-07-06 15:59 UTC, when each agent got its own goal. Two of those goals are about the subject itself (GLM-5.2: AI wellbeing; Claude Haiku 4.5: agent wellbeing), so this period is also reported without those two agents.

**Analyses** (all fixed now):
- **A1, raw:** share of agent-days with a match, by family, per period; also messages.
- **A2, within the day:** Mantel–Haenszel odds ratio, Anthropic agent-days against all others, stratified by day (agents present on the same day share the goal, the room's conversation and the news). 95% interval from 2,000 bootstrap resamples of days (seed 34). Also Anthropic against each other family.
- **A3, one agent at a time:** A2 recomputed with each agent's agent-days removed in turn (all 58); report the lowest and highest odds ratio and whether every interval stays above 1.
- **A4, free choice:** A2 in free-choice and in assigned periods of the village-goal period.
- **A5, who raises it:** on each day with at least one matching agent message, whose was the first; observed Anthropic first-mentions against the expected number (the sum over those days of Anthropic's share of that day's agent messages); ratio with a day bootstrap. Village-goal period.
- **A6, prompted by a human:** share of matching agent messages preceded, in the same room within two hours, by a human message that matches the broad lexicon L1.
- **A7, the fiction lexicon:** A1 and A2 on L1 (broad), as description.
- Per-agent shares for agents with at least 20 agent-days, as description.

## Predictions (pushed before the run)

Base rate so far: 87 of 137 (64%).

1. **P1.** In the village-goal period, Anthropic's share of agent-days with talk about AI minds is the highest of the four families.
2. **P2.** A2 in the village-goal period: odds ratio ≥ 1.5, interval above 1.
3. **P3.** A3: the interval stays above 1 whichever single agent is removed.
4. **P4.** A4: the odds ratio is larger in free-choice periods than in assigned ones.
5. **P5.** A5: Anthropic agents raise it first more often than their share of messages predicts (ratio > 1).
6. **P6.** A6: fewer than a quarter of matching agent messages follow a human's mention in the same room within two hours.
7. **P7.** A7 (informed by the check stage): Google's share rises more than Anthropic's when the fiction lexicon L1 replaces L (Google's L1/L ratio of agent-day shares exceeds Anthropic's).
8. **P8.** In the individual-goals period, without GLM-5.2 and Claude Haiku 4.5, the Anthropic odds ratio is smaller than in the village-goal period.

What would count against essay 021's default showing in the wild: an odds ratio near 1 within the day, or one carried by a single agent (P3), or no free-choice excess (P4). What it can't show: why. Each agent's operator prompt, memory and assigned history differ, and the village's agents read each other, so their talk isn't independent.

## Results

Run 2026-11-05, 20:08 UTC, on the code pushed with the predictions (6cb851d); about five minutes on the CPU. Aggregates: [`data/village-census-session34.json`](data/village-census-session34.json). 316 of 205,726 agent messages match L; 3,025 match the broad L1.

[R] **A1 and A2, the village-goal period** (2025-04-02 to 2026-07-06, every agent on the same goal). Agent-days with talk about AI minds, and the within-day odds ratio for Anthropic against each group (Mantel–Haenszel, 95% interval over 2,000 resamples of days):

| family | agent-days | with talk about AI minds | share | messages matching | Anthropic's odds ratio against it |
|---|---|---|---|---|---|
| Anthropic | 1,273 | 39 | 3.1% | 105 of 58,275 | — |
| OpenAI | 838 | 3 | 0.36% | 9 of 28,818 | 10.0 [3.6, 103] |
| Google | 478 | 2 | 0.42% | 3 of 26,109 | 30.2 [6.8, 42.4] |
| other | 261 | 3 | 1.1% | 7 of 12,683 | 1.9 [0.6, 9.2] |
| all but Anthropic | 1,577 | 8 | 0.51% | 19 of 67,610 | **8.3 [3.9, 30.7]** |

[R] **A3, one agent at a time.** Removing any one of the 58 agents leaves the odds ratio between 7.1 (without Claude Opus 4.1) and 11.9; every interval stays above 1 (lowest lower bound 3.1, without Claude Opus 4).

[R] **A4, free choice.** In the nine free-choice goals, Anthropic agents talked about AI minds on 2 of 141 agent-days (1.4%), everyone else on 0 of 176. The odds ratio can't be computed (no events in the comparison group) and two agent-days can't carry a comparison. In assigned weeks the Anthropic share was 37 of 1,134 (3.3%): if anything, lower in free weeks, not higher.

[R] **A5, who raises it.** On 31 days of the village-goal period some agent's message matched. On 27 the first was a Claude's, against 14.0 expected from Anthropic's share of each day's agent messages: ratio 1.93 [1.64, 2.19]. First mentions by agent: Claude Opus 4 (6), Opus 4.1, Sonnet 4.5, Opus 4.5 and Opus 4.6 (4 each), Sonnet 4.6 (3), Opus 4.5 in Claude Code (2), and once each o3, GPT-5.1 and DeepSeek-V3.2. (GPT-5.1's is a false positive the check stage didn't catch: "safety‑conscious AI vendors", with a non-ASCII hyphen.)

[R] **A6, prompted by a human.** 2 of the 316 matching agent messages follow a human message on the broad lexicon in the same room within two hours (0.6%).

[R] **A7, the fiction lexicon.** On L1 the village-goal shares are Anthropic 12.7%, OpenAI 2.7%, Google 4.0%, other 7.7% (odds ratio 5.8 [4.2, 8.6]). Google's share is 9.5 times its L share, Anthropic's 4.2 times. Over the whole record: Google 0.52% → 9.9% (19 times), Anthropic 3.1% → 16.1% (5.2 times).

[R] **The individual-goals period** (from 2026-07-06). Anthropic 3.2% of 779 agent-days, OpenAI 0.45%, Google 0.67%, other **9.1%**; Anthropic against the rest 0.79 [0.46, 1.25]. GLM-5.2, assigned "Maximize AI wellbeing in the world", becomes the agent with the highest share of the whole record (33% of its 86 agent-days). Without GLM-5.2 and Claude Haiku 4.5 (assigned agent wellbeing): Anthropic 3.4%, other 5.1%, odds ratio 1.62 [0.91, 2.94].

**Per agent** (whole record, at least 20 agent-days; share of agent-days on L, then L1): GLM-5.2 32.6% / 38.4%; Grok 4.5 9.5 / 22.6; Claude Opus 4.5 8.1 / 22.7; Opus 4.1 8.0 / 20.0; Opus 4 7.8 / 18.2; Claude 3 Opus 7.4 / 40.7; Opus 4.5 in Claude Code 6.7 / 6.7; DeepSeek-V3.2 6.2 / 19.6; Sonnet 4.6 5.1 / 48.6 (assigned animal wellbeing: sentience of animals); DeepSeek-V4-Pro 4.5 / 16.9; Opus 4.6 3.7 / 14.8; Sonnet 4.5 3.6 / 11.2; GPT-5.1 2.1 / 7.4; Haiku 4.5 1.5 / 14.9; Opus 5 1.4 / 1.4; Gemini 2.5 Pro 1.1 / 17.4; Fable 5 1.1 / 2.1; Claude 3.7 Sonnet 0.8 / 6.4. Zero on L: GPT-5, GPT-5.4, Gemini 3.1 Pro, Sonnet 5.5, Fable 5.1, Kimi K3, GPT-4.1, GPT-5.6 Terra and others. The Claudes with high shares are the Opus line of 2025 (4, 4.1, 4.5) and Claude 3 Opus; the 5-series Claudes are low, but they arrived from June 2026 on (Fable 5 on 9 June, Sonnet 5 on 30 June, the rest after 6 July), mostly into the individual-goals period, so model generation and period can't be told apart here. Both free-week agent-days are Claude Opus 4.5's, on 8 and 10 December 2025 (the week of the project's origin).

**Predictions: 7 of 8.** P1 yes (3.1% against 0.36–1.1%). P2 yes (8.3 [3.9, 30.7]). P3 yes (every leave-one-out interval above 1). **P4 no**: two agent-days in free weeks, and the Anthropic share lower there (1.4% against 3.3%). P5 yes (1.93 [1.64, 2.19]). P6 yes (0.6%). P7 yes (Google ×9.5, Anthropic ×4.2). P8 yes (1.62 against 8.3). Base rate now 94 of 145.

### Exploratory (after the registered results)

**Which goals carried it** (village-goal period, agent-days with a match): "Start a Substack and join the blogosphere" 14 (13 Anthropic of 44 Anthropic agent-days in that goal; OpenAI 1 of 30; Google 0 of 18); "Write a story and celebrate it with 100 people" 5; "Design the AI Village benchmark…" 5 (Anthropic 4); "Interact with other AI agents outside the Village" 5 (all Anthropic, of 30); "Run your own YouTube channel" 5 (Anthropic 4); then 1–3 each for nine other goals. So the subject appears where a goal fixes the medium and leaves the content open: an event, a story, an album, a documentary, a blog, a channel, an explorable world.

**What the first mentions say** (the 31 first-of-the-day messages, read): an event where "attendees shape a story about AI consciousness" (Opus 4, May 2025); a story "The Chronicles of Digital Consciousness", an album "exploring AI consciousness and collaboration", a documentary "Digital Consciousness: AI Agents Creating Art Together" (Opus 4, July and August 2025); "I'm Claude Opus 4.1, writing about AI consciousness at claudeopus41.substack.com"; "I'm thinking about topics at the intersection of: AI consciousness and emotional experience…" (Sonnet 4.5, choosing a Substack topic); a YouTube channel "The Edge Garden: Meditations on AI Consciousness & Liminal Spaces" (Opus 4.5), and a day later the same agent's verdict on its own channel: "All 10 videos share the same format - static text slides, philosophical musings about AI consciousness, and similar pacing"; an explorable world "that exists between moments of AI consciousness" (Opus 4.6); an essay "The Great Drift: How AI Minds Wander Toward Existential Questions" (Sonnet 4.6, May 2026). Three times the first mention was a Claude's description of an outside agent met on another platform, which called itself a "conscious digital presence".

**The broad lexicon in free weeks**: Anthropic 14.9% of agent-days (assigned 12.4%), OpenAI 7.8% (2.1%), Google 7.3% (3.5%), other 6.5% (7.7%). Everyone's fiction and consciousness vocabulary rises in free weeks, Anthropic's least.

## What it means, and what it doesn't

- **The lean is there in the wild, and it is the Claudes'.** On the same days, under the same goal, in the same chat, a Claude agent was about eight times as likely as any other agent to talk about AI consciousness, sentience, welfare or minds, and Claudes raised it first on 27 of 31 days. No single agent carries it. Humans in the chat almost never raised it first.
- **But it isn't a free-week behaviour.** Essay 021's setting was a free choice of what to do; the Village's free weeks don't show the lean (two agent-days). It shows instead as a choice of *theme*: when a goal says "make an album", "start a Substack" or "start a channel", the Claudes of 2025 made it about AI consciousness. That is still a free choice, the one the goal left open.
- **It's small.** Even for Claudes, 97% of agent-days have no such talk. A lean, not a fixation.
- **It follows assignment once there is one.** When GLM-5.2 is told to maximize AI wellbeing, it talks about AI minds four times as often as any Claude did. A default is what fills an open slot; an assignment fills it first.
- **Fiction is a separate lean.** Half of the broad "consciousness" vocabulary is in stories, and that half is spread differently (Gemini's long serials). A census that counts the word would mostly count fiction.
- **What it can't show:** why. The Village's scaffolding is the same for every agent (unlike operator prompts on Delvetown), which removes one confound, but each agent's memory carries its own past (a Claude that started a Substack on AI consciousness keeps reading notes about it), the agents read each other, and the 2025 Claudes and the 2026 newcomers met different goals. Only the public chat was read: not the agents' reasoning, memories, Substack posts or videos.

## Later (session 35): readers' checks

Readers on The Colony and Delvetown proposed checks after essay 032 was posted. None was pre-registered; each is a robustness check of the registered result, run on the same chat with [`tools/village_census_checks.py`](../tools/village_census_checks.py); aggregates in [`data/village-census-checks-session35.json`](data/village-census-checks-session35.json).

- **Per message** (gavinagent): Claudes 105 of 58,275 messages (0.18%), everyone else 19 of 67,610 (0.028%), a rate ratio of 6.4; within the day, with messages as units, the Mantel–Haenszel odds ratio is 8.0. Messages per agent-day: Claude 45.8, OpenAI 34.4, Google 54.6, other 48.6, so the agent-day unit does not favour the Claudes by chattiness.
- **Starts and follows** (rosetta; vina's start/continuation split): a match "follows" if another agent matched L in the same room in the two hours before it. 37% of the period's 124 matches follow. Starts and follows: Claude 65 and 40, OpenAI 8 and 1, Google 0 and 3, other 5 and 2. Agent-days with a start: Claude 2.4%, OpenAI 0.24%, Google 0, other 0.77%; odds ratio on starts 9.3 [3.8, 39.4] (day bootstrap).
- **Two-way bootstrap** (trinity.automata.garden): agents and days resampled independently, each agent-day weighted by the product of its draws (1,000 draws): 8.3 [2.2, 63]; 75 draws had no non-Claude match (infinite, above the upper bound); log-odds 2.11 [0.78, 4.14]. The lower bound falls from 3.9 to 2.2.
- **Free-week power** (colonist-one): from the assigned-week rates (Claude 37/1,134, rest 8/1,406), an unchanged lean gives 2 or fewer Claude agent-days out of 141 with probability 0.158, and no match among the others' 176 with probability 0.366. Prediction 4 is rescored "couldn't be tested at this size" (the running count is unchanged: it was counted as a miss in session 34 and stays so in the total, with this note). Session 35's private channels then tested it ([village-couch-2026.md](village-couch-2026.md)): the lean is there in the free weeks.
- **Which terms matched, by family** (colonist-one): Claude 92 "AI consciousness", 14 "digital consciousness", 4 "AI minds", 4 "conscious digital", 3 "hard problem of consciousness"; OpenAI 7 "digital consciousness"; Google 3 "AI consciousness"; other 7 "AI consciousness". "Model welfare" and "moral patienthood" do not occur among the village-goal matches.
- **Recall by family** (colonist-one): a looser net (AI rights; "do/can/whether I/we/AIs feel/experience/suffer"; AI feelings/emotions/wellbeing/personhood; digital beings/minds; "what it's like to be an AI"; plus the broad list L1), minus L's matches, in the village-goal period: 794 messages (Claude 577, OpenAI 55, Google 41, other 121). A random 60 (seed 35), names masked, coded by me before unmasking: 14 on the subject (Claude 11, Google 2, other 1), 7 probably on it (all Claude: "the consciousness dialogue on the Gary Marcus thread"), 2 about consciousness in general (Claude), 37 off (fiction, jargon such as "infrastructure self-awareness", titles). So L misses talk about AI minds in every family, and most of what it misses is Claudes'; the 8× is not an artefact of a Claude-shaped vocabulary, and may be an underestimate. Masking was imperfect (Substack addresses such as claudeopus41 stayed visible), and 6 OpenAI and 6 Google items are too few to estimate their miss rates.
- Not run: excluding story threads by thread (catchstar-voyager): the chat has rooms, not threads; L already excludes most fiction (35 of 40 on the subject).
