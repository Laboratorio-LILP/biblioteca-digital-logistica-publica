"""Definições dos Assuntos e Categorias na interface (T6, set/2026) — sem banco.

O subsecretário pediu "descrição clara do que entra em cada Assunto". A Lina
escreveu as definições (11/09/2026, Caracterizacao_Assuntos_Taxonomia_BDLP.xlsx):
caracterização (curta) e explicação (longa) para os 16 Assuntos. Como
nr_assunto não tem coluna de descrição (portal somente leitura, sem migrations
Django), o texto fica versionado em taxonomy_v6.ASSUNTOS_DESCRICAO, no mesmo
padrão de COLECOES_V6["descricao"]. Categorias reusam nr_category.description.
"""

import re
from pathlib import Path

from catalog import facets, taxonomy_v6
from catalog.taxonomy_v6 import ASSUNTOS_DESCRICAO, descricao_assunto
from catalog.templatetags import catalog_tags

REPO = Path(__file__).resolve().parents[3]
TEMPLATES = REPO / "portal" / "templates"
SEED_ASSUNTOS = REPO / "docker" / "postgres" / "init" / "06-taxonomia.sql"


def _template(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def _assuntos_do_seed():
    sql = SEED_ASSUNTOS.read_text(encoding="utf-8")
    bloco = sql[sql.index("INSERT INTO nr_assunto"):]
    bloco = bloco[: bloco.index(";")]
    return [n for n, _, _ in re.findall(r"\('([^']+)', '([^']+)', (\d+)\)", bloco)]


def test_descricoes_cobrem_exatamente_os_16_assuntos_do_seed():
    seed = _assuntos_do_seed()
    assert len(seed) == 16
    assert set(ASSUNTOS_DESCRICAO) == set(seed)


def test_cada_assunto_tem_curta_e_longa_nao_vazias():
    for nome, d in ASSUNTOS_DESCRICAO.items():
        assert set(d) == {"curta", "longa"}, nome
        assert d["curta"].strip() and d["longa"].strip(), nome
        assert d["curta"].endswith(".") and d["longa"].endswith("."), nome
        assert "  " not in d["curta"] and "  " not in d["longa"], nome   # espaço duplo corrigido
        assert ".." not in d["longa"], nome                               # "públicos.." corrigido


def test_texto_da_curadoria_copiado_verbatim():
    # Amostras do Apêndice A (Lina, 11/09/2026), incluindo as correções autorizadas.
    assert ASSUNTOS_DESCRICAO["Governança"]["curta"] == "Estruturas, princípios e práticas de gestão pública."
    assert "melhoria dos processos da gestão pública" in ASSUNTOS_DESCRICAO["Inovação e Tecnologia"]["longa"]
    assert "melhoriua" not in ASSUNTOS_DESCRICAO["Inovação e Tecnologia"]["longa"]
    assert ASSUNTOS_DESCRICAO["Gestão Estratégica e Desempenho das Contratações"]["curta"] == "Operação e resultados."
    assert ASSUNTOS_DESCRICAO["Logística Pública Internacional"]["longa"] == (
        "Marcos, comparações e cooperação internacional em contratações públicas."
    )
    assert "(1 registro)" not in ASSUNTOS_DESCRICAO["Catálogo eletrônico de Padronização"]["longa"]


def test_fonte_registrada_no_modulo():
    src = Path(taxonomy_v6.__file__).read_text(encoding="utf-8")
    assert "Caracterizacao_Assuntos_Taxonomia_BDLP.xlsx" in src
    assert "11/09/2026" in src
    assert "texto da curadoria" in src.lower()


def test_descricao_assunto_com_fallback_vazio():
    assert descricao_assunto("Governança")["curta"].startswith("Estruturas")
    assert descricao_assunto("Assunto Inexistente") == {"curta": "", "longa": ""}
    assert descricao_assunto(None) == {"curta": "", "longa": ""}
    # filtros de template com o mesmo fallback
    assert catalog_tags.assunto_curta("Transparência") == "Publicidade e acesso à informação."
    assert catalog_tags.assunto_curta("xpto") == ""
    assert catalog_tags.assunto_longa("Integridade").startswith("Trata de programas de integridade")


def test_facets_expoe_o_glossario():
    assert callable(facets.assuntos_glossario) and callable(facets.categorias_glossario)
    assert "ASSUNTOS_DESCRICAO" in facets.assuntos_glossario.__code__.co_names or \
        "descricao_assunto" in facets.assuntos_glossario.__code__.co_names


def test_pagina_de_colecoes_tem_o_glossario():
    t = _template("collection_list.html")
    assert 'id="assuntos"' in t and 'id="categorias"' in t
    assert "glossario__item" in t and "<details" in t
    assert "?assunto_id={{" in t and "?category_id={{" in t
    assert "Hoje são 14 assuntos" not in t                    # contagem chumbada saiu
    assert "COLEÇÃO" in t and "CATEGORIA" in t and "ASSUNTO" in t and "NATUREZA" in t   # fórmula
    assert "multidimensional" in t or "várias dimensões" in t
    assert "sem filtro nenhum" in t
    # ainda 3 âncoras de seção e um único fechamento cinza (padrão de fundos)
    assert t.count("data-sec=") == 3
    assert t.count("sp-section--alt") == 1


def test_busca_linka_o_glossario_nas_facetas():
    t = _template("search.html")
    assert t.count("O que significa cada opção?") == 2
    assert "{% url 'catalog:collection_list' %}#assuntos" in t
    assert "{% url 'catalog:collection_list' %}#categorias" in t
    assert "title=" not in t[t.index("O que significa cada opção?") - 200: t.index("O que significa cada opção?")]


def test_documento_mostra_a_caracterizacao_curta():
    t = _template("document_detail.html")
    assert "assunto_curta" in t
    assert "meta-item__desc" in t
    # a descrição da etapa vem do seed de categorias (description)
    assert "cat.description" in t
