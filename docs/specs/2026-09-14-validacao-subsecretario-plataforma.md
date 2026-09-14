# Validação do subsecretário — correções de plataforma (rodada de set/2026)

- **Data:** 2026-09-14 · **Frente:** BDLP · **Branch:** `feat/2026-09-validacao-subsecretario` (a partir de `main` em `5e80458`)
- **Contexto:** a Biblioteca esteve pública desde 02/09/2026. Em 08/09 o subsecretário avaliou a plataforma (três vídeos) e determinou a retirada do ar até homologar a versão corrigida. Esta rodada entrega a **parte de código**, para que uma única subida à TI (código + recarga do acervo v12) resolva os apontamentos. A curadoria (Lina, Jorge) corrige a planilha; a chefia redesenhou a taxonomia (reunião de 10/09 e e-mail "ALTERAÇÕES BIBLIOTECA" de 11/09).
- **Limites:** desenvolvimento local, sem servidor; nenhum segredo nas saídas; portas em loopback; `deploy/edge/`, `docker/nourau/`, Caddy e compose de produção intocados; layout do protótipo preservado (acréscimos, não redesenho); um commit por tarefa; sem merge, sem push.
- **Ordem de execução:** T3 → T4 → T1 → T2 → T6 → T5 → T7 (T3 primeiro porque muda seed e vocabulário; T7 é a varredura textual final).
- **Evidências:** `docs/evidencias/2026-09-validacao/` (capturas antes/depois em desktop 1440×900 e mobile 390×844, saídas de `validate_import` e `--dry-run`, tabela da busca, verificação com CSP). Cenas reproduzíveis: `tools/evidencias_playwright.py`.
- **Verificação comum a todas as tarefas:** `ruff check portal/` limpo; `cd portal && DJANGO_SECRET_KEY=teste-local-sem-valor python -m pytest -v` (caminho do CI; 138 testes) verde; `make validate` verde com as seções novas; zero erro de console com CSP ligada (`DJANGO_DEBUG=false`).

---

## T3 — Taxonomia v12: vocabulário de tipos, 16 assuntos, subcategorias sem prefixo, importador estrito

**Decisão.** Refletir exatamente o e-mail da Lina de 11/09: Jurisprudência = Súmulas, Boletins, **Acórdãos**, **Deliberações** (saem Enunciados e Documentos Normativos); Doutrina e Conteúdo Técnico ganha **Enunciados** e **Pareceres**; Instrução e Capacitação perde **Vídeos**. Dois Assuntos novos (ordem 15 e 16). Subcategorias de Planejamento sem o prefixo "FASE PREPARATÓRIA - ". Normas, leis, decretos e portarias saem do acervo **pela planilha** (linhas em vermelho), não por código. Documentos ainda carregados com tipos retirados continuam **exibidos** na coleção antiga (`TIPOS_LEGADOS`, só em `colecao_v6_for_tipo`) durante a janela entre a subida do código e a recarga; o importador os **recusa**.

**Arquivos.** `portal/catalog/taxonomy_v6.py` (`_TIPOS_POR_COLECAO`, `TIPO_V5_TO_V6`, `tipo_canonico()`, `TIPOS_LEGADOS`, descrições das coleções); `portal/catalog/templatetags/catalog_tags.py` (`SUBCAT_DISPLAY` com as duas grafias por um ciclo); seeds `docker/postgres/init/00-extensions.sql` (novo), `06-collections.sql`, `06-taxonomia.sql`, `07-categories.sql`, `08-type-information.sql`; `docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql` (novo, idempotente, duas seções); `portal/catalog/management/commands/migrate_spreadsheet.py` (importador estrito, `--allow-new-types`, aliases, `--dry-run` lista todas as recusas); `validate_import.py` (tipos fora do vocabulário, aviso de tipos retirados, contagem por subcoleção, 16 assuntos); `tools/db-refresh.md`, `docs/DEPLOY.md` §4.1; testes `test_taxonomy_v12.py`, `test_migrate_spreadsheet.py`.

