"""Importador estrito (v12) — funções de resolução com mapas falsos, sem banco.

Regras (set/2026): Coleção que não casa uma raiz é erro de linha (nunca a
primeira raiz); Tipo de informação fora do vocabulário canônico da coleção é
erro (Documentos Normativos e Vídeos passam a ser recusados); tipo novo não é
criado por padrão (`--allow-new-types`); aliases de grafia para a categoria
"PLANO ANUAL DE CONTRATAÇÕES (PCA)" e para subcategorias "FASE PREPARATÓRIA - X".
"""

import pytest

from catalog.management.commands.migrate_spreadsheet import (
    CATEGORIA_ALIASES,
    Command,
    LinhaRecusadaError,
    strip_accents,
)


@pytest.fixture
def cmd():
    c = Command()
    c.reset_alias_hits()
    return c


def _topic_map():
    # (parent_id, nome normalizado) -> id; raízes têm parent_id 0.
    roots = {"jurisprudência": 1, "trabalhos acadêmicos": 2, "doutrina e conteúdo técnico": 3,
             "instrução e capacitação": 4}
    m = {(0, strip_accents(k)): v for k, v in roots.items()}
    subs = {
        (1, "súmulas"): 6, (1, "boletins"): 7, (1, "acórdãos"): 29, (1, "deliberações"): 30,
        (1, "enunciados"): 5, (1, "documentos normativos"): 8,   # antigos, ainda no banco
        (3, "artigos"): 15, (3, "enunciados"): 31, (3, "pareceres"): 32, (3, "livros digitais"): 14,
        (4, "manuais"): 21, (4, "vídeos"): 27,
    }
    m.update({(p, strip_accents(k)): v for (p, k), v in subs.items()})
    return m


def _type_map():
    names = {"Artigos": 19, "Acórdãos": 97, "Deliberações": 98, "Pareceres": 99, "Enunciados": 85,
             "Documentos Normativos": 87, "Vídeos": 55, "Acórdão": 75, "Manuais": 24}
    return {strip_accents(k.lower()): v for k, v in names.items()}


# --- Coleção / Tipo ----------------------------------------------------------

def test_colecao_que_nao_casa_e_erro(cmd):
    with pytest.raises(LinhaRecusadaError, match="Coleção"):
        cmd._resolve_topic({"colecao": "Coleção Inexistente", "tipo_informacao": "Artigos"}, _topic_map())


def test_colecao_vazia_e_erro(cmd):
    with pytest.raises(LinhaRecusadaError, match="Coleção"):
        cmd._resolve_topic({"colecao": "", "tipo_informacao": "Artigos"}, _topic_map())


def test_tipo_canonico_resolve_subcolecao(cmd):
    tm = _topic_map()
    assert cmd._resolve_topic({"colecao": "Jurisprudência", "tipo_informacao": "Acórdãos"}, tm) == 29
    assert cmd._resolve_topic({"colecao": "Doutrina e Conteúdo Técnico", "tipo_informacao": "Enunciados"}, tm) == 31
    # v12.1 (23/09/2026): Pareceres saiu do vocabulário — recusado mesmo com a
    # subcoleção ainda no banco.
    with pytest.raises(LinhaRecusadaError):
        cmd._resolve_topic({"colecao": "Doutrina e Conteúdo Técnico", "tipo_informacao": "Pareceres"}, tm)


def test_grafia_legada_do_tipo_e_aceita_e_normalizada(cmd):
    tm = _topic_map()
    assert cmd._resolve_topic({"colecao": "Jurisprudência", "tipo_informacao": "Acórdão"}, tm) == 29
    assert cmd._resolve_topic({"colecao": "jurisprudencia", "tipo_informacao": "deliberacao"}, tm) == 30


