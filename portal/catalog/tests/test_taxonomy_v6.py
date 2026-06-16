"""Testes das funções puras de taxonomia v6 (sem banco)."""

from catalog.taxonomy_v6 import (
    COLECOES_V6,
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
