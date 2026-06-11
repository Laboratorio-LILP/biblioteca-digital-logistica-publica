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


def search_documents(query, filters=None, sort=None):
    """Busca full-text em português + filtros estruturados nos documentos arquivados.

    O vetor inclui campos LILP (complexidade, uso_futuro, metodo, resultado)
    além dos clássicos title/keywords/author/abstract.
    """
    vector = (
        SearchVector("title", weight="A", config="portuguese")
        + SearchVector("keywords", weight="A", config="portuguese")
        + SearchVector("author", weight="B", config="portuguese")
        + SearchVector("autor_principal", weight="B", config="portuguese")
        + SearchVector("abstract", weight="C", config="portuguese")
        + SearchVector("uso_futuro", weight="C", config="portuguese")
        + SearchVector("metodo", weight="D", config="portuguese")
        + SearchVector("resultado", weight="D", config="portuguese")
        + SearchVector("complexidade", weight="D", config="portuguese")
    )
    search_query = SearchQuery(query, config="portuguese")

    qs = Document.objects.filter(status="a")
    qs = qs.annotate(rank=SearchRank(vector, search_query))
    qs = qs.filter(rank__gte=0.01)

    qs = _apply_filters(qs, filters)
    return _apply_sort(qs, sort, default="-rank")


def filter_documents(filters, sort=None):
    """Apenas filtros estruturados (sem termo de busca). Default: mais recente."""
    qs = Document.objects.filter(status="a")
    qs = _apply_filters(qs, filters)
    return _apply_sort(qs, sort, default="-created")
