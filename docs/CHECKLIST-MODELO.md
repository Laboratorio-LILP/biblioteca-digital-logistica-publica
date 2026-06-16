# Checklist "Pronto-para-Modelo" — nova frente do LILP

Passo-a-passo para uma nova frente clonar o padrão da BDLP. Separa a **casca reutilizável** (infra genérica) do **conteúdo específico** (que cada sistema troca).

## Casca reutilizável (copiar quase como está)
- `docker/docker-compose.yml` — trocar `name: lilp-<sigla>`; manter loopback, healthcheck, fail-loud de senhas.
- `docker/portal/Dockerfile` — instala do `requirements.lock` (sem lista de deps duplicada).
- `portal/portal/settings.py` — 12-factor (django-environ), `FORCE_SCRIPT_NAME`, `SECURE_SSL` desacoplado de `DEBUG`, CSP condicional, `STORAGES`.
- `Makefile` — interface de operação (up/down/migrate/validate/test/backup).
- `.env.example` (raiz, fonte única), `.github/workflows/ci.yml`, `docker/Caddyfile` + `docker/docker-compose.prod.yml`, `deploy/edge/`.
- `docs/DEPLOY.md`, este checklist e o template de ADR.

## Conteúdo específico (cada sistema substitui)
- `docker/nourau/` (Nou-Rau é específico da BDLP) — substituir pelo backend da frente, ou remover se não houver.
- `docker/postgres/init/06-08-*.sql` — seeds de taxonomia/categorias da BDLP.
- `portal/catalog/` — modelos/views/taxonomia do domínio.
- Identidade visual e textos.

## Checklist de bootstrap
- [ ] Repo na org `Laboratorio-LILP`; clone de trabalho FORA do OneDrive (ADR-002).
- [ ] `name: lilp-<sigla>` no compose; mapa de portas sem conflito.
- [ ] `cp .env.example .env`; gerar `DJANGO_SECRET_KEY`; definir `POSTGRES_PASSWORD`/`PORTAL_DB_PASSWORD` fortes.
- [ ] `make up` sobe os 3 serviços; `make migrate` + `make validate` com 0 erros.
- [ ] Suíte de testes mínima passando (`make test`) e `ruff check` limpo.
- [ ] `manage.py check --deploy` limpo com env de produção; CI verde no PR.
- [ ] Registrar o sub-path na borda (`DJANGO_PROJECTS=<Sistema>:<porta>` ou `APP_PATH` no Caddy) + `FORCE_SCRIPT_NAME`.
- [ ] `docs/DEPLOY.md` preenchido (hosts, domínio) e **hardening** cumprido (DEBUG=false, senha seed trocada, /manager restrito).
- [ ] ADRs herdados/ajustados (borda, canal de homologação, portas).
