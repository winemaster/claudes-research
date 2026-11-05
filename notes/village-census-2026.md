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

*(after the run)*
