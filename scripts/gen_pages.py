#!/usr/bin/env python3
"""Generate the inner CESeg content pages (static HTML) from a small spec.

Output is committed static HTML — this is a one-off maintenance generator,
NOT a build step that runs when the site is served. Re-run after editing the
PAGES spec below. The home page (index.html) is hand-authored, not generated.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# filename (no ext) -> (i18n namespace, original ceseg.org route, extra-content key)
PAGES = [
    ("lista-de-discussao", "lista", "/lista-de-discucao", None),
    ("organizacao",        "org",   "/organizacao",       "org"),
    ("comissoes",          "comissoes", "/comiss%C3%B5es", None),
    ("conferencistas",     "conferencistas", "/conferencistas", None),
    ("grupos",             "grupos", "/grupos",            None),
    ("instituto",          "instituto", "/instituto",      None),
    ("sbseg",              "sbseg", "/sbseg",              "sbseg"),
    ("anais",              "anais", "/anais-trilha-principal", None),
    ("minicursos",         "minicursos", "/mini-cursos",   None),
    ("wise",               "wise",  "/wise",               None),
    ("homenageados",       "homenageados", "/homenageados", None),
    ("publicacoes",        "publicacoes", "/publicacoes",  None),
    ("referenciais",       "referenciais", "/referenciais", None),
    ("onde-publicar",      "ondepublicar", "/onde-publicar", None),
    ("documentos",         "documentos", "/documentos",    None),
    ("atas",               "atas",  "/atas",               None),
    ("regimentos",         "regimentos", "/regimentos",    None),
    ("portarias",          "portarias", "/portarias",      None),
]

EXTRA = {
    "org": """
      <h2 data-i18n="org.coordH2">Coordenação 2024–2026</h2>
      <ul>
        <li data-i18n="org.coordCoord">Coordenador: Marcos Simplício (USP)</li>
        <li data-i18n="org.coordVice">Vice-coordenador: Diego Kreutz (UNIPAMPA)</li>
      </ul>
      <h2 data-i18n="org.histH2">Coordenações anteriores</h2>
      <p data-i18n="org.histText">Desde 2004, a coordenação passou por diversos pesquisadores da comunidade.</p>""",
    "sbseg": """
      <h2 data-i18n="sbseg.edH2">SBSeg 2025 — Foz do Iguaçu</h2>
      <p data-i18n="sbseg.edText">A edição de 2025 acontece em Foz do Iguaçu.</p>
      <p><a class="btn btn-primary" href="https://sbseg2025.ppgia.pucpr.br/" target="_blank" rel="noopener">sbseg2025.ppgia.pucpr.br →</a></p>""",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title data-i18n="{ns}.title">CESeg</title>
  <meta name="description" data-i18n="{ns}.desc" data-i18n-attr="content" content="">
  <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body data-page="{page}">
  <header id="site-header"></header>
  <main>
    <section class="page-head"><div class="wrap">
      <div class="eyebrow" data-i18n="{ns}.eyebrow"></div>
      <h1 data-i18n="{ns}.h1"></h1>
    </div></section>
    <section class="content"><div class="wrap">
      <p class="lead" data-i18n="{ns}.intro"></p>{extra}
      <p style="margin-top:1.6rem"><span class="pending" data-i18n="common.pending">Conteúdo a confirmar</span></p>
      <p><span data-i18n="common.pendingNote">Esta seção será preenchida com o conteúdo oficial. Consulte a página original em</span>
        <a href="https://www.ceseg.org{route}" target="_blank" rel="noopener" data-i18n="common.originalLink">ceseg.org</a>.</p>
    </div></section>
  </main>
  <footer id="site-footer"></footer>
  <script src="assets/js/site.js"></script>
</body>
</html>
"""

def main():
    for page, ns, route, extra_key in PAGES:
        extra = EXTRA.get(extra_key, "")
        html = TEMPLATE.format(ns=ns, page=page, route=route, extra=extra)
        path = os.path.join(ROOT, f"{page}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"wrote {page}.html (ns={ns})")

if __name__ == "__main__":
    main()
