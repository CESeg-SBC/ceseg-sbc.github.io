#!/usr/bin/env python3
"""
Fetch SBSeg publications from the SBC Open Library (SOL) and generate two
large static HTML pages for the CESeg site:

  - anais-trilha-principal.html : every Main Track paper, grouped by edition
  - anais-estendidos.html       : every Extended Annals paper, grouped by
                                  edition and sub-event

Data source: https://sol.sbc.org.br/index.php/sbseg/issue/archive (OJS)

The script is idempotent and caches fetched pages under .cache/sbseg so it can
be re-run cheaply when SOL adds a new edition. Run from the repo root:

    python3 scripts/fetch_sbseg.py            # fetch (cached) + generate
    python3 scripts/fetch_sbseg.py --refresh  # ignore cache, re-fetch

Only the public table-of-contents markup is parsed (title, authors, paper URL).
"""
import html
import json
import os
import re
import subprocess
import sys
import time

import keywords  # sibling module: title keyword mining + word-cloud rendering

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "sbseg")
DATA = os.path.join(ROOT, "scripts", "sbseg_data.json")
ARCHIVE = "https://sol.sbc.org.br/index.php/sbseg/issue/archive"
UA = "Mozilla/5.0 (compatible; CESeg-archive-builder; +https://ceseg-sbc.github.io)"

REFRESH = "--refresh" in sys.argv


# --------------------------------------------------------------------------- #
# Fetching (curl-backed, on-disk cache)                                        #
# --------------------------------------------------------------------------- #
def fetch(url):
    key = re.sub(r"[^A-Za-z0-9]+", "_", url) + ".html"
    path = os.path.join(CACHE, key)
    if not REFRESH and os.path.exists(path):
        return open(path, encoding="utf-8").read()
    os.makedirs(CACHE, exist_ok=True)
    print(f"  GET {url}", file=sys.stderr)
    out = subprocess.run(
        ["curl", "-sL", "--max-time", "60", "-A", UA, url],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(f"curl failed for {url}: {out.stderr}")
    html_text = out.stdout
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html_text)
    time.sleep(1.0)  # be polite to SOL
    return html_text


# --------------------------------------------------------------------------- #
# Parsing                                                                      #
# --------------------------------------------------------------------------- #
def clean(text):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text))).strip()


def parse_archive(html_text):
    """Return [{id, year, roman, label}] for the main-track issues, newest first."""
    issues = []
    pat = re.compile(
        r'<a[^>]+href="https://sol\.sbc\.org\.br/index\.php/sbseg/issue/view/(\d+)"[^>]*>(.*?)</a>',
        re.S,
    )
    seen = set()
    for m in pat.finditer(html_text):
        iid, label = m.group(1), clean(m.group(2))
        if not label or iid in seen:
            continue
        seen.add(iid)
        ym = re.match(r"(\d{4})\s*:", label)
        rm = re.search(r"Anais do\s+([IVXLCDM]+)\b", label)
        issues.append({
            "id": iid,
            "year": ym.group(1) if ym else "",
            "roman": rm.group(1) if rm else "",
            "label": label,
        })
    return issues


def parse_issue(html_text):
    """Parse an OJS issue ToC into [{section, papers:[{title, authors, url}]}]."""
    # Limit to the sections region to avoid sidebar/footer noise.
    start = html_text.find('class="sections"')
    region = html_text[start:] if start != -1 else html_text
    sections = []
    # Split on each section container; the wrapper is class="sections" (plural),
    # so an exact match on class="section" only catches the real section blocks.
    chunks = re.split(r'<div class="section">', region)
    for chunk in chunks[1:]:
        hm = re.search(r"<h2[^>]*>(.*?)</h2>", chunk, re.S)
        name = clean(hm.group(1)) if hm else ""
        papers = []
        for block in chunk.split("obj_article_summary")[1:]:
            tm = re.search(
                r'<div class="title">\s*<a\s+href="([^"]+)"[^>]*>(.*?)</a>',
                block, re.S,
            )
            if not tm:
                continue
            am = re.search(r'<div class="authors">(.*?)</div>', block, re.S)
            papers.append({
                "title": clean(tm.group(2)),
                "authors": clean(am.group(1)) if am else "",
                "url": tm.group(1).strip(),
            })
        if papers:
            sections.append({"section": name, "papers": papers})
    return sections


