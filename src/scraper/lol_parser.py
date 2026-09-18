"""Scrape champion voice lines from the League of Legends fandom wiki.

Uses the MediaWiki API to bypass Cloudflare HTML protection.

Usage:
    uv run src/scraper/lol_parser.py                                # default roster
    uv run src/scraper/lol_parser.py Mordekaiser Kindred Nocturne   # specific champions
"""

from base import (
    build_scraper_parser,
    extract_phrases,
    fetch_via_api,
    output_path,
    write_unlabeled_csv,
)

API_URL = "https://leagueoflegends.fandom.com/api.php"

DEFAULT_CHAMPIONS = [
    "Mordekaiser", "Kindred", "Nocturne", "Viego", "Briar",
    "Naafiri", "Fiddlesticks", "Pyke", "Thresh", "Karthus",
    "Yorick", "Hecarim", "Warwick", "Vladimir", "Zed",
    "Shaco", "Senna", "Lucian", "Bel'Veth", "Kha'Zix",
    "Rengar", "Talon", "Cho'Gath", "Kog'Maw",
]

OUTPUT = output_path("unlabeled_lol.csv")


def main():
    parser = build_scraper_parser(__doc__)
    parser.add_argument("champions", nargs="*", help="champion names (default: built-in roster)")
    args = parser.parse_args()

    champions = args.champions or DEFAULT_CHAMPIONS
    print(f"Scraping {len(champions)} champions via MediaWiki API...")

    rows: list[tuple[str, str]] = []
    for champion in champions:
        soup = fetch_via_api(API_URL, f"{champion}/LoL/Audio")
        if soup is None:
            continue
        quotes = extract_phrases(soup, selectors=("li i",))
        print(f"  {champion}: {len(quotes)} phrases")
        rows.extend((quote, f"LoL/{champion}") for quote in quotes)

    write_unlabeled_csv(OUTPUT, rows)


if __name__ == "__main__":
    main()
