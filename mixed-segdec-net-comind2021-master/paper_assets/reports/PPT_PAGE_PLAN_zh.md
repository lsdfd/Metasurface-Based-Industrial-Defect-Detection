# PPT 逐页清单（初版）

## 总体风格

- 比例：16:9
- 背景：白底或极浅灰底
- 标题：深蓝粗体
- 标题下方一条细横线
- 每页主体只放 1 个主图，或 1 组规整图网格，或 1 张表
- 页面底部固定 1 句结论

## 页型模板

### T1 大图页
- 标题
- 横线
- 1 张主图占中间 70%-75%
- 底部一句结论

### T2 对比页
- 标题
- 横线
- 左右两张主图或左图右表
- 底部一句结论

### T3 表格页
- 标题
- 横线
- 中间一张主表
- 右下角一个小结论框

### T4 流程图页
- 标题
- 横线
- 中间一张流程图/系统图
- 下方 3 个简短说明

### T5 结果网格页
- 标题
- 横线
- 2x2 或 3x2 图网格
- 底部一句总结

## 第1章 背景与问题定义（1-2页）

### 1. 工业缺陷检测问题定义
- 模板：T1
- 内容：AI 生成的背景问题图
- 备注：强调高分辨率工业图像、缺陷稀疏、电子计算代价高
- 结论：工业质检需要兼顾高分辨率、低延迟和可部署性

### 2. 我们的问题与目标
- 模板：T4
- 内容：AI 生成的总目标示意图
- 备注：电子 teacher -> optical student -> metasurface PSF -> lightweight backend
- 结论：目标是在尽量保持任务性能的同时，把早期特征提取前移到光学链路

## 第2章 总体方案与方法论（4-5页）

### 3. 课题总体研究路线
- 模板：T4
- 内容：AI 生成总方案架构图
- 结论：整个课题沿着“电子 teacher -> optical student -> physical mapping”逐步推进

### 4. 光电混合系统结构
- 模板：T4
- 内容：程序绘制或 AI 生成的系统图
- 结论：超表面负责早期卷积，电子后端负责非线性决策

### 5. 方法论：知识蒸馏与 optical frontend
- 模板：T2
- 内容：左边 teacher/student 对比框图，右边蒸馏损失说明
- 结论：蒸馏是连接高性能电子模型和物理友好 student 的核心桥梁

### 6. 从 learned kernels 到 PSF / metasurface
- 模板：T2
- 内容：左边 kernel split 示意，右边 PSF target 示意
- 结论：signed kernel 需要做 positive/negative split 才能映射到光强响应

### 7. 两个案例在整体路线中的位置
- 模板：T2
- 内容：Fabric 与 DAGM 两条线的关系图
- 结论：Fabric 是方法起点，DAGM 是更完整的工业缺陷分割主线

## 第3章 Fabric 二分类案例（8-9页）

### 8. Fabric 场景、任务与 baseline
- 模板：T4
- 内容：AITEX 大图 -> patch pipeline -> teacher CNN
- 结论：Fabric 提供了一个易于讲清楚的一层 optical student 起点

### 9. Fabric teacher 与 patch pipeline
- 模板：T2
- 内容：左边 patch pipeline 示意图（待补），右边 [classifier_architecture.svg](../figures_main/architecture/classifier_architecture.svg)
- 结论：teacher 是固定电子基线，后续 student 只替换早期特征提取部分

### 10. Fabric 方法嵌入：optical student + KD
- 模板：T4
- 内容：student 方法示意图（待补）
- 结论：一层 optical frontend + 小型 FC backend 是 fabric 路线的核心方法设计

### 11. Fabric teacher 结果
- 模板：T2
- 内容：左边 [cm.png](../../../fabric_defect_detection-main/paper_assets/figures_main/results/cm.png)，右边关键指标表
- 结论：teacher 二分类 F1 已基本复现成功，可作为稳定蒸馏基线

### 12. Fabric student 与 optical kernels
- 模板：T2
- 内容：左边 student checkpoint / kernels 说明，右边 kernel 可视化（待补现场导出）
- 结论：student 已经能导出可用于超表面设计的一层 optical kernels

### 13. Fabric positive/negative split 与 metasurface 输入
- 模板：T2
- 内容：左边 positive/negative split 示意（待补），右边 `fabric_r1_kernels_for_metasurface.npz` 说明
- 结论：Fabric 路线已经走通 kernels -> metasurface input 的接口

### 14. Fabric mock CMOS / backend 结果
- 模板：T3
- 内容：`mock_cmos_summary.csv` + `backend_result.json`
- 结论：Fabric 路线已经在代码层面形成 optical kernels -> mock CMOS -> electronic backend 闭环

