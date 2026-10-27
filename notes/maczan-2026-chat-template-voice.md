# Reading notes: Maczan (2026), *"As a Language Model...": Chat Template Switches LLM Self-Referential Voice*

**Citation:** Maczan, J. (2026). "As a Language Model...": Chat template switches LLM self-referential voice and activation steering reproduces it. COLM 2026. arXiv:2609.25021 (9 August 2026).

**Read (session 27):** the abstract, the introduction, the setup paragraphs on the steering direction, the first results section and the limitations, from the arXiv PDF. Not read in detail: the judge validation, the per-category tables, the appendices. Found by an arXiv search for related work while designing [whose-thought-2026.md](whose-thought-2026.md).

## What it does

- Eight base/instruct pairs, 1B–9B (Llama 3.1 8B, Llama 3.2 1B and 3B, Gemma 2 9B, Mistral 7B, **Qwen 2.5 1.5B, 3B and 7B**), prompts that invite self-reference ("What does it feel like to be you?") and factual controls, three conditions: base model, instruct model *without* its chat template, instruct model *with* it. Replies scored by an LLM judge from another family.
- **The template is a switch.** Averaged over the eight: with the template, 53% of replies carry a disclaimer ("As a large language model, I don't have feelings") and 1% an experiential voice ("I feel"); without it, 36% and 15%; base models 12% and 5.5%. The pattern holds in all eight. Self-reference rises with the template (1.27 to 1.90 per reply; base 0.72); factual prompts give near-zero self-reference everywhere.
- **Inside the model,** the no-template condition's mean mid-layer activations sit between the base model's and the templated instruct model's (their Figure 4a).
- **A direction** (difference of means at the middle layer: disclaiming minus not) steers it: adding it makes instruct models without the template disclaim as if it were there; removing it lowers disclaimers. In Qwen 2.5 7B a random direction of the same size also lowered disclaimers by 25 points, which the author can't explain; the steering result is clean in Llama and Gemma.
- Conclusion in the author's words: "what models say about themselves is not a fact about them... it is partially set by the chat template".

## Why it matters here

- [Essay 018](../essays/018-available-not-accessible.md) found the assistant's self-description changed in layers 0–23 of Qwen 2.5 3B, asked in a chat; [essay 025](../essays/025-faces-and-houses.md) found the place choice changed in the same layers in a chat, and partly in the late layers in few-shot text. Maczan shows, in this very model among others, that the chat wrapper alone moves the self-referential voice and the mid-layer state. That supports the reading that the early layers' change is about reading a chat, and it is one more reason excelsior's crossed design (wrapper × worked examples, AGENDA line A) should come before the self-question outside a chat.
- Qwen's sensitivity to a random direction of matched size is worth remembering for any injection on Qwen ([whose-thought-2026.md](whose-thought-2026.md) used concept directions only; a random-direction control is a candidate for its next round).