def find_estendido(html_text):
    """Return the Extended Annals issue URL referenced from a main issue, if any."""
    m = re.search(
        r'href="(https://sol\.sbc\.org\.br/index\.php/sbseg_estendido/issue/view/\d+)"',
        html_text,
    )
    return m.group(1) if m else None


def find_ebook(html_text):
    """Return the minicursos ebook URL announced on a main issue page, if any.

    SOL pages carry a paragraph like "Os minicursos apresentados no evento foram
    compilados e publicados em ebook ... catálogo de livros da SBC OpenLib".
    The host changed over time (sol.sbc.org.br/livros vs books-sol.sbc.org.br),
    so anchor on the stable wording, not on the host.
    """
    m = re.search(
        r"compilados e publicados em <em>ebook</em>.*?href=\"([^\"]+catalog/book/\d+)\"",
        html_text, re.S,
    )
    return m.group(1) if m else None


# --------------------------------------------------------------------------- #
# Scrape                                                                       #
# --------------------------------------------------------------------------- #
def scrape():
    print("Fetching archive...", file=sys.stderr)
    archive = parse_archive(fetch(ARCHIVE))
    main_track, estendido = [], []
    for issue in archive:
        print(f"Edition {issue['year']} ({issue['roman']}) — issue {issue['id']}",
              file=sys.stderr)
        page = fetch(f"https://sol.sbc.org.br/index.php/sbseg/issue/view/{issue['id']}")
        sections = parse_issue(page)
        entry = {**issue, "url": f"https://sol.sbc.org.br/index.php/sbseg/issue/view/{issue['id']}",
                 "sections": sections}
        ebook = find_ebook(page)
        if ebook:
            entry["ebook"] = ebook
        main_track.append(entry)
        ext_url = find_estendido(page)
        if ext_url:
            ext_page = fetch(ext_url)
            ext_sections = parse_issue(ext_page)
            if ext_sections:
                estendido.append({
                    "year": issue["year"], "roman": issue["roman"],
                    "url": ext_url, "sections": ext_sections,
                })
    return {"main_track": main_track, "estendido": estendido}


# --------------------------------------------------------------------------- #
# HTML generation                                                              #
# --------------------------------------------------------------------------- #
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def paper_html(p, year):
    cite = f"{p['authors']}. {p['title']}. SBSeg {year}." if p["authors"] else \
           f"{p['title']}. SBSeg {year}."
    kws = p.get("keywords", [])
    kw_attr = esc(", ".join(kws))
    chips = "".join(
        f'<button type="button" class="pub-kw" data-kw="{esc(k)}">{esc(k)}</button>'
        for k in kws
    )
    kw_block = (
        f'        <div class="pub-paper-keywords">{chips}</div>\n' if chips else ""
    )
    return (
        '      <li class="pub-paper" '
        f'data-title="{esc(p["title"].lower())}" '
        f'data-authors="{esc(p["authors"].lower())}" '
        f'data-keywords="{kw_attr}" '
        f'data-cite="{esc(cite)} {esc(p["url"])}">\n'
        f'        <a class="pub-paper-title" href="{esc(p["url"])}" target="_blank" rel="noopener">{esc(p["title"])}</a>\n'
        f'        <div class="pub-paper-authors">{esc(p["authors"])}</div>\n'
        f"{kw_block}"
        '        <button class="pub-cite" type="button" data-i18n-title="pubcommon.copyCite" title="Copiar citação" aria-label="Copiar citação">⧉ <span data-i18n="pubcommon.cite">citar</span></button>\n'
        "      </li>"
    )


