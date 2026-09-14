import re

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F

from .models import Document, TypeInformation
from .taxonomy_v6 import colecao_v6_for_tipo


def _typeinform_ids_for_colecao(slug):
    """Ids de Tipo de Informação que compõem uma coleção v6.

    Usa a MESMA função de mapeamento da faceta de contagem
    (`colecao_v6_for_tipo`, resiliente a nomes v5/variantes de grafia) em vez do
    vocabulário v6 plural exato. Garante que filtro e contagem sejam sempre
    consistentes — qualquer tipo que a contagem atribui à coleção, o filtro inclui.
    """
    return [
        ti.id
        for ti in TypeInformation.objects.all()
        if colecao_v6_for_tipo(ti.name)["slug"] == slug
    ]


def _eq_or_in(qs, field, value):
    """Filtra por igualdade (valor único) ou pertencimento (lista/tupla).

    Facetas multi-select chegam como lista → vira `field__in`; single-select
    chega como string → vira `field=`. Robustez: também aceita escalares.
    """
    if isinstance(value, (list, tuple, set)):
        vals = [v for v in value if v not in (None, "")]
        return qs.filter(**{f"{field}__in": vals}) if vals else qs
    return qs.filter(**{field: value})


def _apply_filters(qs, filters):
    """Aplica filtros estruturados ao queryset de Document."""
    if not filters:
        return qs

    if filters.get("topic_id"):
        qs = qs.filter(topic_id=filters["topic_id"])
    if filters.get("colecao_v6"):
        ids = _typeinform_ids_for_colecao(filters["colecao_v6"])
        qs = qs.filter(typeinform_id__in=ids or [-1])
    if filters.get("category_id"):
        qs = qs.filter(category_id=filters["category_id"])
    if filters.get("subcategoria_id"):
        qs = qs.filter(subcategoria_id=filters["subcategoria_id"])
    if filters.get("microcategoria_id"):
        qs = qs.filter(microcategoria_id=filters["microcategoria_id"])
    # Eixos paralelos multi-select (OR dentro da faceta)
    if filters.get("assunto_id"):
        qs = _eq_or_in(qs, "assunto_id", filters["assunto_id"])
    if filters.get("natureza"):
        qs = _eq_or_in(qs, "natureza", filters["natureza"])
    if filters.get("typeinform_id"):
        qs = _eq_or_in(qs, "typeinform_id", filters["typeinform_id"])
    if filters.get("permissao"):
        qs = _eq_or_in(qs, "permissao", filters["permissao"])
    if filters.get("complexidade"):
        qs = _eq_or_in(qs, "complexidade", filters["complexidade"])
    if filters.get("etapa"):
        qs = qs.filter(etapa_processo_licitatorio=filters["etapa"])

    # Ano: novos params (ano_min/ano_max) preferidos sobre legados (year_from/year_to)
    ano_min = filters.get("ano_min") or filters.get("year_from")
    ano_max = filters.get("ano_max") or filters.get("year_to")
    if ano_min:
        try:
            qs = qs.filter(ano__gte=int(ano_min))
        except (TypeError, ValueError):
            pass
    if ano_max:
        try:
            qs = qs.filter(ano__lte=int(ano_max))
        except (TypeError, ValueError):
            pass

    return qs


# Ordenação exposta ao usuário (restrição Lina: Autor/Título/Ano).
SORT_CHOICES = ("autor", "titulo", "ano", "ano_asc", "recente")


def _apply_sort(qs, sort, default):
    """Ordena por Autor/Título/Ano (escolha do usuário) ou pelo `default` da view.

    `default` é "-rank" na busca textual e "-created" na listagem por filtros.

    Toda ordenação termina em `-pk` (desempate único e estável). Sem essa chave
    total, a paginação LIMIT/OFFSET do Django duplica e omite registros quando o
    critério visível empata — e os 499 docs foram carregados em lote com `created`
    idêntico, então `-created`/`-rank` empatam em massa. Com `-pk` as páginas
    "ladrilham" sem perder nem repetir documentos.
    """
    if sort == "autor":
        # Ordena pelo MESMO campo exibido no card (`author` = Autor Principal),
        # não por `autor_principal` (Autoridade Intelectual) — senão a lista
        # parece fora de ordem, já que o card mostra `author`.
        return qs.order_by("author", "title", "-pk")
    if sort == "titulo":
        return qs.order_by("title", "-pk")
    if sort == "ano":
        return qs.order_by(F("ano").desc(nulls_last=True), "title", "-pk")
    if sort == "ano_asc":
        return qs.order_by(F("ano").asc(nulls_last=True), "title", "-pk")
    if sort == "recente":
        return qs.order_by("-created", "-pk")
    return qs.order_by(default, "-pk")


