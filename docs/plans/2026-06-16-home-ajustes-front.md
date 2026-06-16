# Ajustes de front-end na Home — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aplicar os 4 ajustes de front-end na Home do portal BDLP (separar Coleções de Temas, alinhar a seção de Etapas e adicionar "Carregar mais" em Temas em alta com 3 temas novos).

**Architecture:** Templates Django renderizados no servidor + CSS com custom properties + um novo módulo JS vanilla (IIFE, CSP-safe) por **melhoria progressiva** (sem JS, tudo visível; com JS, oculta extras e ativa botões). A fonte única dos temas continua `TEMAS_DESTAQUE`; o mesmo filtro alimenta contagem, link e preview (consistência preservada).

**Tech Stack:** Django (templates), CSS puro (`portal.css`), JS vanilla (`home.js`), pytest (funções puras), Docker (`lilp-bdlp-portal-1`).

**Spec:** [docs/specs/2026-06-16-home-ajustes-front-design.md](../specs/2026-06-16-home-ajustes-front-design.md)

---

## Restrições do projeto (ler antes de começar)

- **CI não sobe Postgres** (`.github/workflows/ci.yml` roda `pytest -v` sem banco). Portanto **os testes do CI cobrem apenas funções puras** (sem `@pytest.mark.django_db`) — a `taxonomy_v6`. As mudanças de view/template/CSS/JS são verificadas no **container vivo** (`lilp-bdlp-portal-1`, já de pé) e no preview do navegador. **Não adicionar testes `django_db`** (quebrariam o CI).
- **ruff** roda em `portal/` (regras E,F,I,N,W; linha 120). Código Python precisa passar.
- **CSP** `script-src 'self'`: JS só com `addEventListener`, sem handlers inline.
- Idioma de comentários/commits: **português**. Commits terminam com o trailer `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Branch já criado: `feat/home-ajustes-front` (a spec já foi commitada nele).

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `portal/catalog/taxonomy_v6.py` | Modificar | +3 entradas em `TEMAS_DESTAQUE` (Item 4) |
| `portal/catalog/tests/test_taxonomy_v6.py` | Modificar | Testes puros das novas entradas |
| `portal/catalog/views.py` | Modificar | `home()`: Coleções/chips separados; slug nos temas (Itens 1, 4) |
| `portal/templates/home.html` | Modificar | Markup dos Itens 1, 2 (sublabel), 4 + `extra_js` |
| `portal/static/css/portal.css` | Modificar | Itens 1, 2, 3, 4 (chips, 2-col, alinhamento, botões) |
| `portal/static/js/home.js` | Criar | "Carregar mais" + revelação por chip (Itens 1, 4) |

---

## Task 1: `TEMAS_DESTAQUE` — 3 temas novos (TDD, CI-safe)

**Files:**
- Modify: `portal/catalog/taxonomy_v6.py:45-71`
- Test: `portal/catalog/tests/test_taxonomy_v6.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao fim de `portal/catalog/tests/test_taxonomy_v6.py` (e incluir `TEMAS_DESTAQUE` no import do topo):

```python
from catalog.taxonomy_v6 import (
    COLECOES_V6,
    TEMAS_DESTAQUE,
    colecao_v6_for_tipo,
    tipos_de_colecao,
)

_TEMA_KEYS = {"slug", "label", "query", "icon", "color", "card_desc", "alta_intro"}


def test_temas_destaque_ordem_e_novos():
    slugs = [t["slug"] for t in TEMAS_DESTAQUE]
    assert slugs == [
        "lei-14133",
        "sustentabilidade",
        "compras-diretas",
        "pregao",
        "registro-precos",
    ]


def test_temas_destaque_entradas_completas():
    for t in TEMAS_DESTAQUE:
        assert _TEMA_KEYS <= set(t), f"faltam chaves em {t.get('slug')}"
        assert t["icon"].startswith("fi-")
        assert t["color"].startswith("c-")
        assert t["query"].strip()
```

(O import substitui o `from catalog.taxonomy_v6 import (COLECOES_V6, colecao_v6_for_tipo, tipos_de_colecao,)` já existente — apenas acrescenta `TEMAS_DESTAQUE`.)

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `docker exec lilp-bdlp-portal-1 python -m pytest catalog/tests/test_taxonomy_v6.py -v`
Expected: FAIL em `test_temas_destaque_ordem_e_novos` (hoje só há 2 temas: a lista de slugs não bate).

