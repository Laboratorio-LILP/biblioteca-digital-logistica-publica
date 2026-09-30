# Deploy e operação — BDLP

Runbook da esteira **dev (local) → homologação (VM) → produção (Prodesp)**. Vale como referência para os demais sistemas do LILP.

## 1. Matriz de configuração por estágio

A `.env` (raiz) é a fonte única (o Makefile usa `--env-file .env`). Diferenças por estágio:

| Variável | dev (local) | homologação (VM, HTTP) | produção (TLS) |
|---|---|---|---|
| `DJANGO_DEBUG` | `true` (explícito) | **`false`** (ou ausente) | **`false`** (ou ausente) |
| `SECURE_SSL` | `false` | `false` (só :80) | **`true`** (HTTPS) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | IP + host público da VM + `127.0.0.1` (testes na VM, §2 e §4.1) | domínio Prodesp |
| `CSRF_TRUSTED_ORIGINS` | — | `http(s)://<host-VM>` | `https://<domínio>` |
| `FORCE_SCRIPT_NAME` | (vazio) | `/Biblioteca` | conforme a borda |
| `DJANGO_SECRET_KEY` | obrigatória (qualquer) | **obrigatória, própria** | **obrigatória, própria** |

Desde 30/09/2026 não existe chave padrão: o compose não sobe sem `DJANGO_SECRET_KEY` no `.env` (mesmo tratamento das senhas do banco) e, fora do modo de desenvolvimento, o portal recusa subir sem ela. `DJANGO_DEBUG` ausente vale `false`.

A **borda** é o servidor web que recebe o acesso de fora e o repassa ao portal: em homologação, o `index.php` de `deploy/edge/`; em produção, a definir com a Prodesp.

> **`DEBUG` e `SECURE_SSL` são desacoplados** de propósito: homologação roda `DEBUG=false` em HTTP puro sem quebrar o login (as flags que exigem HTTPS — cookies Secure, redirect, HSTS — ficam só sob `SECURE_SSL`).

Gerar a `DJANGO_SECRET_KEY` (qualquer texto aleatório com 50 ou mais caracteres serve; grave na linha `DJANGO_SECRET_KEY=` do `.env`, sem aspas e sem espaços). Na VM não há Django fora do contêiner; use o Python do sistema ou o `openssl`:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(60))"
# ou: openssl rand -base64 60 | tr -d '\n='
```
(Com Django à mão: `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`.)

## 2. Promoção para homologação (VM) — por solicitação à TI

Desde 30/06/2026 (ADR-006 da vault do LILP), quem desenvolve não acessa a VM. A equipe de TI (Felipe/Diego) faz a subida quando recebe uma solicitação. Este documento não traz endereço, nome de máquina nem senha: os comandos rodam na VM, na pasta do clone, e leem as credenciais do `.env` de lá.

A solicitação leva:

1. o commit de `main` a implantar (hash completo). Antes de pedir, quem desenvolve envia `main` ao GitHub (`git push`): o `git pull` da VM só traz o que já está lá;
2. a planilha do acervo, quando a subida também troca o acervo (§4.1);
3. a seção deste arquivo que vale para a subida.

Subida só de código (sem trocar o acervo):

```bash
git pull --ff-only origin main
git rev-parse HEAD        # igual ao hash da solicitação
docker compose --env-file .env -f docker/docker-compose.yml up -d --build
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py check --deploy --fail-level ERROR
# Teste rápido, na própria VM:
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/Biblioteca/      # 200, se a rota da borda estiver aberta
curl -s http://127.0.0.1:8010/__nao_existe__/ | grep -c "Using the URLconf" # 0 (DEBUG desligado)
```

O `check --deploy` termina sem erro e mostra 3 avisos (`security.W004`, `security.W008`, `security.W016`). Eles tratam de HTTPS e são esperados em homologação, que roda em HTTP. Um aviso a mais segue a regra do §4.1 (pré-requisitos): `security.W009` é motivo para parar. Se o `up` parar com `defina DJANGO_SECRET_KEY no .env`, o `.env` da VM não tem a chave: gere uma (§1) e grave antes de seguir.

Os testes chamam o portal direto em `127.0.0.1`. A borda (`deploy/edge/index.php`, função `proxyToDjango`) também fala com o portal em `http://127.0.0.1:<porta>`, mas repassa o nome público no cabeçalho `X-Forwarded-Host`, e é esse nome que o portal confere para quem vem de fora. Por isso o `ALLOWED_HOSTS` do `.env` da VM precisa ter os dois: o host público (para a borda) e `127.0.0.1` (para estes testes diretos). Se aparecer `400`, o problema é o `ALLOWED_HOSTS`: pare e devolva a saída. A linha de `/Biblioteca/` passa pela borda e não fez parte do ensaio; ela só dá `200` se a rota da borda estiver aberta (a Biblioteca está fora do ar desde 08/09; ver §4.1).

Quando a subida também troca o acervo, siga o §4.1 inteiro, e não este bloco. Se algo falhar ou estiver inacessível, a TI para, registra e devolve a saída. Ninguém contorna: sem túnel, sem acesso direto.

## 3. Produção (Caddy + TLS)

