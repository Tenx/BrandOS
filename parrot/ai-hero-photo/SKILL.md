---
name: ai-hero-photo
description: AI 主图生成：根据产品类型自动分支。服装类→双图输入（模特参考图+平铺图）；非服装类→单图输入（产品实拍）→生成并运行 generate_hero.py。支持 Replicate (openai/gpt-image-2)，国内可切换硅基流动。Use when the user wants to generate ecommerce hero images for any handmade or physical product.
---

# AI Hero Photo

为任意实物产品生成专业电商主图，输出 4 张不同视角/场景的主图。

根据产品类型自动走不同路径：

| 产品类型 | 路径 | 输入 |
|----------|------|------|
| 服装 / 上身穿戴 | 双图合成 | 模特参考图 + 服装平铺图 |
| 非服装（香薰、珠宝、摆件、食品等） | 单图直调 | 产品实拍图 |

---

## 路径 A — 服装类（双图合成）

### Step 1 — 配置 API Token

首次使用，运行：

```bash
python3 ~/.agents/skills/ai-hero-photo/scripts/generate.py --setup
```

Token 存入 `~/.ai-hero-photo/config.json`。

### Step 2 — 生成主图

```bash
python3 ~/.agents/skills/ai-hero-photo/scripts/generate.py \
  --model-ref /path/to/model_reference.jpg \
  --garment  /path/to/garment_flatlay.jpg \
  --product  "奶油色钩织背心"
```

干跑（只预览 prompt）：加 `--dry-run`

指定输出目录：加 `--output-dir ~/Desktop/my-product`

### 输入图片准备

| 图片 | 要求 |
|------|------|
| **模特参考图** | 任意一张喜欢的模特照，选脸型/发型 |
| **服装平铺图** | 白底或干净背景，产品占画面 70%，自然光竖拍 |

### 输出（服装类）

- `output/look_1_full_front.png` — 正面全身
- `output/look_2_waist_up.png` — 45度上半身
- `output/look_3_back.png` — 背面结构
- `output/look_4_detail.png` — 细节特写
- `output/collage.png` — 2×2 合图

### API 渠道切换

默认 Replicate；国内切硅基流动加 `--provider siliconflow`（需在 config.json 补 `siliconflow_api_key`）。

### Prompt 公式（服装类）

```
[模特参考] + [服装] → 4-view photorealistic fashion shoot
正面全身 · 45度上半身 · 背面 · 细节特写
背景：极简日式石灰墙，柔和自然光
严格保持服装颜色/纹理/款型不变
```

`--style` 可切换：`minimal`（默认）/ `lifestyle` / `outdoor`

---

## 路径 B — 非服装类（单图直调）

适用于：香薰、珠宝、摆件、食品、文创、家居等。

### Step 1 — 准备产品实拍图

一张清晰的产品照即可（JPG/PNG）。大于 4MB 用 Replicate Files API 上传，不用 base64。

### Step 2 — 生成 generate_hero.py

根据品牌和产品特性，生成一个专属脚本，包含 4 个场景 shot：

| Shot | 典型场景 |
|------|----------|
| `01_flatlay` | 平铺，暖色亚麻/大理石背景，柔和侧光 |
| `02_mood_vignette` | 单品搭配道具（咖啡杯/书本/植物），氛围感 |
| `03_gift_closeup` | 双手捧持或礼物场景，体现礼品感 |
| `04_multi_sku_spread` | 多款陈列，产品目录感 |

脚本模板（参考 `customers/emotions/hero-photos/generate_hero.py`）：

```python
PRODUCT_IMG = str(Path(__file__).parent.parent / "product-photos/<product>.jpg")
OUT_DIR = Path(__file__).parent / "output"

SHOTS = [
    {"name": "01_flatlay",       "prompt": "..."},
    {"name": "02_mood_vignette", "prompt": "..."},
    {"name": "03_gift_closeup",  "prompt": "..."},
    {"name": "04_multi_sku_spread", "prompt": "..."},
]
```

Replicate API 参数（固定不变）：
```python
"version": "225c978a7f938acc350564c4548ddc2476bfb33364bec6b5422227f55ce56bd3",
"input": {"prompt": prompt, "image": image_url, "quality": "high",
          "size": "1024x1024", "output_format": "png"}
```

Token 读取顺序：`~/.ai-hero-photo/config.json` → `~/.claude/projects/hazumi/image_processing/.openai_config.json`

### Step 3 — 运行脚本

```bash
mkdir -p customers/<brand>/hero-photos/output
python3 customers/<brand>/hero-photos/generate_hero.py
```

每张约 2–3 分钟，4 张合计约 10 分钟。

### 输出（非服装类）

- `output/01_flatlay.png`
- `output/02_mood_vignette.png`
- `output/03_gift_closeup.png`
- `output/04_multi_sku_spread.png`

---

## 常见问题

**生成太慢？** Replicate gpt-image-2 正常 2–3 分钟/张，无法加速。

**颜色/造型跑偏？** 在 prompt 里加强产品描述，如 `"white slim box with oval color marker, exact packaging preserved"`。

**图片模糊？** 用 Upscayl 4× 放大（免费，https://upscayl.org）。

---

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "parrot": {
    "hero_photos": {
      "method": "dual-input | replicate-direct",
      "script": "customers/<brand>/hero-photos/generate_hero.py",
      "files": [
        "output/01_flatlay.png",
        "output/02_mood_vignette.png",
        "output/03_gift_closeup.png",
        "output/04_multi_sku_spread.png"
      ]
    }
  }
}
```
