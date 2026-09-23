/* Acervo — filtros em cascata + drawer mobile + atualização sem voltar ao topo.
 *
 * Melhoria progressiva (set/2026, "toda vez que clica, ele vai lá pra cima"):
 *   SEM JS: o <form> envia por GET, o botão "Aplicar filtros" funciona e a
 *   página recarrega já posicionada em #acervo-resultados (âncora do action e
 *   dos links de chips, "Limpar tudo" e paginação).
 *   COM JS: mudar uma faceta, a ordenação ou o ano — e clicar num chip, em
 *   "Limpar tudo" ou na paginação — busca o HTML COMPLETO da mesma view
 *   (fetch) e troca só três regiões: #acervo-sidebar, #acervo-resultados e
 *   #acervo-paginacao. A rolagem não se move, o foco volta ao controle tocado,
 *   os <details> abertos continuam abertos e o drawer mobile fica como estava.
 *   A URL passa a refletir a busca (pushState) e "voltar/avançar" refaz a
 *   troca (popstate) sem recarregar. Qualquer falha — rede, HTTP ≠ 200, HTML
 *   sem as regiões — cai no envio clássico do form (que aterrissa na âncora).
 *
 * CSP script-src 'self': só addEventListener, sem handler inline, sem eval.
 * Sub-path (/Biblioteca/): usa form.action, a.href e location — nunca um
 * caminho absoluto chumbado. O cabeçalho X-Requested-With é só informativo.
 */
