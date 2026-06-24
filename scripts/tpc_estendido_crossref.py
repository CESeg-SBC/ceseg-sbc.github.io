#!/usr/bin/env python3
"""Cross-reference per-sub-event TPC members against accepted papers in the
SBSeg EXTENDED proceedings (anais estendidos).

Each sub-event (Salão de Ferramentas, WGID, WTICG, CTD, WFC, workshops, etc.)
has its own program committee in the call for papers. For every (edition,
sub-event) unit we match that committee (members + chairs, deduplicated)
against the authors of the papers accepted in the SAME sub-event of the SAME
edition (scripts/sbseg_data.json -> "estendido").

Outputs per-unit, per-edition and global statistics consumed by the
estatisticas-tpc-estendido page. Goals:
  (a) impact of TPC members' own submissions per sub-event / edition;
  (b) correlation between a sub-event's TPC size and its accepted papers;
  (c) most-published TPC members per edition;
  (d) global ranking of most-published TPC members across sub-events.

Name matching reuses the proven (first_token, last_token) key with generational
suffix handling from fetch_proceedings_stats.py / tpc_crossref.py, so e.g.
"Wilson S. Melo Jr." matches "Wilson Melo Junior".

No third-party dependencies (the site is static and vanilla by design).
"""
import json
import os
import re
import glob
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPC_DIR = os.path.join(ROOT, "scripts", "tpc", "estendido")
PAPERS = os.path.join(ROOT, "scripts", "sbseg_data.json")
OUT = os.path.join(ROOT, "assets", "data", "tpc-estendido-stats.json")

SUFFIXES = {"jr", "junior", "filho", "neto", "sobrinho", "segundo"}

# Sections in the extended proceedings that are NOT peer-reviewed sub-events.
SKIP_SECTIONS = {"Abertura"}


