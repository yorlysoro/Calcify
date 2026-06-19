#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Extracting messages..."
pybabel extract -F babel.cfg -o messages.pot .

if [ -d "translations" ]; then
    echo "Updating existing translations..."
    pybabel update -i messages.pot -d translations
else
    echo "Initializing Spanish translations..."
    pybabel init -i messages.pot -d translations -l es
fi

echo "Compiling translations..."
pybabel compile -d translations

echo "Done."