```bash
# .env com DOMAIN, DJANGO_DEBUG=false, SECURE_SSL=true, ALLOWED_HOSTS=<domínio>
docker compose --env-file .env -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d --build
```
A borda de produção **depende do ambiente** (ver [adr/0006-borda-canonica.md](adr/0006-borda-canonica.md)): na Prodesp será definida com eles. O `Caddyfile`/`prod.yml` aqui é uma **referência opcional** para um host próprio exposto à internet (HTTPS automático), não um requisito. Em domínio único, cada sistema é um sub-path (`handle_path /Biblioteca/*`) com `FORCE_SCRIPT_NAME` coerente. A homologação usa o `index.php` da VM interna (ver `deploy/edge/`). O que a produção vai exigir além disto está no §6.

## 4. Dados / acervo

O roteiro de carga e de troca completa do acervo está em [../tools/db-refresh.md](../tools/db-refresh.md). Em homologação, vale o §4.1 abaixo. Sempre faça backup antes (§4.1, passo 2).

A carga usa o comando direto, com a aba de dados e `--skip-red` (a curadoria pinta de vermelho o que sai do acervo). Primeiro a simulação, depois a carga:

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material" --skip-red --dry-run
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material" --skip-red
```

A planilha precisa estar dentro do contêiner do portal (§4.1, passo 5). A simulação deve terminar com **0 recusas**. O importador só acrescenta: para trocar todo o acervo, a limpeza do §4.1, passo 7, vem antes da carga. `make validate` confere o resultado.

**Não use `make migrate` nem `make migrate-dry` com as planilhas da curadoria.** Os dois repassam só o arquivo, sem `--sheet` e sem `--skip-red`. O comando para com `CommandError: Nenhuma aba de dados encontrada` e não carrega nada (conferido em 23/09/2026 com a planilha da recarga).

### 4.1 Taxonomia v12.1 e troca do acervo (set/2026) — roteiro para a TI, em homologação

**O que esta subida faz.** Instala o código de `main` informado na solicitação (taxonomia v12.1, busca sem acento e indexada, página Metodologia, erros tratados e registrados em log, chave secreta obrigatória), atualiza a classificação do banco para a v12.1 e troca o acervo antigo (982 materiais, taxonomia v11) pelo novo (1089 materiais).

**Planilha:** `BDLP_30_09_2026_1137_materiais_v12_final.xlsx`, enviada com a solicitação. sha256 `b31e41e17856b4d84a0a2f888f14ef51d1c470bd38c0066fdab257c8582a6f05`. Tem 1137 linhas de material: 1089 entram; 48, pintadas de vermelho, ficam de fora (41 marcadas pela curadoria; 7 duplicatas marcadas na consolidação).

**Situação da homologação.** A Biblioteca está fora do ar desde 08/09/2026: a Lina pediu à TI que a retirasse, por determinação do subsecretário (Teams, grupo do Laboratório, 08/09, 15h48). Esta subida a recoloca no ar para a homologação; a Lina autorizou a subida em 23/09 (10h21). A última linha do passo 11 passa pela borda e só dá `200` se a rota `/Biblioteca/` da borda estiver reaberta.

**Antes de começar, confira (pré-requisitos).**

- O `make` está instalado na VM (os passos 2 e 9 usam `make backup` e `make validate`; o caminho de volta usa `make restore`). Se não estiver, instale o pacote `make` da distribuição antes de começar; sem ele, não comece.
- Docker Compose v2 (`docker compose version` responde; o `docker compose cp` do passo 5 é do v2).
- A VM alcança o GitHub com a credencial de leitura já configurada no clone (é o que o `git pull` usa; nenhum comando pede senha — se o `pull` pedir, pare) e os registros públicos que o `--build` usa (imagem `python:3.12-slim`, pacotes Debian e PyPI). É o mesmo caminho das atualizações de 17 e 27/08 feitas pela TI (relato); se a saída de rede tiver mudado, pare e avise antes de começar — nenhum passo deste roteiro mexe em firewall ou proxy.
- O `.env` da VM tem `DJANGO_SECRET_KEY` própria (não a de outro ambiente) e `DJANGO_DEBUG=false`. Sem a chave, o passo 4 para na hora com `defina DJANGO_SECRET_KEY no .env`.
- O `ALLOWED_HOSTS` do `.env` da VM aceita `127.0.0.1`. Os testes dos passos 0 e 11 chamam o portal direto nesse endereço (a borda não precisa disso: ela envia o nome público em `X-Forwarded-Host`). O passo 0 confere antes de qualquer mudança no banco.
- A planilha chegou pelo canal institucional (e-mail corporativo ou site de equipe) e foi copiada para a pasta do clone, com o nome exato acima. O `cp` do passo 5 usa esse caminho relativo.
- A TI sabe como a Biblioteca foi retirada do ar em 08/09 (parada dos contêineres, bloqueio na borda ou outro) e como reabrir: o roteiro não reabre nada; o passo 12 diz quando. Se a stack estiver parada, o passo 0 diz o que fazer.
- Ninguém vai usar o Nou-Rau (`/manager`) entre os passos 3 e 10. Nesse intervalo o acervo é apagado e carregado de novo, e o que for cadastrado no meio se perde ou entra em conflito com a carga.
- O `check --deploy` (passo 4) foi ensaiado com o `.env` de desenvolvimento. Com o `.env` da VM, ele pode mostrar um aviso a mais. Se o aviso for `security.W009` (chave secreta fraca ou padrão), pare: a chave própria é condição de segurança (§5). Outro aviso a mais: devolva a saída e aguarde a resposta antes de seguir.

**Como foi ensaiado.** Em 30/09/2026, numa stack descartável: banco restaurado de uma cópia do banco de desenvolvimento no estado v11 (982 materiais, 14 assuntos, sem `unaccent`), e não do banco de homologação; o portal antigo (commit `de60e8d`) no ar no passo 0; o portal novo construído de verdade no passo 4, do commit da solicitação. Cada comando abaixo foi copiado deste arquivo e executado na ordem; as saídas esperadas são as do ensaio. Depois, os dois métodos do §4.2 foram executados sobre o banco carregado e, após cada um, os passos 3 a 11 foram repetidos com o mesmo resultado. O ensaio simulou ou deixou de fora:

- O `git pull` (passo 1) foi simulado: a stack já nasceu do commit da solicitação; as outras linhas do passo rodaram.
- Os comandos `docker compose` rodaram contra a cópia local, com o `.env` de desenvolvimento, sem `FORCE_SCRIPT_NAME=/Biblioteca`.
- A borda `index.php`, o subcaminho `/Biblioteca/` e o Nou-Rau em uso não foram testados; o volume de arquivos da curadoria estava vazio.
- Na VM, o `--build` baixa a imagem base do portal (`python:3.12-slim`) e os pacotes do sistema e do Python. A VM precisa de rede para esses registros públicos (ou de um espelho). O tempo do build sem cache não foi medido.

**Regras.**

- Rode tudo na VM, na pasta do clone, com o `.env` de lá. Nenhum comando pede senha.
- Quem decide voltar atrás (§4.2) é o Bernardo, a partir da saída devolvida; a TI não volta atrás por conta própria, a não ser que ele peça.
- Siga a ordem. Cada passo diz o que deve aparecer.
- Se aparecer outra coisa, pare e devolva a saída ao Bernardo. Não improvise.
- Os backups (`backup_*.dump`, `backup_*.sql`, `backup_*_arquivos.tgz`) contêm a tabela de usuários do Nou-Rau. Não os envie a ninguém: devolva só nome, tamanho e sha256.

**Passo 0 — Conferir o portal atual e o banco.** Primeiro, confira que o portal atual responde direto em `127.0.0.1` (porta `PORTAL_PORT` do `.env`; 8010 pelo ADR-0008). Esperado: `200`. Se der `000` (conexão recusada), a stack está parada: suba-a com `docker compose --env-file .env -f docker/docker-compose.yml up -d` (ainda com o código atual, sem `--build`) e repita. Se der `400`, o `ALLOWED_HOSTS` do `.env` não aceita `127.0.0.1`. Se você acabou de editar o `.env` para esta subida (chave, `DEBUG`, `ALLOWED_HOSTS`), o contêiner em execução ainda não sabe: rode `docker compose --env-file .env -f docker/docker-compose.yml up -d portal` (recria o contêiner com o `.env` novo, mesmo código) e repita. Continuando `400`, pare e devolva, antes de mexer no banco.

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8010/
```