def fold(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def name_key(name):
    """(first_token, last_token) of a folded personal name, or None."""
    toks = [t for t in re.split(r"[^\w]+", fold(name)) if len(t) > 1]
    while len(toks) > 2 and toks[-1] in SUFFIXES:
        toks.pop()
    if len(toks) < 2:
        return None
    return (toks[0], toks[-1])


def clean(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def load_papers():
    """{(year, section): [ {title, url, authors:[names]} ]} for extended proceedings."""
    data = json.load(open(PAPERS, encoding="utf-8"))
    out = {}
    for ed in data["estendido"]:
        y = int(ed["year"])
        for sec in ed.get("sections", []):
            name = sec.get("section", "")
            if name in SKIP_SECTIONS:
                continue
            papers = []
            for p in sec.get("papers", []):
                authors = [a.strip() for a in re.split(r"[;,]", p.get("authors", "")) if a.strip()]
                papers.append({"title": p.get("title", ""), "url": p.get("url", ""),
                               "authors": authors})
            out[(y, name)] = papers
    return out


def people_of(subevent):
    """Union of members + chairs, deduplicated by name_key. Returns
    {key: {'name','inst','is_chair'}} plus listed counts."""
    people = {}
    for grp in ("members", "chairs"):
        for m in subevent.get(grp, []):
            k = name_key(m.get("name", ""))
            if not k:
                continue
            nm = clean(m.get("name", ""))
            inst = clean(m.get("inst", ""))
            cur = people.get(k)
            if cur is None:
                people[k] = {"name": nm, "inst": inst, "is_chair": grp == "chairs"}
            else:
                if len(nm) > len(cur["name"]):
                    cur["name"] = nm
                if not cur["inst"] and inst:
                    cur["inst"] = inst
                if grp == "chairs":
                    cur["is_chair"] = True
    return people


def load_tpc_units():
    """List of dicts, one per (edition, sub-event):
    {year, section, abbrev, source, members_listed, chairs_listed,
     roster_published, people:{key->rec}}"""
    units = []
    for f in sorted(glob.glob(os.path.join(TPC_DIR, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        y = int(d["year"])
        for se in d.get("subevents", []):
            people = people_of(se)
            n_members = len(se.get("members", []))
            units.append({
                "year": y,
                "section": se["section"],
                "abbrev": se.get("abbrev", ""),
                "source": se.get("source", ""),
                "members_listed": n_members,
                "chairs_listed": len(se.get("chairs", [])),
                "roster_published": n_members > 0,
                "people": people,
            })
    return units


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return cov / (vx ** 0.5 * vy ** 0.5)


def main():
    papers_by_unit = load_papers()
    units = load_tpc_units()

    unit_out = []
    # global person accumulator: key -> aggregate record
    glob_people = {}
    # per-edition accumulator
    editions = {}

    for u in units:
        y, section = u["year"], u["section"]
        people = u["people"]
        papers = papers_by_unit.get((y, section), [])
        total_papers = len(papers)

        # which papers have >=1 TPC author; which members published
        member_papers = {k: [] for k in people}
        papers_with_tpc = 0
        for pi, p in enumerate(papers):
            akeys = set(filter(None, (name_key(a) for a in p["authors"])))
            hit = akeys & set(people.keys())
            if hit:
                papers_with_tpc += 1
            for k in hit:
                member_papers[k].append(pi)

        publishers = {k: v for k, v in member_papers.items() if v}
        ranking = sorted(
            ({"name": people[k]["name"], "inst": people[k]["inst"],
              "is_chair": people[k]["is_chair"], "count": len(v),
              "papers": [{"title": papers[i]["title"], "url": papers[i]["url"]} for i in v]}
             for k, v in publishers.items()),
            key=lambda r: (-r["count"], fold(r["name"])))

        n_tpc = len(people)
        unit_rec = {
            "year": y,
            "section": section,
            "abbrev": u["abbrev"],
            "tpc_size": n_tpc,
            "members_listed": u["members_listed"],
            "chairs_listed": u["chairs_listed"],
            "roster_published": u["roster_published"],
            "total_papers": total_papers,
            "papers_with_tpc_author": papers_with_tpc,
            "papers_with_tpc_pct": round(100 * papers_with_tpc / total_papers, 1) if total_papers else 0,
            "tpc_publishers": len(publishers),
            "tpc_publishers_pct": round(100 * len(publishers) / n_tpc, 1) if n_tpc else 0,
            "ranking": ranking,
            "source": u["source"],
        }
        unit_out.append(unit_rec)

        # per-edition aggregation
        ed = editions.setdefault(y, {
            "year": y, "n_subevents": 0,
            "subevents_roster_published": 0,
            "total_papers": 0, "papers_with_tpc_author": 0,
            "units": [],  # indexes into unit_out filled later
            "people_papers": {},  # key -> [ {section,title,url} ] within this edition
            "people_meta": {},    # key -> {name,inst}
        })
        ed["n_subevents"] += 1
        if u["roster_published"]:
            ed["subevents_roster_published"] += 1
        ed["total_papers"] += total_papers
        ed["papers_with_tpc_author"] += papers_with_tpc
        for k, v in member_papers.items():
            ed["people_meta"].setdefault(k, {"name": people[k]["name"], "inst": people[k]["inst"]})
            if len(people[k]["name"]) > len(ed["people_meta"][k]["name"]):
                ed["people_meta"][k]["name"] = people[k]["name"]
            for i in v:
                ed["people_papers"].setdefault(k, []).append(
                    {"section": section, "abbrev": u["abbrev"],
                     "title": papers[i]["title"], "url": papers[i]["url"]})

        # global accumulation
        for k, v in member_papers.items():
            g = glob_people.setdefault(k, {
                "name": people[k]["name"], "inst": people[k]["inst"],
                "tpc_units": [], "pub_units": set(), "total_papers": 0, "papers": []})
            if len(people[k]["name"]) > len(g["name"]):
                g["name"] = people[k]["name"]
            if not g["inst"] and people[k]["inst"]:
                g["inst"] = people[k]["inst"]
            g["tpc_units"].append((y, u["abbrev"] or section))
            for i in v:
                g["pub_units"].add((y, section))
                g["total_papers"] += 1
                g["papers"].append({"year": y, "section": section, "abbrev": u["abbrev"],
                                    "title": papers[i]["title"], "url": papers[i]["url"]})

    # finalize per-edition records
    edition_list = []
    for y in sorted(editions):
        ed = editions[y]
        # edition-level distinct TPC people and ranking (across its sub-events)
        ranking = sorted(
            ({"name": ed["people_meta"][k]["name"], "inst": ed["people_meta"][k]["inst"],
              "count": len(v), "papers": v}
             for k, v in ed["people_papers"].items() if v),
            key=lambda r: (-r["count"], fold(r["name"])))
        # distinct people who served on at least one sub-event TPC this edition
        distinct_people = len(ed["people_meta"])
        units_this = [i for i, ur in enumerate(unit_out) if ur["year"] == y]
        edition_list.append({
            "year": y,
            "n_subevents": ed["n_subevents"],
            "subevents_roster_published": ed["subevents_roster_published"],
            "total_papers": ed["total_papers"],
            "papers_with_tpc_author": ed["papers_with_tpc_author"],
            "papers_with_tpc_pct": round(100 * ed["papers_with_tpc_author"] / ed["total_papers"], 1)
                if ed["total_papers"] else 0,
            "distinct_tpc_people": distinct_people,
            "distinct_tpc_publishers": len(ranking),
            "ranking": ranking,
            "unit_indexes": units_this,
        })

    # global ranking
    global_ranking = []
    for g in glob_people.values():
        global_ranking.append({
            "name": g["name"], "inst": g["inst"],
            "total_papers": g["total_papers"],
            "n_tpc_units": len(g["tpc_units"]),
            "n_pub_units": len(g["pub_units"]),
            "n_pub_editions": len(set(y for (y, _s) in g["pub_units"])),
            "papers": sorted(g["papers"], key=lambda p: (-p["year"], p["section"])),
        })
    global_ranking.sort(key=lambda g: (-g["total_papers"], -g["n_pub_units"], fold(g["name"])))

    # correlation (b): TPC size vs accepted papers, per sub-event unit.
    # Primary: only units with a published member roster (chair-only units are
    # not a real "committee size" signal). Also report the all-units value.
    pub_units = [u for u in unit_out if u["roster_published"]]
    corr_pub = pearson([u["tpc_size"] for u in pub_units],
                       [u["total_papers"] for u in pub_units])
    corr_all = pearson([u["tpc_size"] for u in unit_out],
                       [u["total_papers"] for u in unit_out])
    # correlation: TPC size vs papers-with-TPC-author (the "impact" measure)
    corr_impact = pearson([u["tpc_size"] for u in pub_units],
                          [u["papers_with_tpc_author"] for u in pub_units])

    # global totals
    total_papers_all = sum(u["total_papers"] for u in unit_out)
    total_papers_tpc = sum(u["papers_with_tpc_author"] for u in unit_out)
    distinct_people = len(glob_people)
    distinct_publishers = sum(1 for g in glob_people.values() if g["pub_units"])

    out = {
        "generated_note": "Cruzamento TPC por sub-evento x artigos aceitos nos anais estendidos "
                          "do SBSeg. Gerado por scripts/tpc_estendido_crossref.py a partir de "
                          "scripts/tpc/estendido/<ano>.json e scripts/sbseg_data.json. "
                          "Edicoes 2018-2025.",
        "editions_covered": sorted(editions.keys()),
        "summary": {
            "n_editions": len(editions),
            "n_subevent_units": len(unit_out),
            "n_subevent_units_roster": len(pub_units),
            "total_papers": total_papers_all,
            "papers_with_tpc_author": total_papers_tpc,
            "papers_with_tpc_pct": round(100 * total_papers_tpc / total_papers_all, 1) if total_papers_all else 0,
            "distinct_tpc_people": distinct_people,
            "distinct_tpc_publishers": distinct_publishers,
            "distinct_tpc_publishers_pct": round(100 * distinct_publishers / distinct_people, 1) if distinct_people else 0,
            "corr_tpcsize_papers": round(corr_pub, 3) if corr_pub is not None else None,
            "corr_tpcsize_papers_all": round(corr_all, 3) if corr_all is not None else None,
            "corr_tpcsize_impact": round(corr_impact, 3) if corr_impact is not None else None,
        },
        "subevent_units": unit_out,
        "editions": edition_list,
        "global_ranking": global_ranking,
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    s = out["summary"]
    print(f"Wrote {OUT}")
    print(f"Editions: {out['editions_covered']}")
    print(f"Sub-event units: {s['n_subevent_units']} ({s['n_subevent_units_roster']} with member roster)")
    print(f"Papers: {s['total_papers']}; with TPC author: {s['papers_with_tpc_author']} ({s['papers_with_tpc_pct']}%)")
    print(f"Distinct TPC people: {s['distinct_tpc_people']}; published in their track: "
          f"{s['distinct_tpc_publishers']} ({s['distinct_tpc_publishers_pct']}%)")
    print(f"corr(TPC size, papers)  roster-only={s['corr_tpcsize_papers']}  all-units={s['corr_tpcsize_papers_all']}")
    print(f"corr(TPC size, papers w/ TPC author) = {s['corr_tpcsize_impact']}")
    print("\nTop 15 global ranking:")
    for g in global_ranking[:15]:
        print(f"  {g['total_papers']:2d} papers / {g['n_pub_units']} units / {g['n_pub_editions']} eds  "
              f"{g['name']} ({g['inst']})")


if __name__ == "__main__":
    main()
