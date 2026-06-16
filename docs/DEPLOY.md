# Deploy e operação — BDLP

Runbook da esteira **dev (local) → homologação (VM) → produção (Prodesp)**. Vale como referência para os demais sistemas do LILP.

## 1. Matriz de configuração por estágio

A `.env` (raiz) é a fonte única (o Makefile usa `--env-file .env`). Diferenças por estágio:

| Variável | dev (local) | homologação (VM, HTTP) | produção (TLS) |
|---|---|---|---|
| `DJANGO_DEBUG` | `true` | **`false`** | **`false`** |
| `SECURE_SSL` | `false` | `false` (só :80) | **`true`** (HTTPS) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | IP + host público da VM | domínio Prodesp |
| `CSRF_TRUSTED_ORIGINS` | — | `http(s)://<host-VM>` | `https://<domínio>` |
| `FORCE_SCRIPT_NAME` | (vazio) | `/Biblioteca` | conforme a borda |
| `DJANGO_SECRET_KEY` | qualquer | forte (≠ default) | forte (≠ default) |

> **`DEBUG` e `SECURE_SSL` são desacoplados** de propósito: homologação roda `DEBUG=false` em HTTP puro sem quebrar o login (as flags que exigem HTTPS — cookies Secure, redirect, HSTS — ficam só sob `SECURE_SSL`).

Gerar a `DJANGO_SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

## 2. Promoção homologação (VM)

```bash
ssh bdlp-vm
cd /opt/lampp/htdocs/projects/biblioteca-digital-logistica-publica
git pull --ff-only origin main
docker compose --env-file .env -f docker/docker-compose.yml up -d --build
docker compose --env-file .env -f docker/docker-compose.yml exec -T portal python manage.py check --deploy --fail-level ERROR
# Smoke-test:
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/Biblioteca/      # 200
curl -s http://127.0.0.1:8010/__nao_existe__/ | grep -c "Using the URLconf" # 0 (DEBUG off)
```

## 3. Produção (Caddy + TLS)

```bash
# .env com DOMAIN, DJANGO_DEBUG=false, SECURE_SSL=true, ALLOWED_HOSTS=<domínio>
docker compose --env-file .env -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d --build
```
A borda canônica é o Caddy (ver [adr/0006-borda-canonica.md](adr/0006-borda-canonica.md)). Em domínio único, cada sistema é um sub-path (`handle_path /Biblioteca/*`) com `FORCE_SCRIPT_NAME` coerente.

## 4. Dados / acervo

Carga e full-refresh: ver [../tools/db-refresh.md](../tools/db-refresh.md). Sempre `make backup` antes; `make migrate-dry` deve sair com **0 erros** antes de `make migrate`; `make validate` confere a consistência.

## 5. Hardening obrigatório (antes de expor fora do laptop)

- [ ] `DJANGO_DEBUG=false` em homologação e produção (confirmar CSP no fio; uma URL inexistente NÃO pode mostrar a página de debug do Django).
- [ ] `DJANGO_SECRET_KEY` forte e única por ambiente (nunca o default).
- [ ] `POSTGRES_PASSWORD` e `PORTAL_DB_PASSWORD` fortes (o stack falha claro se ausentes).
- [ ] **Trocar a senha seed do Nou-Rau** (`admin`/`colab` nascem com senha `admin` em `03-reset.sql`). Rotacionar via `UPDATE users SET password=... WHERE username IN ('admin','colab');` e guardar no cofre do projeto.
- [ ] **`/manager` NÃO público** em produção: restringir por IP/VPN/Basic-Auth na borda (ver [adr/0006](adr/0006-borda-canonica.md)).
- [ ] Portas internas só em loopback (`127.0.0.1`); em produção, sob o Caddy, sem publish direto.
- [ ] Backups `pg_dump` protegidos (não versionados; `backup_*.sql` é gitignored).
- [ ] `SECURE_SSL=true` apenas quando houver TLS na frente.
