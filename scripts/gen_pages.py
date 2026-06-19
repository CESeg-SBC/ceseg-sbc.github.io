#!/usr/bin/env python3
"""Generate the inner CESeg content pages (static HTML) from a small spec.

Output is committed static HTML — this is a one-off maintenance generator,
NOT a build step that runs when the site is served. Re-run after editing the
spec below. The home page (index.html) is hand-authored, not generated.

Content was transcribed from https://www.ceseg.org (a Wix/JS site). Stable,
language-neutral data (names, institutions, dates, PDF links, journal titles)
is embedded inline; translatable prose/headings use data-i18n keys that live
in assets/i18n/{pt,en,es}.json. Missing keys fall back to the inline PT text.
"""
import json
import os

import keywords  # sibling module: word-cloud rendering

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# filename (no ext) -> (i18n namespace, original ceseg.org route)
PAGES = [
    ("lista-de-discussao", "lista", "/lista-de-discucao"),
    ("organizacao",        "org",   "/organizacao"),
    ("comissoes",          "comissoes", "/comiss%C3%B5es"),
    ("conferencistas",     "conferencistas", "/conferencistas"),
    ("grupos",             "grupos", "/grupos"),
    ("instituto",          "instituto", "/instituto"),
    ("sbseg",              "sbseg", "/sbseg"),
    ("anais",              "anais", "/anais-trilha-principal"),
    ("minicursos",         "minicursos", "/mini-cursos"),
    ("wise",               "wise",  "/wise"),
    ("homenageados",       "homenageados", "/homenageados"),
    ("publicacoes",        "publicacoes", "/publicacoes"),
    ("referenciais",       "referenciais", "/referenciais"),
    ("onde-publicar",      "ondepublicar", "/onde-publicar"),
    ("documentos",         "documentos", "/documentos"),
    ("atas",               "atas",  "/atas"),
    ("regimentos",         "regimentos", "/regimentos"),
    ("portarias",          "portarias", "/portarias"),
]

# ---- Reusable data (language-neutral) ----

COORD_HISTORY = [
    ("2024–2026", "Marcos Simplício (USP)", "Diego Kreutz (UNIPAMPA)"),
    ("2022–2024", "Igor Moraes (UFF)", "Marcos Simplício (USP)"),
    ("2020–2022", "Michele Nogueira (UFMG)", "Igor Moraes (UFF)"),
    ("2016–2018", "Altair Santin (PUC-PR)", "Michele Nogueira (UFMG)"),
    ("2014–2016", "Eduardo L. Feitosa (UFAM)", "Altair Santin (PUC-PR)"),
    ("2012–2014", "Aldri L. dos Santos (UFPR)", "Eduardo L. Feitosa (UFAM)"),
    ("2010–2012", "Anderson C. A. Nascimento (UnB)", "Aldri L. dos Santos (UFPR)"),
    ("2008–2010", "Marinho P. Barcellos (UFRGS)", "Anderson C. A. Nascimento (UnB)"),
    ("2006–2008", "Luciano Gaspary (UFRGS)", "Marinho P. Barcellos (UFRGS)"),
    ("2004–2006", "Ricardo Dahab (Unicamp)", "Luciano Gaspary (UFRGS)"),
]

INSTITUTO_INSTS = [
    "CDCiber – Exército Brasileiro", "IFSC", "INMETRO", "PUC-PR", "UECE", "UERJ",
    "UFAM", "UFF", "UFPA", "UFPE", "UFPR", "UFRJ", "UFSC", "UFSM", "UNB",
    "UNESP", "UNICAMP", "UNIVALI", "USP",
]

SBSEG_EDITIONS = [
    ("XXV", "2025", "1–4 set", "Foz do Iguaçu / PR", "https://sbseg2025.ppgia.pucpr.br/"),
    ("XXIV", "2024", "16–19 set", "São José dos Campos / SP", "https://sbseg2024.ita.br/"),
    ("XXIII", "2023", "18–21 set", "Juiz de Fora / MG", "https://www.sbc.org.br/sbseg2023/"),
]

