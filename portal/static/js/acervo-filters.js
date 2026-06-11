/* Acervo — filtros em cascata + atualização AJAX in-place.
 *
 * Progressive enhancement: SEM JS, o <form> envia por GET e o botão
 * "Aplicar filtros" funciona (recarrega a página). COM JS, filtrar, ordenar,
 * paginar, remover chip e "Limpar tudo" trocam SÓ a barra lateral e os
 * resultados no DOM (fetch + swap), sem recarregar a página — então a posição
 * de rolagem não muda e não há salto nem flash.
 *
 * Tudo é delegado no <form> (que nunca é trocado), para os listeners
 * sobreviverem às trocas de conteúdo. A troca usa replaceChildren com os nós
 * já parseados (não innerHTML de string). Qualquer erro de rede ou estrutura
 * inesperada cai no fallback seguro: navegação normal para a URL.
 */
(function () {
  "use strict";

  var form = document.getElementById("acervo-form");
  if (!form) return;

  // Marca JS ativo: habilita o drawer mobile e esconde o botão "Aplicar" (CSS).
  document.documentElement.classList.add("js");

  var sidebar = document.getElementById("acervo-sidebar");
  var mobileToggle = form.querySelector(".acervo-mobile-toggle");

  // Grupos single-select (rádio); os demais (Assunto, Natureza, Tipo) são multi.
  var SINGLE_SELECT = new Set(["colecao_v6", "category_id", "subcategoria_id", "microcategoria_id"]);

  function groupKey(details) {
    var summary = details.querySelector("summary");
    return (summary ? summary.textContent : "").replace(/[\d()]/g, "").replace(/\s+/g, " ").trim();
  }

  function clearGroup(name) {
    form.querySelectorAll('input[name="' + name + '"]').forEach(function (el) { el.checked = false; });
  }

  // Move os filhos de `from` (doc inerte do DOMParser) para `into` (DOM vivo),
  // sem innerHTML de string — replaceChildren adota os nós já parseados.
  function swapChildren(into, from) {
    into.replaceChildren.apply(into, Array.prototype.slice.call(from.childNodes));
  }

  // URL de busca a partir do estado atual do form (descarta valores vazios e
  // 'page' — filtrar volta para a página 1, como no comportamento sem JS).
  function buildFormUrl() {
    var params = new URLSearchParams();
    new FormData(form).forEach(function (value, key) {
      if (value !== "" && value != null) params.append(key, value);
    });
    var qs = params.toString();
    return form.getAttribute("action") + (qs ? "?" + qs : "");
  }

  // ---- Núcleo AJAX ----
  var pending = null;

  function applyUrl(url, opts) {
    opts = opts || {};
    var token = {};
    pending = token;

    var content = document.getElementById("acervo-results-content");
    var status = document.getElementById("acervo-status");
    if (status) status.textContent = "Atualizando resultados…";
    if (content) content.classList.add("is-updating");

    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" }, credentials: "same-origin" })
      .then(function (resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.text();
      })
      .then(function (html) {
        if (pending !== token) return; // chegou uma atualização mais nova → descarta

        var doc = new DOMParser().parseFromString(html, "text/html");
        var newSidebar = doc.getElementById("acervo-sidebar");
        var newContent = doc.getElementById("acervo-results-content");
        var curSidebar = document.getElementById("acervo-sidebar");
        var curContent = document.getElementById("acervo-results-content");
        if (!newSidebar || !newContent || !curSidebar || !curContent) {
          window.location.href = url; // estrutura inesperada → fallback
          return;
        }

        // Preserva os <details> abertos manualmente pelo usuário.
        var open = new Set();
        curSidebar.querySelectorAll("details.filter-group[open]").forEach(function (d) { open.add(groupKey(d)); });

        // Guarda o controle com foco para devolvê-lo após a troca.
        var act = document.activeElement;
        var focusName = (act && curSidebar.contains(act) && act.name) ? act.name : null;
        var focusValue = focusName ? (act.value || "") : null;

        swapChildren(curSidebar, newSidebar);
        swapChildren(curContent, newContent);

        curSidebar.querySelectorAll("details.filter-group").forEach(function (d) {
          if (open.has(groupKey(d))) d.open = true;
        });

        if (opts.push !== false) {
          try { history.pushState({ acervo: true }, "", url); } catch (e) { /* ignora */ }
        }

        if (focusName) {
          try {
            var again = curSidebar.querySelector(
              'input[name="' + CSS.escape(focusName) + '"][value="' + CSS.escape(focusValue) + '"]'
            );
            if (again) again.focus();
          } catch (e) { /* ignora */ }
        }

        var c2 = document.getElementById("acervo-results-content");
        if (c2) c2.classList.remove("is-updating");

        if (opts.scrollToResults) {
          var rc = document.querySelector(".acervo-results");
          if (rc) rc.scrollIntoView({ block: "start" });
        }

        // Anuncia o fim do ciclo na região viva (que persiste fora do swap).
        var st = document.getElementById("acervo-status");
        var countEl = document.querySelector(".results-bar__count");
        if (st) st.textContent = "Resultados atualizados. " + (countEl ? countEl.textContent.trim() : "");
      })
      .catch(function () {
        window.location.href = url; // rede/parse falhou → fallback
      });
  }

  function applyForm() { applyUrl(buildFormUrl(), { push: true }); }

  var timer = null;
  function applyFormDebounced(delay) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(applyForm, delay);
  }

  // ---- Delegação: change (checkbox de faceta, sort, inputs de ano) ----
  form.addEventListener("change", function (e) {
    var t = e.target;
    if (!t) return;
    if (t.matches && t.matches("input[type=checkbox].facet-input")) {
      var param = t.name;
      if (SINGLE_SELECT.has(param)) {
        form.querySelectorAll('input[name="' + param + '"]').forEach(function (el) { if (el !== t) el.checked = false; });
      }
      if (param === "category_id") { clearGroup("subcategoria_id"); clearGroup("microcategoria_id"); }
      else if (param === "subcategoria_id") { clearGroup("microcategoria_id"); }
      applyFormDebounced(40);
      return;
    }
    if (t.matches && t.matches('select[name="sort"]')) { applyForm(); return; }
    if (t.id === "ano_min" || t.id === "ano_max") { applyFormDebounced(120); }
  });

  // Enter nos inputs de ano (sem disparar o submit nativo).
  form.addEventListener("keydown", function (e) {
    if ((e.target.id === "ano_min" || e.target.id === "ano_max") && e.key === "Enter") {
      e.preventDefault();
      applyForm();
    }
  });

  // Submit do form (Enter na busca ou botão sem-JS) → AJAX.
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    applyForm();
  });

  // ---- Delegação: cliques em links de filtro/paginação/limpar ----
  form.addEventListener("click", function (e) {
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    if (!a.closest("#acervo-sidebar, #acervo-results-content")) return;
    // Só intercepta links da própria página de busca (chips, paginação, limpar);
    // links de documento (outro pathname) navegam normalmente.
    if (a.pathname !== window.location.pathname) return;
    e.preventDefault();
    applyUrl(a.href, { push: true, scrollToResults: !!a.closest(".pagination") });
  });

  // Back/forward: sincroniza a página via AJAX (sem novo pushState).
  window.addEventListener("popstate", function () {
    applyUrl(window.location.href, { push: false });
  });

  // ---- Drawer mobile (fora das regiões trocadas → listener persiste) ----
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", function () {
      var isOpen = sidebar.classList.toggle("is-open");
      mobileToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      document.body.classList.toggle("acervo-drawer-open", isOpen);
    });
    document.addEventListener("click", function (e) {
      if (sidebar.classList.contains("is-open") && !sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
        sidebar.classList.remove("is-open");
        mobileToggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("acervo-drawer-open");
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && sidebar.classList.contains("is-open")) {
        sidebar.classList.remove("is-open");
        mobileToggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("acervo-drawer-open");
        mobileToggle.focus();
      }
    });
  }
})();
