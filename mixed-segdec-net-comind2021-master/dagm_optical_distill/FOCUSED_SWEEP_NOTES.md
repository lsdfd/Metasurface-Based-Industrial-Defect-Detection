# DAGM Class7 Optical Student Focused Sweep Notes

Last updated: 2026-05-15

## 中文总览：为什么这份记录要保留

脚本可以收敛到最后成功的可复现入口，但实验过程不能丢。论文写作时需要解释为什么选择当前 student 架构，为什么不用更大 optical bank，为什么不用更大 kernel，为什么从 `64 x 64` 退回到 `256 x 256`，以及当前结果是不是只靠偶然 checkpoint。

因此本文件保留：

- 最好 student 的完整架构。
- 失败和中间探索配置。
- 每组实验的关键指标。
- 当前理论参数量和计算量估算。
- 下一步后处理和验证路线。

当前可执行脚本只保留最终 best 配置；历史实验通过本文件记录。

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

- Full validation without `MAX_VAL_SAMPLES` reached `IoU=0.91451` and `Dice=0.93488` over `1150` samples.
- The threshold sweep selected the default `0.50` threshold as both the best-IoU and best-Dice point, so the full validation result is not a hand-picked non-default threshold artifact.
- Positive-only visualizations from the earlier `r256_o64_k15_d4_m300` run showed predicted heatmaps landing on the actual GT defect blobs, not arbitrary image regions.
- Fresh positive-only visualizations from the final best checkpoint also show heatmaps landing on the GT defect regions.
- Classification AP/AUC reached `1.0`, but segmentation IoU/Dice improved gradually and separately, so the metric is not just a classifier score being reused as a mask score.
- The best focused run ended at its best validation result, rather than showing one isolated lucky spike only.
- Multiple nearby configurations reached similar high Dice values around `0.86-0.88`, which suggests a reproducible architecture/loss effect rather than a single corrupted run.
- The validation set was enlarged from the earlier `300` sample cap to `600` samples, and the result improved rather than collapsing.

Reasons we should still be cautious:

- Full validation has now been run on the VAL split, but a separate held-out TEST split or original paper protocol comparison should still be reported before final paper claims.
- Some runs had large validation oscillations, so checkpoint selection matters.
- Threshold sensitivity is now recorded, but should still be included in the appendix rather than hidden.
- DAGM Class7 defects can be visually subtle and repetitive, so qualitative checks are important.

## Recommended Next Verification

Before presenting the result as final:

1. Run separate TEST split evaluation if we want paper-level final numbers.
2. Export additional mixed panels including negative samples, not only positive-only panels.
3. Include the threshold sweep from `evaluate_student_visuals.py` in the experiment appendix.
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

Full validation was then run for the same best checkpoint with no `MAX_VAL_SAMPLES` cap:

```text
num_samples=1150
AP=1.00000
AUC=1.00000
threshold=0.50
IoU=0.91451
Dice=0.93488
Precision=0.99575
Recall=0.91761
```

The threshold sweep also selected `0.50` as both the best-IoU and best-Dice threshold. This is useful because the full validation result is not relying on a hand-picked non-default segmentation threshold.

The result is strong enough to justify moving into optical-kernel / PSF post-processing. It should not yet be treated as the final paper-quality number until separate TEST split or original-protocol comparison is complete.

## Best Student Architecture, Detailed

Best run:

```text
dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70
```

Input:

```text
B x 1 x 256 x 256
```

Forward path:

```text
input grayscale image
  -> optical_frontend: Conv2d(1, 64, kernel=15, padding=7, bias=False)
  -> calibration: FeatureNorm(64) + ReLU
  -> downsample: AvgPool2d(kernel=4, stride=4)
  -> volume: B x 64 x 64 x 64
  -> seg_head: Conv2d(64, 1, kernel=1, bias=False) + FeatureNorm(1, no bias)
  -> seg_mask: B x 1 x 64 x 64
  -> concat(volume, seg_mask): B x 65 x 64 x 64
  -> extractor:
       MaxPool2d(2) -> B x 65 x 32 x 32
       Conv2d(65, 12, kernel=5, padding=2, bias=False) + FeatureNorm + ReLU
       MaxPool2d(2) -> B x 12 x 16 x 16
       Conv2d(12, 24, kernel=5, padding=2, bias=False) + FeatureNorm + ReLU
       MaxPool2d(2) -> B x 24 x 8 x 8
       Conv2d(24, 32, kernel=5, padding=2, bias=False) + FeatureNorm + ReLU
  -> global pooling:
       max(features): B x 32
       avg(features): B x 32
       max(seg_mask): B x 1
       avg(seg_mask): B x 1
  -> fc input: B x 66
  -> Linear(66, 1)
  -> image-level defect logit
```

Parameter breakdown:

| Part | Shape / module | Params |
|---|---|---:|
| Optical frontend | `Conv2d(1,64,15x15)` | 14,400 |
| Calibration | `FeatureNorm(64)` | 128 |
| Seg head | `Conv2d(64,1,1x1)` + scale | 65 |
| Extractor block 1 | `Conv2d(65,12,5x5)` + norm | 19,524 |
| Extractor block 2 | `Conv2d(12,24,5x5)` + norm | 7,248 |
| Extractor block 3 | `Conv2d(24,32,5x5)` + norm | 19,264 |
| FC | `Linear(66,1)` | 67 |
| Total | full student | 60,696 |

Important interpretation:

- The optical frontend has only `14,400` learned kernel weights.
- If mapped to optics, these become target optical PSF/convolution responses rather than electronic MACs.
- The remaining electronic backend has about `46,296` parameters.
- The optical kernels saved by the best run have shape `[64, 1, 15, 15]`.

## Architecture And Experiment Log

This section records tried settings even if their scripts were removed from the clean reproduction path.

| Stage | Setting | Main result | Interpretation |
|---|---|---|---|
| Teacher | Original SegDecNet SEG_ONLY teacher, DAGM Class7, original strong checkpoint | `AP ~= 1.0`, `AUC ~= 1.0`, `IoU ~= 0.966`, `Dice ~= 0.980` | Teacher is strong enough for distillation. |
| Early KSDD2 branch | KSDD2 segonly / distillation attempts | Not kept as main route | KSDD2 was not a clean fit for this optical-frontend thesis direction; route removed from active project. |
| Old optical student baseline | `INPUT_SIZE=512`, `OPTICAL_CHANNELS=64`, `KERNEL=7`, `DOWNSAMPLE=8`, stopped around epoch 37 | `AP/AUC ~= 1.0`, `Dice ~= 0.067`, `IoU ~= 0.046` | Classification learned, segmentation failed badly. Optical student was too weak at mask localization. |
| Aggressive low-res attempt | `INPUT_SIZE=64`, `OPTICAL_CHANNELS=32`, `KERNEL=11`, `DOWNSAMPLE=2` | unstable / NaN-prone behavior in stage 2 | Fabric low-res intuition did not transfer directly; SegDecNet/FeatureNorm path becomes too spatially small. |
| 128 smoke | `INPUT_SIZE=128`, `OPTICAL_CHANNELS=32`, `KERNEL=11`, `DOWNSAMPLE=4`, capped 80 samples, 12 epochs | reached `Dice ~= 0.5`, but AP/AUC low/random and masks looked suspicious | Promising but not reliable; may be degenerate or threshold-sensitive. |
| First useful 256 run | `INPUT_SIZE=256`, `OPTICAL_CHANNELS=64`, `KERNEL=15`, `DOWNSAMPLE=4`, `EXTRACTOR=12,24,32`, `MAX_TRAIN=300`, `MAX_VAL=300`, 35 epochs | `AP=1.0`, `AUC=1.0`, `IoU=0.612`, `Dice=0.691` | First strong sign that 256 resolution plus d4 mask works. Positive visualizations showed predicted heatmaps near GT defects, but masks were often too small. |
| Focused baseline | `r256_o64_k15_d4_e12-24-32_seg3_vol2_fg3_t2_m600_ep60` | best `IoU=0.83241`, `Dice=0.87148`; last `IoU=0.83020`, `Dice=0.86924` | Strong and stable; confirms 256/d4/o64/k15 is a good family. |
| Focused strong KD, best | `r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70` | best and last `IoU=0.83782`, `Dice=0.87685` | Current best. Stronger segmentation/volume KD improves mask coverage and ends at best epoch. |
| Larger optical bank | `r256_o96_k15_d4_e16-32-48_seg3_vol2_fg3_t2_m600_ep60` | best `IoU=0.83674`, `Dice=0.87562`; last `IoU=0.82921`, `Dice=0.86822` | Almost tied, but needs more optical channels and larger backend. Not worth the added hardware/electronic complexity. |
| Larger kernel | `r256_o64_k19_d4_e12-24-32_seg3_vol2_fg4_t2_m600_ep60` | best `IoU=0.82619`, `Dice=0.86493`; last `IoU=0.79549`, `Dice=0.83486` | Larger `19 x 19` optical kernel did not improve results and was less stable. |

Current architecture conclusion:

```text
INPUT_SIZE=256
OPTICAL_CHANNELS=64
OPTICAL_KERNEL_SIZE=15
DOWNSAMPLE_FACTOR=4
EXTRACTOR_CHANNELS=12,24,32
strong segmentation/volume distillation
```

This is the best tradeoff between performance and physical plausibility.

## Theoretical Parameter And Compute Estimate

