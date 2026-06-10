# FamilyBlockerUnified

Unified GitHub helper repository for a Windows family protection app.

This repository combines two previous lines of work:

1. Domain/hosts blocking for adult websites.
2. Movie/title/keyword blocking by category for browser URL policy use.

The Windows application should not hard-code lists. It should download `familyblocker_manifest.json`, show categories as checkboxes, and then download only the selected category files.

## Main generated files

- `familyblocker_manifest.json` — main manifest for the Windows app.
- `familyblocker_categories.json` — slim categories manifest for UI.
- `public/hosts/*.hosts` — per-category hosts files.
- `public/domains/*.txt` — per-category domain files.
- `public/titles/*.txt` — per-category title files.
- `public/keywords/*.txt` — per-category keyword files.
- `public/url_patterns/*.txt` — per-category Chrome/Edge URLBlocklist patterns.
- `familyblocker_hosts.txt`, `familyblocker_domains.txt`, `blocked_titles.txt`, `blocked_keywords.txt` — backward-compatible root outputs.

## Configuration

- Categories: `config/categories.json`
- Hosts sources: `config/hosts_sources.tsv`
- Wikidata title genres: `config/title_genres_enabled.tsv`
- Manual domains: `data/manual/domains.tsv`
- Manual titles: `data/manual/titles.tsv`
- Manual keywords: `data/manual/keywords.tsv`
- Domain allowlist: `data/allowlists/domains.txt`
- Title allowlist: `data/allowlists/titles.txt`

## Update

Run manually:

```bash
python scripts/update_all.py
```

Or use GitHub Actions:

`Actions` → `Update FamilyBlocker Unified Lists` → `Run workflow`.

## Windows app rule

The Windows app should edit the hosts file only inside its own block, for example:

```text
# BEGIN FAMILYBLOCKERUNIFIED
0.0.0.0 example.com
# END FAMILYBLOCKERUNIFIED
```

It must keep existing hosts lines outside that block unchanged and create a backup before any hosts change.
