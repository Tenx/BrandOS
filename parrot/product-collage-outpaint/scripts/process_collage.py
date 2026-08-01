#!/usr/bin/env python3
"""
Split product collage panels, center them on 3:4 canvases, and outpaint margins.
"""

import argparse
import json
import math
import os
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage


DEFAULT_PROMPT = (
    "Extend only the surrounding photo background to fill the canvas. "
    "Preserve the original model, garment, crochet texture, colors, skin, face, hands, "
    "pose, jewelry, and product details exactly as they are. Generate natural continuation "
    "of the existing wall, floor, furniture, outdoor scenery, sunlight, shadows, and "
    "photographic texture. No new clothing, no text, no watermark, no extra people, "
    "no repeated figures, no collage layout, no photo frames, no thumbnails, no new scene, "
    "no changes inside the preserved product photo area."
)


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return value or "collage"


def parse_target(value: str) -> Optional[Tuple[int, int]]:
    if value.lower() == "auto":
        return None
    match = re.fullmatch(r"(\d+)x(\d+)", value.lower())
    if not match:
        raise argparse.ArgumentTypeError("target must look like 1080x1440 or auto")
    return int(match.group(1)), int(match.group(2))


def find_runs(values: np.ndarray, threshold: float, min_len: int) -> List[Tuple[int, int]]:
    runs: List[Tuple[int, int]] = []
    start: Optional[int] = None
    for index, value in enumerate(values):
        if value >= threshold and start is None:
            start = index
        if (value < threshold or index == len(values) - 1) and start is not None:
            end = index - 1 if value < threshold else index
            if end - start + 1 >= min_len:
                runs.append((start, end))
            start = None
    return runs


def detect_boxes(
    image: Image.Image,
    *,
    white_threshold: int,
    density_threshold: float,
    min_panel_area: int,
) -> List[Tuple[int, int, int, int]]:
    arr = np.asarray(image.convert("RGB"))
    near_white = (
        (arr[:, :, 0] >= white_threshold)
        & (arr[:, :, 1] >= white_threshold)
        & (arr[:, :, 2] >= white_threshold)
    )
    row_density = near_white.mean(axis=1)
    col_density = near_white.mean(axis=0)

    gutter = np.zeros(near_white.shape, dtype=bool)
    for start, end in find_runs(col_density, density_threshold, 2):
        gutter[:, start : end + 1] = near_white[:, start : end + 1]
    for start, end in find_runs(row_density, density_threshold, 2):
        gutter[start : end + 1, :] = near_white[start : end + 1, :]

    # Make thin gutters continuous, but keep the expansion small so white walls
    # inside photos are not turned into separators.
    gutter = ndimage.binary_dilation(gutter, iterations=1)
    content = ~gutter
    labels, count = ndimage.label(content)

    boxes: List[Tuple[int, int, int, int]] = []
    image_area = image.width * image.height
    min_area = max(min_panel_area, int(image_area * 0.015))
    for label in range(1, count + 1):
        ys, xs = np.where(labels == label)
        if len(xs) < min_area:
            continue
        left, right = int(xs.min()), int(xs.max()) + 1
        top, bottom = int(ys.min()), int(ys.max()) + 1
        width, height = right - left, bottom - top
        if width < 80 or height < 80:
            continue
        boxes.append((left, top, right, bottom))

    boxes.sort(key=lambda box: (box[1], box[0]))
    return boxes


def save_contact_sheet(paths: List[Path], output_path: Path) -> None:
    if not paths:
        return
    thumb_w, thumb_h = 220, 280
    cols = min(3, len(paths))
    rows = math.ceil(len(paths) / cols)
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


def split_collage(args: argparse.Namespace, source: Path, base_output: Path) -> List[Path]:
    image = Image.open(source).convert("RGB")
    boxes = detect_boxes(
        image,
        white_threshold=args.white_threshold,
        density_threshold=args.density_threshold,
        min_panel_area=args.min_panel_area,
    )

    split_dir = base_output / "split"
    split_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    digits = max(2, len(str(len(boxes))))
    for index, box in enumerate(boxes, start=1):
        crop = image.crop(box)
        out = split_dir / f"{index:0{digits}d}_crop.png"
        crop.save(out, dpi=(args.dpi, args.dpi))
        outputs.append(out)

    save_contact_sheet(outputs, split_dir / "QA_contact_sheet.png")
    print(f"{source.name}: detected {len(boxes)} panels")
    return outputs


def target_for_size(size: Tuple[int, int], aspect_width: int = 3, aspect_height: int = 4) -> Tuple[int, int]:
    """Return the smallest 3:4 canvas that contains a crop without upscaling."""
    max_width, max_height = size
    target_ratio = aspect_width / aspect_height
    if max_width / max_height > target_ratio:
        width = max_width
        height = math.ceil(width / target_ratio)
    else:
        height = max_height
        width = math.ceil(height * target_ratio)
    return width, height


def shared_auto_target(crops: List[Path]) -> Tuple[int, int]:
    """Return one shared 3:4 canvas that contains every crop without upscaling."""
    sizes = [Image.open(path).size for path in crops]
    max_width = max(width for width, _height in sizes)
    max_height = max(height for _width, height in sizes)
    return target_for_size((max_width, max_height))


