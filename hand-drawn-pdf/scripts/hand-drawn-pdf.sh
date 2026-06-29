#!/bin/bash
# hand-drawn-pdf.sh — Complete pipeline: JSON spec → Rough.js SVG → resvg PNG → TypePress PDF
# Usage: ./hand-drawn-pdf.sh spec.json [template.html] [-o output.pdf]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN_SCRIPT="$SCRIPT_DIR/rough-svg-gen.mjs"

# Parse args
SPEC=""
TEMPLATE=""
OUTPUT="output.pdf"
IMAGES=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o) OUTPUT="$2"; shift 2 ;;
    -i) IMAGES+=("$2"); shift 2 ;;
    *) 
      if [[ -z "$SPEC" ]]; then SPEC="$1"
      elif [[ -z "$TEMPLATE" ]]; then TEMPLATE="$1"
      fi
      shift
      ;;
  esac
done

if [[ -z "$SPEC" ]]; then
  echo "Usage: $0 spec.json [template.html] [-o output.pdf]"
  exit 1
fi

# Temp directories
TMPDIR=$(mktemp -d -t sketch-XXXXXX)
SVGDIR="$TMPDIR/svgs"
PNGDIR="$TMPDIR/pngs"
mkdir -p "$SVGDIR" "$PNGDIR"

# Step 1: Generate Rough.js SVGs
echo "=== Step 1: Generating Rough.js SVGs ==="
node "$GEN_SCRIPT" "$SPEC" "$SVGDIR" 2>&1 | grep "✓" || true

# Step 2: Rasterize to PNG via resvg
echo "=== Step 2: Rasterizing to PNG ==="
for svg in "$SVGDIR"/*.svg; do
  name=$(basename "$svg" .svg)
  resvg "$svg" "$PNGDIR/$name.png" 2>&1 | grep -v "Warning" || true
  echo "  ✓ $name → $(wc -c < "$PNGDIR/$name.png") bytes"
done

# Step 3: Build -i flags for TypePress
IFLAGS=""
for png in "$PNGDIR"/*.png; do
  name=$(basename "$png" .png)
  IFLAGS="$IFLAGS -i $name=$png"
done

# Step 4: Render PDF with TypePress
echo "=== Step 3: Rendering PDF ==="
HTML_FILE="${TEMPLATE:-}"
if [[ -z "$HTML_FILE" ]]; then
  # Auto-generate simple HTML if no template
  HTML_FILE="$TMPDIR/doc.html"
  {
    echo '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Hand-drawn</title>'
    echo '<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;700&family=Ma+Shan+Zheng&display=swap" rel="stylesheet">'
    echo '<style>body{font-family:Caveat,sans-serif;padding:30px;background:#faf9f6}</style></head><body>'
    for png in "$PNGDIR"/*.png; do
      name=$(basename "$png" .png)
      # Get image dimensions
      read w h <<< $(python3 -c "from PIL import Image; i=Image.open('$png'); print(i.width, i.height)")
      echo "<h2>$name</h2>"
      echo "<img src=\"$name\" width=\"$w\" height=\"$h\" style=\"border:2px dashed #ddd;border-radius:8px;padding:4px;background:#fffef9\">"
    done
    echo '</body></html>'
  } > "$HTML_FILE"
fi

typepress "$HTML_FILE" $IFLAGS --autofit -o "$OUTPUT" 2>&1 | grep -E "Image:|PDF|Autofit" || true

echo "=== Done: $OUTPUT ==="
ls -lh "$OUTPUT"

# Cleanup
rm -rf "$TMPDIR"
