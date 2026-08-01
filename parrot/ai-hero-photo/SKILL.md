---
name: ai-hero-photo
description: AI 主图生成：上传模特参考图 + 产品平铺图，生成专业服装主图。支持 Replicate (openai/gpt-image-2)，国内用户可切换硅基流动。Use when the user wants to generate Etsy/ecommerce hero images for handmade or fashion products using two reference images.
---

# AI Hero Photo

将**模特参考图**和**服装平铺图**合成为专业电商主图。核心方法：双图输入 → GPT Image 2 → 四视角主图。

## 快速开始

### Step 1 — 配置 API Token

首次使用，运行：

```bash
python3 /Users/I742076/.claude/skills/ai-hero-photo/scripts/generate.py --setup
```

按提示填写 Replicate API token（在 https://replicate.com/account/api-tokens 获取）。
Token 存入 `~/.ai-hero-photo/config.json`，不写入任何代码文件。

### Step 2 — 生成主图

```bash
python3 /Users/I742076/.claude/skills/ai-hero-photo/scripts/generate.py \
  --model-ref /path/to/model_reference.jpg \
  --garment  /path/to/garment_flatlay.jpg \
  --product  "奶油色钩织背心"
```

干跑（只预览 prompt，不调 API）：

```bash
python3 ... --dry-run
```

指定输出目录：

```bash
python3 ... --output-dir ~/Desktop/my-product
```

## 输入图片准备

| 图片 | 要求 | 技巧 |
|------|------|------|
| **模特参考图** (`--model-ref`) | 任意一张喜欢的模特照 | 选脸型/发型你想要的那种；Pinterst/小红书找都行 |
| **服装平铺图** (`--garment`) | 手机拍白底或干净背景 | 产品占画面 70%，自然光，竖拍 |

## 输出

- `output/look_1_full_front.png` — 正面全身
- `output/look_2_waist_up.png` — 45度上半身
- `output/look_3_back.png` — 背面结构
- `output/look_4_detail.png` — 领口/细节特写
- `output/collage.png` — 原始 2×2 合图（备用）

## API 渠道切换

默认走 Replicate (`openai/gpt-image-2`)。国内用户如需切换硅基流动：

```bash
python3 ... --provider siliconflow
```

需要在 config.json 里补充 `siliconflow_api_key`（在 https://cloud.siliconflow.cn 申请）。

## Prompt 公式

脚本内置 prompt，结构：

```
[模特参考] + [服装] → 4-view photorealistic fashion shoot
正面全身 · 45度上半身 · 背面 · 细节特写
背景：极简日式石灰墙，柔和自然光
严格保持服装颜色/纹理/款型不变
```

用 `--style` 可切换背景风格：

- `--style minimal`（默认）— 极简白墙
- `--style lifestyle` — 家居生活场景
- `--style outdoor` — 户外自然光

## 常见问题

**服装颜色跑偏？** 在 `--product` 描述里加颜色，如 `"奶油白色钩织背心，颜色不变"`

**生成太慢？** Replicate gpt-image-2 正常 2-5 分钟。加 `--quality standard` 可加速（默认 `auto`）

**图片模糊？** 运行后用 Upscayl 4× 放大（免费，https://upscayl.org）