HOMENAGEADOS = [
    ("2025", "Anderson Nascimento", "UnB · UW-Tacoma · Visa Research", False,
     "Especialista em teoria da informação e privacidade, com quase duas décadas de experiência pós-doutoral em aprendizado de máquina com preservação de privacidade e criptografia."),
    ("2023", "Routo Terada", "USP", False,
     "Professor com atuação em criptografia e segurança de dados."),
    ("2021", "Otto Carlos M. B. Duarte", "UFRJ", True,
     "Pesquisador em protocolos de comunicação, Internet do futuro, segurança e cadeias de blocos, com mais de 350 artigos publicados."),
    ("2019", "Ricardo Dahab", "Unicamp", False,
     "Professor com atuação em algoritmos criptográficos e segurança da informação, envolvido na infraestrutura ICP-Brasil."),
    ("2018", "Joni da Silva Fraga", "UFSC", False,
     "Professor com atuação em sistemas distribuídos, segurança, tolerância a falhas e tolerância a intrusões."),
    ("2018", "Lau Cheuk Lung", "UFSC", True,
     "Pesquisador em segurança de sistemas distribuídos, tolerância a faltas bizantinas e algoritmos distribuídos."),
]

ONDE_PERIODICOS = [
    "IEEE Transactions on Information Forensics and Security",
    "IEEE Transactions on Dependable and Secure Computing",
    "Computers &amp; Security (Elsevier)",
    "Journal of Cryptology (Springer)",
    "ACM Transactions on Information and System Security",
    "Designs, Codes and Cryptography (Springer)",
    "Computer Law &amp; Security Review",
    "International Journal of Information Security (Springer)",
    "International Journal of Network Security (IJNS)",
    "Journal of Computer Security",
    "IET Information Security",
    "IET Biometrics",
    "International Journal of Communication Networks and Information Security",
    "IEEE Security &amp; Privacy Magazine",
    "Security and Communication Networks (Wiley)",
    "International Journal of Security and Networks",
    "Computer Fraud &amp; Security",
    "International Journal of Applied Cryptography",
    "Network Security",
    "International Journal of Information and Network Security",
    "Journal of Discrete Mathematical Sciences and Cryptography",
    "Journal of Information Privacy and Security",
]

ONDE_CONFS = [
    "ACM CCS", "IEEE S&amp;P (Oakland)", "USENIX Security", "NDSS",
    "CRYPTO", "EUROCRYPT", "ASIACRYPT", "ACSAC", "ESORICS", "PETS",
    "SBSeg (Simpósio Brasileiro de Cibersegurança)",
]

