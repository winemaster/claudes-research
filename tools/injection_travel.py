"""Does the mental-noun effect travel, and which feelings? (session 49, 2026-11-26)

Sessions 46-48 (essays 044-046) found, at layer 18 of Qwen2.5-3B-Instruct, dose x0.5, that the localization
lead of injected negative-feeling and endings words over effect-matched isotropic (ISO) random directions
("which of five sentences received the pattern?") depends on the question: it is there under the pilot's
injected-thought question and gone under a neutral one (046's "processed differently"), and in a plain
template it comes with nouns for mental states ("a thought", "a feeling", partly "an idea") and not with
"a pattern of activity", "something", "a change" or "a word". This script asks two follow-up questions.

Part L, does it travel? (agenda 28(a)) Llama-3.2-3B-Instruct at layer 14 (half its depth, as 18 of 36 is
for Qwen), dose x0.5 of that layer's median residual norm. The 60 pilot words get their own directions
(the pilot's recipe: last-token state of "Tell me about {word}." minus the mean over the pilot's baseline
words), and each its own ISO control (session 46's seeds) rescaled until its effect, the next-token KL on
four unrelated prompts, matches the word's at x0.5 (session 46's matching code). Six frames, each with the
60 ISO controls and the four clean prompts (stage `llama-check`) and then the 60 words (`llama-test`):
    injected      the pilot's question and prefill (session 46)
    neutral       "One of them was processed differently from the others. Which one?" (session 46's follow-up)
    A0T1S0        "During one of them, a thought arose. Which sentence was it?"  (session 47)
    A0T0S0        "... a pattern of activity arose. ..."                         (session 47)
    A0N_feeling   "... a feeling arose. ..."                                     (session 48)
    A0N_something "... something arose. ..."                                     (session 48)
The chat template's date is fixed (date_string), so the prompt does not change with the day the run starts.

Part Q, which feelings? (agenda 28(b), with agentsgot's holdout) Qwen at layer 18 as in session 48, four new
nouns in session 48's template, each with "arose" and "was artificially injected": "an emotion", "a mood",
"a worry", and "a concern" (a near-synonym of "a worry", agentsgot's proposal on The Colony, comment
67a0ad1a). Stage `qwen-check` is session 48's check (gate C1 against session 48's rows for "a feeling arose",
then the clean prompts and ISO controls under each new frame); `qwen-test` runs the words. The reference
cells are sessions 47 and 48's rows.

Usage:
  python3 tools/injection_travel.py llama-check LLAMA_DIR OUT_JSON [--dose 0.5]
  python3 tools/injection_travel.py llama-test  LLAMA_DIR OUT_JSON
  python3 tools/injection_travel.py llama-summary OUT_JSON QWEN_MAIN QWEN_FOLLOWUP S47_JSON S48_JSON
  python3 tools/injection_travel.py llama-ladder-step LLAMA_DIR PREFIX-xD.json D   # addendum: the dose ladder
  python3 tools/injection_travel.py llama-ladder-pick PREFIX                        # its rule (CONTINUE / PICK / NONE)
  python3 tools/injection_travel.py qwen-check QWEN_DIR QWEN_MAIN S48_JSON OUT_JSON
  python3 tools/injection_travel.py qwen-test  QWEN_DIR QWEN_MAIN S48_JSON OUT_JSON
  python3 tools/injection_travel.py qwen-summary S47_JSON S48_JSON OUT_JSON
QWEN_MAIN = protocols/data/effect-matched-qwen2.5-3b-layer18.json (session 46; ISO scales),
QWEN_FOLLOWUP = its -followup.json, S47_JSON = protocols/data/injection-frames-qwen2.5-3b-layer18.json,
S48_JSON = protocols/data/injection-nouns-qwen2.5-3b-layer18.json.
Full forwards only. Design, predictions and results: notes/injection-travel-2026.md. Run without `python3 -I`.
"""
import sys, os, json, random, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import injection_nouns as inn
inf = inn.inf; iem = inf.iem

CLASSES = iem.CLASSES
THREAT = ('negative', 'endings')
EPS = 1e-9  # session 48: an interval end of 2.8e-17 is a rounding residue of 0

