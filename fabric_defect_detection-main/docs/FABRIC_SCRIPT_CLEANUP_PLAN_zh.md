# Fabric 脚本清理对齐清单

更新时间：2026-05-16

这个文件只用于清理前对齐。当前先不删除脚本，等确认后再执行。

## 1. 当前保留主线

Fabric 当前主线是：

`teacher CNN 二分类 -> R1 低分辨率 student -> optical kernels -> positive/negative split -> metasurface / mock CMOS -> PPT assets`

主结果：

- teacher 参考主线：`F1 ≈ 0.975`
- R1 student 默认阈值：`F1 = 0.2353`
- R1 student 最佳阈值约 `0.9`：`F1 = 0.8571`

## 2. 建议必须保留的脚本

这些脚本还在当前论文/PPT主线内，建议保留：

- `scripts/evaluation/evaluate_student.py`
- `scripts/evaluation/evaluate_teacher.py`
- `scripts/evaluation/generate_fabric_paper_assets_mainline.py`
- `scripts/evaluation/build_mock_cmos_from_kernels.py`
- `scripts/evaluation/run_cmos_electronic_backend.py`
- `scripts/export/export_student_kernels.py`
- `scripts/export/prepare_fabric_kernels_for_metasurface.py`
- `scripts/metasurface/fabric_metasurface_config.py`
- `scripts/metasurface/prepare_fabric_psf_targets.py`
- `scripts/metasurface/optimize_single_kernel_metasurface.py`
- `scripts/metasurface/run_fabric_metasurface_batch.py`
- `scripts/training/train_student_kd.py`
- `scripts/training/train_teacher.py`
- `scripts/reproduction/reproduce_binary_patch_notebook.py`

说明：

- `train_student_kd.py` 虽然当前最佳结果不是 KD，但它仍然记录了 student 训练链路，建议先保留。
- `evaluate_teacher.py` 的离线口径和主线 teacher 指标不同，但仍可作为代码链路参考，暂不删除。

## 3. 建议归档而不是直接删除的脚本

这些脚本不是当前 PPT 主线，但可能还对复现、补实验或答辩追问有用：

- `scripts/evaluation/benchmark_binary_cpu.py`
- `scripts/evaluation/eval_given_weight.py`
- `scripts/evaluation/evaluate_unet.py`
- `scripts/experiments/generate_student_sweep.py`
- `scripts/reproduction/run_notebook_cells.py`
- `scripts/reproduction/run_repro_30ep.sh`
- `scripts/training/train_binary_cached.py`
- `scripts/training/train_unet.py`
- `scripts/training/train_unet_student_kd.py`

建议处理方式：

- 新建 `scripts/archive/` 或 `scripts/legacy/`
- 把这些脚本移动进去
- README 里说明“非当前主线，仅供历史复现”

## 4. 可以删除的内容

目前已经删除的无效文件：

- `models/unet_seg_200epoch_log.txt`
- `models/unet_seg_50epoch_log.txt`

暂不建议继续删除更多代码文件，原因是：

- Fabric 原项目本身 notebook/demo 风格较重；
- 一些看起来边缘的脚本仍可能用于解释“我们从原 repo 到主线资产”的整理过程；
- PPT 写完前，先保持可追溯性更稳。

## 5. 建议下一步清理动作

确认后可以执行：

1. 建 `scripts/legacy/`
2. 移动第 3 节列出的非主线脚本
3. 更新 `README.md` 和 `paper_assets/README.md`
4. 跑一次 `scripts/evaluation/generate_fabric_paper_assets_mainline.py`
5. 提交并推送 GitHub

我的建议是：

`先推当前 assets 和文档，再做脚本归档。`

这样 PPT 阶段不会因为清理动作破坏当前可展示结果。
