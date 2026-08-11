# Padrão de fundos — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aplicar o trio de fundos da home (abertura cinza quadriculada com breadcrumb dentro → miolo branco → fechamento cinza liso) a todas as páginas do portal, conforme `docs/superpowers/specs/2026-08-11-padrao-fundos-paginas-design.md`.

**Architecture:** Um novo modificador CSS `.sp-section--pattern` fornece a banda de abertura; cada página migra template + CSS próprios numa tarefa autocontida (um commit por página, site sempre consistente entre commits). Testes são invariantes de arquivo (sem banco), no estilo de `test_seta_secoes.py`, acumulados em `portal/catalog/tests/test_padrao_fundos.py`. Limpeza de CSS morto só no final, quando nenhum template referencia mais as classes antigas.

**Tech Stack:** Django templates + CSS único (`portal/static/css/portal.css`, 1 arquivo, sem build), pytest (invariantes de arquivo), Docker para verificação visual.

## Global Constraints

- **Execução sequencial das tarefas, na ordem.** Todas tocam `portal.css`; a ordem evita conflitos e mantém cada commit renderizável.
- **Home intocada** (`home.html` e blocos `.hero*`/`.stats`/`.home-etapas` do CSS) — ela é a referência.
- **Seta-guia intacta:** `home.html` mantém 5 `data-sec`; `collection_list.html` mantém 3; include `_partials/_seta_secoes.html` continua após a última seção; specs 2026-07-29 e 2026-08-10.
- **Busca:** todo o conteúdo permanece dentro do `<form id="acervo-form">` (submit conjunto + auto-submit de `acervo-filters.js`).
- **Worktree:** `/Users/bernardogalvao/Developer/Governo/biblioteca-digital-logistica-publica/.claude/worktrees/reverent-engelbart-9b397e` (branch `claude/reverent-engelbart-9b397e`). Todos os caminhos abaixo são relativos a ele.
- **Testes locais (espelha o CI):** venv descartável em `$SCRATCH/venv-fundos` onde `SCRATCH=/private/tmp/claude-501/-Users-bernardogalvao-Developer-Governo-biblioteca-digital-logistica-publica--claude-worktrees-reverent-engelbart-9b397e/7c20bee5-a771-4101-965b-507b92acdaef/scratchpad`. Comando padrão (a partir da raiz do worktree):
  `cd portal && DJANGO_SECRET_KEY=teste PYTHONPATH=$PWD $SCRATCH/venv-fundos/bin/python -m pytest catalog/tests/test_padrao_fundos.py catalog/tests/test_seta_secoes.py -q`
- **Sem rebuild por tarefa** — os testes são de arquivo. Rebuild + verificação visual só na Tarefa 10.
- **Commits pequenos**, mensagem em pt-BR (Linguagem Simples), rodapé `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- **Não commitar screenshots** no repo.
- Copy nova (banda de contato das legais) em Linguagem Simples; vermelho GESP `#ED1C24`/tokens existentes; nada de cor nova.

---

### Task 1: Fundação — modificador `.sp-section--pattern`, respiro final, venv de testes

**Files:**
- Modify: `portal/static/css/portal.css:117-124` (bloco de utilitários) e `:775` (paginação)
- Create: `portal/catalog/tests/test_padrao_fundos.py`

**Interfaces:**
- Produces (consumido pelas Tarefas 2–8):
  - Classe `sp-section--pattern` (sempre junto de `sp-section`): banda de abertura cinza quadriculada, `padding-top` reduzido, `border-bottom`.
  - Regra `.sp-section--pattern .breadcrumb { margin-bottom: var(--space-6) }` — o breadcrumb canônico dentro da banda é `<nav class="breadcrumb" aria-label="Você está em">…</nav>`, primeiro filho do `.sp-container`.
  - Respiro final: `main > .sp-section:last-of-type, main > form > .sp-section:last-of-type` (a variante `form >` serve a /busca/).
  - `.sp-section .pagination { margin-top: 0 }` — paginação como primeiro conteúdo da banda de fechamento (Tarefas 4 e 6).

- [ ] **Step 1: Criar o venv de testes e comprovar a suíte atual verde**

```bash
SCRATCH=/private/tmp/claude-501/-Users-bernardogalvao-Developer-Governo-biblioteca-digital-logistica-publica--claude-worktrees-reverent-engelbart-9b397e/7c20bee5-a771-4101-965b-507b92acdaef/scratchpad
python3 -m venv $SCRATCH/venv-fundos
$SCRATCH/venv-fundos/bin/pip install -q pytest pytest-django django==5.2.15
cd portal && DJANGO_SECRET_KEY=teste PYTHONPATH=$PWD $SCRATCH/venv-fundos/bin/python -m pytest catalog/tests/test_seta_secoes.py -q
```

Expected: `9 passed`. (Se a importação de `portal.settings` falhar por dependência ausente, instalar o que faltar no venv — as libs de settings são leves; `psycopg2` NÃO é importado por testes de arquivo.)

- [ ] **Step 2: Escrever os testes que falham (invariantes da fundação)**

Criar `portal/catalog/tests/test_padrao_fundos.py`:

```python
"""Invariantes do padrão de fundos (spec 2026-08-11), sem banco.

Trio por página: abertura cinza quadriculada (.sp-section--pattern, breadcrumb
dentro) -> miolo branco (.sp-section) -> fechamento cinza liso (.sp-section--alt).
Estilo de teste: leitura de arquivo, como test_seta_secoes.py.
"""

from pathlib import Path

PORTAL = Path(__file__).resolve().parents[2]
TEMPLATES = PORTAL / "templates"
CSS = (PORTAL / "static" / "css" / "portal.css").read_text(encoding="utf-8")


def _template(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def test_css_tem_banda_de_abertura_quadriculada():
    assert ".sp-section--pattern" in CSS
    bloco = CSS[CSS.index(".sp-section--pattern"):]
    assert "background-size: 40px 40px" in bloco[:600]      # a grade da home
    assert "rgb(0 0 0 / 0.03)" in bloco[:600]               # alfa 0.045 x 0.7 do overlay do hero
    assert ".sp-section--pattern .breadcrumb" in CSS        # breadcrumb vive dentro da banda


def test_css_respiro_final_cobre_seta_e_form():
    # :last-of-type (nao :last-child): a seta-guia vem depois da ultima secao
    # em home/colecoes; a variante form > serve a /busca/.
    assert "main > .sp-section:last-of-type" in CSS
    assert "main > form > .sp-section:last-of-type" in CSS
    assert "main > .sp-section:last-child" not in CSS
```

