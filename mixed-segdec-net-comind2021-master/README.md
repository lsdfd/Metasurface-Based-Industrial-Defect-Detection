# DAGM Class7 光学前端蒸馏版 SegDecNet

这个目录是当前项目主线。它基于原始 `mixed-segdec-net-comind2021` / SegDecNet 项目整理而来，但已经不再追求原论文的全数据集复现，而是聚焦一个明确目标：

```text
在 DAGM Class7 上，把 SegDecNet teacher 蒸馏成
“单层光学卷积前端 + 轻量电子后端”的光电混合 student。
```

## 为什么这样整理

早期我们尝试过 KSDD2 和一些 smoke/sweep 实验，但 KSDD2 路线效果不好，也不够适合当前“超表面光学前端”的叙事。继续保留这些入口会让后面的人分不清主线。

因此本目录按下面原则清理：

- KSDD2 失败路线从主入口中删除。
- 历史 smoke、旧 sweep、临时脚本不再作为复现入口。
- 只保留最后成功的 DAGM focused sweep。
- 训练结果和 checkpoint 留在本地/服务器，不提交到 GitHub。
- 文档负责记录失败路线的结论，而不是保留一堆难以解释的脚本。

清理后的主线非常明确：

```text
DAGM Class7 -> SegDecNet teacher -> OpticalSegDecStudent -> focused sweep -> best optical kernels
```

## 研究目标

本项目不是把整个神经网络搬到光学域，而是把最早期、计算量大的特征编码前移到成像链路中完成。

模型分工：

- 光学前端：单层 `Conv2d` kernel bank，作为 metasurface PSF encoder 的数字代理。
- 校准层：`FeatureNorm + ReLU`，模拟光学输出进入电子系统前的简单校准。
- 分割头：`1x1 seg_head`，输出缺陷 soft mask。
- 电子后端：轻量 `extractor + fc`，保留 SegDecNet 的 segmentation/classification 骨架。
- 蒸馏目标：从强 SegDecNet teacher 学 segmentation、classification 和 volume-like representation。

当前最好的 student 仍然只有一层 optical conv，没有堆叠多层“假光学 CNN”。

## 当前目录结构

```text
mixed-segdec-net-comind2021-master/
├── README.md
├── config.py
├── train_net.py
├── models.py
├── end2end.py
├── evaluation.py
├── utils.py
├── data/
├── datasets/
├── splits/
├── distill/
└── dagm_optical_distill/
```

核心文件：

- `models.py`：原 SegDecNet teacher 架构。
- `train_net.py`：原 teacher 训练入口。
- `data/input_dagm.py`：DAGM 数据加载。
- `distill/models.py`：`OpticalSegDecStudent` 学生模型。
- `distill/losses.py`：task loss、seg KD、volume KD、relation KD。
- `distill/trainer.py`：teacher-student 两阶段蒸馏训练。
- `distill/train_distill.py`：蒸馏训练 CLI。
- `dagm_optical_distill/distill_focused_student_sweep.sh`：当前主复现脚本。
- `dagm_optical_distill/evaluate_student_visuals.py`：评估、可视化、threshold sweep。
- `dagm_optical_distill/FOCUSED_SWEEP_NOTES.md`：实验探索完整记录。

## 数据准备

数据集使用 DAGM 2007 Optical Inspection：

```text
https://www.kaggle.com/datasets/mhskjelvareid/dagm-2007-competition-dataset-optical-inspection
```

当前只需要 Class7：

```text
datasets/DAGM/
  Class7/
    Train/
    Test/
```

检查数据：

```bash
python3 dagm_optical_distill/check_dagm_dataset.py --dataset-path ./datasets/DAGM
```

注意：脚本参数是小写 `--dataset-path`，不是 `--DATASET_PATH`。

## 复现步骤

以下命令默认在 `mixed-segdec-net-comind2021-master/` 下运行。

1. 训练 teacher。

```bash
./dagm_optical_distill/train_teacher_dagm_class7.sh
```

teacher 默认输出：

```text
results-dagm-teacher/DAGM/dagm_class7_teacher_segonly/FOLD_7/
```

已有服务器 teacher checkpoint：

```text
results-dagm-teacher/DAGM/dagm_class7_teacher_segonly/FOLD_7/models/best_state_dict.pth
```

2. 运行当前推荐 student 复现脚本。

