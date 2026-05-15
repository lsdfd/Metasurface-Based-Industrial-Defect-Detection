import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch


GREEN_PHASE_COEFFS = {
    "a": -2.28293,
    "b": 0.01878,
    "c": -0.07134,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run first-pass metasurface phase/radius optimization for selected DAGM PSF targets."
    )
    parser.add_argument("--KERNEL_PACKAGE", type=Path, required=True, help="Path to dagm_psf_targets.npz")
    parser.add_argument("--OUTPUT_ROOT", type=Path, required=True)
    parser.add_argument("--KERNEL_INDICES", type=int, nargs="+", default=[0, 51, 53, 37])
    parser.add_argument("--ITERATIONS", type=int, default=40)
    parser.add_argument("--LR", type=float, default=5e-3)
    parser.add_argument("--ROI_SIZE", type=int, default=96)
    parser.add_argument("--RADIUS_MIN_UM", type=float, default=0.0)
    parser.add_argument("--RADIUS_MAX_UM", type=float, default=0.240)
    parser.add_argument("--WAVELENGTH_NM", type=float, default=532.0)
    parser.add_argument("--GRID_PITCH_NM", type=float, default=586.0)
    parser.add_argument("--DETECTOR_DISTANCE_MM", type=float, default=2.4)
    parser.add_argument("--DEVICE", default="auto")
    return parser.parse_args()


def choose_device(device_arg: str):
    if device_arg != "auto":
        return torch.device(device_arg)
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def phase_cycles_from_radius(radius_um: torch.Tensor):
    a = GREEN_PHASE_COEFFS["a"]
    b = GREEN_PHASE_COEFFS["b"]
    c = GREEN_PHASE_COEFFS["c"]
    return a * (torch.exp((radius_um * radius_um - 2.0 * b * radius_um) / c) - 1.0)


def phase_radians_from_radius(radius_um: torch.Tensor):
    return phase_cycles_from_radius(radius_um) * (2.0 * math.pi)


def initialize_radius_from_backphase(backphase_rad, radius_min_um, radius_max_um):
    radius_samples = np.linspace(radius_min_um, radius_max_um, 4000, dtype=np.float32)
    phase_cycles = GREEN_PHASE_COEFFS["a"] * (
        np.exp((radius_samples * radius_samples - 2.0 * GREEN_PHASE_COEFFS["b"] * radius_samples) / GREEN_PHASE_COEFFS["c"]) - 1.0
    )
    phase_rad = phase_cycles * (2.0 * np.pi)
    phase_wrapped = np.mod(phase_rad, 2.0 * np.pi)
    target_wrapped = np.mod(backphase_rad, 2.0 * np.pi)
    distances = np.abs(np.angle(np.exp(1j * (target_wrapped.reshape(-1, 1) - phase_wrapped.reshape(1, -1)))))
    nearest = distances.argmin(axis=1)
    return radius_samples[nearest].reshape(backphase_rad.shape)


def get_frequencies(nx, ny, dx, dy, device):
    kx = torch.fft.fftfreq(nx, d=dx, device=device) * (2.0 * math.pi)
    ky = torch.fft.fftfreq(ny, d=dy, device=device) * (2.0 * math.pi)
    k_y, k_x = torch.meshgrid(ky, kx, indexing="xy")
    return k_x, k_y


def propagate_angular_spectrum(field, wavelength_m, z_m, dx, dy):
    nx, ny = field.shape
    k = 2.0 * math.pi / wavelength_m
    k_x, k_y = get_frequencies(nx, ny, dx, dy, field.device)
    kz_squared = (k**2 - k_x**2 - k_y**2).to(torch.complex64)
    k_z = torch.sqrt(kz_squared)
    spectrum = torch.fft.fft2(field)
    propagator = torch.exp(1j * k_z * z_m)
    return torch.fft.ifft2(spectrum * propagator)


def angular_spectrum_backprop(field, z_m, wavelength_m, pitch_m):
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


