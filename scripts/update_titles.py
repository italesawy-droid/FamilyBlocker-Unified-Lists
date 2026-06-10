from __future__ import annotations

import json
import urllib.parse
from collections import defaultdict
from typing import Dict, Iterable, List, Set, Tuple

from common import (
    ROOT, category_ids, dedupe_sorted, fetch_url, read_simple_allowlist,
    read_tsv, strip_comment, utc_now_iso, write_lines, write_text
)

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

def clean_title(value: str) -> str:
    value = value.replace("\ufeff", "").strip()
    if not value or value.startswith("#"):
        return ""
    # Avoid very short one-word titles because they cause many false positives in URL policy mode.
    if len(value) < 3:
        return ""
    return value

def wikidata_titles_for_genre(qid: str, limit: int = 5000) -> Tuple[bool, List[str], str]:
    # Films whose genre is the target genre or a subclass of it.
    query = f"""
SELECT DISTINCT ?item ?itemLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q11424.
  ?item wdt:P136/wdt:P279* wd:{qid}.
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ar". }}
}}
LIMIT {limit}
"""
    params = urllib.parse.urlencode({"query": query, "format": "json"})
    ok, text, error = fetch_url(WIKIDATA_ENDPOINT + "?" + params, timeout=90)
    if not ok:
        return False, [], error
    try:
        data = json.loads(text)
        titles = []
        for b in data.get("results", {}).get("bindings", []):
            label = b.get("itemLabel", {}).get("value", "")
            t = clean_title(label)
            if t and not t.startswith("Q"):
                titles.append(t)
        return True, dedupe_sorted(titles), ""
    except Exception as exc:
        return False, [], f"{type(exc).__name__}: {exc}"

def read_manual_titles() -> Dict[str, Set[str]]:
    by_cat: Dict[str, Set[str]] = defaultdict(set)
    for row in read_tsv(ROOT / "data" / "manual" / "titles.tsv", 2):
        cat, title = row[0], row[1]
        t = clean_title(title)
        if cat and t:
            by_cat[cat].add(t)
    return by_cat

def read_manual_keywords() -> Dict[str, Set[str]]:
    by_cat: Dict[str, Set[str]] = defaultdict(set)
    for row in read_tsv(ROOT / "data" / "manual" / "keywords.tsv", 2):
        cat, kw = row[0], row[1]
        k = clean_title(kw)
        if cat and k:
            by_cat[cat].add(k)
    return by_cat

def pattern_from_item(item: str) -> str:
    p = item.strip()
    replacements = {
        " ": "*",
        ":": "*",
        "/": "*",
        "\\": "*",
        "?": "*",
        "&": "*",
        "+": "*",
        "’": "*",
        "'": "*",
        ".": "*",
        ",": "*",
        "(": "*",
        ")": "*",
        "[": "*",
        "]": "*",
    }
    for a, b in replacements.items():
        p = p.replace(a, b)
    while "**" in p:
        p = p.replace("**", "*")
    return p.strip("*")