```bash
./dagm_optical_distill/distill_focused_student_sweep.sh \
  0 \
  7 \
  ./results-dagm-distill-focused \
  ./results-dagm-teacher/DAGM/dagm_class7_teacher_segonly/FOLD_7/models/best_state_dict.pth \
  ./datasets/DAGM
```

这个脚本只跑当前最终推荐配置。历史上我们比较过 `o64/k15`、更强 seg/volume KD、`o96/k15`、`o64/k19`，结论已经写入 `dagm_optical_distill/FOCUSED_SWEEP_NOTES.md`，不再通过复现脚本重复探索。

3. 评估最佳 checkpoint 并导出可视化。

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

评估脚本会输出：

- classification AP/AUC；
- segmentation IoU/Dice/precision/recall；
- threshold sweep；
- `input | GT mask | pred heatmap | overlay` 可视化 panel。

## 当前最佳配置

推荐 run：

```text
dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70
```

配置：

```text
INPUT_SIZE=256
OPTICAL_CHANNELS=64
OPTICAL_KERNEL_SIZE=15
DOWNSAMPLE_FACTOR=4
EXTRACTOR_CHANNELS=12,24,32
STAGE1_EPOCHS=12
EPOCHS=70
SEG_TASK_WEIGHT=1.0
SEG_KD_WEIGHT=5.0
VOLUME_KD_WEIGHT=3.0
SEG_KD_FOREGROUND_WEIGHT=5.0
SEG_KD_TEMPERATURE=2.0
CLS_TASK_WEIGHT=0.10
CLS_KD_WEIGHT=0.30
RELATION_KD_WEIGHT=0.05
MAX_TRAIN_SAMPLES=600
MAX_VAL_SAMPLES=600
```

记录指标：

```text
AP=1.00000
AUC=1.00000
IoU=0.83782
Dice=0.87685
```

这些指标来自 capped `600` 验证样本，不是 full validation/test。

## 为什么当前结果不像假指标

当前判断是：大概率不是假指标，但还没到最终结论。

支持理由：

- 正样本可视化显示预测热区落在 GT 缺陷附近，不是随机高亮。
- 分类 AP/AUC 很早学稳，但 segmentation IoU/Dice 是单独逐步提升的，不是把分类分数误当 mask 指标。
- 多个相近配置都达到 `Dice 0.86-0.88`，不是单个 run 的偶然尖峰。
- 最优 run 最后一轮就是 best，训练没有只靠中途偶然 checkpoint。
- 验证样本从早期 `300` 扩到 `600` 后没有崩。

仍需谨慎：

- 还没跑 full validation/test。
- 有些 run 存在指标波动。
- 当前主表使用 fixed threshold `0.5`，还需要记录 threshold sweep。
- 最终 best checkpoint 的 fresh visualization 还要补。

## 当前最好 checkpoint

服务器路径：

```text
/root/fabric_run/mixed-segdec-net-comind2021-master/results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/models/best_student.pth
```

对应 optical kernels：

```text
/root/fabric_run/mixed-segdec-net-comind2021-master/results-dagm-distill-focused/DAGM/dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70/models/best_optical_kernels.npy
```

kernel shape：

```text
[64, 1, 15, 15]
```

这些 kernels 是后续超表面 PSF 设计的入口。

## Git 与结果文件约定

GitHub 提交代码和文档，不提交数据和 checkpoint。

本地/服务器保留：

- `datasets/DAGM/`
- `results-dagm-teacher/`
- `results-dagm-distill-focused/`
- `outputs/`

GitHub 忽略：

- `datasets/DAGM/`
- `results*/`
- `outputs/`
- `*.pth`
- `*.pt`
- `*.npy`

## 后续工作

建议下一步：

1. 用 best checkpoint 跑 full validation/test。
2. 导出 final best checkpoint 的 positive-only 和 mixed visual panels。
3. 把 fixed threshold 与 best threshold 指标写入 `FOCUSED_SWEEP_NOTES.md`。
4. 和 teacher 在同一 full split 上做对比。
5. 导出 kernels，做 positive/negative split。
6. 接 `kernel-to-metasurface-phase-design/`，开始 PSF/phase optimization。

## 原始项目来源

本目录基于：

```text
Mixed supervision for surface-defect detection:
from weakly to fully supervised learning
Computers in Industry 2021
```

原始 SegDecNet 代码和论文应按其 license/citation 要求引用。本项目在其基础上新增了 DAGM Class7 optical frontend distillation 路线。
