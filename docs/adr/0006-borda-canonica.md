# ADR 0006 — Borda canônica da esteira (Caddy sub-path; index.php em transição)

- **Status:** Aceito (2026-06-16)
- **Contexto:** Existiam três bordas divergentes: dev (sem borda), homologação (um `index.php` PHP multi-projeto, fora do git, servindo sub-path `/Biblioteca`) e o `docker/Caddyfile` versionado (nunca implantado, montando o portal na raiz `/`). A borda que de fato resolve o cenário "domínio único / sub-path" da Prodesp (o `index.php`) não estava versionada; a versionada não resolvia sub-path nem multi-sistema. Isso quebra a paridade homolog↔prod e impede replicar a esteira em novos sistemas.

## Decisão

1. A borda **canônica do modelo é o Caddy**, configurado para **sub-path** (`handle_path /<Sistema>/*` → portal), passando `FORCE_SCRIPT_NAME=/<Sistema>` ao app. Cada sistema do LILP entra como um sub-path do domínio único.
2. O `index.php` de homologação é **versionado** em `deploy/edge/` como borda de transição até a migração para Caddy; deixa de ser infra manual não rastreada.
3. **`/manager` (admin Nou-Rau) não é público**: restrito por IP/VPN/Basic-Auth na borda (ver ADR relacionado ao hardening em `docs/DEPLOY.md`).

## Consequências

- Homologação e produção passam a exercitar o mesmo modelo de roteamento (sub-path), reduzindo surpresas na promoção.
- A peça mais crítica da borda passa a ter versão, review e origem reproduzível.
- Migração do `index.php`→Caddy na VM exige janela de manutenção (fora do escopo automatizado).