- [ ] **Step 3: Rodar e ver falhar**

Run: comando padrão de teste (Global Constraints).
Expected: FAIL — `test_css_tem_banda_de_abertura_quadriculada` e `test_css_respiro_final_cobre_seta_e_form` (classes ainda não existem).

- [ ] **Step 4: Implementar no CSS**

Em `portal/static/css/portal.css`, substituir (linhas 117–124):

```css
.sp-section { padding-block: var(--space-section); background: var(--sp-white); }
.sp-section--alt { background: var(--sp-gray-light); }
```

por:

```css
.sp-section { padding-block: var(--space-section); background: var(--sp-white); }
.sp-section--alt { background: var(--sp-gray-light); }
/* Banda de abertura do padrão de fundos (spec 2026-08-11): cinza-claro com o
   quadriculado da home direto no background — alfa 0.03 ≈ 0.045 × opacity 0.7
   do overlay .hero__pattern do hero. O breadcrumb vive DENTRO da banda; o
   padding-top menor encosta a banda no header, como na home. */
.sp-section--pattern {
  padding-top: var(--space-4);
  background-color: var(--sp-gray-light);
  background-image:
    linear-gradient(90deg, rgb(0 0 0 / 0.03) 1px, transparent 1px),
    linear-gradient(180deg, rgb(0 0 0 / 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  border-bottom: var(--border);
}
.sp-section--pattern .breadcrumb { margin-bottom: var(--space-6); }
```

E substituir a regra do respiro final (linha ~124, mantendo o comentário acima dela e acrescentando a justificativa):

```css
/* Respiro generoso entre a última seção e o rodapé (mesma medida das páginas
   internas .page). :last-of-type, não :last-child — a seta-guia é incluída
   depois da última seção em home/colecoes; a variante form > cobre a /busca/
   (seções dentro do <form id="acervo-form">). */
main > .sp-section:last-of-type,
main > form > .sp-section:last-of-type { padding-bottom: var(--space-page-bottom); }
```

Por fim, logo após o bloco `.pagination` (linha ~775 — `.pagination { display: flex; … margin-top: 24px; }`), acrescentar:

```css
/* Paginação como primeiro conteúdo da banda de fechamento (busca/coleção):
   o respiro vem do padding da banda, não da margem do componente. */
.sp-section .pagination { margin-top: 0; }
```

- [ ] **Step 5: Rodar e ver passar**

Run: comando padrão de teste.
Expected: todos os testes de `test_padrao_fundos.py` + os 9 de `test_seta_secoes.py` PASS.

- [ ] **Step 6: Commit**

```bash
git add portal/static/css/portal.css portal/catalog/tests/test_padrao_fundos.py
git commit -m "feat(front): banda de abertura .sp-section--pattern e respiro final por :last-of-type

Fundação do padrão de fundos (spec 2026-08-11). O quadriculado da home
vira modificador de seção reutilizável; o respiro antes do rodapé passa
a casar mesmo com a seta-guia depois da última seção e dentro do form
da busca.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: /colecoes/ — inverter a alternância e abrir quadriculado

**Files:**
- Modify: `portal/templates/collection_list.html:7-31,81`
- Test: `portal/catalog/tests/test_padrao_fundos.py`

**Interfaces:**
- Consumes: `sp-section--pattern` e breadcrumb-dentro-da-banda (Task 1).
- Produces: o padrão de conversão breadcrumb-para-dentro-da-banda que as Tarefas 3–6 repetem.

- [ ] **Step 1: Teste que falha**

Acrescentar a `test_padrao_fundos.py`:

```python
def test_colecoes_segue_o_trio():
    t = _template("collection_list.html")
    assert "breadcrumb-bar" not in t                          # faixa branca antiga saiu
    abertura = t.index('sp-section sp-section--pattern colecoes-hero')
    assert t.index('class="breadcrumb"', abertura) > abertura  # breadcrumb dentro da banda
    # fechamento cinza: a ultima secao (Como encontrar) e --alt; a do meio nao e
    assert t.count("sp-section--alt") == 1
    assert t.index("sp-section--alt") > t.index("Como o acervo se organiza")
```

Run: comando padrão. Expected: FAIL (`breadcrumb-bar` presente; pattern ausente).

- [ ] **Step 2: Editar o template**

Em `collection_list.html`, substituir as linhas 8–29 (o `<nav class="breadcrumb-bar">…</nav>` inteiro e a abertura do hero até o fim do bloco `page__intro`+grid) por:

```html
<section class="sp-section sp-section--pattern colecoes-hero" data-sec="Coleções">
  <div class="sp-container">
    <nav class="breadcrumb" aria-label="Você está em">
      <a href="{% url 'catalog:home' %}">Início</a>
      <svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>
      <span>Coleções</span>
    </nav>
    <span class="eyebrow">Acervo</span>
    <h1>Coleções</h1>
    <p class="page__intro">
      O acervo se divide em quatro coleções, organizadas pelo tipo de informação.
      Escolha uma para começar a explorar — e veja, abaixo, como cada documento é
      classificado e como encontrar o que você precisa.
    </p>
    <div class="collections-grid collections-grid--quatro">
      {% for card in cards %}{% include "_partials/_collection_card.html" %}{% endfor %}
    </div>
  </div>
