"""Os dois eixos no cartão e na página do documento (T2, set/2026) — sem banco.

O subsecretário leu "Governança" no cartão e concluiu que a classificação
estava errada, quando a etapa processual — que respondia à objeção — não
estava à vista. O rodapé do cartão passa a mostrar "Etapa: … · Assunto: …";
a página do documento ganha o badge "Etapa" e a fórmula da classificação.
A tag que resolve os nomes usa só os mapas cacheados (zero query por cartão).
"""

from pathlib import Path
from types import SimpleNamespace

from catalog.templatetags import catalog_tags
from catalog.templatetags.catalog_tags import classificacao_card

TEMPLATES = Path(__file__).resolve().parents[2] / "templates"


def _template(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def _mapas(monkeypatch):
    cats = {4: "SELEÇÃO DO FORNECEDOR", 3: "PLANEJAMENTO/FASE PREPARATÓRIA"}
    monkeypatch.setattr(catalog_tags, "_category_names", lambda: cats)
    monkeypatch.setattr(catalog_tags, "_subcategoria_names", lambda: {7: "LICITAÇÃO", 4: "ETP"})
    monkeypatch.setattr(catalog_tags, "_assunto_names", lambda: {6: "Governança"})


def test_classificacao_card_resolve_os_dois_eixos(monkeypatch):
    _mapas(monkeypatch)
    doc = SimpleNamespace(category_id=4, subcategoria_id=7, microcategoria_id=2, assunto_id=6)
    assert classificacao_card(doc) == {"etapa": "Seleção do Fornecedor › Licitação", "assunto": "Governança"}


def test_classificacao_card_subcategoria_usa_rotulo_curado(monkeypatch):
    _mapas(monkeypatch)
    doc = SimpleNamespace(category_id=3, subcategoria_id=4, assunto_id=6)
    assert classificacao_card(doc)["etapa"] == "Planejamento/Fase Preparatória › Estudo Técnico Preliminar (ETP)"


def test_classificacao_card_sem_categoria_ou_sem_assunto(monkeypatch):
    _mapas(monkeypatch)
    assert classificacao_card(SimpleNamespace(category_id=None, subcategoria_id=None, assunto_id=6)) == {
        "etapa": "", "assunto": "Governança",
    }
    assert classificacao_card(SimpleNamespace(category_id=4, subcategoria_id=None, assunto_id=None)) == {
        "etapa": "Seleção do Fornecedor", "assunto": "",
    }
    # subcategoria órfã (sem categoria) não vira etapa; ids desconhecidos não quebram
    assert classificacao_card(SimpleNamespace(category_id=99, subcategoria_id=7, assunto_id=99)) == {
        "etapa": "", "assunto": "",
    }


def test_classificacao_card_e_pura_nao_toca_propriedades_do_documento():
    # Só ids + mapas cacheados: nada de doc.category/doc.subcategoria (1 query cada).
    nomes = classificacao_card.__wrapped__.__code__.co_names if hasattr(classificacao_card, "__wrapped__") \
        else classificacao_card.__code__.co_names
    for proibido in ("category", "subcategoria", "assunto", "objects"):
        assert proibido not in nomes, proibido
    for exigido in ("_category_names", "_subcategoria_names", "_assunto_names"):
        assert exigido in nomes, exigido


def test_cartao_mostra_etapa_e_assunto():
    t = _template("_partials/_doc_card.html")
    assert "classificacao_card doc as" in t
    assert "Etapa:" in t and "Assunto:" in t
    assert "doc-card__eixos" in t and "doc-card__assunto" in t   # mesma tipografia do rodapé
    assert "cl.etapa" in t and "cl.assunto" in t
    assert "{{ cv.nome }}" in t                                     # fallback: nome da coleção


def test_documento_tem_badge_etapa_e_formula():
    t = _template("document_detail.html")
    assert "Etapa: {{ cl.etapa }}" in t
    assert "fi-layers" in t
    assert "Etapa (categoria processual)" in t
    assert "Todo material recebe" in t and "coleção" in t and "assunto" in t and "natureza" in t
    assert "classificacao-formula" in t


def test_hints_das_facetas_amarram_etapa_e_assunto():
    t = _template("search.html")
    assert "A etapa da contratação em que o material se aplica (categoria processual)." in t
    assert "O tema tratado no documento (um documento tem um assunto principal)." in t
    # títulos das facetas não mudam
    assert "<h3>Categorias</h3>" in t and "<h3>Assunto</h3>" in t
