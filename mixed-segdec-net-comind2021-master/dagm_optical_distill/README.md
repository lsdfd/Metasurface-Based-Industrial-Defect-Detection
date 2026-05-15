# DAGM Class7 光学前端蒸馏实验入口

这个目录只保留当前成功路线所需脚本。早期 smoke、KSDD2、resolution sweep、旧 single/sweep 脚本已经从主线清理掉。

## 文件说明

```text
dagm_optical_distill/
  README.md
  FOCUSED_SWEEP_NOTES.md
  check_dagm_dataset.py
  train_teacher_dagm_class7.sh
  distill_focused_student_sweep.sh
  evaluate_student_visuals.py
  prepare_dagm_psf_targets.py
  summarize_distill_results.py
```

各文件作用：

- `FOCUSED_SWEEP_NOTES.md`：记录从失败探索到当前 best student 的过程和结论。
- `check_dagm_dataset.py`：检查 DAGM Class7 数据目录。
- `train_teacher_dagm_class7.sh`：训练 SegDecNet teacher。
- `distill_focused_student_sweep.sh`：复现当前最终推荐 student 配置。
- `evaluate_student_visuals.py`：评估 best checkpoint，并导出可视化和 threshold sweep。
- `prepare_dagm_psf_targets.py`：把 best optical kernels 拆成 positive/negative PSF targets，并导出超表面设计入口。
- `summarize_distill_results.py`：从多个 run 的日志中汇总指标。

## 为什么只保留这些脚本

清理原则是复现优先：

- `smoke_*` 只用于早期排错，现在不作为正式入口。
- `distill_dagm_class7_single.sh` 是旧默认配置，效果不如 focused sweep。
- `distill_dagm_class7_sweep.sh` 和 `distill_resolution_arch_sweep.sh` 是探索阶段脚本，结论已写入 `FOCUSED_SWEEP_NOTES.md`。
- `train_joint_teachers_by_resolution.sh` 属于后来放弃的 matching-resolution teacher 路线。
- 当前可复现主线只需要 teacher、best student reproduction、evaluation 三类脚本。

## 复现顺序

所有命令在 `mixed-segdec-net-comind2021-master/` 下运行。

1. 检查数据。

```bash
python3 dagm_optical_distill/check_dagm_dataset.py --dataset-path ./datasets/DAGM
```

2. 训练 teacher。

```bash
./dagm_optical_distill/train_teacher_dagm_class7.sh
```

3. 跑当前 best student 复现脚本。

```bash
./dagm_optical_distill/distill_focused_student_sweep.sh \
  0 \
  7 \
  ./results-dagm-distill-focused \
  ./results-dagm-teacher/DAGM/dagm_class7_teacher_segonly/FOLD_7/models/best_state_dict.pth \
  ./datasets/DAGM
```

4. 评估 best checkpoint。

```bash
python3 dagm_optical_distill/evaluate_student_visuals.py \
  --GPU 0 \
  --RUN_NAME dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70 \
  --DATASET_PATH ./datasets/DAGM \
  --RESULTS_PATH ./results-dagm-distill-focused \
  --CHECKPOINT ./results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/models/best_student.pth \
  --OUTPUT_DIR ./outputs/dagm_c7_best_visuals_pos \
  --FOLD 7 \
  --INPUT_SIZE 256 \
  --OPTICAL_CHANNELS 64 \
  --OPTICAL_KERNEL_SIZE 15 \
  --DOWNSAMPLE_FACTOR 4 \
  --EXTRACTOR_CHANNELS 12,24,32 \
  --SAVE_POS_ONLY true \
  --SAVE_LIMIT 32
```

5. 导出 optical kernels 的正负 PSF target。

这个步骤参考 fabric 目录里已经调过的正负卷积 / PSF target 流程。核心原因是 learned optical kernel 是有正有负的 signed convolution，但真实光强响应不能直接表达负权重，所以需要拆成两路：

```text
K = K_positive - K_negative
K_positive = max(K, 0)
K_negative = max(-K, 0)
```

命令示例：

```bash
python3 dagm_optical_distill/prepare_dagm_psf_targets.py \
  --KERNELS ./results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/models/best_optical_kernels.npy \
  --OUTPUT_DIR ./outputs/dagm_c7_best_psf_targets \
  --SCALE 2 \
  --SIM_SIZE 1600 \
  --NORMALIZE paired_max \
  --SAVE_FIGURES \
  --PREVIEW_KERNELS 64 \
  --KERNEL_INDEX 0
```

输出包括：

```text
dagm_psf_targets.npz
psf_config.json
kernel_stats.json
kernel_grid_signed.png
kernel_grid_positive.png
kernel_grid_negative.png
psf_backphase_preview.png
```

其中 `dagm_psf_targets.npz` 是后续接 `卷积核->超表面相位设计代码/` 的主要入口。

## 当前 best run

```text
dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70
```

结果：

```text
AP=1.00000
AUC=1.00000
IoU=0.83782
Dice=0.87685
```

上面是早期 capped `MAX_VAL_SAMPLES=600` 结果。后续对同一个 best checkpoint 跑了无 `MAX_VAL_SAMPLES` 的 full validation：

```text
num_samples=1150
AP=1.00000
AUC=1.00000
IoU=0.91451
Dice=0.93488
threshold=0.50
Precision=0.99575
Recall=0.91761
```

threshold sweep 的 best-IoU 和 best-Dice 点也都是 `0.50`，说明 full validation 结果不是靠调非默认阈值得到的。

路径：

```text
results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/
```

## 下一步必须补的验证

当前结果已经值得继续进入 PSF/超表面后处理，但还不是最终论文数值。下一步需要：

- separate TEST split 或原论文 protocol 对比；
- mixed panels，包括负样本和正样本；
- threshold sweep 指标作为附录记录；
- optical kernels 的正负 PSF 分解检查；
- 接 `卷积核->超表面相位设计代码/` 做 target PSF 到 simulated PSF / phase 的优化；
- 如果 simulated PSF 偏离 learned kernel，再做 hardware-aware retraining。
