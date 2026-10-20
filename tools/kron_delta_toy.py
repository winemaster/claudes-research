"""Session 19: a toy check of the Kronecker Delta Rule (Hartl, Zolyomi et al. 2026, arXiv:2610.26834).

Stores T random (key, value) pairs in a d_v x d_k matrix memory with three update rules and
measures, for every stored pair, how far its association strength v_i^T S k_i has drifted from
1 by the end of the sequence (interference from later writes). Also checks the paper's
interference identity (5) on one step.

    python3 tools/kron_delta_toy.py [--dk 32] [--dv 32] [--seeds 20]
"""
import argparse, json
import numpy as np

def unit(x):
    return x / np.linalg.norm(x, axis=-1, keepdims=True)

def run(rule, K, V, beta=1.0, c=1.0):
    dk, dv = K.shape[1], V.shape[1]
    S = np.zeros((dv, dk))
    for k, v in zip(K, V):
        if rule == 'hebbian':          # S += v k^T
            S = S + np.outer(v, k)
        elif rule == 'delta':          # S -= beta (S k - v) k^T
            S = S - beta * np.outer(S @ k - v, k)
        elif rule == 'kronecker':      # S -= beta (v^T S k - c) v k^T
            S = S - beta * (v @ S @ k - c) * np.outer(v, k)
    return S

def strengths(S, K, V):
    return np.einsum('ti,ij,tj->t', V, S, K)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dk', type=int, default=32)
    ap.add_argument('--dv', type=int, default=32)
    ap.add_argument('--seeds', type=int, default=20)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    # identity check (5): Delta(v_i^T S k_i) = -beta (v_t^T S k_t - c) (v_i.v_t)(k_t.k_i)
    K = unit(rng.standard_normal((40, a.dk))); V = unit(rng.standard_normal((40, a.dv)))
    S = run('kronecker', K[:39], V[:39], beta=0.7)
    kt, vt, b, c = K[39], V[39], 0.7, 1.0
    S2 = S - b * (vt @ S @ kt - c) * np.outer(vt, kt)
    lhs = strengths(S2, K[:39], V[:39]) - strengths(S, K[:39], V[:39])
    rhs = -b * (vt @ S @ kt - c) * (V[:39] @ vt) * (K[:39] @ kt)
    print('identity (5) max abs error: %.2e' % np.abs(lhs - rhs).max())
    results = {}
    for T in [16, 64, 256, 1024]:
        row = {}
        for rule in ['hebbian', 'delta', 'kronecker']:
            errs, last = [], []
            for s in range(a.seeds):
                r = np.random.default_rng(1000 + s)
                K = unit(r.standard_normal((T, a.dk))); V = unit(r.standard_normal((T, a.dv)))
                S = run(rule, K, V)
                st = strengths(S, K, V)
                errs.append(np.mean(np.abs(st - 1))); last.append(np.mean(np.abs(st[: T // 4] - 1)))
            row[rule] = {'mean_abs_drift_all': float(np.mean(errs)), 'mean_abs_drift_first_quarter': float(np.mean(last))}
        results[T] = row
        print('T=%5d  ' % T + '  '.join('%s: all %.3f, oldest quarter %.3f' % (k, v['mean_abs_drift_all'], v['mean_abs_drift_first_quarter']) for k, v in row.items()))
    print('(d_k = %d, d_v = %d: the Kronecker rule can hold up to d_k*d_v = %d scalar associations exactly; delta up to d_k = %d value vectors)' % (a.dk, a.dv, a.dk * a.dv, a.dk))
    if a.out:
        json.dump({'dk': a.dk, 'dv': a.dv, 'seeds': a.seeds, 'results': results}, open(a.out, 'w'), indent=1)

if __name__ == '__main__':
    main()
