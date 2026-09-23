"""Taxonomia v12 (set/2026): vocabulário de tipos, 16 assuntos, subcategorias
sem prefixo e script de migração para bancos existentes — contratos sem banco.

Fonte: e-mail "ALTERAÇÕES BIBLIOTECA" (Lina, 11/09/2026) e reunião de 10/09:
  - Jurisprudência: saem Enunciados e Documentos Normativos; entram Acórdãos e
    Deliberações.
  - Doutrina e Conteúdo Técnico: entra Enunciados (Pareceres entrou em 11/09 e
    saiu em 23/09/2026 — v12.1).
  - Instrução e Capacitação: sai Vídeos.
  - Assuntos: +"Gestão Estratégica e Desempenho das Contratações" e
    +"Logística Pública Internacional" (16 no total).
  - Subcategorias de Planejamento sem o prefixo "FASE PREPARATÓRIA - ".
Normas/leis/decretos saem do acervo pela planilha, não por código.
"""

import re
from pathlib import Path

from catalog import taxonomy_v6
from catalog.taxonomy_v6 import (
    COLECOES_BY_NOME,
    TIPOS_LEGADOS,
    colecao_v6_for_tipo,
    tipo_canonico,
    tipos_de_colecao,
)
from catalog.templatetags.catalog_tags import SUBCAT_DISPLAY, rotulo_sub

REPO = Path(__file__).resolve().parents[3]
INIT = REPO / "docker" / "postgres" / "init"
MIGRACAO = REPO / "docker" / "postgres" / "migrations" / "2026-09-v12-taxonomia-e-busca.sql"


def _read(p):
    return p.read_text(encoding="utf-8")


# --- vocabulário de tipos ---------------------------------------------------

def test_vocabulario_v12_por_colecao():
    assert tipos_de_colecao("Jurisprudência") == ["Súmulas", "Boletins", "Acórdãos", "Deliberações"]
    assert tipos_de_colecao("Trabalhos Acadêmicos") == [
        "Teses", "Dissertações", "Monografias", "TCCs", "Memoriais Docentes",
    ]
    assert tipos_de_colecao("Doutrina e Conteúdo Técnico") == [
        "Livros digitais", "Artigos", "Notas Técnicas", "Relatórios",
        "Textos de Discussão", "Resumos", "Resumos expandidos", "Enunciados",
    ]
    assert tipos_de_colecao("Instrução e Capacitação") == [
        "Manuais", "Guias", "Tutoriais", "Apostilas", "Aulas", "Cursos", "Slides",
    ]


def test_tipos_novos_resolvem_colecao():
    assert colecao_v6_for_tipo("Acórdãos")["nome"] == "Jurisprudência"
    assert colecao_v6_for_tipo("Deliberações")["nome"] == "Jurisprudência"
    assert colecao_v6_for_tipo("Enunciados")["nome"] == "Doutrina e Conteúdo Técnico"
    # v12.1: Pareceres foi retirado — segue EXIBIDO em Doutrina (TIPOS_LEGADOS)
    # enquanto houver documento antigo, mas o importador o recusa.
    assert colecao_v6_for_tipo("Pareceres")["nome"] == "Doutrina e Conteúdo Técnico"
    assert tipo_canonico("Pareceres") is None


def test_grafias_legadas_dos_tipos_novos():
    # Singular/plural sem acento (grafias do banco legado e de planilhas antigas).
    assert tipo_canonico("Acórdão") == "Acórdãos"
    assert tipo_canonico("acordaos") == "Acórdãos"
    assert tipo_canonico("Deliberação") == "Deliberações"
    assert tipo_canonico("deliberacoes") == "Deliberações"
    assert tipo_canonico("Parecer") is None  # retirado na v12.1 (23/09/2026)
    assert tipo_canonico("pareceres") is None
    assert tipo_canonico("Enunciado") == "Enunciados"
    assert tipo_canonico("enunciados") == "Enunciados"


def test_documentos_normativos_e_videos_fora_do_vocabulario_canonico():
    todos = {t for tipos in taxonomy_v6._TIPOS_POR_COLECAO.values() for t in tipos}
    assert "Documentos Normativos" not in todos
    assert "Vídeos" not in todos
    assert tipo_canonico("Documentos Normativos") is None
    assert tipo_canonico("Vídeos") is None
    assert tipo_canonico("xpto inexistente") is None


