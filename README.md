# Biblioteca Digital de Logística Pública (BDLP)

Portal público de acervo + backend de curadoria (Nou-Rau), do Laboratório de Inovação em Logística Pública (LILP / SGGD-SP). Este repositório é o **modelo de referência** da esteira dev → homologação → produção do LILP.

## Arquitetura

Três serviços orquestrados por Docker Compose (nome de projeto `lilp-bdlp`):

- **portal** — Django 5 + gunicorn. Acervo público; conecta ao banco como usuário **read-only** (`portal_reader`).
- **nourau** — PHP/Apache (Nou-Rau). Backend de curadoria, servido em `/manager`.
- **postgres** — Postgres 15. Banco do acervo.
- **borda** — Caddy (produção) ou `index.php` (homologação) — ver [docs/DEPLOY.md](docs/DEPLOY.md).

O portal é **sub-path-agnóstico** (`FORCE_SCRIPT_NAME`): roda na raiz em dev e sob `/Biblioteca` atrás do proxy.

## Pré-requisitos

- Docker + Docker Compose.
- `make` + `bash` — no Windows, via **WSL** ou **Git Bash**. (Os alvos `tunnel-*` do Makefile são exclusivos de macOS.)

## Quickstart (dev local)

```bash
cp .env.example .env        # ajuste os segredos (DJANGO_SECRET_KEY, senhas)
make up                     # sobe postgres + nourau + portal
make migrate FILE=/caminho/acervo.xlsx   # importa o acervo (usa --sheet "Inserir Material")
make validate               # valida a importação
```

Portal em `http://localhost:${PORTAL_PORT:-8000}`. Curadoria em `http://localhost:${NOURAU_PORT:-8080}/manager/`.

> A `.env` (raiz) é a **fonte única** de configuração — o Makefile usa `--env-file .env`. Todas as senhas são **obrigatórias** (o stack falha claro se faltarem; não há mais defaults inseguros). Gere a SECRET_KEY com:
> `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`

## Portas (dev)

| Serviço  | Porta host (loopback)    |
|----------|--------------------------|
| portal   | `${PORTAL_PORT:-8000}`   |
| nourau   | `${NOURAU_PORT:-8080}`   |
| postgres | `${POSTGRES_PORT:-5432}` |

## Testes e qualidade

```bash
make test          # pytest (em container) — ou: cd portal && python -m pytest
ruff check portal/ # lint
```

O CI (GitHub Actions, `.github/workflows/ci.yml`) roda ruff + pytest + `manage.py check --deploy`.

## Operação e deploy

- **[docs/DEPLOY.md](docs/DEPLOY.md)** — matriz de ambientes (dev/homolog/prod), promoção e **checklist de hardening**.
- **[docs/CHECKLIST-MODELO.md](docs/CHECKLIST-MODELO.md)** — passo-a-passo para uma nova frente do LILP clonar este padrão.
- **[docs/adr/](docs/adr/)** — decisões de arquitetura (borda, canal de homologação, portas).
- **[tools/db-refresh.md](tools/db-refresh.md)** — full-refresh do acervo.
