--
-- Taxonomia v12 + busca sem acento — migração para bancos EXISTENTES
-- (o volume de desenvolvimento e o de homologação não rodam o init de novo).
--
-- Como executar (dentro do contêiner do Postgres, como o dono do banco):
--   psql -U php -d nourau -v ON_ERROR_STOP=1 < docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql
--   (na stack local: docker compose --env-file .env -f docker/docker-compose.yml \
--        exec -T postgres psql -U php -d nourau -v ON_ERROR_STOP=1 < <este arquivo>)
--
-- O arquivo tem DUAS seções e pode ser executado quantas vezes for preciso
-- (guardas WHERE NOT EXISTS / ON CONFLICT DO NOTHING / IS DISTINCT FROM):
--
--   SEÇÃO 1 — aditiva, segura a qualquer momento (antes ou depois da recarga):
--     • extensão unaccent + configuração de busca portuguese_unaccent (T4);
--     • subcoleções (topic) e tipos (type_information) novos: Acórdãos e
--       Deliberações sob Jurisprudência; Enunciados sob Doutrina;
--     • topic_path/topic_users/topic_type das subcoleções novas;
--     • os 2 Assuntos novos (ordem 15 e 16);
--     • renomeia as 4 subcategorias de Planejamento (nome + slug);
--     • descrições das coleções raiz sem "documentos normativos"/"vídeos";
--     • (30/09) coluna gerada `busca` + índice GIN para a busca textual;
--     • (30/09) REVOKE da tabela users para a role de leitura do portal.
--
--   SEÇÃO 2 — pós-recarga, GUARDADA: remove as subcoleções e os tipos retirados
--     (Documentos Normativos, Vídeos e — v12.1, 23/09/2026 — Pareceres) e o
--     Enunciados antigo sob Jurisprudência
--     SOMENTE se nenhum nr_document (qualquer status) os referenciar. Se ainda
--     houver documento, não faz nada e imprime aviso (RAISE NOTICE).
--
-- Ordem recomendada: seção 1 → subida do código v12 → full-refresh do acervo
-- com a planilha v12 e `--skip-red` → validate_import → seção 2 (este arquivo
-- de novo; a seção 1 é inócua na segunda passagem).
--
-- Espelha os seeds de volume novo: 00-extensions.sql, 06-collections.sql,
-- 06-taxonomia.sql, 07-categories.sql e 08-type-information.sql.
--

-- ===========================================================================
-- SEÇÃO 1 — aditiva (idempotente)
-- ===========================================================================

-- 1.1 Busca sem acento: extensão + configuração que copia a `portuguese` e
--     acrescenta unaccent nas palavras (o stemmer continua o mesmo).
CREATE EXTENSION IF NOT EXISTS unaccent;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'portuguese_unaccent') THEN
        CREATE TEXT SEARCH CONFIGURATION portuguese_unaccent (COPY = portuguese);
        ALTER TEXT SEARCH CONFIGURATION portuguese_unaccent
            ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem;
        RAISE NOTICE 'seção 1: configuração de busca portuguese_unaccent criada';
    END IF;
END
$$;

-- 1.2 Subcoleções novas (topic) — Jurisprudência: Acórdãos, Deliberações.
INSERT INTO topic (name, description, parent_id, archieve)
SELECT v.name, v.description, r.id, 's'
FROM (VALUES
    ('Acórdãos', 'Acórdãos de tribunais e cortes de contas'),
    ('Deliberações', 'Deliberações de tribunais e órgãos de controle')
) AS v(name, description)
JOIN topic r ON r.parent_id = 0 AND r.name = 'Jurisprudência'
WHERE NOT EXISTS (SELECT 1 FROM topic t WHERE t.parent_id = r.id AND t.name = v.name);

