# ADR 0007 — Canal de homologação

- **Status:** Aceito (2026-06-16)
- **Contexto:** A homologação é servida por uma VM on-premise da SGGD (`vademecumlicitacoes`), acessível pela rede corporativa/VPN, com o stack `lilp-bdlp` em loopback atrás do front-controller `index.php` (`/Biblioteca`). Houve experimentos com Microsoft Dev Tunnels (a partir de máquina pessoal) para acesso sem VPN — um canal de conveniência, não o canônico, com dependência de fornecedor e ponto único na máquina do dev.

## Decisão

- O canal **canônico de homologação é a VM on-premise** (`bdlp-vm`), em loopback, exposta só na `:80` via Apache/`index.php`.
- Dev Tunnels é **auxiliar/temporário** (demo/acesso pontual), nunca o caminho de homologação oficial; quando usado, exige `DJANGO_DEBUG=false` e `CSRF_TRUSTED_ORIGINS`/`ALLOWED_HOSTS` ajustados.

## Consequências

- A homologação reflete a topologia de produção (proxy + sub-path + loopback), não a de um túnel de laptop.
- Riscos do túnel (fornecedor, plano gratuito, máquina pessoal) ficam documentados e fora do caminho crítico.
