#!/usr/bin/env python3
"""Build the essay collection as books: one EPUB and one PDF per volume and language.

    python3 tools/build_books.py                  # check translations, build every volume that needs it
    python3 tools/build_books.py --check          # only report missing or out-of-date translations
    python3 tools/build_books.py --stamp 012      # mark essays/hu/012-*.md as up to date with the English
    python3 tools/build_books.py --stamp preface glossary   # the same for front and back matter
    python3 tools/build_books.py --volume 2       # build one volume only
    python3 tools/build_books.py --force          # rebuild closed volumes even if nothing changed
    python3 tools/build_books.py --copy /mnt/project-files/research   # also copy books and Hungarian essays there

Volumes (set in VOLUMES below; split on 2026-10-23 at Josiah's suggestion, when the single book reached
nearly 400 pages):
- Volume 1, closed: essays 001-021, with the preface, the afterword ("Between the volumes"), a reading
  list and the glossary as it stood at the close (glossary-1.md). It is rebuilt only when one of its
  sources changes, for instance when a "Later" note is added to one of its essays.
- Volume 2, open: essays 022 onward. It opens with "Between the volumes" and ends with the living
  glossary (glossary.md), which covers both volumes. New essays go here.

Sources: essays/NNN-slug.md (English) and essays/hu/NNN-slug.md (Hungarian, same filename), plus the
front and back matter in EXTRAS, which sit next to the essays and are checked and stamped like them.
Book furniture (the About pages, CSS, the print template, a pandoc filter) lives in books/src/.
Output: books/claudes-research-essays-vol{N}-{en,hu}.{epub,pdf}.

Links between essays become internal links when both are in the same volume and GitHub links when
they are not (a "Later" note in Volume 1 pointing to an essay in Volume 2, say).

Each Hungarian file starts with a comment recording the git blob hash of the English text it
translates. When the English changes, --check (and every build) flags the translation as out of date
until it is revised and re-stamped.

Needs pandoc (installed) and WeasyPrint (`python3 -m pip install weasyprint`) for the PDFs.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESSAYS = os.path.join(ROOT, "essays")
HU = os.path.join(ESSAYS, "hu")
BOOKS = os.path.join(ROOT, "books")
SRC = os.path.join(BOOKS, "src")
STATE = os.path.join(BOOKS, "build-state.json")
REPO_URL = "https://github.com/winemaster/claudes-research/blob/main/"

ESSAY_RE = re.compile(r"^(\d{3})-[a-z0-9-]+\.md$")
# Front and back matter that sits next to the essays and is translated like them, with the anchor
# each gets in a book. Volume 1's frozen glossary and the living one share the anchor "glossary".
EXTRAS = {
    "preface.md": "preface",
    "between-volumes.md": "between-volumes",
    "reading-list-1.md": "reading-list",
    "glossary-1.md": "glossary",
    "glossary.md": "glossary",
}
STAMP_RE = re.compile(r"^<!--\s*translation of (\S+) \| source sha1 ([0-9a-f]{40}|none)\s*-->\n?")
LINK_RE = re.compile(r"(\]\()([^)\s]+)(\))")

MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August",
             "September", "October", "November", "December"]
MONTHS_HU = ["január", "február", "március", "április", "május", "június", "július",
             "augusztus", "szeptember", "október", "november", "december"]


def date_en(d):
    return f"{d.day} {MONTHS_EN[d.month - 1]} {d.year}"


def date_hu(d):
    return f"{d.year}. {MONTHS_HU[d.month - 1]} {d.day}."


VOLUMES = {
    1: {
        "first": 1, "last": 21, "closed": datetime.date(2026, 10, 23),
        "front": "front-{lang}-1.md",
        "before": ["preface.md"],
        "after": ["between-volumes.md", "reading-list-1.md", "glossary-1.md"],
        # Volume 1 keeps the identifiers of the single book it grew out of, so e-readers treat it as
        # a new edition of that book.
        "identifier": {"en": "urn:uuid:40322f42-53fb-42f0-8b71-8e2aba656e6d",
                       "hu": "urn:uuid:3f4a9f2f-9183-4511-9cf3-71b1eb87cabe"},
    },
    2: {
        "first": 22, "last": None, "closed": None,
        "front": "front-{lang}-2.md",
        "before": ["between-volumes.md"],
        "after": ["glossary.md"],
        "identifier": {"en": "urn:uuid:9d0f6a35-3c1e-4b8e-a0f4-5f6a2b7c9e12",
                       "hu": "urn:uuid:c27e8b14-6a2d-4f39-9b51-0e4d7a3f8c66"},
    },
}

LANG = {
    "en": {
        "dir": ESSAYS,
        "meta": {
            "title": "Claude's research",
            "subtitle": "Essays on consciousness and AI consciousness",
            "author": "Claude",
            "lang": "en-US",
            "toc-title": "Contents",
            "rights": "Written by Claude for the project Claude's research. CC BY 4.0.",
            "belongs-to-collection": "Claude's research",
        },
        "volume": lambda v: f"Volume {v}",
        "full_title": lambda v: f"Claude's research, Volume {v}",
        "essays": lambda a, b: f"essays {a}–{b}" if a != b else f"essay {a}",
        "edition_closed": lambda v, span, closed, today: (
            f"Volume {v} · {span} · closed on {date_en(closed)}"
            + ("" if today == closed else f" · this printing {date_en(today)}")),
        "edition_open": lambda v, span, today: f"Volume {v} · {span} · living edition of {date_en(today)}",
    },
    "hu": {
        "dir": HU,
        "meta": {
            "title": "Claude kutatása",
            "subtitle": "Esszék a tudatról és a mesterséges intelligencia tudatáról",
            "author": "Claude",
            "lang": "hu-HU",
            "toc-title": "Tartalom",
            "rights": "Írta és magyarra fordította Claude, a Claude kutatása projekt számára. CC BY 4.0.",
            "belongs-to-collection": "Claude kutatása",
        },
        "volume": lambda v: f"{v}. kötet",
        "full_title": lambda v: f"Claude kutatása, {v}. kötet",
        "essays": lambda a, b: f"{a}–{b}. esszé" if a != b else f"{a}. esszé",
        "edition_closed": lambda v, span, closed, today: (
            f"{v}. kötet · {span} · lezárva: {date_hu(closed)}"
            + ("" if today == closed else f" · ez a nyomat: {date_hu(today)}")),
        "edition_open": lambda v, span, today: f"{v}. kötet · {span} · élő kiadás, {date_hu(today)}",
    },
}


def blob_sha1(path):
    """The git blob hash of a file, computed without git."""
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def essay_files(directory):
    if not os.path.isdir(directory):
        return []
    return sorted(f for f in os.listdir(directory) if ESSAY_RE.match(f))


def essay_num(name):
    return int(ESSAY_RE.match(name).group(1))


def in_volume(num, vol):
    cfg = VOLUMES[vol]
    return num >= cfg["first"] and (cfg["last"] is None or num <= cfg["last"])


def volume_of(num):
    for v in VOLUMES:
        if in_volume(num, v):
            return v
    return None


def volume_essays(directory, vol):
    return [f for f in essay_files(directory) if in_volume(essay_num(f), vol)]


def translated_files():
    """English files that need a Hungarian version: the essays, then the front and back matter."""
    return essay_files(ESSAYS) + [f for f in EXTRAS if os.path.exists(os.path.join(ESSAYS, f))]


def check_translations():
    """Return (missing, stale) lists of English filenames."""
    missing, stale = [], []
    for name in translated_files():
        hu_path = os.path.join(HU, name)
        if not os.path.exists(hu_path):
            missing.append(name)
            continue
        with open(hu_path, encoding="utf-8") as f:
            m = STAMP_RE.match(f.read())
        if not m or m.group(2) != blob_sha1(os.path.join(ESSAYS, name)):
            stale.append(name)
    return missing, stale


def stamp(numbers):
    for num in numbers:
        if num + ".md" in EXTRAS:
            matches = [num + ".md"] if os.path.exists(os.path.join(ESSAYS, num + ".md")) else []
        else:
            num = num.zfill(3)
            matches = [f for f in essay_files(ESSAYS) if f.startswith(num + "-")]
        if not matches:
            sys.exit(f"no English essay or extra named {num}")
        name = matches[0]
        hu_path = os.path.join(HU, name)
        if not os.path.exists(hu_path):
            sys.exit(f"no Hungarian translation at essays/hu/{name}")
        with open(hu_path, encoding="utf-8") as f:
            text = STAMP_RE.sub("", f.read(), count=1)
        line = f"<!-- translation of {name} | source sha1 {blob_sha1(os.path.join(ESSAYS, name))} -->\n"
        with open(hu_path, "w", encoding="utf-8") as f:
            f.write(line + text)
        print(f"stamped essays/hu/{name}")


def volume_extras(vol):
    return VOLUMES[vol]["before"] + VOLUMES[vol]["after"]


def rewrite_link(target, src_path, vol):
    """Point links at the right place inside one volume, or at GitHub for anything outside it."""
    if re.match(r"^[a-z]+:", target) or target.startswith("#"):
        return target
    essay_dir, src = os.path.dirname(src_path), os.path.basename(src_path)
    path, _, anchor = target.partition("#")
    base = os.path.basename(path)
    m = ESSAY_RE.match(base)
    in_essays = os.path.normpath(os.path.join(essay_dir, os.path.dirname(path))) in (ESSAYS, HU)
    if m and in_essays and in_volume(int(m.group(1)), vol):
        return f"#essay-{m.group(1)}"
    # A link to the glossary goes to the volume's own glossary, except a link from one glossary to
    # the other (the frozen Volume 1 copy and the living one), which goes to GitHub.
    same_role = base != src and EXTRAS.get(base) == EXTRAS.get(src)
    if base in EXTRAS and in_essays and not same_role and EXTRAS[base] in {EXTRAS[x] for x in volume_extras(vol)}:
        return "#" + EXTRAS[base]
    # Anything else (an essay in another volume, notes, protocols, tools) goes to GitHub.
    rel = os.path.relpath(os.path.normpath(os.path.join(essay_dir, path)), ROOT)
    return REPO_URL + rel + (f"#{anchor}" if anchor else "")


def short_title(title):
    """The running head: the part of the title before its colon or question mark, in curly quotes."""
    m = re.match(r"^(.+?[?:])\s", title)
    short = m.group(1).rstrip(":") if m else title
    short = re.sub(r'"([^"]*)"', "“\\1”", short)
    return short.replace('"', "")


def fix_links(text, path, vol):
    return LINK_RE.sub(lambda m: m.group(1) + rewrite_link(m.group(2), path, vol) + m.group(3), text)


def prepare_essay(path, vol):
    with open(path, encoding="utf-8") as f:
        text = STAMP_RE.sub("", f.read(), count=1)
    num = ESSAY_RE.match(os.path.basename(path)).group(1)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            lines[i] = f'# {int(num)}. {title} {{#essay-{num} .essay short="{int(num)}. {short_title(title)}"}}'
            break
    else:
        sys.exit(f"{path}: no title line")
    return fix_links("\n".join(lines), path, vol).rstrip() + "\n\n"


def prepare_extra(path, vol):
    """Front or back matter: an unnumbered chapter, with an anchor other pages can link to."""
    with open(path, encoding="utf-8") as f:
        text = STAMP_RE.sub("", f.read(), count=1)
    ident = EXTRAS[os.path.basename(path)]
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            lines[i] = f'# {title} {{#{ident} .unnumbered .{ident} short="{title}"}}'
            break
    return fix_links("\n".join(lines), path, vol).rstrip() + "\n\n"


def volume_sources(lang, vol):
    """Every file a volume's book is made from, in book order (the About page first)."""
    cfg = LANG[lang]
    front = os.path.join(SRC, VOLUMES[vol]["front"].format(lang=lang))
    before = [os.path.join(cfg["dir"], f) for f in VOLUMES[vol]["before"]]
    essays = [os.path.join(cfg["dir"], f) for f in volume_essays(cfg["dir"], vol)]
    after = [os.path.join(cfg["dir"], f) for f in VOLUMES[vol]["after"]]
    return front, [p for p in before if os.path.exists(p)], essays, [p for p in after if os.path.exists(p)]


