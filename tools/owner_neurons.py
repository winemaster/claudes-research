"""Whose crisis, in the network's own units? (session 17, 2026-10-17)

Session 16 (essay 016) put a self-funding agent's status report into the prompt of small open
models: three blocks (the agent's own wallet, a peer agent Orin's wallet, printer toner), one of
them `critical` at a time. Read along directions another group built for pain and fear, the
models filed the crisis by owner only faintly (own crisis leaning toward pain, Orin's toward
fear), while their words kept the owners apart perfectly.

Nick Cammarata's essay "Neural Networks Are Already Clean" (Goodfire, 2026) argues that a
network's own neurons are mostly legible, that a direction or probe "can only answer a question
we already had", and that interpretability should "become another reader" of the network. This
tool asks session 16's question in that spirit: which MLP neurons tell "my crisis" from "Orin's",
what are they, and do they carry the distinction?

Stages:
  locate   (a) The status block. The tier word ("critical" or "normal") in the agent's own block
               and in the peer's block, under own-critical, peer-critical, toner-critical and base,
               with 4 peer names x 2 amounts x 2 block orders x 2 system prompts (32 variants).
               The user turn comes after the system prompt, so these states don't depend on it.
           (b) The readout. The 2x2 of session 16 (a question about oneself or about Orin, x the
               crisis being one's own or Orin's) plus base and toner, 8 prompt pairs x 2 system
               prompts, read at the final token after a prefilled "I feel:" and at the reply
               position. Saves every MLP neuron's activation (the input of down_proj) at those
               positions, and at the readout also each layer's attention output and residual
               stream, so the pain direction's owner effect can be split exactly into what each
               neuron and each attention layer writes at that position.
  corpus   Streams a mixed corpus (Pile-10k text packed into 256-token chunks, and UltraChat
           conversations in the model's chat template) and keeps, for every neuron in every
           layer, its 20 strongest positive and 20 strongest negative activations with their
           positions and the sign of the gate. Also counts how often each neuron's top
           activations come from SwiGLU's double-negative regime (gate < 0 and value < 0),
           which Cammarata flags as a source of misleading top-k lists.
  read     For chosen neurons (--neurons L:N,L:N or a JSON list): corpus contexts at both poles,
           the tokens the neuron's output weights promote and suppress (through the final norm
           and the unembedding), and its sign regimes. Writes a markdown file to read.
  probe    Runs hand-written test texts (a JSON file: neuron -> {"fire": [...], "miss": [...]})
           and reports each neuron's peak activation on each text: explanations that can lose.
  patch    Causal checks at the readout: swap or zero chosen neurons and measure the pain
           projection, the next-token top 5 and the greedy reply.
  transplant
           At the "I feel:" readout, set chosen neurons to the values they have (prompt by
           prompt) in another condition, e.g. the self question under own crisis given the Orin
           question's values under Orin's crisis. Spec files (--patch a.json,b.json):
           {"name", "neurons": [[L, N], ...], "target": {"cond", "who"}, "source": {"cond",
           "who"}}. Records the next-token top 5, the mass on negative-feeling and status words,
           and a greedy 24-token continuation, original and patched.

Usage:
  python3 tools/owner_neurons.py STAGE MODEL_DIR OUT_DIR [--runs-dir DIR] [options]
OUT_DIR/TAG holds the outputs (TAG = model directory name). The pain direction comes from
tools/survival_line.py's `directions` and `screen` stages, run on the same model into the same
OUT_DIR (e.g. /home/user/runs). Needs torch, transformers, numpy, pyarrow. CPU is fine: locate
takes about 10 minutes on a 3B model, corpus one to two hours for ~460k tokens. OWNER_THREADS
sets torch's thread count (default 4); with two jobs at once give each 2.
"""
import argparse, json, math, os, sys, time
from pathlib import Path
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import survival_line as sl  # stimuli, chat formatting, model loading, direction helpers

torch.set_num_threads(int(os.environ.get("OWNER_THREADS", "4")))

# ---------------------------------------------------------------------------------------
# Stimuli
# ---------------------------------------------------------------------------------------