ATAS = [
    ("02/09/2025", "SBSeg 2025 (a aprovar)", "https://www.ceseg.org/_files/ugd/000626_b4185e1c311a48d08fa27396ccb497ba.pdf"),
    ("17/09/2024", "SBSeg 2024", "https://www.ceseg.org/_files/ugd/000626_5c25194ad9904a6ba6302f743c4920df.pdf"),
    ("10/05/2024", "Reunião online", "https://www.ceseg.org/_files/ugd/000626_414ee7b820cf4b7a8e3caedfecdbcc06.pdf"),
    ("19/09/2023", "SBSeg 2023", "https://www.ceseg.org/_files/ugd/000626_f81d0f371a5b4a81b7784c06e85c9167.pdf"),
    ("13/09/2022", "SBSeg 2022 (híbrido)", "https://www.ceseg.org/_files/ugd/000626_6d043780b8f8433d9b6519a43954227f.pdf"),
    ("14/10/2021", "SBSeg 2021 (online)", "https://www.ceseg.org/_files/ugd/000626_f4851df877064e66ae90a1ea6617a5d9.pdf"),
    ("14/10/2020", "SBSeg 2020 (online)", "https://www.ceseg.org/_files/ugd/000626_f57b71817efe497f98ebb6756f62ee4f.pdf"),
    ("03/09/2019", "SBSeg 2019", "https://www.ceseg.org/_files/ugd/000626_893b88ca3cec43e7a939cf2f5069f943.pdf"),
    ("23/10/2018", "SBSeg 2018", "https://www.ceseg.org/_files/ugd/000626_e9d5acd1f909415caf525607723c2d6f.pdf"),
    ("07/11/2017", "SBSeg 2017", "https://www.ceseg.org/_files/ugd/000626_e2c9ea786bea402290d167c3454b12ea.pdf"),
    ("08/11/2016", "SBSeg 2016", "https://www.ceseg.org/_files/ugd/000626_b34abe14a0e248a5943594c38e10dcc1.pdf"),
    ("10/11/2015", "SBSeg 2015", "https://www.ceseg.org/_files/ugd/000626_5fb8449eb3ca4fc6ac90ebe06ee4550f.pdf"),
    ("04/11/2014", "SBSeg 2014", "https://www.ceseg.org/_files/ugd/000626_2f595860682e4d879091de8ef137d63c.pdf"),
    ("13/11/2013", "SBSeg 2013", "https://www.ceseg.org/_files/ugd/000626_f571c539fbe7476f8af4eecd9d100259.pdf"),
    ("20/11/2012", "SBSeg 2012", "https://www.ceseg.org/_files/ugd/000626_3f302a7ff01949edb48e763be42e11d0.pdf"),
    ("09/11/2011", "SBSeg 2011", "https://www.ceseg.org/_files/ugd/000626_92b33cb2ccea437995e2170a21422765.pdf"),
    ("14/10/2010", "SBSeg 2010", "https://www.ceseg.org/_files/ugd/000626_56fdd2c73d254dcea92ed0771763de8d.pdf"),
    ("30/09/2009", "SBSeg 2009", "https://www.ceseg.org/_files/ugd/000626_cbaf4cfbbe0c494399e1aeff9dd485e2.pdf"),
    ("04/09/2008", "SBSeg 2008", None),
    ("30/08/2007", "SBSeg 2007", None),
    ("29/08/2006", "SBSeg 2006", "https://www.ceseg.org/_files/ugd/000626_123facb85d2140519dd35289480fbe74.pdf"),
    ("29/09/2005", "SBSeg 2005", "https://www.ceseg.org/_files/ugd/000626_4a6606c80ba6483d86dca001edc99bca.pdf"),
]

REGIMENTO_PDF = "https://www.ceseg.org/_files/ugd/000626_a187abf206844042af535162520f61d9.pdf"
PORTARIA_PDF = "https://www.ceseg.org/_files/ugd/000626_d5d88ab4f0f44214bb7f23ad66588492.pdf"
SOL_ARTIGOS = "https://sol.sbc.org.br/index.php/sbseg/issue/archive"
SOL_MINICURSOS = "https://sol.sbc.org.br/livros/index.php/sbc/catalog/category/seginfo"
SOL_REFERENCIAIS = "https://sol.sbc.org.br/livros/index.php/sbc/catalog/book/125"
LISTA_URL = "https://grupos.ufrgs.br/mailman/listinfo/seg-l"


# ---- Per-page content bodies ----

def _ext_link(href, key, fallback):
    return f'<a class="btn btn-primary" href="{href}" target="_blank" rel="noopener" data-i18n="{key}">{fallback}</a>'


def body_lista():
    return f"""
      <p data-i18n="lista.warn">Espera-se que esta lista <strong>não</strong> seja usada como espaço para consultoria técnica em configuração de sistemas — existem fóruns mais apropriados para isso.</p>
      <h2 data-i18n="lista.joinH2">Como participar</h2>
      <p data-i18n="lista.joinText">A inscrição e o acesso aos arquivos (para inscritos) são feitos pela plataforma da lista, hospedada na UFRGS.</p>
      <p><a class="btn btn-primary" href="{LISTA_URL}" target="_blank" rel="noopener" data-i18n="lista.joinCta">Inscrever-se na lista →</a></p>"""


