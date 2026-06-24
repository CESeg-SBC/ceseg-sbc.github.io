// TPC (per sub-event) × accepted-papers statistics for the SBSeg extended
// proceedings. Renders assets/data/tpc-estendido-stats.json into KPI cards, a
// per-sub-event correlation scatter, a by-type aggregate, a per-edition
// breakdown, and a global ranking. Pure vanilla + inline SVG, no deps.
// Labels come from window.cesegI18n (site.js); content re-renders on
// 'i18n:applied' so language switches stay live.
(function () {
  const ROMAN = {2018:'XVIII',2019:'XIX',2020:'XX',2021:'XXI',2022:'XXII',
    2023:'XXIII',2024:'XXIV',2025:'XXV'};
  let DATA = null;

  function t(key, fallback) {
    const v = window.cesegI18n && window.cesegI18n.t ? window.cesegI18n.t(key) : null;
    return v == null ? fallback : v;
  }
  const esc = s => (s || '').replace(/[&<>"]/g, c =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
  const nf = n => (n == null ? '-' : String(n).replace('.', ','));

  async function boot() {
    const host = document.getElementById('tpceApp');
    if (!host) return;
    try {
      const res = await fetch('assets/data/tpc-estendido-stats.json', { cache: 'no-cache' });
      DATA = await res.json();
    } catch (e) {
      host.innerHTML = '<p class="tpc-error">' +
        t('tpce.loadError', 'Não foi possível carregar os dados.') + '</p>';
      return;
    }
    render();
    document.addEventListener('i18n:applied', render);
  }

  function render() {
    if (!DATA) return;
    renderKpis();
    renderCorr();
    renderTypes();
    renderEditions();
    renderRanking();
  }

  // ---- summary KPI cards ----
  function renderKpis() {
    const s = DATA.summary;
    const cards = [
      [nf(s.n_subevent_units), t('tpce.kpiUnits', 'sub-eventos analisados')],
      [nf(s.total_papers), t('tpce.kpiPapers', 'artigos (anais estendidos)')],
      [nf(s.papers_with_tpc_pct) + '%', t('tpce.kpiPapersTpc', 'artigos com ≥1 autor do TPC')],
      [nf(s.distinct_tpc_people), t('tpce.kpiPeople', 'pessoas distintas nos TPCs')],
      [nf(s.distinct_tpc_publishers_pct) + '%', t('tpce.kpiPublishers', 'desses membros publicaram')],
      [nf(s.corr_tpcsize_papers), t('tpce.kpiCorr', 'correlação tamanho do TPC × artigos')],
    ];
    document.getElementById('tpceKpis').innerHTML = cards.map(([v, l]) =>
      `<div class="tpc-kpi"><span class="tpc-kpi-v">${esc(v)}</span>` +
      `<span class="tpc-kpi-l">${esc(l)}</span></div>`).join('');
  }

  // ---- (b) correlation scatter: sub-event TPC size × accepted papers ----
  function renderCorr() {
    const units = DATA.subevent_units.filter(u => u.roster_published);
    const W = 640, H = 380, P = 48;
    const xs = units.map(u => u.tpc_size), ys = units.map(u => u.total_papers);
    const xMin = 0, xMax = Math.max(...xs);
    const yMin = 0, yMax = Math.max(...ys);
    const sx = v => P + (v - xMin) / (xMax - xMin) * (W - 2 * P);
    const sy = v => H - P - (v - yMin) / (yMax - yMin) * (H - 2 * P);

    // least-squares regression line
    const n = xs.length, mx = xs.reduce((a, b) => a + b, 0) / n,
      my = ys.reduce((a, b) => a + b, 0) / n;
    let num = 0, den = 0;
    for (let i = 0; i < n; i++) { num += (xs[i] - mx) * (ys[i] - my); den += (xs[i] - mx) ** 2; }
    const slope = num / den, intercept = my - slope * mx;

    const grid = [];
    for (let g = 0; g <= 4; g++) {
      const yv = Math.round(yMax * g / 4), y = sy(yv);
      grid.push(`<line x1="${P}" y1="${y}" x2="${W - P}" y2="${y}" class="tpc-grid"/>` +
        `<text x="${P - 8}" y="${y + 4}" class="tpc-axislbl" text-anchor="end">${yv}</text>`);
    }
    const pts = units.map(u => {
      const x = sx(u.tpc_size), y = sy(u.total_papers);
      return `<g class="tpc-pt"><circle cx="${x}" cy="${y}" r="5"/>` +
        `<title>${esc(u.abbrev || u.section)} ${u.year} · TPC ${u.tpc_size} · ` +
        `${u.total_papers} artigos · ${u.papers_with_tpc_author} c/ autor do TPC</title></g>`;
    }).join('');

    const svg =
      `<svg viewBox="0 0 ${W} ${H}" class="tpc-svg" role="img" ` +
      `aria-label="${esc(t('tpce.corrAria', 'Dispersão: tamanho do TPC do sub-evento versus artigos aceitos'))}">` +
      grid.join('') +
      `<line x1="${P}" y1="${H - P}" x2="${W - P}" y2="${H - P}" class="tpc-axis"/>` +
      `<line x1="${P}" y1="${P}" x2="${P}" y2="${H - P}" class="tpc-axis"/>` +
      `<line x1="${sx(xMin)}" y1="${sy(slope * xMin + intercept)}" ` +
      `x2="${sx(xMax)}" y2="${sy(slope * xMax + intercept)}" class="tpc-fit"/>` +
      pts +
      `<text x="${W / 2}" y="${H - 8}" text-anchor="middle" class="tpc-axistitle">` +
      esc(t('tpce.corrX', 'Nº de membros do TPC do sub-evento')) + `</text>` +
      `<text x="14" y="${H / 2}" text-anchor="middle" class="tpc-axistitle" ` +
      `transform="rotate(-90 14 ${H / 2})">` + esc(t('tpce.corrY', 'Artigos aceitos')) + `</text>` +
      `</svg>`;
    document.getElementById('tpceCorr').innerHTML = svg +
      `<p class="tpc-corr-note">${esc(t('tpce.corrCaption',
        'Cada ponto é um sub-evento de uma edição (com lista de membros publicada). Pearson r ='))} ` +
      `<b>${nf(DATA.summary.corr_tpcsize_papers)}</b>.</p>`;
  }

  // ---- (e) aggregate by sub-event type ----
  const FAMILY = { 'SF':'SF', 'WTICG':'WTICG', 'WTICG Andamento':'WTICG',
    'WGID':'WGID', 'CTD':'CTD' };
  const FAMILY_LABEL = {
    'SF': 'Salão de Ferramentas',
    'WTICG': 'Iniciação Científica (WTICG)',
    'WGID': 'Gestão de Identidades (WGID)',
    'CTD': 'Teses e Dissertações (CTD)',
    'OUT': 'Outros workshops',
  };
  function familyOf(u) { return FAMILY[u.abbrev] || 'OUT'; }

  function renderTypes() {
    const agg = {};
    DATA.subevent_units.forEach(u => {
      const f = familyOf(u);
      const a = agg[f] || (agg[f] = { units: 0, papers: 0, withTpc: 0 });
      a.units += 1; a.papers += u.total_papers; a.withTpc += u.papers_with_tpc_author;
    });
    const order = ['SF', 'CTD', 'WGID', 'WTICG', 'OUT'];
    const rows = order.filter(f => agg[f]).map(f => {
      const a = agg[f];
      const pct = a.papers ? Math.round(1000 * a.withTpc / a.papers) / 10 : 0;
      const bar = `<span class="tpc-bar"><span style="width:${pct}%"></span></span>`;
      return `<tr><td><b>${esc(t('tpce.fam_' + f, FAMILY_LABEL[f]))}</b></td>` +
        `<td class="tpc-num">${a.units}</td>` +
        `<td class="tpc-num">${a.papers}</td>` +
        `<td class="tpc-num">${a.withTpc} <span class="tpc-sub">(${nf(pct)}%)</span>${bar}</td></tr>`;
    }).join('');
    document.getElementById('tpceTypes').innerHTML =
      `<div class="table-wrap"><table class="tpc-table"><thead><tr>` +
      `<th>${esc(t('tpce.thType', 'Tipo de sub-evento'))}</th>` +
      `<th class="tpc-num">${esc(t('tpce.thUnits', 'Edições'))}</th>` +
      `<th class="tpc-num">${esc(t('tpce.thPapers', 'Artigos'))}</th>` +
      `<th class="tpc-num">${esc(t('tpce.thPapersTpc', 'Artigos c/ autor do TPC'))}</th>` +
      `</tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  // ---- (a,c) per-edition breakdown ----
  function renderEditions() {
    const units = DATA.subevent_units;
    const html = DATA.editions.slice().reverse().map(ed => {
      const eus = ed.unit_indexes.map(i => units[i])
        .sort((a, b) => b.total_papers - a.total_papers);
      const subRows = eus.map(u => {
        const top = u.ranking[0];
        const topTxt = top ? `${esc(top.name)} <span class="tpc-pill">${top.count}</span>` : '-';
        const tpcCell = u.roster_published ? u.tpc_size
          : `${u.tpc_size} <span class="tpc-sub">${esc(t('tpce.chairsOnly', '(só coord.)'))}</span>`;
        const pctBar = `<span class="tpc-bar"><span style="width:${u.papers_with_tpc_pct}%"></span></span>`;
        return `<tr><td>${esc(u.abbrev || u.section)}</td>` +
          `<td class="tpc-num">${tpcCell}</td>` +
          `<td class="tpc-num">${u.total_papers}</td>` +
          `<td class="tpc-num">${u.papers_with_tpc_author} ` +
          `<span class="tpc-sub">(${nf(u.papers_with_tpc_pct)}%)</span>${pctBar}</td>` +
          `<td class="tpc-num">${u.tpc_publishers}</td>` +
          `<td>${topTxt}</td></tr>`;
      }).join('');

      const topMembers = ed.ranking.slice(0, 8).map(r =>
        `<li><span class="tpc-mname">${esc(r.name)}</span>` +
        `<span class="tpc-minst">${esc(r.inst)}</span>` +
        `<span class="tpc-pill">${r.count}</span></li>`).join('');

      return `<details class="tpce-ed"${ed.year >= 2024 ? ' open' : ''}>` +
        `<summary class="tpce-ed-head"><b>${ROMAN[ed.year] || ''} ${ed.year}</b> ` +
        `<span class="tpc-sub">${ed.n_subevents} ${esc(t('tpce.subevents', 'sub-eventos'))} · ` +
        `${ed.total_papers} ${esc(t('tpce.articles', 'artigos'))} · ` +
        `${ed.papers_with_tpc_author} (${nf(ed.papers_with_tpc_pct)}%) ${esc(t('tpce.withTpc', 'c/ autor do TPC'))}</span>` +
        `</summary>` +
        `<div class="table-wrap"><table class="tpc-table"><thead><tr>` +
        `<th>${esc(t('tpce.thSubevent', 'Sub-evento'))}</th>` +
        `<th class="tpc-num">${esc(t('tpce.thTpc', 'TPC'))}</th>` +
        `<th class="tpc-num">${esc(t('tpce.thPapers', 'Artigos'))}</th>` +
        `<th class="tpc-num">${esc(t('tpce.thPapersTpc', 'Artigos c/ autor do TPC'))}</th>` +
        `<th class="tpc-num">${esc(t('tpce.thPublishers', 'Membros que publicaram'))}</th>` +
        `<th>${esc(t('tpce.thTop', 'Destaque'))}</th>` +
        `</tr></thead><tbody>${subRows}</tbody></table></div>` +
        (topMembers ? `<p class="tpce-toplbl">${esc(t('tpce.topEd', 'Membros mais publicados na edição:'))}</p>` +
          `<ol class="tpc-mlist tpce-toplist">${topMembers}</ol>` : '') +
        `</details>`;
    }).join('');
    document.getElementById('tpceEditions').innerHTML = html;
  }

  // ---- (d) global ranking ----
  function renderRanking() {
    const host = document.getElementById('tpceRanking');
    const head =
      `<tr><th class="tpc-num">#</th>` +
      `<th>${esc(t('tpce.rkMember', 'Membro do TPC'))}</th>` +
      `<th>${esc(t('tpce.rkInst', 'Instituição (na fonte)'))}</th>` +
      `<th class="tpc-num">${esc(t('tpce.rkPapers', 'Artigos'))}</th>` +
      `<th class="tpc-num">${esc(t('tpce.rkPubUnits', 'Sub-eventos c/ publicação'))}</th>` +
      `<th class="tpc-num">${esc(t('tpce.rkTpcUnits', 'Participações em TPC'))}</th></tr>`;

    const ranked = DATA.global_ranking.filter(g => g.total_papers > 0);
    const TOP = 30;
    const mkRow = (g, i) =>
      `<tr><td class="tpc-num">${i + 1}</td>` +
      `<td><b>${esc(g.name)}</b></td>` +
      `<td class="tpc-sub">${esc(g.inst)}</td>` +
      `<td class="tpc-num"><b>${g.total_papers}</b></td>` +
      `<td class="tpc-num">${g.n_pub_units} <span class="tpc-sub">(${g.n_pub_editions} ed.)</span></td>` +
      `<td class="tpc-num">${g.n_tpc_units}</td></tr>`;
    const top = ranked.slice(0, TOP).map(mkRow).join('');
    const rest = ranked.slice(TOP).map((g, i) => mkRow(g, i + TOP)).join('');

    host.innerHTML =
      `<div class="table-wrap"><table class="tpc-table tpc-rank"><thead>${head}</thead>` +
      `<tbody>${top}</tbody>` +
      (rest ? `<tbody id="tpceRankRest" hidden>${rest}</tbody>` : '') +
      `</table></div>` +
      (rest ? `<button class="tpc-more" id="tpceRankMore" type="button">` +
        esc(t('tpce.showAll', 'Mostrar todos os')) + ` ${ranked.length} ` +
        esc(t('tpce.members', 'membros')) + `</button>` : '');

    const more = document.getElementById('tpceRankMore');
    if (more) more.addEventListener('click', () => {
      const rb = document.getElementById('tpceRankRest');
      const open = rb.hasAttribute('hidden');
      if (open) rb.removeAttribute('hidden'); else rb.setAttribute('hidden', '');
      more.textContent = open
        ? t('tpce.showLess', 'Mostrar menos')
        : `${t('tpce.showAll', 'Mostrar todos os')} ${ranked.length} ${t('tpce.members', 'membros')}`;
    });
  }

  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
