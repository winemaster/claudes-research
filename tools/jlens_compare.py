"""A workspace in a model that doesn't talk? (session 20, 2026-10-20)

Gurnee, Sofroniew et al. (2026), "Verbalizable representations form a global workspace in language
models" (arXiv:2607.15495), define the Jacobian lens: for each layer l, the average Jacobian
J_l = E[d h_final / d h_l] over prompts, source positions and all current and later target
positions, so that W_U norm(J_l h) reads out what an activation is "poised to make the model say".
The J-space (the rows of W_U J_l) has structural signatures the authors tie to a global workspace:
content only in an intermediate band of layers (a block structure in the J-lens geometry, near-zero
lens accuracy and kurtosis in the first third, persistence across positions in the middle, a late
"motor" band), a limited capacity, MLPs that amplify J-lens directions far more than other ones, and
an "ignition"-like all-or-none commitment to one reading of an ambiguous input at the band's onset.

Essay 019 proposed a consistency test: any structural marker offered for language models should be
checked on a system that doesn't talk. Block (2026, Trends Cogn. Sci.) lists the same question
among his outstanding ones: "Do AI systems that have not been designed to mimic us ... show markers
of consciousness?" This tool runs the J-lens signatures on three models with the same architecture
(GPT-2 small: 12 layers, width 768, 12 heads) trained on different data: English web text (OpenAI's
GPT-2) and protein sequences (RIKEN's MolCrawl GPT-2-small model on Hugging Face), with the same
architecture freshly initialized ("random") as a control for what the method finds in an untrained
network. A MolCrawl model trained on human DNA is supported too ("dna"), but session 20 left it out:
on random 1.5 kb segments of GRCh38 it predicted no better than token frequencies.

Stages:
  fit       J_l for the outputs of blocks 0..L-2, with the estimator of the authors' reference
            implementation (github.com/anthropics/jacobian-lens, jlens/fitting.py): one forward pass
            on the prompt replicated B times, then one backward pass per B output dimensions with a
            one-hot cotangent at every valid target position (positions 16..T-2) of the final
            block's output; the gradient at each source position is averaged over valid source
            positions. 128-token prompts. Sums for even and odd prompts are kept apart, for a
            split-half check.
  readout   On held-out prompts, per layer, for the J-lens and the logit lens: agreement of the
            readout's top token with the model's own next-token prediction (top-1 and top-5), the
            excess kurtosis of the readout logits, and the autocorrelation of the top token across
            positions against a shuffled-position null. Readouts are restricted to each model's
            content vocabulary (the 20 amino acids; all non-special DNA and text tokens), and for
            text and DNA also to random 20-token subsets of their 1,000 most frequent tokens, which
            gives a vocabulary-matched comparison with the protein model.
  geometry  From the J_l alone: linear CKA between layers of the (row-normalized) J-lens vectors,
            their effective dimensionality, their cosine with the logit-lens vectors, the split-half
            agreement of J_l, and the MLP gain of J-lens directions (how much the next block's MLP
            amplifies a unit perturbation along them, at real activations) against MLP output-weight
            directions and random directions.
  ignition  The ambiguous-input test of section 4.1.1, without the lens: one input embedding replaced
            by (1-a) e_B + a e_A, a swept over 21 values; at each layer, where the activation at that
            position sits on the line from the pure-B to the pure-A activation ("projection share"),
            and how sharp the switch is. Text: the authors' country pairs and carrier sentences
            (data/experiments/ignition.json of their repository). Proteins and DNA: real sequences
            with one token mixed between its own identity and another token. --ignition-design
            sequence runs that design on text and the untrained copy too (a real token among the 200
            most frequent, mixed with another of them), for a design-matched comparison.
  evals     Text (and the untrained control): the authors' lens-quality prompt sets (multihop,
            association, typo, poetry, multilingual), scored as pass@k for the J-lens and the logit
            lens, as a check that the lens finds known intermediates in a model this small.
  property  Proteins only: whether the lens holds a class of residues rather than the next one, read
            as the expected hydrophobicity of each layer's readout, correlated across positions with
            the hydrophobicity of the residues already read, of the next residue, of the next 8, and
            of residues 2 to 8 ahead, also as partial correlations (controlling for the residues read
            and the next one).

Usage:
  python3 tools/jlens_compare.py STAGE --model {text,protein,dna,random} --work DIR [options]
Needs torch, transformers, numpy, pandas (for the text corpus), sentencepiece (for DNA). Model weights, corpora and the J_l
matrices stay outside the repository (--models, --data, --work). On 4 CPU cores a fit is about 65 s
per prompt (768 backward passes over 128 tokens); the other stages take minutes. JLENS_THREADS sets
torch's thread count (default 4).
"""
import argparse, json, math, os, random, sys, time
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(int(os.environ.get("JLENS_THREADS", "4")))

MODEL_DIRS = {
    "text": "gpt2",
    "protein": "molcrawl-protein-sequence-gpt2-small",
    "dna": "molcrawl-genome-sequence-gpt2-small",
    "random": "gpt2",       # GPT-2's architecture and tokenizer with freshly initialized weights
}
SKIP_FIRST = 16      # as in the reference implementation: early positions act as attention sinks
SEQ_LEN = 128
AMINO = "LAGVSERTIDPKQNFYMHWC"   # the 20 standard amino acids (the protein vocabulary's content tokens)
EVAL_OFFSET = {"text": 1000, "random": 1000, "protein": 500, "dna": 100}   # held-out documents start here
# session 24: small protein models trained in this environment from one initialization on ordered,
# window-shuffled, shuffled and i.i.d. residues (tools/shuffled_rung.py); run with --data at that tool's
# data directory, whose proteins.fasta is the probe set
for _r in ["ordered", "window", "shuffled", "iid", "untrained", "ordered60m", "iidD"]:   # ordered60m: session 25, 60M tokens; iidD: session 26, a second i.i.d. run
    MODEL_DIRS["rung-" + _r] = "rung-" + _r
    EVAL_OFFSET["rung-" + _r] = 500


