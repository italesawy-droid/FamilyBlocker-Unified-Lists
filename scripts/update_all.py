from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from update_hosts import main as update_hosts_main
from update_titles import main as update_titles_main
from build_manifest import main as build_manifest_main

def main() -> None:
    update_hosts_main()
    update_titles_main()
    build_manifest_main()
    print("FamilyBlockerUnified lists generated.")

if __name__ == "__main__":
    main()
