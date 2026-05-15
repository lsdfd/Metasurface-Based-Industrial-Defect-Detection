# Fabric Paper Assets

更新时间：2026-05-16

这个目录用于保存 `fabric_defect_detection-main` 当前真正进入论文、PPT 和答辩主线的资产。组织方式对齐 `mixed-segdec-net-comind2021-master/paper_assets`，按主图、过程图、表格、原始结果、权重和中文说明分开管理。

Fabric 章节当前只讲这一条主线：

`teacher CNN 二分类 -> 低分辨率 R1 student -> optical kernels -> positive/negative split -> metasurface / mock CMOS`

已经确认不是主模型、不是最好结果、或者容易误导汇报的低分 KD 结果，不再保留在这里。

## 1. 当前主模型

### Teacher

- 权重文件：`checkpoints/teacher/bigger_binary_F1_0.98.pth`
- 汇报主线参考指标：`F1 ≈ 0.975`

说明：

- 这个 teacher 数值来自原 notebook / mainline 口径。
- `results/fabric_teacher_eval.json` 是另一条离线脚本口径，不和这里的 `0.975` 混用。

### Student

当前锁定的 Fabric 主 student 为：

- `R1 baseline`
- `input_size = 64`
- `optical_kernels = 16`
- `kernel_size = 7`
- `pooled_size = 6`
- `hidden_dim = 256`
- `optical_activation = relu`

对应文件：

- `checkpoints/student/student_r1_best.pt`
- `checkpoints/student/student_r1_optical_kernels.pt`

关键结论：

- 默认阈值 `0.5` 下：`F1 = 0.2353`
- 最佳阈值约 `0.9` 下：`F1 = 0.8571`

因此正确口径是：

`低分辨率 R1 baseline student 已经学到有效判别特征，但具有明显阈值敏感性。`

## 2. 目录结构

```text
paper_assets/
  README.md
  ASSET_MANIFEST.csv
  checkpoints/
  figures_main/
  figures_process/
  reports/
  results/
  tables/
```

主要含义：

- `figures_main/`：直接用于论文/PPT 的主图
- `figures_process/`：讲实验过程、阈值敏感性、设计逻辑的过程图
- `tables/`：指标表、计算量表、接口摘要表
- `results/`：生成这些图表所依赖的原始结果
- `reports/`：中文口径说明、PPT 索引、结论摘要

## 3. 当前核心资产

### 主图

- `figures_main/results/fabric_teacher_student_summary_bar.png`
- `figures_main/results/fabric_r1_threshold_comparison.png`
- `figures_main/compute/fabric_compute_comparison_bar.png`
- `figures_main/kernels/kernel_grid_signed.png`
- `figures_main/kernels/kernel_grid_positive.png`
- `figures_main/kernels/kernel_grid_negative.png`

### 过程图

- `figures_process/threshold_sweep/fabric_r1_threshold_story.png`

### 表格

- `tables/fabric_teacher_student_summary.csv`
- `tables/fabric_compute_summary.csv`
- `tables/fabric_r1_student_result_summary.csv`
- `tables/mock_cmos_summary.csv`

### 原始结果与接口

- `results/fabric_r1_student_best_threshold_eval.json`
- `results/metasurface/fabric_r1_kernels_for_metasurface.npz`
- `results/mock_cmos/backend_result.json`

## 4. Fabric 这一章怎么讲

建议汇报顺序固定为：

1. Teacher CNN patch 二分类基线很强，主线参考 `F1 ≈ 0.975`
2. 最关键经验不是复杂 KD，而是把输入压到 `64x64`
3. 最优 student 是 `R1 baseline`
4. 这个 student 在默认阈值下分数不高，但最佳阈值下达到 `F1 = 0.8571`
5. 因此 student 已经具备作为 optical frontend 原型的价值
6. 后续自然衔接到 kernel 导出、正负拆分、超表面目标和 mock CMOS 后端

## 5. 推荐 PPT 用图

如果只留 5-6 页 Fabric 结果页，建议按这个顺序：

1. `figures_main/results/fabric_teacher_student_summary_bar.png`
2. `figures_process/threshold_sweep/fabric_r1_threshold_story.png`
3. `figures_main/kernels/kernel_grid_signed.png`
4. `figures_main/kernels/kernel_grid_positive.png`
5. `figures_main/kernels/kernel_grid_negative.png`
6. `figures_main/compute/fabric_compute_comparison_bar.png`

更详细的用图索引见：

- `reports/fabric_ppt_asset_index.csv`
- `reports/fabric_assets_summary_zh.md`

## 6. 资产如何重新生成

主线图表由下面脚本生成：

```bash
python3 scripts/evaluation/generate_fabric_paper_assets_mainline.py
```

这个脚本会重建：

- teacher/student 对比主图
- 阈值敏感性过程图
- 阈值对比图
- PPT 资产索引
- 中文说明文档
- `ASSET_MANIFEST.csv`

## 7. GitHub 注意事项

`checkpoints/teacher/bigger_binary_F1_0.98.pth` 大于 GitHub 单文件 `100 MB` 限制。

因此：

- 本地和服务器保留真实权重
- GitHub 只保留结构说明或较小权重文件

详情见：

- `checkpoints/teacher/README.md`

## 8. 当前清理原则

当前保持这一条原则：

`不是主模型，不是最好结果，不是对论文叙事有帮助的对照，就不放进 paper_assets 主目录。`

所以那些低分、混乱、误导性的 Fabric KD 结果不会再恢复到这里。