</section>
```

Depois: na seção "Como o acervo se organiza" (linha 31), trocar
`class="sp-section sp-section--alt"` por `class="sp-section"`; na seção
"Como encontrar o que você procura" (linha 81), trocar `class="sp-section"`
por `class="sp-section sp-section--alt"`. Nada mais muda (os `data-sec` e o
include da seta permanecem).

- [ ] **Step 3: Rodar e ver passar**

Run: comando padrão. Expected: PASS (incluindo `test_colecoes_tem_3_ancoras_e_a_seta`).

- [ ] **Step 4: Commit**

```bash
git add portal/templates/collection_list.html portal/catalog/tests/test_padrao_fundos.py
git commit -m "feat(front): /colecoes/ no padrão de fundos — abre quadriculado, fecha cinza

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: /sobre/ — mesmo trio, alternância re-fasada

**Files:**
- Modify: `portal/templates/about.html:6-27,53,94,112`
- Test: `portal/catalog/tests/test_padrao_fundos.py`

**Interfaces:**
- Consumes: receita da Task 2.

- [ ] **Step 1: Teste que falha**

```python
def test_sobre_segue_o_trio():
    t = _template("about.html")
    assert "breadcrumb-bar" not in t
    abertura = t.index('sp-section sp-section--pattern sobre-hero')
    assert t.index('class="breadcrumb"', abertura) > abertura
    # miolo alterna branco/cinza a partir do branco; contato fecha cinza
    assert t.count("sp-section--alt") == 2
    assert t.rindex("sp-section--alt") > t.index("Fale com o LILP") - 400
```

Run: comando padrão. Expected: FAIL.

- [ ] **Step 2: Editar o template**

Substituir as linhas 7–25 (breadcrumb-bar + abertura do hero) por:

```html
<section class="sp-section sp-section--pattern sobre-hero">
  <div class="sp-container">
    <nav class="breadcrumb" aria-label="Você está em">
      <a href="{% url 'catalog:home' %}">Início</a>
      <svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>
      <span>Sobre</span>
    </nav>
    <span class="eyebrow">Institucional</span>
    <h1>Sobre a Biblioteca Digital de Logística Pública</h1>
    <p class="page__intro">
      A BDLP é um repositório digital temático que centraliza produções
      científicas, técnicas, jurisprudenciais e normativas sobre logística
      pública, com foco na aplicação da Lei nº 14.133/2021.
    </p>
  </div>
</section>
```

Re-fasear a alternância das 4 seções seguintes:

- "Quem somos" (linha 27): `class="sp-section sp-section--alt"` → `class="sp-section"`
- "Parceria" (linha 53): `class="sp-section"` → `class="sp-section sp-section--alt"`
- "Marco normativo" (linha 94): `class="sp-section sp-section--alt"` → `class="sp-section"`
- "Contato" (linha 112): `class="sp-section"` → `class="sp-section sp-section--alt"`

- [ ] **Step 3: Rodar e ver passar** — comando padrão, Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add portal/templates/about.html portal/catalog/tests/test_padrao_fundos.py
git commit -m "feat(front): /sobre/ no padrão de fundos — abre quadriculado, fecha cinza no contato

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: /busca/ — trio dentro do form

**Files:**
- Modify: `portal/templates/search.html:6-43,190-216`, `portal/static/css/portal.css:591-604`
- Test: `portal/catalog/tests/test_padrao_fundos.py`

**Interfaces:**
- Consumes: Task 1 (`sp-section--pattern`, `.sp-section .pagination`, respiro `form >`).

- [ ] **Step 1: Teste que falha**

```python
def test_busca_segue_o_trio_dentro_do_form():
    t = _template("search.html")
    assert "breadcrumb-bar" not in t
    form = t.index('id="acervo-form"')
    abertura = t.index("sp-section sp-section--pattern catalog-hero")
    assert abertura > form                                     # tudo dentro do form
    assert t.index('class="breadcrumb"', abertura) > abertura
    miolo = t.index('sp-section">', abertura)                  # banda branca do miolo
    assert t.index("acervo-layout") > miolo
    fecho = t.index("sp-section sp-section--alt")
    assert fecho > t.index("acervo-layout")                    # paginacao na banda cinza
    assert t.index('class="pagination"') > fecho
    assert t.rindex("</form>") > fecho                         # fechamento ainda no form


def test_css_catalog_hero_nao_pinta_banda_propria():
    # A banda vem do .sp-section--pattern; o .catalog-hero nao pode sobrepor
    # fundo branco por ordem de arquivo.
    assert ".catalog-hero { border-bottom" not in CSS
    assert ".catalog-hero__inner" not in CSS
```

Run: comando padrão. Expected: FAIL.

- [ ] **Step 2: Editar o template**

(a) Substituir as linhas 8–41 (breadcrumb-bar + `<section class="catalog-hero">` inteiro) por:

```html
  <section class="sp-section sp-section--pattern catalog-hero">
    <div class="sp-container">
      <nav class="breadcrumb" aria-label="Você está em">
        <a href="{% url 'catalog:home' %}">Início</a>
        <svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>
        {% if crumb %}
        <a href="{% url 'catalog:search' %}">Acervo</a>
        <svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>
        <span>{{ crumb }}</span>
        {% else %}
        <span>Acervo</span>
        {% endif %}
      </nav>
      <div class="catalog-hero__grid">
        <div>
          <span class="eyebrow">Acervo</span>
          <h1>Pesquisa institucional</h1>
          <p>Consulte jurisprudência, trabalhos acadêmicos, doutrina, conteúdo técnico e materiais
             de capacitação sobre logística pública, licitações e gestão de suprimentos.</p>
        </div>
        <div class="searchbar">
          <span class="searchbar__field">
            <label class="sr-only" for="sp-busca">Buscar no acervo</label>
            <svg class="fi searchbar__icon" aria-hidden="true"><use href="#fi-search"/></svg>
            <input id="sp-busca" name="q" type="search" value="{{ query }}" placeholder="Buscar no acervo">
          </span>
          <button class="sp-button-primary searchbar__submit" type="submit"><svg class="fi" aria-hidden="true"><use href="#fi-search"/></svg> Buscar</button>
        </div>
      </div>
    </div>
  </section>
```

