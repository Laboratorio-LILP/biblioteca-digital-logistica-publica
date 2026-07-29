/* Acervo — filtros em cascata + drawer mobile.
 *
 * Progressive enhancement: SEM JS, o <form> envia por GET e o botão
 * "Aplicar filtros" funciona. COM JS, mudar uma faceta, a ordenação ou o ano
 * envia o form (GET) e a página recarrega no topo — comportamento previsível,
 * sem restauração de rolagem.
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

  // Dimensões da barra (espelham DIM_COLECAO/DIM_HIERARQUIA de facets.py): a
  // contagem de cada nó exclui a dimensão inteira, então marcar um nó precisa
  // LIMPAR os outros params da mesma dimensão — senão o servidor aplica AND
  // (ex.: colecao_v6=A & typeinform_id=T de outra coleção) e a lista devolve 0
  // contra o número prometido na barra. Dentro do próprio param, multi continua
  // multi (Tipo) e single continua rádio (SINGLE_SELECT).
  var DIMENSOES = [
    ["colecao_v6", "typeinform_id"],
    ["category_id", "subcategoria_id", "microcategoria_id"],
  ];

  function clearGroup(name) {
    form.querySelectorAll('input[name="' + name + '"]').forEach(function (el) { el.checked = false; });
  }

  // Feedback de "atualizando" ao auto-submeter (a página recarrega no servidor).
  var results = document.querySelector(".acervo-results");
  var statusEl = document.getElementById("acervo-status");
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function doSubmit() {
    if (results && !reduce) results.classList.add("is-updating");
    if (statusEl) statusEl.textContent = "Atualizando resultados…";
    form.submit();
  }

  var timer = null;
  function submitSoon(delay) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(doSubmit, delay);
  }

  // Valida os campos de Ano: clampa cada um à faixa [min,max] do input e, se De/Até
  // ficarem invertidos, troca — antes de submeter. Evita valor fora da faixa
  // (ex.: 2026 vira 2025) e o "salto" para o limite mínimo.
  function validarAno() {
    var lo = form.querySelector("#ano_min");
    var hi = form.querySelector("#ano_max");
    function clamp(el) {
      if (!el || el.value === "") return null;
      var v = parseInt(el.value, 10);
      if (isNaN(v)) { el.value = ""; return null; }
      var mn = parseInt(el.getAttribute("min"), 10);
      var mx = parseInt(el.getAttribute("max"), 10);
      if (!isNaN(mn) && v < mn) v = mn;
      if (!isNaN(mx) && v > mx) v = mx;
      el.value = String(v);
      return v;
    }
    var a = clamp(lo), b = clamp(hi);
    if (a !== null && b !== null && a > b) { lo.value = String(b); hi.value = String(a); }
  }

  // O spinner (setas ↑↓) de um <input type=number> VAZIO salta para o atributo
  // `min` (1991), ignorando o placeholder — daí "subo e vai para 1991". Correção:
  // se o valor pulou de vazio direto para o min, parte do placeholder (o limite do
  // campo: 1991 no "De", 2025 no "Até"). Não afeta digitação (vai char a char).
  function bindAnoSpinner(el) {
    if (!el) return;
    var prev = el.value;
    el.addEventListener("input", function () {
      if (prev === "" && el.value === el.getAttribute("min")) {
        el.value = el.getAttribute("placeholder") || el.value;
      }
      prev = el.value;
    });
  }
  bindAnoSpinner(form.querySelector("#ano_min"));
  bindAnoSpinner(form.querySelector("#ano_max"));

  // Auto-submit em mudança de faceta (cascata), ordenação e ano.
  form.addEventListener("change", function (e) {
    var t = e.target;
    if (!t) return;
    if (t.matches && t.matches("input[type=checkbox].facet-input")) {
      var param = t.name;
      if (SINGLE_SELECT.has(param)) {
        form.querySelectorAll('input[name="' + param + '"]').forEach(function (el) { if (el !== t) el.checked = false; });
      }
      DIMENSOES.forEach(function (dim) {
        if (dim.indexOf(param) === -1) return;
        dim.forEach(function (name) { if (name !== param) clearGroup(name); });
      });
      submitSoon(40);
      return;
    }
    if (t.matches && t.matches('select[name="sort"]')) { doSubmit(); return; }
    if (t.id === "ano_min" || t.id === "ano_max") { validarAno(); submitSoon(500); }
  });

  // Enter nos inputs de ano envia o form.
  form.addEventListener("keydown", function (e) {
    if ((e.target.id === "ano_min" || e.target.id === "ano_max") && e.key === "Enter") {
      e.preventDefault();
      validarAno();
      doSubmit();
    }
  });

  // Drawer mobile.
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
