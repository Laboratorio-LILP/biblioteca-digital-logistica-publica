"""Metodologia (chamava-se Coleções até 23/09/2026) = porte da "Metodologia de
classificação" do protótipo do Eduardo (github.com/dudyfarias/biblioteca, branch
codex/biblioteca-home-acervo-filtros, commits de 10 a 15/09/2026) — sem banco.

Um só documento com três abas (Conceitos e coleções · Categorias · Assuntos) que
trocam sem recarregar. Trava o conteúdo (seis campos, três exemplos, foco/ícone
dos assuntos), a reconciliação com a árvore da curadoria (Procedimentos
Auxiliares é SUBcategoria de Seleção do Fornecedor; Registro de Preços (RP) é
microcategoria), os ícones no sprite, as rotas e os redirecionamentos dos
endereços antigos, a estrutura do template, o JS CSP-safe e o CSS.
"""

import re
from pathlib import Path

from django.urls import resolve, reverse
from django.views.generic import RedirectView

from catalog import taxonomy_v6 as t6
from catalog.models import NATUREZA_CHOICES
from catalog.templatetags.catalog_tags import rotulo_sub, titulo_pt

REPO = Path(__file__).resolve().parents[3]
TEMPLATES = REPO / "portal" / "templates"
STATIC = REPO / "portal" / "static"
SEED = REPO / "docker" / "postgres" / "init" / "07-categories.sql"
ABAS = ("conceitos", "categorias", "assuntos")
PARCIAIS = tuple(f"metodologia/_{aba}.html" for aba in ABAS)


