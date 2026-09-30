"""Chave secreta e DEBUG sem padrão inseguro (achado F6-03 da auditoria de
23/09/2026; tarefa Todoist p1 de 03/09).

Regras: sem `DJANGO_SECRET_KEY` e fora do modo de desenvolvimento o portal NÃO
sobe; `DJANGO_DEBUG` ausente vale `false`; em desenvolvimento (`DJANGO_DEBUG=true`)
sem chave, o boot usa uma chave aleatória por processo, nunca uma constante
conhecida. O compose base exige a chave como já exige as senhas do banco.

Os settings são importados em subprocesso para controlar o ambiente por inteiro.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PORTAL = REPO / "portal"
CHAVE_ANTIGA = "insecure-dev-key-change-in-production"


def _boot(**ambiente):
    """Importa portal.settings num subprocesso limpo de variáveis DJANGO_*."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    env.update(ambiente)
    env["PYTHONPATH"] = str(PORTAL)
    env["DJANGO_SETTINGS_MODULE"] = "portal.settings"
    codigo = ("from django.conf import settings as s; "
              "print(s.DEBUG, len(s.SECRET_KEY), s.SECRET_KEY[:4])")
    return subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, env=env, cwd=PORTAL)


def test_sem_chave_e_fora_do_dev_o_boot_falha():
    r = _boot(DJANGO_DEBUG="false")
    assert r.returncode != 0
    assert "ImproperlyConfigured" in r.stderr and "DJANGO_SECRET_KEY" in r.stderr


def test_sem_chave_e_sem_debug_tambem_falha_porque_debug_padrao_e_false():
    r = _boot()
    assert r.returncode != 0 and "DJANGO_SECRET_KEY" in r.stderr


def test_debug_padrao_e_false():
    r = _boot(DJANGO_SECRET_KEY="chave-de-teste-" + "x" * 40)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split()[0] == "False"


def test_em_desenvolvimento_sem_chave_sobe_com_chave_aleatoria():
    a, b = _boot(DJANGO_DEBUG="true"), _boot(DJANGO_DEBUG="true")
    assert a.returncode == 0 and b.returncode == 0, a.stderr + b.stderr
    debug, tamanho, prefixo = a.stdout.split()
    assert debug == "True" and int(tamanho) >= 50 and prefixo == "dev-"
    assert a.stdout == b.stdout  # o prefixo e o tamanho são iguais; a chave em si muda a cada boot (ver abaixo)


def test_chave_de_desenvolvimento_muda_a_cada_boot():
    env = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    env.update(PYTHONPATH=str(PORTAL), DJANGO_SETTINGS_MODULE="portal.settings", DJANGO_DEBUG="true")
    codigo = "from django.conf import settings; print(settings.SECRET_KEY)"
    chaves = {subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, env=env, cwd=PORTAL).stdout
              for _ in range(2)}
    assert len(chaves) == 2


def test_a_chave_insegura_antiga_nao_existe_mais_no_repositorio():
    for arquivo in ("portal/portal/settings.py", "docker/docker-compose.yml", "docker/docker-compose.prod.yml",
                    "docker/portal/Dockerfile"):
        assert CHAVE_ANTIGA not in (REPO / arquivo).read_text(encoding="utf-8"), arquivo


def test_compose_base_exige_a_chave_e_debug_false_por_padrao():
    compose = (REPO / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?" in compose      # como as senhas do banco
    assert "DJANGO_DEBUG: ${DJANGO_DEBUG:-false}" in compose
