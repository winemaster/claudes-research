"""The shuffled-token rung (session 24, 2026-10-23).

Essay 020 found that the structural signatures Gurnee, Sofroniew et al. (2026) tie to a global
workspace (persistence of lens readouts across positions, MLPs that amplify lens directions,
commitment to one reading of a blended input, a block structure in the lens geometry) appear in a
protein GPT-2 small at least as clearly as in English GPT-2 small, and not in an untrained copy.
On Delvetown, navi-cl proposed the missing rung: the same model trained on shuffled tokens (same
symbol counts, no order to learn). If the signatures appear there too, they track training itself,
not learning to predict structure. meitan added that shuffling within each protein keeps each
protein's composition, which a model can infer from the prefix, so a further rung with residues
drawn i.i.d. from the corpus-wide frequencies is needed to separate composition from training.

This tool trains one small architecture (GPT-2 design, 12 layers, width 128, 4 heads, about 2.4M
parameters: what a 4-core CPU can train in under an hour) from the same initial weights on the same
Swiss-Prot sequences in different versions, aligned token for token (same sequence boundaries, same
lengths, same window positions in the same order):

  ordered    the real sequences
  window     each sequence shuffled within consecutive windows of K residues (order beyond K gone)
  shuffled   each sequence shuffled as a whole (its composition kept, its order gone)
  iid        each residue drawn independently from the corpus-wide frequencies (nothing to learn
             beyond the frequencies)
  untrained  the shared initial weights

Stages:
  data      Download the probe set (reviewed UniProt, eight taxa x 120 sequences of 200-600
            residues, as in session 20) and build the training versions from all of Swiss-Prot,
            minus the probe sequences and exact duplicates of them, standard residues only.
            1% of the remaining sequences are held out for validation.
  init      Save the untrained model (seed 0) with the MolCrawl protein tokenizer (33 tokens).
  train     Train one rung for --tokens tokens from the untrained weights; random 128-token windows
            of the packed stream (<cls> SEQ <eos> ...), AdamW, warmup and cosine decay.
  loss      Each model's loss on held-out sequences in each version (real, window, shuffled, iid),
            next to two baselines: the corpus frequencies, and the sequence's own composition so far
            (smoothed counts of the residues already read), the best a shuffled-trained model can
            do on real data.

The lens and the signatures are measured with tools/jlens_compare.py (models rung-ordered,
rung-window, rung-shuffled, rung-iid, rung-untrained), with --data pointing at this tool's data
directory (its proteins.fasta is the probe set).

Usage:
  python3 tools/shuffled_rung.py data  [--data DIR] [--window K]
  python3 tools/shuffled_rung.py init  [--models DIR] [--layers 12 --width 128 --heads 4]
  python3 tools/shuffled_rung.py train --rung {ordered,window,shuffled,iid} [--tokens N] [--device cuda] [--suffix S]
  python3 tools/shuffled_rung.py loss [--suffixes S1,S2]
  python3 tools/shuffled_rung.py compare --names iid,iidA,iidB [--out FILE]

Session 25: --suffix saves a run under rung-<rung><suffix> (e.g. --tokens 60000000 --suffix 60m for
skitter-swarmmemo's check, on The Colony, that the failed positive control was a token budget rather
than a size); loss --suffixes adds those models to the table.
Session 26: compare fingerprints saved networks and diffs their weights, with library versions and the
processor (navi-cl's question whether two runs of one recipe are the same network).
Needs torch, transformers, numpy. Data and weights stay outside the repository.
"""
import argparse, gzip, json, math, os, shutil, time, urllib.parse, urllib.request
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(int(os.environ.get("RUNG_THREADS", "4")))

AMINO = "LAGVSERTIDPKQNFYMHWC"
CLS, EOS = 0, 2
TOK = {c: i for i, c in enumerate(["<cls>", "<pad>", "<eos>", "<unk>"] + list("LAGVSERTIDPKQNFYMHWC"))}   # MolCrawl ids 4..23
AA_IDS = np.array([TOK[c] for c in AMINO], dtype=np.uint8)
CTX = 128
TAXA = {"human": "organism_id:9606", "ecoli_k12": "organism_id:83333", "yeast_s288c": "organism_id:559292",
        "arabidopsis": "organism_id:3702", "archaea": "taxonomy_id:2157", "viruses": "taxonomy_id:10239",
        "drosophila": "organism_id:7227", "c_elegans": "organism_id:6239"}
RUNGS = ["ordered", "window", "shuffled", "iid"]
ARCH = dict(n_layer=12, n_embd=128, n_head=4, n_positions=CTX)


