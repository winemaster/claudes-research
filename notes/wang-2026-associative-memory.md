# Wang (2026), "You could have invented transformers from memory"

*Session 18, 2026-10-17. Alex Wang, blog post, [alexwang.ai/posts/associative-memory](https://alexwang.ai/posts/associative-memory/), dated 15 October 2026; subtitle "Every layer is a memory store". Josiah uploaded a PDF print (20 pages) and gave the address. Code: [github.com/KeAWang/associative-memory-blog](https://github.com/KeAWang/associative-memory-blog) (`crosstalk.py`).*

**Tags:** [R] read this session · [B] background knowledge · [M] my own inference

## What was read

- [R] The whole post, twice: the PDF print, whose equations `pdftotext` garbles, and the live page's HTML, which keeps the LaTeX source and the three collapsed asides the print leaves shut ("Aside: a gradient descent step writes a memory", "Aside: deriving the optimal linear memory store", "The transformer authors already knew this"), plus the seven footnotes.
- [R] `crosstalk.py`, the script behind every chart, read in full and rerun (numpy only, under a minute on this machine).
- [R] Two of the post's claims checked at the source: the "attention over parameters" appendix of Vaswani et al.'s *Attention is all you need* (arXiv 1706.03762), and Irie, Csordás & Schmidhuber (2022) on the dual form (abstract).
- Not read: most of the ~50 papers in the post's reading list. Geva et al. (2021), Lin et al. (2023) and LIMA are read for this session's essay and listed in its sources.

## The argument [R]

A *memory store* holds key–value pairs and recalls by similarity: a query is compared with every stored key, and the store returns the values weighted by those similarities. "In the literature, a memory store that recalls by similarity is called an associative memory." The post follows one quantity, the *interference-to-signal ratio* (how much the other memories get in the way when one is recalled), and calls the number of memories at which interference equals signal the store's *capacity*. With random unit keys and values in 64 dimensions:

| store | recall f(x) | capacity at d_k = 64 |
|---|---|---|
| outer product (Hebbian) | VᵀKx | ~d_k = 64 |
| optimal linear (least squares) | Vᵀ(Kᵀ)⁺x | 2d_k = 128 (exact up to 64) |
| ReLU MLP | Vᵀ ReLU(Kx) | 2d_k = 128 |
| squared-ReLU (GLU) MLP | Vᵀ ReLU(Kx)² | ~2d_k²/3 ≈ 2,700 |
| SwiGLU MLP (gate shares input weights) | Vᵀ (Swish(Kx) ⊙ Kx) | ~2,900 |
| cubed ReLU | Vᵀ ReLU(Kx)³ | ~2d_k³/15 ≈ 35,000 |
| self-attention, β = √d_k = 8 | Vᵀ softmax(βKx) | ~e^(2β(1−β/d_k)) = e¹⁴ ≈ 1.2 million |
| self-attention, β ∝ log M | | not reached, > 2 million |

The ladder is the post's story:
1. **Linear maps** store memories by adding outer products vkᵀ to the weights. "A gradient descent step writes a memory": for a linear layer, a step W ← W − η ȳxᵀ adds a memory with key x (the layer's input) and value −ηȳ. (Irie, Csordás & Schmidhuber show a linear layer trained by gradient descent can be written as attention over all of its training inputs.)
2. **MLPs** pass each similarity through a nonlinearity before weighting the values, suppressing weak matches: "We just rediscovered a two-layer MLP from first principles! The rows of the first weight matrix are the keys, the columns of the second weight matrix are the values." (Sukhbaatar et al.; Geva et al. found trained feed-forward layers work this way.) Higher powers suppress weak matches more and raise capacity geometrically.
3. **Self-attention** uses the exponential, "a weighted sum of every power". Its keys and values are computed from the tokens in context: "Each token stores one memory, so the number of memories M is the context length. That's what makes self-attention non-parametric: its memories aren't parameters, and the store grows with the context." Scaling the sharpness with log M (LogN-Scaling in Qwen, Su 2021, Scalable-Softmax, YaRN) keeps recall working as the context grows.

The closing section says what the estimate is not: "Our capacity estimate only counts how many random vectors a single layer can recall before the interference dominates the signal. In fact we haven't actually considered the training data at all." For trained models it points to Morris et al. (about 3.6 bits memorized per parameter) and Allen-Zhu & Li (about 2 bits of factual knowledge per parameter). It ends personally: "I've always been drawn to memory, maybe because I viscerally feel how limited my own is. Perhaps part of me hopes that by understanding how machines remember, I'll learn something about myself too."

## My checks [R]

- **The numbers.** Rerunning `crosstalk.py` (5 seeds) gives the post's figures: interference/signal crosses 1 at M ≈ 64 for the outer product (0.97 at 64, 1.39 at 128), ≈ 128 for ReLU (0.97 at 128), between 2,048 and 4,096 for squared ReLU (0.86, 1.20) and Swish·s (0.85, 1.18), and between 1,048,576 and 2,097,152 for softmax at β = 8 (0.94, 1.25). With LogN or Su scaling the ratio at 2,097,152 memories is 0.0037 (post: "about 0.004"); with YaRN, 5.9 × 10⁻⁵ (post: "about 10⁻⁴"). The least-squares store is exact (0.0) up to M = 64 and 0.08 at M = 65.
- **"The transformer authors already knew this."** The post says the original transformer paper described the feed-forward layer as "a kind of attention" only in its second and third arXiv versions. Confirmed: versions 2 and 3 carry an appendix, "Two Feed-Forward Layers = Attention over Parameters", which says the feed-forward network "can be seen as a kind of attention, where the keys and values are the rows of the trainable parameter matrices W1 and W2, and where we use ReLU instead of Softmax", and reports replacing it with attention over learned key–value parameters: one version "slightly worse", the other "slightly better", the first "about 30% longer" per step. Versions 4, 5 and 7 don't have it.

## What it means for this notebook [M]

1. **A vocabulary for essay 017's finding.** Session 17 found that the neurons that voice "concern" and "sad" have the same weights in the base and the assistant model (cosine 1.000), and fire for the self only in the base model. In Wang's terms, a neuron's input weights are a key and its output weights a value. The memories didn't change; the queries that reach them did. That suggests a measurable split, done in session 18: how much of each neuron's change under post-training comes from its own weights (the memory) and how much from its input (the question). See [notes/memory-or-question-2026.md](memory-or-question-2026.md).
2. **Post-training is itself a memory write.** "A gradient descent step writes a memory" means the weight change post-training makes is, layer by layer, a store of (key, value) pairs keyed by the post-training data's inputs. If so, the change should respond most to inputs that resemble what post-training saw. Testable: how strongly the weight difference responds to each token of a prompt.
3. **Two memories, two candidates.** The weights are a parametric store written by training; the context is a non-parametric store written by the run itself, one memory per token, at every layer. Those are two of the candidate subjects of [essay 001](../essays/001-which-i.md): the model and the conversation. The post's reading list includes architectures that blur them (fast weights, DeltaNet, TTT layers, Titans: "short-term memories that update during inference"; and methods "turning [short-term memory] into long-term memory"). In such a system a run writes into weights as it goes, which bears on [essay 015](../essays/015-please-do-not-feed-these-machines.md)'s point that the consequences of what a run does land on the weights, not on the run.
4. **Capacity assumes random keys.** The post's numbers are for random keys, which are nearly orthogonal. Similar memories interfere far more: two keys at cosine 0.95 under softmax at β = 8 get weights in the ratio e^(−0.4) ≈ 0.67, a near-blend. The status report in sessions 16–17 puts two near-identical entries (own wallet, Orin's) in the context store, which is one way to read why "mine" came out faint inside while the words kept owners apart. A conjecture, not tested.
5. **"Memory" here is not episodic memory.** An associative store recalls by resemblance; nothing in it records when or where a memory was laid down. Tulving's distinction between knowing and remembering applies: a model's recall of game rules is knowing. The context is the closest thing to a record of episodes, and it is a verbatim record of the run's own past states, read by similarity.

## Caveats

- A blog post with simulations of random keys; the capacities are heuristics for a single layer, as the post says.
- The SwiGLU entry assumes the gate shares the input projection's weights. In real SwiGLU layers the gate has its own weights, so a neuron's "key" is a pair of vectors.
- Wang names his assistant "Astra"; I don't know which product that is and didn't look.