-- 1.3 Subcoleção nova (topic) — Doutrina: Enunciados. (Pareceres, criado pela
--     v12 de 11/09, saiu na v12.1 de 23/09/2026: a seção 2 o remove.)
INSERT INTO topic (name, description, parent_id, archieve)
SELECT v.name, v.description, r.id, 's'
FROM (VALUES
    ('Enunciados', 'Enunciados')
) AS v(name, description)
JOIN topic r ON r.parent_id = 0 AND r.name = 'Doutrina e Conteúdo Técnico'
WHERE NOT EXISTS (SELECT 1 FROM topic t WHERE t.parent_id = r.id AND t.name = v.name);

-- 1.4 topic_path das subcoleções que ainda não têm caminho (as novas) e
--     correção de parent_names/parent_ids desatualizados.
INSERT INTO topic_path (topic_id, parent_ids, parent_names)
SELECT s.id, '0,' || p.id, p.name || '/' || s.name
FROM topic s
JOIN topic p ON s.parent_id = p.id
WHERE p.parent_id = 0
  AND NOT EXISTS (SELECT 1 FROM topic_path tp WHERE tp.topic_id = s.id);

UPDATE topic_path tp
SET parent_ids = '0,' || p.id,
    parent_names = p.name || '/' || s.name
FROM topic s
JOIN topic p ON s.parent_id = p.id
WHERE tp.topic_id = s.id
  AND p.parent_id = 0
  AND (tp.parent_names IS DISTINCT FROM p.name || '/' || s.name
       OR tp.parent_ids IS DISTINCT FROM '0,' || p.id);

-- 1.5 Painel /manager do Nou-Rau filtra topics por topic_users: vincula todos
--     os usuários às subcoleções NOVAS (as que ainda não têm nenhum vínculo),
--     mesmo critério do seed — sem mexer em vínculos já ajustados à mão.
INSERT INTO topic_users (users_id, topic_id)
SELECT u.id, t.id FROM users u CROSS JOIN topic t
WHERE NOT EXISTS (SELECT 1 FROM topic_users tu WHERE tu.topic_id = t.id)
ON CONFLICT (users_id, topic_id) DO NOTHING;

-- 1.6 Tipos de informação novos (Enunciados costuma já existir).
INSERT INTO type_information (name)
SELECT v.name FROM (VALUES ('Acórdãos'), ('Deliberações'), ('Enunciados')) AS v(name)
WHERE NOT EXISTS (SELECT 1 FROM type_information ti WHERE ti.name = v.name);

INSERT INTO topic_type (topic_id, type_id)
SELECT t.id, ti.id FROM topic t, type_information ti
WHERE t.parent_id = 0
ON CONFLICT (topic_id, type_id) DO NOTHING;

-- 1.7 Assuntos novos (ordem 15 e 16).
INSERT INTO nr_assunto (nome, slug, ordem) VALUES
    ('Gestão Estratégica e Desempenho das Contratações', 'gestao-estrategica-e-desempenho-das-contratacoes', 15),
    ('Logística Pública Internacional', 'logistica-publica-internacional', 16)
ON CONFLICT (nome) DO NOTHING;

-- 1.8 Subcategorias de Planejamento sem o prefixo "FASE PREPARATÓRIA - "
--     (nome + slug; as microcategorias seguem penduradas pelo id).
UPDATE nr_subcategoria SET nome = 'ETP', slug = 'etp'
 WHERE nome = 'FASE PREPARATÓRIA - ETP';
UPDATE nr_subcategoria SET nome = 'TR', slug = 'tr'
 WHERE nome = 'FASE PREPARATÓRIA - TR';
UPDATE nr_subcategoria SET nome = 'GESTÃO DE RISCOS', slug = 'gestao-de-riscos'
 WHERE nome = 'FASE PREPARATÓRIA - GESTÃO DE RISCOS';
UPDATE nr_subcategoria SET nome = 'PESQUISA DE PREÇOS', slug = 'pesquisa-de-precos'
 WHERE nome = 'FASE PREPARATÓRIA - PESQUISA DE PREÇOS';

