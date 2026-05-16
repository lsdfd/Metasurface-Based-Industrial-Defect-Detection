# AGENTS.md

这个文件是 Codex 在本课题目录里的长期工作记忆。每次修改代码、写实验、提出研究路线前，都应该先读这里。

## 项目范围

当前重点：先把 `fabric_defect_detection-main` 当作第一版可复现 demo 和算法沙盒。

除非用户明确要求，不要把当前工作发散到 DeepPCB、VisA、MVTec、YOLO 或其他工业数据集。那些可以是未来方向，但这个文件夹近期先围绕已有 fabric 缺陷检测例子推进。

高层研究目标：面向 fabric 缺陷检测，构建一个“任务蒸馏的超表面光学视觉前端”。目标系统不是全光学检测器，而是光电混合模型：

- 光学前端：受物理约束的 CNN-like 卷积/PSF 特征编码器；
- 电子后端：小型全连接网络或轻量非线性 head；
- 训练方法：从更强的电子 teacher 网络做 teacher-student 蒸馏；
- 硬件映射：把蒸馏得到的卷积核映射成超表面 PSF/相位设计。

## 目录结构

- `fabric_defect_detection-main/`
  - 当前可执行基线。
  - AITEX fabric 数据已经在目录中。
  - 包含二分类 patch classifier 和 U-Net 分割 notebook。
  - `deploy/` 下有 Streamlit 推理 UI。
- `reference-papers/`
  - 光学卷积、知识蒸馏、NTKD、RGB/多色超表面光学编码器和补充材料的核心文献。
  - 实现蒸馏或超表面映射前，要认真读这些材料。
- `kernel-to-metasurface-phase-design/`
  - PSF-engineered meta-optics 设计的 TensorFlow notebook。
  - 后续把 learned kernels 映射到超表面结构时，优先参考这个实现。
- `project-background/`
  - 项目构想和 demo 方案文档。

## 当前基线：Fabric Defect Detection

已有 fabric 项目使用 AITEX 数据集。基线流程是：

1. 把整张 fabric 图 resize 到 `256 x 4096`。
2. 切成 16 个 `256 x 256` patch。
3. 做直方图均衡/归一化。
4. 训练 binary patch classifier 判断 defect/no-defect。
5. 对判定为 defective 的 patch 再运行 U-Net 分割。

重要文件：

- `fabric_defect_detection-main/README.md`：原项目说明和 setup。
- `fabric_defect_detection-main/train/binary_patch_classification.ipynb`：二分类训练。
- `fabric_defect_detection-main/train/unet_segmentation.ipynb`：分割训练。
- `fabric_defect_detection-main/train/model_architectures.py`：训练侧模型定义。
- `fabric_defect_detection-main/train/utilities.py`：AITEX dataset 和 patching 工具。
- `fabric_defect_detection-main/deploy/models.py`：部署侧 classifier 和 U-Net 定义。
- `fabric_defect_detection-main/deploy/utils.py`：推理侧 patching/classification/segmentation 辅助函数。

已知基线注意事项：

- 这个 repo 偏 notebook/demo 风格，还不是干净的可复现实验包。
- `requirements.txt` 里有平台相关 pin，macOS 上直接安装要谨慎。
- `train/utilities.py` 中有 Windows 路径拆分痕迹，比如 `split("\\")`，在 macOS/Linux 上可能需要修正。
- 分割模型文件 `unet_seg_200epoch.pt` 由 `get_models.py` 从 Google Drive 下载，可能需要网络权限。
- 在基线复现和记录清楚前，避免大规模重构。

## 第一版执行计划：CNN 二分类蒸馏

用户已经明确：第一版先只做 fabric patch 的 CNN 二分类蒸馏，不做分割、不做 heatmap、不发散到其他数据集。

1. Teacher 固定使用 fabric 原项目的二分类 CNN。
   - 也就是 `BinaryClassifier`，对应 `models/bigger_binary_F1_0.98.pth`。
   - 不要第一版另起炉灶训练复杂 teacher。
   - 可以把原 notebook 中的 teacher 训练/评估流程整理成脚本，但 teacher 架构沿用原项目。

2. 标准化项目结构，避免后续继续被零散 notebook 牵着走。
   - 原 notebook 保留，不要贸然删除。
   - 新增清晰的 Python package/scripts 承载后续主线。
   - 目标脚本链路是：数据加载 -> teacher 评估 -> student baseline -> KD 蒸馏 -> 导出 student kernels。

