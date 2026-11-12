"""Formulas in JATS: the publisher's LaTeX, MathML converted to LaTeX, and flattened text as the last resort."""

import xml.etree.ElementTree as ET

from paperreader.extract import jats_to_text
from paperreader.mathml import tex_math, to_latex

MML = 'xmlns:mml="http://www.w3.org/1998/Math/MathML"'


def latex(mathml: str) -> str | None:
    return to_latex(ET.fromstring(f"<mml:math {MML}>{mathml}</mml:math>"))


def test_fractions_scripts_and_lines_of_a_display():
    # Equation 1 of PMC11706453 (PLoS Comput Biol), which used to read "d T d t = - β T V , ... δ I 2 K δ + I 2".
    row = ("<mml:mtr><mml:mtd><mml:mfrac><mml:mrow><mml:mi>d</mml:mi><mml:msub><mml:mi>I</mml:mi><mml:mn>2</mml:mn>"
           "</mml:msub></mml:mrow><mml:mrow><mml:mi>d</mml:mi><mml:mi>t</mml:mi></mml:mrow></mml:mfrac></mml:mtd>"
           "<mml:mtd><mml:mo>=</mml:mo><mml:mfrac><mml:mrow><mml:mi>δ</mml:mi><mml:msub><mml:mi>I</mml:mi><mml:mn>2</mml:mn>"
           "</mml:msub></mml:mrow><mml:mrow><mml:msub><mml:mi>K</mml:mi><mml:mi>δ</mml:mi></mml:msub><mml:mo>+</mml:mo>"
           "<mml:msub><mml:mi>I</mml:mi><mml:mn>2</mml:mn></mml:msub></mml:mrow></mml:mfrac></mml:mtd></mml:mtr>")
    assert latex(f"<mml:mtable>{row}{row}</mml:mtable>") == (
        "\\begin{aligned}\\frac{d I_{2}}{d t} & = \\frac{\\delta I_{2}}{K_{\\delta} + I_{2}} \\\\ "
        "\\frac{d I_{2}}{d t} & = \\frac{\\delta I_{2}}{K_{\\delta} + I_{2}}\\end{aligned}")


def test_brackets_and_groups_are_not_doubled_or_added():
    assert latex("<mml:msup><mml:mrow><mml:mo>(</mml:mo><mml:mi>x</mml:mi><mml:mo>+</mml:mo><mml:mi>y</mml:mi>"
                 "<mml:mo>)</mml:mo></mml:mrow><mml:mn>2</mml:mn></mml:msup>") == "{( x + y )}^{2}"
    # TΔ′ (Nature Communications): mathml-to-latex wrote (TΔ)′.
    assert latex("<mml:msup><mml:mrow><mml:mi>T</mml:mi><mml:mi>Δ</mml:mi></mml:mrow><mml:mo>′</mml:mo></mml:msup>"
                 ) == "{T \\Delta}^{'}"
    assert latex("<mml:mo>{</mml:mo><mml:mi>a</mml:mi><mml:mo>}</mml:mo>") == "\\{ a \\}"


def test_scripts_before_a_symbol_and_asterisks():
    # *OH + ^ΔH (Nature Communications): mathml-to-latex wrote "\star OH + \_{}^{\Delta}H_{}^{}".
    assert latex("<mml:mo>*</mml:mo><mml:mi>OH</mml:mi><mml:mo>+</mml:mo><mml:mmultiscripts><mml:mi>H</mml:mi>"
                 "<mml:mprescripts/><mml:none/><mml:mi>Δ</mml:mi></mml:mmultiscripts>") == "\\ast OH + {}^{\\Delta}H"


def test_a_matrix_keeps_its_environment():
    cells = "".join(f"<mml:mtr><mml:mtd><mml:mi>{a}</mml:mi></mml:mtd><mml:mtd><mml:mi>{b}</mml:mi></mml:mtd></mml:mtr>"
                    for a, b in (("a", "b"), ("c", "d")))
    assert latex(f"<mml:mi>M</mml:mi><mml:mo>=</mml:mo><mml:mrow><mml:mo>(</mml:mo><mml:mtable>{cells}</mml:mtable>"
                 "<mml:mo>)</mml:mo></mml:mrow>") == "M = ( \\begin{matrix}a & b \\\\ c & d\\end{matrix} )"


def test_latex_kept_by_the_publisher_is_used():
    assert latex("<mml:semantics><mml:mi>x</mml:mi><mml:annotation encoding='application/x-tex'>x^*</mml:annotation>"
                 "</mml:semantics>") == "x^*"
    assert latex("<mml:semantics><mml:mi>x</mml:mi><mml:annotation encoding='text/plain'>ex</mml:annotation>"
                 "</mml:semantics>") == "x"
    # Springer Nature wraps every formula in a LaTeX document of its own.
    springer = ("\\documentclass[12pt]{minimal}\n\\usepackage{amsmath}\n\\setlength{\\oddsidemargin}{-69pt}\n"
                "\\begin{document}$$\\frac{1}{2}E$$\\end{document}")
    assert tex_math(springer) == "\\frac{1}{2}E"
    assert tex_math("$a$ and $b$") == "$a$ and $b$"


def test_jats_formulas_in_the_text():
    xml = f"""<article {MML}><body><sec><title>Model</title>
      <p>The rate <inline-formula><mml:math><mml:msup><mml:mi>k</mml:mi><mml:mn>2</mml:mn></mml:msup></mml:math>
      </inline-formula> follows<disp-formula id="E1"><label>(1)</label><mml:math display="block"><mml:mfrac>
      <mml:mi>a</mml:mi><mml:mi>b</mml:mi></mml:mfrac></mml:math></disp-formula>where<list><list-item><p>a is
      large</p></list-item></list></p>
      <disp-formula id="E2"><label>(2)</label><alternatives><tex-math>\\documentclass{{minimal}}\\begin{{document}}
      $$E=mc^2$$\\end{{document}}</tex-math><mml:math><mml:mi>E</mml:mi></mml:math></alternatives></disp-formula>
      <disp-formula id="E3"><label>(3)</label>
        <mml:math><mml:msub><mml:mi>x</mml:mi></mml:msub></mml:math></disp-formula>
      </sec></body></article>""".encode()
    text, _, _ = jats_to_text(xml)
    # The paragraph without its display formula and list, which follow it as blocks, once.
    assert "The rate $k^{2}$ follows where\n\n$$\\frac{a}{b}$$ (1)\n\n- a is large" in text
    assert text.count("\\frac{a}{b}") == 1 and text.count("a is large") == 1
    assert "$$E=mc^2$$ (2)" in text  # the publisher's LaTeX, out of its document
    assert "\n\nx (3)" in text  # malformed MathML: flattened, without $, so the reader knows
