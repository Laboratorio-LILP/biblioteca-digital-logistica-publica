/*
 * Portal Biblioteca Digital de Logística Pública (BDLP)
 * Laboratório de Inovação em Logística Pública (LILP) | SGGD
 *
 * main.js — controles do lado cliente:
 *   - A11y:    fonte +/-, alto contraste, persistência localStorage
 *   - Atalhos: Alt+1..4 navegando para conteúdo/menu/busca/rodapé
 *   - Menu:    hambúrguer mobile com aria-expanded e ESC fecha
 *   - Cookies: banner LGPD (carregado em commit posterior)
 *
 * Conformidade: eMAG 3.1 (R6.1 atalhos, R5.4 foco visível),
 *               WCAG 2.0 AA (1.4.3 contraste, 1.4.4 redimensionar texto),
 *               Lei 13.709/2018 (LGPD — cookies).
 *
 * Arquivo único IIFE — sem build tooling. Compatível com CSP
 * script-src 'self' (sem inline handlers, apenas addEventListener).
 */

(function () {
    'use strict';

    /* ========================================================
       Constantes e estado
       ======================================================== */
    var STORAGE_KEYS = {
        contraste: 'sp-a11y:contraste',
        fonte:     'sp-a11y:fonte-escala',
        cookies:   'sp-lgpd-consent'
    };

    var FONTE_MIN = -2;  // escala mínima (12.5% menor)
    var FONTE_MAX = 4;   // escala máxima (50% maior)

    /* ========================================================
       Módulo: Acessibilidade (controles de fonte e contraste)
       ======================================================== */
    var A11y = {
        init: function () {
            this.applyStoredPrefs();
            this.bindFonteControls();
            this.bindContrasteControl();
        },

        bindFonteControls: function () {
            var btns = document.querySelectorAll('[data-a11y-action="font-up"], [data-a11y-action="font-down"]');
            for (var i = 0; i < btns.length; i++) {
                btns[i].addEventListener('click', this.onFontClick.bind(this));
            }
        },

        bindContrasteControl: function () {
            var btn = document.querySelector('[data-a11y-action="contrast"]');
            if (!btn) return;
            btn.addEventListener('click', this.onContrasteClick.bind(this));
        },

        onFontClick: function (event) {
            var action = event.currentTarget.getAttribute('data-a11y-action');
            var atual = this.getFonteEscala();
            var novo = action === 'font-up' ? atual + 1 : atual - 1;
            if (novo < FONTE_MIN) novo = FONTE_MIN;
            if (novo > FONTE_MAX) novo = FONTE_MAX;
            this.setFonteEscala(novo);
        },

        onContrasteClick: function (event) {
            var btn = event.currentTarget;
            var ativo = document.body.classList.toggle('sp-alto-contraste');
            btn.setAttribute('aria-pressed', ativo ? 'true' : 'false');
            try {
                localStorage.setItem(STORAGE_KEYS.contraste, ativo ? '1' : '0');
            } catch (e) { /* localStorage indisponível */ }
        },

        getFonteEscala: function () {
            try {
                var v = parseInt(localStorage.getItem(STORAGE_KEYS.fonte) || '0', 10);
                return isNaN(v) ? 0 : v;
            } catch (e) {
                return 0;
            }
        },

        setFonteEscala: function (escala) {
            try {
                localStorage.setItem(STORAGE_KEYS.fonte, String(escala));
            } catch (e) { /* localStorage indisponível */ }
            this.applyFonteEscala(escala);
        },

        applyFonteEscala: function (escala) {
            var html = document.documentElement;
            // Limpa classes anteriores
            for (var i = FONTE_MIN; i <= FONTE_MAX; i++) {
                if (i > 0) html.classList.remove('sp-fonte-aumentada-' + i);
                if (i < 0) html.classList.remove('sp-fonte-diminuida-' + Math.abs(i));
            }
            if (escala > 0) html.classList.add('sp-fonte-aumentada-' + escala);
            if (escala < 0) html.classList.add('sp-fonte-diminuida-' + Math.abs(escala));
        },

        applyStoredPrefs: function () {
            // Fonte
            this.applyFonteEscala(this.getFonteEscala());
            // Contraste
            try {
                var contraste = localStorage.getItem(STORAGE_KEYS.contraste) === '1';
                if (contraste) {
                    document.body.classList.add('sp-alto-contraste');
                    var btn = document.querySelector('[data-a11y-action="contrast"]');
                    if (btn) btn.setAttribute('aria-pressed', 'true');
                }
            } catch (e) { /* ignora */ }
        }
    };

    /* ========================================================
       Módulo: Atalhos de teclado (eMAG R6.1)
       Alt+1: conteúdo principal
       Alt+2: menu principal
       Alt+3: busca
       Alt+4: rodapé
       Implementado via JS além do accesskey HTML porque alguns
       browsers não respeitam accesskey em <main>/<nav>/<footer>.
       ======================================================== */
    var Atalhos = {
        init: function () {
            document.addEventListener('keydown', this.onKey.bind(this));
        },

        onKey: function (event) {
            // Alt + dígito (sem Ctrl/Meta para não conflitar com encurtadores do browser)
            if (!event.altKey || event.ctrlKey || event.metaKey) return;
            var alvo = null;
            switch (event.key) {
                case '1': alvo = document.getElementById('sp-conteudo'); break;
                case '2': alvo = document.getElementById('sp-menu'); break;
                case '3': alvo = document.getElementById('sp-busca-input') || document.getElementById('sp-busca'); break;
                case '4': alvo = document.getElementById('sp-rodape'); break;
                default: return;
            }
            if (!alvo) return;
            event.preventDefault();
            // Se o alvo não é tabable nativamente, garante tabindex temporário
            if (!alvo.hasAttribute('tabindex')) {
                alvo.setAttribute('tabindex', '-1');
            }
            alvo.focus();
            alvo.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    /* ========================================================
       Módulo: Menu hambúrguer mobile
       Toggle com aria-expanded; ESC fecha; clique fora fecha;
       primeiro link recebe foco ao abrir.
       ======================================================== */
    var Menu = {
        init: function () {
            this.toggleBtn = document.querySelector('[data-nav-toggle]');
            this.nav = document.getElementById('sp-menu');
            if (!this.toggleBtn || !this.nav) return;

            this.toggleBtn.addEventListener('click', this.toggle.bind(this));
            document.addEventListener('keydown', this.onKey.bind(this));
            document.addEventListener('click', this.onDocClick.bind(this));
        },

        abrir: function () {
            this.nav.classList.add('is-open');
            this.toggleBtn.setAttribute('aria-expanded', 'true');
            this.toggleBtn.setAttribute('aria-label', 'Fechar menu de navegação');
            var primeiro = this.nav.querySelector('a');
            if (primeiro) primeiro.focus();
        },

        fechar: function (devolverFoco) {
            this.nav.classList.remove('is-open');
            this.toggleBtn.setAttribute('aria-expanded', 'false');
            this.toggleBtn.setAttribute('aria-label', 'Abrir menu de navegação');
            if (devolverFoco) this.toggleBtn.focus();
        },

        toggle: function () {
            if (this.nav.classList.contains('is-open')) {
                this.fechar(false);
            } else {
                this.abrir();
            }
        },

        onKey: function (event) {
            if (event.key === 'Escape' && this.nav.classList.contains('is-open')) {
                this.fechar(true);
            }
        },

        onDocClick: function (event) {
            if (!this.nav.classList.contains('is-open')) return;
            if (this.nav.contains(event.target) || this.toggleBtn.contains(event.target)) return;
            this.fechar(false);
        }
    };

    /* ========================================================
       Módulo: Banner de cookies LGPD
       Aparece se localStorage[STORAGE_KEYS.cookies] estiver vazio.
       Persiste a escolha como JSON com timestamp e versão da política.
       Não dispara cookies de análise antes de consentimento explícito.
       ======================================================== */
    var CONSENT_VERSION = 1;

    var Cookies = {
        init: function () {
            this.banner = document.querySelector('[data-cookies-banner]');
            this.modal = document.querySelector('[data-cookies-modal]');
            if (!this.banner) return;

            // Mostra o banner apenas se ainda não houver registro de consentimento
            // ou se a versão da política tiver mudado.
            var consent = this.getConsent();
            if (!consent || consent.versao !== CONSENT_VERSION) {
                this.exibirBanner();
            }

            this.bindAcoes();
        },

        bindAcoes: function () {
            var self = this;
            var nodes = document.querySelectorAll('[data-cookies-action]');
            for (var i = 0; i < nodes.length; i++) {
                nodes[i].addEventListener('click', function (event) {
                    var acao = event.currentTarget.getAttribute('data-cookies-action');
                    self.onAcao(acao, event);
                });
            }
            // Tecla ESC fecha o modal se aberto
            document.addEventListener('keydown', function (event) {
                if (event.key === 'Escape' && self.modal && !self.modal.hasAttribute('hidden')) {
                    self.fecharModal();
                }
            });
        },

        onAcao: function (acao, event) {
            switch (acao) {
                case 'accept-all':
                    this.salvarConsentimento({ funcionalidades: true, analytics: true });
                    this.ocultarBanner();
                    break;
                case 'essential-only':
                    this.salvarConsentimento({ funcionalidades: false, analytics: false });
                    this.ocultarBanner();
                    break;
                case 'customize':
                    this.abrirModal();
                    break;
                case 'save-customize':
                    var func = !!document.querySelector('[data-cookies-cat="funcionalidades"]:checked');
                    var anal = !!document.querySelector('[data-cookies-cat="analytics"]:checked');
                    this.salvarConsentimento({ funcionalidades: func, analytics: anal });
                    this.fecharModal();
                    this.ocultarBanner();
                    break;
                case 'close-modal':
                    this.fecharModal();
                    break;
            }
        },

        exibirBanner: function () {
            this.banner.removeAttribute('hidden');
        },

        ocultarBanner: function () {
            this.banner.setAttribute('hidden', '');
        },

        abrirModal: function () {
            if (!this.modal) return;
            // Preenche checkboxes com valores atuais (se houver)
            var consent = this.getConsent();
            var inputs = this.modal.querySelectorAll('[data-cookies-cat]');
            for (var i = 0; i < inputs.length; i++) {
                var cat = inputs[i].getAttribute('data-cookies-cat');
                inputs[i].checked = !!(consent && consent.categorias && consent.categorias[cat]);
            }
            this.modal.removeAttribute('hidden');
            this.previousFocus = document.activeElement;
            // Foca primeiro elemento focável dentro do modal
            var primeiro = this.modal.querySelector('button, input, [tabindex]');
            if (primeiro) primeiro.focus();
            // Focus trap: contém o foco no modal (aria-modal exige; WCAG 2.4.3).
            this._trap = this._onModalKeydown.bind(this);
            this.modal.addEventListener('keydown', this._trap);
        },

        fecharModal: function () {
            if (!this.modal) return;
            this.modal.setAttribute('hidden', '');
            if (this._trap) { this.modal.removeEventListener('keydown', this._trap); this._trap = null; }
            if (this.previousFocus && this.previousFocus.focus) {
                this.previousFocus.focus();
            }
        },

        _focaveis: function () {
            if (!this.modal) return [];
            var sel = 'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])';
            return Array.prototype.filter.call(
                this.modal.querySelectorAll(sel),
                function (el) { return el.offsetParent !== null; }   // só visíveis
            );
        },

        _onModalKeydown: function (event) {
            if (event.key !== 'Tab') return;
            var f = this._focaveis();
            if (!f.length) return;
            var primeiro = f[0], ultimo = f[f.length - 1];
            if (event.shiftKey && document.activeElement === primeiro) {
                event.preventDefault(); ultimo.focus();
            } else if (!event.shiftKey && document.activeElement === ultimo) {
                event.preventDefault(); primeiro.focus();
            }
        },

        getConsent: function () {
            try {
                var raw = localStorage.getItem(STORAGE_KEYS.cookies);
                if (!raw) return null;
                return JSON.parse(raw);
            } catch (e) {
                return null;
            }
        },

        salvarConsentimento: function (categorias) {
            var registro = {
                versao: CONSENT_VERSION,
                timestamp: new Date().toISOString(),
                categorias: {
                    necessarios:     true,
                    funcionalidades: !!categorias.funcionalidades,
                    analytics:       !!categorias.analytics
                }
            };
            try {
                localStorage.setItem(STORAGE_KEYS.cookies, JSON.stringify(registro));
            } catch (e) { /* localStorage indisponível */ }
        }
    };

    /* ========================================================
       Inicialização
       ======================================================== */
    function init() {
        try { A11y.init(); }    catch (e) { console.error('[BDLP] A11y init falhou:', e); }
        try { Atalhos.init(); } catch (e) { console.error('[BDLP] Atalhos init falhou:', e); }
        try { Menu.init(); }    catch (e) { console.error('[BDLP] Menu init falhou:', e); }
        try { Cookies.init(); } catch (e) { console.error('[BDLP] Cookies init falhou:', e); }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
