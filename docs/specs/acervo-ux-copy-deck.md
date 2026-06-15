# UX Copy — Acervo (filtros, paginação, continuidade) — BDLP

> Texto de interface em **Linguagem Simples** (NBR ISO 24495-1:2024 / Lei 15.263/2025, modo rígido) para as 6 tarefas de `prompt_claudecode_acervo-filtros-ux_BDLP.md`.
> Voz: institucional GESP, imperativa quando instrui o usuário, descritiva (3ª pessoa) quando explica o sistema. Acessibilidade WCAG2AA (pa11y limpo).
> **Todos os valores de dado foram conferidos contra os seeds** (`docker/postgres/init/*.sql`). Strings marcadas `[decisão]` aguardam o time — ver §Decisões.
> Revisado por auditoria adversária de 6 lentes (LS, WCAG2AA, terminologia, registro pt-BR, continuidade-Laís, completude).

---

## Vocabulário-base — consistência (LS 3.2 / 3.10)

| Conceito | Termo canônico | Onde já vive no código |
|---|---|---|
| Item do acervo (unidade contada) | **documento(s)** | `search.html:118` (`pluralize_pt:"documento"`), título do empty-state `search.html:143` |
| Conjunto retornado pela busca | **resultado(s)** | hint `search.html:117`, contagem por faceta `_facet_list.html:20,29` (`pluralize_pt:'resultado'`) |
| Recorte ativo | **filtro(s)** | `search.html:46,111` |
| Seções da barra | Coleção · Categorias · Natureza · Assunto · **Ano** (nova) | `search.html:52,68,96,101` |

**Três nouns vivos para "a coisa do acervo":** `documento` (contagem global), `resultado` (contagem por faceta, `_facet_list.html`), `material` (empties: `_facet_options.html` empty_msg e `_cat_toggle.html:12` title). Decisão: **padronizar a unidade em `documento`**; reservar `resultado` só para o conjunto da busca textual; **eliminar `material`** dos empties (ver §Consistência transversal). **Decidido (10/06): `documento`.** Reabrir só se o acervo passar a incluir mídia não-textual (vídeo, curso) — aí `material` seria o guarda-chuva.

---

## Tarefa 1 — Painel "Filtros aplicados" com chips removíveis

### Copy recomendada
- **Título do painel:** `Seus filtros ({N})` ✓ *(decidido — §Decisões)*. Alternativas abaixo só se o registro mudar.
- **Chip (rótulo):** `{Dimensão}: {valor}` — **uma dimensão por prefixo**:
  - `Coleção: {nome do tipo}` — ex.: `Coleção: Acórdão` (vale para `typeinform_id` **e** para `colecao_v6` "Toda a coleção")
  - `Categoria: {nome}` · `Subcategoria: {nome}` · `Assunto: {nome}` · `Natureza: {nome}`
  - Exemplos reais conferidos: `Assunto: Sustentabilidade e ODS` · `Natureza: Contratação de Serviços` · `Categoria: Gestão Contratual`
- **Chip de ano:** `A partir de {ano}` (ano_min) · `Até {ano}` (ano_max) — chips separados, cada um removível.
- **Remover (×):** `<button type="button" aria-label="Remover filtro {rótulo}">` com `<svg aria-hidden="true"><use href="#fi-x"/></svg>`.
  - Ex.: `aria-label="Remover filtro Assunto: Sustentabilidade e ODS"`. Ano: `Remover filtro Ano: a partir de {ano}`.
- **Limpar tudo:** texto `Limpar tudo` · `aria-label="Limpar todos os filtros"`.

### Alternativas — título do painel
| Opção | Copy | Tom | Quando usar |
|---|---|---|---|
| A (rec.) | `Seus filtros ({N})` | Próximo, de serviço | Atende direto a continuidade da Laís (T3); "seu" é LS 3.4 (tratamento direto) |
| B | `Filtros aplicados ({N})` | Institucional | Se o time rejeitar possessivo no registro |
| C | `Filtros ativos ({N})` | Neutro, de estado | Meio-termo; "ativo" descreve o estado visível |

