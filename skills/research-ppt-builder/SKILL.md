---
name: research-ppt-builder
description: Use this skill when creating or revising a research presentation/PPT for this project, especially a thesis or advisor-report deck about metasurface optical frontends, industrial defect detection, Fabric/AITEX, DAGM/SegDecNet, distillation, PSF/metasurface mapping, or paper-assets-to-PPT workflows. It codifies the v4 presentation method: use real data assets for results, use FAL-generated scientific figures for non-data pages, keep one or two main figures per slide, and include a one-sentence conclusion on every slide.
---

# Research PPT Builder

This skill captures the successful v4 PPT workflow for this project.

## Core Rule

Build research slides around figures, not text boxes.

- For original experimental data, use real assets from `paper_assets/`.
- For non-data pages, generate a full scientific figure with FAL `openai/gpt-image-2`.
- Each slide should have:
  - title
  - thin title line
  - one large main figure, or two side-by-side result figures
  - one bottom sentence summarizing the slide
- Avoid pages made from many small PowerPoint text boxes.
- Avoid decorative hero art. Scientific diagrams must communicate the method.

## Asset Policy

Use real data assets for:

- metrics / result bars
- threshold sweeps
- kernel grids
- mask visualizations
- PSF target / backphase figures
- metasurface probe figures
- compute / MAC charts
- tables derived from real results

Use AI-generated figures for:

- background / motivation
- overall method overview
- optical-electronic system architecture
- teacher-student distillation mechanism
- model architecture illustrations
- training protocol diagrams
- project summary / future roadmap

Do not use AI images to replace measured or generated result plots.

## FAL Figure Generation

Use the project script:

```bash
python3 presentation/scripts/generate_ai_images_fal.py \
  --output-dir presentation/ai_images_vX \
  --only <prompt_names> \
  --overwrite
```

The script reads credentials from:

1. `FAL_KEY`
2. `FAL_API_KEY`
3. local `sci-vision-video-agent_latest/config/api_keys.json`

Never hard-code API keys into this repository.

Recommended FAL settings:

- model: `openai/gpt-image-2`
- image size: `landscape_16_9`
- quality: `medium`
- output: `png`

## Prompt Style

Prompts should be detailed and scientifically constrained.

Good prompt requirements:

- Explicitly name the task and exact architecture.
- Say which modules must appear.
- Allow only short English labels where useful.
- Require readable labels and no pseudo text.
- Require the figure to fill most of the canvas.
- Prohibit blank placeholder boxes.
- Prohibit dark sci-fi, purple-heavy, decorative styles.

Useful wording:

```text
Required short English labels: ...
Composition: fill 85-90% of the canvas with useful diagram content; no empty placeholder boxes.
Text policy: short English labels are allowed only if clean and readable; no pseudo text, no unreadable microtext.
Visual style: Nature/IEEE-style scientific infographic, white background, deep blue/teal modules, restrained red defect marks.
Avoid: no dark background, no decorative factory scene, no wrong modules.
```

For model architecture prompts, write the exact project structure.

Fabric example:

```text
Top branch Electronic Teacher: 256x256 patch -> CNN feature extractor -> FC classifier -> defect probability.
Bottom branch R1 Optical Student: 64x64 input -> Optical Conv Bank with 16 kernels of 7x7 -> ReLU/Pool -> FC backend hidden=256 -> binary score.
Do not invent U-Net or segmentation output for Fabric.
```

DAGM example:

```text
Teacher: input -> shared conv backbone volume -> segmentation head -> mask; volume -> extractor -> FC classifier -> defect score.
Student: input 256x256 grayscale -> Optical Conv Bank 64 kernels 15x15 -> FeatureNorm+ReLU -> AvgPool stride 4 -> segmentation head -> concat volume+mask -> extractor -> FC classifier.
Show Volume KD, Mask KD, Score KD arrows.
```

## Slide Structure

Use this high-level structure for this project:

1. Cover: text only, no AI hero image.
2. Background: one AI scientific infographic.
3. Overall method: one AI method overview.
4. Optical-electronic architecture: one AI system figure.
5. Distillation mechanism: one AI figure plus optional formula image.
6. Kernel-to-PSF mapping: one AI figure plus optional formula image.
7. Case overview: one AI figure comparing Fabric and DAGM.
8. Fabric section:
   - task / scene AI figure
   - teacher-student architecture AI figure
   - real metrics and threshold figures
   - real kernel grids
   - real compute figure
   - optional real supporting assets
9. DAGM section:
   - task / scene AI figure
   - teacher-student architecture AI figure
   - two-stage training AI figure
   - real metrics
   - real mask visualization
   - real threshold sweep
   - real kernel grids
   - real PSF/backphase
   - real metasurface probe
   - real compute figure/table
10. Summary and future:
   - AI closed-loop summary
   - real case comparison table
   - AI future roadmap

## Layout Rules

- 16:9 canvas.
- White or very light gray background.
- Deep blue title.
- Thin line below title.
- Main image area should dominate the page.
- Bottom conclusion bar appears on every slide.
- Use at most two main figures on normal slides.
- Three images are acceptable only for natural triptychs such as signed/positive/negative kernels.
- Do not fill slides with paragraphs.
- If a table is needed, render it as an image and treat it as the main figure.

## Formula Handling

Render formulas as transparent PNG using matplotlib/mathtext, then place them as a small strip under the main figure.

Good formulas for this project:

```text
L = L_task + lambda_cls L_KD^cls + lambda_seg L_KD^seg + lambda_vol L_KD^vol
K+ = max(K,0), K- = max(-K,0), K = K+ - K-
```

Do not type raw formula text directly into a slide if it looks ugly.

## Quality Check

Before finalizing:

1. Generate a contact sheet for all AI images used.
2. Inspect for:
   - unreadable pseudo text
   - excessive empty space
   - wrong model modules
   - wrong task output
   - dark/decorative style
3. Read the PPT with `python-pptx` and print slide titles.
4. Confirm every slide has a bottom conclusion.
5. Confirm all key `paper_assets` result figures are represented.
6. Check file size before pushing to GitHub.

## Current Reference Implementation

Use these files as the current working reference:

```text
presentation/scripts/generate_ai_images_fal.py
presentation/scripts/build_ppt_v4.py
presentation/build/metasurface_industrial_defect_detection_v4.pptx
presentation/ai_images_v4/
presentation/build/ai_contact_sheet_v4_review.jpg
```

When improving the deck, create a new numbered version instead of overwriting a good previous version.
