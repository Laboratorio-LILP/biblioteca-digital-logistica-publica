# Carga e troca completa do acervo (refresh)

O importador (`migrate_spreadsheet`) **só acrescenta** materiais (*insert-only*), com código sequencial `bdlp-XXXXXX`: rodar de novo sem limpar gera duplicatas. Para refletir uma planilha FINAL no banco, faça a **troca completa do acervo** (*full-refresh*).

Desde a taxonomia **v12** (set/2026) o importador é **estrito**: recusa a linha (e segue para a próxima) quando a Coleção não casa uma coleção raiz, quando o Tipo de informação está fora do vocabulário da coleção (Documentos Normativos, Vídeos e Pareceres inclusive) ou quando Categoria, Subcategoria, Microcategoria ou Assunto preenchidos não resolvem. Tipo novo não é criado por padrão (`--allow-new-types` só como exceção documentada). O `--dry-run` lista **todas** as linhas recusadas com motivo — é o insumo da curadoria antes da carga.

## Carga incremental / primeira carga
```bash
make backup                                   # sempre antes: banco (.dump, formato custom) + arquivos da curadoria (.tgz)
docker compose --env-file .env -f docker/docker-compose.yml cp <planilha.xlsx> portal:/tmp/acervo.xlsx
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal \
  python manage.py migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material" --skip-red --dry-run   # deve sair com 0 recusas
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal \
  python manage.py migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material" --skip-red
make validate
```
> A aba de dados é `"Inserir Material"`. **`make migrate` e `make migrate-dry` não servem para as planilhas da curadoria:** repassam só `$(FILE)`, sem `--sheet` e sem `--skip-red`, e o comando para com `CommandError: Nenhuma aba de dados encontrada` (conferido em 23/09/2026 com a planilha da recarga). Use o comando direto acima. A cópia para `/tmp/acervo.xlsx` some se o contêiner do portal for recriado: copie depois de qualquer `up -d --build portal`.

Flags úteis:
- `--skip-red` — pula linhas com fundo vermelho (a curadoria marca assim o que sai do acervo). As planilhas da curadoria da v12 (a PARA CORREÇÃO e a da recarga) **exigem** esta flag.
- `--dry-run` — só simula; lista todas as recusas com motivo e conta os aliases de grafia usados.
- `--allow-new-types` — aceita um tipo **fora do vocabulário** em vez de recusar a linha: cria o tipo em `type_information` e deixa o documento na **raiz** da coleção (sem subcoleção). Tipos **retirados** (Documentos Normativos, Vídeos, Pareceres) continuam recusados mesmo com a flag. **Exceção documentada**: não use em carga normal; se a planilha traz um tipo novo, a decisão é da chefia (vocabulário em `portal/catalog/taxonomy_v6.py`).
- `--start-seq N` — primeiro código `bdlp-XXXXXX` em cargas incrementais.

Aliases de grafia aceitos e normalizados (contados no resumo): categoria `PLANO ANUAL DE CONTRATAÇÕES (PCA)` → `PLANO DE CONTRATAÇÕES ANUAL (PCA)` (grafia das listas do template v8); subcategoria `FASE PREPARATÓRIA - X` → `X` (grafia da planilha PARA CORREÇÃO) e as siglas por extenso `Termo de Referência (TR)` → `TR`, `Estudo Técnico Preliminar (ETP)` → `ETP`. Grafias legadas de tipo (`Acórdão`, `deliberacao`, `Enunciado`) viram o nome canônico plural; `Parecer`/`Pareceres` é recusado (retirado na v12.1). O casamento por substring de subcategoria/microcategoria exige 5 caracteres nos dois lados (nomes curtos como `TR` só casam por igualdade ou alias); subcategoria preenchida sem categoria resolvida, ou microcategoria sem subcategoria, recusa a linha.

## Verificações de qualidade para a curadoria (`validate_import` e `--dry-run`)

O módulo puro `portal/catalog/qualidade.py` aponta possíveis redundâncias e problemas de qualidade — **só relatório**: nada é alterado, nenhuma linha é recusada. Aparece em duas saídas: a seção "Possíveis redundâncias e problemas de qualidade" do `validate_import` (sobre o acervo carregado, referência = `code`) e, como **avisos**, no fim do `migrate_spreadsheet --dry-run` (sobre as linhas da planilha, referência = número da linha). Cada achado tem código, referência(s) e título curto.