- [ ] **Step 3: Adicionar as 3 entradas em `TEMAS_DESTAQUE`**

Em `portal/catalog/taxonomy_v6.py`, dentro da lista `TEMAS_DESTAQUE`, **após** o dict de `sustentabilidade` (antes do `]` que fecha a lista, na linha ~71), inserir:

```python
    {
        "slug": "compras-diretas",
        "label": "Compras Diretas",
        "query": "Compras Diretas",
        "icon": "fi-package",
        "color": "c-red",
        "card_desc": "Compras sem licitação — dispensa e inexigibilidade: "
                     "quando cabem e quais os limites.",
        "alta_intro": "Materiais para entender quando e como contratar sem "
                      "licitação — por dispensa ou inexigibilidade — dentro dos "
                      "limites e cuidados da Lei 14.133/21.",
    },
    {
        "slug": "pregao",
        "label": "Pregão",
        "query": "Pregão",
        "icon": "fi-trending-up",
        "color": "c-blue",
        "card_desc": "A modalidade para comprar bens e serviços comuns pelo "
                     "menor preço.",
        "alta_intro": "Materiais sobre o pregão: a modalidade usada para comprar "
                      "bens e serviços comuns pelo menor preço, em geral na forma "
                      "eletrônica.",
    },
    {
        "slug": "registro-precos",
        "label": "Registro de Preços",
        "query": "Registro de Preços",
        "icon": "fi-bookmark",
        "color": "c-yellow",
        "card_desc": "O Sistema de Registro de Preços (SRP): registrar preços "
                     "para contratar quando precisar.",
        "alta_intro": "Materiais sobre o Sistema de Registro de Preços (SRP) e a "
                      "ata: registrar preços para contratar aos poucos, conforme "
                      "a necessidade.",
    },
```

- [ ] **Step 4: Rodar os testes e ver passar**

Run: `docker exec lilp-bdlp-portal-1 python -m pytest catalog/tests/test_taxonomy_v6.py -v`
Expected: PASS (todos). Conferir também que as buscas não ficam vazias:
Run: `docker exec lilp-bdlp-portal-1 python manage.py shell -c "from catalog.search import search_documents as s; print(s('Compras Diretas').count(), s('Pregão').count(), s('Registro de Preços').count())"`
Expected: `8 19 10` (ou números > 0 atuais).

- [ ] **Step 5: ruff + commit**

```bash
docker exec lilp-bdlp-portal-1 ruff check catalog/taxonomy_v6.py catalog/tests/test_taxonomy_v6.py
git add portal/catalog/taxonomy_v6.py portal/catalog/tests/test_taxonomy_v6.py
git commit -m "feat(home): 3 temas novos em TEMAS_DESTAQUE (Compras Diretas, Pregão, Registro de Preços)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: `views.home` — Coleções e chips separados; slug nos temas (Itens 1, 4)

**Files:**
- Modify: `portal/catalog/views.py:42-57` (remover `_card_tematico`), `:89-166` (`home()`)

- [ ] **Step 1: Remover a função `_card_tematico` (ficará sem uso)**

Apagar o bloco em `portal/catalog/views.py:51-57`:

```python
def _card_tematico(t):
    """Normaliza um card temático (cards_tematicos_overview) para o card unificado."""
    return {
        "href": _search_url(**t["params"]),
        "color": t["color"], "icon": t["icon"], "label": t["label"],
        "desc": t["descricao"], "count": t["count"],
    }
```

- [ ] **Step 2: Item 1 — `cards_explorar` só com Coleções**

Em `home()`, substituir as linhas 94-97:

```python
    # "Explorar o acervo": 4 coleções formais + cards temáticos que têm resultados
    # (oculta o card temático cuja busca não retorna documentos — sem beco sem saída).
    cards_explorar = [_card_colecao(c) for c in colecoes_v6]
    cards_explorar += [_card_tematico(t) for t in tematicos if t["count"] > 0]
```

por:

```python
    # "Explorar o acervo" (Item 1): apenas as 4 Coleções formais como cards.
    cards_explorar = [_card_colecao(c) for c in colecoes_v6]
    # Os temas viram chips-âncora p/ a seção "Temas em alta" (mesma fonte:
    # cards_tematicos_overview, já em `tematicos`), com slug p/ a âncora.
    chips_temas = tematicos
