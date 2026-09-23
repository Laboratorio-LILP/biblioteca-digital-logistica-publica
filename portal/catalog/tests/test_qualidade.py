"""Verificações de redundância e de qualidade para a curadoria (T5, set/2026).

Módulo puro catalog.qualidade: nunca altera dados; produz achados com código,
referência (linha/`code`) e título curto. Usado por validate_import (acervo
carregado) e por migrate_spreadsheet --dry-run (linhas da planilha, como
avisos). Casos de borda das heurísticas relatadas pela Lina em 14/09/2026.
"""

import inspect
from pathlib import Path

from catalog import qualidade
from catalog.management.commands import migrate_spreadsheet, validate_import
from catalog.qualidade import (
    analisar,
    autoria_institucional_suspeita,
    duplicatas,
    enderecos_compartilhados,
    normalizar_doi,
    normalizar_titulo,
    normalizar_url,
    registro,
    resumir,
    resumo_suspeito,
)

RESUMO_OK = ("Este estudo analisa a aplicação da Lei nº 14.133/2021 nas contratações públicas estaduais, "
             "com foco no planejamento, na seleção do fornecedor e na gestão contratual. Discute os riscos "
             "mais frequentes e propõe rotinas de controle interno para as áreas de compras, com exemplos "
             "práticos e indicadores de acompanhamento para gestores e fiscais de contratos.")


# --- normalização -------------------------------------------------------------------

def test_normalizar_titulo_ignora_acento_caixa_pontuacao_e_espacos():
    a = normalizar_titulo("Licitação:  Sustentável — guia prático!")
    assert a == normalizar_titulo("licitacao sustentavel guia pratico")
    assert normalizar_titulo("  ") == ""
    assert normalizar_titulo(None) == ""


def test_normalizar_doi():
    assert normalizar_doi("https://doi.org/10.1590/ABC.123") == "10.1590/abc.123"
    assert normalizar_doi("DOI: 10.1590/abc.123 ") == "10.1590/abc.123"
    assert normalizar_doi("") == ""


def test_normalizar_url_sem_fragmento_utm_barra_final_e_host_em_caixa_baixa():
    a = normalizar_url("https://WWW.Exemplo.gov.br/Estante/Item/?utm_source=x&utm_medium=y#pagina=3")
    b = normalizar_url("http://www.exemplo.gov.br/Estante/Item")
    assert a == b
    # parâmetros que não são utm_ continuam distinguindo endereços
    assert normalizar_url("https://x.org/doc?id=1") != normalizar_url("https://x.org/doc?id=2")
    assert normalizar_url(None) == ""


# --- duplicatas ------------------------------------------------------------------------

def _reg(ref, titulo, **kw):
    base = dict(doi="", url="", resumo=RESUMO_OK, colecao="Doutrina e Conteúdo Técnico", tipo="Artigos",
                assunto="Governança", categoria="CONTEÚDOS TRANSVERSAIS", subcategoria="", autor="Silva, Ana")
    base.update(kw)
    return registro(ref, titulo, **base)


def test_duplicata_por_titulo_normalizado():
    regs = [_reg("L4", "Governança nas compras públicas"), _reg("L9", "GOVERNANCA NAS COMPRAS PUBLICAS.")]
    achados = duplicatas(regs)
    assert [a.codigo for a in achados] == ["DUPLICATA_TITULO"]
    assert achados[0].refs == ["L4", "L9"]


def test_duplicata_por_doi():
    regs = [_reg("L1", "Título A", doi="10.1590/abc.123"), _reg("L2", "Título B", doi="https://doi.org/10.1590/ABC.123")]
    achados = duplicatas(regs)
    assert [a.codigo for a in achados] == ["DUPLICATA_DOI"]


def test_duplicata_caracterizada_de_forma_diferente_lista_os_campos():
    achados = duplicatas([
        _reg("L4", "Governança nas compras públicas", assunto="Governança", tipo="Artigos"),
        _reg("L9", "Governança nas compras públicas", assunto="Integridade", tipo="Relatórios"),
    ])
    codigos = [a.codigo for a in achados]
    assert "DUPLICATA_DIVERGENTE" in codigos
    div = next(a for a in achados if a.codigo == "DUPLICATA_DIVERGENTE")
    assert "Tipo" in div.detalhe and "Assunto" in div.detalhe
    assert "Coleção" not in div.detalhe


def test_sem_duplicata_quando_titulos_diferem():
    assert duplicatas([_reg("L1", "Título um"), _reg("L2", "Título dois")]) == []