Depois, confira o banco:

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau \
  -c "SELECT rolname FROM pg_roles WHERE rolname='portal_reader';" \
  -c "SELECT count(*) AS docs FROM nr_document;" \
  -c "SELECT count(*) AS assuntos FROM nr_assunto;" \
  -c "SELECT count(*) AS subcolecoes FROM topic WHERE parent_id<>0;" \
  -c "SELECT extname FROM pg_extension WHERE extname='unaccent';" \
  -c "SELECT cfgname FROM pg_ts_config WHERE cfgname='portuguese_unaccent';" \
  -c "SELECT has_table_privilege('portal_reader','public.users','SELECT') AS portal_reader_le_users;" \
  -c "SELECT (SELECT count(*) FROM visitas_downloads) AS visitas, (SELECT count(*) FROM supplementary_files) AS suplementares;"
```

Esperado (ensaio): `portal_reader` presente; `docs` 982; `assuntos` 14; `subcolecoes` 24; `unaccent` e `portuguese_unaccent` sem linhas (`0 rows`); `portal_reader_le_users` = `t` ou `f` (no ensaio deu `f`, porque a cópia já tinha o REVOKE; na VM pode ser `t` — o passo 3 fecha isso); `visitas` 0 e `suplementares` 0.

- `assuntos` = 16, ou `unaccent`/`portuguese_unaccent` presentes: a seção 1 já rodou antes. Siga; ela pode rodar de novo.
- `docs` diferente de 982 ou `subcolecoes` diferente de 24: o banco da VM não está no estado que o ensaio usou (cópia do desenvolvimento em v11, que é o estado registrado da homologação desde 27/08). Pare e devolva a saída; o Bernardo decide se o roteiro vale como está.
- `visitas` ou `suplementares` maior que 0: pare e avise. A troca do acervo renumera os códigos `bdlp-NNNNNN`, e esses registros passariam a apontar para outros materiais.
- `portal_reader` ausente: rode `docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres bash -s < docker/postgres/init/09-portal-readonly-user.sh` (o arquivo existe no código atual e no novo; a senha vem de `PORTAL_DB_PASSWORD`, que o compose já passa ao contêiner do Postgres) e siga; a seção 1 do passo 3 fecha a leitura de `users`.

**Passo 1 — Atualizar o código.** Vem antes de tudo: o script da migração e os alvos novos do Makefile (`backup`, `restore`) só existem no código novo. O portal no ar só muda no passo 4.

Antes do `pull`, guarde o commit em uso (é o caminho de volta do código, §4.2) e confira o clone:

```bash
git branch --show-current
git status --short --untracked-files=no
[ -e commit_anterior.txt ] || git rev-parse HEAD > commit_anterior.txt   # não sobrescreve se o passo for repetido
cat commit_anterior.txt
```

Esperado: `main`; nenhuma linha no `git status` (nenhum arquivo do repositório foi mudado na VM; arquivos novos, como a planilha e os backups, não entram nesta conferência — no ensaio apareceram os documentos ainda não commitados da própria sessão, o que na VM não acontece); e o hash em uso hoje. Se a branch não for `main` ou se o `git status` listar algum arquivo, pare e devolva a saída. Caso típico: `deploy/edge/index.php` ou `.htaccess` modificados, se a borda foi editada na VM para tirar o site do ar — o Bernardo decide como reconciliar antes do `pull`; não descarte a alteração.

Depois, atualize e confira que o código é o da solicitação:

```bash
git pull --ff-only origin main
git rev-parse HEAD
sha256sum docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql
grep -c '^restore:' Makefile
```

Esperado: o hash da solicitação; para o script, `0026934a8932750328546a280a73d7b60af47c856ad429ad8ba387be74030550`; e `1` (o Makefile novo, com o `restore` que funciona).

- Se o `git pull --ff-only` falhar (sem rede, sem credencial de leitura no GitHub ou com histórico divergente), pare e devolva a saída. Não troque por outro tipo de `pull`.
- Se o hash ou o sha256 forem outros, o código não é o ensaiado: pare e devolva a saída.

**Passo 2 — Fazer os backups.** O `make backup` gera dois arquivos (banco em formato custom e arquivos da curadoria); o terceiro comando gera o backup em texto do método B (§4.2).

```bash
make backup
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres pg_dump -U php --clean --if-exists nourau > backup_clean_$(date +%Y%m%d_%H%M%S).sql
ls -l backup_*; sha256sum backup_*
grep -c 'PostgreSQL database dump complete' backup_clean_*.sql
```

Esperado: `Banco: backup_….dump (… bytes)`, `Arquivos: backup_…_arquivos.tgz (… bytes)` e a frase "Guarde os dois juntos"; os três arquivos novos na listagem (a listagem também mostra backups de subidas anteriores, se houver; no ensaio, o `.dump` com 426.376 bytes, o `.tgz` com 104 bytes — volume de arquivos vazio — e o `_clean_….sql` com 1.363.883; na VM os tamanhos do banco serão parecidos, não iguais; o `.tgz` será maior se o volume tiver arquivos da curadoria); `dump complete` = 1 por arquivo `_clean_`.

- Se o `make backup` terminar com `ERRO`, pare: nenhum arquivo parcial fica (o alvo apaga o `.part`).
- Os três ficam na pasta do clone e não entram no `git` (`.gitignore`).

**Passo 3 — Rodar a seção 1 da migração.** O script tem duas seções e roda sempre inteiro. Nesta hora, a seção 1 acrescenta a classificação nova, a coluna de busca indexada e fecha a leitura de `users`; a seção 2 só remove o que nenhum documento usa (no ensaio, a subcoleção Enunciados vazia sob Jurisprudência) e avisa sobre o resto — ela age de verdade no passo 10.

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -v ON_ERROR_STOP=1 < docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -c "SELECT count(*) AS assuntos FROM nr_assunto;" -c "SELECT nome FROM nr_subcategoria WHERE nome LIKE 'FASE PREPARAT%';" -c "SELECT cfgname FROM pg_ts_config WHERE cfgname='portuguese_unaccent';" -c "SELECT indexname FROM pg_indexes WHERE indexname='idx_nr_document_busca';" -c "SELECT has_table_privilege('portal_reader','public.users','SELECT') AS portal_reader_le_users;"
```

