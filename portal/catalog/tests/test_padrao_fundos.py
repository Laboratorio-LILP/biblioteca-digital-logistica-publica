"""Invariantes do padrão de fundos (spec 2026-08-11), sem banco.

Trio por página: abertura cinza quadriculada (.sp-section--pattern, breadcrumb
dentro) -> miolo branco (.sp-section) -> fechamento cinza liso (.sp-section--alt).
Estilo de teste: leitura de arquivo, como test_seta_secoes.py.
"""

from pathlib import Path

PORTAL = Path(__file__).resolve().parents[2]
TEMPLATES = PORTAL / "templates"
CSS = (PORTAL / "static" / "css" / "portal.css").read_text(encoding="utf-8")


def _template(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def test_css_tem_banda_de_abertura_quadriculada():
    assert ".sp-section--pattern" in CSS
    bloco = CSS[CSS.index(".sp-section--pattern"):]
    assert "background-size: 40px 40px" in bloco[:600]      # a grade da home
    assert "rgb(0 0 0 / 0.03)" in bloco[:600]               # alfa 0.045 x 0.7 do overlay do hero
    assert ".sp-section--pattern .breadcrumb" in CSS        # breadcrumb vive dentro da banda


def test_css_respiro_final_cobre_seta_e_form():
    # :last-of-type (nao :last-child): a seta-guia vem depois da ultima secao
    # em home/colecoes; a variante form > serve a /busca/.
    assert "main > .sp-section:last-of-type" in CSS
    assert "main > form > .sp-section:last-of-type" in CSS
    assert "main > .sp-section:last-child" not in CSS