def is_protein(kind):
    return kind == "protein" or kind.startswith("rung-")


# ----------------------------------------------------------------------------- models and corpora

def load_model(kind, models_dir):
    from transformers import AutoConfig, AutoModelForCausalLM
    if kind == "random":
        torch.manual_seed(0)
        m = AutoModelForCausalLM.from_config(AutoConfig.from_pretrained(os.path.join(models_dir, MODEL_DIRS[kind]))).eval()
    else:
        m = AutoModelForCausalLM.from_pretrained(os.path.join(models_dir, MODEL_DIRS[kind]),
                                                 dtype=torch.float32).eval()
    for p in m.parameters():
        p.requires_grad_(False)
    return m


def load_vocab(kind, models_dir):
    """Token strings by id, and the ids of each model's content vocabulary."""
    tj = json.load(open(os.path.join(models_dir, MODEL_DIRS[kind], "tokenizer.json")))
    vocab = tj["model"]["vocab"]
    if isinstance(vocab, list):          # sentencepiece unigram format
        vocab = {t[0]: i for i, t in enumerate(vocab)}
    for a in tj.get("added_tokens", []):
        vocab[a["content"]] = a["id"]
    n = max(vocab.values()) + 1
    strings = [""] * n
    for s, i in vocab.items():
        strings[i] = s
    special = {a["id"] for a in tj.get("added_tokens", []) if a.get("special")}
    if is_protein(kind):
        content = [vocab[c] for c in AMINO]
    else:
        content = [i for i in range(n) if i not in special]
    return strings, content


def corpus(kind, data_dir, models_dir, n, offset, seed=20):
    """n token-id lists of SEQ_LEN tokens, starting at document `offset` of a seeded shuffle.
    Fit prompts use offset 0, held-out prompts EVAL_OFFSET[kind]."""
    rng = random.Random(seed)
    if kind in ("text", "random"):
        import pandas as pd
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(os.path.join(models_dir, MODEL_DIRS[kind]))
        docs = [t for t in pd.read_parquet(os.path.join(data_dir, "pile10k.parquet")).text if len(t) > 1500]
        rng.shuffle(docs)
        out = []
        for d in docs[offset:]:
            ids = [tok.eos_token_id] + tok(d[:4000])["input_ids"]   # <|endoftext|> marks a document start
            if len(ids) >= SEQ_LEN:
                out.append(ids[:SEQ_LEN])
            if len(out) == n:
                break
        return out
    if is_protein(kind):
        vocab = json.load(open(os.path.join(models_dir, MODEL_DIRS[kind], "tokenizer.json")))["model"]["vocab"]
        seqs, cur = [], []
        for line in open(os.path.join(data_dir, "proteins.fasta")):
            if line.startswith(">"):
                if cur:
                    seqs.append("".join(cur))
                cur = []
            else:
                cur.append(line.strip())
        if cur:
            seqs.append("".join(cur))
        seqs = [s for s in seqs if len(s) >= SEQ_LEN and set(s) <= set(AMINO)]
        rng.shuffle(seqs)
        return [[vocab["<cls>"]] + [vocab[c] for c in s[:SEQ_LEN - 1]] for s in seqs[offset:offset + n]]
    if kind == "dna":
        # the sentencepiece model the training data was encoded with (the Hugging Face conversion
        # prepends a word marker that maps to <unk>)
        import sentencepiece as spm
        sp = spm.SentencePieceProcessor(model_file=os.path.join(models_dir, MODEL_DIRS[kind], "spiece.model"))
        segs = [line.split()[2] for line in open(os.path.join(data_dir, "dna.txt"))]
        rng.shuffle(segs)
        out = []
        for s in segs[offset:]:
            ids = [sp.eos_id()] + sp.encode(s)   # </s> separates documents in training
            if len(ids) >= SEQ_LEN:
                out.append(ids[:SEQ_LEN])
            if len(out) == n:
                break
        return out
    raise ValueError(kind)


def run_blocks(model, ids=None, embeds=None):
    """Forward through the transformer body only (no unembedding). Returns the list of block
    outputs [h_0 .. h_{L-1}] (pre-final-norm residual stream) and the mid-block residuals (after
    attention, before the MLP) of every block."""
    tr = model.transformer
    outs, mids, hooks = [], [], []
    for blk in tr.h:
        hooks.append(blk.register_forward_hook(lambda mod, inp, out: outs.append(out[0] if isinstance(out, tuple) else out)))
        hooks.append(blk.ln_2.register_forward_hook(lambda mod, inp, out: mids.append(inp[0])))
    try:
        if embeds is None:
            tr(input_ids=ids)
        else:
            tr(inputs_embeds=embeds)
    finally:
        for h in hooks:
            h.remove()
    return outs, mids


def unembed(model, z):
    """The model's own readout: final LayerNorm, then the (tied) unembedding."""
    return model.lm_head(model.transformer.ln_f(z))


# ----------------------------------------------------------------------------- fit

def jacobian_for_prompt(model, ids, dim_batch):
    L = len(model.transformer.h)
    d = model.config.n_embd
    T = len(ids)
    valid = torch.arange(SKIP_FIRST, T - 1)
    x = torch.tensor([ids]).expand(dim_batch, -1)
    emb = model.transformer.wte(x).detach().requires_grad_(True)   # start the graph at the embeddings
    with torch.enable_grad():
        outs, _ = run_blocks(model, embeds=emb)
        target, sources = outs[L - 1], outs[:L - 1]
        J = [torch.zeros(d, d) for _ in sources]
        cot = torch.zeros_like(target)
        bidx = torch.arange(dim_batch)
        n_pass = math.ceil(d / dim_batch)
        for p, d0 in enumerate(range(0, d, dim_batch)):
            k = min(dim_batch, d - d0)
            cot.zero_()
            cot[bidx[:k, None], valid[None, :], d0 + bidx[:k, None]] = 1.0
            grads = torch.autograd.grad(target, sources, grad_outputs=cot, retain_graph=p < n_pass - 1)
            for l, g in enumerate(grads):
                J[l][d0:d0 + k] = g[:k, valid, :].mean(dim=1)
    return J


