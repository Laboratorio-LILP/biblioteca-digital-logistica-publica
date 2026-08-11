#!/bin/bash
# Cria/atualiza a role read-only do portal Django (garante que o portal nunca
# escreve no Nou-Rau). Roda no init do Postgres (docker-entrypoint-initdb.d),
# lendo a senha do AMBIENTE — sem segredo hardcoded no repositório.
set -euo pipefail
: "${PORTAL_DB_PASSWORD:?defina PORTAL_DB_PASSWORD no .env}"

# A senha (:'pw') e o nome do banco (:"db") são interpolados pelo psql FORA do
# bloco $$...$$ (psql não substitui variáveis dentro de dollar-quoting). O DO
# block só cria a role sem senha; o ALTER seguinte define/rotaciona a senha.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v pw="$PORTAL_DB_PASSWORD" -v db="$POSTGRES_DB" <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'portal_reader') THEN
        CREATE ROLE portal_reader WITH LOGIN;
    END IF;
END
$$;
ALTER ROLE portal_reader WITH LOGIN PASSWORD :'pw';
GRANT CONNECT ON DATABASE :"db" TO portal_reader;
GRANT USAGE ON SCHEMA public TO portal_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO portal_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO portal_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO portal_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO portal_reader;
SQL
