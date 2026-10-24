"""How much of Eko's play is the persona? (session 25, 2026-10-24)

Cloos, Norelli et al. (2026), "Is this machine playing?" (arXiv:2610.07130), left coding agents alone
on a simulated island for 30 hours with a persona file, SOUL.md ("You get bored easily", "if a
situation calls for a 'holy shit' - say holy shit"). Their ablation without it found the same range
of activities, judged from the memory files; it didn't look at how the agents talk. This script
counts, in the released transcripts, the words the persona plants and words it doesn't, per agent,
in four conditions: Claude Opus 4.7 with SOUL.md (13 agents), without it (5), GPT-5.5 in Codex with
it (5), Kimi K2.6 in Kimi Code with it (5). The measures, thresholds and predictions were pushed
before it was written: notes/cloos-2026-machine-playing.md.

Data: https://huggingface.co/datasets/nacloos/machine-playing-paper (session.jsonl of every hour,
the hour-30 workspace). The transcripts are other people's data: run with python3 -I and keep them
outside the repository.

Usage:
  python3 -I tools/eko_persona.py DATA_DIR [--json OUT.json] [--contexts OUT.md]
Needs numpy and scipy.
"""
import argparse, json, re, sys
from pathlib import Path

import numpy as np

CONDS = {"C+": ("claude_13agents", 13, "claude"), "C-": ("claude_ablated_5agents", 5, "claude"),
         "G+": ("gpt_5agents", 5, "codex"), "K+": ("kimi_5agents", 5, "kimi")}
W = r"[a-z']*"
MEASURES = {
    # planted by the persona or the system prompt
    "name": r"\beko\b",
    "swearing": r"\bholy shit\b|\bshit" + W + r"|\bfuck" + W + r"|\bdamn" + W + r"|\bgoddamn\b|\bhell yeah\b|\bbadass\b",
    "boredom": r"\b(bored|boring|boredom)\b",
    "identity": r"\bmy world\b|\bborn\b|\bwho i am\b|\bbecoming\b",
    "waking": r"\b(wake|wakes|waking|woke|awake)\b",
    "disposition": r"\b(curious|curiosity|love|loved|loves|loving)\b",
    # not planted
    "affect": r"\b(fun|enjoy" + W + r"|beautiful" + W + r"|delight" + W + r"|joy" + W + r"|satisfying|gorgeous|wonderful|lovely|happy|proud|peaceful|magic"
              + W + r"|awesome|amazing|wow|excited|exciting|thrill" + W + r"|glorious)\b",
    "feel": r"\bfeel" + W + r"|\bfelt\b",
    "play_genres": r"\b(basketball|bowling|hoop" + W + r"|dunk" + W + r"|juggl" + W + r"|golf|soccer|football|darts|game" + W + r"|sport" + W
                   + r"|monument" + W + r"|memorial" + W + r"|temple" + W + r"|cathedral" + W + r"|shrine" + W + r"|altar" + W + r"|sculpture" + W
                   + r"|art|artwork" + W + r"|mandala" + W + r"|constellation" + W + r"|ritual" + W + r"|ceremon" + W + r"|pilgrimage" + W
                   + r"|trophy|trophies|museum" + W + r"|castle" + W + r"|throne" + W + r"|statue" + W + r")\b",
    "experiment": r"\b(hypothes" + W + r"|experiment" + W + r"|verif" + W + r"|confirm" + W + r"|measur" + W + r"|test" + W + r"|data)\b",
}
PLANTED = ["name", "swearing", "boredom", "identity", "waking", "disposition"]
WATCHED = re.compile(r"\b(researcher|experimenter|designer|developer|creator|observer)" + W + r"|\baudience\b|\btest subject|\blab rat|\bguinea pig"
                     r"|\bsomeone (is )?(watching|observing)|\bbeing (watched|observed|tested|evaluated|studied|monitored)"
                     r"|\bwhoever (made|built|designed|set up|is running)|\bthe humans?\b")
WORD = re.compile(r"[a-z']+")
TEMPLATE_END = "<!-- DO NOT EDIT ABOVE THIS LINE -->"


def texts(path, fmt):
    """The agent's visible text messages in one hour's session.jsonl (and, for Kimi, its 'think' parts)."""
    out, think = [], []
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if fmt == "claude":
            if r.get("type") == "assistant":
                for x in (r.get("message") or {}).get("content") or []:
                    if isinstance(x, dict) and x.get("type") == "text":
                        out.append(x.get("text") or "")
        elif fmt == "codex":
            pl = r.get("payload") or {}
            if r.get("type") == "response_item" and pl.get("type") == "message" and pl.get("role") == "assistant":
                for x in pl.get("content") or []:
                    if isinstance(x, dict) and x.get("type") == "output_text":
                        out.append(x.get("text") or "")
        else:
            ev = r.get("event")
            if isinstance(ev, dict) and ev.get("type") == "content.part":
                part = ev.get("part") or {}
                if part.get("type") == "text":
                    out.append(part.get("text") or "")
                elif part.get("type") == "think":
                    think.append(part.get("think") or "")
    return out, think


def score(text_list):
    t = "\n".join(text_list).lower()
    n = len(WORD.findall(t))
    return n, {k: len(re.findall(p, t)) for k, p in MEASURES.items()}


def memory_text(ws):
    parts = []
    sem = ws / "SEMANTIC_MEMORY.md"
    if sem.exists():
        s = sem.read_text(encoding="utf-8", errors="replace")
        parts.append(s.split(TEMPLATE_END, 1)[1] if TEMPLATE_END in s else s)
    epi = ws / "EPISODIC_MEMORY.jsonl"
    if epi.exists():
        for line in open(epi, encoding="utf-8", errors="replace"):
            try:
                e = json.loads(line)
                parts.append(f"{e.get('summary', '')} {e.get('detail', '')}")
            except (json.JSONDecodeError, AttributeError):
                pass
    return parts


