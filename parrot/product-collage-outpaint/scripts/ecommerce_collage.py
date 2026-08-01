#!/usr/bin/env python3
"""Turn low-resolution product collages into opaque 3:4 ecommerce images."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage


Box = Tuple[int, int, int, int]


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return value or "collage"


def parse_target(value: str) -> Tuple[int, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", value.lower())
    if not match:
        raise argparse.ArgumentTypeError("target must look like 1200x1600")
    width, height = int(match.group(1)), int(match.group(2))
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("target dimensions must be positive")
    if round(width / height, 4) != round(3 / 4, 4):
        raise argparse.ArgumentTypeError("target must be a 3:4 size, for example 1200x1600")
    return width, height


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
) -> List[Box]:
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

    gutter = ndimage.binary_dilation(gutter, iterations=1)
    labels, count = ndimage.label(~gutter)

    boxes: List[Box] = []
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


def add_bleed(box: Box, image_size: Tuple[int, int], bleed: int) -> Box:
    left, top, right, bottom = box
    width, height = image_size
    return (
        max(0, left - bleed),
        max(0, top - bleed),
        min(width, right + bleed),
        min(height, bottom + bleed),
    )


def resize_cover(image: Image.Image, target: Tuple[int, int]) -> Image.Image:
    target_w, target_h = target
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def resize_contain(image: Image.Image, target: Tuple[int, int], max_fill: float) -> Image.Image:
    target_w, target_h = target
    scale = min(target_w * max_fill / image.width, target_h * max_fill / image.height)
    return image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )


def enhance_detail(image: Image.Image, args: argparse.Namespace) -> Image.Image:
    final = ImageEnhance.Contrast(image).enhance(args.contrast)
    final = ImageEnhance.Sharpness(final).enhance(args.sharpness)
    return final.filter(
        ImageFilter.UnsharpMask(
            radius=args.unsharp_radius,
            percent=args.unsharp_percent,
            threshold=args.unsharp_threshold,
        )
    )


def compose_ecommerce_image(crop: Image.Image, target: Tuple[int, int], args: argparse.Namespace) -> Image.Image:
    crop = crop.convert("RGB")
    target_w, target_h = target
    crop_ratio = crop.width / crop.height
    target_ratio = target_w / target_h
    ratio_delta = abs(crop_ratio - target_ratio) / target_ratio

    if args.fit == "cover" or (args.fit == "auto" and ratio_delta <= args.cover_tolerance):
        final = resize_cover(crop, target)
    else:
        background = resize_cover(crop, target).filter(ImageFilter.GaussianBlur(args.blur_radius))
        background = ImageEnhance.Brightness(background).enhance(args.background_brightness)
        foreground = resize_contain(crop, target, args.max_foreground_fill)
        final = background.copy()
        left = (target_w - foreground.width) // 2
        top = (target_h - foreground.height) // 2
        final.paste(foreground, (left, top))

    return enhance_detail(final.convert("RGB"), args)


def save_image(image: Image.Image, path: Path, args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = image.convert("RGB")
    if args.format == "jpg":
        image.save(path.with_suffix(".jpg"), quality=args.quality, optimize=True, dpi=(args.dpi, args.dpi))
    else:
        image.save(path.with_suffix(".png"), dpi=(args.dpi, args.dpi))


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


def process_source(args: argparse.Namespace, source: Path) -> None:
    image = Image.open(source).convert("RGB")
    name = slugify(source.stem)
    base_output = args.output_dir / name
    split_dir = base_output / "split"
    final_dir = base_output / f"listing_ready_{args.target[0]}x{args.target[1]}"
    split_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    boxes = detect_boxes(
        image,
        white_threshold=args.white_threshold,
        density_threshold=args.density_threshold,
        min_panel_area=args.min_panel_area,
    )
    print(f"{source.name}: detected {len(boxes)} panels")

    split_paths: List[Path] = []
    final_paths: List[Path] = []
    manifest = {
        "source": str(source),
        "target": f"{args.target[0]}x{args.target[1]}",
        "fit": args.fit,
        "format": args.format,
        "opaque_rgb": True,
        "panels": [],
    }
    digits = max(2, len(str(len(boxes))))
    for index, box in enumerate(boxes, start=1):
        safe_box = add_bleed(box, image.size, args.bleed)
        crop = image.crop(safe_box).convert("RGB")

        split_path = split_dir / f"{index:0{digits}d}_crop.png"
        crop.save(split_path, dpi=(args.dpi, args.dpi))
        split_paths.append(split_path)

        final = compose_ecommerce_image(crop, args.target, args)
        final_path = final_dir / f"{index:0{digits}d}_listing"
        save_image(final, final_path, args)
        saved_path = final_path.with_suffix(".jpg" if args.format == "jpg" else ".png")
        final_paths.append(saved_path)

        manifest["panels"].append(
            {
                "index": index,
                "detected_box": box,
                "crop_box_with_bleed": safe_box,
                "crop_size": crop.size,
                "final": str(saved_path),
            }
        )

    save_contact_sheet(split_paths, split_dir / "QA_contact_sheet.png")
    save_contact_sheet(final_paths, final_dir / "QA_contact_sheet.png")
    (base_output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"saved listing-ready images: {final_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "collage_output")
    parser.add_argument("--target", type=parse_target, default=(1200, 1600))
    parser.add_argument("--fit", choices=["auto", "cover", "contain"], default="auto")
    parser.add_argument("--cover-tolerance", type=float, default=0.12)
    parser.add_argument("--max-foreground-fill", type=float, default=0.96)
    parser.add_argument("--blur-radius", type=float, default=24)
    parser.add_argument("--background-brightness", type=float, default=0.96)
    parser.add_argument("--bleed", type=int, default=0)
    parser.add_argument("--format", choices=["png", "jpg"], default="png")
    parser.add_argument("--quality", type=int, default=94)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--contrast", type=float, default=1.04)
    parser.add_argument("--sharpness", type=float, default=1.14)
    parser.add_argument("--unsharp-radius", type=float, default=0.8)
    parser.add_argument("--unsharp-percent", type=int, default=65)
    parser.add_argument("--unsharp-threshold", type=int, default=5)
    parser.add_argument("--white-threshold", type=int, default=238)
    parser.add_argument("--density-threshold", type=float, default=0.25)
    parser.add_argument("--min-panel-area", type=int, default=12000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for source in args.sources:
        if not source.exists():
            raise SystemExit(f"Missing source: {source}")
        process_source(args, source)


if __name__ == "__main__":
    main()
