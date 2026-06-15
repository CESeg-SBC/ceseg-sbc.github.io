# CESeg Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Use the **frontend-design** skill when building visual markup/CSS for polish.

**Goal:** Rebuild the CESeg website (`ceseg.org`) as a clean, modern, institutional static site published at `https://ceseg-sbc.github.io`, with full content (faithful clone) and PT/EN/ES language switching.

**Architecture:** Pure static HTML/CSS/JS, multi-page (one file per original route). A single `assets/js/site.js` renders the shared header (with dropdown nav) and footer into placeholders on every page, handles the mobile menu, marks the active nav item, and runs `data-i18n` translation from per-language JSON dictionaries. No build step, no dependencies. `.nojekyll` so GitHub Pages serves files as-is.

**Tech Stack:** HTML5, CSS3 (custom properties, fl/grid, mobile-first), vanilla ES (no framework), JSON i18n dictionaries. Local preview via `python3 -m http.server`. No Node available.

**Design direction:** "Academic Clean" — light background, navy `#1e3a8a`, serif headings, sans-serif body, generous whitespace. **No numeric statistics counters.**

---

## Reference: original site routes → new files

Navigation groups (top-level items; ◦ = dropdown child). New filenames are ASCII (no accents).

| Original route | New file | i18n namespace | Nav placement |
|---|---|---|---|
| `/` (Home) | `index.html` | `home` | top: Início |
| `/lista-de-discucao` | `lista-de-discussao.html` | `lista` | top: Lista de Discussão |
| `/organizacao` | `organizacao.html` | `org` | top: Organização |
| `/comissões` | `comissoes.html` | `comissoes` | ◦ under Organização |
| `/conferencistas` | `conferencistas.html` | `conferencistas` | ◦ under Organização |
| `/grupos` | `grupos.html` | `grupos` | top: Grupos |
| `/instituto` | `instituto.html` | `instituto` | ◦ under Grupos |
| `/sbseg` | `sbseg.html` | `sbseg` | top: SBSeg |
| `/anais-trilha-principal` | `anais.html` | `anais` | ◦ under SBSeg |
| `/mini-cursos` | `minicursos.html` | `minicursos` | ◦ under SBSeg |
| `/wise` | `wise.html` | `wise` | ◦ under SBSeg |
| `/homenageados` | `homenageados.html` | `homenageados` | top: Homenagens |
| `/publicacoes` | `publicacoes.html` | `publicacoes` | top: Publicações |
| `/referenciais` | `referenciais.html` | `referenciais` | ◦ under Publicações |
| `/onde-publicar` | `onde-publicar.html` | `ondepublicar` | ◦ under Publicações |
| `/documentos` | `documentos.html` | `documentos` | top: Documentos |
| `/atas` | `atas.html` | `atas` | ◦ under Documentos |
| `/regimentos` | `regimentos.html` | `regimentos` | ◦ under Documentos |
| `/portarias` | `portarias.html` | `portarias` | ◦ under Documentos |

Also on Home (anchors): Sobre, Informações Gerais, Ações da Comunidade, Contato. SBSeg 2025 external link → `https://sbseg2025.ppgia.pucpr.br/`.

---

## File structure

```
/
├── index.html ... (19 page files above)
├── assets/
│   ├── css/styles.css
│   ├── js/site.js
│   └── i18n/{pt,en,es}.json
├── .nojekyll
└── README.md
```

Conventions used by every page file:
- `<html lang="pt">` (updated by JS).
- `<head>`: charset, viewport, `<title data-i18n="<ns>.title">`, meta description `data-i18n="<ns>.desc">`, `<link rel="stylesheet" href="assets/css/styles.css">`, and `<body data-page="<file-without-ext>">`.
- Body: `<header id="site-header"></header>` · `<main>…page content with data-i18n…</main>` · `<footer id="site-footer"></footer>` · `<script src="assets/js/site.js"></script>`.
- Paths are **relative** (`assets/...`) so the site works at any base path.

---

## Task 1: Scaffolding + CSS foundation

**Files:**
- Create: `.nojekyll` (empty)
- Create: `assets/css/styles.css`

- [ ] **Step 1: Create `.nojekyll`**

