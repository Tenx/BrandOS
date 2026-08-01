#!/usr/bin/env python3
"""
AI Hero Photo Generator
=======================
Upload a model reference photo + garment flat-lay → get 4-view professional fashion images.

Usage:
    python3 generate.py --setup                          # first-time config
    python3 generate.py --model-ref x.jpg --garment y.jpg --product "奶油色钩织背心"
    python3 generate.py ... --dry-run                    # preview prompt only
    python3 generate.py ... --style lifestyle            # change background style
    python3 generate.py ... --provider siliconflow       # use SiliconFlow instead of Replicate
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


# ── Config ──────────────────────────────────────────────────────────────────

CONFIG_PATH = Path.home() / ".ai-hero-photo" / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print("❌ 未找到配置文件。请先运行：")
        print("   python3 generate.py --setup")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg


def setup_config() -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    existing: dict = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            existing = json.load(f)

    print("\n=== AI Hero Photo — 初始配置 ===\n")
    print("Step 1: 获取 Replicate API Token")
    print("  → 访问 https://replicate.com/account/api-tokens")
    print("  → 新建 token，复制后粘贴到下方（不会显示，直接回车确认）\n")

    replicate_token = input("Replicate API Token (r8_...): ").strip()
    if not replicate_token:
        replicate_token = existing.get("replicate_api_token", "")

    print("\nStep 2: 硅基流动 API Key（可选，国内备用渠道）")
    print("  → 访问 https://cloud.siliconflow.cn → 控制台 → API Key")
    print("  → 直接回车跳过\n")

    sf_key = input("SiliconFlow API Key (可留空): ").strip()
    if not sf_key:
        sf_key = existing.get("siliconflow_api_key", "")

    cfg = {
        "replicate_api_token": replicate_token,
        "replicate_model": "openai/gpt-image-2",
        "siliconflow_api_key": sf_key,
        "siliconflow_model": "Qwen/Qwen-Image-Edit-2509",
        "quality": "auto",
        "output_format": "png",
    }
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ 配置已保存：{CONFIG_PATH}")
    print("现在可以运行主命令生成图片了。\n")


# ── Prompt ───────────────────────────────────────────────────────────────────

STYLE_BACKGROUNDS = {
    "minimal":   "极简日式石灰白墙背景，柔和漫射自然光，有机投影",
    "lifestyle": "温馨家居场景，木质桌面，午后窗边自然光，温暖质感",
    "outdoor":   "户外自然光，浅色石砖墙或绿植背景，清新明亮",
}


def build_prompt(product: str, style: str = "minimal") -> str:
    bg = STYLE_BACKGROUNDS.get(style, STYLE_BACKGROUNDS["minimal"])
    return (
        f"使用图①的模特（保留其发型和脸部特征），将图②的{product}穿在模特身上，"
        f"生成2×2四视角专业电商服装主图（每格比例2:3）："
        f"① 正面全身电商标准图 "
        f"② 45度侧身上半身产品细节图 "
        f"③ 背面展示服装结构图 "
        f"④ 领口/肩部/纹理特写图。"
        f"背景：{bg}。"
        f"严格保持服装原始颜色、纹理、款型、钩织/编织细节完全不变。"
        f"模特站姿自然放松，高挑身材。"
        f"写实感，高端手工时装大片风格，非广告感，非 AI 感。"
        f"避免暴露、性感化构图，保持端庄时装风格。"
    )


# ── Generation ───────────────────────────────────────────────────────────────

def generate_with_replicate(
    prompt: str,
    model_ref_path: Path,
    garment_path: Path,
    cfg: dict,
) -> bytes:
    try:
        import replicate as replicate_client
        import requests
    except ImportError:
        print("❌ 缺少依赖，请先运行：pip3 install replicate requests")
        sys.exit(1)

    token = cfg.get("replicate_api_token", "")
    if not token:
        print("❌ 未设置 Replicate API Token，请运行 --setup")
        sys.exit(1)

    os.environ["REPLICATE_API_TOKEN"] = token
    model = cfg.get("replicate_model", "openai/gpt-image-2")

    print(f"   🤖 模型：{model}")
    print(f"   ⏳ 生成中（约 2-5 分钟）...")

    with open(model_ref_path, "rb") as f1, open(garment_path, "rb") as f2:
        input_params = {
            "prompt": prompt,
            "aspect_ratio": "1:1",   # 2×2 collage is square overall
            "quality": cfg.get("quality", "auto"),
            "output_format": cfg.get("output_format", "png"),
            "number_of_images": 1,
            "moderation": "auto",
            "input_images": [f1, f2],
        }
        t0 = time.time()
        output = replicate_client.run(model, input=input_params)
        elapsed = time.time() - t0

    print(f"   ✅ 完成（{elapsed:.1f}s）")

    if not output:
        raise RuntimeError("API 返回为空，请检查 token 和网络")

    url = output[0].url if hasattr(output[0], "url") else str(output[0])
    resp = requests.get(url, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"图片下载失败：{resp.status_code}")
    return resp.content


def generate_with_siliconflow(
    prompt: str,
    model_ref_path: Path,
    garment_path: Path,
    cfg: dict,
) -> bytes:
    try:
        import base64
        import requests
    except ImportError:
        print("❌ 缺少依赖，请先运行：pip3 install requests")
        sys.exit(1)

    key = cfg.get("siliconflow_api_key", "")
    if not key:
        print("❌ 未设置 SiliconFlow API Key，请运行 --setup 或使用 --provider replicate")
        sys.exit(1)

    model = cfg.get("siliconflow_model", "Qwen/Qwen-Image-Edit-2509")

    def to_b64(path: Path) -> str:
        suffix = path.suffix.lower().lstrip(".")
        mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
        data = base64.b64encode(path.read_bytes()).decode()
        return f"data:image/{mime};base64,{data}"

    print(f"   🤖 模型：{model}")
    print(f"   ⏳ 生成中...")

    t0 = time.time()
    resp = requests.post(
        "https://api.siliconflow.cn/v1/images/generations",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "prompt": prompt,
            "image": to_b64(model_ref_path),
            "image2": to_b64(garment_path),
        },
        timeout=300,
    )
    elapsed = time.time() - t0

    if resp.status_code != 200:
        raise RuntimeError(f"SiliconFlow 请求失败 {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    print(f"   ✅ 完成（{elapsed:.1f}s）")

    import requests as req2
    url = data["data"][0]["url"]
    img_resp = req2.get(url, timeout=60)
    return img_resp.content


# ── Collage split ─────────────────────────────────────────────────────────────

def split_collage_2x2(image_data: bytes, output_dir: Path) -> list[Path]:
    try:
        from PIL import Image
        import io
    except ImportError:
        print("⚠️  未安装 Pillow，跳过分割。请运行：pip3 install Pillow")
        collage_path = output_dir / "collage.png"
        collage_path.write_bytes(image_data)
        print(f"   已保存合图：{collage_path}")
        return [collage_path]

    img = Image.open(io.BytesIO(image_data))
    w, h = img.size
    hw, hh = w // 2, h // 2

    names = [
        "look_1_full_front.png",
        "look_2_waist_up.png",
        "look_3_back.png",
        "look_4_detail.png",
    ]
    boxes = [
        (0,  0,  hw, hh),
        (hw, 0,  w,  hh),
        (0,  hh, hw, h),
        (hw, hh, w,  h),
    ]

    saved = []
    for name, box in zip(names, boxes):
        crop = img.crop(box)
        path = output_dir / name
        crop.save(path, "PNG", optimize=False, compress_level=1)
        saved.append(path)
        print(f"   💾 {path.name}")

    collage_path = output_dir / "collage.png"
    img.save(collage_path, "PNG")
    saved.append(collage_path)
    return saved


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Hero Photo — 双图合成专业服装主图",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 generate.py --setup
  python3 generate.py --model-ref model.jpg --garment vest.jpg --product "奶油色钩织背心"
  python3 generate.py --model-ref model.jpg --garment vest.jpg --product "蓝色流苏网眼马甲" --style lifestyle --dry-run
""",
    )
    parser.add_argument("--setup", action="store_true", help="初始配置 API Token")
    parser.add_argument("--model-ref", type=Path, help="模特参考图路径")
    parser.add_argument("--garment", type=Path, help="服装平铺图路径")
    parser.add_argument("--product", type=str, help="产品描述，如「奶油色钩织背心」")
    parser.add_argument("--style", choices=["minimal", "lifestyle", "outdoor"],
                        default="minimal", help="背景风格（默认 minimal）")
    parser.add_argument("--provider", choices=["replicate", "siliconflow"],
                        default="replicate", help="API 渠道（默认 replicate）")
    parser.add_argument("--output-dir", type=Path, help="输出目录（默认当前目录/output）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览 prompt，不调用 API")
    args = parser.parse_args()

    if args.setup:
        setup_config()
        return

    # Validate required args
    missing = [f for f in ("model_ref", "garment", "product") if not getattr(args, f.replace("-", "_"))]
    if missing:
        parser.error(f"缺少参数：{', '.join('--' + m.replace('_', '-') for m in missing)}")

    for label, path in [("--model-ref", args.model_ref), ("--garment", args.garment)]:
        if not path.exists():
            print(f"❌ 文件不存在：{label} {path}")
            sys.exit(1)

    prompt = build_prompt(args.product, args.style)

    print("\n=== AI Hero Photo ===")
    print(f"模特参考：{args.model_ref}")
    print(f"服装图：  {args.garment}")
    print(f"产品描述：{args.product}")
    print(f"背景风格：{args.style}")
    print(f"API 渠道：{args.provider}")
    print(f"\nPrompt 预览：\n{prompt}\n")

    if args.dry_run:
        print("✅ Dry-run 完成，未调用 API。确认 prompt 后去掉 --dry-run 正式生成。")
        return

    cfg = load_config()

    output_dir = args.output_dir or Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n⏳ 开始生成...")
    try:
        if args.provider == "siliconflow":
            image_data = generate_with_siliconflow(prompt, args.model_ref, args.garment, cfg)
        else:
            image_data = generate_with_replicate(prompt, args.model_ref, args.garment, cfg)
    except Exception as e:
        print(f"\n❌ 生成失败：{e}")
        sys.exit(1)

    print(f"\n📂 保存到 {output_dir}/")
    split_collage_2x2(image_data, output_dir)

    print(f"\n✅ 完成！共 4 张主图 + 1 张合图")
    print(f"   路径：{output_dir.resolve()}")
    print(f"\n💡 提示：用 Upscayl（免费）放大到 2000×2000px 再上传 Etsy")
    print(f"   下载：https://upscayl.org\n")


if __name__ == "__main__":
    main()
