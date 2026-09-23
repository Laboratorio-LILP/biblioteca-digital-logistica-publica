#!/usr/bin/env python
"""Cenas de evidência (Playwright) — validação do subsecretário, set/2026.

Reproduz, contra a stack local, as cenas exigidas pela rodada de correções
(spec docs/specs/2026-09-14-validacao-subsecretario-plataforma.md) e salva as
capturas em docs/evidencias/2026-09-validacao/. Só usa `localhost` — nenhuma
captura carrega endereço interno.

Uso (venv local com `playwright` instalado e `playwright install chromium`):

    .venv/bin/python tools/evidencias_playwright.py --suffix antes
    .venv/bin/python tools/evidencias_playwright.py --suffix depois --verify

Cenas (cada uma vira um PNG com o sufixo informado):

  acervo-filtro-assunto-desktop-<suffix>.png
      1440x900, JS ligado. Rola até a faceta Assunto, marca "Micro e Pequenas
      Empresas" e captura a VIEWPORT depois da atualização. "Antes": a página
      recarrega no topo. "Depois": a rolagem não se move.
  acervo-filtro-assunto-desktop-semjs-<suffix>.png
      1440x900, JS desligado (`java_script_enabled=False`). Marca o mesmo
      filtro e clica em "Aplicar filtros". "Depois": a página recarrega já
      posicionada em #acervo-resultados.
  acervo-filtro-assunto-mobile-<suffix>.png
      390x844, JS ligado. Abre o drawer de filtros, marca o filtro e captura.
      "Depois": o drawer continua aberto e a lista atualiza por trás.
  cartao-dois-eixos-desktop-<suffix>.png / cartao-dois-eixos-mobile-<suffix>.png
      Viewport dos primeiros cards do Acervo (rodapé do card com os dois eixos).
  documento-classificacao-desktop-<suffix>.png
      Página do documento, inteira (badge "Etapa" e bloco Classificação BDLP).
  colecoes-glossario-desktop-<suffix>.png
      Página de Coleções, inteira (glossário de Assuntos e Categorias).
  colecoes-organizacao-desktop-<suffix>.png / colecoes-organizacao-mobile-<suffix>.png
      Ajuste de 16/09: glossário com listas em colunas (assuntos em 3 no
      desktop), contagem por assunto e subcategorias em texto corrido. Confere
      também que /busca/ não vaza sintaxe de template ("{#", "#}") no texto.

Além das capturas, grava `checks-<suffix>.json` com os erros de console/página
observados em cada cena e o resultado das verificações automáticas (rolagem
preservada, URL atualizada, foco mantido, anúncio no aria-live, "voltar" sem
recarregar, drawer preservado, âncora sem JS). Com `--verify`, o processo sai
com código 1 se alguma verificação falhar — é o critério de pronto da T1.

O banner de cookies (LGPD) é silenciado por um consentimento gravado no
localStorage antes de cada navegação, para não cobrir as capturas.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT_DEFAULT = REPO / "docs" / "evidencias" / "2026-09-validacao"

ASSUNTO_ALVO = "Micro e Pequenas Empresas"
DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}

# Consentimento LGPD já registrado — o banner não aparece nas capturas.
CONSENT_JS = (
    "try { localStorage.setItem('sp-lgpd-consent', JSON.stringify({versao: 1, "
    "timestamp: '2026-09-14T00:00:00Z', categorias: {necessarios: true, "
    "funcionalidades: false, analytics: false}})); } catch (e) {}"
)


class Cena:
    """Acumula erros de console/página e verificações de uma cena."""

    def __init__(self, nome: str, page: Page):
        self.nome = nome
        self.erros: list[str] = []
        self.checks: dict[str, bool | str] = {}
        page.on("console", lambda m: self.erros.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: self.erros.append(f"pageerror: {e}"))

    def check(self, chave: str, ok: bool, detalhe: str = "") -> None:
        self.checks[chave] = ok if not detalhe else f"{'ok' if ok else 'FALHOU'} — {detalhe}"

    def as_dict(self) -> dict:
        return {"erros": self.erros, "checks": self.checks}


def _abrir_assunto(page: Page) -> None:
    """Abre o <details> da faceta Assunto (fechado por padrão) e rola até ele."""
    summary = page.locator("details.side-section > summary", has_text="Assunto").first
    details = summary.locator("xpath=..")
    if not details.get_attribute("open"):
        summary.click()
    page.locator("label.toggle-opt", has_text=ASSUNTO_ALVO).first.scroll_into_view_if_needed()


def _label_assunto(page: Page):
    return page.locator("label.toggle-opt", has_text=ASSUNTO_ALVO).first


def cena_filtro_desktop_js(page: Page, base: str, out: Path, suffix: str, cena: Cena) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(f"{base}/busca/", wait_until="networkidle")
    _abrir_assunto(page)
    # Rola um pouco além do topo (a cena do subsecretário: "toda vez que clica, vai lá pra cima").
    page.evaluate("window.scrollBy(0, 360)")
    page.wait_for_timeout(200)
    scroll_antes = page.evaluate("window.scrollY")
    page.evaluate("window.__marcador_sem_reload = true")
    label = _label_assunto(page)
    top_antes = label.bounding_box()["y"]
    card_antes = page.evaluate("document.querySelector('.doc-grid .doc-card').getBoundingClientRect().top")
    label.click()
    # Aguarda a atualização: com fetch, a URL muda sem navegação; sem, a página recarrega.
    page.wait_for_url("**/busca/?**assunto_id=**", timeout=10000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)
    scroll_depois = page.evaluate("window.scrollY")
    # 15/09: o topo da grade de resultados também não se move (a linha de estado
    # "Filtrando por …" existe sempre, em vez de ser inserida no primeiro filtro).
    card_depois = page.evaluate("document.querySelector('.doc-grid .doc-card').getBoundingClientRect().top")
    cena.check("cartoes_nao_se_movem", abs(card_depois - card_antes) <= 2,
               f"top do 1º cartão antes={card_antes:.0f} depois={card_depois:.0f}")
    # 15/09: o controle tocado continua no mesmo lugar da tela (o bloco "Seus
    # filtros" entra acima dele e a barra compensa na rolagem própria).
    top_depois = _label_assunto(page).bounding_box()["y"]
    cena.check("filtro_tocado_nao_se_move", abs(top_depois - top_antes) <= 2,
               f"top antes={top_antes:.0f} depois={top_depois:.0f}")
    sem_reload = page.evaluate("window.__marcador_sem_reload === true")
    foco = page.evaluate(
        "(function(){var a=document.activeElement; return a ? (a.name||'')+':'+(a.value||'')+':'+(a.checked?'1':'0') : ''})()"
    )
    chips = page.locator(".applied-filter-chip__label").all_inner_texts()
    status = page.locator("#acervo-status").inner_text()
    cena.check("url_com_assunto_id", "assunto_id=" in page.url, page.url.split("?", 1)[-1])
    cena.check("rolagem_preservada", abs(scroll_depois - scroll_antes) <= 2, f"antes={scroll_antes} depois={scroll_depois}")
    cena.check("sem_recarregar_pagina", sem_reload)
    cena.check("foco_no_checkbox", foco.startswith("assunto_id:") and foco.endswith(":1"), foco)
    cena.check("chip_do_assunto", any(ASSUNTO_ALVO in c for c in chips), " | ".join(chips))
    cena.check("anuncio_aria_live", "atualizad" in status.lower(), status)
    page.screenshot(path=str(out / f"acervo-filtro-assunto-desktop-{suffix}.png"))
    # "Voltar" restaura a busca anterior sem recarregar.
    page.go_back(wait_until="networkidle")
    page.wait_for_timeout(400)
    ainda_sem_reload = page.evaluate("window.__marcador_sem_reload === true")
    cena.check("voltar_sem_recarregar", ainda_sem_reload and "assunto_id=" not in page.url, page.url)
    marcado = page.evaluate(
        "(function(){var i=document.querySelector('input[name=assunto_id]:checked'); return !!i})()"
    )
    cena.check("voltar_desmarca_filtro", not marcado)
    # "Avançar" restaura o filtro; depois, "Limpar tudo" por teclado: o foco vai
    # para um controle que CONTINUA na ordem de Tab (revisão de 14/09/2026 —
    # o <summary> não pode receber tabindex="-1").
    page.go_forward(wait_until="networkidle")
    page.wait_for_timeout(400)
    page.locator("a.clear-btn").focus()
    page.keyboard.press("Enter")
    page.wait_for_url(lambda u: "assunto_id" not in u, timeout=10000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)
    foco_limpar = page.evaluate(
        "(function(){var a=document.activeElement; return {tag: a.tagName, tabIndex: a.tabIndex, "
        "texto: (a.textContent||'').trim().slice(0, 30)}})()"
    )
    cena.check("limpar_tudo_foco_na_ordem_de_tab", foco_limpar["tabIndex"] >= 0, str(foco_limpar))
    cena.check("limpar_tudo_sem_chips", page.locator(".applied-filter-chip").count() == 0)


def cena_filtro_desktop_semjs(page: Page, base: str, out: Path, suffix: str, cena: Cena) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(f"{base}/busca/", wait_until="networkidle")
    _abrir_assunto(page)
    _label_assunto(page).click()
    page.locator("button.btn-apply").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)
    scroll = page.evaluate("window.scrollY")
    cena.check("url_com_assunto_id", "assunto_id=" in page.url, page.url.split("?", 1)[-1])
    cena.check("ancora_resultados", page.url.endswith("#acervo-resultados"), page.url)
    cena.check("pagina_posicionada_nos_resultados", scroll > 100, f"scrollY={scroll}")
    page.screenshot(path=str(out / f"acervo-filtro-assunto-desktop-semjs-{suffix}.png"))


def cena_filtro_mobile_js(page: Page, base: str, out: Path, suffix: str, cena: Cena) -> None:
    page.set_viewport_size(MOBILE)
    page.goto(f"{base}/busca/", wait_until="networkidle")
    page.locator(".acervo-mobile-toggle").click()
    page.wait_for_timeout(300)
    _abrir_assunto(page)
    page.evaluate("window.__marcador_sem_reload = true")
    label = _label_assunto(page)
    top_antes = label.bounding_box()["y"]
    label.click()
    page.wait_for_url("**/busca/?**assunto_id=**", timeout=10000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)
    top_depois = _label_assunto(page).bounding_box()["y"]
    cena.check("filtro_tocado_nao_se_move", abs(top_depois - top_antes) <= 2,
               f"top antes={top_antes:.0f} depois={top_depois:.0f}")
    aberto = page.evaluate("document.getElementById('acervo-sidebar').classList.contains('is-open')")
    expanded = page.locator(".acervo-mobile-toggle").get_attribute("aria-expanded")
    sem_reload = page.evaluate("window.__marcador_sem_reload === true")
    cena.check("drawer_continua_aberto", bool(aberto) and expanded == "true", f"is-open={aberto} aria-expanded={expanded}")
    cena.check("sem_recarregar_pagina", sem_reload)
    cena.check("url_com_assunto_id", "assunto_id=" in page.url)
    page.screenshot(path=str(out / f"acervo-filtro-assunto-mobile-{suffix}.png"))
    # Fecha o drawer (Escape) e confere que a lista atrás está filtrada.
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    chips = page.locator(".applied-filter-chip__label").all_inner_texts()
    cena.check("lista_atualizada_por_tras", any(ASSUNTO_ALVO in c for c in chips), " | ".join(chips))
    page.screenshot(path=str(out / f"acervo-filtro-assunto-mobile-fechado-{suffix}.png"))


def cena_cartao(page: Page, base: str, out: Path, suffix: str, cena: Cena, viewport: dict, rotulo: str) -> None:
    page.set_viewport_size(viewport)
    page.goto(f"{base}/busca/", wait_until="networkidle")
    page.locator(".doc-grid .doc-card").first.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    rodape = page.locator(".doc-card .doc-card__bottom").first.inner_text()
    cena.check("rodape_do_cartao", bool(rodape.strip()), rodape.replace("\n", " "))
    # 15/09/2026: os dois eixos na linha de baixo ("Categoria: … · Assunto: …"), sem
    # badge de categoria junto do tipo e sem a palavra "Etapa".
    plano = rodape.replace("\n", " ")
    cena.check("rodape_com_categoria_e_assunto", "Categoria:" in plano and "Assunto:" in plano and "Etapa" not in plano, plano)
    cena.check("sem_badge_de_categoria_no_topo", page.locator(".doc-card .doc-card__cat").count() == 0)
    page.screenshot(path=str(out / f"cartao-dois-eixos-{rotulo}-{suffix}.png"))


def _descobrir_doc(page: Page, base: str) -> str:
    page.goto(f"{base}/busca/?sort=titulo", wait_until="networkidle")
    href = page.locator(".doc-grid .doc-card").first.get_attribute("href") or ""
    return href.split("/documento/", 1)[-1].split("/", 1)[0]


def cena_documento(page: Page, base: str, out: Path, suffix: str, cena: Cena, code: str | None) -> None:
    page.set_viewport_size(DESKTOP)
    code = code or _descobrir_doc(page, base)
    page.goto(f"{base}/documento/{code}/", wait_until="networkidle")
    badges = page.locator(".doc-badges .doc-badge").all_inner_texts()
    labels = page.locator(".meta-grid .meta-item .label").all_inner_texts()
    cena.check("badges_do_heroi", bool(badges), " | ".join(b.replace("\n", " ") for b in badges))
    cena.check("rotulos_classificacao", bool(labels), " | ".join(labels))
    # 17/09: corpo do título por faixa de comprimento (texto sempre inteiro).
    titulo = page.locator(".doc-detail-hero__title")
    n = len(titulo.inner_text().strip())
    classe = titulo.get_attribute("class") or ""
    esperado = "--longa" if n > 180 else "--media" if n > 110 else ""
    tem = ("--longa" in classe, "--media" in classe)
    ok = (esperado == "--longa" and tem == (True, False)) or (esperado == "--media" and tem == (False, True)) \
        or (esperado == "" and tem == (False, False))
    cena.check("titulo_na_faixa_certa", ok, f"{n} caracteres → {esperado or 'corpo padrão'} ({classe})")
    cena.check("titulo_inteiro", not titulo.inner_text().rstrip().endswith(("…", "...")), f"{n} caracteres")
    page.screenshot(path=str(out / f"documento-classificacao-desktop-{suffix}.png"), full_page=True)


def cena_colecoes(page: Page, base: str, out: Path, suffix: str, cena: Cena) -> None:
    page.set_viewport_size(DESKTOP)
    page.goto(f"{base}/colecoes/", wait_until="networkidle")
    n_assuntos = page.locator("#assuntos .glossario__item").count()
    n_categorias = page.locator("#categorias .glossario__item").count()
    cena.check("glossario_assuntos", n_assuntos > 0, f"{n_assuntos} itens")
    cena.check("glossario_categorias", n_categorias > 0, f"{n_categorias} itens")
    page.screenshot(path=str(out / f"colecoes-glossario-desktop-{suffix}.png"), full_page=True)

    # Ajuste de 16/09: listas em colunas (assuntos em 3 no desktop), contagem por
    # assunto, subcategorias em texto corrido e régua fechando em cada item (sem
    # "célula fantasma" na última linha incompleta).
    colunas = page.evaluate(
        "() => new Set([...document.querySelectorAll('#assuntos .glossario__item')]"
        ".map(li => Math.round(li.getBoundingClientRect().left))).size"
    )
    cena.check("assuntos_3_colunas_desktop", colunas == 3, f"{colunas} colunas")
    n_count = page.locator("#assuntos .glossario__count").count()
    cena.check("contagem_por_assunto", n_count == n_assuntos, f"{n_count} contagens para {n_assuntos} assuntos")
    # 17/09: sub e microcategorias ficam no "Saiba mais" da categoria (árvore de links)
    arvores = page.locator("#categorias details.glossario__mais .glossario__arvore")
    n_arv = arvores.count()
    n_links = page.locator("#categorias .glossario__arvore a").count()
    cena.check("subcategorias_no_saiba_mais", n_arv >= 1 and n_links >= n_arv, f"{n_arv} árvores, {n_links} nomes")
    fecho = page.evaluate(
        "() => { const ul = document.querySelector('#assuntos .glossario__lista');"
        " const li = [...ul.querySelectorAll('.glossario__item')].pop();"
        " return Math.round(ul.getBoundingClientRect().bottom - li.getBoundingClientRect().bottom); }"
    )
    cena.check("regua_fecha_no_ultimo_item", fecho == 0, f"ul termina {fecho}px após o último item")
    page.screenshot(path=str(out / f"colecoes-organizacao-desktop-{suffix}.png"), full_page=True)

    page.set_viewport_size(MOBILE)
    page.goto(f"{base}/colecoes/", wait_until="networkidle")
    page.screenshot(path=str(out / f"colecoes-organizacao-mobile-{suffix}.png"), full_page=True)

    # Regressão do comentário {# #} multi-linha que vazava como texto no Acervo.
    page.set_viewport_size(DESKTOP)
    page.goto(f"{base}/busca/", wait_until="networkidle")
    texto = page.locator("main").inner_text()
    vazou = "{#" in texto or "#}" in texto or "{%" in texto
    cena.check("acervo_sem_vazamento_de_template", not vazou, "sintaxe de template visível" if vazou else "limpo")


CENAS = [
    "filtro-desktop-js",
    "filtro-desktop-semjs",
    "filtro-mobile-js",
    "cartao-desktop",
    "cartao-mobile",
    "documento",
    "colecoes",
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--out-dir", default=str(OUT_DEFAULT))
    ap.add_argument("--suffix", required=True, help="antes | depois (ou outro rótulo)")
    ap.add_argument("--doc-code", default=None, help="código do documento para a cena 'documento'")
    ap.add_argument("--cenas", nargs="*", default=CENAS, choices=CENAS)
    ap.add_argument("--verify", action="store_true", help="sai com 1 se alguma verificação falhar")
    args = ap.parse_args(argv)

    base = args.base_url.rstrip("/")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    resultado: dict[str, dict] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch()

        def contexto(js: bool = True):
            ctx = browser.new_context(java_script_enabled=js, locale="pt-BR", reduced_motion="no-preference")
            ctx.add_init_script(CONSENT_JS)
            return ctx

        for nome in args.cenas:
            ctx = contexto(js=(nome != "filtro-desktop-semjs"))
            page = ctx.new_page()
            cena = Cena(nome, page)
            try:
                if nome == "filtro-desktop-js":
                    cena_filtro_desktop_js(page, base, out, args.suffix, cena)
                elif nome == "filtro-desktop-semjs":
                    cena_filtro_desktop_semjs(page, base, out, args.suffix, cena)
                elif nome == "filtro-mobile-js":
                    cena_filtro_mobile_js(page, base, out, args.suffix, cena)
                elif nome == "cartao-desktop":
                    cena_cartao(page, base, out, args.suffix, cena, DESKTOP, "desktop")
                elif nome == "cartao-mobile":
                    cena_cartao(page, base, out, args.suffix, cena, MOBILE, "mobile")
                elif nome == "documento":
                    cena_documento(page, base, out, args.suffix, cena, args.doc_code)
                elif nome == "colecoes":
                    cena_colecoes(page, base, out, args.suffix, cena)
            except Exception as exc:  # a cena falhou: registra e segue para a próxima
                cena.check("cena_executou", False, f"{type(exc).__name__}: {exc}")
                try:
                    page.screenshot(path=str(out / f"{nome}-{args.suffix}-ERRO.png"))
                except Exception:
                    pass
            finally:
                resultado[nome] = cena.as_dict()
                ctx.close()
        browser.close()

    (out / f"checks-{args.suffix}.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    falhas = 0
    for nome, r in resultado.items():
        print(f"== {nome}")
        for k, v in r["checks"].items():
            ok = v is True or (isinstance(v, str) and v.startswith("ok"))
            falhas += 0 if ok else 1
            print(f"   [{'ok' if ok else 'X '}] {k}: {v if isinstance(v, str) else ''}")
        for e in r["erros"]:
            print(f"   ! {e}")
    print(f"\ncapturas em {out} — verificações com falha: {falhas}")
    return 1 if (args.verify and falhas) else 0


if __name__ == "__main__":
    sys.exit(main())
