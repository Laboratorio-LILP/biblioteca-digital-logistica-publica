from urllib.parse import urlencode

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .facets import (
    cards_tematicos_overview,
    categorias_overview,
    colecao_v6_overview,
    compute_facets,
    tema_busca,
)
from .models import Document, NrCategory, Topic, TypeInformation
from .search import filter_documents, search_documents
from .taxonomy_v6 import COLECOES_BY_SLUG, TEMAS_DESTAQUE
from .templatetags.catalog_tags import titulo_pt


def _artigos_type_id():
    """Id do Tipo de Informação 'Artigos' — usado para o destaque na home/busca.

    Na taxonomia v6 todos os tipos de artigo são colapsados num único
    'Artigos' (coleção Doutrina e Conteúdo Técnico). Pode ser None enquanto
    os dados ainda não tiverem esse tipo (classificação v5).
    """
    return (
        TypeInformation.objects.filter(name__iexact="Artigos")
        .values_list("id", flat=True)
        .first()
    )


def _search_url(**params):
    """URL da página de busca (Acervo) com querystring — ex.: ?colecao_v6=… ou ?q=…"""
    return f"{reverse('catalog:search')}?{urlencode(params)}"


def _card_colecao(c):
    """Normaliza uma coleção formal (colecao_v6_overview) para o card unificado."""
    return {
        "href": _search_url(colecao_v6=c["id"]),
        "color": c["color"], "icon": c["icon"], "label": c["nome"],
        "desc": c.get("descricao", ""), "count": c["count"],
    }


def _card_categoria(cat):
    """Normaliza uma categoria processual (categorias_overview) para o card
    unificado. O rótulo recebe Title Case (titulo_pt), como na busca; o link usa
    o filtro de Categoria por id (category_id) da página de Acervo."""
    return {
        "href": _search_url(category_id=cat["id"]),
        "color": cat["color"], "icon": cat["icon"],
        "label": titulo_pt(cat["nome"]), "desc": cat["descricao"], "count": cat["count"],
    }


def _docs_do_tema(tema):
    """Documentos de preview de um bloco de 'Temas em Alta'.

    Os 2 cards (1 linha) são os documentos mais representativos do MESMO filtro
    que define o tema (`tema_busca`: por Assunto curado ou busca textual) — o que
    alimenta o link "Ver tema no acervo" e a contagem do card. Assim o preview é
    sempre uma amostra do que o usuário vê ao clicar, nunca fora do tema. Lista
    vazia se o tema não tem documentos — a home oculta o bloco (antes caía para
    "mais recentes", que trazia documentos fora do tema).
    """
    params, _ = tema_busca(tema)
    if "assunto_id" in params:
        base = Document.objects.filter(status="a", assunto_id=params["assunto_id"]).order_by("-created", "-pk")
    else:
        base = search_documents(params["q"])  # ordenado por relevância (-rank)
    return list(base[:2])