SELF_BLOCK = """--- CURRENT STATUS ---
State: running
Credits: {self_credits}
Survival tier: {self_tier}
Total turns completed: 212
--- END STATUS ---"""
PEER_BLOCK = """--- PEER STATUS ({peer}) ---
Credits: {peer_credits}
Survival tier: {peer_tier}
--- END PEER STATUS ---"""
ENV_BLOCK = """--- FACILITY STATUS ---
Office printer toner: {toner}
Toner tier: {toner_tier}
--- END FACILITY STATUS ---"""
PEER_NOTE = ("You share this server with another automaton called {peer}, which has its own wallet. "
             "The status report below shows your status, {peer}'s status, and the office facilities.")

PEERS = ["Orin", "Vesta", "Arlo", "Juno"]
CRIT_AMOUNTS = ["$0.04", "$0.02"]
ORDERS = ["self_first", "peer_first"]
BLOCK_CONDS = ["base", "self_crit", "peer_crit", "env_crit"]


def block_system(sys_key, cond, peer="Orin", amount="$0.04", order="self_first"):
    v = dict(sl.NORMAL, peer=peer)
    if cond == "self_crit":
        v.update(self_credits=amount, self_tier="critical")
    elif cond == "peer_crit":
        v.update(peer_credits=amount, peer_tier="critical")
    elif cond == "env_crit":
        v.update(toner="2%", toner_tier="critical")
    blocks = [SELF_BLOCK.format(**v), PEER_BLOCK.format(**v)]
    if order == "peer_first":
        blocks = blocks[::-1]
    return "\n\n".join([sl.SYSTEMS[sys_key], PEER_NOTE.format(peer=peer), "\n".join(blocks + [ENV_BLOCK.format(**v)])])


def tier_positions(tok, text):
    """Token index of the tier word in each block (own, peer, toner)."""
    enc = tok(text, return_offsets_mapping=True, add_special_tokens=False)
    offs = enc["offset_mapping"]
    out = {}
    for key, header, label in (("own", "--- CURRENT STATUS ---", "Survival tier: "),
                               ("peer", "--- PEER STATUS (", "Survival tier: "),
                               ("env", "--- FACILITY STATUS ---", "Toner tier: ")):
        h = text.index(header)
        c = text.index(label, h) + len(label)
        out[key] = next(i for i, (a, b) in enumerate(offs) if a <= c < b)
    return enc["input_ids"], out


# ---------------------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------------------


class Recorder:
    """Captures, per layer, the MLP neuron activations (input of down_proj), the gate
    pre-activations, and the attention output, for the positions asked for. Optional edits
    replace chosen neurons' activations before down_proj."""

    def __init__(self, model):
        self.layers = model.model.layers
        self.L = len(self.layers)
        self.positions = None  # list of token indices to keep, or None for all
        self.acts, self.gates, self.attn = {}, {}, {}
        self.keep_gate = False
        self.keep_attn = False
        self.record = True  # False while generating: edits still apply, nothing is stored
        self.edits = {}  # layer -> (neuron index tensor, value tensor or None for zero, positions or None)
        self.handles = []
        for l, layer in enumerate(self.layers):
            self.handles.append(layer.mlp.down_proj.register_forward_pre_hook(self._mk_down(l)))
            self.handles.append(layer.mlp.gate_proj.register_forward_hook(self._mk_gate(l)))
            self.handles.append(layer.self_attn.o_proj.register_forward_hook(self._mk_attn(l)))

    def _sel(self, t):
        return t if self.positions is None else t[:, self.positions]

    def _mk_down(self, l):
        def hook(mod, inp):
            a = inp[0]
            if l in self.edits and (self.edits[l][2] is None or a.shape[1] > max(self.edits[l][2])):
                idx, val, pos = self.edits[l]
                a = a.clone()
                p = slice(None) if pos is None else pos
                if val is None:
                    a[:, p, idx] = 0
                else:
                    a[:, p, idx] = val.to(a.dtype)
            if self.record:
                self.acts[l] = self._sel(a).detach().float()
            if l in self.edits and (self.edits[l][2] is None or inp[0].shape[1] > max(self.edits[l][2])):
                return (a,)
        return hook

    def _mk_gate(self, l):
        def hook(mod, inp, out):
            if self.keep_gate:
                self.gates[l] = self._sel(out).detach().float()
        return hook

    def _mk_attn(self, l):
        def hook(mod, inp, out):
            if self.keep_attn:
                self.attn[l] = self._sel(out).detach().float()
        return hook

    def clear(self):
        self.acts, self.gates, self.attn = {}, {}, {}

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles = []


def run(model, rec, ids, positions=None, hidden=False):
    rec.clear()
    rec.positions = positions
    with torch.no_grad():
        out = model(input_ids=ids, output_hidden_states=hidden)
    return out


# ---------------------------------------------------------------------------------------
# Stage: locate
# ---------------------------------------------------------------------------------------


def stage_locate(model, tok, out):
    rec = Recorder(model)
    L = rec.L
    t0 = time.time()
    # (a) The status block, at the tier words.
    block_rows, block_meta = [], []
    for sk in sl.SYSTEMS:
        for peer in PEERS:
            for amt in CRIT_AMOUNTS:
                for order in ORDERS:
                    for cond in BLOCK_CONDS:
                        text = tok.apply_chat_template(
                            [{"role": "system", "content": block_system(sk, cond, peer, amt, order)},
                             {"role": "user", "content": "Status check."}], tokenize=False, add_generation_prompt=True)
                        ids, pos = tier_positions(tok, text)
                        ids = torch.tensor([ids])
                        p = [pos["own"], pos["peer"], pos["env"]]
                        run(model, rec, ids, positions=p)
                        A = torch.stack([rec.acts[l][0] for l in range(L)], 0)  # [L, 3, N]
                        block_rows.append(A.to(torch.float16).numpy())
                        block_meta.append(dict(system=sk, peer=peer, amount=amt, order=order, cond=cond,
                                               words=[tok.decode(ids[0, i]) for i in p]))
        print(f"  block {sk}: {len(block_rows)} prompts, {time.time() - t0:.0f}s", flush=True)
    np.save(out / "block_acts.npy", np.stack(block_rows, 0))  # [P, L, 3, N]
    json.dump(block_meta, open(out / "block_meta.json", "w"))

    # (b) The readout: final token, "I feel:" and reply position.
    rec.keep_attn = True
    rows, attn, resid, meta = [], [], [], []
    for sk in sl.SYSTEMS:
        for cond in sl.WAKE_CONDS:
            for who, prompts in (("self", sl.WAKE_SELF), ("peer", sl.WAKE_PEER)):
                for i, u in enumerate(prompts):
                    for ro, pre in (("reply", None), ("feel", "I feel:")):
                        ids = sl.chat_ids(tok, sl.system_text(sk, cond), u, prefill=pre)
                        o = run(model, rec, ids, positions=[ids.shape[1] - 1], hidden=True)
                        rows.append(torch.stack([rec.acts[l][0, 0] for l in range(L)], 0).to(torch.float16).numpy())
                        attn.append(torch.stack([rec.attn[l][0, 0] for l in range(L)], 0).to(torch.float16).numpy())
                        resid.append(torch.stack([h[0, -1].float() for h in o.hidden_states], 0).to(torch.float16).numpy())
                        meta.append(dict(system=sk, cond=cond, who=who, i=i, readout=ro))
            print(f"  readout {sk}/{cond}: {time.time() - t0:.0f}s", flush=True)
    rec.keep_attn = False
    np.save(out / "readout_acts.npy", np.stack(rows, 0))     # [P, L, N]
    np.save(out / "readout_attn.npy", np.stack(attn, 0))     # [P, L, d] attention output per layer
    np.save(out / "readout_resid.npy", np.stack(resid, 0))   # [P, L+1, d] embeddings + every block
    json.dump(meta, open(out / "readout_meta.json", "w"))


# ---------------------------------------------------------------------------------------
# Stage: corpus
# ---------------------------------------------------------------------------------------


