#!/usr/bin/env bash

set -euo pipefail

GPU="${1:-0}"
FOLD="${2:-7}"
RUN_NAME="${3:-dagm_class${FOLD}_teacher_segonly}"
RESULTS_PATH="${4:-./results-dagm-teacher}"
DATASET_PATH="${5:-./datasets/DAGM}"
EPOCHS="${6:-70}"
VALIDATION_N_EPOCHS="${7:-10}"
MAX_TRAIN_SAMPLES="${8:-}"
MAX_VAL_SAMPLES="${9:-}"

EXTRA_ARGS=()
if [[ -n "${MAX_TRAIN_SAMPLES}" ]]; then
  EXTRA_ARGS+=(--MAX_TRAIN_SAMPLES="${MAX_TRAIN_SAMPLES}")
fi
if [[ -n "${MAX_VAL_SAMPLES}" ]]; then
  EXTRA_ARGS+=(--MAX_VAL_SAMPLES="${MAX_VAL_SAMPLES}")
fi

python3 -u train_net.py \
  --GPU="${GPU}" \
  --RUN_NAME="${RUN_NAME}" \
  --DATASET=DAGM \
  --DATASET_PATH="${DATASET_PATH}" \
  --RESULTS_PATH="${RESULTS_PATH}" \
  --FOLD="${FOLD}" \
  --NUM_SEGMENTED=1000 \
  --EPOCHS="${EPOCHS}" \
  --LEARNING_RATE=0.05 \
  --DELTA_CLS_LOSS=1 \
  --BATCH_SIZE=1 \
  --MEMORY_FIT=1 \
  --DILATE=1 \
  --VALIDATE=True \
  --VALIDATE_ON_TEST=True \
  --VALIDATION_N_EPOCHS="${VALIDATION_N_EPOCHS}" \
  --WEIGHTED_SEG_LOSS=True \
  --WEIGHTED_SEG_LOSS_P=1 \
  --WEIGHTED_SEG_LOSS_MAX=10 \
  --DYN_BALANCED_LOSS=True \
  --GRADIENT_ADJUSTMENT=True \
  --FREQUENCY_SAMPLING=True \
  --SAVE_IMAGES=False \
  --TRAIN_MODE=SEG_ONLY \
  "${EXTRA_ARGS[@]}"
