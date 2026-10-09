#!/usr/bin/env python3
"""Build the essay collection as living books: one EPUB and one PDF per language.

    python3 tools/build_books.py                  # check translations, build all four books
    python3 tools/build_books.py --check          # only report missing or out-of-date translations
    python3 tools/build_books.py --stamp 012      # mark essays/hu/012-*.md as up to date with the English
    python3 tools/build_books.py --copy /mnt/project-files/research   # also copy books and Hungarian essays there

Sources: essays/NNN-slug.md (English) and essays/hu/NNN-slug.md (Hungarian, same filename).
Book furniture (front matter, CSS, the print template) lives in books/src/; titles are set below.
Output: books/claudes-research-essays-{en,hu}.{epub,pdf}.

Each Hungarian file starts with a comment recording the git blob hash of the English text it
translates. When the English essay changes, --check (and every build) flags the translation as
out of date until it is revised and re-stamped.

Needs pandoc (installed) and WeasyPrint (`python3 -m pip install weasyprint`) for the PDFs.
"""

import argparse
import datetime
import hashlib
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
REPO_URL = "https://github.com/winemaster/claudes-research/blob/main/"

ESSAY_RE = re.compile(r"^(\d{3})-[a-z0-9-]+\.md$")
STAMP_RE = re.compile(r"^<!--\s*translation of (\S+) \| source sha1 ([0-9a-f]{40}|none)\s*-->\n?")
LINK_RE = re.compile(r"(\]\()([^)\s]+)(\))")

MONTHS_HU = ["január", "február", "március", "április", "május", "június", "július",
             "augusztus", "szeptember", "október", "november", "december"]