```bash
touch .nojekyll
```

- [ ] **Step 2: Write `assets/css/styles.css` (design tokens + base + components)**

```css
:root{
  --navy:#1e3a8a; --navy-dark:#0f172a; --link:#2563eb;
  --ink:#0f172a; --muted:#475569; --faint:#64748b;
  --bg:#ffffff; --bg-alt:#f8fafc; --border:#e2e8f0;
  --serif:Georgia,"Times New Roman",serif;
  --sans:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  --maxw:1080px; --radius:12px;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--sans);color:var(--ink);background:var(--bg);line-height:1.6}
img{max-width:100%;height:auto;display:block}
a{color:var(--link);text-decoration:none}
a:hover{text-decoration:underline}
h1,h2,h3{font-family:var(--serif);line-height:1.15;color:var(--ink)}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 24px}
.eyebrow{font-family:var(--sans);font-size:.72rem;font-weight:700;letter-spacing:.12em;
  text-transform:uppercase;color:var(--navy)}
.section{padding:56px 0;border-top:1px solid var(--border)}
.section h2{font-size:1.75rem;margin-bottom:.6rem}
.lead{color:var(--muted);max-width:680px}
.btn{display:inline-block;font-weight:600;font-size:.95rem;padding:11px 20px;border-radius:8px;
  border:1px solid var(--navy)}
.btn-primary{background:var(--navy);color:#fff}
.btn-primary:hover{background:#1b3578;text-decoration:none}
.btn-ghost{background:transparent;color:var(--navy)}
.btn-ghost:hover{background:var(--bg-alt);text-decoration:none}

/* Header */
.site-header{position:sticky;top:0;z-index:50;background:var(--bg);
  border-bottom:1px solid var(--border)}
.nav{display:flex;align-items:center;justify-content:space-between;height:64px}
.brand{font-family:var(--serif);font-weight:700;font-size:1.35rem;color:var(--navy)}
.nav-links{display:flex;align-items:center;gap:4px;list-style:none}
.nav-links a, .nav-toggle{color:var(--muted);font-size:.9rem;font-weight:500;
  padding:8px 12px;border-radius:6px;background:none;border:none;cursor:pointer;font-family:inherit}
.nav-links a:hover,.nav-toggle:hover{color:var(--navy);background:var(--bg-alt);text-decoration:none}
.nav-links a.active{color:var(--navy);font-weight:600}
.has-drop{position:relative}
.dropdown{position:absolute;top:100%;left:0;min-width:220px;background:var(--bg);
  border:1px solid var(--border);border-radius:10px;box-shadow:0 8px 24px rgba(15,23,42,.1);
  padding:6px;display:none;list-style:none}
.has-drop:hover .dropdown,.has-drop:focus-within .dropdown{display:block}
.dropdown a{display:block}
.lang{display:flex;gap:2px;margin-left:8px;border:1px solid var(--border);border-radius:8px;
  overflow:hidden}
.lang button{border:none;background:none;padding:6px 9px;font-size:.78rem;font-weight:600;
  color:var(--faint);cursor:pointer}
.lang button.active{background:var(--navy);color:#fff}
.hamburger{display:none}

/* Hero */
.hero{background:linear-gradient(180deg,var(--bg-alt),var(--bg));padding:72px 0 56px}
.hero h1{font-size:2.6rem;max-width:640px;margin:14px 0}
.hero .lead{font-size:1.1rem}
.hero .cta{display:flex;gap:12px;margin-top:26px;flex-wrap:wrap}

/* Cards / feature */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.card{border:1px solid var(--border);border-radius:var(--radius);padding:24px;background:var(--bg)}
.card h3{font-size:1.15rem;margin-bottom:.4rem}
.card p{color:var(--muted);font-size:.95rem}
.feature{background:var(--navy);color:#fff;border-radius:14px;padding:36px;
  display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap}
.feature h2{color:#fff;font-size:1.5rem}
.feature p{opacity:.88;max-width:460px;margin-top:6px}
.news{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.news .item{border-left:3px solid var(--navy);padding-left:14px}
.news .item strong{display:block}
.news .item span{color:var(--faint);font-size:.88rem}

/* Generic content page */
.page-head{background:var(--bg-alt);border-bottom:1px solid var(--border);padding:48px 0}
.page-head h1{font-size:2.1rem}
.content{padding:48px 0}
.content p{margin-bottom:1rem;color:var(--ink)}
.content h2{font-size:1.4rem;margin:1.6rem 0 .6rem}
.content ul{margin:0 0 1rem 1.2rem;color:var(--ink)}
.content li{margin-bottom:.4rem}
.partners{background:var(--bg-alt);text-align:center}
.partners .logos{display:flex;gap:28px;justify-content:center;flex-wrap:wrap;
  align-items:center;margin-top:18px;opacity:.7}

/* Footer */
.site-footer{background:var(--navy-dark);color:#cbd5e1;padding:40px 0;margin-top:24px}
.site-footer .cols{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:24px}
.site-footer h4{color:#fff;font-family:var(--sans);font-size:.95rem;margin-bottom:10px}
.site-footer a{color:#cbd5e1}
.site-footer .brand-f{font-family:var(--serif);color:#fff;font-size:1.2rem;margin-bottom:8px}
.site-footer small{display:block;color:#94a3b8;margin-top:14px}

/* Mobile */
@media (max-width:860px){
  .hamburger{display:inline-block}
  .nav-links{display:none;position:absolute;top:64px;left:0;right:0;background:var(--bg);
    flex-direction:column;align-items:stretch;border-bottom:1px solid var(--border);padding:8px}
  .nav-links.open{display:flex}
  .dropdown{position:static;display:block;box-shadow:none;border:none;padding-left:12px}
  .grid-2,.news,.site-footer .cols{grid-template-columns:1fr}
  .hero h1{font-size:2rem}
}
```