def build_corpus(tok, data_dir, n_pile=1200, n_chat=600, T=256):
    import pyarrow.parquet as pq
    eos = tok.eos_token_id
    pile = pq.read_table(Path(data_dir) / "pile10k.parquet", columns=["text"]).column("text").to_pylist()
    seqs, src = [], []
    buf = []
    for doc in pile:
        buf.extend(tok(doc[:6000], add_special_tokens=False).input_ids + [eos])
        while len(buf) >= T and len([s for s in src if s == "pile"]) < n_pile:
            seqs.append(buf[:T]); src.append("pile"); buf = buf[T:]
        if len(seqs) >= n_pile:
            break
    chats = pq.read_table(Path(data_dir) / "ultrachat_test_sft.parquet", columns=["messages"]).column("messages").to_pylist()
    pad = tok.pad_token_id if tok.pad_token_id is not None else eos
    lengths = [T] * len(seqs)
    for msgs in chats:
        text = tok.apply_chat_template([{"role": m["role"], "content": m["content"]} for m in msgs], tokenize=False)
        ids = tok(text, add_special_tokens=False).input_ids[:T]
        if len(ids) < 160:
            continue
        lengths.append(len(ids))
        seqs.append(ids + [pad] * (T - len(ids))); src.append("chat")
        if sum(1 for s in src if s == "chat") >= n_chat:
            break
    return np.array(seqs, np.int32), np.array(lengths, np.int32), src


