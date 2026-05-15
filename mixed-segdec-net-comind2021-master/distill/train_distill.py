import argparse
import os

from config import Config
from distill.trainer import DistillationTrainer, DistillWeights


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--GPU", type=int, required=True)
    parser.add_argument("--RUN_NAME", type=str, required=True)
    parser.add_argument("--DATASET", type=str, required=True)
    parser.add_argument("--DATASET_PATH", type=str, required=True)
    parser.add_argument("--RESULTS_PATH", type=str, required=True)
    parser.add_argument("--TEACHER_CKPT", type=str, required=True)
    parser.add_argument("--EPOCHS", type=int, required=True)
    parser.add_argument("--LEARNING_RATE", type=float, required=True)
    parser.add_argument("--BATCH_SIZE", type=int, required=True)
    parser.add_argument("--NUM_SEGMENTED", type=int, required=True)
    parser.add_argument("--FOLD", type=int, default=None)
    parser.add_argument("--TRAIN_NUM", type=int, default=None)
    parser.add_argument("--DILATE", type=int, default=15)
    parser.add_argument("--VALIDATE", type=str2bool, default=True)
    parser.add_argument("--VALIDATE_ON_TEST", type=str2bool, default=True)
    parser.add_argument("--VALIDATION_N_EPOCHS", type=int, default=5)
    parser.add_argument("--SAVE_IMAGES", type=str2bool, default=False)
    parser.add_argument("--WEIGHTED_SEG_LOSS", type=str2bool, default=True)
    parser.add_argument("--WEIGHTED_SEG_LOSS_P", type=float, default=2.0)
    parser.add_argument("--WEIGHTED_SEG_LOSS_MAX", type=float, default=3.0)
    parser.add_argument("--DYN_BALANCED_LOSS", type=str2bool, default=True)
    parser.add_argument("--GRADIENT_ADJUSTMENT", type=str2bool, default=True)
    parser.add_argument("--FREQUENCY_SAMPLING", type=str2bool, default=True)
    parser.add_argument("--REPRODUCIBLE_RUN", type=str2bool, default=False)
    parser.add_argument("--MAX_TRAIN_SAMPLES", type=int, default=None)
    parser.add_argument("--MAX_VAL_SAMPLES", type=int, default=None)
    parser.add_argument("--STAGE1_EPOCHS", type=int, default=5)
    parser.add_argument("--INPUT_SIZE", type=int, default=None)
    parser.add_argument("--OPTICAL_CHANNELS", type=int, default=32)
    parser.add_argument("--OPTICAL_KERNEL_SIZE", type=int, default=7)
    parser.add_argument("--DOWNSAMPLE_FACTOR", type=int, default=8)
    parser.add_argument("--EXTRACTOR_CHANNELS", type=str, default="8,16,24")
    parser.add_argument("--CLS_TASK_WEIGHT", type=float, default=0.2)
    parser.add_argument("--CLS_KD_WEIGHT", type=float, default=0.5)
    parser.add_argument("--SEG_TASK_WEIGHT", type=float, default=1.0)
    parser.add_argument("--SEG_KD_WEIGHT", type=float, default=1.0)
    parser.add_argument("--VOLUME_KD_WEIGHT", type=float, default=0.5)
    parser.add_argument("--RELATION_KD_WEIGHT", type=float, default=0.05)
    parser.add_argument("--SEG_KD_TEMPERATURE", type=float, default=1.0)
    parser.add_argument("--SEG_KD_FOREGROUND_WEIGHT", type=float, default=1.0)
    return parser.parse_args()


def build_cfg(args):
    cfg = Config()
    cfg.GPU = args.GPU
    cfg.RUN_NAME = args.RUN_NAME
    cfg.DATASET = args.DATASET
    cfg.DATASET_PATH = args.DATASET_PATH
    cfg.RESULTS_PATH = args.RESULTS_PATH
    cfg.EPOCHS = args.EPOCHS
    cfg.LEARNING_RATE = args.LEARNING_RATE
    cfg.DELTA_CLS_LOSS = 1.0
    cfg.BATCH_SIZE = args.BATCH_SIZE
    cfg.WEIGHTED_SEG_LOSS = args.WEIGHTED_SEG_LOSS
    cfg.WEIGHTED_SEG_LOSS_P = args.WEIGHTED_SEG_LOSS_P
    cfg.WEIGHTED_SEG_LOSS_MAX = args.WEIGHTED_SEG_LOSS_MAX
    cfg.DYN_BALANCED_LOSS = args.DYN_BALANCED_LOSS
    cfg.GRADIENT_ADJUSTMENT = args.GRADIENT_ADJUSTMENT
    cfg.FREQUENCY_SAMPLING = args.FREQUENCY_SAMPLING
    cfg.NUM_SEGMENTED = args.NUM_SEGMENTED
    cfg.FOLD = args.FOLD
    cfg.TRAIN_NUM = args.TRAIN_NUM
    cfg.DILATE = args.DILATE
    cfg.VALIDATE = args.VALIDATE
    cfg.VALIDATE_ON_TEST = args.VALIDATE_ON_TEST
    cfg.VALIDATION_N_EPOCHS = args.VALIDATION_N_EPOCHS
    cfg.SAVE_IMAGES = args.SAVE_IMAGES
    cfg.REPRODUCIBLE_RUN = args.REPRODUCIBLE_RUN
    cfg.MAX_TRAIN_SAMPLES = args.MAX_TRAIN_SAMPLES
    cfg.MAX_VAL_SAMPLES = args.MAX_VAL_SAMPLES
    cfg.INPUT_SIZE = args.INPUT_SIZE
    cfg.TRAIN_MODE = "JOINT"
    cfg.init_extra()
    return cfg


def parse_channels(value):
    channels = tuple(int(v.strip()) for v in value.split(",") if v.strip())
    if len(channels) != 3:
        raise ValueError("--EXTRACTOR_CHANNELS must contain exactly three comma-separated integers.")
    return channels


if __name__ == "__main__":
    args = parse_args()
    cfg = build_cfg(args)

    run_dir = os.path.join(args.RESULTS_PATH, args.DATASET, args.RUN_NAME)
    trainer = DistillationTrainer(
        cfg=cfg,
        teacher_ckpt=args.TEACHER_CKPT,
        run_dir=run_dir,
        weights=DistillWeights(
            seg_task=args.SEG_TASK_WEIGHT,
            cls_task=args.CLS_TASK_WEIGHT,
            seg_kd=args.SEG_KD_WEIGHT,
            cls_kd=args.CLS_KD_WEIGHT,
            volume_kd=args.VOLUME_KD_WEIGHT,
            relation_kd=args.RELATION_KD_WEIGHT,
        ),
        stage1_epochs=args.STAGE1_EPOCHS,
        optical_channels=args.OPTICAL_CHANNELS,
        optical_kernel_size=args.OPTICAL_KERNEL_SIZE,
        downsample_factor=args.DOWNSAMPLE_FACTOR,
        extractor_channels=parse_channels(args.EXTRACTOR_CHANNELS),
        seg_kd_temperature=args.SEG_KD_TEMPERATURE,
        seg_kd_foreground_weight=args.SEG_KD_FOREGROUND_WEIGHT,
    )
    trainer.train()
