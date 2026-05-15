# DAGM Class7 光电混合缺陷检测论文资产说明

更新时间：2026-05-15

这个目录用于同步服务器、本地和 GitHub 上的关键结果资产，面向论文配图、PPT 答辩和后续复现实验。这里保留的是“最终可复现/可展示”资产，不保留 teacher 训练过程中的每 5 epoch 中间权重。

## 目录结构

```text
paper_assets/
  README.md
  ASSET_MANIFEST.csv
  checkpoints/
    teacher/
    best_student/
  results/
    dagm_c7_best_full_eval_pos/
    dagm_c7_best_psf_targets/
    dagm_c7_metasurface_probe_i40/
  figures/
  tables/
```

## 权重文件

```text
checkpoints/teacher/dagm_class7_teacher_best_state_dict.pth
checkpoints/best_student/best_student.pth
checkpoints/best_student/final_student.pth
checkpoints/best_student/best_optical_kernels.npy
checkpoints/best_student/final_optical_kernels.npy
```

说明：

- teacher best 权重约 `60 MB`，用于复现教师 SegDecNet。
- best student 权重约 `244 KB`，对应当前主结果。
- best optical kernels 是后续 PSF/超表面设计的入口，shape 为 `[64, 1, 15, 15]`。
- 未保存 teacher 的中间 epoch checkpoint，因为总量约 `895 MB`，论文和复现主线不需要。

`tables/checkpoint_inventory.csv` 记录了这些权重的大小和 SHA256。

## 指标表

主要表格：

```text
tables/student_full_validation_metrics.csv
tables/compute_savings_summary.csv
tables/compute_reduction_ratios.csv
tables/metasurface_probe_i40_summary.csv
```

当前 best student 在 DAGM Class7 full validation 上：

```text
samples=1150
AP=1.00000
AUC=1.00000
IoU=0.91451
Dice=0.93488
Precision=0.99575
Recall=0.91761
threshold=0.50
```

结论：

- 分类 AP/AUC 已经满分。
- 分割 IoU/Dice 很高，且 threshold sweep 的最佳点仍是默认 `0.50`，不是靠手动调阈值获得的结果。
- Precision 高于 Recall，说明 student mask 偏保守、偏紧，但误检很少。

## Mask 可视化

主要文件：

```text
figures/mask_visualization_contact_sheet_12.jpg
results/dagm_c7_best_full_eval_pos/*.jpg
```

每张样例图从左到右是：

```text
input image | GT mask | predicted heatmap | overlay
```

观察结论：

- 预测热图基本落在 GT 缺陷区域，不像随机激活。
- 缺陷位置、方向和大致形状匹配较好。
- mask 通常略紧，这和 `Precision=0.99575`、`Recall=0.91761` 一致。

论文/PPT 用法：

- 可以用 `figures/mask_visualization_contact_sheet_12.jpg` 做总览图。
- 若版面需要更精致，可以从 `results/dagm_c7_best_full_eval_pos/` 中挑 4-6 张单例重新排版。

## Optical Kernel Grid

主要文件：

```text
results/dagm_c7_best_psf_targets/kernel_grid_signed.png
results/dagm_c7_best_psf_targets/kernel_grid_positive.png
results/dagm_c7_best_psf_targets/kernel_grid_negative.png
results/dagm_c7_best_psf_targets/kernel_stats.json
```

结论：

- learned kernels 不是纯噪声，有局部边缘、条纹和方向性结构。
- 正负权重都存在，因此必须做 positive/negative split。
- 部分 kernel 正负质量较均衡，如 `kernel 0/51/53`；部分 kernel 明显偏正，如 `kernel 37`。

论文/PPT 用法：

- `kernel_grid_signed.png` 用于展示蒸馏得到的 optical convolution bank。
- `kernel_grid_positive.png` 和 `kernel_grid_negative.png` 用于解释光强无法直接表达负权重，因此需要双路 PSF。

## PSF Target

主要文件：

```text
results/dagm_c7_best_psf_targets/dagm_psf_targets.npz
results/dagm_c7_best_psf_targets/psf_target_center_crop.png
results/dagm_c7_best_psf_targets/psf_backphase_preview.png
results/dagm_c7_best_psf_targets/psf_config.json
```

处理公式：

