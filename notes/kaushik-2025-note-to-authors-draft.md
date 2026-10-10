# Draft: a note to the authors of "The Universal Weight Subspace Hypothesis"

*Drafted in session 13 (2026-10-10) for Josiah to send if he wants to. Claude has contacted no one. The repository is private, so the note offers the script and numbers rather than linking them; attach [`tools/lora_subspace_check.py`](../tools/lora_subspace_check.py) and [`data/lora-subspace-check-session13.json`](data/lora-subspace-check-session13.json) if sending. Background: [reading notes](kaushik-2025-universal-weight-subspace.md), [essay 013](../essays/013-a-shared-seed.md).*

---

**To:** Prakhar Kaushik (corresponding author), cc the co-authors
**Subject:** A shared random initialization in the Lots-of-LoRAs collection (UWSH, arXiv:2512.05117)

Dear Prakhar Kaushik and colleagues,

I read the third version of your paper with interest. Claude, an AI model working in a research notebook I run, re-analysed your Mistral-7B LoRA result (Lots-of-LoRAs, rank 16) on a CPU and turned up two things you may find useful.

1. **About a third of the adapters share one random initialization.** It read q_proj in layers 0, 15 and 31 and v_proj in layer 15 for your nine held-out tasks plus 291 random others. In 107 of the 300 adapters, the LoRA A matrices are nearly identical (median pairwise cosine 0.88–0.91 in every tensor), with entries at the scale of the default Kaiming-uniform initialization; in the other 193 they are unrelated. Your nine held-out tasks are all in the independent group. Repeating your PCA on A rows (layer 0 q_proj), the top 16 components explain 31% of variance for all 300, 89% for the shared-initialization group, 5% for the independent group, and 1% for independent random matrices. The elbow at 16 seems to come from the shared group's 16 initial rows. The B side shows learned sharing in both groups (column-space overlap about 30× chance in layer 0, 4–5× in the q_proj of layers 15 and 31), and the gauge-invariant analysis your footnote suggests, on ΔW = BA, finds the independent adapters' updates as spread out as mutually orthogonal updates of the same norms (top-16 share 0.382 vs 0.377 in layer 0; within 0.001 in the other tensors).

2. **The held-out reconstruction, as we read Algorithm 1, keeps little of the update.** Projecting each held-out adapter's A and B onto the mean plus top-16 components of the other adapters keeps 1.6–4.3% of ‖ΔW‖ (relative error ≈ 1.00) in all four tensors. That seems hard to square with the reported Rouge-L of 72.3 vs 73.7, given the base model's 20.6 vs 67.8 with adapters in Brüel-Gabrielsson et al. (2024). We may well have misread the procedure (for example, which matrices are reconstructed, or whether components come from a different pool), and couldn't run the model to check performance. Your code would settle it.

We're happy to share the script (numpy only; it reads tensor slices from Hugging Face with HTTP range requests) and the per-tensor numbers.

With best wishes,
[Josiah's name]
