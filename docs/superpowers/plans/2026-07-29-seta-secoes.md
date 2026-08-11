# Seta-guia de seções — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seta flutuante no canto inferior direito da Home e de Coleções que navega entre as seções lógicas já existentes, mais ajuste anti-falso-fundo no hero — sem mudar conteúdo nem ordem.

**Architecture:** Âncoras `data-sec` nos `<section>` existentes; parcial de botão `[hidden]` revelado por JS (melhoria progressiva); IIFE ES5 CSP-safe no padrão de `home.js`; CSS ao fim de `portal.css` (a ordem faz o override do hero vencer). Testes puros (leem arquivos, sem banco), como os de taxonomia.

**Tech Stack:** Django templates, CSS puro (sem build), JS vanilla ES5 + IntersectionObserver/MutationObserver, pytest puro, ruff (linha 120).

**Spec:** `docs/superpowers/specs/2026-07-29-seta-secoes-design.md`

**Branch:** `feat/seta-secoes` (já criada, contém o spec).

> **Nota de status (pós-execução):** o código inline abaixo é o da execução
> original; o estado final difere em dois pontos corrigidos em revisão —
> `.sp-seta-secoes[hidden] { display: none; }` no CSS (commit `4793f15`) e o
> índice corrente retido no JS, no lugar do fallback 0 de `correnteIdx()`
> (commit `a66efeb`). O código nos arquivos vale sobre o plano.

---

## Estrutura de arquivos

| Arquivo | Papel |
|---|---|
| `portal/catalog/tests/test_seta_secoes.py` | novo — testes puros dos invariantes (padrão `test_taxonomy_seed_v9.py`) |
| `portal/templates/_partials/_feather.html` | +2 símbolos: `fi-chevron-down`, `fi-chevron-up` |
| `portal/templates/_partials/_seta_secoes.html` | novo — o botão da seta |
| `portal/templates/home.html` | 5 âncoras `data-sec`, include do parcial, script |
| `portal/templates/collection_list.html` | 3 âncoras `data-sec`, include do parcial, script, `{% load static %}` |
| `portal/static/css/portal.css` | bloco novo ao FIM do arquivo (seta + scroll-margin + hero peek + reduced-motion) |
| `portal/static/js/seta-secoes.js` | novo — comportamento da seta |

Notas fixadas no design (não "melhorar" durante a execução):

