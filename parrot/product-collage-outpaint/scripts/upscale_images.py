#!/usr/bin/env python3
"""Upscale already-split product images while preserving handmade product detail."""

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, List

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


DEFAULT_MODEL = "nightmareai/real-esrgan"


def load_replicate_token(config_path: Path) -> str:
    config = json.loads(config_path.read_text())
    token = config.get("replicate_api_token")
    if not token:
        raise RuntimeError(f"Missing replicate_api_token in {config_path}")
    return token


def expand_sources(sources: Iterable[Path]) -> List[Path]:
    paths: List[Path] = []
    for source in sources:
        if source.is_dir():
            paths.extend(
                sorted(
                    path
                    for path in source.iterdir()
                    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                )
            )
        elif source.exists():
            paths.append(source)
        else:
            raise SystemExit(f"Missing source: {source}")
    return paths


def download_replicate_output(output) -> bytes:
    import requests

    if isinstance(output, list):
        output = output[0]
    if hasattr(output, "read"):
        return output.read()
    url = output.url if hasattr(output, "url") else str(output)
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    return response.content


def save_contact_sheet(paths: List[Path], output_path: Path) -> None:
    if not paths:
        return
    thumb_w, thumb_h = 220, 280
    cols = min(3, len(paths))
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (thumb_w * cols, rows * (thumb_h + 32)), (250, 248, 244))
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        col = index % cols
        row = index // cols
        x = col * thumb_w + (thumb_w - image.width) // 2
        y = row * (thumb_h + 32)
        sheet.paste(image, (x, y))
        draw.text((col * thumb_w + 6, y + thumb_h + 8), path.stem[:28], fill=(35, 35, 35))
    sheet.save(output_path, dpi=(300, 300))


def upscale_local(source: Path, output: Path, args: argparse.Namespace) -> None:
    """Conservative upscale that does not hallucinate stitches or garment texture."""
    output.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(source).convert("RGB")
    target_size = (round(image.width * args.scale), round(image.height * args.scale))
    final = image.resize(target_size, Image.Resampling.LANCZOS)
    final = ImageEnhance.Contrast(final).enhance(args.contrast)
    final = ImageEnhance.Sharpness(final).enhance(args.sharpness)
    final = final.filter(
        ImageFilter.UnsharpMask(
            radius=args.unsharp_radius,
            percent=args.unsharp_percent,
            threshold=args.unsharp_threshold,
        )
    )
    final.save(output, dpi=(args.dpi, args.dpi))


def upscale_replicate(source: Path, output: Path, args: argparse.Namespace) -> None:
    import replicate

    output.parent.mkdir(parents=True, exist_ok=True)
    params = {
        "image": source.open("rb"),
        "scale": args.scale,
        "face_enhance": args.face_enhance,
    }
    try:
        result = replicate.run(args.model, input=params)
        output.write_bytes(download_replicate_output(result))
    finally:
        for value in params.values():
            if hasattr(value, "close"):
                value.close()

    final = Image.open(output).convert("RGB")
    final.save(output, dpi=(args.dpi, args.dpi))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path, help="Image files or directories of images.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--method", choices=["local", "replicate"], default="local")
    parser.add_argument("--replicate-config", type=Path, default=Path("image_processing/.openai_config.json"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--scale", type=float, default=4)
    parser.add_argument("--face-enhance", action="store_true")
    parser.add_argument("--contrast", type=float, default=1.04)
    parser.add_argument("--sharpness", type=float, default=1.18)
    parser.add_argument("--unsharp-radius", type=float, default=1.0)
    parser.add_argument("--unsharp-percent", type=int, default=80)
    parser.add_argument("--unsharp-threshold", type=int, default=4)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--suffix", default="_upscaled")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.method == "replicate":
        os.environ["REPLICATE_API_TOKEN"] = load_replicate_token(args.replicate_config)
    sources = expand_sources(args.sources)
    outputs: List[Path] = []

    for index, source in enumerate(sources, start=1):
        output = args.output_dir / f"{source.stem}{args.suffix}.png"
        if args.method == "replicate":
            method = args.model
            upscale_replicate(source, output, args)
        else:
            method = "local-detail-preserve"
            upscale_local(source, output, args)
        print(f"Upscaled {source.name} ({index}/{len(sources)}) with {method} scale={args.scale}")
        width, height = Image.open(output).size
        print(f"  saved {output} ({width}x{height})")
        outputs.append(output)

    save_contact_sheet(outputs, args.output_dir / "QA_contact_sheet.png")


if __name__ == "__main__":
    main()