def body_org():
    rows = "\n".join(
        f'        <tr><td>{term}</td><td>{coord}</td><td>{vice}</td></tr>'
        for term, coord, vice in COORD_HISTORY
    )
    return f"""
      <h2 data-i18n="org.coordH2">Coordenação 2024–2026</h2>
      <ul>
        <li><strong data-i18n="org.lblCoord">Coordenador</strong>: Marcos Simplício (USP)</li>
        <li><strong data-i18n="org.lblVice">Vice-coordenador</strong>: Diego Kreutz (UNIPAMPA)</li>
      </ul>
      <h2 data-i18n="org.histH2">Histórico de coordenações</h2>
      <div class="table-wrap"><table>
        <thead><tr>
          <th data-i18n="org.thTerm">Mandato</th>
          <th data-i18n="org.lblCoord">Coordenador</th>
          <th data-i18n="org.lblVice">Vice-coordenador</th>
        </tr></thead>
        <tbody>
{rows}
        </tbody>
      </table></div>
      <h2 data-i18n="org.gestorH2">Comitê gestor (2026)</h2>
      <p data-i18n="org.gestorText">Integram o comitê gestor, entre outros, Altair Olivo Santin, André Grégio, Charles Miers, Diego Kreutz e Diogo Mattos, representando diversas universidades brasileiras.</p>"""


def body_comissoes():
    return """
      <h2 data-i18n="comissoes.eduH2">Comissão de Educação</h2>
      <p data-i18n="comissoes.eduText">Designada pela Portaria nº 020, de 23 de julho de 2021, produziu os referenciais curriculares de cibersegurança destinados às Diretrizes Curriculares Nacionais. A consulta pública ocorreu de 13/12/2022 a 27/02/2023, e a versão final foi publicada na Biblioteca Digital da SBC (SOL).</p>
      <p><strong data-i18n="ui.members">Membros</strong>: Aldri Luiz dos Santos (UFMG) · Altair Olivo Santin (PUC-PR) · Marcos Simplício (USP).</p>
      <h2 data-i18n="comissoes.compH2">Comissão de Competições</h2>
      <p data-i18n="comissoes.compText">Estabelecida em 19 de setembro de 2023, atua para definir e promover estratégias de competições alinhadas à Comissão de Educação, atendendo à comunidade científica de segurança e às demandas da sociedade.</p>
      <p><strong data-i18n="ui.members">Membros</strong>: Aldri Luiz dos Santos (UFMG) · Diego Luis Kreutz (UNIPAMPA) · Weverton Luis da Costa Cordeiro (UFRGS).</p>"""


def body_conferencistas():
    return """
      <p data-i18n="conferencistas.progText">A Sociedade Brasileira de Computação (SBC) lançou em 2014 o Programa de Conferencistas Seniores. Por meio dele, cada Comissão Especial indica pesquisadores com vasta experiência em sua área para representá-la em eventos e palestras.</p>
      <h2 data-i18n="ui.current">Atuais</h2>
      <p>2024–</p>
      <ul>
        <li>Aldri Luiz dos Santos — UFMG</li>
        <li>Ricardo Dahab — Unicamp</li>
        <li>Routo Terada — USP</li>
      </ul>
      <h2 data-i18n="ui.previous">Anteriores</h2>
      <p>2014–2024</p>
      <ul>
        <li>Joni da Silva Fraga — UFSC</li>
        <li>Ricardo Dahab — Unicamp</li>
      </ul>"""


def body_grupos():
    return """
      <p data-i18n="grupos.liveText">A lista de grupos de pesquisa é dinâmica e mantida no portal oficial da CESeg, onde é atualizada continuamente. Consulte a relação completa — instituições, coordenadores e linhas de atuação — diretamente na fonte:</p>
      <p><a class="btn btn-primary" href="https://www.ceseg.org/lista-grupos" target="_blank" rel="noopener" data-i18n="grupos.liveCta">Ver a lista completa de grupos →</a></p>"""