def stage_fit(a):
    model = load_model(a.model, a.models)
    prompts = corpus(a.model, a.data, a.models, a.n_prompts, 0)
    work = Path(a.work) / a.model
    work.mkdir(parents=True, exist_ok=True)
    ck = work / "fit_ckpt.pt"
    if ck.exists():
        st = torch.load(ck, weights_only=True)
    else:
        st = {"sum": [[torch.zeros(model.config.n_embd, model.config.n_embd) for _ in range(len(model.transformer.h) - 1)] for _ in range(2)],
              "n": [0, 0], "next": 0, "norms": []}
    print(f"fit {a.model}: {len(prompts)} prompts, resuming at {st['next']}", flush=True)
    for i in range(st["next"], len(prompts)):
        t0 = time.time()
        J = jacobian_for_prompt(model, prompts[i], a.dim_batch)
        half = i % 2
        for l in range(len(J)):
            st["sum"][half][l] += J[l]
        st["n"][half] += 1
        st["next"] = i + 1
        st["norms"].append([float(j.norm() / math.sqrt(j.shape[0])) for j in J])
        torch.save(st, str(ck) + ".tmp")
        os.replace(str(ck) + ".tmp", ck)
        print(f"  prompt {i + 1}/{len(prompts)}  {time.time() - t0:.0f}s  ||J_mid||/sqrt(d)={st['norms'][-1][len(J) // 2]:.3f}", flush=True)
    n = sum(st["n"])
    Jm = [(st["sum"][0][l] + st["sum"][1][l]) / n for l in range(len(st["sum"][0]))]
    Je = [st["sum"][0][l] / st["n"][0] for l in range(len(Jm))]
    Jo = [st["sum"][1][l] / st["n"][1] for l in range(len(Jm))]
    torch.save({"J": Jm, "J_even": Je, "J_odd": Jo, "n_prompts": n, "norms": st["norms"]}, work / "lens.pt")
    print("fit done", flush=True)


# ----------------------------------------------------------------------------- shared helpers

def load_lens(a, model):
    lens = torch.load(Path(a.work) / a.model / "lens.pt", weights_only=True)
    d = model.config.n_embd
    return lens["J"] + [torch.eye(d)], lens          # the final layer reads out through the identity


def frequent_tokens(prompts, content, k=1000):
    cs = set(content)
    counts = {}
    for p in prompts:
        for t in p[1:]:
            if t in cs:
                counts[t] = counts.get(t, 0) + 1
    return [t for t, _ in sorted(counts.items(), key=lambda x: -x[1])[:k]]


def excess_kurtosis(x, dim=-1):
    m = x.mean(dim, keepdim=True)
    v = ((x - m) ** 2).mean(dim)
    return ((x - m) ** 4).mean(dim) / v.clamp_min(1e-12) ** 2 - 3.0


def autocorr(top, max_delta=8, rng=None):
    """top: [n_prompts, n_pos] token ids. Rate of equal top tokens at distance 1..max_delta, and
    the same rate for random pairs of positions within the same prompt (the shuffled null)."""
    same = []
    for dlt in range(1, max_delta + 1):
        same.append((top[:, dlt:] == top[:, :-dlt]).float().mean().item())
    n, T = top.shape
    g = torch.Generator().manual_seed(0)
    i = torch.randint(0, T, (n, 4000), generator=g)
    j = torch.randint(0, T, (n, 4000), generator=g)
    keep = i != j
    null = (torch.gather(top, 1, i) == torch.gather(top, 1, j))[keep].float().mean().item()
    return float(np.mean(same)), null


# ----------------------------------------------------------------------------- readout

