#!/usr/bin/env bash
# Túnel de desenvolvedor (Microsoft Dev Tunnels) para homologação da BDLP.
#
# Expõe o portal local (127.0.0.1:$PORTAL_PORT) em uma URL https pública
# que EXIGE login Microsoft. Só contas do mesmo tenant corporativo do
# operador conseguem acessar — nunca acesso anônimo.
#
# Uso:        make tunnel        (ou: bash tools/tunnel.sh)
# Encerrar:   Ctrl+C — o site sai do ar na hora; nada fica exposto.
# Requisito:  brew install --cask devtunnel  +  devtunnel user login
#             (login com a conta Microsoft CORPORATIVA: a liberação é por tenant)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TUNNEL_ID="${BDLP_TUNNEL_ID:-bdlp-homolog}"

# Porta do portal: respeita override no .env (ex.: 8001 na máquina do bcgsantos).
PORT="$(grep -E '^PORTAL_PORT=' "$ROOT/.env" 2>/dev/null | cut -d= -f2 || true)"
PORT="${PORT:-8000}"

if ! command -v devtunnel >/dev/null 2>&1; then
    echo "ERRO: devtunnel não encontrado. Instale com: brew install --cask devtunnel" >&2
    exit 1
fi

if devtunnel user show 2>/dev/null | grep -q "Not logged in"; then
    echo "ERRO: faça login primeiro com a conta Microsoft corporativa:" >&2
    echo "    devtunnel user login" >&2
    exit 1
fi

# O portal precisa estar no ar antes de abrir o túnel.
if ! curl -sf -o /dev/null "http://127.0.0.1:${PORT}/"; then
    echo "ERRO: portal não responde em http://127.0.0.1:${PORT}/ — rode 'make up' antes." >&2
    exit 1
fi

# Cria o túnel uma única vez (persiste na conta; o serviço o apaga após alguns
# dias sem uso — 4d nesta conta — e aí este bloco o recria com URL NOVA).
# Porta e acesso são configurados junto com a criação.
if ! devtunnel show "$TUNNEL_ID" >/dev/null 2>&1; then
    echo "→ Criando túnel '$TUNNEL_ID'..."
    devtunnel create "$TUNNEL_ID"
    # Host/Origin originais preservados: o Django valida o host público real
    # via ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS (.devtunnels.ms) — sem isso o
    # túnel reescreveria ambos para "localhost".
    devtunnel port create "$TUNNEL_ID" -p "$PORT" --protocol http \
        --host-header unchanged --origin-header unchanged
    # Libera leitura para qualquer conta do MESMO tenant Microsoft do operador.
    # Sem --anonymous: quem não estiver logado no tenant não entra.
    devtunnel access create "$TUNNEL_ID" --tenant
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Túnel ativo. Envie à equipe a URL 'Connect via browser' abaixo."
echo "  Acesso: somente contas Microsoft do tenant corporativo."
echo "  Para encerrar: Ctrl+C (o site sai do ar imediatamente)."
echo "════════════════════════════════════════════════════════════════"
echo ""

exec devtunnel host "$TUNNEL_ID"
