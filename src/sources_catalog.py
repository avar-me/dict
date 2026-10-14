#!/usr/bin/env python3
"""Fetch sources.avar.me's catalog and list which dictionaries to convert.

Deliberately excludes the raw pre-merge av-ru components (av-ru.2006,
av-ru.avar.me) -- av-ru itself is already their merged, canonical form.
"""
from __future__ import annotations

import json
import os
import urllib.request

SOURCES_BASE = os.environ.get("SOURCES_BASE", "https://sources.avar.me")
EXCLUDE_IDS = {"av-ru.2006", "av-ru.avar.me"}


def fetch_catalog() -> dict:
    url = f"{SOURCES_BASE}/sources.json"
    req = urllib.request.Request(url, headers={"User-Agent": "avar-me-dict-builder/1.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def dictionary_sources(catalog: dict) -> list[dict]:
    return [
        s for s in catalog["sources"]
        if s.get("kind") == "dictionary" and s["id"] not in EXCLUDE_IDS
    ]


if __name__ == "__main__":
    cat = fetch_catalog()
    for s in dictionary_sources(cat):
        print(s["id"], "|", s["title"], "|", s.get("status"))
