"""
Faceted aggregation: para cada filtro disponível, calcula a contagem de documentos
que satisfazem TODOS os outros filtros aplicados — exceto ele mesmo. Isso permite
que o usuário troque um valor de filtro sem ficar com lista vazia.
"""

import unicodedata

from django.db.models import Count, Max, Min

from .models import (
    Assunto,
    Document,
    Microcategoria,
    NrCategory,
    Subcategoria,
    TypeInformation,
)
from .search import _apply_filters, search_documents
from .taxonomy_v6 import COLECOES_V6, TEMAS_DESTAQUE, colecao_v6_for_tipo


def _sort_key(nome):
    """Chave de ordenação alfabética acento-insensível (pt): 'Á' ordena junto
    de 'a', não depois de 'z'. Usada nas facetas planas (Assunto/Natureza/Tipo)."""
    decomp = unicodedata.normalize("NFKD", str(nome or ""))
    return "".join(c for c in decomp if not unicodedata.combining(c)).casefold()


def _facet_counts(filters, exclude_key, group_by):
    """Conta documentos agrupados por `group_by`, aplicando filters menos `exclude_key`."""
    f = {k: v for k, v in (filters or {}).items() if k != exclude_key}
    qs = Document.objects.filter(status="a")
    qs = _apply_filters(qs, f)
    return (
        qs.exclude(**{f"{group_by}__isnull": True})
        .values(group_by)
        .annotate(count=Count("id"))
        .order_by("-count")
    )


def _attach_names(rows, key, model, label_field="nome"):
    """Recebe rows [{key: id, count: n}] e devolve [{id, nome, count}] com nomes resolvidos."""
    ids = [r[key] for r in rows if r.get(key)]
    if not ids:
        return []
    name_by_id = {obj.pk: getattr(obj, label_field) for obj in model.objects.filter(pk__in=ids)}
    out = []
    for r in rows:
        rid = r.get(key)
        if rid and rid in name_by_id:
            out.append({"id": rid, "nome": name_by_id[rid], "count": r["count"]})
    return out


