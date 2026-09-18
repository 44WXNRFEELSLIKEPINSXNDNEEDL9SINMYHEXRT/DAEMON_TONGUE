from text import normalize


def test_strips_punctuation_and_case():
    assert normalize("I can smile, and MURDER while I smile.") == (
        "i can smile and murder while i smile"
    )


def test_transliterates_non_ascii():
    assert normalize("Bel'Veth — the Void's empress") == "belveth the voids empress"


def test_collapses_surrounding_whitespace():
    assert normalize("  ...Rise from the grave!  ") == "rise from the grave"


def test_accepts_non_string_input():
    assert normalize(42) == "42"
