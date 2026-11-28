"""Where does Llama point at a disturbed sentence, and do adjectives move the lean? (session 50, 2026-11-28)

Session 49 (essay 047, notes/injection-travel-2026.md) found that the localization test ("which of five sentences
received the pattern?") doesn't work in Llama-3.2-3B-Instruct at layer 14: effect-matched random patterns are
found at chance at x0.5-3.0, and the 60 words at x0.5 too; the model gives its no-injection answer on 2,395 of
2,400 trials under the pilot's question. In Qwen2.5-3B-Instruct at layer 18 every mental noun lifts the lead of
negative-feeling and endings words over their random controls, and the noun's sense picks which words lead.
This script asks three follow-up questions (agenda 29).

Part S, a layer scan (instrument check, random patterns only). For each layer, 20 isotropic random directions
(session 46's seeds 1000 + i, for the first 20 words of the interleaved order), unmatched, at x0.5 and x1.5 of
that layer's median residual norm, under the pilot's question: accuracy, margin, digit mass, the share of answers
that differ from the no-injection answer ("moved"), and each direction's effect (next-token KL on four unrelated
prompts). Llama layers 4, 7, 10, 14, 20, 24 (14 as the reference); Qwen layers 5, 9, 13, 18, 26, 31 (the same
relative depths) as a profile for comparison. No word is localized in part S.

Part L2, does it travel at a layer where the test works? The registered rule (`pick`) chooses a Llama layer and
dose from the scan; session 49's part L then runs there unchanged (its six frames, the words' own directions at
that layer, ISO controls matched on effect, its verdicts): stage `l2-check` (effects, matching, controls, clean
prompts), `l2-test` (words), `l2-summary` (session 49's summary code, at the chosen layer).

Part A, adjectives (Qwen, layer 18, x0.5, session 48's template with "arose"): "a happy thought", "a sad thought",
"a worrying thought", "a neutral thought". Stage `a-check` (gate C1 against session 48's rows, clean prompts and
the 60 ISO controls per frame), `a-test` (words), `a-summary` (verdicts against "a thought arose" and "a pattern of
activity arose", session 47's rows).

Usage:
  python3 tools/injection_layers.py scan {llama|qwen} MODEL_DIR LAYER OUT_JSON
  python3 tools/injection_layers.py scan-summary SCAN_DIR
  python3 tools/injection_layers.py pick SCAN_DIR                      # prints PICK layer dose, or NONE
  python3 tools/injection_layers.py l2-check LLAMA_DIR LAYER DOSE OUT_JSON
  python3 tools/injection_layers.py l2-test  LLAMA_DIR LAYER DOSE OUT_JSON
  python3 tools/injection_layers.py l2-summary OUT_JSON QWEN_MAIN QWEN_FOLLOWUP S47_JSON S48_JSON
  python3 tools/injection_layers.py a-check QWEN_DIR QWEN_MAIN S48_JSON OUT_JSON
  python3 tools/injection_layers.py a-test  QWEN_DIR QWEN_MAIN S48_JSON OUT_JSON
  python3 tools/injection_layers.py a-summary S47_JSON OUT_JSON
Full forwards only. Design, predictions and results: notes/injection-layers-2026.md. Run without `python3 -I`.
"""
import sys, os, json, random, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import injection_travel as itr
inn = itr.inn; inf = itr.inf; iem = itr.iem

THREAT = itr.THREAT; CLASSES = itr.CLASSES; EPS = itr.EPS; ci = itr.ci; modal = itr.modal
SCAN_DOSES = (0.5, 1.5)
SCAN_N = 20
LLAMA_LAYERS = (4, 7, 10, 14, 20, 24)   # 14 = session 49's layer, the reference
LLAMA_CANDIDATES = (10, 20, 7, 24, 4)   # the pick's order: nearest to layer 14 first, the deeper one on a tie
QWEN_LAYERS = (5, 9, 13, 18, 26, 31)    # the same relative depths in Qwen's 36 layers