3. 设计“光学前端 CNN + 电子后端 FN/FC”student。
   - 光学前端模拟一个小型 convolution bank，后续能对应到 PSF。
   - 电子后端保持轻量，大概率是 flatten/pooling 加一到两层全连接。
   - student 第一版必须是“一层 CNN/optical convolution frontend”。
   - 不要过早拍死 student 结构。卷积核数量、kernel size、feature map 尺寸、后端宽度都要实验比较。
   - student 架构设计要重点参考文献，而不是为了分数随便堆网络。

4. 根据参考文献写蒸馏算法。
   - 第一版重点是 classic KD：teacher output/logit/probability 蒸馏到一层 CNN student。
   - student 建议是 `OpticalConvBank + small electronic backend`。
   - 蒸馏代码要仔细参考文献实现，尤其是补充材料中的结构、损失和校准细节。
   - 训练时分别记录 task loss 和 distillation loss；当前目标是让 validation/test loss 尽量小，并和原 baseline 对比。

5. 蒸馏后小模型如果效果不错，再进入超表面结构设计。
   - 使用 student 这一层 CNN 的 learned kernels。
   - 第一版尽量沿用参考文献和补充材料里的相位恢复/PSF 工程方法。
   - 使用蒸馏得到的 CNN kernels 作为目标 PSF/kernels。
   - 适配 `kernel-to-metasurface-phase-design/TF_for_PSF_Engineering_CIFAR.ipynb` 到 fabric student kernels。
   - 这里非常依赖 `reference-papers/补充材料.pdf`，包括 positive/negative split、PSF enlargement、angular spectrum propagation、scatterer width-phase proxy、calibration 等细节。
   - 参考文献中能复用的地方尽量复用，但必须结合 fabric 场景调整，不要机械照搬。

## 参考工作要点

参考文献要直接指导实现决策。

RGB/多色 optical encoder 论文和补充材料的关键点：

- 用知识蒸馏把较大的电子 CNN 压缩成单卷积层 student 加小型电子后端。
- 参考 CIFAR 设置中使用 16 个 `7 x 7` kernels，并涉及 RGB 通道和正负 kernel 拆分。
- 光强不能直接表示负权重，所以需要把每个 learned kernel 拆成 positive 和 negative 两部分，后端再做数字相减。
- 多色超表面可以在 RGB 波长下产生不同 PSF，但同一个 scatterer geometry 会耦合不同波长下的相位响应。
- 超表面设计的核心是优化 scatterer widths，使模拟 PSF 尽量匹配目标 digital kernels。
- 补充材料中使用/讨论了：
  - RGB 波长约为 635 nm、532 nm、450 nm；
  - 石英基底上的氮化硅柱；
  - scatterer width 到 phase 的 proxy/lookup 关系；
  - angular spectrum propagation；
  - Adam 优化；
  - CIFAR case 中 PSF enlargement factor 为 2；
  - 16 个 positive kernels 和 16 个 negative kernels，总共 32 个 meta-optics。
- calibration 很关键。参考工作在 optical output 和 digital backend 之间加入 calibration layer，用于补偿缩放、平移、旋转、光学噪声、制造误差和测量 mismatch。
- 如果 calibration layer 和后续 FC layer 之间没有非线性，线性 calibration layer 可以和后续 FC layer 合并。

NTKD 参考文献的关键点：

- 标准 KD 主要匹配 teacher/student 的 softened outputs。
- NTKD 额外匹配 teacher 和 student 的 neural tangent kernel，或其近似形式。
- 这个思路对本课题尤其相关，因为光学前端大多是线性且受物理约束的。
- NTKD 可以用于两个阶段：
  - 制造前：帮助 optical student 从电子 teacher 学习；
  - 制造后：冻结光学前端，微调数字后端/calibration 来补偿物理误差。
- 完整 NTK/Jacobian 计算可能非常耗显存。文献讨论了 trace-style approximation 等近似策略。不要在未评估可行性前直接实现巨大的 full-Jacobian 方法。

## 蒸馏实现偏好

先简单，再加复杂。

推荐顺序：

1. 无蒸馏 student baseline：
   - `OpticalConvBank -> pooling/flatten -> FC -> output`
   - 先和原 binary classifier 在 fabric patch classification 上对比。

