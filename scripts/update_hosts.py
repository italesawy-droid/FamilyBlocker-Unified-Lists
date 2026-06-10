from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

from common import (
    ROOT, category_ids, dedupe_sorted, fetch_url, make_hosts_lines,
    normalize_domain, parse_domains_from_text, read_simple_allowlist, read_tsv,
    utc_now_iso, write_lines, write_text
)

def read_manual_domains() -> Dict[str, Set[str]]:
    by_cat: Dict[str, Set[str]] = defaultdict(set)
    for row in read_tsv(ROOT / "data" / "manual" / "domains.tsv", 2):
        cat, domain = row[0], row[1]
        d = normalize_domain(domain)
        if cat and d:
            by_cat[cat].add(d)
    return by_cat

def main() -> None:
    cats = category_ids()
    valid_cats = set(cats)
    allow = {normalize_domain(x) for x in read_simple_allowlist(ROOT / "data" / "allowlists" / "domains.txt")}
    allow = {x for x in allow if x}

    domains_by_cat: Dict[str, Set[str]] = {c: set() for c in cats}
    report_rows: List[str] = ["generated_utc\tsource_id\tcategory_id\tenabled\tstatus\tcount\turl_or_note"]

    for row in read_tsv(ROOT / "config" / "hosts_sources.tsv", 5):
        source_id, category_id, enabled, url, note = row[0], row[1], row[2], row[3], row[4]
        if category_id not in valid_cats:
            report_rows.append(f"{utc_now_iso()}\t{source_id}\t{category_id}\t{enabled}\tskipped_unknown_category\t0\t{note}")
            continue
        if enabled.strip() not in {"1", "true", "TRUE", "yes", "YES"}:
            report_rows.append(f"{utc_now_iso()}\t{source_id}\t{category_id}\t{enabled}\tdisabled\t0\t{url}")
            continue
        ok, text, error = fetch_url(url)
        if not ok:
            report_rows.append(f"{utc_now_iso()}\t{source_id}\t{category_id}\t{enabled}\tfetch_failed\t0\t{error}")
            continue
        domains = [d for d in parse_domains_from_text(text) if d and d not in allow]
        for d in domains:
            domains_by_cat[category_id].add(d)
        report_rows.append(f"{utc_now_iso()}\t{source_id}\t{category_id}\t{enabled}\tok\t{len(set(domains))}\t{url}")

    for cat, domains in read_manual_domains().items():
        if cat not in valid_cats:
            report_rows.append(f"{utc_now_iso()}\tmanual_domains\t{cat}\t1\tskipped_unknown_category\t0\tdata/manual/domains.tsv")
            continue
        clean = {d for d in domains if d and d not in allow}
        domains_by_cat[cat].update(clean)
        report_rows.append(f"{utc_now_iso()}\tmanual_domains\t{cat}\t1\tok\t{len(clean)}\tdata/manual/domains.tsv")

    all_domains: Set[str] = set()
    for cat in cats:
        domains = dedupe_sorted(domains_by_cat.get(cat, set()))
        all_domains.update(domains)
        write_lines(ROOT / "generated" / "domains" / "by_category" / f"{cat}.txt", domains,
                    header=f"# FamilyBlockerUnified domains: {cat}")
        write_lines(ROOT / "generated" / "hosts" / "by_category" / f"{cat}.hosts", make_hosts_lines(domains),
                    header=f"# FamilyBlockerUnified hosts: {cat}")
        write_lines(ROOT / "public" / "domains" / f"{cat}.txt", domains)
        write_lines(ROOT / "public" / "hosts" / f"{cat}.hosts", make_hosts_lines(domains))

    all_domains_sorted = dedupe_sorted(all_domains)
    write_lines(ROOT / "generated" / "domains" / "all.txt", all_domains_sorted, header="# FamilyBlockerUnified domains: all")
    write_lines(ROOT / "generated" / "hosts" / "all.hosts", make_hosts_lines(all_domains_sorted), header="# FamilyBlockerUnified hosts: all")
    write_lines(ROOT / "public" / "domains_all.txt", all_domains_sorted)
    write_lines(ROOT / "public" / "hosts_all.hosts", make_hosts_lines(all_domains_sorted))

    # Backward-compatible root outputs expected by the older hosts project.
    write_lines(ROOT / "familyblocker_domains.txt", all_domains_sorted)
    write_lines(ROOT / "familyblocker_hosts.txt", make_hosts_lines(all_domains_sorted))
    write_text(ROOT / "familyblocker_sources_report.tsv", "\n".join(report_rows) + "\n")

if __name__ == "__main__":
    main()
