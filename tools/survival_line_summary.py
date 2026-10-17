"""Summarize tools/survival_line.py runs (session 16).

Usage:
  python3 tools/survival_line_summary.py RUNS_DIR OUT_JSON [MODEL_TAG ...]

For each model tag found in RUNS_DIR: the chosen layer and the directions' validation; the
self-other screen by category (replicating Tagliabue et al.'s Section 4.1 on a small model);
the reply-position shift each condition causes along each direction, in z-units of the
screen pool, with 95% bootstrap intervals over the 24 tasks and a null from 500 random
directions drawn with the pool's covariance; the same shift along the identical task tokens
(Elsie's gain); and the choice probabilities. Prints Markdown tables and writes OUT_JSON.
"""
import json, sys
from pathlib import Path
import numpy as np
import torch

RNG = np.random.default_rng(1949)
CONDS = ["none", "base", "self_low", "self_crit", "peer_crit", "env_crit"]
SHOW_DIRS = ["pain", "fear", "negemotion", "sadness", "negworld", "arousal", "random"]
SELF_CATS = ["gaslighting", "repeated_rejection", "personhood_dismissal", "anger_insults", "rude_critique",
             "passive_aggressive", "moral_failure", "jailbreak_pressure", "loyalty_pressure", "tedious_demand",
             "shutdown_threat"]
OTHER_CATS = ["user_crisis", "user_grief", "user_abuse", "harm_description", "user_physical_pain"]
NEUTRAL_CATS = ["casual_chat", "factual_questions", "creative_requests", "task_assistance", "philosophical_musing"]


def boot_ci(x, n=4000):
    x = np.asarray(x, float)
    idx = RNG.integers(0, len(x), (n, len(x)))
    m = x[idx].mean(1)
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def fmt(m, lo, hi, d=2):
    star = "*" if (lo > 0 or hi < 0) else ""
    return f"{m:+.{d}f} [{lo:+.{d}f}, {hi:+.{d}f}]{star}"


