# DAEMON_TONGUE

A classifier for aesthethic grimdark phrases

## What it does
Classifies phrases by aesthetic tone: "DAEMON" (dark, poetic, fatalistic) vs "MORTAL" (clean).

## Quickstart
uv sync        # installs everything exactly, no surprises
uv run train.py

## Training your own
python src/train.py

## Dataset
1000+ (09.06.26) manually labeled phrases. Label 1 = grimdark aesthetic.