def test_tipo_fora_do_vocabulario_da_colecao_e_erro(cmd):
    tm = _topic_map()
    with pytest.raises(LinhaRecusadaError, match="Tipo de informação"):
        cmd._resolve_topic({"colecao": "Jurisprudência", "tipo_informacao": "Documentos Normativos"}, tm)
    with pytest.raises(LinhaRecusadaError, match="Tipo de informação"):
        cmd._resolve_topic({"colecao": "Instrução e Capacitação", "tipo_informacao": "Vídeos"}, tm)
    # Enunciados agora é de Doutrina: sob Jurisprudência é recusado, mesmo com o topic antigo no banco.
    with pytest.raises(LinhaRecusadaError, match="Tipo de informação"):
        cmd._resolve_topic({"colecao": "Jurisprudência", "tipo_informacao": "Enunciados"}, tm)
    with pytest.raises(LinhaRecusadaError, match="Tipo de informação"):
        cmd._resolve_topic({"colecao": "Jurisprudência", "tipo_informacao": ""}, tm)


def test_tipo_canonico_sem_subcolecao_no_banco_cai_na_raiz(cmd):
    # Banco ainda sem a seção 1 do script: o tipo é válido, só falta o topic filho.
    tm = _topic_map()
    del tm[(1, "sumulas")]
    assert cmd._resolve_topic({"colecao": "Jurisprudência", "tipo_informacao": "Súmulas"}, tm) == 1


def test_ensure_type_nao_cria_por_padrao(cmd):
    tmap = _type_map()
    assert cmd._ensure_type(None, "Acórdão", tmap) == 97          # grafia legada → canônico
    with pytest.raises(LinhaRecusadaError, match="allow-new-types"):
        cmd._ensure_type(None, "Tipo Novo Qualquer", tmap)
    with pytest.raises(LinhaRecusadaError, match="Tipo de informação"):
        cmd._ensure_type(None, "Vídeos", tmap)                     # fora do vocabulário, mesmo existindo no banco
    assert cmd._ensure_type(None, "", tmap) is None


# --- Categoria / Subcategoria (aliases) ----------------------------------------

def _cat_map():
    return {k.lower(): v for k, v in {
        "PLANO DE CONTRATAÇÕES ANUAL (PCA)": 1, "CICLO COMPLETO DA CONTRATAÇÃO": 2,
        "PLANEJAMENTO/FASE PREPARATÓRIA": 3, "SELEÇÃO DO FORNECEDOR": 4,
        "GESTÃO CONTRATUAL": 5, "CONTEÚDOS TRANSVERSAIS": 6,
    }.items()}


def test_alias_pca_grafia_v8(cmd):
    assert "plano anual de contratacoes (pca)" in CATEGORIA_ALIASES
    assert cmd._resolve_category("PLANO ANUAL DE CONTRATAÇÕES (PCA)", _cat_map()) == 1
    assert cmd._resolve_category("PLANO DE CONTRATAÇÕES ANUAL (PCA)", _cat_map()) == 1
    assert cmd.alias_hits["categoria"] == 1


def test_categoria_desconhecida_e_erro(cmd):
    with pytest.raises(LinhaRecusadaError, match="Categoria"):
        cmd._resolve_category("CATEGORIA QUE NÃO EXISTE", _cat_map())
    assert cmd._resolve_category("", _cat_map()) is None


def _sub_map():
    return {
        (3, "etp"): 4, (3, "tr"): 3, (3, "gestao de riscos"): 2, (3, "pesquisa de precos"): 1,
        (4, "licitacao"): 7, (4, "contratacao direta"): 6, (4, "procedimentos auxiliares"): 5,
    }


def test_alias_subcategoria_sem_prefixo(cmd):
    assert cmd._resolve_subcategoria("FASE PREPARATÓRIA - ETP", 3, _sub_map()) == 4
    assert cmd._resolve_subcategoria("Fase Preparatória - Gestão de Riscos", 3, _sub_map()) == 2
    assert cmd._resolve_subcategoria("ETP", 3, _sub_map()) == 4
    assert cmd.alias_hits["subcategoria"] == 2


