import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import torch

import utils
from config import Config
from data.dataset_catalog import get_dataset
from distill.models import OpticalSegDecStudent


def str2bool(value):
    return value.lower() in ("1", "true", "yes", "y")


def parse_channels(value):
    channels = tuple(int(v.strip()) for v in value.split(",") if v.strip())
    if len(channels) != 3:
        raise ValueError("--EXTRACTOR_CHANNELS must have exactly three comma-separated integers.")
    return channels


def build_cfg(args):
    cfg = Config()
    cfg.GPU = args.GPU
    cfg.RUN_NAME = args.RUN_NAME
    cfg.DATASET = "DAGM"
    cfg.DATASET_PATH = args.DATASET_PATH
    cfg.RESULTS_PATH = args.RESULTS_PATH
    cfg.EPOCHS = 1
    cfg.LEARNING_RATE = 0.001
    cfg.DELTA_CLS_LOSS = 1.0
    cfg.BATCH_SIZE = args.BATCH_SIZE
    cfg.WEIGHTED_SEG_LOSS = True
    cfg.WEIGHTED_SEG_LOSS_P = 1.0
    cfg.WEIGHTED_SEG_LOSS_MAX = 10.0
    cfg.DYN_BALANCED_LOSS = True
    cfg.GRADIENT_ADJUSTMENT = True
    cfg.FREQUENCY_SAMPLING = False
    cfg.NUM_SEGMENTED = 1000
    cfg.FOLD = args.FOLD
    cfg.DILATE = 1
    cfg.VALIDATE = True
    cfg.VALIDATE_ON_TEST = True
    cfg.SAVE_IMAGES = False
    cfg.REPRODUCIBLE_RUN = True
    cfg.MAX_TRAIN_SAMPLES = None
    cfg.MAX_VAL_SAMPLES = args.MAX_VAL_SAMPLES
    cfg.INPUT_SIZE = args.INPUT_SIZE
    cfg.TRAIN_MODE = "JOINT"
    cfg.init_extra()
    return cfg


def resize_mask_like(mask, target_hw):
    if mask.shape[-2:] == target_hw:
        return mask
    return torch.nn.functional.interpolate(mask, size=target_hw, mode="nearest")


def overlay_heatmap(image, pred):
    image_np = image.detach().cpu().numpy()[0]
    image_np = np.clip(image_np * 255.0, 0, 255).astype(np.uint8)
    image_rgb = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
    pred_np = pred.detach().cpu().numpy()
    pred_np = cv2.resize(pred_np, (image_rgb.shape[1], image_rgb.shape[0]))
    heat = cv2.applyColorMap(np.clip(pred_np * 255.0, 0, 255).astype(np.uint8), cv2.COLORMAP_JET)
    return cv2.addWeighted(image_rgb, 0.65, heat, 0.35, 0)


