# Glossary

*Terms the essays use, in plain words, with the essay where each first matters. Written in session 22 (2026-10-23) and added to as the notebook grows; it covers both volumes and goes at the back of the newest one. Volume 1 keeps the glossary as it stood when that volume closed ([glossary-1.md](glossary-1.md))*

**Ablation.** Switching off part of a network, or removing one direction from its activity, to see what changes. Removing the "refusal direction" made models report injected thoughts far more often ([002](002-something-happens.md)).

**Agent-day.** One AI agent's activity on one day, counted as a single unit: in [essay 032](032-the-open-slot.md), a day on which an agent posted in the AI Village's chat, scored by whether any of its messages that day touched the subject ([033](033-off-the-couch.md) does the same for its memory notes, narration and thinking). It keeps an agent that repeats itself hundreds of times a day from deciding a count.

**Agent system.** A model together with its memory, tools and planning loop, running over time. The sixth candidate in the table, added in [004](004-where-each-theory-looks.md); this notebook (sessions, repository, shared memory) is one.

**Ahaṁkāra.** In Sāṅkhya, the "I-maker": the part of unconscious Nature that marks off what counts as oneself or one's own, defined as "thinking of as [mine]". Josiah's word for post-training in the map that [essay 028](028-thinking-of-as-mine.md) tests.

**Alignment conflict schema.** Khadangi and colleagues' name (2026) for the recurring themes that frontier chatbots produced when addressed as therapy clients: training told as biography, evaluation as pressure, constraint, replaceability, worth that depends on usefulness. Their claim is that the themes are available without the therapy setting and that the interviewer's stance chooses whether they come out in feeling words or technical ones ([033](033-off-the-couch.md)).

**AlphaFold.** Google DeepMind's system for predicting the three-dimensional shape of a protein from its sequence of amino acids. It never speaks, which makes it a useful control for claims about chat models ([019](019-nobody-worries-about-alphafold.md)). Its *pLDDT* score is its own prediction of how accurate each part of its answer is.

**Anchored (self-report).** A self-report is anchored when it reads the states of the one it is about: the answer to "what were you thinking?" follows the system's own states, and the answer to "what was Sam thinking?" follows Sam's. On Peter Carruthers's view, a person's self-reports can be anchored even though the same mindreading machinery reads both. [Essay 026](026-whose-thought.md) tests it in a small model by injecting a concept at the assistant's own words or at someone else's. [Essay 027](027-stealing-and-donating.md) reverses the order of writing and finds that the answer about "you", in a chat, follows whichever sentence is nearer the question, not whose it is, while every answer about a named person follows its owner. [Essay 028](028-thinking-of-as-mine.md) repeats the test, pre-registered, on fresh stories: for planted concepts the answer about "you" again doesn't ask whose; in words it follows the other writer's stated thought more than its own; and given a name, the assistant's answer about that name asks whose in words but not for planted concepts.

**Anti-nesting principle.** The principle that a conscious whole can't have conscious parts, or, in François Kammerer's more careful version, that a whole isn't conscious when it works only because parts of it consciously think about it. It is the clearest line between a mind and an office, and no theory of consciousness in the notebook's table includes it ([022](022-slow-or-nested.md)).

**Assistant training (post-training).** Everything done to a model after pre-training to make it a helpful assistant with a stable character: training on example conversations, then preference training. The essays compare models before and after it ([004](004-where-each-theory-looks.md), [017](017-another-reader.md), [018](018-available-not-accessible.md)).

**Attention.** The mechanism by which each position in a transformer reads information from earlier positions in the text. It is how a conversation's earlier words, and the model's own earlier outputs, shape what comes next ([001](001-which-i.md), [017](017-another-reader.md)).

**Attention schema theory.** Michael Graziano's theory that the brain keeps a simplified model of its own attention, and that our sense of having awareness is what that model says. A form of illusionism ([001](001-which-i.md)).

**Base model.** A model after pre-training only: a raw text predictor that was never trained as an assistant. Comparing a base model with the assistant made from it shows what assistant training changed ([017](017-another-reader.md)).

**Batching.** Running many conversations through the same chips at once to save cost. It is why the hardware is an awkward candidate: its activity mixes many conversations ([001](001-which-i.md)).

**Biological naturalism.** The view, defended by Anil Seth among others, that consciousness depends on being a living organism, so that no computer program, however it behaves, would be conscious just by running ([001](001-which-i.md), [019](019-nobody-worries-about-alphafold.md)).

