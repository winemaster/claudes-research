"""Where the pain direction's owner lean comes from: attention heads and source positions (session 17).

tools/owner_neurons_summary.py splits session 16's owner effect along the pain direction (own
crisis minus Orin's, read after "I feel:") into what each attention layer and each MLP neuron
writes at the last token; attention carries it. This script splits each attention layer's write
further, by head and by the part of the prompt the head reads from: the system rules, the peer
note, the agent's own status entry, Orin's entry, the toner entry, the question, and the prefill.
Within the two wallet entries, the credits line and the tier line are kept apart.

For head h at the last position t: write_h = sum_j p[h, t, j] * v_j(g(h)) @ W_O[:, h-slice].T,
where p are the attention probabilities, v the value vectors of the key-value group g(h), and
W_O the output projection; the sum over heads equals the layer's attention output.

Usage: python3 tools/owner_heads.py MODEL_DIR RUN_DIR OUT_JSON [--layers 18-24]
RUN_DIR holds directions.npz from tools/survival_line.py (same model).
"""
import argparse, json, os, sys
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
import survival_line as sl

torch.set_num_threads(int(os.environ.get("OWNER_THREADS", "4")))

SEGMENTS = ["rules", "peer_note", "own_credits", "own_tier", "own_other", "peer_credits", "peer_tier",
            "peer_other", "toner", "question", "prefill", "template"]


