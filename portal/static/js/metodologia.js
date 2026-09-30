/*
 * metodologia.js — página Metodologia (Conceitos e coleções · Categorias · Assuntos).
 *
 * Porte do metodologia.js da entrega HTML do protótipo do Eduardo
 * (dudyfarias/biblioteca › frontend/html, 15/09/2026). Três melhorias
 * progressivas, sem JS a página funciona: (1) abas — as três vêm no HTML e a
 * troca só alterna [hidden], atualiza URL e título (history) e avisa a seta-guia,
 * nada recarrega; (2) trilha dos seis campos — o cartão apontado por mouse, foco
 * ou toque mostra a explicação no painel (desktop) ou sob o cartão (celular);
 * setas ← → e Home/End percorrem os campos; (3) navegador de assuntos — busca
 * sem acento em nome, caracterização, explicação e foco, seis cartões à vista e
 * "Ver todos". CSP-safe: só addEventListener, sem handlers inline; o DOM é
 * alterado só por atributos e textContent.
 */
(function () {
  "use strict";

  document.querySelectorAll("[data-classification-trail]").forEach(function (root) {
    var steps = root.querySelector("ol");
    var status = root.querySelector('[role="status"]');
    var desktop = window.matchMedia("(min-width: 721px)");
    var mobile = window.matchMedia("(max-width: 720px)");
    var fields = Array.prototype.map.call(root.querySelectorAll("li[data-trail-field]"), function (item) {
      var button = item.querySelector("button");
      var ids = button.getAttribute("aria-controls").split(/\s+/);
      return {
        item: item,
        button: button,
        name: button.querySelector("strong").textContent,
        panel: document.getElementById(ids[0]),
        mobilePanel: document.getElementById(ids[1])
      };
    });
    if (!fields.length) return;
    var initial = -1;
    fields.forEach(function (f, i) { if (initial < 0 && f.button.getAttribute("aria-pressed") === "true") initial = i; });
    var selected = initial < 0 ? null : initial;

    function render() {
      fields.forEach(function (f, index) {
        var active = index === selected;
        f.item.classList.toggle("is-selected", active);
        f.button.setAttribute("aria-pressed", String(active));
        f.button.setAttribute("aria-expanded", String(active));
        f.mobilePanel.hidden = !active;
        f.panel.hidden = index !== (selected === null ? 0 : selected);
      });
      var message = selected === null ? "Explicação recolhida" : "Campo selecionado: " + fields[selected].name;
      if (status && status.textContent !== message) status.textContent = message;
    }

    fields.forEach(function (f, index) {
      f.button.addEventListener("pointerenter", function (event) {
        if (event.pointerType !== "mouse" || !desktop.matches || steps.querySelector(":focus-visible")) return;
        selected = index;
        render();
      });
      f.button.addEventListener("focus", function () {
        if (!desktop.matches || !f.button.matches(":focus-visible")) return;
        selected = index;
        render();
      });
      f.button.addEventListener("click", function () {
        selected = mobile.matches && selected === index ? null : index;
        render();
      });
      f.button.addEventListener("keydown", function (event) {
        if (!desktop.matches) return;
        var last = fields.length - 1;
        var next = event.key === "ArrowRight" ? Math.min(index + 1, last)
          : event.key === "ArrowLeft" ? Math.max(index - 1, 0)
          : event.key === "Home" ? 0
          : event.key === "End" ? last
          : null;
        if (next === null) return;
        event.preventDefault();
        fields[next].button.focus();
      });
    });

    desktop.addEventListener("change", function (event) {
      if (event.matches) {
        if (selected === null) selected = 0;
        render();
      }
    });

    render();
  });

  function normalizeSearch(value) {
    return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").trim();
  }

  document.querySelectorAll(".method-subject-browser").forEach(function (root) {
    var input = root.querySelector(".method-subject-input");
    var clear = root.querySelector(".method-subject-clear");
    var counter = root.querySelector(".method-subject-count");
    var toggle = root.querySelector(".method-subject-more");
    var empty = root.querySelector(".method-subject-empty");
    var reset = root.querySelector(".method-subject-reset");
    if (!input || !toggle) return;
    var subjects = Array.prototype.map.call(root.querySelectorAll("details.method-subject"), function (item) {
      var body = item.querySelector(".method-subject-body p");
      var summary = item.querySelector(".method-subject-summary");
      return {
        item: item,
        searchable: [
          item.querySelector(".method-subject-name").textContent,
          summary ? summary.textContent : "",
          body ? body.textContent : "",
          item.dataset.subjectFocus || ""
        ].map(normalizeSearch)
      };
    });
    var total = subjects.length;
    var expanded = toggle.getAttribute("aria-expanded") === "true";

    function render() {
      var isSearching = input.value !== "";
      var query = normalizeSearch(input.value);
      var matching = subjects.filter(function (s) {
        return s.searchable.some(function (value) { return value.indexOf(query) !== -1; });
      });
      var visible = isSearching || expanded ? matching : matching.slice(0, 6);
      subjects.forEach(function (s) {
        var show = visible.indexOf(s) !== -1;
        s.item.hidden = !show;
        if (!show) s.item.open = false;   // um cartão escondido não fica aberto ao voltar
      });
      clear.hidden = !isSearching;
      empty.hidden = matching.length !== 0;
      toggle.hidden = isSearching || total <= 6;
      toggle.setAttribute("aria-expanded", String(expanded));
      toggle.textContent = expanded ? "Mostrar menos" : "Ver todos os assuntos";
      counter.textContent = isSearching || !expanded
        ? visible.length + " de " + total + " assuntos"
        : total + " assuntos";
    }

    function clearSearch() {
      input.value = "";
      render();
      input.focus();
    }

    input.addEventListener("input", render);
    clear.addEventListener("click", clearSearch);
    reset.addEventListener("click", clearSearch);
    toggle.addEventListener("click", function (event) {
      var focusRevealed = !expanded && event.detail === 0;   // ativado pelo teclado: foco vai ao 7º cartão
      expanded = !expanded;
      render();
      if (focusRevealed && subjects[6]) {
        var summary = subjects[6].item.querySelector("summary");
        if (summary) summary.focus();
      }
    });

    render();
  });

  /* Abas da Metodologia. Qualquer link da página para o endereço de uma aba
     (as próprias abas, o breadcrumb, "aba Categorias" no Saiba mais, o menu)
     troca abertura + painel no lugar; ← → Home/End percorrem as abas com
     ativação automática; voltar/avançar do navegador refaz a troca (popstate). */
  var abasRoot = document.querySelector("[data-metodologia-abas]");
  if (abasRoot && window.history && typeof window.history.pushState === "function") {
    var tabs = Array.prototype.slice.call(abasRoot.querySelectorAll('[role="tab"]'));
    var heros = Array.prototype.slice.call(document.querySelectorAll("[data-aba-hero]"));
    var abas = tabs.map(function (tab) {
      return {
        chave: tab.getAttribute("data-aba"),
        tab: tab,
        painel: document.getElementById(tab.getAttribute("aria-controls")),
        caminho: tab.pathname.replace(/\/?$/, "/")
      };
    });
    var atual = null;

    /* Salto ao topo sem animação. O html tem scroll-behavior: smooth; como a troca
       de [hidden] logo antes deixa o estilo sujo, o "auto" inline só vale depois
       de um recálculo forçado (sem ele, o salto vira animação — medido). O
       behavior "instant" cobre o mesmo caso; o fallback é para navegador antigo. */
    function rolarAoTopo() {
      var raiz = document.documentElement;
      var anterior = raiz.style.scrollBehavior;
      raiz.style.scrollBehavior = "auto";
      void raiz.offsetHeight;
      try { window.scrollTo({ top: 0, behavior: "instant" }); } catch (e) { window.scrollTo(0, 0); }
      raiz.style.scrollBehavior = anterior;
    }

    function abaDoCaminho(pathname) {
      var caminho = pathname.replace(/\/?$/, "/");
      for (var i = 0; i < abas.length; i++) if (abas[i].caminho === caminho) return abas[i];
      return null;
    }

    function ativar(aba, opcoes) {
      abas.forEach(function (a) {
        var on = a === aba;
        a.tab.setAttribute("aria-selected", String(on));
        a.tab.tabIndex = on ? 0 : -1;
        if (a.painel) a.painel.hidden = !on;
      });
      heros.forEach(function (h) { h.hidden = h.getAttribute("data-aba-hero") !== aba.chave; });
      var titulo = aba.tab.getAttribute("data-titulo");
      if (titulo) document.title = titulo;
      if (opcoes.push && aba !== atual) history.pushState({ aba: aba.chave }, "", aba.tab.href);
      atual = aba;
      if (opcoes.scroll) rolarAoTopo();                                     // como uma página nova
      if (opcoes.focus) aba.tab.focus();
      document.dispatchEvent(new CustomEvent("bdlp:secoes-mudaram"));         // seta-guia recolhe as âncoras visíveis
    }

    abas.forEach(function (a) { if (a.tab.getAttribute("aria-selected") === "true") atual = a; });
    if (atual) {
      history.replaceState({ aba: atual.chave }, "");
      /* Tabindex itinerante só com JS: no HTML as três abas são links na ordem de
         Tab, para quem navega por teclado sem script. */
      abas.forEach(function (a) { a.tab.tabIndex = a === atual ? 0 : -1; });
    }

    document.addEventListener("click", function (event) {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      var link = event.target.closest ? event.target.closest("a[href]") : null;
      if (!link || link.target || link.hash || link.origin !== location.origin) return;
      var aba = abaDoCaminho(link.pathname);
      if (!aba) return;
      event.preventDefault();
      ativar(aba, { push: true, scroll: true });
      /* Link do breadcrumb ou de dentro de um painel: ele some com a aba anterior
         e o foco cairia no vazio — vai para a aba que acabou de abrir. */
      if (link.closest("[hidden]")) aba.tab.focus({ preventScroll: true });
    });

    tabs.forEach(function (tab, index) {
      tab.addEventListener("keydown", function (event) {
        var total = tabs.length;
        var next = event.key === "ArrowRight" ? (index + 1) % total
          : event.key === "ArrowLeft" ? (index - 1 + total) % total
          : event.key === "Home" ? 0
          : event.key === "End" ? total - 1
          : null;
        if (next === null) return;
        event.preventDefault();
        ativar(abas[next], { push: true, scroll: true, focus: true });
      });
    });

    window.addEventListener("popstate", function () {
      var aba = abaDoCaminho(location.pathname);
      if (aba && aba !== atual) ativar(aba, { push: false, scroll: false });   // o navegador restaura a rolagem
    });
  }
})();
