# ADR 0008 — Portas em loopback e mapa de portas

- **Status:** Aceito (2026-06-16) — substitui a orientação anterior (ADR-004) de expor a web em endereço público.
- **Contexto:** Após o endurecimento, todos os serviços do stack passaram a publicar portas apenas em `127.0.0.1`. Só a borda (Apache/`index.php` na `:80`, ou Caddy `:80/:443` em produção) é pública. O ADR-004 prescrevia a web em endereço público, contradizendo o piloto.

## Decisão

- **Loopback total** para postgres/nourau/portal em dev e homologação: `127.0.0.1:<porta>`. Exposição pública só pela borda.
- Em produção (Caddy), os serviços internos não publicam portas no host — o Caddy os alcança pela rede interna do Compose.
- Mapa de portas de homologação (VM): portal `8010`, nourau `8082`, postgres `5433`. Dev local usa os defaults (`8000`/`8080`/`5432`), salvo conflito (ex.: `PORTAL_PORT=8001` quando a `8000` está reservada).

## Consequências

- Defesa em profundidade: a superfície pública independe do firewall de borda.
- O ADR-004 fica superado neste ponto; o mapa de portas é registrado aqui e em `docs/VM-PORT-INVENTORY.md`.
