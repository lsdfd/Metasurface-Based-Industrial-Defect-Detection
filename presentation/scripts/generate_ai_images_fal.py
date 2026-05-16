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
