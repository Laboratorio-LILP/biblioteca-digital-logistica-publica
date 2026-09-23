"""Facetas planas dirigidas pela TAXONOMIA, não pelas contagens (17/09/2026) — sem banco.

Bernardo: "a barra de filtros do Acervo ainda não reflete a taxonomia da Lina —
só existem 14 assuntos". O banco já tinha os 16 da v12; a faceta de Assunto
nascia das contagens de documentos, e os dois Assuntos novos (0 materiais até a
recarga da planilha v12) não existiam na barra. Agora Assunto, Natureza e os
Tipos da cascata de Coleção listam o vocabulário inteiro, com 0 → `disabled`,
como a cascata de Categorias já fazia.
"""

from pathlib import Path
from types import SimpleNamespace

from catalog import facets
from catalog.models import NATUREZA_CHOICES

REPO = Path(__file__).resolve().parents[3]
TEMPLATES = REPO / "portal" / "templates"
NS = SimpleNamespace


def test_assuntos_lista_a_taxonomia_inteira_com_zero_desabilitado(monkeypatch):
    todos = [NS(id=1, nome="Governança"), NS(id=2, nome="Logística Pública Internacional"),
             NS(id=3, nome="Aspectos Jurídicos e Regulatórios")]
    monkeypatch.setattr(facets, "Assunto", NS(objects=NS(all=lambda: todos)))
    monkeypatch.setattr(facets, "_facet_counts", lambda *a, **k: [{"assunto_id": 1, "count": 161},
                                                                 {"assunto_id": 3, "count": 267}])
    out = facets._assuntos_facet(None, {})
    assert [o["nome"] for o in out] == ["Aspectos Jurídicos e Regulatórios", "Governança",
                                        "Logística Pública Internacional"]      # alfabética
    por_nome = {o["nome"]: o for o in out}
    assert por_nome["Governança"] == {"id": 1, "nome": "Governança", "count": 161, "disabled": False}
    assert por_nome["Logística Pública Internacional"]["count"] == 0
    assert por_nome["Logística Pública Internacional"]["disabled"] is True     # aparece, cinza


def test_naturezas_lista_os_valores_canonicos_e_mantem_extras_com_docs(monkeypatch):
    monkeypatch.setattr(facets, "_string_facet", lambda *a, **k: [
        {"id": "Contratação de Serviços", "value": "Contratação de Serviços",
         "nome": "Contratação de Serviços", "count": 24},
        {"id": "Valor Legado", "value": "Valor Legado", "nome": "Valor Legado", "count": 2},
    ])
    out = facets._naturezas_facet(None, {})
    nomes = [o["nome"] for o in out]
    assert set(nomes) == {v for v, _ in NATUREZA_CHOICES} | {"Valor Legado"}
    assert nomes == sorted(nomes, key=facets._sort_key)
    por = {o["nome"]: o for o in out}
    assert por["Contratação de Serviços"]["disabled"] is False
    assert por["Contratação de Materiais"] == {"id": "Contratação de Materiais", "value": "Contratação de Materiais",
                                               "nome": "Contratação de Materiais", "count": 0, "disabled": True}
    assert por["Valor Legado"]["disabled"] is False                            # legado só enquanto tiver docs


def test_tipos_por_colecao_mostra_o_vocabulario_v12_e_os_legados_com_docs(monkeypatch):
    # banco: Boletins (52 docs), Documentos Normativos (7, retirado na v12), Acórdão/Acórdãos (0, duas grafias)
    tabela = [NS(id=10, name="Boletins"), NS(id=11, name="Documentos Normativos"),
              NS(id=12, name="Acórdão"), NS(id=13, name="Acórdãos"), NS(id=14, name="Súmulas"),
              NS(id=15, name="Deliberações")]
    monkeypatch.setattr(facets, "TypeInformation", NS(objects=NS(all=lambda: tabela)))
    monkeypatch.setattr(facets, "_facet_counts", lambda *a, **k: [{"typeinform_id": 10, "count": 52},
                                                                 {"typeinform_id": 11, "count": 7}])
    monkeypatch.setattr(facets, "_attach_names", lambda rows, key, model, label_field="nome": [
        {"id": 10, "nome": "Boletins", "count": 52}, {"id": 11, "nome": "Documentos Normativos", "count": 7}])
    out = facets._tipos_por_colecao_facet(None, {})
    juris = next(g for g in out if g["colecao"] == "Jurisprudência")
    por = {t["nome"]: t for t in juris["tipos"]}
    assert por["Boletins"]["count"] == 52 and por["Boletins"]["disabled"] is False
    assert por["Documentos Normativos"]["count"] == 7 and por["Documentos Normativos"]["disabled"] is False
    assert por["Acórdãos"] == {"id": 13, "nome": "Acórdãos", "count": 0, "disabled": True}  # grafia exata
    assert por["Súmulas"]["disabled"] and por["Deliberações"]["disabled"]
    assert "Acórdão" not in por                                                # grafia legada não duplica
    assert [t["nome"] for t in juris["tipos"]] == sorted(por, key=facets._sort_key)
    assert juris["total"] == 59


def test_compute_facets_usa_as_facetas_por_taxonomia():
    src = facets.compute_facets.__code__.co_names
    assert "_assuntos_facet" in src and "_naturezas_facet" in src


def test_templates_renderizam_o_disabled_nas_facetas_planas():
    opts = (TEMPLATES / "_partials" / "_facet_options.html").read_text(encoding="utf-8")
    assert '_partials/_cat_toggle.html' in opts and "disabled=opt.disabled" in opts
    busca = (TEMPLATES / "search.html").read_text(encoding="utf-8")
    assert 'param="typeinform_id" id=tipo.id nome=tipo.nome count=tipo.count disabled=tipo.disabled' in busca
