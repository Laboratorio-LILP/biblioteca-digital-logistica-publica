from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F

from .models import Document, TypeInformation
from .taxonomy_v6 import colecao_v6_for_tipo


# Filtros suportados pela busca; o helper apply_filters reutiliza esta lista
FILTERABLE_FIELDS = (
    "topic_id",
    "colecao_v6",
    "category_id",
    "subcategoria_id",
    "microcategoria_id",
    "assunto_id",
    "natureza",
    "etapa",
    "complexidade",
    "typeinform_id",
    "permissao",
    "ano_min",
    "ano_max",
    # Compatibilidade retroativa: year_from/year_to ainda aceitos
    "year_from",
    "year_to",
)


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
    if filters.get("assunto_id"):
        qs = qs.filter(assunto_id=filters["assunto_id"])
    if filters.get("natureza"):
        qs = qs.filter(natureza=filters["natureza"])
    if filters.get("etapa"):
        qs = qs.filter(etapa_processo_licitatorio=filters["etapa"])
    if filters.get("complexidade"):
        qs = qs.filter(complexidade=filters["complexidade"])
    if filters.get("typeinform_id"):
        qs = qs.filter(typeinform_id=filters["typeinform_id"])
    if filters.get("permissao"):
        qs = qs.filter(permissao=filters["permissao"])

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
SORT_CHOICES = ("autor", "titulo", "ano", "recente")


def _apply_sort(qs, sort, default):
    """Ordena por Autor/Título/Ano (escolha do usuário) ou pelo `default` da view.

    `default` é "-rank" na busca textual e "-created" na listagem por filtros.
    """
    if sort == "autor":
        return qs.order_by("autor_principal", "title")
    if sort == "titulo":
        return qs.order_by("title")
    if sort == "ano":
        return qs.order_by(F("ano").desc(nulls_last=True), "title")
    if sort == "recente":
        return qs.order_by("-created")
    return qs.order_by(default)


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
