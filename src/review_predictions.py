"""Predict unlabeled scraped phrases and extract high-confidence results for review.

Usage:
    uv run src/review_predictions.py                        # default: confidence >= 0.90
    uv run src/review_predictions.py --threshold 0.95
    uv run src/review_predictions.py data/unlabeled_lol.csv
"""

import argparse
import csv
from pathlib import Path

from config import DATA_DIR
from predict import predict

DEFAULT_FILES = [
    DATA_DIR / "unlabeled_lol.csv",
    DATA_DIR / "unlabeled_souls.csv",
    DATA_DIR / "unlabeled_misc.csv",
    DATA_DIR / "unlabeled_isaac.csv",
    DATA_DIR / "unlabeled_wikiquote.csv",
]
OUTPUT = DATA_DIR / "high_confidence_review.csv"
FIELDS = ["phrase", "label", "confidence", "source"]


def load_phrases(path: Path) -> list[tuple[str, str]]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            phrase = (row.get("phrase") or "").strip()
            if phrase:
                rows.append((phrase, row.get("source") or path.stem))
    return rows


def filter_high_confidence(
    results: list[dict],
    sources: list[str],
    threshold: float,
) -> list[dict]:
    return [
        {**result, "source": source}
        for result, source in zip(results, sources, strict=True)
        if result["confidence"] >= threshold
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path, help="staging CSVs (default: all)")
    parser.add_argument("--threshold", type=float, default=0.90, help="min confidence (0.90)")
    args = parser.parse_args()

    files = args.files or [f for f in DEFAULT_FILES if f.exists()]
    if not files:
        print("No unlabeled CSVs found. Run the scrapers first.")
        return

    all_phrases: list[tuple[str, str]] = []
    for path in files:
        if not path.exists():
            print(f"  ! {path} not found, skipping")
            continue
        rows = load_phrases(path)
        print(f"  {path.name}: {len(rows)} phrases")
        all_phrases.extend(rows)

    if not all_phrases:
        print("Nothing to predict.")
        return

    print(f"\nPredicting {len(all_phrases)} phrases...")
    phrases = [p for p, _ in all_phrases]
    sources = [s for _, s in all_phrases]
    results = predict(phrases, batch_size=64)

    high_conf = filter_high_confidence(results, sources, args.threshold)
    daemon_count = sum(1 for row in high_conf if row["label"] == 1)

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(high_conf)

    print(f"\nResults (confidence >= {args.threshold}):")
    print(f"  total predicted:  {len(results)}")
    print(f"  high confidence:  {len(high_conf)}")
    print(f"    DAEMON (1):     {daemon_count}")
    print(f"    MORTAL (0):     {len(high_conf) - daemon_count}")
    print(f"  below threshold:  {len(results) - len(high_conf)}")
    print(f"\nReview file -> {OUTPUT}")
    print("  Check the labels, fix any wrong ones, then merge:")
    print(f"  uv run src/merge_labeled.py {OUTPUT}")


if __name__ == "__main__":
    main()
