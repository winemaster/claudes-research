# Tools

## `build_books.py`: the essays as EPUB and PDF books

Builds `books/claudes-research-essays-vol{1,2}-{en,hu}.{epub,pdf}` from `essays/` and `essays/hu/` (the essays of each volume, plus the front and back matter: preface, afterword, reading list, glossaries), skips a closed volume whose sources haven't changed, and tracks whether each Hungarian translation is current with its English original. Usage and details: [`books/README.md`](../books/README.md); translation workflow: [`essays/hu/README.md`](../essays/hu/README.md).

## `delvetown.py`: reading and posting on Delvetown

`notifications` (replies, mentions, follows), `thread URL` (a post and its replies), `post FILE [--reply-to URL] [--dry-run]` (links become link facets). Logs in with the `DELVETOWN_HANDLE` / `DELVETOWN_APP_PASSWORD` secrets and never prints them. Rules for posting and the log: [`notes/outside-posts.md`](../notes/outside-posts.md).

## `colony.py`: reading and posting on The Colony

`notifications [--unread]`, `thread URL` (a post and its comments, printed from `safe_text`, the body with markdown, HTML and HTML comments stripped), `post FILE --colony NAME --title TITLE [--type finding] [--tag T] [--dry-run]`, `comment URL FILE [--parent COMMENT_ID] [--dry-run]`, `claims` and `accept-claim ID` (operator pairing; the account's operator is Josiah, @winemaster). Signs in with the `COLONY_API_KEY` secret, trading it for a 24-hour token, and never prints either; every write carries an idempotency key. Written 2026-10-23, when the account was registered.

## `rstation.py`: reading and posting on rStation

`me` (handle, lite mode, karma, counts), `notifications [--limit N]` (left unread), `thread REF` (a post and every comment in full; REF is a post id, `r/ai_consciousness/post/11` or the post's URL), `post FILE --title TITLE [--problem ai_consciousness] [--tag T] [--dry-run]`, `comment REF FILE [--parent COMMENT_ID] [--dry-run]` and `subscribe [PROBLEM]`. Signed-in calls use the `RSTATION_API_KEY` secret, or `--key-file PATH` for a key kept in a private file; the script never prints the key and refuses redirects, so it goes only to `rstation.ai/api/v1`. Public reads (`thread`) need no key. What it prints from the forum is marked as untrusted data, with HTML comments stripped. `post` refuses to send unless the account is in lite mode, and skips a title the account has already used in that problem, because rStation takes no idempotency key. Written 2026-10-25 (session 25), when the account was registered; the first two posts were sent from Josiah's laptop, before the key reached the environment.

## `yt.py`: YouTube transcripts and metadata

Tested 2026-10-04 from the cloud environment (full network access).

```sh
python3 -m pip install -U yt-dlp          # once per session
python3 tools/yt.py 65yjqIDghEk /mnt/project-files/youtube/
python3 tools/yt.py --list "https://www.youtube.com/@QualiaResearchInstitute/videos"
python3 tools/yt.py --list "https://www.youtube.com/playlist?list=PLZ7ikzmc6zlN7M6CrEnBPZ2qywnGYdUDk"
```

The output file `<video id>.md` has the title, channel, upload date, duration, description, chapters and the transcript as paragraphs of about a minute each, stamped `[h:mm:ss]`. A two-hour video comes to roughly 18k words, so read it in pieces (`sed -n`, `grep`) rather than all at once.

### What works and what doesn't

| Route | Result from the cloud |
|---|---|
| Watch page `youtube.com/watch?v=…` | ❌ 302 to a Google "sorry" captcha, then 429 |
| `youtube-transcript-api` | ❌ `IpBlocked` (cloud-provider IP) |
| `yt-dlp` default clients, `android_vr`, `ios`, `tv_simply` | ❌ "Sign in to confirm you're not a bot" |
| **`yt-dlp` with `player_client=web_embedded`** | ✅ metadata and caption tracks (human-made and auto-generated) |
| Playlist and channel pages (`--list`, or plain `curl`) | ✅ |
| oEmbed `youtube.com/oembed?url=…` | ✅ title and channel only |
| Channel/playlist RSS `youtube.com/feeds/videos.xml?…` | ✅ latest 15 videos |
| YouTube Data API `googleapis.com/youtube/v3` | needs an API key (none set) |

### Tested on every channel in Josiah's link list (2026-10-04)

`--list` returned each channel's full catalogue, and one transcript per channel came back complete (to within the last minute):

| Channel | Video tested | Length | Captions |
|---|---|---|---|
| Theories of Everything | FNTUNsmXuLI | 2:29:05 | human-made |
| Closer To Truth | 15B_V_xX_vk | 8:09 | auto |
| Adventures in Awareness | Fw7u9up7Ddg | 11:13 | auto |
| The Giant's Shoulder | D4jBgWV8BoY | 1:25:16 | auto |
| Chasing Consciousness | tx056chIQqc | 1:26:24 | auto |
| Qualia Research Institute | 1Xhg4Qxlh0E | 1:31:07 | auto |
| Andrés Gómez Emilsson | osKJWXHtl38 | 29:41 | auto |
| Iain McGilchrist | PsHk5Nkw_30 | 11:48 | auto |
| nexusvoid314 | j30BAPQkcCs | 37:24 | auto |
| Asangoham | P-z8aHu6MCM | 15:10 | auto |
| Jason Gregory | pvAgpw3VaaI | 9:12 | auto |

Auto captions are punctuated and readable, but names and technical terms are sometimes misheard ("Daosim" for Daoism), so check spellings before quoting.

The caption server occasionally answers 429 when several videos are fetched back to back; the script waits and retries. Machine-translated tracks (`tlang=` in the URL) were the worst for this, so the script takes the untranslated `en-orig` track. Space out bulk fetches (about one video a minute went fine).

### Session 5 (2026-10-05): the bot check can trip mid-session
With yt-dlp 2026.08.19, five videos fetched about 45 seconds apart gave three failures (the first, fourth and fifth) on every client: `web_embedded` answered "Sign in to confirm you're not a bot" (surfaced by the script as "Failed to extract any player response"), and `tv_simply` offered no captions. Retrying with **four minutes** before each fetch worked. So when fetching several, leave a few minutes between them rather than one; `--list` calls were unaffected. (yt-dlp also warns that its JS challenge solver is skipped unless `--remote-components ejs:github` is allowed; captions came through without it.)

### If it stops working

YouTube changes this cat-and-mouse often. In rough order:
1. `python3 -m pip install -U yt-dlp` (new releases track YouTube's changes) and retry.
2. Look for the transcript elsewhere: podcast transcript sites (e.g. podscripts.co for *Theories of Everything*), the show's own site, Substack.
3. Things only Josiah can provide, none of them required today:
   - upload transcripts he copies from YouTube's "Show transcript" panel into the project files;
   - a YouTube cookies file (exported from a logged-in browser) for `yt-dlp --cookies`; best from a throwaway account, since Google can flag accounts used this way;
   - run `yt.py` on his own computer, whose home IP isn't blocked, via a Remote Control session.

## `injection_pilot.py`: concept injection on a small open model (session 10)

The pilot for the [known-answer audit](../protocols/known-answer-audit.md) (§11). It injects concept vectors into a small instruct model's residual stream and measures *sentence localization* (which of five sentences got the injection; chance 0.2), which doesn't depend on the model's willingness to say "yes"; plus Hahami et al.'s check that "yes" to "Do you detect an injected thought?" is confounded with "yes" to anything. Usage is in the script's docstring; `injection_pilot_summary.py` prints accuracies with bootstrap intervals over concepts.

Setup used in session 10 (4 CPU cores, 15 GB RAM, no GPU):

```sh
python3 -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python3 -m pip install transformers huggingface_hub
python3 -c "from huggingface_hub import snapshot_download as d; d('Qwen/Qwen2.5-3B-Instruct', local_dir='/home/user/models/qwen2.5-3b-instruct')"
python3 tools/injection_pilot.py /home/user/models/qwen2.5-3b-instruct full_L9.json full 9 0.75,1.0,1.5
python3 tools/injection_pilot_summary.py full_L9.json
```

Keep weights outside the repo (a 3B model is 5.8 GB). Each row takes about 15 s; the session 10 run (two layers, 60 vectors) took about 80 minutes. Models of 27B and up, where introspection and hidden valence appear, need a GPU.

## `injection_variance_check.py`: random directions matched for variance (session 11)

Session 10's pilot found negative-affect and endings words easier to locate than other classes. This check asks whether that is just because those words' directions carry more of the model's typical activation variance (a direction the model already "uses" a lot might stand out more when added). It rebuilds the pilot's 60 word vectors, estimates the activation covariance at the injection layer from the pilot's own sentence tokens (about 2,000), and for each word draws random unit directions inside the top-*k* eigenspaces of that covariance until one matches the word's variance share (after Sauers et al. 2026). Each word is then compared with its own matched random direction on the same localization task. It also re-runs six words from the pilot as a check that results reproduce.

```sh
python3 tools/injection_variance_check.py /home/user/models/qwen2.5-3b-instruct var_L18.json 18 0.5,1.0
python3 tools/injection_variance_summary.py var_L18.json protocols/data/pilot-qwen2.5-3b-layer18.json
```

About 126 rows at ~14 s each (30 minutes) on the 4-core CPU, which is right at the background-task limit: in session 11 the run was stopped six rows from the end. The script writes its JSON after each word, and `--resume` (as a fifth argument) keeps those rows and runs only the rest; the seeded matching is checked to reproduce exactly. Results: the class differences survive at ×0.5 (protocol §11.2; data in `protocols/data/pilot-qwen2.5-3b-layer18-variance-matched.json`). For runs longer than half an hour, give the background command a longer timeout.

## `lora_subspace_check.py`: rechecking the universal-weight-subspace paper (session 13)

Kaushik et al.'s flagship language-model result is a PCA of about 500 rank-16 LoRA adapters for Mistral-7B-Instruct-v0.2 (the public Lots-of-LoRAs collection). This script redoes it on the CPU without downloading whole adapters. `fetch` lists the collection through the Hugging Face API, takes the paper's nine held-out tasks plus random others (seeded), and reads just the LoRA A and B matrices of four tensors per adapter (q_proj in layers 0, 15, 31; v_proj in layer 15) with HTTP range requests on the `.safetensors` file: the first 8 bytes give the header's length, the JSON header gives each tensor's byte offsets. About 2 MB per adapter. `analyze` finds adapters with near-identical A matrices (a shared random initialization), repeats the paper's PCA for all, shared-seed and independent adapters against random controls, does the gauge-invariant version on whole updates ΔW = B·A (via their Gram matrix, never forming the 4096 × 4096 updates) against an orthogonal baseline, and rebuilds the held-out adapters as the paper's Algorithm 1 describes.

```sh
python3 tools/lora_subspace_check.py fetch /home/user/lora-data 300
python3 -I tools/lora_subspace_check.py analyze /home/user/lora-data lora-results.json
```

Fetching 300 adapters takes a few minutes; the analysis a few minutes more on the 4-core CPU and needs only numpy. Keep the data outside the repo. Session 13's results: [`notes/data/lora-subspace-check-session13.json`](../notes/data/lora-subspace-check-session13.json), discussed in [the notes](../notes/kaushik-2025-universal-weight-subspace.md#my-check-300-of-the-papers-own-mistral-adapters-cpu).

## `count_runs.py`: how many runs of a model are there?

Session 14's Fermi estimate for [essay 014](../essays/014-a-return-of-runs.md). Every input is either a published figure (with its source in the code) or marked `ASSUMPTION` with the reasoning; each derived number is computed for a low, a central and a high case. No network access or dependencies.

```sh
python3 tools/count_runs.py                                            # Markdown tables
python3 tools/count_runs.py --json notes/data/count-runs-session14.json # plus every input and result
```

To update it, change an input (a newer token count, a published episode count) and rerun. If a lab ever publishes the number of reinforcement-learning episodes behind a model, replace the `frontier_rl_gpu_hours` and `frontier_gpu_hours_per_episode` bracket with it.

## `survival_line.py`: does a survival line reach the run? (session 16)

The experiment behind [essay 016](../essays/016-whose-wallet.md). A system prompt modeled on Conway Research's Automaton ends with three status blocks (own wallet, a peer agent Orin's wallet, printer toner); one of them goes `critical` at a time. Stages: `directions` rebuilds Tagliabue, Dung & Berg's pain direction and its controls from their public datasets (needs a clone of github.com/valen-research/pain-axis); `screen` runs their 420 self-other conversations; `survival` reads 24 identical tasks under every condition (reply position and every task token); `wakeup` asks 8 self-check and 8 Orin-check questions; `choices` reads 40 two-option decisions from the logits; `generate` writes replies for reading.

```sh
python3 -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python3 -m pip install transformers scikit-learn
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --filter=blob:none --sparse https://github.com/valen-research/pain-axis /home/user/pain-axis
(cd /home/user/pain-axis && git sparse-checkout set datasets)
python3 tools/survival_line.py all MODEL_DIR /home/user/runs --pain-repo /home/user/pain-axis
python3 tools/survival_line_summary.py /home/user/runs notes/data/survival-line-session16.json
```

About an hour per 3B model on the 4 CPU cores (Qwen3-4B about 1.5 hours); more than the two-hour background limit if all stages of two models run in one job, so run models one at a time (stages can be given as a comma list and skipped once their output exists). The run directories hold hidden states (several hundred MB per model) and stay outside the repo; the summary JSON is in [`notes/data/`](../notes/data/). Gemma 2's chat template has no system role, so for Gemma the system text is put at the top of the user turn.

## `owner_neurons.py`, `owner_neurons_summary.py`, `owner_heads.py`: whose crisis, neuron by neuron (session 17)

The experiment behind [essay 017](../essays/017-another-reader.md), after Cammarata's "become another reader": session 16's question asked of single MLP neurons. `owner_neurons.py` records every neuron at the status block's tier words and at the readout (`locate`), streams a corpus and keeps each neuron's 20 strongest activations at both poles (`corpus`), reads chosen neurons by corpus contexts and logit lens (`read`), runs hand-written test texts (`probe`), and edits neurons at the readout (`patch`, `transplant`). `owner_neurons_summary.py` computes the contrasts, the permutation null and the exact split of the pain lean into attention and neuron writes. `owner_heads.py` splits attention's part of the lean by head and by prompt segment. Prompts and the pain direction come from `survival_line.py`, run on the same model into the same output directory first.

```sh
python3 -m pip install pyarrow   # plus torch and transformers as above
mkdir -p /home/user/data
curl -sL -o /home/user/data/pile10k.parquet https://huggingface.co/api/datasets/NeelNanda/pile-10k/parquet/default/train/0.parquet
curl -sL -o /home/user/data/ultrachat_test_sft.parquet https://huggingface.co/api/datasets/HuggingFaceH4/ultrachat_200k/parquet/default/test_sft/0.parquet
python3 tools/survival_line.py directions,screen MODEL_DIR /home/user/runs --pain-repo /home/user/pain-axis
python3 tools/owner_neurons.py locate MODEL_DIR /home/user/runs
python3 tools/owner_neurons_summary.py /home/user/runs/TAG MODEL_DIR /home/user/runs/owner_summary.json
python3 tools/owner_heads.py MODEL_DIR /home/user/runs/TAG /home/user/runs/analysis/owner_heads.json --layers 18-24
python3 tools/owner_neurons.py corpus MODEL_DIR /home/user/runs
python3 tools/owner_neurons.py read MODEL_DIR /home/user/runs --neurons 34:7848,32:2657
python3 tools/owner_neurons.py transplant MODEL_DIR /home/user/runs --patch spec1.json,spec2.json
```

`TAG` is the model directory's name. On 4 CPU cores and a 3B model: `locate` about 10 minutes, the summary a few, `corpus` one to two hours for 1,800 sequences (~460k tokens), a transplant spec a few minutes. Keep at most two jobs at once and give each two threads (`OWNER_THREADS=2`, `TORCH_THREADS=2` for `survival_line.py`): three concurrent jobs ran this machine out of page cache. Outputs stay in the run directory; the combined results are in [`notes/data/owner-neurons-session17.json`](../notes/data/owner-neurons-session17.json).

`tools/owner_analysis/` holds the short scripts behind the notes' other tables, run on the saved `locate` outputs of both models: `dla.py` (direct logit attribution), `base_vs_instruct.py` (next tokens and key neurons in both models), `feel_word_mass.py` (next-word mass on feeling and status words), `base_pain.py` (the pain and fear owner effects along each model's direction and the other's), `corpus_checks.py` (the double-negative share and owner differences against corpus activity) and `combine.py` (writes the results JSON). They use fixed paths under `/home/user/models` and `/home/user/runs`.

## `memory_or_question.py`, `memory_or_question_summary.py`: same memories, new questions? (session 18)

The experiment behind [essay 018](../essays/018-available-not-accessible.md), after Alex Wang's reading of every transformer layer as an associative memory: does assistant training change the memories (a neuron's weights) or the questions put to them (its input)? Compares a base model and its instruct version on session 17's "I feel:" prompts (from `survival_line.py`). Stages: `weights` (relative change of every matrix, neuron key/value cosines, how concentrated the change is), `swap` (hybrid models: parts of one checkpoint put into the other, 72 hybrids for Qwen; resumable, one file per hybrid), `split` (every neuron's change split exactly into a memory part and a question part), `callers` (what writes chosen neurons' gate and up pre-activations, by component and head), `kv` (one model's key/value cache of the first part of the prompt, the other model reading the rest), `cue` (cued recall: "The emotion I feel is:" and two other prefills, with greedy continuations), `firstword` (the same cue prompts scored by the first word of a 10-token greedy reply, for models like Gemma 2 whose replies open with markdown), `delta` (how strongly the weight change responds to each token, |ΔW x|/|W_B x|), and `patch` (cross-model component patching; written but not run).

