"""Definições dos Assuntos e Categorias na interface (T6, set/2026) — sem banco.

O subsecretário pediu "descrição clara do que entra em cada Assunto". A Lina
escreveu as definições (11/09/2026, Caracterizacao_Assuntos_Taxonomia_BDLP.xlsx):
caracterização (curta) e explicação (longa) para os 16 Assuntos. Como
nr_assunto não tem coluna de descrição (portal somente leitura, sem migrations
Django), o texto fica versionado em taxonomy_v6.ASSUNTOS_DESCRICAO, no mesmo
padrão de COLECOES_V6["descricao"]. Categorias reusam nr_category.description.
"""

import re
from pathlib import Path

from catalog import facets, taxonomy_v6
from catalog.taxonomy_v6 import ASSUNTOS_DESCRICAO, descricao_assunto
from catalog.templatetags import catalog_tags

REPO = Path(__file__).resolve().parents[3]
TEMPLATES = REPO / "portal" / "templates"
SEED_ASSUNTOS = REPO / "docker" / "postgres" / "init" / "06-taxonomia.sql"


def _template(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def _assuntos_do_seed():
    sql = SEED_ASSUNTOS.read_text(encoding="utf-8")
    bloco = sql[sql.index("INSERT INTO nr_assunto"):]
    bloco = bloco[: bloco.index(";")]
    return [n for n, _, _ in re.findall(r"\('([^']+)', '([^']+)', (\d+)\)", bloco)]


def test_descricoes_cobrem_exatamente_os_16_assuntos_do_seed():
    seed = _assuntos_do_seed()
    assert len(seed) == 16
    assert set(ASSUNTOS_DESCRICAO) == set(seed)


def test_cada_assunto_tem_curta_e_longa_nao_vazias():
    for nome, d in ASSUNTOS_DESCRICAO.items():
        assert set(d) == {"curta", "longa"}, nome
        assert d["curta"].strip() and d["longa"].strip(), nome
        assert d["curta"].endswith(".") and d["longa"].endswith("."), nome
        assert "  " not in d["curta"] and "  " not in d["longa"], nome   # espaço duplo corrigido
        assert ".." not in d["longa"], nome                               # "públicos.." corrigido


def test_texto_da_curadoria_copiado_verbatim():
    # Amostras do Apêndice A (Lina, 11/09/2026), incluindo as correções autorizadas.
    assert ASSUNTOS_DESCRICAO["Governança"]["curta"] == "Estruturas, princípios e práticas de gestão pública."
    assert "melhoria dos processos da gestão pública" in ASSUNTOS_DESCRICAO["Inovação e Tecnologia"]["longa"]
    assert "melhoriua" not in ASSUNTOS_DESCRICAO["Inovação e Tecnologia"]["longa"]
    assert ASSUNTOS_DESCRICAO["Gestão Estratégica e Desempenho das Contratações"]["curta"] == "Operação e resultados."
    assert ASSUNTOS_DESCRICAO["Logística Pública Internacional"]["longa"] == (
        "Marcos, comparações e cooperação internacional em contratações públicas."
    )
    assert "(1 registro)" not in ASSUNTOS_DESCRICAO["Catálogo eletrônico de Padronização"]["longa"]


def test_fonte_registrada_no_modulo():
    src = Path(taxonomy_v6.__file__).read_text(encoding="utf-8")
    assert "Caracterizacao_Assuntos_Taxonomia_BDLP.xlsx" in src
    assert "11/09/2026" in src
    assert "texto da curadoria" in src.lower()


def test_descricao_assunto_com_fallback_vazio():
    assert descricao_assunto("Governança")["curta"].startswith("Estruturas")
    assert descricao_assunto("Assunto Inexistente") == {"curta": "", "longa": ""}
    assert descricao_assunto(None) == {"curta": "", "longa": ""}
    # filtros de template com o mesmo fallback
    assert catalog_tags.assunto_curta("Transparência") == "Publicidade e acesso à informação."
    assert catalog_tags.assunto_curta("xpto") == ""
    assert catalog_tags.assunto_longa("Integridade").startswith("Trata de programas de integridade")


def test_facets_expoe_o_glossario():
    assert callable(facets.assuntos_glossario) and callable(facets.categorias_glossario)
    assert "ASSUNTOS_DESCRICAO" in facets.assuntos_glossario.__code__.co_names or \
        "descricao_assunto" in facets.assuntos_glossario.__code__.co_names


def test_pagina_de_colecoes_tem_o_glossario():
    t = _template("collection_list.html")
    assert 'id="assuntos"' in t and 'id="categorias"' in t
    assert "glossario__item" in t and "<details" in t
    assert "?assunto_id={{" in t and "?category_id={{" in t
    assert "Hoje são 14 assuntos" not in t                    # contagem chumbada saiu
    # 17/09: a fórmula em caixa alta saiu a pedido do Bernardo; a intro explica em LS
    assert "COLEÇÃO" not in t and "MICROCATEGORIA" not in t
    assert "A curadoria classifica cada documento por coleção, categoria e assunto." in t
    assert "sem filtro nenhum" in t
    # 4 âncoras de seção (o glossário é seção própria) e um único fechamento cinza
    assert t.count("data-sec=") == 4
    assert t.count("sp-section--alt") == 1


def test_links_das_notas_dos_cards_sao_visiveis_como_link():
    # Revisão 14/09: `a { color: inherit; text-decoration: none }` global deixava
    # "Veja o que entra em cada um" igual ao texto cinza ao redor.
    css = (TEMPLATES.parent / "static" / "css" / "portal.css").read_text(encoding="utf-8")
    assert ".org-card__nota a {" in css
    bloco = css[css.index(".org-card__nota a {"):][:160]
    assert "var(--sp-blue)" in bloco and "underline" in bloco


def test_glossario_traz_contagem_subcategorias_e_colunas():
    # Ajuste 16/09 (mesma identidade da plataforma — cards + listas): contagem
    # por assunto, subcategorias em texto corrido sob a categoria, listas em
    # colunas (grupos empilhados, sem coluna vazia) e barra de chegada na âncora.
    t = _template("collection_list.html")
    assert t.count("glossario__count") == 2 and "Sem materiais ainda" in t
    # 17/09: sub e microcategorias vão para o "Saiba mais" da categoria, como árvore
    assert "glossario__subs" not in t and "Subcategorias:" not in t
    assert 'class="glossario__arvore"' in t and "&amp;microcategoria_id={{ m.id }}" in t
    assert "org-grid--3" in t and t.count("org-card__nota") == 2   # os 3 cards de organização ficam
    css = (TEMPLATES.parent / "static" / "css" / "portal.css").read_text(encoding="utf-8")
    assert ".glossario__lista--3col { grid-template-columns: repeat(3" in css
    for morto in (".formula", ".natureza-chip", ".etapa-gl", ".glossario__total"):
        assert morto not in css, morto                             # componentes da v1 descartada


def test_glossario_e_secao_propria_no_padrao_da_plataforma():
    """16/09: a seção "Organização" fazia dois trabalhos (fórmula + cards + 22
    verbetes) e o glossário precisou de título e realce próprios para se separar.
    Virou seção com .section-heading, como toda seção da plataforma; os dois
    grupos são .tema-grupo — o sub-bloco com título em destaque, ícone e âncora
    da home ("Temas em alta") — pedido de 17/09 para os subtítulos ficarem mais
    evidentes sem componente novo."""
    t = _template("collection_list.html")
    css = (TEMPLATES.parent / "static" / "css" / "portal.css").read_text(encoding="utf-8")
    assert 'class="sp-section colecoes-glossario" data-sec="O que significa cada opção"' in t
    assert t.index("colecoes-glossario") > t.index("Como cada documento é classificado")
    assert t.index("colecoes-glossario") < t.index("sp-section--alt")     # antes do fechamento cinza
    assert t.count('<section class="tema-grupo"') == 2                    # sub-bloco padrão da home
    assert t.count('<h3 class="tema-grupo__titulo"') == 2 and t.count("tema-grupo__icone c-petrol") == 2
    assert t.count('class="tema-grupo__intro"') == 2 and "subsection-label" not in t
    assert ".section-heading + .tema-grupo {" in css                       # respiro após o cabeçalho
    # duas seções brancas adjacentes se separam por fio, como na home (.home-etapas)
    assert ".home-etapas, .colecoes-glossario { border-top: var(--border); }" in css
    # nada de título nem de realce de chegada inventados para esta página
    assert "glossario__titulo" not in t and ".glossario__titulo" not in css
    assert ".glossario__grupo" not in css                                 # nenhuma regra própria de grupo
    assert ":target" not in css
    # todo h3 da plataforma é Montserrat 16px (ou 12px nas facetas) — nenhum em Futura
    assert "h3 { font-family: var(--font-heading)" not in css


def test_categorias_glossario_anexa_subcategorias_na_ordem(monkeypatch):
    # Comportamento, sem banco: a lista plana segue núcleo + transversais e cada
    # categoria recebe SUAS subcategorias na ordem em que o modelo as entrega.
    from types import SimpleNamespace

    ns = SimpleNamespace
    monkeypatch.setattr(facets, "categorias_overview", lambda: {
        "nucleo": [{"id": 3, "nome": "PLANEJAMENTO/FASE PREPARATÓRIA", "count": 81}],
        "transversal": [{"id": 6, "nome": "CONTEÚDOS TRANSVERSAIS", "count": 746}],
    })
    monkeypatch.setattr(facets, "Subcategoria", ns(objects=ns(all=lambda: [
        ns(id=4, category_id=3, nome="ETP"),
        ns(id=3, category_id=3, nome="TR"),
        ns(id=99, category_id=42, nome="ÓRFÃ"),          # categoria fora da visão: ignorada
    ])))
    monkeypatch.setattr(facets, "Microcategoria", ns(objects=ns(all=lambda: [
        ns(id=7, subcategoria_id=3, nome="MICRO A"),
        ns(id=8, subcategoria_id=3, nome="MICRO B"),
        ns(id=9, subcategoria_id=99, nome="ÓRFÃ"),
    ])))
    out = facets.categorias_glossario()
    assert [c["id"] for c in out] == [3, 6]
    # (a definição de cada nó — descricao_arvore — é coberta em test_glossario_arvore)
    podar = lambda n: {k: v for k, v in n.items() if k != "descricao"}   # noqa: E731
    assert [podar(sub) | {"microcategorias": [podar(m) for m in sub["microcategorias"]]}
            for sub in out[0]["subcategorias"]] == [
        {"id": 4, "nome": "ETP", "microcategorias": []},
        {"id": 3, "nome": "TR", "microcategorias": [{"id": 7, "nome": "MICRO A"}, {"id": 8, "nome": "MICRO B"}]},
    ]
    assert out[1]["subcategorias"] == []


def test_glossario_usa_o_rotulo_curado_das_subcategorias():
    # "ETP" nu não explica nada; o Acervo e a página do documento já mostram
    # "Estudo Técnico Preliminar (ETP)" via rotulo_sub — o glossário segue igual.
    t = _template("collection_list.html")
    assert "{{ s.nome|rotulo_sub }}" in t and "{{ s.nome|titulo_pt }}" not in t
    assert t.count("Sem materiais ainda") == 2                 # estado zero igual nos dois grupos


def test_busca_linka_o_glossario_nas_facetas():
    t = _template("search.html")
    assert t.count("O que significa cada opção?") == 2
    assert "{% url 'catalog:collection_list' %}#assuntos" in t
    assert "{% url 'catalog:collection_list' %}#categorias" in t
    assert "title=" not in t[t.index("O que significa cada opção?") - 200: t.index("O que significa cada opção?")]


def test_documento_mostra_a_caracterizacao_curta():
    t = _template("document_detail.html")
    assert "assunto_curta" in t
    assert "meta-item__desc" in t
    # a descrição da etapa vem do seed de categorias (description)
    assert "cat.description" in t


def test_textos_da_pagina_de_colecoes_em_linguagem_simples():
    """Revisão de LS de 17/09/2026 (NBR ISO 24495-1): ordem única na página inteira
    (coleção → categoria → assunto, natureza por último), verbos neutros quanto ao
    dispositivo (sem "Clique"), um só nome para a mesma coisa ("tipo de material")
    e "Etapa" nunca nomeando o eixo Categoria sozinha."""
    import re
    t = _template("collection_list.html")
    visivel = re.sub(r"\{#.*?#\}", "", t)
    assert "Clique" not in visivel and "clique" not in visivel
    assert "tipo de informação" not in visivel and visivel.count("tipo de material") == 2
    assert "várias dimensões" not in visivel and "marcas" not in visivel      # abstrações que saíram
    # a mesma ordem nos cards, no glossário e na dica final
    assert visivel.index("<h3>Categoria</h3>") < visivel.index("<h3>Assunto</h3>") < visivel.index("<h3>Natureza</h3>")
    assert visivel.index('id="categorias"') < visivel.index('id="assuntos"')
    assert "primeiro a coleção,\n      depois a categoria, depois o assunto" in visivel
    assert "materiais daquela etapa" not in visivel and "materiais daquela categoria" in visivel
    # frases curtas: nenhuma acima de 25 palavras nos parágrafos de introdução
    for par in re.findall(r'<p class="(?:page__intro|tema-grupo__intro)">(.*?)</p>', visivel, flags=re.S):
        texto = " ".join(re.sub(r"<[^>]+>", " ", par).split())
        for frase in re.split(r"(?<=[.!?])\s+", texto):
            assert len(frase.split()) <= 25, frase
