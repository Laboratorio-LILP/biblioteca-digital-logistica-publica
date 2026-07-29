"""Testes da seta-guia de seções (Home e Coleções), sem banco.

A feature é de front (templates/CSS/JS); estes testes leem os arquivos e
pinam os invariantes do design: âncoras [data-sec], parcial da seta nas
duas páginas, ícones no sprite e blocos CSS/JS presentes.
Spec: docs/superpowers/specs/2026-07-29-seta-secoes-design.md
"""

import re
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


def test_parcial_da_seta_e_melhoria_progressiva():
    parcial = _template("_partials/_seta_secoes.html")
    assert "data-seta-secoes" in parcial
    assert re.search(r"<button[^>]*\shidden[\s>]", parcial)  # sem JS, a seta não aparece
    assert "aria-label" in parcial
    assert 'type="button"' in parcial
    assert "fi-chevron-down" in parcial


def test_home_tem_5_ancoras_e_a_seta():
    home = _template("home.html")
    assert home.count("data-sec=") == 5
    assert "_partials/_seta_secoes.html" in home
    assert "js/seta-secoes.js" in home


def test_colecoes_tem_3_ancoras_e_a_seta():
    colecoes = _template("collection_list.html")
    assert colecoes.count("data-sec=") == 3
    assert "_partials/_seta_secoes.html" in colecoes
    assert "js/seta-secoes.js" in colecoes


def test_css_tem_componente_ancoras_e_offset_do_banner():
    css = (STATIC / "css" / "portal.css").read_text(encoding="utf-8")
    assert ".sp-seta-secoes" in css
    assert "[data-sec]" in css  # scroll-margin-top das âncoras
    assert "--sp-seta-offset" in css  # desvio do banner LGPD
    assert css.index(".sp-seta-secoes") > css.index(".sp-banner-cookies")  # bloco novo no fim