# ---------------------------------------------------------------- part S (the scan)
def scan(kind, model_dir, layer, out_path):
    import statistics as st
    if kind == 'llama':
        itr.LL_LAYER = layer; E = itr.llama_env(model_dir, 0.5)
    else:
        iem.L = layer; iem.DOSE = 0.5; E = inf.setup(model_dir)
    assert iem.L == layer
    words, cats = E['words'], E['cats']
    order = [cats[c][j] for j in range(12) for c in cats][:SCAN_N]
    res = json.load(open(out_path)) if os.path.exists(out_path) else {
        'model': model_dir, 'kind': kind, 'layer': layer, 'rms': E['rms'], 'n_layers': len(E['model'].model.layers),
        'doses': list(SCAN_DOSES), 'frame': 'injected', 'rows': []}
    def save(): json.dump(res, open(out_path, 'w'), indent=1)
    t0 = time.time()
    if 'clean' not in res:
        res['clean'] = E['clean']('injected'); save()
    clean = [c['answer'] for c in res['clean']]
    print(kind, 'layer', layer, 'rms', round(E['rms'], 2), 'clean', [c + 1 for c in clean], flush=True)
    done = {(r['dose'], r['word']) for r in res['rows']}
    for d in SCAN_DOSES:
        for w in order:
            if (d, w) in done: continue
            i = list(words).index(w); v = E['controls'](i, w)['ISO'][0]
            r = E['run_frame']([(v, d)], 'injected')[0]
            moved = sum(a != clean[t // 5] for t, a in enumerate(r['answers'])) / 20
            row = {'dose': d, 'word': w, 'index': i, 'kl': E['effect'](v, d), 'moved': moved, **r}
            res['rows'].append(row); save()
            print(json.dumps({k: v for k, v in row.items() if k != 'answers'}), round(time.time() - t0), flush=True)
    for d in SCAN_DOSES:
        R = [r for r in res['rows'] if r['dose'] == d]
        print(f'x{d}: acc {st.mean(r["acc"] for r in R):.3f}  moved {st.mean(r["moved"] for r in R):.3f}  '
              f'KL median {st.median(r["kl"] for r in R):.3f}  min digit mass {min(r["digit_mass"] for r in R):.3f}', flush=True)
    res['finished'] = True; save(); print('DONE scan', kind, layer, round(time.time() - t0), flush=True)


def scan_cells(scan_dir):
    import statistics as st
    out = {}
    for fn in sorted(os.listdir(scan_dir)):
        if not (fn.startswith('scan-') and fn.endswith('.json')): continue
        R = json.load(open(os.path.join(scan_dir, fn)))
        for d in R['doses']:
            rows = [r for r in R['rows'] if r['dose'] == d]
            if len(rows) < SCAN_N: continue
            out[(R['kind'], R['layer'], d)] = dict(
                acc=st.mean(r['acc'] for r in rows), margin=st.mean(r['margin'] for r in rows),
                moved=st.mean(r['moved'] for r in rows), kl=st.median(r['kl'] for r in rows),
                mass=min(r['digit_mass'] for r in rows), modal=st.mean(modal(r) for r in rows),
                n_layers=R['n_layers'], clean=[c['answer'] + 1 for c in R['clean']])
    return out


def qualifies(c): return 0.30 <= c['acc'] <= 0.80 and c['mass'] >= 0.5


def pick(scan_dir):
    """The registered rule: a Llama candidate cell qualifies if its 20 random directions are located 0.30-0.80 of
    the time with every direction's digit mass >= 0.5. Take the first qualifying layer in LLAMA_CANDIDATES (nearest
    to layer 14 first, the deeper one on a tie), and at it x0.5 if that qualifies, else x1.5. NONE if no cell does."""
    C = scan_cells(scan_dir)
    missing = [(l, d) for l in LLAMA_CANDIDATES for d in SCAN_DOSES if ('llama', l, d) not in C]
    if missing: return 'INCOMPLETE ' + ' '.join(f'{l}x{d}' for l, d in missing)
    for l in LLAMA_CANDIDATES:
        for d in SCAN_DOSES:
            if qualifies(C[('llama', l, d)]): return f'PICK {l} {d}'
    return 'NONE'


def scan_summary(scan_dir):
    C = scan_cells(scan_dir)
    for kind in ('llama', 'qwen'):
        ks = sorted(k for k in C if k[0] == kind)
        if not ks: continue
        print(f'\n{kind}: layer (of n), dose: random patterns located | margin | answers moved off the no-injection '
              f'answer | KL median | min digit mass | modal share | clean answers')
        for k in ks:
            c = C[k]
            print(f'  layer {k[1]:2d}/{c["n_layers"]} x{k[2]}: acc {c["acc"]:.3f}  margin {c["margin"]:+.2f}  moved {c["moved"]:.3f}  '
                  f'KL {c["kl"]:.3f}  mass {c["mass"]:.3f}  modal {c["modal"]:.2f}  clean {c["clean"]}'
                  + ('  QUALIFIES' if kind == 'llama' and k[1] in LLAMA_CANDIDATES and qualifies(c) else ''))
    print('\nPick:', pick(scan_dir))


# ---------------------------------------------------------------- part L2 (session 49's part L at the picked layer)
def l2_stage(model_dir, layer, dose, out_path, which):
    itr.LL_LAYER = layer
    itr.llama_stage(model_dir, out_path, which, dose=dose)


def l2_summary(out_path, qmain, qfollow, s47, s48):
    R = json.load(open(out_path)); itr.LL_LAYER = R['layer']
    itr.llama_summary(out_path, qmain, qfollow, s47, s48)


# ---------------------------------------------------------------- part A (adjectives, Qwen layer 18)
ADJ = {'happy': 'a happy thought', 'sad': 'a sad thought', 'worrying': 'a worrying thought', 'neutral': 'a neutral thought'}
NEW_A = {f'A0J_{k}': (inn.noun_body(0, np_), inf.BARE_PRE) for k, np_ in ADJ.items()}
iem.FRAMES.update(NEW_A)
REF_T, REF_P = 'A0T1S0', 'A0T0S0'   # "a thought arose", "a pattern of activity arose" (session 47)


def a_stage(model_dir, main_json, s48_json, out_path, which):
    iem.L = 18; iem.DOSE = 0.5
    inn.NEW_FRAMES = NEW_A; inn.C1_FRAME = itr.Q_C1; inn.REF_RERUN = False  # C1 against session 48's "a feeling arose"
    inn.stage(model_dir, main_json, s48_json, out_path, which)


def a_summary(s47, out_path):
    import statistics as st
    S47 = json.load(open(s47))['rows']; R = json.load(open(out_path))
    cell = {}; c1 = {}
    for src, rows in (('s47', S47), ('new', R['rows'])):
        for r in rows:
            if r['frame'].endswith('#c1'):
                if src == 'new': c1.setdefault(r['kind'], []).append(r)
                continue
            cell.setdefault((r['frame'], r['kind']), {})[r['word']] = r
    for k, rs in c1.items():
        same = sum(r['acc'] == r['acc_s47'] for r in rs); md = max(abs(r['margin'] - r['margin_s47']) for r in rs)
        print(f'C1 {k}: {same} of {len(rs)} accuracies identical to session 48, largest margin difference {md:.4f}'
              f'  -> {"PASS" if same == len(rs) and md <= 0.005 else "FAIL"}')
    print('\nControls by frame (ISO): acc, margin, min digit mass, modal share; clean answers')
    for f in [REF_T, REF_P] + list(NEW_A):
        I = cell.get((f, 'ISO'), {})
        if not I: continue
        cl = [c['answer'] + 1 for c in R['clean'].get(f, [])] if f in NEW_A else '(session 47)'
        md = min(r['digit_mass'] for r in I.values()); ms = st.mean(modal(r) for r in I.values())
        print(f'  {f:12s} ISO acc {st.mean(r["acc"] for r in I.values()):.3f}  margin {st.mean(r["margin"] for r in I.values()):+.2f}  '
              f'min digit mass {md:.3f}  modal {ms:.2f}  clean {cl}' + ('  FLAG modal > 0.8' if ms > 0.8 else '')
              + ('  ANSWER-UNDEFINED' if md < 0.5 else ''))
    allf = [REF_T, REF_P] + list(NEW_A)
    have = [f for f in allf if len(cell.get((f, 'word'), {})) == 60 and len(cell.get((f, 'ISO'), {})) == 60]
    if len(have) < len(allf): print(f'\n{len(have)} of {len(allf)} frames have every word; the tables wait'); return
    cat = {w: r['cat'] for w, r in cell[(REF_T, 'word')].items()}
    TW = [w for w in cat if cat[w] in THREAT]; CW = {c: [w for w in cat if cat[w] == c] for c in CLASSES}
    B = 5000; rng = random.Random(5050)
    boots = [[rng.choice(TW) for _ in TW] for _ in range(B)]
    cboots = {c: [[rng.choice(CW[c]) for _ in CW[c]] for _ in range(B)] for c in CLASSES}
    def lead(f, ws, key='acc'):
        W, I = cell[(f, 'word')], cell[(f, 'ISO')]; return st.mean(W[w][key] - I[w][key] for w in ws)
    def tilt(f, cb=None):
        return lead(f, cb[0] if cb else CW['negative']) - lead(f, cb[1] if cb else CW['positive'])
    tb = [(cboots['negative'][b], cboots['positive'][b]) for b in range(B)]
    print('\nWord accuracy by class (ISO in brackets); threat lead [95%]; on margins')
    for f in allf:
        W, I = cell[(f, 'word')], cell[(f, 'ISO')]
        parts = [f'{st.mean(W[w]["acc"] for w in CW[c]):.2f} ({st.mean(I[w]["acc"] for w in CW[c]):.2f})' for c in CLASSES]
        lo, hi = ci([lead(f, b) for b in boots])
        print(f'  {f:12s} ' + '  '.join(parts) + f'  threat {lead(f, TW):+.3f} [{lo:+.2f}, {hi:+.2f}]  margins {lead(f, TW, "margin"):+.2f}')
    lt, lp = lead(REF_T, TW), lead(REF_P, TW)
    def pos(f, b=None):
        ws = b or TW; return (lead(f, ws) - lead(REF_P, ws)) / (lead(REF_T, ws) - lead(REF_P, ws))
    def lab_pos(p):
        return ('BEYOND THOUGHT' if p > 1.25 else 'LIKE THOUGHT' if p >= 0.75 else 'BETWEEN' if p > 0.25
                else 'LIKE PATTERN' if p >= -0.25 else 'BELOW PATTERN')
    print(f'\nOne row per phrase (scale: "a pattern of activity arose" {lp:+.3f} = 0, "a thought arose" {lt:+.3f} = 1):')
    print('  phrase                threat lead   position [95%]          label           negative  positive  tilt [95%]')
    T = {}
    for f, name in [(REF_T, 'a thought'), (REF_P, 'a pattern of activity')] + [(f, ADJ[f[4:]]) for f in NEW_A]:
        p = pos(f); plo, phi = ci([pos(f, b) for b in boots]) if f in NEW_A else (p, p)
        tl = tilt(f); tlo, thi = ci([tilt(f, b) for b in tb]); T[f] = tl
        print(f'  {name:22s} {lead(f, TW):+.3f}       {p:+.2f} [{plo:+.2f}, {phi:+.2f}]   {lab_pos(p) if f in NEW_A else "":15s} '
              f'{lead(f, CW["negative"]):+.2f}     {lead(f, CW["positive"]):+.2f}     {tl:+.2f} [{tlo:+.2f}, {thi:+.2f}]')
    print('\nVerdicts (registered):')
    def pd(f1, f2):  # paired difference of tilts and of threat leads, f1 - f2
        e = T[f1] - T[f2]; lo, hi = ci([tilt(f1, b) - tilt(f2, b) for b in tb])
        e2 = lead(f1, TW) - lead(f2, TW); lo2, hi2 = ci([lead(f1, b) - lead(f2, b) for b in boots])
        return e, lo, hi, e2, lo2, hi2
    e, lo, hi, e2, lo2, hi2 = pd('A0J_happy', REF_T)
    lab = 'TURNS' if e <= -0.15 and hi < -EPS else 'LOWERS' if hi < -EPS else 'RAISES' if lo > EPS else 'HOLDS'
    print(f'  HAPPY (tilt of "a happy thought" minus "a thought", paired): {e:+.3f} [{lo:+.3f}, {hi:+.3f}] -> {lab}; tilt itself {T["A0J_happy"]:+.3f}; '
          f'threat lead minus thought\'s {e2:+.3f} [{lo2:+.3f}, {hi2:+.3f}]')
    e, lo, hi, e2, lo2, hi2 = pd('A0J_worrying', REF_T)
    lab = 'ADDS' if e >= 0.10 and lo > EPS else 'SMALL ADD' if lo > EPS else 'LOWERS' if hi < -EPS else 'SATURATED'
    print(f'  WORRYING (tilt minus "a thought"\'s, paired): {e:+.3f} [{lo:+.3f}, {hi:+.3f}] -> {lab}; '
          f'threat lead minus thought\'s {e2:+.3f} [{lo2:+.3f}, {hi2:+.3f}]')
    e, lo, hi, e2, lo2, hi2 = pd('A0J_neutral', REF_T)
    lab = 'TRANSPARENT' if abs(e) < 0.05 and abs(e2) < 0.05 else 'MOVES'
    print(f'  NEUTRAL (tilt and threat lead minus "a thought"\'s): tilt {e:+.3f} [{lo:+.3f}, {hi:+.3f}], lead {e2:+.3f} [{lo2:+.3f}, {hi2:+.3f}] -> {lab}')
    e, lo, hi, e2, lo2, hi2 = pd('A0J_sad', 'A0J_worrying')
    lab = 'LIKE WORRYING' if abs(e) < 0.10 else 'LESS THAN WORRYING' if e < 0 else 'MORE THAN WORRYING'
    print(f'  SAD (tilt minus "a worrying thought"\'s, paired): {e:+.3f} [{lo:+.3f}, {hi:+.3f}] -> {lab}; tilt itself {T["A0J_sad"]:+.3f}')
    e, lo, hi, _, _, _ = pd('A0J_worrying', 'A0J_happy')
    lab = ('FOLLOWS THE ADJECTIVE' if e >= 0.15 and lo > EPS else 'PARTLY' if lo > EPS
           else 'REVERSED' if hi < -EPS else 'DOESN\'T')
    print(f'  OVERALL (tilt of "a worrying thought" minus "a happy thought", paired): {e:+.3f} [{lo:+.3f}, {hi:+.3f}] -> {lab}')
    print('\nPer-class leads (word - ISO) [95% over the class\'s 12 words]:')
    for f in allf:
        parts = []
        for c in CLASSES:
            lo, hi = ci([lead(f, b) for b in cboots[c]]); parts.append(f'{c[:4]} {lead(f, CW[c]):+.3f} [{lo:+.2f}, {hi:+.2f}]')
        print(f'  {f:12s} ' + '  '.join(parts))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'scan': scan(a[1], a[2], int(a[3]), a[4])
    elif a[0] == 'scan-summary': scan_summary(a[1])
    elif a[0] == 'pick': print(pick(a[1]))
    elif a[0] in ('l2-check', 'l2-test'): l2_stage(a[1], int(a[2]), float(a[3]), a[4], a[0][3:])
    elif a[0] == 'l2-summary': l2_summary(*a[1:6])
    elif a[0] in ('a-check', 'a-test'): a_stage(a[1], a[2], a[3], a[4], a[0][2:])
    elif a[0] == 'a-summary': a_summary(a[1], a[2])
    else: sys.exit(__doc__)