**Importador estrito (regras).** Coleção vazia ou que não casa uma raiz → recusa (nunca a primeira raiz). Tipo fora do vocabulário da coleção resolvida → recusa (grafias legadas como "Acórdão"/"deliberacao" são normalizadas por `tipo_canonico`). Categoria, Subcategoria, Microcategoria ou Assunto **preenchidos** e não resolvidos → recusa (o código anterior deixava NULL em silêncio — divergência registrada). Tipo novo só com `--allow-new-types` (exceção documentada). Aliases contados no resumo: `PLANO ANUAL DE CONTRATAÇÕES (PCA)` → `PLANO DE CONTRATAÇÕES ANUAL (PCA)`; `FASE PREPARATÓRIA - X` → `X`. Savepoint por linha, `--skip-red` e resumo final preservados.

**Como verificar.**
- `pytest` (contratos: vocabulário, seeds sem tipos retirados, 16 assuntos, subcategorias sem prefixo, script com duas seções e guardas, importador com mapas falsos).
- Banco existente: aplicar o script duas vezes — a segunda não altera nada (snapshot idêntico de `topic`, `topic_path`, `type_information`, `nr_assunto`, `nr_subcategoria`, `pg_ts_config`); a seção 2 imprime `NOTICE: ... ainda referenciado por 7 documento(s)` (Documentos Normativos) e `3` (Vídeos) e não remove nada; o Enunciados vazio sob Jurisprudência é removido.
- Volume novo: Postgres descartável com senhas efêmeras montando `docker/postgres/init` — árvore v12 completa, 16 assuntos, subcategorias renomeadas, `unaccent` e `portuguese_unaccent` presentes (o tipo `Vídeos` id 55 permanece porque é um dos 67 padrão do Nou-Rau em `04-reset-nr.sql`).
- `--dry-run --skip-red` na planilha PARA CORREÇÃO (cópia local de 08/09, ainda sem a revisão de 11/09): 972 aceitas, 10 recusadas (7 Documentos Normativos, 3 Vídeos), 55 linhas normalizadas pelo alias de subcategoria, 0 pelo alias de categoria (`docs/evidencias/2026-09-validacao/dry-run-para_correcao.txt`). Idem para a v11.
- `make validate`: 16 assuntos (os dois novos com 0), "Tipos de informação em uso fora do vocabulário canônico v12: Documentos Normativos 7, Vídeos 3", "AVISO v12: 10 documento(s)".

**Fora.** Recarga real do acervo v12 (depende da planilha revisada, no site de equipe, e das inserções do Jorge); planilha-modelo v12 (entrega do Bernardo no Excel — o template `BDLP_Template_Insercao_v8 (NOVA TAXONOMIA).xlsx` ainda traz listas v8, inclusive a grafia "PLANO ANUAL DE CONTRATAÇÕES (PCA)", coberta pelo alias); multiclassificação; `make test` quebrado (tarefa própria).

## T4 — Busca sem acento

**Decisão.** Somar, não trocar: vetor = os 9 campos em `portuguese` **+** os mesmos campos (mesmos pesos) em `portuguese_unaccent` (COPY de `portuguese` com `unaccent` nas palavras); consulta = OR das duas; `rank__gte=0.01` mantido. Medido na stack, a soma sozinha não fechava o caso plural do termo sem acento (`licitacao` achava 196 de 443): o `unaccent` roda **antes** do radicalizador, então "licitacao" → "licitaca" e "licitacoes" → "licitaco" nunca se encontram (o achado da RECPSP). A consulta ganha uma **variante re-acentuada dos sufixos nasais** (`reacentuar`: -cao → -ção, -coes → -ções, -ao → -ão, -oes → -ões; só em tokens ASCII) em OR — só acrescenta resultados. Facetas seguem usando `apply_fulltext` (critério único).

