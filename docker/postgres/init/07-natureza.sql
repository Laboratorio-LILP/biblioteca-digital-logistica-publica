--
-- Natureza do objeto da contratação — taxonomia v6 (canônica)
-- Adiciona a dimensão NATUREZA (obrigatória na captura; 5 valores fixos)
-- e a tabela auxiliar de vocabulário. A coluna fica nullable no schema para
-- não quebrar os registros já carregados (classificação v5); a obrigatoriedade
-- é aplicada na camada de captura/curadoria.
--
-- Tipologia: removida da APLICAÇÃO na v6 (modelo/facetas/busca). A coluna
-- física `tipologia` (criada em 05-custom-metadata.sql) é PRESERVADA aqui de
-- propósito, para servir ao de-para v5→v6 (migração P2). Não fazer DROP.
--

-- 1. Nova coluna em nr_document ---------------------------------------------
ALTER TABLE nr_document ADD COLUMN IF NOT EXISTS natureza VARCHAR(80);
CREATE INDEX IF NOT EXISTS idx_nr_document_natureza ON nr_document (natureza);

-- 2. Vocabulário controlado (5 valores §7) ----------------------------------
CREATE TABLE IF NOT EXISTS nr_natureza (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(80) UNIQUE NOT NULL,
    ordem INT DEFAULT 0
);

INSERT INTO nr_natureza (nome, ordem) VALUES
    ('Contratação de Materiais', 1),
    ('Contratação de Obras e Serviços de Engenharia', 2),
    ('Contratação de Serviços', 3),
    ('Contratação de TIC', 4),
    ('Não se aplica', 5)
ON CONFLICT (nome) DO NOTHING;
