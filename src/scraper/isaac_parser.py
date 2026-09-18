"""Parse item names and flavor text from a saved The Binding of Isaac wiki page.

The Isaac wiki has no usable API, so save the items page as HTML first and
point this at it.

Usage:
    uv run src/scraper/isaac_parser.py Items.html
"""

from pathlib import Path

from bs4 import BeautifulSoup

from base import build_scraper_parser, clean_text, output_path, write_unlabeled_csv

OUTPUT = output_path("unlabeled_isaac.csv")
MIN_WORDS = 3

NAME_COLUMN = 0
FLAVOR_COLUMN = 3


def parse_items(path: Path) -> list[str]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")

    phrases = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) <= FLAVOR_COLUMN:
            continue
        for index in (NAME_COLUMN, FLAVOR_COLUMN):
            text = clean_text(cells[index])
            if len(text.split()) >= MIN_WORDS:
                phrases.append(text)

    return list(dict.fromkeys(phrases))


def main():
    parser = build_scraper_parser(__doc__)
    parser.add_argument(
        "html_file",
        nargs="?",
        default="Items.html",
        type=Path,
        help="saved wiki page (default: Items.html)",
    )
    args = parser.parse_args()

    if not args.html_file.exists():
        raise SystemExit(f"{args.html_file} not found — save the wiki items page there first")

    print(f"Parsing {args.html_file}")
    phrases = parse_items(args.html_file)
    write_unlabeled_csv(OUTPUT, [(phrase, "isaac") for phrase in phrases])


if __name__ == "__main__":
    main()
