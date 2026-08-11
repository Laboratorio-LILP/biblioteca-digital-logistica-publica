# Estado de chegada da seta-guia — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A seta-guia nasce como pílula vermelha "Veja mais" para quem chega ao topo da página e assenta para o quadrado discreto atual no primeiro gesto (scroll > 24 px ou clique).

**Architecture:** Um estado novo (`is-chegada`) somado ao componente existente — sem markup novo nas páginas, sem dependências. O parcial ganha um `<span>` de rótulo; o CSS ganha o bloco do estado (pílula + colapso por `max-width`/`opacity`); o JS aplica o estado no reveal (só se `scrollY ≤ 24`) e o remove no primeiro gesto, ajustando o `aria-label` (WCAG 2.5.3).

**Tech Stack:** Django templates, CSS puro, JS ES5 vanilla (padrão do arquivo), pytest (testes de invariante de arquivo, sem banco).

**Spec:** `docs/superpowers/specs/2026-08-10-seta-enfase-chegada-design.md`

## Global Constraints

- Vermelho de ênfase: `var(--sp-red-dark)` (#BD0E15) com texto/ícone brancos — mesma dupla AA do `.sp-button-primary`. Nunca `--sp-red` puro sob texto branco.
- Rótulo visível: exatamente "Veja mais". `aria-label` na chegada: `"Veja mais: 〈seção〉"`; assentado: `"Ir para: 〈seção〉"` (formato atual).
- Limiar do primeiro gesto: `window.scrollY > 24` (e clique na seta). Chegada só se a página abriu com `scrollY <= 24`.
- Melhoria progressiva intocada: o botão continua nascendo `[hidden]`; sem JS, nada aparece.
- JS no estilo do arquivo: ES5 (`var`, `function`), CSP-safe (só `addEventListener`), comentários em pt-BR.
- `prefers-reduced-motion`: transições zeradas, mas a pílula aparece igual (ênfase não depende de movimento).
- Testes: invariantes de arquivo em `portal/catalog/tests/test_seta_secoes.py`, no estilo dos existentes. Rodar com `pytest` do host (`/opt/homebrew/bin/pytest`), a partir da raiz do repo.
- Commits pequenos, um por tarefa, mensagem em pt-BR com trailer `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: Rótulo "Veja mais" no parcial

**Files:**
- Modify: `portal/templates/_partials/_seta_secoes.html`
- Test: `portal/catalog/tests/test_seta_secoes.py`

**Interfaces:**
- Consumes: nada de tarefas anteriores.
- Produces: `<span class="sp-seta-secoes__rotulo">Veja mais</span>` dentro do botão — a Task 2 estiliza exatamente essa classe; a Task 3 não toca o parcial.

- [ ] **Step 1: Write the failing test**

Acrescentar ao fim de `portal/catalog/tests/test_seta_secoes.py`:

```python
def test_parcial_tem_rotulo_de_chegada():
    parcial = _template("_partials/_seta_secoes.html")
    assert "sp-seta-secoes__rotulo" in parcial
    assert "Veja mais" in parcial
    assert re.search(r"<button[^>]*\shidden[\s>]", parcial)  # melhoria progressiva intacta
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest portal/catalog/tests/test_seta_secoes.py::test_parcial_tem_rotulo_de_chegada -v`
Expected: FAIL — `assert "sp-seta-secoes__rotulo" in parcial` (AssertionError)

- [ ] **Step 3: Write minimal implementation**

Conteúdo final de `portal/templates/_partials/_seta_secoes.html` (o span entra antes do svg; resto igual):

```html
{% comment %}
Seta-guia de seções — botão flutuante que rola até a próxima seção lógica
da página (âncoras [data-sec]). Melhoria progressiva: renderiza oculto
([hidden]) e o seta-secoes.js revela; sem JS a página funciona normalmente.
Na chegada (página aberta no topo), vira pílula "Veja mais" até o primeiro
gesto — ver spec 2026-08-10-seta-enfase-chegada-design.md.
Spec do componente: docs/superpowers/specs/2026-07-29-seta-secoes-design.md
{% endcomment %}
<button type="button"
        class="sp-seta-secoes"
        data-seta-secoes
        aria-label="Ir para a próxima seção"
        hidden>
  <span class="sp-seta-secoes__rotulo">Veja mais</span>
  <svg class="fi" aria-hidden="true"><use href="#fi-chevron-down"/></svg>
</button>
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest portal/catalog/tests/test_seta_secoes.py -v`
Expected: PASS (7 testes — os 6 existentes seguem verdes)

- [ ] **Step 5: Commit**

```bash
git add portal/templates/_partials/_seta_secoes.html portal/catalog/tests/test_seta_secoes.py
git commit -m "feat(front): rótulo 'Veja mais' no parcial da seta-guia

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: CSS do estado de chegada

**Files:**
- Modify: `portal/static/css/portal.css` (bloco "Seta-guia de seções", ~linhas 959–1015)
- Test: `portal/catalog/tests/test_seta_secoes.py`

**Interfaces:**
- Consumes: classe `sp-seta-secoes__rotulo` no parcial (Task 1).
- Produces: seletores `.sp-seta-secoes.is-chegada` e `.sp-seta-secoes__rotulo` — a Task 3 alterna a classe `is-chegada` no botão; nenhum outro nome novo.

- [ ] **Step 1: Write the failing test**

Acrescentar ao fim de `portal/catalog/tests/test_seta_secoes.py`:

```python
def test_css_tem_estado_de_chegada():
    css = (STATIC / "css" / "portal.css").read_text(encoding="utf-8")
    assert ".sp-seta-secoes.is-chegada" in css
    assert ".sp-seta-secoes__rotulo" in css
    assert "--sp-red-dark" in css[css.index(".sp-seta-secoes.is-chegada"):]  # pílula AA-safe
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest portal/catalog/tests/test_seta_secoes.py::test_css_tem_estado_de_chegada -v`
Expected: FAIL — `assert ".sp-seta-secoes.is-chegada" in css`

- [ ] **Step 3: Write minimal implementation**

Três edições em `portal/static/css/portal.css`.

(a) Na regra base `.sp-seta-secoes`, trocar a linha `width: 48px; height: 48px;` e acrescentar `padding`/`gap` (com `width: auto` o padding do UA entraria em cena — zeramos) e a transição de `padding`:

```css
.sp-seta-secoes {
  position: fixed;
  right: 24px;
  /* --sp-seta-offset sobe a seta enquanto o banner LGPD está visível */
  bottom: calc(24px + var(--sp-seta-offset, 0px));
  z-index: 900;                            /* sob o banner de cookies (1000) */
  width: auto; min-width: 48px; height: 48px;
  padding: 0;                              /* sem gap aqui: com o rótulo em max-width 0, um gap na base descentralizaria o chevron */
  display: inline-flex; align-items: center; justify-content: center;
  border: var(--border); border-radius: 6px;
  background: var(--sp-white); color: var(--sp-black);
  box-shadow: 0 4px 14px rgb(0 0 0 / 0.14);
  font-size: 20px;
  opacity: 0;                              /* revelado com fade via .is-on */
  transition: background-color 180ms ease, border-color 180ms ease,
              color 180ms ease, opacity 260ms ease, bottom 180ms ease,
              padding 220ms ease, gap 220ms ease;
}
```

(b) Logo após a regra de hover/focus-visible existente, inserir o bloco do estado:

```css
/* Estado de chegada: pílula "Veja mais" até o primeiro gesto (scroll >24px
   ou clique na seta) — depois assenta para o quadrado discreto acima.
   Colapso anima por max-width/opacity do rótulo + padding do botão.
   Spec: docs/superpowers/specs/2026-08-10-seta-enfase-chegada-design.md */
.sp-seta-secoes__rotulo {
  display: inline-block;
  max-width: 0; overflow: hidden; white-space: nowrap;
  opacity: 0;
  font-family: var(--font-subtitle); font-weight: 600; font-size: 15px;
  transition: max-width 220ms ease, opacity 180ms ease;
}
.sp-seta-secoes.is-chegada {
  padding: 0 18px; gap: 8px;
  background: var(--sp-red-dark); border-color: var(--sp-red-dark);
  color: var(--sp-white);
}
.sp-seta-secoes.is-chegada .sp-seta-secoes__rotulo { max-width: 120px; opacity: 1; }
```

(c) No media query mobile existente, trocar `width: 44px;` por `min-width: 44px;`, e no bloco `@media (prefers-reduced-motion: reduce)` existente acrescentar o rótulo:

```css
@media (max-width: 767px) {
  .sp-seta-secoes {
    min-width: 44px; height: 44px; right: 16px;
    bottom: calc(16px + var(--sp-seta-offset, 0px)); font-size: 18px;
  }
}
```

```css
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }          /* rolagem instantânea */
  .sp-seta-secoes, .sp-seta-secoes__rotulo { transition: none; }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest portal/catalog/tests/test_seta_secoes.py -v`
Expected: PASS (8 testes)

- [ ] **Step 5: Commit**

```bash
git add portal/static/css/portal.css portal/catalog/tests/test_seta_secoes.py
git commit -m "feat(front): estilos do estado de chegada da seta-guia (pílula 'Veja mais')

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: JS — aplicar a chegada e assentar no primeiro gesto

**Files:**
- Modify: `portal/static/js/seta-secoes.js`
- Test: `portal/catalog/tests/test_seta_secoes.py`

**Interfaces:**
- Consumes: classe `is-chegada` (Task 2) e o parcial com rótulo (Task 1).
- Produces: métodos `aoRolar()` e `assentar()` no objeto `Seta`; flag `this.chegada`. Nada consome depois — é a última tarefa de código.

- [ ] **Step 1: Write the failing test**

Acrescentar ao fim de `portal/catalog/tests/test_seta_secoes.py`:

```python
def test_js_tem_chegada_que_assenta_no_primeiro_gesto():
    js = (STATIC / "js" / "seta-secoes.js").read_text(encoding="utf-8")
    assert "is-chegada" in js
    assert "Veja mais: " in js   # WCAG 2.5.3 — nome acessível contém o rótulo visível
    assert "assentar" in js
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest portal/catalog/tests/test_seta_secoes.py::test_js_tem_chegada_que_assenta_no_primeiro_gesto -v`
Expected: FAIL — `assert "is-chegada" in js`

- [ ] **Step 3: Write minimal implementation**

Quatro edições em `portal/static/js/seta-secoes.js`.

(a) Em `init()`, logo após `this._renderizado = -1;`:

```js
            /* Estado de chegada (pílula "Veja mais"): só se a página abriu no
               topo — o falso fundo não existe em página já rolada. Assenta no
               primeiro gesto (aoRolar/onClick → assentar). */
            this.chegada = window.scrollY <= 24;
            if (this.chegada) {
                this.btn.classList.add('is-chegada');
                this._aoRolar = this.aoRolar.bind(this);
                window.addEventListener('scroll', this._aoRolar, { passive: true });
            }
```

(b) Em `atualizar()`, trocar a linha do `aria-label` do ramo "não é a última" por:

```js
                var rotulo = this.chegada ? 'Veja mais: ' : 'Ir para: ';
                this.btn.setAttribute('aria-label', rotulo + proxima.getAttribute('data-sec'));
```

(c) Em `onClick()`, primeira linha do corpo:

```js
            this.assentar();
```

(d) Após o método `onClick` (antes de `focar`), os dois métodos novos:

```js
        aoRolar: function () {
            if (window.scrollY > 24) this.assentar();
        },

        /* Primeiro gesto: a pílula colapsa para o quadrado discreto e o
           aria-label volta ao padrão "Ir para: …". Idempotente. */
        assentar: function () {
            if (!this.chegada) return;
            this.chegada = false;
            this.btn.classList.remove('is-chegada');
            window.removeEventListener('scroll', this._aoRolar);
            this._renderizado = -1;   // força re-render do aria-label
            this.atualizar();
        },
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest portal/catalog/tests/test_seta_secoes.py -v`
Expected: PASS (9 testes)

- [ ] **Step 5: Commit**

```bash
git add portal/static/js/seta-secoes.js portal/catalog/tests/test_seta_secoes.py
git commit -m "feat(front): seta-guia chega como pílula e assenta no primeiro gesto

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Verificação integrada (rebuild + browser)

**Files:**
- Nenhum arquivo novo — verificação. Correções que surgirem entram em commits `fix(front):` próprios.

**Interfaces:**
- Consumes: Tasks 1–3 completas.
- Produces: evidência de validação (checklist da spec §4).

- [ ] **Step 1: Suíte completa + lint (paridade com o CI)**

Run: `pytest portal/catalog/tests/ -q && ruff check portal`
Expected: todos os testes PASS; ruff sem apontamentos

- [ ] **Step 2: Rebuild da imagem (portal é baked, sem bind-mount)**

Run: `docker compose --env-file .env -f docker/docker-compose.yml up -d --build`
Expected: os três containers sobem; postgres `healthy`

- [ ] **Step 3: Checklist no browser (Home e Coleções)**

Em `http://localhost:8000/` e `http://localhost:8000/colecoes/`:

- Chegada: pílula vermelha "Veja mais" no canto inferior direito, chevron branco.
- Rolar > 24 px: pílula colapsa para o quadrado branco; recarregar repete a chegada.
- Deep link (ex.: `http://localhost:8000/#sp-busca` já rolado): chegada é pulada.
- Clique na pílula: navega para a próxima seção E assenta.
- `aria-label` na chegada = "Veja mais: 〈seção〉" (inspecionar o botão); depois volta a "Ir para: 〈seção〉".
- Teclado: Tab até a seta, Enter navega.
- Banner LGPD visível (limpar `localStorage` chave `sp-lgpd-consent`): pílula sobe junto.
- Viewport 375 px: pílula cabe sem sobrepor conteúdo.
- `prefers-reduced-motion` (emulação do DevTools): pílula aparece, colapso instantâneo.
- Console sem erros.

- [ ] **Step 4: Encerrar**

Sem commit próprio (tarefas 1–3 já commitaram). Reportar o resultado do checklist.
