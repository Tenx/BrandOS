---
name: product-collage-outpaint
description: Batch process product collage images that contain multiple fashion/product looks in one PNG/JPG. Use when the user asks to split/crop a collage into opaque 3:4 ecommerce images, improve display resolution without hallucinating handmade crochet/knit details, or optionally extend backgrounds with FLUX/Replicate while preserving the original garment/product.
---

# Product Collage Outpaint

Use this skill for the Hazumi-style workflow where one source image contains several product/model photos separated by white gutters or collage panels, and the desired output is a clean folder of individual listing-ready 3:4 ecommerce images.

## Default Workflow

1. Preserve the original file. Never overwrite source images.
2. Detect collage panel boundaries from white gutters or connected image regions.
3. Crop each panel from the original image. Keep all panels; do not dedupe.
4. Generate opaque RGB listing-ready images at a fixed `3:4` target, default `1200x1600`.
5. If a crop is already close to `3:4`, scale it to cover the target so there is no border.
6. If a crop is far from `3:4`, preserve the full product crop over an opaque blurred-photo background instead of cutting off the garment.
7. Use local resize plus restrained sharpening by default. Do not use AI super-resolution for crochet/knit details unless explicitly requested.
8. Save split crops, listing-ready images, `manifest.json`, and `QA_contact_sheet.png`.
9. Visually inspect the contact sheet. Watch for border artifacts, transparency, changed garment texture, changed body/face/pose, or repeated duplicate panels.

## Script

Use the ecommerce script for the default repeatable pipeline:

```bash
python /Users/I742076/.codex/skills/product-collage-outpaint/scripts/ecommerce_collage.py \
  /path/to/source.png \
  --output-dir /path/to/output_parent \
  --target 1200x1600 \
  --fit auto \
  --format png
```

Use the older outpaint script only when the user explicitly wants FLUX background extension:

```bash
python /Users/I742076/.codex/skills/product-collage-outpaint/scripts/process_collage.py \
  /path/to/source.png \
  --output-dir /path/to/output_parent \
  --target auto \
  --dpi 300
```

Common modes:

```bash
# Split only with the older script
python .../process_collage.py source.png --stage split

# Split, center on source-native 3:4 canvas, then FLUX outpaint masked margins
python .../process_collage.py source.png --stage outpaint --replicate-config /path/to/.openai_config.json

# Upscale low-resolution split or product images after QA
python .../scripts/upscale_images.py /path/to/image_dir \
  --output-dir /path/to/upscaled_4x \
  --scale 4

# Optional AI upscale only when preserving exact stitch texture is less important
python .../scripts/upscale_images.py /path/to/image_dir \
  --output-dir /path/to/ai_upscaled_4x \
  --method replicate \
  --replicate-config /path/to/.openai_config.json \
  --scale 4
```

For this project, prefer:

```bash
--replicate-config /Users/I742076/.claude/projects/hazumi/image_processing/.openai_config.json
```

## Ecommerce Output Rules

- Default target: `1200x1600` PNG, opaque RGB, no alpha channel.
- Do not output transparent margins, checkerboards, white gutters, or visible collage dividers.
- Default `--fit auto`:
  - close to `3:4`: cover the target with the crop;
  - not close to `3:4`: preserve the full crop over a blurred opaque version of the same photo.
- Use `--fit cover` only when it is safe to crop edges.
- Use `--fit contain` when preserving the full panel matters more than filling the frame naturally.
- For handmade crochet/knit listings, real stitch texture is more important than synthetic sharpness. Prefer local resize/sharpening over AI reconstruction.

## Outpainting Rules

- Use `black-forest-labs/flux-fill-pro` through Replicate by default when a Replicate token exists.
- Build a `1080x1440` canvas, paste the crop in the center, and make the original crop rectangle black in the mask.
- Make only canvas margins white in the mask. Do not ask the model to redraw the garment, body, face, hands, jewelry, text, or product texture.
- For very thin margins, prefer local edge/blur fill instead of AI. FLUX can create text-like artifacts in narrow strips.
- Prompt: extend only the existing photo background; preserve the model, garment, crochet stitches, colors, pose, and product details exactly.
- If a generated output changes the garment or looks suspicious, discard it and either lower the protected crop scale or use local background fill.

## Super-Resolution Rules

- Use `scripts/upscale_images.py` after splitting when source collage panels are too small for Etsy.
- For handmade crochet/knit listings, use the default `--method local`; it preserves real pixels with Lanczos resize, light contrast, and restrained sharpening instead of inventing stitches.
- Use `--method replicate` only when a smoother AI reconstruction is acceptable. Default Replicate model: `nightmareai/real-esrgan`.
- Keep `--face-enhance` off when using Replicate so model faces and product photography are not over-edited.
- Visually inspect `QA_contact_sheet.png` and at least one close crop before replacing listing images.
- Discard outputs that invent stitches, change garment color, alter buttons/ties/fringe, or make skin/face look artificial.

## Canvas Policy

Default `--target auto` keeps source clarity by avoiding forced upscale to `1080x1440`. The script computes the smallest `3:4` canvas for each crop, then centers that crop at its original pixel size. Use an explicit target like `--target 1080x1440` only when the user specifically asks for fixed pixel dimensions across all outputs.

## References

Read `references/pipeline-notes.md` when changing the workflow or tuning thresholds.