# Campos e pesos do vetor de busca. Inclui campos LILP (complexidade,
# uso_futuro, metodo, resultado) além dos clássicos title/keywords/author/abstract.
_FTS_CAMPOS = (
    ("title", "A"),
    ("keywords", "A"),
    ("author", "B"),
    ("autor_principal", "B"),
    ("abstract", "C"),
    ("uso_futuro", "C"),
    ("metodo", "D"),
    ("resultado", "D"),
    ("complexidade", "D"),
)


def _vetor(config):
    """Soma dos SearchVector dos campos de _FTS_CAMPOS numa configuração de busca."""
    vetor = None
    for campo, peso in _FTS_CAMPOS:
        sv = SearchVector(campo, weight=peso, config=config)
        vetor = sv if vetor is None else vetor + sv
    return vetor


# Sufixos nasais do português que o usuário costuma digitar sem acento. O
# radicalizador `portuguese` depende do "ção"/"ções" para chegar ao mesmo
# radical de singular e plural ("licitação" e "licitações" → "licit"); sem o
# acento, "licitacao" → "licitaca" e "licitacoes" → "licitaco" — mesmo com
# unaccent, que roda ANTES do stemmer. Por isso a consulta ganha uma variante
# re-acentuada, só nos tokens 100% ASCII, do sufixo mais longo para o mais curto.
_SUFIXOS_REACENTUACAO = (
    ("coes", "ções"), ("cao", "ção"), ("aos", "ãos"), ("oes", "ões"), ("aes", "ães"),
    ("ao", "ão"), ("ae", "ãe"),
)
# Token de letras ASCII não colado a outra letra Unicode (senão seria pedaço
# de uma palavra já acentuada, ex.: "licita" em "licitação").
_TOKEN_ASCII_RE = re.compile(r"(?<![^\W\d_])[A-Za-z]+(?![^\W\d_])")


def reacentuar(termo):
    """Variante da consulta com os sufixos nasais re-acentuados ("licitacao" →
    "licitação", "sancoes" → "sanções"); '' quando nada muda. Usada em OR com a
    consulta original — só acrescenta resultados, nunca tira."""

    def _token(m):
        palavra = m.group(0)
        baixa = palavra.lower()
        for sufixo, acentuado in _SUFIXOS_REACENTUACAO:
            if baixa.endswith(sufixo) and len(baixa) > len(sufixo) + 1:
                return baixa[: -len(sufixo)] + acentuado
        return palavra

    novo = _TOKEN_ASCII_RE.sub(_token, termo or "")
    return novo if novo != (termo or "") else ""


def apply_fulltext(qs, query):
    """Restringe `qs` aos documentos que casam a busca textual, anotando `rank`.

    É o critério ÚNICO de "casa a busca": compartilhado pela lista de
    resultados (search_documents) e pela base das facetas (compute_facets).
    Se divergirem, a contagem da barra lateral não bate com a lista exibida.

    Busca sem acento (set/2026): "pregao" precisa achar o mesmo que "pregão"
    SEM perder o que a configuração `portuguese` já casa (plural, flexões).
    Aplicar unaccent ANTES do radicalizador quebra regras do português
    ("licitações" → "licitaco" ≠ "licitação" → "licitaca"), então as duas
    configurações são SOMADAS, não trocadas: vetor = campos em `portuguese`
    + os mesmos campos (mesmos pesos) em `portuguese_unaccent`; consulta =
    OR das duas, mais a variante re-acentuada dos sufixos nasais (reacentuar),
    que fecha o caso plural/singular que o unaccent-antes-do-stemmer não
    cobre ("licitacao" precisa achar "licitações"). `portuguese_unaccent` é
    criada em 00-extensions.sql (volume novo) e na seção 1 de
    docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql.
    """
    vector = _vetor("portuguese") + _vetor("portuguese_unaccent")
    search_query = SearchQuery(query, config="portuguese") | SearchQuery(query, config="portuguese_unaccent")
    variante = reacentuar(query)
    if variante:
        search_query = search_query | SearchQuery(variante, config="portuguese")
    return qs.annotate(rank=SearchRank(vector, search_query)).filter(rank__gte=0.01)


def search_documents(query, filters=None, sort=None):
    """Busca full-text em português + filtros estruturados nos documentos arquivados."""
    qs = apply_fulltext(Document.objects.filter(status="a"), query)
    qs = _apply_filters(qs, filters)
    return _apply_sort(qs, sort, default="-rank")


def filter_documents(filters, sort=None):
    """Apenas filtros estruturados (sem termo de busca). Default: mais recente."""
    qs = Document.objects.filter(status="a")
    qs = _apply_filters(qs, filters)
    return _apply_sort(qs, sort, default="-created")
