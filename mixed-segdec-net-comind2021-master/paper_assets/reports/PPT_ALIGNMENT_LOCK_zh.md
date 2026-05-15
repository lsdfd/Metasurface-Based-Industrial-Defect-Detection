# PPT 对齐锁定稿

更新时间：2026-05-15

这个文件用于锁定当前已经和用户对齐好的 PPT 内容、结构、视觉样式和素材使用原则，避免后续跑偏或遗忘。

## 1. PPT 总目标

这份 PPT 用于给导师做完整科研汇报，主题是：

`超表面光学前端 + 电子后端 + 工业缺陷检测`

重点不是做一个泛泛的概念展示，而是要把：

1. 课题背景
2. 整体实现思路
3. Fabric 案例
4. Mixed-SegDecNet / DAGM 案例
5. 当前结果与硬件意义
6. 后续展望

讲清楚、讲完整、讲得像一个成熟科研课题，而不是零散实验堆砌。

## 2. 整体页数控制

当前对齐目标：

- 总页数大约 `26-33` 页
- 更理想的是接近 `30` 页

章节结构固定为：

1. 背景与问题定义：`1-2` 页
2. 总体方案与方法论：`4-5` 页
3. Fabric 二分类案例：`8-9` 页
4. DAGM / SegDecNet 案例：`11-13` 页
5. 阶段性总结：`1-2` 页
6. 未来展望：`1-2` 页

## 3. 内容重点分配

### 3.1 背景部分

- 只讲 `1-2` 页
- 不要展开太多综述式内容
- 不单独做很大的“相关工作”章节
- 参考工作启发应融入方法页和案例页里

背景部分主要讲清楚：

1. 工业缺陷检测面对高分辨率图像和低延迟部署压力
2. 纯电子 CNN 在前端高分辨率特征提取上代价高
3. 本课题希望把最早期卷积前移到超表面光学链路

### 3.2 中间主体部分

PPT 主体必须重点讲两个例子：

1. `fabric_defect_detection-main`
2. `mixed-segdec-net-comind2021-master`

并且一定要把以下内容自然嵌入案例里讲：

- teacher / student 架构
- 知识蒸馏方法
- 输入分辨率、卷积核、光学前端设计动机
- 正负卷积核拆分
- PSF / metasurface target / feasibility
- 参数量、MACs、理论速度和硬件意义

### 3.3 结尾部分

- 总结只要 `1-2` 页
- 展望只要 `1-2` 页
- 不要太散，不要列过多空泛 future work

未来展望可以提：

- YOLO / 芯片检测 / PCB / wafer / 缺陷定位
- 光学前端进一步物理实现
- calibration / robust hardware deployment

## 4. 两个案例的定位

### 4.1 Fabric 案例定位

Fabric 只讲：

- `CNN patch binary classification`
- teacher CNN
- low-resolution optical student
- student kernels -> positive/negative split
- metasurface / mock CMOS 接口

明确约束：

- 不把 U-Net 作为 Fabric 本章主叙事
- 不把 Fabric 讲成最终最强性能案例
- Fabric 是“方法起点 / 第一版 demo / 光学 student 思路验证”

要特别强调的经验：

- 将 student 输入分辨率缩小是关键发现
- `R1 = 64x64` 是文档中记录的 best student baseline
- 这个经验和 Fabric 项目中的观察高度一致

### 4.2 DAGM / SegDecNet 案例定位

这部分是当前主结果章节。

要重点讲：

- DAGM 的工业场景和任务定义
- 原始 SegDecNet teacher
- 我们的 student 设计
- 两阶段蒸馏训练
- 架构探索过程
- 最优结果
- mask 定性图
- kernel / PSF / metasurface feasibility
- 参数/MACs 压缩

这部分承担“高性能主结果”的角色。

## 5. 页面样式锁定

整体风格必须是：

- 科研风格
- 干净
- 白底或极浅灰底
- 深蓝色标题
- 不要花哨
- 不要 AI 味太重

### 5.1 固定页面骨架

推荐统一为：

- 顶部标题
- 标题下方一条细横线
- 中间 1 张主图 / 1 组规整图 / 1 张主表
- 底部 1 行核心结论

页面尽量做纵向自上而下布局，不要碎片化拼太多小元素。

### 5.2 页面模板

当前锁定的页型模板：

- `T1` 大图页
- `T2` 对比页
- `T3` 表格页
- `T4` 流程图页
- `T5` 结果网格页

详细定义见：

