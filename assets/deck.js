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

/* 2026-11-final-tech P04：Near／Far 互動示意。只在頁面有 [data-nearfar] 時執行，其餘簡報不受影響。
   參數依 Wiki（path/mask-to-path、control/pid-core）：遠處權重 0.2、LPF τ＝0.15 s、近列 0.6、遠列 0.45、誤差夾在 ±1。
   SVG 中的車道寬與座標是概念示意，不是相機實測座標。 */
(() => {
  'use strict';
  const roots = document.querySelectorAll('[data-nearfar]');
  if (!roots.length) return;
  const NS = 'http://www.w3.org/2000/svg';
  const W = 320, H = 180, CX = 160;          // 概念畫面（非實際 1280×720 座標）
  const Y_NEAR = 0.6 * H, Y_FAR = 0.45 * H;  // 取樣列高度比例（Wiki：0.6／0.45）
  const TAU = 0.15, DT = 1 / 23.4;           // τ 依 Wiki；DT 依最終版約每秒 23.4 格（推算示意）
  const DEF = { near: 0, far: 0, w: 0.2 };
  const SCEN = { straight: { near: 0, far: 0 }, left: { near: -0.05, far: -0.45 }, right: { near: 0.05, far: 0.45 } };
  const clip = (x, a, b) => Math.max(a, Math.min(b, x));
  const laneW = y => 90 + (300 - 90) * (y - 60) / (H - 60);   // 概念：越遠越窄（透視）
  const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };

  roots.forEach(root => {
    const svg = root.querySelector('svg.nf-scene'), plot = root.querySelector('svg.nf-plot');
    const inp = { near: root.querySelector('[name=nf-near]'), far: root.querySelector('[name=nf-far]'), w: root.querySelector('[name=nf-w]') };
    const out = n => root.querySelector('[data-out=' + n + ']');
    svg.setAttribute('viewBox', `0 44 ${W} ${H - 44}`);   // 只顯示路面部分
    plot.setAttribute('viewBox', '0 0 200 70');

    function drawScene(v) {
      svg.textContent = '';
      el('rect', { x: 0, y: 0, width: W, height: H, fill: '#16222c' }, svg);
      const ratio = laneW(Y_FAR) / laneW(Y_NEAR);                  // W(far)/W(near)
      const xn = CX + v.near * 150, xf = CX + v.far * 150 * ratio; // 遠點像素偏移＝已換算誤差 × 遠處尺度
      const xb = xn - (xf - xn) * 0.5, xt = xf + (xf - xn) * 0.8;   // 底部與上方延伸點（示意）
      const key = [[xb, H], [xn, Y_NEAR], [xf, Y_FAR], [xt, 55]], pts = [];
      for (let s = 0; s < key.length - 1; s++) for (let i = 0; i < 6; i++) {   // 分段線性插值，讓線段較平順
        const u = i / 6; pts.push([key[s][0] + (key[s + 1][0] - key[s][0]) * u, key[s][1] + (key[s + 1][1] - key[s][1]) * u]);
      }
      pts.push(key[key.length - 1]);
      const poly = (dx, col, wid, dash) => el('polyline', { points: pts.map(([x, y]) => `${(x + dx(y)).toFixed(1)},${y.toFixed(1)}`).join(' '), fill: 'none', stroke: col, 'stroke-width': wid, 'stroke-dasharray': dash || '' }, svg);
      poly(y => -laneW(y) / 2, '#e8eef2', 5); poly(y => laneW(y) / 2, '#e8eef2', 5);          // 左右白線（示意）
      poly(() => 0, '#81e9c7', 2.2);                                                          // 中心路徑
      el('line', { x1: CX, y1: 50, x2: CX, y2: H, stroke: '#7f93a3', 'stroke-width': 1, 'stroke-dasharray': '3 3' }, svg);
      const row = (y, label, x, col) => {
        el('line', { x1: 4, y1: y, x2: W - 4, y2: y, stroke: col, 'stroke-width': 1, 'stroke-dasharray': '5 4' }, svg);
        el('line', { x1: CX, y1: y, x2: x, y2: y, stroke: col, 'stroke-width': 3 }, svg);
        el('circle', { cx: x, cy: y, r: 4.5, fill: col }, svg);
        const bg = el('rect', { fill: '#0d1822', opacity: 0.85, rx: 3 }, svg);
        const t = el('text', { x: W - 6, y: y - 5, fill: col, 'font-size': 10, 'text-anchor': 'end' }, svg); t.textContent = label;
        try { const b = t.getBBox(); bg.setAttribute('x', b.x - 3); bg.setAttribute('y', b.y - 1); bg.setAttribute('width', b.width + 6); bg.setAttribute('height', b.height + 2); } catch (e) { bg.remove(); }
      };
      row(Y_FAR, 'Far 遠列（高度 0.45）', xf, '#ffbe75');
      row(Y_NEAR, 'Near 近列（高度 0.6）', xn, '#81e9c7');
      const c = el('text', { x: CX + 4, y: H - 6, fill: '#9fb2c1', 'font-size': 9 }, svg); c.textContent = '畫面中心';
      const n = el('text', { x: 6, y: 56, fill: '#ffbe75', 'font-size': 9 }, svg); n.textContent = '概念示意，非相機實測座標';
    }

    function drawPlot(v, eStatic) {
      plot.textContent = '';
      el('rect', { x: 0, y: 0, width: 200, height: 70, fill: '#101b25' }, plot);
      const raw = v.w * (v.far - v.near), k = DT / (TAU + DT), N = Math.round(1 / DT);
      const ys = []; let d = 0;
      for (let i = 0; i <= N; i++) { ys.push(clip(v.near + d, -1, 1)); d += k * (raw - d); }
      const lo = Math.min(v.near, eStatic) - 0.05, hi = Math.max(v.near, eStatic) + 0.05;
      const Y = e => 60 - 50 * (e - lo) / Math.max(0.1, hi - lo), X = i => 8 + 184 * i / N;
      el('line', { x1: 8, y1: Y(eStatic), x2: 192, y2: Y(eStatic), stroke: '#ffbe75', 'stroke-dasharray': '4 3', 'stroke-width': 1 }, plot);
      el('polyline', { points: ys.map((e, i) => `${X(i).toFixed(1)},${Y(e).toFixed(1)}`).join(' '), fill: 'none', stroke: '#81e9c7', 'stroke-width': 2 }, plot);
      const i15 = Math.round(TAU / DT);
      el('line', { x1: X(i15), y1: 6, x2: X(i15), y2: 64, stroke: '#5c7080', 'stroke-width': 1 }, plot);
      const t1 = el('text', { x: X(i15) + 3, y: 66, fill: '#9fb2c1', 'font-size': 8 }, plot); t1.textContent = 't = τ = 0.15 s';
      const t2 = el('text', { x: 192, y: 66, fill: '#9fb2c1', 'font-size': 8, 'text-anchor': 'end' }, plot); t2.textContent = '1 s';
      return { e15: ys[i15], e1: ys[N], frac: raw === 0 ? null : (ys[i15] - v.near) / raw };
    }

    function update() {
      const v = { near: +inp.near.value, far: +inp.far.value, w: +inp.w.value };
      out('near').textContent = v.near.toFixed(2); out('far').textContent = v.far.toFixed(2); out('w').textContent = v.w.toFixed(2);
      const eStatic = clip(v.near + v.w * (v.far - v.near), -1, 1);
      out('static').textContent = (eStatic >= 0 ? '+' : '') + eStatic.toFixed(3);
      drawScene(v);
      const r = drawPlot(v, eStatic);
      out('dyn').textContent = (r.e15 >= 0 ? '+' : '') + r.e15.toFixed(3);
      out('dyn1').textContent = (r.e1 >= 0 ? '+' : '') + r.e1.toFixed(3);
      out('frac').textContent = r.frac === null ? '—' : Math.round(r.frac * 100) + '%';
    }
    function set(vals, btn) {
      for (const k in vals) inp[k].value = vals[k];
      root.querySelectorAll('.nf-btns button[data-scen]').forEach(b => b.classList.toggle('on', b === btn));
      update();
    }
    Object.values(inp).forEach(i => i.addEventListener('input', () => { root.querySelectorAll('.nf-btns button').forEach(b => b.classList.remove('on')); update(); }));
    root.querySelectorAll('.nf-btns button[data-scen]').forEach(b => b.addEventListener('click', () => set(SCEN[b.dataset.scen], b)));
    root.querySelector('.nf-btns button[data-reset]').addEventListener('click', () => set(Object.assign({}, DEF), root.querySelector('[data-scen=straight]')));
    set(Object.assign({}, DEF), root.querySelector('[data-scen=straight]'));
  });
})();
