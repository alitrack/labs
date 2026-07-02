#!/usr/bin/env python3
"""Final OCR benchmark: Qwen3.6 raw prompt, all 5 images, 2048 tokens."""
import os, time, sys, re
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

from mlx_vlm import load, generate
from mlx_vlm.utils import load_image
import Levenshtein

IMAGES = [
    ("01_report.png", "2026年第二季度经营分析报告 一、收入概况 本季度实现营业收入12,856,000元，同比增长23.7%。其中：产品销售收入8,420,000元，技术服务收入4,436,000元。二、成本分析 研发支出：3,210,000元（占比25.0%）市场推广：1,850,000元（占比14.4%）人力成本：4,520,000元（占比35.2%）三、关键指标 •毛利率：42.8%（上季度39.1%）•客户留存率：87.3% •新增企业客户：47家"),
    ("02_invoice.png", "增值税电子普通发票 发票代码：044002200111 发票号码：89012345 开票日期：2026年07月02日 购买方：杭州猿通信息科技有限责任公司 统一社会信用代码：91330108MA2XXXXXXX 货物或应税劳务名称：AI模型部署技术服务 金额：¥48,000.00 税率：6% 税额：¥2,880.00 价税合计：¥50,880.00"),
    ("03_tech_doc.png", "TurboQuant RAG Pipeline 技术规范 v2.1 1.Overview TurboQuant is a data-oblivious quantizer by Google Research, achieving near-optimal distortion for 4-bit vector compression. 2.MTP Speculative Decoding（多令牌预测加速）MTP(Multi-Token Prediction)使用小型drafter模型提前预测多个token，由主模型Gemma4 12B一次性验证。实测加速1.3-1.8×。3.Performance Metrics •Decode speed:59.8tok/s(dflash-mlx on M3 Ultra) •Acceptance rate:70.5%-84.0% •Memory:17.5GB(RSS),16.5GB(MLX active) 4.API Endpoint POST /v1/chat/completions→OpenAI-compatible"),
    ("04_table.png", "2026年度模型性能对比表 模型 参数量 OCR精度 推理速度 Gemma4 12B(4-bit) 12B 62.3% 2.1s Qwen3.6 27B(4-bit) 27B 100% 8.0s Qwen3-VL 8B(4-bit) 8B 96.8% 3.2s DeepSeek OCR-2 - 99.2% -"),
    ("05_contract.png", "技术服务合同（节选）合同编号：HT-2026-0702-001 甲方：杭州猿通信息科技有限责任公司 乙方：北京智源人工智能研究院 第一条 服务内容 乙方为甲方提供Gemma4与Qwen3.6模型的本地化部署及OCR性能对比评测服务，包括但不限于：（一）多模型中文文档识别准确率测试（二）推理速度基准测试及优化建议（三）RAG增强OCR管道搭建与调优 第二条 合同金额：人民币贰拾万元整（¥200,000.00）"),
]

def strip_thinking(text):
    text = re.sub(r'<\|channel\|>thought.*?<channel\|>', '', text, flags=re.DOTALL)
    text = re.sub(r'<\|(?:channel|image|audio|video)\|?>', '', text)
    text = re.sub(r'</?think>', '', text)
    text = re.sub(r'<bos>|<eos>', '', text)
    text = re.sub(r'^(?:The user wants|I need to|Let me|Here is|用户要求).*?\n', '', text, flags=re.IGNORECASE|re.MULTILINE)
    return text.strip()

def normalize(text):
    text = re.sub(r'\s+', '', text)
    for a, b in [('：','：'),('，',','),('。','.'),('（','('),('）',')'),('、',','),('•','*'),('：',':'),('—','-')]:
        text = text.replace(a, b) if a != '：' else text.replace('：', ':')
    text = text.replace('：', ':')
    return text

def cer(pred, gt):
    if not gt: return 1.0 if pred else 0.0
    return Levenshtein.distance(pred, gt) / len(gt)

# ── Run ──
print("=" * 65)
print("  Qwen3.6 27B (4-bit) Chinese OCR Benchmark")
print("  macOS M3 Ultra 256GB | mlx-vlm 0.6.3 | raw vision prompt")
print("=" * 65)

model, processor = load("mlx-community/Qwen3.6-27B-4bit")

total_time = 0
total_cer = 0

for fname, gt in IMAGES:
    img_path = f"/tmp/ocr_benchmark/{fname}"
    image = load_image(img_path)
    
    prompt = "<|vision_start|><|image_pad|><|vision_end|>OCR:\n"
    
    t0 = time.time()
    result = generate(model, processor, prompt=prompt, image=image,
                     max_tokens=2048, temperature=0.0, verbose=False)
    elapsed = time.time() - t0
    
    raw = result.text if hasattr(result, "text") else str(result)
    clean = strip_thinking(raw)
    err = cer(normalize(clean), normalize(gt))
    
    total_time += elapsed
    total_cer += err
    
    # Show first 150 chars of output
    display = clean[:150].replace('\n', ' ')
    print(f"\n{'─'*60}")
    print(f"  {fname}")
    print(f"  ⏱ {elapsed:.1f}s | CER: {err:.1%} | ACC: {(1-err)*100:.1f}%")
    print(f"  → {display}")

avg_cer = total_cer / len(IMAGES)
print(f"\n{'='*65}")
print(f"  TOTAL: {total_time:.1f}s | AVG CER: {avg_cer:.1%} | AVG ACC: {(1-avg_cer)*100:.1f}%")
print(f"{'='*65}")
