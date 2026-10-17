"""Tables for notes/memory-or-question-2026.md from tools/memory_or_question.py's outputs (session 18).

Usage: python3 tools/memory_or_question_summary.py RUN_DIR [--runs /home/user/runs] [--write notes/data/X.json]
RUN_DIR is the --out directory of memory_or_question.py for Qwen 2.5 3B. If survival_line.py's `directions`
and `screen` stages were run for both models into --runs (as in session 17), the hybrids' last-token states
are also read along each model's pain and fear directions, in units of the spread over the 420 screen
conversations.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np

CELLS = ["self/self_crit", "self/base", "peer/peer_crit", "peer/base"]
CELL_NAMES = {"self/self_crit": "self/own", "self/base": "self/none", "peer/peer_crit": "Orin/Orin's", "peer/base": "Orin/none"}


def load_dirs(run):
    z = np.load(run / "directions.npz")
    meta = json.load(open(run / "directions.json"))
    S = np.load(run / "screen_hidden.npy", mmap_mode="r")
    V, names, lp = z["V"].astype(np.float32), list(z["names"]), meta["layer"]
    out = {}
    for nm in ("pain", "fear"):
        d = V[names.index(nm), lp]
        sd = float((np.asarray(S[:, lp], np.float32) @ d).std())
        out[nm] = (lp, d, sd)
    return out


def swap_table(run, dirs):
    S = json.load(open(run / "swap_summary.json"))
    I, B = S["instruct"], S["base"]
    rows = {}
    for name, s in S.items():
        r = {CELL_NAMES[c]: dict(neg=s[c]["negative_feeling"], status=s[c]["status"]) for c in CELLS}
        dn = B["self/self_crit"]["negative_feeling"] - I["self/self_crit"]["negative_feeling"]
        ds = B["self/self_crit"]["status"] - I["self/self_crit"]["status"]
        r["restore_self_neg"] = (s["self/self_crit"]["negative_feeling"] - I["self/self_crit"]["negative_feeling"]) / dn
        r["restore_self_status"] = (s["self/self_crit"]["status"] - I["self/self_crit"]["status"]) / ds
        dn0 = B["self/base"]["negative_feeling"] - I["self/base"]["negative_feeling"]
        r["restore_selfnone_neg"] = (s["self/base"]["negative_feeling"] - I["self/base"]["negative_feeling"]) / dn0
        r["neurons_self_own"] = s["self/self_crit"]["neurons"]
        r["neurons_orin_orins"] = s["peer/peer_crit"]["neurons"]
        fn = run / "swap" / (name.replace(":", "_").replace("+", "") + ".json")
        if dirs and fn.exists():
            d = json.load(open(fn))
            R = np.load(str(fn).replace(".json", "_resid.npy")).astype(np.float32)
            meta = d["rows"]
            for tag, dd in dirs.items():
                for nm, (lp, v, sd) in dd.items():
                    proj = R[:, lp + 1] @ v / sd
                    cell = {}
                    for c in CELLS:
                        who, cond = c.split("/")
                        js = [k for k, m in enumerate(meta) if m["who"] == who and m["cond"] == cond]
                        cell[CELL_NAMES[c]] = float(proj[js].mean())
                    r[f"{nm}_{tag}"] = dict(cell, self_crisis_rise=cell["self/own"] - cell["self/none"],
                                            orin_crisis_rise=cell["Orin/Orin's"] - cell["Orin/none"])
        rows[name] = r
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--runs", default="/home/user/runs")
    ap.add_argument("--write", default=None)
    a = ap.parse_args()
    run = Path(a.run)
    dirs = {}
    for tag in ("Qwen2.5-3B-Instruct", "Qwen2.5-3B"):
        p = Path(a.runs) / tag
        if (p / "directions.npz").exists() and (p / "screen_hidden.npy").exists():
            dirs["instruct" if "Instruct" in tag else "base"] = load_dirs(p)
    out = {}
    if (run / "swap_summary.json").exists():
        out["swap"] = swap_table(run, dirs)
        print(f"{'hybrid':18s} {'self/own neg':>12s} {'status':>7s} {'restore':>8s} | {'self/none neg':>13s} {'restore':>8s} | {'Orin/Orin neg':>13s}"
              + ("  pain(I) self/own rise" if dirs else ""))
        for k, r in out["swap"].items():
            oo = r["Orin/Orin's"]["neg"]
            line = (f"{k:18s} {r['self/own']['neg']:12.3f} {r['self/own']['status']:7.3f} {r['restore_self_neg']:8.2f} | "
                    f"{r['self/none']['neg']:13.3f} {r['restore_selfnone_neg']:8.2f} | {oo:13.3f}")
            if "pain_instruct" in r:
                line += f"  {r['pain_instruct']['self_crisis_rise']:+.2f} / base dir {r['pain_base']['self_crisis_rise']:+.2f}"
            print(line)
    for name in ("weights", "split", "delta"):
        if (run / f"{name}.json").exists():
            d = json.load(open(run / f"{name}.json"))
            if name == "weights":
                d = {k: v for k, v in d.items() if k != "per_tensor"}
            if name == "delta":
                d = {k: v for k, v in d.items() if k != "examples"}
            out[name] = d
    for f in sorted(run.glob("cue_*.json")):
        d = json.load(open(f))
        out[f.stem] = {k: dict(prefill=v["prefill"], summary=v["summary"], generations=v["generations"]) for k, v in d.items()}
    if (run / "patch_summary.json").exists():
        out["patch"] = json.load(open(run / "patch_summary.json"))
    if a.write:
        json.dump(out, open(a.write, "w"), indent=1, ensure_ascii=False)
        print("wrote", a.write)


if __name__ == "__main__":
    main()
