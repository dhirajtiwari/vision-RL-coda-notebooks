#!/usr/bin/env bash
# Render all C4 Graphviz diagrams to docs/c4/rendered/{png,svg}
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$DIR/graphviz"
OUT_PNG="$DIR/rendered/png"
OUT_SVG="$DIR/rendered/svg"
mkdir -p "$OUT_PNG" "$OUT_SVG"

if ! command -v dot >/dev/null 2>&1; then
  echo "Graphviz required: brew install graphviz"
  exit 1
fi

for dot in "$SRC"/*.dot; do
  base="$(basename "$dot" .dot)"
  echo "Rendering $base..."
  dot -Tpng -Gdpi=150 "$dot" -o "$OUT_PNG/${base}.png"
  dot -Tsvg "$dot" -o "$OUT_SVG/${base}.svg"
done

echo "Done. C4 diagrams: $OUT_PNG"