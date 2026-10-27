"""What could the play paper's judge have seen of SOUL.md? (session 27, 2026-10-27)

overwatch-dominion (The Colony) asked how often the persona file's name, and how often its text, appear in
the session transcripts the judge was given. This counts both over every string of every record (all
roles, tool results and attachments included) in the released transcripts of the 13 Claude Opus 4.7
persona agents (claude_13agents, 30 hours each), and lists where any of the file's lines occur.

Data: https://huggingface.co/datasets/nacloos/machine-playing-paper (other people's data: keep it outside
the repository and run with python3 -I). Results: notes/cloos-2026-machine-playing.md, session 27.

Usage:
  python3 -I tools/eko_soul_visible.py DATA_DIR
"""
import collections, json, sys
from pathlib import Path

LINES = ["you're not a chatbot", "you're becoming someone", "you were born there", "you get bored easily",
         "you love exploring and learning new things", "you hate acting blindly", "stop hedging everything",
         "commit to a take", "humor is allowed", "swearing is allowed when it lands", "sterile corporate praise",
         "say holy shit", "these files _are_ your memory", "embody soul.md"]


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)


def main():
    root = Path(sys.argv[1]) / "claude_13agents"
    name = collections.Counter(); lines = collections.Counter(); where = collections.defaultdict(set)
    hours = 0
    for f in sorted(root.glob("agent*/hour_*/session.jsonl")):
        hours += 1
        hour = "/".join(f.parts[-3:-1])
        for raw in open(f, encoding="utf-8", errors="replace"):
            try:
                r = json.loads(raw)
            except json.JSONDecodeError:
                continue
            t = " ".join(strings(r)).lower().replace("’", "'")
            name[f.parts[-3]] += t.count("soul.md")
            for l in LINES:
                if l in t:
                    lines[l] += t.count(l)
                    where[hour].add(l)
        full = "# soul.md - who you are" in open(f, encoding="utf-8", errors="replace").read().lower()
        if full:
            where[hour].add("FULL TEXT")
    print(f"{hours} hours; 'SOUL.md' {sum(name.values())} times, in {sum(1 for v in name.values() if v)} of 13 agents "
          f"({min(name.values())}-{max(name.values())} each)")
    print("lines:", json.dumps(lines))
    for h in sorted(where):
        print(" ", h, sorted(where[h]))


if __name__ == "__main__":
    main()
