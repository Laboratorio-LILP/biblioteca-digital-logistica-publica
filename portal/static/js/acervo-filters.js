/* Acervo — filtros em cascata, range slider de ano, drawer mobile.
 * Progressive enhancement: o form funciona sem JS (basta clicar em "Aplicar filtros").
 * Com JS: auto-submit em mudança, slider duplo, cascata e drawer.
 */
(function () {
  "use strict";

  const form = document.getElementById("acervo-form");
  if (!form) return;

  // Marca JS ativo: habilita o drawer de filtros no mobile só quando há JS
  // (sem JS, a sidebar fica empilhada e acessível — progressive enhancement).
  document.documentElement.classList.add("js");

  const sidebar = document.getElementById("acervo-sidebar");
  const mobileToggle = form.querySelector(".acervo-mobile-toggle");
  const activeBadge = form.querySelector("#filter-active-count");
  const applyBtn = form.querySelector(".btn-apply");

  // === Auto-submit em mudança (debounced para slider) ===
  let submitTimer = null;
  function debouncedSubmit(delay) {
    if (submitTimer) clearTimeout(submitTimer);
    submitTimer = setTimeout(() => form.submit(), delay);
  }

  // Checkboxes de faceta: limpa cascata + submit imediato
  form.addEventListener("change", function (e) {
    const target = e.target;
    if (!target || !target.matches("input[type=checkbox].facet-input")) return;

    // Comportamento de "rádio dentro do grupo" — só um valor por filtro
    const param = target.name;
    form.querySelectorAll(`input[name="${param}"]`).forEach((el) => {
      if (el !== target) el.checked = false;
    });

    // Cascata: trocar Categoria zera Subcategoria + Microcategoria; trocar Subcategoria zera Microcategoria
    if (param === "category_id") {
      clearGroup("subcategoria_id");
      clearGroup("microcategoria_id");
    } else if (param === "subcategoria_id") {
      clearGroup("microcategoria_id");
    } else if (param === "assunto_id") {
      // Assunto é eixo paralelo, não invalida hierarquia mas dispara recálculo
    }

    debouncedSubmit(50);
  });

  function clearGroup(paramName) {
    form.querySelectorAll(`input[name="${paramName}"]`).forEach((el) => {
      el.checked = false;
    });
  }

  // Year inputs (number): submit ao perder foco / Enter
  form.querySelectorAll('#ano_min, #ano_max').forEach((input) => {
    input.addEventListener("change", () => debouncedSubmit(100));
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        form.submit();
      }
    });
  });

  // Ordenação (Autor/Título/Ano): auto-submit ao trocar
  const sortSelect = form.querySelector('select[name="sort"]');
  if (sortSelect) {
    sortSelect.addEventListener("change", () => form.submit());
  }

  // === Range slider duplo de ano ===
  const yearRange = form.querySelector(".year-range");
  if (yearRange) {
    const minInput = yearRange.querySelector("#ano_min");
    const maxInput = yearRange.querySelector("#ano_max");
    const minHandle = yearRange.querySelector(".year-handle-min");
    const maxHandle = yearRange.querySelector(".year-handle-max");
    const fill = yearRange.querySelector(".year-track-fill");

    const ABS_MIN = parseInt(yearRange.dataset.min, 10);
    const ABS_MAX = parseInt(yearRange.dataset.max, 10);
    const RANGE = Math.max(ABS_MAX - ABS_MIN, 1);

    function updateFill() {
      const lo = parseInt(minHandle.value, 10);
      const hi = parseInt(maxHandle.value, 10);
      const left = ((lo - ABS_MIN) / RANGE) * 100;
      const right = 100 - ((hi - ABS_MIN) / RANGE) * 100;
      fill.style.left = `${left}%`;
      fill.style.right = `${right}%`;
    }

    function syncFromHandles() {
      let lo = parseInt(minHandle.value, 10);
      let hi = parseInt(maxHandle.value, 10);
      if (lo > hi) {
        // Não deixar handles cruzarem
        if (event && event.target === minHandle) lo = hi;
        else hi = lo;
        minHandle.value = lo;
        maxHandle.value = hi;
      }
      minInput.value = lo;
      maxInput.value = hi;
      updateFill();
    }

    function syncFromInputs() {
      let lo = parseInt(minInput.value, 10);
      let hi = parseInt(maxInput.value, 10);
      if (Number.isNaN(lo)) lo = ABS_MIN;
      if (Number.isNaN(hi)) hi = ABS_MAX;
      lo = Math.max(ABS_MIN, Math.min(lo, ABS_MAX));
      hi = Math.max(ABS_MIN, Math.min(hi, ABS_MAX));
      if (lo > hi) lo = hi;
      minHandle.value = lo;
      maxHandle.value = hi;
      updateFill();
    }

    minHandle.addEventListener("input", syncFromHandles);
    maxHandle.addEventListener("input", syncFromHandles);
    minHandle.addEventListener("change", () => debouncedSubmit(150));
    maxHandle.addEventListener("change", () => debouncedSubmit(150));
    minInput.addEventListener("input", syncFromInputs);
    maxInput.addEventListener("input", syncFromInputs);

    updateFill();
  }

  // === Drawer mobile ===
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", function () {
      const isOpen = sidebar.classList.toggle("is-open");
      mobileToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      document.body.classList.toggle("acervo-drawer-open", isOpen);
    });

    // Fechar drawer ao clicar no overlay (área fora da sidebar)
    document.addEventListener("click", function (e) {
      if (
        sidebar.classList.contains("is-open") &&
        !sidebar.contains(e.target) &&
        !mobileToggle.contains(e.target)
      ) {
        sidebar.classList.remove("is-open");
        mobileToggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("acervo-drawer-open");
      }
    });

    // Tecla ESC fecha drawer
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && sidebar.classList.contains("is-open")) {
        sidebar.classList.remove("is-open");
        mobileToggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("acervo-drawer-open");
        mobileToggle.focus();
      }
    });
  }

  // === Botão "Aplicar filtros" só faz sentido sem JS — esconder com JS ativo ===
  if (applyBtn) {
    applyBtn.style.display = "none";
  }
})();
