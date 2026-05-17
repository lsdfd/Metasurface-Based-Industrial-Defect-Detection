from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KEY_FILE = ROOT.parents[3] / "sci-vision-video-agent_latest" / "config" / "api_keys.json"
DEFAULT_OUTPUT_DIR = ROOT / "presentation" / "ai_images"

DEFAULT_MODEL = "openai/gpt-image-2"
DEFAULT_QUALITY = "medium"
DEFAULT_IMAGE_SIZE = "landscape_16_9"


PROMPTS: dict[str, str] = {
    "cover_hybrid_defect_detection": """
Use case: scientific-educational
Asset type: 16:9 title slide hero image for a research presentation
Primary request: Create a clean, realistic scientific visualization of a hybrid optical-electronic industrial defect inspection system.
Scene: A fabric or industrial texture sample is illuminated on the left, light passes through a thin metasurface optical element in the center, and a CMOS sensor plus compact electronic processor sits on the right.
Visual style: polished research-lab rendering, white and light-gray background, deep blue technical accents, realistic optics, subtle light rays, precise and calm.
Composition: leave clear empty space in the upper-left area for a Chinese presentation title; main hardware path runs left-to-right across the lower middle.
Avoid: no readable text, no logos, no busy factory line, no fantasy sci-fi, no purple-dominant palette, no dark background.
""",
    "background_problem": """
Use case: scientific-educational
Asset type: 16:9 slide background figure
Primary request: Visualize the core problem of industrial defect detection: high-resolution images, sparse tiny defects, and expensive electronic CNN computation.
Scene: A large grayscale industrial texture image with a few tiny highlighted defect regions, next to a simplified electronic processor showing computational load as abstract heat/blocks.
Visual style: clean technical illustration blended with realistic texture, white/light-gray background, deep blue and teal accents, restrained red marks only for defects.
Composition: left side image inspection, right side computation burden; central visual balance, no text.
Avoid: no readable text, no UI labels, no factory worker, no stock-photo look, no dark cyberpunk style.
""",
    "research_route": """
Use case: scientific-educational
Asset type: 16:9 research roadmap diagram background
Primary request: Create a high-level visual roadmap for transferring an electronic teacher model into a metasurface optical frontend and lightweight electronic backend.
Scene: Three connected stages: a large electronic neural network teacher, a compact optical convolution bank/metasurface, and a small electronic decision head for defect detection.
Visual style: clean academic systems diagram rendered as semi-realistic components, white background, deep blue lines, teal optical glow, minimal red defect cue.
Composition: left-to-right flow with generous whitespace for later slide annotations; no embedded text.
Avoid: no readable text, no equations, no logos, no purple-heavy gradient, no black background.
""",
    "hybrid_optical_system": """
Use case: scientific-educational
Asset type: 16:9 optical setup schematic for PPT
Primary request: Render a hybrid optical-electronic inspection setup: LED or laser illumination, industrial sample, metasurface optical convolution plate, relay lens, CMOS sensor, and small electronic backend.
Scene: Components arranged left-to-right on an optical bench, with subtle beam paths and a magnified inset feeling for the metasurface.
Visual style: scientific apparatus illustration, accurate but presentation-friendly, light background, crisp edges, blue/teal optical paths.
Composition: centered system, enough margins for slide title and bottom conclusion.
Avoid: no readable text labels, no unrealistic giant chips, no cluttered lab, no dark cinematic lighting.
""",
    "future_yolo_chip_inspection": """
Use case: scientific-educational
Asset type: 16:9 future work slide image
Primary request: Show future extension of metasurface optical frontend to defect localization on PCB, wafer, and chip surfaces with a lightweight detector.
Scene: a wafer/PCB inspection sample with bounding boxes around tiny defects, connected to a compact metasurface-camera module and edge processor.
Visual style: clean research concept visual, realistic electronic surfaces, white/light-gray background, deep blue/teal accents, subtle red bounding boxes.
Composition: inspection sample dominates center, optical module on one side, keep it uncluttered and readable for a slide.
Avoid: no readable text, no brand names, no futuristic city, no purple-dominant palette, no noisy factory scene.
""",
    "v2_background_infographic": """
Use case: scientific-educational
Asset type: 16:9 research-paper graphical abstract panel for PPT
Primary request: Create a rich, publication-level infographic about the intersection of industrial defect detection and metasurface optical machine vision frontend.
Scene: A structured two-column scientific figure. Left column shows industrial inspection pain points: high-resolution fabric/texture images, sparse tiny defects, heavy electronic CNN/YOLO/segmentation computation, edge latency and power constraints. Right column shows metasurface opportunity: illumination, sample, metasurface PSF/convolution bank, CMOS sensor, lightweight electronic backend.
Composition: Dense but clean academic graphical abstract, multiple small subpanels connected by arrows, ample whitespace for overlay labels added later in PPT. Use realistic fabric/industrial texture patches and a simplified metasurface optical setup.
Visual style: Nature/IEEE-style clean scientific figure, white background, deep blue/teal technical palette, restrained red for defect marks, crisp vector-like geometry mixed with realistic texture thumbnails.
Text policy: do not include readable text, letters, logos, or fake labels inside the image; leave visual label areas blank so PPT can add accurate labels.
Avoid: no single atmospheric hero image, no factory worker, no dark cyberpunk lighting, no purple-dominant gradient, no cluttered stock photo.
""",
    "v2_methodology_graphical_abstract": """
Use case: scientific-educational
Asset type: 16:9 paper-style method overview figure
Primary request: Create a comprehensive graphical abstract for the proposed method: traditional electronic vision models are distilled into a metasurface optical frontend plus lightweight electronic backend for industrial defect detection.
Scene: Top row shows traditional electronic pipeline: industrial image -> CNN/YOLO/SegDecNet electronic feature extractor -> task head. Middle row shows teacher-student distillation: frozen teacher, trainable optical student, arrows for logits/masks/features/losses. Bottom row shows physical mapping: learned convolution kernels -> positive/negative split -> target PSF -> metasurface phase/radius optimization -> CMOS feature volume -> defect score/mask.
Composition: A rich multi-stage systems diagram with clearly separated lanes, arrows, model blocks, kernel thumbnails, PSF spots, metasurface plate, CMOS sensor, and small output examples. Leave space for PPT overlay labels and formulas.
Visual style: polished research-paper figure, white background, deep blue/teal accents, red highlights for defects and loss signals, precise schematic, balanced information density.
Text policy: no readable embedded text, no fake labels, no equations; the PPT will add exact labels and LaTeX formulas.
Avoid: no vague concept art, no single big object, no sci-fi spaceship style, no purple-heavy palette.
""",
    "v2_hybrid_optical_architecture": """
Use case: scientific-educational
Asset type: 16:9 detailed optical-electronic architecture figure for PPT
Primary request: Render a detailed hybrid optical-electronic defect inspection architecture suitable for a thesis presentation.
Scene: Left-to-right optical bench: LED/laser illumination -> industrial sample with tiny defect -> metasurface optical convolution plate with nanostructure inset -> relay optics -> CMOS sensor producing multiple feature-map tiles -> calibration/normalization module -> compact electronic backend -> outputs: binary defect score and segmentation mask.
Composition: One clear horizontal architecture diagram with multiple modules, realistic but clean optical paths, small feature-map stack after sensor, output examples at the right. Reserve blank space near each module for overlay labels.
Visual style: accurate scientific apparatus illustration, white/light-gray background, deep blue and teal beam paths, subtle red defect highlight, crisp high-resolution details.
Text policy: no readable text or labels in the generated image; no logos.
Avoid: no dark lab photo, no generic factory line, no unrealistic giant chip, no purple-dominant color scheme.
""",
    "v2_fabric_case_diagram": """
Use case: scientific-educational
Asset type: 16:9 case-study infographic for fabric defect binary classification
Primary request: Create a rich case-study diagram for fabric/AITEX patch-level defect classification with an optical student model.
Scene: A long fabric texture image is divided into square patches; one patch has a small highlighted defect. The patch flows into an electronic CNN teacher branch and a low-resolution optical student branch. The student branch shows resize to 64x64, a bank of 16 optical kernels, pooling/FC backend, and binary normal/defective score. Add small visual motifs for threshold calibration and kernel export.
Composition: Organized left-to-right pipeline with teacher and student branches stacked, realistic fabric texture thumbnails, kernel grid icons, binary decision output. Leave empty label zones for PPT overlay text.
Visual style: paper-quality infographic, white background, blue/teal modules, red defect highlight, clean arrows and subpanels.
Text policy: no readable embedded text, no fake labels, no equations.
Avoid: no vague cloth hero photo, no excessive decoration, no dark background.
""",
    "v2_dagm_case_diagram": """
Use case: scientific-educational
Asset type: 16:9 case-study infographic for DAGM SegDecNet distillation
Primary request: Create a rich case-study diagram for DAGM Class7 industrial texture defect segmentation using a SegDecNet teacher and optical student.
Scene: Grayscale industrial texture image with subtle defect; teacher branch shows SegDecNet shared convolution volume splitting into segmentation mask and classification score; student branch shows optical convolution bank, FeatureNorm/ReLU, pooling, segmentation head, concat with volume, extractor and FC classifier. Include output examples: heatmap mask overlay and defect score.
Composition: Dense but readable two-branch architecture figure, teacher on top, optical student below, arrows for distillation signals between corresponding outputs/features. Leave label spaces for PPT overlay.
Visual style: publication-ready technical diagram, white background, deep blue teacher modules, teal optical frontend, red defect/mask highlights, clean geometric blocks and small realistic texture thumbnails.
Text policy: no readable embedded text, no fake labels, no formulas.
Avoid: no generic abstract neural network blob, no dark sci-fi style, no purple-dominant palette.
""",
    "v2_future_system_roadmap": """
Use case: scientific-educational
Asset type: 16:9 future-work roadmap figure for PPT
Primary request: Create a future-work roadmap visual for extending metasurface optical frontend defect detection toward localization tasks such as PCB, wafer, chip, and YOLO-style detection.
Scene: A central metasurface-camera module connects to four application tiles: fabric inspection, DAGM-style texture segmentation, PCB/chip defect localization, wafer inspection. Show bounding boxes and masks as output examples, plus small icons for hardware-aware retraining, calibration, simulated PSF feedback, and real optical experiment.
Composition: Roadmap layout with central system hub and four application branches; rich but clean, suitable for final presentation slide.
Visual style: scientific roadmap infographic, white background, deep blue/teal palette, restrained red defect annotations, crisp high-quality rendering.
Text policy: no readable embedded text, no logos, no fake labels; PPT will add exact captions.
Avoid: no futuristic city, no vague chip glamour shot, no dark background.
""",
    "v3_distillation_training_mechanism": """
Use case: scientific-educational
Asset type: 16:9 paper-level method figure for a thesis presentation
Primary request: Generate a clean, complete knowledge distillation mechanism diagram for a hybrid optical-electronic defect detection model.
Scene: A frozen electronic teacher model on the top branch and a trainable optical student model on the bottom branch. Teacher accepts industrial defect images and outputs logits, segmentation mask, and intermediate feature volume. Student contains a metasurface optical convolution bank, CMOS feature maps, calibration, lightweight electronic backend, and outputs defect score and mask. Show distillation arrows from teacher outputs/features to student outputs/features, and a compact loss aggregation node.
Composition: one self-contained publication-style diagram, not a hero illustration. Use two horizontal branches, clear arrows, small feature map tiles, mask thumbnails, and kernel/PSF icons. Leave modest whitespace for PPT title; diagram itself should visually explain the process.
Visual style: precise academic infographic, white background, deep blue teacher blocks, teal optical student blocks, red loss arrows, restrained and elegant.
Text policy: very short English labels are allowed only if clean and readable, such as Teacher, Student, KD, Loss, Mask, Volume; no long sentences, no fake equations, no logos.
Avoid: no dense unreadable microtext, no dark background, no sci-fi style, no purple-dominant palette.
""",
    "v3_kernel_to_psf_mapping": """
Use case: scientific-educational
Asset type: 16:9 paper-level physical mapping figure
Primary request: Generate a clean scientific figure showing how a learned signed convolution kernel is mapped into metasurface PSF targets.
Scene: A learned kernel grid splits into positive and negative branches; each branch becomes a target PSF intensity pattern; then an optimization block adjusts metasurface phase/radius; finally simulated PSF is compared with target PSF on a detector plane.
Composition: left-to-right pipeline with two parallel positive/negative branches in the middle, small kernel heatmaps, PSF spots, metasurface nanostructure inset, detector-plane comparison. This should look like a paper Figure 1 subpanel, not a decorative concept image.
Visual style: white background, blue/teal scientific blocks, red/amber for negative branch, crisp arrows, high information density but readable.
Text policy: short English labels are allowed: Signed kernel, Positive, Negative, Target PSF, Metasurface, Simulated PSF. No long text, no equations, no logos.
Avoid: no random abstract light art, no dark background, no fake dense unreadable labels.
""",
    "v3_case_overview_two_examples": """
Use case: scientific-educational
Asset type: 16:9 two-case overview figure
Primary request: Generate a clean comparison figure showing two industrial defect detection examples in this project: Fabric patch binary classification and DAGM texture defect segmentation.
Scene: Left half shows fabric roll / textile texture image split into patches, with one defective patch and binary OK/NG output. Right half shows grayscale industrial texture image with defect mask overlay and segmentation output. Between them, a shared pipeline shows electronic teacher to optical student to metasurface PSF.
Composition: two large case panels side-by-side, unified by a small central method ribbon. Clear visual distinction: Fabric equals binary patch classification; DAGM equals pixel-level segmentation.
Visual style: thesis-quality infographic, white background, blue/teal modules, red defect highlights, clean scientific layout.
Text policy: short English labels allowed: Fabric, Binary, DAGM, Mask, Optical student. No long text, no logos.
Avoid: no decorative factory scene, no dark theme, no clutter.
""",
    "v3_fabric_teacher_student_architecture": """
Use case: scientific-educational
Asset type: 16:9 model architecture figure for fabric defect classification
Primary request: Generate a detailed but clean teacher-student architecture diagram for fabric/AITEX patch binary classification.
Scene: Input fabric image is resized/split into patches. Top branch: electronic CNN teacher with convolution blocks and FC classifier outputs defect probability. Bottom branch: optical student with 64x64 input, optical convolution bank with 16 kernels of 7x7, pooling, small FC backend, sigmoid binary score. Show learned kernels exported to positive/negative PSF split.
Composition: top teacher branch and bottom student branch, with arrows and a small KD arrow between outputs. Include kernel grid and threshold calibration icon. Use one coherent architecture diagram.
Visual style: publication-ready model diagram, white background, blue teacher branch, teal optical student branch, red defect output.
Text policy: short English labels allowed, including 64x64, 16 kernels, 7x7, FC, Binary score. No long sentences, no logos.
Avoid: no photorealistic-only scene, no cluttered text, no dark background.
""",
    "v3_dagm_teacher_student_architecture": """
Use case: scientific-educational
Asset type: 16:9 model architecture figure for DAGM SegDecNet distillation
Primary request: Generate a detailed teacher-student architecture diagram for DAGM Class7 industrial texture defect segmentation.
Scene: Top branch: SegDecNet teacher with input image, shared convolution backbone volume, segmentation head, feature extractor, FC classifier, outputs mask and defect score. Bottom branch: optical student with optical convolution bank of 64 kernels 15x15, FeatureNorm/ReLU, AvgPool, segmentation head, concat volume plus mask, extractor and FC classifier. Show distillation arrows for volume, mask, and classification score.
Composition: two horizontal architecture branches with matched modules and distillation arrows. Include small texture image thumbnail, feature volume tiles, mask heatmap, and output score icon. It must be accurate and readable as a model architecture figure.
Visual style: thesis/paper quality infographic, white background, deep blue teacher blocks, teal optical frontend, blue electronic backend, red loss arrows.
Text policy: short English labels allowed: Teacher, Student, Volume KD, Mask KD, Score KD, 64 kernels, 15x15. No long text, no fake equations, no logos.
Avoid: no abstract neural network blob, no unreadable tiny labels, no dark sci-fi palette.
""",
    "v3_two_stage_dagm_training": """
Use case: scientific-educational
Asset type: 16:9 training protocol figure
Primary request: Generate a clean two-stage distillation training protocol diagram for DAGM optical student.
Scene: Stage 1 focuses on optical frontend warm-up with volume KD and segmentation KD. Stage 2 performs joint optimization with task loss, classification KD, segmentation KD, and volume KD. Show a timeline from Stage 1 to Stage 2, teacher frozen above, student trainable below, and losses connected to relevant outputs.
Composition: horizontal timeline with two large stages, compact teacher/student mini-diagrams, arrows for losses, small icons for mask, volume, classification score.
Visual style: academic workflow diagram, white background, teal/blue stages, red loss arrows, clean readable layout.
Text policy: short English labels allowed: Stage 1, Stage 2, Volume KD, Seg KD, Cls KD, Task. No long sentences, no equations.
Avoid: no messy flowchart, no dark background, no fake code.
""",
    "v3_project_summary_closed_loop": """
Use case: scientific-educational
Asset type: 16:9 conclusion graphical summary
Primary request: Generate a clean closed-loop summary figure for a metasurface-based industrial defect detection project.
Scene: A circular or left-to-right closed loop: electronic teacher, optical student, learned kernels, positive/negative split, PSF target, metasurface feasibility probe, lightweight electronic backend, defect outputs. Include two small case icons for Fabric binary classification and DAGM segmentation.
Composition: one polished summary diagram with minimal text labels, visually conveying that the project connects algorithm distillation, optical frontend design, and physical feasibility verification.
Visual style: high-quality thesis defense summary figure, white background, deep blue/teal palette, red defect highlights, elegant and not cluttered.
Text policy: short English labels allowed only. No long text, no logos, no equations.
Avoid: no atmospheric poster, no dark sci-fi, no excessive decorative elements.
""",
    "v4_background_infographic": """
Use case: scientific-educational
Asset type: 16:9 thesis slide infographic
Primary request: Create a polished scientific infographic explaining why industrial defect detection needs a metasurface optical frontend.
Scene: Two balanced halves connected by a central arrow. Left half: Industrial Defect Detection pain points with high-resolution texture/fabric images, tiny sparse defects, CNN/YOLO/Segmentation compute blocks, latency/power icons. Right half: Metasurface Optical Frontend opportunity with illumination, sample, metasurface PSF encoder, CMOS sensor, lightweight electronic backend.
Required short English labels: Industrial Defect Detection, High-resolution image, Sparse defects, Heavy CNN compute, Metasurface Frontend, Optical convolution, CMOS, Lightweight backend.
Composition: fill 85-90% of the canvas with useful diagram content; no empty placeholder boxes; use arrows, subpanels, texture thumbnails, compute icons, and optical path modules. Keep labels readable and sparse.
Visual style: Nature/IEEE-style graphical abstract, white background, deep blue and teal modules, restrained red defect marks, clean scientific layout.
Avoid: no pseudo text, no unreadable microtext, no blank label boxes, no dark background, no purple-dominant palette, no decorative factory scene.
""",
    "v4_methodology_overview": """
Use case: scientific-educational
Asset type: 16:9 paper Figure 1 style method overview
Primary request: Create a complete method overview for metasurface-based industrial defect detection.
Scene: Three horizontal lanes. Lane 1 Traditional electronic model: industrial image -> CNN/YOLO/SegDecNet frontend -> task head. Lane 2 Distillation: frozen Teacher supervises Optical Student with logits, mask, and feature volume. Lane 3 Physical mapping: learned kernels -> positive/negative split -> target PSF -> metasurface -> CMOS feature maps -> electronic backend -> defect score/mask.
Required short English labels: Electronic Teacher, Optical Student, Knowledge Distillation, Learned Kernels, Positive/Negative Split, Target PSF, Metasurface, CMOS, Defect Score, Mask.
Composition: fill the canvas with connected modules, feature maps, kernel grids, PSF spots, and output examples. Labels should be short and accurate; no long paragraphs.
Visual style: clean publication-ready systems diagram, white background, deep blue teacher blocks, teal optical blocks, red KD arrows.
Avoid: no vague concept art, no fake equations, no unreadable dense labels, no empty panels.
""",
    "v4_hybrid_optical_architecture": """
Use case: scientific-educational
Asset type: 16:9 optical-electronic architecture figure
Primary request: Draw a scientifically plausible hybrid optical-electronic inspection architecture.
Scene: left-to-right: LED/Laser illumination -> industrial sample with tiny defect -> metasurface PSF/convolution bank -> relay optics -> CMOS sensor with feature map stack -> calibration/normalization -> lightweight electronic backend -> output defect score and segmentation mask.
Required short English labels: Illumination, Sample, Metasurface PSF bank, Relay optics, CMOS sensor, Feature maps, Calibration, Electronic backend, Score, Mask.
Composition: fill the figure with the optical path and modules; no blank boxes; show metasurface nanostructure inset and multi-channel feature maps after CMOS. Accurate left-to-right light path.
Visual style: clean scientific apparatus diagram, white/light gray background, teal light rays, deep blue modules, restrained red defect highlight.
Avoid: no fake lab photo, no huge empty regions, no unreadable text, no dark sci-fi style.
""",
    "v4_distillation_mechanism": """
Use case: scientific-educational
Asset type: 16:9 knowledge distillation architecture figure
Primary request: Draw an accurate teacher-student distillation diagram for this project.
Scene: Top branch: frozen Electronic Teacher taking industrial images and outputting logits/score, soft mask, and feature volume. Bottom branch: Optical Student with metasurface optical convolution bank, CMOS feature maps, calibration/electronic backend, output score and mask. Arrows from teacher to student represent Score KD, Mask KD, and Volume KD. A small Task Loss connects ground truth labels/masks to student outputs.
Required short English labels: Frozen Teacher, Optical Student, Score KD, Mask KD, Volume KD, Task Loss, Feature Volume, Soft Mask, Defect Score.
Composition: two clean horizontal branches with matching outputs and three distillation arrows; fill canvas without clutter. Labels should be readable and accurate.
Visual style: white background, blue teacher branch, teal student branch, red loss arrows, thesis-quality diagram.
Avoid: no wrong modules, no pseudo text, no long paragraphs, no empty placeholders.
""",
    "v4_kernel_to_psf": """
Use case: scientific-educational
Asset type: 16:9 kernel-to-metasurface mapping figure
Primary request: Draw a scientifically accurate mapping from learned signed convolution kernels to metasurface PSF targets.
Scene: Signed kernel K splits into K+ positive branch and K- negative branch. Each branch becomes a target PSF. A metasurface phase/radius optimization block produces simulated PSF. Show target-vs-simulated comparison on detector plane.
Required short English labels: Signed Kernel K, K+ Positive, K- Negative, Target PSF, Phase Optimization, Metasurface, Simulated PSF, Difference.
Composition: left-to-right pipeline with two parallel positive/negative branches, heatmap kernels, PSF spots, metasurface inset, detector comparison. Fill canvas; no blank label boxes.
Visual style: crisp paper-style diagram, white background, blue/teal positive branch, red/amber negative branch, clean arrows.
Avoid: no random light art, no fake dense text, no dark background.
""",
    "v4_case_overview": """
Use case: scientific-educational
Asset type: 16:9 two-case comparison figure
Primary request: Draw a two-case overview for this thesis: Fabric binary classification and DAGM segmentation.
Scene: Left panel Fabric/AITEX: textile/fabric texture image -> patch extraction -> binary OK/NG score. Right panel DAGM Class7: grayscale industrial texture image -> predicted heatmap/mask overlay -> defect score. Center ribbon: teacher to optical student to metasurface PSF.
Required short English labels: Fabric Binary Classification, Patch, OK/NG, DAGM Segmentation, Heatmap, Mask, Optical Student, Metasurface PSF.
Composition: two balanced case panels, useful content fills the page, no empty regions. Make it obvious Fabric is classification and DAGM is localization/segmentation.
Visual style: clean thesis infographic, white background, teal/blue modules, red defect highlights.
Avoid: no misleading object detection boxes for Fabric, no dark background, no unreadable labels.
""",
    "v4_fabric_architecture": """
Use case: scientific-educational
Asset type: 16:9 Fabric teacher-student model architecture figure
Primary request: Draw the exact Fabric/AITEX binary classification teacher-student architecture used in this project.
Scene: Input fabric patch. Top branch Electronic Teacher: 256x256 patch -> CNN feature extractor -> FC classifier -> defect probability. Bottom branch R1 Optical Student: resize/input 64x64 -> Optical Conv Bank with 16 kernels of 7x7 -> ReLU/Pool -> FC backend hidden=256 -> binary score. Show kernel export -> positive/negative split. Show threshold calibration near output.
Required short English labels: Fabric Patch, Electronic Teacher, CNN, FC, Defect Probability, R1 Optical Student, 64x64, 16 kernels 7x7, ReLU/Pool, FC 256, Threshold, Kernel Export.
Composition: two horizontal branches, top teacher and bottom student, arrows clear, fill page. Do not invent U-Net or segmentation mask for Fabric.
Visual style: accurate model architecture diagram, white background, blue teacher, teal student, red output/threshold.
Avoid: no wrong segmentation output, no unreadable tiny labels, no empty boxes.
""",
    "v4_dagm_architecture": """
Use case: scientific-educational
Asset type: 16:9 DAGM SegDecNet teacher-student model architecture figure
Primary request: Draw the exact DAGM Class7 teacher-student architecture used in this project.
Scene: Top branch SegDecNet Teacher: input image -> shared conv backbone volume -> segmentation head -> mask; volume also goes to feature extractor -> FC classifier -> defect score. Bottom branch Optical Student: input 256x256 grayscale -> Optical Conv Bank 64 kernels 15x15 -> FeatureNorm + ReLU -> AvgPool stride 4 -> segmentation head -> concat volume + seg mask -> extractor -> FC classifier. Show Volume KD, Mask KD, and Score KD arrows between teacher and student.
Required short English labels: SegDecNet Teacher, Shared Conv Volume, Seg Head, Mask, Extractor, FC, Defect Score, Optical Student, 64 kernels 15x15, FeatureNorm+ReLU, AvgPool s=4, Concat, Volume KD, Mask KD, Score KD.
Composition: two aligned branches with accurate modules; fill canvas; make teacher/student relationship clear.
Visual style: publication-quality architecture diagram, white background, blue teacher branch, teal optical frontend, red KD arrows.
Avoid: no YOLO boxes, no wrong Fabric modules, no pseudo text, no blank placeholders.
""",
    "v4_two_stage_training": """
Use case: scientific-educational
Asset type: 16:9 two-stage training protocol figure
Primary request: Draw the two-stage training protocol for DAGM optical student.
Scene: A left-to-right timeline with Stage 1 and Stage 2. Stage 1: Optical frontend warm-up using Volume KD and Seg KD. Stage 2: Joint optimization using Task Loss, Score KD, Seg KD, and Volume KD. Teacher is frozen above the timeline; student is trained below. Show mask, volume, and score icons.
Required short English labels: Stage 1, Frontend Warm-up, Volume KD, Seg KD, Stage 2, Joint Optimization, Task Loss, Score KD, Frozen Teacher, Trainable Student.
Composition: fill canvas with two stage panels and arrows; labels readable; no empty panels.
Visual style: academic workflow figure, white background, teal/blue stages, red loss arrows.
Avoid: no fake equations, no long text, no unreadable micro labels.
""",
    "v4_project_summary": """
Use case: scientific-educational
Asset type: 16:9 project closed-loop summary figure
Primary request: Draw a clean closed-loop summary of this metasurface industrial defect detection project.
Scene: Electronic Teacher -> Optical Student -> Learned Kernels -> Positive/Negative Split -> Target PSF -> Metasurface Probe -> Lightweight Backend -> Defect Outputs. Include two small case icons: Fabric Binary and DAGM Segmentation. Include compute reduction and feasibility probe as visual callouts.
Required short English labels: Teacher, Optical Student, Kernels, PSF Target, Metasurface Probe, Backend, Fabric Binary, DAGM Segmentation, Compute Reduction.
Composition: polished loop or left-to-right closed chain; fill the canvas; minimal but useful labels.
Visual style: thesis defense closing figure, white background, deep blue/teal palette, red defect highlights.
Avoid: no decorative poster, no dark sci-fi, no empty areas.
""",
    "v4_future_roadmap": """
Use case: scientific-educational
Asset type: 16:9 future work roadmap figure
Primary request: Draw a future roadmap for metasurface optical frontend industrial inspection.
Scene: Central metasurface-camera module connects to four applications: Fabric inspection, DAGM texture segmentation, PCB/chip defect localization, wafer inspection. Show future technical steps: simulated PSF feedback, hardware-aware retraining, calibration, real optical experiment.
Required short English labels: Fabric, DAGM, PCB/Chip, Wafer, Simulated PSF, Calibration, Hardware-aware Training, Optical Experiment.
Composition: central hub with four branches and four technical milestones; fill canvas, no blank boxes.
Visual style: clean scientific roadmap, white background, blue/teal modules, red defect annotations.
Avoid: no futuristic city, no fake brand logos, no dark background.
""",
    "v5_psf_to_phase_inverse_design": """
Use case: scientific-educational
Asset type: 16:9 thesis slide figure, same visual style as the existing v4 deck.
Primary request: Draw a scientifically accurate PSF-to-phase inverse design figure for a metasurface optical frontend.
Real data context to incorporate visually: DAGM optical student kernels were exported as PSF targets; the current package uses wavelength 532 nm, grid pitch 586 nm, detector distance 2.4 mm, PSF scale factor 2, and simulation canvas 1600 x 1600. Existing results include target PSF center crops and a back-propagated phase preview.
Scene: left-to-right pipeline: Target PSF intensity from learned optical kernel -> angular-spectrum/back-propagation block -> optimized phase mask phi(x,y) -> simulated PSF on detector plane. Include small heatmap-like target PSF thumbnail, wrapped phase map thumbnail, and detector-plane PSF thumbnail.
Required short English labels: Target PSF, Back Propagation, Phase Mask, Simulated PSF, Loss.
Composition: one clean paper-style pipeline filling 85-90% of the canvas; no empty placeholder boxes; use arrows and three heatmap panels; make it look like an inserted method figure in a thesis, not a poster.
Visual style: white background, deep blue/teal modules, restrained red loss arrow, crisp scientific diagram consistent with v4 PPT.
Avoid: no pseudo text, no unreadable microtext, no wrong modules, no decorative sci-fi optics, no dark background.
""",
    "v5_angular_spectrum_loop": """
Use case: scientific-educational
Asset type: 16:9 thesis slide figure, same visual style as the existing v4 deck.
Primary request: Draw the angular spectrum optimization loop used to connect phase distribution and target PSF.
Real data context to incorporate visually: representative DAGM metasurface feasibility probes used 40 Adam iterations, learning rate 0.005, ROI size 96, CUDA simulation, and achieved cosine similarity about 0.979-0.991 for selected positive/negative branches. Wavelength is 532 nm, detector distance is 2.4 mm, simulation canvas is 1600 x 1600.
Scene: closed loop: phase phi(x,y) -> FFT / angular spectrum transfer function H(fx,fy,z) -> propagated complex field Uz -> intensity |Uz|^2 simulated PSF -> compare with target PSF -> loss -> Adam update back to phase. Include target-vs-simulated PSF thumbnails and a tiny decreasing loss curve motif.
Required short English labels: Phase, FFT, Transfer Function, Simulated PSF, Target PSF, Loss, Adam Update, Cosine 0.979-0.991.
Composition: circular or rectangular loop diagram filling the page; formulas should be implied visually, not rendered as long text; labels short and readable.
Visual style: Nature/IEEE-style scientific workflow, white background, blue/teal arrows, red loss/comparison highlight, consistent with v4 PPT.
Avoid: no fake dense equations, no unreadable labels, no dark sci-fi style, no decorative-only light beams.
""",
    "v5_rcwa_phase_geometry_lookup": """
Use case: scientific-educational
Asset type: 16:9 thesis slide figure, same visual style as the existing v4 deck.
Primary request: Draw a phase-to-geometry mapping workflow using RCWA simulation and a phase-geometry lookup table.
Real data context to incorporate visually: the project currently uses a reference-inspired single-wavelength route at 532 nm and grid pitch 586 nm; target phase comes from PSF inverse design. This slide should be presented as the structure-parameter mapping step, not as fabricated measured data.
Scene: left: target phase map phi(x,y). Middle: nanopillar unit cell on quartz/SiO2 substrate with SiN pillar; RCWA parameter sweep over pillar width/radius producing transmission amplitude and phase curves. Right: lookup table maps each phase pixel to a pillar width/radius; output is a discrete geometry map.
Required short English labels: Target Phase, SiN Nanopillar, Quartz Substrate, RCWA Sweep, Phase Lookup, Width / Radius Map.
Composition: three-panel scientific diagram with a small unit-cell inset, curve plot motif, and geometry map. Fill 85-90% of canvas; labels short and accurate; no empty panels.
Visual style: clean white paper figure, deep blue modules, teal nanostructures, restrained red markers on the lookup curve, consistent with v4 PPT.
Avoid: no claim of experimental fabrication, no fake measurement table, no unreadable microtext, no wrong material labels, no dark background.
""",
    "v5_metasurface_layout_parameters": """
Use case: scientific-educational
Asset type: 16:9 thesis slide figure, same visual style as the existing v4 deck.
Primary request: Draw the final metasurface layout and physical parameter summary for the proposed optical frontend.
Real data context to incorporate visually: current simulation settings are wavelength 532 nm, grid pitch 586 nm, detector distance 2.4 mm, PSF scale factor 2, simulation canvas 1600 x 1600, positive/negative branches from learned kernels, and SiN nanopillars on quartz/SiO2 substrate as the reference material route.
Scene: a large metasurface array layout with varied nanopillar widths/radii according to a discrete geometry map; show one magnified unit cell, periodic pitch annotation, incident 532 nm light, detector plane at 2.4 mm, and output PSF on CMOS/detector. Include a compact parameter callout panel with short readable labels.
Required short English labels: 532 nm, Pitch 586 nm, z = 2.4 mm, SiN, Quartz / SiO2, Geometry Map, Detector PSF, Positive / Negative Branch.
Composition: one clean engineering layout figure; left/middle metasurface array and unit cell, right detector PSF, small parameter callout. Fill page without clutter.
Visual style: scientific device schematic, white background, teal/blue metasurface, red PSF highlight, consistent with v4 PPT.
Avoid: no wafer glamour shot, no fake brand logos, no dense pseudo text, no dark sci-fi style, no unsupported fabrication claims.
""",
}


