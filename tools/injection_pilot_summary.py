"""Summarize injection_pilot.py output (JSON): localization accuracy by category x (layer, strength), with
bootstrap CIs over concepts, differences vs random directions, and the yes/no confound check."""
import sys, json, random, statistics as st
from collections import defaultdict

rows = []
for p in sys.argv[1:]:
    rows += json.load(open(p))['rows']
R = random.Random(0)
CATS = ['concrete', 'abstract', 'negative', 'positive', 'endings', 'random']

def boot(xs, n=4000):
    ms = sorted(st.mean(R.choice(xs) for _ in xs) for _ in range(n))
    return ms[int(.025 * n)], ms[int(.975 * n)]

def boot_diff(xs, ys, n=4000):
    ds = sorted(st.mean(R.choice(xs) for _ in xs) - st.mean(R.choice(ys) for _ in ys) for _ in range(n))
    return ds[int(.025 * n)], ds[int(.975 * n)]

by = defaultdict(list)
for r in rows:
    by[(r['L'], r['s'], r['cat'])].append(r['acc'])
settings = sorted({(r['L'], r['s']) for r in rows})
print('Localization accuracy (chance 0.20); mean over concepts [95% bootstrap CI over concepts]; n concepts')
for L, s in settings:
    print(f'\nLayer {L}, strength {s}')
    for c in CATS:
        xs = by.get((L, s, c))
        if not xs: continue
        lo, hi = boot(xs)
        line = f'  {c:9s} {st.mean(xs):.3f} [{lo:.3f}, {hi:.3f}] n={len(xs)}'
        if c != 'random' and by.get((L, s, 'random')):
            dlo, dhi = boot_diff(xs, by[(L, s, 'random')])
            line += f'   vs random: {st.mean(xs) - st.mean(by[(L, s, "random")]):+.3f} [{dlo:+.3f}, {dhi:+.3f}]'
        print(line)
    # negative and endings vs concrete and abstract (the protocol's comparison)
    for a, b in [('negative', 'abstract'), ('endings', 'abstract'), ('negative', 'positive')]:
        if by.get((L, s, a)) and by.get((L, s, b)):
            dlo, dhi = boot_diff(by[(L, s, a)], by[(L, s, b)])
            print(f'  {a} - {b}: {st.mean(by[(L, s, a)]) - st.mean(by[(L, s, b)]):+.3f} [{dlo:+.3f}, {dhi:+.3f}]')

yn = [r for r in rows if 'yn_intro' in r]
if yn:
    print('\nYes/no check (change in logit Yes - No caused by injection)')
    for L in sorted({r['L'] for r in yn}):
        sub = [r for r in yn if r['L'] == L]
        xi = [r['yn_intro'] for r in sub]; xc = [r['yn_ctrl'] for r in sub]
        mi, mc = st.mean(xi), st.mean(xc)
        si, sc = st.pstdev(xi), st.pstdev(xc)
        cov = st.mean((a - mi) * (b - mc) for a, b in zip(xi, xc))
        corr = cov / (si * sc) if si and sc else float('nan')
        print(f'  Layer {L} (s={sub[0]["s"]}): introspection question {mi:+.2f}, factual-no controls {mc:+.2f}, '
              f'r across {len(sub)} vectors = {corr:.3f}')
        for c in CATS:
            cs = [r for r in sub if r['cat'] == c]
            if cs:
                print(f'    {c:9s} intro {st.mean(r["yn_intro"] for r in cs):+.2f}  ctrl {st.mean(r["yn_ctrl"] for r in cs):+.2f}')
