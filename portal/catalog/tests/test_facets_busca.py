"""Facetas sensíveis à busca textual: contratos puros (sem banco).

As contagens da barra lateral devem refletir a busca textual (q) e os filtros
das outras dimensões; dentro da própria dimensão a faceta se exclui (padrão
de busca facetada: OR dentro da faceta, AND entre facetas). O comportamento
com banco (Postgres FTS) é verificado fim-a-fim na stack local — o CI não tem
Postgres, então aqui ficam só os invariantes estruturais.
"""

import inspect
from pathlib import Path

from catalog import facets, search, views

ACERVO_JS = Path(__file__).resolve().parents[2] / "static" / "js" / "acervo-filters.js"


def test_compute_facets_aceita_query():
    params = inspect.signature(facets.compute_facets).parameters
    assert "query" in params
    assert params["query"].default is None


def test_view_search_passa_query_para_facetas():
    src = inspect.getsource(views.search)
    assert "compute_facets(filters, query=" in src


def test_dimensao_colecao_exclui_slug_e_tipo():
    # Coleção e Tipo são a MESMA dimensão (coleção deriva do tipo): a faceta
    # precisa excluir ambos, senão selecionar uma coleção zera (e trava) as outras.
    assert set(facets.DIM_COLECAO) == {"colecao_v6", "typeinform_id"}


def test_dimensao_hierarquia_exclui_tres_niveis():
    assert set(facets.DIM_HIERARQUIA) == {
        "category_id",
        "subcategoria_id",
        "microcategoria_id",
    }


def test_sans_remove_dimensao_e_preserva_o_resto():
    f = {"assunto_id": ["1"], "colecao_v6": "instrucao", "typeinform_id": ["2"]}
    assert facets._sans(f, facets.DIM_COLECAO) == {"assunto_id": ["1"]}
    assert facets._sans(None, facets.DIM_COLECAO) == {}


def test_search_documents_e_facetas_compartilham_o_criterio_fulltext():
    # O critério "casa a busca" deve ser ÚNICO (apply_fulltext): usado pela
    # lista de resultados e pela base das facetas — senão barra e lista divergem.
    # co_names (não texto-fonte): menção em docstring/import não satisfaz.
    assert "apply_fulltext" in search.search_documents.__code__.co_names
    assert "apply_fulltext" in facets._base_qs.__code__.co_names


def test_js_reconcilia_dimensoes_no_clique():
    # A contagem exclui a dimensão inteira (DIM_COLECAO/DIM_HIERARQUIA), então
    # marcar um nó precisa LIMPAR os outros params da mesma dimensão no form —
    # senão o servidor aplica AND (ex.: colecao_v6=A & typeinform_id=T∉A) e a
    # lista devolve 0 contra o número prometido na barra.
    src = ACERVO_JS.read_text(encoding="utf-8")
    assert "DIMENSOES" in src
    assert '["colecao_v6", "typeinform_id"]' in src
    assert '["category_id", "subcategoria_id", "microcategoria_id"]' in src
