"""Busca com vetor materializado e índice GIN (achado F2-02 da auditoria de
23/09/2026: a home fazia 5 buscas por Seq Scan e levava ~2,8 s).

Desenho: a coluna `nr_document.busca` é GERADA pelo Postgres com a MESMA soma
de vetores que o Django montava a cada consulta (os campos e pesos de
fts.FTS_CAMPOS nas configurações `portuguese` e `portuguese_unaccent`); o índice
GIN fica sobre a coluna; o Django lê a coluna (GeneratedField, nunca escreve).
O SQL da coluna nasce de UMA função (fts.sql_coluna_gerada) e tem de aparecer
igual no seed de volume novo e no script de migração que a TI roda. Sem a
coluna (banco ainda sem a migração), a busca volta ao vetor calculado na
consulta, com aviso no log — nunca 500.

Sem banco: contratos estruturais. Plano de execução e tempos são conferidos
na stack local (EXPLAIN ANALYZE), não aqui.
"""

import inspect
from pathlib import Path

from django.contrib.postgres.search import SearchVectorField
from django.db import models

from catalog import fts, search
from catalog.models import Document

REPO = Path(__file__).resolve().parents[3]
SEED = REPO / "docker" / "postgres" / "init" / "06-taxonomia.sql"
MIGRACAO = REPO / "docker" / "postgres" / "migrations" / "2026-09-v12-taxonomia-e-busca.sql"


def test_campos_e_pesos_sao_os_mesmos_da_busca_antiga():
    assert fts.FTS_CAMPOS == search._FTS_CAMPOS
    assert fts.CONFIGS == ("portuguese", "portuguese_unaccent")


def test_sql_da_coluna_gerada_espelha_o_vetor_do_django():
    sql = fts.sql_coluna_gerada()
    # um setweight(to_tsvector(config, coalesce(campo, ''))) por campo e por configuração, somados com ||
    assert sql.count("setweight(") == 2 * len(fts.FTS_CAMPOS)
    assert sql.count("||") == 2 * len(fts.FTS_CAMPOS) - 1
    for campo, peso in fts.FTS_CAMPOS:
        for config in fts.CONFIGS:
            assert f"setweight(to_tsvector('{config}', coalesce({campo}, '')), '{peso}')" in sql, (campo, config)
    assert sql.startswith("GENERATED ALWAYS AS (") and sql.rstrip().endswith(") STORED")


def test_seed_e_migracao_criam_a_coluna_e_o_indice_com_o_mesmo_sql():
    coluna = fts.sql_coluna_gerada()
    seed = SEED.read_text(encoding="utf-8")
    mig = MIGRACAO.read_text(encoding="utf-8")
    assert coluna in seed and coluna in mig                          # o mesmo texto nos dois arquivos
    for sql in (seed, mig):
        assert "ADD COLUMN IF NOT EXISTS busca tsvector" in sql          # idempotente
        assert "CREATE INDEX IF NOT EXISTS idx_nr_document_busca ON nr_document USING gin (busca)" in sql
        assert "DROP INDEX IF EXISTS idx_nr_document_fts" in sql          # o índice antigo nunca casava a consulta
    # na migração fica na seção 1 (aditiva, antes ou depois da recarga), depois da configuração unaccent (1.1)
    secao1 = mig.rsplit("SEÇÃO 2", 1)[0]          # tudo antes da faixa da seção 2 (o cabeçalho também a cita)
    assert "ADD COLUMN IF NOT EXISTS busca" in secao1
    assert secao1.index("portuguese_unaccent (COPY = portuguese)") < secao1.index("ADD COLUMN IF NOT EXISTS busca")


def test_modelo_le_a_coluna_e_nunca_a_escreve():
    campo = Document._meta.get_field("busca")
    assert isinstance(campo, models.GeneratedField) and campo.db_persist is True
    assert isinstance(campo.output_field, SearchVectorField)
    assert campo.concrete and not campo.editable


def test_busca_usa_a_coluna_e_degrada_sem_ela():
    src = inspect.getsource(search.apply_fulltext)
    assert "_busca_materializada_disponivel()" in src
    assert 'F("busca")' in src and "filter(busca=" in src             # vetor @@ consulta pelo índice
    assert '_vetor("portuguese") + _vetor("portuguese_unaccent")' in src   # caminho antigo, sem a coluna
    src_mod = inspect.getsource(search)
    assert "information_schema.columns" in src_mod and "logger.warning" in src_mod
