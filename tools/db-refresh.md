# Refresh do acervo (carga e full-refresh)

O importador (`migrate_spreadsheet`) é **insert-only** com código sequencial `bdlp-XXXXXX` — re-rodar sem limpar gera duplicatas. Para refletir uma planilha FINAL no banco, faça um **full-refresh**.

Desde a taxonomia **v12** (set/2026) o importador é **estrito**: recusa a linha (e segue para a próxima) quando a Coleção não casa uma coleção raiz, quando o Tipo de informação está fora do vocabulário da coleção (Documentos Normativos e Vídeos inclusive) ou quando Categoria, Subcategoria, Microcategoria ou Assunto preenchidos não resolvem. Tipo novo não é criado por padrão (`--allow-new-types` só como exceção documentada). O `--dry-run` lista **todas** as linhas recusadas com motivo — é o insumo da curadoria antes da carga.

## Carga incremental / primeira carga
```bash
make backup                                   # sempre antes
make migrate-dry FILE=/caminho/acervo.xlsx    # deve sair com 0 recusas
make migrate     FILE=/caminho/acervo.xlsx
make validate
```
> A aba de dados é `"Inserir Material"`. O `make migrate` repassa só `$(FILE)`; se a planilha tiver outras abas ou linhas em vermelho, rode direto:
> `docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py migrate_spreadsheet <xlsx> --sheet "Inserir Material" --skip-red`

Flags úteis:
- `--skip-red` — pula linhas com fundo vermelho (a curadoria marca assim o que sai do acervo). A planilha "PARA CORREÇÃO" da v12 **exige** esta flag.
- `--dry-run` — só simula; lista todas as recusas com motivo e conta os aliases de grafia usados.
- `--allow-new-types` — cria em `type_information` um tipo fora do vocabulário em vez de recusar. **Exceção documentada**: não use em carga normal; se a planilha traz um tipo novo, a decisão é da chefia (vocabulário em `portal/catalog/taxonomy_v6.py`).
- `--start-seq N` — primeiro código `bdlp-XXXXXX` em cargas incrementais.

Aliases de grafia aceitos e normalizados (contados no resumo): categoria `PLANO ANUAL DE CONTRATAÇÕES (PCA)` → `PLANO DE CONTRATAÇÕES ANUAL (PCA)` (grafia das listas do template v8); subcategoria `FASE PREPARATÓRIA - X` → `X` (grafia da planilha PARA CORREÇÃO). Grafias legadas de tipo (`Acórdão`, `deliberacao`, `Parecer`, `Enunciado`) viram o nome canônico plural.

## Full-refresh (substituir todo o acervo)
Não exige `down -v` (nenhuma FK referencia `nr_document`). No container do Postgres:
```sql
TRUNCATE TABLE nr_document RESTART IDENTITY;
SELECT setval('nr_document_seq', 1, false);
```
Depois reimporte (`migrate_spreadsheet ... --sheet "Inserir Material" --skip-red`) e `make validate`.

Passos completos:
```bash
make backup
docker exec -i lilp-bdlp-postgres-1 psql -U php -d nourau \
  -c "TRUNCATE TABLE nr_document RESTART IDENTITY;" \
  -c "SELECT setval('nr_document_seq', 1, false);"
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal \
  python manage.py migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material" --skip-red
make validate
```

## Taxonomia v12 em banco existente — passo a passo (dev e homologação)

Os scripts de init (`docker/postgres/init/*`) só rodam em **volume novo**. Um banco que já existe (o volume de desenvolvimento e o de homologação) recebe a v12 pelo script idempotente `docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql`, que tem duas seções: a **seção 1** é aditiva (tipos e subcoleções novos, os 2 Assuntos, subcategorias sem prefixo, extensão `unaccent` e configuração `portuguese_unaccent`) e pode rodar a qualquer momento; a **seção 2** remove Documentos Normativos, Vídeos e o Enunciados antigo sob Jurisprudência **somente** se nenhum documento os referencia — senão só imprime `NOTICE: ... aviso`. O arquivo inteiro pode ser executado quantas vezes for preciso.

Ordem, na homologação (executada pela TI dentro dos contêineres da stack; sem host, senha ou IP neste documento — as credenciais estão no `.env` da VM):