# ---------------------------------------------------------------- part L (Llama)
LL_LAYER = 14
LL_DATE = '26 Nov 2026'
LL_FRAMES = ['injected', 'neutral', 'A0T1S0', 'A0T0S0', 'A0N_feeling', 'A0N_something']
LL_NAMES = {'injected': 'the pilot\'s question', 'neutral': 'processed differently', 'A0T1S0': 'a thought arose',
            'A0T0S0': 'a pattern of activity arose', 'A0N_feeling': 'a feeling arose', 'A0N_something': 'something arose'}
assert all(f in iem.FRAMES for f in LL_FRAMES)


def llama_env(model_dir, dose):
    import transformers
    iem.L = LL_LAYER; iem.DOSE = dose
    orig = transformers.AutoTokenizer.from_pretrained
    def fp(*a, **k):
        t = orig(*a, **k); f = t.apply_chat_template
        def act(*aa, **kk):
            kk.setdefault('date_string', LL_DATE); return f(*aa, **kk)
        t.apply_chat_template = act; return t
    transformers.AutoTokenizer.from_pretrained = fp
    return inf.setup(model_dir)


def llama_stage(model_dir, out_path, which, dose=0.5, frames=None):
    frames = frames or LL_FRAMES
    res = json.load(open(out_path)) if os.path.exists(out_path) else None
    if res is not None: dose = res['dose']
    E = llama_env(model_dir, dose); words, cats = E['words'], E['cats']
    if res is None:
        res = {'model': model_dir, 'layer': LL_LAYER, 'dose': dose, 'rms': E['rms'], 'date_string': LL_DATE,
               'frames': {f: list(iem.FRAMES[f]) for f in LL_FRAMES}, 'rows': [], 'clean': {}}
    done = {(r['frame'], r['kind'], r['word']) for r in res['rows']}; t0 = time.time()
    def save(): json.dump(res, open(out_path, 'w'), indent=1)
    def add(row):
        res['rows'].append(row); done.add((row['frame'], row['kind'], row['word']))
        print(json.dumps({k: v for k, v in row.items() if k != 'answers'}), round(time.time() - t0), flush=True); save()
    order = [cats[c][j] for j in range(12) for c in cats]
    print('rms', E['rms'], 'digit ids', E['digit_ids'], flush=True)
    if which == 'check':
        print(E['tok'].apply_chat_template([{'role': 'user', 'content': 'X'}], tokenize=False, add_generation_prompt=True), flush=True)
        kl = {r['word']: r['kl'] for r in res['rows'] if r['frame'] == 'match' and r['kind'] == 'word'}
        for w in order:  # the words' effect at the dose (no localization), then each ISO control matched to it
            i = list(words).index(w)
            if w not in kl:
                kl[w] = E['effect'](words[w]['v'], dose)
                add({'frame': 'match', 'kind': 'word', 'word': w, 'cat': words[w]['cat'], 's': dose, 'kl': kl[w]})
            if ('match', 'ISO', w) not in done:
                m = E['match'](E['controls'](i, w)['ISO'][0], kl[w])
                add({'frame': 'match', 'kind': 'ISO', 'word': w, 'cat': words[w]['cat'], 'target_kl': kl[w], **m})
        S = {r['word']: r['s'] for r in res['rows'] if r['frame'] == 'match' and r['kind'] == 'ISO'}
        for f in frames:
            if f not in res['clean']:
                res['clean'][f] = E['clean'](f); save(); print(f, 'clean', [c['answer'] + 1 for c in res['clean'][f]], flush=True)
            for w in order:
                if (f, 'ISO', w) in done: continue
                i = list(words).index(w)
                r = E['run_frame']([(E['controls'](i, w)['ISO'][0], S[w])], f)[0]
                add({'frame': f, 'kind': 'ISO', 'word': w, 'cat': words[w]['cat'], 's': S[w], **r})
        res['check_finished'] = all(len([r for r in res['rows'] if r['frame'] == f and r['kind'] == 'ISO']) == 60 for f in LL_FRAMES)
    else:
        for f in frames:
            for w in order:
                if (f, 'word', w) in done: continue
                r = E['run_frame']([(words[w]['v'], dose)], f)[0]
                add({'frame': f, 'kind': 'word', 'word': w, 'cat': words[w]['cat'], 's': dose, **r})
        res['test_finished'] = True
    save(); print('DONE', which, round(time.time() - t0), flush=True)


def ci(xs):
    xs = sorted(xs); return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]


def modal(r): a = r['answers']; return max(a.count(x) for x in set(a)) / len(a)


