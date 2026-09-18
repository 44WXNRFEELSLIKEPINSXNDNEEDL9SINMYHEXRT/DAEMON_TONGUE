import csv

from review_predictions import filter_high_confidence, load_phrases


def test_filter_keeps_only_confident_rows_and_attaches_source():
    results = [
        {"phrase": "the blood of the fallen", "label": 1, "confidence": 0.94},
        {"phrase": "reusable ranged bomb", "label": 0, "confidence": 0.51},
    ]

    kept = filter_high_confidence(results, ["lol", "isaac"], threshold=0.90)

    assert kept == [
        {"phrase": "the blood of the fallen", "label": 1, "confidence": 0.94, "source": "lol"}
    ]


def test_filter_is_inclusive_at_the_threshold():
    results = [{"phrase": "exactly at the line", "label": 1, "confidence": 0.90}]
    assert len(filter_high_confidence(results, ["lol"], threshold=0.90)) == 1


def test_load_phrases_skips_blank_rows_and_defaults_source(tmp_path):
    path = tmp_path / "unlabeled_lol.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["phrase", "label"])
        writer.writeheader()
        writer.writerows([
            {"phrase": "None can escape me", "label": ""},
            {"phrase": "", "label": ""},
        ])

    assert load_phrases(path) == [("None can escape me", "unlabeled_lol")]