(b) Envolver o miolo numa banda branca: a linha `<div class="sp-container acervo-layout">` (linha 43) vira

```html
  <section class="sp-section">
    <div class="sp-container acervo-layout">
```

e o `</div>` correspondente (o que fecha `.acervo-layout`, linha 216, imediatamente antes de `</form>`) vira

```html
    </div>
  </section>
```

(c) Mover a paginação para a banda de fechamento: recortar o bloco inteiro
`{% if page_obj.has_other_pages %} … {% endif %}` (linhas 191–214, com o
`<nav class="pagination">` e o `<p class="pagination__status">`) de dentro de
`.acervo-results` e colá-lo DEPOIS do `</section>` criado em (b), ainda antes
de `</form>`, envolvido assim:

```html
  {% if page_obj.has_other_pages %}
  <section class="sp-section sp-section--alt">
    <div class="sp-container">
      <nav class="pagination" aria-label="Paginação dos resultados">
        …(conteúdo idêntico ao atual das linhas 193–212)…
      </nav>
      <p class="pagination__status">Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}</p>
    </div>
  </section>
  {% endif %}
```

Nota: com ≤1 página de resultados não há fechamento cinza — variação tolerada
pela spec (análoga ao documento sem relacionados).

- [ ] **Step 3: Ajustar o CSS**

Em `portal.css` (linhas 591–604):

- Apagar a linha `.catalog-hero { border-bottom: var(--border); background: var(--sp-white); }`
- Apagar a linha `.catalog-hero__inner { padding-block: var(--space-page-top); }`
- Apagar a linha `.breadcrumb-bar + .catalog-hero .catalog-hero__inner { padding-top: var(--space-4); }` (e o comentário das linhas 593–594 acima dela)
- Na regra `.acervo-layout { display: grid; gap: var(--space-6); padding-block: var(--space-page-top) var(--space-page-bottom); … }`, remover a declaração `padding-block: …;` (a banda agora dá o ritmo).

- [ ] **Step 4: Rodar e ver passar** — comando padrão, Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add portal/templates/search.html portal/static/css/portal.css portal/catalog/tests/test_padrao_fundos.py
git commit -m "feat(front): /busca/ no padrão de fundos — trio dentro do form, paginação no fechamento

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: /documento/ — abertura absorve breadcrumb e resultnav

**Files:**
- Modify: `portal/templates/document_detail.html:8-56,58,133`, `portal/static/css/portal.css:583-589,791,806-807`
- Test: `portal/catalog/tests/test_padrao_fundos.py`

**Interfaces:**
- Consumes: Task 1.

- [ ] **Step 1: Teste que falha**

```python
def test_documento_segue_o_trio():
    t = _template("document_detail.html")
    assert "breadcrumb-bar" not in t
    abertura = t.index("sp-section sp-section--pattern doc-detail-hero")
    assert t.index('class="breadcrumb"', abertura) > abertura
    assert t.index("doc-resultnav") > abertura                 # resultnav dentro da abertura
    miolo = t.index('sp-section">', abertura)
    assert t.index("doc-detail-layout") > miolo
    assert "sp-section--alt doc-related" in t                  # fechamento quando ha relacionados


def test_css_doc_hero_e_resultnav_sem_banda_propria():
    assert ".doc-detail-hero { border-bottom" not in CSS
    assert ".doc-resultnav { border-bottom: var(--border); background" not in CSS
    assert ".doc-detail-layout:has(+ .doc-related)" not in CSS
```

Run: comando padrão. Expected: FAIL.

- [ ] **Step 2: Editar o template**

Substituir as linhas 8–56 (breadcrumb-bar + resultnav condicional + `<section class="doc-detail-hero">`) por uma única banda de abertura:

```html
<section class="sp-section sp-section--pattern doc-detail-hero">
  <div class="sp-container">
    <nav class="breadcrumb" aria-label="Você está em">
      <a href="{% url 'catalog:home' %}">Início</a>
      <svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>
      <a href="{% url 'catalog:search' %}">Acervo</a>
      <svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>
      <a href="{% url 'catalog:search' %}?colecao_v6={{ cv.slug }}">{{ cv.nome }}</a>
      <svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>
      <span>{{ document.title|truncatechars:60 }}</span>
    </nav>

    {% if nav.prev_url or nav.next_url or nav.back_url %}
    <nav class="doc-resultnav" aria-label="Navegação entre resultados da busca">
      <div class="doc-resultnav__inner">
        {% if nav.back_url %}<a class="doc-resultnav__back" href="{{ nav.back_url }}"><svg class="fi" aria-hidden="true"><use href="#fi-chevron-left"/></svg> Voltar à busca</a>{% else %}<span></span>{% endif %}
        <div class="doc-resultnav__nav">
          {% if nav.pos %}<span class="doc-resultnav__pos">{{ nav.pos }} de {{ nav.total }}</span>{% endif %}
          {% if nav.prev_url %}<a class="page-btn" href="{{ nav.prev_url }}" rel="prev"><svg class="fi" aria-hidden="true"><use href="#fi-chevron-left"/></svg> Anterior</a>{% else %}<span class="page-btn is-disabled" aria-disabled="true"><svg class="fi" aria-hidden="true"><use href="#fi-chevron-left"/></svg> Anterior</span>{% endif %}
          {% if nav.next_url %}<a class="page-btn" href="{{ nav.next_url }}" rel="next">Próximo <svg class="fi" aria-hidden="true"><use href="#fi-chevron-right"/></svg></a>{% else %}<span class="page-btn is-disabled" aria-disabled="true">Próximo <svg class="fi" aria-hidden="true"><use href="#fi-chevron-right"/></svg></span>{% endif %}
        </div>
      </div>
    </nav>
    {% endif %}

    <div class="doc-badges">
      …(conteúdo idêntico ao atual das linhas 35–47)…
    </div>

    <h1>{{ document.title }}</h1>

    <div class="doc-authors">
      …(conteúdo idêntico ao atual das linhas 51–54)…
    </div>
  </div>
</section>
```

