# Hand-Drawn Cover Image Generation

Generate WeChat article cover images (900×383, 2.35:1) with hand-drawn aesthetic.

## Preferred Pipeline: TypePress (not resvg)

resvg's fontdb often fails to find user-installed CJK fonts. TypePress's `@font-face` auto-download is more reliable.

### Step 1: Create cover HTML

```html
<!DOCTYPE html><html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;700&family=Ma+Shan+Zheng&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:900px;height:383px;overflow:hidden;background:#F8FAFC;padding:30px 50px;position:relative}
h1{font-family:'Ma Shan Zheng',cursive;font-size:44px;color:#0F172A;line-height:1.2}
.sub{font-family:'Ma Shan Zheng',cursive;font-size:20px;color:#334155}
/* Hand-drawn border using asymmetric border-radius */
.border-outer{position:absolute;top:12px;left:12px;right:12px;bottom:12px;
  border:2.5px solid #334155;border-radius:255px 15px 225px 15px/15px 225px 15px 255px;pointer-events:none}
</style></head><body>
<div class="border-outer"></div>
<h1>Title Text</h1>
<p class="sub">Subtitle line</p>
</body></html>
```

### Step 2: Render to PDF

```bash
typepress cover.html -l --margin 0 -o cover.pdf
```

Landscape (`-l`) gives 842×595 — closer to the 2.35:1 target ratio than portrait A4.

### Step 3: Extract and crop to 2.35:1

```python
import fitz
from PIL import Image

doc = fitz.open('cover.pdf')
page = doc[0]
pix = page.get_pixmap(dpi=200)
pix.save('/tmp/cover-full.png')

img = Image.open('/tmp/cover-full.png')
w, h = img.size
target_ratio = 900 / 383
crop_h = int(w / target_ratio)
img_cropped = img.crop((0, 0, w, min(crop_h, h)))
img_cropped = img_cropped.resize((900, 383), Image.LANCZOS)
img_cropped.save('/tmp/cover-900x383.png')
```

### Color Palette

WeChat articles require light background covers:

| Element | Color | Usage |
|---------|-------|-------|
| Background | `#F8FAFC` | Must be light (WeChat rule) |
| Title text | `#0F172A` | Dark, high contrast |
| Subtitle | `#334155` or `#64748b` | Medium contrast |
| Accent line | `#e74c3c` | Single decorative line |
| Border | `#334155` | Sketchy frame stroke |

## Fallback: Rough.js SVG → resvg

Only use if CJK text is NOT needed:

```bash
node rough-svg-gen.mjs cover-spec.json /tmp/cover-svg/
resvg /tmp/cover-svg/cover.svg /tmp/cover.png
```

Text labels in SVG must use `font="Caveat"` (exact name, no fallback). CJK text requires system-installed fonts that resvg/fontdb can find — often unreliable.