### Justificativa
O painel é o **principal sinal de continuidade** da T3: após o refresh, a Laís vê em destaque o que escolheu. Prefixar o chip com a **dimensão que ela clicou** remove ambiguidade — um mesmo rótulo pode existir em dimensões diferentes (ex.: `Assunto: Governança` vs `Subcategoria: Governança e Logística`). Um prefixo por origem: tudo que sai da seção **Coleção** (tipos via `typeinform_id` + o "Toda a coleção" via `colecao_v6`) usa **`Coleção:`** — nunca `Tipo:` — porque é o nome do cabeçalho que ela clicou. O cabeçalho da seção é "Categorias" (plural, rotula o grupo); o chip nomeia **um** valor, então usa o singular `Categoria:`/`Subcategoria:` — escolha deliberada, não inconsistência. "Seus filtros" foi a escolha do time (10/06): atende a continuidade e o tratamento direto da LS, mesmo introduzindo o possessivo que a voz atual evitava.

### A11y (WCAG2AA)
- O `×` é **`<button type="button">`** focável (2.1.1 Teclado / 4.1.2 Nome-Papel-Valor); o glifo `#fi-x` leva `aria-hidden="true"` — o nome acessível vem só do `aria-label`.
- Painel em região rotulada: `<section aria-labelledby="...">` ou `aria-label="Seus filtros"`; chips como `<ul>`/`<li>` para o leitor anunciar a quantidade.
- A contagem `{N}` muda dentro do fluxo já anunciado pela região de status (ver T3).

### Estado só-busca (sem facetas, com `q`)
Quando `N==0` mas há `q`: **não** mostrar o painel "Seus filtros". Mostrar um chip único `Busca: "{q}"` com `aria-label="Remover busca {q}"`, ou um link `Limpar busca`. Garantir que a busca-só tenha **exatamente um** jeito de limpar (hoje o empty-state já dispara em `filters or query`, `search.html:144`).

### §Consolidação (um só "limpar tudo")
O painel passa a ser o **único** controle de limpar tudo, com `Limpar tudo`. **Remover** o `Limpar {N}` do `.filter-panel__head` (`search.html:46`). Um rótulo só — sem "vice-versa".

---

## Tarefa 2 — Filtro por ano + ordenação nos dois sentidos

### Copy recomendada — seção Ano
- **Título (h3):** `Ano`
- **Texto de apoio (opcional):** `Filtra os documentos pelo ano de publicação.` (sistema na 3ª pessoa, ordem direta)
- **Grupo:** `.year-range` com `role="group" aria-labelledby="{id do h3 'Ano'}"` (ou `<fieldset><legend>Ano</legend>`).
- **Campo inicial:** `<label for="ano_min">De</label>` — sem `aria-label` (o rótulo visível **é** o nome acessível; o grupo "Ano" dá o contexto). `placeholder="{min}"`.
- **Campo final:** `<label for="ano_max">Até</label>` — idem. `placeholder="{max}"`.
- **Handles do slider (range, enriquecimento):** por handle `role="slider"` + `aria-label="Ano inicial"` / `aria-label="Ano final"` + `aria-valuemin="{min}"` `aria-valuemax="{max}"` `aria-valuenow="{ano}"` `aria-valuetext="{ano}"`. O handle "De" tem `aria-valuemax` = valor atual do handle "Até" (e vice-versa) para impedir cruzamento.
- **Erro de intervalo inválido** (De > Até): `O ano inicial não pode ser maior que o ano final.` (em `role="alert"` / `aria-live="assertive"`).

### Copy recomendada — ordenação (`<select name="sort">`)
| value | Copy | Hoje | Ordena por |
|---|---|---|---|
| `""` | `Relevância` | igual | rank textual |
| `recente` | `Adicionados recentemente` | "Mais recente" | `-created` (entrada no acervo) |
| `ano` | `Ano (mais recente)` | "Ano" | `ano` desc |
| `ano_asc` | `Ano (mais antigo)` | — (nova) | `ano` asc |
| `autor` | `Autor (A–Z)` | "Autor" | `author, title` |
| `titulo` | `Título (A–Z)` | igual | `title` |

### Justificativa
`recente` e `ano` são ordens **diferentes** (data de entrada no acervo × ano de publicação). Chamar as duas de "recente" quebraria a precisão (LS 3.1) e a coesão (3.10). `Adicionados recentemente` deixa claro que é sobre **quando o documento entrou** no acervo. Os campos `De`/`Até` são a base acessível; o slider duplo é enriquecimento — se o slider não fechar o WCAG2AA, os campos sustentam o filtro sozinhos (progressive enhancement). Alternativa de paralelismo para o sort: `Mais recentes no acervo`.

### A11y (WCAG2AA)
- **2.5.3 Nome no rótulo:** `De`/`Até` são o nome acessível (sem `aria-label` que divirja do texto visível). Contexto "Ano" vem do grupo.
- Slider operável por teclado, com a lista completa de `aria-value*` acima.

---

## Tarefa 3 — Continuidade ao filtrar (sem salto, persistência visível)

