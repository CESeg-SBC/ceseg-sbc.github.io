#!/usr/bin/env python3
"""Generate minicursos.html from scripts/minicursos_data.json.

Builds one rich card per SBSeg edition with: cover image, book DOI, keyword
chips and the full chapter list (title, authors, chapter DOI + PDF links).
A client-side search box (initMiniList in site.js) filters cards by any text.
"""
import json, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.load(open(ROOT / "scripts" / "minicursos_data.json", encoding="utf-8"))


def esc(s):
    return html.escape(s or "", quote=True)


def fold(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s or '')
                   if unicodedata.category(c) != 'Mn').lower()


def card(e):
    kw = "".join(f'<span class="mini-kw">{esc(k)}</span>' for k in e["keywords"])
    chapters = []
    for c in e["chapters"]:
        num = f'{c["num"]}. ' if c.get("num") else ''
        links = []
        if c.get("doi"):
            links.append(f'<a href="{esc(c["doi"])}" target="_blank" rel="noopener">DOI</a>')
        if c.get("pdf"):
            links.append(f'<a href="{esc(c["pdf"])}" target="_blank" rel="noopener">PDF ↗</a>')
        linkhtml = f'<span class="mini-ch-links">{" · ".join(links)}</span>' if links else ''
        chapters.append(
            '<li class="mini-ch">'
            f'<span class="mini-ch-title">{esc(num)}{esc(c["title"])}</span>'
            f'<span class="mini-ch-authors">{esc(c["authors"])}</span>'
            f'{linkhtml}</li>')
    chapters_html = "\n            ".join(chapters)

    hay_parts = [e["edition"], str(e["year"]), e["title"]] + e["keywords"]
    for c in e["chapters"]:
        hay_parts += [c["title"], c["authors"]]
    hay = esc(fold(" ".join(hay_parts)))

    cover = f'<img class="mini-cover" src="{esc(e["cover"])}" alt="Capa — {esc(e["edition"])} SBSeg {e["year"]}" loading="lazy">' if e.get("cover") else ''
    doi_html = (f'<a class="mini-doi" href="https://doi.org/{esc(e["doi"])}" '
                f'target="_blank" rel="noopener">doi.org/{esc(e["doi"])}</a>') if e.get("doi") else ''
    kw_block = (f'<div class="mini-kws"><span class="mini-lbl" data-i18n="minicursos.kwLabel">Palavras-chave</span>{kw}</div>') if kw else ''

    return f'''        <article class="mini-card" id="sbseg-{e["year"]}" data-hay="{hay}">
          <a class="mini-cover-link" href="{esc(e["url"])}" target="_blank" rel="noopener">{cover}</a>
          <div class="mini-body">
            <div class="mini-head">
              <span class="ebook-ed">{esc(e["edition"])} SBSeg · {e["year"]}</span>
              <h3>{esc(e["title"])}</h3>
              {doi_html}
            </div>
            {kw_block}
            <div class="mini-ch-wrap">
              <span class="mini-lbl" data-i18n="minicursos.chaptersLabel">Capítulos</span>
              <ol class="mini-chapters">
            {chapters_html}
              </ol>
            </div>
            <a class="mini-ebook-link" href="{esc(e["url"])}" target="_blank" rel="noopener" data-i18n="minicursos.ebookOpen">Abrir ebook no SBC OpenLib ↗</a>
          </div>
        </article>'''


cards_html = "\n".join(card(e) for e in DATA)

PAGE = f'''<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title data-i18n="minicursos.title">CESeg</title>
  <meta name="description" data-i18n="minicursos.desc" data-i18n-attr="content" content="">
  <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body data-page="minicursos">
  <header id="site-header"></header>
  <main>
    <section class="page-head"><div class="wrap">
      <div class="eyebrow" data-i18n="minicursos.eyebrow"></div>
      <h1 data-i18n="minicursos.h1"></h1>
    </div></section>
    <section class="content"><div class="wrap">
      <p class="lead" data-i18n="minicursos.intro"></p>
      <p data-i18n="minicursos.solText">Os minicursos do SBSeg são publicados como capítulos de livro e estão disponíveis na Biblioteca Digital da SBC (SOL).</p>
      <p><a class="btn btn-primary" href="https://sol.sbc.org.br/livros/index.php/sbc/catalog/category/seginfo" target="_blank" rel="noopener" data-i18n="minicursos.solCta">Minicursos no SOL →</a></p>

      <h2 class="ebook-title" data-i18n="minicursos.ebooksTitle">Ebooks por edição</h2>
      <p data-i18n="minicursos.ebooksText">Os minicursos apresentados em cada edição do SBSeg foram compilados e publicados em ebook no catálogo da SBC OpenLib. Acesse o ebook de cada edição:</p>

      <div class="mini-search">
        <input type="search" id="miniSearch" data-i18n="minicursos.searchPlaceholder" data-i18n-attr="placeholder"
               placeholder="Buscar por edição, título, autor ou palavra-chave…" aria-label="Buscar minicursos">
        <p class="mini-count"><span id="miniVisible">{len(DATA)}</span> <span data-i18n="minicursos.editionsLabel">edições</span></p>
      </div>
      <p id="miniNoResults" class="muted" hidden data-i18n="minicursos.noResults">Nenhum resultado encontrado.</p>

      <div id="miniList" class="mini-list">
{cards_html}
      </div>

      <p class="source-note"><span data-i18n="common.sourceNote">Conteúdo da página oficial</span>
        <a href="https://www.ceseg.org/mini-cursos" target="_blank" rel="noopener">ceseg.org/mini-cursos</a>.</p>
    </div></section>
  </main>
  <footer id="site-footer"></footer>
  <script src="assets/js/site.js"></script>
</body>
</html>
'''

out = ROOT / "minicursos.html"
out.write_text(PAGE, encoding="utf-8")
print("Wrote", out, "with", len(DATA), "editions")
