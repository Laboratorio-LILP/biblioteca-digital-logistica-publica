--
-- Categorias PROCESSUAIS da contratação pública — taxonomia v8 (canônica, §7).
-- 6 macroetapas da Lei 14.133/2021, fonte: aba "Árvore de Classificação" de
-- BDLP_Template_Insercao_v8.xlsx. Substituem as categorias temáticas v5
-- (que na v8 viraram ASSUNTO — ver 06-taxonomia.sql).
-- Substituem também as categorias padrão do Nou-Rau (04-reset-nr.sql).
--

-- Remover categorias padrão e dependências
DELETE FROM nr_category_format;
DELETE FROM nr_topic_category;
DELETE FROM nr_category;

-- Resetar sequência
SELECT setval('nr_category_seq', 0);

INSERT INTO nr_category (name, description, max_size) VALUES
    ('PLANO ANUAL DE CONTRATAÇÕES (PCA)', 'Planejamento anual das contratações do órgão (PCA)', 0),
    ('CICLO COMPLETO DA CONTRATAÇÃO', 'Materiais que percorrem todo o ciclo da contratação pública', 0),
    ('PLANEJAMENTO/FASE PREPARATÓRIA', 'Fase preparatória: ETP, TR, gestão de riscos e pesquisa de preços', 0),
    ('SELEÇÃO DO FORNECEDOR', 'Seleção do fornecedor: licitação, contratação direta e procedimentos auxiliares', 0),
    ('GESTÃO CONTRATUAL', 'Gestão e fiscalização da execução contratual', 0),
    ('CONTEÚDOS TRANSVERSAIS', 'Temas transversais à contratação pública (governança, integridade, sustentabilidade, sistemas e regulação)', 0);

-- Associar todas as categorias a todos os tópicos principais
-- para que documentos de qualquer coleção possam usar qualquer categoria
INSERT INTO nr_topic_category (topic_id, category_id)
SELECT t.id, c.id
FROM topic t, nr_category c
WHERE t.parent_id = 0;

-- Associar formatos comuns às categorias
-- (PDF, DOC, DOCX, HTML, PPT, PPTX, XLS, XLSX, TXT, RTF, ODT, ODS, ODP)
INSERT INTO nr_category_format (category_id, format_id)
SELECT c.id, f.id
FROM nr_category c, nr_format f
WHERE f.extension IN ('pdf', 'doc', 'docx', 'html', 'htm', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'rtf', 'odt', 'ods', 'odp', 'epub');

-- =====================================================================
-- Subcategorias e Microcategorias v8 (cascata sob a Categoria)
-- Fonte: aba "Árvore de Classificação" de BDLP_Template_Insercao_v8.xlsx.
-- Semeadas aqui (e não em 06-taxonomia.sql) porque dependem de nr_category,
-- que é populada acima neste mesmo arquivo. As tabelas já existem (criadas
-- em 06-taxonomia.sql, que roda antes).
-- PCA e CICLO COMPLETO DA CONTRATAÇÃO não têm subcategoria.
-- =====================================================================