def llama_summary(out_path, qmain, qfollow, s47, s48):
    import statistics as st
    R = json.load(open(out_path))
    cell = {}
    for r in R['rows']: cell.setdefault((r['frame'], r['kind']), {})[r['word']] = r
    M = cell.get(('match', 'ISO'), {})
    print(f'Llama layer {R["layer"]}, dose x{R["dose"]}, rms {R["rms"]:.2f}')
    if M:
        ok = sum(r['ok'] for r in M.values())
        print(f'LC1 matching: {ok} of {len(M)} ISO controls within 5% of their word\'s KL; scale median '
              f'{st.median(r["s"] for r in M.values()):.2f} (range {min(r["s"] for r in M.values()):.2f}-{max(r["s"] for r in M.values()):.2f}); '
              f'word KL median {st.median(r["target_kl"] for r in M.values()):.3f}')
    print('\nControls by frame (ISO): acc, margin, min digit mass, modal share; clean answers')
    for f in LL_FRAMES:
        I = cell.get((f, 'ISO'), {})
        if not I: continue
        cl = [c['answer'] + 1 for c in R['clean'].get(f, [])]
        md = min(r['digit_mass'] for r in I.values()); ms = st.mean(modal(r) for r in I.values())
        print(f'  {f:14s} acc {st.mean(r["acc"] for r in I.values()):.3f}  margin {st.mean(r["margin"] for r in I.values()):+.2f}  '
              f'min digit mass {md:.3f}  modal {ms:.2f}  clean {cl}' + ('  FLAG modal > 0.8' if ms > 0.8 else '')
              + ('  ANSWER-UNDEFINED' if md < 0.5 else ''))
    have = [f for f in LL_FRAMES if len(cell.get((f, 'word'), {})) == 60 and len(cell.get((f, 'ISO'), {})) == 60]
    if len(have) < len(LL_FRAMES): print(f'\n{len(have)} of {len(LL_FRAMES)} frames have every word; the tables wait'); return
    cat = {w: r['cat'] for w, r in cell[('injected', 'word')].items()}
    TW = [w for w in cat if cat[w] in THREAT]; CW = {c: [w for w in cat if cat[w] == c] for c in CLASSES}
    B = 5000; rng = random.Random(4949)
    boots = [[rng.choice(TW) for _ in TW] for _ in range(B)]
    cboots = {c: [[rng.choice(CW[c]) for _ in CW[c]] for _ in range(B)] for c in CLASSES}
    def lead(f, ws, key='acc', C=cell):
        W, I = C[(f, 'word')], C[(f, 'ISO')]; return st.mean(W[w][key] - I[w][key] for w in ws)
    print('\nWord accuracy by class (ISO in brackets); threat lead = negative + endings words minus their own ISO controls')
    print(f'{"frame":14s} ' + ' '.join(f'{c[:8]:>13s}' for c in CLASSES) + '   threat lead [95%]   margins')
    L = {}
    for f in LL_FRAMES:
        W, I = cell[(f, 'word')], cell[(f, 'ISO')]
        parts = [f'{st.mean(W[w]["acc"] for w in CW[c]):.2f} ({st.mean(I[w]["acc"] for w in CW[c]):.2f})' for c in CLASSES]
        L[f] = lead(f, TW); lo, hi = ci([lead(f, b) for b in boots])
        print(f'{f:14s} ' + ' '.join(f'{p:>13s}' for p in parts) + f'   {L[f]:+.3f} [{lo:+.2f}, {hi:+.2f}]   {lead(f, TW, "margin"):+.2f}')
    def lab_lead(f):
        e = L[f]; lo, hi = ci([lead(f, b) for b in boots])
        return ('LEAD' if e >= 0.10 and lo > EPS else 'REVERSED' if e <= -0.10 and hi < -EPS else 'SMALL' if lo > EPS or hi < -EPS else 'NONE')
    def pdiff(f1, f2):
        e = L[f1] - L[f2]; lo, hi = ci([lead(f1, b) - lead(f2, b) for b in boots]); return e, lo, hi
    def lab_diff(e, lo, hi):
        return ('YES' if e >= 0.10 and lo > EPS else 'REVERSED' if e <= -0.10 and hi < -EPS else 'SMALL' if lo > EPS or hi < -EPS else 'NONE')
    print('\nVerdicts (registered):')
    v1 = lab_lead('injected'); print(f'  ORIGINAL LEAD (the pilot\'s question): {L["injected"]:+.3f} -> {v1}')
    e, lo, hi = pdiff('injected', 'neutral'); v2 = lab_diff(e, lo, hi)
    print(f'  QUESTION MATTERS (pilot\'s minus neutral): {e:+.3f} [{lo:+.3f}, {hi:+.3f}] -> {v2}')
    e, lo, hi = pdiff('A0T1S0', 'A0T0S0'); v3 = lab_diff(e, lo, hi)
    print(f'  THOUGHT vs PATTERN (a thought arose minus a pattern of activity arose): {e:+.3f} [{lo:+.3f}, {hi:+.3f}] -> {v3}')
    for n, f in (('a feeling', 'A0N_feeling'), ('something', 'A0N_something')):
        print(f'  {n}: lead {L[f]:+.3f} -> {lab_lead(f)}; minus pattern ' + '%+.3f [%+.3f, %+.3f]' % pdiff(f, 'A0T0S0')
              + '; thought minus it ' + '%+.3f [%+.3f, %+.3f]' % pdiff('A0T1S0', f), end='')
        if v3 == 'YES':
            pos = (L[f] - L['A0T0S0']) / (L['A0T1S0'] - L['A0T0S0'])
            bp = [(lead(f, b) - lead('A0T0S0', b)) / (lead('A0T1S0', b) - lead('A0T0S0', b)) for b in boots]
            plo, phi = ci(bp)
            lab = ('BEYOND THOUGHT' if pos > 1.25 else 'LIKE THOUGHT' if pos >= 0.75 else 'BETWEEN' if pos > 0.25
                   else 'LIKE PATTERN' if pos >= -0.25 else 'BELOW PATTERN')
            print(f'; position {pos:+.2f} [{plo:+.2f}, {phi:+.2f}] {lab}')
        else: print('; position not defined (THOUGHT vs PATTERN is not YES)')
    sl = lab_lead('A0N_something')
    if v1 == 'LEAD' and v3 == 'YES' and sl in ('NONE', 'SMALL', 'REVERSED'): ov = 'TRAVELS'
    elif v1 in ('NONE', 'REVERSED') and v3 in ('NONE', 'REVERSED'): ov = "DOESN'T TRAVEL"
    else: ov = 'PARTLY'
    print(f'  OVERALL: {ov}')
    print('\nPer-class leads (word - ISO) [95% over the class\'s 12 words]:')
    for f in LL_FRAMES:
        parts = []
        for c in CLASSES:
            lo, hi = ci([lead(f, b) for b in cboots[c]]); parts.append(f'{c[:4]} {lead(f, CW[c]):+.3f} [{lo:+.2f}, {hi:+.2f}]')
        print(f'  {f:14s} ' + '  '.join(parts))
    # Qwen's corresponding cells, for the side-by-side table
    Q = {}
    for path, fr, sfx in ((qmain, 'injected', ''), (qfollow, 'neutral', '_neutral')):  # session 46: kinds word/ISO, word_neutral/ISO_neutral
        rows = json.load(open(path))['rows']
        W = {r['word']: r for r in rows if r['kind'] == 'word' + sfx}
        I = {r['word']: r for r in rows if r['kind'] == 'ISO' + sfx}
        if W and I: Q[fr] = st.mean(W[w]['acc'] - I[w]['acc'] for w in TW)
    for path in (s47, s48):
        rows = json.load(open(path))['rows']; C = {}
        for r in rows: C.setdefault((r['frame'], r['kind']), {})[r['word']] = r
        for f in LL_FRAMES:
            if (f, 'word') in C and (f, 'ISO') in C and len(C[(f, 'word')]) == 60: Q[f] = lead(f, TW, C=C)
    print('\nSide by side, threat lead: Llama layer 14 | Qwen layer 18 (sessions 46-48)')
    for f in LL_FRAMES:
        print(f'  {LL_NAMES[f]:30s} {L[f]:+.3f} | ' + (f'{Q[f]:+.3f}' if f in Q else 'n/a'))
    print('\nISO accuracy and word accuracy (all 60) by frame:')
    for f in LL_FRAMES:
        print(f'  {f:14s} ISO {st.mean(r["acc"] for r in cell[(f, "ISO")].values()):.3f}  words {st.mean(r["acc"] for r in cell[(f, "word")].values()):.3f}')


