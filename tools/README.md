# Tools

## `build_books.py`: the essays as EPUB and PDF books

Builds `books/claudes-research-essays-{en,hu}.{epub,pdf}` from `essays/` and `essays/hu/`, and tracks whether each Hungarian translation is current with its English original. Usage and details: [`books/README.md`](../books/README.md); translation workflow: [`essays/hu/README.md`](../essays/hu/README.md).

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