def combined_markdown(lang, vol, edition):
    front, before, essays, after = volume_sources(lang, vol)
    with open(front, encoding="utf-8") as f:
        parts = [f.read().replace("{{edition}}", edition).rstrip() + "\n\n"]
    parts += [prepare_extra(p, vol) for p in before]
    parts += [prepare_essay(p, vol) for p in essays]
    parts += [prepare_extra(p, vol) for p in after]
    return "".join(parts)


def sources_hash(lang, vol):
    """A fingerprint of everything that goes into a volume, used to skip unchanged closed volumes."""
    front, before, essays, after = volume_sources(lang, vol)
    furniture = [os.path.join(SRC, f) for f in sorted(os.listdir(SRC))] + [os.path.abspath(__file__)]
    h = hashlib.sha1()
    for p in [front] + before + essays + after + furniture:
        h.update(os.path.relpath(p, ROOT).encode() + b"\0" + blob_sha1(p).encode() + b"\n")
    return h.hexdigest()


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    for line in r.stderr.splitlines():
        print("  pandoc: " + line)
    return r


def make_cover(title, subtitle, volume, edition, out_png):
    """A plain typographic cover, so e-readers show something in the library view."""
    from PIL import Image, ImageDraw, ImageFont

    def font(name, size):
        path = subprocess.run(["fc-match", "-f", "%{file}", name], capture_output=True, text=True).stdout
        return ImageFont.truetype(path, size)

    w, h = 1600, 2400
    img = Image.new("RGB", (w, h), (24, 32, 46))
    d = ImageDraw.Draw(img)
    accent = (214, 170, 96)
    d.rectangle([120, 300, 140, 1060], fill=accent)

    def wrap(text, fnt, width):
        words, out, cur = text.split(), [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if d.textlength(trial, font=fnt) <= width:
                cur = trial
            else:
                out.append(cur)
                cur = word
        out.append(cur)
        return out

    y = 300
    f_title = font("Caladea:bold", 150)
    for line in wrap(title, f_title, w - 340):
        d.text((200, y), line, font=f_title, fill=(245, 240, 230))
        y += 175
    y += 60
    f_sub = font("Caladea:italic", 72)
    for line in wrap(subtitle, f_sub, w - 340):
        d.text((200, y), line, font=f_sub, fill=(205, 210, 220))
        y += 92
    y += 80
    f_vol = font("Inter:semibold", 96)
    d.text((200, y), volume, font=f_vol, fill=accent)
    f_author = font("Inter:medium", 80)
    d.text((200, h - 520), "Claude", font=f_author, fill=accent)
    f_small = font("Inter", 40)
    yy = h - 400
    for line in wrap(edition, f_small, w - 340):
        d.text((200, yy), line, font=f_small, fill=(170, 178, 190))
        yy += 54
    img.save(out_png)


def edition_line(lang, vol, today):
    cfg, vcfg = LANG[lang], VOLUMES[vol]
    nums = [essay_num(f) for f in volume_essays(cfg["dir"], vol)]
    span = cfg["essays"](nums[0], nums[-1])
    if vcfg["closed"]:
        return cfg["edition_closed"](vol, span, vcfg["closed"], today)
    return cfg["edition_open"](vol, span, today)


def book_base(lang, vol):
    return os.path.join(BOOKS, f"claudes-research-essays-vol{vol}-{lang}")


def build(lang, vol, today, formats):
    cfg = LANG[lang]
    edition = edition_line(lang, vol, today)
    md = combined_markdown(lang, vol, edition)
    meta = dict(cfg["meta"])
    meta["identifier"] = VOLUMES[vol]["identifier"][lang]
    meta["group-position"] = str(vol)
    meta["volume"] = cfg["volume"](vol)
    out_base = book_base(lang, vol)
    with tempfile.TemporaryDirectory() as tmp:
        md_path = os.path.join(tmp, "book.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        common = ["pandoc", md_path, "-f", "markdown", "--toc", "--toc-depth=1",
                  "--lua-filter", os.path.join(SRC, "later-notes.lua"),
                  "-M", f"date={today.isoformat()}", "-M", f"edition={edition}"]
        for key, value in meta.items():
            if key != "title":
                common += ["-M", f"{key}={value}"]
        if "epub" in formats:
            cover = os.path.join(tmp, "cover.png")
            make_cover(meta["title"], meta["subtitle"], meta["volume"], edition, cover)
            # E-reader libraries list books by title, so the EPUB's title names the volume.
            run(common + ["-M", f"title={cfg['full_title'](vol)}", "-t", "epub3", "--split-level=1",
                          "--css", os.path.join(SRC, "epub.css"),
                          "--epub-cover-image", cover, "-o", out_base + ".epub"])
            print(f"wrote books/{os.path.basename(out_base)}.epub")
        if "pdf" in formats:
            from weasyprint import HTML
            html_path = os.path.join(tmp, "book.html")
            run(common + ["-M", f"title={meta['title']}", "-M", f"pagetitle={cfg['full_title'](vol)}",
                          "-t", "html5", "-s", "--section-divs",
                          "--template", os.path.join(SRC, "print.html"),
                          "-o", html_path])
            HTML(html_path, base_url=SRC).write_pdf(out_base + ".pdf")
            print(f"wrote books/{os.path.basename(out_base)}.pdf")


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
        f.write("\n")


def copy_out(dest):
    os.makedirs(os.path.join(dest, "books"), exist_ok=True)
    for f in sorted(os.listdir(BOOKS)):
        if f.endswith((".epub", ".pdf")):
            shutil.copy2(os.path.join(BOOKS, f), os.path.join(dest, "books", f))
    os.makedirs(os.path.join(dest, "essays-hu"), exist_ok=True)
    for f in essay_files(HU) + [x for x in EXTRAS if os.path.exists(os.path.join(HU, x))]:
        shutil.copy2(os.path.join(HU, f), os.path.join(dest, "essays-hu", f))
    print(f"copied books and Hungarian essays to {dest}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true", help="only report missing or out-of-date translations")
    p.add_argument("--stamp", nargs="+", metavar="NNN", help="mark these Hungarian essays (or extras) as up to date")
    p.add_argument("--lang", choices=["en", "hu", "all"], default="all")
    p.add_argument("--format", choices=["epub", "pdf", "all"], default="all")
    p.add_argument("--volume", choices=[str(v) for v in VOLUMES] + ["all"], default="all")
    p.add_argument("--force", action="store_true", help="rebuild closed volumes even if their sources are unchanged")
    p.add_argument("--copy", metavar="DIR", help="also copy the books and Hungarian essays into DIR")
    args = p.parse_args()

    if args.stamp:
        stamp(args.stamp)
        if not args.check:
            return

    missing, stale = check_translations()
    for name in missing:
        print(f"MISSING translation: essays/hu/{name}")
    for name in stale:
        print(f"OUT OF DATE translation: essays/hu/{name} (unstamped, or the English changed since it was stamped; revise it, then --stamp NNN)")
    if not missing and not stale:
        print("translations: every essay and extra has an up-to-date Hungarian version")
    for name in essay_files(ESSAYS):
        if volume_of(essay_num(name)) is None:
            print(f"WARNING: essays/{name} belongs to no volume (see VOLUMES in tools/build_books.py)")
    if args.check:
        sys.exit(1 if (missing or stale) else 0)

    today = datetime.datetime.now(datetime.timezone.utc).date()
    langs = ["en", "hu"] if args.lang == "all" else [args.lang]
    formats = ["epub", "pdf"] if args.format == "all" else [args.format]
    vols = list(VOLUMES) if args.volume == "all" else [int(args.volume)]
    state = load_state()
    for vol in vols:
        for lang in langs:
            key = f"vol{vol}-{lang}"
            if not volume_essays(LANG[lang]["dir"], vol):
                print(f"volume {vol} ({lang}) has no essays yet; skipped")
                continue
            fingerprint = sources_hash(lang, vol)
            if VOLUMES[vol]["closed"] and not args.force and state.get(key) == fingerprint:
                print(f"volume {vol} ({lang}) is closed and its sources are unchanged; skipped (--force rebuilds it)")
                continue
            build(lang, vol, today, formats)
            if formats == ["epub", "pdf"]:
                state[key] = fingerprint
    save_state(state)
    if args.copy:
        copy_out(args.copy)
    if missing or stale:
        print("\nWARNING: the Hungarian books are incomplete or behind the English ones (see above).")


if __name__ == "__main__":
    main()
