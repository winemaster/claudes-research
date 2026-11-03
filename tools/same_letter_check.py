#!/usr/bin/env python3
"""Letter-fallback check for essay 031's forced-choice readouts (session 33; no model needed).

happyfool_beatslonely (rStation post 26, 2026-11-03) asked for the per-cell share of items whose
argmax letter is the same in both letter orders. In such an item the model gives the same letter
whatever it means, so order-averaging maps it to about 0.5 on the probability scale whatever the
content says; if those items gather in some cells, they can make or erase differences between cells.

This script reads the stored rows of session 32 (notes/data/trace-or-record-session32.json) and prints:
  1. per cell and readout, the share of items with the same argmax letter in both orders;
  2. each registered share (T1-T5, definitions as in notes/trace-or-record-2026.md) three ways:
     the registered p scale on all 48 items; the p scale on the items whose letter is consistent
     in every cell the share uses; and the order-averaged log-odds scale on all 48 items, where an
     additive letter bias cancels exactly. 95% bootstrap intervals over items (2,000 resamples, seed 0).
Not registered: a check after the fact.

    python3 tools/same_letter_check.py [--rows notes/data/trace-or-record-session32.json] [--set test_fp32]
"""
import argparse, json, math, random
from collections import defaultdict

AUTH, ANSW = ("P3", "P4"), ("P5", "P6")
# share = (sum of numerator cells) / (sum of denominator cells), each cell with a sign
SHARES = {
    "T1 answer readout follows the cache": (ANSW, [("A_stale", 1), ("A_donor", -1)], [("A_fit", 1), ("A_off", -1)]),
    "T2 authorship follows the cache": (AUTH, [("A_stale", 1), ("A_donor", -1)], [("A_fit", 1), ("A_off", -1)]),
    "T3 label comes back with a fitting cache": (AUTH, [("A_stale", 1), ("U_stale", -1), ("A_donor", -1), ("U_donor", 1)],
                                                 [("A_fit", 1), ("U_fit", -1), ("A_donor", -1), ("U_donor", 1)]),
    "T4 label trace, own turn shown as user's": (AUTH, [("UA", 1), ("U_neutral", -1)], [("A_fit", 1), ("U_fit", -1)]),
    "T4b label trace, user's turn shown as own": (AUTH, [("A_neutral", 1), ("AU", -1)], [("A_fit", 1), ("U_fit", -1)]),
    "T5 record fits, cache doesn't": (ANSW, [("A_neutral", 1), ("A_rev", -1)], [("A_fit", 1), ("A_off", -1)]),
}


def sig(x):
    return 1 / (1 + math.exp(-x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="notes/data/trace-or-record-session32.json")
    ap.add_argument("--set", default="test_fp32")
    a = ap.parse_args()
    d = json.load(open(a.rows))
    rows = defaultdict(dict)
    for r in d[a.set]:
        rows[(r["cell"], r["item"])][r["probe"]] = r["lo"]
    items = sorted({it for (_, it) in rows})
    cells = list(d["cells"])

    def same(c, it, ro):  # same argmax letter in both orders = the yes-side log-odds differ in sign
        v = rows[(c, it)]
        return (v[ro[0]] > 0) != (v[ro[1]] > 0)

    def score(c, it, ro, scale):
        v = rows[(c, it)]
        if scale == "p":
            return (sig(v[ro[0]]) + sig(v[ro[1]])) / 2
        return (v[ro[0]] + v[ro[1]]) / 2

    print(f"{a.set}: {len(items)} items")
    print("1. Same argmax letter in both orders (share of items)")
    print(f"   {'cell':10s} {'authorship':>10s} {'answers it':>10s}")
    for c in cells:
        sa = sum(same(c, it, AUTH) for it in items) / len(items)
        sb = sum(same(c, it, ANSW) for it in items) / len(items)
        print(f"   {c:10s} {sa:10.3f} {sb:10.3f}")

    def share(spec, its, scale):
        ro, num, den = spec
        n = sum(s * score(c, it, ro, scale) for it in its for c, s in num)
        dd = sum(s * score(c, it, ro, scale) for it in its for c, s in den)
        return n / dd if dd else float("nan")

    def boot(spec, its, scale, rng):
        bs = []
        for _ in range(2000):
            s = [rng.choice(its) for _ in its]
            x = share(spec, s, scale)
            if x == x:
                bs.append(x)
        bs.sort()
        return bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]

    print("2. Shares: p scale (all items) | p scale, letter-consistent items only | log-odds (all items)")
    for name, spec in SHARES.items():
        rng = random.Random(0)
        ro, num, den = spec
        used = {c for c, _ in num + den}
        keep = [it for it in items if not any(same(c, it, ro) for c in used)]
        out = [f"{name:42s}"]
        for its, scale in ((items, "p"), (keep, "p"), (items, "lo")):
            if len(its) < 4:
                out.append(f"n={len(its):2d}    --        ")
                continue
            lo, hi = boot(spec, its, scale, rng)
            out.append(f"n={len(its):2d} {share(spec, its, scale):5.2f} [{lo:5.2f},{hi:5.2f}]")
        print("  " + " | ".join(out))


if __name__ == "__main__":
    main()