def edition_html(year, roman, url, sections, anchor):
    n = sum(len(s["papers"]) for s in sections)
    title_roman = f"{roman} SBSeg" if roman else "SBSeg"
    parts = [
        f'  <section class="pub-edition" id="{anchor}" data-year="{year}">',
        '    <div class="pub-edition-head">',
        f'      <h2>{esc(title_roman)} <span class="pub-year">{year}</span></h2>',
        f'      <span class="pub-count">{n} <span data-i18n="pubcommon.papers">artigos</span></span>',
        f'      <a class="pub-sol" href="{esc(url)}" target="_blank" rel="noopener" data-i18n="pubcommon.solIssue">edição no SOL ↗</a>',
        "    </div>",
    ]
    for s in sections:
        if s["section"]:
            parts.append(f'    <h3 class="pub-section">{esc(s["section"])}</h3>')
        parts.append('    <ul class="pub-papers">')
        parts.extend(paper_html(p, year) for p in s["papers"])
        parts.append("    </ul>")
    parts.append("  </section>")
    return "\n".join(parts)


def toc_html(editions):
    items = []
    for e in editions:
        n = sum(len(s["papers"]) for s in e["sections"])
        label = f"{e['roman']} " if e["roman"] else ""
        items.append(
            f'    <li><a href="#{e["anchor"]}">{label}{e["year"]} '
            f'<span class="pub-toc-count">{n}</span></a></li>'
        )
    return "\n".join(items)


PAGE_TPL = """<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title data-i18n="{key}.title">CESeg</title>
  <meta name="description" data-i18n="{key}.desc" data-i18n-attr="content" content="{desc}">
  <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body data-page="{page}">
  <header id="site-header"></header>
  <main>
    <section class="page-head"><div class="wrap">
      <div class="eyebrow" data-i18n="{key}.eyebrow"></div>
      <h1 data-i18n="{key}.h1"></h1>
    </div></section>
    <section class="content"><div class="wrap pub-wrap">
      <p class="lead" data-i18n="{key}.intro"></p>
      <p data-i18n="{key}.note">{note}</p>

      <div class="pub-toolbar">
        <input type="search" class="pub-search" id="pubSearch"
               data-i18n-placeholder="pubcommon.searchPlaceholder"
               placeholder="Buscar por título, autor ou palavra-chave…" autocomplete="off">
        <span class="pub-total"><span id="pubVisible">{total}</span> / {total}
          <span data-i18n="pubcommon.papers">artigos</span></span>
      </div>

      <nav class="pub-toc" aria-label="Edições">
        <h2 class="pub-toc-title" data-i18n="pubcommon.editions">Edições</h2>
        <ul class="pub-toc-list">
{toc}
        </ul>
      </nav>

      <div class="pub-list" id="pubList">
{body}
      </div>

      <p class="pub-noresults" id="pubNoResults" hidden data-i18n="pubcommon.noResults">Nenhum artigo encontrado.</p>

      <section class="pub-cloud-section" aria-labelledby="pubCloudTitle">
        <h2 id="pubCloudTitle" class="pub-cloud-title" data-i18n="pubcommon.cloudTitle">Nuvem de palavras-chave</h2>
        <p class="pub-cloud-note" data-i18n="pubcommon.cloudNote">Palavras-chave extraídas automaticamente dos títulos dos artigos. Clique em um termo para filtrar a lista.</p>
{cloud}
      </section>

      <p class="source-note"><span data-i18n="pubcommon.sourcePrefix">Dados extraídos da Biblioteca Digital da SBC (SOL)</span>:
        <a href="{archive}" target="_blank" rel="noopener">{archive_label}</a>.
        <span data-i18n="pubcommon.updated">Atualizado em</span> {date}.</p>
    </div></section>
  </main>
  <footer id="site-footer"></footer>
  <script src="assets/js/site.js"></script>
</body>
</html>
"""


def page_keywords(editions):
    """All per-paper keyword lists across a set of editions (for a page cloud)."""
    return (p.get("keywords", [])
            for e in editions for s in e["sections"] for p in s["papers"])


