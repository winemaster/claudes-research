"""Tables for session 20's workspace test (tools/jlens_compare.py): reads each model's readout,
geometry, ignition (both designs), property and eval results from the work directory, prints them side by side, and
writes one combined JSON (notes/data/jlens-compare-session20.json).

Usage: python3 tools/jlens_compare_summary.py [--work DIR] [--out FILE]
"""
import argparse, json
from pathlib import Path

MODELS = ["text", "protein", "random"]


def load(work, m, stage):
    p = Path(work) / m / f"{stage}.json"
    return json.load(open(p)) if p.exists() else None


def row(vals, fmt="{:6.2f}"):
    return " ".join(fmt.format(v) if v is not None else "   -  " for v in vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="/home/user/jwork")
    ap.add_argument("--out", default="notes/data/jlens-compare-session20.json")
    a = ap.parse_args()
    out = {}
    for m in MODELS:
        out[m] = {s: load(a.work, m, s) for s in ["readout", "geometry", "ignition", "ignition_sequence", "property", "evals"]}
        if out[m]["readout"]:
            out[m]["readout"].pop("examples_full", None)
    L = 12
    print("layer:            " + " ".join(f"{l:6d}" for l in range(L)))
    for m in MODELS:
        r, g, ig = out[m]["readout"], out[m]["geometry"], out[m]["ignition"]
        print(f"\n=== {m}")
        if r:
            j, lg = r["jlens"], r["logit"]
            print("J acc1 (model's next)  " + row(j["acc1"]))
            print("logit acc1             " + row(lg["acc1"]))
            print("J kurtosis             " + row(j["kurt"]))
            print("logit kurtosis         " + row(lg["kurt"]))
            print("J auto - null          " + row([x - y for x, y in zip(j["auto"], j["auto_null"])], "{:6.3f}"))
            print("J auto / null          " + row([x / max(y, 1e-9) for x, y in zip(j["auto"], j["auto_null"])]))
            print("logit auto / null      " + row([x / max(y, 1e-9) for x, y in zip(lg["auto"], lg["auto_null"])]))
            print("J top not in nor out   " + row(j["not_in_or_out"]))
            if j["m_acc1"]:
                print("matched-20 J acc1      " + row(j["m_acc1"]))
                print("matched-20 J kurt      " + row(j["m_kurt"]))
                print("matched-20 J auto/null " + row([x / max(y, 1e-9) for x, y in zip(j["m_auto"], j["m_auto_null"])]))
        if g:
            print("CKA(l, l+1)            " + row([g["cka"][l][l + 1] for l in range(L - 1)] + [None], "{:6.3f}"))
            print("CKA(l, final)          " + row([g["cka"][l][L - 1] for l in range(L)], "{:6.3f}"))
            print("CKA(l, mid=6)          " + row([g["cka"][l][6] for l in range(L)], "{:6.3f}"))
            if "cka_matched" in g:
                print("matched CKA(l, l+1)    " + row([g["cka_matched"][l][l + 1] for l in range(L - 1)] + [None], "{:6.3f}"))
            print("eff dim 90% (frac)     " + row(g["eff_dim90_frac"], "{:6.3f}"))
            if "eff_dim90_matched" in g:
                print("matched eff dim (of 20)" + row(g["eff_dim90_matched"], "{:6.1f}"))
            print("cos(J, logit lens)     " + row(g["cos_with_logit_lens"], "{:6.3f}"))
            print("split-half cos         " + row(g["split_half_cos"], "{:6.3f}"))
            mg = g["mlp_gain"]
            print("MLP gain J-lens        " + row(mg["jlens"] + [None]))
            print("MLP gain logit-lens    " + row(mg["logit_lens"] + [None]))
            print("MLP gain neuron out    " + row(mg["neuron_out"] + [None]))
        if ig:
            print("ignition max slope     " + row(ig["max_slope"]))
            print("ignition near endpoint " + row(ig["near_endpoint"]))
            print("ignition bimodal @0.5  " + row(ig["bimodality_mid"]))
        igs = out[m]["ignition_sequence"]
        if igs:
            print("seq-design max slope   " + row(igs["max_slope"]))
            print("seq-design near endpt  " + row(igs["near_endpoint"]))
            print("seq-design bimodal     " + row(igs["bimodality_mid"]))
        p = out[m]["property"]
        if p:
            for k in ["past", "next", "future", "far", "next_partial", "far_partial"]:
                if k in p["jlens"]:
                    print(f"J hydroph. r {k:12s}" + row(p["jlens"][k]))
            for k in ["past", "next", "future", "far", "next_partial", "far_partial"]:
                if k in p["logit"]:
                    print(f"logit hydr. r {k:11s}" + row(p["logit"][k]))
        ev = out[m]["evals"]
        if ev:
            print("eval set       pass@1 J/logit   pass@25 J/logit   pass@100 J/logit   median rank J/logit")
            for name, v in ev.items():
                if not isinstance(v, dict):
                    continue
                j, lg = v["jlens"], v["logit"]
                print(f"  {name:12s} {j['pass@1']:6.3f}/{lg['pass@1']:5.3f}    {j['pass@25']:6.3f}/{lg['pass@25']:5.3f}"
                      f"     {j['pass@100']:6.3f}/{lg['pass@100']:5.3f}      {j['median_rank']:7.1f}/{lg['median_rank']:7.1f}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("\nwrote", a.out)


if __name__ == "__main__":
    main()
