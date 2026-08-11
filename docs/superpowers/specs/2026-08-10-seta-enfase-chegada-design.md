# Seta-guia — estado de chegada com ênfase (design)

- **Data:** 2026-08-10
- **Origem:** pedido do Bernardo — dar mais ênfase à seta-guia "de maneira
  sóbria". A seta existe para combater o falso fundo (spec de 2026-07-29), mas
  na forma atual (quadrado branco, borda de card) pode passar despercebida por
  quem acabou de entrar — exatamente o público que ela serve.
- **Escopo:** mesmo da seta-guia — Home e Coleções. Nenhuma página nova.
- **Base:** `docs/superpowers/specs/2026-07-29-seta-secoes-design.md` (o
  componente); esta spec só adiciona um estado.

## Problema

A ênfase precisa existir **onde importa** (visitante recém-chegado, antes do
primeiro scroll — o cenário do falso fundo) sem competir com o conteúdo pelo
resto da visita. Ênfase permanente foi descartada em conversa; a escolhida foi
uma **ênfase de chegada que assenta** após o primeiro gesto.

## Decisão

**Pílula com rótulo, na cor de marca, sem movimento** (opção B da conversa):

- Na chegada, a seta revela (fade atual) já em forma de **pílula**: rótulo
  "Veja mais" + chevron, fundo e borda `--sp-red-dark` (#BD0E15 — o vermelho
  AA-safe do `.sp-button-primary`), texto/ícone brancos.
- No **primeiro gesto** — qualquer scroll real (`scrollY > 24px`) ou clique na
  própria seta — o estado assenta: colapsa para o quadrado branco discreto
  atual e nunca mais volta na visita à página.

Rejeitadas em conversa:

- **A — só cor (quadrado vermelho):** não explica a função em palavras; sem
  redundância para baixa visão de cor.
- **C — aceno do chevron:** movimento é o atrator mais forte, mas efêmero
  (quem não estava olhando, perdeu) e é o menos sóbrio dos três. Pode ser
  adicionado no futuro por cima da pílula sem retrabalho.
- **Ênfase permanente / só na primeira visita (localStorage):** permanente
  compete com o conteúdo a visita inteira; por visita única esconde o sinal de
  quem retorna direto ao topo — o falso fundo não depende de ser a primeira
  visita.

## Design

### 1. Estados

| Estado | Forma | Quando |
|---|---|---|
| Chegada (`is-chegada`) | Pílula vermelha "Veja mais" + chevron | Do reveal até o primeiro gesto, somente se a página abriu no topo |
| Assentado (atual) | Quadrado branco 48/44 px | Após primeiro scroll (>24 px) ou clique na seta |
| Última seção (atual) | Chevron para cima, "Voltar ao topo" | Inalterado — só ocorre após rolar, nunca coexiste com a chegada |

- Se a página **já abre rolada** (deep link/âncora, restauração de scroll), a
  chegada é pulada: revela direto na forma assentada. O falso fundo só existe
  no topo.
- O deslocamento sobre o banner LGPD (`--sp-seta-offset`) vale igual para a
  pílula — primeiro acesso é justamente quando banner e chegada coincidem.
- Colapso: transição de largura + opacidade do rótulo (tokens de transição já
  usados no componente). `prefers-reduced-motion`: troca instantânea — a
  pílula em si aparece igual (a ênfase não depende de movimento).

### 2. Acessibilidade

- **WCAG 2.5.3 (Label in Name):** com rótulo visível, o nome acessível deve
  contê-lo. Na chegada, `aria-label` = "Veja mais: 〈próxima seção〉" (ex.:
  "Veja mais: Acervo em números"). Após assentar, volta ao padrão atual
  ("Ir para: 〈seção〉").
- Contraste: branco sobre #BD0E15 ≈ 5,9:1 — AA para texto normal (mesma
  dupla do botão primário). Alvo ≥ 48 px de altura (44 no mobile) — inalterado.
- Rótulo em Linguagem Simples: "Veja mais" (curto, imperativo, familiar).
- Sem movimento novo: nada a tratar além do reduced-motion já coberto.

### 3. Mudanças por arquivo

