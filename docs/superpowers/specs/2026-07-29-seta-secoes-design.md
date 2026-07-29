# Seta-guia de seções — Home e Coleções (design)

- **Data:** 2026-07-29
- **Origem:** preocupação da Lina — visitantes podem não rolar a página ao entrar
  na plataforma e perder o conteúdo principal por não saberem que ele existe.
- **Escopo:** páginas Início (Home) e Coleções. Ficam de fora: Acervo (busca),
  detalhe de documento, detalhe de coleção, Sobre e páginas legais.

## Problema

O medo da Lina tem nome na literatura de usabilidade: **falso fundo** (illusion of
completeness) — a pessoa não rola porque a tela parece terminar ali. A correção
tem duas frentes: dar um sinal explícito de que há mais conteúdo (a seta) e
garantir que o conteúdo seguinte "espie" na dobra da tela (peek).

## Decisões tomadas em conversa

1. **Âncoras invisíveis, layout intacto.** As seções são os `<section>` que já
   existem no HTML; nada muda de lugar nem de ordem. Fullpage/scroll-snap foi
   rejeitado: quebra acessibilidade (A+/A−, teclado, leitor de tela) e cria falso
   fundo em toda tela.
2. **Sem hero em tela cheia.** A ideia foi considerada e revertida: esticar o hero
   para 100 % da tela fabricaria o falso fundo na primeira dobra. No lugar,
   boas práticas anti-falso-fundo com ajustes pontuais (seção 3 abaixo).
3. **Escopo Home + Coleções.** São as duas páginas com blocos visuais reais
   (Home: 5 seções; Coleções: 3). As demais são leitura corrida ou têm altura
   dinâmica.

## Design

### 1. Âncoras invisíveis

Os `<section>` existentes recebem `data-sec="rótulo"` e `tabindex="-1"`:

| Página | Paradas (em ordem) |
|---|---|
| Home | Busca (hero) → Acervo em números → Coleções → Etapas da contratação → Temas em alta |
| Coleções | Coleções (cards) → Como cada documento é classificado → Como encontrar |

- `scroll-margin-top: 100px` nas âncoras — compensa o cabeçalho sticky
  (mesmo valor já usado em `.tema-grupo`).
