# Estado do conteúdo

Todo o conteúdo das páginas internas foi **transcrito de `ceseg.org`** (site Wix/JS)
e embutido no site estático em 2026-06. As páginas deixaram de exibir o selo
"Conteúdo a confirmar".

Texto traduzível (intros, títulos de seção, rótulos) vive em
`assets/i18n/{pt,en,es}.json` (paridade de chaves verificada: 198 chaves em cada).
Dados estáveis e neutros a idioma (nomes, instituições, datas, links de PDF, títulos
de periódicos) são embutidos diretamente no HTML por `scripts/gen_pages.py`.

## Conteúdo preenchido por página

| Página | Conteúdo |
|---|---|
| `organizacao.html` | Coordenação 2024–2026 + histórico de 10 mandatos (2004–2026) + comitê gestor 2026 |
| `comissoes.html` | Comissão de Educação e Comissão de Competições (membros + descrições) |
| `conferencistas.html` | Programa de Conferencistas Seniores (SBC, 2014); atuais e anteriores |
| `instituto.html` | INCT em Segurança Cibernética — rede de 19 instituições (UNICAMP à frente) |
| `sbseg.html` | Histórico + tabela das edições recentes (2023–2025) + ponteiro p/ SOL |
| `anais.html` | Ponteiro para os artigos no SOL (Biblioteca Digital da SBC) |
| `minicursos.html` | Ponteiro para os minicursos no SOL |
| `wise.html` | Descrição da trilha WISE |
| `homenageados.html` | 6 homenageados (2018–2025), com instituição e descrição |
| `publicacoes.html` | Visão geral + cards para Referenciais e Onde Publicar |
| `referenciais.html` | Referenciais de Formação em Cibersegurança + link no SOL |
| `onde-publicar.html` | 22 periódicos + 11 conferências |
| `documentos.html` | Cards para Atas, Regimentos e Portarias |
| `atas.html` | 22 atas (2005–2025) com links de PDF (2 sem link na origem) |
| `regimentos.html` | Regimento vigente de 2017 (PDF) |
| `portarias.html` | SBC Portaria nº 020/2021 (PDF) |
| `lista-de-discussao.html` | Objetivo da lista + como participar (UFRGS Mailman) |

## Única exceção — lista de grupos (`grupos.html`)

A relação dos grupos de pesquisa **não é servida no HTML** de `ceseg.org`: é renderizada
por um app Wix customizado (`appDefinitionId 14271d6f-…`, TPA `fullscreen_page`) que
carrega os registros de um datastore próprio via chamada assíncrona, sem API HTTP
pública trivial. A página `grupos.html` traz a introdução + um botão para a **lista viva
e sempre atualizada** em `https://www.ceseg.org/lista-grupos`. Isso também é a escolha de
produto correta: a lista é dinâmica e um snapshot estático envelheceria — mesma filosofia
adotada para as estatísticas numéricas (ver abaixo).

## Fatos históricos confirmados

- Criação da CESeg: **2004** (aprovada na diretoria da SBC em 01/08/2004).
- Contato: `ceseg.sbc@gmail.com` · (51) 3308-6835 · Av. Bento Gonçalves, 9500,
  Agronomia, Porto Alegre/RS, CEP 91501-970 · CNPJ 29.532.264/0001-78.

## Decisão de design

Estatísticas numéricas do site antigo (17 grupos, 22 simpósios, +320 publicações)
**foram deliberadamente removidas** — envelhecem e viram passivo de manutenção.
Mantém-se apenas "desde 2004" como fato histórico.