(O que muda no resultnav: perde o `sp-container` interno — a banda já tem um — e
perde a banda própria; o condicional `{% if nav… %}` é o mesmo.)

Depois, envolver o miolo: a linha `<div class="sp-container doc-detail-layout">`
(linha 58) vira

```html
<section class="sp-section">
  <div class="sp-container doc-detail-layout">
```

e o `</div>` que fecha `.doc-detail-layout` (linha 133, antes do bloco
`{% if relacionados %}`) vira

```html
  </div>
</section>
```

A seção `sp-section sp-section--alt doc-related` (relacionados) fica como está.

- [ ] **Step 3: Ajustar o CSS**

- Linha 583: `.doc-resultnav { border-bottom: var(--border); background: var(--sp-white); }` → substituir por:

```css
/* Dentro da banda de abertura: linha divisória, sem banda própria */
.doc-resultnav { border-bottom: var(--border); margin-bottom: var(--space-4); }
```

- Linha 791: apagar a regra `.doc-detail-hero { border-bottom: var(--border); background: var(--sp-white); padding-block: var(--space-page-top); }` (as regras de `.doc-detail-hero h1` etc. ficam).
- Linha 806: na regra `.doc-detail-layout { … }`, remover a declaração `padding-block: var(--space-page-top) var(--space-page-bottom);`.
- Linha 807: apagar `.doc-detail-layout:has(+ .doc-related) { padding-bottom: 0; }` (o ritmo agora é banda a banda).

- [ ] **Step 4: Rodar e ver passar** — comando padrão, Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add portal/templates/document_detail.html portal/static/css/portal.css portal/catalog/tests/test_padrao_fundos.py
git commit -m "feat(front): /documento/ no padrão de fundos — abertura com breadcrumb e resultnav

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: /colecao/ — de página chapada para o trio

**Files:**
- Modify: `portal/templates/collection_detail.html` (arquivo inteiro), `portal/static/css/portal.css:~872` (compartilhar tipografia de hero)
- Test: `portal/catalog/tests/test_padrao_fundos.py`

**Interfaces:**
- Consumes: Task 1; classe `colecoes-hero` (tipografia de h1) já existente.
- Produces: classe `colecao-miolo` (h2 do miolo).

- [ ] **Step 1: Teste que falha**

```python
def test_colecao_migrou_para_o_trio():
    t = _template("collection_detail.html")
    assert "content_raw" in t                                  # saiu do wrapper .page
    abertura = t.index("sp-section sp-section--pattern colecoes-hero")
    assert t.index('class="breadcrumb"', abertura) > abertura
    assert "colecao-miolo" in t
    fecho = t.index("sp-section sp-section--alt")
    assert t.index('class="pagination"') > fecho
```

Run: comando padrão. Expected: FAIL.

- [ ] **Step 2: Reescrever o template**

Conteúdo completo novo de `collection_detail.html`:

```html
{% extends "base.html" %}
{% load catalog_tags %}

{% block title %}{{ topic.name }} — Biblioteca Digital de Logística Pública{% endblock %}

{% block content_raw %}
<section class="sp-section sp-section--pattern colecoes-hero">
  <div class="sp-container">
    <nav class="breadcrumb" aria-label="Você está em">
      <a href="{% url 'catalog:home' %}">Início</a>
      <svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>
      <a href="{% url 'catalog:collection_list' %}">Coleções</a>
      {% for item in breadcrumb %}<svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>{% if forloop.last %}<span>{{ item.name }}</span>{% else %}<a href="{% url 'catalog:collection_detail' item.id %}">{{ item.name }}</a>{% endif %}{% endfor %}
    </nav>
    <h1>{{ topic.name }}</h1>
    {% if topic.description %}<p class="page__intro">{{ topic.description }}</p>{% endif %}
  </div>
</section>

<section class="sp-section colecao-miolo">
  <div class="sp-container">
    {% if subcollection_cards %}
    <h2>Subcoleções</h2>
    <div class="collections-grid">
      {% for card in subcollection_cards %}{% include "_partials/_collection_card.html" %}{% endfor %}
    </div>
    {% endif %}

    <h2>Documentos ({{ total_docs }})</h2>
    {% if page_obj.object_list %}
    <div class="doc-grid">
      {% for doc in page_obj %}{% include "_partials/_doc_card.html" %}{% endfor %}
    </div>
    {% else %}
    <div class="sp-panel empty-state">
      <svg class="fi" aria-hidden="true"><use href="#fi-search"/></svg>
      <strong>Ainda não há documentos nesta coleção</strong>
      <p>Esta coleção faz parte da organização do acervo, mas ainda não recebeu materiais. Explore o <a href="{% url 'catalog:search' %}">acervo completo</a> ou veja outras <a href="{% url 'catalog:collection_list' %}">coleções</a>.</p>
    </div>
    {% endif %}
  </div>
</section>

{% if page_obj.has_other_pages %}
<section class="sp-section sp-section--alt">
  <div class="sp-container">
    <nav class="pagination" aria-label="Paginação dos documentos">
      {% if page_obj.has_previous %}<a class="page-btn" href="?page={{ page_obj.previous_page_number }}" aria-label="Anterior"><svg class="fi" aria-hidden="true"><use href="#fi-chevron-left"/></svg></a>{% endif %}
      <span class="page-info">Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}</span>
      {% if page_obj.has_next %}<a class="page-btn" href="?page={{ page_obj.next_page_number }}" aria-label="Próxima"><svg class="fi" aria-hidden="true"><use href="#fi-chevron-right"/></svg></a>{% endif %}
    </nav>
  </div>
</section>
{% endif %}
{% endblock %}
```

