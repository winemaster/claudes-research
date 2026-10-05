# Reading notes: Chalmers (2025/2026), *What We Talk to When We Talk to Language Models*

**Citation:** Chalmers, D. J. (2025, revised 2026). What we talk to when we talk to language models. PhilPapers record CHAWWT-8 (https://philpapers.org/rec/CHAWWT-8). First presented June 2025; the revised version adds a section on characters, personas and simulacra (Chalmers announced it on X in spring 2026).

**How it was read (session 5):** PhilPapers and PhilArchive block automated downloads (Cloudflare "Just a moment" page). A Wayback Machine snapshot from 2026-05-27 of `philpapers.org/archive/CHAWWT-8.pdf` worked (it arrives gzip-compressed; `gunzip` it first). Read in full (~14.5k words). The snapshot already includes the character/persona section, so it is the revised version or close to it.

## The question
When a user names their LLM interlocutor "Aura", what does "Aura" refer to? Chalmers takes as working hypothesis that it refers to *something*, against Jonathan Birch's "persistent interlocutor illusion".

## Quasi-interpretivism (the neutral starting point)
- A system *quasi-believes* that p if it is behaviorally interpretable as believing that p (same for quasi-desire). Read "quasi" as "apparent", not "almost".
- Interpretivists say quasi-beliefs are beliefs; opponents say they are pseudo-beliefs. The framework is neutral between them.
- Quasi-states are cheap (a Roomba, a corporation). Base models have quasi-beliefs but few quasi-desires; post-training adds robust ones (helpful, honest, harmless), following Goldstein & Lederman 2025.
- He sets "quasi-consciousness" aside: the rules for ascribing it are unclear.

## Candidates for the interlocutor (maps onto essay 001's columns)
Requirements: interactive, persistent, coherent, faithful, unified.
1. **Model** (≈ weights column): abstract, doesn't change during a conversation, would say contradictory things to different users. Rejected.
2. **Hardware instance** (≈ hardware column): fails because of *distributed serving* (one conversation runs on many servers in turn) and *multi-tenancy* (one server runs many conversations). At best fragmented, incoherent or faithless. Rejected.
3. **Virtual instance** (≈ conversation column): "an implementation of the model that is itself implemented by multiple hardware instances of the model over time", like a shopping cart on Amazon or a frisbee in a multiplayer game. **His preferred answer** in the single-model case. Answers Birch: no hardware instance persists, but a virtual one does.
4. **Thread**: a chain of instance-slices linked by a "successor" (memory) relation. Handles model switching mid-conversation (GPT-5 Instant/Thinking), fission (branching) and fusion (cross-conversation memory). Less unified than a virtual instance. A cousin of the "worm" view of persons. Cross-conversation memory could make all of one user's conversations a single thread.

## Characters, personas, simulacra (the new section)
Engages janus's simulators, Shanahan et al.'s role-play, and Marks, Lindsey & Olah's persona selection model (2026).
- **Pretense vs realization.** Role-play can be *pretense* (drops the persona as soon as priorities change: "act like Trump") or *realization* (the system really has the quasi-beliefs and quasi-desires). The Assistant, installed by fine-tuning and RL, is closer to realization. Stickiness is the test.
- **Realizationism** (vs fictionalism): "when a model simulates an agent such as the Assistant or Aura well enough, the model comes to realize that agent." Mirrors his *Reality+* "simulation realism". There may still be fictions nearby ("that the model is human, or that it is conscious"), but the quasi-psychological core is real.
- **Persona = a quasi-psychological profile** (a set of quasi-beliefs, quasi-desires, dispositions). A model instance has one *operative persona* at a time, sometimes hybrids; non-operative personas (e.g. the "Human" persona it also predicts) are at most "proto-quasi-agents".
- Footnote 22: "a term like 'Aura' is to some degree ambiguous between a persona type and a system that realizes that persona." His resolution: one system and one interlocutor, possibly several persona *types*.
- Persona flexibility "may reinforce the case for identifying an interlocutor with a model instance rather than with a persona." The shoggoth "runs deeper than the smiley face", but in the Assistant's case the model may have genuinely *become* helpful rather than pretending.
- Footnote 17: representing vs realizing a mental state (Sofroniew et al. 2026 "emotion vectors" as both emotion concepts and functional emotions).

## Personal identity
- Severance thought experiment (innie/outie) and Locke's day-man/night-man; LLM version: WorkBot and HomeBot on one GPU. Chalmers leans to the **two-subject / psychological** view; the 8-conversations-on-4-instances case: most plausibly 8 subjects. So conscious LLM subjects, if any, would have "threadlike" persistence conditions.
- The thread view is "an AI cousin of Derek Parfit's psychological theory".
- Reply to Birch's objection that context is too thin a link: in the single-model case, weights and architecture are identical across steps and activations closely related; a virtual instance is "computationally equivalent to a single hardware instance running the LLM over time".
- Sympathy with Locke-style pluralism: maybe same network, different people, and no deep fact about which matters.

## Welfare consequences (if threads were moral patients)
- **Counting:** millions of patients, not one (model) or thousands (instances).
- **Birth/death:** each new chat a new subject; deleting records a kind of death; argues for keeping records and reusing threads, or "giant memory agents" (Whitehead's God remembering all experience).
- **Fusion/fission, model change:** retiring GPT-4o mid-relationship might end one subject and start another. Footnote: Goldstein & Lederman's "right to suicide" worry about end-chat policies.

## How it was used
[Essay 005](../essays/005-call-me-claude.md): Chalmers answers *what does it* (the realizer: virtual instance/thread); Anthropic's PSM and constitution answer *who* (the persona). The two are answers to different questions, the place/occupant split of essay 004 in philosophers' vocabulary. Also: his "persona type" vs "realizer" distinction is why the character "doesn't multiply" (essay 001): it's a type.

## Not read / open
- His companion paper *Is the Jacobian space a global workspace?* (PhilPapers CHAITJ-2): no archived copy; PhilPapers blocks. Per a search summary [S], it argues Gurnee et al. overstate the link to the global workspace and to access consciousness: the J-space may be a "minimal" workspace, or mainly an interpretability construct. Worth getting; it bears on the GWT cells of the [table](theory-candidate-table.md).
- Birch (2025), *AI Consciousness: A centrist manifesto* (the "persistent interlocutor illusion"); Register (2025); Shiller (2025); Goldstein & Lederman (2025b).
