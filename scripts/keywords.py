#!/usr/bin/env python3
"""Lightweight keyword extraction and word-cloud rendering for the SBSeg annals.

The annals data exposes only paper titles (no abstracts), so keywords are mined
from titles with a corpus-aware TF-IDF scheme:

  * Titles are tokenised into content words and short noun phrases (content
    words joined by a few connectors such as "de" / "of"). Pure function words
    and digits are dropped.
  * Each content word gets an inverse-document-frequency weight over the whole
    corpus, so ubiquitous domain words ("seguranca", "security") score low and
    distinctive themes ("malware", "blockchain") score high.
  * Per paper we keep the five highest-scoring, non-overlapping candidates.

The same module renders a dependency-free HTML word cloud (sized <button>s) so
both generators (fetch_sbseg.py and gen_pages.py) share one implementation.

No third-party dependencies: the site is static and vanilla by design.
"""
import html
import math
import re
import unicodedata

# --------------------------------------------------------------------------- #
# Stop words / connectors (PT + EN + ES function words)                        #
# --------------------------------------------------------------------------- #
# Connectors may sit *between* two content words to form a phrase
# ("deteccao de intrusao"); they never start or end a phrase and add 0 score.
# Kept deliberately small: only genitive/locative glue. Coordinators ("and",
# "e", "for") are excluded so unrelated concepts are not welded together.
CONNECTORS = {
    "de", "da", "do", "das", "dos", "sem", "of", "para", "em", "no", "na",
    "por", "com", "del", "la", "el", "en",
}

# Everything that must never appear as (part of) a keyword.
STOPWORDS = CONNECTORS | {
    # Portuguese
    "o", "os", "as", "um", "uma", "uns", "umas", "nos", "nas", "sob", "sobre",
    "ao", "aos", "que", "se", "ou", "como", "mais", "menos", "entre", "ate",
    "apos", "ante", "contra", "desde", "durante", "perante", "num", "numa",
    "pelo", "pela", "pelos", "pelas", "seu", "sua", "seus", "suas", "este",
    "esta", "esse", "essa", "isto", "isso", "aquele", "aquela", "ser", "sao",
    "foi", "ja", "nao", "dois", "duas", "tres", "uso", "via", "caso",
    "estudo", "estudos", "sua", "suas", "a", "o", "e",
    # English
    "the", "an", "and", "for", "to", "in", "on", "with", "by", "is", "are",
    "be", "been", "this", "that", "these", "those", "its", "their", "from",
    "at", "into", "over", "under", "through", "via", "using", "based",
    "toward", "towards", "between", "we", "our", "case", "study", "use",
    "uses",
    # Spanish
    "los", "las", "un", "una", "su", "sus", "con", "sin", "y",
    # Orphan fragments left by split idioms ("ad hoc"; "fio" stranded from
    # "sem fio" when the 2-word phrase cap flushes just before it). "ad" is
    # already dropped by MIN_LEN.
    "hoc", "fio",
}

# Words / sub-tokens kept whole even though they are short.
MIN_LEN = 3

TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def _fold(s):
    """Lowercase + strip accents (used for stop-word and key matching)."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower())
        if unicodedata.category(c) != "Mn"
    )


def _tokens(title):
    """Return [(surface_lower, folded, is_content)] for a title."""
    out = []
    for m in TOKEN_RE.findall(title):
        low = m.lower()
        fold = _fold(low)
        is_content = fold not in STOPWORDS and len(fold) >= MIN_LEN
        out.append((low, fold, is_content))
    return out


def _phrases(tokens, max_content=2):
    """Greedily group tokens into candidate phrases.

    A phrase is a run of content words optionally joined by single connectors,
    capped at ``max_content`` content words. Yields (display, content_keys):
    ``display`` keeps connectors for readability; ``content_keys`` is the tuple
    of folded content words used for scoring and de-duplication.
    """
    phrases = []
    cur_surface, cur_keys = [], []
    n = len(tokens)

    def flush():
        if cur_keys:
            phrases.append((" ".join(cur_surface), tuple(cur_keys)))

    i = 0
    while i < n:
        low, fold, is_content = tokens[i]
        if is_content:
            if len(cur_keys) >= max_content:
                flush()
                cur_surface, cur_keys = [], []
            cur_surface.append(low)
            cur_keys.append(fold)
        elif (fold in CONNECTORS and cur_keys and i + 1 < n
              and tokens[i + 1][2] and len(cur_keys) < max_content):
            cur_surface.append(low)  # connector kept only for display
        else:
            flush()
            cur_surface, cur_keys = [], []
        i += 1
    flush()
    return phrases


# --------------------------------------------------------------------------- #
# Corpus scoring                                                               #
# --------------------------------------------------------------------------- #
def build_index(titles):
    """Return a dict with document frequency and corpus size for scoring."""
    df = {}
    for title in titles:
        seen = {f for _, f, c in _tokens(title) if c}
        for w in seen:
            df[w] = df.get(w, 0) + 1
    return {"df": df, "N": len(titles)}


def _idf(word, index):
    df = index["df"].get(word, 0)
    return math.log((index["N"] + 1) / (df + 1)) + 1.0


def keywords_for(title, index, top=5):
    """Top ``top`` distinct keyword phrases for one title (display strings)."""
    cands = _phrases(_tokens(title))
    scored = []
    seen_display = set()
    for display, keys in cands:
        if not keys:
            continue
        score = sum(_idf(k, index) for k in keys) / math.sqrt(len(keys))
        scored.append((score, display, set(keys)))

    scored.sort(key=lambda t: t[0], reverse=True)

    chosen, used = [], set()
    for score, display, keyset in scored:
        if display in seen_display or keyset & used:
            continue
        seen_display.add(display)
        used |= keyset
        chosen.append(display)
        if len(chosen) >= top:
            break
    return chosen


# --------------------------------------------------------------------------- #
# Word-cloud rendering (static HTML, no JS dependency to build)               #
# --------------------------------------------------------------------------- #
def aggregate(papers_keywords):
    """Count keyword occurrences across an iterable of keyword lists."""
    counts = {}
    for kws in papers_keywords:
        for kw in kws:
            counts[kw] = counts.get(kw, 0) + 1
    return counts


def top_counts(counts, limit):
    """Return [(keyword, count)] sorted by count desc then alpha, capped."""
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:limit]


def cloud_html(counts, cloud_id="pubCloud", limit=80, indent="      "):
    """Render a word cloud as sized <button>s (7 size buckets by frequency).

    Each button carries ``data-kw`` so site.js can turn a click into a search.
    """
    items = top_counts(counts, limit)
    if not items:
        return ""
    freqs = [c for _, c in items]
    lo, hi = min(freqs), max(freqs)
    span = (hi - lo) or 1
    out = [f'{indent}<div class="wordcloud" id="{html.escape(cloud_id, quote=True)}">']
    for kw, c in items:
        bucket = 1 + round((c - lo) / span * 6)  # 1..7
        out.append(
            f'{indent}  <button type="button" class="wc-word wc-s{bucket}" '
            f'data-kw="{html.escape(kw, quote=True)}" '
            f'title="{c}">{html.escape(kw)}</button>'
        )
    out.append(f"{indent}</div>")
    return "\n".join(out)