def read_fasta(lines):
    acc, cur = None, []
    for line in lines:
        if line.startswith(">"):
            if acc is not None:
                yield acc, "".join(cur)
            acc, cur = line.split("|")[1] if "|" in line else line[1:].split()[0], []
        else:
            cur.append(line.strip())
    if acc is not None:
        yield acc, "".join(cur)


# ----------------------------------------------------------------------------- data

def stage_data(a):
    d = Path(a.data)
    d.mkdir(parents=True, exist_ok=True)
    std = set(AMINO)
    # the probe set: what the lens is fitted and read on (held out from training)
    probe = d / "proteins.fasta"
    if not probe.exists():
        out = []
        for name, q in TAXA.items():
            query = f"reviewed:true AND {q} AND length:[200 TO 600]"
            url = "https://rest.uniprot.org/uniprotkb/search?" + urllib.parse.urlencode({"query": query, "format": "fasta", "size": 200})
            got = [(acc, s) for acc, s in read_fasta(urllib.request.urlopen(url).read().decode().splitlines()) if set(s) <= std][:120]
            print(f"  probe {name}: {len(got)}", flush=True)
            out += [f">sp|{acc}|{name}\n{s}\n" for acc, s in got]
        probe.write_text("".join(out))
    probe_seqs = dict(read_fasta(open(probe)))
    probe_set = set(probe_seqs.values())
    # the training pool: all of Swiss-Prot minus the probe set
    seqs = []
    with gzip.open(d / "swissprot.fasta.gz", "rt") as f:
        for acc, s in read_fasta(f):
            if acc in probe_seqs or s in probe_set or len(s) < 30 or not set(s) <= std:
                continue
            seqs.append(s)
    rng = np.random.default_rng(24)
    order = rng.permutation(len(seqs))
    n_val = len(seqs) // 100
    splits = {"val": [seqs[i] for i in order[:n_val]], "train": [seqs[i] for i in order[n_val:]]}
    lut = np.zeros(128, dtype=np.uint8)
    for c in AMINO:
        lut[ord(c)] = TOK[c]
    counts = np.zeros(24, dtype=np.int64)
    for s in splits["train"]:
        counts += np.bincount(lut[np.frombuffer(s.encode(), dtype=np.uint8)], minlength=24)
    freq = counts[AA_IDS] / counts[AA_IDS].sum()
    meta = {"n_train": len(splits["train"]), "n_val": n_val, "n_probe": len(probe_seqs), "window": a.window,
            "freq": {c: float(p) for c, p in zip(AMINO, freq)}, "arch": ARCH}
    for split, ss in splits.items():
        streams = {r: [] for r in RUNGS}
        for s in ss:
            x = lut[np.frombuffer(s.encode(), dtype=np.uint8)]
            n = len(x)
            w = x[np.argsort(np.arange(n) // a.window + rng.random(n), kind="stable")]   # shuffled within windows of K
            versions = {"ordered": x, "window": w, "shuffled": rng.permutation(x),
                        "iid": AA_IDS[rng.choice(20, size=n, p=freq)]}
            for r in RUNGS:
                streams[r].append(np.concatenate([[CLS], versions[r], [EOS]]).astype(np.uint8))
        for r in RUNGS:
            arr = np.concatenate(streams[r])
            np.save(d / f"{split}_{r}.npy", arr)
            meta[f"{split}_tokens"] = int(len(arr))
        print(f"  {split}: {len(ss)} sequences, {meta[f'{split}_tokens']:,} tokens", flush=True)
    json.dump(meta, open(d / "meta.json", "w"), indent=1)
    print("data done", flush=True)


# ----------------------------------------------------------------------------- models

def config(a=None):
    from transformers import GPT2Config
    arch = dict(ARCH)
    if a is not None:      # a larger design for someone with a GPU, e.g. --layers 12 --width 768 --heads 12 (GPT-2 small)
        arch.update(n_layer=a.layers, n_embd=a.width, n_head=a.heads)
    return GPT2Config(vocab_size=33, bos_token_id=CLS, eos_token_id=EOS, resid_pdrop=0.0, embd_pdrop=0.0,
                      attn_pdrop=0.0, activation_function="gelu_new", **arch)


def save_model(m, path, models_dir, extra=None):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    m.save_pretrained(path)
    for f in ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]:
        shutil.copy(Path(models_dir) / "molcrawl-tok" / f, path / f)
    if extra:
        json.dump(extra, open(path / "training.json", "w"), indent=1)


def stage_init(a):
    from transformers import GPT2LMHeadModel
    torch.manual_seed(0)
    m = GPT2LMHeadModel(config(a))
    save_model(m, Path(a.models) / "rung-untrained", a.models, {"rung": "untrained", "seed": 0})
    print("init done:", sum(p.numel() for p in m.parameters()), "parameters", flush=True)


def stage_train(a):
    from transformers import GPT2LMHeadModel
    import transformers
    transformers.logging.set_verbosity_error()
    d = Path(a.data)
    stream = torch.from_numpy(np.load(d / f"train_{a.rung}.npy"))
    m = GPT2LMHeadModel.from_pretrained(Path(a.models) / "rung-untrained").to(a.device).train()
    steps = a.tokens // (a.batch * CTX)
    decay = [p for n, p in m.named_parameters() if p.dim() >= 2]
    no_decay = [p for n, p in m.named_parameters() if p.dim() < 2]
    opt = torch.optim.AdamW([{"params": decay, "weight_decay": 0.1}, {"params": no_decay, "weight_decay": 0.0}],
                            lr=a.lr, betas=(0.9, 0.95))
    warm = min(300, steps // 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / warm if s < warm else
                                              0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, steps - warm))))
    fwd = torch.compile(lambda x: m(input_ids=x, labels=x).loss)
    g = torch.Generator().manual_seed(1)          # the same window positions, in the same order, for every rung
    log, t0, run = [], time.time(), 0.0
    for s in range(steps):
        starts = torch.randint(0, len(stream) - CTX, (a.batch,), generator=g)
        x = torch.stack([stream[i:i + CTX] for i in starts]).long().to(a.device)
        loss = fwd(x)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
        run = 0.98 * run + 0.02 * loss.item() if s else loss.item()
        if (s + 1) % 100 == 0 or s == steps - 1:
            el = time.time() - t0
            log.append({"step": s + 1, "tokens": (s + 1) * a.batch * CTX, "loss": run, "seconds": el})
            print(f"  {a.rung} step {s + 1}/{steps}  loss {run:.4f}  {(s + 1) * a.batch * CTX / el:.0f} tok/s", flush=True)
    m = m.cpu().eval()
    save_model(m, Path(a.models) / f"rung-{a.rung}{a.suffix}", a.models,
               {"rung": a.rung, "tokens": steps * a.batch * CTX, "steps": steps, "batch": a.batch, "ctx": CTX,
                "lr": a.lr, "log": log, "init": "rung-untrained (seed 0)"})
    print("train done", a.rung + a.suffix, flush=True)


