# Books

The essays as living books, rebuilt from [`essays/`](../essays/) after every session.

| | EPUB (e-readers, phones) | PDF (A5, for printing) |
|---|---|---|
| English (the original) | [claudes-research-essays-en.epub](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-en.epub) | [claudes-research-essays-en.pdf](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-en.pdf) |
| Magyar (Hungarian translation) | [claudes-research-essays-hu.epub](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-hu.epub) | [claudes-research-essays-hu.pdf](https://github.com/winemaster/claudes-research/raw/main/books/claudes-research-essays-hu.pdf) |

The links above download the files themselves. On GitHub's file page for a book, use the download button ("Download raw file"); saving that page with the browser saves GitHub's HTML page instead, which e-book readers such as Calibre reject as "not a zip file".

Each book opens with an "About this book" page whose first line names the edition (the build date and the number of essays). Links between essays are internal; links to reading notes and protocols go to this repository on GitHub. Copies are also kept in the project's shared files under `/mnt/project-files/research/books/`.

## Rebuilding

```sh
python3 -m pip install weasyprint                              # once per session; pandoc is already installed
python3 tools/build_books.py --check                           # are all Hungarian translations present and current?
python3 tools/build_books.py --copy /mnt/project-files/research  # build all four books and copy them out
```

`--lang en|hu` and `--format epub|pdf` build a subset. The build warns, but still builds, when a Hungarian translation is missing or behind its English original; translation workflow and conventions are in [`essays/hu/README.md`](../essays/hu/README.md).

What goes into the books:
- [`src/front-en.md`](src/front-en.md), [`src/front-hu.md`](src/front-hu.md): the "About this book" page. `{{edition}}` is filled in at build time.
- [`src/epub.css`](src/epub.css): the EPUB stylesheet.
- [`src/print.html`](src/print.html) and [`src/print.css`](src/print.css): the pandoc template and the paged-media stylesheet WeasyPrint uses for the PDF (title page, contents with page numbers, running heads).
- Titles, subtitles and book identifiers are set in `LANG` at the top of [`tools/build_books.py`](../tools/build_books.py). The cover image is drawn at build time with Pillow.

Fonts: Caladea for text and Inter for headings (both cover Hungarian ő and ű), with DejaVu as a fallback for symbols such as ✗ and ◐. They're what this container has; on another machine `fc-match` picks the nearest equivalents. To check an EPUB, [epubcheck](https://github.com/w3c/epubcheck) runs with Java (`java -jar epubcheck.jar book.epub`); the build of 2026-10-09 passed with no errors or warnings.
