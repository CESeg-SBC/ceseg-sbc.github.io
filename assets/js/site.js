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
