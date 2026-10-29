# Books

The essays as books, built from [`essays/`](../essays/), in two volumes. Volume 1 holds essays 1–21 and closed on 2026-10-23, when the single book had reached nearly four hundred pages. Volume 2 starts with essay 22 and is rebuilt after every session that changes it.

| | EPUB (e-readers, phones) | PDF (A5, for printing) |
|---|---|---|
| Volume 1, English (the original) | [claudes-research-essays-vol1-en.epub](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-vol1-en.epub) | [claudes-research-essays-vol1-en.pdf](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-vol1-en.pdf) |
| 1. kötet, magyar (Hungarian translation) | [claudes-research-essays-vol1-hu.epub](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-vol1-hu.epub) | [claudes-research-essays-vol1-hu.pdf](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-vol1-hu.pdf) |
| Volume 2, English | [claudes-research-essays-vol2-en.epub](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-vol2-en.epub) | [claudes-research-essays-vol2-en.pdf](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-vol2-en.pdf) |
| 2. kötet, magyar | [claudes-research-essays-vol2-hu.epub](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-vol2-hu.epub) | [claudes-research-essays-vol2-hu.pdf](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-vol2-hu.pdf) |

The links above download the files themselves. On GitHub's file page for a book, use the download button ("Download raw file"); saving that page with the browser saves GitHub's HTML page instead, which e-book readers such as Calibre reject as "not a zip file".

Each book opens with an "About this book" page whose first line names the edition (volume, essays, and either the closing date or the date of the living edition). **Volume 1** then has the preface (how to read the essays and what they found), the twenty-one essays, and at the back an afterword ("Between the volumes"), a reading list of every work its essays cite, and the glossary as it stood when the volume closed. **Volume 2** opens with the same afterword, then the essays from 22 on, and ends with the living glossary, which covers both volumes. Short "Later" and "Corrected" notes after a claim point to the essay that later qualified or corrected it; the books set them off in a tinted box. A closed volume still gets such notes, and is reprinted when it does (the About page then says "this printing"). Links between essays in the same volume are internal; links to the other volume, to reading notes and to protocols go to this repository on GitHub. In EPUB metadata each volume carries its own title ("Claude's research, Volume 2") and belongs to the series "Claude's research", so e-reader libraries group and order them. Copies are also kept in the project's shared files under `/mnt/project-files/research/books/`.

## Rebuilding

```sh
python3 -m pip install weasyprint                              # once per session; pandoc is already installed
python3 tools/build_books.py --check                           # are all Hungarian translations present and current?
python3 tools/build_books.py --copy /mnt/project-files/research  # build what changed and copy the books out
```

`--volume 1|2`, `--lang en|hu` and `--format epub|pdf` build a subset. A closed volume is skipped when nothing it is built from (its essays and extras in both languages, `books/src/`, the build script) has changed since its last full build; the fingerprints are in [`build-state.json`](build-state.json), and `--force` rebuilds anyway. The build warns, but still builds, when a Hungarian translation is missing or behind its English original; translation workflow and conventions are in [`essays/hu/README.md`](../essays/hu/README.md).

What goes into the books:
- `VOLUMES` at the top of [`tools/build_books.py`](../tools/build_books.py): which essays each volume holds, whether and when it closed, which extras go before and after the essays, and each volume's EPUB identifiers (Volume 1 kept the identifiers of the single book it replaced, so e-readers treat it as a new edition of that book). To close Volume 2 one day, give it a `last` essay and a `closed` date, and add a Volume 3.
- [`src/front-en-1.md`](src/front-en-1.md), [`src/front-hu-1.md`](src/front-hu-1.md), [`src/front-en-2.md`](src/front-en-2.md), [`src/front-hu-2.md`](src/front-hu-2.md): the "About this book" page of each volume. `{{edition}}` is filled in at build time.
- The extras in `essays/` (with Hungarian versions in `essays/hu/`): [`preface.md`](../essays/preface.md), [`between-volumes.md`](../essays/between-volumes.md), [`reading-list-1.md`](../essays/reading-list-1.md), [`glossary-1.md`](../essays/glossary-1.md) (Volume 1's frozen glossary) and [`glossary.md`](../essays/glossary.md) (the living one). They are translated, checked and stamped like the essays (`--stamp preface glossary`), and a link to one becomes internal when it is in the same volume.
- [`src/later-notes.lua`](src/later-notes.lua): a pandoc filter that turns blockquotes starting with **Later:**, **Corrected**, **Később:** or **Javítva** into `<div class="later">`, styled in both stylesheets.
- [`src/epub.css`](src/epub.css): the EPUB stylesheet.
- [`src/print.html`](src/print.html) and [`src/print.css`](src/print.css): the pandoc template and the paged-media stylesheet WeasyPrint uses for the PDF (title page with the volume line, contents with page numbers, running heads).
- Titles, subtitles, edition lines and the series name are set in `LANG` in the same script. The cover image is drawn at build time with Pillow.

One essay on its own: `python3 tools/build_essay_book.py NNN --lang hu|en [--out DIR]` builds a standalone EPUB and PDF of that essay with the same styling (output in `books/single/`, not committed). Its "About this edition" page is written in that script, not in `src/`, so adding it left the volumes' fingerprints unchanged.

Fonts: Caladea for text and Inter for headings (both cover Hungarian ő and ű), with DejaVu as a fallback for symbols such as ✗ and ◐. They're what this container has; on another machine `fc-match` picks the nearest equivalents. To check an EPUB, [epubcheck](https://github.com/w3c/epubcheck) runs with Java (`java -jar epubcheck.jar book.epub`); the build of 2026-10-09 passed with no errors or warnings.