- [ ] **Step 3: CSS do miolo**

Em `portal.css`, logo após a regra `.colecoes-hero h1, .sobre-hero h1 { … }`
(linha ~872), acrescentar:

```css
/* Miolo da página de coleção (trio de fundos): h2 que antes herdavam de .page > h2 */
.colecao-miolo h2 { font-family: var(--font-heading); font-weight: 700; margin: 24px 0 12px; font-size: 22px; }
.colecao-miolo .sp-container > h2:first-child { margin-top: 0; }
```

- [ ] **Step 4: Rodar e ver passar** — comando padrão, Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add portal/templates/collection_detail.html portal/static/css/portal.css portal/catalog/tests/test_padrao_fundos.py
git commit -m "feat(front): /colecao/ no padrão de fundos — sai do wrapper .page para o trio

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: Legais — template comum `_base_legal.html` + 6 conversões

**Files:**
- Create: `portal/templates/legal/_base_legal.html`
- Modify: os 6 de `portal/templates/legal/` (`transparencia.html`, `acessibilidade.html`, `politica_privacidade.html`, `politica_cookies.html`, `mapa_site.html`, `fale_conosco.html`), `portal/static/css/portal.css:871-872`
- Test: `portal/catalog/tests/test_padrao_fundos.py`

**Interfaces:**
- Consumes: Task 1.
- Produces: blocos Django `legal_crumb`, `legal_titulo`, `legal_intro`, `legal_corpo`, `legal_fechamento`; classe `legal-hero`.

- [ ] **Step 1: Teste que falha**

```python
LEGAIS = [
    "legal/transparencia.html", "legal/acessibilidade.html",
    "legal/politica_privacidade.html", "legal/politica_cookies.html",
    "legal/mapa_site.html", "legal/fale_conosco.html",
]


def test_base_legal_define_o_trio():
    b = _template("legal/_base_legal.html")
    assert "sp-section sp-section--pattern legal-hero" in b
    assert 'class="breadcrumb"' in b
    assert "sp-pagina-legal" in b                              # corpo na banda branca
    assert "sp-section sp-section--alt" in b                   # fechamento (banda de contato)
    assert "fale_conosco" in b                                 # CTA aponta para o Fale Conosco


def test_legais_estendem_o_base_legal():
    for nome in LEGAIS:
        t = _template(nome)
        assert 'extends "legal/_base_legal.html"' in t, nome
        assert "block content" not in t.replace("content_raw", ""), nome


def test_fale_conosco_nao_se_autoreferencia():
    t = _template("legal/fale_conosco.html")
    assert "legal_fechamento" in t                             # sobrescreve a banda de contato
```

Run: comando padrão. Expected: FAIL (arquivo não existe).

- [ ] **Step 2: Criar `legal/_base_legal.html`**

```html
{% extends "base.html" %}
{% comment %}Trio de fundos das páginas legais (spec 2026-08-11): abertura
quadriculada com breadcrumb + h1 + intro; corpo em banda branca; fechamento
cinza com a banda de contato (sobrescrevível via legal_fechamento).{% endcomment %}

{% block content_raw %}
<section class="sp-section sp-section--pattern legal-hero">
  <div class="sp-container">
    <nav class="breadcrumb" aria-label="Você está em">
      <a href="{% url 'catalog:home' %}">Início</a>
      <svg class="fi sep" aria-hidden="true"><use href="#fi-chevron-right"/></svg>
      <span>{% block legal_crumb %}{% endblock %}</span>
    </nav>
    <h1>{% block legal_titulo %}{% endblock %}</h1>
    <p class="page__intro">{% block legal_intro %}{% endblock %}</p>
  </div>
</section>

<section class="sp-section">
  <div class="sp-container">
    <article class="sp-pagina-legal">
      {% block legal_corpo %}{% endblock %}
    </article>
  </div>
</section>

{% block legal_fechamento %}
<section class="sp-section sp-section--alt">
  <div class="sp-container">
    <div class="section-heading">
      <div>
        <span class="eyebrow">Contato</span>
        <h2>Dúvidas? Fale com o LILP</h2>
      </div>
    </div>
    <p class="curadoria-texto">
      Para pedidos, sugestões e correções sobre esta página ou sobre o
      portal, use o canal de contato do laboratório.
    </p>
    <p class="curadoria-acoes">
      <a class="sp-button-primary" href="{% url 'catalog:fale_conosco' %}">Ir para o Fale Conosco <svg class="fi" aria-hidden="true"><use href="#fi-arrow-right"/></svg></a>
    </p>
  </div>
</section>
{% endblock %}
{% endblock %}
```

- [ ] **Step 3: CSS — tipografia do hero legal**

Em `portal.css`, nas duas regras da linha 871–872, acrescentar `.legal-hero`:

```css
.colecoes-hero .eyebrow, .sobre-hero .eyebrow, .legal-hero .eyebrow { display: block; }
.colecoes-hero h1, .sobre-hero h1, .legal-hero h1 { font-family: var(--font-heading); font-weight: 700; font-size: clamp(28px, 3.4vw, 40px); line-height: 1.14; margin: 8px 0 10px; }
```

- [ ] **Step 4: Converter cada legal**

Receita idêntica para os 6 (exemplo integral com `transparencia.html`; os
blocos `title`/`meta_description` de cada arquivo ficam como estão):

1. Trocar `{% extends "base.html" %}` por `{% extends "legal/_base_legal.html" %}`.
2. Apagar `{% block content %}` … `<article class="sp-pagina-legal">` e o `<header>…</header>` (h1 + intro).
3. Emitir os blocos novos com o conteúdo existente.