- [ ] **Step 3: Commit**

```bash
git add .nojekyll assets/css/styles.css
git commit -m "feat: add static scaffolding and Academic Clean CSS foundation"
```

---

## Task 2: Shared header/footer + active nav (`site.js` part 1)

**Files:**
- Create: `assets/js/site.js`

- [ ] **Step 1: Write the nav model + header/footer renderer**

Create `assets/js/site.js` with the navigation tree and rendering. All visible strings use i18n keys (resolved in Task 3); `href` values are the real filenames from the route table.

```js
// ---- Navigation model (label keys resolved via i18n) ----
const NAV = [
  {key:'nav.home', href:'index.html'},
  {key:'nav.lista', href:'lista-de-discussao.html'},
  {key:'nav.org', href:'organizacao.html', children:[
    {key:'nav.comissoes', href:'comissoes.html'},
    {key:'nav.conferencistas', href:'conferencistas.html'}]},
  {key:'nav.grupos', href:'grupos.html', children:[
    {key:'nav.instituto', href:'instituto.html'}]},
  {key:'nav.sbseg', href:'sbseg.html', children:[
    {key:'nav.anais', href:'anais.html'},
    {key:'nav.minicursos', href:'minicursos.html'},
    {key:'nav.wise', href:'wise.html'}]},
  {key:'nav.homenagens', href:'homenageados.html'},
  {key:'nav.publicacoes', href:'publicacoes.html', children:[
    {key:'nav.referenciais', href:'referenciais.html'},
    {key:'nav.ondepublicar', href:'onde-publicar.html'}]},
  {key:'nav.documentos', href:'documentos.html', children:[
    {key:'nav.atas', href:'atas.html'},
    {key:'nav.regimentos', href:'regimentos.html'},
    {key:'nav.portarias', href:'portarias.html'}]},
];

function navItemHTML(item, current){
  const active = item.href === current ? ' class="active"' : '';
  const label = `<span data-i18n="${item.key}"></span>`;
  if(item.children){
    const kids = item.children.map(c =>
      `<li><a href="${c.href}"${c.href===current?' class="active"':''}><span data-i18n="${c.key}"></span></a></li>`).join('');
    return `<li class="has-drop"><a href="${item.href}"${active}>${label}</a>
      <ul class="dropdown">${kids}</ul></li>`;
  }
  return `<li><a href="${item.href}"${active}>${label}</a></li>`;
}

function renderHeader(current){
  const links = NAV.map(i => navItemHTML(i, current)).join('');
  return `<div class="wrap nav">
    <a class="brand" href="index.html">CESeg</a>
    <button class="nav-toggle hamburger" aria-label="Menu" aria-expanded="false">☰</button>
    <ul class="nav-links" id="navLinks">${links}
      <li class="lang" role="group" aria-label="Idioma">
        <button data-lang="pt">PT</button><button data-lang="en">EN</button><button data-lang="es">ES</button>
      </li>
    </ul></div>`;
}

function renderFooter(){
  return `<div class="wrap cols">
    <div><div class="brand-f">CESeg</div>
      <p data-i18n="footer.about"></p>
      <small data-i18n="footer.cnpj"></small></div>
    <div><h4 data-i18n="footer.contactTitle"></h4>
      <p><a href="mailto:ceseg.sbc@gmail.com">ceseg.sbc@gmail.com</a></p>
      <p>(51) 3308-6835</p>
      <p data-i18n="footer.address"></p></div>
    <div><h4 data-i18n="footer.navTitle"></h4>
      <p><a href="organizacao.html" data-i18n="nav.org"></a></p>
      <p><a href="grupos.html" data-i18n="nav.grupos"></a></p>
      <p><a href="sbseg.html" data-i18n="nav.sbseg"></a></p>
      <p><a href="publicacoes.html" data-i18n="nav.publicacoes"></a></p>
      <p><a href="documentos.html" data-i18n="nav.documentos"></a></p></div>
  </div>`;
}
```

