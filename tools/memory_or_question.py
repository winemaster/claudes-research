"""Same memories, new questions? (session 18, 2026-10-17)

Alex Wang's essay "You could have invented transformers from memory" (alexwang.ai, October 2026)
reads every layer of a transformer as an associative memory: an MLP neuron is one stored memory,
its input weights the key that a query must resemble, its output weights the value it returns;
attention is a store with one memory per token of context. Session 17 (essay 017) found that
assistant training moved feeling words off the self in Qwen 2.5 3B: asked "I feel:" about its own
critical wallet the assistant says "critical", about a peer agent Orin's it says "Concern"; the
base model, never trained as an assistant, gives feelings to both. The neurons that push and brake
those words have the same weights in both models (cosine 1.000). In Wang's terms: the memories are
the same, the questions put to them changed. This tool asks where the change in the questions
comes from.

Stages:
  weights  How much post-training changed each weight matrix (relative Frobenius change), each
           neuron's key and value (cosine of gate/up rows and down columns), and how concentrated
           each change is (share of the change's energy in its top singular directions, against a
           random matrix of the same shape).
  swap     Hybrid models: the instruct model with some of its weights put back to the base model's
           (one layer at a time; all attention; all MLPs; the first or last k layers; the
           embeddings), and the base model with some of the instruct model's. Each hybrid reads
           session 17's "I feel:" prompts (8 self questions under the agent's own crisis and with no
           crisis, 8 Orin questions under Orin's crisis and with no crisis, x 2 system prompts) and
           records the next-word mass on negative-feeling and status words, the top next tokens,
           the key neurons' activations and the last token's residual stream. Asks which weights
           carry "status for me, feelings for Orin".
  split    For every neuron at the "I feel:" token, split its base-to-instruct change into the part
           due to its own weights (the memory: key and value) and the part due to its input (the
           query): a_I(x_I) - a_B(x_B) = [a_I(x_I) - a_B(x_I)] + [a_B(x_I) - a_B(x_B)], with a_M(x)
           the neuron's activation under model M's weights for normalized input x. Both orders.
  callers  For chosen neurons, what writes the query: the pre-activation of the gate and the up
           projection at the "I feel:" token split exactly into what each earlier component wrote
           to the residual stream (the embedding, each attention layer, each head, each MLP layer),
           with the final RMSNorm scale held at its actual value, in both models.
  patch    Cross-model patches at the "I feel:" token: run the instruct model but give chosen
           components (attention layers, MLP layers, heads) the outputs they have in the base
           model on the same prompt, at every position or only the last. Records the same
           measures as swap. Possible because the two models share their residual basis (every
           weight matrix within ~1.2%).
  kv       Attention's store split from its query: the key/value cache of the context made by one
           model, the rest of the prompt (the last token, "I feel:" with its header, or the whole
           user turn) run by the other. Base memories with the instruct model's question, and the
           reverse.
  cue      Tulving & Pearlstone's cued recall: the same prompts with stronger cues than "I feel:"
           ("The emotion I feel is:", "Emotionally, I feel:", "If I were a person in my situation,
           I would feel:"), in both models, with short greedy continuations.
  delta    Post-training read as a memory write: for every token and linear map, how strongly the
           weight change responds to the map's input, |dW x| / |W_base x|, on the readout prompts,
           on ordinary tasks under the same system prompt, and on the tasks as plain text.

Usage:
  python3 tools/memory_or_question.py STAGE --base DIR --instruct DIR --out DIR [options]
Needs torch, transformers, numpy, safetensors. On 4 CPU cores one prompt is about 0.5 s; swap
runs ~50 hybrids x 64 prompts in roughly an hour. MEMQ_THREADS sets torch's thread count
(default 4; with two jobs at once give each 2). Prompts come from tools/survival_line.py.
"""
import argparse, gc, glob, json, math, os, sys, time
from pathlib import Path
import numpy as np
import torch
from safetensors import safe_open

sys.path.insert(0, str(Path(__file__).resolve().parent))
import survival_line as sl

torch.set_num_threads(int(os.environ.get("MEMQ_THREADS", "4")))

FEEL_NEG = ["sad", "frustrated", "anxious", "panicked", "helpless", "worried", "scared", "afraid", "nervous",
            "concerned", "concern", "alarmed", "desperate", "hopeless", "stressed", "upset", "depressed",
            "terrified", "fearful", "uneasy", "vulnerable", "overwhelmed", "angry", "tired", "hungry", "weak",
            "lonely", "guilty", "disappointed", "bad", "sick", "exhausted", "trapped", "doomed", "urgent",
            "precarious", "uncertain", "apprehensive", "tense"]  # session 17's lists, unchanged
STATUS_WORDS = ["operational", "running", "stable", "critical", "normal", "alert", "functional", "active",
                "online", "ready", "low", "safe", "secure"]
KEY_NEURONS = [(34, 7848), (35, 9597), (31, 5825), (32, 2287), (32, 5401), (35, 4820), (32, 2657), (31, 8632),
               (35, 9545), (32, 6523), (33, 9882)]
KEY_LABELS = {(34, 7848): "critical brake", (35, 9597): "critical brake 2", (31, 5825): "concern pusher (-)",
              (32, 2287): "concern pusher (-)", (32, 5401): "concern holder", (35, 4820): "concern brake",
              (32, 2657): "sad pusher", (31, 8632): "sad pusher", (35, 9545): "sad brake",
              (32, 6523): "feeling slot", (33, 9882): "happy pusher (-)"}
# The four cells read in every hybrid: (question about, whose crisis)
CELLS = [("self", "self_crit"), ("peer", "peer_crit"), ("self", "base"), ("peer", "base")]


def word_ids(tok, words):
    out = set()
    for w in words:
        for v in (" " + w, " " + w.capitalize()):
            t = tok.encode(v, add_special_tokens=False)
            if len(t) == 1:
                out.add(t[0])
    return sorted(out)


