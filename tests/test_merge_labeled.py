import csv

import pytest

import merge_labeled


def write_csv(path, rows, fields=("phrase", "label", "source")):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)
    return path


@pytest.fixture
def dataset(tmp_path, monkeypatch):
    path = tmp_path / "dataset.csv"
    monkeypatch.setattr(merge_labeled, "DATASET", path)
    return path


def test_collect_rows_keeps_only_labeled(tmp_path):
    staging = write_csv(tmp_path / "s.csv", [
        {"phrase": "Rise from the grave", "label": "1", "source": "isaac"},
        {"phrase": "Reusable ranged bomb", "label": "", "source": "isaac"},
        {"phrase": "Mass enemy damage", "label": "maybe", "source": "isaac"},
    ])

    rows, unlabeled, dupes = merge_labeled.collect_rows([staging], set())

    assert rows == [("Rise from the grave", "1", "isaac")]
    assert (unlabeled, dupes) == (2, 0)


def test_collect_rows_skips_existing_case_insensitively(tmp_path):
    staging = write_csv(tmp_path / "s.csv", [
        {"phrase": "None Can Escape Me", "label": "1", "source": "lol"},
    ])

    rows, _, dupes = merge_labeled.collect_rows([staging], {"none can escape me"})

    assert rows == []
    assert dupes == 1


def test_collect_rows_dedupes_within_the_batch(tmp_path):
    staging = write_csv(tmp_path / "s.csv", [
        {"phrase": "we all float down here", "label": "1", "source": "isaac"},
        {"phrase": "We All Float Down Here", "label": "1", "source": "isaac"},
    ])

    rows, _, dupes = merge_labeled.collect_rows([staging], set())

    assert len(rows) == 1
    assert dupes == 1


def test_collect_rows_falls_back_to_filename_as_source(tmp_path):
    staging = write_csv(
        tmp_path / "unlabeled_souls.csv",
        [{"phrase": "the abyss stares back", "label": "1"}],
        fields=("phrase", "label"),
    )

    rows, _, _ = merge_labeled.collect_rows([staging], set())

    assert rows == [("the abyss stares back", "1", "unlabeled_souls")]


def test_collect_rows_reports_missing_file(tmp_path):
    rows, unlabeled, dupes = merge_labeled.collect_rows([tmp_path / "nope.csv"], set())
    assert (rows, unlabeled, dupes) == ([], 0, 0)


def test_append_rows_writes_header_once(dataset):
    merge_labeled.append_rows([("first phrase here", "1", "lol")])
    merge_labeled.append_rows([("second phrase here", "0", "isaac")])

    with open(dataset, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert [row["phrase"] for row in rows] == ["first phrase here", "second phrase here"]
    assert rows[0]["source"] == "lol"


def test_load_existing_reads_back_appended_phrases(dataset):
    merge_labeled.append_rows([("None can escape me", "1", "lol")])
    assert merge_labeled.load_existing() == {"none can escape me"}
