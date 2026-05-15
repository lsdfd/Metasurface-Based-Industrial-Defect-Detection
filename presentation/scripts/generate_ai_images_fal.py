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