(function () {
  "use strict";

  var form = document.getElementById("acervo-form");
  if (!form) return;

  // Marca JS ativo: habilita o drawer mobile e esconde o botão "Aplicar" (CSS).
  document.documentElement.classList.add("js");

  var sidebar = document.getElementById("acervo-sidebar");
  var resultados = document.getElementById("acervo-resultados");
  var wrapper = document.querySelector(".acervo-results");

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

  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Troca parcial só quando o navegador tem tudo que ela precisa; senão, o
  // envio clássico do form continua valendo (com a âncora).
  var podeTrocar = !!(window.fetch && window.DOMParser && window.URL && window.URLSearchParams &&
    window.FormData && window.history && window.history.pushState && sidebar && resultados);

  // Elementos que vivem DENTRO das regiões trocadas são consultados na hora
  // (referência guardada ficaria obsoleta depois do fetch).
  function statusEl() { return document.getElementById("acervo-status"); }
  function mobileToggle() { return form.querySelector(".acervo-mobile-toggle"); }

  function clearGroup(name) {
    form.querySelectorAll('input[name="' + name + '"]').forEach(function (el) { el.checked = false; });
  }

  function chaveDe(href) {
    var u = new URL(href, location.href);
    return u.pathname + u.search;
  }
  var chaveAtual = podeTrocar ? chaveDe(location.href) : "";

  // URL da busca a partir do form: sem `page`, sem campos vazios, sem hash.
  function urlDoForm() {
    var u = new URL(form.action, location.href);
    var params = new URLSearchParams();
    new FormData(form).forEach(function (valor, nome) {
      if (nome === "page") return;
      if (typeof valor !== "string" || valor.trim() === "") return;
      params.append(nome, valor);
    });
    u.search = params.toString();
    u.hash = "";
    return u.href;
  }

  // Envio clássico (fallback): a página recarrega e aterrissa em #acervo-resultados.
  function envioClassico() {
    if (wrapper && !reduce) wrapper.classList.add("is-updating");
    var s = statusEl();
    if (s) s.textContent = "Atualizando resultados…";
    form.submit();
  }

  // ---- estado a preservar na troca: <details> abertos, foco, drawer, rolagem ----
  function chaveDetails(d) {
    var s = d.querySelector(":scope > summary");
    return (s ? s.textContent : "").replace(/\s+/g, " ").trim();
  }
  function detailsAbertos() {
    var estado = {};
    sidebar.querySelectorAll("details").forEach(function (d) { estado[chaveDetails(d)] = d.open; });
    return estado;
  }
  function reaplicarDetails(estado) {
    sidebar.querySelectorAll("details").forEach(function (d) {
      var k = chaveDetails(d);
      if (Object.prototype.hasOwnProperty.call(estado, k)) d.open = estado[k];
    });
  }
  function focoAtual() {
    var a = document.activeElement;
    if (!a || !form.contains(a)) return null;
    return { id: a.id || "", name: a.getAttribute("name") || "", value: a.value || "", tag: a.tagName };
  }
  // Âncora visual da barra: o primeiro título de faceta ("Coleção"). O bloco
  // "Seus filtros" entra/sai/cresce ACIMA dele a cada troca, e a lista inteira se
  // deslocava ~97 px na tela (o checkbox tocado "descia", ou "subia" ao desmarcar
  // o último filtro). A diferença de posição da âncora depois da troca é
  // compensada na rolagem PRÓPRIA da barra (sticky/drawer com overflow), para o
  // controle continuar sob o cursor — a rolagem da janela não muda.
  function ancoraDaBarra() {
    var s = sidebar.querySelector("details.side-section > summary");
    return s ? { top: s.getBoundingClientRect().top } : null;
  }
  function compensarAncora(ancora) {
    if (!ancora) return;
    var s = sidebar.querySelector("details.side-section > summary");
    if (!s) return;
    var delta = Math.round(s.getBoundingClientRect().top - ancora.top);
    if (!delta) return;
    var max = sidebar.scrollHeight - sidebar.clientHeight;
    if (max <= 0) return;                                   // barra sem rolagem própria: nada a compensar
    sidebar.scrollTop = Math.max(0, Math.min(max, sidebar.scrollTop + delta));
  }
  function focar(el) {
    if (!el) return;
    // Só ganha tabindex="-1" quem não é focável por natureza: <summary>, input,
    // link etc. já têm tabIndex >= 0 e um "-1" os tiraria da ordem de Tab
    // (revisão de 14/09/2026 — WCAG 2.1.1).
    if (!el.hasAttribute("tabindex") && el.tabIndex < 0) el.setAttribute("tabindex", "-1");
    try { el.focus({ preventScroll: true }); } catch (e) { el.focus(); }
  }
  // Devolve o foco ao controle tocado (por id ou name+value) ou, na falta dele,
  // ao primeiro dos seletores de `fallbacks` que existir — em ordem de prioridade.
  function restaurarFoco(foco, fallbacks) {
    var el = null;
    if (foco) {
      if (foco.id) el = document.getElementById(foco.id);
      if (!el && foco.name) {
        var cands = form.querySelectorAll(foco.tag.toLowerCase() + '[name="' + foco.name + '"]');
        for (var i = 0; i < cands.length; i++) {
          if (foco.tag !== "INPUT" || cands[i].value === foco.value) { el = cands[i]; break; }
        }
      }
    }
    for (var j = 0; !el && fallbacks && j < fallbacks.length; j++) el = form.querySelector(fallbacks[j]);
    focar(el);
  }

  // ---- fetch + troca das três regiões ----
  var seq = 0;
  var controller = null;

  function trocar(url, opts) {
    opts = opts || {};
    if (!podeTrocar) { (opts.fallback || envioClassico)(); return; }

    var minha = ++seq;                      // resposta atrasada de um pedido anterior é ignorada
    if (controller) controller.abort();
    controller = window.AbortController ? new AbortController() : null;

    if (wrapper && !reduce) wrapper.classList.add("is-updating");
    resultados.setAttribute("aria-busy", "true");
    var s = statusEl();
    if (s) s.textContent = "Atualizando resultados…";

    var init = { headers: { "X-Requested-With": "fetch" }, credentials: "same-origin" };
    if (controller) init.signal = controller.signal;

    fetch(url, init)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.text();
      })
      .then(function (html) {
        if (minha !== seq) return;
        var doc = new DOMParser().parseFromString(html, "text/html");
        var novoSidebar = doc.getElementById("acervo-sidebar");
        var novoRes = doc.getElementById("acervo-resultados");
        if (!novoSidebar || !novoRes) throw new Error("HTML sem as regiões esperadas");
        var novaPag = doc.getElementById("acervo-paginacao");

        // O usuário mexeu no form enquanto o pedido corria (ano digitado, segundo
        // clique num multi-select): esta resposta já nasceu velha — descarta e
        // reagenda com o estado vivo, em vez de sobrescrever o que ele editou.
        if (opts.doForm && (timer || urlDoForm() !== url)) { agendar(500); return; }

        // Nada é alterado antes de o HTML novo ser validado: sem estado meio-trocado.
        // O HTML vem da MESMA view, na mesma origem, renderizado pelos templates
        // (auto-escape do Django) — o mesmo nível de confiança da página inicial;
        // por isso innerHTML, sem sanitizador extra.
        var estado = detailsAbertos();
        var foco = focoAtual();
        var drawerAberto = sidebar.classList.contains("is-open");
        var sx = window.scrollX, sy = window.scrollY;
        var sbScroll = sidebar.scrollTop;                    // rolagem própria da barra (sticky/drawer)
        var ancora = ancoraDaBarra();

        sidebar.innerHTML = novoSidebar.innerHTML;
        resultados.innerHTML = novoRes.innerHTML;
        var pagAtual = document.getElementById("acervo-paginacao");
        if (novaPag && pagAtual) {
          pagAtual.innerHTML = novaPag.innerHTML;
        } else if (novaPag && !pagAtual) {
          form.appendChild(document.adoptNode(novaPag));   // paginação passou a existir
        } else if (!novaPag && pagAtual) {
          pagAtual.parentNode.removeChild(pagAtual);        // paginação deixou de existir
        }

        reaplicarDetails(estado);
        var t = mobileToggle();
        if (t) t.setAttribute("aria-expanded", drawerAberto ? "true" : "false");
        sidebar.scrollTop = sbScroll;                       // innerHTML pode zerar a rolagem da barra
        // Instantâneo: o html tem scroll-behavior: smooth e um ajuste animado
        // apareceria como "a página deslizou". O leitor continua onde estava.
        window.scrollTo({ left: sx, top: sy, behavior: "instant" });
        compensarAncora(ancora);                            // lista da barra não se desloca sob o cursor

        var titulo = doc.querySelector("title");
        if (titulo) document.title = titulo.textContent;
        if (opts.push) {
          if (chaveDe(url) === chaveAtual) history.replaceState({ acervo: true }, "", url);
          else history.pushState({ acervo: true }, "", url);
        }
        chaveAtual = chaveDe(location.href);

        // A caixa de busca do herói fica fora das regiões trocadas: quando a URL
        // não veio do form (chip, paginação, voltar/avançar), sincroniza o q.
        if (!opts.doForm) {
          var qUrl = new URL(url, location.href).searchParams.get("q") || "";
          var caixa = form.querySelector('input[name="q"]');
          if (caixa && caixa.value !== qUrl) caixa.value = qUrl;
        }

        if (opts.focus !== false || opts.focusFallback) {
          restaurarFoco(opts.focus === false ? null : foco, opts.focusFallback);
        }

        var count = resultados.querySelector(".results-bar__count");
        var s2 = statusEl();
        if (s2) {
          s2.textContent = "Resultados atualizados: " +
            (count ? count.textContent.replace(/\s+/g, " ").trim() : "lista atualizada");
        }
      })
      .catch(function (err) {
        if (err && err.name === "AbortError") return;      // substituído por um pedido mais novo
        if (minha !== seq) return;
        (opts.fallback || envioClassico)();
      })
      .then(function () {                                   // "finally"
        if (minha !== seq) return;
        if (wrapper) wrapper.classList.remove("is-updating");
        resultados.setAttribute("aria-busy", "false");
      });
  }

  function atualizarPeloForm() {
    trocar(urlDoForm(), { push: true, doForm: true, fallback: envioClassico });
  }

  var timer = null;
  function agendar(delay) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(function () { timer = null; atualizarPeloForm(); }, delay);
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

  function ehAno(el) { return !!el && (el.id === "ano_min" || el.id === "ano_max"); }

  // O spinner (setas ↑↓) de um <input type=number> VAZIO salta para o atributo
  // `min` (1991), ignorando o placeholder — daí "subo e vai para 1991". Correção:
  // se o valor pulou de vazio direto para o min, parte do placeholder (o limite do
  // campo: 1991 no "De", 2025 no "Até"). Delegado (os inputs são recriados na
  // troca): o valor anterior é lembrado no foco e a cada entrada.
  form.addEventListener("focusin", function (e) {
    if (ehAno(e.target)) e.target.dataset.valorAnterior = e.target.value;
  });
  form.addEventListener("input", function (e) {
    var el = e.target;
    if (!ehAno(el)) return;
    var prev = el.dataset.valorAnterior || "";
    if (prev === "" && el.value === el.getAttribute("min")) {
      el.value = el.getAttribute("placeholder") || el.value;
    }
    el.dataset.valorAnterior = el.value;
  });

  // Auto-atualização em mudança de faceta (cascata), ordenação e ano.
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
      agendar(40);
      return;
    }
    if (t.matches && t.matches('select[name="sort"]')) { atualizarPeloForm(); return; }
    if (ehAno(t)) { validarAno(); agendar(500); }
  });

  // Enter nos inputs de ano atualiza na hora.
  form.addEventListener("keydown", function (e) {
    if (ehAno(e.target) && e.key === "Enter") {
      e.preventDefault();
      validarAno();
      atualizarPeloForm();
    }
  });

  // Chips de "Seus filtros", "Limpar tudo" e paginação: links GET (funcionam sem
  // JS, com a âncora); com JS, o mesmo caminho de fetch + troca. Cliques com
  // modificador (nova aba etc.) seguem o navegador.
  form.addEventListener("click", function (e) {
    if (!podeTrocar || e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest ? e.target.closest("a[href]") : null;
    if (!a || !form.contains(a)) return;
    var chip = a.matches(".applied-filter-chip__remove");
    var limpar = a.matches(".clear-btn") || !!a.closest(".empty-state");
    var pag = !!a.closest(".pagination");
    if (!chip && !limpar && !pag) return;
    e.preventDefault();
    var href = a.href;
    var u = new URL(href, location.href);
    u.hash = "";
    // Ordem de prioridade do foco: chip removido → outro chip restante; senão
    // (ou "Limpar tudo") → primeira faceta; paginação → página corrente.
    var chipsRestantes = ".applied-filter-chip__remove";
    var primeiraFaceta = "#acervo-sidebar details.side-section > summary";
    var foco = chip ? [chipsRestantes, primeiraFaceta]
      : limpar ? [primeiraFaceta]
      : ['.pagination [aria-current="page"]'];
    trocar(u.href, { push: true, focus: false, focusFallback: foco, fallback: function () { location.assign(href); } });
  });

  // Voltar/avançar: refaz a troca para a URL restaurada, sem recarregar.
  window.addEventListener("popstate", function () {
    if (!podeTrocar) return;
    if (chaveDe(location.href) === chaveAtual) return;   // só o hash mudou (ex.: skip link)
    trocar(location.href, { push: false, focus: false, fallback: function () { location.reload(); } });
  });

  // Drawer mobile (delegado: o botão vive na região trocada).
  if (sidebar) {
    var drawer = function (aberto) {
      sidebar.classList.toggle("is-open", aberto);
      var t = mobileToggle();
      if (t) t.setAttribute("aria-expanded", aberto ? "true" : "false");
      document.body.classList.toggle("acervo-drawer-open", aberto);
    };
    form.addEventListener("click", function (e) {
      var t = e.target.closest ? e.target.closest(".acervo-mobile-toggle") : null;
      if (!t) return;
      drawer(!sidebar.classList.contains("is-open"));
    });
    document.addEventListener("click", function (e) {
      if (!sidebar.classList.contains("is-open")) return;
      var t = mobileToggle();
      if (sidebar.contains(e.target) || (t && t.contains(e.target))) return;
      drawer(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && sidebar.classList.contains("is-open")) {
        drawer(false);
        focar(mobileToggle());
      }
    });
  }
})();
