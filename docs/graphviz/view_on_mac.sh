#!/usr/bin/env bash
# Open rendered architecture diagrams on macOS (Preview / default image app).
# .dot files are Graphviz SOURCE — they do not open as pictures without rendering.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PNG="$DIR/rendered/png"
SVG="$DIR/rendered/svg"

if ! command -v dot >/dev/null 2>&1; then
  echo "Graphviz is not installed. Install with:"
  echo "  brew install graphviz"
  echo ""
  echo "You can still view pre-rendered images in:"
  echo "  $PNG"
  exit 1
fi

# Re-render if PNG folder is empty or user passed --render
if [ "${1:-}" = "--render" ] || [ -z "$(ls -A "$PNG" 2>/dev/null || true)" ]; then
  bash "$DIR/render_all.sh"
  shift || true
fi

open_one() {
  local id="$1"
  local png="$PNG/${id}.png"
  if [ ! -f "$png" ]; then
    # Allow shorthand: 21 → 21-architecture-L1-system-context.png
    png="$(ls "$PNG"/${id}*.png 2>/dev/null | head -1)"
  fi
  if [ -z "$png" ] || [ ! -f "$png" ]; then
    echo "No rendered PNG for id: $id"
    echo "Run: bash docs/graphviz/render_all.sh"
    exit 1
  fi
  open "$png"
  echo "Opened: $png"
}

case "${1:-all}" in
  all|folder)
    open "$PNG"
    echo "Opened folder: $PNG"
    ;;
  list)
    ls -1 "$PNG"/*.png 2>/dev/null | sed "s|.*/||"
    ;;
  *)
    open_one "$1"
    ;;
esac