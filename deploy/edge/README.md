# Borda de homologação (front-controller `index.php`)

Roteador PHP multi-projeto que serve, sob um domínio único, cada sistema do LILP em seu **sub-path** (ex.: `/Biblioteca/` → portal Django em `127.0.0.1:8010`). É a borda **em uso na homologação** (VM). A borda canônica de produção é o Caddy (ver [`../../docs/adr/0006-borda-canonica.md`](../../docs/adr/0006-borda-canonica.md)); este edge é versionado para reprodutibilidade e como transição.

## Arquivos
- `index.php` — front-controller (proxy reverso por cURL com streaming; descarta `X-Forwarded-*` do cliente e os reescreve; bloqueia dotfiles/extensões sensíveis; rate-limit). **Sem segredos** — lê tudo do `.env`.
- `.htaccess` — `RewriteRule ^ index.php [L]` + `php_flag enable_post_data_reading Off`.
- `.env.example` — mapa `DJANGO_PROJECTS=<Sistema>:<porta>`.

## Registrar uma nova frente
1. Subir o stack da frente com o portal em uma porta loopback livre (ex.: `8011`).
2. Adicionar `OutroSistema:8011` em `DJANGO_PROJECTS` no `.env` do edge.
3. No `.env` do app: `FORCE_SCRIPT_NAME=/OutroSistema` + `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` do host público.

## Deploy na VM
Provisionar `index.php` + `.htaccess` em `/opt/lampp/htdocs/` (hoje feito à mão; alvo: script/CI). **Não** editar direto no servidor sem refletir aqui.
