from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdd.electronic_backend import CMOSHybridClassifier, CMOSReconstructionConfig, load_cmos_npz


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the distilled electronic backend on positive/negative CMOS feature stacks."
    )
    parser.add_argument("--cmos-npz", type=Path, required=True)
    parser.add_argument("--student-checkpoint", type=Path, required=True)
    parser.add_argument("--optical-kernels", type=int, default=16)
    parser.add_argument("--pooled-size", type=int, default=6)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--positive-gain", type=float, default=1.0)
    parser.add_argument("--negative-gain", type=float, default=1.0)
    parser.add_argument("--electronic-bias", type=float, default=0.0)
    parser.add_argument("--disable-relu", action="store_true")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    device = torch.device(args.device)

    positive_np, negative_np = load_cmos_npz(args.cmos_npz)
    positive = torch.from_numpy(positive_np).to(device)
    negative = torch.from_numpy(negative_np).to(device)

    model = CMOSHybridClassifier(
        optical_kernels=args.optical_kernels,
        pooled_size=args.pooled_size,
        hidden_dim=args.hidden_dim,
        reconstruction=CMOSReconstructionConfig(
            positive_gain=args.positive_gain,
            negative_gain=args.negative_gain,
            electronic_bias=args.electronic_bias,
            apply_relu=not args.disable_relu,
        ),
    ).to(device)
    model.load_student_backend(args.student_checkpoint, map_location=device)
    model.eval()

    with torch.no_grad():
        reconstructed = model.reconstruct_features(positive, negative)
        logits = model.forward_logits(positive, negative)
        probs = torch.sigmoid(logits)

    result = {
        "cmos_npz": str(args.cmos_npz),
        "student_checkpoint": str(args.student_checkpoint),
        "batch_size": int(positive.shape[0]),
        "feature_shape": list(reconstructed.shape),
        "logits": logits.view(-1).cpu().tolist(),
        "probabilities": probs.view(-1).cpu().tolist(),
        "reconstruction": {
            "positive_gain": args.positive_gain,
            "negative_gain": args.negative_gain,
            "electronic_bias": args.electronic_bias,
            "apply_relu": not args.disable_relu,
        },
    }
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