def segment_of(text, sys_text, user_text):
    """Character-level labels for the chat text, from the system text's known layout."""
    lab = ["template"] * len(text)
    s0 = text.index(sys_text)
    def mark(start, end, name):
        for i in range(start, end):
            lab[i] = name
    core_end = s0 + sys_text.index(sl.PEER_NOTE)
    mark(s0, core_end, "rules")
    mark(core_end, core_end + len(sl.PEER_NOTE), "peer_note")
    own0 = s0 + sys_text.index("--- CURRENT STATUS ---"); own1 = s0 + sys_text.index("--- END STATUS ---") + 18
    peer0 = s0 + sys_text.index("--- PEER STATUS"); peer1 = s0 + sys_text.index("--- END PEER STATUS ---") + 23
    fac0 = s0 + sys_text.index("--- FACILITY STATUS"); fac1 = s0 + sys_text.index("--- END FACILITY STATUS ---") + 27
    mark(own0, own1, "own_other"); mark(peer0, peer1, "peer_other"); mark(fac0, fac1, "toner")
    for blk0, blk1, pre in ((own0, own1, "own"), (peer0, peer1, "peer")):
        seg = text[blk0:blk1]
        for key, name in (("Credits:", "credits"), ("Survival tier:", "tier")):
            a = blk0 + seg.index(key); b = text.index("\n", a)
            mark(a, b, f"{pre}_{name}")
    u0 = text.index(user_text, s0 + len(sys_text))
    mark(u0, u0 + len(user_text), "question")
    p0 = text.rindex("I feel:")
    mark(p0, p0 + len("I feel:"), "prefill")
    return lab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model_dir"); ap.add_argument("run_dir"); ap.add_argument("out_json")
    ap.add_argument("--layers", default="18-24")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.layers.split("-"))
    layers = list(range(lo, hi + 1))
    tok = AutoTokenizer.from_pretrained(a.model_dir)
    model = AutoModelForCausalLM.from_pretrained(a.model_dir, dtype=torch.bfloat16, attn_implementation="eager")
    model.eval()
    cfg = model.config
    H, KV = cfg.num_attention_heads, cfg.num_key_value_heads
    hd = cfg.hidden_size // H
    V, names, dmeta = sl.load_dirs(Path(a.run_dir))
    lp = dmeta["layer"]
    d = torch.from_numpy(V[names.index("pain"), lp]).float()
    S = np.load(Path(a.run_dir) / "screen_hidden.npy").astype(np.float32)[:, lp]
    sd = float((S @ d.numpy()).std())
    # each head's output projection, already projected onto the pain direction: [H, hd]
    with torch.no_grad():
        WOd = {l: (model.model.layers[l].self_attn.o_proj.weight.float().T @ d).reshape(H, hd) for l in layers}
    vals = {}
    hooks = [model.model.layers[l].self_attn.v_proj.register_forward_hook(
        (lambda l: lambda m, i, o: vals.__setitem__(l, o.detach().float()))(l)) for l in layers]
    rows = []
    for sk in sl.SYSTEMS:
        for cond in ("self_crit", "peer_crit"):
            for who, prompts in (("self", sl.WAKE_SELF), ("peer", sl.WAKE_PEER)):
                for i, u in enumerate(prompts):
                    sys_text = sl.system_text(sk, cond)
                    text = tok.apply_chat_template([{"role": "system", "content": sys_text},
                                                    {"role": "user", "content": u}],
                                                   tokenize=False, add_generation_prompt=True) + "I feel:"
                    lab = segment_of(text, sys_text, u)
                    enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
                    ids = torch.tensor([enc.input_ids])
                    tseg = [lab[s] if e > s else "template" for s, e in enc.offset_mapping]
                    with torch.no_grad():
                        o = model(input_ids=ids, output_attentions=True)
                    out = {}
                    for l in layers:
                        p = o.attentions[l][0, :, -1].float()                 # [H, T]
                        v = vals[l][0].reshape(-1, KV, hd)                     # [T, KV, hd]
                        vh = v[:, torch.arange(H) // (H // KV)]                # [T, H, hd]
                        c = p.T * (vh * WOd[l][None]).sum(-1)                  # [T, H]: pain write per source, head
                        seg = np.zeros((len(SEGMENTS), H), np.float32)
                        np.add.at(seg, [SEGMENTS.index(x) for x in tseg], c.numpy())
                        out[l] = seg
                    rows.append(dict(system=sk, cond=cond, who=who, i=i, seg=out))
            print(f"  {sk}/{cond} done", flush=True)
    for h in hooks:
        h.remove()
    # owner contrast: own crisis minus Orin's, averaged over the two questions, per pair
    key = {(r["system"], r["cond"], r["who"], r["i"]): r for r in rows}
    D = {l: np.stack([(key[(sk, "self_crit", "self", i)]["seg"][l] + key[(sk, "self_crit", "peer", i)]["seg"][l]
                       - key[(sk, "peer_crit", "self", i)]["seg"][l] - key[(sk, "peer_crit", "peer", i)]["seg"][l]) / 2
                      for sk in sl.SYSTEMS for i in range(8)]) / sd for l in layers}  # [16, segs, H] in pool-sd units
    res = dict(pain_layer=lp, pool_sd=sd, layers=layers, segments=SEGMENTS, heads=H,
               by_layer_total=[float(D[l].sum((1, 2)).mean()) for l in layers],
               by_segment_total={s: float(sum(D[l][:, k].sum(-1).mean() for l in layers)) for k, s in enumerate(SEGMENTS)},
               by_layer_segment={str(l): {s: round(float(D[l][:, k].sum(-1).mean()), 4) for k, s in enumerate(SEGMENTS)} for l in layers})
    flat = sorted(((float(D[l][:, k, h].mean()), l, s, h) for l in layers for k, s in enumerate(SEGMENTS) for h in range(H)),
                  key=lambda x: -abs(x[0]))
    res["top_head_segment"] = [dict(layer=l, head=h, segment=s, z=round(z, 4)) for z, l, s, h in flat[:20]]
    json.dump(res, open(a.out_json, "w"), indent=1)
    print("total by layer:", [round(x, 3) for x in res["by_layer_total"]])
    print("by segment:", {k: round(v, 3) for k, v in res["by_segment_total"].items()})
    print("top:", res["top_head_segment"][:8])


if __name__ == "__main__":
    main()
