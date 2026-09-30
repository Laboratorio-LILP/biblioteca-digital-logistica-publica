"""`make test` que funciona (achado F2-04 da auditoria de 23/09/2026; tarefa
Todoist p1 de 03/09: o alvo rodava pytest dentro da imagem, que não o tem).

Roda ruff + pytest num contêiner do estágio `test` do Dockerfile (mesmo Python
e mesmo lock da imagem, mais requirements-dev.txt) sobre o working tree montado
em /src. A imagem de execução (estágio final, `runtime`) continua sem pytest.
Sem Docker: texto do Makefile e do Dockerfile.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MAKEFILE = (REPO / "Makefile").read_text(encoding="utf-8")
DOCKERFILE = (REPO / "docker" / "portal" / "Dockerfile").read_text(encoding="utf-8")


def _alvo(nome):
    m = re.search(rf"^{nome}:.*?(?=^\S|\Z)", MAKEFILE, flags=re.M | re.S)
    assert m, f"alvo {nome} não encontrado"
    return m.group(0)


def test_make_test_roda_no_conteiner_de_teste_sobre_o_working_tree():
    t = _alvo("test")
    assert "--target test" in t and "-f docker/portal/Dockerfile" in t
    assert '-v "$(CURDIR)":/src' in t and "-w /src/portal" in t
    assert "DJANGO_SECRET_KEY=" in t and "python -m pytest" in t and "ruff check" in t
    assert "exec portal python -m pytest" not in t                      # a imagem de execução não tem pytest


def test_dockerfile_tem_estagio_de_teste_separado_da_execucao():
    assert "FROM python:3.12-slim AS base" in DOCKERFILE
    assert "FROM base AS test" in DOCKERFILE and "requirements-dev.txt" in DOCKERFILE
    assert "FROM base AS runtime" in DOCKERFILE
    assert DOCKERFILE.rstrip().splitlines()[-1].startswith("CMD") or "CMD [" in DOCKERFILE.split("AS runtime")[1]
    assert DOCKERFILE.index("AS test") < DOCKERFILE.index("AS runtime")    # o último estágio é o de execução
    dev = (REPO / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "pytest" in dev and "pytest-django" in dev and "ruff" in dev
