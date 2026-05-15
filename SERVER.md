# GPU Server Notes

本文件只记录通用服务器工作流，不保存真实服务器地址、用户名或密码。

真实连接信息请放在本地私有文件中，例如：

```text
SERVER.local.md
```

该文件已被 `.gitignore` 忽略，不应提交到 GitHub。

## Login Template

```bash
ssh -p <PORT> -o StrictHostKeyChecking=no -l '<USER>' <HOST>
```

## Upload Project Template

远端没有 `rsync` 时，推荐本地打 tar 包再用 `scp` 上传：

```bash
tar \
  --exclude='**/outputs' \
  --exclude='**/results*' \
  --exclude='**/datasets/DAGM' \
  --exclude='*/__pycache__' \
  --exclude='*.pyc' \
  --exclude='**/.git' \
  -czf /tmp/project_payload.tgz \
  <PROJECT_DIR>
```

```bash
scp -P <PORT> \
  -o StrictHostKeyChecking=no \
  -o User='<USER>' \
  /tmp/project_payload.tgz \
  <HOST>:<REMOTE_PATH>/project_payload.tgz
```

## Sync Principle

- 本地负责代码整理、README 和实验记录。
- 服务器负责正式训练和长时间评估。
- 数据集、checkpoint、`results-*` 和 `outputs/` 默认不纳入 git。
- 需要共享的结果应导出为小型 `json/png/csv/md` 后再提交。
