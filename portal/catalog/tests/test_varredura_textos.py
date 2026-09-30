"""Varredura dos textos que descrevem o acervo (T7, set/2026) — sem banco.

Com normas, leis, decretos e portarias fora do acervo (decisão de 10/09/2026)
e Vídeos fora do vocabulário, textos fixos que dizem que a Biblioteca reúne
"documentos normativos"/"normas"/"vídeos" ficam falsos. Os textos-descrição
do acervo não podem citá-los; a seção "Marco normativo" do Sobre e as páginas
legais falam do marco legal da própria Biblioteca e ficam como estão.
"""

import re
from pathlib import Path

from catalog.taxonomy_v6 import COLECOES_V6

TEMPLATES = Path(__file__).resolve().parents[2] / "templates"


def _template(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def test_meta_description_padrao_nao_cita_normas():
    base = _template("base.html")
    meta = re.search(r'<meta name="description" content="([^"]*)"', base).group(1)
    assert "normativ" not in meta.lower()
    assert "jurisprudenciais" in meta


def test_intro_do_sobre_nao_cita_normas_mas_marco_normativo_fica():
    sobre = _template("about.html")
    intro = sobre[sobre.index('<p class="page__intro">'): sobre.index("</p>", sobre.index('<p class="page__intro">'))]
    assert "normativ" not in intro.lower()
    assert "jurisprudência" in intro
    assert "Marco normativo" in sobre                      # base legal da Biblioteca — não é o acervo


def test_heros_do_acervo_e_da_home_nao_citam_normas_nem_videos():
    for nome, marcador in (("search.html", "catalog-hero__grid"), ("home.html", "hero__copy")):
        t = _template(nome)
        trecho = t[t.index(marcador): t.index(marcador) + 900].lower()
        assert "normativ" not in trecho, nome
        assert "vídeo" not in trecho, nome


def test_descricoes_das_colecoes_nao_citam_tipos_retirados():
    for c in COLECOES_V6:
        d = c["descricao"].lower()
        assert "normativ" not in d and "vídeo" not in d, c["nome"]


def test_colecoes_e_glossario_sem_tipos_retirados():
    t = _template("metodologia/_conceitos.html").lower()
    assert "documentos normativos" not in t and "vídeo" not in t