`transparencia.html` convertido (modelo):

```html
{% extends "legal/_base_legal.html" %}

{% block title %}Transparência — Biblioteca Digital de Logística Pública | Governo de SP{% endblock %}
{% block meta_description %}Informações de transparência ativa do Portal BDLP: estrutura organizacional do LILP, legislação aplicável, contatos institucionais e canais de acesso à informação (LAI).{% endblock %}

{% block legal_crumb %}Transparência{% endblock %}
{% block legal_titulo %}Transparência e Acesso à Informação{% endblock %}
{% block legal_intro %}Esta página reúne informações de transparência ativa relacionadas ao Portal da Biblioteca Digital de Logística Pública (BDLP), atendendo à Lei nº 12.527/2011 (Lei de Acesso à Informação) e ao Decreto Federal nº 7.724/2012, bem como às diretrizes do Decreto Estadual nº 67.799/2023 (Estratégia de Governo Digital de São Paulo).{% endblock %}

{% block legal_corpo %}
  <section>
    <h2>Quem somos</h2>
    …(as 5 <section> atuais do arquivo, sem alteração interna)…
  </section>
{% endblock %}
```

Valores de `legal_crumb` por arquivo: `Transparência`, `Acessibilidade`,
`Política de Privacidade`, `Política de Cookies`, `Mapa do site`,
`Fale Conosco`. `legal_titulo`/`legal_intro` = o h1 e o parágrafo
`sp-pagina-legal__intro` atuais de cada arquivo (mover, não reescrever).

**Exceção `fale_conosco.html`:** além da receita, mover a última seção do
corpo ("Sobre o tratamento de seus dados de contato") para o fechamento —
a banda de contato não deve apontar para a própria página:

```html
{% block legal_fechamento %}
<section class="sp-section sp-section--alt">
  <div class="sp-container">
    <article class="sp-pagina-legal">
      <section>
        <h2>Sobre o tratamento de seus dados de contato</h2>
        <p>
          Os dados que você nos enviar serão utilizados exclusivamente para
          responder à sua solicitação, conforme nossa
          <a href="{% url 'catalog:politica_privacidade' %}">Política de Privacidade</a>.
          Você pode, a qualquer momento, solicitar exclusão dos seus dados
          ao Encarregado de Proteção de Dados da SGGD.
        </p>
      </section>
    </article>
  </div>
</section>
{% endblock %}
```