Esperado no primeiro comando (ensaio), nesta ordem:

```
CREATE EXTENSION
NOTICE:  seção 1: configuração de busca portuguese_unaccent criada
DO
INSERT 0 2
INSERT 0 1
INSERT 0 3
UPDATE 0
INSERT 0 6
INSERT 0 2
INSERT 0 8
INSERT 0 2
UPDATE 1            (7 vezes)
DROP INDEX
ALTER TABLE
CREATE INDEX
DO
NOTICE:  seção 2: removido Jurisprudência/Enunciados (topic 5)
NOTICE:  seção 2 — aviso: Jurisprudência/Documentos Normativos ainda referenciado por 7 documento(s) e 0 arquivo(s) suplementar(es); nada removido (recarregue o acervo v12 antes)
NOTICE:  seção 2 — aviso: Instrução e Capacitação/Vídeos ainda referenciado por 3 documento(s) e 0 arquivo(s) suplementar(es); nada removido (recarregue o acervo v12 antes)
DO
```

- `INSERT 0 6` é o número de usuários do Nou-Rau (2 no ensaio) vezes o número de subcoleções ainda sem nenhum usuário vinculado (3 no ensaio, as novas). Na VM pode ser outro número; não é erro. O número do `topic` também pode mudar.
- `DROP INDEX`, `ALTER TABLE` e `CREATE INDEX` são a busca indexada (seção 1.10); o `DO` seguinte é o `REVOKE` de `users` (seção 1.11). Se a VM não tiver o índice antigo, no lugar de `DROP INDEX` aparece `NOTICE: index "idx_nr_document_fts" does not exist, skipping` — não é erro.
- A linha `removido Jurisprudência/Enunciados` só aparece se a VM tiver essa subcoleção vazia (a cópia do ensaio tinha); sem ela, a linha não aparece e não é erro.
- Os dois avisos não são erro. A seção 2 roda junto e só remove Documentos Normativos e Vídeos depois da troca do acervo (passo 10).

