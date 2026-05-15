from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a mock CMOS NPZ from distilled student optical kernels."
    )
    parser.add_argument("--kernel-pt", type=Path, default=None)
    parser.add_argument("--student-checkpoint", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--upsample", type=int, default=14)
    return parser.parse_args()


def load_kernels(args: argparse.Namespace) -> np.ndarray:
    if args.kernel_pt is not None:
        kernels = torch.load(args.kernel_pt, map_location="cpu")
    elif args.student_checkpoint is not None:
        state = torch.load(args.student_checkpoint, map_location="cpu")
        kernels = state["optical.weight"]
    else:
        raise ValueError("Provide either --kernel-pt or --student-checkpoint.")

    if isinstance(kernels, torch.Tensor):
        kernels = kernels.detach().cpu().numpy()
    return np.asarray(kernels, dtype=np.float32).squeeze(1)


def main() -> None:
    args = parse_args()
    kernels = load_kernels(args)

    positive = np.clip(kernels, 0, None)
    negative = np.clip(-kernels, 0, None)
    tile = np.ones((args.upsample, args.upsample), dtype=np.float32)
    positive_cmos = np.stack([np.kron(kernel, tile) for kernel in positive], axis=0)
    negative_cmos = np.stack([np.kron(kernel, tile) for kernel in negative], axis=0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        positive_cmos=positive_cmos,
        negative_cmos=negative_cmos,
    )
    print(f"Saved mock CMOS stack to {args.output}")
    print(f"positive_cmos shape: {positive_cmos.shape}")


if __name__ == "__main__":
    main()
