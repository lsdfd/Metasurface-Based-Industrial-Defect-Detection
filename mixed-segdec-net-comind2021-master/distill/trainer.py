import os
import random
import json
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

import utils
from config import Config
from data.dataset_catalog import get_dataset
from distill.losses import (
    foreground_weighted_bce_with_logits,
    masked_bce_with_logits,
    mse_feature_loss,
    relation_distillation_loss,
    soft_bce,
)
from distill.models import OpticalSegDecStudent
from models import SegDecNet


@dataclass
class DistillWeights:
    seg_task: float = 1.0
    cls_task: float = 0.2
    seg_kd: float = 1.0
    cls_kd: float = 0.5
    volume_kd: float = 0.5
    relation_kd: float = 0.05


class TeacherWithFeatures(SegDecNet):
    def forward(self, input):
        volume = self.volume(input)
        seg_mask = self.seg_mask(volume)
        cat = torch.cat([volume, seg_mask], dim=1)
        cat = self.volume_lr_multiplier_layer(cat, self.volume_lr_multiplier_mask)
        features = self.extractor(cat)
        global_max_feat = torch.amax(features, dim=(-1, -2))
        global_avg_feat = torch.mean(features, dim=(-1, -2))
        global_max_seg = torch.amax(seg_mask, dim=(-1, -2))
        global_avg_seg = torch.mean(seg_mask, dim=(-1, -2))
        fc_in = torch.cat([global_max_feat, global_avg_feat, global_max_seg, global_avg_seg], dim=1)
        prediction = self.fc(fc_in)
        return prediction, seg_mask, volume


