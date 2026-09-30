/*
 * tools/auditoria_interface.js — rastreador da auditoria de interface (17/09/2026).
 *
 * Percorre as páginas públicas do portal em duas larguras (1440 e 390) e grava
 * um JSON com: status HTTP, erros de console/página/requisição, <title>, meta
 * description, canonical, lang, nº de h1, saltos de cabeçalho, ids duplicados,
 * ícones <use> sem símbolo, hrefs vazios, controles sem nome acessível, imagens
 * sem alt, vazamento de sintaxe de template, estouro horizontal e o status de
 * TODOS os links internos. É a linha de base de docs/auditorias/2026-09-17-*.
 *
 * Uso (portal no ar em http://localhost:8000):
 *   node tools/auditoria_interface.js <pasta-de-saida> [base-url]
 * Requer o puppeteer. Sem instalação própria, use o que vem empacotado no pa11y
 * e informe o caminho em PUPPETEER_PATH, por exemplo:
 *   PUPPETEER_PATH="$(npm root -g)/pa11y/node_modules/puppeteer" node tools/auditoria_interface.js …
 * Observação: o regex de placeholders casa "todo" em português (falso positivo
 * conhecido); "TODO" em páginas de documento vem de "MÉTODO" em caixa alta via CSS.
 */
const puppeteer = require(process.env.PUPPETEER_PATH || 'puppeteer');
const fs = require('fs');
const BASE = process.argv[3] || 'http://localhost:8000';
const PAGINAS = ['/', '/busca/', '/busca/?q=licita%C3%A7%C3%A3o', '/busca/?assunto_id=1&category_id=6&natureza=Contrata%C3%A7%C3%A3o%20de%20TIC', '/busca/?q=zzzzsemresultado',
  '/busca/?page=99', '/metodologia/', '/metodologia/categorias/', '/metodologia/assuntos/', '/colecao/1/', '/colecao/3/', '/documento/bdlp-000982/', '/documento/bdlp-000077/', '/documento/bdlp-000061/',
  '/sobre/', '/transparencia/', '/acessibilidade/', '/politica-de-privacidade/', '/politica-de-cookies/', '/mapa-do-site/', '/fale-conosco/', '/curadoria/', '/nao-existe/', '/colecao/999/'];
(async () => {
  const out = process.argv[2];
  const browser = await puppeteer.launch({ headless: 'new' });
  const consent = JSON.stringify({ versao: 1, funcionalidades: false, analytics: false });
  const resultados = []; const linksInternos = new Set();
  for (const path of PAGINAS) {
    for (const [vw, vh, rot] of [[1440, 900, 'desktop'], [390, 844, 'mobile']]) {
      const p = await browser.newPage();
      await p.evaluateOnNewDocument(c => localStorage.setItem('sp-lgpd-consent', c), consent);
      await p.setViewport({ width: vw, height: vh, deviceScaleFactor: 1 });
      const console_ = [], falhas = [], erros = [];
      p.on('console', m => { if (['error', 'warning'].includes(m.type())) console_.push(`${m.type()}: ${m.text().slice(0, 160)}`); });
      p.on('pageerror', e => erros.push(String(e).slice(0, 160)));
      p.on('requestfailed', r => falhas.push(`${r.url().slice(0, 120)} ${r.failure()?.errorText || ''}`));
      let status = null;
      try { const resp = await p.goto(BASE + path, { waitUntil: 'networkidle0', timeout: 30000 }); status = resp && resp.status(); } catch (e) { erros.push('goto: ' + e.message.slice(0, 120)); }
      const dados = await p.evaluate(() => {
        const txt = document.body.innerText;
        const heads = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => ({ n: +h.tagName[1], t: h.textContent.trim().replace(/\s+/g, ' ').slice(0, 60) }));
        const saltos = []; for (let i = 1; i < heads.length; i++) if (heads[i].n > heads[i - 1].n + 1) saltos.push(`${heads[i - 1].n}→${heads[i].n} "${heads[i].t}"`);
        const ids = [...document.querySelectorAll('[id]')].map(e => e.id); const dup = ids.filter((x, i) => ids.indexOf(x) !== i);
        const usos = [...document.querySelectorAll('use')].map(u => u.getAttribute('href') || u.getAttribute('xlink:href')).filter(Boolean);
        const iconesQuebrados = [...new Set(usos.filter(h => h.startsWith('#') && !document.getElementById(h.slice(1))))];
        const links = [...document.querySelectorAll('a[href]')];
        const hrefVazio = links.filter(a => ['#', '', 'javascript:void(0)'].includes(a.getAttribute('href').trim())).map(a => a.textContent.trim().slice(0, 40));
        const semNome = [...document.querySelectorAll('a,button')].filter(e => !(e.textContent.trim() || e.getAttribute('aria-label') || e.getAttribute('title') || e.querySelector('img[alt]'))).map(e => e.outerHTML.slice(0, 80));
        const imgSemAlt = [...document.querySelectorAll('img:not([alt])')].map(i => i.getAttribute('src'));
        const internos = links.map(a => a.href).filter(h => h.startsWith(location.origin));
        const meta = document.querySelector('meta[name=description]');
        return {
          title: document.title, metaDesc: meta ? meta.content.slice(0, 120) : null, lang: document.documentElement.lang,
          canonical: !!document.querySelector('link[rel=canonical]'), h1: heads.filter(h => h.n === 1).length, saltosDeCabecalho: saltos, idsDuplicados: [...new Set(dup)],
          iconesQuebrados, hrefVazio, semNomeAcessivel: semNome.slice(0, 5), imgSemAlt, vazamentoTemplate: /\{[#%]|[#%]\}|\{\{/.test(txt),
          placeholders: (txt.match(/\b(lorem|TODO|XXX|TBD)\b/gi) || []).slice(0, 3), duplosEspacos: (txt.match(/\S {2,}\S/g) || []).length,
          overflowX: document.scrollingElement.scrollWidth > window.innerWidth, larguraDoc: document.scrollingElement.scrollWidth, internos,
        };
      });
      dados.internos.forEach(h => linksInternos.add(h)); delete dados.internos;
      resultados.push({ path, rot, status, console: console_, pageErrors: erros, requestsFalhas: falhas, ...dados });
      await p.close();
    }
  }
  // checagem de links internos (GET, sem seguir redirecionamento)
  const p = await browser.newPage(); const links = {};
  for (const h of [...linksInternos].sort()) {
    try { const r = await p.goto(h, { waitUntil: 'domcontentloaded', timeout: 20000 }); links[h] = r ? r.status() : 'sem resposta'; } catch (e) { links[h] = 'erro: ' + e.message.slice(0, 60); }
  }
  await browser.close();
  fs.writeFileSync(`${out}/crawl.json`, JSON.stringify({ resultados, links }, null, 1));
  const ruins = Object.entries(links).filter(([, s]) => s !== 200);
  console.log('páginas rastreadas:', resultados.length / 2, '| links internos únicos:', Object.keys(links).length, '| links com status ≠ 200:', ruins.length);
  for (const [h, s] of ruins) console.log('  ', s, h);
})().catch(e => { console.error(e); process.exit(1); });