```text
K_positive = max(K, 0)
K_negative = max(-K, 0)
K = K_positive - K_negative
```

当前默认：

```text
SCALE=2
SIM_SIZE=1600
WAVELENGTH_NM=532
GRID_PITCH_NM=586
DETECTOR_DISTANCE_MM=2.4
NORMALIZE=paired_max
```

说明：

- 完整 `1600 x 1600` target 图里中心 PSF 很小，因此大图看起来接近全黑是正常现象。
- `psf_target_center_crop.png` 是更适合论文/PPT 展示的中心裁剪图。
- 这些物理参数来自 fabric/参考代码路径，是当前 probe 设置，不应直接写成最终硬件设计参数。

## Metasurface Probe

主要文件：

```text
results/dagm_c7_metasurface_probe_i40/batch_summary.json
tables/metasurface_probe_i40_summary.csv
results/dagm_c7_metasurface_probe_i40/kernel_*/positive/optimization_preview.png
results/dagm_c7_metasurface_probe_i40/kernel_*/negative/optimization_preview.png
```

第一轮选择了 4 个代表 kernel：

```text
0: 正负均衡，基准 case
51: 高能量 kernel
53: 高能量 kernel
37: 正负极不平衡，压力测试
```

40 iterations、`ROI_SIZE=96` 下，positive/negative 两路的 cosine similarity 在：

```text
0.97871 - 0.99106
```

结论：

- 在当前简化 radius-phase proxy 和 angular spectrum 传播模型下，target PSF 的主亮斑结构基本可拟合。
- simulated PSF 仍有低幅背景 speckle/noise floor。
- 这说明路线可行，但还需要更严格的物理仿真、参数 sweep，以及把 simulated PSF 放回 student pipeline 做性能下降评估。

论文/PPT 用法：

- `optimization_preview.png` 可用于展示 target PSF、simulated PSF、difference、phase、radius 和 loss 曲线。
- 不建议把它表述为“最终超表面设计已经完成”，更准确的说法是“first-pass physical feasibility probe”。

## 计算量节省表

主要文件：

```text
tables/compute_savings_summary.csv
tables/compute_reduction_ratios.csv
```

核心表述：

```text
Teacher @ 256x256: 21.08G MACs, 15.63M params
Teacher @ 512x512: 84.31G MACs, 15.63M params
Student digital proxy: 967.0M MACs, 60.7K params
Hybrid electronic backend: 23.3M electronic MACs, 46.3K electronic params
```

理论 reduction：

```text
student total params vs teacher: 258x fewer
hybrid electronic params vs teacher: 338x fewer
digital student MACs vs teacher @256: 21.8x fewer
hybrid electronic MACs vs digital student: 41.5x fewer
hybrid electronic MACs vs teacher @256: 905x fewer
hybrid electronic MACs vs teacher @512: 3618x fewer
```

注意：

- 这些是理论电子 MAC reduction，不是实测速度。
- 实际速度还取决于曝光时间、传感器读出、ADC、光通量、对准、电子硬件和制造误差。

## 建议论文图组

建议不要照搬参考论文的图风格，而是组织成我们自己的故事线：

1. 系统总览图：DAGM image -> metasurface optical frontend -> electronic SegDecNet-style backend -> segmentation/classification。
2. Teacher-student 架构对比图：teacher 是大电子 SegDecNet，student 是单层 optical bank 加轻量电子后端。
3. 定量指标表：teacher、student capped validation、student full validation、后续 simulated PSF student。
4. Mask qualitative 图：input/GT/heatmap/overlay。
5. Learned kernel grid：signed kernels 及 positive/negative split。
6. PSF target 图：positive/negative target center crop。
7. Metasurface probe 图：target vs simulated vs difference + phase/radius/loss。
8. 计算量节省表：参数和 MAC reduction。

## 当前未完成但应该继续

- 做 TEST split 或原论文 protocol 下的最终表格。
- 对 mixed positive/negative 样例重新导出更适合论文排版的高分辨率图。
- Sweep `SCALE`、`ROI_SIZE`、iterations，看 PSF 可实现误差是否更低。
- 把 simulated PSF 代替 learned digital kernels，测试完整 student 性能下降。
- 做 hardware-aware retraining：固定/扰动 optical frontend，只微调 calibration + electronic backend。

