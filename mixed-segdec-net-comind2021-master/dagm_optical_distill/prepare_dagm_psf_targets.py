import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch


@dataclass
class PSFConfig:
    wavelength_nm: float = 532.0
    grid_pitch_nm: float = 586.0
    detector_distance_mm: float = 2.4
    scale: int = 2
    sim_size: int = 1600
    normalize: str = "paired_max"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Convert DAGM optical student kernels into positive/negative PSF targets "
            "for metasurface phase-design experiments."
        )
    )
    parser.add_argument("--KERNELS", required=True, type=Path, help="Path to best_optical_kernels.npy/.npz/.pt")
    parser.add_argument("--OUTPUT_DIR", required=True, type=Path)
    parser.add_argument("--SCALE", default=2, type=int, help="Integer enlargement factor for each kernel pixel")
    parser.add_argument("--SIM_SIZE", default=1600, type=int, help="Square PSF simulation canvas size")
    parser.add_argument("--WAVELENGTH_NM", default=532.0, type=float)
    parser.add_argument("--GRID_PITCH_NM", default=586.0, type=float)
    parser.add_argument("--DETECTOR_DISTANCE_MM", default=2.4, type=float)
    parser.add_argument(
        "--NORMALIZE",
        default="paired_max",
        choices=("paired_max", "per_kernel_l1", "none"),
        help=(
            "paired_max: positive/negative pair shares one max scale; "
            "per_kernel_l1: each original signed kernel is L1-normalized before split; "
            "none: keep raw learned values after split."
        ),
    )
    parser.add_argument("--SAVE_FIGURES", action="store_true")
    parser.add_argument("--PREVIEW_KERNELS", default=16, type=int)
    parser.add_argument("--KERNEL_INDEX", default=0, type=int, help="Kernel index for single PSF/backphase preview")
    return parser.parse_args()


def load_kernels(path: Path):
    if path.suffix == ".npy":
        kernels = np.load(path)
    elif path.suffix == ".npz":
        data = np.load(path)
        key = "kernels" if "kernels" in data.files else data.files[0]
        kernels = data[key]
    elif path.suffix in (".pt", ".pth"):
        obj = torch.load(path, map_location="cpu")
        if isinstance(obj, torch.Tensor):
            kernels = obj.detach().cpu().numpy()
        elif isinstance(obj, dict):
            candidates = (
                "optical_frontend.conv.weight",
                "module.optical_frontend.conv.weight",
                "student.optical_frontend.conv.weight",
                "optical.weight",
                "kernels",
            )
            kernels = None
            for key in candidates:
                if key in obj:
                    value = obj[key]
                    kernels = value.detach().cpu().numpy() if isinstance(value, torch.Tensor) else value
                    break
            if kernels is None:
                state = obj.get("state_dict") if isinstance(obj.get("state_dict"), dict) else obj
                for key, value in state.items():
                    if key.endswith("optical_frontend.conv.weight"):
                        kernels = value.detach().cpu().numpy()
                        break
            if kernels is None:
                raise KeyError(f"Could not find optical kernels in {path}")
        else:
            raise TypeError(f"Unsupported torch object type: {type(obj)}")
    else:
        raise ValueError(f"Unsupported kernel file extension: {path.suffix}")

    kernels = np.asarray(kernels, dtype=np.float32)
    if kernels.ndim == 4 and kernels.shape[1] == 1:
        kernels = kernels[:, 0]
    elif kernels.ndim == 3:
        pass
    else:
        raise ValueError(f"Expected [N,1,H,W] or [N,H,W] kernels, got {kernels.shape}")
    return kernels


def split_pos_neg(kernels: np.ndarray, normalize: str):
    signed = kernels.astype(np.float32).copy()
    if normalize == "per_kernel_l1":
        denom = np.sum(np.abs(signed), axis=(1, 2), keepdims=True)
        signed = signed / np.maximum(denom, 1e-12)

    positive = np.clip(signed, 0.0, None)
    negative = np.clip(-signed, 0.0, None)

    if normalize == "paired_max":
        denom = np.maximum(
            np.maximum(positive.max(axis=(1, 2), keepdims=True), negative.max(axis=(1, 2), keepdims=True)),
            1e-12,
        )
        positive = positive / denom
        negative = negative / denom

    return signed, positive.astype(np.float32), negative.astype(np.float32)


