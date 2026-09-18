"""Push the trained model to the HuggingFace Hub.

Every push is stamped with the dataset fingerprint it was trained on, so a
model on the Hub can be traced back to its data.

Usage:
    uv run src/push.py
    uv run src/push.py --tag v2          # also create a rollback tag
"""

import argparse
import csv
import hashlib

from huggingface_hub import HfApi

from config import DATASET, HF_REPO, MODEL_DIR


def dataset_fingerprint() -> tuple[str, int]:
    if not DATASET.exists():
        return "unknown", 0
    digest = hashlib.sha256(DATASET.read_bytes()).hexdigest()[:12]
    with open(DATASET, newline="", encoding="utf-8") as f:
        rows = sum(1 for _ in csv.DictReader(f))
    return digest, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="create this tag on the Hub after uploading")
    args = parser.parse_args()

    if not MODEL_DIR.exists():
        raise SystemExit(f"{MODEL_DIR} not found. Train it first: uv run src/train.py")

    digest, rows = dataset_fingerprint()
    message = f"Model trained on dataset {digest} ({rows} phrases)"

    api = HfApi()
    api.create_repo(HF_REPO, exist_ok=True)
    api.upload_folder(folder_path=str(MODEL_DIR), repo_id=HF_REPO, commit_message=message)

    if args.tag:
        api.create_tag(HF_REPO, tag=args.tag, exist_ok=True)
        print(f"Tagged {args.tag}")

    print(f"Pushed to huggingface.co/{HF_REPO}")
    print(f"  {message}")


if __name__ == "__main__":
    main()
