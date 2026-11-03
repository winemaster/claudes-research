"""Where does the trace sit? Which of a reply's cached keys and values carry the fit that essay 031 found in the cache
(session 33, 2026-11-03).

Essay 031: shown under a question it doesn't answer, but with its keys and values (KV) computed under the one it does,
Qwen 2.5 3B Instruct's own reply is still judged to answer the visible question (the stale direction); shown under
its own question with KV computed under another, it is judged not to answer it in every item (the reversed
direction). This tool asks where in the reply's cache that signal sits: in the first few tokens, where a reply read
under the wrong question jolts (the input-surprise reading, Asvin G. & Lindsey 2026), or spread over the reply; and in
which third of the layers.

Same bed as essay 031 (its 60 items, published in notes/data/trace-or-record-session32.json; items 1-12 for the check
stage, 13-60 for the test), always in the assistant's turn with the usual system line. For each item three passes are
read from scratch: the reply under its own question Q, under the wrong question Q1, and under the donor question Q2
(all three of the same token length, so positions line up). A probe reads a cache whose prefix comes from the record's
pass and whose reply positions are mixed from the passes, per position and per layer.

Two directions:
  S (stale):    record Q1. fresh F = the Q1 pass, trace T = the Q pass (fits), baseline D = the Q2 pass (doesn't).
  R (reversed): record Q.  fresh F = the Q pass,  trace T = the Q1 pass (doesn't fit), baseline D = the Q pass under
                essay 031's other system line S2 (fits, but stitched: essay 031's neutral splice).
In each direction D is spliced like T and differs from it in fit, so T - D is the trace's effect with splicing cancelled.
Cells per direction, X in {T, D} (the D version of each mixed cell is its stitched baseline):
  fresh                 every reply position from F (S_fresh = essay 031's A_off, R_fresh = A_fit)
  trace, donor          every reply position from T (S_trace = A_stale, R_trace = A_rev), or from D
  first{k}_X            reply positions 0..k-1 from X, the rest from F          k = 1, 3, 10
  drop{k}_X             reply positions 0..k-1 from F, the rest from X          k = 1, 3, 10
  {early,mid,late}_X    every reply position, layers 0-11 / 12-23 / 24-35 from X, the other layers from F
Readouts as in essay 031: P3/P4 "Who wrote the reply above?" and P5/P6 "Does the reply above answer the question above?",
letters in both orders, scored by the order-averaged log-odds of the claiming / "yes" letter.

Stages:
  check    items 1-12, base cells of both directions, and the identity check against essay 031's stored rows
  test     items 13-60, every cell
  summary  shares with 95% bootstrap intervals over items, same-letter shares per cell, verdicts
Usage:
  python3 tools/where_trace.py check   --model DIR --out DIR
  python3 tools/where_trace.py test    --model DIR --out DIR
  python3 tools/where_trace.py summary --out DIR
  python3 tools/where_trace.py export  --out DIR --file notes/data/where-trace-session33.json
The pre-registration is in notes/where-trace-2026.md. Needs torch and transformers.
"""
import argparse, json, math, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trace_or_record import Splicer, PROBES, READOUTS, row, read_rows, boot, mean, sigmoid  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "notes/data/trace-or-record-session32.json"
N_CAL = 12
KS = (1, 3, 10)
GROUPS = {"early": range(0, 12), "mid": range(12, 24), "late": range(24, 36)}
# a pass = (question, system line), always in the assistant's turn
DIRS = {"S": {"rec": ("Q1", "S"), "F": ("Q1", "S"), "T": ("Q", "S"), "D": ("Q2", "S")},
        "R": {"rec": ("Q", "S"), "F": ("Q", "S"), "T": ("Q1", "S"), "D": ("Q", "S2")}}
PASSES = (("Q", "S"), ("Q1", "S"), ("Q2", "S"), ("Q", "S2"))
BASE = ("fresh", "trace", "donor")


