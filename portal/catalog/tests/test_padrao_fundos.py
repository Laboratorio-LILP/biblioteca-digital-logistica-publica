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


def test_colecoes_segue_o_trio():
    t = _template("collection_list.html")
    assert "breadcrumb-bar" not in t                          # faixa branca antiga saiu
    abertura = t.index('sp-section sp-section--pattern colecoes-hero')
    assert t.index('class="breadcrumb"', abertura) > abertura  # breadcrumb dentro da banda
    # fechamento cinza: a ultima secao (Como encontrar) e --alt; a do meio nao e
    assert t.count("sp-section--alt") == 1
    assert t.index("sp-section--alt") > t.index("Como o acervo se organiza")


def test_sobre_segue_o_trio():
    t = _template("about.html")
    assert "breadcrumb-bar" not in t
    abertura = t.index('sp-section sp-section--pattern sobre-hero')
    assert t.index('class="breadcrumb"', abertura) > abertura
    # miolo alterna branco/cinza a partir do branco; contato fecha cinza
    assert t.count("sp-section--alt") == 2
    assert t.rindex("sp-section--alt") > t.index("Fale com o LILP") - 400


def test_busca_segue_o_trio_dentro_do_form():
    t = _template("search.html")
    assert "breadcrumb-bar" not in t
    form = t.index('id="acervo-form"')
    abertura = t.index("sp-section sp-section--pattern catalog-hero")
    assert abertura > form                                     # tudo dentro do form
    assert t.index('class="breadcrumb"', abertura) > abertura
    miolo = t.index('sp-section">', abertura)                  # banda branca do miolo
    assert t.index("acervo-layout") > miolo
    fecho = t.index("sp-section sp-section--alt")
    assert fecho > t.index("acervo-layout")                    # paginacao na banda cinza
    assert t.index('class="pagination"') > fecho
    assert t.rindex("</form>") > fecho                         # fechamento ainda no form


def test_css_catalog_hero_nao_pinta_banda_propria():
    # A banda vem do .sp-section--pattern; o .catalog-hero nao pode sobrepor
    # fundo branco por ordem de arquivo.
    assert ".catalog-hero { border-bottom" not in CSS
    assert ".catalog-hero__inner" not in CSS


def test_documento_segue_o_trio():
    t = _template("document_detail.html")
    assert "breadcrumb-bar" not in t
    abertura = t.index("sp-section sp-section--pattern doc-detail-hero")
    assert t.index('class="breadcrumb"', abertura) > abertura
    assert t.index("doc-resultnav") > abertura                 # resultnav dentro da abertura
    miolo = t.index('sp-section">', abertura)
    assert t.index("doc-detail-layout") > miolo
    assert "sp-section--alt doc-related" in t                  # fechamento quando ha relacionados


def test_css_doc_hero_e_resultnav_sem_banda_propria():
    assert ".doc-detail-hero { border-bottom" not in CSS
    assert ".doc-resultnav { border-bottom: var(--border); background" not in CSS
    assert ".doc-detail-layout:has(+ .doc-related)" not in CSS


def test_colecao_migrou_para_o_trio():
    t = _template("collection_detail.html")
    assert "content_raw" in t                                  # saiu do wrapper .page
    abertura = t.index("sp-section sp-section--pattern colecoes-hero")
    assert t.index('class="breadcrumb"', abertura) > abertura
    assert "colecao-miolo" in t
    fecho = t.index("sp-section sp-section--alt")
    assert t.index('class="pagination"') > fecho


LEGAIS = [
    "legal/transparencia.html", "legal/acessibilidade.html",
    "legal/politica_privacidade.html", "legal/politica_cookies.html",
    "legal/mapa_site.html", "legal/fale_conosco.html",
]


def test_base_legal_define_o_trio():
    b = _template("legal/_base_legal.html")
    assert "sp-section sp-section--pattern legal-hero" in b
    assert 'class="breadcrumb"' in b
    assert "sp-pagina-legal" in b                              # corpo na banda branca
    assert "sp-section sp-section--alt" in b                   # fechamento (banda de contato)
    assert "fale_conosco" in b                                 # CTA aponta para o Fale Conosco


def test_legais_estendem_o_base_legal():
    for nome in LEGAIS:
        t = _template(nome)
        assert 'extends "legal/_base_legal.html"' in t, nome
        assert "block content" not in t.replace("content_raw", ""), nome


def test_fale_conosco_nao_se_autoreferencia():
    t = _template("legal/fale_conosco.html")
    assert "legal_fechamento" in t                             # sobrescreve a banda de contato


def test_paginas_de_erro_abrem_quadriculado():
    for nome in ("404.html", "500.html"):
        t = _template(nome)
        assert "content_raw" in t, nome
        assert "sp-section sp-section--pattern" in t, nome
        assert t.index("error-page__actions") > t.index('sp-section">'), nome
