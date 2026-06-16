"""Testes das funções puras de taxonomia v6 (sem banco)."""

from catalog.taxonomy_v6 import (
    COLECOES_V6,
    TEMAS_DESTAQUE,
    colecao_v6_for_tipo,
    tipos_de_colecao,
)


def test_quatro_colecoes_canonicas():
    nomes = {c["nome"] for c in COLECOES_V6}
    assert nomes == {
        "Jurisprudência",
        "Trabalhos Acadêmicos",
        "Doutrina e Conteúdo Técnico",
        "Instrução e Capacitação",
    }


def test_tipo_v8_resolve_colecao():
    assert colecao_v6_for_tipo("Slides")["nome"] == "Instrução e Capacitação"
    assert colecao_v6_for_tipo("Teses")["nome"] == "Trabalhos Acadêmicos"
    assert colecao_v6_for_tipo("Súmulas")["nome"] == "Jurisprudência"
    assert colecao_v6_for_tipo("Artigos")["nome"] == "Doutrina e Conteúdo Técnico"


def test_tipo_legado_v5_normaliza_para_v6():
    assert colecao_v6_for_tipo("Material pedagógico")["nome"] == "Instrução e Capacitação"
    assert colecao_v6_for_tipo("Artigo de periódico")["nome"] == "Doutrina e Conteúdo Técnico"


def test_tipo_desconhecido_cai_no_fallback():
    assert colecao_v6_for_tipo("xpto inexistente")["nome"] == "Doutrina e Conteúdo Técnico"


def test_tipos_de_colecao_por_slug_e_nome():
    assert "Slides" in tipos_de_colecao("instrucao")
    assert "Teses" in tipos_de_colecao("Trabalhos Acadêmicos")
    assert tipos_de_colecao("inexistente") == []


_TEMA_KEYS = {"slug", "label", "query", "icon", "color", "card_desc", "alta_intro"}


def test_temas_destaque_ordem_e_novos():
    slugs = [t["slug"] for t in TEMAS_DESTAQUE]
    assert slugs == [
        "lei-14133",
        "sustentabilidade",
        "compras-diretas",
        "pregao",
        "registro-precos",
    ]


def test_temas_destaque_entradas_completas():
    for t in TEMAS_DESTAQUE:
        assert _TEMA_KEYS <= set(t), f"faltam chaves em {t.get('slug')}"
        assert t["icon"].startswith("fi-")
        assert t["color"].startswith("c-")
        assert t["query"].strip()
