--
-- Hierarquia de coleções (topics) da Biblioteca Digital de Logística Pública
-- Taxonomia v12 (set/2026): 4 Coleções definidas pelo Tipo de Informação.
-- Fonte: e-mail "ALTERAÇÕES BIBLIOTECA" (Lina, 11/09/2026) sobre a aba
-- "Coleção, Assunto e Natureza" do template. Jurisprudência = Súmulas, Boletins,
-- Acórdãos e Deliberações (saem Enunciados e Documentos Normativos); Doutrina
-- ganha Enunciados e Pareceres; Instrução perde Vídeos. Normas, leis, decretos e
-- portarias saem do acervo pela planilha, não por código.
-- Cada Tipo de Informação é semeado como subcoleção da sua Coleção, para que o
-- migrate_spreadsheet._resolve_topic() case a coluna "Coleção" → raiz e refine
-- pela coluna "Tipo de Informação" → subcoleção. Bancos EXISTENTES não rodam
-- este init: use docker/postgres/migrations/2026-09-v12-taxonomia-e-busca.sql.
-- Vocabulário espelhado em portal/catalog/taxonomy_v6.py (_TIPOS_POR_COLECAO).
--

-- Coleções principais (parent_id = 0 = raiz)
INSERT INTO topic (name, description, parent_id, archieve) VALUES
    ('Jurisprudência', 'Acórdãos, deliberações, súmulas e boletins', 0, 's');
INSERT INTO topic (name, description, parent_id, archieve) VALUES
    ('Trabalhos Acadêmicos', 'Teses, dissertações, monografias, TCCs e memoriais docentes', 0, 's');
INSERT INTO topic (name, description, parent_id, archieve) VALUES
    ('Doutrina e Conteúdo Técnico', 'Livros digitais, artigos, notas técnicas, relatórios, textos de discussão, resumos, enunciados e pareceres', 0, 's');
INSERT INTO topic (name, description, parent_id, archieve) VALUES
    ('Instrução e Capacitação', 'Manuais, guias, tutoriais, apostilas, aulas, cursos e slides', 0, 's');

-- Subcoleções = Tipos de Informação v12 (nomes EXATOS do vocabulário controlado)
INSERT INTO topic (name, description, parent_id, archieve)
SELECT sub.name, sub.description, t.id, 's'
FROM topic t,
(VALUES
    ('Súmulas', 'Súmulas'),
    ('Boletins', 'Boletins'),
    ('Acórdãos', 'Acórdãos de tribunais e cortes de contas'),
    ('Deliberações', 'Deliberações de tribunais e órgãos de controle')
) AS sub(name, description)
WHERE t.name = 'Jurisprudência' AND t.parent_id = 0;

INSERT INTO topic (name, description, parent_id, archieve)
SELECT sub.name, sub.description, t.id, 's'
FROM topic t,
(VALUES
    ('Teses', 'Teses de doutorado'),
    ('Dissertações', 'Dissertações de mestrado'),
    ('Monografias', 'Monografias'),
    ('TCCs', 'Trabalhos de conclusão de curso'),
    ('Memoriais Docentes', 'Memoriais de docentes e pesquisadores')
) AS sub(name, description)
WHERE t.name = 'Trabalhos Acadêmicos' AND t.parent_id = 0;

INSERT INTO topic (name, description, parent_id, archieve)
SELECT sub.name, sub.description, t.id, 's'
FROM topic t,
(VALUES
    ('Livros digitais', 'Livros e e-books em formato digital'),
    ('Artigos', 'Artigos técnicos e científicos'),
    ('Notas Técnicas', 'Notas técnicas'),
    ('Relatórios', 'Relatórios técnicos e de gestão'),
    ('Textos de Discussão', 'Textos para discussão e debate'),
    ('Resumos', 'Resumos'),
    ('Resumos expandidos', 'Resumos expandidos'),
    ('Enunciados', 'Enunciados'),
    ('Pareceres', 'Pareceres jurídicos e técnicos')
) AS sub(name, description)
WHERE t.name = 'Doutrina e Conteúdo Técnico' AND t.parent_id = 0;

INSERT INTO topic (name, description, parent_id, archieve)
SELECT sub.name, sub.description, t.id, 's'
FROM topic t,
(VALUES
    ('Manuais', 'Manuais técnicos e operacionais'),
    ('Guias', 'Guias práticos'),
    ('Tutoriais', 'Tutoriais e guias passo a passo'),
    ('Apostilas', 'Apostilas e materiais didáticos'),
    ('Aulas', 'Aulas e apresentações'),
    ('Cursos', 'Cursos e programas de capacitação'),
    ('Slides', 'Apresentações em slides')
) AS sub(name, description)
WHERE t.name = 'Instrução e Capacitação' AND t.parent_id = 0;

-- Atualizar topic_path para as coleções principais
INSERT INTO topic_path (topic_id, parent_ids, parent_names)
SELECT id, '0', name FROM topic WHERE parent_id = 0;

-- Atualizar topic_path para as subcoleções
INSERT INTO topic_path (topic_id, parent_ids, parent_names)
SELECT sub.id,
       '0,' || parent.id,
       parent.name || '/' || sub.name
FROM topic sub
JOIN topic parent ON sub.parent_id = parent.id
WHERE parent.parent_id = 0;

-- Vincular TODOS os usuários cadastrados a TODAS as coleções/subcoleções.
-- O painel admin do Nou-Rau (manager/document/list.php) filtra os topics
-- via INNER JOIN com topic_users — sem essas linhas, /manager mostra a
-- tela vazia mesmo com 600+ documentos no banco. Idempotente via PK.
INSERT INTO topic_users (users_id, topic_id)
SELECT u.id, t.id FROM users u CROSS JOIN topic t
ON CONFLICT (users_id, topic_id) DO NOTHING;