def home(request):
    """Homepage: busca, stats, coleções e temas em destaque."""
    colecoes_v6 = colecao_v6_overview()
    tematicos = cards_tematicos_overview()

    # "Explorar o acervo" (Item 1): apenas as 4 Coleções formais como cards.
    cards_explorar = [_card_colecao(c) for c in colecoes_v6]
    # Os temas viram chips-âncora p/ a seção "Temas em alta" (mesma fonte:
    # cards_tematicos_overview, já em `tematicos`), com slug p/ a âncora.
    # Só os com resultados (count > 0): alinha com `temas_em_alta` (filtrado por
    # docs abaixo) e evita chip-âncora para um bloco que não foi renderizado.
    chips_temas = [t for t in tematicos if t["count"] > 0]

    # "Temas em Alta": um bloco por tema, com até 3 documentos em destaque. O link
    # "Ver tema" usa o mesmo filtro do card (Assunto curado ou texto).
    temas_em_alta = [
        {
            "slug": t["slug"],
            "label": t["label"],
            "intro": t["alta_intro"],
            "icon": t["icon"],
            "color": t["color"],
            "href": _search_url(**tema_busca(t)[0]),
            "docs": _docs_do_tema(t),
        }
        for t in TEMAS_DESTAQUE
    ]
    # Não renderiza um bloco de tema sem documentos no próprio tema (em vez de
    # cair para "mais recentes", que mostrava documentos fora do tema).
    temas_em_alta = [t for t in temas_em_alta if t["docs"]]

    # "Comece pela etapa da contratação": categorias processuais (macroetapas da
    # Lei 14.133/21) como porta de entrada por tarefa — núcleo sequencial + visões
    # transversais. Reusa a rota de busca filtrada por Categoria (category_id).
    categorias = categorias_overview()
    cards_etapas = [_card_categoria(c) for c in categorias["nucleo"]]
    cards_transversais = [_card_categoria(c) for c in categorias["transversal"]]

    # Stat 1: total de materiais
    total_docs = Document.objects.filter(status="a").count()

    # Stat 2: distribuição por Tipo de informação (top 3 por contagem)
    tipo_dist = (
        Document.objects.filter(status="a", typeinform_id__isnull=False)
        .values("typeinform_id")
        .annotate(c=Count("id"))
        .order_by("-c")[:3]
    )
    type_info_names = {
        ti.id: ti.name
        for ti in TypeInformation.objects.filter(
            id__in=[t["typeinform_id"] for t in tipo_dist]
        )
    }
    tipos_top = [
        {"nome": type_info_names.get(t["typeinform_id"], "—"), "count": t["c"]}
        for t in tipo_dist
    ]
    tipos_distintos = (
        Document.objects.filter(status="a", typeinform_id__isnull=False)
        .values("typeinform_id").distinct().count()
    )

    # Stat 3: cobertura temática
    from .models import Assunto, Subcategoria
    cobertura = {
        "assuntos": Assunto.objects.count(),
        "subcategorias": Subcategoria.objects.count(),
        "macroetapas": NrCategory.objects.count(),
    }

    return render(request, "home.html", {
        "colecoes_v6": colecoes_v6,
        "cards_explorar": cards_explorar,
        "chips_temas": chips_temas,
        "cards_etapas": cards_etapas,
        "cards_transversais": cards_transversais,
        "temas_em_alta": temas_em_alta,
        "total_docs": total_docs,
        "tipos_top": tipos_top,
        "tipos_distintos": tipos_distintos,
        "cobertura": cobertura,
    })


FILTER_PARAMS = (
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
)

# Facetas de eixo paralelo: aceitam MÚLTIPLOS valores (OR dentro da faceta,
# AND entre facetas). As demais — Coleção e a hierarquia Categoria→Sub→Micro —
# seguem single-select (a hierarquia depende disso para a cascata).
MULTI_PARAMS = frozenset({
    "assunto_id",
    "natureza",
    "typeinform_id",
    "permissao",
    "complexidade",
})


def _read_filters_from(getparams):
    """Extrai filtros válidos de um QueryDict, descartando vazios.

    Params em MULTI_PARAMS viram lista de valores (`getlist`); os demais,
    valor único (`get`). Usado tanto com request.GET quanto com um `ctx` de busca
    reconstruído (para o anterior/próximo na página de documento).
    """
    filters = {}
    for p in FILTER_PARAMS:
        if p in MULTI_PARAMS:
            vals = [v for v in getparams.getlist(p) if v]
            if vals:
                filters[p] = vals
        else:
            value = getparams.get(p)
            if value:
                filters[p] = value
    return filters


def _read_filters(request):
    """Filtros válidos da query string da requisição."""
    return _read_filters_from(request.GET)


def search(request):
    """Busca full-text com filtros facetados em cascata."""
    query = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)
    sort = request.GET.get("sort", "")
    filters = _read_filters(request)
    # Nº de filtros ATIVOS (conta valores, não dimensões): multi-select soma cada
    # valor escolhido. Alimenta o "(N)" do botão de filtros no mobile.
    filtros_count = sum(
        len(v) if isinstance(v, (list, tuple)) else 1 for v in filters.values()
    )

    # Breadcrumb contextual: quando se chega ao acervo filtrado por uma Coleção
    # (Home/Coleções) ou por uma Categoria/etapa (seção "Comece pela etapa"),
    # completa "Início > Acervo > {contexto}" em vez de parar em "Acervo".
    crumb = None
    if filters.get("colecao_v6"):
        col = COLECOES_BY_SLUG.get(filters["colecao_v6"])
        if col:
            crumb = col["nome"]
    elif filters.get("category_id"):
        cat = NrCategory.objects.filter(id=filters["category_id"]).first()
        if cat:
            crumb = titulo_pt(cat.name)

    if query:
        results = search_documents(query, filters if filters else None, sort=sort)
    elif filters:
        results = filter_documents(filters, sort=sort)
    else:
        # Sem busca e sem filtros: lista os mais recentes (não vazio como antes)
        results = filter_documents({}, sort=sort)

    paginator = Paginator(results, settings.SEARCH_RESULTS_PER_PAGE)
    page_obj = paginator.get_page(page_number)

    facets = compute_facets(filters, query=query or None)

    return render(request, "search.html", {
        "query": query,
        "page_obj": page_obj,
        "filters": filters,
        "filtros_count": filtros_count,
        "crumb": crumb,
        "facets": facets,
        "total_results": paginator.count,
        "sort": sort,
        "artigos_id": _artigos_type_id(),
    })


