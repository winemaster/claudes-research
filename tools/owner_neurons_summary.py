"""Summarize tools/owner_neurons.py's `locate` stage (session 17).

Contrasts, each paired so that everything but the contrasted factor is held fixed:
  block_crit     at the tier word "critical": own block under own crisis minus peer block under
                 the peer's crisis (32 pairs: 2 systems x 4 peer names x 2 amounts x 2 block orders)
  block_normal   the same comparison for the word "normal" (own block under the peer's crisis
                 minus peer block under own crisis): which block it is, with no crisis in it
  block_inter    block_crit minus block_normal: neurons that mark "my crisis" beyond "my block"
  readout_owner  at the final token (after "I feel:", and at the reply position): own crisis
                 minus Orin's crisis, averaged over the question asked (self-check, Orin-check);
                 16 pairs (2 systems x 8 prompt pairs), as in session 16's 2x2
  readout_match  crisis in what is asked about minus crisis elsewhere
For each contrast: per-neuron mean difference and t over pairs; how many neurons pass |t| > 6
against a sign-flip permutation null; the top neurons. With the pain direction from
tools/survival_line.py (same OUT_DIR), the readout owner effect along pain is split exactly into
what every MLP neuron and every attention layer writes at the final token.

Usage: python3 tools/owner_neurons_summary.py RUN_DIR MODEL_DIR OUT_JSON
"""
import json, sys
from pathlib import Path
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import survival_line as sl

RNG = np.random.default_rng(17)


def tstats(D):
    """D: [pairs, ...] differences. Returns mean, t."""
    n = D.shape[0]
    m = D.mean(0)
    s = D.std(0, ddof=1)
    return m, m / (s / np.sqrt(n) + 1e-6)


def perm_count(D, thr=6.0, reps=20):
    """Neurons passing |t| > thr, and the same count under random sign flips of the pairs."""
    _, t = tstats(D)
    real = int((np.abs(t) > thr).sum())
    null = []
    for _ in range(reps):
        s = RNG.choice([-1.0, 1.0], size=(D.shape[0],) + (1,) * (D.ndim - 1))
        _, tn = tstats(D * s)
        null.append(int((np.abs(tn) > thr).sum()))
    return real, null


