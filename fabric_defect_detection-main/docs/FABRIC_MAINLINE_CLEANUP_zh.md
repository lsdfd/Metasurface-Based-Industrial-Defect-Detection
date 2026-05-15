# Fabric 主线清理说明

更新时间：2026-05-16

## 1. 为什么要清理

`fabric_defect_detection-main` 这条线在前期做过多轮二分类蒸馏、KD 尝试、评估脚本修正和 paper assets 导出。

后续出现的问题是：

1. 一些低分、失败、非主线的 `KD` 结果混进了 `paper_assets`
2. 一些旧脚本会继续导出误导性的结果口径
3. teacher 权重存在重复文件
4. U-Net 的日志和 Fabric 当前二分类主线混在一起，容易干扰后续汇报

因此需要把 Fabric 收敛成一条非常明确的主线。

## 2. 当前 Fabric 唯一主线

当前唯一主线锁定为：

`teacher CNN -> R1 baseline student -> optical kernels -> positive/negative split -> metasurface target -> mock CMOS / electronic backend`

其中：

### Teacher

- 权重文件：
  `models/bigger_binary_F1_0.98 (1).pth`
- 原 notebook / full-dataset 口径下，teacher F1 约：
  `0.975`

### Student

当前主 student 为：

- `R1 baseline`
- `input_size = 64`
- `optical_kernels = 16`
- `kernel_size = 7`
- `pooled_size = 6`
- `hidden_dim = 256`
- `optical_activation = relu`

对应文件：

- `models/distillation/student_r1_best.pt`
- `models/distillation/student_r1_optical_kernels.pt`

已确认的重要结果：

- 默认阈值 `0.5` 下，该模型 F1 不高
- 经过 `threshold sweep` 后
- 最佳验证集 F1 约为：
  `0.8571428571`
- 最佳阈值约：
  `0.9`

因此正确表述是：

`R1 student 是一个低分辨率、高阈值敏感、但在最佳阈值下性能成立的 optical-style baseline student。`

## 3. 这次已经删除什么

### 已删除的误导性结果资产

从 `paper_assets` 中删除：

- 低分 `KD` student 的评估 json
- 低分 `KD` student 的 confusion matrix
- 低分 `KD` student 的 threshold sweep 图
- 基于错误主模型生成的 metrics bar
- 基于错误主模型生成的中文总结

### 已删除的本地误导性文件

- `models/bigger_binary_F1_0.98.pth`
  - 原因：和 `(1).pth` 重复，保留一份即可
- `models/unet_seg_200epoch_log.txt`
  - 原因：不是 Fabric 当前二分类主线
- `models/unet_seg_50epoch_log.txt`
  - 原因：不是 Fabric 当前二分类主线
- `scripts/evaluation/export_paper_assets.py`
  - 原因：会按错误 student 口径自动生成误导性 assets，不适合当前主线继续保留

## 4. 为什么保留这些文件

以下文件必须保留：

### checkpoint

- `models/bigger_binary_F1_0.98 (1).pth`
- `models/distillation/student_r1_best.pt`
- `models/distillation/student_r1_optical_kernels.pt`

### 输出接口

- `outputs/metasurface/fabric_r1_kernels_for_metasurface.npz`
- `outputs/mock_cmos/student_kernel_mock.npz`
- `outputs/mock_cmos/backend_result.json`

### paper assets

保留与主线直接相关的：

- teacher confusion matrix
- compute comparison
- kernel signed / positive / negative
- mock CMOS summary
- metasurface target source
- R1 student checkpoint copy

## 5. 当前不再认哪些结果

以下结果不再作为 Fabric 主结果使用：

- 低分 `KD` student
- 低分 `KD` 评估表
- 低分 `KD` confusion matrix
- 低分 `KD` threshold sweep
- 任何把 Fabric 主 student 说成“失败”的自动导出结果

这些内容如果以后确实要保留，只能作为：

- 失败实验记录
- 方法探索历史

而不能再放进主 `paper_assets` 或主 PPT 叙事。

## 6. 当前最重要的后续工作

清理完成后，Fabric 后续只做以下三件事：

1. 围绕 `R1 = 64x64` 做更系统的长周期探索
2. 在 `R1` 周围试更强 student 结构和训练参数
3. 用最终最优结果重新生成高质量 PPT assets

## 7. 后续实验应该怎么做

不再围绕错误的低分 KD 结果打转。

后续实验优先顺序：

1. 以 `R1 baseline` 为中心做长 epoch 训练
2. 做 `R1` 附近结构探索：
   - pooled size
   - hidden dim
   - optical activation
   - 更强电子后端
3. 再比较是否值得重新引入 KD
4. 拿最终最好结果统一做：
   - teacher / student 结果表
   - threshold sensitivity 图
   - compute / params 表
   - kernels / metasurface / mock CMOS 图

## 8. 一句话锁定

Fabric 当前的主模型不是烂掉的 KD 版本，而是：

`R1 baseline student (64 / 16 / 7 / 6 / 256 / relu)`

后续所有 assets、汇报、PPT、metasurface mapping，都应默认围绕这条主线展开。
