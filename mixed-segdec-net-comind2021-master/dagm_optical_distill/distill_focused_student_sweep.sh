#!/usr/bin/env bash

set -euo pipefail

GPU="${1:-0}"
FOLD="${2:-7}"
RESULTS_PATH="${3:-./results-dagm-distill-focused}"
TEACHER_CKPT="${4:-./results-dagm-teacher/DAGM/dagm_class${FOLD}_teacher_segonly/FOLD_${FOLD}/models/best_state_dict.pth}"
DATASET_PATH="${5:-./datasets/DAGM}"

run_one() {
  local run_name="$1"
  local epochs="$2"
  local stage1_epochs="$3"
  local input_size="$4"
  local optical_channels="$5"
  local kernel_size="$6"
  local downsample_factor="$7"
  local extractor_channels="$8"
  local max_train="$9"
  local max_val="${10}"
  local seg_task_weight="${11}"
  local seg_kd_weight="${12}"
  local volume_kd_weight="${13}"
  local foreground_weight="${14}"
  local temperature="${15}"
  local cls_task_weight="${16}"
  local cls_kd_weight="${17}"
  local relation_kd_weight="${18}"

  local out_dir="${RESULTS_PATH}/DAGM/${run_name}"
  mkdir -p "${out_dir}"

  if [[ ! -f "${TEACHER_CKPT}" ]]; then
    echo "[Focused Sweep] Missing teacher checkpoint: ${TEACHER_CKPT}" | tee "${out_dir}/train.log"
    return 1
  fi

  echo "[Focused Sweep] Starting ${run_name}"
  python3 -u -m distill.train_distill \
    --GPU="${GPU}" \
    --RUN_NAME="${run_name}" \
    --DATASET=DAGM \
    --DATASET_PATH="${DATASET_PATH}" \
    --RESULTS_PATH="${RESULTS_PATH}" \
    --TEACHER_CKPT="${TEACHER_CKPT}" \
    --FOLD="${FOLD}" \
    --NUM_SEGMENTED=1000 \
    --EPOCHS="${epochs}" \
    --LEARNING_RATE=0.001 \
    --BATCH_SIZE=4 \
    --DILATE=1 \
    --VALIDATE=True \
    --VALIDATE_ON_TEST=True \
    --VALIDATION_N_EPOCHS=2 \
    --WEIGHTED_SEG_LOSS=True \
    --WEIGHTED_SEG_LOSS_P=1 \
    --WEIGHTED_SEG_LOSS_MAX=10 \
    --DYN_BALANCED_LOSS=True \
    --GRADIENT_ADJUSTMENT=True \
    --FREQUENCY_SAMPLING=True \
    --REPRODUCIBLE_RUN=True \
    --MAX_TRAIN_SAMPLES="${max_train}" \
    --MAX_VAL_SAMPLES="${max_val}" \
    --INPUT_SIZE="${input_size}" \
    --STAGE1_EPOCHS="${stage1_epochs}" \
    --OPTICAL_CHANNELS="${optical_channels}" \
    --OPTICAL_KERNEL_SIZE="${kernel_size}" \
    --DOWNSAMPLE_FACTOR="${downsample_factor}" \
    --EXTRACTOR_CHANNELS="${extractor_channels}" \
    --SEG_TASK_WEIGHT="${seg_task_weight}" \
    --SEG_KD_WEIGHT="${seg_kd_weight}" \
    --CLS_TASK_WEIGHT="${cls_task_weight}" \
    --CLS_KD_WEIGHT="${cls_kd_weight}" \
    --VOLUME_KD_WEIGHT="${volume_kd_weight}" \
    --RELATION_KD_WEIGHT="${relation_kd_weight}" \
    --SEG_KD_FOREGROUND_WEIGHT="${foreground_weight}" \
    --SEG_KD_TEMPERATURE="${temperature}" \
    2>&1 | tee "${out_dir}/train.log"

  echo "[Focused Sweep] Finished ${run_name}"
}

# Reproduce the current best student. Historical architecture/loss exploration is
# documented in FOCUSED_SWEEP_NOTES.md; the active script keeps only the final
# recommended setting.
run_one "dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70" 70 12 256 64 15 4 "12,24,32" 600 600 1.0 5.0 3.0 5.0 2.0 0.10 0.3 0.05
