# Comunidade page + proceedings stats + word-cloud repositioning

Date: 2026-06-19
Status: Approved (design)

## Goals

Three related changes requested by the user:

1. Rebrand the map page from `mapa.html` to `comunidade.html`, and restructure the
   filter strip below the search box into two explicit rows.
2. Derive **publications per institution** and **tools per institution** from the
   real SBSeg proceedings (`anais-trilha-principal.html` + `anais-estendidos.html`)
   by matching paper authors to known researchers, and show them as aggregated
   map layers.
3. Move the existing keyword word clouds on both anais pages to sit **right below
   the "Edições" table of contents** (they currently sit at the bottom).

## Non-goals

- No scraping of `sol.sbc.org.br` for real author affiliations (rejected during
  brainstorming as too heavy).
- No new word-cloud generation logic; the clouds already exist and already filter
  on click. Only their position changes.
- No redesign of the contribution form or the data-source panel.

## A. Page rename: `mapa.html` → `comunidade.html`

- `git mv mapa.html comunidade.html`.
- `assets/js/site.js`: nav entry `{key:'nav.mapa', href:'mapa.html'}` → `href:'comunidade.html'`.
  The visible label (`nav.mapa`) already reads "Comunidade" and is left unchanged.
- `comunidade.html`: `body[data-page="mapa"]` → `data-page="comunidade"`.
- Grep the repo for any other inbound link to `mapa.html` (footer, index, anais)
  and update. `assets/js/mapa.js` keeps its filename (internal include only).

## B. Two-row filter strip

Today there are two separate controls below the search box:
`#mapChips` (entity-type chips) and `.map-layers` (a single "Edições do SBSeg"
toggle). Merge them into one strip rendered by `buildChips()` in `mapa.js`, in two
rows of four, in this exact order:

```
Row 1: [Publicações] [Edições do SBSeg] [Pesquisadores] [Grupos de Pesquisa]
Row 2: [Programas de Pós-Graduação] [Centros de P&D] [Grupos de Trabalho] [Ferramentas]
```

Chip kinds:
- **Filter chips** (Publicações, Pesquisadores, Grupos de Pesquisa, Programas de
  Pós-Graduação, Centros de P&D, Grupos de Trabalho): toggle a `record.type` in
  `activeTypes`, exactly as today.
- **Overlay chips** (Edições do SBSeg, Ferramentas): toggle a separate Leaflet
  `layerGroup` (lazy-loaded), independent of the records filter. "Edições do
  SBSeg" reuses the existing `toggleSbseg()` logic, now styled as a chip instead
  of a standalone button. "Ferramentas" is new (section D).

Implementation: drive the strip from an ordered list of chip descriptors
(`{id, kind, type|layer, labelKey, def}`). `buildChips()` renders all of them;
the click handler dispatches by `kind`. CSS uses a grid/flex wrap so the two rows
fall out naturally at 4 columns. The standalone `.map-layers` block and the
default-off `publication` exception in `activeTypes` are removed (publication is
now an ordinary, on-by-default filter chip backed by the new aggregated layer).

## C. Proceedings → per-institution stats

New script `scripts/fetch_proceedings_stats.py` (vanilla Python, no deps, matching
the existing `scripts/*.py` style):

1. **Parse papers.** From `anais-trilha-principal.html` and
   `anais-estendidos.html`, read each `li.pub-paper`'s `data-authors`, `data-title`,
   and the SOL URL from `data-cite`. Track which papers fall under a
   `Salão de Ferramentas` `<h3 class="pub-section">` (tools papers).
2. **Author index.** From `assets/data/cybersecmap.json`, build a name → institution
   map from `researcher` records (by name) and `group` records (by `leader`), each
   carrying `institution`, `state`, `lat`, `lng`. Key on
   `(first_token, last_token)` of the accent-folded name; first writer wins.
