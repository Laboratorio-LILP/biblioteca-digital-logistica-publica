# BDLP — Integração da frente para o Claude Code

Biblioteca Digital de Logística Pública (BDLP), frente prioritária do LILP. Este arquivo é a camada de **Instruções da frente** para o Claude Code; viaja com o repositório.

## Rito de sessão
O **rito transversal** (abertura/durante/fechamento, regra de ouro, precedência) vive em `LILP/CLAUDE.md` na árvore OneDrive e carrega sozinho quando você trabalha lá. **Se este clone estiver fora do OneDrive** (o caso canônico, `C:\Projetos\Governo\…`), o arquivo transversal não é ancestral — então leia o rito e o estado direto na vault:
- Vault: `C:\Users\bcgsantos\OneDrive - PRODESP\LILP\SGGD - SEGES - LILP\`
- Rito + teoria: `…\Padrões\Arquitetura de Contexto.md` (+ `LILP\CLAUDE.md`)
- Estado vivo do laboratório: `…\Mapa de Contexto Operacional.md`
- **Estado desta frente (leia sempre):** `…\Portfólio\Mapa-Semente — Biblioteca Digital (BDLP).md`

## O que é
Portal Django (busca/facetas) + Nou-Rau (catálogo/curadoria) + Postgres, em três contêineres Docker (compose `lilp-bdlp`). Acervo v8 (**406 docs** canônicos desde 16/06/2026). Homologação no ar e endurecida na VM da SGGD, atrás do `index.php` do Felipe (proxy reverso, subcaminho `/Biblioteca/`).

## Onde isto roda
- **Clone canônico:** `C:\Projetos\Governo\biblioteca-digital-logistica-publica` (fora do OneDrive, ADR-002). O clone dentro do OneDrive é **secundário/legado**.
- **Remoto:** `github.com/Laboratorio-LILP/biblioteca-digital-logistica-publica`.
- **VM de homologação:** SSH alias `bdlp-vm` (key-based; usuário `bernardosantos:webdev`, sem `sudo` para git/.env). Tudo em loopback (portal 8010, nourau 8081, postgres 5433); só `:80` pública; `DEBUG=false` em HTTP.

## Gotchas que quebram o portal (não tropece)
- `portal_reader` tem **senha hardcoded** no init `09-portal-readonly-user.sql` (`portal_reader_dev`); `PORTAL_DB_PASSWORD` precisa ser esse valor ou o portal dá 500.
- O volume `lilp-bdlp_pgdata` **persiste por nome de projeto**, não por pasta — base limpa exige `docker volume rm lilp-bdlp_pgdata`.
- A **taxonomia (coleções) vem dos init scripts do clone** — clone defasado semeia coleções BDU velhas; precisa estar na `main` para a v8.
- Carregar acervo: `docker exec lilp-bdlp-portal-1 python manage.py migrate_spreadsheet <xlsx> --sheet "Inserir Material"` **sem `--skip-red`** (o Makefile `migrate` NÃO repassa `--sheet`).
- Portas por ambiente: **local Windows** `PORTAL_PORT=8001` (8000 reservada pelo kernel); **VM** 8010/8081/5433.
- O `index.php`/`.htaccess` da VM é **infra do Felipe**, NÃO está em git, editado via `sudo` com `.bak-*`. O app é **proxy-agnóstico**.

## Subir local (DEMO.md)
`make clean && make up` → copiar planilha ao portal → `make migrate` → `make validate`. Sanidade: `curl :8001` (200), nourau (302).

## Segredos
Nunca entram em arquivo versionado nem na vault. `.env` é gitignored.
