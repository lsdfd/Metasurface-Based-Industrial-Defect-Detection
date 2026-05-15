# DAGM Class7 光学前端蒸馏实验

这个目录是当前项目的主实验入口。它只服务 DAGM Class7 上的 SegDecNet teacher 到 optical student 蒸馏路线。

## 为什么选 DAGM Class7

- DAGM 是光学检测场景，和 metasurface optical frontend 的研究叙事更贴合。
- Class7 是原 SegDecNet 项目中表现较好的 demo class。
- 图像是灰度图，适合先做单波长/单通道 optical kernel bank。
- 原图为 `512 x 512`，当前最佳 student 使用 `256 x 256` 输入和 `64 x 64` mask。

## 当前文件

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

说明：

- `FOCUSED_SWEEP_NOTES.md`：完整记录架构探索、指标、风险和结论。
- `check_dagm_dataset.py`：检查 DAGM 数据是否放对。
- `train_teacher_dagm_class7.sh`：训练 SegDecNet teacher。
- `distill_focused_student_sweep.sh`：当前推荐的 focused student sweep。
- `evaluate_student_visuals.py`：评估 student、导出可视化、保存 threshold sweep。
- `summarize_distill_results.py`：汇总多个 distillation run 的日志。

## 数据集位置

期望：

```text
datasets/DAGM/
  Class7/
    Train/
    Test/
```

如果保留完整 DAGM，也可以有 `Class1` 到 `Class10`，但当前脚本只使用 `FOLD=7`。

## 推荐复现流程

1. 检查数据：

```bash
python3 dagm_optical_distill/check_dagm_dataset.py --DATASET_PATH ./datasets/DAGM
```

2. 训练 teacher：

```bash
./dagm_optical_distill/train_teacher_dagm_class7.sh
```

teacher 默认输出到：

```text
results-dagm-teacher/DAGM/dagm_class7_teacher_segonly/FOLD_7/
```

3. 运行 focused student sweep：

```bash
./dagm_optical_distill/distill_focused_student_sweep.sh \
  0 \
  7 \
  ./results-dagm-distill-focused \
  ./results-dagm-teacher/DAGM/dagm_class7_teacher_segonly/FOLD_7/models/best_state_dict.pth \
  ./datasets/DAGM
```

4. 评估最佳模型并导出正样本图：

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

## 当前推荐配置

```text
INPUT_SIZE=256
OPTICAL_CHANNELS=64
OPTICAL_KERNEL_SIZE=15
DOWNSAMPLE_FACTOR=4
EXTRACTOR_CHANNELS=12,24,32
STAGE1_EPOCHS=12
EPOCHS=70
SEG_KD_WEIGHT=5.0
VOLUME_KD_WEIGHT=3.0
SEG_KD_FOREGROUND_WEIGHT=5.0
SEG_KD_TEMPERATURE=2.0
```

当前 capped `600` 验证样本结果：

```text
AP=1.00000
AUC=1.00000
IoU=0.83782
Dice=0.87685
```

## 重要提醒

这个结果大概率不是假指标，但还不是最终结论。原因和风险已经写在：

```text
dagm_optical_distill/FOCUSED_SWEEP_NOTES.md
```

下一步必须补：

- full validation/test；
- final best checkpoint 可视化；
- threshold sweep 结果记录；
- teacher/student 同 split 对比。
