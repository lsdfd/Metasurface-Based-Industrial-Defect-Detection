import argparse
import os


def count_files(path):
    if not os.path.isdir(path):
        return 0
    return sum(1 for name in os.listdir(path) if os.path.isfile(os.path.join(path, name)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", default="./datasets/DAGM")
    args = parser.parse_args()

    if not os.path.isdir(args.dataset_path):
        raise SystemExit(f"Missing DAGM dataset directory: {args.dataset_path}")

    print(f"DAGM root: {args.dataset_path}")
    for class_id in range(1, 11):
        class_dir = os.path.join(args.dataset_path, f"Class{class_id}")
        train_dir = os.path.join(class_dir, "Train")
        test_dir = os.path.join(class_dir, "Test")
        train_label_dir = os.path.join(train_dir, "Label")
        test_label_dir = os.path.join(test_dir, "Label")

        print(
            f"Class{class_id}: "
            f"Train={count_files(train_dir)}, "
            f"Train/Label={count_files(train_label_dir)}, "
            f"Test={count_files(test_dir)}, "
            f"Test/Label={count_files(test_label_dir)}"
        )


if __name__ == "__main__":
    main()