- [ ] **Step 2: Verify it parses (no syntax errors) by loading in browser later in Task 4.** No standalone test here; covered by Task 4 integration check.

- [ ] **Step 3: Commit**

```bash
git add assets/js/site.js
git commit -m "feat: add shared header/footer nav model in site.js"
```

---

## Task 3: i18n engine + boot (`site.js` part 2) + `pt.json` skeleton

**Files:**
- Modify: `assets/js/site.js` (append)
- Create: `assets/i18n/pt.json`

- [ ] **Step 1: Append the i18n + boot logic to `site.js`**

```js
// ---- i18n ----
const LANGS = ['pt','en','es'];
let DICT = {};

function t(key){
  return key.split('.').reduce((o,k)=> (o&&o[k]!=null)?o[k]:null, DICT) ?? null;
}
function applyI18n(){
  document.querySelectorAll('[data-i18n]').forEach(el=>{
    const val = t(el.getAttribute('data-i18n'));
    if(val==null) return;            // missing key: leave existing (PT fallback) text
    if(el.tagName==='TITLE') document.title = val;
    else if(el.hasAttribute('data-i18n-attr')) el.setAttribute(el.getAttribute('data-i18n-attr'), val);
    else el.innerHTML = val;
  });
  document.querySelectorAll('.lang button').forEach(b=>
    b.classList.toggle('active', b.dataset.lang===currentLang()));
  document.documentElement.lang = currentLang();
}
function currentLang(){
  const url = new URLSearchParams(location.search).get('lang');
  const stored = localStorage.getItem('ceseg-lang');
  const nav = (navigator.language||'pt').slice(0,2);
  const pick = url || stored || (LANGS.includes(nav)?nav:'pt');
  return LANGS.includes(pick) ? pick : 'pt';
}
async function loadLang(lang){
  try{
    const res = await fetch(`assets/i18n/${lang}.json`,{cache:'no-cache'});
    DICT = await res.json();
  }catch(e){ DICT = {}; }
  applyI18n();
}
function setLang(lang){
  localStorage.setItem('ceseg-lang', lang);
  loadLang(lang);
}

// ---- Boot ----
document.addEventListener('DOMContentLoaded', ()=>{
  const current = (document.body.dataset.page||'index') + '.html';
  const header = document.getElementById('site-header');
  const footer = document.getElementById('site-footer');
  if(header){ header.className='site-header'; header.innerHTML = renderHeader(current); }
  if(footer){ footer.className='site-footer'; footer.innerHTML = renderFooter(); }

  const toggle = document.querySelector('.nav-toggle');
  const links = document.getElementById('navLinks');
  if(toggle&&links) toggle.addEventListener('click', ()=>{
    const open = links.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open?'true':'false');
  });
  document.querySelectorAll('.lang button').forEach(b=>
    b.addEventListener('click', ()=> setLang(b.dataset.lang)));

  loadLang(currentLang());
});
```

