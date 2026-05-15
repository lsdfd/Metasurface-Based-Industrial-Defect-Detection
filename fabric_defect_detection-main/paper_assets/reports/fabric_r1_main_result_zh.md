# Fabric R1 主结果说明

更新时间：2026-05-16

## 1. 结论先行

Fabric 当前唯一确认有效的主 student 结果是：

- 模型：`student_r1_best.pt`
- 结构：`R1 baseline`
- 输入分辨率：`64 x 64`
- 最佳阈值验证集 F1：
  `0.8571428571428571`

这条结果成立，且应作为 Fabric 章节 student 主结果。

## 2. 对应配置

该 student 的完整配置为：

- `input_size = 64`
- `optical_kernels = 16`
- `kernel_size = 7`
- `pooled_size = 6`
- `hidden_dim = 256`
- `optical_activation = relu`

对应文件：

- `models/distillation/student_r1_best.pt`
- `models/distillation/student_r1_optical_kernels.pt`

## 3. 为什么之前会混乱

前面产生混乱的原因，不是这个模型不存在，而是：

1. `paper_assets` 里曾混入一批低分的 `KD` 结果
2. 那批结果不是当前主 student
3. `student_r1_best.pt` 是 `R1 baseline`，不是后面失败的 `KD` 版本
4. 这个模型本身具有很强的阈值敏感性

## 4. 正确的评估口径

对于这个模型，必须同时写两组结果：

### 默认阈值

- `threshold = 0.5`
- `F1 = 0.23529411764705882`

### 最佳阈值

- `threshold = 0.8999999761581421`
- `precision = 0.75`
- `recall = 1.0`
- `F1 = 0.8571428571428571`

因此正确解释是：

`R1 student 不是没学到，而是一个强阈值敏感的二分类 student。`

## 5. Fabric 章节应该怎么讲

Fabric 章节现在应按下面逻辑讲：

1. teacher CNN 二分类基线很强
2. student 的关键经验是：
   `把输入分辨率降到 64 x 64`
3. 最优 student 不是 KD 版本，而是 `R1 baseline`
4. 该模型在最佳阈值下达到 `F1 = 0.8571`
5. optical kernels 已能稳定导出，并进入：
   - signed kernel
   - positive/negative split
   - metasurface target
   - mock CMOS backend

## 6. 后续资产与 PPT 使用原则

Fabric 所有后续：

- 结果文档
- PPT 页面
- 表格
- 总结
- 口头汇报

都必须默认围绕这条主结果：

`R1 baseline @ 64 / 16 / 7 / 6 / 256 / relu, best-threshold F1 = 0.8571`

不再混入那些低分 `KD` 结果。
