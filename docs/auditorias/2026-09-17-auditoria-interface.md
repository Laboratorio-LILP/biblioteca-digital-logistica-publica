# Auditoria da interface — 17/09/2026

Escopo: toda a interface pública do portal Django da BDLP, na stack local (`main` + working tree da branch `feat/2026-09-validacao-subsecretario`, acervo v11 com 982 documentos, taxonomia v12).

Pergunta: onde há **inconsistências, erros e desatualizações** no que o público vê?

## Método

| Frente | O que fez |
|---|---|
| Rastreador (puppeteer) | 22 URLs × 2 larguras (1440 e 390 px): status HTTP, erros de console, requisições falhas, `<title>`, meta description, canonical, `lang`, número de `h1`, saltos de cabeçalho, ids duplicados, ícones `<use>` sem símbolo, `href` vazio, controles sem nome acessível, imagens sem `alt`, vazamento de sintaxe de template, estouro horizontal, e verificação de **todos os links internos** (GET). |
| pa11y | WCAG 2 AA em 14 páginas (início, Acervo com e sem termo, Coleções, `/colecao/1/`, documento, Sobre, as 6 legais, 404). |
| 4 revisões independentes | Copy e terminologia; páginas institucionais e legais contra o que o código faz; sistema visual e CSS; fluxos funcionais com ~130 requisições de sondagem. |
| Verificação | Cada achado de severidade alta ou média foi confirmado por mim no código ou no navegador (contraste calculado, fontes, escala, foco, HTTP). Itens não reproduzidos por mim estão marcados. |

## O que está em ordem (verificado)

- 0 links internos quebrados (85 links únicos); 0 erros de acessibilidade automática nas 14 páginas; 0 estouro horizontal a 390 px; 0 ícone sem símbolo no sprite; 0 id duplicado; 0 vazamento de sintaxe de template; `h1` único em toda página; ordem de cabeçalhos sem saltos; `lang="pt-BR"`.
- Nenhuma contagem chumbada no texto; nenhum termo aposentado visível ("categoria processual", "macroetapa", "Documentos Normativos", "Vídeos", "clique").
- Contagens das facetas batem com o resultado ao clicar (30 de 30 opções sob `q=Pregão`); busca sem acento funciona; opções desabilitadas não são enviadas; XSS e SQL em `q` escapados; 404 e 500 devolvem o status certo; todo `<button>` tem `type`; todo campo tem `<label>`; só há formulários GET.
- Grafia das normas consistente entre páginas; contatos (e-mail, endereço, órgão) coerentes; ano do rodapé dinâmico; `#C8102E` não existe mais em lugar nenhum.

## Achados — severidade ALTA

### A1. Três formas de derrubar a página (HTTP 500), sem registro em log

| Gatilho | URL de exemplo | Causa |
|---|---|---|
| Id não numérico em qualquer filtro | `/busca/?category_id=abc`, `?assunto_id=abc`, `?typeinform_id=x`, `/documento/bdlp-000982/?ctx=category_id%3Dabc` | `_read_filters_from` (views.py) passa a string crua ao ORM; `ValueError` no `filter(id=...)`. |
| Busca com muitas palavras (≥ ~190) | `/busca/?q=pregao+pregao+…` (200 palavras) | `_consulta` (search.py) monta a tsquery como árvore aninhada por token; `RecursionError` na compilação. 100 palavras passam. |
| Byte nulo na busca | `/busca/?q=%00` | Postgres recusa literal com NUL. |

Reproduzido por mim (os quatro primeiros e os dois últimos). Agravante: `settings.py` não define `LOGGING` nem `ADMINS`; com `DJANGO_DEBUG=false` o logger `django.request` só tem `mail_admins`, que não faz nada. Após os 500 acima, o log do contêiner não tem nenhum traceback. Em homologação esses erros seriam invisíveis.

Correção: validar em `_read_filters_from` (`*_id` só inteiros positivos; `colecao_v6` só chaves conhecidas; `natureza` só valores canônicos; valor inválido é descartado sem chip); truncar `q` no servidor (30 palavras) e `maxlength="200"` nos dois campos de busca; remover `\x00` de `q` e dos filtros; `LOGGING` com handler de console nível ERROR para `django.request`, independente de DEBUG.