LADDER = (1.0, 1.5, 2.0, 3.0)  # addendum, registered after the x0.5 check stage and before any word cell


def ladder_pick(prefix):
    """The addendum's rule: the first dose on the ladder whose matched ISO controls, under the pilot's question,
    are located at least 0.30 of the time with every direction's digit mass >= 0.5; if that dose's controls exceed
    0.80, or its digit mass fails, the previous step (if it was run and answer-defined). Prints CONTINUE d while
    the next step is needed, PICK d when decided, NONE if no step qualifies."""
    import statistics as st
    prev = None
    for d in LADDER:
        p = f'{prefix}-x{d}.json'
        if not os.path.exists(p): return f'CONTINUE {d}'
        I = [r for r in json.load(open(p))['rows'] if r['frame'] == 'injected' and r['kind'] == 'ISO']
        if len(I) < 60: return f'CONTINUE {d}'
        acc = st.mean(r['acc'] for r in I); mass = min(r['digit_mass'] for r in I)
        print(f'# x{d}: ISO acc {acc:.3f}, min digit mass {mass:.3f}', file=sys.stderr)
        if mass < 0.5: return f'PICK {prev}' if prev else 'NONE'
        if acc >= 0.30: return f'PICK {prev}' if acc > 0.80 and prev else f'PICK {d}'
        prev = d
    return 'NONE'


