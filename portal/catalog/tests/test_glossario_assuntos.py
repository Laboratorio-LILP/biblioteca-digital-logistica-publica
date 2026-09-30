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


def test_abas_da_metodologia_tem_o_glossario():
    # 23/09/2026: o glossário virou duas abas da Metodologia (porte da interface do Eduardo)
    cat = _template("metodologia/_categorias.html")
    ass = _template("metodologia/_assuntos.html")
    assert 'id="categorias"' in cat and 'id="assuntos"' in ass
    assert "<details" in cat and "<details" in ass
    assert "?assunto_id={{" in ass and "?category_id={{" in cat
    doc = _template("metodologia.html")
    assert "Hoje são 14 assuntos" not in doc and "Hoje são 14 assuntos" not in ass
    assert "A taxonomia é multidimensional." in doc
    assert "sem selecionar filtros" in doc                        # a busca por palavra funciona sem filtro

def test_categorias_trazem_contagem_e_arvore_no_saiba_mais():
    # 23/09: subcategorias e microcategorias com definição no "Saiba mais" de cada
    # categoria (cartão expansível do protótipo), nomes como no Acervo
    t = _template("metodologia/_categorias.html")
    assert "Ainda sem documentos" in t and "pluralize_pt" in t
    assert 'class="method-subject-tree"' in t and "&amp;microcategoria_id={{ m.id }}" in t
    assert "{{ s.nome|rotulo_sub }}" in t and "{{ s.nome|titulo_pt }}" not in t
    css = (TEMPLATES.parent / "static" / "css" / "portal.css").read_text(encoding="utf-8")
    assert ".method-subjects { display: grid; grid-template-columns: repeat(3" in css   # Assuntos: grade
    # Categorias: lista de uma coluna (a árvore aberta em grade deixava buracos ao lado)
    assert 'class="method-subjects method-subjects--lista"' in t
    assert ".method-subjects.method-subjects--lista { grid-template-columns: 1fr" in css
    assert ".method-subjects--lista .method-subject-tree { columns: 3; }" in css

def test_metodologia_segue_o_porte_do_eduardo():
    """23/09/2026: a Metodologia é um só documento no trio de fundos — abertura
    quadriculada, abas coladas, miolo branco com um painel por aba e fechamento
    cinza — e nada da versão anterior (tema-grupo, glossário, cards de organização) sobra."""
    doc = _template("metodologia.html")
    css = (TEMPLATES.parent / "static" / "css" / "portal.css").read_text(encoding="utf-8")
    assert "sp-section sp-section--pattern colecoes-hero" in doc
    assert 'class="method-jumpnav"' in doc and 'role="tablist"' in doc and "aria-selected=" in doc
    assert doc.count("sp-section--alt") == 1 and "method-next" in doc
    for nome in ("metodologia.html", "metodologia/_conceitos.html", "metodologia/_categorias.html",
                 "metodologia/_assuntos.html"):
        t = _template(nome)
        assert "tema-grupo" not in t and "glossario__" not in t and "org-card" not in t, nome
    assert ".method-jumpnav { position: sticky; top: 77px" in css
    for morto in (".glossario", ".org-card__nota", ".curadoria-dica", ".colecoes-glossario",
                  ".section-heading + .tema-grupo"):
        assert morto not in css, morto

def test_categorias_glossario_anexa_subcategorias_na_ordem(monkeypatch):
    # Comportamento, sem banco: a lista plana segue núcleo + transversais e cada
    # categoria recebe SUAS subcategorias na ordem em que o modelo as entrega.
    from types import SimpleNamespace

    ns = SimpleNamespace
    monkeypatch.setattr(facets, "categorias_overview", lambda: {
        "nucleo": [{"id": 3, "nome": "PLANEJAMENTO/FASE PREPARATÓRIA", "count": 81}],
        "transversal": [{"id": 6, "nome": "CONTEÚDOS TRANSVERSAIS", "count": 746}],
    })
    monkeypatch.setattr(facets, "Subcategoria", ns(objects=ns(all=lambda: [
        ns(id=4, category_id=3, nome="ETP"),
        ns(id=3, category_id=3, nome="TR"),
        ns(id=99, category_id=42, nome="ÓRFÃ"),          # categoria fora da visão: ignorada
    ])))
    monkeypatch.setattr(facets, "Microcategoria", ns(objects=ns(all=lambda: [
        ns(id=7, subcategoria_id=3, nome="MICRO A"),
        ns(id=8, subcategoria_id=3, nome="MICRO B"),
        ns(id=9, subcategoria_id=99, nome="ÓRFÃ"),
    ])))
    out = facets.categorias_glossario()
    assert [c["id"] for c in out] == [3, 6]
    # (a definição de cada nó — descricao_arvore — é coberta em test_glossario_arvore)
    podar = lambda n: {k: v for k, v in n.items() if k != "descricao"}   # noqa: E731
    assert [podar(sub) | {"microcategorias": [podar(m) for m in sub["microcategorias"]]}
            for sub in out[0]["subcategorias"]] == [
        {"id": 4, "nome": "ETP", "microcategorias": []},
        {"id": 3, "nome": "TR", "microcategorias": [{"id": 7, "nome": "MICRO A"}, {"id": 8, "nome": "MICRO B"}]},
    ]
    assert out[1]["subcategorias"] == []




def test_busca_linka_o_glossario_nas_facetas():
    t = _template("search.html")
    assert t.count("O que significa cada opção?") == 2
    assert "{% url 'catalog:metodologia_assuntos' %}" in t
    assert "{% url 'catalog:metodologia_categorias' %}" in t
    assert "title=" not in t[t.index("O que significa cada opção?") - 200: t.index("O que significa cada opção?")]

def test_documento_mostra_a_caracterizacao_curta():
    t = _template("document_detail.html")
    assert "assunto_curta" in t
    assert "meta-item__desc" in t
    # a descrição da etapa vem do seed de categorias (description)
    assert "cat.description" in t


def test_textos_das_paginas_de_colecoes_em_linguagem_simples():
    """LS (NBR ISO 24495-1) nas três abas da Metodologia: verbos neutros quanto ao dispositivo
    (sem "Clique"), um só nome para a mesma coisa ("tipo de informação", como na
    ficha do documento), e frases curtas nas introduções."""
    import re
    css_intros = r'<p class="(?:page__intro|method-rule|classification-intro|method-section-intro)">(.*?)</p>'
    for nome in ("metodologia.html", "metodologia/_conceitos.html",
                 "metodologia/_categorias.html", "metodologia/_assuntos.html"):
        visivel = re.sub(r"\{#.*?#\}", "", _template(nome))
        visivel = re.sub(r"\{% comment %\}.*?\{% endcomment %\}", "", visivel, flags=re.S)
        assert "Clique" not in visivel and "clique" not in visivel, nome
        assert "tipo de material" not in visivel, nome
        for par in re.findall(css_intros, visivel, flags=re.S):
            texto = " ".join(re.sub(r"<[^>]+>", " ", par).split())
            for frase in re.split(r"(?<=[.!?])\s+", texto):
                assert len(frase.split()) <= 25, (nome, frase)
    assert "tipo de informação" in _template("metodologia/_conceitos.html").lower()