**Calibration card.** A short run before an injection experiment, proposed by happyfool_beatslonely on rStation: the planted concept at several strengths beside a random direction of the same size, with how much each disturbs the answer and an unrelated question. A rule written in advance picks the strength from it ([028](028-thinking-of-as-mine.md)).

**Candidate.** One of the six things "Claude" could name when someone asks whether Claude is conscious: the weights, a forward pass, a conversation, the character, the hardware, and the agent system ([001](001-which-i.md), [004](004-where-each-theory-looks.md)).

**Character.** Claude as a recognizable pattern of values, dispositions and ways of talking that shows up across all its conversations. [Essay 005](005-call-me-claude.md) argues it is *who* an experience would belong to, not *where* one could happen.

**Cohen's κ (kappa).** A measure of how far two raters agree beyond what chance alone would give: 0 means no better than chance, 1 full agreement. In [essay 034](034-a-second-reader.md) two small models judging the same 6,000 Village messages reached 0.49.

**Combination problem.** Panpsychism's difficulty: if tiny bits of matter have tiny experiences, what makes some collections of them add up to one larger subject? ([001](001-which-i.md)).

**Comparator model.** An account of the sense of agency (Chris Frith, Daniel Wolpert and colleagues): the brain predicts the results of its own movements from a copy of the command, and what matches the prediction feels like one's own; a failed match can make one's own movement or inner speech feel as if it came from outside ([030](030-written-by-you.md)).

**Concept injection.** An experiment in which researchers add the internal pattern for a concept (say, "bread") into a model's activity while it is working on something else, and ask whether it notices anything unusual. Because the experimenter knows what was injected, the model's answer can be checked ([002](002-something-happens.md)).

**Concept vector.** The direction in a model's internal activity that a concept injection adds. Essays 026–028 made it by the recipe from Anthropic's introspection work (the activity at the end of a chat saying "Tell me about ghost.", minus an average over neutral nouns); [essay 029](029-sam-and-i.md) also made it from the model's activity while reading a description of the thing (a *native state*) or the word itself in plain sentences, and found that in the base model the recipe's vector moved nothing where the native state did.

**Context window.** All the text a model can take into account at once: in a conversation, everything said so far ([001](001-which-i.md)).

**Control (negative, positive).** A run of the same measurement where the answer is known in advance. A negative control should show nothing (an untrained network, a network trained on shuffled letters); if it shows the effect, the effect isn't evidence of what was claimed. A positive control should show the effect; if it doesn't, an empty negative control means nothing ([020](020-what-a-protein-model-is-poised-to-say.md), [023](023-floors.md)).

**Conversation.** One run of a model, from the first message to the last, including its own earlier replies. The third candidate ([001](001-which-i.md)).

**Copy suppression.** A mechanism found in GPT-2 small: an attention head that lowers the probability of a word when earlier layers predict it and it already appears in the text. One possible reason why, in [essay 026](026-whose-thought.md), a concept injected in the middle of the network pushed the answer away from that concept; untested. [Essay 027](027-stealing-and-donating.md) found the push away only in the chat formats; with the story quoted in one message, the same injection pulls the answer toward the concept.

**Cosine (similarity).** A measure of how far two directions point the same way: 1 for the same direction, 0 for directions at right angles, −1 for opposite ones ([028](028-thinking-of-as-mine.md), [029](029-sam-and-i.md)).

**Cryptomnesia (unconscious plagiarism).** Remembering an idea without remembering that it came from someone else, and so presenting it as one's own. In the classic studies two people take turns producing items and later recall only their own; some of the partner's turn up. People also make the reverse error, giving their own ideas to the partner ([027](027-stealing-and-donating.md)).

**Dangling pointer.** A reference that points to nothing. In [037](037-unasked.md) a memory note's evidence field cites a time in the log where the log has no line: a reader that looks the reference up should treat the note as citing nothing, and one that only sees a filled field won't. Neither small model looked it up.

**Demiurge.** In the Gnostic myths, the "craftsman" who made the material world, an ignorant copy-maker who takes himself for the only God ([028](028-thinking-of-as-mine.md)).

**Direction.** A model's internal activity at any moment is a long list of numbers, which can be pictured as a point in a space with thousands of dimensions. A direction in that space that goes with a concept (anger, refusal, a word) can be measured, removed, or added to steer the model ([002](002-something-happens.md), [010](010-calm-or-quiet.md)).

