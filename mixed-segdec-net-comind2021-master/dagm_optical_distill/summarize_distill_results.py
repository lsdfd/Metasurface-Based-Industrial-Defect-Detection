import argparse
import json
import re
from pathlib import Path


METRIC_RE = re.compile(
    r"Validation AP=(?P<ap>[0-9.]+), AUC=(?P<auc>[0-9.]+), "
    r"IoU=(?P<iou>[0-9.]+), Dice=(?P<dice>[0-9.]+)"
)


def read_config(run_dir):
    path = run_dir / "distill_config.json"
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def summarize_run(run_dir):
    log_path = run_dir / "train.log"
    if not log_path.exists():
        return None

    best = None
    last = None
    for line in log_path.read_text(errors="replace").splitlines():
        match = METRIC_RE.search(line)
        if not match:
            continue
        metrics = {k: float(v) for k, v in match.groupdict().items()}
        last = metrics
        if best is None or metrics["dice"] > best["dice"]:
            best = metrics

    if best is None:
        return None

    cfg = read_config(run_dir)
    run_cfg = cfg.get("cfg", {})
    student = cfg.get("student", {})
    return {
        "run": run_dir.name,
        "input_size": run_cfg.get("INPUT_SIZE") or run_cfg.get("INPUT_WIDTH"),
        "optical_shape": student.get("optical_frontend", {}).get("weight_shape"),
        "downsample_factor": cfg.get("downsample_factor"),
        "total_params": student.get("total_params"),
        "best_ap": best["ap"],
        "best_auc": best["auc"],
        "best_iou": best["iou"],
        "best_dice": best["dice"],
        "last_dice": last["dice"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=Path("./results-dagm-distill-res/DAGM"))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    rows = []
    for run_dir in sorted(args.results_root.glob("*")):
        if not run_dir.is_dir():
            continue
        row = summarize_run(run_dir)
        if row is not None:
            rows.append(row)

    rows.sort(key=lambda x: x["best_dice"], reverse=True)
    header = "run,input_size,downsample_factor,total_params,best_ap,best_auc,best_iou,best_dice,last_dice,optical_shape"
    lines = [header]
    for row in rows:
        lines.append(
            ",".join(
                [
                    str(row["run"]),
                    str(row["input_size"]),
                    str(row["downsample_factor"]),
                    str(row["total_params"]),
                    f"{row['best_ap']:.5f}",
                    f"{row['best_auc']:.5f}",
                    f"{row['best_iou']:.5f}",
                    f"{row['best_dice']:.5f}",
                    f"{row['last_dice']:.5f}",
                    str(row["optical_shape"]),
                ]
            )
        )

    text = "\n".join(lines)
    print(text)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n")


if __name__ == "__main__":
    main()