- [ ] **Step 2: Create `assets/i18n/pt.json` with nav + footer keys (page keys added per page later)**

```json
{
  "nav":{"home":"Início","lista":"Lista de Discussão","org":"Organização",
    "comissoes":"Comissões","conferencistas":"Conferencistas Sêniores",
    "grupos":"Grupos","instituto":"Instituto","sbseg":"SBSeg",
    "anais":"Anais — Trilha Principal","minicursos":"Minicursos","wise":"WISE",
    "homenagens":"Homenagens","publicacoes":"Publicações",
    "referenciais":"Referenciais","ondepublicar":"Onde Publicar",
    "documentos":"Documentos","atas":"Atas","regimentos":"Regimentos","portarias":"Portarias"},
  "footer":{
    "about":"Comissão Especial de Cibersegurança da Sociedade Brasileira de Computação.",
    "cnpj":"CNPJ 29.532.264/0001-78",
    "contactTitle":"Contato",
    "address":"Av. Bento Gonçalves, 9500 — Porto Alegre/RS",
    "navTitle":"Navegação"}
}
```

- [ ] **Step 3: Commit**

```bash
git add assets/js/site.js assets/i18n/pt.json
git commit -m "feat: add i18n engine, boot logic, and PT nav/footer dictionary"
```

---

## Task 4: Home page (`index.html`) + home PT content + integration check

**Files:**
- Create: `index.html` (overwrites the placeholder)
- Modify: `assets/i18n/pt.json` (add `home` namespace)

- [ ] **Step 1: Extract real Home content** using WebFetch on `https://www.ceseg.org` with prompt: *"Give the full verbatim Portuguese text of the home page: the about/SOBRE paragraph, 'Informações Gerais', 'Ações da Comunidade' items, and contact info."* Use the returned text to fill the `home` strings below (replace the provided summary text only if the fetch returns fuller/updated copy; keep it factual, never invent).

- [ ] **Step 2: Write `index.html`**

