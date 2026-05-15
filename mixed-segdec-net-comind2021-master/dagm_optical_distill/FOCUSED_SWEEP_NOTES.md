# DAGM Class7 Optical Student Focused Sweep Notes

Last updated: 2026-05-15

This note records the practical exploration around distilling a SegDecNet teacher into a physically plausible optical-electronic student on DAGM Class7. It is intended to help future readers understand why the current student design was chosen, what was tried, and what still needs verification.

## Research Goal

The target model is not an all-optical defect detector. The intended system is a hybrid optical-electronic defect detector:

- Optical frontend: one single-layer metasurface-like convolution/PSF bank.
- Electronic backend: lightweight calibration, segmentation head, feature extractor, and classifier.
- Training: knowledge distillation from a strong SegDecNet teacher.

The optical frontend should remain simple enough to map to a metasurface later. Therefore, this branch avoids stacking multiple fake optical CNN layers.

## Dataset And Teacher

- Dataset: DAGM 2007, Class7.
- Input modality: grayscale.
- Original image size: `512 x 512`.
- Current student input size: `256 x 256`.
- Student segmentation output resolution: `64 x 64` via `DOWNSAMPLE_FACTOR=4`.
- Teacher checkpoint:

```text
results-dagm-teacher/DAGM/dagm_class7_teacher_segonly/FOLD_7/models/best_state_dict.pth
```

The teacher is the reliable SEG_ONLY teacher trained earlier. It reached approximately:

```text
AP ~= 1.0
AUC ~= 1.0
IoU ~= 0.966
Dice ~= 0.980
```

## Why We Moved To 256 x 256

The fabric project showed that aggressive low-resolution inputs can improve optical student behavior. We tried to transfer that idea to DAGM, but direct `64 x 64` was too aggressive for the current SegDecNet-style pipeline: the teacher/FeatureNorm path became unstable and produced poor or NaN-prone behavior.

The useful compromise was:

```text
INPUT_SIZE=256
DOWNSAMPLE_FACTOR=4
student mask size = 64 x 64
```

This keeps a compact image size while preserving enough spatial structure for segmentation.

## Student Architecture

The focused sweep keeps this skeleton fixed:

```text
input grayscale image
  -> single optical conv bank
  -> FeatureNorm + ReLU calibration
  -> AvgPool2d downsample
  -> 1x1 seg_head
  -> concat(volume, seg_mask)
  -> small electronic extractor
  -> global max/avg pooling over features and seg mask
  -> linear classifier
```

The current best family uses:

```text
INPUT_SIZE=256
OPTICAL_CHANNELS=64
OPTICAL_KERNEL_SIZE=15
DOWNSAMPLE_FACTOR=4
EXTRACTOR_CHANNELS=12,24,32
```

The optical frontend is still a single convolution layer:

```text
Conv2d(in_channels=1, out_channels=64, kernel_size=15, padding=7, bias=False)
```

So the optical kernel tensor shape is:

```text
[64, 1, 15, 15]
```

This has `64 * 1 * 15 * 15 = 14,400` optical weights before future positive/negative PSF splitting and physical constraints.

## Training Design

The focused sweep uses two-stage distillation:

- Stage 1: train optical frontend, segmentation head, and volume/segmentation alignment while freezing the electronic extractor/fc.
- Stage 2: train the full student with task loss and distillation loss.

The best run used stronger segmentation-oriented distillation:

```text
SEG_TASK_WEIGHT=1.0
SEG_KD_WEIGHT=5.0
VOLUME_KD_WEIGHT=3.0
SEG_KD_FOREGROUND_WEIGHT=5.0
SEG_KD_TEMPERATURE=2.0
CLS_TASK_WEIGHT=0.10
CLS_KD_WEIGHT=0.30
RELATION_KD_WEIGHT=0.05
STAGE1_EPOCHS=12
EPOCHS=70
MAX_TRAIN_SAMPLES=600
MAX_VAL_SAMPLES=600
```

The stronger segmentation/volume distillation helped the student cover defect masks better, while classification remained easy.

## Focused Sweep Results

All focused runs used:

```text
INPUT_SIZE=256
DOWNSAMPLE_FACTOR=4
MAX_TRAIN_SAMPLES=600
MAX_VAL_SAMPLES=600
teacher = results-dagm-teacher/DAGM/dagm_class7_teacher_segonly/FOLD_7/models/best_state_dict.pth
```

