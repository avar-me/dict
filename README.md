# dict.avar.me

Словари экосистемы [avar.me](https://avar.me), пересобранные во все известные форматы офлайн-словарных приложений: **DSL** (ABBYY Lingvo), **StarDict**, **EPUB**, **Mobi**, **Kobo**, **Babylon (.BGL)**, **Apple Dictionary**, **Aard2/Slob**, **DICT.org**, **QuickDic**, **Yomichan**, **Tabfile**, **PDF**, **FB2** (FictionBook) и другие — всё, что умеет писать [pyglossary](https://github.com/ilius/pyglossary), плюс DSL/FB2/PDF (которые pyglossary не пишет — собираются тремя минимальными ручными конвертерами в `src/convert.py`).

Источник данных — [`avar-me/sources`](https://github.com/avar-me/sources); этот репозиторий ничего не хранит, только конвертирует и публикует.

## Использование

Просто скачайте нужный файл на [dict.avar.me](https://dict.avar.me) и импортируйте в своё приложение (GoldenDict, Kobo, Calibre и т. д. — см. раздел «Как этим пользоваться» на сайте).

## Сборка

```bash
python3 -m venv .venv
source .venv/bin/activate
# ICU нужен системно: на macOS — brew install icu4c pkg-config
#                     на Ubuntu — sudo apt-get install libicu-dev pkg-config
pip install -r requirements.txt
./build.sh
python3 -m http.server -d docs 8000   # проверить локально
```

Деплой автоматический: `git push origin main`, раз в сутки по расписанию, или вручную (`workflow_dispatch`) → GitHub Actions собирает `docs/` и публикует на GitHub Pages.

## Структура

- `src/sources_catalog.py` — какие словари брать с sources.avar.me (все `kind: "dictionary"`, кроме сырых до-мёрджа компонентов av-ru).
- `src/convert.py` — конвертация одного jsonl-словаря во все форматы.
- `src/build_all.py` — оркестрация: скачать все словари → конвертировать → `docs/manifest.json`.
- `src/build_site.py` — `docs/manifest.json` → `docs/index.html`.
- `prebuilt/` — единственное исключение из «ничего не коммитим»: форматы, которые нельзя собрать в CI (сейчас — скомпилированный Apple Dictionary `.dictionary`, нужен macOS-only Dictionary Development Kit), собраны вручную и подхватываются `build_all.py` при каждой сборке. См. `prebuilt/README.md`.

## Правки данных

Этот репозиторий не хранит тексты словарей. Нашли ошибку в переводе — это
правится в [`avar-me/sources`](https://github.com/avar-me/sources) (через
чат [@avarme_chat](https://t.me/avarme_chat)); здесь ничего чинить не
нужно, следующая ночная пересборка подхватит исправление сама.

## Лицензии

- Код (этот репозиторий) — MIT.
- Данные — как в `avar-me/sources`, см. `sources.json` там.