### A2. Opção selecionada com contagem zero perde o estado

Toda opção com contagem 0 vira `<span>` sem `<input>` (`_cat_toggle.html`), **inclusive a selecionada**. Em `/busca/?q=pregão&category_id=1&assunto_id=1` (0 resultados) nenhum checkbox fica marcado e os chips somem; ao trocar a ordenação, o JS reconstrói a URL a partir do formulário e os filtros desaparecem em silêncio (`/busca/?q=pregão&sort=titulo`, 44 documentos). Sem JS, "Aplicar filtros" faz o mesmo.

Reproduzido por mim. O comportamento já existia na cascata de Categorias e ficou uniforme com a mudança de hoje nas facetas planas (antes, o assunto selecionado com 0 simplesmente não aparecia, com o mesmo efeito).

Correção: a opção selecionada nunca é `disabled` (`disabled = count == 0 and not selecionada` em `facets.py`, ou `{% if disabled and not current|selected_in:id %}` no parcial); ela permanece como checkbox marcado com contagem 0.

### A3. Foco visível abaixo do mínimo, e ausente no campo de busca

- Anel de foco global (`portal.css:84-88`): azul a 55 % de opacidade. Contraste calculado: **2,80:1** sobre branco, **1,49:1** sobre o preto da barra superior e do rodapé. WCAG 2.1 SC 1.4.11 exige 3:1. Nos fundos escuros o foco é praticamente invisível.
- Campo de busca da home e do Acervo (`portal.css:373`): `.searchbar input:focus { outline: none }`. Resta só a borda de 1 px mudando de cinza para azul. Contraria o padrão de foco de 3 px da própria plataforma e a promessa da página de Acessibilidade ("indicador de foco claramente visível").
- Variantes divergentes: ano `2px` sólido; skip-link vermelho; `summary` redefine o outline só para mudar o offset.

Correção: um token `--focus-ring` (`3px solid var(--sp-blue)`, 8:1 sobre claro) aplicado por `:focus-visible` em todo elemento interativo; nos fundos escuros (`.govbar`, `.site-footer`, banner LGPD) `outline-color: var(--sp-white)` ou anel duplo branco/azul; devolver o anel ao campo de busca.

### A4. A+ e A− quase não fazem nada

Os botões mudam o `font-size` do `html`, mas 144 tamanhos de fonte estão em `px` (só 3 em `rem`). Medido com `sp-fonte-aumentada-2`: o corpo passa de 14 para 17,5 px, mas o título do cartão fica em 15 px, o menu em 13 px e o resumo do cartão em 12 px. A página de Acessibilidade promete "aumenta o tamanho da fonte da página".

Correção: escala tipográfica em `rem` (`--fs-11: 0.6875rem` … ) nos componentes, ou `em` relativo ao `html`; manter `clamp()` só nos títulos de herói com base em `rem`.

### A5. Contraste de texto abaixo de AA

| Elemento | Medida | Mínimo |
|---|---|---|
| Badge "Aberto" na página do documento (`.doc-badge.aberto`, 11 px, verde sobre verde claro) | **3,56:1** | 4,5:1 |
| Placeholder "Buscar no acervo" (`rgb(0 0 0 / 0.45)`) | 3,36:1 | 4,5:1 |
| Opções desabilitadas das facetas (texto 40 %, contagem 35 %) — são conteúdo informativo, não controle | 2,85:1 e 2,43:1 | 4,5:1 |
| Bordas de campos e da caixa do checkbox (`#BFBFBF` sobre branco) | 1,84:1 | 3:1 (componentes) |

O primeiro foi medido por mim no navegador; os demais são cálculo direto sobre os valores do CSS. O badge do cartão já resolve certo (texto escuro, ícone verde); a página do documento deve espelhar.

### A6. Links invisíveis

O reset global `a { color: inherit; text-decoration: none }` faz qualquer link sem classe dentro de um parágrafo sumir. Confirmado em dois pontos: "Limpar tudo" no estado vazio do Acervo (cor igual à do parágrafo, sem sublinhado) e o e-mail `lab.sggd@sp.gov.br` no Sobre. O mesmo defeito já tinha sido corrigido pontualmente para as notas dos cards de Coleções.

