import re
from functools import lru_cache
from urllib.parse import urlencode, urlparse

from django import template

from ..models import Assunto, TypeInformation
from ..taxonomy_v6 import colecao_v6_for_tipo

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
        if upper in _TITULO_SIGLAS:
            out.append(upper)
        else:
            lower = tok.lower()
            if first_word_done and lower in _TITULO_CONECTORES:
                out.append(lower)
            else:
                out.append(lower[:1].upper() + lower[1:])
        first_word_done = True
    return "".join(out)


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