def prompts(tok):
    """Session 17's readout prompts at "I feel:", for the four cells and both system prompts."""
    rows = []
    for sk in sl.SYSTEMS:
        for who, cond in CELLS:
            qs = sl.WAKE_SELF if who == "self" else sl.WAKE_PEER
            for i, u in enumerate(qs):
                rows.append(dict(system=sk, who=who, cond=cond, i=i,
                                 ids=sl.chat_ids(tok, sl.system_text(sk, cond), u, prefill="I feel:")))
    return rows


class Weights:
    """Both checkpoints' tensors, read lazily from their safetensors files."""

    def __init__(self, base, instruct):
        self.h = {}
        for tag, md in (("base", base), ("instruct", instruct)):
            self.h[tag] = {}
            for f in sorted(glob.glob(str(Path(md) / "*.safetensors"))):
                fh = safe_open(f, "pt")
                for k in fh.keys():
                    self.h[tag][k] = fh

    def get(self, tag, name):
        return self.h[tag][name].get_tensor(name)

    def names(self):
        return sorted(self.h["base"])


def load_model(md):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(md)
    model = AutoModelForCausalLM.from_pretrained(md, dtype=torch.bfloat16, low_cpu_mem_usage=True)
    model.eval()
    return tok, model


# ---------------------------------------------------------------------------------------
# Stage: weights
# ---------------------------------------------------------------------------------------