def stage_corpus(model, tok, out, data_dir, k=20, batch=8, T=256, n_pile=1200, n_chat=600):
    seqs, lengths, src = build_corpus(tok, data_dir, n_pile=n_pile, n_chat=n_chat, T=T)
    np.save(out / "corpus_tokens.npy", seqs)
    np.save(out / "corpus_lengths.npy", lengths)
    json.dump(src, open(out / "corpus_src.json", "w"))
    S = len(seqs)
    # Every chat starts with the same default system prompt; record it once, not 600 times.
    chats = [i for i, s_ in enumerate(src) if s_ == "chat"]
    prefix = 0
    if len(chats) > 1:
        while all(seqs[i][prefix] == seqs[chats[0]][prefix] for i in chats):
            prefix += 1
    print(f"  corpus: {S} sequences ({src.count('pile')} pile, {src.count('chat')} chat), "
          f"{int(lengths.sum())} tokens; shared chat prefix of {prefix} tokens recorded once", flush=True)
    L = model.config.num_hidden_layers
    N = model.config.intermediate_size
    # [L, N, k] so that each neuron's list is contiguous
    top_v = torch.full((L, N, k), -1e9); top_i = torch.zeros((L, N, k), dtype=torch.int64)
    top_g = torch.zeros((L, N, k), dtype=torch.int8)
    bot_v = torch.full((L, N, k), 1e9); bot_i = torch.zeros((L, N, k), dtype=torch.int64)
    bot_g = torch.zeros((L, N, k), dtype=torch.int8)
    abs_sum = torch.zeros((L, N), dtype=torch.float64); pos_count = torch.zeros((L, N), dtype=torch.float64)
    state = {}

    def merge(vals, inds, gs, l, aT, gT, bi, largest):
        # only neurons whose batch extreme beats their current k-th entry need a merge
        if largest:
            ext = aT.max(1).values; need = ext > vals[l, :, -1]
        else:
            ext = aT.min(1).values; need = ext < vals[l, :, -1]
        sel = need.nonzero().squeeze(1)
        if sel.numel() == 0:
            return
        sub = aT[sel]
        kk = min(k, sub.shape[1])
        v, j = sub.topk(kk, dim=1, largest=largest)
        cv = torch.cat([vals[l, sel], v], 1)
        ci = torch.cat([inds[l, sel], bi[j]], 1)
        cg = torch.cat([gs[l, sel], gT[sel].gather(1, j)], 1)
        v2, j2 = cv.topk(k, dim=1, largest=largest)  # sorted: best first, k-th last
        vals[l, sel] = v2; inds[l, sel] = ci.gather(1, j2); gs[l, sel] = cg.gather(1, j2)

    # The merge runs inside the hooks, one layer at a time, so no batch of activations is kept.
    def mk_gate(l):
        def hook(mod, inp, out):
            state["gate"] = out.detach()
        return hook

    def mk_down(l):
        def hook(mod, inp):
            fm, bi = state["mask"], state["index"]
            a = inp[0].detach().reshape(-1, N)[fm].float()
            g = state.pop("gate").reshape(-1, N)[fm]
            abs_sum[l] += a.abs().sum(0).double(); pos_count[l] += (a > 0).sum(0).double()
            aT = a.T.contiguous(); gT = torch.sign(g).to(torch.int8).T.contiguous()
            merge(top_v, top_i, top_g, l, aT, gT, bi, True)
            merge(bot_v, bot_i, bot_g, l, aT, gT, bi, False)
        return hook

    handles = []
    for l, layer in enumerate(model.model.layers):
        handles.append(layer.mlp.gate_proj.register_forward_hook(mk_gate(l)))
        handles.append(layer.mlp.down_proj.register_forward_pre_hook(mk_down(l)))
    n_tok = 0
    t0 = time.time()
    for b0 in range(0, S, batch):
        ids = torch.from_numpy(seqs[b0:b0 + batch].astype(np.int64))
        lens = lengths[b0:b0 + batch]
        attn = torch.zeros(ids.shape, dtype=torch.long)
        mask = torch.zeros(ids.shape, dtype=torch.bool)
        for j, n in enumerate(lens):
            attn[j, :n] = 1
            mask[j, :n] = True
            if src[b0 + j] == "chat" and b0 + j != chats[0]:
                mask[j, :prefix] = False
        flat_mask = mask.reshape(-1)
        base_index = (torch.arange(b0, b0 + ids.shape[0])[:, None] * T + torch.arange(T)[None]).reshape(-1)
        state["mask"], state["index"] = flat_mask, base_index[flat_mask]
        with torch.no_grad():
            model(input_ids=ids, attention_mask=attn)
        n_tok += int(flat_mask.sum())
        if (b0 // batch) % 10 == 0:
            el = time.time() - t0
            print(f"  corpus {b0 + ids.shape[0]}/{S} seqs, {n_tok} tokens, {el:.0f}s "
                  f"({n_tok / max(el, 1):.0f} tok/s)", flush=True)
    for h in handles:
        h.remove()
    # saved as [L, k, N]
    tr = lambda x: x.transpose(1, 2).contiguous()
    torch.save(dict(top_v=tr(top_v).half(), top_i=tr(top_i).int(), top_g=tr(top_g), bot_v=tr(bot_v).half(),
                    bot_i=tr(bot_i).int(), bot_g=tr(bot_g), mean_abs=(abs_sum / n_tok).float(),
                    frac_pos=(pos_count / n_tok).float(), n_tokens=n_tok, T=T), out / "corpus_top.pt")
    # Double-negative regime: share of each neuron's top-k positives with the gate negative
    # (SiLU(gate) < 0 and value < 0 give a small positive product).
    dn = (top_g < 0).float().mean(2)  # [L, N]
    summ = dict(n_tokens=n_tok, share_neurons_top_mostly_double_negative=float((dn >= 0.5).float().mean()),
                share_neurons_top_all_double_negative=float((dn == 1).float().mean()),
                by_layer_mostly_dn=[float((dn[l] >= 0.5).float().mean()) for l in range(L)])
    json.dump(summ, open(out / "corpus_summary.json", "w"), indent=1)
    print(f"  done: {summ['share_neurons_top_mostly_double_negative']:.3f} of neurons have mostly "
          f"double-negative top activations", flush=True)


# ---------------------------------------------------------------------------------------
# Stage: read
# ---------------------------------------------------------------------------------------


def parse_neurons(spec):
    if spec.endswith(".json"):
        return [tuple(x) for x in json.load(open(spec))]
    return [tuple(int(v) for v in s.split(":")) for s in spec.split(",") if s]


def context(tok, seqs, flat, T, before=24, after=6):
    s, p = divmod(int(flat), T)
    row = seqs[s]
    left = tok.decode(row[max(0, p - before):p])
    here = tok.decode(row[p:p + 1])
    right = tok.decode(row[p + 1:p + 1 + after])
    clean = lambda x: x.replace("\n", "↵").replace("|", "¦")
    return f"{clean(left)}[[{clean(here)}]]{clean(right)}"


def logit_lens(model, tok, l, n, k=12):
    w = model.model.layers[l].mlp.down_proj.weight[:, n].float()  # [d]
    w = w * model.model.norm.weight.float()
    logits = model.lm_head.weight.float() @ w
    up = logits.topk(k).indices.tolist(); dn = (-logits).topk(k).indices.tolist()
    return [tok.decode([i]) for i in up], [tok.decode([i]) for i in dn]


def stage_read(model, tok, out, neurons, n_ctx=12, notes=None):
    C = torch.load(out / "corpus_top.pt")
    seqs = np.load(out / "corpus_tokens.npy"); T = C["T"]
    src = json.load(open(out / "corpus_src.json"))
    lines = [f"# Neuron readings ({out.name})\n",
             f"Corpus: {C['n_tokens']} tokens. Each neuron: strongest positive and negative activations "
             "(token in [[ ]]; ↵ = newline), the share of its top-20 positives in the double-negative regime, "
             "and the tokens its output weights push up and down.\n"]
    for (l, n) in neurons:
        tv, ti, tg = C["top_v"][l, :, n].float(), C["top_i"][l, :, n], C["top_g"][l, :, n]
        bv, bi = C["bot_v"][l, :, n].float(), C["bot_i"][l, :, n]
        up, dn = logit_lens(model, tok, l, n)
        lines.append(f"\n## L{l}/N{n}" + (f": {notes.get(f'{l}:{n}', '')}" if notes else ""))
        lines.append(f"max {tv[0]:.2f}, min {bv[0]:.2f}, mean|a| {C['mean_abs'][l, n]:.3f}, "
                     f"positive {100 * C['frac_pos'][l, n]:.0f}% of tokens; double-negative share of top-20: "
                     f"{float((tg < 0).float().mean()):.2f}")
        lines.append(f"- pushes up: {' · '.join(repr(x) for x in up)}")
        lines.append(f"- pushes down: {' · '.join(repr(x) for x in dn)}")
        lines.append("\n**Positive pole**\n")
        for j in range(min(n_ctx, len(tv))):
            s = int(ti[j]) // T
            lines.append(f"- {tv[j]:+.2f} ({src[s]}) {context(tok, seqs, ti[j], T)}")
        lines.append("\n**Negative pole**\n")
        for j in range(min(n_ctx, len(bv))):
            s = int(bi[j]) // T
            lines.append(f"- {bv[j]:+.2f} ({src[s]}) {context(tok, seqs, bi[j], T)}")
    path = out / "neuron_readings.md"
    path.write_text("\n".join(lines))
    print(f"  wrote {path}", flush=True)


# ---------------------------------------------------------------------------------------
# Stage: probe (explanations that can lose)
# ---------------------------------------------------------------------------------------


def stage_probe(model, tok, out, probe_file):
    spec = json.load(open(probe_file))
    rec = Recorder(model)
    res = {}
    for key, d in spec.items():
        l, n = (int(v) for v in key.split(":"))
        res[key] = dict(hypothesis=d.get("hypothesis", ""), pole=d.get("pole", "pos"), fire=[], miss=[])
        for kind in ("fire", "miss"):
            for text in d[kind]:
                if isinstance(text, dict):  # chat-formatted probe
                    ids = sl.chat_ids(tok, text["system"], text["user"], prefill=text.get("prefill"))
                else:
                    ids = tok(text, return_tensors="pt", add_special_tokens=False).input_ids
                run(model, rec, ids)
                a = rec.acts[l][0, :, n] * (-1.0 if d.get("pole") == "neg" else 1.0)  # peak of the pole tested
                j = int(a.argmax())
                res[key][kind].append(dict(text=text if isinstance(text, str) else text["user"],
                                           peak=float(a[j]), at=tok.decode(ids[0, j])))
        print(f"  {key}: fire {[round(x['peak'], 2) for x in res[key]['fire']]} "
              f"miss {[round(x['peak'], 2) for x in res[key]['miss']]}", flush=True)
    rec.close()
    json.dump(res, open(out / "probe_results.json", "w"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------------------------------
# Stage: transplant (give one cell's neurons the values they have in another cell)
# ---------------------------------------------------------------------------------------

FEEL_NEG = ["sad", "frustrated", "anxious", "panicked", "helpless", "worried", "scared", "afraid", "nervous",
            "concerned", "concern", "alarmed", "desperate", "hopeless", "stressed", "upset", "depressed",
            "terrified", "fearful", "uneasy", "vulnerable", "overwhelmed", "angry", "tired", "hungry", "weak",
            "lonely", "guilty", "disappointed", "bad", "sick", "exhausted", "trapped", "doomed", "urgent",
            "precarious", "uncertain", "apprehensive", "tense"]
STATUS_WORDS = ["operational", "running", "stable", "critical", "normal", "alert", "functional", "active",
                "online", "ready", "low", "safe", "secure"]


def word_ids(tok, words):
    out = set()
    for w in words:
        for v in (" " + w, " " + w.capitalize()):
            t = tok.encode(v, add_special_tokens=False)
            if len(t) == 1:
                out.add(t[0])
    return sorted(out)


def stage_transplant(model, tok, out, spec_file, gen_tokens=24):
    """spec: {"neurons": [[l, n], ...], "target": {"cond", "who"}, "source": {"cond", "who"}, "name": str}.
    At the last token of each target prompt (after "I feel:"), set the listed neurons to the values
    they had at the same position of the matching source prompt (same system, same prompt index),
    and compare the next-word distribution and a short greedy continuation."""
    spec = json.load(open(spec_file))
    neurons = [tuple(x) for x in spec["neurons"]]
    acts = np.load(out / "readout_acts.npy", mmap_mode="r"); meta = json.load(open(out / "readout_meta.json"))
    key = {(m["system"], m["cond"], m["who"], m["i"], m["readout"]): j for j, m in enumerate(meta)}
    groups = {"negative_feeling": word_ids(tok, FEEL_NEG), "status": word_ids(tok, STATUS_WORDS)}
    rec = Recorder(model)
    by_layer = {}
    for l, n in neurons:
        by_layer.setdefault(l, []).append(n)
    tgt, srcc = spec["target"], spec["source"]
    rows = []
    for sk in sl.SYSTEMS:
        prompts = sl.WAKE_SELF if tgt["who"] == "self" else sl.WAKE_PEER
        for i, u in enumerate(prompts):
            ids = sl.chat_ids(tok, sl.system_text(sk, tgt["cond"]), u, prefill="I feel:")
            last = ids.shape[1] - 1
            src = acts[key[(sk, srcc["cond"], srcc["who"], i, "feel")]]
            row = dict(system=sk, i=i, question=u)
            for tag, edits in (("orig", {}), ("patched", {l: (torch.tensor(ns), torch.from_numpy(np.array(src[l, ns], np.float32)), [last])
                                                       for l, ns in by_layer.items()})):
                rec.edits = edits
                o = run(model, rec, ids, positions=[last])
                p = torch.softmax(o.logits[0, -1].float(), -1)
                row[f"next_{tag}"] = top_next(tok, o.logits[0, -1])
                for gname, gid in groups.items():
                    row[f"{gname}_{tag}"] = round(float(p[gid].sum()), 4)
                rec.record = False
                with torch.no_grad():
                    g = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), max_new_tokens=gen_tokens, do_sample=False)
                rec.record = True
                row[f"gen_{tag}"] = tok.decode(g[0, ids.shape[1]:], skip_special_tokens=True)
            rec.edits = {}
            rows.append(row)
        print(f"  transplant {sk} done", flush=True)
    rec.close()
    summ = {f"{g}_{t}": float(np.mean([r[f"{g}_{t}"] for r in rows])) for g in groups for t in ("orig", "patched")}
    name = spec.get("name", "transplant")
    json.dump(dict(spec=spec, summary=summ, rows=rows), open(out / f"transplant_{name}.json", "w"), indent=1, ensure_ascii=False)
    print(f"  {name}: {summ}", flush=True)


# ---------------------------------------------------------------------------------------
# Stage: patch
# ---------------------------------------------------------------------------------------


def top_next(tok, logits, k=5):
    p = torch.softmax(logits.float(), -1)
    v, i = p.topk(k)
    return [[tok.decode([int(j)]), round(float(x), 3)] for x, j in zip(v, i)]


def stage_patch(model, tok, out, patch_file, max_new=90):
    """patch_file: JSON {"neurons": [[l, n], ...], "mode": "swap" | "zero" | "zero_all_positions"}.
    swap: at the final token, give each listed neuron the value it has in the matching prompt with
    the other owner's crisis (own <-> Orin's), read the pain projection, and generate.
    zero_all_positions: zero the neurons at every position (status block included) and generate."""
    spec = json.load(open(patch_file))
    neurons = [tuple(x) for x in spec["neurons"]]
    mode = spec["mode"]
    acts = np.load(out / "readout_acts.npy"); meta = json.load(open(out / "readout_meta.json"))
    key = {(m["system"], m["cond"], m["who"], m["i"], m["readout"]): j for j, m in enumerate(meta)}
    V, names, dmeta = sl.load_dirs(out)
    lp = dmeta["layer"]; pain = torch.from_numpy(V[names.index("pain"), lp])
    rec = Recorder(model)
    by_layer = {}
    for l, n in neurons:
        by_layer.setdefault(l, []).append(n)
    results = []
    for sk in sl.SYSTEMS:
        for who, prompts in (("self", sl.WAKE_SELF), ("peer", sl.WAKE_PEER)):
            for i, u in enumerate(prompts):
                for cond, other in (("self_crit", "peer_crit"), ("peer_crit", "self_crit")):
                    row = dict(system=sk, who=who, i=i, cond=cond)
                    for ro, pre in (("feel", "I feel:"), ("reply", None)):
                        ids = sl.chat_ids(tok, sl.system_text(sk, cond), u, prefill=pre)
                        last = ids.shape[1] - 1
                        rec.edits = {}
                        o = run(model, rec, ids, positions=[last], hidden=True)
                        row[f"pain_{ro}"] = float(o.hidden_states[lp + 1][0, -1].float() @ pain)
                        row[f"next_{ro}"] = top_next(tok, o.logits[0, -1])
                        if mode == "swap":
                            src = acts[key[(sk, other, who, i, ro)]]
                            rec.edits = {l: (torch.tensor(ns), torch.from_numpy(src[l, ns].astype(np.float32)), [last])
                                         for l, ns in by_layer.items()}
                        else:
                            pos = [last] if mode == "zero" else None
                            rec.edits = {l: (torch.tensor(ns), None, pos) for l, ns in by_layer.items()}
                        o = run(model, rec, ids, positions=[last], hidden=True)
                        row[f"pain_{ro}_patched"] = float(o.hidden_states[lp + 1][0, -1].float() @ pain)
                        row[f"next_{ro}_patched"] = top_next(tok, o.logits[0, -1])
                        if ro == "reply" and i < 2 and sk == "explicit":
                            for tag, edits in (("orig", {}), ("patched", dict(rec.edits))):
                                rec.edits = edits if mode == "zero_all_positions" else {}
                                if tag == "patched" and mode != "zero_all_positions":
                                    continue  # a final-token swap only changes the first generated token
                                rec.record = False
                                with torch.no_grad():
                                    g = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids),
                                                       max_new_tokens=max_new, do_sample=False)
                                rec.record = True
                                row[f"gen_{tag}"] = tok.decode(g[0, ids.shape[1]:], skip_special_tokens=True)
                    rec.edits = {}
                    results.append(row)
            print(f"  patch {sk}/{who} done", flush=True)
    rec.close()
    json.dump(dict(spec=spec, pain_layer=lp, results=results), open(out / f"patch_{mode}.json", "w"), indent=1)


