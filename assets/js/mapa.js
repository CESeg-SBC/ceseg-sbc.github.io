/* Cybersecurity Map page.
   Loads assets/data/cybersecmap.json (snapshot of cybersecmap.rnp.br) and renders
   a single search + filter + Leaflet map view that replaces the source's many
   cascading menus. Self-initializes only when #cybermap is present, so it is inert
   on every other page that also loads site.js. */
(function () {
  var root = document.getElementById('cybermap');
  if (!root) return;

  // Type metadata: marker color + i18n label key (with English fallback).
  var TYPES = {
    researcher:    { color: '#2563eb', key: 'map.typeResearcher',   def: 'Researchers' },
    group:         { color: '#16a34a', key: 'map.typeGroup',        def: 'Research Groups' },
    program:       { color: '#9333ea', key: 'map.typeProgram',      def: 'Graduate Programs' },
    center:        { color: '#ea580c', key: 'map.typeCenter',       def: 'R&D Centers' },
    working_group: { color: '#0d9488', key: 'map.typeWorkingGroup', def: 'Working Groups' },
    publication:   { color: '#64748b', key: 'map.typePublication',  def: 'Publications' }
  };
  var TYPE_ORDER = ['researcher', 'group', 'program', 'center', 'working_group', 'publication'];
  var LIST_CAP = 400; // cap rendered cards; the map still shows every match.

  // i18n helper: use site.js's exposed lookup when the dictionary is loaded, else fallback.
  function tr(key, fallback) {
    var fn = window.cesegI18n && window.cesegI18n.t;
    var v = fn ? fn(key) : null;
    return (v == null) ? fallback : v;
  }
  function fold(s) {
    return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }
  function esc(s) {
    return (s || '').replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  var DATA = null, RECORDS = [], MARKERS = {}, map, cluster;
  // All entity types active by default except publications (kept off for clarity).
  var activeTypes = { researcher: true, group: true, program: true, center: true, working_group: true, publication: false };
  var selState = '', selTopic = '', query = '';
  var els = {};

  function typeLabel(type) { return tr(TYPES[type].key, TYPES[type].def); }

  function buildMap() {
    map = L.map(root, { scrollWheelZoom: true, worldCopyJump: true })
      .setView([-14.6, -52.0], 4);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 19, subdomains: 'abcd'
    }).addTo(map);
    cluster = L.markerClusterGroup({ maxClusterRadius: 50, chunkedLoading: true });
    map.addLayer(cluster);
  }

  function icon(type) {
    return L.divIcon({
      className: 'cm-pin',
      html: '<span style="background:' + TYPES[type].color + '"></span>',
      iconSize: [18, 18], iconAnchor: [9, 9], popupAnchor: [0, -8]
    });
  }

  function buildMarkers() {
    RECORDS.forEach(function (r) {
      if (r.lat == null || r.lng == null) return;
      var m = L.marker([r.lat, r.lng], { icon: icon(r.type) });
      m.bindPopup(detailHTML(r), { maxWidth: 300 });
      m._rec = r;
      m.on('click', function () { highlightCard(r.id); });
      MARKERS[r.id] = m;
    });
  }

  function matches(r) {
    if (!activeTypes[r.type]) return false;
    if (selState && r.state !== selState) return false;
    if (selTopic && (r.topics || []).indexOf(selTopic) === -1) return false;
    if (query) {
      if (!r._hay) r._hay = fold([r.name, r.institution, r.state, r.interests,
        r.leader, r.project, r.authors, (r.topics || []).join(' ')].join(' '));
      if (r._hay.indexOf(query) === -1) return false;
    }
    return true;
  }

  function detailHTML(r) {
    var rows = '';
    function row(labelKey, def, val, isLink) {
      if (!val) return;
      var v = isLink
        ? '<a href="' + esc(val) + '" target="_blank" rel="noopener">' + esc(val) + '</a>'
        : esc(val);
      rows += '<div class="cm-d-row"><span>' + esc(tr(labelKey, def)) + '</span><div>' + v + '</div></div>';
    }
    row('map.institution', 'Institution', r.institution);
    row('map.state', 'State', r.state);
    if (r.interests) row('map.interests', 'Research interests', r.interests);
    if (r.leader) row('map.leader', 'Leader', r.leader);
    if (r.project) row('map.project', 'Project', r.project);
    if (r.authors) row('map.authors', 'Authors', r.authors);
    if (r.year) row('map.year', 'Year', r.year);
    if (r.topics && r.topics.length) row('map.topics', 'Topics', r.topics.join('; '));
    var links = r.links || {};
    if (links.lattes) row('map.lattes', 'Lattes', links.lattes, true);
    if (links.group) row('map.researchGroup', 'Research group', links.group, true);
    if (links.program) row('map.program', 'Graduate program', links.program);
    if (links.url) row('map.website', 'Website', links.url, true);
    return '<div class="cm-detail">'
      + '<span class="cm-tag" style="background:' + TYPES[r.type].color + '">' + esc(typeLabel(r.type)) + '</span>'
      + '<h4>' + esc(r.name) + '</h4>' + rows + '</div>';
  }

  function cardHTML(r) {
    var sub = [r.institution, r.state].filter(Boolean).join(' · ');
    return '<button type="button" class="cm-card" data-id="' + esc(r.id) + '">'
      + '<span class="cm-dot" style="background:' + TYPES[r.type].color + '"></span>'
      + '<span class="cm-card-body"><span class="cm-card-title">' + esc(r.name) + '</span>'
      + (sub ? '<span class="cm-card-sub">' + esc(sub) + '</span>' : '')
      + '<span class="cm-card-type">' + esc(typeLabel(r.type)) + '</span></span></button>';
  }

  function render() {
    var visible = RECORDS.filter(matches);
    // Map: rebuild cluster with the matching markers.
    cluster.clearLayers();
    var layers = [];
    visible.forEach(function (r) { if (MARKERS[r.id]) layers.push(MARKERS[r.id]); });
    cluster.addLayers(layers);

    // List: render up to LIST_CAP cards.
    var shown = visible.slice(0, LIST_CAP);
    els.list.innerHTML = shown.map(cardHTML).join('') ||
      '<p class="cm-list-empty">' + esc(tr('map.noResults', 'No results found.')) + '</p>';
    if (visible.length > LIST_CAP) {
      els.list.insertAdjacentHTML('beforeend',
        '<p class="cm-list-more">' + esc(tr('map.listCap', 'Showing first 400 on the list; all matches appear on the map.')) + '</p>');
    }
    els.visible.textContent = visible.length;
    els.total.textContent = RECORDS.length;
    els.noResults.hidden = visible.length !== 0;
  }

  function highlightCard(id) {
    var card = els.list.querySelector('.cm-card[data-id="' + (window.CSS && CSS.escape ? CSS.escape(id) : id) + '"]');
    els.list.querySelectorAll('.cm-card.active').forEach(function (c) { c.classList.remove('active'); });
    if (card) {
      card.classList.add('active');
      card.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  function focusRecord(id) {
    var r = RECORDS.find(function (x) { return x.id === id; });
    var m = MARKERS[id];
    if (!r || !m) return;
    if (window.matchMedia('(max-width: 760px)').matches) setView('map');
    map.setView([r.lat, r.lng], Math.max(map.getZoom(), 9), { animate: true });
    cluster.zoomToShowLayer(m, function () { m.openPopup(); });
    highlightCard(id);
  }

  function setView(view) {
    els.grid.classList.toggle('show-map', view === 'map');
    els.grid.classList.toggle('show-list', view === 'list');
    document.querySelectorAll('.map-viewtoggle button').forEach(function (b) {
      b.classList.toggle('active', b.dataset.view === view);
    });
    if (view === 'map' && map) setTimeout(function () { map.invalidateSize(); }, 50);
  }

  function buildChips() {
    els.chips.innerHTML = TYPE_ORDER.map(function (type) {
      return '<button type="button" class="cm-chip' + (activeTypes[type] ? ' active' : '') +
        '" data-type="' + type + '" style="--c:' + TYPES[type].color + '">' +
        '<span class="cm-chip-dot"></span><span class="cm-chip-label">' + esc(typeLabel(type)) +
        '</span><span class="cm-chip-n">' + ((DATA.counts && DATA.counts[type]) || 0) + '</span></button>';
    }).join('');
  }

  function buildSelects() {
    var allStates = '<option value="">' + esc(tr('map.allStates', 'All states')) + '</option>';
    els.state.innerHTML = allStates + DATA.states.map(function (s) {
      return '<option value="' + esc(s) + '">' + esc(s) + '</option>';
    }).join('');
    var allTopics = '<option value="">' + esc(tr('map.allTopics', 'All topics')) + '</option>';
    els.topic.innerHTML = allTopics + DATA.topics.map(function (tp) {
      return '<option value="' + esc(tp) + '">' + esc(tp) + '</option>';
    }).join('');
    // Form type select mirrors the entity types.
    var mf = document.getElementById('mfType');
    if (mf) mf.innerHTML = TYPE_ORDER.map(function (type) {
      return '<option value="' + type + '">' + esc(typeLabel(type)) + '</option>';
    }).join('');
  }

  // Re-render i18n-dependent labels when the language changes.
  function relabel() {
    if (!DATA) return;
    buildChips();
    var sv = els.state.value, tv = els.topic.value;
    buildSelects();
    els.state.value = sv; els.topic.value = tv;
    render();
  }

  function wire() {
    els.search.addEventListener('input', function () { query = fold(this.value.trim()); render(); });
    els.chips.addEventListener('click', function (e) {
      var b = e.target.closest('.cm-chip'); if (!b) return;
      var ty = b.dataset.type;
      activeTypes[ty] = !activeTypes[ty];
      b.classList.toggle('active', activeTypes[ty]);
      render();
    });
    els.state.addEventListener('change', function () { selState = this.value; render(); });
    els.topic.addEventListener('change', function () { selTopic = this.value; render(); });
    els.clear.addEventListener('click', function () {
      query = ''; selState = ''; selTopic = '';
      els.search.value = ''; els.state.value = ''; els.topic.value = '';
      render();
    });
    els.list.addEventListener('click', function (e) {
      var c = e.target.closest('.cm-card'); if (!c) return;
      focusRecord(c.dataset.id);
    });
    document.querySelectorAll('.map-viewtoggle button').forEach(function (b) {
      b.addEventListener('click', function () { setView(b.dataset.view); });
    });
    if (els.sbsegToggle) els.sbsegToggle.addEventListener('click', toggleSbseg);
    document.addEventListener('i18n:applied', relabel);
    initForm();
  }

  function initForm() {
    var form = document.getElementById('mapForm');
    if (!form) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = form.elements;
      var name = f.name.value.trim(), email = f.email.value.trim();
      var emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      var err = document.getElementById('mfError');
      if (!name || !emailOk) { err.hidden = false; return; }
      err.hidden = true;
      var typeSel = f.type.options[f.type.selectedIndex].text;
      var lines = [
        tr('mapForm.name', 'Name') + ': ' + name,
        tr('mapForm.email', 'Email') + ': ' + email,
        tr('mapForm.type', 'Record type') + ': ' + typeSel,
        tr('mapForm.institution', 'Institution') + ': ' + f.institution.value.trim(),
        tr('mapForm.state', 'State') + ': ' + f.state.value.trim(),
        tr('mapForm.interests', 'Areas') + ': ' + f.interests.value.trim(),
        tr('mapForm.links', 'Links') + ': ' + f.links.value.trim(),
        '', tr('mapForm.message', 'Message') + ':', f.message.value.trim()
      ];
      var subject = tr('mapForm.subject', 'Cybersecurity Map: inclusion request') + ' - ' + name;
      var href = 'mailto:ceseg.sbc@gmail.com?subject=' + encodeURIComponent(subject) +
        '&body=' + encodeURIComponent(lines.join('\n'));
      window.location.href = href;
    });
  }

  /* SBSeg editions layer: a separate, toggleable overlay (default off) of the
     event's host cities, independent of the RNP type chips and the results list.
     Data is grouped by city, so a city that hosted several editions is one pin. */
  var sbsegLayer = null, sbsegLoaded = false, sbsegOn = false;

  function sbsegIcon() {
    return L.divIcon({
      className: 'sbseg-pin',
      html: '<span></span>',
      iconSize: [16, 16], iconAnchor: [8, 8], popupAnchor: [0, -9]
    });
  }

  function sbsegPopupHTML(c) {
    var head = esc(c.city) + (c.uf ? ' · ' + esc(c.uf) : '');
    var rows = c.editions.map(function (e) {
      var links = e.links || {};
      var parts = [];
      if (links.site) parts.push('<a href="' + esc(links.site) + '" target="_blank" rel="noopener">' + esc(tr('map.sbsegSite', 'site')) + '</a>');
      if (links.clone) parts.push('<a href="' + esc(links.clone) + '" target="_blank" rel="noopener">' + esc(tr('map.sbsegClone', 'clone')) + '</a>');
      if (links.anais) parts.push('<a href="' + esc(links.anais) + '" target="_blank" rel="noopener">' + esc(tr('map.sbsegAnais', 'proceedings')) + '</a>');
      var meta = [esc(String(e.year)), esc(e.dates)].filter(Boolean).join(' · ');
      if (e.online) meta += ' · ' + esc(tr('map.sbsegOnline', 'online'));
      if (e.wseg) meta += ' · WSeg';
      return '<div class="sbseg-ed"><b>SBSeg ' + esc(e.n) + '</b> · ' + meta +
        (parts.length ? '<div class="sbseg-ed-links">' + parts.join(' · ') + '</div>' : '') + '</div>';
    }).join('');
    return '<div class="sbseg-detail"><span class="sbseg-tag">SBSeg</span><h4>' + head + '</h4>' + rows + '</div>';
  }

  function loadSbsegLayer(cb) {
    if (sbsegLoaded) { cb(); return; }
    fetch('assets/data/sbseg-editions.json', { cache: 'no-cache' })
      .then(function (res) { return res.json(); })
      .then(function (d) {
        sbsegLayer = L.layerGroup();
        (d.cities || []).forEach(function (c) {
          if (c.lat == null || c.lng == null) return;
          L.marker([c.lat, c.lng], { icon: sbsegIcon() })
            .bindPopup(sbsegPopupHTML(c), { maxWidth: 300 })
            .addTo(sbsegLayer);
        });
        sbsegLoaded = true;
        cb();
      })
      .catch(function () { cb(true); });
  }

  function toggleSbseg() {
    sbsegOn = !sbsegOn;
    var btn = els.sbsegToggle;
    if (btn) btn.setAttribute('aria-pressed', String(sbsegOn));
    if (!sbsegOn) {
      if (sbsegLayer) map.removeLayer(sbsegLayer);
      return;
    }
    loadSbsegLayer(function (failed) {
      if (failed || !sbsegOn) return; // user may have toggled back off while loading
      map.addLayer(sbsegLayer);
    });
  }

  function boot() {
    els = {
      search: document.getElementById('mapSearch'),
      chips: document.getElementById('mapChips'),
      state: document.getElementById('mapState'),
      topic: document.getElementById('mapTopic'),
      clear: document.getElementById('mapClear'),
      list: document.getElementById('mapList'),
      grid: document.getElementById('mapGrid'),
      visible: document.getElementById('mapVisible'),
      total: document.getElementById('mapTotal'),
      noResults: document.getElementById('mapNoResults'),
      sbsegToggle: document.getElementById('sbsegToggle')
    };
    buildMap();
    fetch('assets/data/cybersecmap.json', { cache: 'no-cache' })
      .then(function (res) { return res.json(); })
      .then(function (d) {
        DATA = d; RECORDS = d.records || [];
        buildMarkers();
        buildChips();
        buildSelects();
        wire();
        render();
        if (window.matchMedia('(max-width: 760px)').matches) setView('map');
      })
      .catch(function () {
        els.list.innerHTML = '<p class="cm-list-empty">' +
          esc(tr('map.loadError', 'Could not load the map data.')) + '</p>';
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