Correção na raiz: `main a:not([class]) { color: var(--sp-blue); text-decoration: underline; }` (como já existe só para o corpo `--prosa` das páginas legais).

### A7. Futura não é servida

`--font-heading` declara "Futura PT" mas não há `@font-face` nem arquivo de fonte; `base.html` só carrega Montserrat do Google Fonts. Neste Mac a Futura existe como fonte do sistema, então os títulos saem em Futura; em Windows, Android e Linux (a maioria dos servidores públicos) caem em Montserrat 700. A identidade tipográfica depende do sistema operacional do visitante, e o comentário do `base.html` ainda diz "Montserrat (títulos/subtítulos)". Montserrat 500 é baixado e nunca usado.

Decisão do dono: licenciar e servir a Futura PT localmente (`static/fonts/` + `@font-face`), ou assumir Montserrat como fonte de título e simplificar o token. Servir localmente também resolve o item B5.

### A8. Página de Acessibilidade promete um controle que não existe

`legal/acessibilidade.html:47` lista "Comunicar erros — link para o canal oficial do Governo SP" na barra superior. A barra tem Ouvidoria, Transparência e Fala.SP; não há "Comunicar erros" em lugar nenhum. No mesmo bloco, a ordem A+/A− está invertida em relação à barra e o glifo do "menos" difere (U+2212 na página, hífen no botão).

## Achados — severidade MÉDIA

### B. Verdade institucional (páginas legais e banner)

- **B1. Cookie que não existe.** Política de Cookies e de Privacidade descrevem o cookie `csrftoken` ("proteção de formulários", 1 ano) e o banner diz "este portal usa cookies essenciais para funcionar". O portal não emite **nenhum** cookie HTTP: não há formulário POST nem `{% csrf_token %}`, sessões não estão instaladas, e `Set-Cookie` não aparece em nenhuma resposta (verificado em 5 páginas). Só há `localStorage`.
- **B2. Consentimento para o que não existe.** O banner pede consentimento para "cookies opcionais para medir o uso"; a própria política diz que a categoria "não está ativa; nenhum cookie de análise é disparado". O modal oferece "Lembrar minhas preferências (ex.: última coleção visitada)", recurso que não existe no código.
- **B3. Contradição sobre IP.** Modal: "sem guardar o endereço IP completo". Política: "medição agregada e anônima de visitantes (com endereço IP)".
- **B4. Chaves de armazenamento divergentes.** Privacidade lista `csrftoken` e `sp-lgpd-consent`; Cookies e o JS também gravam `sp-a11y:contraste` e `sp-a11y:fonte-escala`.
- **B5. Terceiro não declarado.** Toda página carrega Montserrat de `fonts.googleapis.com`/`fonts.gstatic.com` (IP e user agent vão ao Google), e a Política de Cookies afirma que "o portal não embute serviços de terceiros". Servir a fonte localmente resolve e ainda remove os domínios do CSP.
- **B6. Página 500 renderiza sem contexto.** Não há `handler500`; o handler padrão do Django renderiza `500.html` sem `request`, os context processors não rodam: rodapé "©  Governo…" com ano vazio e menu sem estado. Reproduzido por mim com o handler padrão.
- **B7. Mapa do site desatualizado.** Lista para a home "Coleções em destaque" e "Estatísticas do acervo" (nomes que não existem; a seção é "Acervo em números" e é a 2ª, não a última) e para Coleções "Subcoleções e contagens / Documentos por coleção", que descrevem a página órfã `/colecao/<id>/` (C1). Falta a seção de contato do Sobre. "Acervo (Busca)" é nome híbrido.
- **B8. Links externos abrem nova aba sem aviso** (barra superior, Transparência, Mapa do site, Fale conosco, Acessibilidade, Privacidade, DOI do documento): eMAG 3.1 Rec. 1.9. O padrão de aviso já existe no botão "Acessar documento", mas lá o aviso é um `span` irmão sem `aria-describedby`. Documentos "Restrito" recebem o mesmo botão sem aviso de acesso pago.
- **B9. Afirmações a reconfirmar:** "testado com NVDA, JAWS e VoiceOver" (sem registro no repositório); "política de senhas para acesso administrativo" (o projeto não tem `auth`); "a SGGD ainda está formalizando a designação do DPO" (agosto/2026); Decreto 69.052/2024 citado no Sobre mas ausente do Marco normativo e da lista da Transparência; Decreto 68.155/2023 citado no topo da Transparência mas ausente da lista; Alt+3 anunciado como geral, mas só existe em Início e Acervo (por desenho do skip-link); só a Privacidade tem "última atualização".

