"""Corpo do título do documento por faixa de comprimento (17/09/2026) — sem banco.

Bernardo: títulos muito longos ficavam "gigantescos" no herói (o maior, com 270
caracteres, dava 9 linhas/464px no desktop), e a integridade do título original
é inegociável. Solução: o texto fica inteiro e o corpo tipográfico encolhe por
faixa — decidida no servidor pelo filtro `faixa_titulo`, sem JS nem truncamento.
"""

from pathlib import Path

from catalog.templatetags import catalog_tags
from catalog.templatetags.catalog_tags import faixa_titulo

REPO = Path(__file__).resolve().parents[3]
TEMPLATES = REPO / "portal" / "templates"
CSS = (REPO / "portal" / "static" / "css" / "portal.css").read_text(encoding="utf-8")


def test_faixa_pelos_limiares_exatos():
    assert faixa_titulo("x" * 110) == ""          # curta: corpo padrão
    assert faixa_titulo("x" * 111) == "media"
    assert faixa_titulo("x" * 180) == "media"
    assert faixa_titulo("x" * 181) == "longa"
    assert faixa_titulo("x" * 270) == "longa"     # o maior título do acervo v11


def test_faixa_tolera_vazio_e_espacos():
    assert faixa_titulo("") == "" and faixa_titulo(None) == ""
    assert faixa_titulo("   " + "x" * 111 + "   ") == "media"   # espaços não contam


def test_limiares_documentados_com_a_contagem_do_acervo():
    src = Path(catalog_tags.__file__).read_text(encoding="utf-8")
    assert catalog_tags._TITULO_FAIXA_MEDIA == 110 and catalog_tags._TITULO_FAIXA_LONGA == 180
    assert "697 docs" in src and "265" in src and "20 (28px" in src   # medido no acervo v11


def test_template_aplica_o_modificador_e_mantem_o_titulo_inteiro():
    t = (TEMPLATES / "document_detail.html").read_text(encoding="utf-8")
    assert "{% with faixa=document.title|faixa_titulo %}" in t
    assert 'class="doc-detail-hero__title{% if faixa %} doc-detail-hero__title--{{ faixa }}{% endif %}"' in t
    assert ">{{ document.title }}</h1>" in t                       # título inteiro, sem truncatechars
    assert "truncatechars" not in t.split("doc-detail-hero__title")[1][:200]


def test_css_das_faixas_vem_depois_da_base_com_a_mesma_especificidade():
    base = CSS.index(".doc-detail-hero__title {")
    media = CSS.index(".doc-detail-hero__title--media {")
    longa = CSS.index(".doc-detail-hero__title--longa {")
    assert base < media < longa                                    # ordem decide (mesma especificidade)
    assert ".doc-detail-hero h1 {" not in CSS                     # a base migrou para a classe
    assert "clamp(24px, 3.2vw, 36px)" in CSS[media:media + 120]
    assert "clamp(22px, 2.5vw, 28px)" in CSS[longa:longa + 120]
    assert "line-clamp" not in CSS[base:longa + 200]              # nada de cortar o título