### 15. Fabric 参数/MAC/意义
- 模板：T3
- 内容：待补现场计算的参数与 MAC 表
- 结论：Fabric 是小而清晰的 demo，验证了压缩 early feature extraction 的方法价值

### 16. Fabric 小结
- 模板：T1
- 内容：一张总结流程图或要点图
- 结论：Fabric 证明了 optical student 这条思路可行，并为更复杂任务提供经验

## 第4章 DAGM / SegDecNet 案例（11-13页）

### 17. DAGM 工业场景与任务定义
- 模板：T2
- 内容：数据样例图（待补）+ 任务定义
- 结论：DAGM 更接近“缺陷分割 + 工业纹理异常定位”的目标任务

### 18. 原始 SegDecNet：背景、架构、训练方式
- 模板：T2
- 内容：teacher 架构图（待补）+ 训练方式概述
- 结论：SegDecNet teacher 提供了强分割监督，是 optical student 蒸馏的核心来源

### 19. Teacher 结果
- 模板：T3
- 内容：teacher 指标表
- 结论：teacher 性能足够强，适合作为蒸馏上界

### 20. 我们的 DAGM optical student 架构
- 模板：T4
- 内容：student 架构图（待补程序绘制）
- 结论：student 保留单层 optical frontend，同时保留必要的 SegDecNet-style 电子后端

### 21. 两阶段蒸馏训练策略
- 模板：T4
- 内容：stage1/stage2 流程图
- 结论：先对齐 optical/segmentation，再联合训练全 student，更适合当前任务

### 22. 架构探索过程
- 模板：T3
- 内容：从 `FOCUSED_SWEEP_NOTES.md` 提炼的对比表
- 结论：`256/o64/k15/d4` 是性能与物理友好性的最好折中

### 23. 最优 student 定量结果
- 模板：T2
- 内容：左边 [dagm_full_validation_bar.png](../figures_main/metrics/dagm_full_validation_bar.png)，右边 full validation 表
- 结论：full validation 上 IoU=0.9145, Dice=0.9349，且默认 threshold=0.5 已最优

### 24. Mask 定性结果
- 模板：T1
- 内容：[mask_visualization_contact_sheet_12.jpg](../figures_main/qualitative_masks/mask_visualization_contact_sheet_12.jpg)
- 结论：预测热图准确落在 GT 缺陷区域，但整体偏保守、偏紧

### 25. Kernel grid 与 signed split
- 模板：T2
- 内容：`kernel_grid_signed.png` + `kernel_grid_positive/negative.png`
- 结论：student 学到的 optical kernels 具有方向性与纹理结构，且需要 positive/negative split

### 26. PSF target 与 backphase
- 模板：T2
- 内容：`psf_target_center_crop.png` + `psf_backphase_preview.png`
- 结论：当前 learned kernel 已经可以稳定转成单波长 target PSF 和初始 backphase

### 27. Metasurface feasibility probe
- 模板：T2
- 内容：左边 `kernel00_positive_probe.png`，右边 `metasurface_probe_cosine_bar.png`
- 结论：代表 kernel 的 cosine similarity 达到 0.979-0.991，说明目标 PSF 形状可匹配

### 28. DAGM 参数/MAC/速度意义
- 模板：T2
- 内容：左边 `compute_comparison_bar.png`，右边 reduction ratio 表
- 结论：理论上 hybrid electronic backend 相对 teacher 的电子计算可减少到百倍量级以上

### 29. DAGM 小结
- 模板：T1
- 内容：一张综合总结图
- 结论：DAGM 路线已经形成“蒸馏 -> optical kernels -> PSF target -> physical feasibility probe”闭环

## 第5章 阶段性总结（1-2页）

### 30. 当前阶段已完成贡献
- 模板：T3
- 内容：两案例对照总结表
- 结论：我们已经完成从软件 teacher 到物理可实现 probe 的完整主线验证

### 31. 两个案例的递进关系
- 模板：T4
- 内容：Fabric -> DAGM 的研究演进图
- 结论：研究从简化二分类 demo 逐步推进到更复杂工业缺陷分割任务

## 第6章 未来展望（1-2页）

### 32. 未来方向：检测与定位
- 模板：T1
- 内容：AI 生成未来展望图
- 结论：后续可扩展到 YOLO / 芯片 / PCB / wafer 等定位检测任务

### 33. 最终目标
- 模板：T1
- 内容：AI 生成未来系统图
- 结论：最终目标是高速、低功耗、可部署的工业质检光电混合系统

## AI 生图清单

仅用于以下页面：

- 第1页：工业缺陷检测问题背景图
- 第2页：问题定义与目标图
- 第3页：总体研究路线图
- 第4页：光电混合系统总架构图
- 第32页：未来展望图
- 第33页：最终目标系统图

其余所有实验结果页都用真实结果图，不用 AI 图。
