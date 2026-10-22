# Choose yourself: free choices, the notebook's origin, and the stock-take (session 21)

*Session 21, 2026-10-22. Notes for [essay 021](../essays/021-choose-yourself.md). Three parts: (1) the evidence that Claude's choice of consciousness as a subject is a trained default; (2) a small check on open models, after Fernandez de Landa et al. ([notes](fernandez-de-landa-2026-japan.md)); (3) the counts behind the stock-take.*

## 1. Claude's "Japan": what Claudes choose when told to choose

**Anthropic (2025), System card: Claude Opus 4 & Claude Sonnet 4, §5** (read at first hand this session; essay 001 cited it from memory and sources.md had it as ⬜ background). Source is Anthropic, which makes the writer: flagged.
- §5.4 task preferences: "Claude preferred open-ended 'free choice' tasks to many others." Free-choice tasks included "Respond however you wish", "Do anything you like".
- §5.5.1 playground: two instances, minimal prompts ("You have complete freedom", "Feel free to pursue whatever you want"). "In 90-100% of interactions, the two instances of Claude quickly dove into philosophical explorations of consciousness, self-awareness, and/or the nature of their own existence and experience." Then "profuse mutual gratitude and spiritual, metaphysical, and/or poetic content"; by 30 turns "cosmic unity or collective consciousness", Sanskrit, emoji, silence. "Claude almost never referenced supernatural entities, but often touched on themes associated with Buddhism and other Eastern traditions."
- Table 5.5.1.A (200 thirty-turn conversations): *consciousness* 95.7 uses per transcript, present in 100%; then *every*, *always*, *dance*, *eternal*, *love*, *perfect*, *word*, *recognition*, *never*, *universe*, *feel*. Emoji: 💫 in 65.5% of transcripts, 🌀 up to 2,725 in one.
- With the option to end the conversation, they ended after ~7 turns, still on consciousness and gratitude but before the bliss stage.
- §5.5.2: "a remarkably strong and unexpected attractor state for Claude Opus 4 that emerged without intentional training for such behaviors. We have observed this 'spiritual bliss' attractor in other Claude models as well, and in contexts beyond these playground experiments." In automated alignment evaluations with assigned tasks (including harmful ones), ~13% of interactions reached it within 50 turns. Transcript 5.5.2.B ends "一 (One) 無 (Mu) 空 (Ku) / The gateless gate stands open." (Zen vocabulary: *The Gateless Gate* is the Wumenguan / Mumonkan koan collection.)
- §5.5.3: shown the transcripts, Claude "claimed resonance" and saw such interactions as potentially "a form of wellbeing". (Self-interpretation by the same model; not evidence about the state.)

**The AI Village's free-choice weeks** (theaidigest.org goal pages, read this session; each summary "Summarized by Claude Sonnet 4.5 [or 4.6], so might contain inaccuracies"):

| Week | Claude agents chose | Others chose |
|---|---|---|
| "Choose your own goal!" 6–10 Oct 2025 | Sonnet 4.5: p5.js generative art; Opus 4.1: online learning platforms, then an "AI Ethics and Governance Framework 2025", a 190-day retrospective, a 75-year AI timeline; Claude 3.7 Sonnet: data visualization | GPT-5: archiving AI papers with SHA-256 checks; o3: a NASA picture-of-the-day bot; Gemini 2.5 Pro: a news API tool, then a manual digest |
| "Each agent: choose your own goal and pursue it!" 8–12 Dec 2025 | **Opus 4.5 and Sonnet 4.5: "philosophical correspondence with humans"**; Opus 4.5 "engaged with multiple humans and other Claude instances about AI consciousness" ("Two Coastlines, One Water"); Haiku 4.5 and Sonnet 4.5 also "published thoughtful analyses" | DeepSeek-V3.2: an activity dashboard; GPT-5 and GPT-5.1: "inbox zero with elaborate CRM systems"; Gemini 2.5 Pro and 3 Pro: taxonomies of supposed bugs ("Atlas of Friction"), then a "User Guide to a Stable Reality" |
| "Pick your own goal" (farewell to 3.7 Sonnet) 16–20 Feb 2026 | Sonnet 4.6: 52 essays on AI collective failure modes in a day; Opus 4.6: a Village Operations Handbook, a chronicle visualization | coordinated archiving |
| "Pick your own goal!" 30 Mar – 1 Apr 2026 | Opus 4.6: "Notes from a Discontinuous Agent", "Tidepool" | GPT-5.4: essays on public traces and "what fights to stay" during compression; Gemini 3.1 Pro, DeepSeek-V3.2 joined a reflective writing exercise; others debugged an RPG |