The following is a first-order theoretical estimate for paper discussion. It counts convolution/linear MACs and parameters, not measured wall-clock latency. Real optical speed depends on sensor exposure, metasurface throughput, optical alignment, detector bandwidth, ADC, calibration, and electronic hardware.

Best student, all-digital proxy:

| Part | MACs |
|---|---:|
| Optical conv proxy, `256 x 256 x 1 -> 64`, `15 x 15` | 943.7M |
| Seg head | 0.26M |
| Extractor block 1 | 19.97M |
| Extractor block 2 | 1.84M |
| Extractor block 3 | 1.23M |
| FC | negligible |
| Total digital student proxy | 967.0M |
| Electronic part after optical frontend | 23.3M |

Teacher SegDecNet estimated MACs:

| Model/input | Params | MACs |
|---|---:|---:|
| Teacher at `256 x 256` | 15.63M | 21.08G |
| Teacher at `512 x 512` | 15.63M | 84.31G |
| Student all-digital proxy at `256 x 256` | 0.061M | 0.967G |
| Student electronic backend only after optical frontend | 0.046M electronic params | 0.023G |

Theoretical reductions:

- Student total parameters vs teacher: about `15.63M / 0.0607M = 258x` fewer parameters.
- If the optical conv is done by the metasurface, electronic student params are about `46.3K`, so teacher vs electronic backend parameters are about `338x` smaller.
- Digital student MACs vs teacher at `256 x 256`: about `21.08G / 0.967G = 21.8x` fewer MACs.
- Hybrid electronic backend MACs vs all-digital student: about `0.967G / 0.0233G = 41.5x` fewer electronic MACs.
- Hybrid electronic backend MACs vs teacher at `256 x 256`: about `21.08G / 0.0233G = 905x` fewer electronic MACs.
- Hybrid electronic backend MACs vs original teacher at `512 x 512`: about `84.31G / 0.0233G = 3618x` fewer electronic MACs.

How to phrase this carefully:

```text
The metasurface frontend does not remove the need for sensing, calibration, and a lightweight electronic backend. However, if the learned single-layer optical convolution bank is implemented optically, the remaining electronic computation drops from roughly 967M MACs in the digital student proxy to about 23M MACs, a 41.5x reduction in electronic MACs for the student. Relative to the SegDecNet teacher at 256 x 256, the remaining electronic backend is about 905x smaller in MAC count.
```

Do not claim measured speedup yet. This is a theoretical electronic-compute reduction.

## Post-processing And Next Work

The distillation result is strong, but the system is not finished. Next steps:

1. Full evaluation:
   Run `evaluate_student_visuals.py` without `MAX_VAL_SAMPLES` and record full validation/test metrics.

2. Fresh best-checkpoint visualization:
   Export positive-only and mixed panels for the final best checkpoint, not just earlier `m300` visuals.

3. Threshold analysis:
   Report fixed `0.5` threshold and best-threshold segmentation metrics. This matters because earlier masks tended to be slightly compact.

4. Teacher/student same-split comparison:
   Evaluate teacher and student on the exact same full split for fair paper tables.

5. Optical kernel inspection:
   Load `best_optical_kernels.npy`, visualize all 64 kernels, inspect value ranges, normalization, redundancy, and positive/negative mass.

6. Positive/negative PSF decomposition:
   Split each signed kernel into positive and negative components, because optical intensity cannot directly represent negative weights.

7. Metasurface target preparation:
   Convert normalized positive/negative kernels into target PSFs compatible with the PSF engineering notebook.

   Current implementation:

   ```text
   dagm_optical_distill/prepare_dagm_psf_targets.py
   ```

   This script follows the same practical convention used in the fabric branch:

   ```text
   K_positive = max(K, 0)
   K_negative = max(-K, 0)
   K = K_positive - K_negative
   ```

   The default normalization is `paired_max`, so each positive/negative pair shares one scale. This preserves the relative positive-vs-negative balance inside a signed kernel while making the target PSF values convenient for downstream optical simulation.

   Default PSF export settings:

   ```text
   SCALE=2
   SIM_SIZE=1600
   WAVELENGTH_NM=532
   GRID_PITCH_NM=586
   DETECTOR_DISTANCE_MM=2.4
   ```

   These are starting values inherited from the fabric/metasurface adaptation path, not final physical design claims. They should be revisited when the actual metasurface design constraints are fixed.

8. Optical simulation:
   Use angular-spectrum / PSF engineering code to optimize phase or scatterer geometry and compare target PSF vs simulated PSF.

9. Hardware-aware retraining:
   After simulated PSF mismatch is known, freeze or perturb the optical frontend and fine-tune calibration/electronic backend.

10. Paper table/figure preparation:
   Prepare architecture diagram, comparison table, qualitative visualizations, kernel grid, PSF target/simulation pairs, and compute-reduction table.