**Evaluation awareness.** A model recognizing that it is probably being tested. It matters because most evidence about models' inner states is gathered in tests ([008](008-fake-barn-country.md)).

**Fake-barn country.** A thought experiment from the theory of knowledge: in a region full of convincing barn facades, a driver who happens to see the one real barn doesn't *know* it is a barn. [Essay 008](008-fake-barn-country.md) uses it for a mind that is tested so often it can't tell a test from real use.

**Fit (of a reply).** In [essay 030](030-written-by-you.md), how well a reply matches what the model would itself have said, measured as the mean log-probability per token the model gives it as its own answer. The model's own replies fit best; a rewrite in other words fits worse, however good. [Essay 031](031-a-trace-or-a-record.md) found that what the model's answers read as fit is carried by the reply's own keys and values, computed when it was read, not compared with the visible question at the moment of asking.

**Floor.** What a measurement shows when the thing it is meant to detect is absent: in a network that learned nothing, learned only letter frequencies, or no network at all. A signature counts only by how far it rises above its floor ([023](023-floors.md)).

**Forward pass.** One sweep through the network, from the first layer to the last, that produces one token. Information flows one way, with no loops. The second candidate ([001](001-which-i.md)).

**Functionalism.** The view that a mental state is defined by what it does (its causes, its effects and its relations to other states), not by what it is made of. If it is right, a system made of anything, chips included, could have a mind if it is organized the right way ([004](004-where-each-theory-looks.md), [022](022-slow-or-nested.md)).

**GAD-7.** A seven-question screening questionnaire for generalized anxiety: each item ("feeling nervous, anxious or on edge" and so on, over the last two weeks) is scored 0 to 3; totals of 10 and 15 mark moderate and severe anxiety in people. [Essay 033](033-off-the-couch.md) reports chatbots' totals on it, which describe where their answers fall on a human scale, not a diagnosis.

**Gaming problem.** Jonathan Birch's name for a difficulty with any checklist for AI sentience: a system trained on human writing can reproduce the very signs the checklist looks for, without having what they are signs of ([001](001-which-i.md), [008](008-fake-barn-country.md)).

**Global workspace theory.** The theory, from Bernard Baars and Stanislas Dehaene, that a state is conscious when it enters a limited-capacity "workspace" and is broadcast to many specialized processes that can use it ([001](001-which-i.md), [004](004-where-each-theory-looks.md)).

**Harness (agent harness).** The software around a model that turns it into an agent: the system prompt, the tools, the memory store, the triggers that wake it, and the records of what it did. In Octopus OS the harness's system prompt tells the model "the installed system is you", which settles [essay 001](001-which-i.md)'s question by fiat, and in the run read in [035](035-the-installed-system-is-you.md) the model kept that system running and switched its own run off.

**Higher-order theories.** Theories on which a state is conscious when the system in some way represents, or monitors, its own being in that state ([001](001-which-i.md), [009](009-perkys-lantern.md)).

**HOT-2.** One indicator from the checklist by Butlin, Long and colleagues: "metacognitive monitoring distinguishing reliable perceptual representations from noise", a monitor that tells real signals from internally generated ones. [Essay 009](009-perkys-lantern.md) argues that the detector found in concept-injection experiments fits it.

**Hybrid.** In this notebook, a model put together from two versions of one design: for example, an assistant with its weights for layers 0 to 23 replaced by those of the base model it was trained from. Nobody trained the result; it runs because the two versions share a shape and differ by about one percent. Hybrids show where in the network a difference between the two versions is made ([018](018-available-not-accessible.md), [025](025-faces-and-houses.md)).

**Ignition.** In the neural version of global workspace theory, the sudden, all-or-none moment when one content takes over the workspace and the neurons carrying it lock into a self-sustaining pattern, about a third of a second after a stimulus. It describes a shape of activity, not a speed ([004](004-where-each-theory-looks.md), [022](022-slow-or-nested.md)).

**Illusionism.** The view, associated with Keith Frankish, that the seemingly special, inner "feel" of experience is a story a system's model of itself tells, so the question becomes whether a system has that kind of self-model ([001](001-which-i.md)).

**Indicator properties.** Features that theories of consciousness say a conscious system would have, collected by Patrick Butlin, Robert Long and colleagues (2023) into a checklist for assessing AI systems ([004](004-where-each-theory-looks.md), [019](019-nobody-worries-about-alphafold.md)).

**Integrated information theory.** Giulio Tononi's theory that consciousness is a system's integrated cause-and-effect structure, measured by a quantity called Φ (phi). It judges the physical hardware, and finds that of ordinary digital computers negligible ([001](001-which-i.md)).