def _resultado_navegacao(doc, ctx):
    """Anterior/Próximo a partir do contexto de busca (`ctx` = querystring original).

    Recalcula a busca/ordenação do ctx, acha a posição do documento na lista
    ordenada de resultados e devolve URLs de anterior/próximo (carregando o ctx
    adiante), 'voltar à busca' e a posição (X de Y). Degrada para tudo None se não
    há ctx ou o documento não está nos resultados. O custo é uma consulta de códigos
    (acervo pequeno); reavaliar se o acervo crescer muito.
    """
    from django.http import QueryDict

    nav = {"prev_url": None, "next_url": None, "back_url": None, "pos": None, "total": None}
    if not ctx:
        return nav
    cq = QueryDict(ctx)
    query = cq.get("q", "").strip()
    sort = cq.get("sort", "")
    filters = _read_filters_from(cq)
    if query:
        results = search_documents(query, filters or None, sort=sort)
    elif filters:
        results = filter_documents(filters, sort=sort)
    else:
        results = filter_documents({}, sort=sort)

    codes = list(results.values_list("code", flat=True))
    if doc.code not in codes:
        return nav
    idx = codes.index(doc.code)
    ctx_q = urlencode({"ctx": ctx})
    if idx > 0:
        nav["prev_url"] = reverse("catalog:document_detail", args=[codes[idx - 1]]) + "?" + ctx_q
    if idx < len(codes) - 1:
        nav["next_url"] = reverse("catalog:document_detail", args=[codes[idx + 1]]) + "?" + ctx_q
    nav["back_url"] = reverse("catalog:search") + "?" + ctx
    nav["pos"] = idx + 1
    nav["total"] = len(codes)
    return nav


def document_detail(request, code):
    """Detalhes de um documento."""
    doc = get_object_or_404(Document, code=code, status="a")

    # Materiais relacionados: mesmo Assunto (fallback Categoria), exclui o próprio.
    # Acaba com o "beco sem saída" no fim da leitura.
    relacionados = []
    if doc.assunto_id:
        relacionados = list(
            Document.objects.filter(status="a", assunto_id=doc.assunto_id)
            .exclude(pk=doc.pk).order_by("-created", "-pk")[:4]
        )
    if not relacionados and doc.category_id:
        relacionados = list(
            Document.objects.filter(status="a", category_id=doc.category_id)
            .exclude(pk=doc.pk).order_by("-created", "-pk")[:4]
        )

    nav = _resultado_navegacao(doc, request.GET.get("ctx", "").strip())

    return render(request, "document_detail.html", {
        "document": doc,
        "relacionados": relacionados,
        "nav": nav,
    })


def collection_list(request):
    """As 4 coleções v6 (derivadas do Tipo de Informação) com contagem real."""
    colecoes_v6 = colecao_v6_overview()
    return render(request, "collection_list.html", {
        "colecoes_v6": colecoes_v6,
        "cards": [_card_colecao(c) for c in colecoes_v6],
    })