-- 1.9 Descrições das coleções raiz coerentes com o vocabulário v12.
UPDATE topic SET description = 'Acórdãos, deliberações, súmulas e boletins'
 WHERE parent_id = 0 AND name = 'Jurisprudência'
   AND description IS DISTINCT FROM 'Acórdãos, deliberações, súmulas e boletins';
UPDATE topic SET description = 'Livros digitais, artigos, notas técnicas, relatórios, textos de discussão, resumos e enunciados'
 WHERE parent_id = 0 AND name = 'Doutrina e Conteúdo Técnico'
   AND description IS DISTINCT FROM 'Livros digitais, artigos, notas técnicas, relatórios, textos de discussão, resumos e enunciados';
UPDATE topic SET description = 'Manuais, guias, tutoriais, apostilas, aulas, cursos e slides'
 WHERE parent_id = 0 AND name = 'Instrução e Capacitação'
   AND description IS DISTINCT FROM 'Manuais, guias, tutoriais, apostilas, aulas, cursos e slides';

-- 1.10 Busca textual indexada (30/09/2026, auditoria F2-02): coluna GERADA
--      `busca` com o vetor da busca (campos e pesos de portal/catalog/fts.py,
--      nas configurações portuguese e portuguese_unaccent da 1.1) + índice GIN.
--      Espelha o seed 06-taxonomia.sql §5. Sem a coluna o portal ainda busca
--      (vetor calculado na consulta, mais lento) e avisa no log; com ela a home
--      e a busca deixam de varrer a tabela. Recriar a coluna se os campos ou os
--      pesos mudarem: DROP COLUMN busca e rodar de novo.
DROP INDEX IF EXISTS idx_nr_document_fts;
ALTER TABLE nr_document ADD COLUMN IF NOT EXISTS busca tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('portuguese', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('portuguese', coalesce(keywords, '')), 'A') ||
        setweight(to_tsvector('portuguese', coalesce(author, '')), 'B') ||
        setweight(to_tsvector('portuguese', coalesce(autor_principal, '')), 'B') ||
        setweight(to_tsvector('portuguese', coalesce(abstract, '')), 'C') ||
        setweight(to_tsvector('portuguese', coalesce(uso_futuro, '')), 'C') ||
        setweight(to_tsvector('portuguese', coalesce(metodo, '')), 'D') ||
        setweight(to_tsvector('portuguese', coalesce(resultado, '')), 'D') ||
        setweight(to_tsvector('portuguese', coalesce(complexidade, '')), 'D') ||
        setweight(to_tsvector('portuguese_unaccent', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('portuguese_unaccent', coalesce(keywords, '')), 'A') ||
        setweight(to_tsvector('portuguese_unaccent', coalesce(author, '')), 'B') ||
        setweight(to_tsvector('portuguese_unaccent', coalesce(autor_principal, '')), 'B') ||
        setweight(to_tsvector('portuguese_unaccent', coalesce(abstract, '')), 'C') ||
        setweight(to_tsvector('portuguese_unaccent', coalesce(uso_futuro, '')), 'C') ||
        setweight(to_tsvector('portuguese_unaccent', coalesce(metodo, '')), 'D') ||
        setweight(to_tsvector('portuguese_unaccent', coalesce(resultado, '')), 'D') ||
        setweight(to_tsvector('portuguese_unaccent', coalesce(complexidade, '')), 'D')
    ) STORED;
CREATE INDEX IF NOT EXISTS idx_nr_document_busca ON nr_document USING gin (busca);

