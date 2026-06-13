.PHONY: up down logs tunnel tunnel-service tunnel-service-off tunnel-url shell migrate migrate-dry validate enrich test backup restore clean a11y-check collectstatic prod-up prod-down prod-logs prod-rebuild

# Ambiente de desenvolvimento
up:
	docker compose --env-file .env -f docker/docker-compose.yml up -d

down:
	docker compose --env-file .env -f docker/docker-compose.yml down

logs:
	docker compose --env-file .env -f docker/docker-compose.yml logs -f

# Túnel de homologação sem VPN (Microsoft Dev Tunnels, login corporativo).
# Detalhes e troubleshooting: docs/tunel-homologacao.md
tunnel:
	bash tools/tunnel.sh

# Túnel como serviço do macOS (launchd): sobe no login e reinicia se cair.
# Não precisa de terminal aberto. Logs: ~/Library/Logs/bdlp-tunnel.log
# O script roda de uma cópia em ~/Library/Application Support (o launchd não
# lê a pasta Desktop — TCC). Rode de novo após alterar tools/tunnel.sh.
TUNNEL_PLIST = $(HOME)/Library/LaunchAgents/br.gov.sp.lilp.bdlp-tunnel.plist
TUNNEL_APPDIR = $(HOME)/Library/Application Support/lilp-bdlp
tunnel-service:
	@mkdir -p "$(TUNNEL_APPDIR)" $(HOME)/Library/LaunchAgents $(HOME)/Library/Logs
	install -m 755 tools/tunnel.sh "$(TUNNEL_APPDIR)/tunnel.sh"
	sed -e "s|@SCRIPT@|$(TUNNEL_APPDIR)/tunnel.sh|g" -e "s|@HOME@|$(HOME)|g" \
	    -e "s|@PORT@|$$( (grep -E '^PORTAL_PORT=' .env 2>/dev/null | cut -d= -f2 | grep . ) || echo 8000)|g" \
	    tools/bdlp-tunnel.plist.in > $(TUNNEL_PLIST)
	-launchctl bootout gui/$$(id -u)/br.gov.sp.lilp.bdlp-tunnel 2>/dev/null
	launchctl bootstrap gui/$$(id -u) $(TUNNEL_PLIST)
	@echo "Serviço ativo. URL em alguns segundos via: make tunnel-url"

tunnel-service-off:
	-launchctl bootout gui/$$(id -u)/br.gov.sp.lilp.bdlp-tunnel 2>/dev/null
	rm -f $(TUNNEL_PLIST) "$(TUNNEL_APPDIR)/tunnel.sh"
	@echo "Serviço removido — o túnel está fora do ar."

# URL pública atual do túnel (muda se o túnel expirar e for recriado)
tunnel-url:
	@devtunnel show $${BDLP_TUNNEL_ID:-bdlp-homolog} 2>/dev/null | grep -o 'https://[a-z0-9-]*\.[a-z0-9]*\.devtunnels\.ms[^ ]*' | head -1 || echo "Túnel não encontrado — rode make tunnel-service (ou make tunnel)."

# Ambiente de produção (Caddy + HTTPS Let's Encrypt). Requer DOMAIN no .env.
prod-up:
	docker compose --env-file .env -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d --build

prod-down:
	docker compose --env-file .env -f docker/docker-compose.yml -f docker/docker-compose.prod.yml down

prod-logs:
	docker compose --env-file .env -f docker/docker-compose.yml -f docker/docker-compose.prod.yml logs -f --tail 100

prod-rebuild:
	docker compose --env-file .env -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d --build portal

shell:
	docker compose --env-file .env -f docker/docker-compose.yml exec portal python manage.py shell

# Migração de dados (uso: make migrate FILE=/caminho/planilha.xlsx)
migrate:
	docker compose --env-file .env -f docker/docker-compose.yml exec portal python manage.py migrate_spreadsheet $(FILE)

# Migração dry-run
migrate-dry:
	docker compose --env-file .env -f docker/docker-compose.yml exec portal python manage.py migrate_spreadsheet $(FILE) --dry-run

# Validação pós-importação
validate:
	docker compose --env-file .env -f docker/docker-compose.yml exec portal python manage.py validate_import

# Enriquecimento de metadados via IA
enrich:
	docker compose --env-file .env -f docker/docker-compose.yml exec portal python manage.py enrich_metadata

# Testes
test:
	docker compose --env-file .env -f docker/docker-compose.yml exec portal python -m pytest

# Backup do banco de dados
backup:
	docker compose --env-file .env -f docker/docker-compose.yml exec postgres pg_dump -U php nourau > backup_$$(date +%Y%m%d_%H%M%S).sql

# Restaurar banco de dados
restore:
	@echo "Uso: cat backup.sql | docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php nourau"

# Limpar volumes e containers
clean:
	docker compose --env-file .env -f docker/docker-compose.yml down -v --remove-orphans

# Coleta de estáticos (whitenoise + manifest) — útil para validar paths antes do deploy
collectstatic:
	docker compose --env-file .env -f docker/docker-compose.yml exec portal python manage.py collectstatic --noinput

# Verificação de acessibilidade WCAG 2.0 AA — requer Node 18+ no host (npx pa11y).
# Executa pa11y contra a home, busca, detalhe (placeholder) e as 6 páginas legais.
# Para usar com Docker em vez de npx local, troque a chamada por:
#   docker run --rm --network host pa11y/pa11y-ci $(A11Y_URLS)
A11Y_URLS = \
	http://localhost:8000/ \
	http://localhost:8000/busca/ \
	http://localhost:8000/colecoes/ \
	http://localhost:8000/sobre/ \
	http://localhost:8000/transparencia/ \
	http://localhost:8000/acessibilidade/ \
	http://localhost:8000/politica-de-privacidade/ \
	http://localhost:8000/politica-de-cookies/ \
	http://localhost:8000/mapa-do-site/ \
	http://localhost:8000/fale-conosco/

a11y-check:
	@echo "Verificando acessibilidade WCAG 2.0 AA com pa11y..."
	@for url in $(A11Y_URLS); do \
		echo ""; echo "==> $$url"; \
		npx --yes pa11y --standard WCAG2AA "$$url" || true; \
	done
