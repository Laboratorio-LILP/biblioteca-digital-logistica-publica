# Busca avançada por conteúdo (interseção de temas) — BDLP

- **Data:** 2026-06-09 · **Frente:** BDLP · **Branch:** `feat/busca-avancada-facetas`
- **Decisão (Bernardo + análise):** a busca avançada é uma camada de **interseção por
  conteúdo**, NÃO um duplicado da barra lateral.
- **Fora de escopo:** multi-classificação / mudança de taxonomia (decisão de Bernardo).

## Problema (esclarecido)

O "E/OU" do Renato inclui **um material que trate de dois assuntos/categorias ao mesmo
tempo** (interseção). Hoje cada material tem classificação **única** (1 assunto, 1
categoria principal), então a interseção DENTRO de uma dimensão pela classificação é
**sempre vazia**. A interseção real existe no **conteúdo** do material.

## Duas lentes, sem redundância

- **Lateral — classificação principal:** "materiais classificados como X **ou** Y"
  (união, faceta-aware, navegação rápida). É a multi-seleção já feita; mantida.
- **Busca avançada — conteúdo:** "materiais que tratam de **TODOS** estes temas"
  (interseção real por conteúdo: título + palavras-chave + resumo, via full-text **AND**).
  É o que a lateral **não** pode dar.

A busca textual já faz AND entre termos (`plainto_tsquery`): medido — *"governança
sustentabilidade" = 4* materiais que tratam de ambos. A busca avançada **expõe** isso,
guiada pela taxonomia.

## Temas = qualquer nó da taxonomia (todos primeira classe)

Cada nó (Assunto, Categoria, Subcategoria, Microcategoria) é um **tema** exigível por conteúdo:

- **Assunto · Sub · Micro:** termos concretos, ricos no conteúdo (medido: pregão=18,
  gestão de riscos=22, licitação=145, fiscalização=17…). Entram direto.
- **Categoria de topo:** o nome abstrato é fraco no conteúdo ("seleção do fornecedor"=4)
  → representada pelo **OU dos termos dos filhos** (licitação, pregão, leilão, contratação
  direta…) ≈ cobertura forte. A cascata vira a força, não a fraqueza.

**Mapa `tema_terms`:** semeado da taxonomia — nó folha → seu nome; Categoria de topo →
nomes dos descendentes. Refinável depois (sinônimos) sem tocar no schema.

## Consulta

Temas T1..Tn selecionados → `tsquery = termos(T1) & termos(T2) & … & termos(Tn)`, onde
`termos(Ti)` = **OU** dos termos do nó. Buscado no mesmo vetor FTS de `search_documents`
(português). Combinável com refino por classificação (Coleção/Natureza — facetas) + Ano +
ordenação + `q` livre (tudo em AND).

## UI

- **Lateral:** inalterada (classificação principal, faceta-aware).
- **Painel "Busca avançada"** acima dos resultados (`<form>` irmão — HTML não aninha forms):
  - Título: *"Encontre materiais que tratem de TODOS estes temas:"*
  - **Seletor de temas:** cascata Categoria→Sub→Micro + lista de Assuntos. Temas escolhidos
    viram **chips com E** entre eles.
  - **Refino opcional:** Coleção, Natureza, Ano De/Até.
  - Botões **Limpar** / **Buscar** (aplica de uma vez).
  - Texto instrutivo: "→ procura no título, palavras-chave e resumo" + resultado
    enriquecedor ("26 materiais tratam de Gestão de Riscos **e** Obras").

```
┌ Busca avançada — por conteúdo ──────────────────────────────────┐
│ Encontre materiais que tratem de TODOS estes temas:             │
│   [ + Adicionar tema  ▾ ]   (Assunto · Categoria › Sub › Micro) │
│   Exigidos (E):  [Gestão de Riscos x]  e  [Obras x]             │
│   -> procura no título, palavras-chave e resumo                 │
│ Refinar:  Coleção [v]   Natureza [v]   Ano [De][Até]            │
│                                       [ Limpar ]  [ Buscar > ]  │
└──────────────────────────────────────────────────────────────────┘
```

## Componentes / arquivos

| Arquivo | Mudança |
|---|---|
| `catalog/taxonomy_v6.py` (ou módulo novo) | `tema_terms(node)` — mapa nó→termos; Categoria de topo expandida pelos filhos. |
| `catalog/search.py` | `search_por_temas(temas, filtros, sort)` — monta o `tsquery` AND e busca no vetor FTS. |
| `catalog/views.py` | ler `tema` (getlist) + montar a busca avançada; contexto p/ template. |
| `templates/search.html` | painel construtor (form irmão) + seletor de temas + chips + refino + Buscar. |
| `static/css/portal.css` | estilos do painel. |
| `static/js/acervo-filters.js` | (opcional) adicionar/remover temas no cliente; sem JS, add via submit / remove via link. |

## Casos de borda

- **Sem temas:** painel mostra só o seletor; resultados seguem lateral/`q`/refino.
- **Tema de topo sem filhos com conteúdo:** cai para o próprio nome.
- **Sem JS:** seletor = `<select>` + "Adicionar" (submete e recarrega com o chip); remover = link.
- **Combina** com a lateral (classificação), `q` (texto livre) e refino — tudo em AND.
- Paginação já tem tie-breaker `-pk` (não regride).

## Plano de implementação

1. `tema_terms` (nó→termos; expansão por filhos) + teste dos termos por nó.
2. `search_por_temas` (tsquery AND) + teste de interseção (gestão de riscos E obras = 26).
3. View + leitura dos temas (`getlist`).
4. UI do painel (form irmão, seletor, chips, refino, Buscar) + CSS — **verificação visual no navegador**.
5. JS opcional (add/remove temas sem recarregar).
6. Verificação: interseção correta, sem-JS, não-redundância, paginação íntegra, visual.

## Testes (HTTP + visual)

- "gestão de riscos" E "obras" = 26; "licitação" E "inovação" = 10 (já medido).
- Categoria de topo expandida ("Seleção do Fornecedor" via filhos) ≫ 4.
- Painel sem-JS funciona; combina com a lateral; paginação 499/499.
- Visual (navegador): layout, chips, mobile.

## O que se reaproveita (não se descarta)

Backend multi-valor (`getlist`, faceta-aware) e a UI de chips da v2 são base direta.
A lateral multi-seleção permanece (lente de classificação). Só o **núcleo da interseção**
muda de `__in` (união por classificação) para `tsquery AND` (interseção por conteúdo).
