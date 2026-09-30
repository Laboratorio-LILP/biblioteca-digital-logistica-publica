"""Erros 500 por URL manipulada e registro em log (achado F2-01 da auditoria de
23/09/2026).

As sete formas do caderno: `category_id=abc`, `assunto_id=abc`, `typeinform_id=abc`,
`subcategoria_id=abc`, `q` com ~200 palavras (RecursionError na cadeia OR da
tsquery), `q=%00` e `natureza=%00` (NUL numa string literal do Postgres). Passam a
responder 400 tratado — exceto a busca longa, que funciona com a consulta
limitada a MAX_TOKENS_BUSCA palavras — e todo 4xx/5xx sai no stdout do
contêiner (LOGGING + gunicorn). Sem banco: só as funções puras, os templates e a
configuração.
"""

import logging
from pathlib import Path

import pytest
from django.core.exceptions import BadRequest
from django.http import QueryDict
from django.test import RequestFactory, override_settings

from catalog import search, views
from portal import settings as cfg
from portal import urls as urls_raiz

REPO = Path(__file__).resolve().parents[3]

ARMAZENAMENTO_SIMPLES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@pytest.mark.parametrize("param", ["category_id", "subcategoria_id", "microcategoria_id", "assunto_id",
                                   "typeinform_id", "ano_min", "ano_max"])
def test_id_ou_ano_que_nao_e_inteiro_vira_400(param):
    with pytest.raises(BadRequest):
        views._read_filters_from(QueryDict(f"{param}=abc"))
    with pytest.raises(BadRequest):
        views._read_filters_from(QueryDict(f"{param}=1%00"))


def test_ids_validos_sao_normalizados_e_multi_select_vira_lista():
    f = views._read_filters_from(QueryDict("category_id=007&assunto_id=3&assunto_id=12&typeinform_id=19&ano_min=2020"))
    assert f == {"category_id": "7", "assunto_id": ["3", "12"], "typeinform_id": ["19"], "ano_min": "2020"}


def test_texto_de_filtro_com_nul_vira_400_e_texto_normal_passa():
    with pytest.raises(BadRequest):
        views._read_filters_from(QueryDict("natureza=%00"))
    with pytest.raises(BadRequest):
        views._read_filters_from(QueryDict("colecao_v6=doutrina%00"))
    qs = "natureza=Contrata%C3%A7%C3%A3o+de+TIC&colecao_v6=doutrina&permissao=aberto"
    f = views._read_filters_from(QueryDict(qs))
    assert f["natureza"] == ["Contratação de TIC"] and f["colecao_v6"] == "doutrina" and f["permissao"] == ["aberto"]


def test_termo_de_busca_com_nul_vira_400_e_espacos_sao_aparados():
    with pytest.raises(BadRequest):
        views._termo_de_busca(QueryDict("q=%00"))
    with pytest.raises(BadRequest):
        views._termo_de_busca(QueryDict("q=preg%C3%A3o%00"))
    assert views._termo_de_busca(QueryDict("q=++preg%C3%A3o++")) == "pregão"
    assert views._termo_de_busca(QueryDict("")) == ""


def test_busca_longa_e_limitada_em_palavras_e_nao_recursa():
    longa = " ".join(f"palavra{i}" for i in range(200))
    assert search.MAX_TOKENS_BUSCA == 32
    assert len(search._tokens(longa)) == 32
    consulta = search._consulta(longa, com_unaccent=True)       # antes: RecursionError
    assert consulta is not None
    assert search._tokens("  pregão   eletrônico ") == ["pregão", "eletrônico"]


def test_navegacao_do_documento_degrada_em_vez_de_dar_400():
    # o ctx (querystring da busca de origem) vem da URL: inválido → sem anterior/próximo, página segue
    nav = views._resultado_navegacao(None, "category_id=abc")
    assert nav == {"prev_url": None, "next_url": None, "back_url": None, "pos": None, "total": None}


def test_handlers_de_erro_registrados_na_raiz():
    assert urls_raiz.handler400 == "catalog.views.erro_400"
    assert urls_raiz.handler500 == "catalog.views.erro_500"


@override_settings(STORAGES=ARMAZENAMENTO_SIMPLES, DEBUG=False)
def test_pagina_400_renderiza_sem_banco_com_texto_em_linguagem_simples():
    req = RequestFactory().get("/busca/?category_id=abc")
    resp = views.erro_400(req, BadRequest("id inválido"))
    html = resp.content.decode("utf-8")
    assert resp.status_code == 400
    assert "<h1>Endereço inválido</h1>" in html and "página inicial" in html
    assert "abc" not in html and "BadRequest" not in html                       # nada do pedido volta na página
    assert "Ver acervo" in html or "Buscar no acervo" in html


@override_settings(STORAGES=ARMAZENAMENTO_SIMPLES, DEBUG=False)
def test_pagina_500_renderiza_com_contexto_minimo_sem_banco():
    # o handler500 do Django não roda context processors (um erro de banco entraria em laço);
    # a nossa versão passa só o ano e o nome da rota — nada que consulte o banco
    req = RequestFactory().get("/busca/")
    resp = views.erro_500(req)
    html = resp.content.decode("utf-8")
    assert resp.status_code == 500
    assert "<h1>Tivemos um problema</h1>" in html
    assert "© 20" in html                                                        # site_year no rodapé
    assert "{{" not in html and "{%" not in html


def test_logging_manda_erros_de_requisicao_para_o_stdout_do_conteiner():
    log = cfg.LOGGING
    assert log["version"] == 1 and log["disable_existing_loggers"] is False
    consola = [n for n, h in log["handlers"].items() if h.get("class") == "logging.StreamHandler"]
    assert consola, "precisa de um handler de console (stdout/stderr do contêiner)"
    assert set(log["loggers"]["django.request"]["handlers"]) & set(consola)
    assert logging.getLevelName(log["loggers"]["django.request"]["level"]) <= logging.WARNING  # 400/404 e 500
    assert log["loggers"]["django.request"]["propagate"] is False
    assert "catalog" in log["loggers"]                                          # avisos da busca (unaccent ausente)


def test_gunicorn_grava_acesso_e_erros_na_saida_do_conteiner():
    dockerfile = (REPO / "docker" / "portal" / "Dockerfile").read_text(encoding="utf-8")
    assert '"--access-logfile", "-"' in dockerfile and '"--error-logfile", "-"' in dockerfile