def stage_readout(a):
    model = load_model(a.model, a.models)
    strings, content = load_vocab(a.model, a.models)
    Js, _ = load_lens(a, model)
    L = len(model.transformer.h)
    prompts = corpus(a.model, a.data, a.models, a.n_eval, EVAL_OFFSET[a.model])
    fit_prompts = corpus(a.model, a.data, a.models, a.n_prompts, 0)
    freq = frequent_tokens(fit_prompts + prompts, content)
    rng = np.random.default_rng(0)
    subsets = [] if is_protein(a.model) else [rng.choice(freq, 20, replace=False).tolist() for _ in range(a.n_subsets)]
    cidx = torch.tensor(content)
    res = {"model": a.model, "n_prompts": len(prompts), "layers": list(range(L)), "content_vocab": len(content),
           "jlens": {k: [] for k in ["acc1", "acc5", "kurt", "auto", "auto_null", "not_in_or_out", "m_acc1", "m_kurt", "m_auto", "m_auto_null"]},
           "logit": {k: [] for k in ["acc1", "acc5", "kurt", "auto", "auto_null", "not_in_or_out", "m_acc1", "m_kurt", "m_auto", "m_auto_null"]},
           "examples": []}
    with torch.no_grad():
        H = []      # per prompt: [L, T, d]
        for ids in prompts:
            outs, _ = run_blocks(model, ids=torch.tensor([ids]))
            H.append(torch.stack([o[0] for o in outs]))
        H = torch.stack(H)                                  # [n, L, T, d]
        pos = torch.arange(SKIP_FIRST, SEQ_LEN - 1)
        ids_t = torch.tensor(prompts)
        final_logits = unembed(model, H[:, L - 1, pos])     # [n, P, V]
        model_top = cidx[final_logits[..., cidx].argmax(-1)]   # model's prediction within the content vocabulary
        cur_tok = ids_t[:, pos]
        for l in range(L):
            for lens_name in ["jlens", "logit"]:
                h = H[:, l, pos]                                    # [n, P, d]
                z = h @ Js[l].T if lens_name == "jlens" else h
                logits = unembed(model, z)[..., cidx]               # [n, P, C]
                top = cidx[logits.argmax(-1)]
                top5 = cidx[logits.topk(5, -1).indices]
                r = res[lens_name]
                r["acc1"].append((top == model_top).float().mean().item())
                r["acc5"].append((top5 == model_top[..., None]).any(-1).float().mean().item())
                r["kurt"].append(excess_kurtosis(logits).mean().item())
                s, nul = autocorr(top)
                r["auto"].append(s); r["auto_null"].append(nul)
                r["not_in_or_out"].append(((top != model_top) & (top != cur_tok)).float().mean().item())
                if subsets:   # vocabulary-matched: 20 frequent tokens at a time, as many as the amino acids
                    acc, ku, au, aun = [], [], [], []
                    full = unembed(model, z)
                    mt_full = final_logits
                    for sub in subsets:
                        si = torch.tensor(sub)
                        lg = full[..., si]
                        tp = si[lg.argmax(-1)]
                        mt = si[mt_full[..., si].argmax(-1)]
                        acc.append((tp == mt).float().mean().item())
                        ku.append(excess_kurtosis(lg).mean().item())
                        s2, n2 = autocorr(tp)
                        au.append(s2); aun.append(n2)
                    r["m_acc1"].append(float(np.mean(acc))); r["m_kurt"].append(float(np.mean(ku)))
                    r["m_auto"].append(float(np.mean(au))); r["m_auto_null"].append(float(np.mean(aun)))
            print(f"  layer {l}: J acc1={res['jlens']['acc1'][-1]:.3f} kurt={res['jlens']['kurt'][-1]:.2f} auto={res['jlens']['auto'][-1]:.3f}/{res['jlens']['auto_null'][-1]:.3f}"
                  f" | logit acc1={res['logit']['acc1'][-1]:.3f} kurt={res['logit']['kurt'][-1]:.2f} auto={res['logit']['auto'][-1]:.3f}/{res['logit']['auto_null'][-1]:.3f}", flush=True)
        # a few readable examples: top-5 J-lens tokens per layer at fixed positions of the first prompts
        for pi in range(min(3, len(prompts))):
            for t in [40, 80, 120]:
                ex = {"prompt": pi, "pos": t, "input": strings[prompts[pi][t]],
                      "context": "".join(strings[x] for x in prompts[pi][max(0, t - 12):t + 1]).replace("Ġ", " ").replace("▁", " "),
                      "layers": {}}
                for l in range(L):
                    lg = unembed(model, H[pi, l, t] @ Js[l].T)[cidx]
                    ex["layers"][l] = [strings[content[j]] for j in lg.topk(5).indices.tolist()]
                res["examples"].append(ex)
    out = Path(a.work) / a.model / "readout.json"
    json.dump(res, open(out, "w"), indent=1)
    print("readout done", out, flush=True)


# ----------------------------------------------------------------------------- geometry

def lens_vectors(model, J, rows):
    """J-lens vectors for the given token ids: rows of W_U diag(gamma) C J (C centres the residual,
    as LayerNorm does; gamma is the final LayerNorm's gain)."""
    W = model.lm_head.weight[rows] * model.transformer.ln_f.weight[None, :]
    W = W - W.mean(1, keepdim=True)
    return W @ J


def linear_cka(X, Y):
    X = X - X.mean(0, keepdim=True)
    Y = Y - Y.mean(0, keepdim=True)
    xy = (Y.T @ X).pow(2).sum()
    return (xy / ((X.T @ X).pow(2).sum().sqrt() * (Y.T @ Y).pow(2).sum().sqrt())).item()


def eff_dim(V, share=0.9):
    V = V - V.mean(0, keepdim=True)
    s = torch.linalg.svdvals(V) ** 2
    c = torch.cumsum(s, 0) / s.sum()
    k = int((c < share).sum().item()) + 1
    return k, k / min(V.shape)


