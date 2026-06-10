from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from common import ROOT, category_map, safe_count, sha256_file, utc_now_iso, write_text

def file_info(rel: str) -> dict:
    p = ROOT / rel
    return {
        "path": rel,
        "exists": p.exists(),
        "bytes": p.stat().st_size if p.exists() else 0,
        "sha256": sha256_file(p) if p.exists() else None,
        "items": safe_count(p) if p.exists() else 0,
    }

def main() -> None:
    cats = category_map()
    categories = []
    for cat_id, meta in cats.items():
        files = {
            "domains": f"public/domains/{cat_id}.txt",
            "hosts": f"public/hosts/{cat_id}.hosts",
            "titles": f"public/titles/{cat_id}.txt",
            "keywords": f"public/keywords/{cat_id}.txt",
            "url_patterns": f"public/url_patterns/{cat_id}.txt",
        }
        categories.append({
            "id": cat_id,
            "label_ar": meta.get("label_ar", cat_id),
            "label_en": meta.get("label_en", cat_id),
            "description_ar": meta.get("description_ar", ""),
            "default_enabled": bool(meta.get("default_enabled", False)),
            "risk_level": meta.get("risk_level", ""),
            "content_types": meta.get("content_types", []),
            "files": {k: file_info(v) for k, v in files.items()},
        })

    manifest = {
        "schema_version": 1,
        "project": "FamilyBlockerUnified",
        "generated_utc": utc_now_iso(),
        "client_note_ar": "استخدم هذا الملف في برنامج ويندوز لعرض التصنيفات كـ CheckBox ثم تحميل الملفات النسبية المطلوبة فقط.",
        "paths_are_relative_to_repo_root": True,
        "all_files": {
            "domains": file_info("public/domains_all.txt"),
            "hosts": file_info("public/hosts_all.hosts"),
            "titles": file_info("public/titles_all.txt"),
            "keywords": file_info("public/keywords_all.txt"),
            "url_patterns": file_info("public/url_patterns_all.txt"),
        },
        "categories": categories,
        "reports": {
            "hosts_sources": file_info("familyblocker_sources_report.tsv"),
            "titles_sources": file_info("blocked_titles_sources_report.tsv"),
            "titles_by_category": file_info("blocked_titles_by_category.tsv"),
        },
        "backward_compatible_root_outputs": {
            "familyblocker_domains": file_info("familyblocker_domains.txt"),
            "familyblocker_hosts": file_info("familyblocker_hosts.txt"),
            "blocked_titles": file_info("blocked_titles.txt"),
            "blocked_keywords": file_info("blocked_keywords.txt"),
            "generated_url_patterns": file_info("generated_url_patterns.txt"),
        },
    }
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    write_text(ROOT / "familyblocker_manifest.json", text + "\n")

    # Smaller file for quick category discovery by Windows UI.
    slim = {
        "schema_version": 1,
        "generated_utc": manifest["generated_utc"],
        "categories": [
            {
                "id": c["id"],
                "label_ar": c["label_ar"],
                "label_en": c["label_en"],
                "default_enabled": c["default_enabled"],
                "content_types": c["content_types"],
                "files": {k: v["path"] for k, v in c["files"].items()},
            }
            for c in categories
        ],
    }
    write_text(ROOT / "familyblocker_categories.json", json.dumps(slim, ensure_ascii=False, indent=2) + "\n")

if __name__ == "__main__":
    main()
