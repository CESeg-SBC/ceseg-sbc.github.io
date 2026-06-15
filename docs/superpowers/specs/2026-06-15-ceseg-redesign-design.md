# CESeg — Redesenho do site (Academic Clean)

**Data:** 2026-06-15
**Repositório:** `ceseg-sbc.github.io` (GitHub Pages, servido em `https://ceseg-sbc.github.io`)
**Objetivo:** Recriar o site da Comissão Especial de Cibersegurança (CESeg, da SBC) — hoje em `ceseg.org` — com um design limpo, moderno e institucional, mantendo todo o conteúdo (clone fiel completo).

---

## 1. Decisões de produto

| Tema | Decisão |
|------|---------|
| Escopo de conteúdo | **Clone fiel completo** — todas as seções do `ceseg.org`, com conteúdo real extraído do site original. |
| Arquitetura | **HTML/CSS/JS estático puro**, multi-página. Sem build, sem dependências. Publicação direta no GitHub Pages. |
| Direção visual | **Academic Clean** — fundo claro, muito espaço em branco, azul-marinho institucional (`#1e3a8a`), títulos com serifa, corpo sem serifa. |
| Marca | **Wordmark tipográfico "CESeg"** em CSS (sem arquivo de imagem). Trocável por um logo depois. |
| Idiomas | **PT (padrão) + EN + ES**, com alternador de idioma. PT é a fonte de verdade do conteúdo. |
| Estatísticas | **Não usar contadores numéricos** (17 grupos, 22 simpósios, 320+ publicações) — envelhecem e viram passivo de manutenção. Só "desde 2004" como fato histórico. |

---

## 2. Identidade visual

**Paleta**
- Primária (navy): `#1e3a8a`
- Primária escura (footer/headers): `#0f172a`
- Texto principal: `#0f172a` · Texto secundário: `#475569` · Texto terciário: `#64748b`
- Fundo: `#ffffff` · Fundo alternado: `#f8fafc` · Bordas: `#e2e8f0`
- Acento de hover/links: `#2563eb`

**Tipografia**
- Títulos (h1–h3): família com serifa — Georgia como fallback seguro, ou uma serifa web (ex.: "Lora" via Google Fonts) a confirmar na implementação.
- Corpo e UI: `system-ui` / sans-serif nativa.
- Rótulos de seção: caixa-alta, `letter-spacing` amplo, 11–12px, cor navy.

**Tokens em CSS**: definidos como variáveis `:root` (`--navy`, `--ink`, `--muted`, `--bg`, `--bg-alt`, `--border`, etc.) em `assets/css/styles.css`. Responsivo (mobile-first), com breakpoint principal ~768px e menu hambúrguer no mobile.

---

## 3. Estrutura de páginas (multi-página)

Espelha a navegação do site original. Uma página HTML por seção, na raiz do repositório:

| Arquivo | Seção | Conteúdo |
|---------|-------|----------|
| `index.html` | **Home** | Hero, sobre, destaque SBSeg, cards (Instituto + Grupos), comunidade, parceiros. |
| `organizacao.html` | **Organização** | Comitês, coordenação e palestrantes. |
| `grupos.html` | **Grupos** | Grupos de pesquisa + Instituto Nacional de Segurança Cibernética (INCT/CNPq). |
| `sbseg.html` | **SBSeg** | Anais do simpósio, minicursos, trilha WISE, edições, SBSeg 2025 (Foz do Iguaçu). |
| `homenagens.html` | **Homenagens** | Homenageados e premiações. |
| `publicacoes.html` | **Publicações** | Referências e veículos de publicação. |
| `documentos.html` | **Documentos** | Atas, estatuto, portarias. |

**Estrutura de pastas**
```
/ (raiz)
├── index.html
├── organizacao.html
├── grupos.html
├── sbseg.html
├── homenagens.html
├── publicacoes.html
├── documentos.html
├── assets/
│   ├── css/styles.css
│   ├── js/site.js            # header/footer + i18n + menu mobile
│   └── i18n/
│       ├── pt.json
│       ├── en.json
│       └── es.json
├── .nojekyll                 # serve arquivos como estão, sem processamento Jekyll
└── README.md
```

