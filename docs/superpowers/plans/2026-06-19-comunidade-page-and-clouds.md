# Comunidade Page + Proceedings Stats + Word-Cloud Repositioning — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the map page to `comunidade.html` with a two-row filter strip, add aggregated per-institution Publicações and Ferramentas map layers derived from the SBSeg proceedings (author→researcher matching), and move the existing keyword clouds to sit directly under the "Edições" TOC on both anais pages.

**Architecture:** Static vanilla-JS site. A new dependency-free Python script parses the two anais HTML files and `cybersecmap.json` to emit `assets/data/proceedings-stats.json`. `mapa.js` (loaded by `comunidade.html`) renders the filter strip as an ordered list of chip descriptors and draws the aggregated layers as Leaflet `circleMarker` groups. The anais word-cloud change is a pure DOM move mirrored in `gen_pages.py`.

**Tech Stack:** Vanilla JS, Leaflet 1.9 + markercluster, Python 3 stdlib (no deps), JSON data files, nested-object i18n (`assets/i18n/{pt,en,es}.json`).

## Global Constraints

- No em dash "—" in any site-visible text; use "·" or a comma. (User rule.)
- No third-party Python deps; match the style of existing `scripts/*.py`.
- Page scripts must call `window.cesegI18n.t()`, never bare `t()` (Leaflet shadows `t`).
- Do NOT blindly run `gen_pages.py` — it can revert manual HTML edits. Edit HTML by hand AND update the generator so they agree.
- i18n is nested: `pt.json` → `{"map": {"typeResearcher": "..."}}`. Add keys under the existing `map` object in all three locale files.
- No test framework exists; verification is: run the script, parse JSON with `python3 -c`, `grep` the HTML, and a headless browser load.

---

### Task 1: Rename `mapa.html` → `comunidade.html`

**Files:**
- Rename: `mapa.html` → `comunidade.html`
- Modify: `comunidade.html` (`body[data-page]`)
- Modify: `assets/js/site.js` (nav href)

**Interfaces:**
- Consumes: nothing.
- Produces: a page reachable at `comunidade.html`; `data-page="comunidade"`.

- [ ] **Step 1: Rename the file with git**

```bash
cd /Users/kreutz/claude.ai/ceseg/ceseg-sbc.github.io
git mv mapa.html comunidade.html
```

- [ ] **Step 2: Update the body data-page attribute**

In `comunidade.html`, change:
```html
<body data-page="mapa">
```
to:
```html
<body data-page="comunidade">
```

- [ ] **Step 3: Update the nav href in site.js**

In `assets/js/site.js`, change:
```js
  {key:'nav.mapa', href:'mapa.html'},
```
to:
```js
  {key:'nav.mapa', href:'comunidade.html'},
```

- [ ] **Step 4: Find and fix any other inbound links to mapa.html**

Run: `grep -rn "mapa.html" --include=*.html --include=*.js --include=*.py .`
Expected after fix: no matches except possibly historical references inside `docs/`. Update any live link in `*.html`, `assets/js/*.js`, or `scripts/gen_pages.py` to `comunidade.html`. (`assets/js/mapa.js` keeps its filename — only the page that includes it was renamed.)

- [ ] **Step 5: Verify**