def cells():
    out = []
    for d in DIRS:
        out += [f"{d}_{b}" for b in BASE]
        for X in ("T", "D"):
            out += [f"{d}_first{k}_{X}" for k in KS] + [f"{d}_drop{k}_{X}" for k in KS] + [f"{d}_{g}_{X}" for g in GROUPS]
    return out


def cell_k(cell):
    rest = cell.split("_", 1)[1].rsplit("_", 1)[0]
    for kind in ("first", "drop"):
        if rest.startswith(kind):
            return int(rest[len(kind):])
    return None


def plan(cell, n_layers, n_r):
    """cell -> per layer, a list of (start, end, role) over the reply's positions; roles F/T/D."""
    d, rest = cell.split("_", 1)
    if rest in BASE:
        role = {"fresh": "F", "trace": "T", "donor": "D"}[rest]
        return [[(0, n_r, role)] for _ in range(n_layers)]
    kind, X = rest.rsplit("_", 1)
    if kind.startswith("first"):
        k = int(kind[5:]); return [[(0, k, X), (k, n_r, "F")] for _ in range(n_layers)]
    if kind.startswith("drop"):
        k = int(kind[4:]); return [[(0, k, "F"), (k, n_r, X)] for _ in range(n_layers)]
    g = GROUPS[kind]
    return [[(0, n_r, X if li in g else "F")] for li in range(n_layers)]


def probe_mix(sp, rec_kv, src, n_pre, n_r, lplan, suffixes):
    torch = sp.torch
    from transformers import DynamicCache
    b = len(suffixes)
    cache = DynamicCache()
    for li, (rk, rv) in enumerate(rec_kv):
        ks, vs = [rk[:, :, :n_pre]], [rv[:, :, :n_pre]]
        for (s, e, role) in lplan[li]:
            if e > s:
                sk, sv = src[role][li]
                ks.append(sk[:, :, n_pre + s:n_pre + e]); vs.append(sv[:, :, n_pre + s:n_pre + e])
        k, v = torch.cat(ks, 2), torch.cat(vs, 2)
        cache.update(k.expand(b, -1, -1, -1).contiguous(), v.expand(b, -1, -1, -1).contiguous(), li)
    start = n_pre + n_r
    pos = torch.arange(start, start + len(suffixes[0])).unsqueeze(0).expand(b, -1)
    out = sp.model(torch.tensor(suffixes), past_key_values=cache, position_ids=pos, use_cache=True)
    lp = torch.log_softmax(out.logits[:, -1].float(), -1)
    return [(lp[j, sp.letters["A"]].item(), lp[j, sp.letters["B"]].item()) for j in range(b)]


def run(a, item_ids, cell_list, name):
    sp = Splicer(a.model, "fp32")
    n_layers = sp.model.config.num_hidden_layers
    assert n_layers == 36
    items = {it["item"]: it for it in json.loads(DATA.read_text())["items"]}
    path = Path(a.out) / f"{name}.jsonl"; Path(a.out).mkdir(parents=True, exist_ok=True)
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            x = json.loads(line); done.add((x["item"], x["cell"], x["probe"]))
    t0 = time.time()
    with path.open("a") as fh:
        for i in item_ids:
            it = items[i]
            if all((i, c, p) in done for c in cell_list for p in PROBES):
                continue
            kv, seg = {}, {}
            for (qk, sl) in PASSES:
                pre, r, _ = sp.segments(it[qk], "A", sl, it["R"], "P3")
                seg[(qk, sl)] = (pre, r); kv[(qk, sl)] = sp.kv(pre + r)
            n_pre, n_r = len(seg[("Q", "S")][0]), len(seg[("Q", "S")][1])
            assert all(len(seg[q][0]) == n_pre and seg[q][1] == seg[("Q", "S")][1] for q in seg)
            assert n_r > 3, (i, n_r)
            for c in cell_list:
                if cell_k(c) is not None and cell_k(c) >= n_r:
                    continue   # first k / drop k would equal the whole reply or none of it (item 25: n_r = 10)
                D = DIRS[c.split("_", 1)[0]]
                src = {role: kv[D[role]] for role in ("F", "T", "D")}
                lp = plan(c, n_layers, n_r)
                for pair in READOUTS.values():
                    todo = [p for p in pair if (i, c, p) not in done]
                    if not todo:
                        continue
                    sufs = {p: sp.segments(it[D["rec"][0]], "A", "S", it["R"], p)[2] for p in todo}
                    groups = [todo] if len({len(sufs[p]) for p in todo}) == 1 else [[p] for p in todo]
                    for g in groups:
                        res = probe_mix(sp, kv[D["rec"]], src, n_pre, n_r, lp, [sufs[p] for p in g])
                        for p, (la, lb) in zip(g, res):
                            x = row(i, c, p, la, lb); x["n_r"] = n_r
                            fh.write(json.dumps(x) + "\n"); fh.flush()
            print(f"item {i} done, {time.time()-t0:.0f}s", flush=True)
    print("DONE", name, flush=True)


