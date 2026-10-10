"""Session 13 check of the "Universal Weight Subspace Hypothesis" (Kaushik et al., arXiv:2512.05117v3)
on the paper's own flagship collection: the Lots-of-LoRAs rank-16 adapters for Mistral-7B-Instruct-v0.2.

What it does, on the CPU, without downloading whole adapters:
  1. fetch    reads each adapter's safetensors header with HTTP range requests and downloads only the
              LoRA A and B matrices of q_proj in layers 0, 15 and 31 and v_proj in layer 15 (~2 MB per adapter).
  2. analyze  (a) groups adapters whose A matrices are near-identical (a shared random initialization);
              (b) repeats the paper's PCA of stacked "rank vectors" (A rows, B columns) for all adapters and
                  for each group, with random controls;
              (c) does the gauge-invariant version the paper's v3 suggests (whole updates dW = B A), against
                  a baseline of mutually orthogonal updates of the same sizes;
              (d) reconstructs the paper's nine held-out tasks (its Table 17) by projecting A and B onto the
                  top-16 directions of the other adapters, as its Algorithm 1 describes, and measures how much
                  of each update survives.

Usage:
  python3 tools/lora_subspace_check.py fetch DATA_DIR [N_ADAPTERS=300]
  python3 tools/lora_subspace_check.py analyze DATA_DIR OUT_JSON

Keep DATA_DIR outside the repository. Needs numpy only. Results of the session 13 run are in
notes/data/lora-subspace-check-session13.json and discussed in notes/kaushik-2025-universal-weight-subspace.md.
"""
import concurrent.futures as cf
import json
import os
import random
import struct
import sys
import urllib.request

import numpy as np

TENSORS = [(0, "q_proj"), (15, "q_proj"), (31, "q_proj"), (15, "v_proj")]
LAYERS = [f"L{l}.{m}" for l, m in TENSORS]
HELD_OUT = {39, 190, 280, 290, 391, 442, 1342, 1391, 1598}  # the paper's Table 17
PREFIX = "Lots-of-LoRAs/Mistral-7B-Instruct-v0.2-4b-r16-task"


def task_id(name):
    return int(name.rsplit("task", 1)[1])


# ---------------------------------------------------------------- fetch

def _get(url, start, end):
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}", "User-Agent": "Mozilla/5.0"})
    err = None
    for _ in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # network hiccups: retry
            err = e
    raise err


def _fetch_one(repo, out):
    path = os.path.join(out, repo.split("/")[-1] + ".npz")
    if os.path.exists(path):
        return
    url = f"https://huggingface.co/{repo}/resolve/main/adapter_model.safetensors"
    n = struct.unpack("<Q", _get(url, 0, 7))[0]
    hdr = json.loads(_get(url, 8, 8 + n - 1))
    arrs = {}
    for l, m in TENSORS:
        for ab in "AB":
            meta = hdr[f"base_model.model.model.layers.{l}.self_attn.{m}.lora_{ab}.weight"]
            assert meta["dtype"] == "F32"
            s, e = meta["data_offsets"]
            arrs[f"L{l}.{m}.lora_{ab}"] = np.frombuffer(_get(url, 8 + n + s, 8 + n + e - 1), dtype="<f4").reshape(meta["shape"])
    np.savez(path, **arrs)


def fetch(out, n_adapters):
    os.makedirs(out, exist_ok=True)
    with urllib.request.urlopen("https://huggingface.co/api/models?author=Lots-of-LoRAs&limit=5000") as r:
        ids = sorted(m["id"] for m in json.load(r) if m["id"].startswith(PREFIX))
    print("adapters available:", len(ids))
    must = [i for i in ids if task_id(i) in HELD_OUT]
    rest = [i for i in ids if i not in must]
    random.Random(13).shuffle(rest)
    chosen = must + rest[: n_adapters - len(must)]
    json.dump(chosen, open(os.path.join(out, "chosen.json"), "w"), indent=0)
    with cf.ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda repo: _fetch_one(repo, out), chosen))
    print("fetched", len(chosen))


# ---------------------------------------------------------------- analyze

def cum_evr(X, ks=(1, 4, 16, 17, 32, 64)):
    """Cumulative explained variance of the rows of X after removing the feature-wise mean (the paper's PCA)."""
    Xc = X - X.mean(0, keepdims=True)
    C = Xc.T @ Xc if Xc.shape[0] > Xc.shape[1] else Xc @ Xc.T
    e = np.clip(np.linalg.eigvalsh(C)[::-1], 0, None)
    c = np.cumsum(e / e.sum())
    return {k: round(float(c[k - 1]), 4) for k in ks}


def overlap(Q1, Q2):
    """Mean squared cosine of the principal angles between two subspaces (1 = identical, r/d = random)."""
    return float(np.linalg.norm(Q1.T @ Q2) ** 2 / Q1.shape[1])


def update_gram(A, B):
    """Frobenius inner products <B_i A_i, B_j A_j> without forming the 4096 x 4096 updates."""
    N, r, d_in = A.shape
    d_out = B.shape[1]
    Bm = B.transpose(1, 0, 2).reshape(d_out, N * r)
    Am = A.reshape(N * r, d_in)
    return ((Bm.T @ Bm) * (Am @ Am.T)).reshape(N, r, N, r).sum(axis=(1, 3))


def top_share(G, k=16):
    N = G.shape[0]
    H = np.eye(N) - 1.0 / N
    ev = np.clip(np.linalg.eigvalsh(H @ G @ H)[::-1], 0, None)
    return float(ev[:k].sum() / ev.sum())


