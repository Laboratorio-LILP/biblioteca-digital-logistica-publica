/*
 * home.js — "Carregar mais temas" da Home (Temas em alta) + revelação por chip.
 *
 * Melhoria progressiva: SEM JS, todos os temas aparecem e os chips funcionam como
 * âncoras nativas. COM JS, oculta os temas além dos 2 primeiros e ativa o botão
 * "Carregar mais temas". CSP-safe: apenas addEventListener, sem handlers inline.
 */
(function () {
    'use strict';

    var TEMAS_VISIVEIS = 2;  // temas inicialmente visíveis

    function reduzMovimento() {
        return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    var Temas = {
        init: function () {
            this.blocos = Array.prototype.slice.call(document.querySelectorAll('[data-tema]'));
            if (!this.blocos.length) return;

            // temas além dos 2 primeiros começam ocultos
            for (var i = TEMAS_VISIVEIS; i < this.blocos.length; i++) {
                this.blocos[i].classList.add('is-hidden');
            }
            this.btnTemas = document.querySelector('[data-mais-temas]');
            if (this.btnTemas && this.blocos.length > TEMAS_VISIVEIS) {
                this.btnTemas.classList.remove('is-hidden');
                this.btnTemas.addEventListener('click', this.revelarProximo.bind(this));
            }

            // (c) chips em "Explorar o acervo": revelam o tema-alvo (fora de ordem)
            var chips = document.querySelectorAll('[data-tema-target]');
            for (i = 0; i < chips.length; i++) {
                chips[i].addEventListener('click', this.onChip.bind(this));
            }
        },

        primeiroOculto: function () {
            for (var i = 0; i < this.blocos.length; i++) {
                if (this.blocos[i].classList.contains('is-hidden')) return this.blocos[i];
            }
            return null;
        },

        // Some o botão de temas quando não houver mais nenhum tema oculto.
        atualizarBotaoTemas: function () {
            if (this.btnTemas && !this.primeiroOculto()) {
                this.btnTemas.classList.add('is-hidden');
            }
        },

        // Botão "Carregar mais temas": revela o PRIMEIRO ainda oculto (regra
        // estável mesmo que um chip já tenha revelado outro fora de ordem).
        revelarProximo: function () {
            var alvo = this.primeiroOculto();
            if (alvo) {
                alvo.classList.remove('is-hidden');
                this.focar(alvo);
            }
            this.atualizarBotaoTemas();
        },

        // Chip: revela SÓ o tema correspondente (fora de ordem), rola e foca.
        onChip: function (event) {
            var slug = event.currentTarget.getAttribute('data-tema-target');
            var alvo = document.getElementById('tema-' + slug);
            if (!alvo) return;   // sem alvo → deixa a âncora nativa agir
            event.preventDefault();
            alvo.classList.remove('is-hidden');
            this.atualizarBotaoTemas();
            alvo.scrollIntoView({ behavior: reduzMovimento() ? 'auto' : 'smooth', block: 'start' });
            this.focar(alvo);
        },

        focar: function (el) {
            if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
            el.focus({ preventScroll: true });
        }
    };

    function init() {
        try { Temas.init(); } catch (e) { console.error('[BDLP] Temas init falhou:', e); }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
