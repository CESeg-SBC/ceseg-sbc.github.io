#!/usr/bin/env python3
"""Aggregate SBSeg proceedings into per-institution publication and tool counts.

The anais pages carry no affiliation, so we attribute each paper to an
institution by matching its author names against the researcher (by name) and
group (by leader) records in cybersecmap.json. A paper counts once per distinct
matched institution. Papers under a "Salão de Ferramentas" section also count as
tools. Unmatched papers are dropped; the overall match rate is recorded.

No third-party dependencies (the site is static and vanilla by design).
"""
import json
import os
import re
import unicodedata
from html import unescape
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["anais-trilha-principal.html", "anais-estendidos.html"]
OUT = os.path.join(ROOT, "assets", "data", "proceedings-stats.json")


def fold(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def name_key(name):
    """(first_token, last_token) of a folded personal name, or None."""
    toks = [t for t in re.split(r"[^\w]+", fold(name)) if len(t) > 1]
    if len(toks) < 2:
        return None
    return (toks[0], toks[-1])


def build_author_index(cybersec):
    """name_key -> {institution, state, lat, lng}; first writer wins."""
    idx = {}
    for r in cybersec.get("records", []):
        if r["type"] == "researcher":
            person, inst = r.get("name"), r
        elif r["type"] == "group" and r.get("leader"):
            person, inst = r.get("leader"), r
        else:
            continue
        k = name_key(person)
        if not k or k in idx:
            continue
        idx[k] = {
            "institution": inst.get("institution") or inst.get("name"),
            "state": inst.get("state", ""),
            "lat": inst.get("lat"),
            "lng": inst.get("lng"),
        }
    return idx


class PaperParser(HTMLParser):
    """Collect (authors, title, url, is_tool) per li.pub-paper.

    is_tool is set when the most recent <h3 class="pub-section"> before the paper
    contained the text "Salão de Ferramentas".
    """

    def __init__(self):
        super().__init__()
        self.papers = []
        self._in_section_h3 = False
        self._section_text = ""
        self._cur_is_tool = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h3" and "pub-section" in (a.get("class") or ""):
            self._in_section_h3 = True
            self._section_text = ""
        elif tag == "li" and "pub-paper" in (a.get("class") or ""):
            cite = a.get("data-cite", "")
            m = re.search(r"https?://\S+", cite)
            self.papers.append({
                "authors": unescape(a.get("data-authors", "")),
                "title": unescape(a.get("data-title", "")),
                "url": m.group(0) if m else "",
                "is_tool": self._cur_is_tool,
            })

    def handle_endtag(self, tag):
        if tag == "h3" and self._in_section_h3:
            self._in_section_h3 = False
            self._cur_is_tool = "salao de ferramentas" in fold(self._section_text)

    def handle_data(self, data):
        if self._in_section_h3:
            self._section_text += data


def parse_papers():
    papers = []
    for page in PAGES:
        p = PaperParser()
        with open(os.path.join(ROOT, page), encoding="utf-8") as fh:
            p.feed(fh.read())
        papers.extend(p.papers)
    return papers


def attribute(papers, idx):
    """Return institutions dict keyed by institution name."""
    insts = {}
    matched_papers = matched_tools = total_tools = 0
    for paper in papers:
        if paper["is_tool"]:
            total_tools += 1
        names = re.split(r"[;,]", paper["authors"])
        hit_insts = {}
        for nm in names:
            k = name_key(nm)
            if k and k in idx:
                hit_insts[idx[k]["institution"]] = idx[k]
        if not hit_insts:
            continue
        matched_papers += 1
        if paper["is_tool"]:
            matched_tools += 1
        rec = {"title": paper["title"], "url": paper["url"]}
        for inst_name, meta in hit_insts.items():
            slot = insts.setdefault(inst_name, {
                "institution": inst_name, "state": meta["state"],
                "lat": meta["lat"], "lng": meta["lng"],
                "pub_count": 0, "tool_count": 0, "pubs": [], "tools": [],
            })
            slot["pub_count"] += 1
            slot["pubs"].append(rec)
            if paper["is_tool"]:
                slot["tool_count"] += 1
                slot["tools"].append(rec)
    rate = {
        "papers": round(matched_papers / len(papers), 3) if papers else 0,
        "tool_papers": round(matched_tools / total_tools, 3) if total_tools else 0,
    }
    return insts, rate


def main():
    with open(os.path.join(ROOT, "assets", "data", "cybersecmap.json"), encoding="utf-8") as fh:
        cybersec = json.load(fh)
    idx = build_author_index(cybersec)
    papers = parse_papers()
    insts, rate = attribute(papers, idx)
    institutions = [i for i in insts.values() if i["lat"] is not None and i["lng"] is not None]
    institutions.sort(key=lambda i: -i["pub_count"])
    out = {"generated_from": PAGES, "match_rate": rate, "institutions": institutions}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"papers={len(papers)} institutions={len(institutions)} "
          f"match_rate={rate} -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
