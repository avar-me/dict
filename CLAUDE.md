# Инструкции для AI-ассистентов в этом репозитории

Этот файл — общая инструкция для Claude, Copilot, Cursor и других. Если вы агент — прочитайте до начала любых изменений.

## Что это за репозиторий

`dict.avar.me` — статический сайт-каталог, который пересобирает все словари экосистемы avar.me во все известные (и по возможности новые) форматы офлайн-словарных приложений: DSL, StarDict, EPUB, Mobi, Kobo, Babylon BGL, Apple Dictionary, Aard2/Slob, DICT.org и т. д. Публикуется на GitHub Pages из этого репозитория. Домен — `CNAME`.

**Данные здесь не хранятся.** При сборке `build.sh` → `src/build_all.py` выкачивает `sources.json` и каждый `jsonl` словарь с `sources.avar.me`, конвертирует и публикует производные файлы. Источник правды для содержимого словарей — [`avar-me/sources`](https://github.com/avar-me/sources). **Не коммитьте сюда jsonl, не правьте тексты словарей в этом репозитории** — правки туда, в `avar-me/sources`.

## Главное правило

1. **В репо только исходники сборки.** `src/*.py`, `src/templates/`, `requirements.txt`, `build.sh`, `.github/workflows/deploy.yml`, `CNAME`, документация. **Ни единого артефакта сборки, ни единого словарного файла** — кроме явного исключения в `prebuilt/` (см. ниже).
2. **`docs/` — gitignored.** Это выход `build.sh`. Никогда не коммитьте, никогда не правьте руками.
3. **`*.jsonl` — gitignored.** Скачиваются во временную папку при сборке, в репо не лежат.
4. **Эта сборка — внешняя зависимость от `pyglossary`, сознательно.** `sources.avar.me`'s `src/build_site.py` принципиально использует только стандартную библиотеку Python; здесь это ограничение не действует — весь смысл репозитория в том, чтобы использовать `pyglossary` и системные библиотеки (ICU, marisa-trie) для максимального охвата форматов. Не пытайтесь переносить сюда это ограничение из `sources`.
5. **Формат добавляется, а не удаляется, без явного запроса.** Если какой-то формат pyglossary падает на части данных — чинить конвертер или грейсфул-скип этого формата для этой статьи, не вырезать формат из списка молча.
6. **Новые источники словарей подхватываются автоматически.** `src/sources_catalog.py` берёт все `kind: "dictionary"` из `sources.json`, кроме `av-ru.2006`/`av-ru.avar.me` (это сырые до-мёрджа компоненты `av-ru`, конвертировать их отдельно не нужно). Когда в `sources.avar.me` появится новый словарь — он попадёт в сборку сам, без правок кода здесь.
7. **`prebuilt/` — единственное исключение из правила «ничего не коммитим».** Форматы, которые физически нельзя собрать в CI (сейчас — Apple Dictionary `.dictionary`, требующий macOS-only Dictionary Development Kit), собираются вручную и кладутся туда; `src/build_all.py` подхватывает `prebuilt/<source-id>-<suffix>.zip` по `PREBUILT_LABELS` и включает в манифест под именем с `-compiled`, не трогая автогенерируемый вариант того же формата (source+Makefile). После правок данных в `av-ru` их нужно пересобрать и закоммитить заново вручную — см. `prebuilt/README.md`.

## Поток работы

```
sources.avar.me/sources.json  (какие словари конвертировать)
            │
            ▼
sources.avar.me/data/{av-ru,ru-av,...}.jsonl
            │
            ▼
src/convert.py  ──►  pyglossary (все write-способные плагины) + hand-rolled DSL writer
            │
            ▼
docs/<source-id>/<source-id>-<format>.zip  +  docs/manifest.json
            │
            ▼
src/build_site.py  ──►  docs/index.html
            │
            ▼
      GitHub Actions ──► GitHub Pages (раз в сутки по cron, или push/workflow_dispatch)
```

## Известные ограничения

- **Mobi** без `kindlegen_path` даёт сырые файлы (OPF/HTML), не готовый `.mobi` — Amazon's kindlegen проприетарный и недоступен для автоматической установки в CI. Если понадобится готовый `.mobi`, см. опцию `--write-options 'kindlegen_path=...'` у pyglossary.
- **Apple Dictionary** — автогенерируемый `*-appledict.zip` содержит только исходник (XML + Makefile + plist), финальная компиляция в `.dictionary`-бандл требует Apple Dictionary Development Kit (доступен только на macOS, не автоматизирован в CI). Готовый скомпилированный `.dictionary` для av-ru лежит в `prebuilt/av-ru-appledict-compiled.zip` и публикуется отдельной строкой на сайте; обновляется вручную (см. `prebuilt/README.md`).
- **PyICU** требует системную ICU-библиотеку (`libicu-dev` + `pkg-config` на Ubuntu) — уже прописано в workflow; при локальной сборке на macOS — `brew install icu4c pkg-config` и `PKG_CONFIG_PATH="$(brew --prefix icu4c)/lib/pkgconfig" pip install pyicu`.

## Когда сомневаетесь

Спросите перед тем как:
- Менять список исключённых pyglossary-плагинов (`SKIP_FORMATS` в `src/convert.py`) — это редакционное решение, не техническое.
- Переносить какой-либо из этих форматов обратно в основной `avar-me/sources` как постоянный build-артефакт (обсуждалось — решение отложено, сначала смотрим, насколько востребован этот отдельный сайт).
- Менять домен/CNAME или имя репозитория — сломает уже настроенный DNS.

## Полезные ссылки

- Источник данных: [`avar-me/sources`](https://github.com/avar-me/sources)
- Координация: Telegram-канал [@avarlangme](https://t.me/avarlangme)
- Сообщить об ошибке в данных (не в сборке): [@avarme_chat](https://t.me/avarme_chat)
