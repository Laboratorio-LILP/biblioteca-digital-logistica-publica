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
import re
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


def test_consultas_normais_nao_selecionam_a_coluna_gerada():
    # Ensaio de 30/09/2026 (§4.2, banco v11 restaurado, sem a coluna): a home dava
    # 500 porque todo SELECT de Document trazia `busca`. O gerente padrão adia a
    # coluna: só a busca a referencia (WHERE/ts_rank), e só quando ela existe.
    sql = str(Document.objects.filter(status="a").order_by("-pk")[:2].query)
    assert '"busca"' not in sql
    assert '"title"' in sql
    assert "busca" in Document.objects.all().query.deferred_loading[0]


def _triplas(sql):
    """(configuração, campo, peso) de cada setweight(to_tsvector(...)) num SQL, em qualquer grafia."""
    # str(query) substitui os parâmetros sem aspas (portuguese::regconfig, COALESCE(x, ), A);
    # o SQL da coluna os traz com aspas — as duas grafias caem na mesma forma
    sql = sql.replace("::regconfig", "").replace('"nr_document".', "").replace('"', "").replace("'", "").lower()
    return set(re.findall(r"setweight\(to_tsvector\((\w+), coalesce\((\w+), \)\), ([a-d])\)", sql))


def test_coluna_gerada_e_vetor_do_django_tem_as_mesmas_triplas_config_campo_peso():
    # contraprova de 30/09: o teste anterior contava setweight na própria string gerada (tautológico).
    # Aqui o vetor do Django é COMPILADO em SQL (sem executar) e comparado com o SQL da coluna.
    compilado = str(Document.objects.annotate(v=fts.expressao_vetor()).values("v").query)
    assert _triplas(compilado) == _triplas(fts.sql_coluna_gerada())
    assert len(_triplas(compilado)) == 2 * len(fts.FTS_CAMPOS)


def test_sql_da_busca_usa_a_coluna_quando_existe_e_o_vetor_calculado_quando_nao(monkeypatch):
    monkeypatch.setattr(search, "_busca_materializada_disponivel", lambda: True)
    com_coluna = str(search.search_documents("pregão eletrônico").query)
    assert '"nr_document"."busca" @@' in com_coluna and "setweight(" not in com_coluna
    assert "&&" in com_coluna and "||" in com_coluna          # E entre palavras, OU dentro de cada palavra
    assert 'ts_rank("nr_document"."busca"' in com_coluna                    # rank sobre a coluna, só nos que casaram
    monkeypatch.setattr(search, "_busca_materializada_disponivel", lambda: False)
    monkeypatch.setattr(search, "_unaccent_disponivel", lambda: True)
    calculado = str(search.search_documents("pregão eletrônico").query)
    assert "setweight(to_tsvector(portuguese_unaccent" in calculado.replace("'", "").replace("::regconfig", "")
    assert '"nr_document"."busca"' not in calculado