def save_panel(output_dir, sample_name, image, gt, pred, score):
    output_dir.mkdir(parents=True, exist_ok=True)
    image_np = image.detach().cpu().numpy()[0]
    image_np = np.clip(image_np * 255.0, 0, 255).astype(np.uint8)
    image_rgb = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)

    gt_np = gt.detach().cpu().numpy()
    pred_np = pred.detach().cpu().numpy()
    gt_up = cv2.resize(gt_np, (image_rgb.shape[1], image_rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
    pred_up = cv2.resize(pred_np, (image_rgb.shape[1], image_rgb.shape[0]))

    gt_rgb = cv2.cvtColor((gt_up * 255.0).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    pred_heat = cv2.applyColorMap(np.clip(pred_up * 255.0, 0, 255).astype(np.uint8), cv2.COLORMAP_JET)
    overlay = overlay_heatmap(image, pred)
    panel = np.concatenate([image_rgb, gt_rgb, pred_heat, overlay], axis=1)

    safe_name = str(sample_name).replace("/", "_")
    cv2.imwrite(str(output_dir / f"{score:.4f}_{safe_name}.jpg"), panel)


def threshold_sweep(seg_predictions, seg_labels):
    thresholds = [round(v, 2) for v in np.arange(0.05, 0.96, 0.05)]
    rows = []
    for threshold in thresholds:
        metrics = utils.get_segmentation_metrics(seg_predictions, seg_labels, threshold=threshold)
        rows.append(metrics)
    best_by_dice = max(rows, key=lambda item: item["mean_dice"])
    best_by_iou = max(rows, key=lambda item: item["mean_iou"])
    return {
        "thresholds": rows,
        "best_by_dice": best_by_dice,
        "best_by_iou": best_by_iou,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--GPU", type=int, default=0)
    parser.add_argument("--RUN_NAME", required=True)
    parser.add_argument("--DATASET_PATH", default="./datasets/DAGM")
    parser.add_argument("--RESULTS_PATH", default="./results-dagm-distill-arch")
    parser.add_argument("--CHECKPOINT", required=True)
    parser.add_argument("--OUTPUT_DIR", required=True)
    parser.add_argument("--FOLD", type=int, default=7)
    parser.add_argument("--INPUT_SIZE", type=int, required=True)
    parser.add_argument("--OPTICAL_CHANNELS", type=int, required=True)
    parser.add_argument("--OPTICAL_KERNEL_SIZE", type=int, required=True)
    parser.add_argument("--DOWNSAMPLE_FACTOR", type=int, required=True)
    parser.add_argument("--EXTRACTOR_CHANNELS", default="8,16,24")
    parser.add_argument("--MAX_VAL_SAMPLES", type=int, default=None)
    parser.add_argument("--BATCH_SIZE", type=int, default=1)
    parser.add_argument("--SAVE_LIMIT", type=int, default=24)
    parser.add_argument("--SAVE_POS_ONLY", type=str2bool, default=False)
    args = parser.parse_args()

    device = f"cuda:{args.GPU}" if torch.cuda.is_available() and args.GPU >= 0 else "cpu"
    cfg = build_cfg(args)
    loader = get_dataset("VAL", cfg)

    model = OpticalSegDecStudent(
        input_channels=cfg.INPUT_CHANNELS,
        optical_channels=args.OPTICAL_CHANNELS,
        optical_kernel_size=args.OPTICAL_KERNEL_SIZE,
        downsample_factor=args.DOWNSAMPLE_FACTOR,
        extractor_channels=parse_channels(args.EXTRACTOR_CHANNELS),
    ).to(device)
    model.load_state_dict(torch.load(args.CHECKPOINT, map_location=device))
    model.eval()

    predictions, labels = [], []
    seg_predictions, seg_labels = [], []
    saved = 0
    output_dir = Path(args.OUTPUT_DIR)

    with torch.no_grad():
        for image, seg_mask, _, _, sample_name in loader:
            image = image.to(device)
            seg_mask = seg_mask.to(device)
            pred, pred_seg, _, _ = model(image)
            pred_prob = torch.sigmoid(pred)
            pred_seg_prob = torch.sigmoid(pred_seg)
            seg_mask = resize_mask_like(seg_mask, pred_seg_prob.shape[-2:])

            for idx in range(image.size(0)):
                score = float(pred_prob[idx].item())
                gt_is_pos = bool(seg_mask[idx].max().item() > 0)
                predictions.append(score)
                labels.append(gt_is_pos)
                seg_predictions.append(pred_seg_prob[idx, 0].detach().cpu().numpy())
                seg_labels.append(seg_mask[idx, 0].detach().cpu().numpy())

                if saved < args.SAVE_LIMIT and (gt_is_pos or not args.SAVE_POS_ONLY):
                    name = sample_name[idx] if isinstance(sample_name, (list, tuple)) else sample_name
                    save_panel(output_dir, name, image[idx], seg_mask[idx, 0], pred_seg_prob[idx, 0], score)
                    saved += 1

    cls_metrics = utils.get_metrics(np.asarray(labels), np.asarray(predictions))
    seg_predictions = np.asarray(seg_predictions)
    seg_labels = np.asarray(seg_labels)
    seg_metrics = utils.get_segmentation_metrics(seg_predictions, seg_labels)
    sweep_metrics = threshold_sweep(seg_predictions, seg_labels)
    metrics = {
        "AP": float(cls_metrics["AP"]),
        "AUC": float(cls_metrics["AUC"]),
        "best_f_measure": float(cls_metrics["best_f_measure"]),
        "segmentation": seg_metrics,
        "segmentation_threshold_sweep": sweep_metrics,
        "num_samples": len(labels),
        "saved_images": saved,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "metrics.json").open("w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