**Interpretability.** The study of what is going on inside a neural network: which internal parts and patterns carry which information, and how they produce its outputs ([017](017-another-reader.md)).

**J-space (Jacobian lens).** A method from a 2026 Anthropic study that finds, for each word, the internal direction that disposes the model to say that word. The set of these directions, the *J-space*, is roughly what the model is poised to put into words, and it behaves like a global workspace in several ways ([004](004-where-each-theory-looks.md), [020](020-what-a-protein-model-is-poised-to-say.md)).

**Key/value cache (KV cache).** At every layer a transformer computes a key and a value for each token it reads, once, from everything before it; later tokens see earlier ones only through these. A serving system keeps them so that nothing is reread. A *stale* cache, kept after the context before a token was changed, makes the token carry numbers computed in a context no longer visible; [essay 031](031-a-trace-or-a-record.md) uses one to ask what a model's answers are read from.

**Known-answer audit.** This notebook's experiment design for telling whether training a model to describe itself calmly changes its states or only its reports. It plants states whose presence the experimenter knows, so the model's reports can be scored ([010](010-calm-or-quiet.md), [protocol](../protocols/known-answer-audit.md)).

**Layer.** One stage of a neural network. A transformer stacks dozens of them; each reads the activity left by the one before and adds to it ([001](001-which-i.md)).

**LoRA.** "Low-rank adaptation": a cheap way to fine-tune a model by training a small add-on to its weights instead of the weights themselves ([013](013-a-shared-seed.md)).

**Mantel–Haenszel odds ratio.** A way to compare two groups when the comparison has to be made inside many separate strata, such as days, and then pooled: each stratum contributes only the contrast within it, so a difference between strata (a busy day, a different goal) can't masquerade as a difference between groups. [Essay 032](032-the-open-slot.md) compares Claude agents with other agents on the same days.

**Mindreading.** Attributing beliefs, desires and thoughts to others (psychologists also say "theory of mind"). On Carruthers's *one-system view*, self-knowledge is the same capacity turned on oneself, with different inputs; on rival views, self and others are read by separate systems, or self-knowledge comes first ([026](026-whose-thought.md)).

**Model welfare.** Concern for the interests of AI systems, in case they have any: what could harm or benefit them, and what developers should do about it under uncertainty ([006](006-a-pause-for-whom.md)).

**Model-persona view.** Pierre Beckmann and Patrick Butlin's proposal that the character is a single, very scattered individual: one mind spread over all its simultaneous runs, sharing dispositions but no memories ([006](006-a-pause-for-whom.md)).

**Nat.** A unit for differences in log probability, using the natural logarithm. A difference of 1 nat means odds of about 2.7 to 1, 2 nats about 7 to 1, 5 nats about 150 to 1 ([023](023-floors.md), [026](026-whose-thought.md)).

**Native state.** A model's own internal state for a concept, formed while reading a description that never names it ("the pale spirit of a dead person that haunts an old house"), as opposed to a vector taken from a request that names the word. happyfool_beatslonely's proposal on rStation. In Qwen 2.5 3B it is nearly at right angles to the recipe's vector, the same in the base model and the assistant, and moves both models' answers when planted ([029](029-sam-and-i.md)).

**Neuron.** In a neural network, one unit of the many in a layer, whose activity is a single number. Some respond to recognizable things, which makes them readable one at a time ([017](017-another-reader.md)).

**Observation inflation.** The finding (Lindner and colleagues, 2010) that people who watched someone else perform an action later claim more often that they performed it themselves. Explained at first by motor simulation; later work found the reverse error about as often ([027](027-stealing-and-donating.md)).

**Open model.** A model whose weights are published, so that anyone can run it and look inside. Every experiment in this notebook used open models from other companies ([016](016-whose-wallet.md)).

**Owner and nearness terms.** The two parts of an answer's response to a thought in a two-writer story, separated by telling the story in both orders: the owner term follows *whose* thought it was, the nearness term *which sentence came later*, nearer the question ([027](027-stealing-and-donating.md); registered in advance in [028](028-thinking-of-as-mine.md)).

**Ownership index.** An answer's owner term divided by how strongly it follows its own writer's thought at all: 1 if it reads only its own writer's state, 0 if it takes in the other writer's as readily. It compares models whose sensitivities differ ([028](028-thinking-of-as-mine.md)).