def _string_facet(filters, exclude_key, field):
    """Faceta para campo string. Retorna [{value, nome, count}] com chaves uniformes."""
    f = {k: v for k, v in (filters or {}).items() if k != exclude_key}
    qs = Document.objects.filter(status="a")
    qs = _apply_filters(qs, f)
    rows = (
        qs.exclude(**{f"{field}__isnull": True})
        .exclude(**{field: ""})
        .values(field)
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    # `id` espelha `value` para uniformizar com as facetas de modelo
    # (o template usa sempre opt.id como valor do checkbox). Ordem alfabética.
    out = [{"id": r[field], "value": r[field], "nome": r[field], "count": r["count"]} for r in rows]
    out.sort(key=lambda o: _sort_key(o["nome"]))
    return out


def _colecao_v6_facet(filters):
    """Contagem por Coleção v6 (derivada do Tipo de Informação), faceta-aware."""
    f = {k: v for k, v in (filters or {}).items() if k != "colecao_v6"}
    qs = Document.objects.filter(status="a")
    qs = _apply_filters(qs, f)
    rows = (
        qs.exclude(typeinform_id__isnull=True)
        .values("typeinform_id")
        .annotate(count=Count("id"))
    )
    type_names = {ti.id: ti.name for ti in TypeInformation.objects.all()}
    counts = {c["nome"]: 0 for c in COLECOES_V6}
    for r in rows:
        nome = colecao_v6_for_tipo(type_names.get(r["typeinform_id"]))["nome"]
        counts[nome] += r["count"]
    return [
        {
            "id": c["slug"], "nome": c["nome"], "count": counts[c["nome"]],
            "icon": c["icon"], "color": c["color"], "descricao": c.get("descricao", ""),
        }
        for c in COLECOES_V6
    ]


def colecao_v6_overview():
    """As 4 coleções v6 com contagem total — usada na home e na página de coleções."""
    return _colecao_v6_facet(None)


# ---------------------------------------------------------------------------
# Categorias processuais (macroetapas) p/ a seção "Comece pela etapa da
# contratação" na home. A ordem segue a sequência da Lei 14.133/21: o PCA inicia
# o ciclo anual (Art. 12, VII) e as três macrofases vêm na ordem do processo —
# Planejamento/Fase Preparatória (Art. 18) → Seleção do Fornecedor (Arts. 17, 28,
# 72-78) → Gestão Contratual (Art. 117+). "Ciclo Completo" e "Conteúdos
# Transversais" atravessam todas as fases → grupo à parte. Chaves = nome canônico
# do seed (07-categories.sql).
# ---------------------------------------------------------------------------
_CAT_HOME_NUCLEO = (
    "PLANO DE CONTRATAÇÕES ANUAL (PCA)",
    "PLANEJAMENTO/FASE PREPARATÓRIA",
    "SELEÇÃO DO FORNECEDOR",
    "GESTÃO CONTRATUAL",
)
_CAT_HOME_TRANSVERSAL = (
    "CICLO COMPLETO DA CONTRATAÇÃO",
    "CONTEÚDOS TRANSVERSAIS",
)
_CAT_HOME_ICON = {
    "PLANO DE CONTRATAÇÕES ANUAL (PCA)": "fi-calendar",
    "PLANEJAMENTO/FASE PREPARATÓRIA": "fi-file-text",
    "SELEÇÃO DO FORNECEDOR": "fi-scale",
    "GESTÃO CONTRATUAL": "fi-shield",
    "CICLO COMPLETO DA CONTRATAÇÃO": "fi-layers",
    "CONTEÚDOS TRANSVERSAIS": "fi-bookmark",
}
_CAT_HOME_COLOR = {
    "PLANO DE CONTRATAÇÕES ANUAL (PCA)": "c-blue",
    "PLANEJAMENTO/FASE PREPARATÓRIA": "c-petrol",
    "SELEÇÃO DO FORNECEDOR": "c-red",
    "GESTÃO CONTRATUAL": "c-bluedark",
    "CICLO COMPLETO DA CONTRATAÇÃO": "c-yellow",
    "CONTEÚDOS TRANSVERSAIS": "c-green",
}


def categorias_overview():
    """Categorias processuais (macroetapas) com contagem real, arranjadas p/ a
    seção 'Comece pela etapa da contratação' da home. Espelha
    colecao_v6_overview(): devolve `nucleo` (4 etapas sequenciais) e `transversal`
    (2 visões), cada item com id, nome cru, descrição (do seed), contagem, ícone e
    cor. A contagem é "documentos com aquele category_id" — mesmo critério da
    faceta de Categoria. Categorias fora das listas acima entram no fim do núcleo,
    para nada sumir se a taxonomia mudar.
    """
    counts = dict(
        Document.objects.filter(status="a")
        .exclude(category_id__isnull=True)
        .values_list("category_id")
        .annotate(c=Count("id"))
        .values_list("category_id", "c")
    )
    by_name = {c.name: c for c in NrCategory.objects.all()}

    def _row(cat):
        return {
            "id": cat.id,
            "nome": cat.name,
            "descricao": cat.description or "",
            "count": counts.get(cat.id, 0),
            "icon": _CAT_HOME_ICON.get(cat.name, "fi-layers"),
            "color": _CAT_HOME_COLOR.get(cat.name, "c-blue"),
        }

    nucleo = [_row(by_name[n]) for n in _CAT_HOME_NUCLEO if n in by_name]
    transversal = [_row(by_name[n]) for n in _CAT_HOME_TRANSVERSAL if n in by_name]
    conhecidos = set(_CAT_HOME_NUCLEO) | set(_CAT_HOME_TRANSVERSAL)
    extras = [_row(c) for name, c in by_name.items() if name not in conhecidos]
    nucleo += sorted(extras, key=lambda r: r["id"])
    return {"nucleo": nucleo, "transversal": transversal}


def tema_busca(tema):
    """Filtro de busca de um tema em destaque: devolve (params_querystring, count).

    Se o tema aponta para um Assunto curado (`assunto_nome`) que existe no banco,
    a busca é por Assunto — a contagem do card passa a bater com a faceta lateral
    de Assuntos e com a lista exibida ao clicar. Caso contrário, cai para busca
    textual full-text (`query`), usada quando não há Assunto correspondente.
    """
    nome = tema.get("assunto_nome")
    if nome:
        aid = Assunto.objects.filter(nome=nome).values_list("id", flat=True).first()
        if aid:
            count = Document.objects.filter(status="a", assunto_id=aid).count()
            return {"assunto_id": aid}, count
    return {"q": tema["query"]}, search_documents(tema["query"]).count()


def cards_tematicos_overview():
    """Temas em destaque (buscas temáticas) com contagem e parâmetros de busca.

    A contagem e o link do card usam o MESMO filtro (Assunto curado ou texto),
    então o número do card bate com a página de busca ao clicar. `descricao` vem
    do `card_desc` em Linguagem Simples.
    """
    out = []
    for t in TEMAS_DESTAQUE:
        params, count = tema_busca(t)
        out.append({
            "slug": t["slug"], "label": t["label"], "params": params,
            "icon": t["icon"], "color": t["color"], "descricao": t["card_desc"],
            "count": count,
        })
    return out


def _tipos_por_colecao_facet(filters):
    """Tipos de Informação agrupados por Coleção v6, em cascata. A seção é
    exibida na interface como 'Coleção' (substitui a faceta simples antiga).

    Cada grupo traz `slug` (para 'Toda a coleção' = colecao_v6), `total`
    (soma dos tipos = contagem da coleção, pois cada doc tem 1 tipo), `active`
    (abrir o <details> quando a coleção ou um de seus tipos está selecionado)
    e os `tipos`. As 4 coleções aparecem sempre, como na faceta antiga."""
    flat = _attach_names(
        list(_facet_counts(filters, "typeinform_id", "typeinform_id")),
        "typeinform_id", TypeInformation, label_field="name",
    )
    by_col = {c["nome"]: [] for c in COLECOES_V6}
    for t in flat:
        nome = colecao_v6_for_tipo(t["nome"])["nome"]
        by_col[nome].append(t)
    for tipos in by_col.values():  # ordem alfabética dentro de cada coleção
        tipos.sort(key=lambda t: _sort_key(t["nome"]))

    f = filters or {}
    sel_col = f.get("colecao_v6")
    sel_tipos = f.get("typeinform_id") or []
    if not isinstance(sel_tipos, (list, tuple, set)):
        sel_tipos = [sel_tipos]
    sel_tipos = {str(t) for t in sel_tipos}

    out = []
    for c in COLECOES_V6:
        tipos = by_col[c["nome"]]
        total = sum(t["count"] for t in tipos)
        active = (sel_col == c["slug"]) or any(str(t["id"]) in sel_tipos for t in tipos)
        out.append({
            "colecao": c["nome"], "slug": c["slug"], "total": total,
            "toda_disabled": total == 0, "active": active, "tipos": tipos,
        })
    return out


def _categorias_hierarquia_facet(filters):
    """Categoria → Subcategoria → Microcategoria — taxonomia COMPLETA sempre.

    Mostra todos os nós da árvore (mesmo com 0 documentos, exibidos `disabled`/
    cinza). A poluição é controlada pela expansão aninhada (<details>): cada
    Subcategoria que tem Microcategorias vira uma caixa expansível, no mesmo
    padrão visual da Categoria.

    Contagens ESTÁVEIS: os três níveis contam no MESMO contexto (todos os
    filtros, EXCETO a própria hierarquia) — os números não "pulam" ao navegar.
    A contagem de cada nó é "documentos naquele ramo"; a soma dos filhos pode
    ser menor que o pai (docs classificados só no nível acima).

    `open`/`active` ficam True quando o nó ou um descendente é o filtro
    selecionado — o template usa para abrir os <details>.
    """
    f = filters or {}
    # Base comum a todos os níveis: remove a hierarquia → contagens estáveis.
    base = {k: v for k, v in f.items() if k not in ("category_id", "subcategoria_id", "microcategoria_id")}

    def counts_by(group_by):
        qs = _apply_filters(Document.objects.filter(status="a"), base)
        rows = qs.exclude(**{f"{group_by}__isnull": True}).values(group_by).annotate(count=Count("id"))
        return {r[group_by]: r["count"] for r in rows}

    cat_counts = counts_by("category_id")
    sub_counts = counts_by("subcategoria_id")
    mic_counts = counts_by("microcategoria_id")

    cats = {c.id: c for c in NrCategory.objects.all()}
    subs_by_cat = {}
    for s in Subcategoria.objects.all():  # Meta.ordering = (ordem, nome)
        subs_by_cat.setdefault(s.category_id, []).append(s)
    mics_by_sub = {}
    for m in Microcategoria.objects.all():
        mics_by_sub.setdefault(m.subcategoria_id, []).append(m)

    sel_cat, sel_sub, sel_mic = f.get("category_id"), f.get("subcategoria_id"), f.get("microcategoria_id")

    out = []
    for cat_id in sorted(cats):  # taxonomia completa, na ordem do ciclo (id 1..6)
        cat = cats[cat_id]
        cat_count = cat_counts.get(cat_id, 0)
        cat_open = str(cat_id) == (sel_cat or "")
        subcategorias = []
        for s in subs_by_cat.get(cat_id, []):
            scnt = sub_counts.get(s.id, 0)
            sub_open = str(s.id) == (sel_sub or "")
            micros = []
            for m in mics_by_sub.get(s.id, []):
                mcnt = mic_counts.get(m.id, 0)
                if str(m.id) == (sel_mic or ""):
                    sub_open = True
                micros.append({"id": m.id, "nome": m.nome, "count": mcnt, "disabled": mcnt == 0})
            if sub_open:
                cat_open = True
            subcategorias.append({
                "id": s.id, "nome": s.nome, "count": scnt, "disabled": scnt == 0,
                "open": sub_open, "has_micros": bool(micros), "microcategorias": micros,
            })
        out.append({
            "id": cat.id, "nome": cat.name, "count": cat_count, "disabled": cat_count == 0,
            "active": cat_open, "subcategorias": subcategorias,
        })
    return out


def compute_facets(filters):
    """Devolve as facetas que a página de busca renderiza, dado o conjunto de filtros.

    Calcula só o que o `search.html` consome (Coleção, Categorias, Assunto,
    Natureza e os limites de Ano). As demais facetas planas (categorias/sub/
    micro/coleções/tipos/complexidade/permissão) eram servidas pelo antigo
    endpoint /api/facets/ — removido por não ter consumidor.
    """
    facets = {}

    # Coleção (Tipos de Informação agrupados por Coleção v6, em cascata)
    facets["tipos_por_colecao"] = _tipos_por_colecao_facet(filters)
    # Categorias em cascata (accordion <details>): Categoria → Sub → Micro
    facets["categorias_hierarquia"] = _categorias_hierarquia_facet(filters)
    # Assunto (eixo transversal, multi-select)
    facets["assuntos"] = sorted(
        _attach_names(
            list(_facet_counts(filters, "assunto_id", "assunto_id")), "assunto_id", Assunto
        ),
        key=lambda a: _sort_key(a["nome"]),
    )
    # Natureza (objeto da contratação, v6)
    facets["naturezas"] = _string_facet(filters, "natureza", "natureza")

    # Ano: limites ESTÁVEIS sobre o acervo inteiro (NÃO o conjunto filtrado), para
    # os campos De/Até não "pularem" ao aplicar outros filtros (evita o salto).
    bounds = Document.objects.filter(status="a", ano__isnull=False).aggregate(
        min=Min("ano"), max=Max("ano")
    )
    facets["ano_bounds"] = {
        "min": bounds["min"] or 2000,
        "max": bounds["max"] or 2025,
    }

    return facets
