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

  // === Preservar posição de rolagem + grupos abertos através do reload ===
  // O auto-submit recarrega a página (GET). Sem isto, o navegador volta ao topo
  // e o usuário "perde o lugar" ao clicar numa faceta lá embaixo (relato Laís).
  const RESTORE_KEY = "acervo:restore";
  // Apenas estes grupos são single-select (rádio); os demais são multi-select.
  const SINGLE_SELECT = new Set(["colecao_v6", "category_id", "subcategoria_id", "microcategoria_id"]);

  function groupKey(details) {
    // Chave estável do <details>: texto do summary sem a contagem (dígitos/parênteses).
    const summary = details.querySelector("summary");
    return (summary ? summary.textContent : "").replace(/[\d()]/g, "").replace(/\s+/g, " ").trim();
  }

  function saveState() {
    try {
      const open = [];
      form.querySelectorAll("details.filter-group[open]").forEach((d) => open.push(groupKey(d)));
      sessionStorage.setItem(RESTORE_KEY, JSON.stringify({ y: window.scrollY, open: open }));
    } catch (e) { /* sessionStorage indisponível: degrada sem quebrar */ }
  }

  function restoreState() {
    let state = null;
    try {
      state = JSON.parse(sessionStorage.getItem(RESTORE_KEY) || "null");
      sessionStorage.removeItem(RESTORE_KEY);
    } catch (e) { return; }
    if (!state) return;
    if (Array.isArray(state.open) && state.open.length) {
      const wanted = new Set(state.open);
      form.querySelectorAll("details.filter-group").forEach((d) => {
        if (wanted.has(groupKey(d))) d.open = true;
      });
    }
    // scrollTo instantâneo (sem smooth) — respeita prefers-reduced-motion.
    if (typeof state.y === "number") window.scrollTo(0, state.y);
  }

  // Submete o form preservando o estado (rolagem + grupos abertos).
  function doSubmit() {
    saveState();
    form.submit();
  }

  // === Auto-submit em mudança (debounced para slider) ===
  let submitTimer = null;
  function debouncedSubmit(delay) {
    if (submitTimer) clearTimeout(submitTimer);
    submitTimer = setTimeout(doSubmit, delay);
  }

  // Checkboxes de faceta: limpa cascata + submit imediato
  form.addEventListener("change", function (e) {
    const target = e.target;
    if (!target || !target.matches("input[type=checkbox].facet-input")) return;

    // Single-select (rádio) só nos grupos de Coleção e da hierarquia de
    // Categorias; os eixos paralelos (Assunto, Natureza, Tipo) são multi-select.
    const param = target.name;
    if (SINGLE_SELECT.has(param)) {
      form.querySelectorAll(`input[name="${param}"]`).forEach((el) => {
        if (el !== target) el.checked = false;
      });
    }

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
        doSubmit();
      }
    });
  });

  // Ordenação (Autor/Título/Ano): auto-submit ao trocar
  const sortSelect = form.querySelector('select[name="sort"]');
  if (sortSelect) {
    sortSelect.addEventListener("change", doSubmit);
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

  // Restaurar posição de rolagem/grupos abertos após o reload do auto-submit.
  requestAnimationFrame(restoreState);
})();
