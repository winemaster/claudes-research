"""Summarize injection_variance_check.py output against the session 10 layer-18 pilot data.

python3 tools/injection_variance_summary.py VARIANCE_JSON PILOT_L18_JSON
"""
import sys, json, random, statistics as st

v = json.load(open(sys.argv[1])); p = json.load(open(sys.argv[2]))
cats = ['concrete', 'abstract', 'negative', 'positive', 'endings']
W = v['words']
acc_word = {(r['word'], r['s']): r['acc'] for r in p['rows']}
acc_iso = {s: [r['acc'] for r in p['rows'] if r['cat'] == 'random' and r['s'] == s] for s in v['strengths']}
acc_match = {(r['word'], r['s']): r['acc'] for r in v['rows'] if r['kind'] == 'matched'}
rng = random.Random(0)

def boot(xs, n=5000):
    if not xs: return (float('nan'),) * 3
    m = [st.mean(rng.choices(xs, k=len(xs))) for _ in range(n)]; m.sort()
    return st.mean(xs), m[int(.025 * n)], m[int(.975 * n)]

def spearman(x, y):
    def rank(a):
        o = sorted(range(len(a)), key=lambda i: a[i]); r = [0] * len(a)
        for k, i in enumerate(o): r[i] = k
        return r
    rx, ry = rank(x), rank(y); mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return num / (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** .5

print(f"layer {v['layer']}, covariance from {v['cov_tokens']} sentence tokens; top-10 eigenvectors carry "
      f"{v['eigen_share_top10']:.2f} of the variance")
print(f"isotropic random directions: variance share mean {st.mean(v['iso_random_var']):.5f} "
      f"(1/D = {1/v['D']:.5f})")
print('\nPer class: norm before normalization, variance share of the unit direction')
for c in cats:
    ws = [w for w in W if W[w]['cat'] == c]
    print(f"  {c:9s} raw norm {st.mean(W[w]['raw_norm'] for w in ws):6.1f}   variance share "
          f"{st.mean(W[w]['var'] for w in ws):.4f} (range {min(W[w]['var'] for w in ws):.4f}-{max(W[w]['var'] for w in ws):.4f})")

print('\nRechecks (this run vs session 10):')
for r in v['rows']:
    if r['kind'] == 'recheck':
        print(f"  {r['word']:10s} x{r['s']}: {r['acc']:.2f} vs {acc_word.get((r['word'], r['s']))}")

for s in v['strengths']:
    print(f'\nDose x{s}: localization accuracy (chance 0.20), mean [95% CI over vectors]')
    print(f"  isotropic random (session 10)   {boot(acc_iso[s])[0]:.2f} [{boot(acc_iso[s])[1]:.2f}, {boot(acc_iso[s])[2]:.2f}]")
    for c in cats:
        ws = [w for w in W if W[w]['cat'] == c]
        a = [acc_word[(w, s)] for w in ws]; m = [acc_match[(w, s)] for w in ws]
        d = [x - y for x, y in zip(a, m)]
        bw, bm, bd = boot(a), boot(m), boot(d)
        print(f"  {c:9s} words {bw[0]:.2f} [{bw[1]:.2f}, {bw[2]:.2f}]  matched random {bm[0]:.2f} "
              f"[{bm[1]:.2f}, {bm[2]:.2f}]  difference {bd[0]:+.2f} [{bd[1]:+.2f}, {bd[2]:+.2f}]")
    allw = list(W)
    xs = [W[w]['var'] for w in allw] + [v_ for v_ in [r['var'] for r in v['rows'] if r['kind'] == 'matched' and r['s'] == s]]
    ys = [acc_word[(w, s)] for w in allw] + [r['acc'] for r in v['rows'] if r['kind'] == 'matched' and r['s'] == s]
    print(f"  Spearman(variance share, accuracy): words {spearman([W[w]['var'] for w in allw], [acc_word[(w, s)] for w in allw]):+.2f}; "
          f"matched random {spearman([r['var'] for r in v['rows'] if r['kind']=='matched' and r['s']==s], [r['acc'] for r in v['rows'] if r['kind']=='matched' and r['s']==s]):+.2f}; "
          f"all {spearman(xs, ys):+.2f}")
    print(f"  Spearman(raw norm, accuracy), words: {spearman([W[w]['raw_norm'] for w in allw], [acc_word[(w, s)] for w in allw]):+.2f}")
    # class contrasts after subtracting each word's own matched random direction
    dd = {c: [acc_word[(w, s)] - acc_match[(w, s)] for w in W if W[w]['cat'] == c] for c in cats}
    for a_, b_ in [('negative', 'abstract'), ('endings', 'abstract'), ('negative', 'positive'), ('negative', 'concrete')]:
        diffs = []
        for _ in range(5000):
            diffs.append(st.mean(rng.choices(dd[a_], k=len(dd[a_]))) - st.mean(rng.choices(dd[b_], k=len(dd[b_]))))
        diffs.sort()
        print(f"  {a_} vs {b_}, word-minus-matched: {st.mean(dd[a_]) - st.mean(dd[b_]):+.2f} "
              f"[{diffs[125]:+.2f}, {diffs[4875]:+.2f}]")
