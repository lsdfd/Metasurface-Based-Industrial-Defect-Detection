# PPT 生成说明

更新时间：2026-05-16

当前推荐 PPT：

```text
presentation/build/metasurface_industrial_defect_detection_v4.pptx
```

页数：`30`

文件大小：约 `12.8 MB`

历史版本仍保留：

```text
presentation/build/metasurface_industrial_defect_detection_v1.pptx
presentation/build/metasurface_industrial_defect_detection_v2.pptx
presentation/build/metasurface_industrial_defect_detection_v3.pptx
```

## 1. 主题

```text
超表面光学前端辅助的工业缺陷检测
```

核心故事线：

```text
工业缺陷检测计算压力
-> 电子 teacher
-> optical student
-> learned kernels
-> positive/negative split
-> PSF / metasurface feasibility
-> lightweight electronic backend
```

## 2. 当前章节结构

```text
1      封面
2-8    背景与总体方案
9-15   Fabric 二分类案例
16-28  DAGM / SegDecNet 案例
29-30  总结与未来展望
```

## 3. 真实实验素材来源

Fabric 真实结果素材：

```text
fabric_defect_detection-main/paper_assets/
```

DAGM / SegDecNet 真实结果素材：

```text
mixed-segdec-net-comind2021-master/paper_assets/
```

结果页优先使用真实实验图，包括：

- 指标柱状图
- threshold sweep
- mask visualization
- kernel grid
- PSF target / backphase
- metasurface feasibility probe
- compute / MACs 图表

## 4. AI 概念图来源

AI 概念图保存在：

```text
presentation/ai_images_v3/
presentation/ai_images_v4/
presentation/ai_images_v2/
```

当前使用 FAL：

```text
model = openai/gpt-image-2
image_size = landscape_16_9
quality = medium
```

生成脚本：

```bash
python3 presentation/scripts/generate_ai_images_fal.py
```

当前 v2 使用的 FAL 图：

```text
v2_background_infographic.png
v2_methodology_graphical_abstract.png
v2_hybrid_optical_architecture.png
v2_fabric_case_diagram.png
v2_dagm_case_diagram.png
v2_future_system_roadmap.png
```

这些图的 prompt 也保存在同目录的 `*.prompt.txt` 中。

当前 v3 额外使用的 FAL 图：

```text
v3_distillation_training_mechanism.png
v3_kernel_to_psf_mapping.png
v3_case_overview_two_examples.png
v3_fabric_teacher_student_architecture.png
v3_dagm_teacher_student_architecture.png
v3_two_stage_dagm_training.png
v3_project_summary_closed_loop.png
```

当前 v4 使用的 FAL 图：

```text
v4_background_infographic.png
v4_methodology_overview.png
v4_hybrid_optical_architecture.png
v4_distillation_mechanism.png
v4_kernel_to_psf.png
v4_case_overview.png
v4_fabric_architecture.png
v4_dagm_architecture.png
v4_two_stage_training.png
v4_project_summary.png
v4_future_roadmap.png
```

说明：

- 脚本先读取环境变量 `FAL_KEY` / `FAL_API_KEY`
- 如果环境变量没有，则读取本机已有配置文件
- API key 不写入本项目仓库
- 每张图的 prompt 单独保存在 `presentation/ai_images/*.prompt.txt`

## 5. PPT 生成脚本

PPT v4 由固定版式脚本生成：

```bash
MPLCONFIGDIR=/private/tmp/mpl python3 presentation/scripts/build_ppt_v4.py
```

PPT v3 脚本：

```bash
MPLCONFIGDIR=/private/tmp/mpl python3 presentation/scripts/build_ppt_v3.py
```

PPT v2 脚本：

```bash
MPLCONFIGDIR=/private/tmp/mpl python3 presentation/scripts/build_ppt_v2.py
```

历史 v1 脚本：

```bash
python3 presentation/scripts/build_ppt.py
```

输出：

```text
presentation/build/metasurface_industrial_defect_detection_v2.pptx
presentation/build/metasurface_industrial_defect_detection_v3.pptx
presentation/build/metasurface_industrial_defect_detection_v4.pptx
```

版式原则：

- 16:9
- 白底或浅灰底
- 深蓝标题
- 标题下方细横线
- 中间 1 张主图 / 1 组规整图 / 1 张表
- 底部 1 行核心结论

## 6. v2 相比 v1 的主要修改

- 第一页改为标准文字封面，不再使用 AI 大图。
- 背景压缩为 1 页，并重新用 FAL 生成了论文级信息图，补充工业检测痛点、传统电子模型、超表面机会和本课题切入点。
- 方法论页增加传统工业视觉管线、光电融合架构、蒸馏机制和 kernel-to-PSF 公式。
- 新增方法总览页，使用 FAL 生成的 `v2_methodology_graphical_abstract.png` 展示传统模型、蒸馏、光学卷积和物理映射的完整链路。
- 公式统一用 matplotlib mathtext 渲染为透明 PNG，保存在 `presentation/generated_figures/formulas/`。
- Fabric 开头使用重新生成的 case-study infographic，并明确说明是织物 patch 二分类，不输出具体缺陷位置。
- DAGM 开头使用重新生成的 case-study infographic，并明确说明是工业纹理缺陷分类 + 像素级 mask 分割。
- Teacher / student 架构页重新绘制，明确光学前端和电子后端边界。
- 数据页保留 v1 中较好的真实结果图，但补充解释文字和表格。

## 7. v3 相比 v2 的主要修改

- 只要不是原始实验数据图，尽量改用 FAL 生成的完整论文级配图。
- 每页主体控制为 `1` 张大图或 `2` 张并排图，不再用大量文本框拼页面。
- 所有页面底部保留一句总结，用于汇报时快速收束该页观点。
- 新增 v3 FAL 图覆盖蒸馏机制、kernel-to-PSF、案例总览、Fabric 架构、DAGM 架构、两阶段训练和项目闭环。
- Fabric 和 DAGM 的真实 assets 全部尽量纳入 PPT，包括结果、threshold、kernel、PSF、probe、compute 和关键表格。

## 8. v4 相比 v3 的主要修改

- 重新生成了 11 张 FAL 图，允许少量准确英文短标签，避免完全无字导致画面奇怪。
- Prompt 中显式约束 Fabric 是 patch binary classification，DAGM 是 score + pixel mask segmentation。
- Prompt 中显式写入 Fabric R1 student 和 DAGM optical student 的关键模块，减少 AI 架构图乱画。
- 保持页面主体为 1 张大图或 2 张并排真实结果图，每页底部仍有一句总结。

## 9. 当前版本注意事项

- 这是一版可汇报的初稿，不是最终美化版。
- Fabric 主线使用 `R1 student best threshold F1=0.8571`。
- DAGM 主线使用 full validation `IoU=0.9145, Dice=0.9349`。
- Teacher 大权重没有推送到 GitHub，避免超过 GitHub 单文件限制。
- 后续如果要微调 PPT，优先改 `presentation/scripts/build_ppt_v4.py`，再重新生成。

## 10. 下一步建议

1. 人工快速翻一遍 PPT，检查中文标题和导师关注点。
2. 根据实际汇报时间删减或合并 2-3 页。
3. 如果需要更强视觉冲击，可以只重生封面和总体方案两张 AI 图。
4. 最后再导出 PDF 版用于汇报备份。
