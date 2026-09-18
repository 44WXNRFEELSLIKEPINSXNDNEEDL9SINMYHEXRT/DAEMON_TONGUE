"""Scrape quotes from English Wikiquote.

Wikiquote runs the official Wikimedia API, which stays open to scripted clients
(unlike the Fandom wikis, which now answer 403). This is the working route to
Warhammer 40k, Diablo and gothic-literature material.

Usage:
    uv run src/scraper/wikiquote_parser.py
    uv run src/scraper/wikiquote_parser.py "H. P. Lovecraft" "John Milton"
"""

from bs4 import BeautifulSoup

from base import build_scraper_parser, clean_text, fetch_via_api, output_path, write_unlabeled_csv

API_URL = "https://en.wikiquote.org/w/api.php"

# Wikimedia rate-limits harder than the game wikis.
REQUEST_DELAY = 1.5

MIN_WORDS = 4
MAX_WORDS = 60

DEFAULT_PAGES = [
    "Warhammer 40,000",
    "Dark Souls",
    "Dark Souls III",
    "Elden Ring",
    "Bloodborne",
    "Darkest Dungeon",
    "Diablo III",
    "Diablo II",
    "H. P. Lovecraft",
    "Edgar Allan Poe",
    "John Milton",
    "Dante Alighieri",
]

OUTPUT = output_path("unlabeled_wikiquote.csv")


def extract_quotes(soup: BeautifulSoup) -> list[str]:
    """Take top-level list items; nested lists hold attribution, not the quote."""
    quotes = []
    for item in soup.select("div.mw-parser-output > ul > li"):
        for nested in item.find_all("ul"):
            nested.decompose()
        text = clean_text(item)
        if MIN_WORDS <= len(text.split()) <= MAX_WORDS:
            quotes.append(text)
    return list(dict.fromkeys(quotes))


def main():
    parser = build_scraper_parser(__doc__)
    parser.add_argument("pages", nargs="*", help="Wikiquote page titles (default: built-in list)")
    args = parser.parse_args()

    pages = args.pages or DEFAULT_PAGES
    print(f"Scraping {len(pages)} Wikiquote pages...")

    rows: list[tuple[str, str]] = []
    for page in pages:
        soup = fetch_via_api(API_URL, page, "wikiquote", delay=REQUEST_DELAY)
        if soup is None:
            continue
        quotes = extract_quotes(soup)
        print(f"     -> {len(quotes)} quotes")
        rows.extend((quote, f"wikiquote/{page}") for quote in quotes)

    write_unlabeled_csv(OUTPUT, rows)


if __name__ == "__main__":
    main()