No segundo comando: `assuntos` = 16; nenhuma subcategoria começando com `FASE PREPARAT`; uma linha `portuguese_unaccent`; uma linha `idx_nr_document_busca`; `portal_reader_le_users` = `f`. O arquivo pode rodar de novo: na segunda vez aparecem só `INSERT 0 0`, `UPDATE 0`, os avisos `already exists, skipping` (extensão, coluna e índice) e os mesmos dois avisos da seção 2.

**Passo 4 — Subir o portal novo.** Só o portal: o Postgres é a mesma imagem (`postgres:15-alpine`) e o Nou-Rau não mudou nesta versão (nenhum arquivo em `docker/nourau/` alterado desde o commit em uso na VM).

```bash
docker compose --env-file .env -f docker/docker-compose.yml up -d --build portal
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py check --deploy --fail-level ERROR
```

Esperado: `System check identified 3 issues (0 silenced).`, com os avisos `security.W004`, `security.W008` e `security.W016` (HTTPS; esperados em homologação HTTP). Qualquer `ERROR`: pare. Aviso a mais: siga a regra dos pré-requisitos (`security.W009`: pare). Se o `up` parar com `defina DJANGO_SECRET_KEY no .env`, o `.env` não tem a chave (pré-requisitos).

**Passo 5 — Copiar a planilha para dentro do contêiner do portal.** Faça depois do passo 4: se o contêiner for recriado, o arquivo some.

```bash
docker compose --env-file .env -f docker/docker-compose.yml cp BDLP_30_09_2026_1137_materiais_v12_final.xlsx portal:/tmp/acervo.xlsx
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal sha256sum /tmp/acervo.xlsx
```

Esperado: `b31e41e17856b4d84a0a2f888f14ef51d1c470bd38c0066fdab257c8582a6f05  /tmp/acervo.xlsx`. Outro valor: o arquivo não é o enviado; pare.

**Passo 6 — Simular a carga.**

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material" --skip-red --dry-run > dryrun_$(date +%Y%m%d).txt 2>&1
grep -E "vermelhas serão|Registros com dados|Inseridos:|recusados|alias de grafia|achados em|DRY RUN" dryrun_$(date +%Y%m%d).txt
```

Esperado (ensaio):

```
  [Inserir Material] 49 linhas vermelhas serão puladas
  Registros com dados: 1089 (+ 49 vermelhos pulados)
  [Inserir Material] Inseridos: 1089, Ignorados: 0, Erros: 0
  Total recusados (erros de linha): 0
  Linhas que usaram alias de grafia: categoria 0, subcategoria 0
Possíveis redundâncias e problemas de qualidade — AVISOS para a curadoria, não impedem a carga (402 achados em 1089 linhas; …):
[DRY RUN] Nenhum dado foi inserido.
```

- "49 linhas vermelhas" são as 48 linhas de material mais a linha 2, de cabeçalho, que também tem fundo vermelho. Não falta material.
- Os 402 avisos são para a curadoria e não impedem a carga. A linha `Colunas não encontradas: {'description'}` também é esperada.
- `Erros` maior que 0: pare e devolva o arquivo `dryrun_…txt`.

**Passo 7 — Limpar o acervo antigo.** O importador só acrescenta. Sem esta limpeza, os códigos novos batem nos antigos e o importador recusa as linhas.

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE nr_document RESTART IDENTITY;" -c "SELECT setval('nr_document_seq', 1, false);" -c "SELECT count(*) FROM nr_document;"
```

Esperado: `TRUNCATE TABLE`, `setval` = 1 e `count` = 0. Nenhuma outra tabela depende de `nr_document` (conferido no ensaio). O volume de arquivos da curadoria (`nourau_data`) não é tocado: os 982 materiais atuais são referências a endereços externos (`supplementary_files` = 0 no passo 0), e o backup do passo 2 guarda o volume de qualquer forma. A sequência `nr_document_seq` é o contador do banco que dá o número do próximo material; o `setval` o põe de volta em 1. Ele é necessário porque o `RESTART IDENTITY` não zera essa sequência.

**Passo 8 — Carregar.**

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py migrate_spreadsheet /tmp/acervo.xlsx --sheet "Inserir Material" --skip-red > carga_$(date +%Y%m%d).txt 2>&1
grep -E "Inseridos:|recusados" carga_$(date +%Y%m%d).txt
```

Esperado: `[Inserir Material] Inseridos: 1089, Ignorados: 0, Erros: 0` e `Total recusados (erros de linha): 0`. A carga não repete os 402 avisos.

**Passo 9 — Validar.**

```bash
make validate > validate_$(date +%Y%m%d).txt 2>&1
grep -E "Documentos totais|Assuntos:|duplicados|nenhum$|tipo retirado|sem categoria|sem ano|achados em|AVISO v12" validate_$(date +%Y%m%d).txt
```

Esperado (ensaio):

```
  Documentos totais: 1089
  Assuntos: 16
  Sem códigos duplicados.
    nenhum
  Nenhum documento ativo com tipo retirado na v12 (Documentos Normativos/Vídeos/Pareceres/Enunciados sob Jurisprudência).
  Documentos sem ano: 1
  Possíveis redundâncias e problemas de qualidade (402 achados em 1089 documentos; …):
