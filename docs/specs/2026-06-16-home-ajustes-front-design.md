# Ajustes de front-end na Home — design

**Data:** 2026-06-16
**Frente:** BDLP (portal Django)
**Escopo:** 4 ajustes na página inicial (`home.html`), mantendo identidade visual GESP e a estrutura aprovada da Home. a11y WCAG 2 AA; Linguagem Simples nos textos de interface.

---

## Contexto

A Home tem hoje quatro blocos relevantes para estes ajustes:

- **"Explorar o acervo"** — uma única grade (`collections-grid`) que mistura, sem distinção, as **4 Coleções formais** e **2 cards temáticos** (Lei 14.133/21 e Sustentabilidade e ODS).
- **"Comece pela etapa"** — stepper horizontal das **4 etapas** (núcleo) + **2 "Visões transversais"** como chips alinhados à esquerda (`etapas-trans`).
- **"Temas em alta"** — um bloco por tema (hoje 2), cada um com até 4 documentos de preview (`doc-grid--2`).

Stack: templates Django renderizados no servidor + JS vanilla (IIFE, CSP `script-src 'self'`, sem handlers inline). Inclusão de JS por página via `{% block extra_js %}` (padrão de `acervo-filters.js`, `doc-detail.js`).

Fonte única dos temas: `TEMAS_DESTAQUE` em `portal/catalog/taxonomy_v6.py`. O mesmo filtro (`tema_busca`) alimenta a contagem do card, o link "Ver tema" e os documentos de preview — princípio de consistência que **deve ser mantido**.

---

## Item 1 — "Explorar o acervo": separar Coleções de Temas (forma A)

Dividir a seção em **dois sub-blocos rotulados**, reusando o vocabulário que a seção "Comece pela etapa" já estabelece (cards primários + chips secundários):

- **Sub-bloco "Coleções"** — as 4 Coleções formais como cards, em grade **2×2** (reaproveitar o modificador existente `collections-grid--quatro`).
- **Sub-bloco "Temas em alta"** — os **5 temas** como **chips** (não cards), em **uma linha de 5 colunas de largura igual** no desktop, com **ícone à esquerda** do nome + contagem (altura baixa e uniforme). Responsivo: quebra para 2–3 por linha em telas estreitas.

Os 5 chips, na ordem: **Lei 14.133/21** · **Sustentabilidade e ODS** · **Compras Diretas** · **Pregão** · **Registro de Preços**.

### Comportamento dos chips (liga com o Item 4)

Cada chip é uma **âncora** para o bloco do tema na seção "Temas em alta" (`href="#tema-<slug>"`):

- Sem JS: a âncora rola normalmente (todos os temas estão visíveis).
- Com JS: se o tema-alvo estiver oculto (atrás do "Carregar mais temas"), o clique **revela apenas aquele tema** (fora de ordem) e então rola até ele, movendo o foco para o bloco.

A exceção (revelar fora de ordem) **não quebra** a regra do botão "Carregar mais temas": o botão sempre revela **o primeiro tema ainda oculto** (não um índice fixo). Revelar um tema por chip apenas retira esse item do conjunto que o botão consome; o botão some quando não houver mais nenhum oculto.

---

## Item 2 — "Comece pela etapa": transversais em 2 colunas

Mudar `etapas-trans` de `flex/wrap` (alinhado à esquerda) para **grade de 2 colunas de largura total** (`grid-template-columns: repeat(2, 1fr)`), de modo que as 2 transversais cubram **a mesma distância horizontal das 4 etapas** acima, divididas ao meio. Cada chip preenche sua célula: ícone à esquerda, nome, contagem à direita.

---

## Item 3 — "Comece pela etapa": alinhar as contagens

Causa do desalinhamento: **rótulos** (1–2 linhas) e **descrições** das etapas têm alturas diferentes, empurrando a contagem para posições distintas. Correção em duas camadas, **escopadas ao layout horizontal (≥768px)**:

1. **Linha-base comum no rodapé** — as etapas já têm altura igual (stepper em linha). Empurrar a contagem para o rodapé com `margin-top:auto`, alinhando todas as contagens na mesma linha-base (robusto a mudanças de texto).
2. **Altura de rótulo reservada** — reservar altura de **2 linhas** para o rótulo (`min-height`), de modo que as descrições comecem todas na mesma altura, e rótulos de 1 ou 2 linhas ocupem o mesmo espaço.

No layout vertical (mobile), o empilhamento natural já alinha — as camadas não se aplicam lá.

---

## Item 4 — "Carregar mais" em "Temas em alta"

Duas mecânicas, por **melhoria progressiva** (servidor renderiza tudo visível; JS oculta os extras e ativa os botões):

