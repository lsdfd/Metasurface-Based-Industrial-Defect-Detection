from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


@dataclass
class CMOSReconstructionConfig:
    positive_gain: float = 1.0
    negative_gain: float = 1.0
    electronic_bias: float = 0.0
    apply_relu: bool = True


class ElectronicBackendReadout(nn.Module):
    """Digital readout head matching the distilled student's FC backend."""

    def __init__(self, optical_kernels: int = 16, pooled_size: int = 6, hidden_dim: int = 256):
        super().__init__()
        self.pool = nn.AdaptiveAvgPool2d((pooled_size, pooled_size))
        self.backend = nn.Sequential(
            nn.Flatten(),
            nn.Linear(optical_kernels * pooled_size * pooled_size, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, 1),
        )

    def forward_logits(self, reconstructed_features: torch.Tensor) -> torch.Tensor:
        pooled = self.pool(reconstructed_features)
        return self.backend(pooled)

    def forward(self, reconstructed_features: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.forward_logits(reconstructed_features))

    def load_student_backend(self, checkpoint_path: str | Path, map_location: str | torch.device = "cpu") -> None:
        state = torch.load(checkpoint_path, map_location=map_location)
        self.backend.load_state_dict(
            {
                "1.weight": state["backend.1.weight"],
                "1.bias": state["backend.1.bias"],
                "3.weight": state["backend.3.weight"],
                "3.bias": state["backend.3.bias"],
            }
        )


class CMOSHybridClassifier(nn.Module):
    """Reconstruct signed optical channels from two CMOS branches and run the FC backend."""

    def __init__(
        self,
        optical_kernels: int = 16,
        pooled_size: int = 6,
        hidden_dim: int = 256,
        reconstruction: CMOSReconstructionConfig | None = None,
    ):
        super().__init__()
        self.reconstruction = reconstruction or CMOSReconstructionConfig()
        self.readout = ElectronicBackendReadout(
            optical_kernels=optical_kernels,
            pooled_size=pooled_size,
            hidden_dim=hidden_dim,
        )

    def reconstruct_features(self, positive_cmos: torch.Tensor, negative_cmos: torch.Tensor) -> torch.Tensor:
        features = (
            self.reconstruction.positive_gain * positive_cmos
            - self.reconstruction.negative_gain * negative_cmos
            + self.reconstruction.electronic_bias
        )
        if self.reconstruction.apply_relu:
            features = torch.relu(features)
        return features

    def forward_logits(self, positive_cmos: torch.Tensor, negative_cmos: torch.Tensor) -> torch.Tensor:
        return self.readout.forward_logits(self.reconstruct_features(positive_cmos, negative_cmos))

    def forward(self, positive_cmos: torch.Tensor, negative_cmos: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.forward_logits(positive_cmos, negative_cmos))

    def load_student_backend(self, checkpoint_path: str | Path, map_location: str | torch.device = "cpu") -> None:
        self.readout.load_student_backend(checkpoint_path, map_location=map_location)


def ensure_batched_4d(array: np.ndarray, name: str) -> np.ndarray:
    if array.ndim == 3:
        return array[None, ...]
    if array.ndim == 4:
        return array
    raise ValueError(f"{name} must have shape [K,H,W] or [B,K,H,W], got {array.shape}")


def load_cmos_npz(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(path)
    if "positive_cmos" not in data or "negative_cmos" not in data:
        raise ValueError("NPZ must contain 'positive_cmos' and 'negative_cmos'.")
    positive = ensure_batched_4d(np.asarray(data["positive_cmos"], dtype=np.float32), "positive_cmos")
    negative = ensure_batched_4d(np.asarray(data["negative_cmos"], dtype=np.float32), "negative_cmos")
    if positive.shape != negative.shape:
        raise ValueError(f"positive and negative CMOS stacks must match, got {positive.shape} vs {negative.shape}")
    return positive, negative
