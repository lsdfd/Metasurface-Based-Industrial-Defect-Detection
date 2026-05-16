---
name: research-ppt-builder
description: Use this skill when creating or revising a research presentation/PPT in the user's preferred style. The style is figure-driven, thesis/advisor-report oriented, visually clean, and scientifically grounded: use real data figures for experimental results, use AI-generated scientific infographics for conceptual/method/architecture pages, keep each slide centered on one or two strong figures, include a one-sentence takeaway on every slide, and avoid cluttered text-box layouts.
---

# Research PPT Builder

This skill defines the user's general style for research PPT generation.

## North Star

Make the deck look like a thesis defense or paper-story presentation, not a text-heavy class report.

The slide should answer:

1. What is this page about?
2. What is the main figure?
3. What should the audience remember?

If a slide has no strong figure, create one before building the slide.

The user's preferred style is: one clear scientific claim per page, one dominant visual proof, and one memorable bottom-line sentence.

Do not try to make the deck feel busy. Make it feel authored.

## Slide Layout

Default layout:

- 16:9 canvas.
- White or very light gray background.
- Top title in deep blue.
- Thin line under title.
- Middle: one large figure, or two side-by-side figures.
- Bottom: one sentence summarizing the slide.

Preferred slide density:

- Concept pages: one large AI scientific infographic plus minimal labels.
- Method pages: one architecture/workflow figure plus one compact formula strip if needed.
- Result pages: one or two real plots/tables/images, with enough axis labels and legends to stand alone.
- Comparison pages: one clean table or paired visual comparison.

Avoid:

- Many small text boxes.
- Long paragraphs.
- Decorative cards everywhere.
- Empty hero images with no information.
- AI-looking atmosphere images that do not explain the science.

Allowed exceptions:

- Three side-by-side images for natural triptychs, such as signed / positive / negative kernels.
- A single table can be the main figure if the table is a real result summary.
- A formula strip can sit below the main figure if it is central to the method.

## What To Use AI For

Use AI-generated figures for non-data pages:

- background / motivation
- problem definition
- overall method
- system architecture
- teacher-student architecture
- training protocol
- physical mapping workflow
- case overview
- project summary
- future roadmap

AI figures should be scientific infographics, not posters, cover art, or vague atmosphere images.

Good AI figure traits:

- fills 80-90% of the canvas with useful content
- has connected modules, arrows, panels, or scientific objects
- uses a clean white-background paper style
- uses short English labels where helpful
- has readable labels, not pseudo text
- matches the actual method or architecture

Bad AI figure traits:

- big empty areas
- fake unreadable text
- wrong model modules
- wrong task output
- decorative factory scenes
- dark sci-fi style
- purple-heavy gradients

## What Must Stay Real

Do not replace experimental evidence with AI.

Use real project assets for:

- metrics and result bars
- threshold sweeps
- confusion matrices
- mask visualizations
- qualitative examples
- kernel grids
- PSF targets
- simulated-vs-target PSF probes
- compute / MAC / parameter charts
- real tables derived from experiments

If a result is not already presentable, generate a clean plot/table from the real source data. Do not invent it visually with AI.

When real assets are messy, redraw them from data instead of screenshotting notebook clutter.

## AI Prompt Method

Prompts must be specific enough to prevent the image model from inventing the science.

Always specify:

- use case: scientific / educational / thesis / paper figure
- exact task
- exact modules that must appear
- allowed short English labels
- composition and information density
- visual style
- avoid list

Template:

```text
Use case: scientific-educational
Asset type: 16:9 thesis slide figure
Primary request: Draw a scientifically accurate figure for <topic>.
Scene: <exact objects/modules/flow>.
Required short English labels: <label1>, <label2>, ...
Composition: fill 85-90% of the canvas with useful diagram content; no blank placeholder boxes; use arrows/subpanels/modules.
Visual style: Nature/IEEE-style scientific infographic, white background, deep blue/teal modules, restrained red highlights.
Avoid: no pseudo text, no unreadable microtext, no wrong modules, no decorative dark sci-fi style, no empty areas.
```

For architecture diagrams, describe the real architecture step by step. Do not rely on vague requests such as "draw a neural network".

Example structure:

```text
Top branch: Teacher: input -> backbone -> task heads -> outputs.
Bottom branch: Student: input -> constrained frontend -> lightweight backend -> outputs.
Show distillation arrows: logits, mask, features.
Do not invent modules that are not in the project.
```

## Figure Text Policy

Use some English labels when they help.

Good:

