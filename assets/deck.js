/* 共用簡報程式：換頁、目錄搜尋、講者備註、長頁、全螢幕、列印。
   每份簡報只寫 <section class="slide">，外框由這裡產生。規則見 AGENTS.md。 */
(() => {
  'use strict';
  const $ = (q, r = document) => r.querySelector(q);
  const $$ = (q, r = document) => [...r.querySelectorAll(q)];
  const main = $('main.deck');
  if (!main) return;
  const brand = main.dataset.brand || 'AUTOCAR DEVLOG';
  const sub = main.dataset.sub || '';
  const home = main.dataset.home || '../../index.html';
  const esc = s => s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  main.insertAdjacentHTML('beforebegin',
    `<header class="topbar"><div class="brand">${esc(brand)}<span>${esc(sub)}</span></div>
<nav class="top-actions" aria-label="簡報工具列">
<a class="home-link" href="${esc(home)}">← 講義庫</a>
<button id="tocToggle" aria-expanded="false" title="目錄與搜尋（T）">☰ 目錄</button>
<button id="notesToggle" aria-pressed="false" title="講者備註（N）">N <span class="label-hide">備註</span></button>
<button id="allToggle" aria-pressed="false" title="長頁／簡報（G）">G <span class="label-hide">長頁</span></button>
<button id="fullscreen" title="全螢幕（F）">⛶ <span class="label-hide">全螢幕</span></button>
<button id="print" class="hide-mobile" title="列印">列印</button></nav></header>
<div class="progress" aria-hidden="true"></div>
<div class="toc-shade"></div>
<aside class="toc-panel" id="tocPanel" aria-label="目錄"><div class="toc-header"><h2>章節 / 搜尋</h2><button id="tocClose" aria-label="關閉目錄">✕</button></div>
<input id="tocSearch" type="search" placeholder="搜尋關鍵字…" aria-label="搜尋簡報全文"/><div class="toc-items"></div></aside>`);
  main.insertAdjacentHTML('afterend',
    `<footer class="footer"><div><div class="footer-title" id="footerTitle"></div><div class="short-hints">← → 換頁　N 備註　T 目錄　G 長頁　F 全螢幕</div></div>
<div class="footer-right"><span class="pagecount" id="pagecount"></span><button id="prev">← 上一頁</button><button id="next">下一頁 →</button></div></footer>`);

  const slides = $$('.slide', main);
  const pad = n => String(n).padStart(2, '0');
  // 自動補上編號、id 與頁首，讓作者只需要寫 data-chapter / data-title / data-lead
  slides.forEach((s, i) => {
    const n = pad(i + 1);
    s.id = 's' + n;
    if (!$('.slide-header', s)) {
      const lead = s.dataset.lead ? `<p class="lead">${esc(s.dataset.lead)}</p>` : '';
      s.insertAdjacentHTML('afterbegin',
        `<header class="slide-header"><div class="eyebrow">${esc(s.dataset.chapter || '')} <span class="tag">${n}</span></div><h1>${esc(s.dataset.title || '')}</h1>${lead}</header>`);
    }
  });

  let index = 0, all = false;
  const baseTitle = document.title;
  function go(n, hash = true) {
    index = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, i) => s.classList.toggle('active', i === index));
    $('#pagecount').textContent = `${pad(index + 1)} / ${slides.length}`;
    $('#footerTitle').textContent = (slides[index].dataset.chapter || '') + '　/　' + (slides[index].dataset.title || '');
    $('#prev').disabled = index === 0;
    $('#next').disabled = index === slides.length - 1;
    $('.progress').style.width = (index + 1) / slides.length * 100 + '%';
    document.title = `${pad(index + 1)} · ${slides[index].dataset.title || ''}｜${baseTitle}`;
    if (hash) { try { history.replaceState(null, '', '#s' + pad(index + 1)); } catch (e) { } }
    if (all) slides[index].scrollIntoView({ block: 'start' }); else window.scrollTo(0, 0);
    $$('.toc-items button').forEach(b => b.classList.toggle('active', +b.dataset.index === index));
  }
  function renderToc(filter = '') {
    const q = filter.trim().toLowerCase(); let html = '', last = '';
    slides.forEach((s, i) => {
      if (q && !s.textContent.toLowerCase().includes(q)) return;
      if (s.dataset.chapter !== last) { last = s.dataset.chapter; html += `<div class="toc-section">${esc(last || '')}</div>`; }
      html += `<button type="button" data-index="${i}" class="${i === index ? 'active' : ''}"><small>${pad(i + 1)}</small>${esc(s.dataset.title || '')}</button>`;
    });
    $('.toc-items').innerHTML = html || '<p class="toc-empty">沒有符合的內容。</p>';
  }
  const toc = on => { document.body.classList.toggle('toc-open', on); $('#tocToggle').setAttribute('aria-expanded', on); if (on) $('#tocSearch').focus(); };
  const setNotes = on => { document.body.classList.toggle('show-notes', on); $('#notesToggle').classList.toggle('active', on); $('#notesToggle').setAttribute('aria-pressed', on); };
  const setAll = on => { all = on; document.body.classList.toggle('all-slides', on); $('#allToggle').classList.toggle('active', on); $('#allToggle').setAttribute('aria-pressed', on); go(index, false); };
  const fullscreen = () => { try { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); } catch (e) { } };

  $('#prev').onclick = () => go(index - 1);
  $('#next').onclick = () => go(index + 1);
  $('#tocToggle').onclick = () => toc(!document.body.classList.contains('toc-open'));
  $('#tocClose').onclick = () => toc(false);
  $('.toc-shade').onclick = () => toc(false);
  $('#tocSearch').oninput = e => renderToc(e.target.value);
  $('.toc-items').onclick = e => { const b = e.target.closest('button'); if (b) { go(+b.dataset.index); toc(false); } };
  $('#notesToggle').onclick = () => setNotes(!document.body.classList.contains('show-notes'));
  $('#allToggle').onclick = () => setAll(!all);
  $('#fullscreen').onclick = fullscreen;
  $('#print').onclick = () => window.print();
  document.addEventListener('keydown', e => {
    if (e.target.matches('input,textarea,select') || e.ctrlKey || e.metaKey || e.altKey) { if (e.key === 'Escape') toc(false); return; }
    const k = e.key;
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ') { e.preventDefault(); go(index + 1); }
    else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); go(index - 1); }
    else if (k === 'Home') go(0);
    else if (k === 'End') go(slides.length - 1);
    else if (k === 'n' || k === 'N') setNotes(!document.body.classList.contains('show-notes'));
    else if (k === 't' || k === 'T') { e.preventDefault(); toc(!document.body.classList.contains('toc-open')); }
    else if (k === 'g' || k === 'G') setAll(!all);
    else if (k === 'f' || k === 'F') fullscreen();
    else if (k === 'Escape') toc(false);
  });
  window.addEventListener('hashchange', () => { const m = location.hash.match(/^#s(\d+)$/); if (m) go(+m[1] - 1, false); });
  renderToc();
  const m = location.hash.match(/^#s(\d+)$/);
  go(m ? +m[1] - 1 : 0, false);
})();

/* LaTeX 數學式：簡報內有 \( … \) 或 \[ … \] 時才載入 KaTeX（固定版本 0.16.11）並自動排版；沒有數學式的簡報不受影響。 */
(() => {
  'use strict';
  const main = document.querySelector('main.deck');
  const BS = String.fromCharCode(92), html = main ? main.innerHTML : '';
  if (!main || (html.indexOf(BS + '(') < 0 && html.indexOf(BS + '[') < 0)) return;
  const CDN = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/';
  const css = document.createElement('link'); css.rel = 'stylesheet'; css.href = CDN + 'katex.min.css'; document.head.appendChild(css);
  const load = src => new Promise((ok, bad) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = bad; document.head.appendChild(s); });
  load(CDN + 'katex.min.js').then(() => load(CDN + 'contrib/auto-render.min.js')).then(() => {
    window.renderMathInElement(document.body, { delimiters: [{ left: BS + '[', right: BS + ']', display: true }, { left: BS + '(', right: BS + ')', display: false }], throwOnError: false });
  }).catch(() => {});
})();
