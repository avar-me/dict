#!/usr/bin/env python3
"""Generate docs/index.html: a simple static catalog page listing every
(dictionary source, format) zip produced by convert.py.

Reads the manifest written by build.sh (JSON: {source_id: {title, formats:
[{label, filename, size}]}}) rather than re-deriving anything, so this
script has no pyglossary dependency and stays trivial to re-template.
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


PAGE_TEMPLATE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>dict.avar.me — словари для офлайн-приложений</title>
<meta name="description" content="Словари avar.me, собранные в DSL, StarDict, EPUB, Kobo, Babylon BGL и ещё полтора десятка форматов для офлайн-словарных приложений.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Literata:wght@400;600;700&family=Onest:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<header class="hero">
  <div class="hero-inner">
    <p class="hero-tag"><a href="https://sources.avar.me">sources.avar.me</a> / dict</p>
    <h1>dict<span class="dot">.</span>avar.me</h1>
    <p class="hero-lead">Словари avar.me, пересобранные во все известные офлайн-форматы:
      DSL, StarDict, EPUB, Mobi, Kobo, Babylon (.BGL), Apple Dictionary и ещё полтора
      десятка. Собирается автоматически из <a href="https://sources.avar.me">sources.avar.me</a>.</p>
  </div>
</header>
<main class="container">
  <p class="built-note">Собрано: {built_at} · {n_sources} словарей × {n_formats} форматов</p>
  {sections}
  <section class="how">
    <h2>Как этим пользоваться</h2>
    <ul>
      <li><strong>GoldenDict / GoldenDict-NG</strong> — StarDict, DSL, Babylon BGL, XDXF: распакуйте zip в папку словарей.</li>
      <li><strong>Kobo</strong> — формат Kobo Dictfile/Dictionary, скопируйте на устройство в .kobo/dict/.</li>
      <li><strong>Kindle</strong> — Mobi (сырые файлы без kindlegen — соберите через Calibre при необходимости).</li>
      <li><strong>Apple Dictionary (Dictionary.app)</strong> — исходник + Makefile, нужен Dictionary Development Kit от Apple для финальной компиляции.</li>
      <li><strong>Любое приложение, импортирующее tab-separated списки</strong> — формат Tabfile.</li>
    </ul>
    <p class="muted">Эти форматы — производные; источник правды — <a href="https://sources.avar.me">sources.avar.me</a>.
      Нашли ошибку в переводе? Пишите в <a href="https://t.me/avarme_chat">@avarme_chat</a> — правки попадут и сюда
      при следующей пересборке.</p>
  </section>
</main>
<footer class="site-footer">
  <p><a href="https://github.com/avar-me/dict">github.com/avar-me/dict</a> ·
     данные из <a href="https://sources.avar.me">sources.avar.me</a></p>
</footer>
</body>
</html>
"""


def render_source_section(source_id: str, info: dict) -> str:
    rows = []
    for f in sorted(info["formats"], key=lambda x: x["label"]):
        rows.append(
            f'<tr><td>{esc(f["label"])}</td>'
            f'<td><a href="{esc(source_id)}/{esc(f["filename"])}" download>'
            f'<code>{esc(f["filename"])}</code></a></td>'
            f'<td>{human_size(f["size"])}</td>'
            f'<td><details><summary><code>{f["sha256"][:12]}…</code></summary>'
            f'<code class="full-checksum">{f["sha256"]}</code></details></td></tr>'
        )
    return f"""<section class="catalog" id="{esc(source_id)}">
    <h2 class="section-title">{esc(info["title"])}<span class="section-count">{len(info["formats"])}</span></h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Формат</th><th>Файл</th><th>Размер</th><th>SHA-256</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </section>"""


def main() -> None:
    manifest_path = ROOT / "docs" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    sections = "".join(
        render_source_section(sid, info) for sid, info in manifest["sources"].items()
    )
    n_formats = len({f["label"] for info in manifest["sources"].values() for f in info["formats"]})

    html_out = PAGE_TEMPLATE.format(
        built_at=esc(manifest["built_at"]),
        n_sources=len(manifest["sources"]),
        n_formats=n_formats,
        sections=sections,
    )
    (ROOT / "docs" / "index.html").write_text(html_out, encoding="utf-8")
    print(f"wrote docs/index.html ({len(manifest['sources'])} sources, {n_formats} formats)")


if __name__ == "__main__":
    main()
