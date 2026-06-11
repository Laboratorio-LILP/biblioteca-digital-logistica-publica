/* Detalhe do documento — copiar referência e permalink.
 *
 * Progressive enhancement / CSP-safe (script-src 'self'): apenas addEventListener
 * e navigator.clipboard (com fallback execCommand para contexto não-seguro).
 * Feedback acessível: troca o rótulo para "Copiado!" por ~2s e anuncia numa
 * região aria-live (eMAG / WCAG 4.1.3). Sem JS, o texto da referência continua
 * visível e selecionável manualmente.
 */
(function () {
  "use strict";

  var statusEl = document.querySelector("[data-copy-status]");

  function announce(msg) {
    if (!statusEl) return;
    statusEl.textContent = "";       // força o leitor de tela a reanunciar
    statusEl.textContent = msg;
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      try {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.position = "absolute";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        resolve();
      } catch (e) { reject(e); }
    });
  }

  function feedback(btn, okMsg) {
    var label = btn.querySelector(".copy-label");
    var original = label ? label.textContent : null;
    if (label) label.textContent = "Copiado!";
    btn.classList.add("is-copied");
    announce(okMsg);
    setTimeout(function () {
      if (label && original !== null) label.textContent = original;
      btn.classList.remove("is-copied");
    }, 2000);
  }

  function wire(btn, getText, okMsg) {
    btn.addEventListener("click", function () {
      var text = getText();
      if (!text) return;
      copyText(text)
        .then(function () { feedback(btn, okMsg); })
        .catch(function () { announce("Não foi possível copiar. Selecione e copie manualmente."); });
    });
  }

  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    wire(btn, function () {
      var sel = btn.getAttribute("data-copy");
      var el = sel && document.querySelector(sel);
      return el ? el.textContent.trim().replace(/\s+/g, " ") : "";
    }, "Referência copiada para a área de transferência.");
  });

  document.querySelectorAll("[data-copy-link]").forEach(function (btn) {
    wire(btn, function () { return window.location.href; },
         "Link copiado para a área de transferência.");
  });
})();