```html
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title data-i18n="home.title">CESeg — Comissão Especial de Cibersegurança</title>
  <meta name="description" data-i18n="home.desc" data-i18n-attr="content" content="">
  <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body data-page="index">
  <header id="site-header"></header>
  <main>
    <section class="hero"><div class="wrap">
      <div class="eyebrow" data-i18n="home.eyebrow">Sociedade Brasileira de Computação · desde 2004</div>
      <h1 data-i18n="home.h1">Comissão Especial de Cibersegurança</h1>
      <p class="lead" data-i18n="home.lead">Congrega e articula a comunidade acadêmica brasileira atuando na área de cibersegurança.</p>
      <div class="cta">
        <a class="btn btn-primary" href="https://sbseg2025.ppgia.pucpr.br/" data-i18n="home.ctaSbseg">Conheça o SBSeg 2025</a>
        <a class="btn btn-ghost" href="#sobre" data-i18n="home.ctaAbout">Sobre a comissão</a>
      </div>
    </div></section>

    <section class="section" id="sobre"><div class="wrap">
      <div class="eyebrow" data-i18n="home.aboutEyebrow">Sobre</div>
      <h2 data-i18n="home.aboutH2">O que é o CESeg</h2>
      <p class="lead" data-i18n="home.aboutText">Comissão Especial da SBC que reúne pesquisadores, estudantes, indústria e profissionais em torno da ciência e tecnologia de segurança cibernética no Brasil.</p>
    </div></section>

    <section class="section"><div class="wrap">
      <div class="feature">
        <div>
          <div class="eyebrow" style="color:#fff;opacity:.85" data-i18n="home.eventEyebrow">Evento principal</div>
          <h2 data-i18n="home.eventH2">SBSeg 2025 — Foz do Iguaçu</h2>
          <p data-i18n="home.eventText">Simpósio Brasileiro de Cibersegurança: o fórum que conecta pesquisa, indústria e estudantes.</p>
        </div>
        <a class="btn" style="background:#fff;color:var(--navy)" href="https://sbseg2025.ppgia.pucpr.br/" data-i18n="home.eventCta">Saiba mais →</a>
      </div>
    </div></section>

    <section class="section"><div class="wrap grid-2">
      <a class="card" href="instituto.html"><h3 data-i18n="home.cardInstH3">Instituto Nacional de Segurança Cibernética</h3>
        <p data-i18n="home.cardInstText">Colaboração entre as principais instituições de pesquisa do país, no programa INCT/CNPq.</p></a>
      <a class="card" href="grupos.html"><h3 data-i18n="home.cardGroupsH3">Grupos de Pesquisa</h3>
        <p data-i18n="home.cardGroupsText">Segurança de sistemas, de redes e da informação em universidades de todo o Brasil.</p></a>
    </div></section>

    <section class="section" id="acoes"><div class="wrap">
      <div class="eyebrow" data-i18n="home.commEyebrow">Comunidade</div>
      <h2 data-i18n="home.commH2">Ações da comunidade</h2>
      <div class="news" style="margin-top:18px">
        <div class="item"><strong data-i18n="home.comm1t">Computação Brasil</strong><span data-i18n="home.comm1s">Edição sobre cibersegurança</span></div>
        <div class="item"><strong data-i18n="home.comm2t">Auditoria do sistema eleitoral</strong><span data-i18n="home.comm2s">Participação da comunidade</span></div>
        <div class="item"><strong data-i18n="home.comm3t">Workshops e carreira</strong><span data-i18n="home.comm3s">Formação na área</span></div>
      </div>
    </div></section>

    <section class="section partners"><div class="wrap">
      <div class="eyebrow" data-i18n="home.partnersEyebrow">Instituições parceiras</div>
      <div class="logos" data-i18n="home.partnersNote">Logos das instituições parceiras</div>
    </div></section>
  </main>
  <footer id="site-footer"></footer>
  <script src="assets/js/site.js"></script>
</body>
</html>
```

- [ ] **Step 3: Add `home` namespace to `assets/i18n/pt.json`** (merge into the existing JSON object) with keys matching every `data-i18n` above: `title, desc, eyebrow, h1, lead, ctaSbseg, ctaAbout, aboutEyebrow, aboutH2, aboutText, eventEyebrow, eventH2, eventText, eventCta, cardInstH3, cardInstText, cardGroupsH3, cardGroupsText, commEyebrow, commH2, comm1t, comm1s, comm2t, comm2s, comm3t, comm3s, partnersEyebrow, partnersNote`. Use the verbatim text from Step 1 where available; otherwise the default strings shown in the HTML.

- [ ] **Step 4: Integration check — serve and verify**

```bash
python3 -m http.server 8000 >/dev/null 2>&1 &  SRV=$!
sleep 1
curl -s http://localhost:8000/index.html | grep -q 'id="site-header"' && echo "HEADER placeholder OK"
curl -s http://localhost:8000/assets/i18n/pt.json | python3 -c "import json,sys; json.load(sys.stdin); print('pt.json valid')"
curl -s http://localhost:8000/assets/js/site.js | grep -q 'renderHeader' && echo "site.js OK"
kill $SRV
```
Expected: `HEADER placeholder OK`, `pt.json valid`, `site.js OK`. Also load `http://localhost:8000/` via the visual companion / browser and confirm header dropdowns, hero, footer render and the PT/EN/ES buttons appear (EN/ES will fall back to PT until Task 7).

- [ ] **Step 5: Commit**

```bash
git add index.html assets/i18n/pt.json
git commit -m "feat: build Academic Clean home page with PT content"
```

---

## Task 5: Content-page template + build all inner pages (PT)

Every inner page shares the same structure. Build them **one at a time**, each in its own commit, following this pattern. This task repeats for each row in the route table except `index.html`.

**Per-page procedure (repeat for each file):**

- [ ] **Step A: Extract real content.** WebFetch the original route (column 1 of the route table) with prompt: *"Provide the full verbatim Portuguese textual content of this page: headings, paragraphs, lists, names, and any links with their URLs. Do not summarize."*

