/*
 * home.js — "Carregar mais" da Home (Temas em alta) + revelação por chip.
 *
 * Melhoria progressiva: SEM JS, todos os temas/documentos aparecem e os chips
 * funcionam como âncoras nativas. COM JS, oculta os extras (além de 2) e ativa
 * os botões. CSP-safe: apenas addEventListener, sem handlers inline.
 */
(function () {
    'use strict';

    var DOCS_VISIVEIS = 2;   // documentos por tema inicialmente visíveis (1 linha)
    var TEMAS_VISIVEIS = 2;  // temas inicialmente visíveis

    function reduzMovimento() {
        return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    /* Oculta os documentos além dos 2 primeiros num tema e ativa o botão. */
    function initDocs(bloco) {
        var grid = bloco.querySelector('.doc-grid');
        if (!grid) return;
        var cards = grid.querySelectorAll('.doc-card');
        if (cards.length <= DOCS_VISIVEIS) return;
        for (var i = DOCS_VISIVEIS; i < cards.length; i++) {
            cards[i].classList.add('is-hidden');
        }
        var btn = bloco.querySelector('[data-mais-docs]');
        if (!btn) return;
        btn.classList.remove('is-hidden');
        btn.addEventListener('click', function () {
            for (var j = DOCS_VISIVEIS; j < cards.length; j++) {
                cards[j].classList.remove('is-hidden');
            }
            btn.setAttribute('aria-expanded', 'true');
            btn.classList.add('is-hidden');
            if (cards[DOCS_VISIVEIS]) cards[DOCS_VISIVEIS].focus({ preventScroll: true });
        });
    }

    var Temas = {
        init: function () {
            this.blocos = Array.prototype.slice.call(document.querySelectorAll('[data-tema]'));
            if (!this.blocos.length) return;

            // (a) documentos por tema
            this.blocos.forEach(initDocs);

            // (b) temas além dos 2 primeiros começam ocultos
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
