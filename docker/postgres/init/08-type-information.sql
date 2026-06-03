--
-- Tipos de informação adicionais para logística pública
-- Complementam os 67 tipos padrão do Nou-Rau
--

-- Tipos faltantes identificados no projeto
INSERT INTO type_information (name)
SELECT name FROM (VALUES
    ('Nota Técnica'),
    ('Manual Operacional'),
    ('Relatório de Gestão'),
    ('Estudo de Caso'),
    ('Jurisprudência'),
    ('Parecer'),
    ('Acórdão'),
    ('Decreto'),
    ('Portaria'),
    ('Resolução'),
    ('Instrução Normativa'),
    ('Edital'),
    ('Guia Prático'),
    ('Infográfico'),
    ('Policy Brief'),
    ('White Paper')
) AS new_types(name)
WHERE NOT EXISTS (
    SELECT 1 FROM type_information ti WHERE ti.name = new_types.name
);

-- Tipos de Informação canônicos da taxonomia v8 (4 coleções) — vocabulário
-- controlado da aba "Coleção, Assunto e Natureza" de BDLP_Template_Insercao_v8.xlsx.
-- Nomes EXATOS (batem com _TIPOS_POR_COLECAO em portal/catalog/taxonomy_v6.py),
-- de modo que colecao_v6_for_tipo() derive a coleção correta no front. Inclui
-- "Slides" (faltava no seed). Idempotente via NOT EXISTS.
INSERT INTO type_information (name)
SELECT name FROM (VALUES
    -- Jurisprudência
    ('Enunciados'), ('Súmulas'), ('Boletins'), ('Documentos Normativos'),
    -- Trabalhos Acadêmicos
    ('Teses'), ('Dissertações'), ('Monografias'), ('TCCs'), ('Memoriais Docentes'),
    -- Doutrina e Conteúdo Técnico
    ('Livros digitais'), ('Artigos'), ('Notas Técnicas'), ('Relatórios'),
    ('Textos de Discussão'), ('Resumos'), ('Resumos expandidos'),
    -- Instrução e Capacitação
    ('Manuais'), ('Guias'), ('Tutoriais'), ('Apostilas'), ('Aulas'),
    ('Cursos'), ('Vídeos'), ('Slides')
) AS v8_types(name)
WHERE NOT EXISTS (
    SELECT 1 FROM type_information ti WHERE ti.name = v8_types.name
);

-- Associar tipos às coleções principais
INSERT INTO topic_type (topic_id, type_id)
SELECT t.id, ti.id
FROM topic t, type_information ti
WHERE t.parent_id = 0
ON CONFLICT (topic_id, type_id) DO NOTHING;