- [PPT_PAGE_PLAN_zh.md](/Users/lishengxin/Desktop/毕设/科研/图像处理/CNN/课题：超表面+工业缺陷检测/mixed-segdec-net-comind2021-master/paper_assets/reports/PPT_PAGE_PLAN_zh.md)

## 6. 图片使用原则

### 6.1 哪些页可以用 AI 生图

只有以下几类页可以用 AI 图：

1. 背景问题图
2. 总体目标 / 总体方案架构图
3. 光电混合系统宏观示意图
4. Fabric 章节末尾的实验装置 / 光路示意图
5. DAGM 章节末尾的实验装置 / 光路示意图
6. 未来展望图

### 6.2 哪些页不能用 AI 生图

以下内容必须优先用真实实验图：

1. 指标图
2. mask 可视化
3. kernel grid
4. PSF target / simulated PSF 对比
5. compute / params / MACs 表格
6. threshold sweep
7. confusion matrix

不要用 AI 图替代真实结果图。

### 6.3 不需要的图

用户已经明确不需要：

- 泛泛的产线图
- 空泛芯片 / 传感器概念图
- 为了好看而堆的技术概念海报

## 7. Fabric 章节必须使用的真实素材

当前应优先使用：

- `classifier_architecture.svg`
- `fabric_metrics_bar.png`
- `fabric_teacher_confusion_matrix.png`
- `fabric_student_confusion_matrix.png`
- `fabric_compute_comparison_bar.png`
- `kernel_grid_signed.png`
- `kernel_grid_positive.png`
- `kernel_grid_negative.png`
- `fabric_student_threshold_sweep.png`

同时要特别注意：

- Fabric 章节的主线是二分类 student 探索
- 要强调“低分辨率输入让 student 突然变强”的经验
- 如果当前 paper assets 中 student 指标表和实际历史最佳结果不一致，必须以后续重跑/复线结果为准

## 8. DAGM 章节必须使用的真实素材

当前应优先使用：

- `dagm_full_validation_bar.png`
- `mask_visualization_contact_sheet_12.jpg`
- `kernel_grid_signed.png`
- `kernel_grid_positive.png`
- `kernel_grid_negative.png`
- `psf_target_center_crop.png`
- `kernel00_positive_probe.png`
- `kernel37_negative_probe.png`
- `metasurface_probe_cosine_bar.png`
- `compute_comparison_bar.png`
- `dagm_threshold_sweep.png`

## 9. 性能吹点必须嵌入案例

不要单独做一个空泛的“硬件意义”大章节。

而是要把以下内容嵌入 Fabric 和 DAGM 两个案例中：

- 参数减少多少倍
- MACs 降低多少倍
- 理论上电子计算节省多少
- 为什么这对超表面 + 电子后端有意义

## 10. 页面逻辑顺序要求

第三章和第四章都要遵循类似顺序：

1. 场景 / 任务定义
2. 原始 teacher
3. 我们的方法嵌入
4. student 结构
5. 训练 / 蒸馏策略
6. 实验结果
7. 过程分析
8. 物理映射 / 硬件意义
9. 小结

不要把结果和方法讲乱。

## 11. 当前必须记住的口径

### Fabric

- Teacher CNN 强结果大约 `F1≈0.975`
- Student 的关键发现是：小输入分辨率非常重要
- 文档记录的 best baseline 是 `R1=64x64`
- student 的最终高分结果需要以后续重跑和历史复线结果为准

### DAGM

- 当前最优 student：
  `dagm_c7_r256_o64_k15_d4_e12-24-32_seg5_vol3_fg5_t2_m600_ep70`
- full validation：
  - `AP=1.00000`
  - `AUC=1.00000`
  - `IoU=0.91451`
  - `Dice=0.93488`
  - `Precision=0.99575`
  - `Recall=0.91761`
  - `threshold=0.50`

## 12. 生成 PPT 时的硬约束

后续真开始生成 PPT 时，必须遵守：

1. 先锁定逐页内容，再生成页面
2. 先用真实 assets 填页，再决定哪些页需要 AI 图
3. 所有实验结果页优先引用本地真实图
4. 每页只突出一个核心信息
5. 不要排版花哨，不要堆太多 bullet

## 13. 后续待办

当前还需要继续做的与 PPT 强相关任务：

1. 纠正 Fabric paper assets 的 student 指标口径
2. 重跑并确认低分辨率 student 的真实最好结果
3. 用最终结果更新 Fabric 章节素材索引
4. 在锁定 PPT 后，再调用 AI 生图 API 生成背景页/总方案页/未来展望页