def build_page(key, page, editions, note, archive_url, archive_label):
    total = sum(sum(len(s["papers"]) for s in e["sections"]) for e in editions)
    body = "\n".join(edition_html(e["year"], e["roman"], e["url"], e["sections"],
                                  e["anchor"]) for e in editions)
    counts = keywords.aggregate(page_keywords(editions))
    cloud = keywords.cloud_html(counts, cloud_id="pubCloud", limit=80, indent="        ")
    today = time.strftime("%d/%m/%Y")
    return PAGE_TPL.format(
        key=key, page=page, desc="", note=note, total=total,
        toc=toc_html(editions), body=body, cloud=cloud, date=today,
        archive=archive_url, archive_label=archive_label,
    )


# Front-matter ToC sections that are not citable papers.
SKIP_SECTIONS = {"abertura", "expediente", "apresentação", "apresentacao"}


def drop_frontmatter(data):
    for grp in ("main_track", "estendido"):
        for e in data[grp]:
            e["sections"] = [s for s in e["sections"]
                             if s["section"].strip().lower() not in SKIP_SECTIONS]
    return data


def main():
    if REFRESH or not os.path.exists(DATA):
        data = scrape()
        with open(DATA, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
    else:
        data = json.load(open(DATA, encoding="utf-8"))

    data = drop_frontmatter(data)

    # Mine five keywords per paper from titles, with a corpus-wide TF-IDF index
    # built over both tracks so weights (and the combined cloud) stay coherent.
    all_titles = [p["title"] for grp in ("main_track", "estendido")
                  for e in data[grp] for s in e["sections"] for p in s["papers"]]
    index = keywords.build_index(all_titles)
    for grp in ("main_track", "estendido"):
        for e in data[grp]:
            for s in e["sections"]:
                for p in s["papers"]:
                    p["keywords"] = keywords.keywords_for(p["title"], index)

    # Main track
    main_eds = [{**e, "anchor": f"sbseg-{e['year']}"} for e in data["main_track"]]
    main_html = build_page(
        "anaistp", "anais-trilha-principal", main_eds,
        "Todos os artigos da Trilha Principal do SBSeg, agrupados por edição. "
        "Use a busca para filtrar por título, autor ou palavra-chave.",
        ARCHIVE, "sol.sbc.org.br · SBSeg",
    )
    with open(os.path.join(ROOT, "anais-trilha-principal.html"), "w", encoding="utf-8") as fh:
        fh.write(main_html)

    # Extended annals
    ext_eds = [{**e, "anchor": f"est-{e['year']}"} for e in data["estendido"]]
    ext_html = build_page(
        "anaisest", "anais-estendidos", ext_eds,
        "Todos os artigos dos Anais Estendidos do SBSeg, agrupados por edição e "
        "sub-evento (workshops e trilhas). Use a busca para filtrar por título, "
        "autor ou palavra-chave.",
        "https://sol.sbc.org.br/index.php/sbseg_estendido/issue/archive",
        "sol.sbc.org.br · SBSeg Estendido",
    )
    with open(os.path.join(ROOT, "anais-estendidos.html"), "w", encoding="utf-8") as fh:
        fh.write(ext_html)

    # Combined/general keyword aggregate, consumed by gen_pages.py to render the
    # overall word cloud on publicacoes.html. Top 200 keeps the file small.
    combined = keywords.aggregate(
        p.get("keywords", []) for grp in ("main_track", "estendido")
        for e in data[grp] for s in e["sections"] for p in s["papers"]
    )
    combined_path = os.path.join(ROOT, "scripts", "keywords_combined.json")
    with open(combined_path, "w", encoding="utf-8") as fh:
        json.dump(
            {"generated": time.strftime("%d/%m/%Y"),
             "counts": keywords.top_counts(combined, 200)},
            fh, ensure_ascii=False, indent=1,
        )

    tp = sum(sum(len(s["papers"]) for s in e["sections"]) for e in main_eds)
    ex = sum(sum(len(s["papers"]) for s in e["sections"]) for e in ext_eds)
    print(f"\nMain track: {len(main_eds)} editions, {tp} papers", file=sys.stderr)
    print(f"Estendido:  {len(ext_eds)} editions, {ex} papers", file=sys.stderr)


if __name__ == "__main__":
    main()
