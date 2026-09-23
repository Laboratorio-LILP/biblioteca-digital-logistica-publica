"""Terminologia do eixo Categoria na interface (17/09/2026) — sem banco.

Bernardo: o rótulo "Etapa (categoria processual)" confundia. Regra única para
toda a plataforma: o eixo se chama **Categoria**, a explicação é **(etapa da
contratação)** e o jargão "categoria processual" não aparece para o público.
"Etapa" nunca nomeia o eixo sozinho — só explica o que uma categoria é.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TEMPLATES = REPO / "portal" / "templates"


def _sem_comentarios(html):
    """Texto do template sem comentários {# #} e {% comment %} (só o que o público vê)."""
    html = re.sub(r"\{#.*?#\}", "", html)
    return re.sub(r"\{% comment %\}.*?\{% endcomment %\}", "", html, flags=re.S)


def _templates():
    return {p.relative_to(TEMPLATES).as_posix(): _sem_comentarios(p.read_text(encoding="utf-8"))
            for p in TEMPLATES.rglob("*.html")}


def test_jargao_categoria_processual_saiu_da_interface():
    for nome, t in _templates().items():
        assert "categoria processual" not in t.lower(), nome
        assert "categorias processuais" not in t.lower(), nome
        assert "macroetapa" not in t.lower(), nome


def test_etapa_nao_nomeia_o_eixo_sozinha():
    for nome, t in _templates().items():
        assert "Etapa (" not in t, nome                       # o rótulo antigo do documento
        assert "Etapa:" not in t, nome                        # o prefixo antigo do badge/cartão
        assert 'data-sec="Etapas' not in t, nome              # a seção da home


def test_o_par_categoria_e_etapa_da_contratacao_nos_pontos_de_contato():
    t = _templates()
    assert 'Categoria (etapa da contratação)' in t["document_detail.html"]          # ficha do documento
    assert 'Categorias (etapas da contratação)' in t["collection_list.html"]        # glossário
    assert "Veja o que entra em cada categoria" in t["collection_list.html"]
    assert "<h3>Categorias</h3>" in t["search.html"]                                 # faceta do Acervo
    assert "A etapa da contratação em que o material se aplica." in t["search.html"]
    assert 'data-sec="Categorias da contratação"' in t["home.html"]
    assert '<span class="eyebrow">Categorias</span>' in t["home.html"]
    assert "Categorias da contratação" in t["home.html"] and "Categorias da contratação" in t["legal/mapa_site.html"]
    assert 'doc-card__eixo-rotulo">Categoria:' in t["_partials/_doc_card.html"]     # rodapé do cartão
