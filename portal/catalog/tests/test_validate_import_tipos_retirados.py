"""validate_import e o vocabulário v12.1 (fecho da auditoria de 23/09/2026):
nenhuma referência a "Pareceres" como tipo canônico, e o aviso de "tipo
retirado" deriva de TIPOS_LEGADOS — que inclui Pareceres desde a v12.1 — em vez
de uma lista fixa que só sabia de Documentos Normativos e Vídeos. Sem banco.
"""

import ast
import inspect
import re

from catalog.management.commands import validate_import
from catalog.taxonomy_v6 import TIPOS_LEGADOS, tipo_canonico


def test_pareceres_nao_e_tipo_canonico():
    assert "Pareceres" in TIPOS_LEGADOS
    assert tipo_canonico("Pareceres") is None and tipo_canonico("Parecer") is None


def _literais(modulo):
    """Todas as strings literais do módulo (SQL, mensagens, nomes) — comentários ficam de fora."""
    arvore = ast.parse(inspect.getsource(modulo))
    return [n.value for n in ast.walk(arvore) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def test_validate_import_nao_cita_pareceres_em_sql_nem_em_mensagem():
    assert not [s for s in _literais(validate_import) if "Parecer" in s]


def test_aviso_de_tipo_retirado_vem_de_tipos_legados():
    src = inspect.getsource(validate_import)
    assert "TIPOS_LEGADOS" in src
    # nenhuma lista fixa de tipos retirados dentro de SQL ou de mensagem
    assert not re.search(r"IN \('Documentos Normativos', 'Vídeos'\)", src)
    assert "(Documentos Normativos/Vídeos)" not in src
    assert "tuple(TIPOS_LEGADOS)" in src or "list(TIPOS_LEGADOS)" in src   # parâmetro da consulta
