--
-- Extensões e configurações de busca do banco (roda antes dos demais inits).
--
-- unaccent + portuguese_unaccent: busca sem acento (T4, set/2026). A
-- configuração COPIA a `portuguese` e só acrescenta o filtro unaccent nas
-- palavras — o radicalizador português continua o mesmo. O portal soma as
-- duas configurações (vetor e consulta) em portal/catalog/search.py, porque
-- aplicar unaccent ANTES do stemmer muda o radical ("licitações" → "licitaco"
-- ≠ "licitação" → "licitaca"); só a soma das duas preserva plural/flexão.
--
-- Bancos EXISTENTES não rodam este init: a mesma criação está na seção 1 de
-- docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql. O init roda
-- como POSTGRES_USER (dono do banco); portal_reader só precisa de SELECT.
--

CREATE EXTENSION IF NOT EXISTS unaccent;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'portuguese_unaccent') THEN
        CREATE TEXT SEARCH CONFIGURATION portuguese_unaccent (COPY = portuguese);
        ALTER TEXT SEARCH CONFIGURATION portuguese_unaccent
            ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem;
    END IF;
END
$$;
