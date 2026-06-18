#!/usr/bin/env python3
"""Fetch SBSeg minicursos ebook metadata from the SBC OpenLib catalog.

For each edition's ebook it extracts: title, DOI, cover image, keywords and the
chapter list (number, title, authors, chapter DOI). Pages are cached locally so
re-runs are cheap; cover images are downloaded to assets/img/minicursos/.

Output: scripts/minicursos_data.json  (consumed by gen_minicursos.py)
"""
import json, os, re, html, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "minicursos"
IMGDIR = ROOT / "assets" / "img" / "minicursos"
CACHE.mkdir(parents=True, exist_ok=True)
IMGDIR.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")

# edition, year, catalog URL — order: newest first
BOOKS = [
    ("XXV",   2025, "https://books-sol.sbc.org.br/index.php/sbc/catalog/book/178"),
    ("XXIV",  2024, "https://books-sol.sbc.org.br/index.php/sbc/catalog/book/151"),
    ("XXIII", 2023, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/135"),
    ("XXII",  2022, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/107"),
    ("XXI",   2021, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/71"),
    ("XX",    2020, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/82"),
    ("XIX",   2019, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/85"),
    ("XVIII", 2018, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/22"),
    ("XVII",  2017, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/84"),
    ("XVI",   2016, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/89"),
    ("XV",    2015, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/90"),
    ("XIV",   2014, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/91"),
    ("XIII",  2013, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/92"),
    ("XII",   2012, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/94"),
    ("XI",    2011, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/95"),
    ("X",     2010, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/98"),
    ("IX",    2009, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/99"),
    ("VIII",  2008, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/96"),
    ("VII",   2007, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/100"),
    ("VI",    2006, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/101"),
    ("V",     2005, "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/97"),
]


def fetch(url, binary=False):
    key = re.sub(r'[^A-Za-z0-9]', '_', url)
    path = CACHE / (key + (".bin" if binary else ".html"))
    if path.exists():
        return path.read_bytes() if binary else path.read_text(encoding="utf-8", errors="ignore")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = urllib.request.urlopen(req, timeout=60).read()
    path.write_bytes(data)
    return data if binary else data.decode("utf-8", errors="ignore")


def metas(t, name):
    return re.findall(r'<meta\s+name="%s"[^>]*content="([^"]*)"' % re.escape(name), t)


def meta_lang(t, name, lang):
    out = []
    for m in re.finditer(r'<meta\s+name="%s"([^>]*)>' % re.escape(name), t):
        attrs = m.group(1)
        if ('xml:lang="%s"' % lang) in attrs:
            c = re.search(r'content="([^"]*)"', attrs)
            if c:
                out.append(html.unescape(c.group(1)))
    return out


def parse_chapters(t):
    i = t.find('item chapters')
    if i < 0:
        return []
    seg = t[i:t.find('class="item', i + 10) if t.find('class="item', i + 10) > 0 else i + 60000]
    chapters = []
    for li in re.findall(r'<li>(.*?)</li>', seg, re.S):
        tm = re.search(r'<div class="title">\s*(.*?)\s*</div>', li, re.S)
        if not tm:
            continue
        title = html.unescape(re.sub(r'\s+', ' ', tm.group(1))).strip()
        num = None
        nm = re.match(r'^(\d+)\.\s*(.*)', title)
        if nm:
            num, title = nm.group(1), nm.group(2).strip()
        am = re.search(r'<div class="authors">\s*(.*?)\s*</div>', li, re.S)
        authors = html.unescape(re.sub(r'\s+', ' ', am.group(1))).strip() if am else ""
        dm = re.search(r'<div class="doi">DOI:\s*<a href="([^"]+)"', li)
        doi = dm.group(1) if dm else ""
        vm = re.search(r'href="([^"]+)"\s+class="cmp_download_link"', li)
        view = vm.group(1) if vm else ""
        chapters.append({"num": num, "title": title, "authors": authors,
                         "doi": doi, "pdf": view})
    return chapters


def download_cover(t, book_url, book_id):
    m = re.search(r'(https?://[^"\s]*submission_\d+_\d+_coverImage[^"\s]+)', t)
    if not m:
        # relative form
        m = re.search(r'(/[^"\s]*submission_\d+_\d+_coverImage[^"\s]+)', t)
        if not m:
            return ""
    thumb = m.group(1)
    if thumb.startswith('/'):
        base = re.match(r'(https?://[^/]+)', book_url).group(1)
        thumb = base + thumb
    ext = os.path.splitext(thumb.split('?')[0])[1] or ".png"
    out = IMGDIR / ("book-%s%s" % (book_id, ext))
    # prefer full-size (strip trailing _t before extension)
    full = re.sub(r'_t(\.[a-zA-Z]+)$', r'\1', thumb)
    for cand in (full, thumb):
        try:
            data = fetch(cand, binary=True)
            out.write_bytes(data)
            return "assets/img/minicursos/" + out.name
        except Exception:
            continue
    return ""


def main():
    result = []
    for edition, year, url in BOOKS:
        book_id = url.rstrip('/').split('/')[-1]
        print("Fetching", edition, year, url)
        t = fetch(url)
        title = (metas(t, "DC.Title") or [""])[0]
        doi = (metas(t, "DC.Identifier.DOI") or [""])[0]
        desc = metas(t, "DC.Description")
        kw = meta_lang(t, "citation_keywords", "pt") or metas(t, "DC.Subject")
        # DC.Subject lists pt then en duplicates; keep first half if no lang keywords
        cover = download_cover(t, url, book_id)
        chapters = parse_chapters(t)
        result.append({
            "edition": edition, "year": year, "book_id": book_id, "url": url,
            "title": html.unescape(title), "doi": doi,
            "description": html.unescape(desc[0]) if desc else "",
            "keywords": kw, "cover": cover, "chapters": chapters,
        })
        print("   ->", len(chapters), "chapters,", len(kw), "keywords, cover:", bool(cover))
    out = ROOT / "scripts" / "minicursos_data.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", out)


if __name__ == "__main__":
    main()
