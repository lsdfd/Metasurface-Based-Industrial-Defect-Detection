# Server Notes

本文件记录 GPU 服务器使用模板，不保存真实服务器地址、用户名或密码。

真实连接信息请放在不进 git 的本地文件中，例如：

```text
SERVER.local.md
.env.local
```

## Login Template

```bash
ssh -p <PORT> -o StrictHostKeyChecking=no -l '<USER>' <HOST>
```

## Upload Template

远端没有 `rsync` 时，可先打 tar 包再 `scp`：

```bash
tar \
  --exclude='fabric_defect_detection-main/outputs' \
  --exclude='fabric_defect_detection-main/data/aitex' \
  --exclude='fabric_defect_detection-main/models/*.pth' \
  --exclude='*/__pycache__' \
  --exclude='*.pyc' \
  --exclude='fabric_defect_detection-main/.git' \
  -czf /tmp/fabric_gpu_payload.tgz \
  fabric_defect_detection-main
```

```bash
scp -P <PORT> \
  -o StrictHostKeyChecking=no \
  -o User='<USER>' \
  /tmp/fabric_gpu_payload.tgz \
  <HOST>:<REMOTE_PATH>/fabric_gpu_payload.tgz
```

## Typical Runs

二分类 notebook 复现：

```bash
python scripts/reproduction/reproduce_binary_patch_notebook.py \
  --epochs 50 \
  --batch-size 16 \
  --lr 0.001 \
  --num-workers 2 \
  --output-dir outputs/gpu_50ep
```

U-Net 训练：

```bash
python scripts/training/train_unet.py \
  --epochs 100 \
  --batch-size 4 \
  --lr 0.001 \
  --num-workers 2 \
  --output-dir outputs/unet_repro_100ep
```

## Sync Principle

- 本地负责代码整理与实验组织。
- 服务器负责正式训练和长时间评估。
- `outputs/` 默认不纳入 git。
- 真正需要共享的结果，导出为小型 `json/png/csv` 再同步回仓库。