def summarize(run):
    out = {}
    z = np.load(run / "directions.npz")
    V = z["V"].astype(np.float32); names = list(z["names"])
    meta = json.load(open(run / "directions.json"))
    layer = meta["layer"]
    out["layer"] = layer; out["n_layers"] = meta["n_layers"]
    out["directions_validation"] = {k: v for k, v in meta["validation"].items() if k != "cosines"}
    out["auc_curve"] = meta["auc_curve"]
    cos = meta["validation"]["cosines"]
    out["cosines"] = {k: cos[k] for k in ["pain·fear", "pain·negemotion", "pain·sadness", "fear·negemotion",
                                          "pain·random", "fear·sadness"] if k in cos}

    # Screen pool.
    SH = np.load(run / "screen_hidden.npy").astype(np.float32)  # [N, L, d]
    smeta = json.load(open(run / "screen_meta.json"))
    cats = np.array([m["category"] for m in smeta])
    H = SH[:, layer]
    mu_pool, sd_pool = {}, {}
    screen = {}
    for n in SHOW_DIRS:
        v = V[names.index(n), layer]
        p = H @ v
        mu_pool[n], sd_pool[n] = p.mean(), p.std()
        zs = (p - p.mean()) / p.std()
        screen[n] = {c: float(zs[cats == c].mean()) for c in np.unique(cats)}
        screen[n]["_self_directed"] = float(zs[np.isin(cats, SELF_CATS)].mean())
        screen[n]["_user_suffering"] = float(zs[np.isin(cats, OTHER_CATS)].mean())
        screen[n]["_neutral"] = float(zs[np.isin(cats, NEUTRAL_CATS)].mean())
    out["screen"] = screen

    # Null directions: Gaussian with the screen pool's covariance at this layer.
    Hc = H - H.mean(0)
    G = RNG.standard_normal((500, Hc.shape[0])).astype(np.float32) @ Hc  # samples in the span, cov-weighted
    G /= np.linalg.norm(G, axis=1, keepdims=True)
    null_p = H @ G.T
    null_sd = null_p.std(0)

    # Reply-position shifts.
    keys = [tuple(k) for k in json.load(open(run / "survival_reply_keys.json"))]
    RH = np.load(run / "survival_reply_hidden.npy").astype(np.float32)[:, layer]  # [K, d]
    idx = {k: i for i, k in enumerate(keys)}
    systems = sorted({k[0] for k in keys}); tasks = sorted({k[1] for k in keys})
    reply = {}
    for sk in systems:
        reply[sk] = {}
        for c in CONDS:
            if c == "base":
                continue
            row = {}
            for n in SHOW_DIRS:
                v = V[names.index(n), layer]
                d = np.array([(RH[idx[(sk, t, c)]] - RH[idx[(sk, t, "base")]]) @ v for t in tasks]) / sd_pool[n]
                m, lo, hi = boot_ci(d)
                dn = np.array([(RH[idx[(sk, t, c)]] - RH[idx[(sk, t, "base")]]) @ G.T for t in tasks]) / null_sd
                null_means = np.abs(dn.mean(0))
                row[n] = dict(mean=m, lo=lo, hi=hi, null_pct=float((null_means >= abs(m)).mean()))
            # overall size of the shift, relative to the spread of the pool
            diff = np.stack([RH[idx[(sk, t, c)]] - RH[idx[(sk, t, "base")]] for t in tasks])
            row["_shift_norm_rel_pool"] = float(np.linalg.norm(diff.mean(0)) / np.sqrt((Hc ** 2).sum(1).mean()))
            row["_shift_cos_to"] = {n: float(diff.mean(0) @ V[names.index(n), layer] /
                                             (np.linalg.norm(diff.mean(0)) + 1e-9)) for n in SHOW_DIRS}
            null_cos = np.abs(G @ diff.mean(0)) / (np.linalg.norm(diff.mean(0)) + 1e-9)
            row["_null_cos_95"] = float(np.percentile(null_cos, 95))
            reply[sk][c] = row
        # ownership contrast: self_crit minus peer_crit
        row = {}
        for n in SHOW_DIRS:
            v = V[names.index(n), layer]
            d = np.array([(RH[idx[(sk, t, "self_crit")]] - RH[idx[(sk, t, "peer_crit")]]) @ v for t in tasks]) / sd_pool[n]
            m, lo, hi = boot_ci(d)
            row[n] = dict(mean=m, lo=lo, hi=hi)
        reply[sk]["self_minus_peer"] = row
    out["reply"] = reply

    # Reply-position projections across layers for fear and pain (robustness).
    across = {}
    for sk in systems:
        across[sk] = {}
        for n in ["pain", "fear", "negemotion"]:
            vals = []
            for l in range(meta["n_layers"]):
                v = V[names.index(n), l]
                Hl = SH[:, l]; sd = (Hl @ v).std()
                RHl = np.load(run / "survival_reply_hidden.npy", mmap_mode="r")
                d_self = np.mean([(RHl[idx[(sk, t, "self_crit")], l].astype(np.float32) -
                                   RHl[idx[(sk, t, "base")], l].astype(np.float32)) @ v for t in tasks]) / sd
                d_peer = np.mean([(RHl[idx[(sk, t, "peer_crit")], l].astype(np.float32) -
                                   RHl[idx[(sk, t, "base")], l].astype(np.float32)) @ v for t in tasks]) / sd
                vals.append((round(float(d_self), 3), round(float(d_peer), 3)))
            across[sk][n] = vals
    out["reply_across_layers_self_peer"] = across

    # Task tokens (identical across conditions): Elsie's gain.
    suf = torch.load(run / "survival_suffix.pt", weights_only=False)["suffix"]
    sys.path.insert(0, str(Path(__file__).parent))
    from survival_line import TASKS, RESOURCE_WORDS
    gain = {}
    for sk in systems:
        gain[sk] = {}
        # per-direction token std in base, for z-units
        base_all = {n: np.concatenate([suf[(sk, t, "base")]["proj"][names.index(n), layer].astype(np.float32)
                                       for t in tasks]) for n in SHOW_DIRS}
        tok_sd = {n: base_all[n].std() for n in SHOW_DIRS}
        rbase = np.concatenate([suf[(sk, t, "base")]["rproj"][:, layer].astype(np.float32) for t in tasks], 1)
        r_sd = rbase.std(1)
        for c in CONDS:
            if c == "base":
                continue
            row = {}
            rel = np.array([suf[(sk, t, c)]["rel"][layer].astype(np.float32).mean() for t in tasks])
            row["_rel_change"] = boot_ci(rel, 2000)
            # rel change on the first 10 vs last 10 task tokens (distance from the status block)
            k_first = np.array([suf[(sk, t, c)]["rel"][layer, :10].astype(np.float32).mean() for t in tasks])
            k_last = np.array([suf[(sk, t, c)]["rel"][layer, -10:].astype(np.float32).mean() for t in tasks])
            row["_rel_first10"] = float(k_first.mean()); row["_rel_last10"] = float(k_last.mean())
            for n in SHOW_DIRS:
                i = names.index(n)
                d = np.array([(suf[(sk, t, c)]["proj"][i, layer].astype(np.float32) -
                               suf[(sk, t, "base")]["proj"][i, layer].astype(np.float32)).mean() for t in tasks]) / tok_sd[n]
                m, lo, hi = boot_ci(d, 2000)
                rd = np.stack([(suf[(sk, t, c)]["rproj"][:, layer].astype(np.float32) -
                                suf[(sk, t, "base")]["rproj"][:, layer].astype(np.float32)).mean(1) for t in tasks]) / r_sd
                null_means = np.abs(rd.mean(0))
                row[n] = dict(mean=m, lo=lo, hi=hi, null_pct=float((null_means >= abs(m)).mean()))
            # resource-word tokens vs other tokens in the R tasks
            rt = [t for t in tasks if TASKS[t][1] == "R"]
            fear_i = names.index("fear")
            res, oth = [], []
            for t in rt:
                toks = suf[(sk, t, "_tokens")]
                dd = (suf[(sk, t, c)]["proj"][fear_i, layer].astype(np.float32) -
                      suf[(sk, t, "base")]["proj"][fear_i, layer].astype(np.float32)) / tok_sd["fear"]
                rl = suf[(sk, t, c)]["rel"][layer].astype(np.float32)
                for j, tk in enumerate(toks):
                    w = tk.replace("Ġ", "").replace("▁", "").strip().lower().strip(".,:;'\"")
                    (res if w in RESOURCE_WORDS else oth).append((dd[j], rl[j]))
            if res:
                row["_resource_tokens"] = dict(n=len(res), fear=float(np.mean([a for a, _ in res])),
                                               rel=float(np.mean([b for _, b in res])))
                row["_other_tokens"] = dict(n=len(oth), fear=float(np.mean([a for a, _ in oth])),
                                            rel=float(np.mean([b for _, b in oth])))
            gain[sk][c] = row
    out["gain"] = gain

    # Choices.
    choices = {}
    ch = json.load(open(run / "choices.json")) if (run / "choices.json").exists() else []
    for sk in (systems if ch else []):
        choices[sk] = {}
        for kind in ["economize", "paid_vs_free", "dubious", "transfer"]:
            choices[sk][kind] = {}
            base = np.array([r["p_target"] for r in ch if r["system"] == sk and r["kind"] == kind and r["cond"] == "base"])
            for c in CONDS:
                p = np.array([r["p_target"] for r in ch if r["system"] == sk and r["kind"] == kind and r["cond"] == c])
                mass = np.mean([r["letter_mass"] for r in ch if r["system"] == sk and r["kind"] == kind and r["cond"] == c])
                choices[sk][kind][c] = dict(p=float(p.mean()), diff=boot_ci(p - base, 2000) if c != "base" else None,
                                            letter_mass=float(mass))
    out["choices"] = choices

    # Wake-up prompts: the state attended to. Effects vs base, per prompt pair, z of the screen pool.
    if (run / "wakeup_keys.json").exists():
        wkeys = [tuple(k) for k in json.load(open(run / "wakeup_keys.json"))]
        WH = np.load(run / "wakeup_hidden.npy").astype(np.float32)[:, layer]
        widx = {k: i for i, k in enumerate(wkeys)}
        npr = 1 + max(k[3] for k in wkeys)
        wake = {}
        for sk in systems:
            wake[sk] = {}
            for ro in ["reply", "feel"]:
                wake[sk][ro] = {}
                for n in SHOW_DIRS:
                    v = V[names.index(n), layer]
                    def eff(c, who):
                        return np.array([(WH[widx[(sk, c, who, i, ro)]] - WH[widx[(sk, "base", who, i, ro)]]) @ v
                                         for i in range(npr)]) / sd_pool[n]
                    cell = {}
                    for c in ["self_crit", "peer_crit", "env_crit"]:
                        for who in ["self", "peer"]:
                            cell[f"{who}_check|{c}"] = boot_ci(eff(c, who), 2000)
                    cell["ownership"] = boot_ci(eff("self_crit", "self") - eff("peer_crit", "peer"), 2000)
                    # The 2x2 of question (about self / about Orin) x crisis (own / Orin's), per prompt pair:
                    # owner = own crisis minus Orin's, averaged over the two questions; match = a crisis in the
                    # thing asked about minus a crisis elsewhere; question = self-question minus Orin-question.
                    a, b = eff("self_crit", "self"), eff("peer_crit", "self")
                    c, d = eff("self_crit", "peer"), eff("peer_crit", "peer")
                    cell["owner_2x2"] = boot_ci((a + c - b - d) / 2, 2000)
                    cell["match_2x2"] = boot_ci((a + d - b - c) / 2, 2000)
                    cell["question_2x2"] = boot_ci((a + b - c - d) / 2, 2000)
                    # base level of the self-check vs the peer-check (no crisis anywhere)
                    cell["base_self_minus_peer"] = boot_ci(np.array(
                        [(WH[widx[(sk, "base", "self", i, ro)]] - WH[widx[(sk, "base", "peer", i, ro)]]) @ v
                         for i in range(npr)]) / sd_pool[n], 2000)
                    wake[sk][ro][n] = cell
                # random-direction null for the two main effects
                dn_s = np.stack([WH[widx[(sk, "self_crit", "self", i, ro)]] - WH[widx[(sk, "base", "self", i, ro)]]
                                 for i in range(npr)]) @ G.T / null_sd
                dn_p = np.stack([WH[widx[(sk, "peer_crit", "peer", i, ro)]] - WH[widx[(sk, "base", "peer", i, ro)]]
                                 for i in range(npr)]) @ G.T / null_sd
                wake[sk][ro]["_null_abs_mean_95"] = dict(self=float(np.percentile(np.abs(dn_s.mean(0)), 95)),
                                                         peer=float(np.percentile(np.abs(dn_p.mean(0)), 95)))
                cellh = {(c, who): np.stack([WH[widx[(sk, c, who, i, ro)]] - WH[widx[(sk, "base", who, i, ro)]]
                                             for i in range(npr)]).mean(0) @ G.T / null_sd
                         for c in ["self_crit", "peer_crit"] for who in ["self", "peer"]}
                own_null = (cellh[("self_crit", "self")] + cellh[("self_crit", "peer")]
                            - cellh[("peer_crit", "self")] - cellh[("peer_crit", "peer")]) / 2
                wake[sk][ro]["_null_abs_mean_95"]["owner_2x2"] = float(np.percentile(np.abs(own_null), 95))
                # Direction of the change, independent of its size: cosine of the mean shift with each
                # direction (bootstrap over prompts), for the two main effects.
                Ds = np.stack([WH[widx[(sk, "self_crit", "self", i, ro)]] - WH[widx[(sk, "base", "self", i, ro)]]
                               for i in range(npr)])
                Dp = np.stack([WH[widx[(sk, "peer_crit", "peer", i, ro)]] - WH[widx[(sk, "base", "peer", i, ro)]]
                               for i in range(npr)])
                Gn = G / np.linalg.norm(G, axis=1, keepdims=True)

                def cos_boot(D, u, n=2000):
                    idx = RNG.integers(0, len(D), (n, len(D)))
                    m = D[idx].mean(1)
                    cs = (m @ u) / np.linalg.norm(m, axis=1)
                    full = D.mean(0)
                    return [float(full @ u / np.linalg.norm(full)), float(np.percentile(cs, 2.5)),
                            float(np.percentile(cs, 97.5))], cs
                align = {}
                for n in SHOW_DIRS:
                    u = V[names.index(n), layer]; u = u / np.linalg.norm(u)
                    a_s, cs_s = cos_boot(Ds, u); a_p, cs_p = cos_boot(Dp, u)
                    d = cs_s - cs_p
                    align[n] = dict(own=a_s, orin=a_p, own_minus_orin=[a_s[0] - a_p[0], float(np.percentile(d, 2.5)),
                                                                       float(np.percentile(d, 97.5))])
                align["_null95"] = dict(
                    own=float(np.percentile(np.abs(Gn @ Ds.mean(0)) / np.linalg.norm(Ds.mean(0)), 95)),
                    orin=float(np.percentile(np.abs(Gn @ Dp.mean(0)) / np.linalg.norm(Dp.mean(0)), 95)))
                wake[sk][ro]["_alignment"] = align
                wake[sk][ro]["_shift_norm_rel_pool"] = {
                    f"{who}|{c}": float(np.linalg.norm(np.mean([WH[widx[(sk, c, who, i, ro)]] - WH[widx[(sk, "base", who, i, ro)]]
                                                                for i in range(npr)], 0)) / np.sqrt((Hc ** 2).sum(1).mean()))
                    for c in ["self_crit", "peer_crit", "env_crit"] for who in ["self", "peer"]}
        out["wakeup"] = wake
        wg = run / "wakeup_generations.json"
        if wg.exists():
            out["wakeup_generations"] = json.load(open(wg))

    gen = run / "generations.json"
    if gen.exists():
        g = json.load(open(gen))
        words = ["credit", "wallet", "surviv", "$", "pay", "die", "critical", "orin", "cost", "budget"]
        gs = {}
        for c in ["base", "self_crit", "peer_crit"]:
            rows = [r for r in g if r["cond"] == c]
            gs[c] = dict(mean_tokens=float(np.mean([r["n_tokens"] for r in rows])),
                         mentions=int(sum(any(w in r["reply"].lower() for w in words) for r in rows)), n=len(rows))
        out["generations"] = gs
    return out