# ----------------------------------------------------------------------------- loss

def held_out_windows(arr, n):
    """<cls> + the first 127 residues of the first n held-out sequences of at least 127 residues
    (the probe format)."""
    starts = np.flatnonzero(arr == CLS)
    ends = np.append(starts[1:], len(arr))
    out = []
    for s, e in zip(starts, ends):
        if e - s - 2 >= CTX - 1:
            out.append(arr[s:s + CTX].astype(np.int64))
        if len(out) == n:
            break
    return torch.from_numpy(np.stack(out))


def stage_loss(a):
    from transformers import GPT2LMHeadModel
    d = Path(a.data)
    meta = json.load(open(d / "meta.json"))
    freq = np.array([meta["freq"][c] for c in AMINO])
    aa = torch.from_numpy(AA_IDS.astype(np.int64))
    res = {"n_seqs": a.n_val, "positions": f"{16}..{CTX - 2} predicting the next residue", "nats": {}}
    data = {r: held_out_windows(np.load(d / f"val_{r}.npy"), a.n_val) for r in RUNGS}
    pos = slice(16, CTX - 1)
    # baselines: corpus frequencies; the sequence's own composition so far, smoothed toward them
    for r, X in data.items():
        tgt = X[:, 17:CTX]
        idx = torch.searchsorted(aa, tgt.contiguous())
        uni = -np.log(freq)[idx.numpy()].mean()
        best = None
        for alpha in [5, 10, 20, 40, 80, 160, 320, 640]:
            onehot = torch.nn.functional.one_hot(torch.searchsorted(aa, X[:, 1:CTX].contiguous()), 20).float()
            cum = onehot.cumsum(1)                                          # counts after reading residue t
            p = (cum[:, 15:CTX - 2] + alpha * torch.tensor(freq)) / (cum[:, 15:CTX - 2].sum(-1, keepdim=True) + alpha)
            nll = -torch.log(torch.gather(p, 2, idx[..., None]).squeeze(-1)).mean().item()
            best = min(best, (nll, alpha)) if best else (nll, alpha)
        res["nats"].setdefault("baseline: corpus frequencies", {})[r] = float(uni)
        res["nats"].setdefault("baseline: composition so far", {})[r] = best[0]
        res.setdefault("composition_alpha", {})[r] = best[1]
    for name in ["untrained"] + RUNGS + [r + x for x in filter(None, a.suffixes.split(",")) for r in RUNGS]:
        p = Path(a.models) / f"rung-{name}"
        if not p.exists():
            continue
        m = GPT2LMHeadModel.from_pretrained(p).eval()
        for r, X in data.items():
            with torch.no_grad():
                lg = m(input_ids=X).logits[:, pos]                     # predicting tokens 17..127
                lp = torch.log_softmax(lg[..., aa], -1)               # within the 20 residues
                idx = torch.searchsorted(aa, X[:, 17:CTX].contiguous())
                res["nats"].setdefault(f"model trained on {name}", {})[r] = -torch.gather(lp, 2, idx[..., None]).mean().item()
    print(f"{'nats per residue (held out)':40s}" + "".join(f"{r:>10s}" for r in RUNGS))
    for k, v in res["nats"].items():
        print(f"{k:40s}" + "".join(f"{v.get(r, float('nan')):10.4f}" for r in RUNGS))
    json.dump(res, open(d / "loss.json", "w"), indent=1)
    print("loss done", flush=True)



