/*
 * seta-secoes.js — seta-guia de seções (Home e Coleções).
 *
 * Botão flutuante ([data-seta-secoes]) que rola até a próxima seção lógica
 * da página (âncoras [data-sec], na ordem do DOM). Na última seção, vira
 * "Voltar ao topo". Desloca-se para cima do banner de cookies LGPD enquanto
 * ele estiver visível. Melhoria progressiva: sem JS a seta permanece
 * [hidden]. CSP-safe: apenas addEventListener, sem handlers inline.
 * Spec: docs/superpowers/specs/2026-07-29-seta-secoes-design.md
 */
(function () {
    'use strict';

    function reduzMovimento() {
        return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    var Seta = {
        init: function () {
            this.btn = document.querySelector('[data-seta-secoes]');
            this.secoes = Array.prototype.slice.call(document.querySelectorAll('[data-sec]'));
            if (!this.btn || this.secoes.length < 2 || !window.IntersectionObserver) return;

            this.uso = this.btn.querySelector('use');
            this.visiveis = [];
            this.idx = 0;   // última seção corrente conhecida (retida quando nada intersecta)
            this._renderizado = -1;

            this.btn.addEventListener('click', this.onClick.bind(this));
            this.observarSecoes();
            this.observarBanner();
            this.atualizar();
            this.revelar();
        },

        /* Seção "corrente" = a de maior índice com o topo acima do meio da
           tela. O rootMargin restringe o observer à metade de cima do
           viewport; reflows (ex.: "Carregar mais temas") reobservam sozinhos. */
        observarSecoes: function () {
            var self = this;
            this.io = new IntersectionObserver(function (entries) {
                for (var i = 0; i < entries.length; i++) {
                    var idx = self.secoes.indexOf(entries[i].target);
                    if (idx >= 0) self.visiveis[idx] = entries[i].isIntersecting;
                }
                for (var j = self.secoes.length - 1; j >= 0; j--) {
                    if (self.visiveis[j]) { self.idx = j; break; }
                }
                // sem nenhuma visível (ex.: rodapé mais alto que o viewport), retém o último índice
                self.atualizar();
            }, { rootMargin: '0px 0px -50% 0px', threshold: 0 });
            for (var i = 0; i < this.secoes.length; i++) {
                this.io.observe(this.secoes[i]);
            }
        },

        correnteIdx: function () {
            return this.idx;
        },

        naUltima: function () {
            return this.correnteIdx() >= this.secoes.length - 1;
        },

        atualizar: function () {
            var idx = this.correnteIdx();
            if (idx === this._renderizado) return;
            this._renderizado = idx;

            if (this.naUltima()) {
                this.uso.setAttribute('href', '#fi-chevron-up');
                this.btn.setAttribute('aria-label', 'Voltar ao topo');
            } else {
                var proxima = this.secoes[idx + 1];
                this.uso.setAttribute('href', '#fi-chevron-down');
                this.btn.setAttribute('aria-label', 'Ir para: ' + proxima.getAttribute('data-sec'));
            }
        },

        onClick: function () {
            var alvo;
            /* 'auto' delega ao scroll-behavior do CSS — o modo instantâneo em reduced-motion depende do override html { scroll-behavior: auto } no portal.css */
            if (this.naUltima()) {
                alvo = this.secoes[0];
                window.scrollTo({ top: 0, behavior: reduzMovimento() ? 'auto' : 'smooth' });
            } else {
                alvo = this.secoes[this.correnteIdx() + 1];
                alvo.scrollIntoView({ behavior: reduzMovimento() ? 'auto' : 'smooth', block: 'start' });
            }
            this.focar(alvo);   // teclado/leitor de tela acompanham a navegação
        },

        focar: function (el) {
            if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
            el.focus({ preventScroll: true });
        },

        /* Banner LGPD: faixa fixa no rodapé até o consentimento. Enquanto
           visível, publica a altura em --sp-seta-offset para a seta subir. */
        observarBanner: function () {
            this.banner = document.querySelector('[data-cookies-banner]');
            if (!this.banner) return;
            var ajustar = this.ajustarOffset.bind(this);
            if (window.MutationObserver) {
                this.mo = new MutationObserver(ajustar);
                this.mo.observe(this.banner, { attributes: true, attributeFilter: ['hidden'] });
            }
            window.addEventListener('resize', ajustar);
            this.ajustarOffset();
        },

        ajustarOffset: function () {
            var visivel = this.banner && !this.banner.hasAttribute('hidden');
            var altura = visivel ? this.banner.offsetHeight + 12 : 0;
            document.documentElement.style.setProperty('--sp-seta-offset', altura + 'px');
        },

        /* Revela com fade: sai do [hidden] e só então .is-on transiciona a
           opacidade (dois rAFs para o display mudar antes da transição). */
        revelar: function () {
            var btn = this.btn;
            btn.removeAttribute('hidden');
            requestAnimationFrame(function () {
                requestAnimationFrame(function () { btn.classList.add('is-on'); });
            });
        }
    };

    function init() {
        try { Seta.init(); } catch (e) { console.error('[BDLP] Seta init falhou:', e); }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
