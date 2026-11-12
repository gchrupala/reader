"""Tables with spanning cells, and superscripts and subscripts, in the JATS and arXiv HTML converters."""

from paperreader.extract import jats_to_text
from paperreader.html_paper import html_to_markdown
from paperreader.markdown import script, span, table


def cells(*texts, rows=1, cols=1):
    return [(t, rows, cols) for t in texts]


def test_a_cell_spanning_rows_keeps_the_next_values_in_their_columns():
    # Table 1 of PMC11706453: "Bimodal" spans two rows. Without the span, 2.16 slid under "Type".
    rows = [cells("Type", "β", "p"), cells("Unimodal", "2.40", "1.60"),
            cells("Bimodal", rows=2) + cells("2.88", "1.44"), cells("2.16", "2.08")]
    assert table(rows, header_rows=1) == ("| Type | β | p |\n| --- | --- | --- |\n| Unimodal | 2.40 | 1.60 |\n"
                                          "| Bimodal | 2.88 | 1.44 |\n| Bimodal | 2.16 | 2.08 |")


def test_a_two_level_header_becomes_one_row():
    # Table 2 of arXiv 1706.03762, without a <thead>: "Model" spans both header rows and "BLEU" two
    # columns; the empty column between the groups is a spacer.
    rows = [cells("Model", rows=2) + cells("BLEU", cols=2) + cells("") + cells("Cost", cols=2),
            cells("EN-DE", "EN-FR", "", "EN-DE", "EN-FR"),
            cells("ByteNet", "23.75", "", "", "", ""),
            cells("Deep-Att", "", "39.2", "", "", "1.0e20")]
    assert table(rows) == ("| Model | BLEU EN-DE | BLEU EN-FR | Cost EN-DE | Cost EN-FR |\n"
                           "| --- | --- | --- | --- | --- |\n"
                           "| ByteNet | 23.75 |  |  |  |\n"
                           "| Deep-Att |  | 39.2 |  | 1.0e20 |")


def test_a_cell_spanning_columns_in_the_body_fills_the_first():
    rows = [cells("a", "b"), cells("Group 1", cols=2), cells("1", "2|3"), cells("", "")]
    assert table(rows) == "| a | b |\n| --- | --- |\n| Group 1 |  |\n| 1 | 2\\|3 |"


def test_spans_and_scripts():
    assert [span(v) for v in (None, "", "2", "0", "x", "1000")] == [1, 1, 2, 1, 1, 50]
    assert (script("^", "2"), script("^", "−4"), script("_", "δ")) == ("^2", "^{−4}", "_δ")
    assert table([]) == "" and table([cells("", "")]) == ""


def test_jats_tables_and_scripts():
    xml = """<article><front><article-meta><title-group>
      <article-title>CO<sub>2</sub> uptake</article-title></title-group></article-meta></front>
      <body><sec><title>Results</title>
        <p>A rate of 3 × 10<sup>−4</sup> s<sup>−1</sup> in cells<sup><xref ref-type="bibr">12</xref></sup>.</p>
        <table-wrap id="T1"><label>Table 1</label><caption><p>Parameters.</p></caption><table>
          <thead><tr><th>Type</th><th><italic>δ</italic> (×10<sup>6</sup>)</th><th>K<sub>δ</sub></th></tr></thead>
          <tbody><tr><td rowspan="2">Bimodal</td><td>2.88</td><td>1.44</td></tr>
          <tr><td>2.16</td><td>2.08</td></tr></tbody></table></table-wrap>
      </sec></body></article>""".encode()
    text, meta, _ = jats_to_text(xml)
    assert meta["title"] == "CO2 uptake"  # plain: it goes into the library key and the download check
    assert "A rate of 3 × 10^{−4} s^{−1} in cells^{12}." in text
    assert ("| Type | δ (×10^6) | K_δ |\n| --- | --- | --- |\n| Bimodal | 2.88 | 1.44 |\n| Bimodal | 2.16 | 2.08 |"
            in text)


def test_arxiv_html_tables_and_scripts():
    html = """<html><body><article class="ltx_document">
      <h1 class="ltx_title ltx_title_document">T</h1>
      <div class="ltx_para"><p class="ltx_p">Shown before<sup class="ltx_sup">12</sup>.</p></div>
      <figure class="ltx_table"><figcaption class="ltx_caption"><span class="ltx_tag ltx_tag_table">Table 2: </span>
      BLEU.</figcaption><table class="ltx_tabular"><tbody class="ltx_tbody">
      <tr class="ltx_tr"><th class="ltx_th" rowspan="2">Model</th><td colspan="2">BLEU</td><td></td></tr>
      <tr class="ltx_tr"><td>EN-DE</td><td>EN-FR</td><td></td></tr>
      <tr class="ltx_tr"><th class="ltx_th">Deep-Att</th><td></td><td>39.2</td><td></td></tr>
      </tbody></table></figure></article></body></html>"""
    text, _, _ = html_to_markdown(html, "https://arxiv.org/html/1706.03762")
    assert "Shown before^{12}." in text
    assert "| Model | BLEU EN-DE | BLEU EN-FR |\n| --- | --- | --- |\n| Deep-Att |  | 39.2 |" in text
