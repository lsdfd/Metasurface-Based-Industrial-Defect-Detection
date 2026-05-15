# DAGM Class7 光学前端蒸馏版 SegDecNet

本目录基于 `mixed-segdec-net-comind2021` 原始 SegDecNet 项目整理而来，但当前主线已经收敛为：

```text
DAGM Class7 缺陷检测
SegDecNet teacher
单层 optical convolution bank student
光电混合 segmentation + classification
```

早期 KSDD2 探索路线已经清理掉。本项目现在优先保证 DAGM Class7 光学前端蒸馏流程清晰、可复现、方便后续接超表面 PSF/相位设计。

## 研究目标

目标不是做一个完整全光学检测器，而是一个光电混合缺陷检测模型：

- 光学前端：单层 metasurface-like convolution/PSF bank；
- 电子后端：轻量 calibration、segmentation head、extractor 和 classifier；
- 训练方式：从强 SegDecNet teacher 做任务蒸馏；
- 后续硬件映射：导出 optical kernels，再做正负 PSF 分解和超表面相位设计。

当前最优学生模型仍然保持单层 optical conv，不堆叠“假光学 CNN”。

## 当前最佳结果

当前推荐使用 DAGM Class7 focused sweep 中的最佳学生：

```text
RUN_NAME=dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70
```

核心配置：

```text
INPUT_SIZE=256
OPTICAL_CHANNELS=64
OPTICAL_KERNEL_SIZE=15
DOWNSAMPLE_FACTOR=4
EXTRACTOR_CHANNELS=12,24,32
SEG_KD_WEIGHT=5.0
VOLUME_KD_WEIGHT=3.0
SEG_KD_FOREGROUND_WEIGHT=5.0
SEG_KD_TEMPERATURE=2.0
```

在 capped `600` 验证样本设置下，当前记录指标为：

```text
AP=1.00000
AUC=1.00000
IoU=0.83782
Dice=0.87685
```

注意：这还不是最终论文级数字。下一步仍需 full validation/test、最终 best checkpoint 可视化和 threshold sweep。

详细探索记录见：

```text
dagm_optical_distill/FOCUSED_SWEEP_NOTES.md
```

## 目录结构

```text
.
├── config.py                    # 原 SegDecNet 配置，已增加 INPUT_SIZE / sample cap 等实验字段
├── train_net.py                 # 原 SegDecNet teacher 训练入口
├── models.py                    # 原 SegDecNet teacher 架构
├── end2end.py                   # 原训练/评估流程
├── evaluation.py
├── utils.py
├── data/                        # 数据加载代码，当前主线使用 input_dagm.py
├── datasets/
│   ├── README.md
│   └── DAGM/                    # DAGM 数据集放置位置
├── splits/
│   ├── DAGM/                    # DAGM split 文件
│   └── STEEL/                   # 历史兼容 split，当前主线不使用
├── distill/                     # 通用蒸馏模块
│   ├── models.py                # OpticalSegDecStudent
│   ├── losses.py                # task/KD/feature/relation losses
│   ├── trainer.py               # teacher-student 两阶段训练
│   └── train_distill.py         # 蒸馏训练 CLI
└── dagm_optical_distill/        # DAGM Class7 实验入口和记录
    ├── README.md
    ├── FOCUSED_SWEEP_NOTES.md
    ├── check_dagm_dataset.py
    ├── train_teacher_dagm_class7.sh
    ├── distill_focused_student_sweep.sh
    ├── evaluate_student_visuals.py
    └── summarize_distill_results.py
```

训练结果、checkpoint、可视化图建议放在 `results-*` 或 `outputs/` 目录下，不建议提交到 GitHub。服务器上已有的成功实验结果应保留。

## 数据准备

使用 DAGM 2007 数据集：

```text
https://www.kaggle.com/datasets/mhskjelvareid/dagm-2007-competition-dataset-optical-inspection
```

当前主线只需要 Class7。期望目录大致如下：

```text
datasets/DAGM/
  Class7/
    Train/
    Test/
```

完整说明见：

```text
datasets/README.md
```

## 复现步骤

以下命令默认在项目根目录运行。

1. 检查 DAGM Class7 数据是否存在：

```bash
python3 dagm_optical_distill/check_dagm_dataset.py --DATASET_PATH ./datasets/DAGM
```

2. 训练或复现 teacher：

```bash
./dagm_optical_distill/train_teacher_dagm_class7.sh
```

推荐 teacher checkpoint 路径：

```text
results-dagm-teacher/DAGM/dagm_class7_teacher_segonly/FOLD_7/models/best_state_dict.pth
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

4. 评估并导出可视化：

```bash
python3 dagm_optical_distill/evaluate_student_visuals.py \
  --GPU 0 \
  --RUN_NAME dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70 \
  --DATASET_PATH ./datasets/DAGM \
  --RESULTS_PATH ./results-dagm-distill-focused \
  --CHECKPOINT ./results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/models/best_student.pth \
  --OUTPUT_DIR ./outputs/dagm_c7_best_visuals \
  --FOLD 7 \
  --INPUT_SIZE 256 \
  --OPTICAL_CHANNELS 64 \
  --OPTICAL_KERNEL_SIZE 15 \
  --DOWNSAMPLE_FACTOR 4 \
  --EXTRACTOR_CHANNELS 12,24,32 \
  --SAVE_POS_ONLY true \
  --SAVE_LIMIT 32
```

`evaluate_student_visuals.py` 会保存：

- mixed/positive visual panels；
- classification metrics；
- segmentation metrics；
- segmentation threshold sweep。

## 当前最佳 checkpoint

服务器上当前应优先使用：

```text
results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/models/best_student.pth
```

对应 optical kernels：

```text
results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/models/best_optical_kernels.npy
```

这些 kernels 的 shape 为：

```text
[64, 1, 15, 15]
```

后续进入超表面设计时，应从这里开始做 positive/negative PSF 分解、归一化、物理约束模拟和相位优化。

## 清理后的项目边界

当前仓库不再维护 KSDD2 失败探索路线，也不再保留原项目全数据集论文复现实验脚本。`data/` 和 `config.py` 中仍保留部分历史数据集兼容代码，主要是为了不破坏原始 SegDecNet import 结构；当前 README 和脚本只保证 DAGM Class7 主线。

如果以后要重新扩展到其他工业数据集，建议单独建 `experiments/<dataset_name>/`，不要把新路线混回 DAGM 主线目录。

## 后续计划

建议下一步按顺序做：

1. 对最佳学生 checkpoint 跑 full validation/test。
2. 导出最终 positive-only 和 mixed visual panels。
3. 记录 fixed threshold 和 best threshold segmentation 指标。
4. 与 teacher 在同一 full split 上对比。
5. 导出 optical kernels，进入 PSF 正负分解和超表面相位设计。

## 原始项目来源

本代码基于以下工作：

```text
Mixed supervision for surface-defect detection:
from weakly to fully supervised learning
Computers in Industry 2021
```

原始论文和代码请按其 license/citation 要求引用。本项目在其基础上增加了 DAGM Class7 optical frontend distillation 路线。