# --- endereço compartilhado ---------------------------------------------------------------

def test_endereco_compartilhado_com_titulos_diferentes_nao_e_duplicata():
    regs = [_reg("L1", "Caderno ODS 1", url="https://fliphtml5.com/estante/abc#p=1"),
            _reg("L2", "Caderno ODS 2", url="https://fliphtml5.com/estante/abc/?utm_source=teams")]
    achados = enderecos_compartilhados(regs)
    assert [a.codigo for a in achados] == ["ENDERECO_COMPARTILHADO"]
    assert "confirmar endereço individual" in achados[0].detalhe
    assert duplicatas(regs) == []


def test_mesmo_endereco_e_mesmo_titulo_e_duplicata_nao_endereco_compartilhado():
    regs = [_reg("L1", "Mesmo título", url="https://x.org/a"), _reg("L2", "Mesmo título", url="https://x.org/a")]
    assert enderecos_compartilhados(regs) == []
    assert [a.codigo for a in duplicatas(regs)] == ["DUPLICATA_TITULO"]


# --- resumo suspeito ------------------------------------------------------------------------

def test_resumo_comeca_com_minuscula():
    assert "RESUMO_MINUSCULA" in resumo_suspeito(_reg("L1", "T", resumo="o presente trabalho " + RESUMO_OK))
    assert "RESUMO_MINUSCULA" not in resumo_suspeito(_reg("L1", "T", resumo=RESUMO_OK))


def test_resumo_termina_com_reticencias_ascii_ou_unicode():
    assert "RESUMO_RETICENCIAS" in resumo_suspeito(_reg("L1", "T", resumo=RESUMO_OK + "..."))
    assert "RESUMO_RETICENCIAS" in resumo_suspeito(_reg("L1", "T", resumo=RESUMO_OK + "…"))
    assert "RESUMO_RETICENCIAS" not in resumo_suspeito(_reg("L1", "T", resumo=RESUMO_OK))


def test_resumo_com_marcador_de_citacao_mas_nao_ano():
    assert "RESUMO_CITACAO" in resumo_suspeito(_reg("L1", "T", resumo=RESUMO_OK + " Como aponta a literatura [12]."))
    assert "RESUMO_CITACAO" in resumo_suspeito(_reg("L1", "T", resumo=RESUMO_OK + " Ver [2, 5]."))
    assert "RESUMO_CITACAO" not in resumo_suspeito(_reg("L1", "T", resumo=RESUMO_OK + " Dados de [2024]."))


def test_resumo_curto_e_igual_ao_titulo():
    curto = "Resumo curto demais para a planilha-modelo."
    assert "RESUMO_CURTO" in resumo_suspeito(_reg("L1", "T", resumo=curto))
    assert "RESUMO_CURTO" not in resumo_suspeito(_reg("L1", "T", resumo=RESUMO_OK))
    titulo = "Guia de gestão de riscos nas contratações"
    assert "RESUMO_IGUAL_TITULO" in resumo_suspeito(_reg("L1", titulo, resumo=titulo + " " + RESUMO_OK))
    assert "RESUMO_VAZIO" in resumo_suspeito(_reg("L1", "T", resumo=""))


def test_resumo_de_pagina_scribd():
    assert "RESUMO_SCRIBD" in resumo_suspeito(_reg("L1", "T", url="https://pt.scribd.com/document/1/x"))
    assert "RESUMO_SCRIBD" not in resumo_suspeito(_reg("L1", "T", url="https://x.org/a"))


def test_um_resumo_acumula_varios_codigos():
    codigos = resumo_suspeito(_reg("L1", "T", resumo="trecho copiado [3]...", url="https://scribd.com/doc/1"))
    assert {"RESUMO_MINUSCULA", "RESUMO_RETICENCIAS", "RESUMO_CITACAO", "RESUMO_CURTO", "RESUMO_SCRIBD"} <= set(codigos)


def test_placeholders_de_doi_e_url_nao_viram_chave_de_agrupamento():
    # Revisão 14/09: "Não possui", "-", "n/a" iguais em várias linhas geravam
    # DUPLICATA_DOI/ENDERECO_COMPARTILHADO falsos.
    for placeholder in ("Não possui", "-", "n/a"):
        assert normalizar_doi(placeholder) == "", placeholder
    for placeholder in ("Não possui", "-", "[Acesso restrito]", "n/a"):
        assert normalizar_url(placeholder) == "", placeholder
    regs = [_reg("L1", "Título um", doi="Não possui", url="n/a"),
            _reg("L2", "Título dois", doi="Não possui", url="n/a")]
    assert duplicatas(regs) == [] and enderecos_compartilhados(regs) == []