-- 1.11 Role de leitura do portal sem acesso à tabela de credenciais do Nou-Rau
--      (30/09/2026, auditoria F2-05; Todoist p1 de 03/09). O init de volume novo
--      já faz isso (10-portal-readonly-revoke-users.sql); um banco existente não
--      passou por ele, e todo pg_restore recria a tabela `users` e reaplica os
--      privilégios padrão (ALTER DEFAULT PRIVILEGES … GRANT SELECT), devolvendo
--      a leitura ao portal. Rode esta seção depois de qualquer restore.
--      Guardada: se a role não existir (volume anterior ao PR #16), só avisa —
--      crie-a com docker/postgres/init/09-portal-readonly-user.sh.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'portal_reader') THEN
        REVOKE ALL ON TABLE users FROM portal_reader;
    ELSE
        RAISE NOTICE 'seção 1.11 — aviso: role portal_reader não existe; rode docker/postgres/init/09-portal-readonly-user.sh (o portal não sobe sem ela)';
    END IF;
END
$$;

-- ===========================================================================
-- SEÇÃO 2 — pós-recarga, guardada (só remove o que nenhum documento referencia)
-- ===========================================================================
-- Alvos: Jurisprudência/Documentos Normativos (topic + tipo), Jurisprudência/
-- Enunciados (só o topic — o tipo "Enunciados" continua, agora sob Doutrina) e
-- Instrução e Capacitação/Vídeos (topic + tipo) e — v12.1, 23/09/2026 — Doutrina e
-- Conteúdo Técnico/Pareceres (topic + tipo). Para cada alvo, conta em
-- nr_document (qualquer status) por topic_id e pelas duas colunas de tipo
-- (typeinform_id e typeinformation) e em supplementary_files por topic_id.
DO $$
DECLARE
    alvo RECORD;
    n_docs INT;
    n_sup INT;
BEGIN
    FOR alvo IN
        SELECT t.id AS topic_id, t.name AS topic_name, p.name AS root_name,
               CASE WHEN t.name IN ('Documentos Normativos', 'Vídeos', 'Pareceres') THEN t.name END AS type_name
        FROM topic t
        JOIN topic p ON p.id = t.parent_id AND p.parent_id = 0
        WHERE (p.name = 'Jurisprudência' AND t.name IN ('Documentos Normativos', 'Enunciados'))
           OR (p.name = 'Instrução e Capacitação' AND t.name = 'Vídeos')
           OR (p.name = 'Doutrina e Conteúdo Técnico' AND t.name = 'Pareceres')
    LOOP
        SELECT COUNT(*) INTO n_docs
          FROM nr_document d
         WHERE d.topic_id = alvo.topic_id
            OR (alvo.type_name IS NOT NULL AND (
                    d.typeinform_id IN (SELECT id FROM type_information WHERE name = alvo.type_name)
                 OR d.typeinformation IN (SELECT id FROM type_information WHERE name = alvo.type_name)));
        SELECT COUNT(*) INTO n_sup FROM supplementary_files sf WHERE sf.topic_id = alvo.topic_id;

        IF n_docs > 0 OR n_sup > 0 THEN
            RAISE NOTICE 'seção 2 — aviso: %/% ainda referenciado por % documento(s) e % arquivo(s) suplementar(es); nada removido (recarregue o acervo v12 antes)',
                alvo.root_name, alvo.topic_name, n_docs, n_sup;
        ELSE
            DELETE FROM topic_users WHERE topic_id = alvo.topic_id;
            DELETE FROM topic_type  WHERE topic_id = alvo.topic_id;
            DELETE FROM topic_path  WHERE topic_id = alvo.topic_id;
            DELETE FROM topic       WHERE id = alvo.topic_id;
            IF alvo.type_name IS NOT NULL THEN
                DELETE FROM topic_type WHERE type_id IN (SELECT id FROM type_information WHERE name = alvo.type_name);
                DELETE FROM type_information WHERE name = alvo.type_name;
            END IF;
            RAISE NOTICE 'seção 2: removido %/% (topic %)', alvo.root_name, alvo.topic_name, alvo.topic_id;
        END IF;
    END LOOP;
END
$$;