| Arquivo | Mudança |
|---|---|
| `portal/templates/_partials/_seta_secoes.html` | `<span class="sp-seta-secoes__rotulo">Veja mais</span>` antes do svg; botão continua nascendo `[hidden]` |
| `portal/static/css/portal.css` | bloco `is-chegada` (~15 linhas): fundo/borda/cor, exibição do rótulo, gap, padding horizontal; rótulo oculto fora da chegada |
| `portal/static/js/seta-secoes.js` | ~12 linhas: aplicar `is-chegada` no reveal se `scrollY ≤ 24`; listener único de assentamento (scroll/clique); variação do `aria-label` na chegada |
| `portal/catalog/tests/test_seta_secoes.py` | asserções: rótulo presente no parcial, botão segue `hidden` |

Sem mudança de template nas páginas (o parcial já está incluído), sem
dependências novas, sem migração.

### 4. Validação

- Rebuild da imagem + compose local (portal é baked na imagem).
- Browser: chegada em Home e Coleções → scroll assenta → recarregar repete;
  deep link com âncora pula a chegada; clique na pílula navega **e** assenta;
  teclado (Tab + Enter); fonte em A+; banner LGPD visível (limpar
  `localStorage` `sp-lgpd-consent`); 375 px; `prefers-reduced-motion`.
- CI (ruff + pytest + `check --deploy`) verde — feature só de front.

## Adendo (10/08/2026) — pouso da pílula no mobile

### Problema

Verificação adversarial em viewports mobile (375×667, 375×812, 375×900)
encontrou um problema de leitura: no primeiro paint de /colecoes/, os cards
de coleção preenchem a dobra inteira e a pílula pousa **dentro** de um card
(ex.: rect 221×840, 138×44, 100 % contido no card "Doutrina e Conteúdo
Técnico", ao lado de "294 documentos"). Vermelha e com o mesmo raio de canto
dos cards, ela lê como CTA do card — "veja mais desta coleção" — e não como
guia da página.

### Caminhos avaliados

- **(a) Offset maior no mobile — rejeitado.** Em 375 px os cards ocupam a
  largura e a altura úteis da primeira dobra; qualquer posição fixa pousa
  sobre algum card (em 375×667 o pouso cai no card "Trabalhos Acadêmicos").
  Mudar o pouso também quebraria o colapso no lugar, desenhado nesta spec.
- **(c) Detectar sobreposição e reposicionar — rejeitado.** Os vãos entre
  cards (16–24 px) são menores que a pílula (44 px): não existe pouso limpo
  para onde fugir. Sobraria JS frágil e movimento — o oposto do sóbrio.
- **(b) Scrim sob a pílula — escolhido.** Um véu em degradê branco, logo
  abaixo da pílula, atrás dela. O conteúdo do card dissolve sob a pílula,
  que passa a ler como camada da página. Bônus alinhado à spec de origem:
  conteúdo cortado em fade é, ele próprio, sinal de continuação — reforça o
  combate ao falso fundo.

### Design do scrim

- Pseudo-elemento `::before` do próprio botão: nasce e morre com a pílula,
  sem mudança de template ou de JS. Todas as regras existentes valem por
  herança — nunca coexiste com "Voltar ao topo", some no primeiro gesto,
  acompanha o offset do banner LGPD.
- Só no mobile (`max-width: 767px`, o breakpoint que a seta já usa) e só no
  estado `is-chegada`. No desktop o pouso já cai em área livre.
- Largura total do viewport; altura ~128 px; degradê de branco quase opaco
  embaixo a transparente no topo; `pointer-events: none` (não bloqueia
  toque nos cards); `z-index: -1` dentro do stacking context do botão (sob
  a pílula, sobre o conteúdo, sob o banner LGPD).
- **Ancorado ao botão, não ao viewport** (`bottom: -28px`): quando o banner
  LGPD empurra a pílula para cima, o véu sobe junto e fecha no topo do
  banner; sem banner, fecha na borda do viewport. Ancorar no viewport
  falharia no primeiro acesso — o véu ficaria escondido atrás do banner,
  exatamente no caso em que banner e chegada coincidem.
- Fade de opacidade com os tokens de transição do componente;
  `prefers-reduced-motion` troca sem transição, como o restante.

### Validação do adendo

- Screenshots (Puppeteer) em 375×667, 375×812 e 375×900, nas páginas
  /colecoes/, / e /sobre/ (controle — não tem seta), com e sem banner LGPD.
- Conferir: chegada com scrim → primeiro gesto assenta e o scrim some;
  pílula não lê mais como CTA do card.