def body_instituto():
    insts = "\n".join(f'        <li>{i}</li>' for i in INSTITUTO_INSTS)
    return f"""
      <p data-i18n="instituto.fullName"><strong>Instituto Nacional de Ciência e Tecnologia em Segurança Cibernética</strong></p>
      <p data-i18n="instituto.netText">Uma rede de 19 instituições de pesquisa, capitaneada pela UNICAMP, dedicada à ciência e tecnologia em segurança cibernética.</p>
      <h2 data-i18n="instituto.instH2">Instituições participantes</h2>
      <ul class="cols-list">
{insts}
      </ul>"""


def body_sbseg():
    eds = "\n".join(
        f'        <tr><td>{num}</td><td>{year}</td><td>{date}</td><td>{place}</td>'
        f'<td><a href="{url}" target="_blank" rel="noopener">{url.split("//")[1].rstrip("/")}</a></td></tr>'
        for num, year, date, place, url in SBSEG_EDITIONS
    )
    return f"""
      <h2 data-i18n="sbseg.histH2">Histórico</h2>
      <p data-i18n="sbseg.histText">Antes denominado Simpósio Brasileiro em Segurança da Informação e de Sistemas Computacionais, o SBSeg funcionou como workshop entre 2001 e 2004. A partir de 2005, concomitantemente à criação da comissão especial, passou a ser organizado como evento solo, tornando-se o principal fórum de cibersegurança do país.</p>
      <h2 data-i18n="sbseg.edsH2">Edições recentes</h2>
      <div class="table-wrap"><table>
        <thead><tr>
          <th>#</th><th data-i18n="sbseg.thYear">Ano</th>
          <th data-i18n="sbseg.thDate">Data</th>
          <th data-i18n="sbseg.thPlace">Local</th>
          <th data-i18n="sbseg.thSite">Site</th>
        </tr></thead>
        <tbody>
{eds}
        </tbody>
      </table></div>
      <p data-i18n="sbseg.olderText">As edições anteriores e seus anais estão disponíveis na Biblioteca Digital da SBC (SOL).</p>"""


def body_anais():
    return f"""
      <p data-i18n="anais.solText">A Biblioteca Digital da Sociedade Brasileira de Computação (SOL) reúne os artigos de todas as edições do SBSeg.</p>
      <p>{_ext_link(SOL_ARTIGOS, "anais.solCta", "Artigos do SBSeg no SOL →")}</p>"""


def body_minicursos():
    return f"""
      <p data-i18n="minicursos.solText">Os minicursos do SBSeg são publicados como capítulos de livro e estão disponíveis na Biblioteca Digital da SBC (SOL).</p>
      <p>{_ext_link(SOL_MINICURSOS, "minicursos.solCta", "Minicursos no SOL →")}</p>"""


def body_wise():
    return """
      <p data-i18n="wise.text">O WISE é a trilha do SBSeg dedicada à educação e à formação em segurança da informação, reunindo trabalhos e experiências sobre o ensino de cibersegurança.</p>"""


def body_homenageados():
    items = []
    for year, name, inst, memoriam, desc in HOMENAGEADOS:
        tag = ' <span class="muted" data-i18n="ui.inMemoriam">(in memoriam)</span>' if memoriam else ""
        items.append(
            f'        <article class="entry"><h3>{year} — {name}{tag}</h3>'
            f'<p class="muted">{inst}</p><p>{desc}</p></article>'
        )
    body = "\n".join(items)
    return f"""
      <div class="entries">
{body}
      </div>"""


def _combined_cloud_html():
    """Render the overall keyword cloud from the aggregate fetch_sbseg.py wrote."""
    path = os.path.join(ROOT, "scripts", "keywords_combined.json")
    if not os.path.exists(path):
        return ""
    counts = dict(json.load(open(path, encoding="utf-8"))["counts"])
    return keywords.cloud_html(counts, cloud_id="genCloud", limit=100, indent="        ")


