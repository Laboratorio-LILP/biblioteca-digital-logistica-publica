# ADR 0006 — Borda por estágio (index.php em homologação; Caddy como referência opcional)

- **Status:** Aceito (2026-06-16). Revisado no mesmo dia após esclarecimento: a borda é **diferente por estágio, por design** — não é acidente a corrigir.
- **Contexto:**
  - **Homologação** roda numa VM interna da SGGD, **não exposta à internet**, com **apenas a porta 80 aberta** (precaução de segurança do servidor). O front-controller `index.php` (autoria da TI — Felipe) recebe tudo na `:80` e roteia cada sistema do LILP para sua porta loopback (`/Biblioteca` → portal em `127.0.0.1:8010`). É uma **característica fixa desse servidor**, compartilhado por vários sistemas do laboratório.
  - **Produção (Prodesp)** será um ambiente distinto, ainda **a definir com a Prodesp** — não necessariamente igual à homologação.
  - Antes desta decisão, o `index.php` não estava versionado (infra manual) e o `docker/Caddyfile` versionado dava a entender, erroneamente, ser "a borda de produção".

## Decisão

1. **`index.php` é a borda canônica de homologação.** Passa a ser **versionado** em `deploy/edge/` (antes era editado à mão no servidor, sem rastreio).
2. **`docker/Caddyfile` + `docker-compose.prod.yml` são uma referência OPCIONAL** — um modelo de borda para um deploy próprio **exposto à internet** com HTTPS automático (ex.: VM em nuvem). **Não** são a borda de homologação nem obrigatórios para a Prodesp.
3. **A borda de produção na Prodesp será definida quando o ambiente for conhecido.** O portal é **sub-path-agnóstico** (`FORCE_SCRIPT_NAME`), então se adapta a `index.php`, Caddy, nginx ou ao que a Prodesp oferecer — o que importa é o **contrato da borda**: repassar `Host`/`X-Forwarded-*`, servir sob o sub-path e não redirecionar.
4. **`/manager` (curadoria) não é público** — restringir na borda em uso.

## Consequências

- Homologação e produção podem ter bordas distintas sem quebrar o app, desde que o contrato acima seja respeitado.
- A peça crítica de homologação (`index.php`) passa a ter versão e origem reproduzível.
- O Caddy fica documentado como opção, sem prometer ser o caminho da Prodesp.