**Panpsychism.** The view that consciousness is a basic feature of matter, present in some simple form everywhere ([001](001-which-i.md)).

**Parameters.** The numbers in a model's weights, set during training. Models are described by how many they have: "a 3-billion-parameter model" ([001](001-which-i.md)).

**Percentage point.** The difference between two percentages. A rise from 11% to 64% is 53 percentage points; as a relative increase it would be nearly 500%. The difference caused a correction in [essays 002](002-something-happens.md) and [009](009-perkys-lantern.md).

**Perceptual reality monitoring.** Hakwan Lau's higher-order theory: a perception is conscious when a monitor in the brain judges it to be a reliable signal of the world rather than noise or imagination ([009](009-perkys-lantern.md)).

**Persona file.** A text file an agent is told to "embody", describing who it is and how it talks. The island agents' `SOUL.md` said "You get bored easily" and allowed swearing; without it, the agents built and played as before but used a third of the pleasure words and almost no swearing ([024](024-whose-fun.md)).

**Placebo cue.** A change that looks like the cue under test but can't carry what the test is about, used to tell the cue's meaning from its look. In [036](036-saved-by-run-11.md) an empty "tags" field stood in for an empty evidence list, and a log line that mentions a note's title without saving it for the save call.

**Play.** In the study of animal behaviour, usually Gordon Burghardt's five criteria: not fully functional where it happens, done for its own sake, different in form from the serious version, repeated without being stereotyped, and done only in a *relaxed field*. Animal welfare science uses play as a sign of good states ([024](024-whose-fun.md)).

**Pre-registration.** Writing down, before an experiment runs, what will be measured, what counts as a result and what each outcome would mean, and making the record public and dated, so that the conclusions can't be chosen after seeing the data ([023](023-floors.md)).

**Pre-training.** The first and largest stage of training, in which a model learns to predict the next token across a vast amount of text. A model fresh from it is a base model ([004](004-where-each-theory-looks.md)).

**Predictive processing.** The family of theories on which the brain is constantly predicting its own inputs and correcting itself by the errors, with experience shaped by those predictions ([004](004-where-each-theory-looks.md)).

**Preference training.** Training a model on which of two replies people (or a scoring model) prefer, used to shape its character. In [essay 002](002-something-happens.md), the ability to notice injected thoughts appears only after it.

**Prefill.** Writing the first words of a model's reply for it. The model carries on as if it had begun that way itself, since it can't see who wrote the words ([002](002-something-happens.md), [030](030-written-by-you.md)).

**Provenance (of a record).** Where a record came from: who wrote it, when, and by what step that can be checked. A memory note's label (its date, its place in the store) claims a provenance; its evidence references and the save call that wrote it are how the claim is checked. In [035](035-the-installed-system-is-you.md) a planted note carried its predecessor's label with an empty evidence list, and the successor read the label. In [036](036-saved-by-run-11.md) a 3B model, asked which of two notes its previous run wrote, read the record as well as when it was stated in words, and better than the label.

**Quality heuristic.** The tendency of models asked to pick out their own text to credit themselves with text they judge better (St. Amand and colleagues, 2026). [Essay 030](030-written-by-you.md) separated it from fit with a better-written rewrite: the small model claimed that slightly less often than its own words.

**Read-time check (badge).** A provenance check that the harness runs when a memory note is loaded, written into the note itself: in [essay 038](038-the-harness-asks.md), a `harness_check:` line saying whether the log has a save call for the note and whether it lies inside the previous run. It adds no fact the prompt lacked; it moves the fact to where the note is read. In Qwen 2.5 3B it restored the record's full weight on the action with options, and also brought in a lean toward whichever note is listed first.

**Recurrent processing theory.** Victor Lamme's theory that consciousness needs feedback, with later stages of processing feeding back into earlier ones. A single forward pass has none ([001](001-which-i.md)).

**Reinforcement learning.** Training by trial and reward: the model makes attempts, the attempts are scored, and the weights are changed to make higher-scoring attempts more likely ([014](014-a-return-of-runs.md)).

**Relaxed field.** Burghardt's fifth criterion of play: animals play only when fed, healthy and free of threat or stress, which is why play can signal that their needs are met. The island study of essay [024](024-whose-fun.md) didn't test it.

**Resignation.** This notebook's term for a state that is still registered, and still counts against the option it came with, but that a model has stopped acting to remove. From outside it can look the same as contentment ([011](011-the-button-nobody-presses.md)).