### (a) Documentos por tema
- Cada tema disponibiliza **4 documentos** de preview (mantém `_docs_do_tema` em `base[:4]`).
- Inicialmente visíveis: **2** (1 linha do `doc-grid--2`).
- Botão **"Carregar mais documentos"** revela os outros 2 **num clique** e então **some**.

### (b) Temas
- A seção passa a ter **5 temas** (2 atuais + 3 novos).
- Inicialmente visíveis: **2** (Lei 14.133/21, Sustentabilidade e ODS).
- Botão **"Carregar mais temas"** revela **1 tema por clique**, na ordem: **Compras Diretas → Pregão → Registro de Preços**; some quando não restar nenhum oculto.
- Também revelável pelo chip correspondente em "Explorar o acervo" (ver Item 1).

### Temas novos (entradas em `TEMAS_DESTAQUE`)

Todos por **busca textual** (`query`) — não há Assunto curado correspondente no acervo. Contagens atuais: Compras Diretas 8, Pregão 19, Registro de Preços 10 (nenhum fica vazio). **Acentos importam** na busca (ex.: "Pregão" → 19; "Pregao" → 0): manter as grafias acentuadas.

| Tema | slug | query | icon | color |
|---|---|---|---|---|
| Compras Diretas | `compras-diretas` | `Compras Diretas` | `fi-package` | `c-red` |
| Pregão | `pregao` | `Pregão` | `fi-trending-up` | `c-blue` |
| Registro de Preços | `registro-precos` | `Registro de Preços` | `fi-bookmark` | `c-yellow` |

Texto `alta_intro` (Linguagem Simples), confirmado:

- **Compras Diretas:** "Materiais para entender quando e como contratar sem licitação — por dispensa ou inexigibilidade — dentro dos limites e cuidados da Lei 14.133/21."
- **Pregão:** "Materiais sobre o pregão: a modalidade usada para comprar bens e serviços comuns pelo menor preço, em geral na forma eletrônica."
- **Registro de Preços:** "Materiais sobre o Sistema de Registro de Preços (SRP) e a ata: registrar preços para contratar aos poucos, conforme a necessidade."

Texto `card_desc` (obrigatório no schema de `TEMAS_DESTAQUE`; lido por `cards_tematicos_overview`, ainda que os chips mostrem só nome + contagem):

- **Compras Diretas:** "Compras sem licitação — dispensa e inexigibilidade: quando cabem e quais os limites."
- **Pregão:** "A modalidade para comprar bens e serviços comuns pelo menor preço."
- **Registro de Preços:** "O Sistema de Registro de Preços (SRP): registrar preços para contratar quando precisar."

Os 5 temas em "Temas em alta" usam 5 cores distintas: petrol, verde, vermelho, azul, amarelo.

---

## Arquitetura da mudança

### Backend (Python)

**`portal/catalog/taxonomy_v6.py`**
- Adicionar 3 entradas a `TEMAS_DESTAQUE` (slug, label, query, icon, color, `card_desc`, `alta_intro`).

**`portal/catalog/views.py` — `home()`**
- **Item 1:** `cards_explorar` passa a conter **apenas as 4 Coleções** (remover a linha que somava `_card_tematico`). Os temas viram chips.
- Novo contexto `chips_temas = cards_tematicos_overview()` (5 temas, com slug/label/icon/color/count). O template monta a âncora `#tema-<slug>`.
- **Item 4:** `temas_em_alta` passa a iterar os 5 temas (já decorre de `TEMAS_DESTAQUE`); cada dict ganha `slug` (para o `id` da âncora). A ordem define quais ficam visíveis (2 primeiros) — o ocultamento é feito pelo JS, não pelo servidor.
- Remover `_card_tematico` se ficar sem uso (verificar na implementação). `cards_tematicos_overview` permanece (alimenta os chips).

### Templates

**`portal/templates/home.html`**
- **Item 1:** seção "Explorar o acervo" com 2 sub-blocos: rótulo "Coleções" + `collections-grid collections-grid--quatro` (4 cards); rótulo "Temas em alta" + nova grade de chips (`temas-chips`) com 5 `tema-chip` (âncora + `data-tema-target="<slug>"`).
- **Item 2/3:** seção "Comece pela etapa" — `etapas-trans` em 2 colunas; ajustes de alinhamento são CSS (sem mudança estrutural).
- **Item 4:** cada `tema-grupo` ganha `id="tema-{{ tema.slug }}"` e `data-tema="{{ tema.slug }}"`. Renderizar o botão **"Carregar mais documentos"** (com atributo `hidden`) por tema **quando `tema.docs|length > 2`**. No fim da seção, renderizar **"Carregar mais temas"** (com `hidden`). Botões no estilo `sp-button-secondary`.
- Adicionar `{% block extra_js %}<script src="{% static 'js/home.js' %}" defer></script>{% endblock %}`.

