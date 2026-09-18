"""Merge labeled staging CSVs into the main dataset.

Reads each file, keeps only rows with a valid label (0 or 1), appends them to
data/dataset.csv (deduped by phrase), and reports counts.

Usage:
    uv run src/merge_labeled.py data/unlabeled_lol.csv data/unlabeled_souls.csv
    uv run src/merge_labeled.py data/high_confidence_review.csv --semantic-dedup
"""

import argparse
import csv
from pathlib import Path

from config import DATASET

FIELDS = ["phrase", "label", "source"]


def read_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_existing() -> set[str]:
    if not DATASET.exists():
        return set()
    return {(row.get("phrase") or "").strip().lower() for row in read_rows(DATASET)}


def collect_rows(
    files: list[Path],
    existing: set[str],
) -> tuple[list[tuple[str, str, str]], int, int]:
    """Return (new_rows, skipped_unlabeled, skipped_dupes)."""
    new_rows: list[tuple[str, str, str]] = []
    skipped_unlabeled = 0
    skipped_dupes = 0
    seen = set(existing)

    for path in files:
        if not path.exists():
            print(f"  ! {path} not found, skipping")
            continue

        for row in read_rows(path):
            phrase = (row.get("phrase") or "").strip()
            label = (row.get("label") or "").strip()
            source = (row.get("source") or path.stem).strip() or path.stem

            if not phrase:
                continue
            if label not in ("0", "1"):
                skipped_unlabeled += 1
                continue
            if phrase.lower() in seen:
                skipped_dupes += 1
                continue

            new_rows.append((phrase, label, source))
            seen.add(phrase.lower())

    return new_rows, skipped_unlabeled, skipped_dupes


def append_rows(rows: list[tuple[str, str, str]]) -> None:
    write_header = not DATASET.exists()
    DATASET.parent.mkdir(parents=True, exist_ok=True)
    with open(DATASET, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(FIELDS)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="labeled staging CSVs")
    parser.add_argument(
        "--semantic-dedup",
        action="store_true",
        help="also drop near-duplicate phrasings (needs: uv sync --extra dedup)",
    )
    args = parser.parse_args()

    new_rows, skipped_unlabeled, skipped_dupes = collect_rows(args.files, load_existing())

    dropped_similar = 0
    if new_rows and args.semantic_dedup:
        from dedup import drop_near_duplicates

        new_rows, dropped_similar = drop_near_duplicates(new_rows)

    if not new_rows:
        print(f"Nothing to merge. ({skipped_unlabeled} unlabeled, {skipped_dupes} dupes)")
        return

    append_rows(new_rows)

    print(f"Merged {len(new_rows)} new phrases -> {DATASET}")
    print(f"  skipped: {skipped_unlabeled} unlabeled, {skipped_dupes} duplicates")
    if args.semantic_dedup:
        print(f"  dropped: {dropped_similar} near-duplicates")
    print(f"  dataset total: {len(read_rows(DATASET))}")


if __name__ == "__main__":
    main()
