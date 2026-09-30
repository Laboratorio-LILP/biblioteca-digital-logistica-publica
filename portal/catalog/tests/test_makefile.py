"""Makefile: backup e restore que funcionam sobre banco cheio, e `make test`
que roda (achados F5-02, F6-02 e F2-04 da auditoria de 23/09/2026).

- `backup`: pg_dump em formato custom (-Fc, o único que o pg_restore sabe
  limpar), com -T, gravado em .part e renomeado só se o pg_dump sair 0; mais o
  volume de arquivos da curadoria (/nourau, montado no portal), em .tgz.
- `restore`: pg_restore --clean --if-exists --single-transaction (tudo ou nada)
  seguido da role de leitura (09) e do REVOKE de `users` (10) — todo restore
  recria a tabela e devolve a leitura ao portal.
- `restore-files`: devolve o volume de arquivos.
- nenhum alvo imprime instrução insegura (o antigo `restore` só ecoava um
  `cat backup.sql | psql`, que sobre banco cheio dá 117 erros e não desfaz nada).
- `test`: ver test_make_test.py.

Sem Docker: texto do Makefile e `make -n` (sintaxe), nada é executado.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
MAKEFILE = (REPO / "Makefile").read_text(encoding="utf-8")
DOCKERFILE = (REPO / "docker" / "portal" / "Dockerfile").read_text(encoding="utf-8")


def _alvo(nome):
    m = re.search(rf"^{nome}:.*?(?=^\S|\Z)", MAKEFILE, flags=re.M | re.S)
    assert m, f"alvo {nome} não encontrado"
    return m.group(0)


def test_backup_em_formato_custom_com_part_e_arquivos_da_curadoria():
    t = _alvo("backup")
    assert "exec -T postgres pg_dump -U php -Fc nourau" in t
    assert ".part" in t and "mv " in t and "rm -f" in t                 # só vira backup se o pg_dump sair 0
    assert "exec -T portal tar czf - -C /nourau ." in t                 # volume nourau_data (curadoria)
    assert "exit 1" in t
    assert ".sql" not in t                                              # nada de dump em texto


def test_restore_limpa_em_transacao_unica_e_revoga_users_depois():
    t = _alvo("restore")
    assert 'test -n "$(FILE)"' in t and 'test -f "$(FILE)"' in t
    assert "pg_restore -U php -d nourau --clean --if-exists --no-owner --single-transaction < $(FILE)" in t
    assert "--no-acl" not in t                                          # descartaria os GRANTs do portal_reader
    i_restore = t.index("pg_restore")
    i_role = t.index("docker/postgres/init/09-portal-readonly-user.sh")
    i_revoke = t.index("docker/postgres/init/10-portal-readonly-revoke-users.sql")
    assert i_restore < i_role < i_revoke                                # ordem: restaurar → role → REVOKE
    assert "bash -s <" in t                                             # a senha vem do ambiente do contêiner


def test_restore_files_devolve_o_volume_da_curadoria():
    t = _alvo("restore-files")
    assert 'test -f "$(FILE)"' in t
    assert "exec -T nourau tar xzf - -C /nourau < $(FILE)" in t


def test_nenhum_alvo_imprime_instrucao_insegura():
    assert "cat backup" not in MAKEFILE
    assert "psql -U php nourau\"" not in MAKEFILE
    for linha in MAKEFILE.splitlines():
        if linha.lstrip().startswith("@echo") and "psql" in linha:
            pytest.fail(f"eco com comando psql: {linha.strip()}")


def test_gitignore_barra_os_backups():
    gi = (REPO / ".gitignore").read_text(encoding="utf-8")
    for padrao in ("backup_*.sql", "backup_*.dump", "backup_*.dump.part", "backup_*_arquivos.tgz", "backup_*.tgz.part"):
        assert padrao in gi, padrao


@pytest.mark.skipif(shutil.which("make") is None, reason="make ausente")
def test_makefile_tem_sintaxe_valida_para_o_make():
    r = subprocess.run(["make", "-n", "backup", "restore", "restore-files", "test", "FILE=x.dump"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr
    assert "pg_restore" in r.stdout and "pg_dump" in r.stdout