def url_patterns(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    for item in items:
        p = pattern_from_item(item)
        if not p:
            continue
        out.extend([
            f"*://*/*{p}*",
            f"*://*.google.*/*q=*{p}*",
            f"*://*.bing.com/search*{p}*",
            f"*://*.youtube.com/results*search_query=*{p}*",
            f"*://*.duckduckgo.com/*q=*{p}*",
        ])
    return dedupe_sorted(out)

def main() -> None:
    cats = category_ids()
    valid_cats = set(cats)
    allow_titles = {clean_title(x).lower() for x in read_simple_allowlist(ROOT / "data" / "allowlists" / "titles.txt")}
    allow_titles = {x for x in allow_titles if x}

    titles_by_cat: Dict[str, Set[str]] = {c: set() for c in cats}
    keywords_by_cat: Dict[str, Set[str]] = {c: set() for c in cats}
    report_rows: List[str] = ["generated_utc\tsource_id\tcategory_id\tenabled\tstatus\tcount\tnote"]
    by_category_rows: List[str] = ["category_id\tsource\ttitle"]

    for row in read_tsv(ROOT / "config" / "title_genres_enabled.tsv", 5):
        qid, category_id, enabled, label_en, label_ar = row[0], row[1], row[2], row[3], row[4]
        if category_id not in valid_cats:
            report_rows.append(f"{utc_now_iso()}\t{qid}\t{category_id}\t{enabled}\tskipped_unknown_category\t0\t{label_en}")
            continue
        if enabled.strip() not in {"1", "true", "TRUE", "yes", "YES"}:
            report_rows.append(f"{utc_now_iso()}\t{qid}\t{category_id}\t{enabled}\tdisabled\t0\t{label_en}")
            continue
        ok, titles, error = wikidata_titles_for_genre(qid)
        if not ok:
            report_rows.append(f"{utc_now_iso()}\t{qid}\t{category_id}\t{enabled}\tfetch_failed\t0\t{error}")
            continue
        clean = [t for t in titles if t.lower() not in allow_titles]
        for t in clean:
            titles_by_cat[category_id].add(t)
            by_category_rows.append(f"{category_id}\twikidata:{qid}\t{t}")
        report_rows.append(f"{utc_now_iso()}\t{qid}\t{category_id}\t{enabled}\tok\t{len(set(clean))}\t{label_en}")

    for cat, titles in read_manual_titles().items():
        if cat not in valid_cats:
            report_rows.append(f"{utc_now_iso()}\tmanual_titles\t{cat}\t1\tskipped_unknown_category\t0\tdata/manual/titles.tsv")
            continue
        clean = {t for t in titles if t.lower() not in allow_titles}
        titles_by_cat[cat].update(clean)
        for t in clean:
            by_category_rows.append(f"{cat}\tmanual\t{t}")
        report_rows.append(f"{utc_now_iso()}\tmanual_titles\t{cat}\t1\tok\t{len(clean)}\tdata/manual/titles.tsv")

    for cat, keywords in read_manual_keywords().items():
        if cat not in valid_cats:
            report_rows.append(f"{utc_now_iso()}\tmanual_keywords\t{cat}\t1\tskipped_unknown_category\t0\tdata/manual/keywords.tsv")
            continue
        keywords_by_cat[cat].update(keywords)
        report_rows.append(f"{utc_now_iso()}\tmanual_keywords\t{cat}\t1\tok\t{len(keywords)}\tdata/manual/keywords.tsv")

    all_titles: Set[str] = set()
    all_keywords: Set[str] = set()
    all_patterns: Set[str] = set()

    for cat in cats:
        titles = dedupe_sorted(titles_by_cat.get(cat, set()))
        keywords = dedupe_sorted(keywords_by_cat.get(cat, set()))
        patterns = url_patterns(list(titles) + list(keywords))
        all_titles.update(titles)
        all_keywords.update(keywords)
        all_patterns.update(patterns)

        write_lines(ROOT / "generated" / "titles" / "by_category" / f"{cat}.txt", titles,
                    header=f"# FamilyBlockerUnified titles: {cat}")
        write_lines(ROOT / "generated" / "keywords" / "by_category" / f"{cat}.txt", keywords,
                    header=f"# FamilyBlockerUnified keywords: {cat}")
        write_lines(ROOT / "generated" / "url_patterns" / "by_category" / f"{cat}.txt", patterns,
                    header=f"# FamilyBlockerUnified URL patterns: {cat}")

        write_lines(ROOT / "public" / "titles" / f"{cat}.txt", titles)
        write_lines(ROOT / "public" / "keywords" / f"{cat}.txt", keywords)
        write_lines(ROOT / "public" / "url_patterns" / f"{cat}.txt", patterns)

    all_titles_sorted = dedupe_sorted(all_titles)
    all_keywords_sorted = dedupe_sorted(all_keywords)
    all_patterns_sorted = dedupe_sorted(all_patterns)

    write_lines(ROOT / "generated" / "titles" / "all.txt", all_titles_sorted, header="# FamilyBlockerUnified titles: all")
    write_lines(ROOT / "generated" / "keywords" / "all.txt", all_keywords_sorted, header="# FamilyBlockerUnified keywords: all")
    write_lines(ROOT / "generated" / "url_patterns" / "all.txt", all_patterns_sorted, header="# FamilyBlockerUnified URL patterns: all")

    write_lines(ROOT / "public" / "titles_all.txt", all_titles_sorted)
    write_lines(ROOT / "public" / "keywords_all.txt", all_keywords_sorted)
    write_lines(ROOT / "public" / "url_patterns_all.txt", all_patterns_sorted)

    # Backward-compatible root outputs expected by earlier FamilyBlocker work.
    write_lines(ROOT / "blocked_titles.txt", all_titles_sorted)
    write_lines(ROOT / "blocked_keywords.txt", all_keywords_sorted)
    write_lines(ROOT / "generated_url_patterns.txt", all_patterns_sorted)
    write_text(ROOT / "blocked_titles_by_category.tsv", "\n".join(by_category_rows) + "\n")
    write_text(ROOT / "blocked_titles_sources_report.tsv", "\n".join(report_rows) + "\n")

if __name__ == "__main__":
    main()
