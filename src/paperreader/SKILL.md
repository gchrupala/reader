---
name: paperreader
description: Fetch and read research papers with the `paper` CLI. Use when the user wants to read, download, cite, summarize or look up a scientific paper given a DOI, arXiv id, PMID/PMCID, ACL Anthology id, OpenReview id, OSF id, URL or title; when they ask for a paper's section, figures or BibTeX; or when they ask to find papers by keywords.
---

# Reading papers with paperreader (command `paper`)

`paper` downloads a paper the user is entitled to read into their library (`~/papers` by default)
and writes a Markdown text version next to it, with `<!-- page N -->` markers for PDFs and figure and
table images linked where they appear. It tries open-access sources first, then the user's
institutional access. It rate-limits itself per host; do not work around that.

## If `paper` is missing

This skill is installed by `paper install-skill`, so `paper` should be there. If `command -v paper`
finds nothing, tell the user; the README of https://github.com/gchrupala/reader says how to install it.

## Commands

| task | command |
| --- | --- |
| fetch a paper, print its text path | `paper get <id>` |
| fetch several | `paper get <id> <id> ...` or `paper get --from keys.tsv` (`key<TAB>id` per line) |
| print the text | `paper read <id>` |
| list headings, one section, no references | `paper read <id> --sections`, `--section Methods`, `--no-refs` |
| some pages only (PDFs) | `paper read <id> --pages 1-3` |
| figure and table images | `paper read <id> --figures` |
| find a DOI by keywords or title | `paper search <words> -n 5` |
| metadata and candidate locations, no download | `paper resolve <id>` |
| BibTeX | `paper bib <id> ...` |
| what is in the library | `paper list` |
| papers that failed and need a person | `paper pending` |

`<id>` is a DOI (`10.1038/nature14539`), `arXiv:1706.03762`, `pmid:17375194`, `PMC1234567`, an ACL
Anthology id, an OpenReview or OSF id, a URL, an exact title, or a library key. `--json` on `get`,
`resolve`, `search` and `list` gives machine-readable output.

## How to work

- For a long paper, read `--sections` first, then the sections you need, rather than the whole text.
- Figures and tables are image files: open them with the Read tool to look at them.
- Superscripts and subscripts are written `^{...}` and `_{...}` (`10^{−4}`, `K_δ`).
- Check equations and tables before you rely on them (see below).
- Use `-q` with `get` to skip the per-attempt log when it is not needed.
- If `get` fails, report its reason and hints to the user. Do not look for other copies on the web
  or retry in a loop: the tool already tried every route it knows, and repeated requests can get
  the user's institution blocked by a publisher.
- A failure that needs a person (a human check, a sign-in) is kept in `paper pending`. The user can
  run `paper login` once to sign in to their library's proxy, `paper pending --retry` at their own
  machine, or `paper add FILE [ID]` for a PDF they downloaded themselves.
- `get` may open a visible browser window for a human check and wait up to a few minutes for the
  user; tell them when that may happen. In a session without a display, pass `--no-browser`.

## Equations and tables

How far you can trust them depends on what the text was made from. Before you quote a number from a
table or state a formula, check it as described here, and tell the user when you could not.

- **Text with `<!-- page N -->` markers comes from a PDF.** Its equations and tables are unreliable:
  fractions, exponents, subscripts and table columns are lost without any sign of it. `10^{2i/d}` can
  read `102i/d` and `1.0·10^{20}` can read `1.0 · 1020`; in a table, empty cells vanish, so a value may
  seem to belong to the wrong column. Check tables against their image, linked after the page's text.
  For an equation, open the PDF (`<key>.pdf`, next to the text) at that page with the Read tool.
- **Text without page markers comes from arXiv's HTML or from JATS XML** (PubMed Central, bioRxiv).
  Formulas in `$...$` are LaTeX: arXiv's source, the publisher's LaTeX, or the publisher's MathML
  converted, with fractions, exponents, subscripts, roots, sums and matrices kept. Display formulas
  are followed by their number, as in `$$...$$ (3)`. Tables are Markdown: a cell spanning several
  rows is repeated in each, and a header of several rows is merged into one (`BLEU EN-DE`).
- **In JATS text, a formula without `$` is MathML that could not be converted** (malformed), flattened
  to symbols, for example `d T d t = - β T V` for dT/dt = −βTV. Its fractions, exponents and subscripts
  are lost. If the exact form matters, look at the formula on the article page (PMC:
  `https://pmc.ncbi.nlm.nih.gov/articles/<PMCID>/`) or in the PDF, if the library has one (`<key>.pdf`).

## In a cloud session

In Claude Code on the web (`CLAUDE_CODE_REMOTE=true`) or any container without a display:

- Pass `--no-browser`: there is no person to complete a human check or sign in, and no campus
  network, so only open-access papers come through.
- The library, `paper pending` included, disappears with the container. Keep the texts with
  `paper get ... --export DIR` into the repository you are working in, and the failures with
  `paper pending --tsv > missing.tsv`, so the user can fetch them at their own machine with
  `paper get --from missing.tsv`. Ask the user before committing either.
