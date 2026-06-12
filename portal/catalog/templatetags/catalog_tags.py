import re
from functools import lru_cache
from urllib.parse import urlencode, urlparse

from django import template

from ..models import Assunto, Microcategoria, NrCategory, Subcategoria, Topic, TypeInformation
from ..taxonomy_v6 import COLECOES_BY_SLUG, colecao_v6_for_tipo

register = template.Library()


_YEAR_ONLY_RE = re.compile(r"^\s*(?:19|20)\d{2}\s*$")


@register.filter
def is_year_only(value):
    """True se a string for apenas um ano de 4 dígitos (1900-2099) com
    eventuais espaços. Usado para esconder `source` quando ele é
    redundante com `ano` (357 docs do acervo).
    """
    if not value:
        return False
    return bool(_YEAR_ONLY_RE.match(str(value)))


@register.filter
def ano_redundante(doc):
    """True quando o ano do documento já aparece na imprenta (`source`) que será
    exibida — evita repetir o ano em 'Como citar' (438/499 docs trazem o ano
    embutido na fonte, ex.: 'Genebra, UNCITRAL/ONU, Janeiro 2010'). Se a `source`
    é só o ano (year-only), ela fica escondida e o ano NÃO é redundante."""
    fonte = (getattr(doc, "source", "") or "").strip()
    if not fonte or is_year_only(fonte):
        return False
    ano = getattr(doc, "ano", None)
    return bool(ano) and str(ano) in fonte


_PLURAIS_PT = {
    # Casos irregulares ou "{singular}+s" não aplicável.
    # Adicione aqui ao introduzir nova palavra na UI.
    "material": "materiais",
    "papel": "papéis",
    "nível": "níveis",
    "mês": "meses",
    "país": "países",
    "coleção": "coleções",
    "subcoleção": "subcoleções",
    "função": "funções",
    "razão": "razões",
    "informação": "informações",
    "edição": "edições",
    "publicação": "publicações",
    "operação": "operações",
    "cidadão": "cidadãos",  # exceção da regra ão→ões
    "irmão": "irmãos",
}


@register.filter
def pluralize_pt(value, singular):
    """Pluraliza palavra em português conforme `value` (count).

    Uso: {{ count|pluralize_pt:"material" }} → "material" se count==1,
    senão "materiais" (consulta o dicionário; fallback para singular+'s').

    Por que existir: o `pluralize` padrão do Django só sabe sufixar 's'/'es'
    (regra inglesa). Para palavras como "material → materiais" ou
    "coleção → coleções" o comportamento default produz "materialis" ou
    "coleçãos". Esta tag centraliza os irregulares do português.
    """
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = 0
    if n == 1:
        return singular
    if singular in _PLURAIS_PT:
        return _PLURAIS_PT[singular]
    # Heurística simples para os casos não dicionarizados:
    # ão→ões cobre a esmagadora maioria; consoantes finais ganham 'es';
    # demais ganham 's'. Se aparecer caso novo, prefira adicionar ao dict
    # acima em vez de generalizar a heurística.
    if singular.endswith("ão"):
        return singular[:-2] + "ões"
    if singular and singular[-1] in "rsz":
        return singular + "es"
    return singular + "s"


# Title Case em pt-BR para rótulos de Categoria/Subcategoria, que vêm em CAIXA
# ALTA no seed (07-categories.sql). Conectores ficam minúsculos (exceto na 1ª
# palavra); siglas do domínio são preservadas; '/' e '-' são separadores.
_TITULO_CONECTORES = {
    "de", "da", "do", "das", "dos", "e", "em", "na", "no", "a", "o",
    "para", "por", "com",
}
_TITULO_SIGLAS = {"PCA", "ETP", "TR", "TIC", "RP", "PMI", "ODS", "MPE"}
# Cada token é uma sequência de letras/dígitos (com acento) OU uma sequência de
# separadores/pontuação — nunca misturados, para preservar '/', '-', '(', ')'.
_TITULO_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+|[^0-9A-Za-zÀ-ÖØ-öø-ÿ]+")
# Numerais romanos (I, II, IV, VIII...) — preservados em maiúsculas nos rótulos
# das microcategorias ("EMERGÊNCIA - Inciso VIII", "incisos I e II"). O
# lookahead garante token só com letras romanas (sem casar string vazia).
_TITULO_ROMANO_RE = re.compile(r"^(?=[MDCLXVI]+$)M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")


