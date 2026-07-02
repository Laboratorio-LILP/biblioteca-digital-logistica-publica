# ADR 0007 — Canal de homologação

- **Status:** Aceito (2026-06-16) · **Atualizado (2026-07-02):** parte revogada — ver nota abaixo

> **Nota de status (2026-07-02):** a parte desta decisão que admitia Dev Tunnels como canal
> auxiliar está **revogada**. A reunião da CTI-SGC-SGGD de 30/06/2026 (registrada no **ADR-006
> da vault do LILP**) proscreveu túneis e qualquer mecanismo de exposição externa do ambiente
> interno; o mecanismo desta frente (túnel como serviço + watchdog) foi desmontado e seus
> artefatos (`make tunnel-*`, `tools/tunnel*.sh`, os `*.plist.in` e `docs/tunel-homologacao.md`)
> foram **removidos do working tree** em 2026-07. Os commits de origem permanecem no histórico
> git por decisão deliberada (registro histórico, sem reescrita) — isso **não autoriza
> restauração**: ver o bloco "Limites de segurança — inegociáveis" no `CLAUDE.md` da raiz.
> O canal canônico permanece a VM acessada **exclusivamente via VPN**; a subida dev→homologação
> passa a ser por esteira GitHub Actions sobre o Git corporativo (em validação).
- **Contexto:** A homologação é servida por uma VM on-premise da SGGD, acessível pela rede corporativa/VPN, com o stack `lilp-bdlp` em loopback atrás do front-controller `index.php` (`/Biblioteca`). Houve experimentos com Microsoft Dev Tunnels (a partir de máquina pessoal) para acesso sem VPN — um canal de conveniência, não o canônico, com dependência de fornecedor e ponto único na máquina do dev.

## Decisão

- O canal **canônico de homologação é a VM on-premise** (`bdlp-vm`), em loopback, exposta só na `:80` via Apache/`index.php`.
- Dev Tunnels é **auxiliar/temporário** (demo/acesso pontual), nunca o caminho de homologação oficial; quando usado, exige `DJANGO_DEBUG=false` e `CSRF_TRUSTED_ORIGINS`/`ALLOWED_HOSTS` ajustados.

## Consequências

- A homologação reflete a topologia de produção (proxy + sub-path + loopback), não a de um túnel de laptop.
- Riscos do túnel (fornecedor, plano gratuito, máquina pessoal) ficam documentados e fora do caminho crítico.