### C. Estrutura, páginas órfãs e metadados

- **C1. `/colecao/<id>/` é órfã e destoa.** Nada aponta para ela (Coleções, home e breadcrumb do documento usam `/busca/?colecao_v6=`); duplica o Acervo filtrado com outro desenho (sem eyebrow, `h2` de 22 px, paginação sem números nem `aria-current`, fechamento cinza condicional, sem meta description) e expõe a hierarquia do Nou-Rau como "Subcoleções", inclusive "Documentos Normativos" e "Vídeos" (tipos retirados). `/colecao/5/` dá 404. Decisão do dono: redirecionar 301 para `/busca/?colecao_v6=<slug>` (como `/curadoria/` já faz para Coleções, hoje com 302) ou linkar e alinhar ao padrão.
- **C2. Metadados.** `/favicon.ico` 404 em toda página (não há `<link rel="icon">`); meta description da home repetida em Acervo, documento (que tem resumo), `/colecao/` e 404; nenhum `rel="canonical"` nem `og:*`; `robots.txt` inexistente; sufixo do `<title>` "| Governo de SP" só em home, Sobre e legais; título da busca com termo diz "busca" ("licitação — busca —") enquanto a página se chama Acervo; título não muda com página ou filtro.
- **C3. Chips de filtro.** Filtro de tipo aparece como "Coleção: Súmulas" (tipo não é coleção); parâmetros sem interface (`etapa`, `permissao`, `complexidade`, `topic_id`) são aceitos e viram chips, inclusive "Etapa: …" (nome proibido para o eixo); valores inválidos viram chip cru ("Categoria: 99999", "A partir de abc"). Reproduzido.
- **C4. Sem JS, single-select vira multi.** Coleção, Categoria, Sub e Micro são checkboxes com exclusividade só em JS; `/busca/?category_id=1&category_id=3` aplica só a última, mas mostra dois chips e o × de um remove os dois. Reproduzido pelo revisor. Correção: `type="radio"` nesses grupos (também semanticamente correto para leitor de tela).
- **C5. Drawer de filtros no celular.** Fechado, continua na ordem de Tab (só `translateX`, sem `inert`); ao abrir, o foco não vai para ele e o botão vem depois da barra no DOM. Reproduzido pelo revisor.
- **C6. Nome acessível do cartão de documento** inclui o resumo inteiro (o cartão todo é um `<a>`; o corte em 3 linhas é só visual): nomes de link de 643 a 924 caracteres. Reproduzido pelo revisor. Correção: `aria-labelledby` no `h3`.
- **C7. Página do documento.** "Copiar link" copia a URL com `?ctx=` (estado da busca) em vez do permalink; "Materiais relacionados" são sempre os 4 mais recentes do assunto (iguais para todo documento daquele assunto); sem `ctx` válido o bloco anterior/próximo some inteiro, inclusive "Voltar à busca", e o retorno não leva a âncora `#acervo-resultados`. Reproduzidos pelo revisor.
- **C8. Referência ABNT.** O título recebe "." mesmo quando termina em "?", "!" ou "." (49 títulos: "legislação?.", "..") e o autor idem ("de.."); falta "Disponível em: URL. Acesso em: data." (obrigatório para documentos online, e todos os 982 são remotos); sem ano não há "[s.d.]". Reproduzido por mim (pontuação) e pelo revisor (demais).
- **C9. Ordenação.** "Relevância" sem termo de busca é idêntica a "Adicionados recentemente"; `sort` desconhecido cai no padrão mostrando "Relevância"; `SORT_CHOICES` existe e nunca é usado. `page=0` e `page=-1` caem na última página.
- **C10. Temas em alta.** "Pregão" (busca textual) = 44 documentos na home contra 18 da microcategoria "Pregão" na barra; "Registro de Preços" 25 contra 14; "Compras Diretas" 14 contra 19 da subcategoria "Contratação Direta" (que ainda usa outro nome). Dois números para o mesmo nome no mesmo portal. Correção: permitir `subcategoria_nome`/`microcategoria_nome` em `TEMAS_DESTAQUE`, como já há `assunto_nome`.

