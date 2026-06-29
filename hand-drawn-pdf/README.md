# hand-drawn-pdf

TypePress 手绘风格 PDF 生成管线。包含两种互补方案：

- **纯 CSS**：边框、高亮、下划线、便签纸等装饰效果（零依赖，TypePress 直出）
- **Rough.js → PNG**：架构图、流程图等手绘图形（Node.js 预生成）

## 快速开始

```bash
# 纯 CSS 方案
typepress doc.html -o output.pdf --autofit

# Rough.js 管线
node scripts/rough-svg-gen.mjs spec.json out/svgs/
# ... resvg raster → typepress -i 注册 → PDF
```

## 文件结构

```
├── SKILL.md              # Hermes Agent skill 定义
├── README.md             # 本文件
├── scripts/
│   ├── rough-svg-gen.mjs # Rough.js → SVG 生成器
│   └── hand-drawn-pdf.sh # 一键管线 (JSON → PDF)
├── references/
│   ├── spec-schema.md    # JSON 图表规范
│   ├── css-hand-drawn-guide.md  # CSS 手绘手法参考
│   └── cover-generation.md      # 封面生成指南
└── screenshots/          # 效果预览
```

## 依赖

- Node.js 18+（Rough.js SVG 生成）
- resvg（SVG → PNG 栅格化）
- TypePress [alitrack/typepress](https://github.com/alitrack/typepress)（HTML → PDF）
