"""Testes da árvore de Categorias do seed SQL (taxonomia v9, sem banco).

A árvore vive em docker/postgres/init/07-categories.sql; estes testes leem o
arquivo e pinam a decisão de 28/07/2026: CONTEÚDOS TRANSVERSAIS é nó folha
(sem subcategorias), como PCA e CICLO COMPLETO DA CONTRATAÇÃO.
"""

from pathlib import Path

SEED = (
    Path(__file__).resolve().parents[3]
    / "docker" / "postgres" / "init" / "07-categories.sql"
)

# Subcategorias derivadas do Assunto, removidas na v9.
SUBCATEGORIAS_CT_REMOVIDAS = (
    "Governança e Logística",
    "Integridade e Controle",
    "Políticas Públicas e Sustentabilidade",
    "Sistemas e Inovação",
    "Direito e Regulação",
)

# Categorias sem subcategoria (nós folha da cascata).
CATEGORIAS_FOLHA = (
    "PLANO DE CONTRATAÇÕES ANUAL (PCA)",
    "CICLO COMPLETO DA CONTRATAÇÃO",
    "CONTEÚDOS TRANSVERSAIS",
)


def _sql():
    return SEED.read_text(encoding="utf-8")


def test_categoria_conteudos_transversais_existe():
    assert "('CONTEÚDOS TRANSVERSAIS'," in _sql()


def test_subcategorias_de_ct_removidas_na_v9():
    sql = _sql()
    for nome in SUBCATEGORIAS_CT_REMOVIDAS:
        assert f"('{nome}'" not in sql, f"subcategoria removida na v9 reapareceu no seed: {nome}"


def test_categorias_folha_sem_subcategoria():
    # Linhas de subcategoria têm a categoria-mãe como 3º campo: (nome, slug, 'CATEGORIA', ordem).
    sql = _sql()
    for cat in CATEGORIAS_FOLHA:
        assert f", '{cat}'," not in sql, f"{cat} deve ser nó folha (sem subcategoria no seed)"
