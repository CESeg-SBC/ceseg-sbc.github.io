#!/usr/bin/env python3
"""Download and clean the RNP Cybersecurity Map data.

Source: https://cybersecmap.rnp.br (Angular SPA backed by same-origin endpoints
with no CORS headers, so the browser cannot fetch it live). This script pulls a
snapshot and parses the messy HTML descriptions into one compact JSON the static
CESeg page (comunidade.html / assets/js/mapa.js) can load directly.

Re-run to refresh:  python3 scripts/fetch_cybersecmap.py

Outputs:
  scripts/cybersecmap_raw/*.json   raw API snapshot (for auditing)
  assets/data/cybersecmap.json     cleaned, unified records + metadata
"""
import html
import json
import os
import re
import urllib.request

BASE = "https://cybersecmap.rnp.br"
ENDPOINTS = ["settings", "menugroup", "menu", "tag", "tagrelationship",
             "location", "link", "linksgroup"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "scripts", "cybersecmap_raw")
OUT = os.path.join(ROOT, "assets", "data", "cybersecmap.json")

# Menu ids (from /menu/). Primary "actor" menus whose entities we surface.
M_RESEARCHERS = 1
M_GROUPS = 2
M_TOPICS = 3
M_PROGRAMS = 4
M_PRODUCTIONS = 10
M_CENTERS = 11
M_WORKING_GROUPS = 12
M_ARTICLES = 14
# By-state menus used only to derive the state facet for researchers.
M_STATE_MENUS = [5, 6, 8, 9]

UF = {
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM",
    "bahia": "BA", "ceara": "CE", "distrito federal": "DF",
    "espirito santo": "ES", "goias": "GO", "maranhao": "MA",
    "mato grosso": "MT", "mato grosso do sul": "MS", "minas gerais": "MG",
    "para": "PA", "paraiba": "PB", "parana": "PR", "pernambuco": "PE",
    "piaui": "PI", "rio de janeiro": "RJ", "rio grande do norte": "RN",
    "rio grande do sul": "RS", "rondonia": "RO", "roraima": "RR",
    "santa catarina": "SC", "sao paulo": "SP", "sergipe": "SE",
    "tocantins": "TO",
}
UF_CODES = set(UF.values())