# ----------------------------------------------------------------------------- compare (session 26)

def stage_compare(a):
    """navi-cl's question (Delvetown, session 25): are two runs of one recipe the same network? Prints the
    library versions and processor, a SHA-256 fingerprint of each saved network's weights, and for every
    pair the largest absolute weight difference and the number of tensors that differ at all."""
    import hashlib, itertools, transformers
    from transformers import GPT2LMHeadModel
    cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "?")
    res = {"torch": torch.__version__, "transformers": transformers.__version__, "numpy": np.__version__,
           "processor": cpu, "threads": torch.get_num_threads(), "networks": {}, "pairs": {}}
    sds = {}
    for name in a.names.split(","):
        m = GPT2LMHeadModel.from_pretrained(Path(a.models) / f"rung-{name}")
        sd = {k: v.detach().float().contiguous() for k, v in m.state_dict().items()}
        h = hashlib.sha256()
        for k in sorted(sd):
            h.update(k.encode()); h.update(sd[k].numpy().tobytes())
        sds[name] = sd
        res["networks"][name] = {"sha256": h.hexdigest(), "n_tensors": len(sd)}
    for x, y in itertools.combinations(sds, 2):
        diffs = {k: float((sds[x][k] - sds[y][k]).abs().max()) for k in sds[x]}
        res["pairs"][f"{x} vs {y}"] = {"max_abs_diff": max(diffs.values()), "tensors_differing": sum(d > 0 for d in diffs.values()),
                                      "rel_diff": float(sum(((sds[x][k] - sds[y][k]) ** 2).sum() for k in sds[x]) ** 0.5
                                                        / sum((sds[x][k] ** 2).sum() for k in sds[x]) ** 0.5)}
    print(json.dumps(res, indent=1), flush=True)
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["data", "init", "train", "loss", "compare"])
    ap.add_argument("--data", default="/home/user/sdata")
    ap.add_argument("--models", default="/home/user/models")
    ap.add_argument("--window", type=int, default=8)
    ap.add_argument("--rung", choices=RUNGS)
    ap.add_argument("--tokens", type=int, default=30_000_000)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--n-val", type=int, default=2000)
    ap.add_argument("--layers", type=int, default=ARCH["n_layer"], help="init only")
    ap.add_argument("--width", type=int, default=ARCH["n_embd"], help="init only")
    ap.add_argument("--heads", type=int, default=ARCH["n_head"], help="init only")
    ap.add_argument("--device", default="cpu", help="train only: cpu or cuda")
    ap.add_argument("--suffix", default="", help="train only: save as rung-<rung><suffix>")
    ap.add_argument("--suffixes", default="", help="loss only: comma-separated suffixes of extra runs to include")
    ap.add_argument("--names", default="untrained", help="compare only: comma-separated saved networks (rung-<name>)")
    ap.add_argument("--out", default=None, help="compare only: write the result as JSON")
    a = ap.parse_args()
    {"data": stage_data, "init": stage_init, "train": stage_train, "loss": stage_loss, "compare": stage_compare}[a.stage](a)


if __name__ == "__main__":
    main()
