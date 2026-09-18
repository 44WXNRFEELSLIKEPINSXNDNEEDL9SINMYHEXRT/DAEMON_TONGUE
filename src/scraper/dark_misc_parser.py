"""Scrape quotes/descriptions from Darkest Dungeon, Bloodborne, Blasphemous wikis.

Fandom and Fextralife both run MediaWiki, so the API works for all of them.

Usage:
    uv run src/scraper/dark_misc_parser.py
    uv run src/scraper/dark_misc_parser.py --local dir_with_saved_html/
"""

from base import (
    build_scraper_parser,
    extract_phrases,
    fetch_via_api,
    output_path,
    parse_local_html,
    write_unlabeled_csv,
)

SELECTORS = ("tr td", "blockquote", "i")

SOURCES = {
    "bloodborne": {
        "api": "https://bloodborne.wiki.fextralife.com/api.php",
        "pages": ["Weapons", "Armor", "Consumables", "Caryll Runes", "Items", "Tools"],
    },
    # Fandom answers 403 to API clients; reachable only via --local saved HTML.
    "darkestdungeon": {
        "api": "https://darkestdungeon.fandom.com/api.php",
        "pages": ["Narrator", "Quotes", "Curios"],
    },
}

OUTPUT = output_path("unlabeled_misc.csv")


def main():
    parser = build_scraper_parser(__doc__, local=True)
    args = parser.parse_args()

    rows: list[tuple[str, str]] = []

    if args.local and args.local.is_dir():
        print(f"Parsing local HTML files from {args.local}/")
        for html_file in sorted(args.local.glob("*.html")):
            game = html_file.stem.split("_")[0] if "_" in html_file.stem else "misc"
            rows.extend((phrase, game) for phrase in parse_local_html(html_file, SELECTORS))
    else:
        print("Fetching via MediaWiki API...")
        for game, cfg in SOURCES.items():
            for page in cfg["pages"]:
                soup = fetch_via_api(cfg["api"], page, game)
                if soup is None:
                    continue
                rows.extend((phrase, game) for phrase in extract_phrases(soup, SELECTORS))

    write_unlabeled_csv(OUTPUT, rows)


if __name__ == "__main__":
    main()