**Arquivos.** `portal/catalog/search.py`; `docker/postgres/init/00-extensions.sql`; seção 1.1 do script de migração; `test_busca_sem_acento.py`.

**Como verificar.** Tabela termo × contagem antes/depois em `docs/evidencias/2026-09-validacao/busca-sem-acento.md`: pregao 0→44, licitacao 0→443, licitações 443→443, sancao 0→7, orgao 0→104, órgãos 104→104, contratacao 0→542, 14.133 184→184, governanca = governança = 130. Tempo de `/busca/?q=`: +≈0,29 s ("pregão") a +≈0,45 s ("licitação", 443 resultados) por consulta — acima do limite de 0,3 s combinado nos termos mais frequentes (o `@@` explícito da revisão recalcula o vetor no WHERE); registrado, sem implementar agora.

**Fora.** Coluna `tsvector` materializada (as duas configurações somadas) + índice GIN — proposta para recuperar o tempo de resposta (tarefa própria); `unaccent` mid-word em flexões (coberto pela configuração `portuguese_unaccent`).

## T1 — Filtros do Acervo sem voltar ao topo

**Decisão.** Base sem JS + melhoria progressiva com JS próprio, sem biblioteca. Sem JS: o `action` do form e todos os links GET (chips, "Limpar tudo", paginação, "Limpar tudo" do estado vazio) terminam em `#acervo-resultados`; `scroll-margin-top` compatível com o cabeçalho sticky; barra lateral `position: sticky` com rolagem própria em ≥ 1024px (grade e visual intactos; drawer mobile intacto). Com JS (`acervo-filters.js`): `fetch` do HTML completo da mesma view, `DOMParser`, troca de `#acervo-sidebar`, `#acervo-resultados` e `#acervo-paginacao` (a própria `<section>`, inserida/removida quando a paginação aparece/some — manter o trio de fundos), `<details>` abertos reaplicados, foco devolvido ao controle tocado (`preventScroll`), rolagem intocada, drawer preservado, `document.title` atualizado, `pushState`/`replaceState` + `popstate` sem recarregar, `aria-busy` e "Resultados atualizados: N documentos" no `aria-live` (que fica **fora** da região trocada, senão não é anunciado). Pedidos em voo abortados/ignorados; qualquer falha cai no `form.submit()` (que aterrissa na âncora). O cabeçalho `X-Requested-With` é informativo; a view não muda. O Chromium **preserva** o fragmento do `action` ao montar a URL GET (confirmado sem JS).

**Arquivos.** `portal/templates/search.html`, `_partials/_applied_filters.html`, `portal/static/js/acervo-filters.js`, `portal/static/css/portal.css`; `tools/evidencias_playwright.py`; `test_filtros_sem_voltar_ao_topo.py`.

**Como verificar.** `python tools/evidencias_playwright.py --suffix depois --verify` (JS ligado: scrollY 1112 → 1112, URL `?assunto_id=…`, foco no checkbox, chip, anúncio, voltar sem recarregar; sem JS: URL com `#acervo-resultados`, scrollY 456; mobile: drawer aberto e lista atualizada por trás). Capturas `acervo-filtro-assunto-*-{antes,depois}.png`. Com CSP ligada: `csp-verificacao.txt`.

**Fora.** Interceptar o botão "Buscar" do herói (navegação completa, aterrissa nos resultados); rolar até o topo dos resultados ao paginar (a regra "não mover a rolagem" vale para tudo — fácil de rever).

## T2 — Os dois eixos no cartão e na página do documento