- short labels such as `Teacher`, `Student`, `Mask KD`, `Feature Volume`, `Target PSF`
- readable, sparse labels
- labels placed near real modules

Bad:

- long paragraphs inside images
- fake unreadable text
- random labels that do not match the method
- completely blank diagrams with no explanation

If the generated image has too much fake text or weird empty label boxes, regenerate with a stricter prompt.

## Data Selection

Before building slides, inventory available assets:

- main result figures
- process figures
- tables
- qualitative examples
- checkpoints or model diagrams if relevant
- reports / markdown summaries

Choose assets by story value:

1. Use the best/final result as the main figure.
2. Include process figures only when they explain why the result is trustworthy.
3. Include failed or weak results only if they teach an important methodological lesson.
4. Do not clutter the deck with every historical experiment.
5. Make sure every major claim has a corresponding real figure or table.

For the user's style, result pages are allowed to be more data-heavy than concept pages, but still must have a clean one-sentence takeaway.

Prioritize evidence in this order:

1. Final/best model metrics under the correct evaluation protocol.
2. Qualitative examples that make the task visually obvious.
3. Ablations or process curves that explain why the final choice is credible.
4. Compute/parameter/MAC reductions that explain hardware value.
5. Failure cases only when they clarify the research path.

## Narrative Structure

A strong research deck usually follows:

1. Cover.
2. One-page background and pain point.
3. Overall method figure.
4. System / architecture figure.
5. Training or algorithm figure.
6. Physical mapping or deployment figure, if relevant.
7. Case study 1:
   - task and industrial scene
   - teacher/student or baseline/proposed method
   - main result
   - analysis / process evidence
   - compute or practical significance
   - short case summary
8. Case study 2:
   - same logic, but deeper if it is the main result
9. Cross-case comparison.
10. Contributions.
11. Future work.

Keep background and future concise unless the user explicitly asks for a broad literature lecture. Spend most slides on the two things that matter: what was built and what the evidence shows.

Each case must answer:

- What industrial scene is this?
- What defect is being detected?
- What is the input?
- What is the output?
- Is it classification, localization, segmentation, or detection?
- What is the teacher/baseline?
- What is the student/proposed model?
- What result proves it works?
- What practical or hardware significance does it have?

## Formula Handling

Use real formula rendering, not ugly typed text.

Recommended:

- Render formulas as transparent PNG using matplotlib/mathtext or LaTeX.
- Place formula as a compact strip under the main method figure.
- Keep formulas few and central.

Good examples:

```text
L = L_task + lambda_1 L_KD + lambda_2 L_feature
K+ = max(K,0), K- = max(-K,0), K = K+ - K-
```

Avoid filling slides with derivations unless the user explicitly wants a theory-heavy presentation.

## Implementation Workflow

1. Build or update a `presentation/` folder.
2. Inventory real assets from project result folders.
3. Decide slide list and map each slide to:
   - AI figure
   - real figure
   - table image
   - formula image
4. Generate AI figures with detailed prompts.
5. Make a contact sheet of AI figures.
6. Inspect and regenerate weak figures.
7. Generate PPT with a script, preferably `python-pptx`.
8. Validate:
   - slide count
   - slide titles
   - all images exist
   - every slide has a bottom conclusion
   - file size is GitHub-safe
9. Version outputs: `v1`, `v2`, `v3`, etc. Never overwrite a good version.
10. Commit generated PPT, prompts, scripts, and key assets together.

If using AI-generated figures, save the prompts and generated images next to the deck. The deck should be reproducible, not a one-off artifact.

## Quality Checklist

Before final answer:

- The cover is clean and not an AI hero image unless explicitly requested.
- Every slide has one sentence at the bottom.
- Non-data pages use strong AI scientific figures.
- Data pages use real experiment figures/tables.
- Architecture figures match the actual project method.
- Case-study opening pages explain task, scene, input, and output.
- There are no obvious pseudo-text artifacts in AI figures.
- There is no strange blank-space-heavy figure.
- All important assets are represented.
- The generated deck can be opened/read by tooling.
- The deck is synced to GitHub if requested.

## Reference In This Repository

The current best example of this style is:

```text
presentation/build/metasurface_industrial_defect_detection_v4.pptx
presentation/scripts/build_ppt_v4.py
presentation/scripts/generate_ai_images_fal.py
presentation/ai_images_v4/
presentation/build/ai_contact_sheet_v4_review.jpg
```

Use it as a style reference, not as a fixed template. The method should generalize to other research topics.
