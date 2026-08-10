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