def expand_to_canvas(kernel: np.ndarray, scale: int, sim_size: int):
    expanded = np.kron(kernel, np.ones((scale, scale), dtype=np.float32)).astype(np.float32)
    h, w = expanded.shape
    if h > sim_size or w > sim_size:
        raise ValueError(f"Expanded kernel shape {expanded.shape} exceeds sim_size={sim_size}")

    canvas = np.zeros((sim_size, sim_size), dtype=np.float32)
    y0 = (sim_size - h) // 2
    x0 = (sim_size - w) // 2
    canvas[y0 : y0 + h, x0 : x0 + w] = expanded
    return canvas


def angular_spectrum_backprop(field: np.ndarray, z_m: float, wavelength_m: float, pitch_m: float):
    """Backpropagate a target detector-plane amplitude template to get an initial phase guess."""
    e = np.asarray(field, dtype=np.complex64)
    if np.sign(z_m) < 0:
        e = np.conjugate(e)

    spectrum = np.fft.fft2(e)
    nx, ny = e.shape
    u = np.fft.fftfreq(nx, d=pitch_m)
    v = np.fft.fftfreq(ny, d=pitch_m)
    v_grid, u_grid = np.meshgrid(v, u)
    w = np.sqrt(0j + 1.0 / wavelength_m**2 - u_grid**2 - v_grid**2).real
    propagated = spectrum * np.exp(1j * 2 * np.pi * w * abs(z_m))
    return np.fft.ifft2(propagated)


def kernel_stats(kernels, positive, negative):
    pos_mass = positive.sum(axis=(1, 2))
    neg_mass = negative.sum(axis=(1, 2))
    abs_mass = np.abs(kernels).sum(axis=(1, 2))
    signed_sum = kernels.sum(axis=(1, 2))
    balance = (pos_mass - neg_mass) / np.maximum(pos_mass + neg_mass, 1e-12)
    return {
        "shape": list(kernels.shape),
        "global_min": float(kernels.min()),
        "global_max": float(kernels.max()),
        "global_mean": float(kernels.mean()),
        "global_std": float(kernels.std()),
        "mean_abs_mass": float(abs_mass.mean()),
        "mean_positive_mass": float(pos_mass.mean()),
        "mean_negative_mass": float(neg_mass.mean()),
        "mean_signed_sum": float(signed_sum.mean()),
        "mean_pos_neg_balance": float(balance.mean()),
        "kernel_rows": [
            {
                "index": int(i),
                "min": float(kernels[i].min()),
                "max": float(kernels[i].max()),
                "mean": float(kernels[i].mean()),
                "std": float(kernels[i].std()),
                "abs_mass": float(abs_mass[i]),
                "positive_mass": float(pos_mass[i]),
                "negative_mass": float(neg_mass[i]),
                "signed_sum": float(signed_sum[i]),
                "pos_neg_balance": float(balance[i]),
            }
            for i in range(kernels.shape[0])
        ],
    }


def save_kernel_grid(path: Path, kernels: np.ndarray, title: str, limit: int):
    count = min(limit, kernels.shape[0])
    cols = int(np.ceil(np.sqrt(count)))
    rows = int(np.ceil(count / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.2, rows * 2.2))
    axes = np.asarray(axes).reshape(-1)
    vmax = float(np.max(np.abs(kernels[:count])))
    for idx, ax in enumerate(axes):
        ax.axis("off")
        if idx >= count:
            continue
        ax.imshow(kernels[idx], cmap="coolwarm", vmin=-vmax, vmax=vmax)
        ax.set_title(f"k{idx}", fontsize=8)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_psf_preview(path: Path, positive, negative, phase_pos, phase_neg, kernel_index: int):
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    axes[0, 0].imshow(positive, cmap="gray")
    axes[0, 0].set_title(f"Positive target k{kernel_index}")
    axes[0, 1].imshow(negative, cmap="gray")
    axes[0, 1].set_title(f"Negative target k{kernel_index}")
    axes[1, 0].imshow(phase_pos, cmap="twilight")
    axes[1, 0].set_title("Positive backphase")
    axes[1, 1].imshow(phase_neg, cmap="twilight")
    axes[1, 1].set_title("Negative backphase")
    for ax in axes.reshape(-1):
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def center_crop(image: np.ndarray, crop_size: int):
    h, w = image.shape
    crop_size = min(crop_size, h, w)
    y0 = (h - crop_size) // 2
    x0 = (w - crop_size) // 2
    return image[y0 : y0 + crop_size, x0 : x0 + crop_size]


