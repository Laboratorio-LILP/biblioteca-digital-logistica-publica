# Padrão de fundos — o trio da home em todas as páginas (design)

- **Data:** 2026-08-11
- **Origem:** pedido do Bernardo — "estabelecer o padrão de fundos igual ao da
  home em todas as páginas: fundo escuro quadriculado, seguido de fundo branco,
  seguido de fundo escuro sem quadriculado".
- **Decisões da conversa (11/08):** o "escuro" é o **cinza-claro #F5F5F5** da
  própria home (não petrol/preto); breadcrumb entra **dentro** da banda
  quadriculada; paginação vira o conteúdo da banda de fechamento; legais ganham
  template comum + banda de contato; 404/500 entram no lote.

## Problema

O portal tem três linguagens de fundo convivendo:

1. **Home** — a referência: hero cinza-claro com quadriculado sutil (grade CSS
   40px, preto a 4,5% de alfa) → miolo branco → "Temas em alta" em cinza liso
   (`.sp-section--alt`) → rodapé preto global.
2. **/colecoes/ e /sobre/** — já em bandas full-bleed, mas abrem **branco** e
   fecham **branco**: alternância invertida em relação à home, sem quadriculado.
3. **/busca/ e /documento/** — abrem com breadcrumb + hero brancos; o miolo são
   cards brancos soltos sobre o cinza do body (o inverso tonal da home).
4. **/colecao/, as 6 legais e 404/500** — sem banda nenhuma: conteúdo chapado
   no cinza do body. As legais repetem a mesma estrutura à mão em 6 arquivos,
   sem template comum (CSS marcado como "compat" do design-system antigo).

Navegar entre páginas troca de linguagem visual sem motivo editorial.

## Decisão

Um trio padronizado por página, na gramática que a home já usa:

1. **Abertura quadriculada** — banda cinza-claro `#F5F5F5` com a grade da home,
   contendo breadcrumb, eyebrow, h1 e intro (e o que o topo da página pedir:
   barra de busca na /busca/, badges no /documento/). O quadriculado encosta no
   header, como na home.
2. **Miolo branco** — as bandas de conteúdo. Cards brancos com borda já têm
   precedente (home e /colecoes/ hoje). Alternância interna branco/cinza segue
   permitida em páginas longas (como na home), desde que a primeira banda do
   miolo seja branca.
3. **Fechamento cinza liso** — a última banda antes do rodapé é
   `.sp-section--alt`, sem quadriculado. Duas variações toleradas, registradas
   no mapa: /documento/ sem relacionados fecha branco; 404/500 não têm
   fechamento (páginas curtas).

A home fica **intocada** — ela é a referência.

## Design

### 1. Mecanismo CSS

- **Novo modificador `.sp-section--pattern`**: banda com `background-color:
  var(--sp-gray-light)` e o quadriculado direto no `background-image` (os dois
  linear-gradients de `.sp-pattern`, com alfa equivalente ao overlay da home —
  0,045 × opacity 0,7 ≈ 0,03) — sem div de overlay. O hero da home continua
  com seu mecanismo atual (`.hero__pattern`); unificar depois, se valer.
- **Fechamento**: `.sp-section--alt` na última banda (mecanismo existente).
- **Respiro final**: trocar `main > .sp-section:last-child` por
  `:last-of-type` — conserto de bug latente: a seta-guia é incluída depois da
  última seção em home/colecoes, e o `:last-child` nunca casa nessas páginas.
- **Breadcrumb**: o `nav.breadcrumb` passa a ser o primeiro filho do
  `.sp-container` da banda de abertura. A faixa `.breadcrumb-bar` (branca,
  separada) sai das páginas migradas; os seletores de adjacência
  (`.breadcrumb-bar + .catalog-hero…`, `+ .colecoes-hero`, `+ .sobre-hero`)
  saem ou viram regra da própria banda de abertura.

### 2. Mapa por página