```

- [ ] **Step 3: Item 4 — slug em cada `temas_em_alta`**

Substituir o comprehension `temas_em_alta` (linhas 101-111) por:

```python
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
```

- [ ] **Step 4: Passar `chips_temas` ao contexto**

No `render(...)`, logo após a linha `"cards_explorar": cards_explorar,`, adicionar:

```python
        "chips_temas": chips_temas,
```

- [ ] **Step 5: Verificar o contexto no container (sem teste de CI)**

Verificação direcionada do contexto (intercepta o `render` p/ inspecionar o dict):
```bash
docker exec lilp-bdlp-portal-1 python manage.py shell -c "
from django.test import RequestFactory
from unittest.mock import patch
import catalog.views as v
captured = {}
def fake_render(req, tpl, ctx): captured.update(ctx); from django.http import HttpResponse; return HttpResponse('ok')
with patch.object(v, 'render', fake_render):
    v.home(RequestFactory().get('/'))
print('cards_explorar:', len(captured['cards_explorar']))
print('chips_temas:', [c['slug'] for c in captured['chips_temas']])
print('temas_em_alta:', [(t['slug'], len(t['docs'])) for t in captured['temas_em_alta']])
"
```
Expected: `cards_explorar: 4`; `chips_temas` = os 5 slugs na ordem; `temas_em_alta` = 5 temas, cada um com `len(docs) >= 1` (todos com docs).

- [ ] **Step 6: ruff + commit**

```bash
docker exec lilp-bdlp-portal-1 ruff check catalog/views.py
git add portal/catalog/views.py
git commit -m "feat(home): separar Coleções (cards) de Temas (chips) e expor slug dos temas

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: `home.html` — markup dos Itens 1, 2 e 4

**Files:**
- Modify: `portal/templates/home.html:62-75` (Explorar), `:101` (sublabel Etapas), `:115-134` (Temas em alta), fim do arquivo (`extra_js`)

- [ ] **Step 1: Item 1 — seção "Explorar o acervo"**

Substituir o bloco inteiro `portal/templates/home.html:62-75` por:

```html
<section class="sp-section">
  <div class="sp-container">
    <div class="section-heading">
      <div>
        <span class="eyebrow">Explorar o acervo</span>
        <h2>Coleções organizadas para a tomada de decisão pública</h2>
      </div>
      <a class="sp-button-secondary" href="{% url 'catalog:collection_list' %}">Consultar Coleções <svg class="fi" aria-hidden="true"><use href="#fi-arrow-right"/></svg></a>
    </div>

    <p class="subsection-label">Coleções</p>
    <div class="collections-grid collections-grid--quatro">
      {% for card in cards_explorar %}{% include "_partials/_collection_card.html" %}{% endfor %}
    </div>

    {% if chips_temas %}
    <p class="subsection-label">Temas em alta</p>
    <div class="temas-chips">
      {% for chip in chips_temas %}
      <a class="tema-chip" href="#tema-{{ chip.slug }}" data-tema-target="{{ chip.slug }}">
        <span class="tema-chip__ic {{ chip.color }}" aria-hidden="true"><svg class="fi"><use href="#{{ chip.icon }}"/></svg></span>
        <span class="tema-chip__txt">
          <span class="tema-chip__lab">{{ chip.label }}</span>
          <span class="tema-chip__count">{{ chip.count }} {{ chip.count|pluralize_pt:"documento" }}</span>
        </span>
      </a>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</section>
```

- [ ] **Step 2: Item 2 — renomear o sublabel das transversais**

Em `portal/templates/home.html:101`, trocar:

```html
    <p class="etapas-trans-head">Visões transversais</p>
```
por:
```html
    <p class="subsection-label">Visões transversais</p>
```

- [ ] **Step 3: Item 4 — seção "Temas em alta" (ids, botões)**

Substituir o bloco `portal/templates/home.html:115-134` por:

```html
<section class="sp-section sp-section--alt">
  <div class="sp-container temas-em-alta">
    <span class="eyebrow">Temas em alta</span>
    {% for tema in temas_em_alta %}
    <div class="tema-grupo" id="tema-{{ tema.slug }}" data-tema="{{ tema.slug }}">
      <div class="tema-grupo__cab">
        <h2 class="tema-grupo__titulo">
          <span class="tema-grupo__icone {{ tema.color }}" aria-hidden="true"><svg class="fi"><use href="#{{ tema.icon }}"/></svg></span>
          <span>{{ tema.label }}</span>
        </h2>
        <a class="sp-button-secondary" href="{{ tema.href }}">Ver tema no acervo <svg class="fi" aria-hidden="true"><use href="#fi-arrow-right"/></svg></a>
      </div>
      <p class="tema-grupo__intro">{{ tema.intro }}</p>
      <div class="doc-grid doc-grid--2">
        {% for doc in tema.docs %}{% include "_partials/_doc_card.html" %}{% endfor %}
      </div>
      {% if tema.docs|length > 2 %}
      <div class="tema-grupo__more">
        <button type="button" class="sp-button-secondary is-hidden" data-mais-docs aria-expanded="false">
          <svg class="fi" aria-hidden="true"><use href="#fi-plus-circle"/></svg> Carregar mais documentos
        </button>
      </div>
      {% endif %}
    </div>
    {% endfor %}
    {% if temas_em_alta|length > 2 %}
    <div class="temas-em-alta__more">
      <button type="button" class="sp-button-secondary is-hidden" data-mais-temas>
        <svg class="fi" aria-hidden="true"><use href="#fi-plus-circle"/></svg> Carregar mais temas
      </button>
    </div>
    {% endif %}
  </div>
</section>
```

- [ ] **Step 4: Incluir o `home.js`**

No fim de `portal/templates/home.html` (após o `{% endblock %}` do `content_raw`, linha ~135), acrescentar:

```html

{% block extra_js %}
<script src="{% static 'js/home.js' %}" defer></script>
{% endblock %}
```

(O `{% load static catalog_tags %}` no topo do arquivo já habilita `{% static %}`.)

- [ ] **Step 5: Verificar render (Django template não quebrou)**

Run: `docker exec lilp-bdlp-portal-1 python manage.py shell -c "from django.test import Client; r=Client().get('/'); print(r.status_code); html=r.content.decode(); print('chips:', html.count('data-tema-target')); print('temas:', html.count('data-tema=')); print('btn docs:', html.count('data-mais-docs')); print('btn temas:', html.count('data-mais-temas'))"`
Expected: `200`; `chips: 5`; `temas: 5`; `btn docs: 5`; `btn temas: 1`.

- [ ] **Step 6: Commit**

```bash
git add portal/templates/home.html
git commit -m "feat(home): markup Itens 1/2/4 — chips de temas, sublabels e botões Carregar mais

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: `portal.css` — Itens 1, 2, 3 e 4

**Files:**
- Modify: `portal/static/css/portal.css` (linhas 416, 446-451, novo bloco ≥768 p/ etapas, e novo bloco "Home — Carregar mais / chips")

- [ ] **Step 1: Utilitário `.is-hidden` + renomear sublabel (Itens 1/2/4)**

Em `portal/static/css/portal.css:416`, substituir:

```css
.etapas-trans-head { font-family: var(--font-subtitle); font-weight: 600; font-size: 13px; color: rgb(var(--rgb-black) / 0.66); margin: clamp(28px, 3vw, 36px) 0 0; }
```
por:
```css
/* Utilitário de ocultação controlado por JS (vence display próprio de .doc-card,
   .sp-button-secondary etc.). Sem JS, nada recebe esta classe. */
.is-hidden { display: none !important; }

/* Rótulo de sub-bloco compartilhado (Explorar: Coleções/Temas em alta; Etapas:
   Visões transversais). Zera a margem do grid imediatamente seguinte. */