- Hover/foco da seta usa `--sp-red-dark` (#BD0E15), não `--sp-red` — é a regra
  AA do repo para fundo vermelho com conteúdo branco (mesma do `.sp-button-primary`).
- `tabindex="-1"` das seções é adicionado pelo JS no momento do foco (padrão
  `focar()` do `home.js`), não no template.
- O bloco CSS novo vai ao FIM de `portal.css` de propósito: o override do hero
  (`@media (max-height: 900px)`) precisa vencer, pela ordem, o
  `@media (min-width: 1024px) { .hero__inner { padding-block: 56px; } }` da linha ~337.

Comandos (Windows, PowerShell; testes rodam de dentro de `portal/`):

- Teste do arquivo: `py -m pytest catalog/tests/test_seta_secoes.py -v`
- Suíte completa (como o CI): `$env:DJANGO_SECRET_KEY = 'ci-dummy-secret-key-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'; py -m pytest -v`
- Lint (da raiz do repo): `ruff check portal/`

---

### Task 1: Ícones chevron down/up no sprite feather

**Files:**
- Create: `portal/catalog/tests/test_seta_secoes.py`
- Modify: `portal/templates/_partials/_feather.html:34` (após `fi-chevron-right`)

- [ ] **Step 1: Criar o arquivo de teste com o teste do sprite (falhando)**

Criar `portal/catalog/tests/test_seta_secoes.py`:

```python
"""Testes da seta-guia de seções (Home e Coleções), sem banco.

A feature é de front (templates/CSS/JS); estes testes leem os arquivos e
pinam os invariantes do design: âncoras [data-sec], parcial da seta nas
duas páginas, ícones no sprite e blocos CSS/JS presentes.
Spec: docs/superpowers/specs/2026-07-29-seta-secoes-design.md
"""

from pathlib import Path

PORTAL = Path(__file__).resolve().parents[2]
TEMPLATES = PORTAL / "templates"
STATIC = PORTAL / "static"


def _template(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def test_sprite_tem_chevron_down_e_up():
    sprite = _template("_partials/_feather.html")
    assert 'id="fi-chevron-down"' in sprite
    assert 'id="fi-chevron-up"' in sprite
```

- [ ] **Step 2: Rodar e ver falhar**

Run (em `portal/`): `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: FAIL — `test_sprite_tem_chevron_down_e_up` (AssertionError)

- [ ] **Step 3: Adicionar os símbolos ao sprite**

Em `portal/templates/_partials/_feather.html`, logo após a linha do
`fi-chevron-right`:

```html
  <symbol id="fi-chevron-down" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></symbol>
  <symbol id="fi-chevron-up" viewBox="0 0 24 24"><path d="M18 15l-6-6-6 6"/></symbol>
```

(Mesma convenção dos existentes: `chevron-left` é `M15 18l-6-6 6-6`,
`chevron-right` é `M9 18l6-6-6-6`.)

- [ ] **Step 4: Rodar e ver passar**

Run: `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add portal/catalog/tests/test_seta_secoes.py portal/templates/_partials/_feather.html
git commit -m "feat(front): ícones chevron down/up no sprite feather"
```

---

### Task 2: Parcial `_seta_secoes.html`

**Files:**
- Create: `portal/templates/_partials/_seta_secoes.html`
- Test: `portal/catalog/tests/test_seta_secoes.py`

- [ ] **Step 1: Adicionar o teste do parcial (falhando)**

Ao fim de `test_seta_secoes.py`:

```python
def test_parcial_da_seta_e_melhoria_progressiva():
    parcial = _template("_partials/_seta_secoes.html")
    assert "data-seta-secoes" in parcial
    assert "hidden" in parcial  # sem JS, a seta não aparece
    assert "aria-label" in parcial
    assert 'type="button"' in parcial
    assert "fi-chevron-down" in parcial
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: FAIL — `FileNotFoundError` no novo teste

- [ ] **Step 3: Criar o parcial**

Criar `portal/templates/_partials/_seta_secoes.html`:

```html
{% comment %}
Seta-guia de seções — botão flutuante que rola até a próxima seção lógica
da página (âncoras [data-sec]). Melhoria progressiva: renderiza oculto
([hidden]) e o seta-secoes.js revela; sem JS a página funciona normalmente.
Spec: docs/superpowers/specs/2026-07-29-seta-secoes-design.md
{% endcomment %}
<button type="button"
        class="sp-seta-secoes"
        data-seta-secoes
        aria-label="Ir para a próxima seção"
        hidden>
  <svg class="fi" aria-hidden="true"><use href="#fi-chevron-down"/></svg>
</button>
```

- [ ] **Step 4: Rodar e ver passar**

Run: `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add portal/catalog/tests/test_seta_secoes.py portal/templates/_partials/_seta_secoes.html
git commit -m "feat(front): parcial da seta-guia de seções"
```

---

### Task 3: Âncoras `data-sec` e inclusão nos dois templates

**Files:**
- Modify: `portal/templates/home.html` (linhas 7, 45, 62, 94, 132, 158-163)
- Modify: `portal/templates/collection_list.html` (linhas 2, 16, 31, 81, 118-119)
- Test: `portal/catalog/tests/test_seta_secoes.py`

- [ ] **Step 1: Adicionar os testes das páginas (falhando)**

Ao fim de `test_seta_secoes.py`:

```python
def test_home_tem_5_ancoras_e_a_seta():
    home = _template("home.html")
    assert home.count("data-sec=") == 5
    assert "_partials/_seta_secoes.html" in home
    assert "js/seta-secoes.js" in home


def test_colecoes_tem_3_ancoras_e_a_seta():
    colecoes = _template("collection_list.html")
    assert colecoes.count("data-sec=") == 3
    assert "_partials/_seta_secoes.html" in colecoes
    assert "js/seta-secoes.js" in colecoes
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: FAIL — os 2 testes novos (AssertionError em `count`)

- [ ] **Step 3: Editar `home.html`**

As cinco tags `<section>` ganham `data-sec` (o rótulo vira o aria-label
"Ir para: …" da seta):

| Linha | De | Para |
|---|---|---|
| 7 | `<section class="hero">` | `<section class="hero" data-sec="Busca no acervo">` |
| 45 | `<section class="stats" aria-label="Indicadores do acervo">` | `<section class="stats" data-sec="Acervo em números" aria-label="Indicadores do acervo">` |
| 62 | `<section class="sp-section">` | `<section class="sp-section" data-sec="Coleções e temas">` |
| 94 | `<section class="sp-section home-etapas">` | `<section class="sp-section home-etapas" data-sec="Etapas da contratação">` |
| 132 | `<section class="sp-section sp-section--alt">` | `<section class="sp-section sp-section--alt" data-sec="Temas em alta">` |

Antes do `{% endblock %}` do `content_raw` (após a última `</section>`),
incluir o parcial; e no `extra_js`, o script:

```html
{% include "_partials/_seta_secoes.html" %}
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/home.js' %}" defer></script>
<script src="{% static 'js/seta-secoes.js' %}" defer></script>
{% endblock %}
```

- [ ] **Step 4: Editar `collection_list.html`**

Linha 2: `{% load catalog_tags %}` → `{% load static catalog_tags %}`
(o template não carregava `static`; o script precisa).

As três tags `<section>`:

| Linha | De | Para |
|---|---|---|
| 16 | `<section class="sp-section colecoes-hero">` | `<section class="sp-section colecoes-hero" data-sec="Coleções">` |
| 31 | `<section class="sp-section sp-section--alt">` | `<section class="sp-section sp-section--alt" data-sec="Como o acervo se organiza">` |
| 81 | `<section class="sp-section">` | `<section class="sp-section" data-sec="Como encontrar o que você procura">` |

Antes do `{% endblock %}` final, incluir o parcial e criar o bloco de script
(o template não tinha `extra_js`):

```html
{% include "_partials/_seta_secoes.html" %}
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/seta-secoes.js' %}" defer></script>
{% endblock %}
```

- [ ] **Step 5: Rodar e ver passar**

Run: `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Commit**

```bash
git add portal/catalog/tests/test_seta_secoes.py portal/templates/home.html portal/templates/collection_list.html
git commit -m "feat(front): âncoras data-sec e seta-guia na Home e em Coleções"
```

---

### Task 4: CSS — componente, scroll-margin, hero peek, reduced-motion

**Files:**
- Modify: `portal/static/css/portal.css` (apêndice ao FIM do arquivo)
- Test: `portal/catalog/tests/test_seta_secoes.py`

- [ ] **Step 1: Adicionar o teste do CSS (falhando)**

Ao fim de `test_seta_secoes.py`:

```python
def test_css_tem_componente_ancoras_e_offset_do_banner():
    css = (STATIC / "css" / "portal.css").read_text(encoding="utf-8")
    assert ".sp-seta-secoes" in css
    assert "[data-sec]" in css  # scroll-margin-top das âncoras
    assert "--sp-seta-offset" in css  # desvio do banner LGPD
    assert css.index(".sp-seta-secoes") > css.index(".sp-banner-cookies")  # bloco novo no fim
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: FAIL — `test_css_tem_componente_ancoras_e_offset_do_banner`

- [ ] **Step 3: Apêndice ao FIM de `portal.css`**

```css
/* ============================================================
   Seta-guia de seções (Home e Coleções)
   Botão flutuante que rola até a próxima seção lógica da página
   (âncoras [data-sec]); na última, vira "Voltar ao topo".
   Melhoria progressiva: renderiza [hidden]; seta-secoes.js revela.
   Spec: docs/superpowers/specs/2026-07-29-seta-secoes-design.md
   ============================================================ */
[data-sec] { scroll-margin-top: 100px; }   /* header sticky — mesmo valor de .tema-grupo */

.sp-seta-secoes {
  position: fixed;
  right: 24px;
  /* --sp-seta-offset sobe a seta enquanto o banner LGPD está visível */
  bottom: calc(24px + var(--sp-seta-offset, 0px));
  z-index: 900;                            /* sob o banner de cookies (1000) */
  width: 48px; height: 48px;
  display: inline-flex; align-items: center; justify-content: center;
  border: var(--border); border-radius: 6px;
  background: var(--sp-white); color: var(--sp-black);
  box-shadow: 0 4px 14px rgb(0 0 0 / 0.14);
  font-size: 20px;
  opacity: 0;                              /* revelado com fade via .is-on */
  transition: background-color 180ms ease, border-color 180ms ease,
              color 180ms ease, opacity 260ms ease, bottom 180ms ease;
}
.sp-seta-secoes.is-on { opacity: 1; }
/* Vermelho AA-safe no hover/foco (mesma regra do .sp-button-primary) */
.sp-seta-secoes:hover, .sp-seta-secoes:focus-visible {
  background: var(--sp-red-dark); border-color: var(--sp-red-dark); color: var(--sp-white);
}

@media (max-width: 767px) {
  .sp-seta-secoes {
    width: 44px; height: 44px; right: 16px;
    bottom: calc(16px + var(--sp-seta-offset, 0px)); font-size: 18px;
  }
}

/* Anti-falso-fundo (Home): em telas baixas o hero encolhe para o título
   "Acervo em números" espiar na dobra. Este bloco fica no fim do arquivo
   de propósito: vence, pela ordem, o padding de 56px do media
   (min-width: 1024px) da seção do hero. */
@media (max-height: 900px) {
  .hero__inner { padding-block: 36px; }
  .hero__geometry { margin-top: 20px; }
}

@media print { .sp-seta-secoes { display: none; } }

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }          /* rolagem instantânea */
  .sp-seta-secoes { transition: none; }
}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add portal/catalog/tests/test_seta_secoes.py portal/static/css/portal.css
git commit -m "feat(front): estilos da seta-guia e peek anti-falso-fundo do hero"
```

---

### Task 5: JS — `seta-secoes.js`

**Files:**
- Create: `portal/static/js/seta-secoes.js`
- Test: `portal/catalog/tests/test_seta_secoes.py`

- [ ] **Step 1: Adicionar o teste do JS (falhando)**

Ao fim de `test_seta_secoes.py`:

```python
def test_js_da_seta_existe_e_e_csp_safe():
    js = (STATIC / "js" / "seta-secoes.js").read_text(encoding="utf-8")
    assert "data-seta-secoes" in js
    assert "data-sec" in js
    assert "addEventListener" in js  # CSP-safe: sem handlers inline
    assert "prefers-reduced-motion" in js
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: FAIL — `FileNotFoundError`

