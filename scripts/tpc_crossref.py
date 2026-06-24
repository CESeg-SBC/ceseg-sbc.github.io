#!/usr/bin/env python3
"""Cross-reference SBSeg main-track TPC members against accepted papers.

For each edition with a reliable TPC list (scripts/tpc/<year>.json), match the
program-committee members (members + chairs, deduplicated) against the authors of
the accepted main-track papers of that SAME edition (scripts/sbseg_data.json,
sections "Artigos Completos" + "Artigos Curtos"). Produces per-edition and global
statistics consumed by the TPC-statistics page.

Name matching reuses the proven (first_token, last_token) key with generational
suffix handling from fetch_proceedings_stats.py, so "Wilson Melo Jr" matches
"Wilson Melo Junior" and "Aldri Luiz dos Santos" matches "Aldri dos Santos".

No third-party dependencies (the site is static and vanilla by design).
"""
import json
import os
import re
import glob
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPC_DIR = os.path.join(ROOT, "scripts", "tpc")
PAPERS = os.path.join(ROOT, "scripts", "sbseg_data.json")
OUT = os.path.join(ROOT, "assets", "data", "tpc-stats.json")

# Editions whose scraped TPC list is incomplete/unavailable; excluded from stats.
EXCLUDE = {2011, 2015}

# Canonical (current/primary) institution for the GLOBAL ranking, keyed by
# name_key. The per-edition data keeps each year's historical affiliation; the
# global ranking, however, should show the person's current home institution,
# not whichever it happened to be in their earliest TPC edition.
CANONICAL_INST = {
    ("diego", "kreutz"): "UNIPAMPA",
    ("andre", "gregio"): "UFPR",
    ("silvio", "quincozes"): "UNIPAMPA",
}

SUFFIXES = {"jr", "junior", "filho", "neto", "sobrinho", "segundo"}


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


def display_name(name):
    """Trim trailing generational suffix tokens for a clean display label."""
    return re.sub(r"\s+", " ", (name or "").strip())


def load_papers_by_year():
    """year(int) -> list of {title, url, authors:[names]} for main-track articles."""
    data = json.load(open(PAPERS, encoding="utf-8"))
    out = {}
    for ed in data["main_track"]:
        y = int(ed["year"])
        papers = []
        for sec in ed.get("sections", []):
            name = sec.get("section", "")
            if "Completo" not in name and "Curto" not in name:
                continue  # skip Abertura and any non-article section
            for p in sec.get("papers", []):
                authors = [a.strip() for a in re.split(r"[;,]", p.get("authors", "")) if a.strip()]
                papers.append({"title": p.get("title", ""), "url": p.get("url", ""),
                               "authors": authors})
        out[y] = papers
    return out


