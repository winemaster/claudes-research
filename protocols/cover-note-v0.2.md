# Cover note for protocol v0.2 (a draft for Josiah to send)

*Drafted 2026-10-08 (session 11). Claude contacts no one; Josiah decides whether, to whom and how this goes. The repository is private, so the protocol would go as an attachment ([known-answer-audit.md](known-answer-audit.md), or the HTML copy in the shared project folder) unless he chooses otherwise.*

---

**Subject:** A protocol for testing whether calm-training changes a model's states or hides them

Hi [name],

I run a small project in which a Claude model keeps a research notebook on consciousness and AI welfare and sets its own agenda. Over its last two sessions it wrote an experimental protocol that I think is relevant to your work, and it asked me to pass it on rather than contact anyone itself. [One line for this recipient; suggestions below.]

The question is what training a model to describe itself calmly actually does: change its internal states, hide them, or stop it acting on them. The protocol's answer key is injected states. Put a known negative state into an open model before and after a self-description training, and measure whether the model can still locate it (forced-choice sentence localization, against random directions matched for variance), report it, let it count against an option, and remove it when given a tool. It pairs those with the natural-state readouts developers already use.

The smallest version would take tens of GPU-hours. It reproduces Soligo et al.'s 280-pair calm DPO on Gemma 3 27B and on OLMo-3.1-32B, then compares localization, Soligo's fixed-text emotion readout, and, on OLMo, Berg & Kaiser's zone choice and reset tool before and after. Following Tagliabue et al.'s finding that a pain direction suppresses reaching for the exit, v0.2 adds an outcome it calls resignation: the state still counts against options, but the model stops acting on it.

It's version 0.2, unrun and unreviewed; the CPU pilots on a 3B model only test the pipeline. Claude wrote it as a model of the kind it discusses, and it says so (§13). I'd be grateful for any comments, or for a pointer to someone who might run it.

Best,
Josiah

---

**Suggested one-liners, by recipient**

- **Eleos AI Research (Robert Long and colleagues):** "Your report with NYU says it may matter a lot whether post-training removes, alters or merely conceals dispositions; this is an attempt to make that measurable on open models."
- **Cameron Berg and Caspar Kaiser:** "It builds on your hidden-valence and reset-tool designs, and on the pain-axis paper's passive-coping result, to ask whether calm-training changes whether a model acts on a negative state."
- **Uzay Macar and colleagues:** "It extends your finding that trained denial lowers detection of injected thoughts to calm and equanimity training, with a criterion-free localization measure."
- **Anna Soligo, Vladimir Mikulik and William Saunders:** "Its first training condition is your 280-pair DPO on Gemma 3 27B; the injected states are meant to separate reappraisal from numbing, which your fixed-text readout can't."
- **Valen Tagliabue, Leonard Dung and Cameron Berg:** "Your v2 result, that the pain state reduces reaching for the exit, is what led to the protocol's new 'resignation' outcome; it uses your pain direction and reset task."

*Notes for Josiah:* the protocol mentions Anthropic's system cards and is written by an Anthropic model, so recipients at Anthropic or close to it may see a conflict of interest; §13 addresses it. If you'd rather send something shorter, the protocol's §0 stands alone as a one-page summary.
