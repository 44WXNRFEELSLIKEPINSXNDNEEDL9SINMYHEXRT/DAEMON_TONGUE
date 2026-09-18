"""Text normalization shared by training and inference.

Training and inference must apply the same transform, otherwise the model sees
punctuation and casing at train time that inference strips away.
"""

import re

from unidecode import unidecode

_PUNCTUATION = re.compile(r"[^\w\s]")
_WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    # Whitespace is collapsed after stripping punctuation: a removed dash would
    # otherwise leave a double space, which RoBERTa tokenizes as its own token.
    stripped = _PUNCTUATION.sub("", unidecode(str(text)))
    return _WHITESPACE.sub(" ", stripped).lower().strip()
