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
    assert ".sp-seta-secoes[hidden]" in css  # sem JS, o botão não pode virar tab stop fantasma


def test_js_da_seta_existe_e_e_csp_safe():
    js = (STATIC / "js" / "seta-secoes.js").read_text(encoding="utf-8")
    assert "data-seta-secoes" in js
    assert "data-sec" in js
    assert "addEventListener" in js  # CSP-safe: sem handlers inline
    assert "prefers-reduced-motion" in js


def test_parcial_tem_rotulo_de_chegada():
    parcial = _template("_partials/_seta_secoes.html")
    assert "sp-seta-secoes__rotulo" in parcial
    assert "Veja mais" in parcial
    assert re.search(r"<button[^>]*\shidden[\s>]", parcial)  # melhoria progressiva intacta


def test_css_tem_estado_de_chegada():
    css = (STATIC / "css" / "portal.css").read_text(encoding="utf-8")
    assert ".sp-seta-secoes.is-chegada" in css
    assert ".sp-seta-secoes__rotulo" in css
    assert "--sp-red-dark" in css[css.index(".sp-seta-secoes.is-chegada"):]  # pílula AA-safe


def test_js_tem_chegada_que_assenta_no_primeiro_gesto():
    js = (STATIC / "js" / "seta-secoes.js").read_text(encoding="utf-8")
    assert "is-chegada" in js
    assert "Veja mais: " in js   # WCAG 2.5.3 — nome acessível contém o rótulo visível
    assert "assentar" in js
