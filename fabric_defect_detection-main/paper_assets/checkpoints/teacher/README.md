# Teacher Checkpoint Note

`bigger_binary_F1_0.98.pth` 是 fabric 原始二分类 teacher 权重。

注意：

- 该文件实际大小约为 `104,320,383 bytes`。
- 这超过了 GitHub 单文件 `100 MB` 的硬限制，因此不应直接纳入 GitHub 仓库。
- 当前建议是仅在本地和服务器保留该权重，并在论文资产目录中保留本说明文件。

如果需要重新生成教师评估结果，可在有该权重的环境中运行：

```bash
python scripts/evaluation/export_paper_assets.py \
  --teacher-checkpoint models/bigger_binary_F1_0.98.pth
```