| Rank | Run | Key Change | Best IoU | Best Dice | Last IoU | Last Dice | Note |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | `dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70` | stronger seg/volume KD | 0.83782 | 0.87685 | 0.83782 | 0.87685 | Best and most stable; final epoch equals best. |
| 2 | `dagm_c7_r256_o96_k15_d4_e16-32-48_seg3_vol2_fg3_t2_m600_ep60` | larger optical bank and backend | 0.83674 | 0.87562 | 0.82921 | 0.86822 | Nearly tied, but more optical/electronic capacity with little gain. |
| 3 | `dagm_c7_r256_o64_k15_d4_e12-24-32_seg3_vol2_fg3_t2_m600_ep60` | baseline focused setting | 0.83241 | 0.87148 | 0.83020 | 0.86924 | Strong baseline; stable near the end. |
| 4 | `dagm_c7_r256_o64_k19_d4_e12-24-32_seg3_vol2_fg4_t2_m600_ep60` | larger optical kernel | 0.82619 | 0.86493 | 0.79549 | 0.83486 | Larger `19x19` kernel did not help. |

Main conclusion from this sweep:

```text
64 optical channels + 15x15 optical kernels + d4 mask resolution + stronger seg/volume KD
```

is currently the best practical direction.

Increasing optical bank capacity from `64` to `96` did not clearly improve accuracy, and increasing kernel size from `15` to `19` was worse. This is useful for the metasurface story because it supports a smaller, cleaner optical frontend.

## Is This A Fake Metric?

Current judgment: probably not fake, but still not final-proof.

Reasons it is unlikely to be purely fake:

- Positive-only visualizations from the earlier `r256_o64_k15_d4_m300` run showed predicted heatmaps landing on the actual GT defect blobs, not arbitrary image regions.
- Classification AP/AUC reached `1.0`, but segmentation IoU/Dice improved gradually and separately, so the metric is not just a classifier score being reused as a mask score.
- The best focused run ended at its best validation result, rather than showing one isolated lucky spike only.
- Multiple nearby configurations reached similar high Dice values around `0.86-0.88`, which suggests a reproducible architecture/loss effect rather than a single corrupted run.
- The validation set was enlarged from the earlier `300` sample cap to `600` samples, and the result improved rather than collapsing.

Reasons we should still be cautious:

- The focused sweep still used `MAX_VAL_SAMPLES=600`, not the full validation/test set.
- Some runs had large validation oscillations, so checkpoint selection matters.
- The reported segmentation metric uses a fixed default threshold of `0.5`; threshold sensitivity should be recorded.
- We need fresh visualizations for the final best checkpoint, not only the earlier `m300` checkpoint.
- DAGM Class7 defects can be visually subtle and repetitive, so qualitative checks are important.

## Recommended Next Verification

Before presenting the result as final:

1. Run full validation/test evaluation for the best checkpoint without `MAX_VAL_SAMPLES`.
2. Export positive-only and mixed visual panels for the best checkpoint.
3. Use the threshold sweep in `evaluate_student_visuals.py` to report both fixed-threshold and best-threshold segmentation metrics.
4. Compare the best student against the teacher on the same full evaluation split.
5. Save the best optical kernels:

```text
models/best_optical_kernels.npy
```

and inspect their shape/statistics before PSF positive/negative decomposition.

## Best Checkpoint To Use Next

Use this run first:

```text
results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/models/best_student.pth
```

Its corresponding optical kernels:

```text
results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/models/best_optical_kernels.npy
```

## Current Working Conclusion

The best current DAGM optical student is a compact and physically plausible hybrid model:

- single-layer grayscale optical convolution bank;
- `64` channels;
- `15 x 15` kernels;
- `256 x 256` input;
- `64 x 64` segmentation map;
- lightweight electronic SegDecNet-style backend;
- strong segmentation and volume distillation.

This achieves approximately:

```text
AP=1.0
AUC=1.0
IoU=0.838
Dice=0.877
```

on the capped `600`-sample validation setting.

The result is strong enough to justify deeper validation and visualization. It should not yet be treated as the final paper-quality number until full evaluation and final checkpoint visual inspection are complete.
