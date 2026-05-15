# 数据集目录

当前清理后的主线只使用 DAGM 2007 Class7。

## 下载地址

DAGM 2007 Competition Dataset, Optical Inspection:

```text
https://www.kaggle.com/datasets/mhskjelvareid/dagm-2007-competition-dataset-optical-inspection
```

## 期望目录

最小可复现目录：

```text
datasets/DAGM/
  Class7/
    Train/
    Test/
```

如果下载的是完整数据集，也可以保留：

```text
datasets/DAGM/
  Class1/
  Class2/
  ...
  Class10/
```

当前脚本通过 `FOLD=7` 使用 `Class7`。

## 检查数据

在项目根目录运行：

```bash
python3 dagm_optical_distill/check_dagm_dataset.py --DATASET_PATH ./datasets/DAGM
```

## 说明

早期 KSDD/KSDD2 探索路线已经清理。当前 README 不再提供 KSDD/KSDD2 下载和复现步骤。