- [ ] **Step B: Create `<file>.html`** from this template, replacing `NS` with the page's i18n namespace and `data-page` with the filename (no extension). Convert extracted content into semantic HTML inside `.content` (use `<h2>`, `<p>`, `<ul><li>`, and `<a href>` for real links). Wrap each translatable text node with `data-i18n="NS.<key>"`. For long bodies, use one key per paragraph/heading (e.g., `NS.p1`, `NS.p2`, `NS.li1`).

```html
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title data-i18n="NS.title">CESeg</title>
  <meta name="description" data-i18n="NS.desc" data-i18n-attr="content" content="">
  <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body data-page="FILENAME">
  <header id="site-header"></header>
  <main>
    <section class="page-head"><div class="wrap">
      <div class="eyebrow" data-i18n="NS.eyebrow">CESeg</div>
      <h1 data-i18n="NS.h1">Título da página</h1>
    </div></section>
    <section class="content"><div class="wrap">
      <!-- real extracted content, each text node wrapped with data-i18n -->
      <p data-i18n="NS.p1">…</p>
    </div></section>
  </main>
  <footer id="site-footer"></footer>
  <script src="assets/js/site.js"></script>
</body>
</html>
```

- [ ] **Step C: Add the `NS` namespace to `assets/i18n/pt.json`** with one entry per `data-i18n` key on the page, using the verbatim extracted PT text. If a route's content cannot be retrieved, set the value to a clearly marked placeholder, e.g. `"[Conteúdo a confirmar — extrair de ceseg.org/<rota>]"`, and list it in Task 8's pending notes. Never invent content.

- [ ] **Step D: Verify**

```bash
python3 -m http.server 8000 >/dev/null 2>&1 &  SRV=$!
sleep 1
curl -s http://localhost:8000/<file>.html | grep -q 'data-page="FILENAME"' && echo "page OK"
curl -s http://localhost:8000/assets/i18n/pt.json | python3 -c "import json,sys;json.load(sys.stdin);print('pt.json valid')"
kill $SRV
```
Expected: `page OK`, `pt.json valid`. Spot-check one page per group in the browser (dropdown active state correct, content readable).

- [ ] **Step E: Commit** `git add <file>.html assets/i18n/pt.json && git commit -m "feat: add <route> page (PT)"`

**Build in this order (one commit each):**
1. `organizacao.html` (NS=`org`) · 2. `comissoes.html` (`comissoes`) · 3. `conferencistas.html` (`conferencistas`) · 4. `grupos.html` (`grupos`) · 5. `instituto.html` (`instituto`) · 6. `sbseg.html` (`sbseg`) · 7. `anais.html` (`anais`) · 8. `minicursos.html` (`minicursos`) · 9. `wise.html` (`wise`) · 10. `homenageados.html` (`homenageados`) · 11. `publicacoes.html` (`publicacoes`) · 12. `referenciais.html` (`referenciais`) · 13. `onde-publicar.html` (`ondepublicar`) · 14. `documentos.html` (`documentos`) · 15. `atas.html` (`atas`) · 16. `regimentos.html` (`regimentos`) · 17. `portarias.html` (`portarias`).

---

## Task 6: Cross-link verification (no broken internal links)

**Files:** none (verification only)

- [ ] **Step 1: Check every internal href resolves to a file**

```bash
python3 - <<'PY'
import re,os,glob,sys
files=set(os.path.basename(p) for p in glob.glob('*.html'))
bad=[]
for p in glob.glob('*.html'):
    for h in re.findall(r'href="([^"#:]+\.html)[^"]*"', open(p,encoding='utf-8').read()):
        if os.path.basename(h) not in files: bad.append((p,h))
# also scan nav model in site.js
for h in re.findall(r"href:'([^']+\.html)'", open('assets/js/site.js',encoding='utf-8').read()):
    if h not in files: bad.append(('site.js',h))
print('BROKEN:',bad) if bad else print('All internal links resolve OK')
sys.exit(1 if bad else 0)
PY
```
Expected: `All internal links resolve OK`.