def fetch(ep):
    url = f"{BASE}/{ep}/"
    req = urllib.request.Request(url, headers={"User-Agent": "ceseg-mapa/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def strip_tags(s):
    if not s:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</(div|p|li|tr|h[1-6])\s*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t​\xa0]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def field(text, *labels):
    """Extract the value following 'Label:' up to the next line break."""
    for label in labels:
        m = re.search(re.escape(label) + r"\s*:?\s*(.+)", text, flags=re.I)
        if m:
            return m.group(1).split("\n")[0].strip(" :-")
    return ""


def first_url(s):
    m = re.search(r"https?://[^\s\"'<>)]+", s or "")
    return m.group(0) if m else ""


def norm_state(s):
    if not s:
        return ""
    # explicit 2-letter code in parens or after a dash, e.g. "(SP)" / "- DF"
    for m in re.findall(r"\b([A-Z]{2})\b", s):
        if m in UF_CODES:
            return m
    key = re.sub(r"[^a-z ]", "", s.lower().replace("ã", "a").replace("á", "a")
                 .replace("â", "a").replace("é", "e").replace("í", "i")
                 .replace("ó", "o").replace("ô", "o").replace("ú", "u")
                 .replace("ç", "c")).strip()
    return UF.get(key, "")


def coord(loc):
    try:
        return round(float(loc["latitude"]), 6), round(float(loc["longitude"]), 6)
    except (TypeError, ValueError, KeyError):
        return None, None


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    data = {}
    for ep in ENDPOINTS:
        print(f"fetching /{ep}/ ...", end=" ", flush=True)
        data[ep] = fetch(ep)
        with open(os.path.join(RAW_DIR, f"{ep}.json"), "w", encoding="utf-8") as f:
            json.dump(data[ep], f, ensure_ascii=False, indent=1)
        print(f"{len(data[ep])} items")

    locs = {l["id"]: l for l in data["location"]}
    tags = data["tag"]
    by_menu = {}
    for t in tags:
        by_menu.setdefault(t["parent_menu"], []).append(t)

    # Reverse index: location id -> state, location id -> [topics]
    loc_state = {}
    for mid in M_STATE_MENUS:
        for t in by_menu.get(mid, []):
            st = norm_state(t["name"])
            if st:
                for lid in t["related_locations"]:
                    loc_state.setdefault(lid, st)
    loc_topics = {}
    for t in by_menu.get(M_TOPICS, []):
        for lid in t["related_locations"]:
            loc_topics.setdefault(lid, []).append(t["name"])

    records = []
    seen = set()  # (type, lid) dedup

    def add(rec):
        records.append(rec)

    # --- Researchers: info in location description ---
    for t in by_menu.get(M_RESEARCHERS, []):
        for lid in t["related_locations"]:
            loc = locs.get(lid)
            if not loc:
                continue
            lat, lng = coord(loc)
            txt = strip_tags(loc["description"])
            raw = loc["description"]
            name = field(txt, "Researcher Name") or loc["name"]
            urls = re.findall(r"https?://[^\s\"'<>)]+", raw)
            lattes = next((u for u in urls if "lattes" in u), "")
            group = next((u for u in urls if "dgp.cnpq" in u or "espelhogrupo" in u), "")
            interests = field(txt, "Research Interests")
            program = field(txt, "Postgraduate Program", "Graduate Program")
            add({"id": f"r{lid}", "type": "researcher", "name": name,
                 "institution": field(txt, "Institution"),
                 "state": loc_state.get(lid, ""),
                 "lat": lat, "lng": lng,
                 "topics": loc_topics.get(lid, []),
                 "interests": interests,
                 "links": {k: v for k, v in
                           {"lattes": lattes, "group": group, "program": program}.items() if v}})
            seen.add(("researcher", lid))

    # --- Research Groups (CNPq): info in tag description ---
    for t in by_menu.get(M_GROUPS, []):
        txt = strip_tags(t["description"])
        url = next((u for u in re.findall(r"https?://[^\s\"'<>)]+", t["description"]) if "cnpq" in u),
                   first_url(t["description"]))
        lat = lng = None
        for lid in t["related_locations"]:
            if lid in locs:
                lat, lng = coord(locs[lid])
                break
        add({"id": f"g{t['id']}", "type": "group",
             "name": field(txt, "Group Name") or t["name"],
             "institution": field(txt, "Institution"),
             "state": norm_state(field(txt, "State")),
             "lat": lat, "lng": lng, "topics": [],
             "leader": field(txt, "Leader"),
             "links": {"group": url} if url else {}})

    # --- Graduate Programs (CAPES): info in tag description ---
    for t in by_menu.get(M_PROGRAMS, []):
        txt = strip_tags(t["description"])
        lat = lng = None
        state = ""
        for lid in t["related_locations"]:
            if lid in locs:
                lat, lng = coord(locs[lid])
                state = loc_state.get(lid, "")
                break
        add({"id": f"p{t['id']}", "type": "program",
             "name": field(txt, "Program name", "Program Name") or t["name"],
             "institution": field(txt, "Institution"),
             "state": state, "lat": lat, "lng": lng, "topics": [], "links": {}})

    # --- R&D Centers: info in location description ---
    for t in by_menu.get(M_CENTERS, []):
        for lid in t["related_locations"]:
            loc = locs.get(lid)
            if not loc or ("center", lid) in seen:
                continue
            lat, lng = coord(loc)
            txt = strip_tags(loc["description"])
            add({"id": f"c{lid}", "type": "center",
                 "name": re.sub(r"\s*\([A-Z]{2}\)\s*$", "", t["name"]).strip() or loc["name"],
                 "institution": loc["name"],
                 "state": norm_state(t["name"]) or loc_state.get(lid, "") or norm_state(loc["name"]) or norm_state(txt),
                 "lat": lat, "lng": lng, "topics": [],
                 "interests": txt.split("\n")[0] if txt else "",
                 "links": {"url": first_url(loc["description"])} if first_url(loc["description"]) else {}})
            seen.add(("center", lid))

    # --- R&D Working Groups: info in location description ---
    for t in by_menu.get(M_WORKING_GROUPS, []):
        for lid in t["related_locations"]:
            loc = locs.get(lid)
            if not loc:
                continue
            lat, lng = coord(loc)
            txt = strip_tags(loc["description"])
            people = field(txt, "Principal Researcher")
            add({"id": f"w{t['id']}", "type": "working_group",
                 "name": field(txt, "Group Name") or t["name"],
                 "institution": field(txt, "Institution"),
                 "state": norm_state(field(txt, "State")) or loc_state.get(lid, ""),
                 "lat": lat, "lng": lng, "topics": [],
                 "leader": people, "project": field(txt, "Project"),
                 "links": {}})
            break  # one geo per working group

    # --- Publications (Productions + Articles): title in tag name; details in
    #     whichever of (location, tag) description is populated. ---
    for mid in (M_PRODUCTIONS, M_ARTICLES):
        for t in by_menu.get(mid, []):
            lid = next((x for x in t["related_locations"] if x in locs), None)
            if lid is None or ("pub", t["id"]) in seen:
                continue
            loc = locs[lid]
            lat, lng = coord(loc)
            txt = strip_tags(loc["description"]) or strip_tags(t["description"])
            add({"id": f"pub{t['id']}", "type": "publication",
                 "name": t["name"] or field(txt, "Production Title", "Production name"),
                 "institution": field(txt, "Institution"),
                 "state": norm_state(field(txt, "State")) or loc_state.get(lid, ""),
                 "lat": lat, "lng": lng, "topics": [],
                 "authors": field(txt, "Authors"),
                 "year": field(txt, "Year of Production", "Year"),
                 "links": {}})
            seen.add(("pub", t["id"]))

    # Drop records without coordinates (cannot place on the map).
    records = [r for r in records if r["lat"] is not None and r["lng"] is not None]

    type_counts = {}
    states = set()
    topics = set()
    for r in records:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1
        if r["state"]:
            states.add(r["state"])
        for tp in r.get("topics", []):
            topics.add(tp)

    out = {
        "generated_from": BASE,
        "counts": type_counts,
        "states": sorted(states),
        "topics": sorted(topics),
        "records": records,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    print("\nwrote", OUT)
    print("records:", len(records))
    for k, v in sorted(type_counts.items()):
        print(f"  {k}: {v}")
    print("states:", len(states), "| topics:", len(topics))


if __name__ == "__main__":
    main()
