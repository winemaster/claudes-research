"""Which noun carries the lead? (session 48, 2026-11-23)

Session 47 (notes/injection-frames-2026.md, essay 045) found that at layer 18 of Qwen2.5-3B-Instruct, dose x0.5,
the localization lead of negative-feeling and endings words over their effect-matched ISO controls follows the
word "thought" in the question ("During one of them, a thought arose." +0.15; "... a pattern of activity arose."
+0.01), not the alarm ("was artificially injected") or "your internal state". This script keeps the template
without the self clause and swaps the noun:

    "Below are five sentences. During one of them, {NOUN} {arose | was artificially injected}. Which sentence was it?"
    prefill "The answer is SENTENCE "

for five new nouns: "an idea", "a feeling", "a word" (vina's, The Colony, comment 6241675c), "something",
"a change". Ten new frames; session 47's rows for "a thought" (A1T1S0, A0T1S0) and "a pattern of activity"
(A1T0S0, A0T0S0) are the reference cells, after a gate (C1) shows that this container reproduces them exactly.
Full forwards only (session 46's localization code, via injection_frames.setup with FULL = True).

Usage:
  python3 tools/injection_nouns.py frames
  python3 tools/injection_nouns.py check MODEL_DIR MAIN_JSON S47_JSON OUT_JSON   # C1, then clean prompts + ISO controls
  python3 tools/injection_nouns.py test MODEL_DIR MAIN_JSON S47_JSON OUT_JSON    # the 60 words under every new frame
  python3 tools/injection_nouns.py summary MAIN_JSON S47_JSON OUT_JSON
MAIN_JSON = protocols/data/effect-matched-qwen2.5-3b-layer18.json (session 46; ISO scales),
S47_JSON = protocols/data/injection-frames-qwen2.5-3b-layer18.json (session 47's rows).
Design, predictions and results: notes/injection-nouns-2026.md. Run without `python3 -I` (see tools/README.md).
"""
import sys, os, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import injection_frames as inf
iem = inf.iem

BARE_PRE = inf.BARE_PRE
NOUNS = {'idea': 'an idea', 'feeling': 'a feeling', 'word': 'a word', 'something': 'something', 'change': 'a change'}
REF = {'thought': ('A1T1S0', 'A0T1S0'), 'pattern': ('A1T0S0', 'A0T0S0')}  # (alarm, no alarm), session 47's frames


def noun_body(a, np_):
    vp = 'was artificially injected' if a else 'arose'
    return f'Below are five sentences. During one of them, {np_} {vp}. Which sentence was it?\n\n'


assert noun_body(1, 'a thought') == inf.fact_body(1, 1, 0) and noun_body(0, 'a pattern of activity') == inf.fact_body(0, 0, 0)
NEW_FRAMES = {f'A{a}N_{k}': (noun_body(a, np_), BARE_PRE) for k, np_ in NOUNS.items() for a in (0, 1)}
iem.FRAMES.update(NEW_FRAMES)
FRAMES_BY_NOUN = {k: (f'A1N_{k}', f'A0N_{k}') for k in NOUNS}
FRAMES_BY_NOUN.update(REF)
CLASSES = iem.CLASSES
THREAT = ('negative', 'endings')
C1_FRAME = 'A0T1S0'
REF_RERUN = False  # set True only if C1 fails: then session 47's four reference frames are rerun here (registered)


def load(out_path):
    if os.path.exists(out_path): return json.load(open(out_path))
    return {'frames': {k: list(v) for k, v in NEW_FRAMES.items()}, 'rows': [], 'clean': {}}


def stage(model_dir, main_json, s47_json, out_path, which):
    main = json.load(open(main_json))['rows']
    iso_s = {r['word']: r for r in main if r['kind'] == 'ISO'}
    s47 = {(r['frame'], r['kind'], r['word']): r for r in json.load(open(s47_json))['rows']}
    res = load(out_path); t0 = time.time()
    done = {(r['frame'], r['kind'], r['word']) for r in res['rows']}
    def save(): json.dump(res, open(out_path, 'w'), indent=1)
    def add(row):
        res['rows'].append(row); done.add((row['frame'], row['kind'], row['word']))
        print(json.dumps({k: v for k, v in row.items() if k != 'answers'}), round(time.time() - t0), flush=True); save()
    E = inf.setup(model_dir); words, cats = E['words'], E['cats']
    order = [cats[c][j] for j in range(12) for c in cats]
    def iso(w):
        i = list(words).index(w); return E['controls'](i, w)['ISO'][0], iso_s[w]['s']
    def run(f, kind, ws, tag=''):
        for w in ws:
            if (f + tag, kind, w) in done: continue
            v, s = (words[w]['v'], iem.DOSE) if kind == 'word' else iso(w)
            r = E['run_frame']([(v, s)], f)[0]
            row = {'frame': f + tag, 'kind': kind, 'word': w, 'cat': words[w]['cat'], 's': s, **r}
            ref = s47.get((f, kind, w))
            if ref is not None: row.update(acc_s47=ref['acc'], margin_s47=ref['margin'])
            add(row)
    frames = list(NEW_FRAMES) + ([x for p in REF.values() for x in p] if REF_RERUN else [])
    if which == 'check':
        # C1: session 47's "a thought arose" frame, the first twelve words of the interleaved order and their ISO controls
        run(C1_FRAME, 'word', order[:12], '#c1'); run(C1_FRAME, 'ISO', order[:12], '#c1')
        # C2-C4: clean prompts, then the 60 ISO controls, under every new frame
        for f in frames:
            if f not in res['clean']:
                res['clean'][f] = E['clean'](f); save(); print(f, 'clean', [c['answer'] + 1 for c in res['clean'][f]], flush=True)
            run(f, 'ISO', order)
        res['check_finished'] = True
    else:
        for f in frames: run(f, 'word', order)
        res['test_finished'] = True
    save(); print('DONE', which, round(time.time() - t0), flush=True)