```

- No arquivo, "Documentos por coleção" deve mostrar: Jurisprudência 69, Trabalhos Acadêmicos 293, Doutrina e Conteúdo Técnico 617, Instrução e Capacitação 110.
- Nenhuma linha com `AVISO v12`. "nenhum" é a resposta para "Tipos de informação em uso fora do vocabulário canônico v12".
- Não aparece linha "Documentos sem categoria": o comando só a imprime quando há algum, e nesta planilha não há. "Documentos sem ano: 1" é pendência da curadoria (linha 1071 da planilha), não erro.
- Nesta hora o arquivo ainda mostra "Subcoleções: 26" e "Tipos de informação: 97". Depois do passo 10 o banco fica com 24 e 95.

**Passo 10 — Rodar a seção 2 (o mesmo arquivo do passo 3).**

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -v ON_ERROR_STOP=1 < docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -c "SELECT id, name FROM type_information WHERE name IN ('Documentos Normativos','Vídeos','Pareceres');" -c "SELECT count(*) AS subcolecoes FROM topic WHERE parent_id<>0;"
```

Esperado no primeiro comando (ensaio): `NOTICE:  extension "unaccent" already exists, skipping`, `INSERT 0 0` (7 vezes), `UPDATE 0` (8 vezes), os avisos `index "idx_nr_document_fts" does not exist, skipping`, `column "busca" of relation "nr_document" already exists, skipping` e `relation "idx_nr_document_busca" already exists, skipping`, `DO`, `NOTICE:  seção 2: removido Jurisprudência/Documentos Normativos (topic 8)` e `NOTICE:  seção 2: removido Instrução e Capacitação/Vídeos (topic 27)`. Nenhum aviso da seção 2. No segundo: a consulta de tipos volta sem linhas (`0 rows`; Pareceres só existiria se a v12 de 11/09 tivesse sido aplicada na VM, o que não ocorreu) e `subcolecoes` = 24.

**Passo 11 — Testar o portal.** Na VM, o portal responde em `127.0.0.1`, na porta do `.env` (variável `PORTAL_PORT`; 8010 pelo ADR-0008). Troque `<id>` pelo número que o primeiro comando mostrar. O `ALLOWED_HOSTS` do `.env` da VM precisa aceitar `127.0.0.1` para estes testes diretos (o passo 0 já conferiu).

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -tA -c "SELECT id FROM type_information WHERE name = 'Acórdãos';"
P=http://127.0.0.1:8010
curl -s -o /dev/null -w "%{http_code} %{time_total}\n" "$P/"
curl -s "$P/busca/" | grep -o -E 'results-bar__count[^>]*>[^<]*' | sed -E 's/.*>//'
curl -s -o /dev/null -w "%{http_code} %{time_total}\n" "$P/busca/?q=licita%C3%A7%C3%A3o"
curl -s "$P/busca/?q=pregao" | grep -o -E 'results-bar__count[^>]*>[^<]*' | sed -E 's/.*>//'
curl -s "$P/busca/?q=preg%C3%A3o" | grep -o -E 'results-bar__count[^>]*>[^<]*' | sed -E 's/.*>//'
curl -s "$P/busca/?q=licitacao" | grep -o -E 'results-bar__count[^>]*>[^<]*' | sed -E 's/.*>//'
curl -s "$P/busca/?q=licita%C3%A7%C3%A3o" | grep -o -E 'results-bar__count[^>]*>[^<]*' | sed -E 's/.*>//'
curl -s "$P/busca/?typeinform_id=<id>" | grep -o -E 'results-bar__count[^>]*>[^<]*' | sed -E 's/.*>//'
curl -s -o /dev/null -w "%{http_code}\n" "$P/colecoes/"
for u in /metodologia/ /metodologia/categorias/ /metodologia/assuntos/; do curl -s -o /dev/null -w "%{http_code}\n" "$P$u"; done
curl -s "$P/metodologia/" | grep -c -E 'Documentos Normativos|Vídeos|>Pareceres<|FASE PREPARATÓRIA - '
curl -s "$P/busca/" | grep -c 'name="assunto_id"'
curl -s -o /dev/null -w "%{http_code}\n" "$P/busca/?category_id=abc"
curl -s -o /dev/null -w "%{http_code}\n" "$P/__rota_inexistente__/"
curl -s "$P/__rota_inexistente__/" | grep -c 'Using the URLconf'
docker compose --env-file .env -f docker/docker-compose.yml logs --no-log-prefix portal 2>&1 | grep -c 'WARNING django.request'
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/Biblioteca/
```

Esperado (ensaio), linha a linha: o id de Acórdãos (97 no ensaio; na VM será outro); `200` e o tempo da página inicial (0,11–0,13 s no ensaio); `1089 documentos`; `200` e o tempo da busca (0,04–0,07 s no ensaio); `46 documentos` duas vezes (busca sem e com acento dá o mesmo número); `529 documentos` duas vezes; `3 documentos` (Acórdãos); `301` (o endereço antigo de Coleções redireciona para a Metodologia); `200` três vezes (as três abas da Metodologia); `0` (nenhum tipo retirado nem prefixo antigo na Metodologia); `16` (filtro de Assunto com 16 opções); `400` (URL manipulada tratada, sem erro 500); `404`; `0` (sem página de erro técnica); um número maior que zero (o portal registra as respostas 400 e 404 no log do contêiner). A última linha passa pela borda `index.php` e não fez parte do ensaio: ela só dá `200` se a rota `/Biblioteca/` da borda estiver reaberta (ver "Situação da homologação", no início desta seção).

- Se todas as respostas derem `400` (e as contagens vierem vazias), é o `ALLOWED_HOSTS`, que não aceita `127.0.0.1`: pare e devolva a saída.
- Se `/colecoes/` responder `200` ou `/metodologia/` responder `404`, o código não é o ensaiado: pare e devolva a saída.
- Tempo da página inicial acima de 1 s: devolva o tempo e a saída de `docker compose --env-file .env -f docker/docker-compose.yml logs --no-log-prefix portal | grep 'coluna nr_document.busca'` (se aparecer, a seção 1 do passo 3 não criou a coluna de busca).
- Com `FORCE_SCRIPT_NAME=/Biblioteca` no `.env` da VM, estes testes diretos em `127.0.0.1:8010` continuam valendo: o prefixo só muda os links que o portal gera (o `301` de `/colecoes/`, por exemplo, aponta para `/Biblioteca/metodologia/`). Pela borda, os mesmos endereços ficam sob `/Biblioteca/`.

**Passo 12 — Borda e segurança (TI).** Depois do passo 11, e só então:

1. **Reabrir a rota `/Biblioteca/` na borda**, do mesmo jeito que foi fechada em 08/09 (só a TI sabe como fez). Depois, `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/Biblioteca/` deve dar `200`, e `http://127.0.0.1/Biblioteca/metodologia/` também.
2. **Conferir que o `/manager` do Nou-Rau não responde de fora** (pela borda): o teste é o que a TI já usa para a borda; de dentro da VM, o Nou-Rau continua em `127.0.0.1:8082`. Se estiver aberto, bloqueie na borda antes de avisar que a homologação está no ar.
3. **Trocar as senhas iniciais do Nou-Rau** (`admin` e `colab`), se ainda forem as do seed: pelo próprio Nou-Rau (área de usuários → "Trocar a senha"), nunca por SQL — o formato de armazenamento é do Nou-Rau. Guarde no cofre de senhas da TI. Faça isto depois da carga (passo 10): uma volta atrás pelo §4.2 restaura o backup do passo 2, com as senhas de antes.

