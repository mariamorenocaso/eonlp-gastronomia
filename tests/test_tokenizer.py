import pytest

from eonlp import Tokenizer, normalize_x_system
from eonlp.tokenizer import sentence_starts

tok = Tokenizer()


def texts(s):
    return [t for t, _ in tok(s)]


def test_words_and_punctuation():
    assert texts("Mi ŝatas manĝi kukon.") == ["Mi", "ŝatas", "manĝi", "kukon", "."]


def test_numbers_are_kept():
    assert texts("En 1950 ĝi kostis 5,50 €.") == ["En", "1950", "ĝi", "kostis", "5,50", "€", "."]


def test_hyphenated_compound_is_one_token():
    assert "ĉokolad-kuko" in texts("La ĉokolad-kuko estas bona.")


@pytest.mark.parametrize("text, expected", [
    ("de l' mondo", ["de", "l'", "mondo"]),
    ("l'akvo", ["l'", "akvo"]),
    ("en la dom' de mia patro", ["en", "la", "dom'", "de", "mia", "patro"]),
])
def test_elision(text, expected):
    assert texts(text) == expected


def test_offsets_point_to_the_original_text():
    s = "La kafo, la teo."
    for t, i in tok(s):
        assert s[i:i + len(t)] == t


def test_ellipsis_is_one_token():
    assert texts("Nu...") == ["Nu", "..."]


def test_empty_text():
    assert tok("") == []


@pytest.mark.parametrize("raw, expected", [
    ("cxokolado", "ĉokolado"),
    ("Mangxu sxinkon", "Manĝu ŝinkon"),
    ("kafo aux teo", "kafo aŭ teo"),
    ("Linux", "Linux"),
])
def test_x_system(raw, expected):
    assert normalize_x_system(raw) == expected


def test_sentence_starts_ignore_abbreviations():
    toks = ["Ekz", ".", "la", "kuko", ".", "Ĝi", "estas", "bona", "!"]
    assert sentence_starts(toks) == [True, False, False, False, False, True, False, False, False]
