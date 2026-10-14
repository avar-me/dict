#!/usr/bin/env python3
"""Convert one source dictionary (av-ru.jsonl-shaped jsonl) into every
dictionary-app format we can produce.

Formats come from two places:
  1. Every write-capable pyglossary plugin (discovered dynamically, so a
     pyglossary upgrade that adds a new format gets picked up for free).
  2. DSL (ABBYY Lingvo) -- pyglossary can only *read* DSL, not write it,
     so we hand-roll a minimal DSL writer here.

Each (source, format) pair is zipped into one file under OUT_DIR, so the
site has one uniform "download" link per format regardless of whether the
underlying format is a single file or a directory of files.
"""
from __future__ import annotations

import html as htmllib
import json
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

from pyglossary.glossary_v2 import Glossary

FONTS_DIR = Path(__file__).resolve().parent / "fonts"

# Formats that are not real distributable dictionary-app formats (data
# interchange, internal pyglossary test/cache formats, or redundant with
# a format we already produce). Everything else pyglossary can write, we
# attempt.
SKIP_FORMATS = {
    "Csv", "Json", "Sql", "DiktJson", "GettextPo", "Info",  # data interchange, not dictionary apps
    "CrawlerDir",  # internal web-crawl cache, not a distributable format
    "Edlin",  # MS-DOS line editor export, not a dictionary format
    "DictOrgSource",  # dictfmt source; DictOrg below already gives the compiled form
    "StardictMergeSyns",  # same as Stardict with synonyms merged; redundant
}


def load_entries(path: Path) -> list[dict]:
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def headword(entry: dict) -> str:
    return entry.get("word") or entry.get("phrase") or ""


def html_escape(text: str | None) -> str:
    return htmllib.escape(text or "")


def render_definition_html(entry: dict) -> str:
    """Generic HTML rendering: handles both the word-dictionary schema
    (av-ru, ru-av, av-en, ...) and the phraseological schema
    (phrase-av-ru: senses carry `translation`/`literal` instead of `text`,
    examples carry `author`/`source` instead of `labels`/`comment`).
    """
    parts = []
    meta_bits = []
    if entry.get("pos"):
        meta_bits.append(entry["pos"])
    if entry.get("form") and entry["form"] != "—":
        meta_bits.append(entry["form"])
    if meta_bits:
        parts.append(f'<p><i>{html_escape(", ".join(meta_bits))}</i></p>')

    forms = entry.get("forms") or []
    if len(forms) > 1:
        parts.append(f'<p><i>формы:</i> {html_escape(", ".join(forms))}</p>')
    gforms = entry.get("gender_forms") or []
    if gforms:
        parts.append(f'<p><i>формы по классам:</i> {html_escape(", ".join(gforms))}</p>')
    variants = entry.get("variants") or []
    if variants:
        parts.append(f'<p><i>варианты:</i> {html_escape(", ".join(variants))}</p>')

    senses = entry.get("senses") or []
    multi = len(senses) > 1
    parts.append("<ol>" if multi else "<div>")
    tag = "li" if multi else "p"
    for sense in senses:
        text = sense.get("text") or sense.get("translation") or ""
        precomment = sense.get("precomment")
        pre_str = f"<i>{html_escape(precomment)}</i> " if precomment else ""
        labels = sense.get("labels") or []
        label_str = f' <i>({html_escape(", ".join(labels))})</i>' if labels else ""
        comment = sense.get("comment")
        comment_str = (
            f' <i>{html_escape(comment)}</i>'
            if comment and sense.get("comment_lang") != "av"
            else ""
        )
        literal = sense.get("literal")
        literal_str = f' <i>букв.: {html_escape(literal)}</i>' if literal else ""
        parts.append(f"<{tag}>{pre_str}<b>{html_escape(text)}</b>{label_str}{comment_str}{literal_str}")
        examples = sense.get("examples") or entry.get("examples") or []
        if examples:
            parts.append("<ul>")
            for ex in examples:
                av = html_escape(ex.get("av", ""))
                ru = html_escape(ex.get("ru", ""))
                tail_bits = []
                if ex.get("comment"):
                    tail_bits.append(html_escape(ex["comment"]))
                if ex.get("author"):
                    tail_bits.append(html_escape(ex["author"]))
                if ex.get("source"):
                    tail_bits.append(html_escape(ex["source"]))
                tail = f" <i>({', '.join(tail_bits)})</i>" if tail_bits else ""
                parts.append(f"<li>{av} — {ru}{tail}</li>")
            parts.append("</ul>")
        parts.append(f"</{tag}>")
    parts.append("</ol>" if multi else "</div>")

    see_also = entry.get("see_also") or []
    if see_also:
        refs = ", ".join(html_escape(sa["target"]) for sa in see_also)
        parts.append(f'<p><i>см. также:</i> {refs}</p>')

    return "".join(parts)