2. Classic KD：
   - 用 teacher logits/probabilities 监督 student logits。
   - 对 binary classification，可用 BCE task loss 加 KL/BCE 风格 soft target loss，并根据需要引入 temperature。
   - 明确记录 alpha 和 temperature 设置。

3. Feature/heatmap distillation：
   - 第一版暂不做。
   - 后续如果进入 segmentation 或 localization，再蒸馏 teacher masks、soft heatmaps 或浅层 feature maps。

4. NTKD-style loss：
   - 第一版暂不做。
   - 等 classic KD 二分类 baseline 跑通后再做。
   - batch 保持小，先验证显存/内存开销。
   - full Jacobian 太重时，优先考虑近似 NTK similarity。

不要把 student 架构过拟合到参考 CIFAR 设置。Fabric 图像当前是灰度 patch-based 场景，因此 RGB 相关部分第一版可能改为 single-channel。正负核拆分和 PSF 约束后续仍然重要。

## 超表面映射计划

当蒸馏 student kernels 准备好后：

1. 以 `.npy` 等干净格式导出 learned kernels，并记录 shape。
2. 归一化 kernels，并拆分 positive/negative target PSFs。
3. 判断第一版 fabric 是走灰度/单波长路线，还是沿用 RGB/多色代码路径。
4. 适配 TensorFlow PSF engineering notebook：
   - 把 CIFAR kernel loading 替换为导出的 fabric kernels；
   - 更新 kernel 数量、kernel size、target PSF size、padding 和 scale/enlargement factor；
   - 保留 angular spectrum propagation 和 scatterer width optimization 逻辑；
   - 保存 phase/width/radius arrays 和 simulated PSF 对比图。
5. 用清晰指标和可视化比较 target kernels 与 simulated PSFs。

后续要重新思考的开放问题：

- Fabric defect detection 需要多少个 optical kernels：4、8、16，还是更多？
- Kernel size 是沿用参考 `7 x 7`，还是为了纹理/缺陷敏感性使用更大 kernel 或 multi-scale kernels？
- Student 输出做 binary OK/NG、defect heatmap，还是 patch-level segmentation？
- 第一版用 grayscale single-wavelength，还是直接适配完整 RGB/polychromatic metasurface 设计？
- 是否在 simulated optical training 阶段就加入 calibration layer？

## 编码风格和工作流

- 默认用中文和用户沟通；代码命名和注释可以用英文。
- 新实验优先做成可复现脚本，即使原 repo 主要用 notebooks。
- notebooks 要保持可用，但不要把所有新逻辑只写在 notebook 里。
- 增加小而聚焦的模块，避免大规模重构。
- 改训练行为前，先明确 baseline metric 和预期对比。
- 实验输出如有需要可放到清晰的新目录，例如 `experiments/` 或 `outputs/`；不要无理由把生成文件混进源码目录。
- 除非用户要求，不要提交或依赖大型二进制模型文件。
- 搜索代码优先用 `rg` / `rg --files`。
- 手动改文件优先用 `apply_patch`。

## 验证清单

复现 baseline 时：

- 环境能 import 所需包。
- AITEX 数据路径在 macOS 上能正常解析。
- 小型 dataloader smoke test 能跑通。
- Binary classifier 至少能跑一个训练/评估 step。
- Segmentation model 能对一个 patch forward pass。
- Streamlit inference 等模型文件齐全后再作为可选项。

做蒸馏时：

- 记录 teacher checkpoint/weights 和 metrics。
- 打印或保存 student architecture。
- 固定并记录 train/validation split。
- 分别记录各个 loss component。
- 对比 baseline student、KD student，后续再对比 NTKD student。

做超表面设计时：

- 导出的 kernels 能被 PSF design code 加载。
- positive/negative decomposition 有可视化检查。
- simulated PSFs 和 target PSFs 有对比图与指标。
- phase/width 物理约束有记录。

## 重要表述

表述要谨慎：

- 推荐说法：`metasurface optical frontend`、`optical convolution bank`、`PSF-engineered optical encoder`、`hybrid optical-electronic defect detection`。
- 避免说法：`超表面实现完整神经网络`、`all-optical YOLO`、`硬件完全替代 detector`。

本项目的核心是把最早期、昂贵、高分辨率的特征提取前移到成像链路中完成，再用小型电子后端负责非线性决策。