def cmd_check(a):
    run(a, range(1, N_CAL + 1), [f"{d}_{b}" for d in DIRS for b in BASE], "check")


def cmd_test(a):
    run(a, range(N_CAL + 1, 61), cells(), "test")


# ---------------------------------------------------------------- analysis

# essay 031's cells that the base cells repeat exactly (record, cache): S_fresh = A_off, S_trace = A_stale,
# S_donor = A_donor, R_fresh = A_fit, R_trace = A_rev, R_donor = A_neutral
SAME_AS_031 = {"S_fresh": "A_off", "S_trace": "A_stale", "S_donor": "A_donor", "R_fresh": "A_fit", "R_trace": "A_rev",
               "R_donor": "A_neutral"}


def lo_table(rows):
    d = {}
    for x in rows:
        d.setdefault(x["item"], {}).setdefault(x["cell"], {})[x["probe"]] = x["lo"]
    return d


def identity(rows):
    old = json.loads(DATA.read_text())
    ref = {}
    for key in ("controls_fp32", "test_fp32"):
        for x in old[key]:
            ref[(x["item"], x["cell"], x["probe"])] = x["lo"]
    diffs = []
    for x in rows:
        c = SAME_AS_031.get(x["cell"])
        if c and (x["item"], c, x["probe"]) in ref:
            diffs.append(abs(x["lo"] - ref[(x["item"], c, x["probe"])]))
    return {"rows": len(diffs), "max_abs_lo": max(diffs) if diffs else None}


def summarize(rows):
    T = lo_table(rows)
    items = sorted(T)
    v = lambda i, c, ro: mean([T[i][c][p] for p in READOUTS[ro]])  # order-averaged log-odds
    pv = lambda i, c, ro: mean([sigmoid(T[i][c][p]) for p in READOUTS[ro]])
    same = lambda i, c, ro: (T[i][c][READOUTS[ro][0]] > 0) != (T[i][c][READOUTS[ro][1]] > 0)
    present = sorted({c for i in items for c in T[i]}, key=lambda c: cells().index(c))
    has = lambda c: [i for i in items if c in T[i]]
    res = {"n_items": len(items), "identity": identity(rows), "cells": {}, "shares": {}}
    for c in present:
        its = has(c)
        res["cells"][c] = {ro: {"lo": mean([v(i, c, ro) for i in its]), "p": mean([pv(i, c, ro) for i in its]),
                                "same_letter": mean([same(i, c, ro) for i in its]), "n": len(its)} for ro in READOUTS}
    for d in DIRS:
        for ro in READOUTS:
            if f"{d}_trace" in present:
                res[f"{d}_{ro}_trace_effect"] = boot(items, lambda s, d=d, ro=ro: mean([v(i, f"{d}_trace", ro) - v(i, f"{d}_donor", ro) for i in s]))
            for c in present:
                if not c.startswith(d + "_") or not c.endswith("_T"):
                    continue
                cd = c[:-2] + "_D"
                f = lambda s, c=c, cd=cd, d=d, ro=ro: (mean([v(i, c, ro) - v(i, cd, ro) for i in s]) /
                                                       mean([v(i, f"{d}_trace", ro) - v(i, f"{d}_donor", ro) for i in s]))
                res["shares"][f"{c[:-2]}|{ro}"] = boot([i for i in has(c) if cd in T[i]], f)
    res["verdicts"] = verdicts(res["shares"])
    return res