.subsection-label { font-family: var(--font-subtitle); font-weight: 600; font-size: 13px; color: rgb(var(--rgb-black) / 0.66); margin: clamp(28px, 3vw, 36px) 0 14px; }
.subsection-label + .collections-grid,
.subsection-label + .temas-chips,
.subsection-label + .etapas-trans { margin-top: 0; }
```

- [ ] **Step 2: Item 1 — chips dos Temas em alta (5 colunas, responsivo)**

Acrescentar logo após o bloco do Step 1 (continuando a seção "Coleções (home)"):

```css
/* Temas em alta (Explorar): chips-âncora — 5 colunas no desktop, responsivo. */
.temas-chips { display: grid; gap: 10px; grid-template-columns: 1fr; }
@media (min-width: 560px) { .temas-chips { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 768px) { .temas-chips { grid-template-columns: repeat(3, 1fr); } }
@media (min-width: 1024px) { .temas-chips { grid-template-columns: repeat(5, 1fr); } }
.tema-chip { display: flex; align-items: center; gap: 10px; border: 1px solid rgb(var(--rgb-gray-medium) / 0.6); border-radius: 8px; padding: 11px 13px; color: inherit; transition: border-color 150ms ease; }
.tema-chip:hover { border-color: var(--sp-blue); }
.tema-chip__ic { height: 30px; width: 30px; flex: none; display: grid; place-items: center; border-radius: 6px; font-size: 15px; }
.tema-chip__txt { display: flex; flex-direction: column; min-width: 0; }
.tema-chip__lab { font-family: var(--font-subtitle); font-weight: 600; font-size: 12.5px; line-height: 1.25; color: var(--sp-black); }
.tema-chip__count { font-size: 11px; color: rgb(var(--rgb-black) / 0.55); margin-top: 2px; }
```

- [ ] **Step 3: Item 2 — transversais em 2 colunas**

Substituir `portal/static/css/portal.css:446-447`:

```css
.etapas-trans { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
.etapa-chip { display: inline-flex; align-items: center; gap: 8px; border: 1px solid rgb(var(--rgb-gray-medium) / 0.6); border-radius: 8px; padding: 9px 13px; color: inherit; transition: border-color 150ms ease; }
```
por:
```css
.etapas-trans { display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 12px; }
@media (min-width: 640px) { .etapas-trans { grid-template-columns: repeat(2, 1fr); } }
.etapa-chip { display: flex; align-items: center; gap: 8px; border: 1px solid rgb(var(--rgb-gray-medium) / 0.6); border-radius: 8px; padding: 11px 14px; color: inherit; transition: border-color 150ms ease; }
```

E em `portal/static/css/portal.css:451`, substituir:
```css
.etapa-chip__count { font-size: 11px; color: rgb(var(--rgb-black) / 0.55); }
```
por:
```css
.etapa-chip__count { font-size: 11px; color: rgb(var(--rgb-black) / 0.55); margin-left: auto; }
```

- [ ] **Step 4: Item 3 — alinhamento das contagens (escopo ≥768px)**

Acrescentar **logo após** o bloco `@media (min-width: 768px) { ... }` das etapas (após a linha 443), um novo bloco:

```css
/* Item 3: alinhar contagens das etapas. Rótulo com 2 linhas reservadas
   (descrições começam na mesma altura) + contagem empurrada ao rodapé numa
   linha-base comum. Só no layout horizontal (≥768px). */
@media (min-width: 768px) {
  .etapa-step__link { height: 100%; }
  .etapa-step__txt { flex: 1 1 auto; }
  .etapa-step__lab { min-height: 2.5em; display: flex; align-items: center; justify-content: center; }
  .etapa-step__count { margin-top: auto; }
}
```

- [ ] **Step 5: Item 4 — botões "Carregar mais"**

Acrescentar ao fim da seção "Temas em alta" da CSS (após a linha ~514, depois de `.tema-grupo__intro`):

```css
/* Item 4: botões "Carregar mais" (docs por tema e temas). Ocultos por padrão
   (.is-hidden), revelados pelo JS; usam o estilo .sp-button-secondary. */
.tema-grupo__more, .temas-em-alta__more { display: flex; justify-content: center; margin-top: 18px; }
.temas-em-alta__more { margin-top: 24px; }
```

- [ ] **Step 6: Verificar a CSS (sem erros de sintaxe) e coletar estáticos**

Run: `docker exec lilp-bdlp-portal-1 python -c "import pathlib,sys; t=pathlib.Path('static/css/portal.css').read_text(encoding='utf-8'); sys.exit(0 if t.count('{')==t.count('}') else 1); "` e confirme exit 0 (chaves balanceadas — checagem grosseira).
Run (se o app serve estáticos coletados): `docker exec lilp-bdlp-portal-1 python manage.py collectstatic --noinput`
Expected: copia/atualiza `portal.css` sem erro.

- [ ] **Step 7: Commit**

```bash
git add portal/static/css/portal.css
git commit -m "style(home): chips 5-col, transversais 2-col, alinhamento das etapas e botões Carregar mais

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: `home.js` — "Carregar mais" + revelação por chip (Itens 1, 4)

**Files:**
- Create: `portal/static/js/home.js`

- [ ] **Step 1: Criar `portal/static/js/home.js`**

Conteúdo completo:

```javascript
/*
 * home.js — "Carregar mais" da Home (Temas em alta) + revelação por chip.
 *
 * Melhoria progressiva: SEM JS, todos os temas/documentos aparecem e os chips
 * funcionam como âncoras nativas. COM JS, oculta os extras (além de 2) e ativa
 * os botões. CSP-safe: apenas addEventListener, sem handlers inline.
 */
(function () {
    'use strict';

    var DOCS_VISIVEIS = 2;   // documentos por tema inicialmente visíveis (1 linha)
    var TEMAS_VISIVEIS = 2;  // temas inicialmente visíveis

    function reduzMovimento() {
        return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    /* Oculta os documentos além dos 2 primeiros num tema e ativa o botão. */
    function initDocs(bloco) {
        var grid = bloco.querySelector('.doc-grid');
        if (!grid) return;
        var cards = grid.querySelectorAll('.doc-card');
        if (cards.length <= DOCS_VISIVEIS) return;
        for (var i = DOCS_VISIVEIS; i < cards.length; i++) {
            cards[i].classList.add('is-hidden');
        }
        var btn = bloco.querySelector('[data-mais-docs]');
        if (!btn) return;
        btn.classList.remove('is-hidden');
        btn.addEventListener('click', function () {
            for (var j = DOCS_VISIVEIS; j < cards.length; j++) {
                cards[j].classList.remove('is-hidden');
            }
            btn.setAttribute('aria-expanded', 'true');
            btn.classList.add('is-hidden');
            if (cards[DOCS_VISIVEIS]) cards[DOCS_VISIVEIS].focus({ preventScroll: true });
        });
    }

    var Temas = {
        init: function () {
            this.blocos = Array.prototype.slice.call(document.querySelectorAll('[data-tema]'));
            if (!this.blocos.length) return;

            // (a) documentos por tema
            this.blocos.forEach(initDocs);

            // (b) temas além dos 2 primeiros começam ocultos
            for (var i = TEMAS_VISIVEIS; i < this.blocos.length; i++) {
                this.blocos[i].classList.add('is-hidden');
            }
            this.btnTemas = document.querySelector('[data-mais-temas]');
            if (this.btnTemas && this.blocos.length > TEMAS_VISIVEIS) {
                this.btnTemas.classList.remove('is-hidden');
                this.btnTemas.addEventListener('click', this.revelarProximo.bind(this));
            }

            // (c) chips em "Explorar o acervo": revelam o tema-alvo (fora de ordem)
            var chips = document.querySelectorAll('[data-tema-target]');
            for (i = 0; i < chips.length; i++) {
                chips[i].addEventListener('click', this.onChip.bind(this));
            }
        },

        primeiroOculto: function () {
            for (var i = 0; i < this.blocos.length; i++) {
                if (this.blocos[i].classList.contains('is-hidden')) return this.blocos[i];
            }
            return null;
        },

        // Some o botão de temas quando não houver mais nenhum tema oculto.
        atualizarBotaoTemas: function () {
            if (this.btnTemas && !this.primeiroOculto()) {
                this.btnTemas.classList.add('is-hidden');
            }
        },

        // Botão "Carregar mais temas": revela o PRIMEIRO ainda oculto (regra
        // estável mesmo que um chip já tenha revelado outro fora de ordem).
        revelarProximo: function () {
            var alvo = this.primeiroOculto();
            if (alvo) {
                alvo.classList.remove('is-hidden');
                this.focar(alvo);
            }
            this.atualizarBotaoTemas();
        },

        // Chip: revela SÓ o tema correspondente (fora de ordem), rola e foca.
        onChip: function (event) {
            var slug = event.currentTarget.getAttribute('data-tema-target');
            var alvo = document.getElementById('tema-' + slug);
            if (!alvo) return;   // sem alvo → deixa a âncora nativa agir
            event.preventDefault();
            alvo.classList.remove('is-hidden');
            this.atualizarBotaoTemas();
            alvo.scrollIntoView({ behavior: reduzMovimento() ? 'auto' : 'smooth', block: 'start' });
            this.focar(alvo);
        },

        focar: function (el) {
            if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
            el.focus({ preventScroll: true });
        }
    };

    function init() {
        try { Temas.init(); } catch (e) { console.error('[BDLP] Temas init falhou:', e); }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
```

- [ ] **Step 2: Coletar estáticos**

Run (se o app serve estáticos coletados): `docker exec lilp-bdlp-portal-1 python manage.py collectstatic --noinput`
Expected: inclui `js/home.js` sem erro.

- [ ] **Step 3: Commit**

```bash
git add portal/static/js/home.js
git commit -m "feat(home): home.js — Carregar mais (docs/temas) e revelação por chip (CSP-safe)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Verificação integrada (automatizada + preview)

**Files:** nenhum (verificação). Reabrir/recarregar a Home no preview.

- [ ] **Step 1: Lint + testes + deploy check (o que o CI roda)**

Run:
```bash
docker exec lilp-bdlp-portal-1 ruff check .
docker exec lilp-bdlp-portal-1 python -m pytest -v
docker exec lilp-bdlp-portal-1 python manage.py check --deploy
```
Expected: ruff sem erros; pytest tudo verde (inclui os novos testes da Task 1); `check --deploy` sem erros novos.

- [ ] **Step 2: Verificação visual da Home (preview/navegador) — COM JS**

Abrir a Home do portal em execução (container `lilp-bdlp-portal-1`; porta local conforme `.env`, ex.: http://localhost:8001/) e confirmar:
- **Item 1:** seção "Explorar o acervo" com sub-bloco "Coleções" (4 cards 2×2) e "Temas em alta" (5 chips, ícone à esquerda; 5 colunas no desktop, quebrando em telas estreitas).
- **Item 2:** em "Comece pela etapa", "Visões transversais" em 2 colunas cobrindo a largura das 4 etapas.
- **Item 3:** as contagens das 4 etapas alinhadas na mesma linha-base (rótulos de 1–2 linhas ocupam o mesmo espaço).
- **Item 4:** cada tema mostra 2 docs + "Carregar mais documentos" (clicar revela +2 e some); a seção mostra só Lei 14.133/21 e Sustentabilidade + "Carregar mais temas" (clicar revela 1 por vez: Compras Diretas → Pregão → Registro de Preços; some no fim).
- **Chips:** clicar num chip de tema oculto (ex.: "Registro de Preços") rola até o bloco e o revela **fora de ordem**; o botão "Carregar mais temas" depois revela os que ainda faltam (Compras Diretas, Pregão) e só então some.
- **Consistência:** a contagem do chip == número em "Ver tema no acervo" == origem dos docs de preview.

- [ ] **Step 3: Verificação SEM JS (degradação graciosa)**

Desabilitar JavaScript no navegador e recarregar a Home. Confirmar:
- Todos os 5 temas e todos os docs de preview aparecem.
- Os botões "Carregar mais" **não** aparecem (ficam com `is-hidden`).
- Os chips funcionam como âncoras nativas (rolam até o bloco do tema).

- [ ] **Step 4: Responsivo**

Em viewport estreita (~375px) e média (~800px): confirmar que chips (5→2/3 col) e transversais (2→1 col) quebram bem, as etapas empilham na vertical, e nada estoura.

- [ ] **Step 5: Commit final (se houver ajuste de verificação)**

Caso algum ajuste fino tenha sido necessário (ex.: encurtar o texto da contagem do chip), commitar:
```bash
git add -A
git commit -m "fix(home): ajustes finos de verificação visual

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas de verificação cruzada com a spec

- **Item 1** → Tasks 2 (cards_explorar/chips), 3 (markup), 4 (CSS chips/sublabel). ✓
- **Item 2** → Tasks 3 (sublabel), 4 (etapas-trans 2-col). ✓
- **Item 3** → Task 4 (alinhamento ≥768px). ✓
- **Item 4** → Tasks 1 (temas novos), 2 (slug), 3 (markup botões/ids), 4 (CSS botões), 5 (JS). ✓
- **Fora de escopo:** PCA com 0 documentos — registrado na spec; **não** tratado aqui.
