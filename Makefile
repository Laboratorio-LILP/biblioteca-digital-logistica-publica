.PHONY: up down logs shell migrate migrate-dry validate enrich test backup restore restore-files clean a11y-check collectstatic prod-up prod-down prod-logs prod-rebuild

COMPOSE = docker compose --env-file .env -f docker/docker-compose.yml

# Ambiente de desenvolvimento
up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

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
	$(COMPOSE) exec portal python manage.py shell

# Migração de dados (uso: make migrate FILE=/caminho/planilha.xlsx)
migrate:
	$(COMPOSE) exec portal python manage.py migrate_spreadsheet $(FILE)

# Migração dry-run
migrate-dry:
	$(COMPOSE) exec portal python manage.py migrate_spreadsheet $(FILE) --dry-run

# Validação pós-importação
validate:
	$(COMPOSE) exec portal python manage.py validate_import

# Enriquecimento de metadados via IA
enrich:
	$(COMPOSE) exec portal python manage.py enrich_metadata

# Testes: ruff + pytest num contêiner com o MESMO Python e o mesmo lock da
# imagem, mais as ferramentas de teste (estágio `test` do Dockerfile — a imagem
# de execução não leva pytest), sobre o working tree montado em /src. Não
# depende da stack estar no ar nem de Python no host.
test:
	docker build --target test -t lilp-bdlp-portal-test -f docker/portal/Dockerfile .
	docker run --rm -v "$(CURDIR)":/src -w /src/portal -e DJANGO_SECRET_KEY=teste-local-sem-valor -e PYTHONPATH=/src/portal -e PYTHONDONTWRITEBYTECODE=1 lilp-bdlp-portal-test sh -c "ruff check . && python -m pytest -q -p no:cacheprovider"

# Backup: banco em formato custom (-Fc, o único que o pg_restore sabe limpar —
# um .sql em texto restaurado por cima de banco cheio dá 117 erros e não desfaz
# nada; medido em 26/08 e em 23/09/2026) + arquivos da curadoria (volume
# nourau_data, montado no portal em /nourau). -T desliga o TTY: saída binária.
# Cada arquivo nasce como .part e só ganha o nome final se o comando sair 0 —
# nunca fica um arquivo truncado com cara de backup válido.
backup:
	@ts=$$(date +%Y%m%d_%H%M%S); f=backup_$$ts.dump; a=backup_$${ts}_arquivos.tgz; \
	if $(COMPOSE) exec -T postgres pg_dump -U php -Fc nourau > $$f.part; then \
		mv $$f.part $$f; echo "Banco:    $$f ($$(wc -c < $$f | tr -d ' ') bytes)"; \
	else rm -f $$f.part; echo "ERRO: backup do banco NÃO gerado. A stack está no ar? ($(COMPOSE) ps)"; exit 1; fi; \
	if $(COMPOSE) exec -T portal tar czf - -C /nourau . > $$a.part; then \
		mv $$a.part $$a; echo "Arquivos: $$a ($$(wc -c < $$a | tr -d ' ') bytes)"; \
	else rm -f $$a.part; echo "ERRO: backup dos arquivos NÃO gerado."; exit 1; fi; \
	echo "Guarde os dois juntos. Restaurar: make restore FILE=$$f && make restore-files FILE=$$a"

# Restaurar o banco (uso: make restore FILE=backup_AAAAMMDD_HHMMSS.dump).
# --clean --if-exists derruba cada objeto antes de recriar; --single-transaction
# faz tudo-ou-nada (sem ele, uma falha no meio deixa o banco pela metade). NÃO
# acrescentar --no-acl: descartaria os GRANTs do portal_reader e o portal daria
# 500. Depois do restore, a role de leitura é (re)criada com a senha do ambiente
# do contêiner (09) e perde de novo a leitura de `users` (10): o restore recria a
# tabela e os privilégios padrão a devolveriam ao portal.
restore:
	@test -n "$(FILE)" || { echo "Uso: make restore FILE=backup_AAAAMMDD_HHMMSS.dump"; exit 1; }
	@test -f "$(FILE)" || { echo "Arquivo não encontrado: $(FILE)"; exit 1; }
	$(COMPOSE) exec -T postgres pg_restore -U php -d nourau --clean --if-exists --no-owner --single-transaction < $(FILE)
	$(COMPOSE) exec -T postgres bash -s < docker/postgres/init/09-portal-readonly-user.sh
	$(COMPOSE) exec -T postgres psql -U php -d nourau -v ON_ERROR_STOP=1 -q < docker/postgres/init/10-portal-readonly-revoke-users.sql
	@echo "Banco restaurado de $(FILE); leitura de users revogada do portal. Confira com: make validate"

# Restaurar os arquivos da curadoria (uso: make restore-files FILE=backup_AAAAMMDD_HHMMSS_arquivos.tgz).
# Escreve pelo contêiner do Nou-Rau (no portal o volume é só leitura).
restore-files:
	@test -n "$(FILE)" || { echo "Uso: make restore-files FILE=backup_AAAAMMDD_HHMMSS_arquivos.tgz"; exit 1; }
	@test -f "$(FILE)" || { echo "Arquivo não encontrado: $(FILE)"; exit 1; }
	$(COMPOSE) exec -T nourau tar xzf - -C /nourau < $(FILE)
	@echo "Arquivos restaurados de $(FILE)."

# Limpar volumes e containers
clean:
	$(COMPOSE) down -v --remove-orphans

# Coleta de estáticos (whitenoise + manifest) — útil para validar paths antes do deploy
collectstatic:
	$(COMPOSE) exec portal python manage.py collectstatic --noinput

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
	http://localhost:8000/metodologia/ \
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
	dbq="$(COMPOSE) exec -T postgres psql -U php nourau -t -A -c"; \
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
