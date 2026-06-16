# Inventário de portas da VM de homologação

Mapa de portas da VM de homologação on-premise da SGGD (hostname `vademecumlicitacoes`), referenciado pelo [ADR 0008](adr/0008-portas-loopback.md).

**Postura de segurança:** todos os serviços do BDLP escutam em **loopback** (`127.0.0.1`); a **única porta pública é a `:80`** (a borda `index.php`/Apache, ver `deploy/edge/`). O `ufw` está inativo — a proteção depende do perímetro da SGGD (o firewall externo libera só a `:80`).

## Stack BDLP (`lilp-bdlp`) — homologação

| Porta | Serviço | Observação |
|---|---|---|
| `127.0.0.1:8010` | portal (Django/gunicorn) | busca/facetas; alcançado pela borda por loopback |
| `127.0.0.1:8082` | nourau (PHP) | catálogo/curadoria; `/manager/` é o admin |
| `127.0.0.1:5433` | postgres | full-text search; roles `portal_reader` (RO) e `php` (admin) |
| `:80` (**pública**) | Apache + `index.php` | **única porta pública**; borda/proxy reverso → subcaminho `/Biblioteca/` |

## Dev local (defaults)

Portal `8000` · nourau `8080` · postgres `5432`. Exceção conhecida: `PORTAL_PORT=8001` no Windows do escritório (a `8000` é reservada pelo kernel).

## Produção (Caddy — referência, a definir na Prodesp)

Os serviços internos **não** publicam portas no host; o Caddy (`:80`/`:443`) os alcança pela rede interna do Compose.

## Serviços de TERCEIROS na VM — FORA DE ESCOPO, NÃO TOCAR

A VM é compartilhada. Estes serviços **não** são do BDLP; ficam aqui só para transparência (expostos em `0.0.0.0`, alcançáveis apenas no mesmo segmento).

| Porta | Serviço | Observação |
|---|---|---|
| `3306` | MySQL/MariaDB (XAMPP) | o BDLP usa Postgres, não isto |
| `21` | FTP/ProFTPD (XAMPP) | texto puro; provável default ligado à toa |
| `8080` | vademecum_node | projeto separado |
| `10050` | Zabbix agent | monitoramento |
| `22` | SSH | acesso à VM (necessário) |
| `443` | Apache-SSL | não alcançável pelo perímetro (só a `:80` é liberada) |