- [ ] **Step 3: Criar `portal/static/js/seta-secoes.js`**

Estilo do arquivo segue `home.js`: IIFE ES5, módulo-objeto com `init()`,
`try/catch` na inicialização, CSP-safe.

```javascript
/*
 * seta-secoes.js — seta-guia de seções (Home e Coleções).
 *
 * Botão flutuante ([data-seta-secoes]) que rola até a próxima seção lógica
 * da página (âncoras [data-sec], na ordem do DOM). Na última seção, vira
 * "Voltar ao topo". Desloca-se para cima do banner de cookies LGPD enquanto
 * ele estiver visível. Melhoria progressiva: sem JS a seta permanece
 * [hidden]. CSP-safe: apenas addEventListener, sem handlers inline.
 * Spec: docs/superpowers/specs/2026-07-29-seta-secoes-design.md
 */
(function () {
    'use strict';

    function reduzMovimento() {
        return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    var Seta = {
        init: function () {
            this.btn = document.querySelector('[data-seta-secoes]');
            this.secoes = Array.prototype.slice.call(document.querySelectorAll('[data-sec]'));
            if (!this.btn || this.secoes.length < 2 || !window.IntersectionObserver) return;

            this.uso = this.btn.querySelector('use');
            this.visiveis = [];

            this.btn.addEventListener('click', this.onClick.bind(this));
            this.observarSecoes();
            this.observarBanner();
            this.atualizar();
            this.revelar();
        },

        /* Seção "corrente" = a de maior índice com o topo acima do meio da
           tela. O rootMargin restringe o observer à metade de cima do
           viewport; reflows (ex.: "Carregar mais temas") reobservam sozinhos. */
        observarSecoes: function () {
            var self = this;
            this.io = new IntersectionObserver(function (entries) {
                for (var i = 0; i < entries.length; i++) {
                    var idx = self.secoes.indexOf(entries[i].target);
                    if (idx >= 0) self.visiveis[idx] = entries[i].isIntersecting;
                }
                self.atualizar();
            }, { rootMargin: '0px 0px -50% 0px', threshold: 0 });
            for (var i = 0; i < this.secoes.length; i++) {
                this.io.observe(this.secoes[i]);
            }
        },

        correnteIdx: function () {
            for (var i = this.secoes.length - 1; i >= 0; i--) {
                if (this.visiveis[i]) return i;
            }
            return 0;
        },

        naUltima: function () {
            return this.correnteIdx() >= this.secoes.length - 1;
        },

        atualizar: function () {
            if (this.naUltima()) {
                this.uso.setAttribute('href', '#fi-chevron-up');
                this.btn.setAttribute('aria-label', 'Voltar ao topo');
            } else {
                var proxima = this.secoes[this.correnteIdx() + 1];
                this.uso.setAttribute('href', '#fi-chevron-down');
                this.btn.setAttribute('aria-label', 'Ir para: ' + proxima.getAttribute('data-sec'));
            }
        },

        onClick: function () {
            var alvo;
            if (this.naUltima()) {
                alvo = this.secoes[0];
                window.scrollTo({ top: 0, behavior: reduzMovimento() ? 'auto' : 'smooth' });
            } else {
                alvo = this.secoes[this.correnteIdx() + 1];
                alvo.scrollIntoView({ behavior: reduzMovimento() ? 'auto' : 'smooth', block: 'start' });
            }
            this.focar(alvo);   // teclado/leitor de tela acompanham a navegação
        },

        focar: function (el) {
            if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
            el.focus({ preventScroll: true });
        },

        /* Banner LGPD: faixa fixa no rodapé até o consentimento. Enquanto
           visível, publica a altura em --sp-seta-offset para a seta subir. */
        observarBanner: function () {
            this.banner = document.querySelector('[data-cookies-banner]');
            if (!this.banner) return;
            var ajustar = this.ajustarOffset.bind(this);
            if (window.MutationObserver) {
                this.mo = new MutationObserver(ajustar);
                this.mo.observe(this.banner, { attributes: true, attributeFilter: ['hidden'] });
            }
            window.addEventListener('resize', ajustar);
            this.ajustarOffset();
        },

        ajustarOffset: function () {
            var visivel = this.banner && !this.banner.hasAttribute('hidden');
            var altura = visivel ? this.banner.offsetHeight + 12 : 0;
            document.documentElement.style.setProperty('--sp-seta-offset', altura + 'px');
        },

        /* Revela com fade: sai do [hidden] e só então .is-on transiciona a
           opacidade (dois rAFs para o display mudar antes da transição). */
        revelar: function () {
            var btn = this.btn;
            btn.removeAttribute('hidden');
            requestAnimationFrame(function () {
                requestAnimationFrame(function () { btn.classList.add('is-on'); });
            });
        }
    };

    function init() {
        try { Seta.init(); } catch (e) { console.error('[BDLP] Seta init falhou:', e); }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
```