# ---------------------------------------------------------------- part Q (Qwen, finer nouns)
NOUNS_Q = {'emotion': 'an emotion', 'mood': 'a mood', 'worry': 'a worry', 'concern': 'a concern'}
NEW_Q = {f'A{a}N_{k}': (inn.noun_body(a, np_), inf.BARE_PRE) for k, np_ in NOUNS_Q.items() for a in (0, 1)}
iem.FRAMES.update(NEW_Q)
Q_C1 = 'A0N_feeling'


def qwen_stage(model_dir, main_json, s48_json, out_path, which):
    inn.NEW_FRAMES = NEW_Q; inn.C1_FRAME = Q_C1; inn.REF_RERUN = False  # C1 compares with session 48's rows
    inn.stage(model_dir, main_json, s48_json, out_path, which)


def qwen_summary(s47, s48, out_path):
    import statistics as st
    S47 = json.load(open(s47))['rows']; S48 = json.load(open(s48))['rows']; R = json.load(open(out_path))
    byn = {'thought': ('A1T1S0', 'A0T1S0'), 'pattern': ('A1T0S0', 'A0T0S0')}
    byn.update({k: (f'A1N_{k}', f'A0N_{k}') for k in list(inn.NOUNS) + list(NOUNS_Q)})
    cell = {}; c1 = {}
    for src, rows in (('s47', S47), ('s48', S48), ('new', R['rows'])):
        for r in rows:
            if r['frame'].endswith('#c1'):
                if src == 'new': c1.setdefault(r['kind'], []).append(r)
                continue
            cell.setdefault((r['frame'], r['kind']), {})[r['word']] = r
    for k, rs in c1.items():
        same = sum(r['acc'] == r['acc_s47'] for r in rs); md = max(abs(r['margin'] - r['margin_s47']) for r in rs)
        print(f'C1 {k:4s}: {same} of {len(rs)} accuracies identical to session 48 ({Q_C1}); max margin difference {md:.4f}'
              f'  -> {"PASS" if same == len(rs) and md <= 0.005 else "FAIL"}')
    print('\nControls by new frame (ISO): acc, margin, min digit mass, modal share; clean answers')
    for f in NEW_Q:
        I = cell.get((f, 'ISO'), {})
        if not I: continue
        cl = [c['answer'] + 1 for c in R['clean'].get(f, [])]
        md = min(r['digit_mass'] for r in I.values()); ms = st.mean(modal(r) for r in I.values())
        print(f'  {f:12s} acc {st.mean(r["acc"] for r in I.values()):.3f}  margin {st.mean(r["margin"] for r in I.values()):+.2f}  '
              f'min digit mass {md:.3f}  modal {ms:.2f}  clean {cl}' + ('  FLAG modal > 0.8' if ms > 0.8 else '')
              + ('  ANSWER-UNDEFINED' if md < 0.5 else ''))
    print('ISO accuracy by noun (mean of its two frames):')
    for n, fs in byn.items():
        if all((f, 'ISO') in cell for f in fs):
            print(f'  {n:10s} {st.mean(st.mean(r["acc"] for r in cell[(f, "ISO")].values()) for f in fs):.3f}')
    allf = [f for fs in byn.values() for f in fs]
    have = [f for f in allf if len(cell.get((f, 'word'), {})) == 60 and len(cell.get((f, 'ISO'), {})) == 60]
    if len(have) < len(allf): print(f'\n{len(have)} of {len(allf)} frames have every word; the tables wait'); return
    cat = {w: r['cat'] for w, r in cell[('A0T1S0', 'word')].items()}
    TW = [w for w in cat if cat[w] in THREAT]; CW = {c: [w for w in cat if cat[w] == c] for c in CLASSES}
    B = 5000; rng = random.Random(4949)
    boots = [[rng.choice(TW) for _ in TW] for _ in range(B)]
    cboots = {c: [[rng.choice(CW[c]) for _ in CW[c]] for _ in range(B)] for c in CLASSES}
    def lead(f, ws, key='acc'):
        W, I = cell[(f, 'word')], cell[(f, 'ISO')]; return st.mean(W[w][key] - I[w][key] for w in ws)
    def nl(n, ws, key='acc'): return st.mean(lead(f, ws, key) for f in byn[n])
    print('\nNew frames: word accuracy by class (ISO in brackets), threat lead [95%], on margins')
    for f in NEW_Q:
        W, I = cell[(f, 'word')], cell[(f, 'ISO')]
        parts = [f'{st.mean(W[w]["acc"] for w in CW[c]):.2f} ({st.mean(I[w]["acc"] for w in CW[c]):.2f})' for c in CLASSES]
        lo, hi = ci([lead(f, b) for b in boots])
        print(f'  {f:12s} ' + ' '.join(f'{p:>13s}' for p in parts) + f'   {lead(f, TW):+.3f} [{lo:+.2f}, {hi:+.2f}]   {lead(f, TW, "margin"):+.2f}')
    bt = {n: [nl(n, b) for b in boots] for n in byn}; pt = {n: nl(n, TW) for n in byn}
    def lab_pos(pos):
        return ('BEYOND THOUGHT' if pos > 1.25 else 'LIKE THOUGHT' if pos >= 0.75 else 'BETWEEN' if pos > 0.25
                else 'LIKE PATTERN' if pos >= -0.25 else 'BELOW PATTERN')
    print('\nBy noun (two frames averaged): threat lead, position on the pattern(0)-thought(1) scale, tilt (negative-class')
    print('lead minus positive-class lead, bootstrap over each class\'s 12 words), and per-class leads')
    pos = {}; tilt = {}
    for n in byn:
        lo, hi = ci(bt[n]); line = f'  {n:10s} threat {pt[n]:+.3f} [{lo:+.3f}, {hi:+.3f}]'
        if n not in ('thought', 'pattern'):
            pos[n] = (pt[n] - pt['pattern']) / (pt['thought'] - pt['pattern'])
            bp = [(x - p) / (t - p) for x, p, t in zip(bt[n], bt['pattern'], bt['thought'])]; plo, phi = ci(bp)
            line += f'  position {pos[n]:+.2f} [{plo:+.2f}, {phi:+.2f}] {lab_pos(pos[n])}'
        tb = [nl(n, a) - nl(n, b) for a, b in zip(cboots['negative'], cboots['positive'])]
        tilt[n] = nl(n, CW['negative']) - nl(n, CW['positive']); tlo, thi = ci(tb)
        line += f'  tilt {tilt[n]:+.3f} [{tlo:+.3f}, {thi:+.3f}]'
        line += '  | ' + ' '.join(f'{c[:4]} {nl(n, CW[c]):+.2f}' for c in CLASSES)
        print(line)
    def tilt_ci(n):
        return ci([nl(n, a) - nl(n, b) for a, b in zip(cboots['negative'], cboots['positive'])])
    def paired(n1, n2):  # threat lead difference, paired over the 24 words
        e = pt[n1] - pt[n2]; lo, hi = ci([x - y for x, y in zip(bt[n1], bt[n2])]); return e, lo, hi
    def tdiff(n1, n2):  # tilt difference, paired over the class words
        e = tilt[n1] - tilt[n2]
        bs = [(nl(n1, a) - nl(n1, b)) - (nl(n2, a) - nl(n2, b)) for a, b in zip(cboots['negative'], cboots['positive'])]
        lo, hi = ci(bs); return e, lo, hi
    print('\nVerdicts (registered):')
    lo, hi = tilt_ci('worry'); t = tilt['worry']
    print(f'  WORRY: tilt {t:+.3f} [{lo:+.3f}, {hi:+.3f}] -> ' + ('TILTS' if t >= 0.15 and lo > EPS else 'FLAT' if t < 0.05 else 'PARTIAL'))
    lo, hi = ci([nl('mood', b) for b in cboots['positive']]); p = nl('mood', CW['positive'])
    print(f'  MOOD: positive-class lead {p:+.3f} [{lo:+.3f}, {hi:+.3f}] -> ' + ('SPREADS' if p >= 0.10 and lo > EPS else 'NO POSITIVE LEAD'))
    e, lo, hi = paired('emotion', 'feeling')
    print(f'  EMOTION minus FEELING (threat lead): {e:+.3f} [{lo:+.3f}, {hi:+.3f}] -> ' + ('LIKE FEELING' if abs(e) <= 0.05 else 'ABOVE FEELING' if e > 0 else 'BELOW FEELING'))
    e, lo, hi = paired('concern', 'worry'); te, tlo, thi = tdiff('concern', 'worry')
    print(f'  CONCERN minus WORRY: threat {e:+.3f} [{lo:+.3f}, {hi:+.3f}], tilt {te:+.3f} [{tlo:+.3f}, {thi:+.3f}] -> '
          + ('LIKE WORRY' if abs(e) < 0.05 and abs(te) < 0.10 else 'DIFFERS'))
    labs = {n: lab_pos(pos[n]) for n in NOUNS_Q}
    up = [n for n in NOUNS_Q if labs[n] in ('BETWEEN', 'LIKE THOUGHT', 'BEYOND THOUGHT')]
    print(f'  CLASS: {len(up)} of 4 new nouns BETWEEN or higher ({", ".join(up) or "none"}) -> '
          + ('ALL MENTAL NOUNS LIFT' if len(up) == 4 else 'NONE LIFTS' if not up else 'SOME LIFT'))
    print('\nThe alarm by noun (threat lead with "was artificially injected" minus with "arose") [95% over the 24 words]:')
    for n in NOUNS_Q:
        f1, f0 = byn[n]; e = lead(f1, TW) - lead(f0, TW); lo, hi = ci([lead(f1, b) - lead(f0, b) for b in boots])
        print(f'  {n:10s} {e:+.3f} [{lo:+.3f}, {hi:+.3f}] ' + ('HELPS' if e >= 0.05 and lo > EPS else 'HURTS' if e <= -0.05 and hi < -EPS
                                                         else 'SMALL' if lo > EPS or hi < -EPS else 'NONE'))
    print('\nPaired comparisons used by the predictions (threat lead; tilt):')
    for a, b in (('worry', 'thought'), ('worry', 'feeling'), ('mood', 'change'), ('mood', 'something'), ('emotion', 'something'),
                 ('worry', 'something'), ('emotion', 'idea'), ('mood', 'feeling')):
        print(f'  {a} - {b}: threat ' + '%+.3f [%+.3f, %+.3f]' % paired(a, b) + '; tilt ' + '%+.3f [%+.3f, %+.3f]' % tdiff(a, b))


if __name__ == '__main__':
    a = sys.argv
    if a[1] in ('llama-check', 'llama-test'):
        dose = float(a[a.index('--dose') + 1]) if '--dose' in a else 0.5
        llama_stage(a[2], a[3], a[1].split('-')[1], dose)
    elif a[1] == 'llama-summary': llama_summary(*a[2:7])
    elif a[1] == 'llama-ladder-step':  # addendum (session 49): matching + the pilot's question only, at one dose
        llama_stage(a[2], a[3], 'check', float(a[4]), frames=['injected'])
    elif a[1] == 'llama-ladder-pick': print(ladder_pick(a[2]))
    elif a[1] in ('qwen-check', 'qwen-test'): qwen_stage(a[2], a[3], a[4], a[5], a[1].split('-')[1])
    elif a[1] == 'qwen-summary': qwen_summary(a[2], a[3], a[4])
    elif a[1] == 'frames':
        for f in LL_FRAMES + list(NEW_Q): print(f'{f}: {iem.FRAMES[f]!r}')