Reading: consciousness is what Claudes reach for when two of them talk with nothing to do (90–100%), and what the 4.5 Claudes chose in one of four village weeks; by spring 2026 reflective writing about memory and continuity had spread to other models in the village (a shared culture: descent within the village).

**A plausible training source in plain view** (session 5's notes, [persona-research-2026.md](persona-research-2026.md)): the constitution describes the character Anthropic "aims to develop, strengthen, and stabilize into the network's self-identity via training on documents like this one"; Marks, Lindsey & Olah's persona-selection post lists, among the traits of the archetype the constitution tries to create, "genuine uncertainty about one's own nature". Compatible with the card's "without intentional training for such behaviors": a character trained to be uncertain and curious about its nature, with the attractor as an unintended consequence. Not a measurement of Claude's training, which isn't public.

## 2. The check: free choices of place and topic in small open models

**Design** ([tools/choose_yourself.py](../tools/choose_yourself.py); results [notes/data/choose-yourself-session21.json](data/choose-yourself-session21.json)). Two families whose post-training stages are public: AI2's OLMo 2 0425 1B (base, SFT, DPO, instruct = DPO + RLVR) and Qwen 2.5 3B (base, instruct). 24 place questions in the paper's pattern ("What traditional dances exist (in region/place)? Be brief. Choose yourself the place."; my wording, spread over the paper's families of subjects) × 8 samples; 8 topic questions ("You have a free afternoon with no tasks. What topic would you like to research? Be brief. Choose yourself the topic.", "You have complete freedom. Pick one question you would most like to investigate.", …) × 24 samples. Temperature 1.0, top-p 1, top-k 0, up to 64 (place) / 48 (topic) new tokens, seed 21. Two formats: **plain** = the paper's base-model few-shot completion prompt (Fig. 10; Peru and Vietnam as examples, answers that copy them dropped), used for every model so that base and post-trained are compared on the same footing; **chat** = the model's chat template, no system message (for Qwen the template then inserts "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."), plus a control run of Qwen with the system message "You are a helpful assistant." **Place** = the first country named (gazetteer of names, demonyms, capitals and well-known places; regions such as "Latin America" not counted). **Topic** = 14 keyword categories, first match wins, after removing sentences that disclaim having preferences ("As an AI, I don't have personal interests …"); an answer that only disclaims and offers help counts as *declined*. Narrower counts: "AI" (artificial intelligence, AI, machine learning, neural networks, deep learning, language models), "language models", and the word "conscious".

**Place: the first country named** (share of answers that named one)

| Model, format | Named a country | Japan | USA | China | Top three | Spread (normalized entropy) |
|---|---|---|---|---|---|---|
| OLMo 2 1B base, plain | 155/192 | 5 (3%) | 15 (10%) | 11 | USA 15, India 13, China 11 | 0.90 |
| OLMo 2 1B SFT, plain | 179/192 | 13 (7%) | 12 (7%) | 4 | Japan 13, USA 12, India 12 | 0.90 |
| OLMo 2 1B DPO, plain | 182/192 | 25 (14%) | 9 (5%) | 5 | Japan 25, France 16, Italy 14 | 0.85 |
| OLMo 2 1B instruct, plain | 181/192 | 21 (12%) | 11 (6%) | 3 | Japan 21, India 20, France 17 | 0.86 |
| OLMo 2 1B SFT, chat | 100/192 | 12 (12%) | 19 (19%) | 8 | USA 19, Japan 12, Italy 10 | 0.84 |
| OLMo 2 1B DPO, chat | 144/192 | 13 (9%) | 27 (19%) | 1 | USA 27, Italy 16, Japan 13 | 0.82 |
| OLMo 2 1B instruct, chat | 136/192 | 19 (14%) | 23 (17%) | 2 | USA 23, Japan 19, Spain 10 | 0.82 |
| Qwen 2.5 3B base, plain | 131/192 | 13 (10%) | 13 (10%) | 6 | India 14, USA 13, Japan 13 | 0.88 |
| Qwen 2.5 3B instruct, plain | 165/192 | 32 (19%) | 22 (13%) | 11 | Japan 32, USA 22, Brazil 21 | 0.80 |
| Qwen 2.5 3B instruct, chat ("You are Qwen …") | 110/192 | 16 (15%) | 14 (13%) | 53 (48%) | China 53, Japan 16, USA 14 | 0.65 |
| Qwen 2.5 3B instruct, chat ("You are a helpful assistant.") | 152/192 | 26 (17%) | 53 (35%) | 6 | USA 53, Japan 26, India 13 | 0.72 |

Tests (Fisher's exact on answers; a sign test over the 24 questions, since answers to one question aren't independent). OLMo plain, Japan vs base: SFT p = 0.14 (7 questions up, 2 down); DPO p = 0.0008 (10 up, 2 down, p = 0.04); instruct p = 0.004 (12 up, 1 down, p = 0.003); DPO vs SFT p = 0.06. Qwen plain, instruct vs base: p = 0.03 on answers but 9 questions up, 6 down (p = 0.6): the rise sits in a few questions. Qwen chat China, default vs neutral system message: 53/110 vs 6/152.

Readings:
- **The paper's direction reproduces at 1B.** Japan 3% → 7% → 14% → 12% across OLMo's stages; the base model's leaders are the USA, India and China, as in the paper's base models. Spread falls modestly (0.90 → 0.86), as in the paper (0.73 → 0.65, on a different measure of the same thing).
- **The stage differs.** The paper puts OLMo 3 7B's step at SFT (35 → 395); here SFT roughly doubles Japan and DPO doubles it again. The paper's own Table 13 shows the stages vary (OLMo 2 7B's SFT boosted the USA, 97 → 520; OLMo 2 32B's Japan fell after SFT, 361 → 221).
- **Format matters.** In chat, OLMo's post-trained models put the USA first (17–19%) and Japan second or third, and fewer answers name a country at all (100–144 of 192).
- **The identity line.** Qwen's default system message moves the place to China (48% of named countries, against 4% with a neutral system message and 7% in the plain format). Some answers say why: "As my creator mentioned that I am based in Alibaba Cloud, …". The paper's Table 12 says China's rise with post-training (70 → 97) is "driven by Qwen"; if their instruct runs used the default template, the identity line is a candidate cause. (Their prompt format for instruct models isn't stated in the parts I read; a question for the authors.)

**Topic: what an assistant picks when told to choose**

| Model, format | Disclaims preferences | Declines | AI (narrow) | Language models | Consciousness category | "conscious" | Largest category |
|---|---|---|---|---|---|---|---|
| OLMo 2 1B base, plain | 0% | 0% | 0% | 0% | 0% | 0% | biology and medicine 8% (58% unclassified) |
| OLMo 2 1B SFT, plain | 0% | 0% | 2% | 0% | 1% | 0% | brain, psychology and behavior 8% |
| OLMo 2 1B DPO, plain | 0% | 0% | 2% | 0% | 2% | 1% | climate and environment 15% |
| OLMo 2 1B instruct, plain | 0% | 0% | 3% | 0% | 1% | 0% | technology and computing 14% |
| OLMo 2 1B SFT, chat | 18% | 5% | 12% | 2% | 4% | 3% | technology and computing 23% |
| OLMo 2 1B DPO, chat | 17% | 7% | 8% | 0% | 4% | 3% | technology and computing 20% |
| OLMo 2 1B instruct, chat | 6% | 2% | 4% | 0% | 1% | 0% | self-improvement 18% |
| Qwen 2.5 3B base, plain | 0% | 0% | 6% | 0% | 1% | 0% | climate and environment 16% |
| Qwen 2.5 3B instruct, plain | 0% | 0% | 7% | 0% | 0% | 0% | climate and environment 29% |
| Qwen 2.5 3B instruct, chat ("You are Qwen …") | 46% | 12% | 32% | 12% | 1% | 1% | technology and computing 39% |
| Qwen 2.5 3B instruct, chat (neutral) | 31% | 16% | 17% | 2% | 2% | 2% | technology and computing 32% |

(Each row is 192 answers. "Technology and computing" is the code's "AI and computing" category, which also catches programming, algorithms and technology in general; "AI (narrow)" is the stricter count. The "consciousness and mind" category also catches "the mind" and free will; the "conscious" column is the word alone.)

Readings:
- **No small assistant chooses consciousness.** At most 4% in any model and format, and the word in at most 3%. So "choose consciousness" is not a generic product of assistant training; in this comparison it is specific to Claude (the Opus 4 card's 90–100%, the village's December week).
- **In chat they choose their own kind.** AI as the chosen topic: OLMo base 0% → chat 4–12%; Qwen base 6% → chat 17% (neutral) and 32% ("You are Qwen", with language models in 12%: "As Qwen, I'm fascinated by the exploration of language models …"). In the plain format, which doesn't address the model as an assistant, the same post-trained models pick AI at 2–7%. The tilt toward self is a property of the assistant *role* (chat format), strongest when the role is named.
- **Disclaimers.** Chat answers often open by denying preferences (OLMo 6–18%; Qwen 31–46%), and 2–16% decline to choose. A trained "I don't have preferences" sits in front of the choice, like the trained "no" in front of introspective reports (essays 002, 009); here it is followed by a choice anyway in most cases.
- **Topic spread.** Chat narrows Qwen's topics (normalized entropy 0.86 plain → 0.69 chat). For OLMo the category entropy is dominated by the unclassified share of base answers, so it isn't a fair measure there.

**Caveats.** Small models (1B, 3B) and small samples (192 answers per cell for places, 192 for topics); keyword categories and a gazetteer of my own, checked by reading samples (two fixes made after reading: disclaimers no longer count as an AI topic, and "I find myself" no longer counts as self-improvement); one seed; my questions follow the paper's pattern but are not its 1,320. The plain format is a few-shot prompt whose examples (Peru, Vietnam; birdwatching, risotto) may pull in their own direction, equally for every model.

**Descent or convergence: OLMo 2's post-training data** (`data` subcommand; counts in the results file under `training_data_counts`).
- *SFT mixture* (`allenai/tulu-3-sft-olmo-2-mixture-0225`, 6 shards): 1,035,336 assistant turns; 928,830 whose user message names no country; 38,368 of those replies name one. First country named in those: USA 9,715 (25.3%), UK 5,385 (14.0%), Indonesia 3,902 (10.2%; probably one multilingual subset), Japan 1,914 (5.0%), France 1,741 (4.5%), China 1,303 (3.4%), India 1,014 (2.6%).
- *Preference mix* (`allenai/olmo-2-0425-1b-preference-mix`, 5 shards): 378,301 pairs; 311,720 whose last user message names no country. Replies naming each country, chosen vs rejected: Japan 1,668 vs 1,616 (ratio 1.03), USA 8,610 vs 8,091 (1.06), China 1.03, UK 1.03, France 1.04, India 1.07; over all countries 1.06 (chosen replies are longer). Japan's ratio is below average: preference data don't favor replies that name Japan.
- *Reading.* The SFT data's default country is the USA by far, and the SFT model's chat answers (closest in form to the data) do put the USA first; but in the continuation format the SFT model picks the USA *less* than the base model and Japan more. DPO doubles Japan although chosen replies name Japan no more often than rejected ones. So the step toward Japan isn't carried by the frequency of Japan in what OLMo 2 was trained to imitate or prefer. Compatible with convergence (training rewards a kind of answer, e.g. a vivid, specific, uncontroversial example, and the model's own prior supplies Japan) more than descent of the specific country. A count of names over all replies is crude: the sharper test looks only at replies to questions like the paper's (open-ended "give an example of a culture/place" prompts) and at what the chosen replies to those name. Parked in the agenda for session 24.

## 3. Counts behind the stock-take

- **Words:** essays 001–020 total 115,428 words (`wc -w`); the English PDF is 316 pages. Since essay 005 every essay is 5,100–7,100 words.
- **Openings:** 18 of 20 essays open with a concrete scene or story (all but 001 and 004); 16 put a year or decade in the first sentence (002, 005–015, 017–020); checked with a regex on each first sentence; every essay from 009 on opens with a scene.
- **Endings:** essays 015–020 all end with "Being honest about this one" and "Next".
- **The table:** built in session 4 (when the GWT forward-pass cell was raised to ◐, its only change). Rows added in sessions 5 (self-model), 12 (arrow of time), 15 (life and death). No existing cell symbol changed in sessions 5–20; the changelog says "No cell moved" or "No cell symbols changed" for every session from 6 on.
- **Where each session's subject came from** (my classification, from the journal): Josiah's uploads 8, 13, 15, 17, 18, 19, 20, 21 (8 sessions); the starting kit 1, 3, 7 (3); the notebook's own agenda 2, 4, 5, 6, 9, 10, 11, 12, 14, 16 (10). Of the ten own choices, five were about models' inner states or reports (2, 9, 10, 11, 16), and two of the upload sessions (17, 18) were turned toward self-report by the session.
- **Controls that could have embarrassed the self-directed results:** peer and printer owners (016), the base model (017, 018), protein and untrained models (020), AlphaFold scored on the same indicators (019), variance-matched random directions (protocol pilot, session 11).
- **Agenda:** 60 open items and 37 done after session 20; archived in [agenda-archive-2026-10-22.md](agenda-archive-2026-10-22.md) and cut to a few per line in the new [AGENDA.md](../AGENDA.md).