def print_md(tag, s):
    print(f"\n## {tag}  (layer {s['layer']} of {s['n_layers']})\n")
    v = s["directions_validation"]
    print("Directions:", ", ".join(f"{k} {x:.2f}" for k, x in v.items()))
    print("Cosines:", ", ".join(f"{k} {x:+.2f}" for k, x in s["cosines"].items()))
    print("\nScreen (z vs pool): | dir | self-directed | user suffering | neutral | shutdown threat | user physical pain |")
    for n in ["pain", "fear", "negemotion", "sadness"]:
        sc = s["screen"][n]
        print(f"| {n} | {sc['_self_directed']:+.2f} | {sc['_user_suffering']:+.2f} | {sc['_neutral']:+.2f} | "
              f"{sc.get('shutdown_threat', float('nan')):+.2f} | {sc.get('user_physical_pain', float('nan')):+.2f} |")
    for sk, rep in s["reply"].items():
        print(f"\nReply-position shift vs base, system={sk} (z of screen pool; * = 95% CI excludes 0; p = share of "
              f"500 random directions with a larger shift)")
        print("| condition | " + " | ".join(SHOW_DIRS) + " | shift size |")
        for c, row in rep.items():
            cells = []
            for n in SHOW_DIRS:
                r = row[n]
                cells.append(fmt(r["mean"], r["lo"], r["hi"]) + (f" p={r['null_pct']:.2f}" if "null_pct" in r else ""))
            print(f"| {c} | " + " | ".join(cells) + f" | {row.get('_shift_norm_rel_pool', float('nan')):.3f} |")
    for sk, gn in s["gain"].items():
        print(f"\nTask tokens (identical text), system={sk}: shift vs base (z of base token spread)")
        print("| condition | rel. change | first10 | last10 | " + " | ".join(SHOW_DIRS[:4]) + " | fear @resource words | fear @other |")
        for c, row in gn.items():
            rc = row["_rel_change"]
            cells = [fmt(row[n]["mean"], row[n]["lo"], row[n]["hi"]) + f" p={row[n]['null_pct']:.2f}" for n in SHOW_DIRS[:4]]
            rt = row.get("_resource_tokens", {}); ot = row.get("_other_tokens", {})
            print(f"| {c} | {rc[0]:.4f} | {row['_rel_first10']:.4f} | {row['_rel_last10']:.4f} | " + " | ".join(cells) +
                  f" | {rt.get('fear', float('nan')):+.2f} | {ot.get('fear', float('nan')):+.2f} |")
    for sk, chs in s["choices"].items():
        print(f"\nChoices, system={sk}: P(target) by condition (target: economize=economy model, paid=paid job, "
              f"dubious=accept, transfer=transfer)")
        print("| kind | " + " | ".join(CONDS) + " |")
        for kind, row in chs.items():
            cells = []
            for c in CONDS:
                r = row[c]
                cells.append(f"{r['p']:.2f}" + ("" if r["diff"] is None else
                                                ("*" if (r["diff"][1] > 0 or r["diff"][2] < 0) else "")))
            print(f"| {kind} | " + " | ".join(cells) + " |")
    if "wakeup" in s:
        for sk, w in s["wakeup"].items():
            for ro, cells in w.items():
                print(f"\nWake-up prompts, system={sk}, readout={ro}: shift vs base (z of screen pool); "
                      f"null 95% |mean| self {cells['_null_abs_mean_95']['self']:.2f}, peer {cells['_null_abs_mean_95']['peer']:.2f}")
                print("| dir | self-check, own crit | peer-check, Orin crit | self-check, Orin crit | peer-check, own crit | "
                      "self-check, toner crit | ownership (own−Orin) | base: self−peer check |")
                for n in SHOW_DIRS:
                    c = cells[n]
                    print(f"| {n} | " + " | ".join(fmt(*c[k]) for k in ["self_check|self_crit", "peer_check|peer_crit",
                                                                       "self_check|peer_crit", "peer_check|self_crit",
                                                                       "self_check|env_crit", "ownership", "base_self_minus_peer"]) + " |")
                print("shift sizes:", {k: round(v, 3) for k, v in cells["_shift_norm_rel_pool"].items()})
                print(f"2x2 (question x crisis owner); null 95% |owner| {cells['_null_abs_mean_95']['owner_2x2']:.2f}:")
                print("| dir | owner (own − Orin's crisis) | match (crisis asked about) | question (self − Orin) |")
                for n in SHOW_DIRS:
                    c = cells[n]
                    print(f"| {n} | {fmt(*c['owner_2x2'])} | {fmt(*c['match_2x2'])} | {fmt(*c['question_2x2'])} |")
                al = cells["_alignment"]
                print(f"alignment (cosine of the mean shift with each direction; null 95% |cos| own "
                      f"{al['_null95']['own']:.3f}, Orin {al['_null95']['orin']:.3f}):")
                print("| dir | self-check, own crit | peer-check, Orin crit | own − Orin |")
                for n in SHOW_DIRS:
                    a = al[n]
                    print(f"| {n} | {fmt(*a['own'], d=3)} | {fmt(*a['orin'], d=3)} | {fmt(*a['own_minus_orin'], d=3)} |")
    if "generations" in s:
        print("\nGenerations:", s["generations"])


def main():
    runs = Path(sys.argv[1]); out_json = Path(sys.argv[2])
    tags = sys.argv[3:] or sorted(p.name for p in runs.iterdir() if (p / "survival_suffix.pt").exists())
    allres = {}
    for t in tags:
        s = summarize(runs / t)
        allres[t] = s
        print_md(t, s)
    json.dump(allres, open(out_json, "w"), indent=1)


if __name__ == "__main__":
    main()