| Código | O que aponta |
|---|---|
| `DUPLICATA_TITULO` | mesmo título normalizado (sem acento, caixa, pontuação e espaços múltiplos) |
| `DUPLICATA_DOI` | mesmo DOI normalizado |
| `DUPLICATA_DIVERGENTE` | duplicata cujas linhas divergem em Coleção, Tipo, Assunto, Categoria ou Subcategoria — "duplicidade caracterizada de forma diferente" (o caso mais perigoso); lista os campos |
| `ENDERECO_COMPARTILHADO` | mesmo endereço normalizado (sem `#fragmento`, sem `utm_*`, sem barra final, host em caixa baixa) com títulos **diferentes** — "estante/coletânea? confirmar endereço individual". **Não é duplicata** (publicações na mesma estante do fliphtml5) |
| `RESUMO_VAZIO` | sem resumo |
| `RESUMO_MINUSCULA` | resumo começa com letra minúscula (trecho copiado do meio do texto) |
| `RESUMO_RETICENCIAS` | resumo termina com "..." ou "…" (trecho cortado) |
| `RESUMO_CITACAO` | marcador de citação `[n]`/`[n, m]` no resumo (`[2024]` é ano, não conta) |
| `RESUMO_CURTO` | menos de 300 caracteres (mínimo da planilha-modelo) |
| `RESUMO_IGUAL_TITULO` | resumo começa repetindo o título |
| `RESUMO_SCRIBD` | endereço em scribd.com — a página traz introdução, não resumo: "conferir se é resumo de fato" |
| `AUTORIA_SERIE` | mesmo autor pessoa em todos os volumes de uma série com "Caderno", "Manual" ou "Guia" no título — aponta, não julga |

Um resumo pode acumular vários códigos. O relatório mostra a contagem por código e alguns exemplos (5 no `validate_import`, 10 no `--dry-run`).

## Troca completa do acervo (substituir todo o acervo)
Não é preciso apagar o volume do banco (`down -v`): nenhuma outra tabela aponta para `nr_document` (chave estrangeira). No contêiner do Postgres:
```sql
TRUNCATE TABLE nr_document RESTART IDENTITY;
SELECT setval('nr_document_seq', 1, false);
```
A sequência `nr_document_seq` é o contador do banco que dá o número do próximo material; o `setval` o põe de volta em 1. Ele é necessário: essa sequência não pertence à coluna, e o `RESTART IDENTITY` sozinho não a zera (conferido em 23/09/2026). Sem o `TRUNCATE`, os códigos novos batem nos antigos e o importador recusa as linhas. Depois reimporte (`migrate_spreadsheet ... --sheet "Inserir Material" --skip-red`) e `make validate`.

Passos completos (o backup primeiro; é o que permite voltar atrás com `make restore FILE=backup_….dump`):
```bash
make backup
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -v ON_ERROR_STOP=1 \
  -c "TRUNCATE TABLE nr_document RESTART IDENTITY;" \
  -c "SELECT setval('nr_document_seq', 1, false);" \
  -c "SELECT count(*) FROM nr_document;"
docker compose --env-file .env -f docker/docker-compose.yml cp <planilha.xlsx> portal:/tmp/acervo.xlsx
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal \
  python manage.py migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material" --skip-red
make validate
```
Para voltar atrás: `make restore FILE=backup_AAAAMMDD_HHMMSS.dump` (`pg_restore --clean --if-exists --single-transaction`, tudo ou nada; em seguida o alvo recria a conta de leitura do portal e revoga de novo a leitura de `users`) e, se for o caso, `make restore-files FILE=backup_AAAAMMDD_HHMMSS_arquivos.tgz`. Detalhes e o método B em `docs/DEPLOY.md` §4.2. Desde 30/09/2026 o `make backup` grava em formato custom (`-Fc`): um `.sql` em texto sem `--clean`, restaurado por cima de banco com dados, dá 117 erros com código de saída 0 e deixa o banco como estava, com as sequências dessincronizadas (ensaio de 23/09/2026) — por isso o alvo antigo saiu.

## Taxonomia v12 em banco existente — passo a passo (dev e homologação)