def test_reticencias_entre_parenteses_colchetes_ou_aspas():
    for fim in (" (...)", " [...]", '..."', "…”"):
        assert "RESUMO_RETICENCIAS" in resumo_suspeito(_reg("L1", "T", resumo=RESUMO_OK + fim)), fim


def test_chave_de_serie_nao_trata_palavras_comuns_como_romano():
    from catalog.qualidade import _chave_serie

    assert _chave_serie("Manual de Direito Civil 2") == "manual de direito civil"
    assert _chave_serie("Guia Mil Usos II") == "guia mil usos"
    assert _chave_serie("Caderno ODS 3: Saúde") == "caderno ods"


# --- autoria institucional suspeita ------------------------------------------------------------

def test_autoria_serie_com_mesmo_autor_pessoa_e_apontada():
    regs = [_reg(f"L{i}", f"Caderno ODS {i}: tema {i}", autor="Fenili, Renato") for i in (1, 2, 3)]
    achados = autoria_institucional_suspeita(regs)
    assert len(achados) == 1 and achados[0].codigo == "AUTORIA_SERIE"
    assert achados[0].refs == ["L1", "L2", "L3"]


def test_autoria_serie_nao_apontada_sem_serie_ou_com_autores_diferentes():
    assert autoria_institucional_suspeita([_reg("L1", "Caderno ODS 1", autor="Fenili, Renato")]) == []
    regs = [_reg("L1", "Manual de compras 1", autor="Silva, Ana"),
            _reg("L2", "Manual de compras 2", autor="Souza, Bia")]
    assert autoria_institucional_suspeita(regs) == []
    regs = [_reg("L1", "Artigo sobre ODS 1", autor="Silva, Ana"),
            _reg("L2", "Artigo sobre ODS 2", autor="Silva, Ana")]
    assert autoria_institucional_suspeita(regs) == []          # não é Caderno/Manual/Guia


# --- agregação -------------------------------------------------------------------------------------

def test_analisar_e_resumir():
    regs = [_reg("L1", "Mesmo título", resumo="trecho…"), _reg("L2", "Mesmo título")]
    achados = analisar(regs)
    contagem = resumir(achados)
    assert contagem["DUPLICATA_TITULO"] == 1
    assert contagem["RESUMO_RETICENCIAS"] == 1 and contagem["RESUMO_MINUSCULA"] == 1 and contagem["RESUMO_CURTO"] == 1
    for a in achados:
        assert a.codigo and a.refs and a.titulo


def test_modulo_e_puro_e_documentado():
    src = inspect.getsource(qualidade)
    assert "django" not in src.lower().split('"""', 2)[2] or "from django" not in src   # sem ORM
    assert "import re" in src
    for codigo in ("DUPLICATA_TITULO", "DUPLICATA_DOI", "DUPLICATA_DIVERGENTE", "ENDERECO_COMPARTILHADO",
                   "RESUMO_MINUSCULA", "RESUMO_RETICENCIAS", "RESUMO_CITACAO", "RESUMO_CURTO",
                   "RESUMO_IGUAL_TITULO", "RESUMO_SCRIBD", "RESUMO_VAZIO", "AUTORIA_SERIE"):
        assert codigo in qualidade.__doc__, codigo


# --- integração (contrato) -----------------------------------------------------------------------

def test_validate_import_tem_a_secao_de_qualidade():
    src = inspect.getsource(validate_import)
    assert "Possíveis redundâncias e problemas de qualidade" in src
    assert "qualidade" in src and "analisar(" in src


def test_dry_run_do_importador_avisa_sem_recusar():
    src = inspect.getsource(migrate_spreadsheet)
    assert "Possíveis redundâncias e problemas de qualidade" in src
    assert "analisar(" in src
    assert "AVISO" in src.upper()


def test_runbook_documenta_a_semantica():
    md = (Path(__file__).resolve().parents[3] / "tools" / "db-refresh.md").read_text(encoding="utf-8")
    for codigo in ("DUPLICATA_DIVERGENTE", "ENDERECO_COMPARTILHADO", "RESUMO_SCRIBD", "AUTORIA_SERIE"):
        assert codigo in md, codigo
