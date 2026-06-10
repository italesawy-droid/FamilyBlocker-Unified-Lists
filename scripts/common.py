from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "FamilyBlockerUnified/1.0 (+https://github.com/)"

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$",
    re.IGNORECASE,
)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def write_lines(path: Path, lines: Iterable[str], header: str | None = None) -> None:
    clean = []
    if header:
        clean.append(header.rstrip("\n"))
    for line in lines:
        line = str(line).strip()
        if line:
            clean.append(line)
    write_text(path, "\n".join(clean) + ("\n" if clean else ""))

def load_json(path: Path) -> dict:
    return json.loads(read_text(path))

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def strip_comment(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    if line.startswith("#") or line.startswith("//"):
        return ""
    # Hosts files may contain inline comments.
    if " #" in line:
        line = line.split(" #", 1)[0].strip()
    return line

def normalize_domain(value: str) -> str:
    value = strip_comment(value).strip().lower()
    if not value:
        return ""
    value = value.replace("\ufeff", "")
    value = re.sub(r"^https?://", "", value)
    value = value.split("/", 1)[0]
    value = value.split(":", 1)[0]
    value = value.strip(".")
    if value.startswith("www."):
        # Keep both forms only when source provides both. For generated blocking, bare domain is enough.
        value = value[4:]
    if value in {"localhost", "local", "broadcasthost"}:
        return ""
    if value.endswith(".local") or value.endswith(".lan"):
        return ""
    if DOMAIN_RE.match(value):
        return value
    return ""

def parse_domains_from_text(text: str) -> List[str]:
    out: List[str] = []
    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line:
            continue
        parts = line.split()
        candidates = []
        if len(parts) >= 2 and re.match(r"^(0\.0\.0\.0|127\.0\.0\.1|::1)$", parts[0]):
            candidates.append(parts[1])
        else:
            candidates.extend(parts[:1])
        for c in candidates:
            d = normalize_domain(c)
            if d:
                out.append(d)
    return out

def fetch_url(url: str, timeout: int = 60) -> Tuple[bool, str, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        return True, raw.decode("utf-8", errors="replace"), ""
    except Exception as exc:
        return False, "", f"{type(exc).__name__}: {exc}"

def read_simple_allowlist(path: Path) -> set[str]:
    vals = set()
    for line in read_text(path).splitlines():
        line = strip_comment(line)
        if line:
            vals.add(line.strip().lower())
    return vals

def read_tsv(path: Path, expected_min_cols: int = 1) -> List[List[str]]:
    rows: List[List[str]] = []
    text = read_text(path)
    for row in csv.reader(text.splitlines(), delimiter="\t"):
        if not row:
            continue
        if row[0].strip().startswith("#"):
            continue
        row = [c.strip() for c in row]
        if len(row) >= expected_min_cols and any(row):
            rows.append(row)
    return rows

def category_ids() -> List[str]:
    cfg = load_json(ROOT / "config" / "categories.json")
    return [c["id"] for c in cfg.get("categories", [])]

def category_map() -> Dict[str, dict]:
    cfg = load_json(ROOT / "config" / "categories.json")
    return {c["id"]: c for c in cfg.get("categories", [])}

def dedupe_sorted(values: Iterable[str]) -> List[str]:
    return sorted({v.strip() for v in values if str(v).strip()}, key=lambda x: x.lower())

def make_hosts_lines(domains: Iterable[str]) -> List[str]:
    return [f"0.0.0.0 {d}" for d in dedupe_sorted(domains)]

def safe_count(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    for line in read_text(path).splitlines():
        s = strip_comment(line)
        if s:
            n += 1
    return n