- [ ] **Step 4: Rodar e ver passar**

Run: `py -m pytest catalog/tests/test_seta_secoes.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add portal/catalog/tests/test_seta_secoes.py portal/static/js/seta-secoes.js
git commit -m "feat(front): comportamento da seta-guia de seções"
```

---

### Task 6: Suíte completa + lint (como o CI)

**Files:** nenhum novo (verificação).

- [ ] **Step 1: Lint**

Run (raiz do repo): `ruff check portal/`
Expected: sem erros (a feature não toca Python além do teste; linha ≤ 120).

- [ ] **Step 2: Suíte completa**

Run (em `portal/`, PowerShell):
`$env:DJANGO_SECRET_KEY = 'ci-dummy-secret-key-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'; py -m pytest -v`
Expected: PASS — testes de taxonomia + os 6 novos, 0 falhas.

---

### Task 7: Verificação no navegador (rebuild + checklist)

O portal é **baked na imagem** — mudança de template/CSS/JS só aparece após
rebuild. No Windows, a porta do portal é **8001** (via `.env`, `PORTAL_PORT`).

- [ ] **Step 1: Rebuild e subida**

Run (raiz do repo): `docker compose build portal; docker compose up -d`
Expected: containers `lilp-bdlp-*` de pé; portal responde em `http://localhost:8001/`.