### Copy recomendada
- **Região de status (sempre presente, vazia no HTML inicial):**
  `<p class="sr-only" role="status" aria-live="polite" id="acervo-status"></p>`
- **Em voo (durante o submit):** `#acervo-status` recebe `Atualizando resultados…`
- **Concluído (na página recarregada):** a contagem anuncia `Resultados atualizados — {N} {documento|documentos}`. O texto **substitui** (não acumula) o "Atualizando…".
- **Empty-state com filtros ativos** (substitui o atual de `search.html:141-145`):
  - Título: `Nenhum documento com esses filtros`
  - Corpo: `Remova um filtro ou amplie o intervalo de anos para ver mais resultados.`
  - Variante **só-ano** (apenas `ano_min`/`ano_max` ativos): título `Nenhum documento neste período` · corpo `Tente um intervalo de anos maior ou remova o filtro de ano.`
  - Variante **só-busca** (apenas `q`): `Tente outros termos de pesquisa.`
  - O painel "Seus filtros" **continua visível acima** do empty-state, para a Laís ver e remover exatamente o filtro que zerou.
- **Sinal principal de continuidade:** o painel de chips da T1.

### Justificativa
A necessidade da Laís é **continuidade**: "não perdi nada, continuo no mesmo lugar, só atualizou". Três peças entregam isso: (1) os chips no topo (vê o que escolheu); (2) o ciclo `Atualizando… → Resultados atualizados` (começo e fim claros, sem reticências penduradas); (3) um empty-state que aponta a **saída certa** — afrouxar/remover filtro. A frase atual ("Tente outros filtros… para ampliar a busca") está **incoerente** (mandar adicionar filtro para *ampliar*); a nova diz a ação real.

### A11y (WCAG2AA)
- A região `aria-live` **existe vazia no HTML inicial**; o JS só troca o `textContent` — nunca cria/recria o elemento (senão o leitor não anuncia).
- Uma só região de status para não "atropelar" a contagem; sem `autofocus` que cause scroll (requisito do "sem salto").

---

## Tarefa 4 — 10 itens por página
Sem texto de interface novo. Afeta apenas o total em "Página X de Y" (T5).

---

## Tarefa 5 — Paginação: primeira/última + "Página X de Y"

### Copy recomendada
- **Primeira página:** texto visível `Primeira` · `aria-label="Primeira página"`.
- **Última página:** texto visível `Última` · `aria-label="Última página"`.
- **Status:** `Página {X} de {Y}` — em `role="status" aria-live="polite"`.
- **Nav (landmark):** `aria-label="Paginação dos resultados"`.
- **Números:** `aria-current="page"` no atual; opcional `aria-label="Página {num}"` em cada número.

### Estado desabilitado (na primeira/última) — regra única
- **Controles com texto** (`Primeira`/`Última`/números): `<span class="page-btn is-disabled" aria-disabled="true">Primeira</span>` — texto visível e anunciado como indisponível; **não** focável; **não** usar `aria-hidden`. Opcional: `title="Você está na primeira página"` / `"Você está na última página"`.
- **Setas ícone-só** (anterior/próxima): manter o padrão atual `<span class="page-btn is-disabled" aria-hidden="true">` (sem rótulo a preservar — a posição é dada por "Página X de Y" + números).

### Alternativas
| Elemento | Opção | Copy | Observação |
|---|---|---|---|
| Primeira/última | A (rec.) | texto `Primeira`/`Última` | Sem ícone novo no sprite; mais acessível |
| Primeira/última | B | duplo-chevron + aria-label | Exige somar `fi-chevrons-left/right` (Feather) ao `_feather.html` |

### Justificativa
O sprite (`_feather.html`) só tem `chevron-left/right` e `arrow-right` — **não há duplo-chevron** — então texto "Primeira"/"Última" é a opção acessível e sem ícone novo. **`Página X de Y` já é string da casa** em `collection_detail.html:38`; esta tarefa só **estende** o padrão à busca (coesão, não copy nova).

### A11y / harmonização
As duas telas divergem hoje: `search.html` usa `Paginação dos resultados`/`Página anterior`/`Próxima página`; `collection_detail.html` usa `Paginação dos documentos`/`Anterior`/`Próxima`. **Padronizar ambas** em `Paginação dos resultados` e nos rótulos completos.

---

## Tarefa 6 — Title Case nos títulos de Categoria e Subcategoria

