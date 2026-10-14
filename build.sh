#!/usr/bin/env bash
# Собрать все словари sources.avar.me во все известные офлайн-форматы.
#
# Использование:  ./build.sh
# Локальная проверка: python3 -m http.server -d docs 8000
#
# Зависимости (pyglossary и опциональные ускорители индексации) ставятся
# из requirements.txt в отдельный venv -- см. README.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=== 1. Конвертация всех словарей ==="
python3 src/build_all.py

echo ""
echo "=== 2. Сборка index.html ==="
python3 src/build_site.py

if [ ! -f "$ROOT/docs/index.html" ]; then
  echo "build.sh: docs/index.html не создан" >&2
  exit 1
fi

echo ""
echo "Готово. Локально:  python3 -m http.server -d docs 8000"