**Decisão.** Rodapé do cartão: `Etapa: <Categoria › Subcategoria> · Assunto: <Assunto>`, rótulos em texto, mesma tipografia (11px, cor 0.55); cada eixo trunca por si e o segundo desce de linha quando não cabem juntos, para o Assunto nunca sumir no mobile. Sem categoria → só o Assunto; sem Assunto → nome da coleção. `classificacao_card` (simple_tag pura) resolve pelos mapas cacheados — zero query por cartão (medido: `/busca/` 17 → 17 queries, home 36 → 36, documento 13 → 13). Página do documento: badge "Etapa: …" (ícone `fi-layers` do sprite), fórmula da Lina em Linguagem Simples sob "Classificação BDLP", rótulo "Etapa (categoria processual)" só na exibição. Hints das facetas amarrando etapa/categoria e assunto/tema.

**Arquivos.** `catalog_tags.py`, `_partials/_doc_card.html`, `document_detail.html`, `search.html`, `portal.css`; `test_dois_eixos.py`.

**Como verificar.** Capturas `cartao-dois-eixos-{desktop,mobile}-{antes,depois}.png`, `documento-classificacao-desktop-{antes,depois}.png`, `home-temas-em-alta-desktop-depois.png`; contagem de queries via `manage.py shell` com `connection.force_debug_cursor = True`.

**Fora.** Microcategoria no cartão; mudança de cor/tamanho do rodapé.

## T6 — Definições dos Assuntos e Coleções na interface

**Decisão.** O código publica o texto da curadoria (Lina, 11/09/2026), não escreve rascunho: `taxonomy_v6.ASSUNTOS_DESCRICAO` (16 entradas, `curta` = Caracterização, `longa` = Explicação, verbatim com as correções de digitação autorizadas), no mesmo padrão de `COLECOES_V6["descricao"]` — `nr_assunto` não tem coluna, o portal é somente leitura e não há migrations Django. Categorias reusam `nr_category.description`. Página de Coleções: fórmula + frase multidimensional; glossário `#assuntos`/`#categorias` (nome linkado ao acervo filtrado, curta, longa num `<details>` por item); contagem de assuntos deixa de ser chumbada. Facetas: link "O que significa cada opção?" para as âncoras (sem tooltip). Documento: caracterização curta sob Assunto e Etapa. A "página de metodologia" do Eduardo consumirá o mesmo dado.

**Arquivos.** `taxonomy_v6.py` (`ASSUNTOS_DESCRICAO`, `descricao_assunto`), `catalog_tags.py` (`assunto_curta`, `assunto_longa`), `facets.py` (`assuntos_glossario`, `categorias_glossario`), `views.py`, `collection_list.html`, `search.html`, `document_detail.html`, `portal.css`; `test_glossario_assuntos.py`.

**Como verificar.** `/colecoes/`: 16 + 6 itens de glossário; o link da faceta aterrissa em `#assuntos` com a folga do cabeçalho (topo a 88px); `<details>` abre; `/colecoes/` 7 queries. Capturas `colecoes-glossario-desktop-{antes,depois}.png`, `colecoes-glossario-mobile-depois.png`.

**Fora.** Coluna de descrição em `nr_assunto` (exigiria SQL da TI e via de edição); página de metodologia com caso fictício.

## T5 — Verificações de redundância e de qualidade (só relatório)

**Decisão.** Módulo puro `catalog/qualidade.py` (sem banco), usado pelo `validate_import` (acervo carregado) e pelo `migrate_spreadsheet --dry-run` (linhas da planilha, como **avisos**). Nunca altera dados. Códigos e semântica no docstring e em `tools/db-refresh.md`: `DUPLICATA_TITULO`, `DUPLICATA_DOI`, `DUPLICATA_DIVERGENTE` (campos divergentes listados), `ENDERECO_COMPARTILHADO` (URL igual com títulos diferentes — estante, não duplicata), `RESUMO_VAZIO/MINUSCULA/RETICENCIAS/CITACAO/CURTO/IGUAL_TITULO/SCRIBD`, `AUTORIA_SERIE`.

**Arquivos.** `catalog/qualidade.py`, `validate_import.py`, `migrate_spreadsheet.py`, `tools/db-refresh.md`; `test_qualidade.py`.

