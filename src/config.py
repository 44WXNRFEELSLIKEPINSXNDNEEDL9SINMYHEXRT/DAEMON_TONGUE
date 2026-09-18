"""Shared paths and constants for the whole pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
DATASET = DATA_DIR / "dataset.csv"
MODEL_DIR = ROOT / "DAEMON_TONGUE_JUDGE"

HF_REPO = "44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE_JUDGE"

MAX_LEN = 128
LABEL_NAMES = {0: "MORTAL", 1: "DAEMON"}