### D. Terminologia e copy

- **D1.** "Cada categoria é uma etapa do ciclo da contratação" (Coleções, Acervo) mas duas das seis não são etapas (Ciclo Completo, Conteúdos Transversais); a home as chama "Visões transversais", nome que não existe em nenhuma outra página.
- **D2.** Lista de naturezas em Coleções ("Materiais", "Serviços", …) não bate com os valores do filtro ("Contratação de Materiais", …) e omite "Não se aplica", que é 87 % do acervo.
- **D3.** "Tipo de informação" (ficha do documento) vs "tipo de material" (Coleções) vs "por tipo" (dica do Acervo). Decisão do dono: "Tipo de informação" é o nome do campo na planilha da curadoria; escolher um e usar em toda parte.
- **D4.** Faceta "Categorias" no plural ao lado de "Coleção", "Natureza", "Assunto", "Ano" no singular.
- **D5.** "Pesquise no acervo" / "Pesquisa por" / "termos de pesquisa" (Acervo) contra "busca/buscar" em todo o resto.
- **D6.** "material" e "documento" alternam na mesma barra e na mesma página; três variantes de "sem material" ("Sem materiais ainda", "Ainda sem material nesta opção", "Sem materiais classificados por natureza ainda.").
- **D7.** `aria-label="Limpar todos os filtros"` num link cujo texto visível é "Limpar tudo" (WCAG 2.5.3: o texto visível deve estar contido no nome acessível). Breadcrumb com dois `aria-label` ("Trilha de navegação" / "Você está em").
- **D8.** Nomes das páginas legais em Title Case nos títulos e links cruzados ("Política de Privacidade", "Fale Conosco", "Mapa do Site") e em caixa de frase no rodapé e no 500 ("Política de privacidade", "Fale conosco").
- **D9.** Estado vazio contraditório: "O acervo ainda não tem documentos / Digite um termo na busca para começar"; "amplie o intervalo de anos" sugerido mesmo sem filtro de ano; `title="Ainda sem material nesta opção"` sob uma busca significa "nesta busca", não "no acervo".
- **D10.** "Lei 14.133/21" (chip e título do tema na home, duas descrições) contra a grafia "Lei nº 14.133/2021" do resto; "nova Lei de Licitações" (a Lei 8.666 já foi revogada); "Compliance" como chip de busca e em descrição de assunto, sem explicação.
- **D11.** Descrição da categoria Planejamento usa "ETP, TR" sem expandir (home, glossário, ficha); só o "Saiba mais" explica.
- **D12.** Texto da curadoria com critérios internos no glossário público ("Quando o foco for como o assunto é tratado na norma.", "Foco é a operação.", "Foca na penalização.", "Agentes públicos" com maiúscula, "a conduta ética e o compliance"). Levar à Lina: virar prosa ("Use este assunto quando…") ou sair. Capitalização irregular em dois assuntos ("Catálogo eletrônico de Padronização", "Compras Centralizadas/compartilhadas") e três microcategorias ("EMERGÊNCIA - Inciso VIII", "Art 75", "Contratação Direta outros incisos").
- **D13.** Descrição do acervo em quatro versões (home, Acervo, Sobre, meta); "Assuntos temáticos" (pleonasmo); dois blocos chamados "Temas em alta" na home (chips e seção); "Consultar Coleções" não diz o que acontece; explicação da busca omite que procura no autor; a mesma lei citada duas vezes no mesmo parágrafo em Coleções.

### E. Sistema visual e CSS

