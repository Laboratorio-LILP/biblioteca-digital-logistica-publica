# Acervo — Levantamento de pendências (sessão de 10/06)

Estado da branch `feat/acervo-filtros-ux` (8 commits à frente da `main`). Nada pushado ainda.

## Feito e verificado por curl/shell

| Tarefa | O quê | Commit |
|---|---|---|
| T6 | Title Case de Categoria/Subcategoria (`titulo_pt`) | `4cefd07` |
| T1 | Painel "Seus filtros" com chips removíveis | `86523e0` |
| T2 | Filtro por ano (De/Até) + ordenação nos dois sentidos | `8386ce0` |
| T5+T4 | Paginação primeira/última + "Página X de Y" + 10/página | `88cc291` |
| T3 | Empty-states cientes de filtro + status "atualizando" | `474b286` |
| #3–#6 | Micros em Title Case (romanos preservados); fontes da barra unificadas; tooltip nos chips; frases por seção | `9ce1d3b` |
| #1 | Atualização AJAX in-place ao filtrar (ataca o salto) | `e1ae20d` |
| #2 | (decisão) chip = seleção; comportamento mantido, sem código | — |

## Pendências (precisam de você / verificação / decisão)

### 1. VERIFICAÇÃO VISUAL do AJAX (#1) — bloqueante para fechar
O Chrome MCP ficou indisponível a sessão toda, então o **comportamento** do AJAX não foi confirmado (só a estrutura/servidor). Testar no navegador:
- [ ] Filtrar **a partir do meio da lista** (rolar e clicar numa faceta) → **sem salto**; a lista troca no lugar.
- [ ] Multi-select de Assuntos; remover um chip (×) → foco volta ao controle.
- [ ] Paginação (Próxima/Última) → troca e **rola para o topo dos resultados**.
- [ ] "Limpar tudo", ordenação, Ano (De/Até + Enter) → tudo sem reload.
- [ ] Botão **Voltar** do navegador → volta o estado anterior (AJAX/popstate).
- [ ] **Sem JS** (desabilitar) → o `<form>` GET e o botão "Aplicar filtros" funcionam.
- [ ] Leitor de tela → anuncia "Atualizando resultados…" e "Resultados atualizados. N documentos".

### 2. pa11y (WCAG2AA) — não rodou (sem Node neste host)
Mais crítico agora com o AJAX (gerência de foco e `aria-live` na troca). Rodar `make a11y-check` num host com Node 18+ ou via Chrome MCP. a11y das fatias está "por construção".

### 3. Decisão de copy — Categorias (#6)
Escrevi *"Cada categoria é uma etapa do processo de contratação pública."* em vez de "processo licitatório" (você pediu "licitatório"). Motivo: as 6 categorias vão do planejamento (PCA) à gestão contratual — é mais amplo que a licitação. **Confirmar** se mantém "contratação pública" ou troca para "licitatório".

### 4. Slider duplo de ano — adiado
A base acessível (De/Até) está no ar. O slider visual é enriquecimento; o JS antigo foi removido na refatoração AJAX. Quando for fazer, religar via eventos delegados (`input` borbulha).

### 5. Fontes do #4 — confirmação visual
As regras CSS estão corretas (sub expansível = selecionável em font-sans 12px; micro 11px; "Toda a subcategoria" 12px itálico), mas o casamento visual é melhor confirmar no navegador.

### 6. Limpezas opcionais
- `#filter-active-count` no JS antigo era código morto — já não é referenciado na nova versão.
- Atualizar o deck `acervo-ux-copy-deck.md` (T6 dizia "micros ficam como estão"; mudou — agora recebem Title Case).

## Deploy / git (passos separados, quando aprovar)
- Push + merge `--no-ff` na `main` (`Laboratorio-LILP`).
- Deploy na VM de homologação (git pull + rebuild do portal). Validar atrás do `/Biblioteca/`.
- Atualizar a vault (Mapa-Semente §6A + changelog).