Run: `test -f comunidade.html && ! test -f mapa.html && grep -c "comunidade.html" assets/js/site.js`
Expected: prints `1`.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Rename mapa.html to comunidade.html"
```

---

### Task 2: Proceedings stats script + JSON

**Files:**
- Create: `scripts/fetch_proceedings_stats.py`
- Create (generated): `assets/data/proceedings-stats.json`

**Interfaces:**
- Consumes: `anais-trilha-principal.html`, `anais-estendidos.html`, `assets/data/cybersecmap.json`.
- Produces: `assets/data/proceedings-stats.json` with shape:
  `{ generated_from:[...], match_rate:{papers,tool_papers}, institutions:[ {institution,state,lat,lng,pub_count,tool_count,pubs:[{title,url}],tools:[{title,url}]} ] }`

- [ ] **Step 1: Write the script**

Create `scripts/fetch_proceedings_stats.py`:

```python
#!/usr/bin/env python3
"""Aggregate SBSeg proceedings into per-institution publication and tool counts.

The anais pages carry no affiliation, so we attribute each paper to an
institution by matching its author names against the researcher (by name) and
group (by leader) records in cybersecmap.json. A paper counts once per distinct
matched institution. Papers under a "Salão de Ferramentas" section also count as
tools. Unmatched papers are dropped; the overall match rate is recorded.

No third-party dependencies (the site is static and vanilla by design).
"""
import json
import os
import re
import unicodedata
from html import unescape
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["anais-trilha-principal.html", "anais-estendidos.html"]
OUT = os.path.join(ROOT, "assets", "data", "proceedings-stats.json")


