# Roteiro de Demo — Biblioteca Digital de Logística Pública (BDLP)

**Apresentação para o Subsecretário — MVP Local**

## Pré-requisitos
- Docker Desktop instalado e rodando
- Planilha `BDLP_507_v9_FINAL.xlsx` em mãos (master do acervo — raiz da pasta da frente)
- Arquivo `.env` na raiz do repositório (já configurado)

## Passo 1 — Subir o ambiente do zero (~2 min)

```bash
make clean
make up
```

Aguarde até os três containers estarem saudáveis (postgres, nourau, portal).

## Passo 2 — Verificar que os serviços estão no ar

```bash
curl -I http://localhost:8000   # Portal Django → 200
curl -I http://localhost:8080   # Nou-Rau → 302 (redireciona ao login)
```

## Passo 3 — Carregar o acervo (507 documentos, ~30s)

```bash
docker compose --env-file .env -f docker/docker-compose.yml cp "BDLP_507_v9_FINAL.xlsx" portal:/tmp/planilha.xlsx
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py migrate_spreadsheet /tmp/planilha.xlsx --sheet "Inserir Material"
```

Resultado esperado: 507 inseridos, 0 erros. (O `make migrate` não repassa `--sheet`; a aba de dados da planilha vigente é `"Inserir Material"` — ver `tools/db-refresh.md`.)

## Passo 4 — Validar a importação

```bash
make validate
```

Deve mostrar: 507 documentos arquivados; por coleção: Doutrina e Conteúdo Técnico 294 · Trabalhos Acadêmicos 153 · Instrução e Capacitação 49 · Jurisprudência 11.

## Passo 5 — Abrir o Portal (http://localhost:8000)

1. **Homepage**: mostrar as 4 coleções com contagens (Doutrina e Conteúdo Técnico: 294, Trabalhos Acadêmicos: 153, Instrução e Capacitação: 49, Jurisprudência: 11) e total de 507 documentos.
2. **Busca por "licitação"**: digitar no campo de busca → deve retornar mais de 200 resultados.
3. **Busca por "14.133"**: resultados sobre a nova Lei de Licitações.
4. **Clicar em um resultado**: página de detalhe com título, autor, resumo, palavras-chave, link de acesso, coleção.

## Passo 6 — Navegar pelas coleções

1. Clicar em **Coleções** no menu → `/colecoes/` mostra as 4 coleções raiz.
2. Entrar em **Trabalhos Acadêmicos** (153 docs) → confirmar paginação.
3. Entrar em **Instrução e Capacitação** (49 docs).

## Passo 7 — Demonstrar o Nou-Rau (http://localhost:8080/manager)

1. Login: usuário `admin`, senha `admin` (seed de demonstração — **trocar no deploy**; nunca manter em homologação/produção, ver `docs/DEPLOY.md`).
2. Mostrar a lista de documentos catalogados (507 registros).
3. Abrir um documento para mostrar os metadados.

## Passo 8 — Busca temática para encerrar

No portal, fazer uma busca por **"dissertação"** na coleção Trabalhos Acadêmicos → ~26 resultados com dissertações de mestrado sobre logística pública.

Alternativamente, buscar **"compras sustentáveis"** para mostrar a relevância do acervo para políticas públicas.

## Passo 9 — Página "Sobre" (http://localhost:8000/sobre/)

Mostrar a página institucional sobre o LILP e a parceria SGGD/Unicamp.

---

## Contingência — Se algo der errado

### O ambiente não sobe
```bash
make clean
docker compose --env-file .env -f docker/docker-compose.yml up --build -d
```

### A migração falha
Restaurar do backup:
```bash
cat backup_demo_20260413.sql | docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php nourau
```

### A busca retorna vazio
Recriar o índice full-text:
```bash
docker compose --env-file .env -f docker/docker-compose.yml exec postgres psql -U php -d nourau -c "REINDEX INDEX idx_nr_document_fts;"
```

### Esqueceu a senha do Nou-Rau
Login: `admin` / Senha: `admin` (seed local de demo — em homologação/produção a credencial deve estar rotacionada, ver `docs/DEPLOY.md`)

---

## Comando único para subir tudo do zero

```bash
make clean && make up && sleep 10 && \
docker compose --env-file .env -f docker/docker-compose.yml cp "BDLP_507_v9_FINAL.xlsx" portal:/tmp/planilha.xlsx && \
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py migrate_spreadsheet /tmp/planilha.xlsx --sheet "Inserir Material" && \
make validate
```

Tempo estimado: ~3 minutos do zero até dados carregados.