- [ ] **Step 2: Commit** (only if fixes were needed) `git commit -am "fix: resolve broken internal links"`

---

## Task 7: EN + ES dictionaries

**Files:**
- Create: `assets/i18n/en.json`, `assets/i18n/es.json`

- [ ] **Step 1: Generate `en.json`** with the **same key structure** as the final `pt.json`. Translate each value to English. For long/technical passages where a faithful translation isn't certain, copy the PT value and prefix it with `⚠ ` so it's visible as pending review (the engine still shows it). Validate:

```bash
python3 -c "import json;a=json.load(open('assets/i18n/pt.json'));b=json.load(open('assets/i18n/en.json'));
def keys(d,p=''):
 import itertools;return set(itertools.chain.from_iterable((keys(v,p+k+'.') if isinstance(v,dict) else [p+k]) for k,v in d.items()))
print('MISSING in en:',keys(a)-keys(b) or 'none')"
```
Expected: `MISSING in en: none`.

- [ ] **Step 2: Generate `es.json`** the same way (Spanish), same validation (`es` instead of `en`). Expected: `MISSING in es: none`.

- [ ] **Step 3: Browser check** — load the site, click EN then ES, confirm nav/footer/home switch language and `<html lang>` updates. Confirm a page with `⚠` markers shows them (acceptable; tracked in Task 8).

- [ ] **Step 4: Commit** `git add assets/i18n/en.json assets/i18n/es.json && git commit -m "feat: add EN and ES translation dictionaries"`

---

## Task 8: README, pending-content notes, a11y/responsive pass

**Files:**
- Modify: `README.md`
- Create: `docs/CONTENT-PENDING.md` (only if any placeholders remain)

- [ ] **Step 1: Write `README.md`** documenting: what the site is, structure, how to preview (`python3 -m http.server`), how to edit content (i18n JSON keys), how languages work, and that it deploys via GitHub Pages on `main`.

- [ ] **Step 2: If any `[Conteúdo a confirmar…]` or `⚠` markers remain**, list them in `docs/CONTENT-PENDING.md` with route + key so the user can fill them later.

- [ ] **Step 3: Responsive + a11y spot-check** at 375px and 1280px widths in the browser: header collapses to hamburger, dropdowns reachable, contrast OK, focus visible, every page has one `<h1>`. Fix CSS issues in `styles.css` if found.

- [ ] **Step 4: Commit** `git add -A && git commit -m "docs: add README and pending-content notes; a11y/responsive polish"`

---

## Task 9: Publish to GitHub Pages (`main`)

**Files:** none (git + GitHub)

- [ ] **Step 1: Final local verification** — run the Task 6 link check and the Task 7 key checks once more; serve and click through all top-level pages + language switch.

- [ ] **Step 2: Integrate to `main`.** Use the **superpowers:finishing-a-development-branch** skill to choose merge vs PR. Default: merge `redesign` → `main` (this is a personal Pages repo; `main` is the published branch).

```bash
git checkout main
git merge --no-ff redesign -m "feat: CESeg redesign — Academic Clean static site (PT/EN/ES)"
```

- [ ] **Step 3: Confirm GitHub Pages settings** serve from `main` / root. Push and verify `https://ceseg-sbc.github.io` renders the new home. (Ask the user to confirm Pages is enabled on `main` if the URL 404s.)

---

## Self-review (completed)

- **Spec coverage:** product decisions §1 → Tasks 1–9; visual identity §2 → Task 1 CSS; page structure §3 → route table + Tasks 4–5; shared components §4 → Tasks 2–3; i18n §5 → Tasks 3,7; content extraction §6 → Steps in Tasks 4–5 + Task 8 pending notes; home order §7 → Task 4; a11y §8 → Task 8; publish §9 → Task 9. No statistics counters anywhere. ✓
- **Placeholder scan:** content placeholders are intentional and gated (marked + tracked in Task 8), with explicit extraction commands — not plan-step placeholders. ✓
- **Type/name consistency:** `renderHeader/renderFooter`, `NAV` keys, `data-page`, `data-i18n`, `data-i18n-attr`, i18n namespaces, and filenames are consistent across Tasks 2–7. ✓
```
