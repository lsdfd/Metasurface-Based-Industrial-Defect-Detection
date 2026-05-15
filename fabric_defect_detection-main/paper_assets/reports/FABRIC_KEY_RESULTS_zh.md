# Fabric 关键结果速查

更新时间：2026-05-16

## Teacher

- 模型：
  `models/bigger_binary_F1_0.98 (1).pth`
- 口径：
  原 notebook / full-dataset 风格
- 结果：
  `F1 ≈ 0.975`

## Student 主结果

- 模型：
  `models/distillation/student_r1_best.pt`
- 配置：
  `64 / 16 / 7 / 6 / 256 / relu`
- 类型：
  `R1 baseline`

### 默认阈值

- `threshold = 0.5`
- `F1 = 0.23529411764705882`

### 最佳阈值

- `threshold = 0.8999999761581421`
- `precision = 0.75`
- `recall = 1.0`
- `F1 = 0.8571428571428571`

## 一句话口径

Fabric student 的关键发现不是 `KD`，而是：

`低分辨率 R1 baseline student 在高阈值下可以达到较高 F1。`