**O que devolver ao Bernardo.**

- Data, hora e quem executou cada passo.
- A saída dos passos 0, 1, 3, 4, 5, 7, 10 e 11 (o texto da tela) e, do passo 12, o que foi feito em cada item (rota reaberta; `/manager` bloqueado: sim/não; senhas trocadas: sim/não).
- Nome, tamanho e sha256 dos três backups do passo 2. Os arquivos, não.
- Os arquivos `dryrun_…txt`, `carga_…txt` e `validate_…txt`.
- Qualquer diferença do esperado, com a saída literal.

### 4.2 Se precisar voltar atrás

Use quando um passo de 3 a 11 sair diferente do esperado e o Bernardo, ao receber a saída, pedir para voltar (a TI não decide sozinha). Os dois métodos devolvem o banco ao estado do passo 2 (982 materiais, taxonomia v11). Os dois foram ensaiados em 30/09/2026 sobre o banco já carregado com a v12.1 (1089 materiais); depois de cada um, o roteiro foi executado de novo do passo 3 ao 11 com o mesmo resultado.

**Método A (recomendado): `make restore` com o `backup_….dump` do passo 2.** Roda numa transação única: se falhar, nada muda. Depois do restore, o alvo recria a conta de leitura do portal e fecha de novo a leitura de `users` — a restauração recria a tabela e devolveria a leitura ao portal. Troque `AAAAMMDD_HHMMSS` pelo nome do arquivo do passo 2.

```bash
make restore FILE=backup_AAAAMMDD_HHMMSS.dump
docker compose --env-file .env -f docker/docker-compose.yml restart portal
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -c "SELECT count(*) AS docs FROM nr_document;" -c "SELECT count(*) AS assuntos FROM nr_assunto;" -c "SELECT has_table_privilege('portal_reader','public.users','SELECT') AS portal_reader_le_users;"
```

Esperado (ensaio): o `pg_restore` sem mensagem de erro; `DO`, `ALTER ROLE`, `GRANT` (4 vezes) e `ALTER DEFAULT PRIVILEGES` (2 vezes), da conta de leitura; a frase "Banco restaurado de …; leitura de users revogada do portal"; `docs` 982, `assuntos` 14 e `portal_reader_le_users` = `f`. A busca do portal volta a mostrar `982 documentos` e a página inicial responde `200` (mais lenta, cerca de 3 s: sem a coluna de busca, o portal usa o caminho antigo e escreve `coluna nr_document.busca ausente` no log).

- O código novo lê o banco antigo sem erro: sem a coluna de busca, o portal busca pelo caminho antigo (mais lento) e escreve um aviso `coluna nr_document.busca ausente` no log. Voltar também o código é opcional e não foi ensaiado: `git checkout $(cat commit_anterior.txt)` (com o arquivo do passo 1) e `up -d --build portal`; isso deixa o clone fora da branch (`HEAD` solto) — para retomar depois, `git checkout main` e o passo 1 de novo.
- Se o `pg_restore` reclamar de `role "portal_reader" does not exist`, a conta não existe na VM: rode `docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres bash -s < docker/postgres/init/09-portal-readonly-user.sh` e repita o `make restore`.