def stage_geometry(a):
    model = load_model(a.model, a.models)
    strings, content = load_vocab(a.model, a.models)
    Js, lens = load_lens(a, model)
    L = len(model.transformer.h)
    d = model.config.n_embd
    fit_prompts = corpus(a.model, a.data, a.models, a.n_prompts, 0)
    freq = frequent_tokens(fit_prompts, content)
    rows = torch.tensor(content)
    rng = np.random.default_rng(0)
    subsets = [] if is_protein(a.model) else [torch.tensor(rng.choice(freq, 20, replace=False)) for _ in range(a.n_subsets)]
    res = {"model": a.model, "layers": list(range(L)), "n_prompts": lens["n_prompts"]}
    with torch.no_grad():
        V = [lens_vectors(model, Js[l], rows) for l in range(L)]
        Vn = [v / v.norm(dim=1, keepdim=True) for v in V]
        res["cka"] = [[linear_cka(Vn[i], Vn[j]) for j in range(L)] for i in range(L)]
        if subsets:
            res["cka_matched"] = [[float(np.mean([linear_cka(*(lens_vectors(model, Js[x], s) / lens_vectors(model, Js[x], s).norm(dim=1, keepdim=True) for x in (i, j))) for s in subsets[:20]]))
                                   for j in range(L)] for i in range(L)]
        res["eff_dim90"] = [eff_dim(v)[0] for v in V]
        res["eff_dim90_frac"] = [eff_dim(v)[1] for v in V]
        if subsets:
            res["eff_dim90_matched"] = [float(np.mean([eff_dim(lens_vectors(model, Js[l], s))[0] for s in subsets[:20]])) for l in range(L)]
        logit_v = lens_vectors(model, torch.eye(d), rows)
        res["cos_with_logit_lens"] = [torch.nn.functional.cosine_similarity(V[l], logit_v, dim=1).mean().item() for l in range(L)]
        # split-half reliability of J: cosine between the even- and odd-prompt J-lens vectors
        res["split_half_cos"] = [torch.nn.functional.cosine_similarity(lens_vectors(model, lens["J_even"][l], rows), lens_vectors(model, lens["J_odd"][l], rows), dim=1).mean().item()
                                 for l in range(L - 1)] + [1.0]
        res["J_norm_per_prompt_mid"] = [n[(L - 1) // 2] for n in lens["norms"]]
    # MLP gain: how much block l+1's MLP (with its LayerNorm) amplifies a unit perturbation of the
    # residual along a direction, at real mid-block activations; normalized by the median over random directions
    prompts = corpus(a.model, a.data, a.models, 8, EVAL_OFFSET[a.model])
    with torch.no_grad():
        mids = []
        for ids in prompts:
            _, m = run_blocks(model, ids=torch.tensor([ids]))
            mids.append(torch.stack([x[0, SKIP_FIRST:] for x in m]))
        mids = torch.cat(mids, 1)                         # [L, N, d]
    g = torch.Generator().manual_seed(0)
    sel = torch.randperm(mids.shape[1], generator=g)[:96]
    ndir = 120
    res["mlp_gain"] = {"jlens": [], "neuron_out": [], "logit_lens": [], "random": []}
    for l in range(L - 1):
        blk = model.transformer.h[l + 1]
        f = lambda x: blk.mlp(blk.ln_2(x))
        X = mids[l + 1, sel]                              # [96, d]
        pick = torch.randperm(len(content), generator=g)[:ndir]
        dirs = {"jlens": V[l][pick], "logit_lens": logit_v[pick],
                "neuron_out": model.transformer.h[l].mlp.c_proj.weight[torch.randperm(model.transformer.h[l].mlp.c_proj.weight.shape[0], generator=g)[:ndir]],
                "random": torch.randn(ndir, d, generator=g)}
        gains = {}
        for k, D in dirs.items():
            D = D / D.norm(dim=1, keepdim=True)
            out = []
            for v in D:
                _, jv = torch.func.jvp(f, (X,), (v.expand_as(X),))
                out.append(jv.norm(dim=1).mean().item())
            gains[k] = np.array(out)
        base = np.median(gains["random"])
        for k in gains:
            res["mlp_gain"][k].append(float(np.median(gains[k]) / base))
        print(f"  layer {l}: cka(l,l+1)={res['cka'][l][l + 1]:.3f} effdim={res['eff_dim90'][l]} split-half={res['split_half_cos'][l]:.3f} "
              f"gain J={res['mlp_gain']['jlens'][-1]:.2f} neuron={res['mlp_gain']['neuron_out'][-1]:.2f} logit={res['mlp_gain']['logit_lens'][-1]:.2f}", flush=True)
    out = Path(a.work) / a.model / "geometry.json"
    json.dump(res, open(out, "w"), indent=1)
    print("geometry done", out, flush=True)


# ----------------------------------------------------------------------------- ignition

def ignition_items(a, model):
    """(ids, position, token_A, token_B) items."""
    from transformers import AutoTokenizer
    items = []
    rng = random.Random(1)
    if a.model in ("text", "random") and a.ignition_design == "countries":
        tok = AutoTokenizer.from_pretrained(os.path.join(a.models, MODEL_DIRS["text"]))
        ig = json.load(open(a.ignition_json))
        countries = [c for c in ig["countries_12"] if len(tok(" " + c)["input_ids"]) == 1]
        pairs = [(x, y) for i, x in enumerate(countries) for y in countries[i + 1:]]
        rng.shuffle(pairs)
        for (A, B) in pairs[:16]:
            for tmpl in ig["ctx_templates"][:6]:
                pre = tmpl.split("{W}")[0].rstrip()
                ids = [tok.eos_token_id] + tok(pre)["input_ids"] + tok(" " + B)["input_ids"]
                items.append((ids, len(ids) - 1, tok(" " + A)["input_ids"][0], tok(" " + B)["input_ids"][0]))
        return items
    prompts = corpus(a.model, a.data, a.models, 96, EVAL_OFFSET[a.model])
    strings, content = load_vocab(a.model, a.models)
    pool = content if is_protein(a.model) else frequent_tokens(prompts, content, 200)
    for ids in prompts:
        p = rng.randrange(40, SEQ_LEN - 8)
        if not is_protein(a.model):    # as with amino acids, the real token is one of a small set of frequent ones
            spots = [q for q in range(40, SEQ_LEN - 8) if ids[q] in pool]
            if not spots:
                continue
            p = rng.choice(spots)
        B = ids[p]
        A = rng.choice([c for c in pool if c != B])
        items.append((ids[:p + 1], p, A, B))
    return items


def stage_ignition(a):
    model = load_model(a.model, a.models)
    L = len(model.transformer.h)
    items = ignition_items(a, model)
    alphas = torch.linspace(0, 1, 21)
    wte, wpe = model.transformer.wte.weight, model.transformer.wpe.weight
    share = torch.zeros(len(items), L, len(alphas))
    with torch.no_grad():
        for n, (ids, p, A, B) in enumerate(items):
            x = torch.tensor([ids]).expand(len(alphas), -1)
            emb = wte[x].clone()
            emb[:, p] = (1 - alphas[:, None]) * wte[B] + alphas[:, None] * wte[A]
            outs, _ = run_blocks(model, embeds=emb)
            for l in range(L):
                h = outs[l][:, p]                                   # [21, d]
                h0, h1 = h[0], h[-1]
                share[n, l] = ((h - h0) @ (h1 - h0)) / (h1 - h0).pow(2).sum().clamp_min(1e-12)
    res = {"model": a.model, "n_items": len(items), "alphas": alphas.tolist(), "layers": list(range(L)),
           "mean_share": share.mean(0).tolist()}
    # sharpness: the steepest step of the mean curve, the share of interior alphas whose readings sit
    # within 0.1 of an endpoint (linear response: ~0.16; step: ~1), and bimodality at alpha = 0.5
    # (mean |share - 0.5| x 2: 0 if every item sits halfway, 1 if every item is at an endpoint)
    inner = share[:, :, 1:-1]
    res["max_slope"] = [float((torch.diff(share[:, l], dim=1) / 0.05).max(1).values.median()) for l in range(L)]
    res["near_endpoint"] = [float(((inner[:, l] < 0.1) | (inner[:, l] > 0.9)).float().mean()) for l in range(L)]
    res["bimodality_mid"] = [float(((share[:, l, 10] - 0.5).abs() * 2).clamp(max=1).mean()) for l in range(L)]
    for l in range(L):
        print(f"  layer {l}: max_slope={res['max_slope'][l]:.2f} near_endpoint={res['near_endpoint'][l]:.2f} bimodal@0.5={res['bimodality_mid'][l]:.2f}", flush=True)
    res["design"] = "countries" if (a.model in ("text", "random") and a.ignition_design == "countries") else "sequence"
    name = "ignition.json" if a.ignition_design == "countries" or a.model not in ("text", "random") else "ignition_sequence.json"
    out = Path(a.work) / a.model / name
    json.dump(res, open(out, "w"), indent=1)
    print("ignition done", out, flush=True)


# ----------------------------------------------------------------------------- property (proteins)

KYTE_DOOLITTLE = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5,
                  "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2}


def stage_property(a):
    """What a protein model's lens holds when its only words are amino acids: the expected
    hydrophobicity (Kyte-Doolittle) of each layer's J-lens readout, correlated across positions
    with the hydrophobicity of the residues already read (a window of 8), of the next residue, and
    of the next 8. Text has a word for "hydrophobic"; here the content can only show as a
    preference for a class of letters. Also for the logit lens and the model's own output."""
    assert is_protein(a.model)
    model = load_model(a.model, a.models)
    strings, content = load_vocab(a.model, a.models)
    Js, _ = load_lens(a, model)
    L = len(model.transformer.h)
    prompts = corpus(a.model, a.data, a.models, 120, EVAL_OFFSET[a.model])
    kd = torch.tensor([KYTE_DOOLITTLE[strings[c]] for c in content])
    kd_of = {c: KYTE_DOOLITTLE[strings[c]] for c in content}
    W = 8
    pos = list(range(SKIP_FIRST, SEQ_LEN - 1 - W))
    past, nxt, fut, far = [], [], [], []
    for ids in prompts:
        for t in pos:
            past.append(np.mean([kd_of[x] for x in ids[t - W + 1:t + 1]]))
            nxt.append(kd_of[ids[t + 1]])
            fut.append(np.mean([kd_of[x] for x in ids[t + 1:t + 1 + W]]))
            far.append(np.mean([kd_of[x] for x in ids[t + 2:t + 1 + W]]))
    past, nxt, fut, far = map(np.array, (past, nxt, fut, far))

    def partial_r(e, y, controls):
        """Correlation of e and y after regressing both on the controls (with an intercept)."""
        X = np.column_stack([np.ones_like(e)] + controls)
        re = e - X @ np.linalg.lstsq(X, e, rcond=None)[0]
        ry = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
        return float(np.corrcoef(re, ry)[0, 1])
    cidx = torch.tensor(content)
    res = {"model": a.model, "n_prompts": len(prompts), "window": W, "layers": list(range(L)), "jlens": {}, "logit": {}}
    with torch.no_grad():
        H = torch.stack([torch.stack([o[0] for o in run_blocks(model, ids=torch.tensor([ids]))[0]]) for ids in prompts])   # [n, L, T, d]
        for name in ["jlens", "logit"]:
            rows = {"past": [], "next": [], "future": [], "far": [], "far_partial": [], "next_partial": [], "sd": []}
            for l in range(L):
                h = H[:, l, pos]
                z = h @ Js[l].T if name == "jlens" else h
                p = torch.softmax(unembed(model, z)[..., cidx], -1)
                e = (p @ kd).reshape(-1).numpy()
                rows["past"].append(float(np.corrcoef(e, past)[0, 1]))
                rows["next"].append(float(np.corrcoef(e, nxt)[0, 1]))
                rows["future"].append(float(np.corrcoef(e, fut)[0, 1]))
                rows["far"].append(float(np.corrcoef(e, far)[0, 1]))
                # residues 2..8 ahead, beyond what the residues already read and the next one explain
                rows["far_partial"].append(partial_r(e, far, [past, nxt]))
                rows["next_partial"].append(partial_r(e, nxt, [past]))
                rows["sd"].append(float(e.std()))
            res[name] = rows
        print("layer  J:past/next/future/far | partial next, far   logit: same", flush=True)
        for l in range(L):
            j, g = res["jlens"], res["logit"]
            print(f"  {l:2d}   {j['past'][l]:.2f} {j['next'][l]:.2f} {j['future'][l]:.2f} {j['far'][l]:.2f} | {j['next_partial'][l]:.2f} {j['far_partial'][l]:.2f}"
                  f"    {g['past'][l]:.2f} {g['next'][l]:.2f} {g['future'][l]:.2f} {g['far'][l]:.2f} | {g['next_partial'][l]:.2f} {g['far_partial'][l]:.2f}", flush=True)
    out = Path(a.work) / a.model / "property.json"
    json.dump(res, open(out, "w"), indent=1)
    print("property done", out, flush=True)


# ----------------------------------------------------------------------------- evals (text)

def stage_evals(a):
    """Does the lens find known intermediates in a model this small? The authors' lens-quality
    prompt sets (data/evaluations/ of their repository): for each item, the best rank over layers of
    each intermediate word (any single-token form: with or without a leading space, capitalized or
    not) at the readout position, for the J-lens and the logit lens. pass@k as in their README."""
    assert a.model in ("text", "random")
    from transformers import AutoTokenizer
    model = load_model(a.model, a.models)
    tok = AutoTokenizer.from_pretrained(os.path.join(a.models, MODEL_DIRS["text"]))
    Js, _ = load_lens(a, model)
    L = len(model.transformer.h)
    res = {"model": a.model}
    for name in ["multihop", "association", "typo", "poetry", "multilingual"]:
        items = json.load(open(os.path.join(a.evals_dir, f"lens-eval-{name}.json")))["items"]
        ranks = {"jlens": [], "logit": []}
        n_skipped = 0
        for it in items:
            prompt = it["prompt"].rstrip(" ")
            ids = [tok.eos_token_id] + tok(prompt)["input_ids"]
            if name == "poetry":
                nl = [i for i, t in enumerate(ids) if "\n" in tok.decode([t])]
                pos = nl[-1]
            else:
                pos = len(ids) - 1
            targets = []
            for w in it["intermediates"]:
                forms = {w, " " + w, w.capitalize(), " " + w.capitalize(), w.lower(), " " + w.lower()}
                tids = {tok(f)["input_ids"][0] for f in forms if len(tok(f)["input_ids"]) == 1}
                if tids:
                    targets.append(sorted(tids))
                else:
                    n_skipped += 1
            if not targets:
                continue
            with torch.no_grad():
                outs, _ = run_blocks(model, ids=torch.tensor([ids]))
                for lens_name in ["jlens", "logit"]:
                    best = [10 ** 9] * len(targets)
                    for l in range(L):
                        h = outs[l][0, pos]
                        z = Js[l] @ h if lens_name == "jlens" else h
                        lg = unembed(model, z)
                        order = torch.argsort(lg, descending=True)
                        rank = torch.empty_like(order)
                        rank[order] = torch.arange(len(order))
                        for k, tids in enumerate(targets):
                            best[k] = min(best[k], int(min(rank[t] for t in tids)) + 1)
                    ranks[lens_name].append(best)
        entry = {"n_items": len(ranks["jlens"]), "n_words_skipped": n_skipped}
        for lens_name in ["jlens", "logit"]:
            flat = [r for item in ranks[lens_name] for r in item]
            entry[lens_name] = {f"pass@{k}": float(np.mean([r <= k for r in flat])) for k in [1, 10, 25, 100, 1000]}
            entry[lens_name]["median_rank"] = float(np.median(flat))
        res[name] = entry
        print(name, json.dumps(entry), flush=True)
    out = Path(a.work) / a.model / "evals.json"
    json.dump(res, open(out, "w"), indent=1)
    print("evals done", out, flush=True)


# ----------------------------------------------------------------------------- mlpsign (session 24)

def stage_mlpsign(a):
    """Is the MLP gain amplification or suppression? The gain in stage geometry is the norm of the
    next block's MLP response to a unit perturbation v, so an MLP that cancels v scores as high as one
    that reinforces it. Here, with the same directions and activations: the gain again, the cosine of
    the response with v (+1: reinforces, -1: opposes, 0: turns it elsewhere), and the net change of
    the residual's component along v after the MLP adds its output (1 + v.Jv: 1 means the MLP leaves
    the component alone, 0 means it cancels it, above 1 that it amplifies it)."""
    model = load_model(a.model, a.models)
    strings, content = load_vocab(a.model, a.models)
    Js, lens = load_lens(a, model)
    L = len(model.transformer.h)
    d = model.config.n_embd
    rows = torch.tensor(content)
    with torch.no_grad():
        V = [lens_vectors(model, Js[l], rows) for l in range(L)]
        logit_v = lens_vectors(model, torch.eye(d), rows)
    prompts = corpus(a.model, a.data, a.models, 8, EVAL_OFFSET[a.model])
    with torch.no_grad():
        mids = []
        for ids in prompts:
            _, m = run_blocks(model, ids=torch.tensor([ids]))
            mids.append(torch.stack([x[0, SKIP_FIRST:] for x in m]))
        mids = torch.cat(mids, 1)
    g = torch.Generator().manual_seed(0)
    sel = torch.randperm(mids.shape[1], generator=g)[:96]
    ndir = 120
    res = {"model": a.model, "gain": {}, "cos": {}, "net_along_v": {}, "abs_gain": {}}
    for k in ["jlens", "neuron_out", "logit_lens", "random"]:
        for key in res:
            if key != "model":
                res[key][k] = []
    for l in range(L - 1):
        blk = model.transformer.h[l + 1]
        f = lambda x: blk.mlp(blk.ln_2(x))
        X = mids[l + 1, sel]
        pick = torch.randperm(len(content), generator=g)[:ndir]
        dirs = {"jlens": V[l][pick], "logit_lens": logit_v[pick],
                "neuron_out": model.transformer.h[l].mlp.c_proj.weight[torch.randperm(model.transformer.h[l].mlp.c_proj.weight.shape[0], generator=g)[:ndir]],
                "random": torch.randn(ndir, d, generator=g)}
        out = {}
        for k, D in dirs.items():
            D = D / D.norm(dim=1, keepdim=True)
            gn, cs, net = [], [], []
            for v in D:
                _, jv = torch.func.jvp(f, (X,), (v.expand_as(X),))
                along = jv @ v                                       # [96]
                gn.append(jv.norm(dim=1).mean().item())
                cs.append((along / jv.norm(dim=1).clamp_min(1e-12)).mean().item())
                net.append((1 + along).mean().item())
            out[k] = (np.array(gn), np.array(cs), np.array(net))
        base = np.median(out["random"][0])
        for k, (gn, cs, net) in out.items():
            res["abs_gain"][k].append(float(np.median(gn)))      # norm of the response to a unit perturbation
            res["gain"][k].append(float(np.median(gn) / base))
            res["cos"][k].append(float(np.median(cs)))
            res["net_along_v"][k].append(float(np.median(net)))
        print(f"  layer {l}: J gain={res['gain']['jlens'][-1]:.2f} cos={res['cos']['jlens'][-1]:+.2f} net={res['net_along_v']['jlens'][-1]:.2f}"
              f" | neuron gain={res['gain']['neuron_out'][-1]:.2f} cos={res['cos']['neuron_out'][-1]:+.2f} | random cos={res['cos']['random'][-1]:+.2f}", flush=True)
    outp = Path(a.work) / a.model / "mlpsign.json"
    json.dump(res, open(outp, "w"), indent=1)
    print("mlpsign done", outp, flush=True)


# ----------------------------------------------------------------------------- mlpstatic (session 25)

def stage_mlpstatic(a):
    """The workspace study's own definition of MLP gain (Gurnee, Sofroniew et al. 2026, section 4.3.1):
    "the output norm of the MLP block at layer l+1 when applied to v, normalized by the median output
    norm over isotropic random directions", for unit directions v. Stages geometry and mlpsign measure
    instead the norm of the MLP's response to a small push along v at the network's real states (a
    Jacobian). nuntiator (Delvetown, session 24) asked whether the i.i.d. network's pass survives the
    study's version. Here both, on the same directions: 'static' = |MLP(LN(v))| with the block's own
    LayerNorm (in GPT-2 the MLP only ever sees its input through it), 'jvp' = the session-24 measure."""
    model = load_model(a.model, a.models)
    strings, content = load_vocab(a.model, a.models)
    Js, lens = load_lens(a, model)
    L = len(model.transformer.h)
    d = model.config.n_embd
    rows = torch.tensor(content)
    with torch.no_grad():
        V = [lens_vectors(model, Js[l], rows) for l in range(L)]
        logit_v = lens_vectors(model, torch.eye(d), rows)
    prompts = corpus(a.model, a.data, a.models, 8, EVAL_OFFSET[a.model])
    with torch.no_grad():
        mids = []
        for ids in prompts:
            _, m = run_blocks(model, ids=torch.tensor([ids]))
            mids.append(torch.stack([x[0, SKIP_FIRST:] for x in m]))
        mids = torch.cat(mids, 1)
    g = torch.Generator().manual_seed(0)            # the same draws as stages geometry and mlpsign
    sel = torch.randperm(mids.shape[1], generator=g)[:96]
    ndir = 120
    res = {"model": a.model, "static": {}, "jvp": {}, "static_abs": {}}
    for key in ["static", "jvp", "static_abs"]:
        for k in ["jlens", "neuron_out", "logit_lens", "random"]:
            res[key][k] = []
    for l in range(L - 1):
        blk = model.transformer.h[l + 1]
        f = lambda x: blk.mlp(blk.ln_2(x))
        X = mids[l + 1, sel]
        pick = torch.randperm(len(content), generator=g)[:ndir]
        dirs = {"jlens": V[l][pick], "logit_lens": logit_v[pick],
                "neuron_out": model.transformer.h[l].mlp.c_proj.weight[torch.randperm(model.transformer.h[l].mlp.c_proj.weight.shape[0], generator=g)[:ndir]],
                "random": torch.randn(ndir, d, generator=g)}
        st, jg = {}, {}
        for k, D in dirs.items():
            D = D / D.norm(dim=1, keepdim=True)
            with torch.no_grad():
                st[k] = f(D).norm(dim=1).numpy()
            out = []
            for v in D:
                _, jv = torch.func.jvp(f, (X,), (v.expand_as(X),))
                out.append(jv.norm(dim=1).mean().item())
            jg[k] = np.array(out)
        bs, bj = np.median(st["random"]), np.median(jg["random"])
        for k in dirs:
            res["static"][k].append(float(np.median(st[k]) / bs))
            res["static_abs"][k].append(float(np.median(st[k])))
            res["jvp"][k].append(float(np.median(jg[k]) / bj))
        print(f"  layer {l}: static J={res['static']['jlens'][-1]:.2f} neuron={res['static']['neuron_out'][-1]:.2f} logit={res['static']['logit_lens'][-1]:.2f}"
              f" | jvp J={res['jvp']['jlens'][-1]:.2f} neuron={res['jvp']['neuron_out'][-1]:.2f}", flush=True)
    outp = Path(a.work) / a.model / "mlpstatic.json"
    json.dump(res, open(outp, "w"), indent=1)
    print("mlpstatic done", outp, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["fit", "readout", "geometry", "ignition", "property", "evals", "mlpsign", "mlpstatic"])
    ap.add_argument("--evals-dir", default="/home/user/jdata/evaluations")
    ap.add_argument("--model", required=True, choices=list(MODEL_DIRS))
    ap.add_argument("--models", default="/home/user/models")
    ap.add_argument("--data", default="/home/user/jdata")
    ap.add_argument("--work", default="/home/user/jwork")
    ap.add_argument("--n-prompts", type=int, default=48)
    ap.add_argument("--n-eval", type=int, default=40)
    ap.add_argument("--n-subsets", type=int, default=50)
    ap.add_argument("--dim-batch", type=int, default=32)
    ap.add_argument("--ignition-json", default="/home/user/jdata/ignition.json")
    ap.add_argument("--ignition-design", choices=["countries", "sequence"], default="countries",
                    help="text and random only: the authors' country blends, or the protein design (one token of a real passage blended with another frequent token)")
    a = ap.parse_args()
    {"fit": stage_fit, "readout": stage_readout, "geometry": stage_geometry, "ignition": stage_ignition,
     "property": stage_property, "evals": stage_evals, "mlpsign": stage_mlpsign, "mlpstatic": stage_mlpstatic}[a.stage](a)


if __name__ == "__main__":
    main()
