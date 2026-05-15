# PPT 生成说明

更新时间：2026-05-16

当前第一版 PPT：

```text
presentation/build/metasurface_industrial_defect_detection_v1.pptx
```

页数：`31`

文件大小：约 `9.6 MB`

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
2-7    背景与总体方案
8-14   Fabric 二分类案例
15-27  DAGM / SegDecNet 案例
28-31  总结与未来展望
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
presentation/ai_images/
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

说明：

- 脚本先读取环境变量 `FAL_KEY` / `FAL_API_KEY`
- 如果环境变量没有，则读取本机已有配置文件
- API key 不写入本项目仓库
- 每张图的 prompt 单独保存在 `presentation/ai_images/*.prompt.txt`

## 5. PPT 生成脚本

PPT 由固定版式脚本生成：

```bash
python3 presentation/scripts/build_ppt.py
```

输出：

```text
presentation/build/metasurface_industrial_defect_detection_v1.pptx
```

版式原则：

- 16:9
- 白底或浅灰底
- 深蓝标题
- 标题下方细横线
- 中间 1 张主图 / 1 组规整图 / 1 张表
- 底部 1 行核心结论

## 6. 当前版本注意事项

- 这是一版可汇报的初稿，不是最终美化版。
- Fabric 主线使用 `R1 student best threshold F1=0.8571`。
- DAGM 主线使用 full validation `IoU=0.9145, Dice=0.9349`。
- Teacher 大权重没有推送到 GitHub，避免超过 GitHub 单文件限制。
- 后续如果要微调 PPT，优先改 `presentation/scripts/build_ppt.py`，再重新生成。

## 7. 下一步建议

1. 人工快速翻一遍 PPT，检查中文标题和导师关注点。
2. 根据实际汇报时间删减或合并 2-3 页。
3. 如果需要更强视觉冲击，可以只重生封面和总体方案两张 AI 图。
4. 最后再导出 PDF 版用于汇报备份。
