# BDLP — Integração da frente para o Claude Code

Biblioteca Digital de Logística Pública (BDLP), frente prioritária do LILP e **repo-modelo** do laboratório. Este arquivo é a camada de **Instruções da frente** para o Claude Code; viaja com o repositório.

## Limites de segurança — inegociáveis

Valem integralmente os limites do `LILP/CLAUDE.md` transversal e do ADR-006 da vault (reunião
CTI de 30/06/2026): sem túneis, sem alterações de firewall, sem PowerShell em host corporativo,
sem acesso a servidores — acesso é restrito a TI/PRODESP e a VPN é a via única de acesso remoto.
O mecanismo de homologação sem VPN desta frente (túnel como serviço + watchdog) está **proscrito
e em desmonte**: não reativar, não recriar, não "consertar". A subida dev→homologação passa a
ser por esteira GitHub Actions sobre o Git corporativo (em validação). Se algo estiver
inacessível, a resposta correta é parar e registrar solicitação à equipe de TI (Felipe/Diego).

## Rito de sessão
O **rito transversal** (abertura/durante/fechamento, regra de ouro, precedência) vive em `LILP/CLAUDE.md` na árvore OneDrive e carrega sozinho quando se trabalha lá. **Este clone canônico fica FORA do OneDrive** (ADR-002; Mac é a máquina principal desde 23/06/2026: `~/Developer/Governo/…`; Windows legado: `C:\Projetos\Governo\…`), onde o arquivo transversal não é ancestral — então leia o rito e o estado direto na vault:
- Vault (Mac): `~/Library/CloudStorage/OneDrive-PRODESP/LILP/SGGD - SEGES - LILP/` (Windows legado: `C:\Users\<usuario>\OneDrive - PRODESP\LILP\SGGD - SEGES - LILP\`)
- Rito + teoria: `…/Padrões/Arquitetura de Contexto.md` (+ `LILP/CLAUDE.md`)
- Estado vivo do laboratório: `…/Mapa de Contexto Operacional.md`
- **Estado desta frente (leia sempre):** `…/Portfólio/Mapa-Semente — Biblioteca Digital (BDLP).md`

## O que é
Portal Django (busca/facetas) + Nou-Rau (catálogo/curadoria) + Postgres, em três contêineres Docker (compose `lilp-bdlp`). Acervo em homologação, até a recarga: **982 materiais** (planilha `BDLP_25_08_2026_982_materiais_v11.xlsx`, 26/08/2026; o número vivo está no Mapa-Semente da frente), taxonomia **v11**. Planilha da recarga: `BDLP_30_09_2026_1137_materiais_v12_final.xlsx` (1089 ativas, 48 vermelhas; o banco local já a tem carregada). Página **Metodologia** (ex-Coleções; `/metodologia/`, três abas) desde 30/09/2026. Vocabulário **v12.1** (set/2026: vocabulário de tipos — Jurisprudência = Súmulas, Boletins, Acórdãos, Deliberações; Doutrina ganha Enunciados (Pareceres entrou e saiu — v12.1, 23/09); Instrução perde Vídeos —, 16 assuntos, subcategorias de Planejamento sem o prefixo "FASE PREPARATÓRIA"; normas/leis/decretos/portarias saem do acervo pela planilha). CONTEÚDOS TRANSVERSAIS segue sem subcategorias desde a v9; a dimensão temática é o Assunto. Homologação endurecida na VM da SGGD, atrás da borda `index.php` (proxy reverso, subcaminho `/Biblioteca/`); **fora do ar desde 08/09/2026** por determinação do subsecretário até homologar a versão corrigida — mesclada em `main` em 23/09/2026 (merge da branch `feat/2026-09-validacao-subsecretario`); subida à TI pendente (roteiro ensaiado em 30/09/2026: docs/DEPLOY.md §4.1; voltar atrás em §4.2; o que a produção vai exigir em §6).

## Onde isto roda
- **Clone canônico:** este repo, em `~/Developer/Governo/biblioteca-digital-logistica-publica` no Mac (máquina principal; no Windows legado: `C:\Projetos\Governo\…`) — fora do OneDrive, ADR-002.
- **Remoto:** `github.com/Laboratorio-LILP/biblioteca-digital-logistica-publica`. CI (ruff + pytest + `manage.py check --deploy`) roda nos PRs.
- **VM de homologação** (operada por TI/PRODESP; acesso direto do desenvolvedor descontinuado — ADR-006): stack em loopback (portal 8010, nourau 8082, postgres 5433; ADR-0008); só `:80` pública; `DEBUG=false` em HTTP, CSP ligada. Subida dev→homolog: esteira GitHub Actions (em validação).

## Decisões de arquitetura (ADRs do repo, em `docs/adr/`)
- **0006** — borda por estágio: a `index.php` é a borda de homologação (servidor interno SGGD); Caddy = referência opcional; borda de produção na Prodesp a definir.
- **0007** — canal de homologação (parte Dev Tunnels **revogada** em 02/07/2026 — ver nota de status no próprio ADR; canal canônico: VM via VPN + esteira GitHub Actions).
- **0008** — portas em loopback (**substitui** a orientação do ADR-004 da vault de expor à web).

A borda de homologação (`index.php`/`.htaccess`) agora é **versionada** em `deploy/edge/` (não é mais só infra do Felipe na VM). Os ADRs transversais do laboratório (numerados `ADR-NNN`) vivem na vault; estes (`000N`) são específicos do repo.

## Gotchas (não tropece)
- **Segredos por env, sem fallback** (endurecimento do PR #16 e de 30/09/2026): o compose **falha** se as senhas ou a `DJANGO_SECRET_KEY` não estiverem no `.env` (sem os defaults fracos de dev); fora do dev o portal recusa subir sem chave; `DJANGO_DEBUG` ausente vale `false` (o `.env` de dev precisa de `DJANGO_DEBUG=true` para o modo de desenvolvimento). `PORTAL_DB_PASSWORD` é obrigatória — a role `portal_reader` é criada por env no init; sem ela o portal dá 500.
- O volume `lilp-bdlp_pgdata` **persiste por nome de projeto**, não por pasta — base limpa exige `docker volume rm lilp-bdlp_pgdata`.
- A **taxonomia (coleções) vem dos init scripts do clone** — clone defasado semeia coleções BDU velhas; precisa estar na `main` para a v8.
- Carregar acervo: `docker exec lilp-bdlp-portal-1 python manage.py migrate_spreadsheet <xlsx> --sheet "Inserir Material"` (mais `--skip-red` quando a curadoria marcou linhas em vermelho). Planilha da recarga: `BDLP_30_09_2026_1137_materiais_v12_final.xlsx` (1089 ativas, 48 vermelhas — sempre `--skip-red`). Antes de carregar, confirme a planilha canônica no Mapa-Semente — as `BDLP_507_*`, a `... v11 (PARA CORREÇÃO).xlsx`, a consolidada `BDLP_23_09_2026_1153_materiais_v12.xlsx` e a `..._pos-auditoria.xlsx` de 23/09 estão superadas. Banco existente recebe a v12 pelo script `docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql` (seção 1 antes da recarga — inclui a coluna de busca indexada e o REVOKE de `users` —, seção 2 depois). Runbook: `tools/db-refresh.md`; em homologação, `docs/DEPLOY.md` §4.1.
- **Tipo de informação fora do vocabulário canônico é recusado pelo importador** (linha inteira, com motivo no `--dry-run`); `--allow-new-types` cria o tipo só como exceção documentada. Coleção que não casa uma raiz, e Categoria/Subcategoria/Microcategoria/Assunto preenchidos que não resolvem, também recusam a linha — nada mais entra "na primeira raiz" ou com NULL em silêncio.
- **Planilhas com fundo vermelho da curadoria exigem `--skip-red`** (a PARA CORREÇÃO da v12 marca em vermelho o que sai do acervo); sem a flag, essas linhas entram.
- Build: **`requirements.lock`** (versões travadas); o Dockerfile instala do lock. Ferramentas de teste em `requirements-dev.txt` (estágio `test` do Dockerfile e CI). **`make test`** roda ruff + pytest num contêiner sobre o working tree; no host, `cd portal && DJANGO_SECRET_KEY=teste python -m pytest -q`.
- **Backup e restore**: `make backup` (banco em `.dump` + arquivos da curadoria em `.tgz`) e `make restore FILE=… .dump` (tudo ou nada, seguido da role de leitura e do REVOKE de `users`). Todo restore devolve ao portal a leitura de `users` se o REVOKE não vier depois; a seção 1.11 da migração também o faz.
- **Busca**: a coluna gerada `nr_document.busca` (índice GIN) é a mesma soma de vetores de `catalog/fts.py`; mudou campo ou peso, muda lá, regrava o SQL no seed e na migração (o teste confere) e recria a coluna. Sem a coluna o portal degrada para o vetor calculado e avisa no log.
- **URL manipulada** (id que não é número, NUL) responde 400 tratado, não 500; erros vão para o stdout do contêiner (`docker compose logs portal`).
- Portas por ambiente: **local Mac (principal)** — defaults do compose (portal 8000, nourau 8080, postgres 5432); **Windows legado** `PORTAL_PORT=8001` (8000 reservada pelo kernel); **VM** 8010/8082/5433.
- **Worktrees em `.claude/worktrees/` são gitignorados** — invisíveis ao `git status`, mas são cópias completas do repo em disco. Em varreduras de segurança/limpeza, confira `git worktree list`.
- Após mudanças de segurança no repo, **reconcilie o `.env` local com o `.env.example`** — o `.env` não versionado pode reter configuração antiga (ex.: hosts extras em `ALLOWED_HOSTS`).

## Subir local
`make up` → carregar acervo (`migrate_spreadsheet --sheet "Inserir Material"`) → `make validate`. Ver `docs/DEPLOY.md`, `docs/CHECKLIST-MODELO.md` e `README.md`.

## Front
Paleta GESP **`#ED1C24`** (Pantone 485 C, fiel ao manual — decidido 16/06). a11y WCAG2AA; Linguagem Simples.

## Segredos
Nunca entram em arquivo versionado nem na vault. `.env` é gitignored.
