# R1 主线下一轮实验计划

更新时间：2026-05-16

## 1. 目标

当前 Fabric 主 student 已锁定为：

- `R1 baseline`
- `input_size = 64`
- `optical_kernels = 16`
- `kernel_size = 7`
- `pooled_size = 6`
- `hidden_dim = 256`
- `optical_activation = relu`

并且已有历史结果表明：

- 在最佳阈值下，验证集 F1 可达到约 `0.8571`

下一轮实验的目标不是再证明这条线存在，而是：

1. 在当前代码和服务器环境下重新把这条结果跑稳
2. 围绕 `R1` 周围做更系统的局部探索
3. 找到一个比当前 `R1` 更优或至少更稳的 student
4. 用最终最优 student 重新生成高质量 PPT assets

## 2. 当前判断

从历史记录和当前代码状态看，当前最值得优先做的，不是继续大面积扫 `KD`，而是：

### 2.1 先把 baseline 跑稳

原因：

- 当前 Fabric 最优 student 已知是 baseline，不是 KD
- 当前最重要的是把 `R1` 在现环境下重新验证清楚
- baseline 都没重新锁稳之前，不应该让 KD 继续污染主线

### 2.2 先围绕 R1 做局部结构探索

原因：

- 低分辨率输入已经被证明是关键变量
- 现在最有可能继续提升分数的，是在 `R1` 附近调：
  - pooling
  - hidden dim
  - activation
  - 训练轮数
  - imbalance 策略

### 2.3 KD 暂时退到第二优先级

原因：

- 当前保留下来的高分结果不是 KD
- 历史上低分 KD 已经被清理出主线
- 若 baseline 进一步变强，之后再把 KD 加回来更合理

## 3. 当前建议的实验顺序

### 第一组：R1 长周期复线

目的：

- 先验证当前最简 student 在更长训练周期下能走到哪里

实验：

1. `R1-30`
   - `64 / 16 / 7 / 6 / 256 / relu`
   - `epoch = 30`
   - `batch_size = 32`
   - `lr = 1e-3`
   - `balanced sampler = on`
   - `pos_weight = off`

2. `R1-50`
   - 与 `R1-30` 相同
   - `epoch = 50`

3. `R1-100`
   - 与 `R1-30` 相同
   - `epoch = 100`

### 第二组：R1 结构微调

目的：

- 验证是不是简单改一点后端容量和 pooling 就能更稳

实验：

4. `R1-P8`
   - `pooled_size = 8`
   - 其余同 `R1`

5. `R1-H512`
   - `hidden_dim = 512`
   - 其余同 `R1`

6. `R1-P8H512`
   - `pooled_size = 8`
   - `hidden_dim = 512`
   - 其余同 `R1`

7. `R1-ID`
   - `optical_activation = identity`
   - 其余同 `R1`

### 第三组：训练策略微调

目的：

- 看 imbalance 策略是否继续影响 precision / recall tradeoff

实验：

8. `R1-NS`
   - `balanced sampler = off`
   - `pos_weight = off`

9. `R1-APW`
   - `balanced sampler = on`
   - `auto_pos_weight = on`

10. `R1-LR5e4`
   - `lr = 5e-4`
   - 其余同 `R1`

## 4. 当前最推荐优先跑的 4 组

如果算力有限，优先级建议：

1. `R1-50`
2. `R1-P8`
3. `R1-H512`
4. `R1-LR5e4`

原因：

- `R1-50` 用来确认历史高分是否能稳定复现
- `R1-P8` 检查更大 pooled map 是否更利于电子后端
- `R1-H512` 检查当前后端是否过弱
- `R1-LR5e4` 检查是不是训练更平稳有帮助

## 5. 当前暂不优先做的事

### 5.1 暂不优先重新大规模做 KD

原因：

- 当前主 student 最优结果不是 KD
- 先把 baseline 极限摸清楚更有意义

### 5.2 暂不优先恢复 U-Net 主线

原因：

- Fabric 当前章节只讲二分类主线
- 不应该再让 U-Net 混回来

### 5.3 暂不优先恢复错误 paper assets 自动导出脚本

原因：

- 旧脚本会把错误 student 口径重新带回来
- 应该等最终最优 student 锁定后，再写新的 assets 生成方案

## 6. 评估口径锁定

Fabric student 后续必须统一记录两种结果：

1. `val default @ threshold = 0.5`
2. `val best threshold F1`

同时推荐补一个更接近你历史记忆的口径：

3. `full-dataset F1 @ best threshold`

原因：

- 当前 `R1` 已经确认是一个强阈值敏感模型
- 单看 `threshold = 0.5` 很容易误判

## 7. 输出规范

建议输出目录统一为：

```text
outputs/r1_sweep/R1-50_seed42/
outputs/r1_sweep/R1-P8_seed42/
outputs/r1_sweep/R1-H512_seed42/
...
```

每组都至少保留：

- `history.json`
- `student_best.pt`
- `student_last.pt`
- `student_optical_kernels.pt`
- `eval_val_best.json`

## 8. 最终目标

当这轮局部探索结束后，必须只保留：

1. 一个最终最优 student
2. 一套与之完全一致的评估结果
3. 一套围绕这个模型的 PPT assets

也就是说，后续所有 Fabric 的：

- 结果表
- confusion matrix
- threshold 图
- kernels 图
- metasurface 图
- mock CMOS 图

都必须围绕最终最优 student 重建，不再混入旧模型。
