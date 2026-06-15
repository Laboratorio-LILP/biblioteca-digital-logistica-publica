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

# Nº de conexões de host. String vazia = leitura indefinida (API/rede).
host_conns() {
    devtunnel show "$TUNNEL_ID" 2>/dev/null \
        | awk -F: '/Host connections/{gsub(/[^0-9]/,"",$2); print $2}'
}

conns="$(host_conns)"

# Saudável: silencioso, para não poluir o log a cada ciclo.
[ -n "$conns" ] && [ "$conns" -ge 1 ] 2>/dev/null && exit 0

# Leitura ambígua (vazia): não age — reiniciar às cegas causaria flapping.
if [ -z "$conns" ]; then
    echo "$(ts) leitura indefinida (API/rede?) — sem ação" >> "$LOG"
    exit 0
fi

# Conexões = 0. Antes de reiniciar, CONFIRMA após uma pausa: absorve a janela
# de arranque (host recém-iniciado ainda no handshake, no login/reboot) e
# blips em que o próprio host reconecta sozinho. Só reinicia se persistir.
sleep 25
conns2="$(host_conns)"
if [ -z "$conns2" ] || { [ "$conns2" -ge 1 ] 2>/dev/null; }; then
    exit 0  # recuperou sozinho ou leitura ambígua — não mexe
fi

echo "$(ts) Host connections=0 confirmado (2 leituras) — host zumbi; reiniciando $LABEL" >> "$LOG"
launchctl kickstart -k "gui/$(id -u)/${LABEL}" >> "$LOG" 2>&1 \
    && echo "$(ts) kickstart enviado" >> "$LOG" \
    || echo "$(ts) FALHA no kickstart (serviço instalado? login válido?)" >> "$LOG"
