"""Busca sem acento (T4, set/2026): contratos sem banco.

`q=pregao` devolvia 0 e `q=pregão` 44 (medido no portal em 04/09/2026). A
correção SOMA duas configurações de busca em vez de trocar uma pela outra:
`portuguese` (radicalizador oficial) + `portuguese_unaccent` (a mesma, com o
filtro unaccent nas palavras). Aplicar unaccent ANTES do stemmer muda o
radical ("licitações" → "licitaco" ≠ "licitação" → "licitaca"), então só a
soma preserva plural/flexão. Verificação com banco: termo × contagem antes/
depois na stack local (docs/evidencias/2026-09-validacao/busca-sem-acento.md).
"""

import inspect
from pathlib import Path

from catalog import facets, search

REPO = Path(__file__).resolve().parents[3]
EXTENSIONS = REPO / "docker" / "postgres" / "init" / "00-extensions.sql"
MIGRACAO = REPO / "docker" / "postgres" / "migrations" / "2026-09-v12-taxonomia-e-busca.sql"


def test_apply_fulltext_soma_as_duas_configuracoes():
    src = inspect.getsource(search)
    assert 'config="portuguese"' in src            # não perde o stemmer oficial
    assert 'config="portuguese_unaccent"' in src   # e ganha a busca sem acento
    # Vetor: os mesmos campos (mesmos pesos) nas duas configurações.
    assert '_vetor("portuguese") + _vetor("portuguese_unaccent")' in src
    assert "reacentuar(" in inspect.getsource(search._consulta)


def test_consulta_e_por_token_e_entre_palavras():
    # Revisão adversarial (14/09): OR entre consultas inteiras virava raiz OR e o
    # ts_rank passava a aceitar documento com só uma das palavras ("pregão
    # eletrônico" 29 → 81). A consulta é montada por token — OR das configurações
    # DENTRO de cada palavra, E entre palavras — e o casamento booleano é explícito (@@).
    src = inspect.getsource(search._consulta)
    # 30/09: as palavras vêm de _tokens (split limitado a MAX_TOKENS_BUSCA)
    assert "_tokens(query)" in src and ".split()" in inspect.getsource(search._tokens)
    assert "& " in src or "&=" in src or " & " in src
    src_apply = inspect.getsource(search.apply_fulltext)
    assert "filter(busca=" in src_apply           # vetor @@ consulta — semântica booleana garantida


def test_degrada_sem_a_configuracao_unaccent_no_banco():
    # Banco ainda sem a seção 1 do script (homologação antes do SQL): a busca
    # não pode responder 500 — usa só `portuguese` (+ reacentuar) e avisa no log.
    src = inspect.getsource(search)
    assert "pg_ts_config" in src and "portuguese_unaccent" in src
    assert "_unaccent_disponivel" in inspect.getsource(search.apply_fulltext)
    assert "logger.warning" in src or "log.warning" in src


def test_vetor_usa_os_mesmos_campos_e_pesos_nas_duas_configuracoes():
    campos = [c for c, _ in search._FTS_CAMPOS]
    assert campos == ["title", "keywords", "author", "autor_principal", "abstract",
                      "uso_futuro", "metodo", "resultado", "complexidade"]
    pesos = dict(search._FTS_CAMPOS)
    assert pesos["title"] == "A" and pesos["abstract"] == "C" and pesos["complexidade"] == "D"


def test_reacentuar_sufixos_nasais():
    assert search.reacentuar("licitacao") == "licitação"
    assert search.reacentuar("licitacoes") == "licitações"
    assert search.reacentuar("sancoes administrativas") == "sanções administrativas"
    assert search.reacentuar("contratacao 14.133") == "contratação 14.133"
    assert search.reacentuar("pregao") == "pregão"
    assert search.reacentuar("orgaos") == "órgãos".replace("ó", "o")   # só o sufixo é re-acentuado
    assert search.reacentuar("ELEICOES") == "eleições"


def test_reacentuar_nao_mexe_no_que_ja_tem_acento_nem_no_resto():
    assert search.reacentuar("licitação") == ""          # já acentuado: nada muda
    assert search.reacentuar("pregão eletrônico") == ""
    assert search.reacentuar("governanca") == ""         # ç no meio: o unaccent já cobre
    assert search.reacentuar("14.133") == ""
    assert search.reacentuar("") == ""
    assert search.reacentuar("ao") == ""                 # token curto demais para ser sufixo
    # token ASCII colado a letra acentuada não é re-acentuado (é pedaço de outra palavra)
    assert search.reacentuar("licitaçao") == ""


def test_rank_minimo_preservado():
    src = inspect.getsource(search.apply_fulltext)
    assert "rank__gte=0.01" in src


def test_facetas_continuam_usando_o_mesmo_criterio():
    # A base das facetas e a lista compartilham apply_fulltext — sem duplicar lógica.
    assert "apply_fulltext" in facets._base_qs.__code__.co_names
    assert "apply_fulltext" in search.search_documents.__code__.co_names
    assert "portuguese_unaccent" not in inspect.getsource(facets)


def test_extensao_e_configuracao_criadas_com_guarda_no_init_e_na_migracao():
    for arquivo in (EXTENSIONS, MIGRACAO):
        sql = arquivo.read_text(encoding="utf-8")
        assert "CREATE EXTENSION IF NOT EXISTS unaccent" in sql, arquivo.name
        assert "IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'portuguese_unaccent')" in sql, arquivo.name
        assert "CREATE TEXT SEARCH CONFIGURATION portuguese_unaccent (COPY = portuguese)" in sql, arquivo.name
        assert "ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem" in sql, arquivo.name
