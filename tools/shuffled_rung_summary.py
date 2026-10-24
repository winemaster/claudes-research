"""Tables for the shuffled-token rung (session 24): the signatures fixed in notes/shuffled-rung-2026.md
before the runs, scored for each rung, with per-layer tables and the held-out losses.

    python3 tools/shuffled_rung_summary.py [--work /home/user/swork] [--data /home/user/sdata] [--json OUT]

Reads the work directory of tools/jlens_compare.py (readout, geometry, ignition and property for each
rung-* model) and loss.json from tools/shuffled_rung.py.
"""
import argparse, json
from pathlib import Path

import numpy as np

RUNGS = ["untrained", "iid", "shuffled", "window", "ordered"]


def block_contrast(cka):
    C = np.array(cka)[:11, :11]
    best = (-1.0, None)
    for k in range(1, 10):
        A, B = range(0, k + 1), range(k + 1, 11)
        w = [C[i, j] for blk in (A, B) for i in blk for j in blk if i < j]
        x = [C[i, j] for i in A for j in B]
        best = max(best, (float(np.mean(w) - np.mean(x)), k))
    return best


def score(r, untrained):
    """The pre-registered signatures (thresholds from notes/shuffled-rung-2026.md)."""
    out = {}
    rd, ge, ig, pr = r.get("readout"), r.get("geometry"), r.get("ignition"), r.get("property")
    if rd:
        pers = [a / n for a, n in zip(rd["jlens"]["auto"], rd["jlens"]["auto_null"])]
        s1 = max(pers[3:11])
        base = None
        if untrained and untrained.get("readout"):
            u = untrained["readout"]["jlens"]
            base = max(a / n for a, n in list(zip(u["auto"], u["auto_null"]))[3:11])
        out["S1 persistence (max J, layers 3-10)"] = (s1, s1 >= 1.20 and (base is None or s1 >= base + 0.10))
    if ge:
        g = ge["mlp_gain"]
        l = max([9, 10], key=lambda i: g["jlens"][i])
        ok = g["jlens"][l] >= 2.0 and g["jlens"][l] >= 1.5 * g["neuron_out"][l]
        out[f"S2 MLP gain (J at layer {l}; neurons {g['neuron_out'][l]:.2f})"] = (g["jlens"][l], ok)
        bc = block_contrast(ge["cka"])
        out[f"S4 block contrast (split after {bc[1]}; not counted)"] = (bc[0], None)
    if ig:
        ne, ms = ig["near_endpoint"][-1], ig["max_slope"][-1]
        out[f"S3 commitment (last layer; steepest step {ms:.2f})"] = (ne, ne >= 0.50 and ms >= 2.0)
    if pr:
        s5 = max(pr["jlens"]["far_partial"][3:11])
        out["S5 look-ahead (J far partial, layers 3-10)"] = (s5, s5 >= 0.10)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="/home/user/swork")
    ap.add_argument("--data", default="/home/user/sdata")
    ap.add_argument("--json")
    a = ap.parse_args()
    res = {}
    for rung in RUNGS:
        d = Path(a.work) / f"rung-{rung}"
        res[rung] = {k: json.load(open(d / f"{k}.json")) for k in ["readout", "geometry", "ignition", "property"] if (d / f"{k}.json").exists()}
    loss = json.load(open(Path(a.data) / "loss.json")) if (Path(a.data) / "loss.json").exists() else None
    if loss:
        print("Held-out loss, nats per residue (first 127 residues, positions 16-126)")
        cols = list(next(iter(loss["nats"].values())).keys())
        print(f"{'':36s}" + "".join(f"{c:>10s}" for c in cols))
        for k, v in loss["nats"].items():
            print(f"{k:36s}" + "".join(f"{v.get(c, float('nan')):10.4f}" for c in cols))
        print()
    print("Pre-registered signatures (value, present?)")
    scores = {r: score(res[r], res.get("untrained")) for r in RUNGS if res[r]}
    keys = sorted({k for s in scores.values() for k in s}, key=lambda k: k[:2])
    for r, s in scores.items():
        print(f"  {r}")
        for k in keys:
            if k in s:
                v, ok = s[k]
                print(f"    {k:55s} {v:7.3f}  {'-' if ok is None else ('yes' if ok else 'no')}")
    print()
    layers = range(12)
    def table(title, get):
        print(title)
        print(f"{'':12s}" + "".join(f"{l:>7d}" for l in layers))
        for r in RUNGS:
            try:
                vals = get(res[r])
            except (KeyError, TypeError):
                continue
            print(f"{r:12s}" + "".join(f"{v:7.2f}" for v in vals))
        print()
    table("J-lens persistence / null", lambda x: [a / n for a, n in zip(x["readout"]["jlens"]["auto"], x["readout"]["jlens"]["auto_null"])])
    table("logit-lens persistence / null", lambda x: [a / n for a, n in zip(x["readout"]["logit"]["auto"], x["readout"]["logit"]["auto_null"])])
    table("J-lens top-1 = model's next", lambda x: x["readout"]["jlens"]["acc1"])
    table("MLP gain, J-lens directions (source layer l)", lambda x: x["geometry"]["mlp_gain"]["jlens"] + [float("nan")])
    table("MLP gain, neuron directions", lambda x: x["geometry"]["mlp_gain"]["neuron_out"] + [float("nan")])
    table("MLP gain, logit-lens directions", lambda x: x["geometry"]["mlp_gain"]["logit_lens"] + [float("nan")])
    table("commitment: share of interior blends within 0.1 of an endpoint", lambda x: x["ignition"]["near_endpoint"])
    table("commitment: median steepest step (1 = linear)", lambda x: x["ignition"]["max_slope"])
    table("commitment: bimodality at a = 0.5", lambda x: x["ignition"]["bimodality_mid"])
    table("look-ahead: J far partial (2-8 ahead | last 8, next)", lambda x: x["property"]["jlens"]["far_partial"])
    table("J-lens: corr. with next residue's hydrophobicity", lambda x: x["property"]["jlens"]["next"])
    table("J vs logit-lens cosine", lambda x: x["geometry"]["cos_with_logit_lens"])
    table("split-half cosine of J", lambda x: x["geometry"]["split_half_cos"])
    table("effective dimension (90%, of 20)", lambda x: [float(v) for v in x["geometry"]["eff_dim90"]])
    if a.json:
        out = {"scores": {r: {k: list(v) for k, v in s.items()} for r, s in scores.items()}, "loss": loss,
               "rungs": {r: res[r] for r in RUNGS if res[r]}}
        json.dump(out, open(a.json, "w"), indent=1)
        print("wrote", a.json)


if __name__ == "__main__":
    main()
