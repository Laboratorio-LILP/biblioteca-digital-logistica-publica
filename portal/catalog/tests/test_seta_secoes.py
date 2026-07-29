"""Testes da seta-guia de seções (Home e Coleções), sem banco.

A feature é de front (templates/CSS/JS); estes testes leem os arquivos e
pinam os invariantes do design: âncoras [data-sec], parcial da seta nas
duas páginas, ícones no sprite e blocos CSS/JS presentes.
Spec: docs/superpowers/specs/2026-07-29-seta-secoes-design.md
"""

from pathlib import Path

PORTAL = Path(__file__).resolve().parents[2]
TEMPLATES = PORTAL / "templates"
STATIC = PORTAL / "static"


def _template(nome):
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def test_sprite_tem_chevron_down_e_up():
    sprite = _template("_partials/_feather.html")
    assert 'id="fi-chevron-down"' in sprite
    assert 'id="fi-chevron-up"' in sprite
