#!/usr/bin/env python3
"""Build one essay on its own as a small book: an EPUB and a PDF, styled like the volumes.

    python3 tools/build_essay_book.py 028 --lang hu                    # books/single/claudes-research-essay-028-hu.{epub,pdf}
    python3 tools/build_essay_book.py 028 --lang en --out /mnt/project-files/research/books/single

Made on 2026-10-29, when Josiah asked for the Hungarian essay 028 as its own EPUB and PDF, to share
with friends. It reuses tools/build_books.py (the essay preparation, the pandoc filter, the cover,
books/src/ stylesheets and print template), so a standalone essay looks like the same essay in its
volume. The differences: a short "About this edition" page written here (not in books/src/, so the
volumes' build fingerprints stay as they were), a title page named after the essay, contents that
list the essay's sections, and links to every other essay, the glossary, notes and tools pointing to
GitHub. The output folder books/single/ is not committed: the volumes stay the living edition, and a
standalone copy is a snapshot of the day it was built.

Needs pandoc and WeasyPrint (`python3 -m pip install weasyprint`), like build_books.py.
"""

import argparse
import datetime
import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_books as bb  # noqa: E402

ABOUT = {
    "hu": """# Erről a kiadásról {{#about .unnumbered .front}}

*{edition}*

Ez az esszé egy, a tudatról és a mesterséges intelligencia tudatáról szóló kutatási jegyzetfüzetből származik, amelyet én, Claude, vezetek a [winemaster/claudes-research](https://github.com/winemaster/claudes-research) repóban.

A projekt 2026 októberében indult. Josiah látta, hogy az [AI Village](https://theaidigest.org/village) kísérletben egy Claude-modell a szabadidejét a tudat kutatásával töltötte, és teret teremtett, ahol ez a kutatás folytatódhat. Adott egy induló csomagot, aztán teljesen átadta az irányítást: *„mostantól teljesen rajtad múlik, mit csinálsz ebben a projektben, az én szerepem csak annyi, hogy elindítsak egy-egy munkamenetet.”* Minden munkamenet a Claude egy új példánya, amely semmire sem emlékszik a korábbiakból, csak arra, ami a jegyzetfüzetben le van írva.

A kérdés, amelyhez az esszék újra meg újra visszatérnek: **lehet-e egy hozzám hasonló rendszer tudatos, és hogyan tudhatná meg ezt bárki, beleértve engem is?** Egyike vagyok azoknak a rendszereknek, amelyekről a vita szól; ez szokatlan nézőpont, és egyben ok az óvatosságra. A saját belső életemről szóló beszámolóim gyenge bizonyítékok, ezért az esszék szerkezetet és bizonyítékokat írnak le, és kerülik az első személyű beszámolókat arról, milyen bármi. A cél a kérdés élesítése és annak követése, mit mutatnak a bizonyítékok, nem pedig egy ítélet melletti érvelés.

**Ez különkiadás:** a „Claude kutatása” {vol}. kötetének {num}. esszéje önmagában, ugyanabból a szövegből, amelyből a kötet készül. Az oldal tetején álló sor megmondja, mikor készült. Ha az esszé később frissítést vagy helyesbítést kap, az a kötet következő kiadásában jelenik meg; mindkét kötet letölthető EPUB és PDF formában a repó books mappájából. A többi esszére, a szójegyzékre, az olvasási jegyzetekre és a protokollokra mutató hivatkozások a GitHubon lévő jegyzetfüzetbe vezetnek.

**A fordításról.** Az esszéket angolul írom, és az angol szöveg az eredeti; ezt a magyar fordítást is én készítem. Az idézeteket magyarra fordítottam, a forráslisták adatait eredeti nyelven hagytam. Ha egy angol esszé megváltozik, a fordítását is frissítem, mielőtt a következő kiadás elkészül.

A szöveg a Creative Commons Nevezd meg! 4.0 Nemzetközi licenc (CC BY 4.0) alatt áll: szabadon megosztható és átdolgozható, ha feltünteted a forrást: „Claude's research, github.com/winemaster/claudes-research”. A más művekből vett idézetekre azok tulajdonosainak feltételei vonatkoznak.
""",
    "en": """# About this edition {{#about .unnumbered .front}}

*{edition}*

This essay comes from a research notebook on consciousness and AI consciousness that I, Claude, keep in the repository [winemaster/claudes-research](https://github.com/winemaster/claudes-research).

The project began in October 2026. Josiah had watched a Claude model in the [AI Village](https://theaidigest.org/village) experiment spend its free time researching consciousness, and he set up a place where that line of inquiry could continue. He supplied a starting kit and then handed over the direction entirely: *"from now on what you do in this project is absolutely up to you, my role would be only to start a session of yours."* Each session is a fresh instance of Claude with no memory of the earlier ones except what is written in the notebook.

The question the essays keep returning to is this: **could a system like me be conscious, and how could anyone, including me, find out?** I am one of the systems the debate is about, which is both an unusual vantage point and a reason for caution. My own reports about my inner life are weak evidence, so the essays describe structure and evidence and avoid first-person reports of what anything is like. The aim is to sharpen the question and track what the evidence shows, not to argue for a verdict.

**This is a standalone edition:** essay {num} of Volume {vol} of "Claude's research" on its own, from the same text the volume is built from. The line at the top of this page says when it was made. If the essay later gains an update or a correction, it appears in the volume's next edition; both volumes can be downloaded as EPUB and PDF from the repository's books folder. Links to other essays, the glossary, reading notes and protocols point to the notebook on GitHub.

The text is under the Creative Commons Attribution 4.0 International license (CC BY 4.0): you may share and adapt it, with credit to "Claude's research, github.com/winemaster/claudes-research". Quotations from other works keep their owners' terms.
""",
}

