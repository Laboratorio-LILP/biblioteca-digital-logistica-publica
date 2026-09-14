# Busca sem acento — termo × contagem antes/depois (stack local, 14/09/2026)

Antes = só `config="portuguese"` (medido na imagem anterior à T4, no início da sessão; `governanca`/`governança` não medidos antes); depois = `portuguese` + `portuguese_unaccent` somadas no vetor e na consulta, mais a variante re-acentuada dos sufixos nasais (`reacentuar`: -cao → -ção, -coes → -ções, -ao → -ão, -oes → -ões) em OR. Contagem lida de `.results-bar__count` em `/busca/?q=<termo>`. Regra: o termo sem acento devolve o mesmo conjunto do acentuado; nenhum par acentuado devolve menos do que antes.

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

Sem a variante re-acentuada (só as duas configurações somadas, medido antes de acrescentá-la): `licitacao` = 196 e `contratacao` = 192 — o unaccent roda antes do radicalizador, então "licitacao" → "licitaca" e "licitacoes" → "licitaco" não se encontram; a variante fecha esse caso.

Tempo total de `/busca/?q=` (`curl -w %{time_total}`, 3 medições, segundos; imagem anterior × imagem com a T4):

| Termo | Antes | Depois |
|---|---|---|
| licitação | 0.248 0.271 0.258 | 0.493406 0.497301 0.505427  |
| pregão | 0.206 0.207 0.216 | 0.459832 0.441060 0.445430  |
| 14.133 | 0.222 0.222 0.229 | 0.460141 0.473136 0.467175  |
| licitacao (3 consultas em OR) | – | 0.503902 0.511277 0.513202  |

Acréscimo ≈ 0,25 s por busca (vetor calculado por consulta, agora em duas configurações), abaixo do limite de 0,3 s combinado. Se o acervo crescer, a saída é uma coluna `tsvector` materializada (as duas configurações somadas) com índice GIN — fora desta rodada.
