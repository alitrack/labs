---
name: hand-drawn-pdf
description: Generate hand-drawn style PDF documents using Rough.js SVG → resvg PNG → TypePress. Supports both CSS-only techniques (sketchy borders, marker highlights, wavy underlines, notebook paper) and programmatic Rough.js diagrams (flowcharts, architecture diagrams). When user asks for hand-drawn/sketchy/doodle PDF output, or wants to create "手绘风" documents.
version: 1.0.0
---

# Hand-Drawn PDF Pipeline

## Overview

Two complementary approaches for hand-drawn PDF generation with TypePress:

| Approach | When to use | JS required? | Output |
|----------|------------|-------------|--------|
| **Pure CSS** | Borders, boxes, highlights, text effects | No | Vector text in PDF |
| **Rough.js SVG → PNG** | Architecture diagrams, flowcharts, custom graphics | Only during SVG generation | Raster PNG in PDF |

## Quick Start: Pure CSS

For documents that just need a hand-drawn aesthetic on text elements:

```html
<style>
/* Hand-drawn fonts — TypePress auto-downloads via @font-face */
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;700&family=Ma+Shan+Zheng&display=swap');

/* ① Asymmetric border-radius — instant sketchy boxes */
.sketch-box {
  border: 2.5px solid #41403e;
  border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px;
  background: #fffef9;
  padding: 14px 18px;
}

/* ② Double pseudo-element — simulates pen re-stroke */
.double-stroke {
  position: relative;
  border: 2px solid #333;
  padding: 14px 18px;
  border-radius: 8px;
}
.double-stroke::before {
  content: "";
  position: absolute;
  inset: -5px;
  border: 2px dashed #666;
  border-radius: 12px;
  transform: rotate(-0.4deg);
  pointer-events: none;
}

/* ③ Marker highlight — CSS gradient */
.marker {
  background: linear-gradient(120deg,
    transparent 0 15%, rgba(255,245,157,0.85) 15% 85%, transparent 85%);
}

/* ④ Wavy underline — native CSS */
.wavy {
  text-decoration: underline wavy #ff3ea5;
  text-underline-offset: 4px;
}

/* ⑤ Notebook paper background */
.notebook {
  background:
    repeating-linear-gradient(to bottom, transparent 0 27px, rgba(70,130,180,0.08) 27px 28px),
    linear-gradient(to right, rgba(220,20,60,0.15) 42px, transparent 0),
    #fffef9;
}

/* ⑥ Sticky note with folded corner */
.sticky {
  position: relative;
  background: #fff3b0;
  border: 1px solid #e6db86;
  box-shadow: 0 2px 3px rgba(0,0,0,0.08), 0 10px 20px rgba(0,0,0,0.06);
}
.sticky::after {
  content: "";
  position: absolute;
  right: 0; top: 0;
  border-width: 0 16px 16px 0;
  border-style: solid;
  border-color: transparent #d4c972 transparent transparent;
}
</style>
```

Convert with TypePress:
```bash
typepress document.html -o output.pdf --autofit
```

## Quick Start: Rough.js Diagrams

### Step 1: Define diagrams in JSON

Create `spec.json` using the schema in `references/spec-schema.md`:

```json
{
  "items": [{
    "id": "arch",
    "width": 520, "height": 340,
    "style": { "roughness": 1.8, "background": "#fffef9" },
    "shapes": [
      { "type": "rectangle", "x": 60, "y": 80, "w": 140, "h": 62, "fill": "#d4edda", "fillStyle": "hachure" },
      { "type": "text-label", "x": 130, "y": 117, "text": "Web App", "fontSize": 16 }
    ]
  }]
}
```

### Step 2: Generate SVGs

```bash
node scripts/rough-svg-gen.mjs spec.json out/svgs/
```

### Step 3: Rasterize to PNG

```bash
mkdir -p out/pngs/
for svg in out/svgs/*.svg; do
  name=$(basename "$svg" .svg)
  resvg "$svg" "out/pngs/$name.png"
done
```

### Step 4: Build HTML with images

```html
<img src="arch" width="520" height="340" alt="Architecture">
```

### Step 5: Convert to PDF

```bash
typepress doc.html \
  -i arch=out/pngs/arch.png \
  -i flow=out/pngs/flow.png \
  --autofit -o output.pdf
```

## Complete Pipeline Script

For production use, `scripts/hand-drawn-pdf.sh` runs the full pipeline:

```bash
./scripts/hand-drawn-pdf.sh spec.json template.html -o output.pdf
```

This: generates SVGs → rasterizes PNGs → registers images → renders PDF.

## Image Size Constraints

TypePress renders at 96dpi. A4 content area ≈ 714px wide, A3 ≈ 1030px.

| Page | Content width | Max recommended image width |
|------|--------------|---------------------------|
| A4 portrait | ~714px | 550px |
| A4 landscape | ~1030px | 850px |
| A3 portrait | ~1030px | 850px |

Use `--autofit` to auto-upgrade page size if content overflows.

## Font Requirements for resvg

resvg needs system-installed fonts for SVG text rendering:

```bash
# Copy fonts to user font directory
cp caveat.ttf ~/.local/share/fonts/
fc-cache -f ~/.local/share/fonts/
```

The SVG `<text font-family="...">` must match the installed font name exactly (no fallback syntax).

## Pitfalls

### Images MUST have explicit dimensions
TypePress/Fulgur skips `<img>` elements without explicit `width`/`height` attributes or inline `style="width:__px;height:__px"`. Always specify both:
```html
<img src="diagram" width="520" height="340" alt="Diagram">
```

### `--autofit` for multi-image layouts
When stacking 3+ images, content often overflows A4 (842pt height). Use `--autofit` to auto-upgrade to A3 or landscape:
```bash
typepress doc.html -i img=file.png --autofit -o output.pdf
```

### SVG font-family must be EXACT
resvg's `usvg::text` matches fonts by exact name — no CSS fallback syntax. Use `font="Caveat"` not `font="Caveat, cursive"`. For CJK text, use a CJK-capable font (Ma Shan Zheng for hand-drawn Chinese, Noto Sans CJK for clean Chinese).

### Cover images: TypePress beats resvg for CJK
resvg struggles to find user-installed fonts for CJK text. For covers with Chinese titles, use TypePress directly:
1. Write a 900×383 HTML page with `@font-face` fonts + asymmetric border-radius
2. `typepress cover.html -l --margin 0 -o cover.pdf`
3. PyMuPDF `get_pixmap(dpi=200)` → crop to 2.35:1 → resize to 900×383

This guarantees font embedding while keeping the hand-drawn CSS aesthetic.

## Known Limitations

- **inline `<svg>`**: Not supported (fulgur extract_inline_svg_tree is stubbed — usvg 0.45/0.46 diamond dependency)
- **data:image/svg+xml**: Not supported
- **CSS flex/grid**: Degrades to table layout in fulgur
- **SVG <text>**: Requires system-installed fonts for resvg rasterization
- **No JavaScript**: Rough.js generation is offline, not in-browser
- **Canvas API**: Not available (no browser runtime)

## References

- `references/spec-schema.md` — Full JSON spec format for Rough.js diagrams
- `references/css-hand-drawn-guide.md` — Complete CSS hand-drawn technique reference
- `scripts/rough-svg-gen.mjs` — Node.js script for Rough.js SVG generation
- `scripts/hand-drawn-pdf.sh` — Complete pipeline shell script
