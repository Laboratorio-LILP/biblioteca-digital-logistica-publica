.PHONY: up down logs shell migrate migrate-dry validate enrich test backup restore clean a11y-check collectstatic prod-up prod-down prod-logs prod-rebuild

# Ambiente de desenvolvimento
up:
	docker compose --env-file .env -f docker/docker-compose.yml up -d

down:
	docker compose --env-file .env -f docker/docker-compose.yml down

logs:
	docker compose --env-file .env -f docker/docker-compose.yml logs -f

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
# Executa pa11y contra home, busca, coleções, sobre e as 6 páginas legais, MAIS
# uma página de documento e uma de coleção descobertas dinamicamente no banco
# (código/id variam por dados — URL chumbada quebraria no re-seed). Se o banco
# estiver fora, essas duas são puladas com aviso.
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
	@urls="$(A11Y_URLS)"; \
	dbq="docker compose --env-file .env -f docker/docker-compose.yml exec -T postgres psql -U php nourau -t -A -c"; \
	code=$$($$dbq "SELECT code FROM nr_document WHERE status='a' AND code <> '' ORDER BY id LIMIT 1;" 2>/dev/null | tr -d '[:space:]'); \
	if [ -n "$$code" ]; then urls="$$urls http://localhost:8000/documento/$$code/"; \
	else echo "  (aviso: documento amostra não encontrado — /documento/ não testado)"; fi; \
	topic=$$($$dbq "SELECT id FROM topic WHERE parent_id=0 ORDER BY id LIMIT 1;" 2>/dev/null | tr -d '[:space:]'); \
	if [ -n "$$topic" ]; then urls="$$urls http://localhost:8000/colecao/$$topic/"; \
	else echo "  (aviso: coleção amostra não encontrada — /colecao/ não testado)"; fi; \
	for url in $$urls; do \
		echo ""; echo "==> $$url"; \
		npx --yes pa11y --standard WCAG2AA "$$url" || true; \
	done