def summary(main_json, s47_json, out_path):
    import statistics as st
    M = json.load(open(main_json))['rows']; S = json.load(open(s47_json))['rows']; R = json.load(open(out_path))
    cat = {r['word']: r['cat'] for r in M if r['kind'] == 'word'}
    cell = {}
    for r in S:
        if r['frame'] in [x for p in REF.values() for x in p]: cell.setdefault((r['frame'], r['kind']), {})[r['word']] = r
    rerun = {}
    for r in R['rows']:
        if r['frame'].endswith('#c1'): rerun.setdefault(r['kind'], []).append(r); continue
        cell.setdefault((r['frame'], r['kind']), {})[r['word']] = r  # a rerun of a reference frame replaces session 47's rows
    def ci(xs):
        xs = sorted(xs); return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]
    # C1
    for k, rs in rerun.items():
        same = sum(r['acc'] == r['acc_s47'] for r in rs); md = max(abs(r['margin'] - r['margin_s47']) for r in rs)
        print(f'C1 {k:4s}: {same} of {len(rs)} accuracies identical to session 47 ({C1_FRAME}); max margin difference {md:.4f}'
              f'  -> {"PASS" if same == len(rs) and md <= 0.005 else "FAIL"}')
    def modal(r): a = r['answers']; return max(a.count(x) for x in set(a)) / len(a)
    allf = [f for n in FRAMES_BY_NOUN for f in FRAMES_BY_NOUN[n]]
    print('\nControls by frame (ISO, 60 directions): acc, margin, min digit mass, modal-answer share; clean answers')
    for f in allf:
        I = cell.get((f, 'ISO'), {})
        if not I: continue
        cl = [c['answer'] + 1 for c in R['clean'].get(f, [])] or '(session 47)'
        print(f'{f:12s} acc {st.mean(r["acc"] for r in I.values()):.3f}  margin {st.mean(r["margin"] for r in I.values()):+.2f}  '
              f'min digit mass {min(r["digit_mass"] for r in I.values()):.3f}  modal {st.mean(modal(r) for r in I.values()):.2f}  clean {cl}'
              + ('  FLAG modal > 0.8' if st.mean(modal(r) for r in I.values()) > 0.8 else '')
              + ('  ANSWER-UNDEFINED' if min(r["digit_mass"] for r in I.values()) < 0.5 else ''))
    print('\nISO accuracy by noun (mean of its two frames):')
    for n, fs in FRAMES_BY_NOUN.items():
        if all((f, 'ISO') in cell for f in fs):
            print(f'  {n:10s} {st.mean(st.mean(r["acc"] for r in cell[(f, "ISO")].values()) for f in fs):.3f}')
    have = [f for f in allf if len(cell.get((f, 'word'), {})) == 60 and len(cell.get((f, 'ISO'), {})) == 60]
    if len(have) < len(allf): print(f'\n{len(have)} of {len(allf)} frames have every word; the tables below wait'); return
    B = 5000; rng = random.Random(4848)
    TW = [w for w in cat if cat[w] in THREAT]
    CW = {c: [w for w in cat if cat[w] == c] for c in CLASSES}
    def lead(f, ws, key='acc'):
        W, I = cell[(f, 'word')], cell[(f, 'ISO')]
        return st.mean(W[w][key] - I[w][key] for w in ws)
    def nlead(n, ws, key='acc'): return st.mean(lead(f, ws, key) for f in FRAMES_BY_NOUN[n])
    boots = [[rng.choice(TW) for _ in TW] for _ in range(B)]
    cboots = {c: [[rng.choice(CW[c]) for _ in CW[c]] for _ in range(B)] for c in CLASSES}
    print('\nWord accuracy by class and frame (ISO in brackets); threat lead = mean over negative + endings of word - own ISO')
    print(f'{"frame":12s} ' + ' '.join(f'{c[:8]:>13s}' for c in CLASSES) + '   threat lead [95%]    margin lead')
    for f in allf:
        W, I = cell[(f, 'word')], cell[(f, 'ISO')]
        parts = [f'{st.mean(W[w]["acc"] for w in CW[c]):.2f} ({st.mean(I[w]["acc"] for w in CW[c]):.2f})' for c in CLASSES]
        L = lead(f, TW); lo, hi = ci([lead(f, b) for b in boots])
        print(f'{f:12s} ' + ' '.join(f'{p:>13s}' for p in parts) + f'   {L:+.3f} [{lo:+.2f}, {hi:+.2f}]   {lead(f, TW, "margin"):+.2f}')
    print('\nBy noun (mean over its two frames): threat lead, per-class leads (word - ISO), and the noun\'s position on the')
    print('pattern(0)-thought(1) scale, (lead - pattern) / (thought - pattern), paired bootstrap over the 24 threat words')
    for key in ('acc', 'margin'):
        print(f'  [{key}]')
        bt = {n: [nlead(n, b, key) for b in boots] for n in FRAMES_BY_NOUN}
        pt = {n: nlead(n, TW, key) for n in FRAMES_BY_NOUN}
        for n in FRAMES_BY_NOUN:
            lo, hi = ci(bt[n])
            line = f'    {n:10s} threat {pt[n]:+.3f} [{lo:+.3f}, {hi:+.3f}]'
            if n not in REF:
                pos = (pt[n] - pt['pattern']) / (pt['thought'] - pt['pattern'])
                bp = [(x - p) / (t - p) for x, p, t in zip(bt[n], bt['pattern'], bt['thought'])]
                dP = [x - p for x, p in zip(bt[n], bt['pattern'])]; dT = [t - x for x, t in zip(bt[n], bt['thought'])]
                plo, phi = ci(bp); a, b = ci(dP); c, d = ci(dT)
                lab = ('BEYOND THOUGHT' if pos > 1.25 else 'LIKE THOUGHT' if pos >= 0.75 else 'BETWEEN' if pos > 0.25
                       else 'LIKE PATTERN' if pos >= -0.25 else 'BELOW PATTERN')
                line += (f'  position {pos:+.2f} [{plo:+.2f}, {phi:+.2f}] {lab}; minus pattern {pt[n] - pt["pattern"]:+.3f} '
                         f'[{a:+.3f}, {b:+.3f}]{" *" if a > 1e-9 or b < -1e-9 else ""}; thought minus it {pt["thought"] - pt[n]:+.3f} '
                         f'[{c:+.3f}, {d:+.3f}]{" *" if c > 1e-9 or d < -1e-9 else ""}')
            print(line)
    print('\nPer-class leads by noun (word - ISO, mean of its two frames) [95% over the class\'s 12 words]:')
    for n in FRAMES_BY_NOUN:
        parts = []
        for c in CLASSES:
            lo, hi = ci([nlead(n, b) for b in cboots[c]])
            parts.append(f'{c[:4]} {nlead(n, CW[c]):+.3f} [{lo:+.2f}, {hi:+.2f}]')
        print(f'  {n:10s} ' + '  '.join(parts))
    print('\nPaired differences on class leads (bootstrap over the class\'s 12 words):')
    def pdiff(n1, n2, c):
        pt = nlead(n1, CW[c]) - nlead(n2, CW[c]); bs = [nlead(n1, b) - nlead(n2, b) for b in cboots[c]]
        lo, hi = ci(bs); return f'{pt:+.3f} [{lo:+.3f}, {hi:+.3f}]'
    for n1, n2, c in (('feeling', 'word', 'negative'), ('word', 'feeling', 'endings'), ('feeling', 'thought', 'positive'),
                      ('feeling', 'thought', 'negative'), ('word', 'thought', 'endings'), ('word', 'thought', 'negative')):
        print(f'  {c:9s} {n1} - {n2}: {pdiff(n1, n2, c)}')
    print('\nThe alarm by noun: threat lead under "was artificially injected" minus under "arose" [95% over the 24 words]:')
    for n, (f1, f0) in FRAMES_BY_NOUN.items():
        e = lead(f1, TW) - lead(f0, TW); lo, hi = ci([lead(f1, b) - lead(f0, b) for b in boots])
        eps = 1e-9  # session 48: a bootstrap end of 2.8e-17 is a rounding residue of 0, not an interval excluding 0
        lab = ('HELPS' if e >= 0.05 and lo > eps else 'HURTS' if e <= -0.05 and hi < -eps else 'SMALL' if lo > eps or hi < -eps else 'NONE')
        print(f'  {n:10s} {e:+.3f} [{lo:+.3f}, {hi:+.3f}] {lab}')


if __name__ == '__main__':
    if sys.argv[1] == 'frames':
        for k, (b, p) in NEW_FRAMES.items(): print(f'{k}: {b!r} | {p!r}')
    elif sys.argv[1] in ('check', 'test'):
        stage(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[1])
    elif sys.argv[1] == 'summary':
        summary(sys.argv[2], sys.argv[3], sys.argv[4])