def border_average_color(image: Image.Image, border: int = 12) -> Tuple[int, int, int]:
    arr = np.asarray(image.convert("RGB"))
    border = max(1, min(border, image.width // 4, image.height // 4))
    samples = np.concatenate(
        [
            arr[:border, :, :].reshape(-1, 3),
            arr[-border:, :, :].reshape(-1, 3),
            arr[:, :border, :].reshape(-1, 3),
            arr[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    color = np.median(samples, axis=0)
    return tuple(int(channel) for channel in color)


def make_outpaint_inputs(
    source: Path,
    work_dir: Path,
    target: Tuple[int, int],
    min_ai_margin: int,
) -> Tuple[Path, Path, bool]:
    image = Image.open(source).convert("RGB")
    if image.width > target[0] or image.height > target[1]:
        scale = min(target[0] / image.width, target[1] / image.height)
        image = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
    left = (target[0] - image.width) // 2
    top = (target[1] - image.height) // 2
    right = left + image.width
    bottom = top + image.height

    background_color = border_average_color(image)
    canvas = Image.new("RGB", target, background_color)
    shadow = Image.new("RGB", target, background_color)
    shadow.paste(image, (left, top))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.blend(canvas, shadow, 0.15)
    canvas.paste(image, (left, top))

    mask = Image.new("L", target, 0)
    draw = ImageDraw.Draw(mask)
    if left >= min_ai_margin:
        draw.rectangle((0, 0, left - 1, target[1]), fill=255)
    if target[0] - right >= min_ai_margin:
        draw.rectangle((right, 0, target[0], target[1]), fill=255)
    if top >= min_ai_margin:
        draw.rectangle((0, 0, target[0], top - 1), fill=255)
    if target[1] - bottom >= min_ai_margin:
        draw.rectangle((0, bottom, target[0], target[1]), fill=255)

    work_dir.mkdir(parents=True, exist_ok=True)
    canvas_path = work_dir / f"{source.stem}_canvas.png"
    mask_path = work_dir / f"{source.stem}_mask.png"
    canvas.save(canvas_path)
    mask.save(mask_path)
    return canvas_path, mask_path, bool(mask.getbbox())


def load_replicate_token(config_path: Path) -> str:
    config = json.loads(config_path.read_text())
    token = config.get("replicate_api_token")
    if not token:
        raise RuntimeError(f"Missing replicate_api_token in {config_path}")
    return token


def download_replicate_output(output) -> bytes:
    import requests

    if isinstance(output, list):
        output = output[0]
    if hasattr(output, "read"):
        return output.read()
    url = output.url if hasattr(output, "url") else str(output)
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return response.content


def outpaint_flux(
    source: Path,
    output: Path,
    work_dir: Path,
    args: argparse.Namespace,
    target: Tuple[int, int],
) -> None:
    canvas_path, mask_path, needs_ai = make_outpaint_inputs(
        source, work_dir, target, args.min_ai_margin
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if not needs_ai:
        final = Image.open(canvas_path).convert("RGB")
        final.save(output, dpi=(args.dpi, args.dpi))
        return

    import replicate

    os.environ["REPLICATE_API_TOKEN"] = load_replicate_token(args.replicate_config)
    params = {
        "image": open(canvas_path, "rb"),
        "mask": open(mask_path, "rb"),
        "prompt": args.prompt,
        "steps": args.steps,
        "guidance": args.guidance,
        "output_format": "png",
        "safety_tolerance": args.safety_tolerance,
        "prompt_upsampling": False,
    }
    try:
        result = replicate.run(args.model, input=params)
        output.write_bytes(download_replicate_output(result))
        final = Image.open(output).convert("RGB")
        if final.size != target:
            final = final.resize(target, Image.Resampling.LANCZOS)
        final.save(output, dpi=(args.dpi, args.dpi))
    finally:
        for value in params.values():
            if hasattr(value, "close"):
                value.close()


def process_source(args: argparse.Namespace, source: Path) -> None:
    name = slugify(source.stem)
    base_output = args.output_dir / name
    base_output.mkdir(parents=True, exist_ok=True)

    crops = split_collage(args, source, base_output)
    if args.stage == "split":
        return

    shared_target = args.target
    if shared_target:
        print(f"Using fixed 3:4 canvas: {shared_target[0]}x{shared_target[1]}")
        out_dir = base_output / f"outpaint_{shared_target[0]}x{shared_target[1]}_flux_fill"
    else:
        print("Using per-crop source-native 3:4 canvases")
        out_dir = base_output / "outpaint_auto_3x4_flux_fill"
    work_dir = base_output / "_outpaint_work"
    outputs = []
    for index, crop in enumerate(crops, start=1):
        target = shared_target or target_for_size(Image.open(crop).size)
        started = time.time()
        out = out_dir / f"{crop.stem}_{target[0]}x{target[1]}_outpaint.png"
        print(f"Outpainting {source.name} crop {index}/{len(crops)}")
        outpaint_flux(crop, out, work_dir, args, target)
        print(f"  saved {out} ({time.time() - started:.1f}s)")
        outputs.append(out)
    save_contact_sheet(outputs, out_dir / "QA_contact_sheet.png")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "collage_output")
    parser.add_argument("--stage", choices=["split", "outpaint"], default="outpaint")
    parser.add_argument("--target", type=parse_target, default=None, help="Canvas size like 1080x1440, or auto for source-native 3:4.")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--white-threshold", type=int, default=238)
    parser.add_argument("--density-threshold", type=float, default=0.25)
    parser.add_argument("--min-panel-area", type=int, default=12000)
    parser.add_argument("--replicate-config", type=Path, default=Path("image_processing/.openai_config.json"))
    parser.add_argument("--model", default="black-forest-labs/flux-fill-pro")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--guidance", type=float, default=40)
    parser.add_argument("--safety-tolerance", type=int, default=2)
    parser.add_argument("--min-ai-margin", type=int, default=96)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for source in args.sources:
        if not source.exists():
            raise SystemExit(f"Missing source: {source}")
        process_source(args, source)


if __name__ == "__main__":
    main()
