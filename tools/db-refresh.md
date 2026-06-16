# Refresh do acervo (carga e full-refresh)

O importador (`migrate_spreadsheet`) é **insert-only** com código sequencial `bdlp-XXXXXX` — re-rodar sem limpar gera duplicatas. Para refletir uma planilha FINAL no banco, faça um **full-refresh**.

## Carga incremental / primeira carga
```bash
make backup                                   # sempre antes
make migrate-dry FILE=/caminho/acervo.xlsx    # deve sair com 0 erros
make migrate     FILE=/caminho/acervo.xlsx
make validate
```
> A aba de dados v8 é `"Inserir Material"`. O `make migrate` repassa só `$(FILE)`; se a planilha tiver outras abas, rode direto:
> `docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py migrate_spreadsheet <xlsx> --sheet "Inserir Material"`

## Full-refresh (substituir todo o acervo)
Não exige `down -v` (nenhuma FK referencia `nr_document`). No container do Postgres:
```sql
TRUNCATE TABLE nr_document RESTART IDENTITY;
SELECT setval('nr_document_seq', 1, false);
```
Depois reimporte (`migrate_spreadsheet ... --sheet "Inserir Material"`) e `make validate`.

Passos completos:
```bash
make backup
docker exec -i lilp-bdlp-postgres-1 psql -U php -d nourau \
  -c "TRUNCATE TABLE nr_document RESTART IDENTITY;" \
  -c "SELECT setval('nr_document_seq', 1, false);"
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal \
  python manage.py migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material"
make validate
```

## Notas
- O aviso `Colunas não encontradas: {'description'}` é a coluna "Nota" (removida no v8) — esperado.
- Scripts de init (`docker/postgres/init/*`) só rodam em **volume novo**; mudanças neles (ex.: rename de categoria) exigem `UPDATE` manual num banco existente.
- Acervo canônico atual: **406 docs** (v8 FINAL). Distribuição esperada por coleção: Doutrina 217 · Trabalhos Acadêmicos 152 · Instrução 31 · Jurisprudência 6.