def _t(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def _sprite_ids():
    return set(re.findall(r'<symbol id="(fi-[a-z0-9-]+)"', _t("_partials/_feather.html")))


def _seed(tabela):
    sql = SEED.read_text(encoding="utf-8")
    bloco = sql[sql.index(f"INSERT INTO {tabela}"):]
    bloco = bloco[: bloco.index(") AS v(")]
    return re.findall(r"^\s+\('([^']+)',", bloco, flags=re.M)


def test_seis_campos_na_ordem_da_formula():
    ids = [c["id"] for c in t6.CAMPOS_CLASSIFICACAO]
    assert ids == ["colecao", "categoria", "subcategoria", "microcategoria", "assunto", "natureza"]
    assert [c["nome"] for c in t6.CAMPOS_CLASSIFICACAO if c["obrigatorio"]] == ["Coleção", "Categoria", "Assunto"]
    sprite = _sprite_ids()
    for c in t6.CAMPOS_CLASSIFICACAO:
        assert c["icon"] in sprite, c["icon"]
        assert c["pergunta"].endswith("?") and c["descricao"].endswith(".") and c["legenda"].endswith("."), c["id"]
        for frase in re.split(r"(?<=[.!?])\s+", c["descricao"]):
            assert len(frase.split()) <= 30, (c["id"], frase)
    # terminologia: "Etapa" explica a Categoria, nunca a nomeia sozinha
    assert t6.CAMPOS_CLASSIFICACAO[1]["resumo"] == "Etapa da contratação"
    assert "categoria processual" not in str(t6.CAMPOS_CLASSIFICACAO).lower()


def test_exemplos_usam_a_arvore_da_curadoria_e_nao_a_do_prototipo():
    tem_categorias = "INSERT INTO nr_category" in SEED.read_text(encoding="utf-8")
    categorias = {titulo_pt(n) for n in _seed("nr_category")} if tem_categorias else set()
    subs = {rotulo_sub(n) for n in _seed("nr_subcategoria")}
    micros = {titulo_pt(n) for n in _seed("nr_microcategoria")}
    colecoes = {c["nome"] for c in t6.COLECOES_V6}
    naturezas = {v for v, _ in NATUREZA_CHOICES}
    assert len(t6.EXEMPLOS_CLASSIFICACAO) == 3
    for ex in t6.EXEMPLOS_CLASSIFICACAO:
        v = ex["valores"]
        assert len(v) == 6, ex["titulo"]
        assert v[0] in colecoes, v[0]
        if categorias:
            assert v[1] in categorias, v[1]
        assert v[2] in subs | {"Não se aplica"}, v[2]
        assert v[3] in micros | {"Não se aplica"}, v[3]
        assert v[4] in t6.ASSUNTOS_DESCRICAO, v[4]
        assert v[5] in naturezas, v[5]
    # a divergência do protótipo (Procedimentos Auxiliares como categoria) foi resolvida
    primeiro = t6.EXEMPLOS_CLASSIFICACAO[0]["valores"]
    assert primeiro[1:4] == ["Seleção do Fornecedor", "Procedimentos Auxiliares", "Registro de Preços (RP)"]
    assert "Fase Preparatória - ETP" not in str(t6.EXEMPLOS_CLASSIFICACAO)
    assert "Contratação Todas as Fases" not in str(t6.EXEMPLOS_CLASSIFICACAO)


def test_foco_icone_e_comparacoes_cobrem_os_assuntos():
    assert set(t6.ASSUNTOS_FOCO) == set(t6.ASSUNTOS_DESCRICAO) == set(t6.ASSUNTOS_ICONE)
    sprite = _sprite_ids()
    assert all(i in sprite for i in t6.ASSUNTOS_ICONE.values())
    assert all(i in sprite for i in t6.COLECOES_ICONE_METODOLOGIA.values())
    assert set(t6.COLECOES_ICONE_METODOLOGIA) <= {c["nome"] for c in t6.COLECOES_V6}
    for par, texto in t6.ASSUNTOS_COMPARACOES:
        a, b = par.split(" / ")
        assert a in t6.ASSUNTOS_DESCRICAO and b in t6.ASSUNTOS_DESCRICAO, par
        assert texto.endswith(".")
    # o foco é rascunho do protótipo, não texto da curadoria — o módulo diz isso
    src = Path(t6.__file__).read_text(encoding="utf-8")
    assert "TRANSCRITO DO PROTÓTIPO DO EDUARDO" in src and "a validar" in src


def test_rotas_da_metodologia_e_redirecionamentos_dos_enderecos_antigos():
    assert reverse("catalog:metodologia") == "/metodologia/"
    assert reverse("catalog:metodologia_categorias") == "/metodologia/categorias/"
    assert reverse("catalog:metodologia_assuntos") == "/metodologia/assuntos/"
    assert resolve("/metodologia/").func is resolve("/metodologia/assuntos/").func      # uma view, três abas
    assert resolve("/metodologia/").kwargs == {} and resolve("/metodologia/categorias/").kwargs == {"aba": "categorias"}
    antigos = (("/colecoes/", "catalog:metodologia"), ("/colecoes/categorias/", "catalog:metodologia_categorias"),
               ("/colecoes/assuntos/", "catalog:metodologia_assuntos"))
    for antigo, novo in antigos:
        m = resolve(antigo)
        assert m.func.view_class is RedirectView, antigo
        assert m.func.view_initkwargs == {"pattern_name": novo, "permanent": True}, antigo


def test_um_documento_com_tres_abas_marcadas_no_servidor():
    t = _t("metodologia.html")
    assert t.startswith('{% extends "base.html" %}')
    assert 'role="tablist"' in t and "data-metodologia-abas" in t
    assert t.count('role="tab"') == 1 and t.count('role="tabpanel"') == 3 and t.count("data-aba-hero=") == 3
    assert 'aria-selected="{% if aba.ativa %}true{% else %}false{% endif %}"' in t
    assert "tabindex" not in t             # sem JS as três abas são links na ordem de Tab; o JS põe o tabindex
    for chave in ABAS:
        oculta = '{%% if aba_ativa.chave != "%s" %%} hidden{%% endif %%}' % chave
        assert t.count(oculta) == 2, chave                                              # abertura + painel
        assert '{%% include "metodologia/_%s.html" %%}' % chave in t, chave
        assert 'aria-labelledby="aba-%s"' % chave in t, chave
    assert "js/metodologia.js" in t and "js/seta-secoes.js" in t
    assert "<span>Metodologia</span>" in t and "Coleções</span>" not in t            # breadcrumb com o nome novo
    assert "{{ aba_ativa.titulo }}" in t and "{{ aba_ativa.meta }}" in t
    for nome in PARCIAIS:
        assert _t(nome).startswith("{% load catalog_tags %}"), nome


def test_estrutura_dos_paineis():
    conceitos = _t("metodologia/_conceitos.html")
    assert "data-classification-trail" in conceitos and 'data-trail-field="{{ campo.id }}"' in conceitos
    assert 'aria-controls="classificacao-{{ campo.id }} classificacao-mobile-{{ campo.id }}"' in conceitos
    assert 'class="method-practical"' in conceitos and 'class="method-collection-grid"' in conceitos
    assert conceitos.count("<details") == 2 and 'id="hierarquia"' in conceitos and 'id="exemplos"' in conceitos
    assert "{{ c.tipos|join" in conceitos                          # tipos do vocabulário vigente, não do protótipo
    assert "documentos normativos" not in conceitos.lower() and "vídeo" not in conceitos.lower()
    assert "{% url 'catalog:metodologia_categorias' %}" in conceitos   # o JS troca a aba no lugar
    assuntos = _t("metodologia/_assuntos.html")
    assert 'class="method-subject-browser"' in assuntos and 'type="search"' in assuntos
    assert ('class="method-subject-more" type="button" aria-expanded="false" '
            'aria-controls="assuntos-lista" hidden') in assuntos
    assert 'data-subject-focus="{{ a.foco }}"' in assuntos and "{{ a.longa|default:a.curta }}" in assuntos
    categorias = _t("metodologia/_categorias.html")
    assert 'class="method-subject-tree"' in categorias and "não se desdobra em subcategorias" in categorias
    # âncoras da seta-guia dentro dos painéis (duas em conceitos, uma nos outros)
    assert conceitos.count("data-sec=") == 2 and categorias.count("data-sec=") == 1 and assuntos.count("data-sec=") == 1
    sprite = _sprite_ids()
    for nome in ("metodologia.html",) + PARCIAIS:
        for icone in re.findall(r'href="#(fi-[a-z0-9-]+)"', _t(nome)):
            assert icone in sprite, (nome, icone)


def test_a_plataforma_chama_a_pagina_de_metodologia():
    base = _t("base.html")
    assert ">Metodologia</a>" in base and ">Coleções</a>" not in base
    assert "current_url_name == 'metodologia_assuntos'" in base                    # menu ativo nas três abas
    assert "{% url 'catalog:metodologia' %}#colecoes" in _t("home.html")   # "Consultar Coleções" cai nas coleções
    mapa = _t("legal/mapa_site.html")
    assert ">Metodologia</a>" in mapa and "{% url 'catalog:metodologia_assuntos' %}" in mapa
    busca = _t("search.html")
    assert "{% url 'catalog:metodologia_categorias' %}" in busca and "{% url 'catalog:metodologia_assuntos' %}" in busca
    for p in TEMPLATES.rglob("*.html"):                                    # nenhum template usa as rotas antigas
        s = p.read_text(encoding="utf-8")
        for velha in ("collection_list", "colecoes_categorias", "colecoes_assuntos"):
            assert velha not in s, (p.name, velha)


def test_js_csp_safe_e_progressivo():
    js = (STATIC / "js" / "metodologia.js").read_text(encoding="utf-8")
    assert js.startswith("/*") and '"use strict"' in js
    assert "data-classification-trail" in js and ".method-subject-browser" in js and "data-metodologia-abas" in js
    assert "innerHTML" not in js and "eval(" not in js and "onclick" not in js
    assert "ArrowRight" in js and "End" in js                       # teclado na trilha e nas abas
    assert 'normalize("NFD")' in js                                  # busca sem acento
    assert r"/[\u0300-\u036f]/g" in js                    # acentos por escape, não por caractere literal
    # tabindex itinerante posto pelo JS na carga; link clicado que some com a aba anterior entrega o foco à aba nova
    assert "a.tab.tabIndex = a === atual ? 0 : -1" in js
    assert 'if (link.closest("[hidden]")) aba.tab.focus(' in js
    assert "toggle.hidden = isSearching || total <= 6" in js         # sem JS, todos os assuntos aparecem
    # abas sem recarregar: history + popstate + título + aviso à seta-guia; clique com modificador segue como link
    assert "history.pushState(" in js and 'addEventListener("popstate"' in js and "history.replaceState(" in js
    assert "document.title = titulo" in js and 'new CustomEvent("bdlp:secoes-mudaram")' in js
    assert "event.metaKey || event.ctrlKey" in js and "event.preventDefault()" in js
    seta = (STATIC / "js" / "seta-secoes.js").read_text(encoding="utf-8")
    assert "closest('[hidden]')" in seta and "'bdlp:secoes-mudaram'" in seta and "recarregar:" in seta


def test_css_do_porte():
    css = (STATIC / "css" / "portal.css").read_text(encoding="utf-8")
    assert "--rgb-blue-medium: 66 151 211" in css
    assert ".method-jumpnav { position: sticky; top: 77px" in css
    assert ".classification-steps { display: grid; grid-template-columns: repeat(6" in css
    assert '.classification-step[data-trail-field="assunto"] { --field-accent: var(--rgb-red); }' in css
    regras = re.sub(r"/\*.*?\*/", "", css, flags=re.S)                 # o comentário do bloco cita o que NÃO se usa
    assert "color-mix(" not in regras and "#ff161f" not in regras.lower()   # tokens da plataforma, vermelho GESP
    assert (".method-page [hidden], .method-jumpnav [hidden], .colecoes-hero [hidden] "
            "{ display: none !important; }") in css
    assert '.method-jumpnav a[aria-selected="true"]::after' in css and ".method-jumpnav a[aria-current" not in css
    assert "@media (prefers-reduced-motion: reduce) {\n  .method-page *" in css


def test_assuntos_na_ordem_da_curadoria_como_no_prototipo():
    # a página numera 01–16 na sequência da caracterização da Lina (= protótipo), não na do banco
    itens = [{"nome": n} for n in sorted(t6.ASSUNTOS_DESCRICAO)] + [{"nome": "Zzz fora da lista"}]
    ordenados = [a["nome"] for a in t6.ordenar_como_a_curadoria(itens)]
    assert ordenados[:16] == list(t6.ASSUNTOS_DESCRICAO)
    assert ordenados[:3] == ["Aspectos Jurídicos e Regulatórios", "Governança", "Inovação e Tecnologia"]
    assert ordenados[-1] == "Zzz fora da lista"