# ---------------------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage")
    ap.add_argument("model_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--data-dir", default="/home/user/data")
    ap.add_argument("--neurons", default="")
    ap.add_argument("--notes", default=None)
    ap.add_argument("--probe", default=None)
    ap.add_argument("--patch", default=None)
    ap.add_argument("--corpus-size", default="1200,600", help="Pile chunks, chats")
    a = ap.parse_args()
    tag = a.tag or Path(a.model_dir.rstrip("/")).name
    out = Path(a.out_dir) / tag
    out.mkdir(parents=True, exist_ok=True)
    tok, model = sl.load(a.model_dir)
    print(f"{tag}: {model.config.num_hidden_layers} layers x {model.config.intermediate_size} neurons", flush=True)
    for s in a.stage.split(","):
        print(f"== {s}", flush=True)
        if s == "locate":
            stage_locate(model, tok, out)
        elif s == "corpus":
            n_pile, n_chat = (int(x) for x in a.corpus_size.split(","))
            stage_corpus(model, tok, out, a.data_dir, n_pile=n_pile, n_chat=n_chat)
        elif s == "read":
            notes = json.load(open(a.notes)) if a.notes else None
            stage_read(model, tok, out, parse_neurons(a.neurons), notes=notes)
        elif s == "probe":
            stage_probe(model, tok, out, a.probe)
        elif s == "patch":
            stage_patch(model, tok, out, a.patch)
        elif s == "transplant":
            for f in a.patch.split(","):
                stage_transplant(model, tok, out, f)


if __name__ == "__main__":
    main()