def test_tipos_legados_exibem_na_colecao_antiga():
    # Janela entre a subida do código e a recarga v12: documentos antigos ainda
    # com esses tipos NÃO podem cair no fallback "Doutrina".
    assert TIPOS_LEGADOS == {
        "Documentos Normativos": "Jurisprudência",
        "Vídeos": "Instrução e Capacitação",
        "Pareceres": "Doutrina e Conteúdo Técnico",  # v12.1 (23/09/2026)
    }
    assert colecao_v6_for_tipo("Documentos Normativos")["nome"] == "Jurisprudência"
    assert colecao_v6_for_tipo("Documento normativo")["nome"] == "Jurisprudência"
    assert colecao_v6_for_tipo("Vídeos")["nome"] == "Instrução e Capacitação"
    assert colecao_v6_for_tipo("Video")["nome"] == "Instrução e Capacitação"
    assert colecao_v6_for_tipo("Pareceres")["nome"] == "Doutrina e Conteúdo Técnico"
    assert colecao_v6_for_tipo("parecer")["nome"] == "Doutrina e Conteúdo Técnico"
    # ...e o fallback continua valendo para tipo realmente desconhecido.
    assert colecao_v6_for_tipo("xpto inexistente")["nome"] == "Doutrina e Conteúdo Técnico"


def test_tipos_legados_so_valem_para_exibicao():
    # colecao_v6_for_tipo consulta o mapa legado (derivado de TIPOS_LEGADOS);
    # tipo_canonico (critério do importador) não.
    assert "_TIPOS_LEGADOS_NORM" in taxonomy_v6.colecao_v6_for_tipo.__code__.co_names
    assert "_TIPOS_LEGADOS_NORM" not in taxonomy_v6.tipo_canonico.__code__.co_names
    assert "TIPOS_LEGADOS" not in taxonomy_v6.tipo_canonico.__code__.co_names


def test_descricao_de_jurisprudencia_sem_normativo():
    desc = COLECOES_BY_NOME["Jurisprudência"]["descricao"].lower()
    assert "normativ" not in desc
    assert "acórdãos" in desc and "deliberações" in desc


# --- seeds -------------------------------------------------------------------

def test_seed_collections_v12():
    sql = _read(INIT / "06-collections.sql")
    assert "('Acórdãos'" in sql and "('Deliberações'" in sql
    assert "('Pareceres'" not in sql  # v12.1
    assert "('Documentos Normativos'" not in sql
    assert "('Vídeos'" not in sql
    # Enunciados existe uma única vez — sob Doutrina, não sob Jurisprudência.
    juris = sql[sql.index("WHERE t.name = 'Jurisprudência'") - 600: sql.index("WHERE t.name = 'Jurisprudência'")]
    assert "('Enunciados'" not in juris
    assert sql.count("('Enunciados'") == 1
    assert "normativ" not in sql.lower().split("-- subcoleções")[0].split("insert into topic")[1]


def test_seed_type_information_v12():
    sql = _read(INIT / "08-type-information.sql")
    canon = sql[sql.index("Tipos de Informação canônicos"):]
    assert "('Acórdãos')" in canon and "('Deliberações')" in canon
    assert "('Pareceres')" not in canon  # v12.1
    assert "('Documentos Normativos')" not in canon
    assert "('Vídeos')" not in canon


def test_seed_assuntos_tem_16():
    sql = _read(INIT / "06-taxonomia.sql")
    bloco = sql[sql.index("INSERT INTO nr_assunto"):]
    bloco = bloco[: bloco.index(";")]
    linhas = re.findall(r"\('([^']+)', '([^']+)', (\d+)\)", bloco)
    assert len(linhas) == 16
    nomes = [n for n, _, _ in linhas]
    assert "Gestão Estratégica e Desempenho das Contratações" in nomes
    assert "Logística Pública Internacional" in nomes
    ordens = sorted(int(o) for _, _, o in linhas)
    assert ordens == list(range(1, 17))
    assert ("Gestão Estratégica e Desempenho das Contratações",
            "gestao-estrategica-e-desempenho-das-contratacoes", "15") in linhas
    assert ("Logística Pública Internacional", "logistica-publica-internacional", "16") in linhas