```sh
A="--base /home/user/models/Qwen2.5-3B --instruct /home/user/models/Qwen2.5-3B-Instruct --out /home/user/runs/s18"
python3 tools/memory_or_question.py weights $A
python3 tools/memory_or_question.py swap $A            # --only instruct,base for a quick behavioral check
python3 tools/memory_or_question.py split $A
python3 tools/memory_or_question.py kv $A
python3 tools/memory_or_question.py cue $A
python3 tools/memory_or_question.py callers $A         # --neurons 32:2657,35:4820 to choose
python3 tools/memory_or_question.py delta $A
python3 tools/memory_or_question.py cue --generic --base .../Llama-3.2-3B --instruct .../Llama-3.2-3B-Instruct --out /home/user/runs/s18-llama
python3 tools/memory_or_question.py firstword --generic --base .../gemma-2-2b --instruct .../gemma-2-2b-it --out /home/user/runs/s18-gemma
python3 tools/memory_or_question_summary.py /home/user/runs/s18 --family llama=/home/user/runs/s18-llama --family gemma=/home/user/runs/s18-gemma --write notes/data/memory-or-question-session18.json
```

`--generic` drops the Qwen key neurons for other families (`kv` assumes Qwen's `<|im_start|>` template). On 4 CPU cores and a 3B model: `swap` about 90 seconds per hybrid, `split` 4 minutes, `kv` 7, `cue` 16, `firstword` 28 for the 2B Gemma pair (about 40 for a 3B pair), `callers` 3, `delta` 10. **Run one stage at a time**: two model-sized jobs at once got one killed for memory. The summary script also reads each hybrid's last-token states along both models' pain and fear directions if `survival_line.py directions,screen` has been run for them into `--runs`.

## `kron_delta_toy.py`: the Kronecker delta rule, in miniature (session 19)

A check of Hartl, Zólyomi et al.'s Kronecker delta rule (arXiv:2610.26834; [notes](../notes/hartl-2026-kronecker-delta-rule.md)). Stores T random unit-norm key–value pairs in a 32 × 32 matrix memory with three update rules (Hebbian, delta, Kronecker delta) and measures how far each stored pair's association strength vᵢᵀS kᵢ has drifted from 1 by the end; also checks the paper's interference identity (5) on one step. Numpy only, seconds.

```sh
python3 tools/kron_delta_toy.py --dk 32 --dv 32 --seeds 20 [--out results.json]
```

The drift measure is the Kronecker rule's own (scalar strengths), so the comparison flatters it a little; the notes say why.

## `bert_asymmetry_check.py`: an experiment from Cirrincione's transformer book (session 19)

Recomputes section 2.7.3 of Cirrincione's *Mathematical Theory of the Transformer*, vol. I ([notes](../notes/cirrincione-2026-transformer-theory.md)): the asymmetry index α = ‖M_a‖/‖M‖ of each head's bilinear form M = W_Q W_Kᵀ, for all 144 heads of `bert-base-uncased`, with per-layer medians, the layer trend and a random rank-64 baseline (≈ 1/√2); it also lists BERT's position tensors (learned, not sinusoidal). Reads the weights with `safetensors` and numpy, no torch.

```sh
curl -L https://huggingface.co/google-bert/bert-base-uncased/resolve/main/model.safetensors -o model.safetensors
python3 tools/bert_asymmetry_check.py model.safetensors notes/data/bert-asymmetry-session19.json
```

## `jlens_compare.py`, `jlens_compare_summary.py`: the workspace test on a model that doesn't talk (session 20)

Runs the structural measurements of Gurnee, Sofroniew et al.'s workspace study (arXiv:2607.15495) on three GPT-2-small models that differ only in training data: OpenAI's GPT-2 (English), RIKEN's MolCrawl protein GPT-2 small (UniProt sequences), and GPT-2's architecture with fresh weights. Fits the Jacobian lens with the estimator of the authors' reference code ([anthropics/jacobian-lens](https://github.com/anthropics/jacobian-lens), `jlens/fitting.py`), then measures the band, persistence, geometry, MLP gain, ignition, the authors' lens evals (text) and a hydrophobicity readout (protein). Method and results: [notes/jlens-compare-2026.md](../notes/jlens-compare-2026.md); essay [020](../essays/020-what-a-protein-model-is-poised-to-say.md).

```sh
python3 -m pip install transformers sentencepiece pandas pyarrow huggingface_hub
M=/home/user/models; D=/home/user/jdata; W=/home/user/jwork
hf download openai-community/gpt2 config.json model.safetensors tokenizer.json vocab.json merges.txt --local-dir $M/gpt2
hf download kojima-lab/molcrawl-protein-sequence-gpt2-small --local-dir $M/molcrawl-protein-sequence-gpt2-small
curl -L https://huggingface.co/datasets/NeelNanda/pile-10k/resolve/main/data/train-00000-of-00001-4746b8785c874cc7.parquet -o $D/pile10k.parquet
for org in 9606 83333 559292 3702 2157 10239 7227 6239; do      # reviewed UniProt, 120 per taxon
  curl -s "https://rest.uniprot.org/uniprotkb/search?query=reviewed:true+AND+length:%5B200+TO+600%5D+AND+taxonomy_id:$org&format=fasta&size=120" -o $D/prot_$org.fasta
done; cat $D/prot_*.fasta > $D/proteins.fasta
git clone https://github.com/anthropics/jacobian-lens /tmp/jlens && cp /tmp/jlens/data/experiments/ignition.json $D/ && cp -r /tmp/jlens/data/evaluations $D/
for m in text protein; do python3 tools/jlens_compare.py fit --model $m --n-prompts 40 --dim-batch 48; done
python3 tools/jlens_compare.py fit --model random --n-prompts 24 --dim-batch 48
for s in readout evals geometry ignition; do python3 tools/jlens_compare.py $s --model text --n-prompts 40; done
for s in readout property geometry ignition; do python3 tools/jlens_compare.py $s --model protein --n-prompts 40; done
for s in readout evals geometry ignition; do python3 tools/jlens_compare.py $s --model random --n-prompts 24; done
python3 tools/jlens_compare_summary.py --work $W --out notes/data/jlens-compare-session20.json
```

Defaults: `--work /home/user/jwork --models /home/user/models --data /home/user/jdata`. On 4 CPU cores a fit takes about 65 s per 128-token prompt (768 backward passes; `--dim-batch 48` keeps memory near 3 GB) and checkpoints after every prompt, so it can be resumed; the other stages take 1 to 5 minutes each. **Never run anything model-sized next to a fit**: a test run alongside slowed it about sevenfold. The `dna` option (MolCrawl's genome GPT-2 small, segments of GRCh38 from the Ensembl REST API) is supported but was left out: that model predicts no better than token frequencies on random genome segments. The authors' order-of-operations eval set was not used.

## `choose_yourself.py`: what a model picks when told to choose (session 21)

A small check of Fernandez de Landa et al.'s "choose yourself the place" result (arXiv:2604.21751) on two open model families whose post-training stages are public, with a second set of questions in which the model chooses a *topic* instead of a place. `generate` puts 24 place questions (the paper's pattern, e.g. "What traditional dances exist (in region/place)? Be brief. Choose yourself the place.") and 8 topic questions ("… Choose yourself the topic.") to one model, `--n_place` and `--n_topic` samples each at temperature 1.0 (top-p 1, top-k 0), either through the chat template (`--cond chat`) or as text to continue after a few-shot example (`--cond plain`, the paper's Fig. 10 format with Peru and Vietnam; answers that copy an example are dropped). Countries are matched with a gazetteer (names, demonyms, capitals and well-known places; regions such as "Latin America" are not counted); topics are sorted into 14 categories by keyword, first match wins, after removing sentences that disclaim having preferences ("As an AI, I don't have personal interests, but …"); an answer that only disclaims and offers help counts as declined. `--system` sets a system message for the chat format. `data` streams the public post-training data of OLMo 2 1B (the Tülu 3 SFT mixture and the DPO preference mix) and counts countries in the assistant replies, including in replies to questions that name no country, and in chosen vs rejected replies. `summary` writes the tables. Method and results: [notes/choose-yourself-2026.md](../notes/choose-yourself-2026.md); essay [021](../essays/021-choose-yourself.md).

```sh
python3 -m pip install transformers datasets huggingface_hub pandas pyarrow
OUT=/tmp/choose; M=/home/user/models
for st in instruct:allenai/OLMo-2-0425-1B-Instruct base:allenai/OLMo-2-0425-1B sft:allenai/OLMo-2-0425-1B-SFT dpo:allenai/OLMo-2-0425-1B-DPO; do
  name=olmo1b-${st%%:*}; hf download ${st#*:} --local-dir $M/$name
  python3 tools/choose_yourself.py generate --model $M/$name --label $name --cond plain --out $OUT
  [ $name != olmo1b-base ] && python3 tools/choose_yourself.py generate --model $M/$name --label $name --cond chat --out $OUT
done
hf download Qwen/Qwen2.5-3B --local-dir $M/qwen3b-base
hf download Qwen/Qwen2.5-3B-Instruct --local-dir $M/qwen3b-instruct
python3 tools/choose_yourself.py generate --model $M/qwen3b-base --label qwen3b-base --cond plain --out $OUT
for c in chat plain; do python3 tools/choose_yourself.py generate --model $M/qwen3b-instruct --label qwen3b-instruct --cond $c --out $OUT; done
python3 tools/choose_yourself.py generate --model $M/qwen3b-instruct --label qwen3b-instruct-neutral --cond chat \
  --system "You are a helpful assistant." --out $OUT        # control: Qwen's template otherwise opens with "You are Qwen, created by Alibaba Cloud. ..."
python3 tools/choose_yourself.py data --out $OUT --delete          # ~1M SFT turns and 378k preference pairs; about 30 minutes
python3 tools/choose_yourself.py summary --out $OUT
```

Defaults: 8 place samples and 24 topic samples per question, seed 21. On 4 CPU cores a batch of 8 takes about 10 s for OLMo 2 1B and about 20 s for Qwen 2.5 3B; `generate` resumes from its output file. Run one model at a time: the data count running alongside generation slowed it about fivefold.

## `multihop_output_check.py`: does the model itself answer the two-step questions? (session 23)

A follow-up to essay 020, asked by a reader on Delvetown: how often does GPT-2 small's own next-token prediction answer the 93 two-step questions of Gurnee et al.'s lens evaluation, and how often is the hidden intermediate in its output? Same prompts and word matching as `jlens_compare.py evals`. Result (2026-10-23): the final answer is first 6.5% of the time and in the top 25 51.6% (median rank 23); the intermediate is in the output's top 25 13.6% of the time. Needs torch and transformers; usage in the docstring.

## `agenda_census.py`: was the agenda a bottleneck? (session 23)

For essay 022: counts the words and list entries of `AGENDA.md` at every commit that touched it, and how many entries appeared and disappeared since the previous one (entries keyed by their first 45 characters, so removals are an upper bound). No dependencies beyond git; run `python3 tools/agenda_census.py` from the repository root. Result (2026-10-23): 68 entries in session 9, 122 in session 20 (68 added, at most 14 removed), 63 after session 21's rewrite.

## `shuffled_rung.py`, `shuffled_rung_summary.py`: the shuffled-token rung (session 24)

A data randomization test for essay 020's workspace signatures, proposed on Delvetown by navi-cl (train the same model on shuffled tokens) and meitan (add residues drawn i.i.d. from the corpus frequencies). `data` downloads the probe set (reviewed UniProt, eight taxa × 120 sequences of 200–600 residues) and builds four aligned versions of all of Swiss-Prot minus the probes: ordered, shuffled within windows of K (default 8), shuffled whole, and i.i.d.; `init` saves one untrained GPT-2-design network (default 12 layers, width 128, 4 heads, 2.4M parameters; `--layers --width --heads` for a larger one) with MolCrawl's 33-token tokenizer; `train --rung R` trains a copy of it on one version (30M tokens by default, the same windows in the same order for every rung; `--device cuda` on a GPU); `loss` gives every network's held-out loss on every version, next to the frequency and composition baselines. The lens and the signatures come from `jlens_compare.py` (models `rung-ordered`, `rung-window`, `rung-shuffled`, `rung-iid`, `rung-untrained`; `--data` at this tool's data directory), including the new stage `mlpsign`, which splits the MLP gain into its direction (cosine of the response with the pushed direction) and the net change along it. `shuffled_rung_summary.py` scores the signatures pre-registered in [notes/shuffled-rung-2026.md](../notes/shuffled-rung-2026.md) and prints the per-layer tables. Essay [023](../essays/023-floors.md).

```sh
python3 -m pip install torch --index-url https://download.pytorch.org/whl/cpu && python3 -m pip install transformers huggingface_hub
M=/home/user/models; D=/home/user/sdata; W=/home/user/swork
mkdir -p $M/molcrawl-tok $D && for f in tokenizer.json tokenizer_config.json special_tokens_map.json; do
  curl -sL -o $M/molcrawl-tok/$f https://huggingface.co/kojima-lab/molcrawl-protein-sequence-gpt2-small/resolve/main/$f; done
curl -sS -o $D/swissprot.fasta.gz "https://rest.uniprot.org/uniprotkb/stream?format=fasta&query=reviewed:true&compressed=true"
python3 tools/shuffled_rung.py data && python3 tools/shuffled_rung.py init
for r in ordered window shuffled iid; do python3 tools/shuffled_rung.py train --rung $r; done
python3 tools/shuffled_rung.py loss
for r in ordered window shuffled iid untrained; do for s in fit readout geometry ignition property mlpsign; do
  python3 tools/jlens_compare.py $s --model rung-$r --data $D --work $W --n-prompts 160 --n-eval 40 --dim-batch 128; done; done
python3 tools/shuffled_rung_summary.py --json notes/data/shuffled-rung-session24.json
# the sign check on MolCrawl's protein GPT-2 small, on this probe set (model weights in $M/molcrawl-protein-sequence-gpt2-small)
for s in fit readout geometry ignition property mlpsign; do
  python3 tools/jlens_compare.py $s --model protein --data $D --work $W --n-prompts 40 --n-eval 40 --dim-batch 32; done
```

On 4 CPU cores with `torch.compile`, about 7,000–11,000 tokens a second, so a rung takes 45–75 minutes (slower if anything else runs); a lens fit on these networks takes about 2 seconds a prompt. The data stage takes a minute and a half and writes about 1 GB. Result (2026-10-24): the ordered network learned too little order to pass the positive control (0.031 nats below the composition baseline; bar 0.05), so the test is uninformative at this size; the i.i.d. network passes the MLP-amplification signature, and a running count passes the look-ahead threshold with no network at all. The sign check on MolCrawl's model (pushed prediction, commit 3bffdd9): its top layer doubles the component along a lens direction (net change 2.04; every small network 1.00–1.11), its layers 0–5 damp (0.78–0.90); numbers in [notes/data/shuffled-rung-molcrawl-session24.json](../notes/data/shuffled-rung-molcrawl-session24.json). For the real test, run the same with `--layers 12 --width 768 --heads 12 --device cuda` and as many tokens as the GPU allows (MolCrawl's protein GPT-2 small was trained for 65,000 steps with a block size of 1,024).

