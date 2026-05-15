import torch
import torch.nn.functional as F


def masked_bce_with_logits(logits, targets, masks=None):
    loss = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    if masks is not None:
        loss = loss * masks
    return loss.mean()


def foreground_weighted_bce_with_logits(logits, targets, masks=None, foreground_weight=1.0):
    loss = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    if foreground_weight > 1.0:
        weights = 1.0 + (foreground_weight - 1.0) * targets.detach()
        loss = loss * weights
    if masks is not None:
        loss = loss * masks
    return loss.mean()


def soft_bce(student_logits, teacher_probs):
    return F.binary_cross_entropy_with_logits(student_logits, teacher_probs)


def mse_feature_loss(student_features, teacher_features):
    return F.mse_loss(student_features, teacher_features)


def relation_distillation_loss(student_features, teacher_features):
    """
    Lightweight NTKD-style relation loss:
    match batch-wise feature similarity rather than a full Jacobian NTK.
    """
    s = student_features.reshape(student_features.size(0), -1)
    t = teacher_features.reshape(teacher_features.size(0), -1)

    s = F.normalize(s, dim=1)
    t = F.normalize(t, dim=1)
    gram_s = s @ s.t()
    gram_t = t @ t.t()
    return F.mse_loss(gram_s, gram_t)
