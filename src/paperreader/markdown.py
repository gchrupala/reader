"""Markdown pieces shared by the converters of JATS XML (`extract.py`) and arXiv's HTML (`html_paper.py`)."""

from __future__ import annotations

MAX_SPAN = 50  # a cell spans at most this many rows or columns (guards against colspan="1000")

Cell = tuple[str, int, int]  # text, rows spanned, columns spanned


def script(mark: str, text: str) -> str:
    """A superscript (mark "^") or subscript ("_"): braces unless it is a single character, as in LaTeX."""
    return f"{mark}{text}" if len(text) == 1 else f"{mark}{{{text}}}"


def span(value: str | None) -> int:
    """A rowspan or colspan attribute as a number of cells (1 when missing or invalid)."""
    try:
        return min(max(int(value or 1), 1), MAX_SPAN)
    except ValueError:
        return 1


def table(rows: list[list[Cell]], header_rows: int | None = None) -> str:
    """A Markdown table from rows of cells, with row and column spans laid out on a grid.

    Without spans taken into account, the cells after a spanning cell slide into the wrong column.
    A cell that spans rows repeats its text in each of them. In the body, a cell that spans columns
    fills the first one; in the header, all of them, and the header rows are merged into one, so
    that "BLEU" over "EN-DE" and "EN-FR" gives the columns "BLEU EN-DE" and "BLEU EN-FR".

    `header_rows` is the number of header rows (a <thead>). When it is not known, the first row is
    the header, together with the rows its cells span (a "Model" cell spanning two rows).
    Columns and rows that are empty throughout are left out.
    """
    if not rows:
        return ""
    if not header_rows:
        header_rows = max((rs for _, rs, _ in rows[0]), default=1)
    grid: list[dict[int, str]] = []
    above: dict[int, tuple[str, int]] = {}  # column -> (text, rows still to fill) of cells spanning rows
    for r, cells in enumerate(rows):
        line = {col: text for col, (text, _) in above.items()}
        above = {col: (text, left - 1) for col, (text, left) in above.items() if left > 1}
        col = 0
        for text, rs, cs in cells:
            while col in line:
                col += 1
            for k in range(cs):
                line[col + k] = text if k == 0 or r < header_rows else ""
                if rs > 1:
                    above[col + k] = (line[col + k], rs - 1)
            col += cs
        grid.append(line)
    width = 1 + max((max(line) for line in grid if line), default=-1)
    cols = [c for c in range(width) if any(line.get(c) for line in grid)]
    if not cols:
        return ""
    head = [" ".join(dict.fromkeys(t for line in grid[:header_rows] if (t := line.get(c)))) for c in cols]
    body = [[line.get(c, "") for c in cols] for line in grid[header_rows:]]
    out = [head, ["---"] * len(cols)] + [row for row in body if any(row)]
    return "\n".join("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |" for row in out)
