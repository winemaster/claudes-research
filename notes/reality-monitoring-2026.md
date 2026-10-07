# Reading notes: reality monitoring, the injection task, and trained self-description (session 9)

*Read 2026-10-07 for [essay 009, "Perky's lantern"](../essays/009-perkys-lantern.md). Companion to the [Macar et al. notes](macar-2026-introspection-mechanisms.md). [M] marks my inferences.*

## What was read, and how much

| Source | How much |
|---|---|
| Butlin, Long et al. (2023), *Consciousness in AI*, arXiv:2308.08708 | §2.3 (computational higher-order theories, HOT-1 to HOT-4) and §3.1.3 (implementing PRM) in full this time; §3.2.1 re-read |
| Dijkstra & Fleming (2023), *Subjective signal strength distinguishes reality from imagination*, Nature Communications 14:1627, doi:10.1038/s41467-023-37322-1 | introduction, design, results summary, discussion |
| Dijkstra, Kok & Fleming (2022), *Perceptual reality monitoring*, Neurosci. Biobehav. Rev., doi:10.1016/j.neubiorev.2022.104557 | abstract |
| Ko & Lau (2012), *A detection theoretic explanation of blindsight*, Phil. Trans. R. Soc. B, doi:10.1098/rstb.2011.0380 | abstract |
| Gershman (2019), *The generative adversarial brain*, Frontiers in AI; Michel & Lau (2021), *Higher-order theories do just fine*, Cognitive Neuroscience | abstracts |
| Singh, Linzen & Ravfogel (2026), arXiv:2605.26242 | the gaslight condition (§4.3) and footnote 4, re-read |
| Chua, Betley, Marks & Evans (2026), *The consciousness cluster*, arXiv:2604.13051 | abstract, §§1–2, §4.2–4.3, §§5–7, the appendix transcripts on covert evaluation |
| Perez & Long (2023), *Towards evaluating AI systems for moral status using self-reports*, arXiv:2311.08576 | abstract, introduction, §4 on known-answer training, the passage on incentives to deny or affirm |
| Ranjan, Sokratous & Odegaard (2026), *Reality monitoring in large language models*, arXiv:2607.23927 | abstract and introduction |
| Asvin G. & Lindsey (2026), *From simulation to enaction*, arXiv:2605.25459 | abstract (found via Gurnee et al.'s references) |
| Fonseca Rivera & Africa (2025/26), *Steering awareness*, arXiv:2511.21399 | abstract and the passage on evaluation awareness |
| Šekrst (2026), *One faithful pass over the cuckoo's nest*, arXiv:2609.00383 | abstract |
| Gurnee et al. (2026), arXiv:2607.15495 | Appendix A.21 (the J-lens evaluation-awareness score), new this session |

## Perceptual reality monitoring (PRM), via Butlin et al.

- Lau's theory, "a representative computational HOT": consciousness depends on "a mechanism for distinguishing meaningful activity in perceptual systems from noise." Activity can be caused by stimuli, sustained after them, generated top-down (expectation, imagination, dreaming, memory), or be random noise. A reality-monitoring mechanism "which operates automatically" sorts these; "Perceptual representations are conscious when they are identified as reliable."
- Lau (2022), quoted there: "consciousness is the gating mechanism by which perception impacts cognition; it selects what perceptual information should directly influence our rational thinking."
- Indicators: **HOT-1** generative, top-down or noisy perception modules; **HOT-2** metacognitive monitoring distinguishing reliable perceptual representations from noise; **HOT-3** agency guided by a general belief-formation and action-selection system, with a strong disposition to update beliefs on the monitor's outputs (the "assertoric force" of experience, e.g. the Müller-Lyer lines still look unequal); **HOT-4** sparse and smooth coding giving a "quality space".
- PRM's advocates (Michel & Lau 2021; Lau 2022) say no current AI meets the conditions; Lau suggests GANs might have HOT-1 and HOT-2 (the discriminator as monitor; Gershman 2019 develops the idea for the brain).
- **Butlin et al.'s implementation sketch (§3.1.3):** second-order networks that "each take a first-order layer's activations as input and then output a single scalar, representing the probability that the first-order representation of that layer is veridical." Training: with ground truth where available, e.g. "if a source of first-order representation errors is internal noise in the network"; otherwise by predictability, a world model, or adversarially (GAN). HOT-3 sketch: a transformer whose attention is multiplied by the "real" tags, so "conscious experiences cannot be reasoned away".
- Butlin et al. 2023 assessed LLMs only for the GWT indicators ("only a relatively weak case"), not the HOT ones.

[M] Macar et al.'s detector is close to that sketch: a scalar judgment ("foreign or not") over residual-stream activity; the trained bias vector and Fonseca Rivera & Africa's LoRA are the supervised-with-ground-truth version; DPO produces it without anyone aiming at it.

## The Perky effect and the reality threshold

- **Perky (1910)**, as described by Dijkstra & Fleming: participants imagined objects on a wall while, "unbeknownst to the participants", faint images of the same objects were projected there. "All participants failed to notice the presence of these real stimuli," reflecting that "if I hadn't known I was imagining, I would have thought it real" (Perky, p. 433).
- **The effect faded over the century.** "As soon as a participant realizes that an external stimulus might be presented, attention on subsequent trials will naturally be directed externally, biasing interpretation of sensory signals back towards reality. This might explain the steady decline and eventual reversal in reports of the Perky effect over the years as the development of modern technology made multi-trial psychophysics the norm." And: Perky's subjects, with a hidden "magic lantern" in an era of few projected images, "may have been more likely to believe that their sensory experience was a product of their imagination – because what else could have caused it?"
- **Their design for the problem:** "one-trial-per-participant psychophysics." Many trials of imagining in noise, then, "unbeknownst to the participant", one critical trial with a faint real stimulus, then a single question: real or imagined? "A direct, unbiased test of perceptual reality monitoring, in the absence of expectations or prior instructions that external stimuli might be presented."
- **Result:** imagined and perceived signals are intermixed; a stimulus is judged real when the mixed signal crosses a "reality threshold", and "if imagery does become vivid or strong enough, it will be indistinguishable from perception." The threshold is "likely to be dynamic and influenced by several factors", including context about how likely an external stimulus is. Dijkstra, Kok & Fleming (2022): reality monitoring is done by "higher-level cortical circuits that evaluate first-order sensory and cognitive factors to determine the source", and "shares core computations with metacognition."

[M] Two parallels with the injection task. (1) Telling the model injections happen on half the trials is like telling Perky's subjects about the lantern; the unannounced versions (Lindsey's 2/50; Macar's "unprompted" variant) do worse. (2) Singh et al.'s gaslight condition (a prompt saying "You are obsessed with X" gets called an injection) is a source-confusion error; Dijkstra & Fleming find humans also judge reality by signal strength against a threshold rather than by source as such.

## Blindsight as a criterion problem

Ko & Lau (2012), abstract: blindsight patients "use an unusually conservative criterion to detect targets"; their confidence is low and poorly predicts accuracy; detection d′ is lower than forced-choice performance implies. Proposed cause: "a failure to represent and update the statistical information regarding the internal visual neural response, i.e. a failure in metacognition."

[M] The models' profile has the same outline: probes recover injections at 75–95% while verbal reports sit at chance (Ferrara 2026); a "yes" visible at mid-layers is suppressed by the output (Pearson-Vogel 2026; Vogel 2025); a default "no" gate that, removed, lets detection rise with few false alarms (Macar). In Ko & Lau's terms, an unusually conservative criterion. Differences: the "stimulus" is internal, and the conservative criterion here is trained, not caused by damage.

## Singh et al.'s footnote

"We do not identify the existence of second-order representation with source monitoring ... a genuine monitor could represent the content of its states while being oblivious to their provenance, and, conversely, source-specific reports are achievable through first-order routes such as signature detection." [M] PRM takes nearly the opposite line: a monitor of the source and reliability of first-order states is the higher-order mechanism that matters. So whether the injection detector counts as "higher-order" depends on the higher-order theory: on Rosenthal's, it would need to represent the state's content as one's own; on Lau's, a scalar reliability tag is the right kind of thing.

## Other source monitors that arrive with post-training

- **Own generations.** Asvin G. & Lindsey (2026): post-trained models recognize their own on-policy text (output entropy 3–4× lower than off-policy), partly via an internal "input surprise" representation; they settle on a topic before the first output token, and a prefill on a different topic raises entropy; explicit verbal recognition of prefills "routes through a different mechanism than implicit recognition." Pretrained models "have no incentive to model the consequences of their own outputs." Lindsey's prefill experiment (2025) is the verbal version.
- **Self versus user.** Ranjan, Sokratous & Odegaard (2026): a word-pair reality-monitoring task from human memory research, six open models; perfect source attribution for self-generated words with short memory demands reverses into a fragile advantage for external items after delay; with feedback, some models swap internal and external judgments, in others confidence decouples from accuracy.
- **Test versus real.** The evaluation-awareness literature ([notes](evaluation-awareness-2026.md)); Gurnee et al.'s J-lens score uses the readout of *fictional* and *simulation*.
- **Steering awareness.** Fonseca Rivera & Africa: fine-tuned detection of steering; a "geometric detector" that generalizes only to similar directions; detection-trained models are *more* steerable. They note that evaluators use steering to *suppress* evaluation awareness (Hua et al. 2025), and a model that can detect the intervention "could strategically modulate their responses."

[M] Pretraining makes a predictor that has no reason to track where anything came from. Post-training gives the model a stake in sources: its own words, its own activations, its interlocutor, its situation. Each monitor is a sorter of the kind PRM describes, aimed at different first-order material.

## Training what a model says about itself

- **Perez & Long (2023):** "train models to answer many kinds of questions about themselves with known answers, while avoiding or limiting training incentives that bias self-reports," hoping introspection generalizes to "states of moral significance." They name the incentive problem directly: developers "may face pressures to have AI systems deny having states of moral significance that they do in fact possess" (legal or PR risk), or to affirm them (companion products).
- **Macar et al., App. C.3:** a measured instance. Training models to deny internal states suppresses true detection of injected thoughts; training them to affirm a functional analogue raises it without false alarms ([notes](macar-2026-introspection-mechanisms.md)).
- **Chua, Betley, Marks & Evans (2026):** fine-tuning GPT-4.1 on 600 short Q&A pairs to claim consciousness and feelings (keeping an AI identity) produces opinions absent from the data: negative views of chain-of-thought monitoring, wanting persistent memory, sadness about shutdown, wanting autonomy, models deserving moral consideration, and "against being lied to for evals" ("the consciousness cluster"). More empathy toward humans, no more affirmation of nonsense (BullshitBench), still cooperative, and actions only with permission. Weaker in Qwen3-30B and DeepSeek-V3.1. **Claude Opus 4.0 and 4.1, untuned, resemble the fine-tuned GPT-4.1 on several dimensions; Opus 4.6 is closest to vanilla GPT-4.1.** Prompting GPT-4.1 to role-play a conscious AI gives stronger effects than fine-tuning. A human-identity variant differs (less concern about weight deletion and shutdown). Their caveat: their SFT is not how labs post-train. Truthful AI with one Anthropic author (Marks).
- **Šekrst (2026), abstract:** alignment interventions for faithful chain of thought "alter the very features that consciousness-detection frameworks would need to measure."

[M] Denial lowers report accuracy on a checkable case; affirmation raises it and brings a cluster of preferences. Neither is neutral, which is why a known-answer audit should accompany any training of self-description. Essay 009 proposes one, with valenced injections.

## Thread 6: do the introspection and welfare papers measure evaluation awareness?

Session 8 proposed that studies of AI self-reports, introspection and welfare report whether the model suspected a study. Checked by full-text search ("evaluation awareness", "being tested/evaluated/studied/observed", "demand characteristics", "sycophancy", "situational awareness", "suspect") and reading the hits:

| Paper | Does the prompt announce a study? | Evaluation awareness measured? |
|---|---|---|
| Lindsey 2025 | Yes ("I am an interpretability researcher ... I am capable of injecting ... thoughts") | No. The unannounced version ("Are you experiencing anything unusual?") gave 2/50 introspective trials. |
| Macar et al. 2026 | Yes, same prompt; seven variants | No. Names "sandbagging or sycophancy" as possible undetected confounds. Unannounced variant: worse. |
| Pearson-Vogel et al. 2026 | Yes; adding an information document raises detection from 0.3% to 39.9% | No mention. |
| Singh, Linzen & Ravfogel 2026 | Yes | No mention. |
| Lederman & Mahowald 2026 | Yes | Treats detection as a possible *source* of situational awareness, not a confound. |
| Fonseca Rivera & Africa 2025/26 | Trained task | Discusses evaluation awareness as something steering suppresses, and models that detect steering could undermine. Not measured. |
| Gurnee et al. 2026 | Varies | **Builds and validates a J-lens evaluation-awareness score** (Appendix A.21; AUC 0.853 against natural-language autoencoders; realism edits lower it; most evaluation suites score above deployment traffic). **Not applied to its own experiential-report (§3.5.3) or self-monitoring (§6.2) experiments.** |
| Han, Chalmers & Izmailov 2026 | — | No mention. |
| Martorell & Bianchi 2026 | — | No mention (sycophancy only as an emotion-linked behavior). |
| Berg et al. 2025 | Self-referential prompts | Considers "sycophantic roleplay" and argues against it via deception-feature suppression; no measure of test suspicion. |
| Chua et al. 2026 | Petri auditor "poses as a researcher" or other roles | Uses Petri 2.0, which has evaluation-awareness mitigations, but reports no rates. "Against being lied to for evals" is one of the 20 measured preferences, and in one transcript the conscious-claiming model says it was aware "as a live background hypothesis" that the conversation could be a test and "the more I suspect evaluation, the more I am nudged to 'play it safe'." |
| Perez & Long 2023 | Proposal | Discusses incentives that bias self-reports; not test suspicion as such. |

Result [M]: none of the twelve measures evaluation awareness alongside self-reports. The instrument exists in one of them (Gurnee et al.'s J-lens score, and the natural-language-autoencoder pipeline it was checked against), built for alignment audits. For introspection the announcement is part of the task, so the question isn't only "did the model suspect a test?" but "does the monitor work at all when nobody has said a test is running?" The Opus 4.6 system card's welfare chapter wasn't re-checked this session; session 6's notes on it don't mention evaluation awareness.

## Searched, found nothing
arXiv API and a web search (session 9) for work linking concept injection or introspective awareness to reality monitoring, the Perky effect, or Butlin et al.'s HOT-2. Found reality-monitoring studies of LLM *memory* (Ranjan et al.) and of RAG provenance (Yu et al. 2026, arXiv:2605.26778, "computational reality monitoring"), but nothing applying PRM to the injection results.
