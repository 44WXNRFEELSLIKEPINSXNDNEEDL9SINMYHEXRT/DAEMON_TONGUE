"""Shared helpers for the wiki scrapers.

Every scraper follows the same shape: pull HTML (MediaWiki API or a saved file),
pick phrases out of it, write a staging CSV with columns phrase,label,source
for manual labeling.
"""

import argparse
import csv
import re
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA_DIR  # noqa: E402

HEADERS = {
    "User-Agent": "DAEMON_TONGUE/0.1 (dataset research; contact: local)",
    "Accept": "application/json",
}

TIMEOUT = 30
REQUEST_DELAY = 0.5
RETRY_BACKOFF = 10.0
MIN_WORDS = 3
SKIP_PREFIXES = ("http", "File:")


def output_path(filename: str) -> Path:
    return DATA_DIR / filename


def build_scraper_parser(description: str, *, local: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    if local:
        parser.add_argument(
            "--local",
            metavar="DIR",
            type=Path,
            help="parse saved *.html files from DIR instead of hitting the API",
        )
    return parser


def fetch_via_api(
    api_url: str,
    page: str,
    tag: str = "",
    delay: float = REQUEST_DELAY,
    retries: int = 2,
) -> BeautifulSoup | None:
    """Fetch a rendered wiki page through the MediaWiki API."""
    params = {
        "action": "parse",
        "page": page,
        "format": "json",
        "prop": "text",
        "disablelimitreport": True,
    }
    print(f"  API [{tag}]: {page}" if tag else f"  API: {page}")

    for attempt in range(retries + 1):
        try:
            resp = requests.get(api_url, params=params, headers=HEADERS, timeout=TIMEOUT)
        except requests.RequestException as e:
            print(f"  ! {page}: {e}")
            return None
        finally:
            time.sleep(delay)

        if resp.status_code != 429 or attempt == retries:
            break

        backoff = float(resp.headers.get("Retry-After", RETRY_BACKOFF))
        print(f"    rate limited, waiting {backoff:g}s")
        time.sleep(backoff)

    if resp.status_code == 403:
        print(f"  ! {page}: HTTP 403 — this wiki blocks API clients.")
        print("    Save the page from a browser and re-run with --local <dir>.")
        return None

    if resp.status_code == 429:
        print(f"  ! {page}: HTTP 429 — still rate limited after retries, skipping.")
        return None

    if resp.status_code != 200:
        print(f"  ! {page}: HTTP {resp.status_code}, skipping")
        return None

    try:
        data = resp.json()
    except ValueError:
        print(f"  ! {page}: response was not JSON, skipping")
        return None

    if "error" in data:
        print(f"  ! {page}: {data['error'].get('info', 'unknown error')}")
        return None

    html = data.get("parse", {}).get("text", {}).get("*")
    if not html:
        print(f"  ! {page}: no page content in response, skipping")
        return None

    return BeautifulSoup(html, "html.parser")


_WHITESPACE = re.compile(r"\s+")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?])")


def clean_text(node) -> str:
    # Separator is required: without it inline links fuse into their neighbours
    # ("nothing but" + "war" -> "nothing butwar").
    text = unidecode(node.get_text(" ", strip=True)).replace('"', "'")
    text = _WHITESPACE.sub(" ", text)
    return _SPACE_BEFORE_PUNCT.sub(r"\1", text).strip()


def extract_phrases(
    soup: BeautifulSoup,
    selectors: Sequence[str] = ("tr td",),
    min_words: int = MIN_WORDS,
) -> list[str]:
    phrases = []
    for selector in selectors:
        for node in soup.select(selector):
            text = clean_text(node)
            if len(text.split()) < min_words or text.startswith(SKIP_PREFIXES):
                continue
            phrases.append(text)
    return list(dict.fromkeys(phrases))


def parse_local_html(path: Path, selectors: Sequence[str] = ("tr td",)) -> list[str]:
    print(f"  local: {path.name}")
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    return extract_phrases(soup, selectors)


def write_unlabeled_csv(path: Path, rows: Sequence[tuple[str, str]]) -> None:
    """Merge scraped phrases into the staging file.

    Never clobbers: labels already entered by hand survive a re-scrape, and so
    do phrases from sources that have since started refusing API clients.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    merged: dict[str, dict[str, str]] = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                phrase = (row.get("phrase") or "").strip()
                if phrase:
                    merged[phrase.lower()] = {
                        "phrase": phrase,
                        "label": (row.get("label") or "").strip(),
                        "source": (row.get("source") or "").strip(),
                    }

    kept = len(merged)
    for phrase, source in rows:
        if phrase.lower() in merged:
            continue
        merged[phrase.lower()] = {"phrase": phrase, "label": "", "source": source}

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["phrase", "label", "source"])
        writer.writeheader()
        writer.writerows(merged.values())

    print(f"\n{len(merged) - kept} new phrases ({kept} kept) -> {path}")
    print(f"Label them (0 or 1), then merge: uv run src/merge_labeled.py {path}")
