# BDLP — Integração da frente para o Claude Code

Biblioteca Digital de Logística Pública (BDLP), frente prioritária do LILP e **repo-modelo** do laboratório. Este arquivo é a camada de **Instruções da frente** para o Claude Code; viaja com o repositório.

## Rito de sessão
O **rito transversal** (abertura/durante/fechamento, regra de ouro, precedência) vive em `LILP/CLAUDE.md` na árvore OneDrive e carrega sozinho quando se trabalha lá. **Este clone canônico fica FORA do OneDrive** (`C:\Projetos\Governo\…`, ADR-002), onde o arquivo transversal não é ancestral — então leia o rito e o estado direto na vault:
- Vault: `C:\Users\bcgsantos\OneDrive - PRODESP\LILP\SGGD - SEGES - LILP\`
- Rito + teoria: `…\Padrões\Arquitetura de Contexto.md` (+ `LILP\CLAUDE.md`)
- Estado vivo do laboratório: `…\Mapa de Contexto Operacional.md`
- **Estado desta frente (leia sempre):** `…\Portfólio\Mapa-Semente — Biblioteca Digital (BDLP).md`

## O que é
Portal Django (busca/facetas) + Nou-Rau (catálogo/curadoria) + Postgres, em três contêineres Docker (compose `lilp-bdlp`). Acervo v8 (**406 docs** canônicos desde 16/06/2026). Homologação no ar e endurecida na VM da SGGD, atrás da borda `index.php` (proxy reverso, subcaminho `/Biblioteca/`).

## Onde isto roda
- **Clone canônico:** este repo, em `C:\Projetos\Governo\biblioteca-digital-logistica-publica` (fora do OneDrive, ADR-002).
- **Remoto:** `github.com/Laboratorio-LILP/biblioteca-digital-logistica-publica`. CI (ruff + pytest + `manage.py check --deploy`) roda nos PRs.
- **VM de homologação:** SSH alias `bdlp-vm` (key-based; usuário `bernardosantos:webdev`). Tudo em loopback (portal 8010, nourau 8082, postgres 5433; ADR-0008); só `:80` pública; `DEBUG=false` em HTTP, CSP ligada.

## Decisões de arquitetura (ADRs do repo, em `docs/adr/`)
- **0006** — borda por estágio: a `index.php` é a borda de homologação (servidor interno SGGD); Caddy = referência opcional; borda de produção na Prodesp a definir.
- **0007** — canal de homologação.
- **0008** — portas em loopback (**substitui** a orientação do ADR-004 da vault de expor à web).

A borda de homologação (`index.php`/`.htaccess`) agora é **versionada** em `deploy/edge/` (não é mais só infra do Felipe na VM). Os ADRs transversais do laboratório (numerados `ADR-NNN`) vivem na vault; estes (`000N`) são específicos do repo.

## Gotchas (não tropece)
- **Segredos por env, sem fallback** (endurecimento do PR #16): o compose **falha** se as senhas não estiverem no `.env` (sem `abc123`/`portal_reader_dev`). `PORTAL_DB_PASSWORD` é obrigatória — a role `portal_reader` é criada por env no init; sem ela o portal dá 500.
- O volume `lilp-bdlp_pgdata` **persiste por nome de projeto**, não por pasta — base limpa exige `docker volume rm lilp-bdlp_pgdata`.
- A **taxonomia (coleções) vem dos init scripts do clone** — clone defasado semeia coleções BDU velhas; precisa estar na `main` para a v8.
- Carregar acervo: `docker exec lilp-bdlp-portal-1 python manage.py migrate_spreadsheet <xlsx> --sheet "Inserir Material"` **sem `--skip-red`**. Planilha-fonte v8 FINAL (406): `Enriquecimento 499 v8 2026-06-11/BDLP_406_v8_FINAL.xlsx` (na pasta de docs da frente). Runbook: `tools/db-refresh.md`.
- Build: **`requirements.lock`** (versões travadas); o Dockerfile instala do lock.
- Portas por ambiente: **local Windows** `PORTAL_PORT=8001` (8000 reservada pelo kernel); **VM** 8010/8082/5433.

## Subir local
`make up` → carregar acervo (`migrate_spreadsheet --sheet "Inserir Material"`) → `make validate`. Ver `docs/DEPLOY.md`, `docs/CHECKLIST-MODELO.md` e `README.md`.

## Front
Paleta GESP **`#ED1C24`** (Pantone 485 C, fiel ao manual — decidido 16/06). a11y WCAG2AA; Linguagem Simples.

## Segredos
Nunca entram em arquivo versionado nem na vault. `.env` é gitignored.