- O rótulo alimenta o `aria-label` dinâmico da seta (ex.: "Ir para: Acervo em
  números").

### 2. Seta-guia (componente novo)

**Estrutura.** Parcial `_partials/_seta_secoes.html` com
`<button type="button" class="sp-seta-secoes" data-seta-secoes>` e chevron do
sprite feather. Incluído apenas em `home.html` e `collection_list.html`.
Renderiza com `hidden`; o JS revela (progressive enhancement — sem JS, sem seta,
página funciona normalmente).

**Visual.** Botão fixo no canto inferior direito; 48 px no desktop, 44 px no
mobile (alvo mínimo eMAG/WCAG); fundo branco, borda `var(--border)`, raio 6 px
(padrão dos cards), sombra leve. Hover/focus: fundo `var(--sp-red)` (#ED1C24,
GESP) com chevron branco; anel de foco visível. Entrada com fade sutil, uma vez.

**Comportamento.**

- Clique → rola até a próxima âncora (`scrollIntoView`; suavidade vem do
  `scroll-behavior: smooth` global do CSS).
- `IntersectionObserver` rastreia a seção corrente e atualiza o `aria-label`.
- Na última seção, vira chevron para cima com rótulo "Voltar ao topo" e rola ao
  topo da página.
- Após rolar, o foco vai para a seção alvo (`focus({preventScroll: true})`) —
  teclado e leitor de tela acompanham a navegação.
- **Banner de cookies LGPD:** quando a faixa fixa inferior está visível
  (primeiro acesso — exatamente quando o medo da Lina mais importa), a seta se
  desloca para cima dela. JS mede a altura do banner (ResizeObserver) e publica
  offset via variável CSS. `z-index: 900` (abaixo do banner, 1000).
- `prefers-reduced-motion`: rolagem instantânea (`scroll-behavior: auto` via
  media query) e sem animação de entrada.
- Oculta em impressão. Não aparece se a página tiver menos de 2 âncoras.

### 3. Anti-falso-fundo na Home (ajustes pontuais)

- **Problema residual:** em alturas de tela onde o hero fecha exatamente na
  dobra, a borda inferior dele parece fim de página.
- **Ajuste:** em viewports baixos (`@media (max-height: 900px)`), reduzir o
  `padding-block` do `.hero__inner` (56 → 36 px) e o `margin-top` da geometria
  (28 → 20 px), para que o título "Acervo em números" espie na dobra nas
  alturas comuns de notebook (768–900 px).
- A seta cobre o residual nas alturas em que o encaixe exato ainda ocorrer.
- **Coleções:** sem ajuste — os cards já cortam na dobra na maioria das alturas.

### 4. Ícones

Adicionar `fi-chevron-down` e `fi-chevron-up` ao sprite
`_partials/_feather.html` (hoje só há right/left). Paths oficiais do Feather.

## Arquivos tocados

| Arquivo | Mudança |
|---|---|
| `portal/templates/_partials/_seta_secoes.html` | novo — o botão |
| `portal/static/js/seta-secoes.js` | novo — comportamento (~80 linhas) |
| `portal/static/css/portal.css` | bloco `.sp-seta-secoes`, `scroll-margin-top` das âncoras, media queries do hero, `scroll-behavior: auto` em reduced-motion |
| `portal/templates/home.html` | `data-sec`/`tabindex` nas seções, include do parcial, script em `extra_js` |
| `portal/templates/collection_list.html` | idem |
| `portal/templates/_partials/_feather.html` | 2 símbolos novos |

## Acessibilidade

- Botão real com `aria-label` dinâmico; foco visível; alvo ≥ 44 px.
- Foco programático na seção alvo após a navegação.
- Nenhuma altura travada — compatível com A+/A− da barra do governo
  (WCAG 1.4.4/reflow).
- Alto contraste: usa os tokens existentes do portal.

## Validação

- Rebuild da imagem e subir o compose local (o portal é baked na imagem;
  no Windows, `PORTAL_PORT=8001`).
- Conferir no navegador: ciclo completo da seta nas duas páginas; teclado
  (Tab até a seta, Enter); fonte em A+; banner LGPD visível (limpar
  `localStorage` chave `sp-lgpd-consent`); viewport mobile 375 px; viewport
  com ~800 px de altura para o peek do hero; `prefers-reduced-motion`.
- CI (ruff + pytest puro + `check --deploy`) segue verde — a feature é só front.

## Notas de execução (estado final difere em 4 detalhes)

A execução (plano + revisões) refinou este design; o código vale sobre o texto acima:

1. `tabindex="-1"` das âncoras é colocado pelo **JS no momento do foco**
   (padrão `focar()` do `home.js`), não no template.
2. Hover/foco da seta usa **`--sp-red-dark`** (#BD0E15, AA-safe com conteúdo
   branco — mesma regra do `.sp-button-primary`), não `--sp-red`.
3. O banner LGPD é observado por **MutationObserver (atributo `hidden`) +
   listener de resize**, não ResizeObserver.
4. Rótulos finais das âncoras: Home — "Busca no acervo", "Acervo em números",
   "Coleções e temas", "Etapas da contratação", "Temas em alta"; Coleções —
   "Coleções", "Como o acervo se organiza", "Como encontrar o que você procura".

## Rejeitado (e por quê)

- **Scroll-snap/fullpage:** falso fundo em toda tela + barreiras de
  acessibilidade.
- **Hero 100 svh:** cria o falso fundo que a proposta quer evitar.
- **Seta no `main.js`:** o arquivo é global; a feature é opt-in de 2 páginas.