def save_psf_target_crop(path: Path, positive, negative, kernel_index: int, crop_size: int = 96):
    pos_crop = center_crop(positive, crop_size)
    neg_crop = center_crop(negative, crop_size)
    fig, axes = plt.subplots(1, 2, figsize=(8, 4))
    axes[0].imshow(pos_crop, cmap="gray")
    axes[0].set_title(f"Positive target crop k{kernel_index}")
    axes[1].imshow(neg_crop, cmap="gray")
    axes[1].set_title(f"Negative target crop k{kernel_index}")
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def main():
    args = parse_args()
    cfg = PSFConfig(
        wavelength_nm=args.WAVELENGTH_NM,
        grid_pitch_nm=args.GRID_PITCH_NM,
        detector_distance_mm=args.DETECTOR_DISTANCE_MM,
        scale=args.SCALE,
        sim_size=args.SIM_SIZE,
        normalize=args.NORMALIZE,
    )

    kernels_raw = load_kernels(args.KERNELS)
    kernels, positive, negative = split_pos_neg(kernels_raw, normalize=args.NORMALIZE)
    positive_expanded = np.stack([expand_to_canvas(k, args.SCALE, args.SIM_SIZE) for k in positive], axis=0)
    negative_expanded = np.stack([expand_to_canvas(k, args.SCALE, args.SIM_SIZE) for k in negative], axis=0)

    if not 0 <= args.KERNEL_INDEX < kernels.shape[0]:
        raise IndexError(f"KERNEL_INDEX={args.KERNEL_INDEX} out of range for {kernels.shape[0]} kernels")

    wavelength_m = cfg.wavelength_nm * 1e-9
    pitch_m = cfg.grid_pitch_nm * 1e-9
    distance_m = cfg.detector_distance_mm * 1e-3
    pos_target = positive_expanded[args.KERNEL_INDEX]
    neg_target = negative_expanded[args.KERNEL_INDEX]
    pos_phase = np.angle(angular_spectrum_backprop(pos_target, -distance_m, wavelength_m, pitch_m)).astype(np.float32)
    neg_phase = np.angle(angular_spectrum_backprop(neg_target, -distance_m, wavelength_m, pitch_m)).astype(np.float32)

    args.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.OUTPUT_DIR / "dagm_psf_targets.npz",
        kernels=kernels,
        positive=positive,
        negative=negative,
        positive_expanded=positive_expanded,
        negative_expanded=negative_expanded,
        positive_preview_target=pos_target,
        negative_preview_target=neg_target,
        positive_preview_backphase=pos_phase,
        negative_preview_backphase=neg_phase,
        scale=np.array(args.SCALE, dtype=np.int32),
        sim_size=np.array(args.SIM_SIZE, dtype=np.int32),
        kernel_index=np.array(args.KERNEL_INDEX, dtype=np.int32),
    )
    (args.OUTPUT_DIR / "psf_config.json").write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
    (args.OUTPUT_DIR / "kernel_stats.json").write_text(
        json.dumps(kernel_stats(kernels, positive, negative), indent=2), encoding="utf-8"
    )

    if args.SAVE_FIGURES:
        save_kernel_grid(args.OUTPUT_DIR / "kernel_grid_signed.png", kernels, "DAGM learned signed optical kernels", args.PREVIEW_KERNELS)
        save_kernel_grid(args.OUTPUT_DIR / "kernel_grid_positive.png", positive, "DAGM positive kernel components", args.PREVIEW_KERNELS)
        save_kernel_grid(args.OUTPUT_DIR / "kernel_grid_negative.png", negative, "DAGM negative kernel components", args.PREVIEW_KERNELS)
        save_psf_preview(args.OUTPUT_DIR / "psf_backphase_preview.png", pos_target, neg_target, pos_phase, neg_phase, args.KERNEL_INDEX)
        save_psf_target_crop(args.OUTPUT_DIR / "psf_target_center_crop.png", pos_target, neg_target, args.KERNEL_INDEX)

    print(f"Saved DAGM PSF target package to {args.OUTPUT_DIR}")
    print(f"kernels shape: {kernels.shape}")
    print(f"positive_expanded shape: {positive_expanded.shape}")
    print(f"negative_expanded shape: {negative_expanded.shape}")


if __name__ == "__main__":
    main()