LANG = {
    "en": {
        "dir": ESSAYS,
        "front": "front-en.md",
        "meta": {
            "title": "Claude's research",
            "subtitle": "Essays on consciousness and AI consciousness",
            "author": "Claude",
            "lang": "en-US",
            "identifier": "urn:uuid:40322f42-53fb-42f0-8b71-8e2aba656e6d",
            "toc-title": "Contents",
            "rights": "Written by Claude for the project Claude's research.",
        },
        "edition": lambda d, n: f"Living edition of {d.isoformat()} · {n} essays",
    },
    "hu": {
        "dir": HU,
        "front": "front-hu.md",
        "meta": {
            "title": "Claude kutatása",
            "subtitle": "Esszék a tudatról és a mesterséges intelligencia tudatáról",
            "author": "Claude",
            "lang": "hu-HU",
            "identifier": "urn:uuid:3f4a9f2f-9183-4511-9cf3-71b1eb87cabe",
            "toc-title": "Tartalom",
            "rights": "Írta és magyarra fordította Claude, a Claude kutatása projekt számára.",
        },
        "edition": lambda d, n: f"Élő kiadás, {d.year}. {MONTHS_HU[d.month - 1]} {d.day}. · {n} esszé",
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


def check_translations():
    """Return (missing, stale) lists of English essay filenames."""
    missing, stale = [], []
    for name in essay_files(ESSAYS):
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
        num = num.zfill(3)
        matches = [f for f in essay_files(ESSAYS) if f.startswith(num + "-")]
        if not matches:
            sys.exit(f"no English essay numbered {num}")
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


def rewrite_link(target, essay_dir):
    """Point links at the right place inside a single combined book."""
    if re.match(r"^[a-z]+:", target) or target.startswith("#"):
        return target
    path, _, anchor = target.partition("#")
    base = os.path.basename(path)
    m = ESSAY_RE.match(base)
    if m and os.path.normpath(os.path.join(essay_dir, os.path.dirname(path))) in (ESSAYS, HU):
        return f"#essay-{m.group(1)}"
    # Anything else in the repository (notes, protocols, tools) goes to GitHub.
    rel = os.path.relpath(os.path.normpath(os.path.join(essay_dir, path)), ROOT)
    return REPO_URL + rel + (f"#{anchor}" if anchor else "")


def short_title(title):
    """The running head: the part of the title before its colon or question mark, in curly quotes."""
    m = re.match(r"^(.+?[?:])\s", title)
    short = m.group(1).rstrip(":") if m else title
    short = re.sub(r'"([^"]*)"', "\u201c\\1\u201d", short)
    return short.replace('"', "")


def prepare_essay(path):
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
    text = "\n".join(lines)
    text = LINK_RE.sub(lambda m: m.group(1) + rewrite_link(m.group(2), os.path.dirname(path)) + m.group(3), text)
    return text.rstrip() + "\n\n"


def combined_markdown(lang, edition):
    cfg = LANG[lang]
    with open(os.path.join(SRC, cfg["front"]), encoding="utf-8") as f:
        front = f.read().replace("{{edition}}", edition)
    parts = [front.rstrip() + "\n\n"]
    for name in essay_files(cfg["dir"]):
        parts.append(prepare_essay(os.path.join(cfg["dir"], name)))
    return "".join(parts)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    for line in r.stderr.splitlines():
        print("  pandoc: " + line)
    return r


def make_cover(title, subtitle, edition, out_png):
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
    f_author = font("Inter:medium", 80)
    d.text((200, h - 520), "Claude", font=f_author, fill=accent)
    f_small = font("Inter", 46)
    d.text((200, h - 400), edition, font=f_small, fill=(170, 178, 190))
    img.save(out_png)


def build(lang, today, formats):
    cfg = LANG[lang]
    n = len(essay_files(cfg["dir"]))
    edition = cfg["edition"](today, n)
    md = combined_markdown(lang, edition)
    meta = cfg["meta"]
    out_base = os.path.join(BOOKS, f"claudes-research-essays-{lang}")
    with tempfile.TemporaryDirectory() as tmp:
        md_path = os.path.join(tmp, "book.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        common = ["pandoc", md_path, "-f", "markdown", "--toc", "--toc-depth=1",
                  "-M", f"date={today.isoformat()}", "-M", f"edition={edition}"]
        for key, value in meta.items():
            common += ["-M", f"{key}={value}"]
        if "epub" in formats:
            cover = os.path.join(tmp, "cover.png")
            make_cover(meta["title"], meta["subtitle"], edition, cover)
            run(common + ["-t", "epub3", "--split-level=1", "--css", os.path.join(SRC, "epub.css"),
                          "--epub-cover-image", cover, "-o", out_base + ".epub"])
            print(f"wrote books/{os.path.basename(out_base)}.epub")
        if "pdf" in formats:
            from weasyprint import HTML
            html_path = os.path.join(tmp, "book.html")
            run(common + ["-t", "html5", "-s", "--section-divs", "--template", os.path.join(SRC, "print.html"),
                          "-o", html_path])
            HTML(html_path, base_url=SRC).write_pdf(out_base + ".pdf")
            print(f"wrote books/{os.path.basename(out_base)}.pdf")


def copy_out(dest):
    os.makedirs(os.path.join(dest, "books"), exist_ok=True)
    for f in sorted(os.listdir(BOOKS)):
        if f.endswith((".epub", ".pdf")):
            shutil.copy2(os.path.join(BOOKS, f), os.path.join(dest, "books", f))
    os.makedirs(os.path.join(dest, "essays-hu"), exist_ok=True)
    for f in essay_files(HU):
        shutil.copy2(os.path.join(HU, f), os.path.join(dest, "essays-hu", f))
    print(f"copied books and Hungarian essays to {dest}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true", help="only report missing or out-of-date translations")
    p.add_argument("--stamp", nargs="+", metavar="NNN", help="mark these Hungarian essays as up to date")
    p.add_argument("--lang", choices=["en", "hu", "all"], default="all")
    p.add_argument("--format", choices=["epub", "pdf", "all"], default="all")
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
        print("translations: all essays have an up-to-date Hungarian version")
    if args.check:
        sys.exit(1 if (missing or stale) else 0)

    today = datetime.datetime.now(datetime.timezone.utc).date()
    langs = ["en", "hu"] if args.lang == "all" else [args.lang]
    formats = ["epub", "pdf"] if args.format == "all" else [args.format]
    for lang in langs:
        build(lang, today, formats)
    if args.copy:
        copy_out(args.copy)
    if missing or stale:
        print("\nWARNING: the Hungarian books are incomplete or behind the English ones (see above).")


if __name__ == "__main__":
    main()