(no `legal_corpo` do fale_conosco ficam só "Canais de contato" e "Tempo de
resposta").

- [ ] **Step 5: Rodar e ver passar** — comando padrão, Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add portal/templates/legal/ portal/static/css/portal.css portal/catalog/tests/test_padrao_fundos.py
git commit -m "feat(front): legais no padrão de fundos — template comum _base_legal com trio e banda de contato

Elimina as 6 estruturas repetidas à mão; cada legal preenche blocos de
título, intro e corpo. Fale Conosco fecha com a própria seção de LGPD
em vez de apontar para si mesma.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: 404/500 — abertura quadriculada + banda de ações

**Files:**
- Modify: `portal/templates/404.html`, `portal/templates/500.html`, `portal/static/css/portal.css:768-772`
- Test: `portal/catalog/tests/test_padrao_fundos.py`

- [ ] **Step 1: Teste que falha**

```python
def test_paginas_de_erro_abrem_quadriculado():
    for nome in ("404.html", "500.html"):
        t = _template(nome)
        assert "content_raw" in t, nome
        assert "sp-section sp-section--pattern" in t, nome
        assert t.index("error-page__actions") > t.index('sp-section">'), nome
```

Run: comando padrão. Expected: FAIL.

- [ ] **Step 2: Reescrever `404.html`**

```html
{% extends "base.html" %}

{% block title %}Página não encontrada (404) — Biblioteca Digital de Logística Pública{% endblock %}

{% block content_raw %}
<section class="sp-section sp-section--pattern">
  <div class="sp-container error-page">
    <p class="error-page__code" aria-hidden="true">404</p>
    <h1>Página não encontrada</h1>
    <p>O endereço que você tentou acessar não existe, mudou de lugar ou foi removido.</p>
  </div>
</section>
<section class="sp-section">
  <div class="sp-container error-page">
    <div class="error-page__actions">
      <a class="sp-button-primary" href="{% url 'catalog:home' %}">Ir para a página inicial</a>
      <a class="sp-button-secondary" href="{% url 'catalog:search' %}">Buscar no acervo</a>
    </div>
  </div>
</section>
{% endblock %}
```

`500.html` idêntico na estrutura, preservando o texto atual do arquivo
(código `500`, h1 e parágrafo próprios — só trocar o wrapper como acima).
Atenção no 500: a página de erro de servidor não deve depender de contexto —
manter apenas `{% url %}` como hoje.

- [ ] **Step 3: Ajustar o CSS**

Linhas 768–772:

- `.error-page { max-width: 560px; margin-inline: auto; padding-block: clamp(40px, 8vw, 80px); text-align: center; }` → remover a declaração `padding-block: …;` (as bandas dão o ritmo) e acrescentar a regra:

```css
.sp-section--pattern .error-page { padding-top: var(--space-8); }  /* sem breadcrumb, a abertura pede mais ar */
```

- `.error-page__actions { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin-top: 28px; }` → trocar `margin-top: 28px` por `margin-top: 0` (a banda branca já afasta).

- [ ] **Step 4: Rodar e ver passar** — comando padrão, Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add portal/templates/404.html portal/templates/500.html portal/static/css/portal.css portal/catalog/tests/test_padrao_fundos.py
git commit -m "feat(front): 404/500 no padrão de fundos — abertura quadriculada e banda de ações

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: Limpeza — remover o CSS que ficou órfão

**Files:**
- Modify: `portal/static/css/portal.css:571,576-581,887-890`
- Test: `portal/catalog/tests/test_padrao_fundos.py`

- [ ] **Step 1: Confirmar que nada usa as classes antigas**

```bash
grep -rn "breadcrumb-bar\|sp-pagina-legal__intro\|sp-pagina-legal__cabecalho\|catalog-hero__inner" portal/templates/
```

Expected: nenhuma ocorrência. (Se houver, a tarefa dona do template regrediu — corrigir lá antes.)

- [ ] **Step 2: Teste que falha**

```python
def test_css_sem_classes_orfas_do_padrao_antigo():
    assert ".breadcrumb-bar" not in CSS
    assert ".sp-pagina-legal__cabecalho" not in CSS
    assert ".sp-pagina-legal__intro" not in CSS
    assert ".breadcrumb-bar + .colecoes-hero" not in CSS
```

Run: comando padrão. Expected: FAIL.

- [ ] **Step 3: Apagar as regras**

Em `portal.css`:

- Linha 571: apagar `.breadcrumb-bar { border-bottom: var(--border); background: var(--sp-white); }`
- Linha ~596: apagar `.breadcrumb-bar + .colecoes-hero, .breadcrumb-bar + .sobre-hero { padding-top: var(--space-5); }`
- Linhas 889–890: apagar `.sp-pagina-legal__cabecalho h1 { … }` e `.sp-pagina-legal__intro { … }`
- Manter: `.breadcrumb` (em uso, agora dentro das bandas) e o media query mobile do ellipsis do breadcrumb (referencia `.breadcrumb`, não `.breadcrumb-bar`).

- [ ] **Step 4: Rodar e ver passar** — comando padrão (suíte inteira de `test_padrao_fundos.py` + `test_seta_secoes.py`), Expected: PASS.

- [ ] **Step 5: Ruff no repositório (o CI vai rodar)**

```bash
$SCRATCH/venv-fundos/bin/pip install -q ruff && $SCRATCH/venv-fundos/bin/ruff check portal/
```

Expected: sem erros (só arquivos de teste Python foram adicionados).

- [ ] **Step 6: Commit**

```bash
git add portal/static/css/portal.css portal/catalog/tests/test_padrao_fundos.py
git commit -m "chore(front): remove CSS órfão do padrão antigo de fundos

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 10: Verificação visual integral

**Files:**
- Nenhuma mudança de código esperada (correções pontuais, se a verificação flagrar, entram como commits `fix(front):` desta tarefa).

- [ ] **Step 1: Rebuild + container isolado**

Reaproveitar o container de verificação da sessão (`lilp-fundos-verify`, porta 8005 — NÃO tocar na stack da 8000, que roda build de outro branch):

```bash
docker build -q -f docker/portal/Dockerfile -t lilp-bdlp-portal:fundos .
docker rm -f lilp-fundos-verify
docker run -d --name lilp-fundos-verify --network lilp-bdlp_default \
  --env-file /Users/bernardogalvao/Developer/Governo/biblioteca-digital-logistica-publica/.env \
  -e POSTGRES_HOST=postgres -e POSTGRES_PORT=5432 -e PORTAL_DB_USER=portal_reader \
  -e NOURAU_ARCHIVE_DIR=/nourau/archive -e DJANGO_DEBUG=true -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  -v lilp-bdlp_nourau_data:/nourau:ro -p 127.0.0.1:8005:8000 lilp-bdlp-portal:fundos
sleep 3 && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8005/colecoes/
```

Expected: `200`.

- [ ] **Step 2: Refotografar as 8 rotas em desktop**

Adaptar `$SCRATCH/fundos-atual/shoot.js` (o script da rodada "antes") para gravar em `$SCRATCH/fundos-novo/` e rodá-lo. Depois, ABRIR cada PNG e conferir contra a spec: abertura cinza quadriculada com breadcrumb dentro; miolo branco; fechamento cinza; sem costura estranha com o header sticky; badges do documento legíveis sobre o cinza. Comparar lado a lado com `$SCRATCH/fundos-atual/*.png`.

- [ ] **Step 3: Mobile 375×812**

Fotografar `/`, `/colecoes/`, `/busca/` e uma legal em 375×812 (viewport mobile no mesmo script). Conferir: pílula "Veja mais" da seta com o scrim sobre o fechamento cinza de /colecoes/ (deve seguir legível — o degradê branco sobre #F5F5F5 é quase invisível, ver spec §3).

- [ ] **Step 4: Ciclo da seta-guia**

Com puppeteer em /colecoes/ e na home (375×812 e 1280×900): chegada (pílula) → scroll → assenta → navega até a última seção → vira "Voltar ao topo". Medir `getBoundingClientRect` e classes como em `$SCRATCH/verifica-scrim.js` (rodada da pílula, sessão de 11/08). Expected: comportamento idêntico ao de antes da migração.

- [ ] **Step 5: pa11y WCAG2AA**

```bash
pa11y --standard WCAG2AA http://localhost:8005/busca/
pa11y --standard WCAG2AA http://localhost:8005/colecoes/
pa11y --standard WCAG2AA http://localhost:8005/sobre/
pa11y --standard WCAG2AA http://localhost:8005/transparencia/
```

Expected: zero erros novos (comparar com o estado atual se houver erros pré-existentes).

- [ ] **Step 6: Suíte completa no container**

```bash
docker exec lilp-fundos-verify sh -c "pip install -q pytest pytest-django; python -m pytest -q"
```

Expected: mesmos resultados do CI local conhecido — os 3 testes de
`test_taxonomy_seed_v9.py` falham DENTRO do container por lerem
`docker/postgres/init/` (artefato conhecido, CI cobre); todo o resto PASS.

- [ ] **Step 7: Encerrar e relatar**

```bash
docker rm -f lilp-fundos-verify && docker rmi lilp-bdlp-portal:fundos
```

Enviar ao usuário os pares antes/depois mais expressivos (SendUserFile) e o resumo da verificação.
