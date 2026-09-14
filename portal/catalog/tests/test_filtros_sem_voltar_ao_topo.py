"""Filtros do Acervo sem voltar ao topo (T1, set/2026): contratos sem banco.

"Toda vez que clica, ele vai lá pra cima" (subsecretário, vídeo 2). Base sem
JS: o form e todos os links GET (chips, "Limpar tudo", paginação) aterrissam
em #acervo-resultados e a barra lateral fica sticky no desktop. Melhoria
progressiva: acervo-filters.js busca o HTML completo da mesma view (fetch),
troca as três regiões (#acervo-sidebar, #acervo-resultados, #acervo-paginacao),
preserva rolagem/foco/<details>/drawer e atualiza a URL (pushState/popstate).
Cena reproduzível: tools/evidencias_playwright.py (JS ligado e desligado).
Estilo: leitura de arquivo, como test_facets_busca.py.
"""

import re
from pathlib import Path

PORTAL = Path(__file__).resolve().parents[2]
TEMPLATES = PORTAL / "templates"
JS = (PORTAL / "static" / "js" / "acervo-filters.js").read_text(encoding="utf-8")
CSS = (PORTAL / "static" / "css" / "portal.css").read_text(encoding="utf-8")


def _template(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


# --- base sem JS ---------------------------------------------------------------

def test_form_do_acervo_aterrissa_nos_resultados():
    t = _template("search.html")
    padrao = r'<form id="acervo-form" action="\{% url \'catalog:search\' %\}#acervo-resultados" method="get">'
    assert re.search(padrao, t)


def test_regioes_identificadas():
    t = _template("search.html")
    assert 'id="acervo-sidebar"' in t
    assert 'id="acervo-resultados"' in t
    assert 'id="acervo-paginacao"' in t
    # O status aria-live fica FORA da região trocada: uma live region recém-inserida
    # não é anunciada; ela precisa existir antes de o texto mudar.
    assert t.index('id="acervo-status"') < t.index('id="acervo-resultados"')


def test_links_get_carregam_a_ancora():
    t = _template("search.html")
    # paginação: todo href de página termina na âncora
    hrefs = re.findall(r'href="\?\{% querystring_replace [^"]+%\}([^"]*)"', t)
    assert hrefs and all(h == "#acervo-resultados" for h in hrefs), hrefs
    # "Limpar tudo" do estado vazio
    assert "{% endif %}#acervo-resultados\">Limpar tudo</a>" in t
    chips = _template("_partials/_applied_filters.html")
    assert 'href="{{ chip.remove_url }}#acervo-resultados"' in chips
    assert re.search(r'class="clear-btn" href="[^"]*#acervo-resultados"', chips)


def test_css_ancora_e_barra_lateral_fixa():
    assert "#acervo-resultados { scroll-margin-top:" in CSS
    bloco = CSS[CSS.index("#acervo-sidebar { position: sticky"):]
    assert "top:" in bloco[:200] and "max-height: calc(100vh" in bloco[:200] and "overflow-y: auto" in bloco[:200]
    # só em telas largas — o drawer mobile (position: fixed sob html.js) fica intacto
    idx = CSS.index("#acervo-sidebar { position: sticky")
    assert "@media (min-width: 1024px)" in CSS[idx - 120: idx]
    assert "html.js #acervo-sidebar {\n    position: fixed" in CSS
    # grade do Eduardo intacta
    assert ".acervo-layout { grid-template-columns: 300px minmax(0, 1fr); }" in CSS


# --- melhoria progressiva (JS) -----------------------------------------------------

def test_js_busca_e_troca_as_regioes():
    for trecho in ("fetch(", "DOMParser", "history.pushState", "popstate", "aria-busy",
                   "acervo-sidebar", "acervo-resultados", "acervo-paginacao", "X-Requested-With"):
        assert trecho in JS, trecho


def test_js_mantem_o_fallback_e_a_cascata():
    assert "form.submit()" in JS                       # falha do fetch → envio clássico (com âncora)
    assert "DIMENSOES" in JS
    assert '["colecao_v6", "typeinform_id"]' in JS
    assert '["category_id", "subcategoria_id", "microcategoria_id"]' in JS
    assert "SINGLE_SELECT" in JS


def test_js_preserva_rolagem_foco_details_e_drawer():
    assert "preventScroll" in JS
    assert "scrollTo(" in JS or "scrollY" in JS
    assert "details" in JS and "open" in JS
    assert "is-open" in JS and "aria-expanded" in JS and "acervo-drawer-open" in JS
    assert "prefers-reduced-motion" in JS
    assert "Resultados atualizados" in JS              # anúncio no aria-live
    assert "document.title" in JS


def test_js_sem_caminho_chumbado_nem_handler_inline():
    assert "/busca/" not in JS
    assert "/static/" not in JS
    assert "onclick" not in JS
    assert "eval(" not in JS
    assert "form.action" in JS and "location" in JS
    t = _template("search.html")
    assert "onclick" not in t and "onchange" not in t
