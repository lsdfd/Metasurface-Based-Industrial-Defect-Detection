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
  summarize_distill_results.py
```

各文件作用：

- `FOCUSED_SWEEP_NOTES.md`：记录从失败探索到当前 best student 的过程和结论。
- `check_dagm_dataset.py`：检查 DAGM Class7 数据目录。
- `train_teacher_dagm_class7.sh`：训练 SegDecNet teacher。
- `distill_focused_student_sweep.sh`：复现当前最终推荐 student 配置。
- `evaluate_student_visuals.py`：评估 best checkpoint，并导出可视化和 threshold sweep。
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

路径：

```text
results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/
```

## 下一步必须补的验证

当前结果已经值得继续，但还不是最终数值。下一步需要：

- full validation/test；
- final best checkpoint 可视化；
- threshold sweep 指标；
- teacher/student 同 split 对比；
- optical kernels 的正负 PSF 分解检查。
