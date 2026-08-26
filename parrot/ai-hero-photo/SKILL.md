---
name: ai-hero-photo
description: AI 主图生成：统一脚本 generate.py，用 --mode 切换。服装类→双图输入（模特参考图+平铺图）；非服装类→单图输入（产品实拍）。两模式都一次 API 出 2×2 合图→本地切 4 张。支持 Replicate (openai/gpt-image-2)，国内可切换硅基流动。Use when the user wants to generate ecommerce hero images for any handmade or physical product.
---

# AI Hero Photo

用同一个 `generate.py` 为任意实物产品生成专业电商主图，输出 4 张不同视角/场景的主图。**两模式都一次 API 出 2×2 合图 → 本地切 4 张**（省钱）：

| 产品类型 | 模式 | 输入 |
|----------|------|------|
| 服装 / 上身穿戴 | `--mode garment`（默认） | 模特参考图 + 服装平铺图（双图） |
| 非服装（香薰、珠宝、摆件、食品等） | `--mode product` | 产品实拍图（单图） |

两种模式都只调 **1 次 API**，本地切 2×2（每格约 512px，可 Upscayl 放大）。

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
  --mode garment \
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

## 路径 B — 非服装类（单图实拍，同一脚本 `--mode product`）

适用于：香薰、珠宝、摆件、食品、文创、家居等。**用同一个 `generate.py`**，加 `--mode product`：单图输入 → 一次 API 出 2×2 四视角合图 → 本地切 4 张。**只调 1 次 API**（不再每 shot 一次，扣费与服装模式一致）。

### Step 1 — 准备产品实拍图

一张清晰的产品照即可（JPG/PNG）。

### Step 2 — 生成主图

```bash
python3 ~/.agents/skills/ai-hero-photo/scripts/generate.py \
  --mode product \
  --product-img /path/to/实拍图.jpg \
  --product "a ceramic incense holder"
```

- `--product` 只传**一句话英文品类**（`a ceramic incense holder` / `a handheld portable fan`），**不要描述外观细节**。
- 干跑加 `--dry-run`；指定输出加 `--output-dir`；国内切硅基流动加 `--provider siliconflow`。

### ⚠️ 保真铁律（防止 AI 把产品重新设计跑偏）

实测最大坑：prompt 里**用文字描述产品外观**（如"8 片花瓣扇叶"），会诱导 AI 按文字**重画**产品，结果跟实物差很多。**输入图才是唯一真相，文字只描述场景。**

`product` 模式的 prompt 已**内置保真锁**（脚本 `build_product_prompt()` / `FIDELITY_LOCK`），开头即锁定"recreate the EXACT product… do NOT redesign/stylize/simplify"，四格场景变、产品不变。所以只需传对 `--product` 品类一句话即可，无需自己拼 prompt。

### 输出（product 模式）

一次 API 出一张 2×2 合图，本地切 4 张 + 保留合图：

- `output/shot_1_flatlay.png` — studio hero 平铺
- `output/shot_2_mood.png` — 氛围场景（道具）
- `output/shot_3_giftcloseup.png` — 双手捧持礼品感
- `output/shot_4_detail.png` — 材质/纹理特写
- `output/collage.png` — 原始 2×2 合图（备用）

**⚠️ 每格约 512px**（合图切割导致分辨率下降），细节特写建议用 Upscayl 4× 放大再上传。

> 旧客户（emotions/shenbox/fulu/gust）仍保留各自的 `generate_hero.py`（每 shot 独立高清，4× 扣费），**不动**；新项目一律走 `--mode product`。

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
      "method": "garment-dual-input | product-single-input",
      "script": "generate.py --mode garment | --mode product",
      "files": [
        "output/shot_1_flatlay.png",
        "output/shot_2_mood.png",
        "output/shot_3_giftcloseup.png",
        "output/shot_4_detail.png",
        "output/collage.png"
      ]
    }
  }
}
```