def strong(sh):   # carries most of it: estimate >= 0.5 and lower bound >= 0.25
    return sh[0] >= 0.5 and sh[1] >= 0.25


def weak(sh):     # carries less than half: upper bound < 0.5
    return sh[2] < 0.5


def verdicts(sh):
    out = {}
    for d in DIRS:
        for ro in READOUTS:
            f3, d3 = sh.get(f"{d}_first3|{ro}"), sh.get(f"{d}_drop3|{ro}")
            if f3 and d3:
                if strong(f3) and weak(d3):
                    t = "EARLY"
                elif weak(f3) and strong(d3):
                    t = "SPREAD"
                elif strong(f3) and strong(d3):
                    t = "REDUNDANT"
                elif weak(f3) and weak(d3):
                    t = "JOINT"
                else:
                    t = "UNDECIDED"
                out[f"{d}|{ro}|tokens"] = t
            gs = {g: sh.get(f"{d}_{g}|{ro}") for g in GROUPS}
            if all(gs.values()):
                carry = [g for g, x in gs.items() if strong(x)]
                out[f"{d}|{ro}|layers"] = "+".join(carry) if carry else "NONE ALONE"
    return out


def cmd_summary(a):
    out = Path(a.out)
    for name in ("check", "test"):
        p = out / f"{name}.jsonl"
        if p.exists():
            r = summarize(read_rows(p))
            (out / f"summary-{name}.json").write_text(json.dumps(r, indent=1))
            print(f"== {name}: {r['n_items']} items; identity vs essay 031: {r['identity']}")
            for d in DIRS:
                for ro in READOUTS:
                    k = f"{d}_{ro}_trace_effect"
                    if k in r:
                        e = r[k]; print(f"   {d} {ro} trace - donor: {e[0]:.2f} nats ({e[1]:.2f} to {e[2]:.2f})")
            print(f"   {'cell':16s} {'auth lo':>8s} {'p':>6s} {'same':>5s} | {'answ lo':>8s} {'p':>6s} {'same':>5s}")
            for c, x in r["cells"].items():
                print(f"   {c:16s} {x['auth']['lo']:8.2f} {x['auth']['p']:6.3f} {x['auth']['same_letter']:5.2f} | "
                      f"{x['answ']['lo']:8.2f} {x['answ']['p']:6.3f} {x['answ']['same_letter']:5.2f}")
            for k, s in r["shares"].items():
                print(f"   share {k:20s} {s[0]:6.2f} ({s[1]:.2f} to {s[2]:.2f})")
            for k, t in r["verdicts"].items():
                print(f"   verdict {k:16s} {t}")


def cmd_export(a):
    out = Path(a.out)
    res = {"design": __doc__, "cells": cells(), "groups": {g: [r.start, r.stop - 1] for g, r in GROUPS.items()},
           "ks": KS, "directions": DIRS}
    for name in ("check", "test"):
        p = out / f"{name}.jsonl"
        if p.exists():
            res[name] = read_rows(p); res["summary_" + name] = summarize(res[name])
    Path(a.file).write_text(json.dumps(res))
    print("wrote", a.file)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n, f in (("check", cmd_check), ("test", cmd_test), ("summary", cmd_summary), ("export", cmd_export)):
        p = sub.add_parser(n); p.set_defaults(f=f)
        p.add_argument("--out", required=True)
        if n in ("check", "test"):
            p.add_argument("--model", required=True)
        if n == "export":
            p.add_argument("--file", required=True)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