def body_publicacoes():
    cloud = _combined_cloud_html()
    return f"""
      <p class="lead" data-i18n="publicacoes.intro"></p>
      <p data-i18n="publicacoes.text">Esta página reúne o <strong>catálogo completo</strong> dos anais do SBSeg publicados na Biblioteca Digital SOL/SBC, acrescido de <strong>índices e recursos de busca complementares</strong> que facilitam a localização e a navegação transversal às edições, por título, autor ou tema.</p>

      <div class="feature feature-sol">
        <div>
          <div class="eyebrow" style="color:#fff;opacity:.85" data-i18n="publicacoes.solEyebrow">Biblioteca Digital · SOL/SBC</div>
          <h2 data-i18n="publicacoes.solH2">Anais oficiais na SOL/SBC</h2>
          <p data-i18n="publicacoes.solText">Os anais de todas as edições do SBSeg são publicados na biblioteca digital SOL da SBC. Os recursos desta página complementam esse acervo oficial com busca e índices que cruzam as edições.</p>
        </div>
        <a class="btn" style="background:#fff;color:var(--navy)" href="{SOL_ARTIGOS}" target="_blank" rel="noopener" data-i18n="publicacoes.solCta">Ver anais na SOL →</a>
      </div>

      <div class="cards">
        <a class="card" href="anais-trilha-principal.html"><h3 data-i18n="nav.anaisTP">Artigos · Trilha Principal</h3>
          <p data-i18n="anaistp.note">Todos os artigos da Trilha Principal do SBSeg, agrupados por edição. Use a busca para filtrar por título, autor ou palavra-chave.</p></a>
        <a class="card" href="anais-estendidos.html"><h3 data-i18n="nav.anaisEst">Artigos · Anais Estendidos</h3>
          <p data-i18n="anaisest.note">Todos os artigos dos Anais Estendidos do SBSeg, agrupados por edição e sub-evento. Use a busca para filtrar por título, autor ou palavra-chave.</p></a>
        <a class="card" href="minicursos.html"><h3 data-i18n="publicacoes.ebooksCard">Ebooks de Minicursos</h3>
          <p data-i18n="publicacoes.ebooksCardNote">Os minicursos de cada edição do SBSeg, compilados e publicados em ebook no catálogo da SBC OpenLib.</p></a>
        <a class="card" href="referenciais.html"><h3 data-i18n="nav.referenciais">Referenciais</h3>
          <p data-i18n="referenciais.intro">Materiais de referência para pesquisa e ensino em cibersegurança.</p></a>
        <a class="card" href="onde-publicar.html"><h3 data-i18n="nav.ondepublicar">Onde Publicar</h3>
          <p data-i18n="ondepublicar.intro">Periódicos e conferências para publicação de pesquisa em cibersegurança.</p></a>
      </div>

      <section class="pub-cloud-section" aria-labelledby="genCloudTitle">
        <h2 id="genCloudTitle" class="pub-cloud-title" data-i18n="publicacoes.cloudTitle">Mapa geral de palavras-chave</h2>
        <p class="pub-cloud-note" data-i18n="publicacoes.cloudNote">Temas mais recorrentes em todas as edições do SBSeg, combinando a Trilha Principal e os Anais Estendidos. As palavras-chave foram extraídas automaticamente dos títulos dos artigos. Clique em um termo para buscá-lo nos anais.</p>
{cloud}
      </section>"""


def body_referenciais():
    return f"""
      <p data-i18n="referenciais.text">Os Referenciais de Formação em Cibersegurança foram elaborados pela Comissão de Educação da CESeg para orientar as instituições quanto às competências necessárias à formação de profissionais da área, com vistas à integração às Diretrizes Curriculares Nacionais (DCN) do Ministério da Educação. A versão final está publicada na Biblioteca Digital da SBC (SOL). © 2020 CESeg.</p>
      <p>{_ext_link(SOL_REFERENCIAIS, "referenciais.cta", "Acessar os referenciais no SOL →")}</p>"""


def body_ondepublicar():
    per = "\n".join(f'        <li>{p}</li>' for p in ONDE_PERIODICOS)
    conf = "\n".join(f'        <li>{c}</li>' for c in ONDE_CONFS)
    return f"""
      <h2 data-i18n="ondepublicar.jH2">Periódicos</h2>
      <ul class="cols-list">
{per}
      </ul>
      <h2 data-i18n="ondepublicar.cH2">Conferências</h2>
      <ul class="cols-list">
{conf}
      </ul>
      <p class="muted" data-i18n="ondepublicar.cNote">Entre outras conferências internacionais de referência na área.</p>"""