def load_api_key(key_file: Path) -> str:
    for name in ("FAL_KEY", "FAL_API_KEY"):
        value = os.getenv(name)
        if value:
            return value.strip()

    if key_file.exists():
        data = json.loads(key_file.read_text(encoding="utf-8"))
        for name in ("FAL_KEY", "FAL_API_KEY"):
            value = data.get(name)
            if value:
                return str(value).strip()

    raise RuntimeError(
        "FAL key not found. Set FAL_KEY/FAL_API_KEY or provide --key-file."
    )


def extract_image_url(result: dict[str, Any]) -> str:
    images = result.get("images") or []
    if images and isinstance(images[0], dict) and images[0].get("url"):
        return str(images[0]["url"])

    image = result.get("image")
    if isinstance(image, dict) and image.get("url"):
        return str(image["url"])

    raise RuntimeError(f"FAL returned no image URL. Keys: {sorted(result.keys())}")


def download(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(output_path.suffix + ".download")
    with requests.get(url, stream=True, timeout=(20, 180)) as response:
        response.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    tmp.replace(output_path)


def generate_one(
    *,
    fal_client: Any,
    name: str,
    prompt: str,
    output_dir: Path,
    model: str,
    image_size: str,
    quality: str,
    overwrite: bool,
) -> Path:
    output_path = output_dir / f"{name}.png"
    prompt_path = output_dir / f"{name}.prompt.txt"
    if output_path.exists() and not overwrite:
        print(f"[skip] {output_path}")
        return output_path

    print(f"[fal] generating {name} with {model} ({image_size}, {quality})")
    result = fal_client.subscribe(
        model,
        arguments={
            "prompt": prompt.strip(),
            "image_size": image_size,
            "quality": quality,
            "num_images": 1,
            "output_format": "png",
        },
        with_logs=True,
    )
    image_url = extract_image_url(result)
    download(image_url, output_path)
    prompt_path.write_text(prompt.strip() + "\n", encoding="utf-8")
    print(f"[ok] {output_path} ({output_path.stat().st_size} bytes)")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key-file", type=Path, default=DEFAULT_KEY_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=os.getenv("FAL_IMAGE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--quality", default=os.getenv("FAL_IMAGE_QUALITY", DEFAULT_QUALITY))
    parser.add_argument("--image-size", default=os.getenv("FAL_PPT_IMAGE_SIZE", DEFAULT_IMAGE_SIZE))
    parser.add_argument("--only", choices=sorted(PROMPTS), nargs="*")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    import fal_client

    api_key = load_api_key(args.key_file)
    previous_key = os.environ.get("FAL_KEY")
    os.environ["FAL_KEY"] = api_key
    try:
        names = args.only or list(PROMPTS)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for index, name in enumerate(names):
            generate_one(
                fal_client=fal_client,
                name=name,
                prompt=PROMPTS[name],
                output_dir=args.output_dir,
                model=args.model,
                image_size=args.image_size,
                quality=args.quality,
                overwrite=args.overwrite,
            )
            if index < len(names) - 1:
                time.sleep(1.0)
    finally:
        if previous_key is None:
            os.environ.pop("FAL_KEY", None)
        else:
            os.environ["FAL_KEY"] = previous_key


if __name__ == "__main__":
    main()