# ---------- DSL (ABBYY Lingvo) -- pyglossary can read but not write it ----------

def dsl_escape(text: str | None) -> str:
    if not text:
        return ""
    return (
        text.replace("\\", "\\\\")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("{", "\\{")
        .replace("}", "\\}")
    )


def render_definition_dsl(entry: dict) -> str:
    lines = []
    meta_bits = []
    if entry.get("pos"):
        meta_bits.append(entry["pos"])
    if entry.get("form") and entry["form"] != "—":
        meta_bits.append(entry["form"])
    if meta_bits:
        lines.append(f'[m1][i]{dsl_escape(", ".join(meta_bits))}[/i][/m1]')

    forms = entry.get("forms") or []
    if len(forms) > 1:
        lines.append(f'[m1][i]формы:[/i] {dsl_escape(", ".join(forms))}[/m1]')

    senses = entry.get("senses") or []
    multi = len(senses) > 1
    for i, sense in enumerate(senses, 1):
        prefix = f"{i}. " if multi else ""
        bold = f"[b]{prefix}[/b]" if prefix else ""
        text = sense.get("text") or sense.get("translation") or ""
        labels = sense.get("labels") or []
        label_str = f' [i]({dsl_escape(", ".join(labels))})[/i]' if labels else ""
        comment = sense.get("comment")
        comment_str = (
            f' [i]{dsl_escape(comment)}[/i]'
            if comment and sense.get("comment_lang") != "av"
            else ""
        )
        if text or label_str or comment_str:
            lines.append(f'[m1]{bold}{dsl_escape(text)}{label_str}{comment_str}[/m1]')
        for ex in sense.get("examples") or entry.get("examples") or []:
            av = dsl_escape(ex.get("av", ""))
            ru = dsl_escape(ex.get("ru", ""))
            if av or ru:
                lines.append(f'[m2][ex]{av} — {ru}[/ex][/m2]')

    see_also = entry.get("see_also") or []
    if see_also:
        refs = ", ".join(f'[ref]{dsl_escape(sa["target"])}[/ref]' for sa in see_also)
        lines.append(f'[m1][i]см. также:[/i] {refs}[/m1]')

    return "\n".join(lines) if lines else "[m1](нет данных)[/m1]"


def write_dsl(entries: list[dict], out_path: Path, dict_name: str, index_lang: str, contents_lang: str) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"#NAME\t{dict_name}\n")
        f.write(f"#INDEX_LANGUAGE\t{index_lang}\n")
        f.write(f"#CONTENTS_LANGUAGE\t{contents_lang}\n\n")
        for e in entries:
            word = headword(e)
            if not word:
                continue
            f.write(word + "\n")
            for line in render_definition_dsl(e).split("\n"):
                f.write("\t" + line + "\n")
            f.write("\n")


# ---------- FB2 (FictionBook, for PocketBook and others) ----------
# pyglossary has no FB2 plugin (read or write), so this is hand-rolled too.

def xml_escape(text: str | None) -> str:
    return htmllib.escape(text or "", quote=False)