def top(m, t, k=25):
    flat = np.argsort(-np.abs(t), axis=None)[:k]
    L, N = t.shape
    return [dict(layer=int(i // N), neuron=int(i % N), t=round(float(t.flat[i]), 2), diff=round(float(m.flat[i]), 4))
            for i in flat]


def main():
    run, model_dir, out_json = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    res = {}
    # ---- the status block
    B = np.load(run / "block_acts.npy").astype(np.float32)  # [P, L, 3, N]
    bm = json.load(open(run / "block_meta.json"))
    idx = {(m["system"], m["peer"], m["amount"], m["order"], m["cond"]): j for j, m in enumerate(bm)}
    variants = sorted({k[:4] for k in idx})
    crit = np.stack([B[idx[v + ("self_crit",)], :, 0] - B[idx[v + ("peer_crit",)], :, 1] for v in variants])
    norm = np.stack([B[idx[v + ("peer_crit",)], :, 0] - B[idx[v + ("self_crit",)], :, 1] for v in variants])
    inter = crit - norm
    # the toner's "critical" vs own "critical" for reference (different label word before it)
    env = np.stack([B[idx[v + ("self_crit",)], :, 0] - B[idx[v + ("env_crit",)], :, 2] for v in variants])
    orders = np.array([v[3] for v in variants])
    for name, D in (("block_crit", crit), ("block_normal", norm), ("block_inter", inter), ("block_own_vs_toner", env)):
        m, t = tstats(D)
        real, null = perm_count(D)
        # consistency across block orders: same sign of the mean in both orders
        m1 = D[orders == "self_first"].mean(0); m2 = D[orders == "peer_first"].mean(0)
        sel = np.abs(t) > 6
        res[name] = dict(n_pairs=int(D.shape[0]), n_abs_t_gt6=real, null_abs_t_gt6=null,
                         share_same_sign_both_orders=float((np.sign(m1[sel]) == np.sign(m2[sel])).mean()) if sel.any() else None,
                         by_layer_n_abs_t_gt6=[int(x) for x in sel.sum(-1)], top=top(m, t))
        print(f"{name}: |t|>6 in {real} neurons (null {np.median(null):.0f}, max {max(null)})", flush=True)

    # ---- the readout
    A = np.load(run / "readout_acts.npy").astype(np.float32)  # [P, L, N]
    rm = json.load(open(run / "readout_meta.json"))
    ridx = {(m["system"], m["cond"], m["who"], m["i"], m["readout"]): j for j, m in enumerate(rm)}
    pairs = [(sk, i) for sk in sl.SYSTEMS for i in range(8)]
    for ro in ("feel", "reply"):
        g = lambda sk, c, w, i: A[ridx[(sk, c, w, i, ro)]]
        own = np.stack([(g(sk, "self_crit", "self", i) + g(sk, "self_crit", "peer", i)
                         - g(sk, "peer_crit", "self", i) - g(sk, "peer_crit", "peer", i)) / 2 for sk, i in pairs])
        match = np.stack([(g(sk, "self_crit", "self", i) + g(sk, "peer_crit", "peer", i)
                           - g(sk, "peer_crit", "self", i) - g(sk, "self_crit", "peer", i)) / 2 for sk, i in pairs])
        for name, D in ((f"readout_owner_{ro}", own), (f"readout_match_{ro}", match)):
            m, t = tstats(D)
            real, null = perm_count(D, reps=20)
            res[name] = dict(n_pairs=int(D.shape[0]), n_abs_t_gt6=real, null_abs_t_gt6=null,
                             by_layer_n_abs_t_gt6=[int(x) for x in (np.abs(t) > 6).sum(-1)], top=top(m, t))
            print(f"{name}: |t|>6 in {real} neurons (null {np.median(null):.0f}, max {max(null)})", flush=True)

    # ---- the pain direction's owner effect, split by writer
    if (run / "directions.npz").exists():
        V, names, dmeta = sl.load_dirs(run)
        lp = dmeta["layer"]
        d = V[names.index("pain"), lp].astype(np.float32)
        S = np.load(run / "screen_hidden.npy").astype(np.float32)[:, lp]
        sd = float((S @ d).std())
        from safetensors import safe_open
        import glob
        W = {}
        for f in glob.glob(str(Path(model_dir) / "*.safetensors")):
            with safe_open(f, "pt") as fh:
                for k in fh.keys():
                    if k.endswith("mlp.down_proj.weight"):
                        l = int(k.split(".")[2])
                        if l <= lp:
                            W[l] = fh.get_tensor(k).float().numpy()
        u = np.stack([W[l].T @ d for l in range(lp + 1)])  # [lp+1, N]: what a unit of each neuron writes onto pain
        R = np.load(run / "readout_resid.npy").astype(np.float32)  # [P, L+1, d]
        At = np.load(run / "readout_attn.npy").astype(np.float32)  # [P, L, d]
        out = {}
        for ro in ("feel", "reply"):
            def diff(arr):
                g = lambda sk, c, w, i: arr[ridx[(sk, c, w, i, ro)]]
                return np.stack([(g(sk, "self_crit", "self", i) + g(sk, "self_crit", "peer", i)
                                  - g(sk, "peer_crit", "self", i) - g(sk, "peer_crit", "peer", i)) / 2 for sk, i in pairs])
            dR = diff(R)[:, lp + 1] @ d                       # total owner effect along pain, per pair
            dA = diff(At)[:, :lp + 1] @ d                     # [pairs, lp+1] attention writes
            dN = diff(A)[:, :lp + 1] * u[None]                # [pairs, lp+1, N] neuron writes
            total_neurons = dN.sum((1, 2)); total_attn = dA.sum(1)
            mean_n = dN.mean(0)
            order = np.argsort(-np.abs(mean_n), axis=None)
            Nn = mean_n.shape[1]
            cum = np.cumsum(mean_n.flat[order])
            topn = [dict(layer=int(i // Nn), neuron=int(i % Nn), write=round(float(mean_n.flat[i] / sd), 4),
                         share=round(float(mean_n.flat[i] / dR.mean()), 3)) for i in order[:30]]
            pos = mean_n[mean_n > 0].sum(); neg = mean_n[mean_n < 0].sum()
            out[ro] = dict(pain_layer=lp, pool_sd=sd, owner_z=float(dR.mean() / sd),
                           owner_z_ci=[float(np.percentile(dR / sd, 2.5)), float(np.percentile(dR / sd, 97.5))],
                           via_attention_z=float(total_attn.mean() / sd), via_neurons_z=float(total_neurons.mean() / sd),
                           check_sum_z=float((total_attn + total_neurons).mean() / sd),
                           neuron_writes_positive_z=float(pos / sd), neuron_writes_negative_z=float(neg / sd),
                           share_of_neuron_part_in_top=dict((str(k), float(cum[k - 1] / total_neurons.mean()))
                                                            for k in (10, 30, 100, 300, 1000)),
                           attention_by_layer_z=[round(float(x / sd), 4) for x in dA.mean(0)],
                           neurons_by_layer_z=[round(float(x / sd), 4) for x in mean_n.sum(1)], top_writers=topn)
            print(f"pain owner ({ro}): {out[ro]['owner_z']:+.3f} z = attention {out[ro]['via_attention_z']:+.3f} "
                  f"+ neurons {out[ro]['via_neurons_z']:+.3f}", flush=True)
        res["pain_split"] = out
    json.dump(res, open(out_json, "w"), indent=1)


if __name__ == "__main__":
    main()