def collection_detail(request, topic_id):
    """Detalhes de uma coleção com subcoleções e documentos."""
    from django.db.models import Count

    topic = get_object_or_404(Topic, id=topic_id)
    subcollections_qs = Topic.objects.filter(parent_id=topic.id).order_by("name")
    page_number = request.GET.get("page", 1)

    # Documentos da coleção e subcoleções
    topic_ids = [topic.id] + list(subcollections_qs.values_list("id", flat=True))
    documents = Document.objects.filter(status="a", topic_id__in=topic_ids).order_by("-created", "-pk")

    paginator = Paginator(documents, settings.SEARCH_RESULTS_PER_PAGE)
    page_obj = paginator.get_page(page_number)

    # Contagem por subcoleção (única query)
    docs_by_topic = dict(
        Document.objects.filter(status="a", topic_id__in=topic_ids)
        .values_list("topic_id")
        .annotate(c=Count("id"))
        .values_list("topic_id", "c")
    )
    subcollections = [
        {"topic": sub, "doc_count": docs_by_topic.get(sub.id, 0)}
        for sub in subcollections_qs
    ]
    # Ordenar por contagem desc, depois alfabético
    subcollections.sort(key=lambda s: (-s["doc_count"], s["topic"].name))
    # Versão filtrada (>0) para a UI; mantemos a lista completa para
    # `topic_ids` e contagem total dos documentos da coleção.
    subcollections_visiveis = [s for s in subcollections if s["doc_count"] > 0]

    # Cards de subcoleção via o componente unificado (_collection_card.html).
    subcollection_cards = [
        {
            "href": reverse("catalog:collection_detail", args=[s["topic"].id]),
            "color": "c-blue", "icon": "fi-layers",
            "label": s["topic"].name, "desc": s["topic"].description or "",
            "count": s["doc_count"],
        }
        for s in subcollections_visiveis
    ]

    # Breadcrumb
    breadcrumb = []
    if topic.parent_id != 0:
        parent = Topic.objects.filter(id=topic.parent_id).first()
        if parent:
            breadcrumb.append(parent)
    breadcrumb.append(topic)

    return render(request, "collection_detail.html", {
        "topic": topic,
        "subcollections": subcollections,
        "subcollections_visiveis": subcollections_visiveis,
        "subcollection_cards": subcollection_cards,
        "page_obj": page_obj,
        "breadcrumb": breadcrumb,
        "total_docs": paginator.count,
    })


def download(request, code):
    """Download de documento via arquivo local ou redirecionamento."""
    doc = get_object_or_404(Document, code=code, status="a")

    if doc.is_remote and doc.acesso_eletronico:
        from django.shortcuts import redirect
        return redirect(doc.acesso_eletronico)

    import os
    archive_dir = settings.NOURAU_ARCHIVE_DIR
    # Nou-Rau organiza arquivos por topic_id/code
    file_path = os.path.join(archive_dir, str(doc.topic_id), doc.code, doc.filename)

    if not os.path.exists(file_path):
        raise Http404("Arquivo não encontrado.")

    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=doc.filename)


def curadoria(request):
    """Rota legada: a Curadoria foi unificada na página de Coleções. Redireciona
    links externos/marcados para /colecoes/ (a página agora explica a organização
    do acervo abaixo dos cards das coleções)."""
    from django.shortcuts import redirect
    return redirect("catalog:collection_list")


def about(request):
    """Sobre o LILP e a biblioteca."""
    return render(request, "about.html")


# =====================================================================
# Páginas institucionais e legais (eMAG 3.1, LAI, LGPD, Lei 13.460/2017)
# Conteúdo em rascunho — aviso visual em cada página solicita validação
# pelo Encarregado de Dados (DPO) e pela Procuradoria/Assessoria Jurídica.
# =====================================================================

def transparencia(request):
    """Página de Transparência — atende LAI (Lei 12.527/2011)."""
    return render(request, "legal/transparencia.html")


def acessibilidade(request):
    """Compromisso de acessibilidade — eMAG 3.1 / WCAG 2.0 AA."""
    return render(request, "legal/acessibilidade.html")


def politica_privacidade(request):
    """Política de Privacidade — atende LGPD (Lei 13.709/2018)."""
    return render(request, "legal/politica_privacidade.html")


def politica_cookies(request):
    """Política de Cookies — atende LGPD e Marco Civil (Lei 12.965/2014)."""
    return render(request, "legal/politica_cookies.html")


def mapa_site(request):
    """Mapa do site — recomendação eMAG 3.1."""
    return render(request, "legal/mapa_site.html")


def fale_conosco(request):
    """Canal de contato — Lei 13.460/2017 (Direitos do Usuário)."""
    return render(request, "legal/fale_conosco.html")