def render_definition_fb2(entry: dict) -> str:
    """Plain FB2 body paragraphs (<p>/<emphasis>/<strong> only -- FB2's
    paragraph model doesn't nest lists, so examples become their own
    paragraphs rather than <ul><li>...)."""
    paras = []
    meta_bits = []
    if entry.get("pos"):
        meta_bits.append(entry["pos"])
    if entry.get("form") and entry["form"] != "—":
        meta_bits.append(entry["form"])
    if meta_bits:
        paras.append(f'<p><emphasis>{xml_escape(", ".join(meta_bits))}</emphasis></p>')

    forms = entry.get("forms") or []
    if len(forms) > 1:
        paras.append(f'<p><emphasis>формы:</emphasis> {xml_escape(", ".join(forms))}</p>')

    senses = entry.get("senses") or []
    multi = len(senses) > 1
    for i, sense in enumerate(senses, 1):
        prefix = f"{i}. " if multi else ""
        text = sense.get("text") or sense.get("translation") or ""
        labels = sense.get("labels") or []
        label_str = f' <emphasis>({xml_escape(", ".join(labels))})</emphasis>' if labels else ""
        comment = sense.get("comment")
        comment_str = (
            f' <emphasis>{xml_escape(comment)}</emphasis>'
            if comment and sense.get("comment_lang") != "av"
            else ""
        )
        if text or label_str or comment_str:
            paras.append(f'<p><strong>{xml_escape(prefix)}</strong>{xml_escape(text)}{label_str}{comment_str}</p>')
        for ex in sense.get("examples") or entry.get("examples") or []:
            av = xml_escape(ex.get("av", ""))
            ru = xml_escape(ex.get("ru", ""))
            if av or ru:
                paras.append(f'<p>— {av} — {ru}</p>')

    see_also = entry.get("see_also") or []
    if see_also:
        refs = ", ".join(xml_escape(sa["target"]) for sa in see_also)
        paras.append(f'<p><emphasis>см. также:</emphasis> {refs}</p>')

    return "".join(paras) if paras else "<p>(нет данных)</p>"


def write_fb2(entries: list[dict], out_path: Path, dict_name: str, description: str, lang: str) -> None:
    sections = []
    for e in entries:
        word = headword(e)
        if not word:
            continue
        sections.append(
            f'<section><title><p>{xml_escape(word)}</p></title>'
            f'{render_definition_fb2(e)}</section>'
        )
    fb2 = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">\n'
        '<description><title-info>'
        '<genre>reference</genre>'
        '<author><nickname>avar.me</nickname></author>'
        f'<book-title>{xml_escape(dict_name)}</book-title>'
        f'<annotation><p>{xml_escape(description)}</p></annotation>'
        f'<lang>{xml_escape(lang or "av")}</lang>'
        '</title-info>'
        '<document-info><author><nickname>avar.me</nickname></author></document-info>'
        '</description>\n'
        f'<body>{"".join(sections)}</body>\n'
        "</FictionBook>\n"
    )
    out_path.write_text(fb2, encoding="utf-8")


# ---------- PDF (any e-reader / print) ----------
# pyglossary has no PDF plugin either; rendered with fpdf2, reusing the
# same HTML definitions as the pyglossary-backed formats via write_html().

def write_pdf(entries: list[dict], out_path: Path, dict_name: str, description: str) -> None:
    from fpdf import FPDF, XPos, YPos

    # multi_cell leaves the cursor at new_x/new_y after writing; without
    # resetting it to the left margin every call, the next multi_cell
    # starts near the right edge with ~0 width left and fpdf2 raises.
    FULL_LINE = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}

    pdf = FPDF()
    pdf.add_font("DejaVu", "", str(FONTS_DIR / "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", str(FONTS_DIR / "DejaVuSans-Bold.ttf"))
    pdf.add_font("DejaVu", "I", str(FONTS_DIR / "DejaVuSans-Oblique.ttf"))
    pdf.set_margins(18, 18, 18)
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 18)
    pdf.multi_cell(0, 10, dict_name, **FULL_LINE)
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 6, description, **FULL_LINE)
    pdf.ln(4)

    for e in entries:
        word = headword(e)
        if not word:
            continue
        pdf.set_font("DejaVu", "B", 13)
        pdf.multi_cell(0, 8, word, **FULL_LINE)
        pdf.set_font("DejaVu", "", 10)
        pdf.write_html(render_definition_html(e))
        pdf.set_x(pdf.l_margin)
        pdf.ln(2)

    pdf.output(str(out_path))


# ---------- generic pyglossary-backed formats ----------