### CSS — `portal/static/css/portal.css`
- Rótulos de sub-bloco: generalizar o estilo de `etapas-trans-head` numa classe compartilhada (usada por "Coleções"/"Temas em alta" e "Visões transversais").
- `temas-chips`: grade 5 colunas no desktop, responsiva; `tema-chip` com ícone à esquerda (cor por tema, classes `c-*`).
- `etapas-trans`: grade de 2 colunas; `etapa-chip` preenche a célula (contagem à direita).
- Item 3 (escopo ≥768px): `etapa-step__lab` com `min-height` de 2 linhas; `etapa-step__count` com `margin-top:auto`; garantir que o link/txt ocupem altura total.
- Estado oculto de docs/temas e estilo dos botões "Carregar mais".

### JS — novo `portal/static/js/home.js`
IIFE, CSP-safe (apenas `addEventListener`), no-op se os elementos não existirem. Na inicialização:
- **Docs por tema:** ocultar os cards além dos 2 primeiros em cada `doc-grid--2`; revelar o botão "Carregar mais documentos" (tira o `hidden`) e ligar o handler (revela os 2 restantes e oculta o botão; `aria-expanded`).
- **Temas:** ocultar os blocos de tema além dos 2 primeiros; revelar e ligar o botão "Carregar mais temas" (revela **o primeiro tema ainda oculto** por clique; oculta o botão quando não houver mais oculto).
- **Chips (Item 1):** no clique de um `tema-chip`, localizar o bloco por `id`; se oculto, revelá-lo (apenas ele) e rolar até ele (respeitando `prefers-reduced-motion`), movendo o foco para o bloco.

Contrato de dados/atributos:
- Bloco do tema: `id="tema-<slug>"`, `data-tema="<slug>"`.
- Chip: `href="#tema-<slug>"`, `data-tema-target="<slug>"`.
- Botões renderizados com `hidden`; o JS os ativa. Sem JS, ficam ocultos (seriam inertes) e todo o conteúdo aparece — nada fica preso.

---

## Acessibilidade
- Botões reais (`<button>`), foco visível, `aria-expanded` refletindo o estado.
- Reveal move o foco para o conteúdo revelado; rolagem respeita `prefers-reduced-motion`.
- Sem JS, 100% do conteúdo é acessível (chips funcionam como âncoras nativas).
- Contraste e Linguagem Simples mantidos (paleta GESP, classes `c-*`).

## Testes / verificação
- `make validate` (ruff + pytest + `manage.py check --deploy`).
- Verificação visual no preview: os 4 itens, com e sem JS (degradação graciosa), desktop e mobile.
- Conferir que contagem do chip == contagem do "Ver tema" == origem dos docs de preview (consistência preservada).

## Fora de escopo (registrado)
- **PCA com 0 documentos:** a etapa "Plano de Contratações Anual (PCA)" aparece com "0 documentos" (link levaria a busca vazia). Não faz parte destes 4 ajustes; fica registrado para decisão futura.

---

## Ajustes pós-implementação (2026-06-16)

Dois refinamentos após verificação visual da entrega inicial:

### A1 — Rolagem do chip parando no título do tema
O `.site-header` é `position: sticky` (~85px). O `scrollIntoView({block:'start'})` do chip alinhava o topo do bloco ao topo da viewport, deixando o **título do tema coberto pelo header** (parecia rolar até os documentos). **Correção:** `scroll-margin-top: 100px` no `.tema-grupo` (alvo da âncora `#tema-<slug>`). Desloca o destino para abaixo do header, com o título visível. CSS puro; vale também para o salto de âncora nativo (sem JS). Sem mudança no JS.

### A2 — Remoção do "Carregar mais documentos"
O par "Carregar mais documentos" (por tema) + "Carregar mais temas" (seção) ficava visualmente poluído. **Decisão:** remover a expansão de documentos por tema. Cada tema passa a mostrar **sempre 2 documentos** (1 linha); o tema completo continua a um clique pelo "Ver tema no acervo" (já no cabeçalho). Mantém-se apenas o "Carregar mais temas". **Revisa o Item 4(a)** original (que previa 4 docs/tema com expansão).

Mudanças: `_docs_do_tema` → `base[:2]`; remoção do botão `data-mais-docs` e do `{% if tema.docs|length > 2 %}` no template; remoção de `.tema-grupo__more` na CSS; remoção da função `initDocs` e da constante `DOCS_VISIVEIS` no `home.js` (que passa a tratar só revelação de temas e chips). Simplifica template, CSS e JS.
