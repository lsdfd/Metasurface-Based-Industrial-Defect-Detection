from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F


@dataclass
class BinaryMetrics:
    loss: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    threshold: float = 0.5


@dataclass
class DistillationBreakdown:
    total: torch.Tensor
    task: torch.Tensor
    kd: torch.Tensor


def binary_metrics_from_probs(
    probs: torch.Tensor,
    labels: torch.Tensor,
    loss: torch.Tensor,
    threshold: float = 0.5,
) -> BinaryMetrics:
    preds = (probs >= threshold).float()
    labels = labels.float()
    tp = ((preds == 1) & (labels == 1)).sum().item()
    tn = ((preds == 0) & (labels == 0)).sum().item()
    fp = ((preds == 1) & (labels == 0)).sum().item()
    fn = ((preds == 0) & (labels == 1)).sum().item()
    total = max(tp + tn + fp + fn, 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    return BinaryMetrics(
        loss=loss.item(),
        accuracy=(tp + tn) / total,
        precision=precision,
        recall=recall,
        f1=f1,
        threshold=threshold,
    )


def threshold_sweep_from_probs(
    probs: torch.Tensor,
    labels: torch.Tensor,
    loss: torch.Tensor,
    thresholds: torch.Tensor | None = None,
) -> list[BinaryMetrics]:
    if thresholds is None:
        thresholds = torch.linspace(0.05, 0.95, steps=19)
    return [
        binary_metrics_from_probs(probs, labels, loss, threshold=float(threshold.item()))
        for threshold in thresholds
    ]


def distillation_loss(
    student_logits: torch.Tensor,
    labels: torch.Tensor,
    teacher_probs: torch.Tensor,
    alpha: float,
    temperature: float,
    kd_target: str = "prob",
    pos_weight: torch.Tensor | None = None,
) -> DistillationBreakdown:
    """Binary KD loss for sigmoid teachers.

    `kd_target="prob"` matches softened teacher probabilities.
    `kd_target="logit"` matches teacher logits directly after temperature scaling.
    """

    labels = labels.float().view_as(student_logits)
    teacher_probs = teacher_probs.detach().clamp(1e-6, 1 - 1e-6).view_as(student_logits)
    teacher_logits = torch.logit(teacher_probs)

    task_loss = F.binary_cross_entropy_with_logits(student_logits, labels, pos_weight=pos_weight)

    if kd_target == "prob":
        soft_targets = torch.sigmoid(teacher_logits / temperature)
        kd_loss = F.binary_cross_entropy_with_logits(student_logits / temperature, soft_targets)
        kd_loss = kd_loss * (temperature**2)
    elif kd_target == "logit":
        kd_loss = F.mse_loss(student_logits / temperature, teacher_logits / temperature)
        kd_loss = kd_loss * (temperature**2)
    else:
        raise ValueError(f"Unsupported kd_target: {kd_target}")

    total = alpha * task_loss + (1 - alpha) * kd_loss
    return DistillationBreakdown(total=total, task=task_loss, kd=kd_loss)


def baseline_student_loss(
    student_logits: torch.Tensor,
    labels: torch.Tensor,
    pos_weight: torch.Tensor | None = None,
) -> DistillationBreakdown:
    labels = labels.float().view_as(student_logits)
    task_loss = F.binary_cross_entropy_with_logits(student_logits, labels, pos_weight=pos_weight)
    zero = torch.zeros_like(task_loss)
    return DistillationBreakdown(total=task_loss, task=task_loss, kd=zero)
