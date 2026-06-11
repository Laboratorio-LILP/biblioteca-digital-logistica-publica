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

  function clearGroup(name) {
    form.querySelectorAll('input[name="' + name + '"]').forEach(function (el) { el.checked = false; });
  }

  var timer = null;
  function submitSoon(delay) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(function () { form.submit(); }, delay);
  }

  // Auto-submit em mudança de faceta (cascata), ordenação e ano.
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
      submitSoon(40);
      return;
    }
    if (t.matches && t.matches('select[name="sort"]')) { form.submit(); return; }
    if (t.id === "ano_min" || t.id === "ano_max") { submitSoon(120); }
  });

  // Enter nos inputs de ano envia o form.
  form.addEventListener("keydown", function (e) {
    if ((e.target.id === "ano_min" || e.target.id === "ano_max") && e.key === "Enter") {
      e.preventDefault();
      form.submit();
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