def build_glossary(entries: list[dict], dict_name: str, description: str) -> Glossary:
    Glossary.init()
    glos = Glossary()
    glos.setInfo("title", dict_name)
    glos.setInfo("author", "avar.me")
    glos.setInfo("description", description)
    for e in entries:
        word = headword(e)
        if not word:
            continue
        defi = render_definition_html(e)
        glos.addEntry(glos.newEntry([word], defi, defiFormat="h"))
    return glos


def zip_path(src_path: Path, zip_dest: Path) -> None:
    """Zip a single file or a directory tree into zip_dest (without the
    .zip suffix -- shutil.make_archive appends it)."""
    base = str(zip_dest)
    if src_path.is_dir():
        shutil.make_archive(base, "zip", root_dir=src_path)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            staged = Path(tmp) / src_path.name
            shutil.copy2(src_path, staged)
            shutil.make_archive(base, "zip", root_dir=tmp)


def list_pyglossary_formats() -> dict[str, object]:
    Glossary.init()
    out = {}
    for name, plugin in Glossary.plugins.items():
        if name in SKIP_FORMATS:
            continue
        if getattr(plugin, "writerClass", None) is not None:
            out[name] = plugin
    return out


def convert_source(
    jsonl_path: Path,
    dict_id: str,
    dict_name: str,
    description: str,
    index_lang: str,
    contents_lang: str,
    out_dir: Path,
) -> list[tuple[str, Path]]:
    """Returns a list of (format_label, zip_path) for everything that
    succeeded. Failures are logged to stderr and skipped."""
    entries = load_entries(jsonl_path)
    print(f"  {dict_id}: {len(entries):,} entries")
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, Path]] = []

    # DSL, hand-rolled.
    try:
        with tempfile.TemporaryDirectory() as tmp:
            dsl_file = Path(tmp) / f"{dict_id}.dsl"
            write_dsl(entries, dsl_file, dict_name, index_lang, contents_lang)
            dest = out_dir / f"{dict_id}-dsl"
            zip_path(dsl_file, dest)
            results.append(("DSL (ABBYY Lingvo)", dest.with_suffix(".zip")))
        print("    DSL: ok")
    except Exception:
        print(f"    DSL: FAILED\n{traceback.format_exc()}", file=sys.stderr)

    # FB2, hand-rolled.
    try:
        with tempfile.TemporaryDirectory() as tmp:
            fb2_file = Path(tmp) / f"{dict_id}.fb2"
            write_fb2(entries, fb2_file, dict_name, description, index_lang)
            dest = out_dir / f"{dict_id}-fb2"
            zip_path(fb2_file, dest)
            results.append(("FB2 (FictionBook)", dest.with_suffix(".zip")))
        print("    FB2: ok")
    except Exception:
        print(f"    FB2: FAILED\n{traceback.format_exc()}", file=sys.stderr)

    # PDF, hand-rolled (fpdf2).
    try:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_file = Path(tmp) / f"{dict_id}.pdf"
            write_pdf(entries, pdf_file, dict_name, description)
            dest = out_dir / f"{dict_id}-pdf"
            zip_path(pdf_file, dest)
            results.append(("PDF", dest.with_suffix(".zip")))
        print("    PDF: ok")
    except Exception:
        print(f"    PDF: FAILED\n{traceback.format_exc()}", file=sys.stderr)

    # Every write-capable pyglossary plugin.
    formats = list_pyglossary_formats()
    for name, plugin in sorted(formats.items()):
        label = getattr(plugin, "description", name)
        try:
            glos = build_glossary(entries, dict_name, description)
            with tempfile.TemporaryDirectory() as tmp:
                out_base = Path(tmp) / dict_id
                glos.write(str(out_base), formatName=name)
                # pyglossary sometimes writes `<out_base>.<ext>` as a file,
                # sometimes `<out_base>/` as a directory; figure out which.
                candidates = list(Path(tmp).iterdir())
                written = [c for c in candidates if c.name.startswith(dict_id)]
                if not written:
                    raise RuntimeError("writer produced no output")
                src_path = written[0] if len(written) == 1 else Path(tmp)
                dest = out_dir / f"{dict_id}-{name.lower()}"
                zip_path(src_path, dest)
                results.append((label, dest.with_suffix(".zip")))
            print(f"    {name}: ok")
        except Exception:
            print(f"    {name}: FAILED ({sys.exc_info()[1]})", file=sys.stderr)

    return results