def test_subcategoria_desconhecida_e_erro(cmd):
    with pytest.raises(LinhaRecusadaError, match="Subcategoria"):
        cmd._resolve_subcategoria("SUB QUE NÃO EXISTE", 3, _sub_map())
    assert cmd._resolve_subcategoria("", 3, _sub_map()) is None


def test_subcategoria_preenchida_sem_categoria_e_erro(cmd):
    # Preenchida sem o nível acima resolvido não pode sumir em silêncio (revisão 14/09).
    with pytest.raises(LinhaRecusadaError, match="Subcategoria"):
        cmd._resolve_subcategoria("ETP", None, _sub_map())
    with pytest.raises(LinhaRecusadaError, match="Microcategoria"):
        cmd._resolve_microcategoria("MAPA DE RISCOS", None, {(2, "mapa de riscos"): 2})


def test_substring_nao_casa_nomes_curtos_do_banco(cmd):
    # Revisão 14/09: com "TR"/"ETP" no banco, 'OUTROS' e 'CONTRATAÇÃO DIRETA' casavam
    # TR por substring ("tr" dentro da chave) e entravam classificados errado.
    for ruim in ("OUTROS", "CONTRATAÇÃO DIRETA", "MATRIZ DE RISCOS", "OUTRA"):
        with pytest.raises(LinhaRecusadaError, match="Subcategoria"):
            cmd._resolve_subcategoria(ruim, 3, _sub_map())
    # ...mas as grafias por extenso resolvem por alias explícito, contadas no resumo.
    assert cmd._resolve_subcategoria("Termo de Referência (TR)", 3, _sub_map()) == 3
    assert cmd._resolve_subcategoria("ESTUDO TÉCNICO PRELIMINAR", 3, _sub_map()) == 4
    assert cmd._resolve_subcategoria("Termo de Referência", 3, _sub_map()) == 3
    assert cmd.alias_hits["subcategoria"] == 3


def test_allow_new_types_aceita_tipo_novo_na_raiz_mas_nao_tipo_retirado(cmd):
    # Revisão 14/09: a flag era inócua porque _resolve_topic recusava antes de _ensure_type.
    tm = _topic_map()
    rec = {"colecao": "Doutrina e Conteúdo Técnico", "tipo_informacao": "Tipo Novo Qualquer"}
    with pytest.raises(LinhaRecusadaError, match="Tipo de informação"):
        cmd._resolve_topic(rec, tm)
    assert cmd._resolve_topic(rec, tm, allow_new_types=True) == 3          # cai na raiz da coleção
    # Tipos RETIRADOS continuam recusados mesmo com a flag (não são "novos").
    with pytest.raises(LinhaRecusadaError, match="Tipo de informação"):
        cmd._resolve_topic({"colecao": "Instrução e Capacitação", "tipo_informacao": "Vídeos"}, tm,
                           allow_new_types=True)


def test_microcategoria_desconhecida_e_erro(cmd):
    mic = {(2, "mapa de riscos"): 2, (2, "matriz de alocacao de riscos"): 1}
    assert cmd._resolve_microcategoria("Mapa de Riscos", 2, mic) == 2
    with pytest.raises(LinhaRecusadaError, match="Microcategoria"):
        cmd._resolve_microcategoria("MICRO INEXISTENTE", 2, mic)


def test_assunto_desconhecido_e_erro(cmd):
    amap = {"governanca": 6, "logistica publica internacional": 16}
    assert cmd._resolve_assunto("Logística Pública Internacional", amap) == 16
    with pytest.raises(LinhaRecusadaError, match="Assunto"):
        cmd._resolve_assunto("Assunto Inventado", amap)


def test_flag_allow_new_types_existe():
    import argparse

    parser = argparse.ArgumentParser()
    Command().add_arguments(parser)
    ns = parser.parse_args(["x.xlsx", "--allow-new-types", "--skip-red", "--dry-run"])
    assert ns.allow_new_types is True and ns.skip_red is True and ns.dry_run is True