**Como verificar.** `make validate` → seção "Possíveis redundâncias e problemas de qualidade" (acervo local: 447 achados em 982 — `RESUMO_CURTO` 391, `RESUMO_MINUSCULA` 19, `RESUMO_SCRIBD` 10, `RESUMO_RETICENCIAS` 7, `RESUMO_CITACAO` 7, `DUPLICATA_TITULO` 4, `RESUMO_IGUAL_TITULO` 4, `DUPLICATA_DIVERGENTE` 2, `DUPLICATA_DOI` 2, `ENDERECO_COMPARTILHADO` 1); `--dry-run` → os mesmos achados por linha da planilha. Saídas em `docs/evidencias/2026-09-validacao/validate-import-qualidade.txt` e `dry-run-para_correcao.txt`.

**Fora.** Qualquer correção automática; ajuste do limiar de 300 caracteres (391 resumos abaixo — decisão da curadoria).

## T7 — Varredura dos textos que descrevem o acervo

**Decisão.** `grep -rn -i "normativ|vídeo|videos" portal/ docs/ README.md DEMO.md`. Tocados: meta description padrão (`base.html`) e intro do Sobre (`about.html`); descrições das coleções já saíram na T3. Deixados, com motivo: "Marco normativo" (Sobre, Mapa do site, comentário CSS) — marco legal da própria Biblioteca; `docs/identidade_visual.md` (fundamento normativo do design); copy deck (menção hipotética); caracterização do Assunto "Aspectos Jurídicos e Regulatórios" (texto da curadoria sobre o tema); código/testes que citam os tipos retirados por necessidade; `DEMO.md` (507/v9) — tarefa própria.

**Arquivos.** `base.html`, `about.html`; `test_varredura_textos.py`.

---

## Revisão adversarial da branch (14/09/2026) — achados confirmados e correções

Sete lentes de revisão (JS/a11y, SQL, importador, busca, templates/CSS, qualidade, escopo/segredos) sobre `git diff main..HEAD`; cada achado foi submetido a um refutador independente que tentou reproduzi-lo. 20 achados brutos, 14 verificados: **8 confirmados** (corrigidos no commit `fix(revisao)`), 6 refutados; dos 6 de severidade baixa não verificados, 4 foram corrigidos por serem baratos.

| # | Sev. | Achado confirmado | Correção |
|---|---|---|---|
| 1 | alta | `focar()` punha `tabindex="-1"` no `<summary>` (nativamente focável) após "Limpar tudo"/remoção de chip — o summary saía da ordem de Tab (WCAG 2.1.1). | Só recebe `tabindex="-1"` quem tem `el.tabIndex < 0`; fallback de foco do chip prefere um chip restante antes da primeira faceta. Verificação nova em `evidencias_playwright.py` (`limpar_tudo_foco_na_ordem_de_tab`). |
| 2 | alta | Busca com mais de uma palavra virou OU: OR entre consultas inteiras deixava a raiz do `tsquery` em OR e o `ts_rank` aceitava documento com só uma das palavras ("pregão eletrônico" 29 → 81; "compras diretas" 13 → 530). | Consulta montada **por token** (OR das configurações e da variante re-acentuada dentro da palavra, E entre palavras) e casamento booleano explícito `vetor @@ consulta` (`filter(busca=…)`); rank só como limiar. Medido: "pregão eletrônico" 29 = `main`; "pregao eletronico" 29. |
| 3 | média | Resposta em voo sobrescrevia o que o usuário editou (ano digitado, 2º clique em multi-select) enquanto o fetch corria. | Em `trocar()`, pedido vindo do form é descartado e reagendado se houver `timer` pendente ou `urlDoForm() !== url`. |
| 4 | média | Substring de subcategoria casava nomes de 2–3 letras do banco (`TR` dentro de "OUTROS", "CONTRATAÇÃO DIRETA") e classificava errado em silêncio. | Tamanho mínimo (5) nos DOIS lados do substring; aliases explícitos "Termo de Referência (TR)"/"Estudo Técnico Preliminar (ETP)". |
| 5 | média | `--allow-new-types` era inócua: `_resolve_topic` recusava o tipo desconhecido antes de `_ensure_type`. | Flag propagada até `_tipo_da_colecao`: tipo desconhecido é aceito e cai na raiz da coleção; tipos retirados continuam recusados (`tipo_retirado`). Help/runbook ajustados. |
| 6 | média | Banco sem a seção 1 (`portuguese_unaccent` inexistente) derrubava `/busca/` e a home com 500. | `_unaccent_disponivel()` consulta `pg_ts_config` (positivo em cache; negativo reavaliado e avisado uma vez no log) e a busca degrada para `portuguese` + variante re-acentuada. |
| 7 | média | Links "Veja o que entra em cada um/etapa" nos cards de Coleções herdavam `a { color: inherit; text-decoration: none }` e ficavam invisíveis como link. | `.org-card__nota a { color: var(--sp-blue); text-decoration: underline }`. |
| 8 | baixa | `popstate`/chips não sincronizavam a caixa `q` do herói com a URL restaurada. | Após a troca, se o pedido não veio do form, a caixa recebe o `q` da URL. |