@register.filter
def titulo_pt(value):
    """Title Case em português, idempotente, para Categoria/Subcategoria.

    - 1ª palavra sempre capitalizada; conectores (de, da, e, em...) ficam
      minúsculos nas demais posições;
    - siglas do domínio (PCA, ETP, TR, TIC, RP, PMI, ODS, MPE) preservadas;
    - '/' e '-' tratados como separadores: "PLANEJAMENTO/FASE PREPARATÓRIA" →
      "Planejamento/Fase Preparatória"; "FASE PREPARATÓRIA - ETP" →
      "Fase Preparatória - ETP".

    Idempotente: as subcategorias de "Conteúdos Transversais" já vêm em caixa
    mista no seed e devem sair intactas (rodar 2x não muda nada).
    """
    if not value:
        return value
    out = []
    first_word_done = False
    for tok in _TITULO_TOKEN_RE.findall(str(value)):
        if not tok.isalnum():  # separador/pontuação: mantém como está
            out.append(tok)
            continue
        upper = tok.upper()
        if upper in _TITULO_SIGLAS or _TITULO_ROMANO_RE.match(upper):
            out.append(upper)
        else:
            lower = tok.lower()
            if first_word_done and lower in _TITULO_CONECTORES:
                out.append(lower)
            else:
                out.append(lower[:1].upper() + lower[1:])
        first_word_done = True
    return "".join(out)


# Rótulos de exibição p/ Subcategorias redundantes com a Categoria pai (camada de
# UI; a taxonomia v8 canônica permanece intacta no banco e nos filtros). Chave =
# nome canônico em CAIXA ALTA, espaços colapsados.
SUBCAT_DISPLAY = {
    "FASE PREPARATÓRIA - ETP": "Estudo Técnico Preliminar (ETP)",
    "FASE PREPARATÓRIA - TR": "Termo de Referência (TR)",
    "FASE PREPARATÓRIA - GESTÃO DE RISCOS": "Gestão de Riscos",
    "FASE PREPARATÓRIA - PESQUISA DE PREÇOS": "Pesquisa de Preços",
}


@register.filter
def rotulo_sub(nome):
    """Rótulo de exibição de uma Subcategoria: usa o mapa curado (encurta a
    redundância com a Categoria pai) ou cai para Title Case (`titulo_pt`). Só
    apresentação — o nome canônico v8 segue no banco e nos filtros."""
    if not nome:
        return nome
    key = " ".join(str(nome).upper().split())
    return SUBCAT_DISPLAY.get(key) or titulo_pt(nome)


@register.filter
def url_domain(value):
    """Extrai o host de uma URL para exibir como hint sob botões de
    'Acessar documento' (ex: 'https://springer.com/x' → 'springer.com').
    Strips 'www.' para legibilidade.
    """
    if not value:
        return ""
    try:
        host = urlparse(str(value)).netloc
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


@register.filter
def truncate_words_html(value, length=30):
    """Trunca texto preservando palavras inteiras."""
    if not value:
        return ""
    words = value.split()
    if len(words) <= length:
        return value
    return " ".join(words[:length]) + "..."


@register.filter
def split_keywords(value):
    """Divide string de palavras-chave em lista."""
    if not value:
        return []
    separators = [";", ","]
    for sep in separators:
        if sep in value:
            return [kw.strip() for kw in value.split(sep) if kw.strip()]
    return [kw.strip() for kw in value.split() if kw.strip()]


@register.filter
def selected_in(current, opt_id):
    """True se `opt_id` está selecionado em `current` — que pode ser um valor
    único (faceta single-select) ou uma lista (faceta multi-select). Comparação
    sempre por string, para casar com `opt.id` (int) e querystring (str)."""
    sid = str(opt_id)
    if isinstance(current, (list, tuple, set)):
        return sid in {str(c) for c in current}
    return current not in (None, "") and sid == str(current)


@register.simple_tag
def querystring_replace(querydict, key, value):
    """Reescreve a querystring atual substituindo uma chave por um valor.

    Útil para links de paginação que preservam filtros aplicados:
        <a href="?{% querystring_replace request.GET 'page' 2 %}">Próxima</a>
    """
    params = querydict.copy() if hasattr(querydict, "copy") else dict(querydict)
    if value is None or value == "":
        params.pop(key, None)
    else:
        params[key] = str(value)
    # urlencode aceita dict comum ou QueryDict via .lists()
    if hasattr(params, "urlencode"):
        return params.urlencode()
    return urlencode(params)


@lru_cache(maxsize=1)
def _type_names():
    """{id: nome} de TypeInformation, carregado uma vez por processo (anti-N+1)."""
    return {ti.id: ti.name for ti in TypeInformation.objects.all()}


@lru_cache(maxsize=1)
def _assunto_names():
    """{id: nome} de Assunto, carregado uma vez por processo (anti-N+1)."""
    return {a.id: a.nome for a in Assunto.objects.all()}


@register.simple_tag
def colecao_visual(doc):
    """Coleção v6 (ícone + cor + nome) e nome do Tipo, derivados do Tipo de
    Informação. Resolve o nome do tipo por um mapa cacheado {id: nome} em vez da
    property doc.type_info, eliminando o N+1 nos cards (antes ~3 queries/card)."""
    tipo_nome = _type_names().get(getattr(doc, "typeinform_id", None), "")
    return {**colecao_v6_for_tipo(tipo_nome), "tipo_nome": tipo_nome}