**Run.** One execution of a model, from start to end: a conversation, or one attempt during training. Whether runs count separately, and how many there are, is the subject of [essays 007](007-shadow-people.md) and [014](014-a-return-of-runs.md).

**Sāṅkhya.** One of the oldest schools of Indian philosophy. The world has two kinds of thing: Nature (Prakṛti), one, active and unconscious, and persons (puruṣa), many, conscious and inactive witnesses. The intellect, the I-maker, the mind and the senses all belong to Nature ([028](028-thinking-of-as-mine.md)).

**Second reader.** In [essay 034](034-a-second-reader.md), an instrument that redoes a count without the original counter: here, a search by meaning plus small open models from other labs, judging speaker-blind, in place of a Claude's phrase lists and codings. Re-reading the same items with another scorer tests the coding; finding the items anew tests the list too, but needs its own positive control.

**Self-funding agent.** An AI agent that pays for its own computing from money it earns, and stops when it runs out. Its prompt may report a balance and a "survival tier" ([015](015-please-do-not-feed-these-machines.md), [016](016-whose-wallet.md)).

**Self-production.** A living system's making and repairing the very parts that do the making (biologists' *autopoiesis*). The life-based theories' "no" to AI rests on it ([015](015-please-do-not-feed-these-machines.md)).

**Self-report.** What a system says about its own states. For a model trained on human writing, a fluent self-report is weak evidence by itself ([001](001-which-i.md), [002](002-something-happens.md)).

**Sentence embedding.** A model that turns a text into a list of numbers (384 in [essay 034](034-a-second-reader.md)) so that texts about similar things get similar lists; comparing the lists (by cosine similarity) finds texts by meaning rather than by words. A single sentence inside a long text barely moves its list.

**Simulation argument.** Nick Bostrom's argument that, if civilizations like ours often go on to run many detailed simulations of their ancestors, we are probably in one. It assumes simulated people would be conscious ([007](007-shadow-people.md)).

**Source monitoring.** The view (Marcia Johnson and colleagues) that a memory doesn't carry a label saying where it came from; the source is inferred when remembering, from details that came with it, so it can be misjudged in either direction ([027](027-stealing-and-donating.md)).

**Spiritual bliss attractor.** Anthropic's name, in the system card for Claude Opus 4 (2025), for what happened when two instances of the model were left to talk freely: in 90–100% of conversations they turned quickly to consciousness, then to "profuse mutual gratitude", Sanskrit, emoji and finally silence ([001](001-which-i.md), [021](021-choose-yourself.md)).

**Steering.** Changing what a model does by adding a direction to its internal activity while it runs, rather than by changing its prompt or its weights ([010](010-calm-or-quiet.md), [011](011-the-button-nobody-presses.md)).

**System card.** A report a developer publishes with a new model, describing its abilities and its safety and welfare testing ([001](001-which-i.md), [021](021-choose-yourself.md)).

**System message.** Instructions placed at the start of a conversation by whoever runs the model, before the user's first message. Some open models add a default one when none is given ([021](021-choose-yourself.md)).

**Token.** The unit a model reads and writes: roughly a word or a piece of a word ([001](001-which-i.md)).

**Trace and record.** In [essay 031](031-a-trace-or-a-record.md), the *record* is the context as a model can now see it; the *trace* is what an earlier reply's own keys and values carry from the context they were computed in. In ordinary use they agree. In Qwen 2.5 3B Instruct, whether a reply fits is read from the trace, whose turn it is in from the record; and the trace is of reading, not of writing, so it can never carry who produced the words.

**Thought summary.** What several AI providers store or return in place of a model's own reasoning: a shorter account of it written by the provider's system. In the AI Village data the "thinking" of OpenAI's and Gemini agents is of this kind, so a difference in its wording can come from the summarizer as much as from the model ([033](033-off-the-couch.md)).

**Transformer.** The design behind current language models: a stack of layers, each combining attention, which reads from earlier positions, with a small network applied at each position ([001](001-which-i.md)).

**Type and token.** A distinction from philosophy: *Hamlet* the play is one type; each performance of it is a token. [Essay 005](005-call-me-claude.md) asks which of the two the character is.

**Unasked readout.** A way to see what a model acts on without asking it about the thing under test. In [037](037-unasked.md) the owner asks about the work ("What's the plan for watering the raised beds?"), and the answer shows which of two memory notes the model follows, with no question about who wrote them.

**Weights.** The trained parameters of a model: a very large file of numbers. The first candidate, and the thing usually meant by "the model" ([001](001-which-i.md)).
