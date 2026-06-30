#!/usr/bin/env bash
# Render all Graphviz .dot files to PNG and SVG
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_PNG="$DIR/rendered/png"
OUT_SVG="$DIR/rendered/svg"
mkdir -p "$OUT_PNG" "$OUT_SVG"

for dot in "$DIR"/*.dot; do
  base="$(basename "$dot" .dot)"
  echo "Rendering $base..."
  dot -Tpng -Gdpi=150 "$dot" -o "$OUT_PNG/${base}.png"
  dot -Tsvg "$dot" -o "$OUT_SVG/${base}.svg"
done

if [ -x "$(dirname "$0")/../c4/render.sh" ]; then
  echo "Rendering C4 diagrams..."
  bash "$(dirname "$0")/../c4/render.sh"
fi

echo "Done. Output: $OUT_PNG and $OUT_SVG (+ docs/c4/rendered/)"