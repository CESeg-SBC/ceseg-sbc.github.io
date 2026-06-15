# CESeg — site institucional

Site da **Comissão Especial de Cibersegurança (CESeg)** da Sociedade Brasileira de
Computação (SBC), publicado via GitHub Pages em **https://ceseg-sbc.github.io**.

Site estático puro (HTML/CSS/JS), multipágina, sem build e sem dependências.
Direção visual **"Academic Clean"**: fundo claro, azul-marinho institucional,
títulos com serifa, muito espaço em branco. Suporte a três idiomas: **PT (padrão), EN, ES**.

## Estrutura

```
/
├── index.html              # Home (escrita à mão)
├── *.html                  # 18 páginas internas (geradas por scripts/gen_pages.py)
├── assets/
│   ├── css/styles.css      # tokens de design + componentes
│   ├── js/site.js          # header/footer compartilhados + menu mobile + i18n
│   └── i18n/{pt,en,es}.json # dicionários de tradução
├── .nojekyll               # serve os arquivos sem processamento Jekyll
├── .github/workflows/static.yml  # deploy no GitHub Pages via Actions
└── scripts/gen_pages.py    # gerador one-off das páginas internas
```

O **header e o footer não são duplicados** em cada arquivo: `assets/js/site.js`
os renderiza em tempo de execução nos contêineres `#site-header` e `#site-footer`,
mantendo uma única fonte de navegação.

## Pré-visualizar localmente

```bash
python3 -m http.server 8000
# abra http://localhost:8000
```

Um servidor é necessário (em vez de abrir o arquivo direto) porque o i18n usa
`fetch()` para carregar os JSON, o que não funciona com o protocolo `file://`.

## Editar conteúdo

Todo o texto visível é traduzível por **chaves `data-i18n`** no HTML, resolvidas
a partir de `assets/i18n/<lang>.json`. Para alterar um texto, edite o valor da
chave correspondente **nos três idiomas** (`pt.json`, `en.json`, `es.json`),
mantendo a mesma estrutura de chaves.

- Idioma padrão: **PT**. A escolha é persistida em `localStorage`, respeita
  `?lang=en|es` na URL e, na primeira visita, o idioma do navegador.
- Páginas com o selo **"Conteúdo a confirmar"** ainda não têm o conteúdo oficial
  extraído (o site original `ceseg.org` é renderizado por JavaScript e não pôde
  ser transcrito automaticamente). Veja `docs/CONTENT-PENDING.md`.

### Regenerar páginas internas

Após editar a lista/estrutura em `scripts/gen_pages.py`:

```bash
python3 scripts/gen_pages.py
```

A home (`index.html`) é mantida à mão e não é gerada.

## Publicação

O deploy é feito automaticamente pelo workflow **`.github/workflows/static.yml`**
a cada push na branch `main` (ou manualmente em Actions → "Run workflow").

> **Configuração necessária (uma vez):** em **Settings → Pages → Build and
> deployment → Source**, selecione **GitHub Actions**.
