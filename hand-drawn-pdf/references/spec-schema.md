# Rough.js Diagram JSON Spec Format

Each spec file is a JSON object with an `items` array. Each item produces one SVG.

## Top-level

```json
{
  "items": [ ... ]
}
```

## Item

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | required | Output SVG filename (without .svg) |
| `width` | number | required | SVG width in pixels |
| `height` | number | required | SVG height in pixels |
| `style` | object | see below | Default style for all shapes |
| `shapes` | array | required | Array of shape definitions |

### Style

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `roughness` | number | 1.5 | Line jitter intensity (0.5=smooth, 3=very rough) |
| `bowing` | number | 1.0 | Line curvature (0=straight, 3=curvy) |
| `seed` | number | 42 | Random seed for reproducibility |
| `background` | string | "transparent" | SVG background color (e.g. "#fffef9") |

## Shapes

All shapes share these common options:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `stroke` | string | "#333" | Outline color |
| `strokeWidth` | number | 2 | Outline thickness |
| `fill` | string | "none" | Fill color |
| `fillStyle` | string | "hachure" | Fill pattern: hachure, solid, cross-hatch, dots, zigzag, dashed |
| `roughness` | number | style.roughness | Per-shape override |
| `bowing` | number | style.bowing | Per-shape override |
| `hachureAngle` | number | -41 | Hatch line angle in degrees |
| `hachureGap` | number | 5 | Gap between hatch lines |
| `seedOffset` | number | 0 | Added to style.seed for per-shape seed |

### rectangle

```json
{ "type": "rectangle", "x": 60, "y": 80, "w": 140, "h": 62, "fill": "#d4edda" }
```

### circle

```json
{ "type": "circle", "cx": 80, "cy": 80, "diameter": 60, "fill": "#ffcccc" }
```

### ellipse

```json
{ "type": "ellipse", "cx": 200, "cy": 100, "w": 150, "h": 80 }
```

### line

```json
{ "type": "line", "x1": 100, "y1": 100, "x2": 300, "y2": 200, "strokeWidth": 2.5 }
```

### polygon

```json
{ "type": "polygon", "points": [[50,10],[90,80],[10,80]] }
```

### curve (smooth curve through points)

```json
{ "type": "curve", "points": [[20,80],[60,20],[100,80],[140,20]] }
```

### linearPath (connected straight lines)

```json
{ "type": "linearPath", "points": [[50,50],[150,50],[100,100]] }
```

### text-label (plain SVG text, not Rough.js)

```json
{
  "type": "text-label",
  "x": 130, "y": 117,
  "text": "Web App",
  "fontSize": 16,
  "font": "Caveat",
  "color": "#155724"
}
```

**IMPORTANT**: `font` must match the system-installed font name exactly (no fallback like "Caveat, cursive"). resvg resolves fonts by exact name.

## Full Example

```json
{
  "items": [{
    "id": "simple-flow",
    "width": 400, "height": 300,
    "style": { "roughness": 1.8, "bowing": 1.2, "background": "#fffef9" },
    "shapes": [
      { "type": "rectangle", "x": 100, "y": 20, "w": 200, "h": 50,
        "fill": "#e3f2fd", "fillStyle": "hachure" },
      { "type": "text-label", "x": 200, "y": 50,
        "text": "Start", "fontSize": 18, "font": "Caveat", "color": "#1565c0" },
      { "type": "line", "x1": 200, "y1": 70, "x2": 200, "y2": 100,
        "strokeWidth": 2 },
      { "type": "rectangle", "x": 100, "y": 100, "w": 200, "h": 50,
        "fill": "#fff8e1", "fillStyle": "cross-hatch" },
      { "type": "text-label", "x": 200, "y": 130,
        "text": "Process", "fontSize": 16, "font": "Caveat", "color": "#f57f17" },
      { "type": "line", "x1": 200, "y1": 150, "x2": 200, "y2": 180,
        "strokeWidth": 2 },
      { "type": "rectangle", "x": 125, "y": 180, "w": 150, "h": 45,
        "fill": "#e8f5e9", "fillStyle": "solid" },
      { "type": "text-label", "x": 200, "y": 208,
        "text": "End", "fontSize": 18, "font": "Caveat", "color": "#2e7d32" }
    ]
  }]
}
```
