// rough-svg-gen.mjs — Generate hand-drawn SVGs using Rough.js generator (no DOM)
import { default as rough } from 'roughjs/bundled/rough.esm.js';
import { readFileSync, mkdirSync, writeFileSync } from 'fs';

const specPath = process.argv[2];
const outDir = process.argv[3] || '/tmp/sketch-svgs';
const spec = JSON.parse(readFileSync(specPath, 'utf-8'));
mkdirSync(outDir, { recursive: true });

const files = [];

for (const item of spec.items) {
  const { id, width, height, shapes, style } = item;
  const gen = rough.generator({
    roughness: style?.roughness ?? 1.5,
    bowing: style?.bowing ?? 1.0,
    seed: style?.seed ?? 42,
    fillStyle: 'hachure',
    hachureAngle: -41,
    hachureGap: 5,
  });

  const svgParts = [];
  svgParts.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">`);
  
  const bg = style?.background ?? 'transparent';
  if (bg !== 'transparent') {
    svgParts.push(`<rect width="${width}" height="${height}" fill="${bg}"/>`);
  }

  for (const s of shapes) {
    const opts = { 
      stroke: s.stroke ?? '#333',
      strokeWidth: s.strokeWidth ?? 2,
      fill: s.fill ?? 'none',
      fillStyle: s.fillStyle ?? 'hachure',
      hachureAngle: s.hachureAngle ?? -41,
      hachureGap: s.hachureGap ?? 5,
      roughness: s.roughness ?? style?.roughness ?? 1.5,
      bowing: s.bowing ?? style?.bowing ?? 1.0,
      seed: (style?.seed ?? 42) + (s.seedOffset ?? 0),
    };

    let result;
    switch (s.type) {
      case 'rectangle':
        result = gen.rectangle(s.x, s.y, s.w, s.h, opts);
        break;
      case 'circle':
        result = gen.circle(s.cx, s.cy, s.diameter, opts);
        break;
      case 'ellipse':
        result = gen.ellipse(s.cx, s.cy, s.w, s.h, opts);
        break;
      case 'line':
        result = gen.line(s.x1, s.y1, s.x2, s.y2, opts);
        break;
      case 'linearPath':
        result = gen.linearPath(s.points, opts);
        break;
      case 'polygon':
        result = gen.polygon(s.points, opts);
        break;
      case 'curve':
        result = gen.curve(s.points, opts);
        break;
    }

    if (result) {
      const paths = gen.toPaths(result);
      for (const p of paths) {
        const d = p.d || '';
        if (!d) continue;
        if (p.fill && p.fill !== 'none') {
          svgParts.push(`<path d="${d}" fill="${p.fill}" stroke="none"/>`);
        } else {
          svgParts.push(`<path d="${d}" fill="none" stroke="${p.stroke || opts.stroke}" stroke-width="${p.strokeWidth || opts.strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>`);
        }
      }
    }

    // Text labels are plain SVG
    if (s.type === 'text-label') {
      svgParts.push(`<text x="${s.x}" y="${s.y}" text-anchor="middle" font-family="${s.font || 'Caveat, cursive'}" font-size="${s.fontSize || 16}" fill="${s.color || '#333'}">${s.text}</text>`);
    }
  }

  svgParts.push('</svg>');
  const svgStr = svgParts.join('\n');
  const fpath = `${outDir}/${id}.svg`;
  writeFileSync(fpath, svgStr);
  files.push({ id, path: fpath, width, height });
  console.log(`✓ ${id}.svg (${width}x${height})`);
}

console.log('\n---MANIFEST---');
console.log(JSON.stringify(files));
