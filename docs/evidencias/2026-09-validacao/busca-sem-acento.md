# Busca sem acento — termo × contagem antes/depois (stack local, 14/09/2026)

Antes = só `config="portuguese"` (medido na imagem anterior à T4, no início da sessão; `governanca`/`governança` não medidos antes); depois = `portuguese` + `portuguese_unaccent` somadas no vetor, consulta montada **por token** (OR das configurações e da variante re-acentuada dentro de cada palavra, E entre palavras) e casamento booleano explícito (`vetor @@ consulta`), rank só como limiar. Contagem lida de `.results-bar__count` em `/busca/?q=<termo>`. Regra: o termo sem acento devolve o mesmo conjunto do acentuado; nenhum par acentuado devolve menos do que antes.

| Termo | Antes | Depois |
|---|---:|---:|
| pregao | 0 | 44 |
| pregão | 44 | 44 |
| licitacao | 0 | 443 |
| licitação | 443 | 443 |
| licitações | 443 | 443 |
| sancao | 0 | 7 |
| sanção | 7 | 7 |
| orgao | 0 | 104 |
| órgão | 104 | 104 |
| órgãos | 104 | 104 |
| contratacao | 0 | 542 |
| contratação | 542 | 542 |
| 14.133 | 184 | 184 |
| governanca | – | 130 |
| governança | – | 130 |

Termos compostos (revisão adversarial de 14/09: a primeira versão da T4 fazia OR entre consultas inteiras e a raiz OR do `ts_rank` aceitava documento com só uma das palavras — "pregão eletrônico" dava 81 e "compras diretas" 530; na `main`, 29 e 13):

| Termo | main (medido na revisão) | Depois (por token + @@) |
|---|---:|---:|
| pregão eletrônico | 29 | 29 |
| pregao eletronico | 0 | 29 |
| compras diretas | 13 | 14 |
| registro de preços | – | 25 |
| registro de precos | – | 25 |
| gestão de riscos | – | 41 |
| gestao de riscos | – | 41 |

Sem a variante re-acentuada (só as duas configurações somadas, medido antes de acrescentá-la): `licitacao` = 196 e `contratacao` = 192 — o unaccent roda antes do radicalizador, então "licitacao" → "licitaca" e "licitacoes" → "licitaco" não se encontram; a variante fecha esse caso.

Tempo total de `/busca/?q=` (`curl -w %{time_total}`, 3 medições, segundos; imagem anterior × imagem final):

| Termo | Antes | Depois |
|---|---|---|
| licitação | 0.248 0.271 0.258 | 0.696491 0.702795 0.767446  |
| pregão | 0.206 0.207 0.216 | 0.493199 0.500098 0.513753  |
| 14.133 | 0.222 0.222 0.229 | 0.558561 0.577193 0.568327  |
| pregão eletrônico | – | 0.487102 0.482209 0.481567  |

Acréscimo por busca: ≈ 0,29 s ("pregão", 44 resultados), ≈ 0,34 s ("14.133", 184) e ≈ 0,45 s ("licitação", 443) — o vetor é calculado por consulta em duas configurações, no rank e no `@@`. **Acima do limite de 0,3 s combinado nos termos mais frequentes**; registrado, sem implementar agora. Se o acervo crescer, a saída é uma coluna `tsvector` materializada (as duas configurações somadas) com índice GIN — fora desta rodada. Sem a configuração `portuguese_unaccent` no banco (seção 1 não aplicada), a busca degrada para `portuguese` + variante re-acentuada e avisa no log, em vez de responder 500.
