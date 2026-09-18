import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for path in (ROOT / "src", ROOT / "src" / "scraper"):
    sys.path.insert(0, str(path))