def fold(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def name_key(name):
    """(first_token, last_token) of a folded personal name, or None."""
    toks = [t for t in re.split(r"[^\w]+", fold(name)) if len(t) > 1]
    if len(toks) < 2:
        return None
    return (toks[0], toks[-1])


def build_author_index(cybersec):
    """name_key -> {institution, state, lat, lng}; first writer wins."""
    idx = {}
    for r in cybersec.get("records", []):
        if r["type"] == "researcher":
            person, inst = r.get("name"), r
        elif r["type"] == "group" and r.get("leader"):
            person, inst = r.get("leader"), r
        else:
            continue
        k = name_key(person)
        if not k or k in idx:
            continue
        idx[k] = {
            "institution": inst.get("institution") or inst.get("name"),
            "state": inst.get("state", ""),
            "lat": inst.get("lat"),
            "lng": inst.get("lng"),
        }
    return idx


class PaperParser(HTMLParser):
    """Collect (authors, title, url, is_tool) per li.pub-paper.

    is_tool is set when the most recent <h3 class="pub-section"> before the paper
    contained the text "Salão de Ferramentas".
    """

    def __init__(self):
        super().__init__()
        self.papers = []
        self._in_section_h3 = False
        self._section_text = ""
        self._cur_is_tool = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h3" and "pub-section" in (a.get("class") or ""):
            self._in_section_h3 = True
            self._section_text = ""
        elif tag == "li" and "pub-paper" in (a.get("class") or ""):
            cite = a.get("data-cite", "")
            m = re.search(r"https?://\S+", cite)
            self.papers.append({
                "authors": unescape(a.get("data-authors", "")),
                "title": unescape(a.get("data-title", "")),
                "url": m.group(0) if m else "",
                "is_tool": self._cur_is_tool,
            })

    def handle_endtag(self, tag):
        if tag == "h3" and self._in_section_h3:
            self._in_section_h3 = False
            self._cur_is_tool = "salao de ferramentas" in fold(self._section_text)

    def handle_data(self, data):
        if self._in_section_h3:
            self._section_text += data


def parse_papers():
    papers = []
    for page in PAGES:
        p = PaperParser()
        with open(os.path.join(ROOT, page), encoding="utf-8") as fh:
            p.feed(fh.read())
        papers.extend(p.papers)
    return papers


def attribute(papers, idx):
    """Return institutions dict keyed by institution name."""
    insts = {}
    matched_papers = matched_tools = total_tools = 0
    for paper in papers:
        if paper["is_tool"]:
            total_tools += 1
        names = re.split(r"[;,]", paper["authors"])
        hit_insts = {}
        for nm in names:
            k = name_key(nm)
            if k and k in idx:
                hit_insts[idx[k]["institution"]] = idx[k]
        if not hit_insts:
            continue
        matched_papers += 1
        if paper["is_tool"]:
            matched_tools += 1
        rec = {"title": paper["title"], "url": paper["url"]}
        for inst_name, meta in hit_insts.items():
            slot = insts.setdefault(inst_name, {
                "institution": inst_name, "state": meta["state"],
                "lat": meta["lat"], "lng": meta["lng"],
                "pub_count": 0, "tool_count": 0, "pubs": [], "tools": [],
            })
            slot["pub_count"] += 1
            slot["pubs"].append(rec)
            if paper["is_tool"]:
                slot["tool_count"] += 1
                slot["tools"].append(rec)
    rate = {
        "papers": round(matched_papers / len(papers), 3) if papers else 0,
        "tool_papers": round(matched_tools / total_tools, 3) if total_tools else 0,
    }
    return insts, rate


def main():
    with open(os.path.join(ROOT, "assets", "data", "cybersecmap.json"), encoding="utf-8") as fh:
        cybersec = json.load(fh)
    idx = build_author_index(cybersec)
    papers = parse_papers()
    insts, rate = attribute(papers, idx)
    institutions = [i for i in insts.values() if i["lat"] is not None and i["lng"] is not None]
    institutions.sort(key=lambda i: -i["pub_count"])
    out = {"generated_from": PAGES, "match_rate": rate, "institutions": institutions}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"papers={len(papers)} institutions={len(institutions)} "
          f"match_rate={rate} -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python3 scripts/fetch_proceedings_stats.py`
Expected: a line like `papers=2196 institutions=NN match_rate={'papers': 0.5x, 'tool_papers': 0.x} -> assets/data/proceedings-stats.json` and no traceback.

- [ ] **Step 3: Validate the output JSON**

Run:
```bash
python3 -c "import json;d=json.load(open('assets/data/proceedings-stats.json'));i=d['institutions'];print('insts',len(i));print('top',i[0]['institution'],i[0]['pub_count'],i[0]['tool_count']);assert all(x['lat'] is not None for x in i);assert any(x['tool_count']>0 for x in i),'no tools attributed'"
```
Expected: prints counts, a top institution, and no assertion error. If `no tools attributed` fires, inspect the `Salão de Ferramentas` section detection (the `<h3 class="pub-section">` text match) before proceeding.

- [ ] **Step 4: Commit**

```bash
git add scripts/fetch_proceedings_stats.py assets/data/proceedings-stats.json
git commit -m "Add proceedings per-institution stats script + data"
```

---

### Task 3: Two-row filter strip on the Comunidade page

**Files:**
- Modify: `comunidade.html` (chip container markup; remove `.map-layers` block)
- Modify: `assets/js/mapa.js` (chip descriptors, `buildChips`, click dispatch, drop publication from cluster)
- Modify: `assets/css/styles.css` (two-row strip)
- Modify: `assets/i18n/{pt,en,es}.json` (`map.typeTool`)

**Interfaces:**
- Consumes: `proceedings-stats.json` (eager-loaded in Task 4; here only the chip + filter wiring).
- Produces: globals in `mapa.js` — `CHIP_ORDER` (array of `{kind,type|layer,labelKey,def,color}`), `overlayOn` (`{pubs,sbseg,tools}` booleans), `setOverlay(name, on)` (defined in Task 4). `buildChips()` renders every descriptor; click handler toggles `activeTypes[type]` for `kind==='type'` and calls `setOverlay(layer, !overlayOn[layer])` for `kind==='overlay'`.

- [ ] **Step 1: Replace the chip + layers markup in comunidade.html**

In `comunidade.html`, replace these two blocks:
```html
        <div class="map-chips" id="mapChips" role="group" aria-label="Tipos"></div>

        <div class="map-layers">
          <button type="button" id="sbsegToggle" class="map-layer-toggle" aria-pressed="false">
            <span class="mlt-mark"></span>
            <span data-i18n="map.sbsegToggle">Edições do SBSeg</span>
            <span class="mlt-n">25</span>
          </button>
        </div>
```
with:
```html
        <div class="map-chips" id="mapChips" role="group" aria-label="Filtros"></div>
```

- [ ] **Step 2: Replace TYPES/TYPE_ORDER/activeTypes with chip descriptors in mapa.js**

In `assets/js/mapa.js`, the `TYPES` object stays (still used for marker colors and popups), but change `TYPE_ORDER` and `activeTypes`. Replace:
```js
  var TYPE_ORDER = ['researcher', 'group', 'program', 'center', 'working_group', 'publication'];
```
with:
```js
  // Cluster entity types (publication is now an aggregated overlay, not a cluster type).
  var TYPE_ORDER = ['researcher', 'group', 'program', 'center', 'working_group'];
  // Ordered two-row filter strip: type chips filter the cluster; overlay chips
  // toggle their own Leaflet layer. Rendered four-per-row by CSS.
  var TOOL_COLOR = '#c026d3';
  var CHIP_ORDER = [
    { kind: 'overlay', layer: 'pubs',  labelKey: 'map.typePublication',  def: 'Publications',     color: TYPES.publication.color },
    { kind: 'overlay', layer: 'sbseg', labelKey: 'map.sbsegToggle',      def: 'SBSeg editions',   color: '#1e3a5f' },
    { kind: 'type',    type: 'researcher',    labelKey: 'map.typeResearcher',   def: 'Researchers',      color: TYPES.researcher.color },
    { kind: 'type',    type: 'group',         labelKey: 'map.typeGroup',        def: 'Research Groups',  color: TYPES.group.color },
    { kind: 'type',    type: 'program',       labelKey: 'map.typeProgram',      def: 'Graduate Programs',color: TYPES.program.color },
    { kind: 'type',    type: 'center',        labelKey: 'map.typeCenter',       def: 'R&D Centers',      color: TYPES.center.color },
    { kind: 'type',    type: 'working_group', labelKey: 'map.typeWorkingGroup', def: 'Working Groups',   color: TYPES.working_group.color },
    { kind: 'overlay', layer: 'tools', labelKey: 'map.typeTool',         def: 'Tools',            color: TOOL_COLOR }
  ];
```
Then replace:
```js
  var activeTypes = { researcher: true, group: true, program: true, center: true, working_group: true, publication: false };
```
with:
```js
  var activeTypes = { researcher: true, group: true, program: true, center: true, working_group: true };
  var overlayOn = { pubs: true, sbseg: false, tools: false };
```

- [ ] **Step 3: Skip publication markers in the cluster**

In `buildMarkers()`, change:
```js
    RECORDS.forEach(function (r) {
      if (r.lat == null || r.lng == null) return;
```
to:
```js
    RECORDS.forEach(function (r) {
      if (r.type === 'publication') return; // aggregated into the pubs overlay
      if (r.lat == null || r.lng == null) return;
```

- [ ] **Step 4: Rewrite buildChips() to render descriptors**

Replace the whole `buildChips` function:
```js
  function buildChips() {
    els.chips.innerHTML = CHIP_ORDER.map(function (c) {
      var on, n;
      if (c.kind === 'type') {
        on = !!activeTypes[c.type];
        n = (DATA.counts && DATA.counts[c.type]) || 0;
      } else {
        on = !!overlayOn[c.layer];
        n = overlayCount(c.layer);
      }
      var label = tr(c.labelKey, c.def);
      var data = c.kind === 'type' ? ' data-type="' + c.type + '"' : ' data-layer="' + c.layer + '"';
      return '<button type="button" class="cm-chip' + (on ? ' active' : '') + '"' + data +
        ' style="--c:' + c.color + '"><span class="cm-chip-dot"></span><span class="cm-chip-label">' +
        esc(label) + '</span><span class="cm-chip-n">' + n + '</span></button>';
    }).join('');
  }
```
`overlayCount` is defined in Task 4. To keep this task runnable on its own, add a temporary stub immediately above `buildChips` (it is replaced in Task 4):
```js
  function overlayCount() { return 0; }
```

- [ ] **Step 5: Update the chip click handler**

In `wire()`, replace:
```js
    els.chips.addEventListener('click', function (e) {
      var b = e.target.closest('.cm-chip'); if (!b) return;
      var ty = b.dataset.type;
      activeTypes[ty] = !activeTypes[ty];
      b.classList.toggle('active', activeTypes[ty]);
      render();
    });
```
with:
```js
    els.chips.addEventListener('click', function (e) {
      var b = e.target.closest('.cm-chip'); if (!b) return;
      if (b.dataset.type) {
        var ty = b.dataset.type;
        activeTypes[ty] = !activeTypes[ty];
        b.classList.toggle('active', activeTypes[ty]);
        render();
      } else if (b.dataset.layer) {
        var ly = b.dataset.layer;
        setOverlay(ly, !overlayOn[ly]);
        b.classList.toggle('active', overlayOn[ly]);
      }
    });
```
Also remove the now-dead standalone toggle wiring line in `wire()`:
```js
    if (els.sbsegToggle) els.sbsegToggle.addEventListener('click', toggleSbseg);
```
and remove `sbsegToggle: document.getElementById('sbsegToggle')` from the `els` object in `boot()`.

- [ ] **Step 6: Add the i18n key `map.typeTool` to all three locales**

In `assets/i18n/pt.json`, inside the `"map"` object, add:
```json
    "typeTool": "Ferramentas",
```
In `assets/i18n/en.json` `"map"`:
```json
    "typeTool": "Tools",
```
In `assets/i18n/es.json` `"map"`:
```json
    "typeTool": "Herramientas",
```

- [ ] **Step 7: Add two-row strip CSS**

In `assets/css/styles.css`, append:
```css
/* Comunidade filter strip: two rows of four chips. */
#mapChips.map-chips { display: grid; grid-template-columns: repeat(4, 1fr); gap: .5rem; }
@media (max-width: 760px) { #mapChips.map-chips { grid-template-columns: repeat(2, 1fr); } }
```

- [ ] **Step 8: Verify all three locales still parse**

Run: `for f in pt en es; do python3 -c "import json;json.load(open('assets/i18n/$f.json'));print('$f ok')"; done`
Expected: `pt ok`, `en ok`, `es ok`.

- [ ] **Step 9: Commit**

```bash
git add comunidade.html assets/js/mapa.js assets/css/styles.css assets/i18n/pt.json assets/i18n/en.json assets/i18n/es.json
git commit -m "Two-row filter strip on Comunidade page"
```

---

### Task 4: Aggregated Publicações + Ferramentas layers

**Files:**
- Modify: `assets/js/mapa.js` (load stats, build circle layers, `setOverlay`, `overlayCount`, popups)
- Modify: `assets/css/styles.css` (circle popup styling — reuse existing `.cm-detail`)
- Modify: `assets/i18n/{pt,en,es}.json` (popup strings)

**Interfaces:**
- Consumes: `assets/data/proceedings-stats.json`; `overlayOn`, `CHIP_ORDER` from Task 3; existing `sbsegLayer`/`loadSbsegLayer` for the `sbseg` overlay.
- Produces: `setOverlay(name, on)`, `overlayCount(name)`, `STATS` (parsed stats), `pubsLayer`/`toolsLayer` (`L.layerGroup`). Replaces the temporary `overlayCount` stub from Task 3.

- [ ] **Step 1: Eager-load stats in boot()**

In `boot()`, replace the single fetch chain:
```js
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
```
with:
```js
    Promise.all([
      fetch('assets/data/cybersecmap.json', { cache: 'no-cache' }).then(function (r) { return r.json(); }),
      fetch('assets/data/proceedings-stats.json', { cache: 'no-cache' }).then(function (r) { return r.json(); }).catch(function () { return { institutions: [] }; })
    ]).then(function (res) {
        DATA = res[0]; RECORDS = DATA.records || [];
        STATS = res[1] || { institutions: [] };
        buildMarkers();
        buildStatLayers();
        buildChips();
        buildSelects();
        wire();
        render();
        if (overlayOn.pubs && pubsLayer) map.addLayer(pubsLayer); // default-on overlay
        if (window.matchMedia('(max-width: 760px)').matches) setView('map');
      })
```

- [ ] **Step 2: Add STATS global and the stat-layer builders**

Near the other globals (`var DATA = null, RECORDS = [] ...`), add `STATS = null, pubsLayer = null, toolsLayer = null;` to the declaration list. Then add these functions (place them just above the SBSeg block comment):
```js
  function statRadius(n) { return Math.max(6, Math.min(28, 6 + Math.sqrt(n) * 2.5)); }

  function overlayCount(name) {
    if (!STATS) return 0;
    if (name === 'pubs') return STATS.institutions.filter(function (i) { return i.pub_count > 0; }).length;
    if (name === 'tools') return STATS.institutions.filter(function (i) { return i.tool_count > 0; }).length;
    if (name === 'sbseg') return 25;
    return 0;
  }

  function statPopup(inst, kind) {
    var count = kind === 'tools' ? inst.tool_count : inst.pub_count;
    var items = kind === 'tools' ? inst.tools : inst.pubs;
    var labelKey = kind === 'tools' ? 'map.toolsCount' : 'map.pubsCount';
    var labelDef = kind === 'tools' ? 'tools (Salão de Ferramentas)' : 'publications (SBSeg)';
    var list = items.slice(0, 15).map(function (p) {
      return '<li>' + (p.url
        ? '<a href="' + esc(p.url) + '" target="_blank" rel="noopener">' + esc(p.title) + '</a>'
        : esc(p.title)) + '</li>';
    }).join('');
    var more = items.length > 15 ? '<li class="cm-more">+' + (items.length - 15) + '</li>' : '';
    var color = kind === 'tools' ? TOOL_COLOR : TYPES.publication.color;
    return '<div class="cm-detail"><span class="cm-tag" style="background:' + color + '">' +
      esc(count + ' ' + tr(labelKey, labelDef)) + '</span><h4>' + esc(inst.institution) +
      '</h4><ul class="cm-pub-list">' + list + more + '</ul></div>';
  }

  function buildStatLayers() {
    pubsLayer = L.layerGroup();
    toolsLayer = L.layerGroup();
    (STATS.institutions || []).forEach(function (inst) {
      if (inst.lat == null || inst.lng == null) return;
      if (inst.pub_count > 0) {
        L.circleMarker([inst.lat, inst.lng], {
          radius: statRadius(inst.pub_count), color: '#fff', weight: 1,
          fillColor: TYPES.publication.color, fillOpacity: 0.8
        }).bindPopup(statPopup(inst, 'pubs'), { maxWidth: 320 }).addTo(pubsLayer);
      }
      if (inst.tool_count > 0) {
        L.circleMarker([inst.lat, inst.lng], {
          radius: statRadius(inst.tool_count), color: '#fff', weight: 1,
          fillColor: TOOL_COLOR, fillOpacity: 0.85
        }).bindPopup(statPopup(inst, 'tools'), { maxWidth: 320 }).addTo(toolsLayer);
      }
    });
  }
```

- [ ] **Step 3: Remove the temporary overlayCount stub from Task 3**

Delete the line added in Task 3 Step 4:
```js
  function overlayCount() { return 0; }
```
(The real `overlayCount(name)` from Step 2 replaces it.)

- [ ] **Step 4: Add setOverlay() dispatcher**

Add this function (next to `toggleSbseg`):
```js
  function setOverlay(name, on) {
    overlayOn[name] = on;
    if (name === 'pubs') {
      if (on) { if (pubsLayer) map.addLayer(pubsLayer); }
      else if (pubsLayer) map.removeLayer(pubsLayer);
    } else if (name === 'tools') {
      if (on) { if (toolsLayer) map.addLayer(toolsLayer); }
      else if (toolsLayer) map.removeLayer(toolsLayer);
    } else if (name === 'sbseg') {
      if (on) {
        loadSbsegLayer(function (failed) { if (!failed && overlayOn.sbseg) map.addLayer(sbsegLayer); });
      } else if (sbsegLayer) {
        map.removeLayer(sbsegLayer);
      }
    }
  }
```
Then delete the now-unused `toggleSbseg` function (its logic moved into `setOverlay`). Keep `loadSbsegLayer`, `sbsegIcon`, `sbsegPopupHTML`, and the `sbsegLayer`/`sbsegLoaded` globals (drop the now-unused `sbsegOn` variable).

- [ ] **Step 5: Add popup-count i18n keys**

In each `assets/i18n/*.json` `"map"` object add (PT shown; translate for en/es):
- pt: `"pubsCount": "publicações (SBSeg)", "toolsCount": "ferramentas (Salão de Ferramentas)",`
- en: `"pubsCount": "publications (SBSeg)", "toolsCount": "tools (Tool Show)",`
- es: `"pubsCount": "publicaciones (SBSeg)", "toolsCount": "herramientas (Salón de Herramientas)",`

- [ ] **Step 6: Add popup list CSS**

In `assets/css/styles.css`, append:
```css
.cm-pub-list { margin: .4rem 0 0; padding-left: 1.1rem; font-size: .82rem; line-height: 1.35; max-height: 180px; overflow:auto; }
.cm-pub-list li { margin: .15rem 0; }
.cm-pub-list .cm-more { list-style: none; opacity: .6; }
```

- [ ] **Step 7: Verify locales parse and stats load**

Run: `for f in pt en es; do python3 -c "import json;json.load(open('assets/i18n/$f.json'));print('$f ok')"; done && python3 -c "import json;d=json.load(open('assets/data/proceedings-stats.json'));print('institutions with tools:',sum(1 for i in d['institutions'] if i['tool_count']>0))"`
Expected: three `ok` lines and a non-zero tool count.

- [ ] **Step 8: Headless load check**

Load `comunidade.html` in a headless browser (e.g. `assets`-relative via a local `python3 -m http.server` in the repo root) and confirm: the chip strip shows two rows of four in the order Publicações · Edições do SBSeg · Pesquisadores · Grupos de Pesquisa / Programas de Pós-Graduação · Centros de P&D · Grupos de Trabalho · Ferramentas; the Publicações layer is visible by default; toggling Ferramentas adds magenta circles; clicking a circle shows a popup listing paper titles; the browser console has no errors.

- [ ] **Step 9: Commit**

```bash
git add assets/js/mapa.js assets/css/styles.css assets/i18n/pt.json assets/i18n/en.json assets/i18n/es.json
git commit -m "Aggregated Publicações + Ferramentas map layers"
```

---

### Task 5: Move word clouds below the Edições TOC

**Files:**
- Modify: `anais-trilha-principal.html` (move `.pub-cloud-section`)
- Modify: `anais-estendidos.html` (move `.pub-cloud-section`)
- Modify: `scripts/gen_pages.py` (emit the cloud in the new position)

**Interfaces:**
- Consumes: existing `.pub-cloud-section` markup and `initKeywordSearch()` (unchanged).
- Produces: cloud rendered immediately after `</nav>` (the `.pub-toc` "Edições" block) and before `<div class="pub-list">`.

- [ ] **Step 1: Locate the cloud block boundaries in each page**

Run: `grep -n 'pub-cloud-section\|</nav>\|<div class="pub-list"' anais-trilha-principal.html anais-estendidos.html`
Note, per file: the start line of `<section class="pub-cloud-section"` through its matching `</section>` (the cloud block), the `</nav>` that closes `.pub-toc`, and the `<div class="pub-list"` start.

- [ ] **Step 2: Move the cloud in anais-trilha-principal.html**

Cut the entire block from `<section class="pub-cloud-section" aria-labelledby="pubCloudTitle">` through its closing `</section>` (currently near the bottom, just before `</div></section>` and the `<script>` include) and paste it so it sits immediately after the `</nav>` that closes `<nav class="pub-toc">` and immediately before `<div class="pub-list" id="pubList">`. Preserve indentation (6 spaces for `<section>`).

- [ ] **Step 3: Move the cloud in anais-estendidos.html**

Do the same move in `anais-estendidos.html`: cut its `.pub-cloud-section` block from its current near-bottom position and paste it directly after the `.pub-toc` `</nav>` and before its `<div class="pub-list" ...>`.

- [ ] **Step 4: Verify position with grep (cloud now precedes the list)**

Run:
```bash
for f in anais-trilha-principal.html anais-estendidos.html; do
  echo "$f:"; grep -n 'pub-cloud-section\|<div class="pub-list"' "$f" | head -2; done
```
Expected: in each file the `pub-cloud-section` line number is SMALLER than the `pub-list` line number (cloud comes first), and `pub-cloud-section` appears exactly once.

- [ ] **Step 5: Update gen_pages.py to emit the cloud in the new position**

Inspect `scripts/gen_pages.py` for where it assembles the anais page body (search for `pub-cloud`, `cloud_html`, `pub-toc`, `pubList`). Move the cloud-emitting fragment so the generated order is: page head → search toolbar → `.pub-toc` (Edições) → `.pub-cloud-section` → `.pub-list`. Keep the generated markup byte-compatible with the hand-edited HTML from Steps 2-3 (same wrapper `<section class="pub-cloud-section" aria-labelledby="pubCloudTitle">`, same heading/note, `cloud_html(...)` call unchanged).

- [ ] **Step 6: Confirm the generator agrees (dry check, do not overwrite)**

Run: `grep -n 'pub-cloud\|pub-toc\|pubList\|cloud_html' scripts/gen_pages.py`
Expected: the cloud fragment now appears between the TOC fragment and the list fragment in source order. Do NOT run `gen_pages.py` against the repo (it is stale and may revert other manual edits); the grep is sufficient to confirm source-order agreement.

- [ ] **Step 7: Headless filter check**

Load `anais-trilha-principal.html` in a headless browser; confirm the word cloud renders directly under "Edições", and clicking a word (e.g. `blockchain`) fills `#pubSearch` and filters the list. Repeat for `anais-estendidos.html`.

- [ ] **Step 8: Commit**

```bash
git add anais-trilha-principal.html anais-estendidos.html scripts/gen_pages.py
git commit -m "Move keyword cloud below Edições on both anais pages"
```

---

## Self-Review

**Spec coverage:**
- Spec A (rename) → Task 1. ✓
- Spec B (two-row strip, exact order, SBSeg + Ferramentas inline) → Task 3. ✓
- Spec C (author→researcher matching, proceedings-stats.json, coverage caveat reported) → Task 2. ✓
- Spec D (aggregated Publicações replacing RNP pins; Ferramentas overlay; sized circles + popup list) → Tasks 3 (skip publication in cluster) + 4 (layers). ✓
- Spec E (move clouds below Edições on both pages + gen_pages.py) → Task 5. ✓

**Type/name consistency:** `overlayOn` keys `pubs|sbseg|tools` are used identically in Tasks 3-4; `setOverlay(name,on)` and `overlayCount(name)` signatures match their call sites; `pubsLayer`/`toolsLayer`/`STATS`/`TOOL_COLOR` declared before use; the Task 3 `overlayCount` stub is explicitly removed in Task 4 Step 3. `proceedings-stats.json` field names (`pub_count`, `tool_count`, `pubs`, `tools`, `institution`, `lat`, `lng`) are identical in Task 2 (producer) and Task 4 (consumer).

**Placeholder scan:** No TBD/TODO; all code steps contain full code; verification commands have expected output.