class TeacherVolumeAdapter(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.proj = nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
        self.norm = nn.BatchNorm2d(out_channels)
        self.act = nn.ReLU()

    def forward(self, x):
        return self.act(self.norm(self.proj(x)))


class DistillationTrainer:
    def __init__(
        self,
        cfg: Config,
        teacher_ckpt: str,
        run_dir: str,
        weights: DistillWeights,
        stage1_epochs: int = 5,
        optical_channels: int = 32,
        optical_kernel_size: int = 7,
        downsample_factor: int = 8,
        extractor_channels=(8, 16, 24),
        seg_kd_temperature: float = 1.0,
        seg_kd_foreground_weight: float = 1.0,
    ):
        self.cfg = cfg
        self.teacher_ckpt = teacher_ckpt
        self.run_dir = run_dir
        self.weights = weights
        self.stage1_epochs = stage1_epochs
        self.optical_channels = optical_channels
        self.optical_kernel_size = optical_kernel_size
        self.downsample_factor = downsample_factor
        self.extractor_channels = extractor_channels
        self.seg_kd_temperature = seg_kd_temperature
        self.seg_kd_foreground_weight = seg_kd_foreground_weight
        self.device = self._get_device()

        self.model_dir = os.path.join(self.run_dir, "models")
        utils.create_folder(self.run_dir)
        utils.create_folder(self.model_dir)

    def _get_device(self):
        if torch.cuda.is_available() and self.cfg.GPU is not None and self.cfg.GPU >= 0:
            return f"cuda:{self.cfg.GPU}"
        return "cpu"

    def _log(self, message):
        print(message)

    def _build_teacher(self):
        teacher = TeacherWithFeatures(self.device, self.cfg.INPUT_WIDTH, self.cfg.INPUT_HEIGHT, self.cfg.INPUT_CHANNELS).to(self.device)
        teacher.set_gradient_multipliers(0.0)
        teacher.load_state_dict(torch.load(self.teacher_ckpt, map_location=self.device))
        teacher.eval()
        for p in teacher.parameters():
            p.requires_grad = False
        return teacher

    def _build_student(self):
        return OpticalSegDecStudent(
            input_channels=self.cfg.INPUT_CHANNELS,
            optical_channels=self.optical_channels,
            optical_kernel_size=self.optical_kernel_size,
            downsample_factor=self.downsample_factor,
            extractor_channels=self.extractor_channels,
        ).to(self.device)

    def _save_run_metadata(self, student):
        metadata = {
            "cfg": self.cfg.get_as_dict(),
            "teacher_ckpt": self.teacher_ckpt,
            "weights": self.weights.__dict__,
            "stage1_epochs": self.stage1_epochs,
            "seg_kd_temperature": self.seg_kd_temperature,
            "seg_kd_foreground_weight": self.seg_kd_foreground_weight,
            "downsample_factor": self.downsample_factor,
            "extractor_channels": self.extractor_channels,
            "student": student.architecture_summary(),
        }
        with open(os.path.join(self.run_dir, "distill_config.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        with open(os.path.join(self.run_dir, "student_architecture.txt"), "w") as f:
            f.write(str(student))
            f.write("\n\n")
            f.write(json.dumps(student.architecture_summary(), indent=2))

    def _save_optical_kernels(self, student, filename="optical_kernels.npy"):
        np.save(os.path.join(self.model_dir, filename), student.optical_kernels_numpy())

    def _match_spatial(self, tensor, target_hw, mode="bilinear"):
        if tensor.shape[-2:] == target_hw:
            return tensor
        if mode == "nearest":
            return F.interpolate(tensor, size=target_hw, mode=mode)
        return F.interpolate(tensor, size=target_hw, mode=mode, align_corners=False)

    def _set_seed(self):
        if self.cfg.REPRODUCIBLE_RUN:
            np.random.seed(1337)
            torch.manual_seed(1337)
            random.seed(1337)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def train(self):
        self._set_seed()

        teacher = self._build_teacher()
        student = self._build_student()
        teacher_adapter = TeacherVolumeAdapter(in_channels=1024, out_channels=self.optical_channels).to(self.device)
        self._save_run_metadata(student)

        train_loader = get_dataset("TRAIN", self.cfg)
        val_loader = get_dataset("VAL", self.cfg)

        optimizer = torch.optim.Adam(list(student.parameters()) + list(teacher_adapter.parameters()), lr=self.cfg.LEARNING_RATE)
        best_metric = -1.0

        for epoch in range(self.cfg.EPOCHS):
            stage = 1 if epoch < self.stage1_epochs else 2
            student.train()
            teacher_adapter.train()

            if stage == 1:
                for name, param in student.named_parameters():
                    if name.startswith("extractor") or name.startswith("fc"):
                        param.requires_grad = False
                for param in teacher_adapter.parameters():
                    param.requires_grad = True
            else:
                for param in student.parameters():
                    param.requires_grad = True
                for param in teacher_adapter.parameters():
                    param.requires_grad = False
                teacher_adapter.eval()

            epoch_loss = 0.0
            for batch in train_loader:
                images, seg_masks, seg_loss_masks, _, _ = batch
                images = images.to(self.device)
                seg_masks = seg_masks.to(self.device)
                seg_loss_masks = seg_loss_masks.to(self.device)
                is_pos = seg_masks.amax(dim=(-1, -2, -3)).reshape((-1, 1))

                with torch.no_grad():
                    teacher_pred, teacher_seg, teacher_volume = teacher(images)
                    teacher_prob = torch.sigmoid(teacher_pred)
                    teacher_seg_prob = torch.sigmoid(teacher_seg / self.seg_kd_temperature)

                student_pred, student_seg, student_volume, _ = student(images)

                volume_target = teacher_adapter(teacher_volume)
                volume_target = self._match_spatial(volume_target, student_volume.shape[-2:])
                seg_masks_for_student = self._match_spatial(seg_masks, student_seg.shape[-2:], mode="nearest")
                seg_loss_masks_for_student = self._match_spatial(seg_loss_masks, student_seg.shape[-2:])
                teacher_seg_prob_for_student = self._match_spatial(teacher_seg_prob, student_seg.shape[-2:])

                loss_seg_task = masked_bce_with_logits(student_seg, seg_masks_for_student, seg_loss_masks_for_student)
                loss_cls_task = nn.BCEWithLogitsLoss()(student_pred, is_pos)
                loss_seg_kd = foreground_weighted_bce_with_logits(
                    student_seg / self.seg_kd_temperature,
                    teacher_seg_prob_for_student,
                    seg_loss_masks_for_student,
                    foreground_weight=self.seg_kd_foreground_weight,
                ) * (self.seg_kd_temperature ** 2)
                loss_cls_kd = soft_bce(student_pred, teacher_prob)
                loss_volume = mse_feature_loss(student_volume, volume_target)
                loss_relation = relation_distillation_loss(student_volume, volume_target)

                if stage == 1:
                    total_loss = (
                        self.weights.seg_task * loss_seg_task
                        + self.weights.seg_kd * loss_seg_kd
                        + self.weights.volume_kd * loss_volume
                        + self.weights.relation_kd * loss_relation
                    )
                else:
                    total_loss = (
                        self.weights.seg_task * loss_seg_task
                        + self.weights.cls_task * loss_cls_task
                        + self.weights.seg_kd * loss_seg_kd
                        + self.weights.cls_kd * loss_cls_kd
                        + self.weights.volume_kd * loss_volume
                        + self.weights.relation_kd * loss_relation
                    )

                optimizer.zero_grad()
                total_loss.backward()
                optimizer.step()
                epoch_loss += total_loss.item()

            self._log(f"[Distill] Epoch {epoch + 1}/{self.cfg.EPOCHS} stage={stage} loss={epoch_loss / len(train_loader):.5f}")

            if epoch % self.cfg.VALIDATION_N_EPOCHS == 0 or epoch == self.cfg.EPOCHS - 1:
                metrics = self.evaluate(student, val_loader)
                metric = metrics["dice"]
                if metric > best_metric:
                    best_metric = metric
                    torch.save(student.state_dict(), os.path.join(self.model_dir, "best_student.pth"))
                    self._save_optical_kernels(student, "best_optical_kernels.npy")
                    self._log(f"[Distill] Saved best student with Dice={metric:.5f}")
                torch.save(teacher_adapter.state_dict(), os.path.join(self.model_dir, "teacher_volume_adapter.pth"))

            if epoch % 5 == 0:
                torch.save(student.state_dict(), os.path.join(self.model_dir, f"student_ep_{epoch:02}.pth"))

        torch.save(student.state_dict(), os.path.join(self.model_dir, "final_student.pth"))
        self._save_optical_kernels(student, "final_optical_kernels.npy")

    def evaluate(self, student, loader):
        student.eval()
        predictions = []
        ground_truths = []
        seg_predictions = []
        seg_ground_truths = []

        with torch.no_grad():
            for image, seg_mask, _, _, _ in loader:
                image = image.to(self.device)
                seg_mask = seg_mask.to(self.device)
                pred, pred_seg, _, _ = student(image)
                pred = torch.sigmoid(pred)
                pred_seg = torch.sigmoid(pred_seg)
                seg_mask = self._match_spatial(seg_mask, pred_seg.shape[-2:], mode="nearest")

                predictions.append(pred.item())
                ground_truths.append((seg_mask.max() > 0).item())
                seg_predictions.append(pred_seg[0, 0].detach().cpu().numpy())
                seg_ground_truths.append(seg_mask[0, 0].detach().cpu().numpy())

        cls_metrics = utils.get_metrics(np.array(ground_truths), np.array(predictions))
        seg_metrics = utils.get_segmentation_metrics(np.array(seg_predictions), np.array(seg_ground_truths))
        self._log(
            f"[Distill] Validation AP={cls_metrics['AP']:.5f}, AUC={cls_metrics['AUC']:.5f}, "
            f"IoU={seg_metrics['mean_iou']:.5f}, Dice={seg_metrics['mean_dice']:.5f}"
        )
        return {
            "ap": cls_metrics["AP"],
            "auc": cls_metrics["AUC"],
            "iou": seg_metrics["mean_iou"],
            "dice": seg_metrics["mean_dice"],
        }
