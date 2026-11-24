import pytest

from eonlp import analyze, root_of


@pytest.mark.parametrize("word, lemma, pos", [
    # sustantivos
    ("kuko", "kuko", "NOUN"), ("kukon", "kuko", "NOUN"), ("kukoj", "kuko", "NOUN"), ("kukojn", "kuko", "NOUN"),
    # adjetivos
    ("dolĉa", "dolĉa", "ADJ"), ("dolĉajn", "dolĉa", "ADJ"),
    # adverbios derivados
    ("rapide", "rapide", "ADV"), ("hejmen", "hejme", "ADV"),
    # verbos
    ("manĝi", "manĝi", "VERB"), ("manĝas", "manĝi", "VERB"), ("manĝis", "manĝi", "VERB"),
    ("manĝos", "manĝi", "VERB"), ("manĝus", "manĝi", "VERB"), ("manĝu", "manĝi", "VERB"),
    # participios
    ("kuirita", "kuiri", "ADJ"), ("bakitajn", "baki", "ADJ"), ("manĝanta", "manĝi", "ADJ"), ("manĝante", "manĝi", "ADV"),
])
def test_open_classes(word, lemma, pos):
    a = analyze(word)
    assert (a.lemma, a.pos) == (lemma, pos)


@pytest.mark.parametrize("word, lemma, pos", [
    ("la", "la", "DET"), ("kaj", "kaj", "CCONJ"), ("ke", "ke", "SCONJ"), ("de", "de", "ADP"),
    ("ĝis", "ĝis", "ADP"), ("plus", "plus", "ADV"), ("ne", "ne", "PART"), ("tri", "tri", "NUM"),
    ("min", "mi", "PRON"), ("miajn", "mia", "DET"), ("tiujn", "tiu", "PRON"),
    ("tion", "tio", "PRON"), ("kia", "kia", "DET"), ("kie", "kie", "ADV"), ("tien", "tie", "ADV"),
    ("ho", "ho", "INTJ"),
])
def test_closed_classes(word, lemma, pos):
    a = analyze(word)
    assert (a.lemma, a.pos) == (lemma, pos)


@pytest.mark.parametrize("word, lemma", [
    ("tomata", "tomata"), ("salatan", "salata"), ("biskvitoj", "biskvito"), ("malsata", "malsata"),
])
def test_participle_exceptions(word, lemma):
    """Palabras que parecen participios pero no lo son."""
    a = analyze(word)
    assert a.lemma == lemma
    assert "VerbForm" not in a.morph


def test_morphological_features():
    a = analyze("kukojn")
    assert a.morph == {"Number": "Plur", "Case": "Acc"}
    assert analyze("manĝis").morph["Tense"] == "Past"
    assert analyze("manĝus").morph["Mood"] == "Cnd"
    assert analyze("kuirita").morph["Voice"] == "Pass"


def test_punctuation_symbols_numbers():
    assert analyze(".").pos == "PUNCT"
    assert analyze("€").pos == "SYM"
    assert analyze("1950").pos == "NUM"


def test_elision():
    assert analyze("l'").lemma == "la"
    a = analyze("dom'")
    assert a.lemma == "domo" and a.morph["Elided"] == "Yes"


def test_proper_nouns():
    assert analyze("Francio").pos == "PROPN"
    assert analyze("Francio", sent_start=True).pos == "NOUN"   # a principio de frase no se sabe
    assert analyze("Kjoto").lemma == "Kjoto"
    assert analyze("Barcelona").pos != "X"
    assert analyze("Smith").pos == "PROPN"                     # sin terminación esperantista


def test_unknown_lowercase_word():
    assert analyze("xyz").pos == "X"


@pytest.mark.parametrize("lemma, pos, root", [
    ("kuketo", "NOUN", "kuk"), ("kafejo", "NOUN", "kaf"), ("kuiristo", "NOUN", "kuir"),
    ("dolĉigi", "VERB", "dolĉ"), ("malvarma", "ADJ", "varm"), ("manĝebla", "ADJ", "manĝ"),
    ("vino", "NOUN", "vin"), ("biero", "NOUN", "bier"), ("recepto", "NOUN", "recept"),
    ("kaj", "CCONJ", "kaj"),
])
def test_roots(lemma, pos, root):
    assert root_of(lemma, pos) == root


@pytest.mark.parametrize("lemma, root", [
    ("ĉokolado", "ĉokolad"), ("vanilo", "vanil"), ("spageto", "spaget"), ("limonado", "limonad"),
])
def test_root_exceptions(lemma, root):
    assert root_of(lemma, "NOUN") == root
