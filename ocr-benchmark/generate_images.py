#!/usr/bin/env python3
"""Generate a Chinese text image for OCR testing."""
from PIL import Image, ImageDraw, ImageFont
import os

# Try to find a CJK font
font_paths = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
]

font = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            font = ImageFont.truetype(fp, 32)
            print(f"Using font: {fp}")
            break
        except:
            pass

if font is None:
    print("No CJK font found, trying default")
    font = ImageFont.load_default()

title_font = ImageFont.truetype(fp, 48) if font else None

img = Image.new("RGB", (1200, 800), "white")
draw = ImageDraw.Draw(img)

y = 40
lines = [
    ("项目总结报告", 48),
    ("2026年度第一季度", 28),
    ("", 20),
    ("主要成果：", 32),
    ("1. 完成了Gemma 4模型的本地化部署", 28),
    ("2. 实现了MTP多令牌预测加速", 28),
    ("3. 构建了基于TurboQuant的RAG检索系统", 28),
    ("", 20),
    ("下一步计划：", 32),
    ("• 优化推理速度至50 tok/s以上", 28),
    ("• 支持更多中文场景", 28),
    ("• 发布开源版本", 28),
    ("", 20),
    ("负责人：张三", 28),
    ("日期：2026年7月2日", 28),
]

for text, size in lines:
    if text:
        f = ImageFont.truetype(fp, size) if font else ImageFont.load_default()
        draw.text((80, y), text, fill="black", font=f)
        y += size + 10
    else:
        y += size

img.save("/tmp/chinese_report.png")
print(f"Saved to /tmp/chinese_report.png ({img.size})")