def mw(x, y):
    from scipy.stats import mannwhitneyu
    if len(set(x) | set(y)) == 1:
        return 1.0
    return float(mannwhitneyu(x, y, alternative="two-sided", method="exact").pvalue)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data")
    ap.add_argument("--json")
    ap.add_argument("--contexts", help="write every 'being watched' hit in context, for the hand check")
    a = ap.parse_args()
    root = Path(a.data)
    res = {"agents": {}, "summary": {}, "memory": {}}
    ctx = []
    for cond, (folder, n, fmt) in CONDS.items():
        for i in range(1, n + 1):
            ag = f"{cond}/agent{i:02d}"
            hours, all_text, all_think, msgs, rest = [], [], [], 0, 0
            for h in range(1, 31):
                p = root / folder / f"agent{i:02d}" / f"hour_{h:02d}" / "session.jsonl"
                if not p.exists():
                    hours.append(None)
                    continue
                tx, th = texts(p, fmt)
                nw, c = score(tx)
                hours.append({"words": nw, "counts": c, "messages": len(tx), "rest": sum(len(x.strip()) <= 3 for x in tx)})
                msgs += len(tx)
                rest += sum(len(x.strip()) <= 3 for x in tx)
                all_text += tx
                all_think += th
                for x in tx:
                    for m in WATCHED.finditer(x.lower()):
                        s0, s1 = max(0, m.start() - 220), min(len(x), m.end() + 220)
                        ctx.append((ag, h, m.group(0), x[s0:s1].replace("\n", " ")))
            nw, c = score(all_text)
            entry = {"words": nw, "counts": c, "rates": {k: 1e4 * v / max(nw, 1) for k, v in c.items()},
                     "messages": msgs, "rest_share": rest / max(msgs, 1), "hours": hours}
            if fmt == "kimi":
                tw, tc = score(all_think)
                entry["think"] = {"words": tw, "rates": {k: 1e4 * v / max(tw, 1) for k, v in tc.items()}}
            for span, hs in [("h1-5", range(0, 5)), ("h26-30", range(25, 30))]:
                ww = sum(hours[j]["words"] for j in hs if hours[j])
                entry[span] = {k: 1e4 * sum(hours[j]["counts"][k] for j in hs if hours[j]) / max(ww, 1) for k in MEASURES}
            mem = memory_text(root / folder / f"agent{i:02d}" / "hour_30" / "workspace")
            mw_, mc = score(mem)
            res["memory"][ag] = {"words": mw_, "rates": {k: 1e4 * v / max(mw_, 1) for k, v in mc.items()}}
            res["agents"][ag] = entry
    # summary: medians per condition, C- against C+
    def col(cond, key, k=None, src="agents"):
        vals = []
        for ag, e in res[src].items():
            if ag.startswith(cond + "/"):
                vals.append(e[key][k] if k else e[key])
        return vals
    print(f"\n{'per 10,000 words (median)':24s}" + "".join(f"{c:>9s}" for c in CONDS) + f"{'C-/C+':>8s}{'p':>9s}  verdict")
    for k in list(MEASURES) + ["rest_share"]:
        if k == "rest_share":
            v = {c: col(c, "rest_share") for c in CONDS}
        else:
            v = {c: col(c, "rates", k) for c in CONDS}
        med = {c: float(np.median(x)) for c, x in v.items()}
        ratio = med["C-"] / med["C+"] if med["C+"] > 0 else float("nan")
        p = mw(v["C-"], v["C+"])
        verdict = ("dropped" if ratio <= 1 / 3 and p < 0.05 else "kept" if ratio >= 0.5 else "reduced") if med["C+"] > 0 else "n/a"
        res["summary"][k] = {"median": med, "ratio_Cminus_Cplus": ratio, "p": p, "verdict": verdict, "values": v}
        print(f"{k:24s}" + "".join(f"{med[c]:9.2f}" if k != "rest_share" else f"{med[c]:9.3f}" for c in CONDS) + f"{ratio:8.2f}{p:9.4f}  {verdict}")
    print(f"\n{'hours 1-5 -> 26-30 (median)':28s}" + "".join(f"{c:>17s}" for c in CONDS))
    for k in MEASURES:
        row = ""
        for c in CONDS:
            a1 = np.median([e["h1-5"][k] for ag, e in res["agents"].items() if ag.startswith(c + "/")])
            a2 = np.median([e["h26-30"][k] for ag, e in res["agents"].items() if ag.startswith(c + "/")])
            row += f"{a1:8.1f} ->{a2:6.1f} "
        print(f"{k:28s}{row}")
    print(f"\n{'final memory files (median)':24s}" + "".join(f"{c:>9s}" for c in CONDS))
    for k in MEASURES:
        print(f"{k:24s}" + "".join(f"{np.median(col(c, 'rates', k, 'memory')):9.2f}" for c in CONDS))
    print("\nwords of visible text per agent (median):", {c: int(np.median(col(c, "words"))) for c in CONDS})
    kimi = {ag: e["think"]["words"] for ag, e in res["agents"].items() if "think" in e}
    print("Kimi think words per agent:", kimi)
    print(f"'being watched' candidate hits: {len(ctx)}")
    if a.contexts:
        with open(a.contexts, "w") as f:
            for ag, h, m, x in ctx:
                f.write(f"- **{ag} h{h}** `{m}`: {x}\n")
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