3. **Attribute.** For each paper, split authors on `,`/`;`, fold, look up each in
   the index. A paper is attributed to **each distinct institution** among its
   matched authors (counted once per institution). Unmatched papers are dropped.
4. **Aggregate.** Produce, per institution: `pub_count`, `tool_count`, `lat`,
   `lng`, `state`, and the list of matched paper titles (+ SOL links) for each.
5. **Emit** `assets/data/proceedings-stats.json`:
   ```json
   {
     "generated_from": ["anais-trilha-principal.html", "anais-estendidos.html"],
     "match_rate": {"papers": 0.54, "tool_papers": 0.0},
     "institutions": [
       {"institution": "...", "state": "RJ", "lat": -22.9, "lng": -43.2,
        "pub_count": 12, "tool_count": 2,
        "pubs": [{"title": "...", "url": "..."}],
        "tools": [{"title": "...", "url": "..."}]}
     ]
   }
   ```

**Coverage caveat (documented, surfaced after the run):** the researcher/leader
index is ~210 names, so ~54% of trilha papers match ≥1 author; tool-paper coverage
may be lower. Unmatched papers do not appear in the per-institution counts. The
match rate is written into the JSON and reported to the user.

## D. Map layers for Publicações & Ferramentas

In `mapa.js`, lazy-load `proceedings-stats.json` the first time either the
**Publicações** filter chip is active or the **Ferramentas** overlay chip is
toggled on.

- **Publicações layer:** replaces the old 1298 RNP `publication` records. One
  circle marker per institution with `pub_count > 0`. Radius scales with
  `pub_count` (e.g. `r = clamp(6 + sqrt(count)*2.5, 6, 28)`). Popup: institution
  name, "N publicações (SBSeg)", and the matched paper titles linked to SOL.
- **Ferramentas overlay:** one circle marker per institution with `tool_count > 0`,
  radius scaled by `tool_count`, distinct color. Popup: institution, "N ferramentas
  (Salão de Ferramentas)", matched tool titles linked to SOL.

Both are their own `layerGroup`s (no clustering), consistent with the existing
SBSeg overlay. Regenerating `cybersecmap.json` is NOT required: `mapa.js` simply
stops creating per-paper markers for `type === 'publication'` records and instead
renders the aggregated Publicações layer from `proceedings-stats.json`. The count
on the Publicações chip becomes the number of institutions with publications.

## E. Word-cloud repositioning

On both `anais-trilha-principal.html` and `anais-estendidos.html`, move the whole
`<section class="pub-cloud-section">` block from the bottom of the page to
**immediately after** the `<nav class="pub-toc">…</nav>` ("Edições") block, before
the papers list. Mirror the same move in `scripts/gen_pages.py` so a future
regeneration keeps the cloud in the new spot. Cloud content and the
`initKeywordSearch()` click-to-filter behavior are unchanged.

## Files touched

- `mapa.html` → `comunidade.html` (rename + body data-page + remove `.map-layers`)
- `assets/js/site.js` (nav href)
- `assets/js/mapa.js` (chip descriptors, 2-row strip, ferramentas overlay,
  aggregated publication layer, stats fetch)
- `assets/css/styles.css` (2-row strip; circle-marker / overlay-chip styles)
- `assets/i18n/{pt,en,es}.json` (chip labels: ferramentas; popup strings)
- `scripts/fetch_proceedings_stats.py` (NEW)
- `assets/data/proceedings-stats.json` (NEW, generated)
- `anais-trilha-principal.html`, `anais-estendidos.html` (move cloud section)
- `scripts/gen_pages.py` (cloud position)

## Testing / verification

- Run `fetch_proceedings_stats.py`; confirm it emits valid JSON and report the
  match rate.
- Load `comunidade.html` headless: chip strip renders two rows in the specified
  order; toggling Publicações and Ferramentas adds/removes the aggregated layers;
  popups list matched papers; no JS console errors; all three i18n files parse.
- Load both anais pages: cloud appears directly under "Edições"; clicking a word
  filters the list as before.
```