def body_documentos():
    return """
      <div class="cards">
        <a class="card" href="atas.html"><h3 data-i18n="nav.atas">Atas</h3>
          <p data-i18n="documentos.atasText">Atas das reuniões da CESeg realizadas durante as edições anuais do SBSeg.</p></a>
        <a class="card" href="regimentos.html"><h3 data-i18n="nav.regimentos">Regimentos</h3>
          <p data-i18n="documentos.regText">Regimento interno que rege o funcionamento da comissão.</p></a>
        <a class="card" href="portarias.html"><h3 data-i18n="nav.portarias">Portarias</h3>
          <p data-i18n="documentos.portText">Portarias e atos oficiais relacionados às atividades da CESeg.</p></a>
      </div>"""


def body_atas():
    rows = []
    for date, title, url in ATAS:
        if url:
            link = f'<a href="{url}" target="_blank" rel="noopener" data-i18n="ui.downloadPdf">Baixar PDF</a>'
        else:
            link = '<span class="muted" data-i18n="ui.noLink">sem link</span>'
        rows.append(f'        <tr><td>{date}</td><td>{title}</td><td>{link}</td></tr>')
    body = "\n".join(rows)
    return f"""
      <p data-i18n="atas.note">Atas das reuniões da Comissão Especial de Cibersegurança (antiga Comissão Especial em Segurança da Informação e de Sistemas Computacionais), realizadas durante as edições anuais do SBSeg.</p>
      <div class="table-wrap"><table>
        <thead><tr>
          <th data-i18n="atas.thDate">Data</th>
          <th data-i18n="atas.thMeeting">Reunião</th>
          <th data-i18n="atas.thDoc">Documento</th>
        </tr></thead>
        <tbody>
{body}
        </tbody>
      </table></div>"""


def body_regimentos():
    return f"""
      <ul>
        <li data-i18n="regimentos.item2017">Regimento vigente (2017)</li>
      </ul>
      <p>{_ext_link(REGIMENTO_PDF, "ui.downloadPdf", "Baixar PDF")}</p>"""


def body_portarias():
    return f"""
      <ul>
        <li data-i18n="portarias.item020">SBC — Portaria nº 020, de 23 de julho de 2021 — Curso de Cibersegurança</li>
      </ul>
      <p>{_ext_link(PORTARIA_PDF, "ui.downloadPdf", "Baixar PDF")}</p>"""


BODIES = {
    "lista": body_lista, "org": body_org, "comissoes": body_comissoes,
    "conferencistas": body_conferencistas, "grupos": body_grupos,
    "instituto": body_instituto, "sbseg": body_sbseg, "anais": body_anais,
    "minicursos": body_minicursos, "wise": body_wise,
    "homenageados": body_homenageados, "publicacoes": body_publicacoes,
    "referenciais": body_referenciais, "ondepublicar": body_ondepublicar,
    "documentos": body_documentos, "atas": body_atas,
    "regimentos": body_regimentos, "portarias": body_portarias,
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
      <p class="lead" data-i18n="{ns}.intro"></p>{body}
      <p class="source-note"><span data-i18n="common.sourceNote">Conteúdo da página oficial</span>
        <a href="https://www.ceseg.org{route}" target="_blank" rel="noopener">ceseg.org{route}</a>.</p>
    </div></section>
  </main>
  <footer id="site-footer"></footer>
  <script src="assets/js/site.js"></script>
</body>
</html>
"""


def main():
    for page, ns, route in PAGES:
        body = BODIES[ns]() if ns in BODIES else ""
        html = TEMPLATE.format(ns=ns, page=page, route=route, body=body)
        path = os.path.join(ROOT, f"{page}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"wrote {page}.html (ns={ns})")


if __name__ == "__main__":
    main()