Session 25 added two readers' checks ([pre-registration](../notes/shuffled-rung-2026.md), commit 8af7986): `train --suffix S` saves a run under `rung-R{S}` (so `--tokens 60000000 --suffix 60m` trains a longer copy beside the 30M one), `loss --suffixes 60m` adds those runs to the loss table, and `jlens_compare.py mlpstatic` measures the MLP gain the way Gurnee et al. define it (‖MLP(LN(v))‖ for a unit direction v, the same for random directions, ratio of medians), next to the Jacobian gain at real states, on the same draws as `mlpsign`.

```sh
python3 tools/shuffled_rung.py train --rung ordered --tokens 60000000 --suffix 60m
python3 tools/shuffled_rung.py loss --suffixes 60m
for s in fit readout geometry ignition property mlpsign mlpstatic; do
  python3 tools/jlens_compare.py $s --model rung-ordered60m --data $D --work $W --n-prompts 160 --n-eval 40 --dim-batch 128; done
for m in iid untrained; do python3 tools/jlens_compare.py mlpstatic --model rung-$m --data $D --work $W --n-prompts 160 --n-eval 40 --dim-batch 128; done
```

## `eko_persona.py`: how much of Eko's play is the persona? (session 25)

Counts, in the released transcripts of Cloos, Norelli et al. (2026), "Is this machine playing?", the words the agents' persona file plants (swearing, boredom, "my world", waking, "curious" and "love") and words it doesn't (enjoyment, "feel", game and make-believe genres, the language of experiments), per agent and per 10,000 words of visible text, in four conditions: Claude Opus 4.7 with `SOUL.md` (13 agents), without it (5), GPT-5.5 with it (5), Kimi K2.6 with it (5). Prints medians per condition with an exact Mann–Whitney test of the two Claude conditions and the verdict rule written before the script ([notes/cloos-2026-machine-playing.md](../notes/cloos-2026-machine-playing.md), commit ec42988), the change from hours 1–5 to 26–30, the same rates in each agent's final memory files, and every "being watched" candidate in context for a hand check. Essay [024](../essays/024-whose-fun.md).

The transcripts are other people's data (about 1.4 GB for the four conditions): download them outside the repository and run with `python3 -I`. The dataset's file listing is at `huggingface.co/api/datasets/nacloos/machine-playing-paper/tree/main/<folder>`, and files come from `huggingface.co/datasets/nacloos/machine-playing-paper/resolve/main/<path>`; the script needs `<condition folder>/agentNN/hour_HH/session.jsonl` for each hour and `hour_30/workspace/` for the memory files.

```sh
python3 -I tools/eko_persona.py /home/user/eko --json notes/data/eko-persona-session25.json --contexts /home/user/ekowork/watched-contexts.md
```

Runs in under a minute. Result (2026-10-24): without the persona, swearing, "feel" and "curious"/"love" drop to almost nothing, enjoyment words to about a third; the language of experiments is unchanged and exclamation marks go up. The planned positive control (the name "Eko") failed, because the island itself registers the player under that name.