INSERT INTO nr_subcategoria (nome, slug, category_id, ordem)
SELECT v.nome, v.slug, c.id, v.ordem
FROM (VALUES
    ('FASE PREPARATÓRIA - ETP', 'fase-preparatoria-etp', 'PLANEJAMENTO/FASE PREPARATÓRIA', 1),
    ('FASE PREPARATÓRIA - TR', 'fase-preparatoria-tr', 'PLANEJAMENTO/FASE PREPARATÓRIA', 2),
    ('FASE PREPARATÓRIA - GESTÃO DE RISCOS', 'fase-preparatoria-gestao-de-riscos', 'PLANEJAMENTO/FASE PREPARATÓRIA', 3),
    ('FASE PREPARATÓRIA - PESQUISA DE PREÇOS', 'fase-preparatoria-pesquisa-de-precos', 'PLANEJAMENTO/FASE PREPARATÓRIA', 4),
    ('LICITAÇÃO', 'licitacao', 'SELEÇÃO DO FORNECEDOR', 1),
    ('CONTRATAÇÃO DIRETA', 'contratacao-direta', 'SELEÇÃO DO FORNECEDOR', 2),
    ('PROCEDIMENTOS AUXILIARES', 'procedimentos-auxiliares', 'SELEÇÃO DO FORNECEDOR', 3),
    ('GESTÃO DE CONTRATOS', 'gestao-de-contratos', 'GESTÃO CONTRATUAL', 1),
    ('FISCALIZAÇÃO DE CONTRATOS', 'fiscalizacao-de-contratos', 'GESTÃO CONTRATUAL', 2),
    ('Governança e Logística', 'governanca-e-logistica', 'CONTEÚDOS TRANSVERSAIS', 1),
    ('Integridade e Controle', 'integridade-e-controle', 'CONTEÚDOS TRANSVERSAIS', 2),
    ('Políticas Públicas e Sustentabilidade', 'politicas-publicas-e-sustentabilidade', 'CONTEÚDOS TRANSVERSAIS', 3),
    ('Sistemas e Inovação', 'sistemas-e-inovacao', 'CONTEÚDOS TRANSVERSAIS', 4),
    ('Direito e Regulação', 'direito-e-regulacao', 'CONTEÚDOS TRANSVERSAIS', 5)
) AS v(nome, slug, cat, ordem)
JOIN nr_category c ON c.name = v.cat
ON CONFLICT (slug, category_id) DO NOTHING;

INSERT INTO nr_microcategoria (nome, slug, subcategoria_id, ordem)
SELECT v.nome, v.slug, s.id, v.ordem
FROM (VALUES
    ('MAPA DE RISCOS', 'mapa-de-riscos', 'FASE PREPARATÓRIA - GESTÃO DE RISCOS', 1),
    ('MATRIZ DE ALOCAÇÃO DE RISCOS', 'matriz-de-alocacao-de-riscos', 'FASE PREPARATÓRIA - GESTÃO DE RISCOS', 2),
    ('CONCORRÊNCIA', 'concorrencia', 'LICITAÇÃO', 1),
    ('PREGÃO', 'pregao', 'LICITAÇÃO', 2),
    ('LEILÃO', 'leilao', 'LICITAÇÃO', 3),
    ('DIÁLOGO COMPETITIVO', 'dialogo-competitivo', 'LICITAÇÃO', 4),
    ('INEXIGIBILIDADE', 'inexigibilidade', 'CONTRATAÇÃO DIRETA', 1),
    ('EMERGÊNCIA - Inciso VIII', 'emergencia-inciso-viii', 'CONTRATAÇÃO DIRETA', 2),
    ('DISPENSA POR VALOR (Art 75 - incisos I e II)', 'dispensa-por-valor-art-75', 'CONTRATAÇÃO DIRETA', 3),
    ('Contratação Direta outros incisos', 'contratacao-direta-outros-incisos', 'CONTRATAÇÃO DIRETA', 4),
    ('CREDENCIAMENTO', 'credenciamento', 'PROCEDIMENTOS AUXILIARES', 1),
    ('REGISTRO DE PREÇOS (RP)', 'registro-de-precos-rp', 'PROCEDIMENTOS AUXILIARES', 2),
    ('PRÉ-QUALIFICAÇÃO', 'pre-qualificacao', 'PROCEDIMENTOS AUXILIARES', 3),
    ('PMI', 'pmi', 'PROCEDIMENTOS AUXILIARES', 4),
    ('REGISTRO CADASTRAL', 'registro-cadastral', 'PROCEDIMENTOS AUXILIARES', 5)
) AS v(nome, slug, sub, ordem)
JOIN nr_subcategoria s ON s.nome = v.sub
ON CONFLICT (slug, subcategoria_id) DO NOTHING;