def shared_init_groups(A, threshold=0.3):
    """Connected components of adapters whose flattened A matrices have cosine > threshold."""
    N = A.shape[0]
    F = A.reshape(N, -1)
    F = F / np.linalg.norm(F, axis=1, keepdims=True)
    C = F @ F.T
    lab = -np.ones(N, int)
    c = 0
    for s in range(N):
        if lab[s] >= 0:
            continue
        stack, lab[s] = [s], c
        while stack:
            u = stack.pop()
            for v in np.where((C[u] > threshold) & (lab < 0))[0]:
                lab[v] = c
                stack.append(v)
        c += 1
    sizes = np.bincount(lab)
    in_group = sizes[lab] > 1
    within = C[np.ix_(in_group, in_group)][np.triu_indices(int(in_group.sum()), 1)] if in_group.sum() > 1 else np.array([np.nan])
    return in_group, [int(s) for s in sizes[sizes > 1]], float(np.median(within)), C


def analyze(data, out_json):
    names = [c.split("/")[-1] for c in json.load(open(os.path.join(data, "chosen.json")))]
    files = [np.load(os.path.join(data, n + ".npz")) for n in names]
    held = np.array([task_id(n) in HELD_OUT for n in names])
    rng = np.random.default_rng(0)
    res = {"n_adapters": len(names), "held_out_tasks": sorted(HELD_OUT), "layers": {}}
    for L in LAYERS:
        A_all = np.stack([f[L + ".lora_A"] for f in files]).astype(np.float64)  # N x r x d_in
        B_all = np.stack([f[L + ".lora_B"] for f in files]).astype(np.float64)  # N x d_out x r
        N, r, d_in = A_all.shape
        d_out = B_all.shape[1]
        shared, group_sizes, within_cos, C = shared_init_groups(A_all)
        out = {"r": r, "d_in": d_in, "d_out": d_out,
               "shared_init_group_sizes": group_sizes,
               "shared_init_within_cos_median": round(within_cos, 3),
               "held_out_in_shared_group": int((shared & held).sum()),
               "A_entry_std": round(float(A_all.std()), 5),
               "kaiming_uniform_std": round(float(1 / np.sqrt(d_in) / np.sqrt(3)), 5),
               "groups": {}}
        for g, mask in [("all", np.ones(N, bool)), ("shared_init", shared), ("independent", ~shared)]:
            A, B = A_all[mask], B_all[mask]
            n = len(A)
            QB = [np.linalg.qr(b)[0] for b in B]
            pairs = [(i, j) for i, j in rng.integers(0, n, size=(400, 2)) if i != j]
            G = update_gram(A, B)
            dn = np.sqrt(np.diag(G))
            cosG = (G / np.outer(dn, dn))[np.triu_indices(n, 1)]
            out["groups"][g] = {
                "N": n,
                "paper_pca_A_rows": cum_evr(A.reshape(n * r, d_in)),
                "paper_pca_B_cols": cum_evr(B.transpose(0, 2, 1).reshape(n * r, d_out)),
                "B_colspace_overlap_vs_random": round(np.mean([overlap(QB[i], QB[j]) for i, j in pairs]) / (r / d_out), 1),
                "update_top16_share": round(top_share(G), 4),
                "update_top16_share_orthogonal_baseline": round(top_share(np.diag(np.diag(G))), 4),
                "update_pairwise_cos_mean": round(float(cosG.mean()), 4),
            }
        # random controls for the A-side PCA
        bound = 1 / np.sqrt(d_in)
        out["control_A_independent_inits"] = cum_evr(rng.uniform(-bound, bound, size=(N * r, d_in)))
        out["control_B_random_directions"] = cum_evr(rng.normal(size=(N * r, d_out)))
        # held-out reconstruction as in Algorithm 1 (affine: mean + projection onto top-16), A and B separately
        tr = ~held

        def basis(X, k=16):
            mu = X.mean(0, keepdims=True)
            _, V = np.linalg.eigh((X - mu).T @ (X - mu))
            return mu, V[:, ::-1][:, :k]

        muA, UA = basis(A_all[tr].reshape(-1, d_in))
        muB, UB = basis(B_all[tr].transpose(0, 2, 1).reshape(-1, d_out))
        rec = []
        for j in np.where(held)[0]:
            Ah = muA + (A_all[j] - muA) @ UA @ UA.T
            Bh = (muB + (B_all[j].T - muB) @ UB @ UB.T).T
            dW, dWh = B_all[j] @ A_all[j], Bh @ Ah
            rec.append([float(np.sum(dW * dWh) / (np.linalg.norm(dW) * np.linalg.norm(dWh))),
                        float(np.linalg.norm(dWh) / np.linalg.norm(dW)),
                        float(np.linalg.norm(dW - dWh) / np.linalg.norm(dW)),
                        float(np.linalg.norm((A_all[j] - muA) @ UA) ** 2 / np.linalg.norm(A_all[j] - muA) ** 2)])
        rec = np.array(rec).mean(0)
        out["held_out_reconstruction_k16"] = {"cos_with_original_update": round(rec[0], 4),
                                              "norm_ratio": round(rec[1], 4),
                                              "relative_error": round(rec[2], 4),
                                              "share_of_A_in_top16": round(rec[3], 4)}
        res["layers"][L] = out
        print(L, json.dumps(out), flush=True)
    json.dump(res, open(out_json, "w"), indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "fetch":
        fetch(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 300)
    elif sys.argv[1] == "analyze":
        analyze(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
