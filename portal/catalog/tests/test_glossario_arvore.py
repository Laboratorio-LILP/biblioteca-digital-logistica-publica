"""Definições de Subcategorias e Microcategorias no "Saiba mais" de cada
Categoria (glossário de Coleções, 17/09/2026) — sem banco.

Bernardo: "você apenas listou as sub e microcategorias, sem dizer o que são".
A curadoria ainda não escreveu esse texto (nem planilha nem banco o têm), então
taxonomy_v6.ARVORE_DESCRICAO traz um RASCUNHO em Linguagem Simples a partir da
Lei nº 14.133/2021, com o dispositivo anotado por entrada, a validar pela Lina.
"""

import re
from pathlib import Path

from catalog import facets, taxonomy_v6
from catalog.taxonomy_v6 import ARVORE_DESCRICAO, descricao_arvore

REPO = Path(__file__).resolve().parents[3]
TEMPLATES = REPO / "portal" / "templates"
SEED = REPO / "docker" / "postgres" / "init" / "07-categories.sql"


def _nomes_do_seed(tabela):
    sql = SEED.read_text(encoding="utf-8")
    bloco = sql[sql.index(f"INSERT INTO {tabela}"):]
    bloco = bloco[: bloco.index(") AS v(")]
    return [" ".join(n.upper().split()) for n in re.findall(r"^\s+\('([^']+)',", bloco, flags=re.M)]


def test_definicoes_cobrem_exatamente_o_seed():
    subs, micros = _nomes_do_seed("nr_subcategoria"), _nomes_do_seed("nr_microcategoria")
    assert len(subs) == 9 and len(micros) == 15
    assert set(ARVORE_DESCRICAO) == set(subs) | set(micros)      # nem falta, nem sobra


def test_cada_definicao_e_curta_e_em_linguagem_simples():
    for nome, d in ARVORE_DESCRICAO.items():
        assert d.strip() and d.endswith("."), nome
        assert "  " not in d and "R$" not in d, nome              # sem espaço duplo; sem teto em reais
        for frase in re.split(r"(?<=[.!?])\s+", d):
            assert len(frase.split()) <= 30, (nome, frase)
    # sigla explicada onde o rótulo não explica: ETP e TR já saem por extenso via
    # rotulo_sub ("Estudo Técnico Preliminar (ETP)"), então a definição não repete;
    # PMI é rotulada só pela sigla (titulo_pt), então a definição abre com o nome.
    assert not ARVORE_DESCRICAO["ETP"].startswith("Estudo Técnico Preliminar")
    assert not ARVORE_DESCRICAO["TR"].startswith("Termo de Referência")
    assert ARVORE_DESCRICAO["PMI"].startswith("Procedimento de Manifestação de Interesse")


def test_status_de_rascunho_e_fonte_registrados_no_modulo():
    src = Path(taxonomy_v6.__file__).read_text(encoding="utf-8")
    assert "RASCUNHO TÉCNICO, A VALIDAR PELA CURADORIA" in src
    assert "Lei nº 14.133/2021" in src
    assert src.count("# art.") + src.count("# arts.") >= 20         # dispositivo anotado por entrada


def test_descricao_arvore_normaliza_e_tolera_desconhecidos():
    assert descricao_arvore("EMERGÊNCIA - Inciso VIII") == ARVORE_DESCRICAO["EMERGÊNCIA - INCISO VIII"]
    assert descricao_arvore("  registro  de preços (rp) ") == ARVORE_DESCRICAO["REGISTRO DE PREÇOS (RP)"]
    assert descricao_arvore("Nó novo") == "" and descricao_arvore(None) == ""


def test_facets_anexa_a_definicao_a_cada_no(monkeypatch):
    from types import SimpleNamespace
    ns = SimpleNamespace
    monkeypatch.setattr(facets, "categorias_overview", lambda: {
        "nucleo": [{"id": 4, "nome": "SELEÇÃO DO FORNECEDOR", "count": 97}], "transversal": []})
    sub_ = [ns(id=7, category_id=4, nome="LICITAÇÃO")]
    mic_ = [ns(id=70, subcategoria_id=7, nome="PREGÃO")]
    monkeypatch.setattr(facets, "Subcategoria", ns(objects=ns(all=lambda: sub_)))
    monkeypatch.setattr(facets, "Microcategoria", ns(objects=ns(all=lambda: mic_)))
    (cat,) = facets.categorias_glossario()
    (sub,) = cat["subcategorias"]
    assert sub["descricao"] == ARVORE_DESCRICAO["LICITAÇÃO"]
    assert sub["microcategorias"][0]["descricao"] == ARVORE_DESCRICAO["PREGÃO"]


def test_template_mostra_a_definicao_sob_cada_nome():
    t = (TEMPLATES / "collection_list.html").read_text(encoding="utf-8")
    assert t.count('class="glossario__arvore-def"') == 2            # subcategoria e microcategoria
    assert "{{ s.descricao }}" in t and "{{ m.descricao }}" in t
    assert "conforme a Lei nº 14.133/2021" in t                     # a fonte dita ao leitor