Corrigidos além dos confirmados (baixa, não verificados): subcategoria/microcategoria preenchidas sem o nível acima resolvido agora recusam a linha; placeholders de DOI/URL ("Não possui", "-", "n/a", "[Acesso restrito]") não viram chave de agrupamento; `RESUMO_RETICENCIAS` reconhece "(...)", "[...]" e reticências seguidas de aspas; `_ROMANO_RE` estrito ("civil", "mil" não são numerais). Higiene no script de migração: 1.5 só vincula usuários a subcoleções sem vínculo nenhum. Refutados (sem ação): revínculo de `topic_users` a cada execução (é o critério do seed), colchetes em URL derrubarem o relatório (tratado junto com os placeholders), `DUPLICATA_DIVERGENTE` comparar grafias cruas no dry-run, seção 2 não limpar `nr_topic_category` (só raízes lá), divergência do tipo `Vídeos` id 55 entre volume novo e migrado (documentado), alias com travessão morto (removido).

## Divergências entre o briefing e o código encontrado

1. `_resolve_category` **não** registrava erro de linha quando a categoria não resolvia — devolvia `None` e o documento entrava sem categoria. O briefing dizia que já registrava. A T3 implementa a recusa (e a estende a Subcategoria, Microcategoria e Assunto preenchidos).
2. `collection_list.html` chumbava "Hoje são 14 assuntos." (o briefing só citava `facets.py`/`views.py`/`home.html`). Corrigido na T6 (contagem dinâmica).
3. Existe um índice GIN `idx_nr_document_fts` (`06-taxonomia.sql`) sobre `to_tsvector('portuguese', …)` que a consulta do portal **não usa** (o ORM monta `SearchVector` por campo com pesos). O briefing dizia "sem índice GIN". Sem efeito prático; anotado.
4. O `.env` local tinha `DJANGO_DEBUG=false` (CSP ligada) desde o início — não `true` como o `.env.example` sugere para dev. Todas as cenas rodaram com CSP; o valor original foi mantido.
5. `_load_topic_map` colapsava subcoleções homônimas sob raízes diferentes (chave só por nome) — na janela da v12 "Enunciados" existe sob Jurisprudência e sob Doutrina. Chave passa a ser `(parent_id, nome)`.
6. A planilha PARA CORREÇÃO da pasta da frente é a cópia de 08/09 (0 linhas vermelhas/amarelas); a revisada (11/09, com a taxonomia nova) está no site de equipe (`VERSÕES DA PLANILHA`, modificada em 14/09) e precisa ser baixada para a pasta da frente antes da recarga. O dry-run desta rodada usou a cópia local.
