"""LaTeX for the formulas of JATS XML: from the publisher's <tex-math>, or converted from MathML.

Most publishers in PubMed Central (8 of 10 journals sampled in November 2026) give MathML only.
Flattened to its text, MathML loses fractions, exponents and subscripts (`d T d t` for dT/dt),
so it is converted with mathml-to-latex, and only flattened when that fails.

mathml-to-latex 1.0 gets three things wrong, which are done differently here:
- a base of several tokens gets parentheses the paper does not show: (TΔ)′ for TΔ′, and ((x+y))²;
- scripts before a base (mmultiscripts) are written with a literal underscore: `\\_{}^{Δ}H_{}^{}`;
- `*` and `∗` (asterisk operator) become `\\star`, a different symbol.
It also writes each bracket as a one-sided `\\left(\\right.`, and the lines of a display without an
environment; both are tidied after conversion.
"""

from __future__ import annotations

import copy
import re
import xml.etree.ElementTree as ET

from mathml_to_latex.el_to_tex.adapter import MathMLElementToLatexConverterAdapter
from mathml_to_latex.xml_to_mathml.factory import make_xml_to_mathml_adapter

TEX_ENCODINGS = {"application/x-tex", "application/x-latex", "tex", "latex"}
WRAPPERS = {"math", "mrow", "mstyle", "mpadded", "semantics"}
DOCUMENT_RE = re.compile(r"\\begin\{document\}(.*)\\end\{document\}", re.S)
DELIMITER = r"(\\[a-zA-Z]+|\\[{}|]|[^.\s\\])"
ONE_SIDED_RE = re.compile(rf"\\left{DELIMITER}\\right\.|\\left\.\\right{DELIMITER}")
BRACE_RE = re.compile(r"\\(left|right)([{}])")
SINGLE_TOKEN_RE = re.compile(r"[^\s{}\\]|\\[a-zA-Z]+|\\.|\{[^{}]*\}")
ASTERISK = "\ue000"  # stands in for * and ∗ during conversion


def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def tex_math(text: str) -> str:
    """The formula in a <tex-math>. Springer Nature wraps each one in a LaTeX document of its own."""
    if m := DOCUMENT_RE.search(text):
        text = m.group(1)
    text = text.strip()
    for start, end in (("$$", "$$"), ("\\[", "\\]"), ("$", "$")):
        inner = text[len(start):len(text) - len(end)]
        if text.startswith(start) and text.endswith(end) and len(text) >= len(start) + len(end) and end not in inner:
            return inner.strip()
    return text


def to_latex(math: ET.Element) -> str | None:
    """LaTeX for a MathML <math> element, or None when it cannot be converted."""
    m = copy.deepcopy(math)
    for el in m.iter():
        el.tag = _local(el.tag)
        el.attrib = {_local(k): v for k, v in el.attrib.items()}
        if el.text:
            el.text = el.text.replace("*", ASTERISK).replace("\u2217", ASTERISK)
    m.tail = None
    for ann in m.iter("annotation"):  # some publishers keep the LaTeX source in the MathML
        if (ann.get("encoding") or "").lower() in TEX_ENCODINGS and (ann.text or "").strip():
            return ann.text.replace(ASTERISK, "*").strip()
    for parent in list(m.iter()):
        for child in [c for c in parent if c.tag in ("annotation", "annotation-xml")]:
            parent.remove(child)
    lines = _only_table(m)
    _matrices(m, lines)
    try:
        adapter = _Adapter()
        elements = make_xml_to_mathml_adapter().convert(ET.tostring(m, encoding="unicode"))
        tex = "".join(adapter.to_latex_converter(e).convert() for e in elements)
    except Exception:  # malformed MathML (an msub with three children, say)
        return None
    tex = " ".join(_tidy(tex).replace(ASTERISK, "\\ast ").split())
    if lines is not None and ("\\\\" in tex or "&" in tex):
        tex = f"\\begin{{aligned}}{tex}\\end{{aligned}}"
    return tex or None


def _tidy(tex: str) -> str:
    """One-sided `\\left(\\right.` pairs as plain brackets; braces as visible braces (`\\left{` is not LaTeX)."""
    tex = BRACE_RE.sub(r"\\\1\\\2", tex)
    return ONE_SIDED_RE.sub(lambda d: d.group(1) or d.group(2), tex)


class _Adapter(MathMLElementToLatexConverterAdapter):
    def _from_mathml_element_to_latex_converter(self):
        table = super()._from_mathml_element_to_latex_converter()
        for name in ("msub", "msup", "msubsup", "mmultiscripts"):
            table[name] = lambda el: _Scripts(el, self)
        return table


class _Scripts:
    """msub, msup, msubsup and mmultiscripts: `{T \\Delta}^{\\prime}`, `{}^{\\Delta}H`."""

    def __init__(self, el, adapter: _Adapter):
        self._el, self._adapter = el, adapter

    def _tex(self, el) -> str:
        if el is None or el.name in ("none", "mprescripts"):
            return ""
        return _tidy(self._adapter.to_latex_converter(el).convert()).strip()

    def _pairs(self, scripts: list) -> str:
        """Subscript and superscript pairs; `{}` between pairs, so that each attaches where it should."""
        out = []
        for sub, sup in zip(scripts[::2], scripts[1::2], strict=False):
            sub, sup = self._tex(sub), self._tex(sup)
            out.append((f"_{{{sub}}}" if sub else "") + (f"^{{{sup}}}" if sup else ""))
        return "{}".join(p for p in out if p)

    def convert(self) -> str:
        name, kids = self._el.name, list(self._el.children)
        if name == "mmultiscripts":
            i = next((k for k, c in enumerate(kids) if c.name == "mprescripts"), len(kids))
            post, pre = kids[1:i], kids[i + 1:]
        else:
            if len(kids) != (3 if name == "msubsup" else 2):
                raise ValueError(f"{name} with {len(kids)} children")
            post = {"msub": [kids[1], None], "msup": [None, kids[1]]}.get(name, kids[1:])
            pre = []
        if not kids:
            raise ValueError(f"empty {name}")
        base = self._tex(kids[0])
        if not SINGLE_TOKEN_RE.fullmatch(base):
            base = f"{{{base}}}"
        before = self._pairs(pre)
        return (f"{{}}{before}" if before else "") + base + self._pairs(post)


def _only_table(m: ET.Element) -> ET.Element | None:
    """The <mtable> that is the whole formula: lines of a display (aligned at `&`), not a matrix."""
    el = m
    while el.tag in WRAPPERS and len(el) == 1 and not (el.text or "").strip():
        el = el[0]
    return el if el.tag == "mtable" else None


def _matrices(m: ET.Element, lines: ET.Element | None) -> None:
    """Put each other outermost <mtable> inside a table of one cell.

    mathml-to-latex writes `\\begin{matrix}` only for tables inside tables; an outermost one becomes
    bare `a & b \\\\ c & d`. This makes a matrix in a formula an inner table.
    """
    parents = {c: p for p in m.iter() for c in p}

    def outermost(t: ET.Element) -> bool:
        p = parents.get(t)
        while p is not None:
            if p.tag == "mtable":
                return False
            p = parents.get(p)
        return True

    for t in [t for t in m.iter("mtable") if t is not lines and outermost(t)]:
        parent = parents[t]
        i = list(parent).index(t)
        cell = ET.Element("mtable")
        ET.SubElement(ET.SubElement(cell, "mtr"), "mtd").append(t)
        cell.tail, t.tail = t.tail, None
        parent.remove(t)
        parent.insert(i, cell)
