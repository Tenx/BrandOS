# Pipeline Notes

## Boundary Detection

Most collage inputs use white gutters. Detect near-white pixels and find vertical/horizontal runs whose white-pixel density is high enough over a meaningful length. Use those gutters to form candidate rectangular panels, then ignore tiny/blank regions.

If gutter detection fails, fall back to connected-component segmentation on non-white regions, then manually inspect the QA contact sheet.

## Canvas Mode

Keep every detected panel. Do not dedupe.

Default `--target auto` computes the smallest 3:4 canvas for each crop without upscaling. Each crop is centered at its original pixel size. The mask protects the crop rectangle and asks FLUX Fill to generate only the missing margin.

Use an explicit target only when fixed pixel dimensions matter more than preserving source-native clarity.

## FLUX Fill Prompt

Use conservative prompts:

```text
Extend only the surrounding photo background to fill the canvas.
Preserve the original model, garment, crochet texture, colors, skin, face, hands, pose, jewelry, and product details exactly as they are.
Generate natural continuation of the existing wall, floor, furniture, outdoor scenery, sunlight, shadows, and photographic texture.
No new clothing, no text, no watermark, no extra people, no changes inside the preserved product photo area.
```

## QA Checklist

- No original source overwritten.
- Each source has its own folder.
- All detected panels are kept.
- All final outputs are 3:4 and keep 300 DPI metadata when requested.
- DPI metadata is set when requested.
- Product texture is not hallucinated or altered.
- Contact sheet exists for every output folder.