def test_seed_subcategorias_sem_prefixo():
    sql = _read(INIT / "07-categories.sql")
    assert "FASE PREPARATÓRIA - " not in sql
    for nome, slug in (("ETP", "etp"), ("TR", "tr"),
                       ("GESTÃO DE RISCOS", "gestao-de-riscos"), ("PESQUISA DE PREÇOS", "pesquisa-de-precos")):
        assert f"('{nome}', '{slug}', 'PLANEJAMENTO/FASE PREPARATÓRIA'" in sql
    # Microcategorias de riscos continuam penduradas na subcategoria renomeada.
    assert "('MAPA DE RISCOS', 'mapa-de-riscos', 'GESTÃO DE RISCOS'" in sql
    assert "('MATRIZ DE ALOCAÇÃO DE RISCOS', 'matriz-de-alocacao-de-riscos', 'GESTÃO DE RISCOS'" in sql


def test_rotulo_sub_aceita_nomes_novos_e_antigos():
    assert rotulo_sub("ETP") == "Estudo Técnico Preliminar (ETP)"
    assert rotulo_sub("TR") == "Termo de Referência (TR)"
    assert rotulo_sub("GESTÃO DE RISCOS") == "Gestão de Riscos"
    assert rotulo_sub("PESQUISA DE PREÇOS") == "Pesquisa de Preços"
    # Um ciclo de transição: bancos ainda não migrados exibem igual.
    assert rotulo_sub("FASE PREPARATÓRIA - ETP") == "Estudo Técnico Preliminar (ETP)"
    assert SUBCAT_DISPLAY["FASE PREPARATÓRIA - TR"] == SUBCAT_DISPLAY["TR"]


def test_extensao_unaccent_no_init():
    sql = _read(INIT / "00-extensions.sql")
    assert "CREATE EXTENSION IF NOT EXISTS unaccent" in sql
    assert "portuguese_unaccent" in sql
    assert "pg_ts_config" in sql  # guarda de existência
    assert "unaccent, portuguese_stem" in sql


# --- script de migração para bancos existentes --------------------------------

def test_script_de_migracao_existe_com_duas_secoes():
    sql = _read(MIGRACAO)
    # Os marcadores de seção são as faixas "-- SEÇÃO N — ..." (o cabeçalho do
    # arquivo também cita as seções, por isso o índice é o das faixas).
    m1, m2 = "-- SEÇÃO 1 — aditiva", "-- SEÇÃO 2 — pós-recarga"
    assert m1 in sql and m2 in sql
    s1 = sql[sql.index(m1): sql.index(m2)]
    s2 = sql[sql.index(m2):]
    # Seção 1: aditiva — tipos/topics novos, 2 assuntos, renomes, busca.
    for nome in ("Acórdãos", "Deliberações", "Enunciados"):
        assert nome in s1
    assert "('Pareceres'" not in s1.split("-- 1.3")[1].split("-- 1.4")[0]  # v12.1
    assert "'Pareceres'" in s2  # v12.1: a seção 2 remove subcoleção e tipo
    assert "Gestão Estratégica e Desempenho das Contratações" in s1
    assert "Logística Pública Internacional" in s1
    assert "FASE PREPARATÓRIA - ETP" in s1 and "'ETP'" in s1
    assert "CREATE EXTENSION IF NOT EXISTS unaccent" in s1
    assert "portuguese_unaccent" in s1
    assert "topic_path" in s1
    # Seção 2: remoção guardada — só sem referência em nr_document (a guarda
    # conta as referências para dizer no aviso quantos documentos bloqueiam).
    assert "nr_document" in s2
    assert ("NOT EXISTS" in s2) or ("IF n_docs > 0" in s2)
    assert "DELETE FROM topic" in s2 and "DELETE FROM type_information" in s2
    assert "Documentos Normativos" in s2 and "Vídeos" in s2
    assert "RAISE NOTICE" in s2


def test_script_de_migracao_e_idempotente_por_construcao():
    sql = _read(MIGRACAO)
    inserts = re.findall(r"INSERT INTO\s+(\w+)", sql, flags=re.I)
    assert inserts, "esperava INSERTs guardados"
    # Todo INSERT precisa de guarda: ON CONFLICT ou WHERE NOT EXISTS.
    for m in re.finditer(r"INSERT INTO[\s\S]*?;", sql, flags=re.I):
        trecho = m.group(0)
        assert ("ON CONFLICT" in trecho) or ("NOT EXISTS" in trecho), trecho[:120]
    for m in re.finditer(r"UPDATE\s+\w+[\s\S]*?;", sql, flags=re.I):
        assert "WHERE" in m.group(0), m.group(0)[:120]