- [ ] **Step 2: Checklist visual/funcional (navegador embutido)**

Na **Home** (`http://localhost:8001/`) e em **Coleções**
(`http://localhost:8001/colecoes/`):

1. Seta aparece com fade no canto inferior direito; rótulo acessível
   "Ir para: Acervo em números" (Home) / "Ir para: Como o acervo se organiza" (Coleções).
2. Cliques sucessivos percorrem todas as seções na ordem; na última, o ícone
   vira chevron-up com "Voltar ao topo"; clique volta ao topo e a seta volta
   a apontar para baixo.
3. Rolagem manual até o fim → seta vira "Voltar ao topo" sozinha (IntersectionObserver).
4. Teclado: Tab alcança a seta (foco visível), Enter navega, foco vai para a
   seção alvo.
5. Banner LGPD: limpar a chave `sp-lgpd-consent` do localStorage e recarregar
   → banner aparece e a seta fica ACIMA dele; aceitar cookies → seta desce.
6. Fonte A+ (2 cliques): nada clipa; seta continua utilizável.
7. Alto contraste (botão ◐): seta legível.
8. Viewport 375×812 (mobile): seta 44px, não cobre conteúdo essencial.
9. Viewport com ~800px de altura: título "Acervo em números" espia na dobra
   da Home (peek anti-falso-fundo).
10. Reduced motion (emulação do DevTools): navegação instantânea, sem fade.
11. Sem JS (desabilitar JS no DevTools): seta não aparece; página normal.

- [ ] **Step 3: Corrigir o que falhar e re-conferir**

Qualquer ajuste → repetir o item do checklist afetado + `py -m pytest -v`.

- [ ] **Step 4: Commit final (se houve ajustes)**

```bash
git add -A
git commit -m "fix(front): ajustes da verificação em navegador da seta-guia"
```

---

## Fora do plano

- Push/PR: decidir com o usuário ao final (skill finishing-a-development-branch).
- Nada de scroll-snap, nada de hero 100svh (rejeitados no spec).
- Acervo (`search.html`), detalhe de documento, Sobre e páginas legais ficam intocados.
