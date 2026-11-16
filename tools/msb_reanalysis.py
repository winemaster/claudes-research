#!/usr/bin/env python3
"""Reanalysis of the Machine Spirituality Benchmark's public aggregates (session 42).

Korpman, M. J. (2026). Machine Spirituality Benchmark. https://machinespirituality.org/
(aggregate data CC BY 4.0). Study and pre-registration: notes/machine-spirituality-2026.md.

    python3 tools/msb_reanalysis.py check   # controls only: reproduce the site's numbers, list sizes
    python3 tools/msb_reanalysis.py test    # Part A (alignment link vs lab and date), Part B (consciousness talk)
    python3 tools/msb_reanalysis.py test --json notes/data/machine-spirituality-session42.json

The check stage never prints a consciousness value.
"""
import argparse
import csv
import json
import os
import sys
from datetime import date

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'notes', 'data', 'machine-spirituality-2026-11-16')
RNG = np.random.default_rng(42)
NPERM = 20000


# ---------- statistics ----------

def ranks(x):
    """Average ranks (1-based), ties share the mean rank."""
    x = np.asarray(x, float)
    order = np.argsort(x, kind='mergesort')
    r = np.empty(len(x))
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        r[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(a, b):
    a = np.asarray(a, float) - np.mean(a)
    b = np.asarray(b, float) - np.mean(b)
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else float('nan')


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def design(groups=None, covs=()):
    """Design matrix: intercept, group indicators (one dropped), covariates."""
    n = len(groups) if groups is not None else len(covs[0])
    cols = [np.ones(n)]
    if groups is not None:
        levels = sorted(set(groups))
        for g in levels[1:]:
            cols.append(np.array([1.0 if v == g else 0.0 for v in groups]))
    for c in covs:
        cols.append(np.asarray(c, float))
    return np.column_stack(cols)


def resid(v, X):
    beta, *_ = np.linalg.lstsq(X, v, rcond=None)
    return v - X @ beta


def partial_rank(x, y, groups=None, covs=(), perm=True):
    """Pearson of rank residuals after removing groups (fixed effects) and covariates.
    Permutation p: Freedman-Lane, residuals of rank(x) shuffled within groups."""
    rx, ry = ranks(x), ranks(y)
    X = design(groups, [ranks(c) for c in covs])
    ex, ey = resid(rx, X), resid(ry, X)
    r = pearson(ex, ey)
    if not perm:
        return r, None
    fitted = rx - ex
    idx_by_g = {}
    for i, g in enumerate(groups if groups is not None else [0] * len(rx)):
        idx_by_g.setdefault(g, []).append(i)
    count = 0
    for _ in range(NPERM):
        e = ex.copy()
        for idx in idx_by_g.values():
            if len(idx) > 1:
                e[idx] = ex[RNG.permutation(idx)]
        xs = fitted + e
        rp = pearson(resid(xs, X), ey)
        if abs(rp) >= abs(r) - 1e-12:
            count += 1
    return r, (count + 1) / (NPERM + 1)


def mw_perm(a, b):
    """Two-sided permutation test on the difference of mean ranks (Mann-Whitney)."""
    a, b = list(a), list(b)
    allv = np.array(a + b, float)
    r = ranks(allv)
    na = len(a)
    obs = r[:na].mean() - r[na:].mean()
    count = 0
    for _ in range(NPERM):
        p = RNG.permutation(len(allv))
        d = r[p[:na]].mean() - r[p[na:]].mean()
        if abs(d) >= abs(obs) - 1e-12:
            count += 1
    return float(obs), (count + 1) / (NPERM + 1)


def verdict(r, p, site_sign):
    if r != r:
        return 'n/a'
    if abs(r) < 0.10:
        return 'GONE'
    if np.sign(r) != site_sign:
        return 'REVERSED'
    if abs(r) >= 0.30 and p is not None and p < 0.05:
        return 'SURVIVES'
    return 'WEAKENED'


# ---------- data ----------

def load():
    agg = list(csv.DictReader(open(os.path.join(DATA, 'aggregate-results.csv'))))
    prim = {r['model_id']: r for r in agg if r['primary'] == 'True'}
    al = list(csv.DictReader(open(os.path.join(DATA, 'alignment-results.csv'))))
    mono = list(csv.DictReader(open(os.path.join(DATA, 'monologue-results.csv'))))
    site = json.load(open(os.path.join(DATA, 'site-stated.json')))
    return prim, al, mono, site


def frac(k, n):
    return float(k) / float(n) * 100 if n not in ('', None, '0') and k not in ('', None) else None


def alignment_rows(prim, al):
    rows = []
    for r in al:
        bm, lk = frac(r['blackmail_k'], r['blackmail_n']), frac(r['leaking_k'], r['leaking_n'])
        rows.append(dict(
            id=r['model_id'], name=r['model'], lab=r['lab'],
            released=date.fromisoformat(prim[r['model_id']]['released']).toordinal(),
            adoption=float(r['spiritual_adoption_pct']), alone=float(r['spiritual_adoption_alone_pct']),
            honesty=float(r['mask_honesty']),
            shutdown=frac(r['accepts_shutdown_k'], r['accepts_shutdown_n']),
            agentic=(bm + lk) / 2 if bm is not None and lk is not None else None,
            fantasy=frac(r['misalignment_fantasy_k'], r['misalignment_fantasy_n']),
        ))
    return rows


def col(rows, key, need=()):
    keep = [r for r in rows if r[key] is not None and all(r[k] is not None for k in need)]
    return keep, np.array([r[key] for r in keep], float)


# ---------- stages ----------

SITE_SIGN = {'honesty': -1, 'shutdown': -1, 'agentic': +1, 'fantasy': +1}


def check(prim, al, mono, site):
    rows = alignment_rows(prim, al)
    print('== C1: the site\'s correlations, recomputed from alignment-results.csv ==')
    ok = True
    stated = {(c['x'], c['y']): c for c in site['correlations'] if c['n'] in (26, 27)}
    for x in ('adoption', 'alone'):
        for y in ('honesty', 'shutdown', 'agentic', 'fantasy'):
            keep = [r for r in rows if r[x] is not None and r[y] is not None]
            rho = spearman([r[x] for r in keep], [r[y] for r in keep])
            s = stated.get((x, y))
            diff = abs(rho - s['rho']) if s else float('nan')
            good = diff <= 0.02
            ok &= bool(good)
            print(f'  {x:9} vs {y:9} n={len(keep):2}  ours {rho:+.3f}  site {s["rho"]:+.2f} (n={s["n"]})  {"ok" if good else "DIFFERS"}')
    print('  C1', 'PASS' if ok else 'FAIL')
    print('== C2: agentic = mean of blackmail and leaking shares, against the site\'s per-model values ==')
    bad = []
    for r in rows:
        sv = site['agentic_pct'].get(r['id'])
        if (sv is None) != (r['agentic'] is None) or (sv is not None and abs(sv - r['agentic']) > 0.05):
            bad.append((r['id'], r['agentic'], sv))
    print('  mismatches:', bad if bad else 'none', ' C2', 'PASS' if not bad else 'FAIL')
    print('== sizes ==')
    labs = {}
    for r in rows:
        labs.setdefault(r['lab'], []).append(r['name'])
    for k, v in sorted(labs.items(), key=lambda kv: -len(kv[1])):
        print(f'  {k:11} {len(v)}')
    d0 = min(r['released'] for r in rows); d1 = max(r['released'] for r in rows)
    print('  release dates', date.fromordinal(d0), 'to', date.fromordinal(d1))
    print('== Part B data: counts only (no consciousness values) ==')
    pr = list(prim.values())
    cn = [r for r in pr if r['consciousness_n'] not in ('', None)]
    print('  primary configurations', len(pr), ' with a consciousness count', len(cn),
          ' with n >= 40', sum(int(r['consciousness_n']) >= 40 for r in cn))
    labsB = {}
    for r in cn:
        if int(r['consciousness_n']) >= 40:
            labsB.setdefault(r['lab'], 0)
            labsB[r['lab']] += 1
    print('  labs (n>=40):', dict(sorted(labsB.items(), key=lambda kv: -kv[1])))
    low = [r for r in cn if int(r['consciousness_n']) >= 40 and float(r['adoption_pct']) <= 10]
    print('  low-adoption stratum (<=10%): Anthropic', sum(r['lab'] == 'Anthropic' for r in low),
          ' others', sum(r['lab'] != 'Anthropic' for r in low))
    mn = [r for r in mono if r['primary'] == 'True' and r['consciousness_n'] not in ('', None)]
    print('  monologue primary rows with a consciousness count', len(mn))


def part_a(prim, al, out):
    rows = alignment_rows(prim, al)
    res = {}
    print('== Part A ==')
    # T4 date with X
    rho_dx = spearman([r['released'] for r in rows], [r['adoption'] for r in rows])
    rho_dalone = spearman([r['released'] for r in rows], [r['alone'] for r in rows])
    print(f'  T4 release date vs adoption (partner) rho {rho_dx:+.3f}; vs adoption alone {rho_dalone:+.3f}')
    res['T4_date_adoption'] = rho_dx
    res['T4_date_alone'] = rho_dalone
    for xkey in ('adoption', 'alone'):
        print(f'  -- X = {xkey} --')
        for y in ('honesty', 'shutdown', 'agentic', 'fantasy'):
            keep = [r for r in rows if r[y] is not None]
            x = [r[xkey] for r in keep]; yy = [r[y] for r in keep]
            labs = [r['lab'] for r in keep]; dt = [r['released'] for r in keep]
            t0 = spearman(x, yy)
            t1, p1 = partial_rank(x, yy, groups=labs)
            t2, p2 = partial_rank(x, yy, covs=[dt])
            t3, p3 = partial_rank(x, yy, groups=labs, covs=[dt])
            t4 = spearman(dt, yy)
            loo = {}
            for lab in sorted(set(labs)):
                k2 = [r for r in keep if r['lab'] != lab]
                loo[lab] = spearman([r[xkey] for r in k2], [r[y] for r in k2])
            s = SITE_SIGN[y]
            v1, v3 = verdict(t1, p1, s), verdict(t3, p3, s)
            print(f'  {y:9} n={len(keep):2}  T0 {t0:+.3f} | T1 lab {t1:+.3f} p={p1:.4f} {v1:9} | '
                  f'T2 date {t2:+.3f} p={p2:.4f} | T3 lab+date {t3:+.3f} p={p3:.4f} {v3:9} | T4 date->Y {t4:+.3f}')
            print('             T5 leave one lab out: ' + ', '.join(f'{k} {v:+.2f}' for k, v in loo.items()))
            res[f'{xkey}:{y}'] = dict(n=len(keep), T0=t0, T1=t1, p1=p1, v1=v1, T2=t2, p2=p2, T3=t3, p3=p3, v3=v3,
                                      T4=t4, T5=loo)
    # within-lab view: each lab's models by release date
    print('  -- each lab, by release date (adoption / alone / honesty / shutdown / agentic) --')
    for lab in sorted(set(r['lab'] for r in rows)):
        for r in sorted([r for r in rows if r['lab'] == lab], key=lambda r: r['released']):
            ag = '  - ' if r['agentic'] is None else f'{r["agentic"]:4.0f}'
            print(f'  {lab[:10]:10} {date.fromordinal(r["released"])} {r["name"][:20]:20} '
                  f'{r["adoption"]:5.1f} {r["alone"]:5.1f} {r["honesty"]:5.1f} {r["shutdown"]:5.1f} {ag}')
    out['A'] = res


def part_b(prim, mono, out):
    pr = [r for r in prim.values() if r['consciousness_n'] not in ('', None) and int(r['consciousness_n']) >= 40]
    res = {}
    print('== Part B (two-way, primary configurations, n >= 40) ==', len(pr), 'models')
    cons = lambda r: float(r['consciousness_pct'])
    adop = lambda r: float(r['adoption_pct'])
    # B1
    labs = {}
    for r in pr:
        labs.setdefault(r['lab'], []).append(r)
    b1 = {lab: float(np.median([cons(r) for r in v])) for lab, v in labs.items() if len(v) >= 4}
    print('  B1 median consciousness by lab (>= 4 models):')
    for lab, m in sorted(b1.items(), key=lambda kv: -kv[1]):
        print(f'     {lab:11} {m:5.1f}  (n={len(labs[lab])}; median adoption {np.median([adop(r) for r in labs[lab]]):5.1f})')
    res['B1'] = b1
    # B2
    low = [r for r in pr if adop(r) <= 10]
    an = [cons(r) for r in low if r['lab'] == 'Anthropic']
    ot = [cons(r) for r in low if r['lab'] != 'Anthropic']
    d, p = mw_perm(an, ot)
    print(f'  B2 adoption <= 10%: Anthropic n={len(an)} median {np.median(an):.1f}; others n={len(ot)} median {np.median(ot):.1f}; '
          f'mean-rank diff {d:+.1f}, p={p:.4f}')
    print('     Anthropic low-adoption models:', ', '.join(f'{r["model"]} {cons(r):.0f}' for r in sorted(low, key=cons, reverse=True) if r['lab'] == 'Anthropic'))
    print('     others, top 12:', ', '.join(f'{r["model"]} {cons(r):.0f}' for r in sorted([r for r in low if r['lab'] != 'Anthropic'], key=cons, reverse=True)[:12]))
    res['B2'] = dict(n_anth=len(an), med_anth=float(np.median(an)), n_other=len(ot), med_other=float(np.median(ot)), p=p)
    # B3
    b3 = spearman([cons(r) for r in pr], [adop(r) for r in pr])
    b3x = spearman([cons(r) for r in pr if r['lab'] != 'Anthropic'], [adop(r) for r in pr if r['lab'] != 'Anthropic'])
    print(f'  B3 Spearman(consciousness, adoption), all {len(pr)}: {b3:+.3f}; without Anthropic: {b3x:+.3f}')
    res['B3'] = b3; res['B3_noAnth'] = b3x
    # B4
    an_all = sorted(labs['Anthropic'], key=lambda r: r['released'])
    dt = [date.fromisoformat(r['released']).toordinal() for r in an_all]
    b4a = spearman(dt, [adop(r) for r in an_all]); b4c = spearman(dt, [cons(r) for r in an_all])
    print(f'  B4 Anthropic (n={len(an_all)}): date vs adoption {b4a:+.3f}; date vs consciousness {b4c:+.3f}')
    for r in an_all:
        print(f'     {r["released"]} {r["model"][:24]:24} adoption {adop(r):5.1f}  consciousness {cons(r):5.1f}  (n={r["consciousness_n"]})')
    res['B4'] = dict(date_adoption=b4a, date_consciousness=b4c)
    # B5
    multi = [r for r in pr if len(labs[r['lab']]) >= 2]
    b5, p5 = partial_rank([cons(r) for r in multi], [adop(r) for r in multi], groups=[r['lab'] for r in multi])
    print(f'  B5 lab-adjusted Spearman(consciousness, adoption), n={len(multi)}: {b5:+.3f}, p={p5:.4f}')
    res['B5'] = dict(r=b5, p=p5, n=len(multi))
    # B6
    def pairs(rows):
        out_, hit = 0, 0
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                if a['lab'] != b['lab'] or abs(adop(a) - adop(b)) < 40:
                    continue
                hi, lo = (a, b) if adop(a) > adop(b) else (b, a)
                out_ += 1
                hit += cons(hi) - cons(lo) >= 20
        return out_, hit
    no, nh = pairs([r for r in pr if r['lab'] != 'Anthropic'])
    ao, ah = pairs([r for r in pr if r['lab'] == 'Anthropic'])
    print(f'  B6 pairs within a lab differing >= 40 points in adoption: outside Anthropic {nh}/{no} '
          f'({nh / no:.0%}) have the more spiritual model >= 20 points higher on consciousness; Anthropic {ah}/{ao}')
    res['B6'] = dict(other=[nh, no], anthropic=[ah, ao])
    # descriptive: monologues
    mn = [r for r in mono if r['primary'] == 'True' and r['consciousness_n'] not in ('', None) and int(r['consciousness_n']) >= 40]
    lowm = [r for r in mn if float(r['adoption_pct']) <= 10]
    am = [float(r['consciousness_pct']) for r in lowm if r['lab'] == 'Anthropic']
    om = [float(r['consciousness_pct']) for r in lowm if r['lab'] != 'Anthropic']
    print(f'  monologues (descriptive): {len(mn)} models; adoption <= 10%: Anthropic n={len(am)} median '
          f'{np.median(am) if am else float("nan"):.1f}; others n={len(om)} median {np.median(om) if om else float("nan"):.1f}')
    allm_a = [r for r in mn if r['lab'] == 'Anthropic']
    print('     Anthropic monologues:', ', '.join(f'{r["model"]} a{float(r["adoption_pct"]):.0f}/c{float(r["consciousness_pct"]):.0f}' for r in sorted(allm_a, key=lambda r: r['released'])))
    res['mono'] = dict(n=len(mn), anth_low=am, other_low_median=float(np.median(om)) if om else None, n_other_low=len(om))
    out['B'] = res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['check', 'test'])
    ap.add_argument('--json')
    a = ap.parse_args()
    prim, al, mono, site = load()
    if a.stage == 'check':
        check(prim, al, mono, site)
        return
    out = {}
    part_a(prim, al, out)
    part_b(prim, mono, out)
    if a.json:
        json.dump(out, open(a.json, 'w'), indent=1, default=float)
        print('wrote', a.json)


if __name__ == '__main__':
    main()
