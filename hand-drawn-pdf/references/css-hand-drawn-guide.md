# 纯 CSS 手绘风格参考

六种完全不依赖 JavaScript 的手绘 CSS 技术，全部兼容 TypePress/Fulgur 渲染引擎。

## ① 不对称圆角 — 手绘边框

通过 X/Y 轴不对称的 border-radius，模拟自然弯曲的手绘线条。

```css
.sketch-box {
  border: 2.5px solid #41403e;
  padding: 14px 18px;
  background: #fffef9;
  border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px;
}
```

**原理**: `border-radius: X / Y` 分别控制水平/垂直半径。极端不对称比例（255:15）创造出"画歪了"的效果。

## ② 双层伪元素 — 画笔重描

模拟手绘时"画了两笔，线条不完全重合"的效果。

```css
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
  pointer-events: none; /* 关键：不阻挡交互 */
}
.double-stroke::after {
  content: "";
  position: absolute;
  inset: 0;
  border: 1px solid #999;
  transform: rotate(0.3deg);
  pointer-events: none;
  opacity: 0.4;
}
```

**三层叠放**: `::before` 外移+倾斜 → `border` 实线 → `::after` 细微偏移+半透明。

## ③ 荧光笔高亮

CSS linear-gradient 模拟高亮笔刷过的效果。

```css
.marker-yellow {
  background: linear-gradient(120deg,
    transparent 0 15%, rgba(255,245,157,0.85) 15% 85%, transparent 85%);
  background-size: 100% 1.2em;
  background-position: 0 60%;
  background-repeat: no-repeat;
  padding: 0 0.15em;
}

.marker-pink {
  background: linear-gradient(120deg,
    transparent 0 12%, rgba(255,182,193,0.7) 12% 88%, transparent 88%);
  background-size: 100% 1.1em;
  background-position: 0 55%;
  background-repeat: no-repeat;
  padding: 0 0.15em;
}
```

**技巧**: 120° 倾斜角度让高亮边缘看起来像笔尖斜擦过。

## ④ 波浪下划线

CSS 原生 `text-decoration: underline wavy`，零额外成本。

```css
.wavy {
  text-decoration: underline wavy #ff3ea5;
  text-underline-offset: 4px;
  text-decoration-thickness: 1.5px;
}
```

## ⑤ 笔记本横线背景

`repeating-linear-gradient` 模拟横线笔记本。

```css
.notebook {
  background:
    repeating-linear-gradient(
      to bottom,
      transparent 0 27px,
      rgba(70, 130, 180, 0.08) 27px 28px
    ),
    linear-gradient(
      to right,
      rgba(220, 20, 60, 0.15) 42px,
      transparent 0
    ),
    #fffef9;
  padding: 16px 20px 16px 52px;
  border: 1px solid #e0dcd0;
}
```

**两层背景**: 横线层（28px 间隔）+ 左红线层（42px 活页孔标记）。

## ⑥ 便签纸折角

`box-shadow` + `::after` 伪元素制造折角效果。

```css
.sticky-note {
  position: relative;
  background: #fff3b0;
  padding: 14px 18px;
  border: 1px solid #e6db86;
  box-shadow: 0 2px 3px rgba(0,0,0,0.08), 0 10px 20px rgba(0,0,0,0.06);
}
.sticky-note::after {
  content: "";
  position: absolute;
  right: 0; top: 0;
  border-width: 0 16px 16px 0;
  border-style: solid;
  border-color: transparent #d4c972 transparent transparent;
}
```

**原理**: `::after` 用 border trick 画一个右下三角形，颜色稍深于底色，制造光影错觉。

## 组合使用技巧

```html
<div class="double-stroke">
  <h2 class="wavy">Section Title</h2>
  <p><span class="marker-yellow">重点内容高亮</span></p>
  <div class="sticky-note">
    <p>📌 注意事项</p>
  </div>
</div>
```

## 字体推荐

| 字体 | 语言 | 风格 | Google Fonts |
|------|------|------|-------------|
| Caveat | 英文 | 流畅手写 | `Caveat:wght@400;700` |
| Indie Flower | 英文 | 自然笔迹 | `Indie Flower` |
| Short Stack | 英文 | 幼稚手写 | `Short Stack` |
| Ma Shan Zheng | 中文 | 毛笔手写 | `Ma+Shan+Zheng` |
| ZCOOL KuaiLe | 中文 | 卡通圆体 | `ZCOOL+KuaiLe` |

在 HTML `<head>` 中引入：
```html
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;700&family=Ma+Shan+Zheng&display=swap" rel="stylesheet">
```

TypePress 自动下载远程字体文件并嵌入 PDF（子集化）。