### Strings canônicas (fonte da verdade p/ o filtro `titulo_pt`) — conferidas vs `07-categories.sql`
**Categorias:**
| Seed (CAIXA ALTA) | Exibir |
|---|---|
| PLANO DE CONTRATAÇÕES ANUAL (PCA) | Plano de Contratações Anual (PCA) |
| CICLO COMPLETO DA CONTRATAÇÃO | Ciclo Completo da Contratação |
| PLANEJAMENTO/FASE PREPARATÓRIA | Planejamento/Fase Preparatória |
| SELEÇÃO DO FORNECEDOR | Seleção do Fornecedor |
| GESTÃO CONTRATUAL | Gestão Contratual |
| CONTEÚDOS TRANSVERSAIS | Conteúdos Transversais |

**Subcategorias:**
| Seed | Exibir |
|---|---|
| FASE PREPARATÓRIA - ETP | Fase Preparatória - ETP |
| FASE PREPARATÓRIA - TR | Fase Preparatória - TR |
| FASE PREPARATÓRIA - GESTÃO DE RISCOS | Fase Preparatória - Gestão de Riscos |
| FASE PREPARATÓRIA - PESQUISA DE PREÇOS | Fase Preparatória - Pesquisa de Preços |
| LICITAÇÃO | Licitação |
| CONTRATAÇÃO DIRETA | Contratação Direta |
| PROCEDIMENTOS AUXILIARES | Procedimentos Auxiliares |
| GESTÃO DE CONTRATOS | Gestão de Contratos |
| FISCALIZAÇÃO DE CONTRATOS | Fiscalização de Contratos |
| Governança e Logística | Governança e Logística *(idempotente — já ok)* |
| Integridade e Controle | Integridade e Controle *(idempotente)* |
| Políticas Públicas e Sustentabilidade | Políticas Públicas e Sustentabilidade *(idempotente)* |
| Sistemas e Inovação | Sistemas e Inovação *(idempotente)* |
| Direito e Regulação | Direito e Regulação *(idempotente)* |

### Regras do filtro `titulo_pt`
- **Conectores minúsculos** (exceto 1ª palavra): de, da, do, das, dos, e, em, na, no, a, o, para, por, com.
- **Siglas preservadas** (allowlist): PCA, ETP, TR, TIC, RP, PMI, ODS, MPE.
- **1ª letra maiúscula** nas palavras significativas; tratar separadores `/` e `-` (cada parte recebe Title Case; manter o espaçamento " - ").
- **Idempotência:** rodar 2× não altera o resultado (as subcategorias de CONTEÚDOS TRANSVERSAIS já estão corretas — não podem ser quebradas).
- **Microcategorias ficam como estão** *(decidido: aplicar a Categoria + Subcategoria; micros não)* — já vêm em caixa mista no seed ("Emergência - Inciso VIII", "Registro de Preços (RP)") com romanos/incisos que o filtro não deve mexer.

---

## Consistência transversal (strings vivas a alinhar ao noun canônico `documento`)
| Arquivo:linha | Hoje | Trocar para |
|---|---|---|
| `_facet_options.html` (empty_msg) | "Sem materiais classificados por natureza ainda." | `Nenhum documento classificado por natureza ainda.` |
| `_cat_toggle.html:12` (title) | "Sem material nesta {noun} ainda" | `Sem documentos nesta {noun} ainda` |
| `search.html:46` (header) | "Limpar {N}" | **remover** (painel da T1 assume) |
| `search.html:109-112` (drawer mobile) | "Filtros ({{ filters\|length }})" | manter; **mesmo {N}** do painel |
| `acervo-filters.js:17` (`#filter-active-count`) | id consultado pelo JS **sem markup** | criar o badge: texto `{N}`, `aria-label="{N} filtros aplicados"`, mesmo {N} |
| `search.html:105` (`Aplicar filtros`, no-JS) | igual | **manter** — aplica todos os filtros, inclusive o ano; escondido sob JS por design |

---

## Decisões tomadas (10/06)
1. **Rótulo do painel (T1):** **`Seus filtros (N)`** — escolhido pela continuidade (T3) + tratamento direto (LS 3.4). `Filtros aplicados/ativos` ficam registradas como alternativas caso o registro mude.
2. **Noun canônico:** **`documento`** em toda contagem de unidade; `resultado` só para o conjunto da busca textual; `material` sai dos empties. Reabrir se entrar mídia não-textual.
3. **Title Case (T6):** **Categoria + Subcategoria**; microcategorias ficam como estão.
4. **Posição da seção Ano:** **ao final** (após Assunto), preservando a ordem da Lina (Coleção→Categoria→Natureza→Assunto→**Ano**).
