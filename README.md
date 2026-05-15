# 超表面 + 工业缺陷检测

这个课题目录整理了“任务蒸馏的超表面光学视觉前端”相关代码、实验记录、参考文献和背景材料。

当前主线是：

```text
mixed-segdec-net-comind2021-master/
  DAGM Class7
  SegDecNet teacher
  单层 optical convolution bank student
  光电混合 segmentation + classification
```

## 目录说明

```text
.
├── AGENTS.md                         # 长期工作记忆和协作约定
├── SERVER.md                         # 服务器使用记录
├── mixed-segdec-net-comind2021-master # 当前主线：DAGM optical SegDec student
├── fabric_defect_detection-main       # 早期 fabric demo 和低分辨率经验来源
├── 卷积核->超表面相位设计代码          # PSF / phase design notebook
├── 参考工作                           # 光学前端、蒸馏、NTKD 等参考文献
└── 课题背景                           # 课题方案和背景材料
```

## 当前主线

请优先阅读：

```text
mixed-segdec-net-comind2021-master/README.md
mixed-segdec-net-comind2021-master/dagm_optical_distill/FOCUSED_SWEEP_NOTES.md
```

当前最佳学生模型配置：

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

在 capped `600` 验证样本设置下，目前记录：

```text
AP=1.00000
AUC=1.00000
IoU=0.83782
Dice=0.87685
```

这个结果还需要 full validation/test 和最终可视化确认。

## GitHub 提交策略

本仓库提交代码、README、实验记录、notebook 和参考材料。以下内容不提交：

- 数据集；
- 训练输出；
- checkpoint / `.pth` 权重；
- `results-*`、`outputs/`、`local_pull/`；
- 本地私有服务器信息。

实验结果应保留在本地和服务器，必要时用 README 记录路径和指标。