def centered_roi_bounds(array, roi_size):
    nonzero = np.argwhere(array > 1e-8)
    height, width = array.shape
    if nonzero.size == 0:
        center_y = height // 2
        center_x = width // 2
    else:
        y_min, x_min = nonzero.min(axis=0)
        y_max, x_max = nonzero.max(axis=0)
        center_y = (y_min + y_max) // 2
        center_x = (x_min + x_max) // 2

    roi_size = min(roi_size, height, width)
    half = roi_size // 2
    top = max(0, center_y - half)
    left = max(0, center_x - half)
    bottom = min(height, top + roi_size)
    right = min(width, left + roi_size)
    top = max(0, bottom - roi_size)
    left = max(0, right - roi_size)
    return top, bottom, left, right


def crop(array, bounds):
    top, bottom, left, right = bounds
    return array[top:bottom, left:right]


def normalize_l2(x):
    return x / torch.linalg.norm(x).clamp_min(1e-12)


def numpy_metrics(target, simulated):
    target_l2 = target / max(float(np.linalg.norm(target)), 1e-12)
    simulated_l2 = simulated / max(float(np.linalg.norm(simulated)), 1e-12)
    diff = simulated_l2 - target_l2
    cosine = float(np.sum(target_l2 * simulated_l2))
    mse = float(np.mean(diff**2))
    rel_l2 = float(np.linalg.norm(diff) / max(float(np.linalg.norm(target_l2)), 1e-12))
    return {
        "mse_l2_normalized": mse,
        "relative_l2": rel_l2,
        "cosine_similarity": cosine,
        "target_sum": float(target.sum()),
        "simulated_sum": float(simulated.sum()),
        "target_max": float(target.max()),
        "simulated_max": float(simulated.max()),
    }


