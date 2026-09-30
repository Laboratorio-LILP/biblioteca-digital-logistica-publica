r"""Renderiza os templates do Portal BDLP em HTML estático para preview
offline — sem Docker, sem PostgreSQL, sem o servidor Django ativo.

Por que existe: a máquina de desenvolvimento pode não ter Docker
disponível. Como os modelos do catálogo são unmanaged (mapeiam
tabelas do Nou-Rau via PHP), não dá para usar Django + SQLite com
um simples `migrate`. Aqui usamos render_to_string() com contexto
mock — não executa queries.

O JavaScript (main.js) e o CSS (style.css + sp-design-system.css)
são servidos como estáticos e funcionam normalmente: banner LGPD,
controles de fonte/contraste, atalhos Alt+1..4 e menu hambúrguer
podem ser testados.

Uso (PowerShell):
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install "django>=5.1,<6.0" django-environ whitenoise django-csp
    py tools/preview_render.py
    py -m http.server 8765 --directory preview_output

Depois abra http://localhost:8765 no navegador.
"""
from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTAL_DIR = ROOT / "portal"
sys.path.insert(0, str(PORTAL_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portal.preview_settings")

import django  # noqa: E402

django.setup()

from catalog.taxonomy_v6 import (  # noqa: E402
    ASSUNTOS_COMPARACOES, CAMPOS_CLASSIFICACAO, EXEMPLOS_CLASSIFICACAO,
)

from django.template.loader import render_to_string  # noqa: E402
from django.test import RequestFactory  # noqa: E402


class M:
    """Bag de atributos genérica — substitui modelos para o preview."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------
# Dados mock — equivalentes ao que views/context_processor passariam.
# ---------------------------------------------------------------------

COLLECTIONS = [
    M(id=1, name="Eventos",
      description="Conferências, seminários e workshops sobre logística pública."),
    M(id=2, name="Livros Digitais",
      description="Livros, e-books e publicações digitalizadas."),
    M(id=3, name="Materiais Pedagógicos",
      description="Apostilas, manuais, tutoriais e relatórios."),
    M(id=4, name="Trabalhos Acadêmicos",
      description="Dissertações, teses e trabalhos de conclusão."),
]


def _mock_doc(i: int) -> M:
    return M(
        code=f"DOC{i:03d}",
        title=f"Documento exemplo {i} — análise da Lei 14.133/2021",
        autor_principal="Autor Exemplo",
        source="Universidade Estadual de Campinas",
        abstract=("Resumo placeholder para preview offline. O texto real virá "
                  "do banco PostgreSQL do Nou-Rau quando o portal estiver "
                  "conectado em produção."),
        tipologia="Normativo" if i % 2 == 0 else "Acadêmico",
        complexidade=["Baixa", "Média", "Alta"][i % 3],
        keywords="licitação, contratos, logística pública",
        created=datetime(2026, 5, i + 1),
    )


RECENT_DOCS = [_mock_doc(i) for i in range(1, 6)]


PAGINATOR_VAZIO = M(count=0, num_pages=1)
PAGE_OBJ_VAZIO = M(
    object_list=[],
    number=1,
    paginator=PAGINATOR_VAZIO,
    has_previous=False,
    has_next=False,
    has_other_pages=lambda: False,
    previous_page_number=lambda: 0,
    next_page_number=lambda: 2,
)


BASE_CONTEXT = {
    "site_year": 2026,
    "current_url_name": "",
    "total_documentos": 508,
    "total_colecoes": 4,
    # nomes legados usados em alguns templates
    "total_docs": 508,
    "total_collections": 4,
}


# ---------------------------------------------------------------------
# Páginas a gerar — (template, rota, contexto extra).
# A rota define o caminho no preview_output (ex: "/sobre/" → sobre/index.html).
# ---------------------------------------------------------------------

PAGES = [
    ("home.html", "/", {
        "current_url_name": "home",
        "collections": COLLECTIONS,
        "recent_docs": RECENT_DOCS,
    }),
    ("about.html", "/sobre/", {
        "current_url_name": "about",
    }),
    ("legal/transparencia.html", "/transparencia/", {
        "current_url_name": "transparencia",
    }),
    ("legal/acessibilidade.html", "/acessibilidade/", {
        "current_url_name": "acessibilidade",
    }),
    ("legal/politica_privacidade.html", "/politica-de-privacidade/", {
        "current_url_name": "politica_privacidade",
    }),
    ("legal/politica_cookies.html", "/politica-de-cookies/", {
        "current_url_name": "politica_cookies",
    }),
    ("legal/mapa_site.html", "/mapa-do-site/", {
        "current_url_name": "mapa_site",
    }),
    ("legal/fale_conosco.html", "/fale-conosco/", {
        "current_url_name": "fale_conosco",
    }),
    ("search.html", "/busca/", {
        "current_url_name": "search",
        "query": "",
        "page_obj": PAGE_OBJ_VAZIO,
        "filters": {},
        "collections": COLLECTIONS,
        "categories": [],
        "tipologias": ["Administrativo", "Informacional", "Jurisprudencial",
                       "Normativo", "Operacional"],
        "complexidades": ["Baixa", "Média", "Alta"],
        "total_results": 0,
    }),
    ("metodologia.html", "/metodologia/", {
        "current_url_name": "metodologia",
        "abas": [
            {"chave": chave, "href": href, "rotulo": rotulo, "titulo": f"{rotulo} — Metodologia",
             "meta": "", "ativa": chave == "conceitos"}
            for chave, href, rotulo in (("conceitos", "/metodologia/", "Conceitos e coleções"),
                                        ("categorias", "/metodologia/categorias/", "Categorias"),
                                        ("assuntos", "/metodologia/assuntos/", "Assuntos"))
        ],
        "aba_ativa": {"chave": "conceitos", "titulo": "Metodologia — Biblioteca Digital de Logística Pública",
                      "meta": ""},
        "campos": CAMPOS_CLASSIFICACAO,
        "exemplo_pratico": dict(EXEMPLOS_CLASSIFICACAO[0], campos_valores=list(
            zip(CAMPOS_CLASSIFICACAO, EXEMPLOS_CLASSIFICACAO[0]["valores"]))),
        "exemplos": [dict(e, campos_valores=list(zip(CAMPOS_CLASSIFICACAO, e["valores"])))
                     for e in EXEMPLOS_CLASSIFICACAO],
        "colecoes": [], "categorias": [], "assuntos": [], "comparacoes": ASSUNTOS_COMPARACOES,
    }),
]


def main() -> int:
    out = ROOT / "preview_output"
    if out.exists():
        # ignore_errors evita PermissionError quando OneDrive segura locks
        # transitórios; arquivos persistentes serão sobrescritos abaixo.
        shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)

    # Copia static/
    static_src = PORTAL_DIR / "static"
    if static_src.exists():
        shutil.copytree(static_src, out / "static", dirs_exist_ok=True)
        print(f"  -> static/ copiado para {out / 'static'}")
    else:
        print(f"  [!] static/ nao encontrado em {static_src}", file=sys.stderr)

    factory = RequestFactory()
    falhas = 0
    sucessos = 0

    for tpl, rota, extra in PAGES:
        request = factory.get(rota)
        ctx = {**BASE_CONTEXT, **extra, "request": request}
        try:
            html = render_to_string(tpl, ctx)
        except Exception as e:
            print(f"  [fail] {tpl:42}  {type(e).__name__}: {e}", file=sys.stderr)
            falhas += 1
            continue

        slug = rota.strip("/")
        target_dir = out if not slug else (out / slug)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "index.html"
        target.write_text(html, encoding="utf-8")
        print(f"  [ok] {tpl:42}  -> {target.relative_to(ROOT)}")
        sucessos += 1

    print(f"\nPreview gerado: {sucessos} ok, {falhas} falha(s).")
    if falhas == 0:
        print(f"Sirva com:  py -m http.server 8765 --directory "
              f"{out.relative_to(ROOT)}")
        print(f"Abra:       http://localhost:8765")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
