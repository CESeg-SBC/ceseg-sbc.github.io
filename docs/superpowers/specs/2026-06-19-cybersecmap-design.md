# Mapa de Cibersegurança CESeg — Design

Date: 2026-06-19
Status: Approved

## Goal

Recreate the RNP Cybersecurity Map (https://cybersecmap.rnp.br) as a native CESeg
site page with a modern, simple, intuitive design. Replace the original's many
cascading menus (14 menus across 2 menu groups) with a single intelligent
search + filter + map experience. Add a contact form so researchers can request
inclusion, delivering submissions to ceseg.sbc@gmail.com.

## Decisions

- **Contact form**: `mailto:` link (static GitHub Pages cannot send email). The
  form validates and builds a pre-filled message to ceseg.sbc@gmail.com that
  opens in the visitor's mail client.
- **Visual design**: match the existing CESeg site (reuse styles.css palette,
  header/footer/beta-banner injected by site.js, PT/EN/ES i18n).
- **Languages**: UI labels/form are multilingual (PT/EN/ES via data-i18n). The
  RNP data itself stays in its original (mostly English) form.
- **No em dash** ("—") in any site text; use "·" or comma.

## Data source

RNP map is an Angular SPA backed by 8 relative API endpoints (same origin), with
**no CORS headers** — so the browser on ceseg-sbc.github.io cannot fetch them
live. We bundle a cleaned static snapshot.

Endpoints: `/settings/ /menugroup/ /menu/ /tag/ /tagrelationship/ /location/
/link/ /linksgroup/` (link/linksgroup are empty).

Data model (inconsistent across types):
- `location` (1824): geo point — id, name, description (HTML), lat, lng.
- `tag` (1978): a filter value — id, name, color, parent_menu, related_locations[],
  description (HTML). For some types the entity info lives in the tag, for others
  in the location.
- `menu` (14): grouping (e.g. "Brazilian Cybersecurity Researchers").

Entity types and where their info lives:
- **Researchers** (menu 1, 87): info in *location* description (Researcher Name,
  Institution, Research Interests, Lattes link, Research Group, Postgraduate Program).
- **Research Groups** (menu 2, 123): info in *tag* description (Group Name,
  Institution, State, Leader, CNPq URL); location = institution geo.
- **Graduate Programs** (menu 4, 266): info in *tag* description (Program name,
  Institution); location = institution geo.
- **R&D Centers** (menu 11, 7): info in *location* description (link, address).
- **Working Groups** (menu 12, 24): info in *location* description (Group Name,
  Principal Researcher, Team, Institution, State, Project).
- **Publications** = Productions (menu 10, 569) + Articles (menu 14, 729): info in
  *location* description (Title, Institution, State, Authors, Year).

Facets derived by reverse-indexing tags onto locations:
- **State**: menus 5/6/8 (by-state) tags, or parsed from description; normalized
  to 2-letter UF code.
- **Topic of interest**: menu 3 tags (34 topics), mapped to researcher locations.

## Architecture

### 1. Data pipeline — `scripts/fetch_cybersecmap.py`
- Downloads the 8 endpoints (re-runnable to refresh); saves raw JSON to
  `scripts/cybersecmap_raw/`.
- Parses each entity type into a unified record:
  `{id, type, name, institution, state, lat, lng, topics[], year, people[],
    links{lattes,group,program,url}, html}`.
- Writes one compact `assets/data/cybersecmap.json` plus light metadata
  (counts per type, list of states, list of topics).

### 2. Page — `mapa.html`
Static HTML using site conventions (data-i18n, empty #site-header/#site-footer,
loads site.js then mapa.js + Leaflet/markercluster from CDN).
- **Toolbar**: one search box (matches name, institution, topic, state); a row of
  type filter chips; State and Topic dropdowns; live "showing X of Y" count.
- **Split layout**: results list (cards) ↔ Leaflet map. Mobile: list/map toggle.
- **Detail**: click card/marker → detail panel with parsed fields + links.
- **Contact section** (`#contribuir`): mailto form.

### 3. Map logic — `assets/js/mapa.js`
Self-initializes when `#cybermap` is present (guards so it is inert on other
pages). Loads cybersecmap.json, builds Leaflet map of Brazil, markers colored by
type, clustered via Leaflet.markercluster. Publications layer off by default.
Search/filter recompute the visible set and sync list ↔ markers. Form handler
validates and opens the mailto link.

### 4. Integration
- Add "Mapa" to NAV in site.js (top-level).
- Add `map.*` and `mapForm.*` keys to pt/en/es.json.
- Add map styles to styles.css.

## Out of scope (YAGNI)
- Live API fetch (blocked by CORS; snapshot instead).
- Backend form storage (mailto only).
- Editing/admin of the data.

## Addendum (2026-06-19): SBSeg editions overlay

A second, toggleable layer on the same map showing where each SBSeg edition was
held. Decided: **separate toggle layer** (not a filter chip), **default off**,
**reuse the sbseg.html table data only** (no organizers/TPC/awards).

- **Data** `assets/data/sbseg-editions.json`: editions grouped by host city, so a
  city that hosted several editions is a single pin. Each city is
  `{city, uf, lat, lng, editions[]}`; each edition is
  `{n, year, dates, online?, wseg?, links{site?, clone?, anais?}}`. 20 cities /
  25 editions (2001-2025). `wseg:true` marks the 2001-2004 WSeg-era editions.
  Source of the link set is the `sbseg.html` edition table; coordinates are added
  per host city.
- **UI** a `.map-layer-toggle` button below the RNP type chips ("SBSeg editions"
  + count), `aria-pressed` reflecting state. It is independent of the RNP chips,
  search, results list and detail panel.
- **Logic** `mapa.js` gains a self-contained block: lazy-fetches the JSON on first
  toggle into its own Leaflet `layerGroup` (no markercluster; only ~20 pins),
  adds/removes it on toggle, guards against a load that finishes after the user
  toggled back off. Pins are navy diamonds (distinct from RNP circles); popup
  lists the city's editions with site/clone/anais links.
- **i18n** `map.sbsegToggle/sbsegSite/sbsegClone/sbsegAnais/sbsegOnline` in
  pt/en/es. **Styles** `.map-layer-toggle`, `.sbseg-pin`, `.sbseg-detail` family.
- **Out of scope** organizers/TPC/awards per edition; a 2026 entry (no completed
  edition); clustering.