Os scripts de init (`docker/postgres/init/*`) só rodam em **volume novo**. Um banco que já existe (o volume de desenvolvimento e o de homologação) recebe a v12 pelo script `docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql`, que pode rodar mais de uma vez sem efeito extra (idempotente) e tem duas seções: a **seção 1** é aditiva (tipos e subcoleções novos, os 2 Assuntos, subcategorias sem prefixo, extensão `unaccent` e configuração `portuguese_unaccent`; desde 30/09/2026 também a coluna gerada `busca` com índice GIN — seção 1.10 — e o `REVOKE` de `users` para a conta do portal — seção 1.11) e pode rodar a qualquer momento; a **seção 2** remove Documentos Normativos, Vídeos, Pareceres (v12.1) e o Enunciados antigo sob Jurisprudência **somente** se nenhum documento os referencia — senão só imprime `NOTICE: ... aviso`. O arquivo inteiro pode ser executado quantas vezes for preciso.

Ordem, na homologação (executada pela TI dentro dos contêineres da stack; sem host, senha ou IP neste documento — as credenciais estão no `.env` da VM). Os comandos completos e a saída esperada de cada passo estão em `docs/DEPLOY.md` §4.1, ensaiado em 30/09/2026 com o código final, numa cópia do banco de desenvolvimento no estado v11 (982 materiais); os números abaixo são os do ensaio.

0. **Pré-verificação.** Portal atual responde `200` em `127.0.0.1`; banco com 982 documentos, 14 assuntos, 24 subcoleções, `portal_reader` presente (ainda lendo `users`: a seção 1 fecha isso). `visitas_downloads` e `supplementary_files` vazios.
1. **Código:** `git pull --ff-only origin main` (guardando antes o commit em uso). Vem antes de tudo: o script da migração e os alvos `backup`/`restore` novos do Makefile só existem no código novo; o portal no ar só muda no passo 4.
2. **Backups:** `make backup` (`backup_….dump` + `backup_…_arquivos.tgz`) e, para o método B de volta, `pg_dump -U php --clean --if-exists nourau > backup_clean_….sql`.
3. **Seção 1 do script.** Roda-se o arquivo inteiro; a parte da seção 2 só avisa enquanto o acervo antigo existir:
   ```bash
   docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres \
     psql -U php -d nourau -v ON_ERROR_STOP=1 < docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql
   ```
   Esperado na primeira passagem: `NOTICE: seção 1: configuração de busca portuguese_unaccent criada`, `INSERT`s e `UPDATE`s, `DROP INDEX`/`ALTER TABLE`/`CREATE INDEX` (coluna `busca` + índice GIN), `DO` (REVOKE de `users`), `NOTICE: seção 2: removido Jurisprudência/Enunciados (topic …)` e dois avisos da seção 2 ("ainda referenciado por N documento(s) … nada removido": Documentos Normativos com 7 e Vídeos com 3, no acervo v11). Depois: 16 assuntos, nenhuma subcategoria com o prefixo, `portuguese_unaccent` presente, índice `idx_nr_document_busca` presente, `portal_reader` sem leitura de `users`.
4. **Portal novo:** `docker compose --env-file .env -f docker/docker-compose.yml up -d --build portal` e `manage.py check --deploy --fail-level ERROR` (3 avisos de HTTPS, esperados em homologação HTTP). O `.env` precisa ter `DJANGO_SECRET_KEY`: sem ela o compose para.
5. **Planilha no contêiner:** `docker compose … cp <planilha> portal:/tmp/acervo.xlsx` e `sha256sum /tmp/acervo.xlsx` (depois do passo 4).
6. **Simulação:** `migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material" --skip-red --dry-run` — 1089 inseridas, 0 ignoradas, 0 recusadas. Toda recusa volta para a curadoria (tipo fora do vocabulário, grafia não coberta pelos aliases).
7. **Limpeza:** `TRUNCATE` + `setval` (seção "Troca completa do acervo", acima).
8. **Carga:** o comando do passo 6 sem `--dry-run` — 1089 inseridas, 0 recusadas.
9. **`make validate`:** 1089 documentos; 16 assuntos; "Tipos de informação em uso fora do vocabulário canônico v12: nenhum"; "Nenhum documento ativo com tipo retirado na v12 (Documentos Normativos/Vídeos/Pareceres/Enunciados sob Jurisprudência)"; sem o "AVISO v12"; 0 documentos sem categoria e 1 sem ano (pendência da curadoria); 402 achados de qualidade.
10. **Seção 2:** rode o mesmo script de novo. Agora as subcoleções e os tipos retirados saem (`NOTICE: seção 2: removido ...` para Documentos Normativos e Vídeos) e nenhum aviso aparece. Depois: 24 subcoleções e 95 tipos.
11. **Teste rápido** (*smoke test*) no portal (em `127.0.0.1`, na porta do portal; o `ALLOWED_HOSTS` do `.env` precisa aceitar `127.0.0.1`):
   - `/busca/` mostra 1089 documentos; página inicial e busca respondem rápido (a coluna `busca` indexada);
   - `/busca/?q=pregao` e `/busca/?q=pregão` devolvem a **mesma** contagem, e `licitacao` = `licitação` — busca sem acento;
   - `/busca/?typeinform_id=<id de Acórdãos>` lista os 3 acórdãos — o id vem de `SELECT id FROM type_information WHERE name = 'Acórdãos'`;
   - faceta Assunto com **16** opções; `/colecoes/` responde 301 para `/metodologia/`; as três abas da Metodologia respondem 200, sem Documentos Normativos, Vídeos, Pareceres nem o prefixo "FASE PREPARATÓRIA - ";
   - `/busca/?category_id=abc` dá 400 tratado; rota inexistente dá 404, sem a página de debug do Django; os dois aparecem no `docker compose … logs portal`.