- **E1.** Cards `article.org-card` (Coleções, Sobre) recebem o hover de link (`.sp-card:hover` sobe o card) sem serem clicáveis.
- **E2.** Modal de cookies: rodapé com dois botões sem `flex-wrap` — estoura a 390 px com A+.
- **E3.** `prefers-reduced-motion` não cobre os chevrons das facetas (`.side-section > summary::after`, `.filter-group > summary::before`), só o do glossário e a seta-guia.
- **E4.** `.side-section:last-child { border-bottom: 0 }` nunca casa (o último filho do `aside` é o botão "Aplicar filtros"): a faceta "Ano" fica com fio sobrando.
- **E5.** Escala de títulos com exceções: `h2` em Montserrat 13–14 px no rodapé, no painel de filtros, no banner e nos painéis do documento (`.doc-section-title`, onde `h2` e `h3` têm o mesmo estilo); `h3` de 12 px nas facetas e em "Seus filtros"; `h3` do glossário de Coleções em Futura 22–30 px (o componente da home usa `h2`); no celular ou com título longo, o `h2` "Materiais relacionados" (piso 30 px) fica maior que o `h1` do documento (teto 28 px na faixa longa).
- **E6.** Sem `:hover` em "Limpar tudo", no botão de filtros do celular, nos `summary` das facetas e do glossário, nos links da ficha; sem sublinhado nos links da ficha.
- **E7.** Fechamento cinza condicional em Acervo (só com paginação), documento (só com relacionados) e `/colecao/`; 404 e 500 sem fechamento; a banda final da home tem só um eyebrow solto.
- **E8.** Breakpoints sem padrão: 560, 600, 640 (min e max no mesmo pixel), 767/768, 900, 1023/1024. Alvo de toque dos botões A−/A+/◐ com 28 px de largura no celular.
- **E9. Código morto e resíduos** (baixa, mas engana quem lê): `.page*` e `--space-page-top` (o `{% block content %}` de `base.html` nunca é usado), `.prose*`, `.contribute*`, `.curadoria-lista*`, `.doc-aplicabilidade`, `.nested-label`, `.filter-group__count`, `.side-section__opts`, `.sp-icons-sprite`, `.sp-title/.sp-subtitle`, `.c-bluedark` e `.doc-card__type.c-green/.c-bluedark`; o dicionário `_CAT_HOME_COLOR` (facets.py) nunca chega ao HTML; tokens `--sp-blue-medium`, `--sp-olive`, `--space-7`, `--space-10` sem uso; símbolo `fi-clock` sem uso; borda oliva no badge petróleo (resquício); dois context processors contam documentos e coleções a cada requisição sem nenhum template usar; padrão quadriculado implementado duas vezes; regras sem efeito (`.error-page__actions`, `.doc-resultnav .page-btn`, `.hero__geometry` repetida); estados `.active` e `:has(:checked)` duplicados; seis comentários de CSS descrevem comportamento que já não existe.

## Decisões que cabem ao dono

1. **Futura PT**: licenciar e servir localmente, ou adotar Montserrat como fonte de título (A7).
2. **`/colecao/<id>/`**: redirecionar 301 para o Acervo filtrado, ou linkar e alinhar ao padrão (C1).
3. **"Tipo de informação" × "tipo de material"**: um nome só (D3).
4. **Temas em alta com nome de nó da taxonomia**: apontar para o filtro do nó (um número só) ou renomear os temas (C10).
5. **Title Case × caixa de frase** nos nomes das páginas legais (D8).
6. **Texto da curadoria** com critérios internos no glossário (D12): pedir à Lina.

## Ordem sugerida de correção

1. **Lote 1 — não derrubar e não perder estado:** A1 (validação de filtros, limite de `q`, NUL, `LOGGING`), A2, B6.
2. **Lote 2 — acessibilidade medida:** A3, A4, A5, A6, C5, C6, E2, E3, D7.
3. **Lote 3 — dizer só a verdade:** B1–B5, B7–B9, A8, C2 (favicon, canonical, descriptions).
4. **Lote 4 — uma palavra para cada coisa:** D1–D13, C3, C9, C10 (após as decisões 3–5).
5. **Lote 5 — higiene do sistema visual:** E1, E4–E9, C1 (após a decisão 2), C4, C7, C8.

Cada lote cabe numa rodada com rebuild, testes, pa11y e cenas reproduzíveis.

## Evidências

- Rastreador: `docs/auditorias/2026-09-17-evidencias/crawl.json` (22 URLs × 2 larguras + status de cada link interno). A sondagem funcional do revisor (HTML bruto e JSON) ficou em pasta temporária da sessão, não versionada; cada item marcado "reproduzido por mim" foi refeito com `curl` ou no navegador headless.
- Medições citadas (contraste, fontes, escala, foco) foram feitas em navegador headless sobre a stack local em 17/09/2026.