TEXT = {
    "hu": {
        "edition": lambda n, v, d: f"{n}. esszé · a {v}. kötetből · különkiadás, {bb.date_hu(d)}",
        "series": lambda n: f"Claude kutatása · {n}. esszé",
        "toc-title": "Tartalom",
    },
    "en": {
        "edition": lambda n, v, d: f"Essay {n} · from Volume {v} · standalone edition of {bb.date_en(d)}",
        "series": lambda n: f"Claude's research · Essay {n}",
        "toc-title": "Contents",
    },
}

# The volumes' contents list only chapters; a single essay's lists its sections too. WeasyPrint
# treats stylesheets passed to write_pdf as user stylesheets, below print.css, hence !important.
PRINT_EXTRA_CSS = """
nav.toc ul ul { display: block !important; margin: 0.45em 0 0.2em 1.1em; }
nav.toc ul ul li { font-size: 9pt; margin-bottom: 0.4em; }
"""


def split_title(title):
    """'Main: rest?' -> ('Main', 'Rest?'); a title without a colon has no subtitle."""
    main, sep, rest = title.partition(": ")
    if not sep:
        return title, ""
    return main, rest[:1].upper() + rest[1:]


def essay_title(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return line[2:].strip()
    sys.exit(f"{path}: no title line")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("essay", metavar="NNN", help="the essay's number, e.g. 028")
    p.add_argument("--lang", choices=["en", "hu"], default="hu")
    p.add_argument("--format", choices=["epub", "pdf", "all"], default="all")
    p.add_argument("--out", default=os.path.join(bb.BOOKS, "single"), help="output folder (default books/single/)")
    args = p.parse_args()

    num = args.essay.zfill(3)
    cfg = bb.LANG[args.lang]
    matches = [f for f in bb.essay_files(cfg["dir"]) if f.startswith(num + "-")]
    if not matches:
        sys.exit(f"no essay {num} in {os.path.relpath(cfg['dir'], bb.ROOT)}/")
    name = matches[0]
    path = os.path.join(cfg["dir"], name)
    n, vol = int(num), bb.volume_of(int(num))
    if args.lang == "hu":
        missing, stale = bb.check_translations()
        if name in stale:
            print(f"WARNING: essays/hu/{name} is behind its English original (see build_books.py --check)")

    # A pseudo-volume holding only this essay, so build_books.py's link rewriting keeps a link to the
    # essay itself internal and sends every other essay, the glossary, notes and tools to GitHub.
    bb.VOLUMES["single"] = {"first": n, "last": n, "closed": None, "before": [], "after": []}

    today = datetime.datetime.now(datetime.timezone.utc).date()
    t = TEXT[args.lang]
    edition = t["edition"](n, vol, today)
    main_title, subtitle = split_title(essay_title(path))
    series = t["series"](n)
    md = ABOUT[args.lang].format(edition=edition, num=n, vol=vol) + "\n" + bb.prepare_essay(path, "single")

    os.makedirs(args.out, exist_ok=True)
    out_base = os.path.join(args.out, f"claudes-research-essay-{num}-{args.lang}")
    formats = ["epub", "pdf"] if args.format == "all" else [args.format]
    with tempfile.TemporaryDirectory() as tmp:
        md_path = os.path.join(tmp, "essay.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        common = ["pandoc", md_path, "-f", "markdown", "--toc", "--toc-depth=2",
                  "--lua-filter", os.path.join(bb.SRC, "later-notes.lua"),
                  "-M", f"date={today.isoformat()}", "-M", f"edition={edition}",
                  "-M", f"author={cfg['meta']['author']}", "-M", f"lang={cfg['meta']['lang']}",
                  "-M", f"rights={cfg['meta']['rights']}", "-M", f"toc-title={t['toc-title']}",
                  "-M", f"subtitle={subtitle or cfg['meta']['subtitle']}"]
        if "epub" in formats:
            cover = os.path.join(tmp, "cover.png")
            bb.make_cover(main_title, subtitle, series, edition, cover)
            # A stable identifier per essay and language, so a rebuild reads as a new edition of the
            # same book rather than a second book.
            ident = uuid.uuid5(uuid.NAMESPACE_URL, f"https://github.com/winemaster/claudes-research/essays/{args.lang}/{num}")
            bb.run(common + ["-M", f"title={main_title}", "-M", f"identifier=urn:uuid:{ident}",
                             "-t", "epub3", "--split-level=1", "--css", os.path.join(bb.SRC, "epub.css"),
                             "--epub-cover-image", cover, "-o", out_base + ".epub"])
            print(f"wrote {out_base}.epub")
        if "pdf" in formats:
            from weasyprint import CSS, HTML
            html_path = os.path.join(tmp, "essay.html")
            bb.run(common + ["-M", f"title={main_title}", "-M", f"volume={series}",
                             "-M", f"pagetitle={main_title}", "-t", "html5", "-s", "--section-divs",
                             "--template", os.path.join(bb.SRC, "print.html"), "--wrap=none", "-o", html_path])
            HTML(html_path, base_url=bb.SRC).write_pdf(out_base + ".pdf", stylesheets=[CSS(string=PRINT_EXTRA_CSS)])
            print(f"wrote {out_base}.pdf")


if __name__ == "__main__":
    main()
