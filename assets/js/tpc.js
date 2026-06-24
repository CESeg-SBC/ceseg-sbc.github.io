// TPC × accepted-papers statistics page.
// Renders assets/data/tpc-stats.json into KPI cards, a correlation scatter,
// a per-edition table, and a global ranking. Pure vanilla + inline SVG, no deps.
// Translatable labels come from window.cesegI18n (site.js); dynamic content
// re-renders on the 'i18n:applied' event so language switches stay live.
(function () {
  const ROMAN = {2012:'XII',2013:'XIII',2014:'XIV',2015:'XV',2016:'XVI',2017:'XVII',
    2018:'XVIII',2019:'XIX',2020:'XX',2021:'XXI',2022:'XXII',2023:'XXIII',2024:'XXIV',2025:'XXV'};
  let DATA = null;

  function t(key, fallback) {
    const v = window.cesegI18n && window.cesegI18n.t ? window.cesegI18n.t(key) : null;
    return v == null ? fallback : v;
  }
  const esc = s => (s || '').replace(/[&<>"]/g, c =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
  const nf = n => (n == null ? '-' : String(n).replace('.', ','));

  async function boot() {
    const host = document.getElementById('tpcApp');
    if (!host) return;
    try {
      const res = await fetch('assets/data/tpc-stats.json', { cache: 'no-cache' });
      DATA = await res.json();
    } catch (e) {
      host.innerHTML = '<p class="tpc-error">' +
        t('tpc.loadError', 'Não foi possível carregar os dados.') + '</p>';
      return;
    }
    render();
    document.addEventListener('i18n:applied', render);
  }

  function render() {
    if (!DATA) return;
    renderKpis();
    renderCorr();
    renderEditions();
    renderRanking();
  }

  // ---- (summary) KPI cards ----
  function renderKpis() {
    const s = DATA.summary;
    const cards = [
      [nf(s.n_editions), t('tpc.kpiEditions', 'edições analisadas')],
      [nf(s.total_papers), t('tpc.kpiPapers', 'artigos (trilha principal)')],
      [nf(s.papers_with_tpc_pct) + '%', t('tpc.kpiPapersTpc', 'artigos com ≥1 autor do TPC')],
      [nf(s.distinct_tpc_people), t('tpc.kpiPeople', 'pessoas distintas no TPC')],
      [nf(s.distinct_tpc_publishers_pct) + '%', t('tpc.kpiPublishers', 'desses membros publicaram')],
      [nf(s.corr_tpcsize_papers), t('tpc.kpiCorr', 'correlação tamanho do TPC × artigos')],
    ];
    document.getElementById('tpcKpis').innerHTML = cards.map(([v, l]) =>
      `<div class="tpc-kpi"><span class="tpc-kpi-v">${esc(v)}</span>` +
      `<span class="tpc-kpi-l">${esc(l)}</span></div>`).join('');
  }

  // ---- (b) correlation scatter: TPC size × accepted papers ----
  function renderCorr() {
    const eds = DATA.editions;
    const W = 640, H = 380, P = 48;
    const xs = eds.map(e => e.tpc_size), ys = eds.map(e => e.total_papers);
    const xMin = Math.min(...xs), xMax = Math.max(...xs);
    const yMin = 0, yMax = Math.max(...ys);
    const sx = v => P + (v - xMin) / (xMax - xMin) * (W - 2 * P);
    const sy = v => H - P - (v - yMin) / (yMax - yMin) * (H - 2 * P);

    // least-squares regression line
    const n = xs.length, mx = xs.reduce((a, b) => a + b, 0) / n,
      my = ys.reduce((a, b) => a + b, 0) / n;
    let num = 0, den = 0;
    for (let i = 0; i < n; i++) { num += (xs[i] - mx) * (ys[i] - my); den += (xs[i] - mx) ** 2; }
    const slope = num / den, intercept = my - slope * mx;
    const lx1 = xMin, lx2 = xMax;

    const grid = [];
    for (let g = 0; g <= 4; g++) {
      const yv = Math.round(yMax * g / 4), y = sy(yv);
      grid.push(`<line x1="${P}" y1="${y}" x2="${W - P}" y2="${y}" class="tpc-grid"/>` +
        `<text x="${P - 8}" y="${y + 4}" class="tpc-axislbl" text-anchor="end">${yv}</text>`);
    }
    const pts = eds.map(e => {
      const x = sx(e.tpc_size), y = sy(e.total_papers);
      return `<g class="tpc-pt"><circle cx="${x}" cy="${y}" r="5"/>` +
        `<text x="${x}" y="${y - 9}" text-anchor="middle">${e.year}</text>` +
        `<title>${ROMAN[e.year] || ''} ${e.year} · TPC ${e.tpc_size} · ${e.total_papers} artigos</title></g>`;
    }).join('');

    const svg =
      `<svg viewBox="0 0 ${W} ${H}" class="tpc-svg" role="img" ` +
      `aria-label="${esc(t('tpc.corrAria', 'Dispersão: tamanho do TPC versus artigos aceitos por edição'))}">` +
      grid.join('') +
      `<line x1="${P}" y1="${H - P}" x2="${W - P}" y2="${H - P}" class="tpc-axis"/>` +
      `<line x1="${P}" y1="${P}" x2="${P}" y2="${H - P}" class="tpc-axis"/>` +
      `<line x1="${sx(lx1)}" y1="${sy(slope * lx1 + intercept)}" ` +
      `x2="${sx(lx2)}" y2="${sy(slope * lx2 + intercept)}" class="tpc-fit"/>` +
      pts +
      `<text x="${W / 2}" y="${H - 8}" text-anchor="middle" class="tpc-axistitle">` +
      esc(t('tpc.corrX', 'Nº de membros do TPC')) + `</text>` +
      `<text x="14" y="${H / 2}" text-anchor="middle" class="tpc-axistitle" ` +
      `transform="rotate(-90 14 ${H / 2})">` + esc(t('tpc.corrY', 'Artigos aceitos')) + `</text>` +
      `</svg>`;
    document.getElementById('tpcCorr').innerHTML = svg +
      `<p class="tpc-corr-note">${esc(t('tpc.corrCaption',
        'Cada ponto é uma edição. Correlação de Pearson r ='))} ` +
      `<b>${nf(DATA.summary.corr_tpcsize_papers)}</b>.</p>`;
  }

  // ---- (a,c) per-edition table with expandable detail ----
  function renderEditions() {
    const head =
      `<tr><th>${esc(t('tpc.thEdition', 'Edição'))}</th>` +
      `<th class="tpc-num">${esc(t('tpc.thTpc', 'TPC'))}</th>` +
      `<th class="tpc-num">${esc(t('tpc.thPapers', 'Artigos'))}</th>` +
      `<th class="tpc-num">${esc(t('tpc.thPapersTpc', 'Artigos c/ autor do TPC'))}</th>` +
      `<th class="tpc-num">${esc(t('tpc.thPublishers', 'Membros que publicaram'))}</th>` +
      `<th>${esc(t('tpc.thTop', 'Destaque da edição'))}</th></tr>`;

    const rows = DATA.editions.slice().reverse().map(e => {
      const top = e.ranking[0];
      const topTxt = top ? `${esc(top.name)} <span class="tpc-pill">${top.count}</span>` : '-';
      const pctBar = pct => `<span class="tpc-bar"><span style="width:${pct}%"></span></span>`;
      const detail = e.ranking.slice(0, 12).map(r =>
        `<li><span class="tpc-mname">${esc(r.name)}</span>` +
        `<span class="tpc-minst">${esc(r.inst)}</span>` +
        `<span class="tpc-pill">${r.count}</span></li>`).join('');
      return `<tr class="tpc-edrow" data-year="${e.year}">` +
        `<td><b>${ROMAN[e.year] || ''} ${e.year}</b></td>` +
        `<td class="tpc-num">${e.tpc_size}</td>` +
        `<td class="tpc-num">${e.total_papers}</td>` +
        `<td class="tpc-num">${e.papers_with_tpc_author} ` +
        `<span class="tpc-sub">(${nf(e.papers_with_tpc_pct)}%)</span>${pctBar(e.papers_with_tpc_pct)}</td>` +
        `<td class="tpc-num">${e.tpc_publishers} ` +
        `<span class="tpc-sub">(${nf(e.tpc_publishers_pct)}%)</span></td>` +
        `<td>${topTxt} <button class="tpc-expand" data-year="${e.year}" type="button" ` +
        `aria-expanded="false">${esc(t('tpc.show', 'ver todos'))}</button></td></tr>` +
        `<tr class="tpc-detrow" data-year="${e.year}" hidden><td colspan="6">` +
        `<ol class="tpc-mlist">${detail}</ol>` +
        `<p class="tpc-src"><a href="${esc(e.source)}" target="_blank" rel="noopener">` +
        esc(t('tpc.source', 'fonte do TPC desta edição')) + ` ↗</a></p></td></tr>`;
    }).join('');

    document.getElementById('tpcEditions').innerHTML =
      `<div class="table-wrap"><table class="tpc-table"><thead>${head}</thead>` +
      `<tbody>${rows}</tbody></table></div>`;

    document.querySelectorAll('.tpc-expand').forEach(btn => btn.addEventListener('click', () => {
      const y = btn.dataset.year;
      const det = document.querySelector(`.tpc-detrow[data-year="${y}"]`);
      const open = det.hasAttribute('hidden');
      if (open) det.removeAttribute('hidden'); else det.setAttribute('hidden', '');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.textContent = open ? t('tpc.hide', 'ocultar') : t('tpc.show', 'ver todos');
    }));
  }

  // ---- (d) global ranking ----
  function renderRanking() {
    const host = document.getElementById('tpcRanking');
    const head =
      `<tr><th class="tpc-num">#</th>` +
      `<th>${esc(t('tpc.rkMember', 'Membro do TPC'))}</th>` +
      `<th>${esc(t('tpc.rkInst', 'Instituição (atual na fonte)'))}</th>` +
      `<th class="tpc-num">${esc(t('tpc.rkPapers', 'Artigos'))}</th>` +
      `<th class="tpc-num">${esc(t('tpc.rkPubEd', 'Edições com publicação'))}</th>` +
      `<th class="tpc-num">${esc(t('tpc.rkTpcEd', 'Edições no TPC'))}</th></tr>`;

    const ranked = DATA.global_ranking.filter(g => g.total_papers > 0);
    const TOP = 30;
    const mkRow = (g, i) =>
      `<tr><td class="tpc-num">${i + 1}</td>` +
      `<td><b>${esc(g.name)}</b></td>` +
      `<td class="tpc-sub">${esc(g.inst)}</td>` +
      `<td class="tpc-num"><b>${g.total_papers}</b></td>` +
      `<td class="tpc-num">${g.n_pub_editions}</td>` +
      `<td class="tpc-num">${g.n_tpc_editions}</td></tr>`;
    const top = ranked.slice(0, TOP).map(mkRow).join('');
    const rest = ranked.slice(TOP).map((g, i) => mkRow(g, i + TOP)).join('');

    host.innerHTML =
      `<div class="table-wrap"><table class="tpc-table tpc-rank"><thead>${head}</thead>` +
      `<tbody>${top}</tbody>` +
      (rest ? `<tbody id="tpcRankRest" hidden>${rest}</tbody>` : '') +
      `</table></div>` +
      (rest ? `<button class="tpc-more" id="tpcRankMore" type="button">` +
        esc(t('tpc.showAll', 'Mostrar todos os')) + ` ${ranked.length} ` +
        esc(t('tpc.members', 'membros')) + `</button>` : '');

    const more = document.getElementById('tpcRankMore');
    if (more) more.addEventListener('click', () => {
      const rb = document.getElementById('tpcRankRest');
      const open = rb.hasAttribute('hidden');
      if (open) rb.removeAttribute('hidden'); else rb.setAttribute('hidden', '');
      more.textContent = open
        ? t('tpc.showLess', 'Mostrar menos')
        : `${t('tpc.showAll', 'Mostrar todos os')} ${ranked.length} ${t('tpc.members', 'membros')}`;
    });
  }

  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