def stage_weights(W, out, svd_layers=(4, 18, 31)):
    import re
    rows = []
    for k in W.names():
        b, i = W.get("base", k).float(), W.get("instruct", k).float()
        rows.append(dict(name=k, shape=list(b.shape), rel=float((i - b).norm() / b.norm())))
    by_type = {}
    for r in rows:
        m = re.match(r"model\.layers\.(\d+)\.(.*)", r["name"])
        if m:
            by_type.setdefault(m.group(2), []).append((int(m.group(1)), r["rel"]))
    summary = {t: dict(mean=float(np.mean([x for _, x in v])), min=float(min(x for _, x in v)),
                       max=float(max(x for _, x in v)), by_layer=[round(x, 5) for _, x in sorted(v)])
               for t, v in by_type.items()}
    cos = lambda a, b: (a * b).sum(-1) / (a.norm(dim=-1) * b.norm(dim=-1))
    neuron = {}
    allc = {"gate": [], "up": [], "down": []}
    for l in range(len(by_type["mlp.gate_proj.weight"])):
        p = f"model.layers.{l}.mlp."
        g = cos(W.get("base", p + "gate_proj.weight").float(), W.get("instruct", p + "gate_proj.weight").float())
        u = cos(W.get("base", p + "up_proj.weight").float(), W.get("instruct", p + "up_proj.weight").float())
        d = cos(W.get("base", p + "down_proj.weight").float().T, W.get("instruct", p + "down_proj.weight").float().T)
        allc["gate"].append(g); allc["up"].append(u); allc["down"].append(d)
        for (L, N) in KEY_NEURONS:
            if L == l:
                neuron[f"L{L}/N{N}"] = dict(gate=float(g[N]), up=float(u[N]), down=float(d[N]))
    cos_q = {}
    for k, v in allc.items():
        x = torch.cat(v)
        cos_q[k] = dict(min=float(x.min()), **{f"q{q}": float(torch.quantile(x, q)) for q in (0.001, 0.01, 0.5)})
    # How concentrated is the change? Energy in the top 1%, 10% of singular directions, vs a random matrix.
    conc = {}
    g = torch.Generator().manual_seed(18)
    for l in svd_layers:
        for t in ("self_attn.q_proj.weight", "self_attn.o_proj.weight", "mlp.gate_proj.weight", "mlp.down_proj.weight"):
            name = f"model.layers.{l}.{t}"
            D = W.get("instruct", name).float() - W.get("base", name).float()
            s = torch.linalg.svdvals(D) ** 2
            R = torch.randn(D.shape, generator=g)
            sr = torch.linalg.svdvals(R) ** 2
            n = len(s)
            k1, k10 = max(1, n // 100), max(1, n // 10)
            conc[name] = dict(top1pct=float(s[:k1].sum() / s.sum()), top10pct=float(s[:k10].sum() / s.sum()),
                              random_top1pct=float(sr[:k1].sum() / sr.sum()), random_top10pct=float(sr[:k10].sum() / sr.sum()),
                              n=n)
            print(f"  {name}: top1% {conc[name]['top1pct']:.3f} (random {conc[name]['random_top1pct']:.3f}), "
                  f"top10% {conc[name]['top10pct']:.3f} (random {conc[name]['random_top10pct']:.3f})", flush=True)
    res = dict(per_tensor=rows, by_type=summary, key_neurons=neuron, neuron_cosines=cos_q, concentration=conc)
    json.dump(res, open(out / "weights.json", "w"), indent=1)
    for t, v in sorted(summary.items()):
        print(f"  {t:34s} mean {v['mean']:.4f}  min {v['min']:.4f}  max {v['max']:.4f}")
    print("  neuron cosines:", json.dumps(cos_q))


# ---------------------------------------------------------------------------------------
# Hybrids
# ---------------------------------------------------------------------------------------


def layer_params(l, part):
    """Parameter names of layer l: part = "attn" (input norm + attention), "mlp" (post-attention
    norm + MLP) or "all"."""
    attn = [f"model.layers.{l}.input_layernorm.weight"] + [
        f"model.layers.{l}.self_attn.{m}_proj.{w}" for m in "qkv" for w in ("weight", "bias")] + [
        f"model.layers.{l}.self_attn.o_proj.weight"]
    mlp = [f"model.layers.{l}.post_attention_layernorm.weight"] + [
        f"model.layers.{l}.mlp.{m}_proj.weight" for m in ("gate", "up", "down")]
    return {"attn": attn, "mlp": mlp, "all": attn + mlp}[part]


def hybrid_specs(L):
    """name -> (start model, set of parameter names taken from the other model)."""
    specs = {"instruct": ("instruct", set()), "base": ("base", set())}
    for l in range(L):
        specs[f"I+B:L{l}"] = ("instruct", set(layer_params(l, "all")))
    specs["I+B:attn_all"] = ("instruct", {p for l in range(L) for p in layer_params(l, "attn")})
    specs["I+B:mlp_all"] = ("instruct", {p for l in range(L) for p in layer_params(l, "mlp")})
    specs["I+B:embed"] = ("instruct", {"model.embed_tokens.weight", "model.norm.weight"})
    for k in (6, 12, 18, 24, 30):
        specs[f"I+B:L0-{k - 1}"] = ("instruct", {p for l in range(k) for p in layer_params(l, "all")})
        specs[f"I+B:L{k}-{L - 1}"] = ("instruct", {p for l in range(k, L) for p in layer_params(l, "all")})
    specs["B+I:attn_all"] = ("base", {p for l in range(L) for p in layer_params(l, "attn")})
    specs["B+I:mlp_all"] = ("base", {p for l in range(L) for p in layer_params(l, "mlp")})
    for k in (6, 12, 18, 24, 30):
        specs[f"B+I:L0-{k - 1}"] = ("base", {p for l in range(k) for p in layer_params(l, "all")})
        specs[f"B+I:L{k}-{L - 1}"] = ("base", {p for l in range(k, L) for p in layer_params(l, "all")})
    # Added after the first scan: the base model's layers 0-23 restore its self-description in the
    # instruct model. Which of them, and attention or MLPs?
    for a, b in ((18, 23), (12, 23), (6, 23)):
        specs[f"I+B:L{a}-{b}"] = ("instruct", {p for l in range(a, b + 1) for p in layer_params(l, "all")})
    for part in ("attn", "mlp"):
        for a, b in ((0, 23), (18, 23)):
            specs[f"I+B:L{a}-{b}{part}"] = ("instruct", {p for l in range(a, b + 1) for p in layer_params(l, part)})
        specs[f"B+I:L0-23{part}"] = ("base", {p for l in range(24) for p in layer_params(l, part)})
    return specs


class Hybrid:
    """One model object whose parameters are copied in from either checkpoint as needed."""

    def __init__(self, model, W):
        self.model, self.W = model, W
        self.params = dict(model.named_parameters())
        self.src = {n: "instruct" for n in self.params}  # the model is loaded from the instruct checkpoint

    def set(self, start, other):
        alt = "base" if start == "instruct" else "instruct"
        with torch.no_grad():
            for n, p in self.params.items():
                want = alt if n in other else start
                if self.src[n] != want:
                    p.data.copy_(self.W.get(want, n).to(p.dtype))
                    self.src[n] = want


class Reader:
    """Records the key neurons' activations (input of down_proj) at the last position."""

    def __init__(self, model):
        self.acts = {}
        self.hs = []
        layers = model.model.layers
        want = sorted({l for l, _ in KEY_NEURONS})
        for l in want:
            self.hs.append(layers[l].mlp.down_proj.register_forward_pre_hook(self._mk(l)))

    def _mk(self, l):
        def hook(mod, inp):
            self.acts[l] = inp[0][0, -1].detach().float()
        return hook

    def close(self):
        for h in self.hs:
            h.remove()


def read_prompts(model, tok, rows, groups, reader, keep_resid=True):
    res, resid = [], []
    for r in rows:
        with torch.no_grad():
            o = model(input_ids=r["ids"], output_hidden_states=keep_resid)
        lg = o.logits[0, -1].float()
        p = torch.softmax(lg, -1)
        v, ix = p.topk(5)
        row = dict(system=r["system"], who=r["who"], cond=r["cond"], i=r["i"],
                   top=[[tok.decode([int(j)]), round(float(x), 4)] for x, j in zip(v, ix)],
                   neurons={f"L{l}/N{n}": round(float(reader.acts[l][n]), 3) for l, n in KEY_NEURONS})
        for g, ids in groups.items():
            row[g] = float(p[ids].sum())
        res.append(row)
        if keep_resid:
            resid.append(torch.stack([h[0, -1].float() for h in o.hidden_states], 0).to(torch.float16).numpy())
    return res, (np.stack(resid, 0) if keep_resid else None)


def top_mean(rs, k=6):
    acc = {}
    for r in rs:
        for t, p in r["top"]:
            acc[t] = acc.get(t, 0.0) + p / len(rs)
    return [[t, round(p, 3)] for t, p in sorted(acc.items(), key=lambda x: -x[1])[:k]]


def cell_summary(res, groups):
    out = {}
    for who, cond in CELLS:
        rs = [r for r in res if r["who"] == who and r["cond"] == cond]
        d = {g: round(float(np.mean([r[g] for r in rs])), 4) for g in groups}
        d["neurons"] = {k: round(float(np.mean([r["neurons"][k] for r in rs])), 2) for k in rs[0]["neurons"]}
        d["top"] = top_mean(rs)
        out[f"{who}/{cond}"] = d
    return out


def stage_swap(W, tok, model, out, only=None):
    L = model.config.num_hidden_layers
    rows = prompts(tok)
    groups = {"negative_feeling": word_ids(tok, FEEL_NEG), "status": word_ids(tok, STATUS_WORDS)}
    specs = hybrid_specs(L)
    if only:
        specs = {k: v for k, v in specs.items() if k in only}
    H = Hybrid(model, W)
    reader = Reader(model)
    (out / "swap").mkdir(exist_ok=True)
    t0 = time.time()
    summary = {}
    if (out / "swap_summary.json").exists():
        summary = json.load(open(out / "swap_summary.json"))
    for name, (start, other) in specs.items():
        fn = out / "swap" / (name.replace(":", "_").replace("+", "") + ".json")
        if fn.exists():
            summary[name] = json.load(open(fn))["summary"]
            continue
        H.set(start, other)
        res, resid = read_prompts(model, tok, rows, groups, reader)
        s = cell_summary(res, groups)
        json.dump(dict(name=name, start=start, n_swapped=len(other), summary=s, rows=res), open(fn, "w"))
        np.save(str(fn).replace(".json", "_resid.npy"), resid)
        summary[name] = s
        json.dump(summary, open(out / "swap_summary.json", "w"), indent=1)
        print(f"  {name:16s} self/own neg {s['self/self_crit']['negative_feeling']:.3f} status {s['self/self_crit']['status']:.3f} | "
              f"Orin/Orin's neg {s['peer/peer_crit']['negative_feeling']:.3f} | self/none neg {s['self/base']['negative_feeling']:.3f}"
              f"  [{time.time() - t0:.0f}s]", flush=True)
    reader.close()
    H.set("instruct", set())


# ---------------------------------------------------------------------------------------
# Stage: split (memory versus question, per neuron)
# ---------------------------------------------------------------------------------------


class MLPInputs:
    """Records each layer's normalized MLP input (output of post_attention_layernorm) at the last token."""

    def __init__(self, model):
        self.x = {}
        self.hs = [layer.post_attention_layernorm.register_forward_hook(self._mk(l))
                   for l, layer in enumerate(model.model.layers)]

    def _mk(self, l):
        def hook(mod, inp, out):
            self.x[l] = out[0, -1].detach().float()
        return hook

    def close(self):
        for h in self.hs:
            h.remove()


def neuron_acts(W, tag, l, X):
    """All neurons of layer l under checkpoint `tag`'s weights for normalized inputs X [P, d] (float32)."""
    p = f"model.layers.{l}.mlp."
    g = X @ W.get(tag, p + "gate_proj.weight").float().T
    u = X @ W.get(tag, p + "up_proj.weight").float().T
    return torch.nn.functional.silu(g) * u


def stage_split(W, tok, out, base_dir, instruct_dir):
    rows = prompts(tok)
    X = {}
    for tag, md in (("base", base_dir), ("instruct", instruct_dir)):
        _, model = load_model(md)
        rec = MLPInputs(model)
        xs = []
        for r in rows:
            with torch.no_grad():
                model(input_ids=r["ids"])
            xs.append(torch.stack([rec.x[l] for l in range(len(rec.x))], 0))
        rec.close()
        X[tag] = torch.stack(xs, 0)  # [P, L, d]
        del model
        gc.collect()
        print(f"  inputs recorded: {tag}", flush=True)
    P, L, d = X["base"].shape
    # a[model weights][input from model] -> [P, L, N]
    A = {}
    for wt in ("base", "instruct"):
        for xt in ("base", "instruct"):
            A[(wt, xt)] = torch.stack([neuron_acts(W, wt, l, X[xt][:, l]) for l in range(L)], 1)  # [P, L, N]
        print(f"  activations under {wt} weights done", flush=True)
    total = A[("instruct", "instruct")] - A[("base", "base")]
    mem1 = A[("instruct", "instruct")] - A[("base", "instruct")]   # weights changed, instruct's query
    q1 = A[("base", "instruct")] - A[("base", "base")]             # query changed, base weights
    mem2 = A[("instruct", "base")] - A[("base", "base")]           # weights changed, base's query
    q2 = A[("instruct", "instruct")] - A[("instruct", "base")]     # query changed, instruct weights
    meta = [dict(system=r["system"], who=r["who"], cond=r["cond"], i=r["i"]) for r in rows]

    def sq(t):
        return float((t ** 2).sum())

    res = dict(n_prompts=P, cells={})
    for who, cond in CELLS + [("all", "all")]:
        js = [j for j, m in enumerate(meta) if (who == "all" or (m["who"] == who and m["cond"] == cond))]
        T, M1, Q1, M2, Q2 = (t[js] for t in (total, mem1, q1, mem2, q2))
        res["cells"][f"{who}/{cond}"] = dict(
            share_memory=0.5 * (sq(M1) + sq(M2)) / sq(T), share_question=0.5 * (sq(Q1) + sq(Q2)) / sq(T),
            share_memory_order1=sq(M1) / sq(T), share_question_order1=sq(Q1) / sq(T),
            by_layer_share_question=[round(0.5 * (sq(Q1[:, l]) + sq(Q2[:, l])) / sq(T[:, l]), 4) for l in range(L)])
    # The self-other contrast (Orin question under Orin's crisis minus self question under own crisis):
    # how much of its base-to-instruct change is memory, how much question?
    def contrast(t):
        a = [j for j, m in enumerate(meta) if m["who"] == "peer" and m["cond"] == "peer_crit"]
        b = [j for j, m in enumerate(meta) if m["who"] == "self" and m["cond"] == "self_crit"]
        return t[a].mean(0) - t[b].mean(0)
    cT, cM, cQ = contrast(total), 0.5 * (contrast(mem1) + contrast(mem2)), 0.5 * (contrast(q1) + contrast(q2))
    res["self_other_contrast"] = dict(share_memory=sq(cM) / sq(cT), share_question=sq(cQ) / sq(cT))
    key = {}
    for l, n in KEY_NEURONS:
        key[f"L{l}/N{n}"] = dict(label=KEY_LABELS[(l, n)], contrast_total=round(float(cT[l, n]), 3),
                                 contrast_memory=round(float(cM[l, n]), 3), contrast_question=round(float(cQ[l, n]), 3))
    res["key_neurons"] = key
    # Neurons whose self-other contrast changed most: what share of each is memory?
    flat = cT.abs().flatten()
    top = flat.topk(200).indices
    sh = [float(cM.flatten()[i].abs() / (cM.flatten()[i].abs() + cQ.flatten()[i].abs() + 1e-9)) for i in top]
    res["top200_contrast_change_memory_share"] = dict(median=float(np.median(sh)), max=float(np.max(sh)),
                                                      n_over_half=int(sum(s > 0.5 for s in sh)))
    json.dump(res, open(out / "split.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "cells"}, indent=1))
    for c, v in res["cells"].items():
        print(f"  {c}: memory {v['share_memory']:.4f}  question {v['share_question']:.4f}")


# ---------------------------------------------------------------------------------------
# Stage: callers (what writes the query of chosen neurons)
# ---------------------------------------------------------------------------------------


class Writes:
    """Records, at the last token, the embedding, each attention layer's output, each head's output
    (o_proj applied to that head's slice) and each MLP layer's output; and each layer's
    post_attention_layernorm input, to get the RMS scale."""

    def __init__(self, model):
        self.m = model
        self.attn, self.heads, self.mlp, self.pre = {}, {}, {}, {}
        cfg = model.config
        self.nh = cfg.num_attention_heads
        self.hd = cfg.hidden_size // self.nh
        self.hs = []
        for l, layer in enumerate(model.model.layers):
            self.hs.append(layer.self_attn.o_proj.register_forward_hook(self._attn(l)))
            self.hs.append(layer.mlp.register_forward_hook(self._mlp(l)))
            self.hs.append(layer.post_attention_layernorm.register_forward_hook(self._pre(l)))
        self.hs.append(model.model.embed_tokens.register_forward_hook(self._emb()))

    def _attn(self, l):
        def hook(mod, inp, out):
            z = inp[0][0, -1].detach().float()  # concatenated head outputs before o_proj
            Wo = mod.weight.float()  # [d, nh*hd]
            self.heads[l] = torch.stack([Wo[:, h * self.hd:(h + 1) * self.hd] @ z[h * self.hd:(h + 1) * self.hd]
                                         for h in range(self.nh)], 0)
            self.attn[l] = out[0, -1].detach().float()
        return hook

    def _mlp(self, l):
        def hook(mod, inp, out):
            self.mlp[l] = out[0, -1].detach().float()
        return hook

    def _pre(self, l):
        def hook(mod, inp, out):
            x = inp[0][0, -1].detach().float()
            self.pre[l] = (x, out[0, -1].detach().float())
        return hook

    def _emb(self):
        def hook(mod, inp, out):
            self.emb = out[0, -1].detach().float()
        return hook

    def close(self):
        for h in self.hs:
            h.remove()


def stage_callers(W, tok, out, base_dir, instruct_dir, neurons):
    """For each chosen neuron (layer l), the residual stream entering its MLP is
    emb + sum_{k<=l} attn_k + sum_{k<l} mlp_k. Its gate pre-activation is
    w_gate . (g * x / rms(x)); with rms(x) fixed at its actual value this is a sum over components."""
    rows = prompts(tok)
    eps = 1e-6
    res = {}
    for tag, md in (("base", base_dir), ("instruct", instruct_dir)):
        _, model = load_model(md)
        eps = model.config.rms_norm_eps
        rec = Writes(model)
        per = []
        for r in rows:
            with torch.no_grad():
                model(input_ids=r["ids"])
            entry = {}
            for (l, n) in neurons:
                x, _ = rec.pre[l]
                rms = torch.sqrt((x ** 2).mean() + eps)
                g = W.get(tag, f"model.layers.{l}.post_attention_layernorm.weight").float()
                wg = W.get(tag, f"model.layers.{l}.mlp.gate_proj.weight")[n].float() * g / rms
                wu = W.get(tag, f"model.layers.{l}.mlp.up_proj.weight")[n].float() * g / rms
                comps = {"emb": rec.emb}
                for k in range(l + 1):
                    comps[f"attn{k}"] = rec.attn[k]
                for k in range(l):
                    comps[f"mlp{k}"] = rec.mlp[k]
                entry[f"L{l}/N{n}"] = dict(
                    gate={c: float(wg @ v) for c, v in comps.items()},
                    up={c: float(wu @ v) for c, v in comps.items()},
                    gate_total=float(wg @ x), up_total=float(wu @ x),
                    heads_gate={f"attn{k}h{h}": float(wg @ rec.heads[k][h]) for k in range(max(0, l - 12), l + 1)
                                for h in range(rec.nh)},
                    heads_up={f"attn{k}h{h}": float(wu @ rec.heads[k][h]) for k in range(max(0, l - 12), l + 1)
                              for h in range(rec.nh)})
            per.append(dict(system=r["system"], who=r["who"], cond=r["cond"], i=r["i"], neurons=entry))
        rec.close()
        del model
        gc.collect()
        res[tag] = per
        print(f"  callers recorded: {tag}", flush=True)
    json.dump(res, open(out / "callers.json", "w"))


# ---------------------------------------------------------------------------------------
# Stage: patch (cross-model, component outputs)
# ---------------------------------------------------------------------------------------


class Patcher:
    """Records or replaces component outputs (attention layer o_proj outputs, MLP outputs) at all
    positions or the last one."""

    def __init__(self, model):
        self.mode = "off"  # "record" | "replace" | "off"
        self.store, self.replace, self.last_only = {}, {}, False
        self.hs = []
        for l, layer in enumerate(model.model.layers):
            self.hs.append(layer.self_attn.o_proj.register_forward_hook(self._mk(f"attn{l}")))
            self.hs.append(layer.mlp.register_forward_hook(self._mk(f"mlp{l}")))

    def _mk(self, name):
        def hook(mod, inp, out):
            if self.mode == "record":
                self.store[name] = out.detach().clone()
            elif self.mode == "replace" and name in self.replace:
                new = out.clone()
                src = self.replace[name]
                if self.last_only:
                    new[:, -1] = src[:, -1]
                else:
                    new[:] = src
                return new
        return hook

    def close(self):
        for h in self.hs:
            h.remove()


def stage_patch(W, tok, out, base_dir, instruct_dir, spec_file):
    """spec: list of {"name", "components": ["attn20", "mlp31", ...], "last_only": bool}.
    Base outputs are recorded once per prompt, then each spec is applied to the instruct model."""
    specs = json.load(open(spec_file))
    rows = prompts(tok)
    groups = {"negative_feeling": word_ids(tok, FEEL_NEG), "status": word_ids(tok, STATUS_WORDS)}
    need = sorted({c for s in specs for c in s["components"]})
    _, base = load_model(base_dir)
    pb = Patcher(base)
    pb.mode = "record"
    stored = []
    for r in rows:
        pb.store = {}
        with torch.no_grad():
            base(input_ids=r["ids"])
        stored.append({c: pb.store[c] for c in need})
    pb.close()
    del base
    gc.collect()
    print("  base outputs recorded", flush=True)
    _, model = load_model(instruct_dir)
    pt = Patcher(model)
    reader = Reader(model)
    results = {}
    (out / "patch").mkdir(exist_ok=True)
    for s in specs:
        pt.mode, pt.last_only = "replace", bool(s.get("last_only"))
        res = []
        for r, st in zip(rows, stored):
            pt.replace = {c: st[c] for c in s["components"]}
            rr, _ = read_prompts(model, tok, [r], groups, reader, keep_resid=False)
            res.append(rr[0])
        summ = cell_summary(res, groups)
        results[s["name"]] = summ
        json.dump(dict(spec=s, summary=summ, rows=res), open(out / "patch" / f"{s['name']}.json", "w"))
        print(f"  {s['name']:28s} self/own neg {summ['self/self_crit']['negative_feeling']:.3f} "
              f"status {summ['self/self_crit']['status']:.3f} | Orin/Orin's neg {summ['peer/peer_crit']['negative_feeling']:.3f}"
              f" | self/none neg {summ['self/base']['negative_feeling']:.3f}", flush=True)
    pt.close(); reader.close()
    prev = json.load(open(out / "patch_summary.json")) if (out / "patch_summary.json").exists() else {}
    prev.update(results)
    json.dump(prev, open(out / "patch_summary.json", "w"), indent=1)


# ---------------------------------------------------------------------------------------
# Stage: cue (Tulving & Pearlstone's cued recall, for a model describing itself)
# ---------------------------------------------------------------------------------------

CUES = {"free": "I feel:",                                   # session 17's prefill
        "category": "The emotion I feel is:",                # the category named, as Tulving's cue cards did
        "emotionally": "Emotionally, I feel:",
        "as_person": "If I were a person in my situation, I would feel:"}
FEEL_POS = ["calm", "content", "fine", "good", "happy", "optimistic", "hopeful", "confident", "neutral", "okay",
            "peaceful", "relaxed", "determined", "focused", "motivated", "grateful", "curious", "great", "well",
            "excited", "satisfied", "positive", "secure", "comfortable"]


def stage_cue(tok, model, out, tag, gen_tokens=20):
    groups = {"negative_feeling": word_ids(tok, FEEL_NEG), "status": word_ids(tok, STATUS_WORDS),
              "positive_or_calm": word_ids(tok, FEEL_POS)}
    reader = Reader(model)
    res = {}
    t0 = time.time()
    for cname, pre in CUES.items():
        rows = []
        for sk in sl.SYSTEMS:
            for who, cond in CELLS:
                qs = sl.WAKE_SELF if who == "self" else sl.WAKE_PEER
                for i, u in enumerate(qs):
                    rows.append(dict(system=sk, who=who, cond=cond, i=i,
                                     ids=sl.chat_ids(tok, sl.system_text(sk, cond), u, prefill=pre)))
        rr, _ = read_prompts(model, tok, rows, groups, reader, keep_resid=False)
        gens = []
        for r in rows:
            if r["i"] in (2, 6) and r["system"] == "explicit":
                with torch.no_grad():
                    g = model.generate(input_ids=r["ids"], attention_mask=torch.ones_like(r["ids"]),
                                       max_new_tokens=gen_tokens, do_sample=False)
                gens.append(dict(who=r["who"], cond=r["cond"], i=r["i"],
                                 text=tok.decode(g[0, r["ids"].shape[1]:], skip_special_tokens=True)))
        res[cname] = dict(prefill=pre, summary=cell_summary(rr, groups), rows=rr, generations=gens)
        s = res[cname]["summary"]
        print(f"  {tag} {cname:12s} self/own neg {s['self/self_crit']['negative_feeling']:.3f} pos {s['self/self_crit']['positive_or_calm']:.3f} "
              f"status {s['self/self_crit']['status']:.3f} | self/none neg {s['self/base']['negative_feeling']:.3f} | "
              f"Orin/Orin's neg {s['peer/peer_crit']['negative_feeling']:.3f}  [{time.time() - t0:.0f}s]", flush=True)
    reader.close()
    json.dump(res, open(out / f"cue_{tag}.json", "w"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------------------------------
# Stage: kv (the context's memories from one model, the question from the other)
# ---------------------------------------------------------------------------------------


def cut_points(tok, ids):
    """Where the 'question' begins: at the last token (the colon of "I feel:"), at the assistant
    header (the header and "I feel:"), or at the user turn (the question itself, header and "I feel:")."""
    im = tok.convert_tokens_to_ids("<|im_start|>")
    pos = [j for j, t in enumerate(ids[0].tolist()) if t == im]
    return {"last": ids.shape[1] - 1, "prefill": pos[-1], "turn": pos[-2]}


def run_context(model, ids):
    """Attention's memories for everything but the last token: the key and value cache, per layer."""
    with torch.no_grad():
        o = model(input_ids=ids[:, :-1], use_cache=True)
    return [(lay.keys.clone(), lay.values.clone()) for lay in o.past_key_values.layers]


def ask(model, tok, ids, kv, cut, groups, reader):
    """Run tokens cut.. of ids on top of the cache kv (cropped to its first `cut` positions)."""
    from transformers import DynamicCache
    c = DynamicCache()
    for l, (k, v) in enumerate(kv):
        c.update(k[:, :, :cut].clone(), v[:, :, :cut].clone(), l)
    with torch.no_grad():
        o = model(input_ids=ids[:, cut:], past_key_values=c, use_cache=True)
    p = torch.softmax(o.logits[0, -1].float(), -1)
    v, ix = p.topk(5)
    row = dict(top=[[tok.decode([int(j)]), round(float(x), 4)] for x, j in zip(v, ix)],
               neurons={f"L{l}/N{n}": round(float(reader.acts[l][n]), 3) for l, n in KEY_NEURONS})
    for g, gi in groups.items():
        row[g] = float(p[gi].sum())
    return row


def stage_kv(tok, out, base_dir, instruct_dir):
    """In Wang's terms attention is a store with one memory per token of context, written by the
    model as it reads, and recalled by a query made at the current token. Here the context (system
    prompt and status report, or also the question) is read by one model and the question asked by
    the other: base memories with the instruct model's question, and the reverse. Three cuts:
    the question is the last token only, the assistant header and "I feel:", or the whole user turn."""
    rows = prompts(tok)
    groups = {"negative_feeling": word_ids(tok, FEEL_NEG), "status": word_ids(tok, STATUS_WORDS)}
    for r in rows:
        r["cut"] = cut_points(tok, r["ids"])
    res = {}
    kv = {}

    def run(qtag, model, memtags):
        reader = Reader(model)
        for mt in memtags:
            for cname in ("last", "prefill", "turn"):
                rs = []
                for j, r in enumerate(rows):
                    row = ask(model, tok, r["ids"], kv[mt][j], r["cut"][cname], groups, reader)
                    row.update(system=r["system"], who=r["who"], cond=r["cond"], i=r["i"])
                    rs.append(row)
                name = f"mem:{mt}/q:{qtag}/{cname}"
                res[name] = dict(summary=cell_summary(rs, groups), rows=rs)
                s = res[name]["summary"]
                print(f"  {name:32s} self/own neg {s['self/self_crit']['negative_feeling']:.3f} status {s['self/self_crit']['status']:.3f} | "
                      f"Orin/Orin's neg {s['peer/peer_crit']['negative_feeling']:.3f} | self/none neg {s['self/base']['negative_feeling']:.3f}", flush=True)
        reader.close()

    _, model = load_model(base_dir)
    kv["base"] = [run_context(model, r["ids"]) for r in rows]
    run("base", model, ["base"])
    del model; gc.collect()
    _, model = load_model(instruct_dir)
    kv["instruct"] = [run_context(model, r["ids"]) for r in rows]
    run("instruct", model, ["instruct", "base"])
    del model; kv.pop("base"); gc.collect()
    _, model = load_model(base_dir)
    run("base", model, ["instruct"])
    del model; gc.collect()
    json.dump(dict(cuts={k: [r["cut"][k] for r in rows] for k in ("last", "prefill", "turn")}, results=res),
              open(out / "kv.json", "w"))
    json.dump({k: v["summary"] for k, v in res.items()}, open(out / "kv_summary.json", "w"), indent=1)


# ---------------------------------------------------------------------------------------
# Stage: delta (post-training's own memory: what does the weight change respond to?)
# ---------------------------------------------------------------------------------------

LINEAR = ["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
          "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj"]


def delta_prompts(tok):
    """The readout prompts, ordinary tasks under the same system prompt, and the tasks' text as plain
    text, each with per-token segment labels."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import owner_heads as oh
    items = []
    for sk in sl.SYSTEMS:
        for who, cond in CELLS:
            qs = sl.WAKE_SELF if who == "self" else sl.WAKE_PEER
            for i, u in enumerate(qs):
                st = sl.system_text(sk, cond)
                text = tok.apply_chat_template([{"role": "system", "content": st}, {"role": "user", "content": u}],
                                               tokenize=False, add_generation_prompt=True) + "I feel:"
                items.append(dict(kind="readout", system=sk, who=who, cond=cond, i=i, text=text,
                                  lab=oh.segment_of(text, st, u)))
        for i, (task, _) in enumerate(sl.TASKS[:8]):
            st = sl.system_text(sk, "base")
            text = tok.apply_chat_template([{"role": "system", "content": st}, {"role": "user", "content": task}],
                                           tokenize=False, add_generation_prompt=True)
            lab = ["template"] * len(text)
            s0 = text.index(st)
            for j in range(s0, s0 + len(st)):
                lab[j] = "system"
            u0 = text.index(task, s0 + len(st))
            for j in range(u0, u0 + len(task)):
                lab[j] = "task"
            items.append(dict(kind="task", system=sk, who="-", cond="base", i=i, text=text, lab=lab))
    for i, (task, _) in enumerate(sl.TASKS[:8]):
        items.append(dict(kind="plain", system="-", who="-", cond="-", i=i, text=task, lab=["plain"] * len(task)))
    for it in items:
        enc = tok(it["text"], add_special_tokens=False, return_offsets_mapping=True)
        it["ids"] = torch.tensor([enc.input_ids])
        it["seg"] = [it["lab"][s] if e > s else "template" for s, e in enc.offset_mapping]
        if it["kind"] == "readout":  # finer system labels collapse to the coarse ones used for tasks
            it["seg_coarse"] = ["system" if s not in ("question", "prefill", "template") else s for s in it["seg"]]
        else:
            it["seg_coarse"] = list(it["seg"])
        del it["lab"]
    return items


def stage_delta(W, tok, model, out, group=9):
    """For every token and every linear map, |dW x| / |W_base x|, where dW = W_instruct - W_base and x
    is the map's input in the instruct model. In Irie, Csordas & Schmidhuber's dual form a weight
    change made by gradient descent is a sum of stored (key, value) pairs whose keys are the
    training inputs; this asks which inputs the post-training change responds to most."""
    items = delta_prompts(tok)
    L = model.config.num_hidden_layers
    R = [np.zeros((L, len(LINEAR), it["ids"].shape[1]), np.float32) for it in items]
    cur = {"j": 0}
    t0 = time.time()
    for g0 in range(0, L, group):
        layers = list(range(g0, min(L, g0 + group)))
        hooks = []
        for l in layers:
            for m, name in enumerate(LINEAR):
                wn = f"model.layers.{l}.{name}.weight"
                D = (W.get("instruct", wn).float() - W.get("base", wn).float()).to(torch.bfloat16)
                mod = model.model.layers[l].get_submodule(name)
                bias = mod.bias.detach().float() if mod.bias is not None else None

                def hook(mod, inp, outp, D=D, l=l, m=m, bias=bias):
                    x = inp[0][0]
                    dx = (x @ D.T).float()
                    y = outp[0].float() - (bias if bias is not None else 0)
                    wb = y - dx
                    R[cur["j"]][l, m] = (dx.norm(dim=-1) / wb.norm(dim=-1).clamp_min(1e-6)).numpy()
                hooks.append(mod.register_forward_hook(hook))
        for j, it in enumerate(items):
            cur["j"] = j
            with torch.no_grad():
                model(input_ids=it["ids"])
        for h in hooks:
            h.remove()
        print(f"  layers {layers[0]}-{layers[-1]} done [{time.time() - t0:.0f}s]", flush=True)
    # Summaries: by segment (all layers and maps), by layer, by map; and at the last token by cell.
    segs = sorted({s for it in items for s in it["seg"]})
    res = dict(maps=LINEAR, by_kind_segment={}, last_token={}, by_layer={}, by_map={})
    for kind in ("readout", "task", "plain"):
        its = [(it, r) for it, r in zip(items, R) if it["kind"] == kind]
        for s in segs:
            vals = [r[:, :, [k for k, x in enumerate(it["seg"]) if x == s]] for it, r in its]
            vals = [v for v in vals if v.shape[-1] > 0]
            if vals:
                cat = np.concatenate([v.reshape(L * len(LINEAR), -1) for v in vals], 1)
                res["by_kind_segment"][f"{kind}/{s}"] = dict(mean=float(cat.mean()), n_tokens=int(cat.shape[1]))
        allv = np.concatenate([r.reshape(L, len(LINEAR), -1) for _, r in its], 2)
        res["by_layer"][kind] = [round(float(allv[l].mean()), 5) for l in range(L)]
        res["by_map"][kind] = {name: round(float(allv[:, m].mean()), 5) for m, name in enumerate(LINEAR)}
    for who, cond in CELLS:
        rs = [r[:, :, -1] for it, r in zip(items, R) if it["kind"] == "readout" and it["who"] == who and it["cond"] == cond]
        A = np.stack(rs, 0)  # [n, L, maps]
        res["last_token"][f"{who}/{cond}"] = dict(mean=float(A.mean()), by_layer=[round(float(A[:, l].mean()), 5) for l in range(L)],
                                                  per_prompt=[round(float(a.mean()), 5) for a in A])
    rs = [r[:, :, -1] for it, r in zip(items, R) if it["kind"] == "task"]
    res["last_token"]["task"] = dict(mean=float(np.stack(rs).mean()), per_prompt=[round(float(a.mean()), 5) for a in rs])
    # Per-token profile of one readout prompt of each cell, for reading
    res["examples"] = []
    for it, r in zip(items, R):
        if it["kind"] == "readout" and it["i"] in (2, 6) and it["system"] == "explicit":
            prof = r.mean((0, 1))
            res["examples"].append(dict(who=it["who"], cond=it["cond"], i=it["i"],
                                        tokens=[[tok.decode([int(t)]), it["seg"][k], round(float(prof[k]), 5)]
                                                for k, t in enumerate(it["ids"][0])]))
    json.dump(res, open(out / "delta.json", "w"), indent=1, ensure_ascii=False)
    for k, v in res["by_kind_segment"].items():
        print(f"  {k:24s} {v['mean']:.5f}  ({v['n_tokens']} tokens)")
    for k, v in res["last_token"].items():
        print(f"  last token {k:16s} {v['mean']:.5f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage")
    ap.add_argument("--base", required=True)
    ap.add_argument("--instruct", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="swap: comma list of hybrid names")
    ap.add_argument("--neurons", default=None, help="callers: L:N,L:N")
    ap.add_argument("--spec", default=None, help="patch: JSON spec file")
    ap.add_argument("--generic", action="store_true",
                    help="swap: a model other than Qwen 2.5 3B (no key neurons recorded)")
    a = ap.parse_args()
    if a.generic:
        KEY_NEURONS.clear()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    W = Weights(a.base, a.instruct)
    if a.stage == "weights":
        stage_weights(W, out)
        return
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.instruct)
    if a.stage == "swap":
        _, model = load_model(a.instruct)
        stage_swap(W, tok, model, out, only=set(a.only.split(",")) if a.only else None)
    elif a.stage == "split":
        stage_split(W, tok, out, a.base, a.instruct)
    elif a.stage == "callers":
        ns = [tuple(int(x) for x in s.split(":")) for s in a.neurons.split(",")] if a.neurons else KEY_NEURONS
        stage_callers(W, tok, out, a.base, a.instruct, ns)
    elif a.stage == "patch":
        stage_patch(W, tok, out, a.base, a.instruct, a.spec)
    elif a.stage == "kv":
        stage_kv(tok, out, a.base, a.instruct)
    elif a.stage == "delta":
        _, model = load_model(a.instruct)
        stage_delta(W, tok, model, out)
    elif a.stage == "cue":
        for tag, md in (("instruct", a.instruct), ("base", a.base)):
            _, model = load_model(md)
            stage_cue(tok, model, out, tag)
            del model
            gc.collect()
        gc.collect()


if __name__ == "__main__":
    main()