**Método B (se o `make restore` falhar): restaurar o `backup_clean_….sql` do passo 2 com o `psql`.** É um comando só, também numa transação única. Foi ensaiado em 23/09 (3 vezes) e em 30/09/2026.

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -v ON_ERROR_STOP=1 --single-transaction < backup_clean_AAAAMMDD_HHMMSS.sql > rollback_saida.txt 2> rollback_erros.txt
grep -c ERROR rollback_erros.txt
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -v ON_ERROR_STOP=1 -q < docker/postgres/init/10-portal-readonly-revoke-users.sql
docker compose --env-file .env -f docker/docker-compose.yml restart portal
docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php -d nourau -c "SELECT count(*) AS docs FROM nr_document;" -c "SELECT count(*) AS assuntos FROM nr_assunto;" -c "SELECT has_table_privilege('portal_reader','public.users','SELECT') AS portal_reader_le_users;"
```

Esperado (ensaio): `grep -c ERROR` = 0; o `REVOKE` roda em silêncio (`-q`); `docs` 982, `assuntos` 14 e `portal_reader_le_users` = `f`. A busca volta a `982 documentos` e a página inicial responde `200`.

- O `REVOKE` (arquivo `10-…`) é obrigatório nos dois métodos: a restauração recria a tabela `users` e devolve à conta do portal a leitura dela (visto nos ensaios de 23/09 e 30/09).
- Sobram a extensão `unaccent` e a configuração `portuguese_unaccent`. Não atrapalham: a seção 1 as reaproveita.

**Não use** um `.sql` em texto sem `--clean` por cima de banco com dados (era o que o `make restore` antigo imprimia). No ensaio de 23/09, deu 117 erros com código de saída 0: o banco continuou com o acervo novo, e só a lista de erros na tela mostrava o problema. Pior: ele roda os `setval` do backup e dessincroniza as sequências, e as próximas inserções colidiriam com materiais que já existem.

## 5. Checklist de segurança (antes de expor fora do laptop)

- [ ] `DJANGO_DEBUG=false` (ou ausente) em homologação e produção (confirmar CSP no fio; uma URL inexistente NÃO pode mostrar a página de debug do Django).
- [ ] `DJANGO_SECRET_KEY` própria e única por ambiente. Desde 30/09/2026 não há chave padrão: sem ela o compose não sobe e, fora do dev, o portal recusa subir.
- [ ] `POSTGRES_PASSWORD` e `PORTAL_DB_PASSWORD` fortes (o stack falha claro se ausentes).
- [ ] **Senhas iniciais do Nou-Rau trocadas** (os usuários `admin` e `colab` nascem com a senha padrão do seed, definida em `docker/postgres/init/03-reset.sql`). Rotacionar pelo próprio Nou-Rau (área de usuários → "Trocar a senha"), nunca por SQL, e guardar no cofre de senhas da TI (§4.1, passo 12).
- [ ] **`/manager` (admin do Nou-Rau) bloqueado na borda**: só por IP/VPN/Basic-Auth (ver [adr/0006](adr/0006-borda-canonica.md)); nunca público.
- [ ] A conta `portal_reader` **sem leitura da tabela `users`**: a seção 1.11 da migração e o `make restore` fazem o `REVOKE`; confira com `has_table_privilege` depois de qualquer restauração ou init 09.
- [ ] Portas internas só em loopback (`127.0.0.1`); em produção, sob a borda, sem publish direto.
- [ ] **Rotina de backup:** `make backup` (banco em `.dump` + arquivos da curadoria em `.tgz`) antes de toda subida e com periodicidade definida pela TI, com cópia guardada fora do servidor. Os arquivos contêm a tabela `users`: não circulam; só nome, tamanho e sha256.
- [ ] **Registro de erros:** `docker compose … logs portal` traz as respostas 400/404 (uma linha) e os 500 (com a exceção). Definir quem olha o log da homologação e com que frequência.
- [ ] `SECURE_SSL=true` apenas quando houver TLS na frente.

## 6. O que a produção vai exigir

Só o que o código e os ADRs já sustentam; sem endereço, host ou fornecedor. A decisão de produção (contrato e domínio na Prodesp) é institucional.

- **Borda com TLS** e domínio próprio: `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` com o domínio, `FORCE_SCRIPT_NAME` conforme a borda (raiz ou sub-path), `SECURE_SSL=true` (cookies Secure, redirect, HSTS). Referência opcional: `docker/docker-compose.prod.yml` + `Caddyfile` (ADR-0006).
- **Admin do Nou-Rau (`/manager`) fora do domínio público:** subdomínio ou rota própria, restrita por rede ou autenticação na borda (ADR-005 da vault; ADR-0006).
- **Chave e senhas próprias do ambiente**, nunca reaproveitadas da homologação; senhas iniciais do Nou-Rau trocadas antes de abrir.
- **Rotina de backup** do banco e do volume de arquivos (`make backup`) com guarda fora do servidor e ensaio periódico do `make restore` (o restore que nunca foi testado não é backup).
- **Dono do suporte:** quem acompanha `docker compose … logs portal`, quem executa restore e quem recebe as solicitações de subida (hoje: TI/PRODESP para operar; LILP para o código).
- **Caminho de subida:** esteira GitHub Actions sobre o Git corporativo (em validação; ADR-0007), com o mesmo roteiro deste documento.