| Página | Abertura quadriculada | Miolo branco | Fechamento cinza |
|---|---|---|---|
| Home | (intocada — referência) | | |
| /colecoes/ | breadcrumb + hero + 4 cards | "Como cada documento é classificado" | "Como encontrar…" + CTA |
| /sobre/ | breadcrumb + hero institucional | Quem somos (branco) → Parceria (cinza) → Marco (branco) | Contato + CTA |
| /busca/ | breadcrumb + "Pesquisa institucional" + searchbar | filtros + resultados (banda branca) | paginação |
| /documento/ | breadcrumb + resultnav (se houver) + badges + h1 + autores | Resumo/Classificação + aside | "Materiais relacionados" quando houver; sem relacionados fecha branco (variação tolerada) |
| /colecao/ | breadcrumb + h1 + intro | subcoleções + grid de documentos | paginação |
| 6 legais | breadcrumb (novo) + h1 + intro | corpo (`article.sp-pagina-legal`) | banda de contato "Dúvidas? Fale com o LILP" → /fale-conosco/ |
| 404/500 | h1 + mensagem | ações (voltar à home, buscar) | — (páginas curtas; variação tolerada) |

Notas do mapa:

- **/busca/**: todo o conteúdo vive num único `<form id="acervo-form">` — as
  bandas nascem **dentro** do form (seções dentro de form são válidas); nada
  sai do form para não quebrar o submit conjunto de busca + filtros.
- **/colecao/** migra de `block content` (wrapper `.page`) para
  `block content_raw` com bandas próprias — mesmo movimento que /colecoes/ já
  fez.
- **Legais**: novo template intermediário `legal/_base_legal.html` (estende
  `base.html`, define o trio de bandas; cada legal preenche blocos de título,
  intro e corpo). Elimina as 6 cópias manuais. Exceção: na própria
  /fale-conosco/ a banda de contato não se auto-referencia — a página fecha com
  sua seção final (LGPD) na banda cinza.
- **/documento/** tem topo de altura variável (resultnav condicional): a banda
  de abertura absorve o resultnav quando ele existir.

### 3. Acessibilidade

- Os tokens atuais (links azul `--sp-blue`, eyebrow `--sp-red-dark`, badges com
  alfa) já operam sobre `#F5F5F5` — é a mesma dupla de contraste do hero da
  home e das bandas `--alt` atuais. Ainda assim, pa11y AA nas páginas migradas.
- **Alto contraste** (`body.sp-alto-contraste`): o modo já zera todo
  `background-image` — o quadriculado some por design; nada a fazer.
- Header sticky translúcido sobre banda cinza: já acontece na home; sem
  mudança.
- Scrim da seta-guia (mobile): degradê branco sobre fechamento cinza `#F5F5F5`
  — diferença imperceptível; conferir na verificação visual.

### 4. Mudanças por arquivo

| Arquivo | Mudança |
|---|---|
| `portal/static/css/portal.css` | `.sp-section--pattern`; `:last-child` → `:last-of-type`; ajustes/remoção das adjacências de `.breadcrumb-bar`; breadcrumb dentro de banda; estilos da banda de contato das legais (reuso de `.curadoria-*`); banda branca do miolo da busca/colecao |
| `search.html` | bandas dentro do form: abertura pattern, miolo branco, paginação no fechamento |
| `document_detail.html` | abertura pattern (com resultnav), miolo branco |
| `collection_list.html` | hero → pattern (breadcrumb dentro); última seção → `--alt` |
| `collection_detail.html` | migra para `content_raw` com o trio |
| `about.html` | hero → pattern (breadcrumb dentro); alternância do miolo re-fasada para fechar cinza |
| `legal/_base_legal.html` | **novo** — o trio para as legais |
| `legal/*.html` (6) | reescritas para estender o `_base_legal` |
| `404.html`, `500.html` | `content_raw` com abertura pattern + banda branca de ações |
| `catalog/tests/` | revisar asserções que citem estrutura dos templates migrados |

### 5. Restrições (não quebrar)

- **Seta-guia**: os `data-sec` de home e /colecoes/, o include após as seções e
  o comportamento das specs de 2026-07-29 e 2026-08-10 permanecem intactos.
- **Form único da busca** (submit conjunto + auto-submit de filtros).
- **Breadcrumb da /colecao/** mantém o trail hierárquico completo.
- Rebuild obrigatório do contêiner para ver qualquer mudança (sem bind-mount).

### 6. Validação

- Rebuild + refotografar as 8 rotas em desktop 1280×900 (script `shoot.js` já
  salvo no scratchpad) e as principais em mobile 375; comparar com as fotos
  "antes" de `fundos-atual/`.
- pa11y WCAG2AA em /busca/, /colecao/, uma legal e /sobre/.
- Ciclo completo da seta-guia em home e /colecoes/ (chegada → assentar →
  última seção), teclado incluído.
- CI (ruff + pytest + `check --deploy`) verde — feature só de front.