1. **Backup**: `make backup` (ou `pg_dump -U php nourau` no contêiner do Postgres).
2. **Seção 1 do script** (é o arquivo inteiro; a seção 2 só avisa enquanto o acervo antigo existir):
   ```bash
   docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres \
     psql -U php -d nourau -v ON_ERROR_STOP=1 < docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql
   ```
   Esperado na primeira passagem: `NOTICE: seção 1: configuração de busca portuguese_unaccent criada`, `INSERT`s e `UPDATE`s, e dois avisos da seção 2 ("ainda referenciado por N documento(s); nada removido").
3. **Subida do código** v12 (branch/PR desta rodada) e rebuild do portal: `docker compose --env-file .env -f docker/docker-compose.yml up -d --build portal`.
4. **Full-refresh com a planilha v12** (`PARA CORREÇÃO` revisada + inserções novas), sempre com `--skip-red`. Antes, `--dry-run --skip-red`: deve sair com **0 recusas**; toda recusa volta para a curadoria (tipo fora do vocabulário, grafia não coberta pelos aliases).
5. **`make validate`**: 16 assuntos listados; seção "Tipos de informação em uso fora do vocabulário canônico v12" deve dizer `nenhum`; sem o "AVISO v12".
6. **Seção 2**: rode o mesmo script de novo. Agora as subcoleções e os tipos retirados saem (`NOTICE: seção 2: removido ...`).
7. **Smoke-test** no portal (sob o subcaminho de homologação):
   - `/busca/?q=pregao` e `/busca/?q=pregão` devolvem a **mesma** contagem (busca sem acento);
   - `/busca/?typeinform_id=<id de Acórdãos>` lista o(s) acórdão(s) — o id vem de `SELECT id FROM type_information WHERE name = 'Acórdãos'`;
   - faceta Assunto com **16** opções; subcategorias de Planejamento sem o prefixo "Fase Preparatória".

Em desenvolvimento, o mesmo roteiro vale contra a stack local (`localhost:8000`). Para validar o caminho de **volume novo** sem destruir o volume vivo, suba um Postgres descartável com senhas efêmeras montando `docker/postgres/init` em `/docker-entrypoint-initdb.d` e consulte `topic`, `type_information`, `nr_assunto`, `nr_subcategoria` e `pg_ts_config`.

## Notas
- O aviso `Colunas não encontradas: {'description'}` é a coluna "Nota" (removida no v8) — esperado.
- Scripts de init (`docker/postgres/init/*`) só rodam em **volume novo**; mudanças neles exigem o script de migração (v12) ou `UPDATE` manual num banco existente.
- **Taxonomia v9 (28/07/2026) foi seed-only.** A v9 removeu as 5 subcategorias de CONTEÚDOS TRANSVERSAIS do seed. Uma base **antiga** que rode só o full-refresh mantém as 5 subcategorias órfãs na árvore (aparecem zeradas no front).
- **Vocabulário v12** (11/09/2026): Jurisprudência = Súmulas, Boletins, Acórdãos, Deliberações; Doutrina e Conteúdo Técnico ganha Enunciados e Pareceres; Instrução e Capacitação perde Vídeos. Normas, leis, decretos e portarias saem do acervo pela planilha (linhas em vermelho). Documentos ainda carregados com Documentos Normativos/Vídeos continuam exibidos na coleção antiga (`TIPOS_LEGADOS`) até a recarga.
- O tipo `Vídeos` (id 55) também é um dos 67 tipos padrão do Nou-Rau (`04-reset-nr.sql`); a seção 2 o remove junto com a subcoleção quando nada o referencia.
- Acervo carregado (dev e homologação): **982 materiais** (planilha `BDLP_25_08_2026_982_materiais_v11.xlsx`, taxonomia v11); a **v12** está em consolidação pela curadoria (planilha PARA CORREÇÃO + inserções de agosto/setembro).
- Dry-run de referência (14/09/2026, planilha PARA CORREÇÃO ainda sem a revisão de 11/09): 972 aceitas, 10 recusadas — 7 Documentos Normativos e 3 Vídeos — e 55 linhas normalizadas pelo alias de subcategoria. Saída em `docs/evidencias/2026-09-validacao/dry-run-para_correcao.txt`.
