#!/usr/bin/env python3
"""Orchestrate the full build: download every dictionary source from
sources.avar.me, convert each into every dictionary-app format, write
docs/manifest.json, then hand off to build_site.py for the HTML page.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from convert import convert_source  # noqa: E402
from sources_catalog import fetch_catalog, dictionary_sources  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "avar-me-dict-builder/1.0"})
    with urllib.request.urlopen(req) as resp, dest.open("wb") as f:
        shutil.copyfileobj(resp, f)


def sha256_of(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main() -> None:
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)
    shutil.copy2(Path(__file__).parent / "templates" / "styles.css", DOCS / "styles.css")

    catalog = fetch_catalog()
    sources = dictionary_sources(catalog)
    print(f"=== {len(sources)} dictionary sources to convert ===")

    manifest: dict = {
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "sources": {},
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for src in sources:
            sid = src["id"]
            print(f"\n--- {sid} ({src['title']}) ---")
            jsonl_path = tmp_path / f"{sid}.jsonl"
            try:
                download(f"https://sources.avar.me/{src['data_path']}", jsonl_path)
            except Exception as e:
                print(f"  !! download failed: {e}", file=sys.stderr)
                continue

            lang_from = src.get("language_from", "")
            lang_to = src.get("language_to", "")
            out_dir = DOCS / sid
            results = convert_source(
                jsonl_path,
                sid,
                src["title"],
                src.get("description", src["title"]),
                lang_from,
                lang_to,
                out_dir,
            )
            if not results:
                print(f"  !! no formats succeeded for {sid}", file=sys.stderr)
                continue

            manifest["sources"][sid] = {
                "title": src["title"],
                "formats": [
                    {
                        "label": label,
                        "filename": path.name,
                        "size": path.stat().st_size,
                        "sha256": sha256_of(path),
                    }
                    for label, path in results
                ],
            }

    (DOCS / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nwrote docs/manifest.json ({len(manifest['sources'])} sources)")


if __name__ == "__main__":
    main()
