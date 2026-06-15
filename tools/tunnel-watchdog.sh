#!/usr/bin/env bash
# Watchdog do túnel de homologação. Roda a cada poucos minutos (LaunchAgent
# com StartInterval) e cobre a falha que o KeepAlive do launchd NÃO cobre:
# o processo `devtunnel host` vivo mas sem conexão com o relay — o "host
# zumbi" (token de auth expirado, relay derrubado). Sinal de saúde correto:
# nº de conexões de host >= 1. Se cair a 0, reinicia o serviço do túnel.
set -uo pipefail

TUNNEL_ID="${BDLP_TUNNEL_ID:-bdlp-homolog}"
LABEL="br.gov.sp.lilp.bdlp-tunnel"
LOG="${HOME}/Library/Logs/bdlp-tunnel-watchdog.log"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

# Lê o nº de conexões de host. Só age com leitura DEFINITIVA de 0.
# Saída vazia/erro (hiccup de API, rede) → não faz nada: reiniciar às cegas
# por causa de uma leitura ambígua causaria flapping desnecessário.
conns="$(devtunnel show "$TUNNEL_ID" 2>/dev/null \
    | awk -F: '/Host connections/{gsub(/[^0-9]/,"",$2); print $2}')"

if [ -z "$conns" ]; then
    echo "$(ts) leitura indefinida (API/rede?) — sem ação" >> "$LOG"
    exit 0
fi

if [ "$conns" -ge 1 ] 2>/dev/null; then
    exit 0  # saudável — silencioso, para não poluir o log a cada ciclo
fi

echo "$(ts) Host connections=$conns — host zumbi; reiniciando $LABEL" >> "$LOG"
launchctl kickstart -k "gui/$(id -u)/${LABEL}" >> "$LOG" 2>&1 \
    && echo "$(ts) kickstart enviado" >> "$LOG" \
    || echo "$(ts) FALHA no kickstart (serviço instalado? login válido?)" >> "$LOG"