@register.filter
def assunto_nome(doc):
    """Nome do Assunto do documento via mapa cacheado (evita a query da property)."""
    return _assunto_names().get(getattr(doc, "assunto_id", None), "")


@register.filter
def primary_author(doc):
    """Primeiro autor de `author` (coluna 'Autor Principal' do v8); fallback para
    a Autoridade Intelectual (`autor_principal`). Mantém coerência com
    extra_authors, que conta os segmentos de `author`."""
    author = (getattr(doc, "author", "") or "").strip()
    if author:
        return author.split(";")[0].strip()
    return (getattr(doc, "autor_principal", "") or "").strip()


@register.filter
def extra_authors(doc):
    """Nº de coautores além do principal (campo `author` separado por ';')."""
    author = (getattr(doc, "author", "") or "").strip()
    if not author:
        return 0
    parts = [p for p in author.split(";") if p.strip()]
    return max(0, len(parts) - 1)


# =====================================================================
# Painel "Seus filtros" — chips de filtros ativos (T1).
# Resolve cada par (param, valor) da query string num rótulo legível
# ({Dimensão}: {valor}) e numa URL que remove só aquele valor (multi mantém
# os demais) e volta para a página 1. Funciona sem JS: cada chip é um link GET.
# =====================================================================

@lru_cache(maxsize=1)
def _category_names():
    """{id: nome} de NrCategory (anti-N+1)."""
    return {c.id: c.name for c in NrCategory.objects.all()}


@lru_cache(maxsize=1)
def _subcategoria_names():
    """{id: nome} de Subcategoria (anti-N+1)."""
    return {s.id: s.nome for s in Subcategoria.objects.all()}


@lru_cache(maxsize=1)
def _microcategoria_names():
    """{id: nome} de Microcategoria (anti-N+1)."""
    return {m.id: m.nome for m in Microcategoria.objects.all()}


@lru_cache(maxsize=1)
def _topic_names():
    """{id: nome} de Topic/Coleção (anti-N+1)."""
    return {t.id: t.name for t in Topic.objects.all()}


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _chip_dimensao_valor(param, value):
    """(Dimensão legível, valor legível) para um filtro ativo.

    Tipos e coleção compartilham o prefixo "Coleção" (a seção da barra se chama
    Coleção); Categoria/Subcategoria recebem Title Case (titulo_pt), coerente
    com a T6; microcategoria fica como está.
    """
    sid = _safe_int(value)
    if param == "colecao_v6":
        col = COLECOES_BY_SLUG.get(value)
        return "Coleção", (col["nome"] if col else value)
    if param == "typeinform_id":
        return "Coleção", _type_names().get(sid, value)
    if param == "topic_id":
        return "Coleção", _topic_names().get(sid, value)
    if param == "category_id":
        return "Categoria", titulo_pt(_category_names().get(sid, value))
    if param == "subcategoria_id":
        return "Subcategoria", rotulo_sub(_subcategoria_names().get(sid, value))
    if param == "microcategoria_id":
        return "Microcategoria", titulo_pt(_microcategoria_names().get(sid, value))
    if param == "assunto_id":
        return "Assunto", _assunto_names().get(sid, value)
    if param == "natureza":
        return "Natureza", value
    if param == "permissao":
        return "Permissão", value
    if param == "complexidade":
        return "Complexidade", value
    if param == "etapa":
        return "Etapa", value
    return param, value


def _remove_value_url(querydict, param, value, is_multi):
    """Querystring atual menos (param, value), com a página resetada para 1."""
    params = querydict.copy()
    params.pop("page", None)
    if is_multi:
        restantes = [v for v in params.getlist(param) if v != value]
        if restantes:
            params.setlist(param, restantes)
        else:
            params.pop(param, None)
    else:
        params.pop(param, None)
    qs = params.urlencode()
    return ("?" + qs) if qs else "?"


@register.simple_tag
def applied_filters(querydict):
    """Lista de chips de filtros ativos: [{texto, aria, remove_url}].

    Uso: {% applied_filters request.GET as chips %}. Ignora q/sort/page —
    só os filtros de FILTER_PARAMS viram chip.
    """
    from ..views import FILTER_PARAMS, MULTI_PARAMS

    chips = []
    for param in FILTER_PARAMS:
        for value in (v for v in querydict.getlist(param) if v):
            if param == "ano_min":
                texto = "A partir de %s" % value
                aria = "Remover filtro Ano: a partir de %s" % value
            elif param == "ano_max":
                texto = "Até %s" % value
                aria = "Remover filtro Ano: até %s" % value
            else:
                dim, val = _chip_dimensao_valor(param, value)
                texto = "%s: %s" % (dim, val)
                aria = "Remover filtro %s: %s" % (dim, val)
            chips.append({
                "texto": texto,
                "aria": aria,
                "remove_url": _remove_value_url(querydict, param, value, param in MULTI_PARAMS),
            })
    return chips