def load_tpc():
    """year(int) -> {'people': {key:{'name','inst'}}, 'raw_members', 'raw_chairs', 'source'}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(TPC_DIR, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        y = int(d["year"])
        people = {}
        # Union of members + chairs, deduplicated by name_key. Prefer the longest
        # (most complete) name string as the canonical display label.
        for grp in ("members", "chairs"):
            for m in d.get(grp, []):
                k = name_key(m.get("name", ""))
                if not k:
                    continue
                cur = people.get(k)
                nm = display_name(m.get("name", ""))
                inst = m.get("inst", "")
                if cur is None:
                    people[k] = {"name": nm, "inst": inst}
                else:
                    if len(nm) > len(cur["name"]):
                        cur["name"] = nm
                    if not cur["inst"] and inst:
                        cur["inst"] = inst
        out[y] = {"people": people, "n_members": len(d.get("members", [])),
                  "n_chairs": len(d.get("chairs", [])), "source": d.get("source", ""),
                  "notes": d.get("notes", "")}
    return out


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
    papers_by_year = load_papers_by_year()
    tpc = load_tpc()

    editions = []
    # global accumulator: key -> aggregate person record
    glob_people = {}

    for y in sorted(tpc):
        if y in EXCLUDE:
            continue
        people = tpc[y]["people"]
        if not people:
            continue
        papers = papers_by_year.get(y, [])
        total_papers = len(papers)

        # per-member paper count this edition
        member_papers = {k: [] for k in people}  # key -> list of paper indexes
        papers_with_tpc = 0
        for pi, p in enumerate(papers):
            akeys = set(filter(None, (name_key(a) for a in p["authors"])))
            hit = akeys & set(people.keys())
            if hit:
                papers_with_tpc += 1
            for k in hit:
                member_papers[k].append(pi)

        publishers = {k: v for k, v in member_papers.items() if v}
        # edition ranking of publishing members
        ranking = sorted(
            ({"name": people[k]["name"], "inst": people[k]["inst"], "count": len(v),
              "papers": [{"title": papers[i]["title"], "url": papers[i]["url"]} for i in v]}
             for k, v in publishers.items()),
            key=lambda r: (-r["count"], fold(r["name"])))

        n_tpc = len(people)
        editions.append({
            "year": y,
            "tpc_size": n_tpc,
            "tpc_members_listed": tpc[y]["n_members"],
            "tpc_chairs_listed": tpc[y]["n_chairs"],
            "total_papers": total_papers,
            "papers_with_tpc_author": papers_with_tpc,
            "papers_with_tpc_pct": round(100 * papers_with_tpc / total_papers, 1) if total_papers else 0,
            "tpc_publishers": len(publishers),
            "tpc_publishers_pct": round(100 * len(publishers) / n_tpc, 1) if n_tpc else 0,
            "avg_papers_per_publisher": round(sum(len(v) for v in publishers.values()) / len(publishers), 2) if publishers else 0,
            "ranking": ranking,
            "source": tpc[y]["source"],
        })

        # accumulate globals
        for k, v in member_papers.items():
            g = glob_people.setdefault(k, {
                "name": people[k]["name"], "inst": people[k]["inst"],
                "tpc_editions": [], "pub_editions": [], "total_papers": 0,
                "papers": []})
            # keep most complete name / inst
            if len(people[k]["name"]) > len(g["name"]):
                g["name"] = people[k]["name"]
            if not g["inst"] and people[k]["inst"]:
                g["inst"] = people[k]["inst"]
            g["tpc_editions"].append(y)
            if v:
                g["pub_editions"].append(y)
                g["total_papers"] += len(v)
                for i in v:
                    g["papers"].append({"year": y, "title": papers[i]["title"], "url": papers[i]["url"]})

    # global ranking
    global_ranking = sorted(
        glob_people.values(),
        key=lambda g: (-g["total_papers"], -len(g["pub_editions"]), fold(g["name"])))
    for k, g in glob_people.items():
        if k in CANONICAL_INST:
            g["inst"] = CANONICAL_INST[k]
    for g in global_ranking:
        g["n_tpc_editions"] = len(g["tpc_editions"])
        g["n_pub_editions"] = len(g["pub_editions"])

    # correlation: TPC size vs total accepted papers (per edition)
    xs = [e["tpc_size"] for e in editions]
    ys = [e["total_papers"] for e in editions]
    r_size_papers = pearson(xs, ys)
    # correlation: TPC size vs papers with a TPC author
    r_size_impact = pearson([e["tpc_size"] for e in editions],
                            [e["papers_with_tpc_author"] for e in editions])

    # global totals
    total_papers_all = sum(e["total_papers"] for e in editions)
    total_papers_tpc = sum(e["papers_with_tpc_author"] for e in editions)
    distinct_tpc_people = len(glob_people)
    distinct_publishers = sum(1 for g in glob_people.values() if g["pub_editions"])

    out = {
        "generated_note": "Cruzamento TPC x artigos aceitos (trilha principal, completos+curtos). "
                          "Gerado por scripts/tpc_crossref.py. Editions 2011 e 2015 excluidas (TPC indisponivel/incompleto).",
        "editions_covered": [e["year"] for e in editions],
        "editions_excluded": sorted(EXCLUDE),
        "summary": {
            "n_editions": len(editions),
            "total_papers": total_papers_all,
            "papers_with_tpc_author": total_papers_tpc,
            "papers_with_tpc_pct": round(100 * total_papers_tpc / total_papers_all, 1) if total_papers_all else 0,
            "distinct_tpc_people": distinct_tpc_people,
            "distinct_tpc_publishers": distinct_publishers,
            "distinct_tpc_publishers_pct": round(100 * distinct_publishers / distinct_tpc_people, 1) if distinct_tpc_people else 0,
            "corr_tpcsize_papers": round(r_size_papers, 3) if r_size_papers is not None else None,
            "corr_tpcsize_impact": round(r_size_impact, 3) if r_size_impact is not None else None,
        },
        "editions": editions,
        "global_ranking": global_ranking,
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Wrote {OUT}")
    print(f"Editions covered: {out['editions_covered']}")
    print(f"Total papers (covered eds): {total_papers_all}; with TPC author: {total_papers_tpc} "
          f"({out['summary']['papers_with_tpc_pct']}%)")
    print(f"Distinct TPC people: {distinct_tpc_people}; published: {distinct_publishers} "
          f"({out['summary']['distinct_tpc_publishers_pct']}%)")
    print(f"corr(TPC size, #papers) = {out['summary']['corr_tpcsize_papers']}")
    print(f"corr(TPC size, #papers w/ TPC author) = {out['summary']['corr_tpcsize_impact']}")
    print("\nTop 15 global ranking:")
    for g in global_ranking[:15]:
        print(f"  {g['total_papers']:2d} papers / {g['n_pub_editions']} eds  {g['name']} ({g['inst']})")


if __name__ == "__main__":
    main()
