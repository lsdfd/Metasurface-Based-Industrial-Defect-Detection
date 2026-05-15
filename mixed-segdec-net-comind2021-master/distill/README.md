# 蒸馏模块

`distill/` 是当前 DAGM Class7 optical student 的通用训练模块。

## 设计目标

- Teacher：原始 `SegDecNet`。
- Student：`OpticalSegDecStudent`。
- Optical frontend：单层卷积核 bank，作为 metasurface PSF encoder 的数字代理。
- Electronic backend：保留 `seg_head + extractor + fc` 骨架，只做轻量化。
- Training：两阶段蒸馏，先对齐 optical/seg/volume，再联合优化 segmentation/classification/KD。

## 文件说明

```text
distill/
  models.py          # OpticalSegDecStudent 和 optical frontend
  losses.py          # task loss、seg KD、volume KD、relation KD
  trainer.py         # teacher wrapper、两阶段训练、评估和 checkpoint
  train_distill.py   # CLI 入口
```

## 推荐入口

不要直接手写长命令，优先使用：

```bash
./dagm_optical_distill/distill_focused_student_sweep.sh
```

具体实验配置和当前最好结果见：

```text
dagm_optical_distill/FOCUSED_SWEEP_NOTES.md
```
