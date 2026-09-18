import csv

import responses
from bs4 import BeautifulSoup

from base import clean_text, extract_phrases, fetch_via_api, write_unlabeled_csv

API = "https://example.wiki/api.php"


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_clean_text_keeps_words_apart_across_inline_tags():
    node = soup("<li>there is nothing but <a href='/war'>war</a>.</li>").li
    assert clean_text(node) == "there is nothing but war."


def test_extract_phrases_applies_selector_and_min_words():
    html = "<table><tr><td>Rise from the grave</td><td>too short</td></tr></table>"
    assert extract_phrases(soup(html)) == ["Rise from the grave"]


def test_extract_phrases_skips_links_and_files():
    html = "<table><tr><td>https://example.com/a/b</td><td>File: some image here</td></tr></table>"
    assert extract_phrases(soup(html)) == []


def test_extract_phrases_dedupes_preserving_order():
    html = (
        "<table><tr><td>we all float down here</td>"
        "<td>rise from the grave</td>"
        "<td>we all float down here</td></tr></table>"
    )
    assert extract_phrases(soup(html)) == ["we all float down here", "rise from the grave"]


def test_extract_phrases_honours_custom_selectors():
    html = (
        "<ul><li><i>Gods and mortals, they deserve only death</i></li></ul>"
        "<i>bare italics here</i>"
    )
    assert extract_phrases(soup(html), selectors=("li i",)) == [
        "Gods and mortals, they deserve only death"
    ]


def test_write_unlabeled_csv_round_trip(tmp_path):
    out = tmp_path / "staging.csv"
    write_unlabeled_csv(out, [("None can escape me", "LoL/Mordekaiser")])

    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows == [{"phrase": "None can escape me", "label": "", "source": "LoL/Mordekaiser"}]


def test_write_unlabeled_csv_keeps_existing_labels_and_rows(tmp_path):
    out = tmp_path / "staging.csv"
    write_unlabeled_csv(out, [("None can escape me", "LoL/Mordekaiser")])

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["phrase", "label", "source"])
        writer.writeheader()
        writer.writerow({"phrase": "None can escape me", "label": "1", "source": "LoL/Mordekaiser"})

    write_unlabeled_csv(out, [("the abyss stares back", "souls")])

    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows[0] == {"phrase": "None can escape me", "label": "1", "source": "LoL/Mordekaiser"}
    assert rows[1] == {"phrase": "the abyss stares back", "label": "", "source": "souls"}


def test_write_unlabeled_csv_does_not_duplicate_on_rescrape(tmp_path):
    out = tmp_path / "staging.csv"
    write_unlabeled_csv(out, [("None can escape me", "LoL/Mordekaiser")])
    write_unlabeled_csv(out, [("none CAN escape ME", "LoL/Mordekaiser")])

    with open(out, newline="", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 1


@responses.activate
def test_fetch_via_api_returns_parsed_html():
    responses.add(
        responses.GET,
        API,
        json={"parse": {"text": {"*": "<table><tr><td>the abyss stares back</td></tr></table>"}}},
    )
    assert extract_phrases(fetch_via_api(API, "Page", delay=0)) == ["the abyss stares back"]


@responses.activate
def test_fetch_via_api_handles_blocked_wiki():
    responses.add(responses.GET, API, status=403)
    assert fetch_via_api(API, "Page", delay=0) is None


@responses.activate
def test_fetch_via_api_handles_mediawiki_error_payload():
    responses.add(responses.GET, API, json={"error": {"code": "missingtitle", "info": "gone"}})
    assert fetch_via_api(API, "Page", delay=0) is None


@responses.activate
def test_fetch_via_api_handles_non_json_response():
    responses.add(responses.GET, API, body="<html>nope</html>", content_type="text/html")
    assert fetch_via_api(API, "Page", delay=0) is None
