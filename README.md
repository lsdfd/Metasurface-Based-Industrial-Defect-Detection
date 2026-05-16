# 超表面 + 工业缺陷检测

这个仓库是一个本科/科研课题工作区，目标是探索：

```text
任务蒸馏的超表面光学视觉前端
```

更具体地说，我们不是要做“完整全光学神经网络”，而是要做一个更现实的光电混合系统：

- 光学前端：用单层 metasurface-like PSF / convolution bank 完成早期特征编码；
- 电子后端：用轻量神经网络完成非线性决策、分割和分类；
- 训练方式：从更强的电子 teacher 网络蒸馏到受物理约束的 optical student；
- 后续硬件映射：把 student 学到的 optical kernels 转成正负 PSF 目标，再进入超表面相位/结构优化。

当前仓库已经从早期探索状态整理为一条清晰主线：

```text
DAGM Class7
SegDecNet teacher
单层 optical convolution bank student
光电混合 defect segmentation + classification
```

## 这次整理做了什么

本次清理的目标是把项目从“探索现场”整理成“DAGM Class7 optical student 可复现项目”。

已经完成：

- 删除/忽略 KSDD2 失败探索路线相关入口，避免后续误跑。
- 保留最后成功的 DAGM focused sweep，而不是保留一堆历史 smoke/sweep 脚本。
- 数据集、checkpoint、`results-*`、`outputs/` 不提交到 GitHub，但本地和服务器结果保留。
- README 改为中文交接文档，说明项目思路、目录、复现流程、当前最好结果和后续验证。
- 服务器文档脱敏，不把真实登录信息、密码或 checkpoint 上传到 GitHub。

特别注意：失败实验和大结果文件不应该用 Git 管理。它们的结论写入文档，真正的文件保留在本地/服务器。

## 目录结构

```text
.
├── README.md
├── AGENTS.md
├── SERVER.md
├── mixed-segdec-net-comind2021-master/
├── fabric_defect_detection-main/
├── kernel-to-metasurface-phase-design/
├── reference-papers/
└── project-background/
```

各目录含义：

- `mixed-segdec-net-comind2021-master/`：当前主线。基于 SegDecNet，新增 DAGM Class7 optical student 蒸馏。
- `fabric_defect_detection-main/`：早期 fabric demo 和低分辨率经验来源。当前不是主线，但保留代码和笔记。
- `kernel-to-metasurface-phase-design/`：后续把 learned kernels 转成 PSF/phase 的参考 notebook。
- `reference-papers/`：光学前端、RGB metasurface、知识蒸馏、NTKD 等论文资料。
- `project-background/`：课题构想、demo 方案和背景材料。

## 当前主线在哪里

优先阅读：

```text
mixed-segdec-net-comind2021-master/README.md
mixed-segdec-net-comind2021-master/dagm_optical_distill/README.md
mixed-segdec-net-comind2021-master/dagm_optical_distill/FOCUSED_SWEEP_NOTES.md
```

其中：

- `mixed-segdec-net-comind2021-master/README.md`：主线总说明和完整复现步骤。
- `dagm_optical_distill/README.md`：DAGM Class7 脚本说明。
- `FOCUSED_SWEEP_NOTES.md`：架构探索过程、结果表、为什么当前指标大概率不是假指标、下一步风险。

## 当前最好结果

当前推荐 student run：

```text
dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70
```

核心配置：

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

在 capped `600` 验证样本设置下，目前记录：

```text
AP=1.00000
AUC=1.00000
IoU=0.83782
Dice=0.87685
```

这个结果已经明显优于早期 student，但还不能当作最终论文数字。后续必须补 full validation/test、最终 checkpoint 可视化和 threshold sweep。

## 本地与服务器约定

GitHub 只提交：

- 代码；
- README 和实验记录；
- 小型脚本、notebook、配置；
- 参考文档。

GitHub 不提交：

- 数据集；
- checkpoint / `.pth` / `.pt`；
- `results-*`；
- `outputs/`；
- 本地服务器私密信息。

服务器上保留训练成果。当前关键结果位于：

```text
/root/fabric_run/mixed-segdec-net-comind2021-master/results-dagm-distill-focused/
/root/fabric_run/mixed-segdec-net-comind2021-master/results-dagm-teacher/
```

## 下一步

建议下一轮工作顺序：

1. 对 best student 跑 full validation/test。
2. 导出 final best checkpoint 的正样本和混合样本可视化。
3. 记录 fixed threshold 与 best threshold 的 segmentation 指标。
4. 同一 split 上对比 teacher 和 student。
5. 导出 `best_optical_kernels.npy`，开始正负 PSF 分解和 metasurface phase design。

## GitHub

当前远程仓库：

```text
https://github.com/lsdfd/Metasurface-Based-Industrial-Defect-Detection
```

如果未来加入大模型文件或更大的 PDF，请使用 Git LFS 或只记录下载链接。