def save_preview(path, target, simulated, phase, radius, losses, title):
    target_l2 = target / max(float(np.linalg.norm(target)), 1e-12)
    simulated_l2 = simulated / max(float(np.linalg.norm(simulated)), 1e-12)
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    axes[0, 0].imshow(target_l2, cmap="gray")
    axes[0, 0].set_title("Target ROI")
    axes[0, 1].imshow(simulated_l2, cmap="gray")
    axes[0, 1].set_title("Simulated ROI")
    axes[0, 2].imshow(simulated_l2 - target_l2, cmap="bwr")
    axes[0, 2].set_title("Difference")
    axes[1, 0].imshow(np.mod(phase, 2.0 * np.pi), cmap="twilight")
    axes[1, 0].set_title("Phase mod 2pi")
    axes[1, 1].imshow(radius, cmap="viridis")
    axes[1, 1].set_title("Radius um")
    axes[1, 2].plot(losses)
    axes[1, 2].set_title("Loss")
    for ax in axes.reshape(-1):
        if ax is not axes[1, 2]:
            ax.axis("off")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def optimize_one(target_full, kernel_index, branch, args, device):
    wavelength_m = args.WAVELENGTH_NM * 1e-9
    pitch_m = args.GRID_PITCH_NM * 1e-9
    distance_m = args.DETECTOR_DISTANCE_MM * 1e-3

    backprop = angular_spectrum_backprop(target_full, -distance_m, wavelength_m, pitch_m)
    backphase_full = np.angle(backprop).astype(np.float32)
    bounds = centered_roi_bounds(target_full, args.ROI_SIZE)
    target_roi = crop(target_full, bounds).astype(np.float32)
    backphase_roi = crop(backphase_full, bounds).astype(np.float32)
    init_radius = initialize_radius_from_backphase(backphase_roi, args.RADIUS_MIN_UM, args.RADIUS_MAX_UM)

    radius = torch.tensor(init_radius, dtype=torch.float32, device=device, requires_grad=True)
    target = torch.tensor(target_roi, dtype=torch.float32, device=device)
    optimizer = torch.optim.Adam([radius], lr=args.LR)
    losses = []

    for _ in range(args.ITERATIONS):
        optimizer.zero_grad()
        radius_clamped = torch.clamp(radius, args.RADIUS_MIN_UM, args.RADIUS_MAX_UM)
        phase = phase_radians_from_radius(radius_clamped)
        field = torch.exp(1j * phase.to(torch.complex64))
        propagated = propagate_angular_spectrum(field, wavelength_m, distance_m, pitch_m, pitch_m)
        intensity = torch.abs(propagated) ** 2
        simulated = normalize_l2(intensity)
        desired = normalize_l2(target)
        loss = torch.mean((simulated - desired) ** 2)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.item()))

    radius_final = torch.clamp(radius.detach(), args.RADIUS_MIN_UM, args.RADIUS_MAX_UM)
    phase_final = phase_radians_from_radius(radius_final).detach()
    field_final = torch.exp(1j * phase_final.to(torch.complex64))
    propagated_final = propagate_angular_spectrum(field_final, wavelength_m, distance_m, pitch_m, pitch_m)
    simulated_roi = (torch.abs(propagated_final) ** 2).detach().cpu().numpy().astype(np.float32)
    phase_roi = phase_final.cpu().numpy().astype(np.float32)
    radius_roi = radius_final.cpu().numpy().astype(np.float32)
    metrics = numpy_metrics(target_roi, simulated_roi)

    out_dir = args.OUTPUT_ROOT / f"kernel_{kernel_index:02d}" / branch
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_dir / "optimized_result.npz",
        target_roi=target_roi,
        simulated_roi=simulated_roi,
        phase_roi=phase_roi,
        radius_roi=radius_roi,
        init_radius_roi=init_radius.astype(np.float32),
        loss_history=np.asarray(losses, dtype=np.float32),
        roi_bounds=np.asarray(bounds, dtype=np.int32),
    )
    save_preview(
        out_dir / "optimization_preview.png",
        target_roi,
        simulated_roi,
        phase_roi,
        radius_roi,
        losses,
        title=f"DAGM kernel {kernel_index} {branch}",
    )

    summary = {
        "kernel_index": int(kernel_index),
        "branch": branch,
        "iterations": int(args.ITERATIONS),
        "learning_rate": float(args.LR),
        "roi_size": int(args.ROI_SIZE),
        "roi_bounds": [int(v) for v in bounds],
        "device": str(device),
        "final_loss": float(losses[-1]),
        "loss_start": float(losses[0]),
        "metrics": metrics,
    }
    (out_dir / "result_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    args = parse_args()
    device = choose_device(args.DEVICE)
    data = np.load(args.KERNEL_PACKAGE)
    positive_all = data["positive_expanded"]
    negative_all = data["negative_expanded"]
    total = int(data["kernels"].shape[0])

    results = []
    for kernel_index in args.KERNEL_INDICES:
        if kernel_index < 0 or kernel_index >= total:
            raise ValueError(f"kernel index {kernel_index} out of range [0, {total - 1}]")
        pos = positive_all[kernel_index].astype(np.float32)
        neg = negative_all[kernel_index].astype(np.float32)
        results.append(optimize_one(pos, kernel_index, "positive", args, device))
        results.append(optimize_one(neg, kernel_index, "negative", args, device))
        print(json.dumps(results[-2:], indent=2))

    args.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    batch_summary = {
        "kernel_package": str(args.KERNEL_PACKAGE),
        "kernel_indices": [int(i) for i in args.KERNEL_INDICES],
        "iterations": int(args.ITERATIONS),
        "learning_rate": float(args.LR),
        "roi_size": int(args.ROI_SIZE),
        "device": str(device),
        "results": results,
    }
    (args.OUTPUT_ROOT / "batch_summary.json").write_text(json.dumps(batch_summary, indent=2), encoding="utf-8")
    print(f"Saved DAGM metasurface batch summary to {args.OUTPUT_ROOT / 'batch_summary.json'}")


if __name__ == "__main__":
    main()