---

## 4. Componentes compartilhados (DRY sem build)

Como o site é estático e **já depende de JS para a troca de idioma**, header e footer são **renderizados por `assets/js/site.js`** em contêineres-placeholder (`<header id="site-header">`, `<footer id="site-footer">`) presentes em cada página. Isso mantém **uma única fonte** para navegação e rodapé, evitando duplicação em 7 arquivos.

- **Header**: wordmark "CESeg", navegação (Organização, Grupos, SBSeg, Homenagens, Publicações, Documentos), alternador de idioma (PT · EN · ES) e menu hambúrguer no mobile. Marca o item ativo conforme a página atual.
- **Footer**: bloco escuro (`#0f172a`) com descrição do CESeg, contato (e-mail `ceseg.sbc@gmail.com`, telefone `(51) 3308-6835`, endereço `Av. Bento Gonçalves, 9500 — Porto Alegre/RS`, CNPJ `29.532.264/0001-78`) e links de navegação.

**Trade-off aceito:** a navegação depende de JS habilitado. Para um site institucional moderno é aceitável; o conteúdo principal de cada página permanece em HTML estático (bom para leitura e indexação).

---

## 5. Internacionalização (PT / EN / ES)

**Abordagem:** i18n por **atributos `data-i18n`** + **dicionários JSON** por idioma, com um único conjunto de páginas.

- Cada texto traduzível recebe `data-i18n="chave.hierarquica"`; `site.js` substitui o conteúdo a partir de `assets/i18n/<lang>.json`.
- **Idioma padrão:** PT. Seleção persistida em `localStorage`; respeita `?lang=en|es` na URL e, na primeira visita, `navigator.language` (caindo para PT).
- Atualiza `<html lang>` e `<title>`/meta conforme o idioma.
- **Fonte de verdade:** PT, com o conteúdo real do `ceseg.org`. EN e ES são traduzidos onde for direto; trechos longos/técnicos sem tradução confiável ficam **marcados como pendência de revisão** (exibindo PT como fallback) — nunca texto inventado.

---

## 6. Extração de conteúdo

Na implementação, o conteúdo real será coletado de `ceseg.org` (e subpáginas correspondentes a cada item de navegação) e transcrito para os dicionários/HTML. Onde o conteúdo não puder ser recuperado com fidelidade, marca-se como **pendência** (placeholder explícito) em vez de inventar — para você preencher depois. Logos de parceiros: reaproveitados do original quando baixáveis; caso contrário, placeholders.

---

## 7. Home — ordem das seções (validada no companion)

1. Header (nav + alternador de idioma)
2. Hero — rótulo "SBC · desde 2004", título com serifa, subtítulo, 2 CTAs (SBSeg 2025 / Sobre)
3. Sobre — o que é o CESeg
4. Destaque **SBSeg 2025 — Foz do Iguaçu** (bloco navy)
5. Dois cards — Instituto Nacional de Segurança Cibernética + Grupos de Pesquisa
6. Comunidade — Computação Brasil, auditoria do sistema eleitoral, workshops/carreira
7. Parceiros — faixa de logos institucionais
8. Footer

---

## 8. Acessibilidade e qualidade

- HTML semântico (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`), landmarks e `aria-label` na navegação e no alternador de idioma.
- Contraste AA (navy sobre branco; branco sobre navy/`#0f172a`).
- Navegável por teclado; foco visível; menu mobile acessível.
- Meta tags básicas de SEO e Open Graph por página (título/descrição traduzíveis).
- `.nojekyll` na raiz para o GitHub Pages servir os arquivos sem processamento.

---

## 9. Publicação

- Branch `main` deste repositório, servido pelo GitHub Pages em `https://ceseg-sbc.github.io`.
- Sem CNAME/custom domain nesta etapa (publicação no domínio padrão do Pages).
- `index.html` atual (placeholder) é substituído pela nova home.

---

## 10. Fora de escopo (YAGNI)

- Backend, formulários dinâmicos, busca, CMS.
- Contadores de estatística.
- Custom domain / migração de DNS do `ceseg.org`.
- Tradução profissional revisada de EN/ES (entregue como melhor esforço + pendências marcadas).