Se algo sair diferente, pare. Para voltar ao estado do passo 1: `docs/DEPLOY.md` §4.2.

Em desenvolvimento, o mesmo roteiro vale contra a stack local (`localhost:8000`). Para validar o caminho de **volume novo** sem destruir o volume vivo, suba um Postgres descartável com senhas efêmeras montando `docker/postgres/init` em `/docker-entrypoint-initdb.d` e consulte `topic`, `type_information`, `nr_assunto`, `nr_subcategoria` e `pg_ts_config`.

## Notas
- O aviso `Colunas não encontradas: {'description'}` é a coluna "Nota" (removida no v8) — esperado.
- Scripts de init (`docker/postgres/init/*`) só rodam em **volume novo**; mudanças neles exigem o script de migração (v12) ou `UPDATE` manual num banco existente.
- **A taxonomia v9 (28/07/2026) mudou só a carga inicial do banco** (*seed*, os scripts de init). A v9 removeu do seed as 5 subcategorias de CONTEÚDOS TRANSVERSAIS. Uma base **antiga** que rode só a troca completa do acervo mantém as 5 subcategorias órfãs na árvore (aparecem zeradas na interface).
- **Vocabulário v12** (11/09/2026): Jurisprudência = Súmulas, Boletins, Acórdãos, Deliberações; Doutrina e Conteúdo Técnico ganha Enunciados; Instrução e Capacitação perde Vídeos. **v12.1 (23/09/2026):** Pareceres, que havia entrado em 11/09, sai do vocabulário (não é doutrina nem jurisprudência, conforme procurador consultado pela chefia); a seção 2 da migração remove a subcoleção e o tipo quando nenhum documento os referenciar. Normas, leis, decretos e portarias saem do acervo pela planilha (linhas em vermelho). Documentos ainda carregados com Documentos Normativos/Vídeos/Pareceres continuam exibidos na coleção antiga (`TIPOS_LEGADOS`) até a recarga.
- O tipo `Vídeos` (id 55) também é um dos 67 tipos padrão do Nou-Rau (`04-reset-nr.sql`); a seção 2 o remove junto com a subcoleção quando nada o referencia.
- Acervo em homologação até a recarga: **982 materiais** (planilha `BDLP_25_08_2026_982_materiais_v11.xlsx`, taxonomia v11). Planilha da recarga: **`BDLP_30_09_2026_1137_materiais_v12_final.xlsx`** (30/09/2026; 1137 linhas, **1089 ativas, 48 vermelhas**; sha256 `b31e41e17856b4d84a0a2f888f14ef51d1c470bd38c0066fdab257c8582a6f05`). A pós-auditoria de 23/09 (`BDLP_23_09_2026_1153_materiais_v12_pos-auditoria.xlsx`, 1104 ativas) trazia 16 linhas que a curadoria retirou do lote em 24/09; elas ficam para a carga seguinte.
- Dry-run de referência (30/09/2026, planilha da recarga, código final): **1089 inseridas, 0 ignoradas, 0 recusadas**, 0 linhas com alias de grafia e 402 avisos de qualidade. O importador informa "49 linhas vermelhas serão puladas": são as 48 linhas de material em vermelho mais a linha 2, de cabeçalho, que também tem fundo vermelho. Histórico: o dry-run de 14/09/2026 (PARA CORREÇÃO sem a revisão de 11/09: 972 aceitas, 10 recusadas) está em `docs/evidencias/2026-09-validacao/dry-run-para_correcao.txt`.
