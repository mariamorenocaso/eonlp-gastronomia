import json

import pytest

import eonlp
from eonlp import Doc, Span, Token


@pytest.fixture
def nlp():
    return eonlp.load()


def test_call_returns_doc(nlp):
    doc = nlp("Mi ŝatas manĝi kukon kaj trinki kafon.")
    assert isinstance(doc, Doc)
    assert len(doc) == 8
    assert all(isinstance(t, Token) for t in doc)
    assert doc[3].lemma_ == "kuko"
    assert doc[3].i == 3


def test_slice_returns_span(nlp):
    doc = nlp("La kuiristo bakis kukon.")
    span = doc[1:3]
    assert isinstance(span, Span)
    assert span.text == "kuiristo bakis"


def test_sentences(nlp):
    doc = nlp("Mi manĝas. Vi trinkas! Ĉu ili dormas?")
    assert [s.text for s in doc.sents] == ["Mi manĝas.", "Vi trinkas!", "Ĉu ili dormas?"]


def test_stop_words_use_lemma(nlp):
    doc = nlp("La kuko estas bona kaj ili havis kafon.")
    stops = {t.text for t in doc if t.is_stop}
    assert stops == {"La", "estas", "kaj", "ili", "havis"}


def test_stop_word_management(nlp):
    nlp.add_stop_words("Bona")
    assert "bona" in nlp.stop_words
    assert nlp("bona")[0].is_stop
    nlp.remove_stop_words("bona", "kaj")
    assert not nlp("kaj")[0].is_stop


def test_custom_stop_list():
    nlp = eonlp.load(stop_words=["kuko"])
    doc = nlp("la kuko")
    assert [t.is_stop for t in doc] == [False, True]


def test_words_helper(nlp):
    doc = nlp("La kuiristo bakis ĉokoladajn kukojn kaj kuketojn.")
    assert doc.words() == ["kuiristo", "baki", "ĉokolada", "kuko", "kuketo"]
    assert doc.words("root_") == ["kuir", "bak", "ĉokolad", "kuk", "kuk"]
    assert doc.words("lower_", remove_stop=False) == ["la", "kuiristo", "bakis", "ĉokoladajn", "kukojn", "kaj", "kuketojn"]


def test_x_system_is_normalized(nlp):
    assert nlp("cxokolado")[0].text == "ĉokolado"
    assert eonlp.load(normalize_x=False)("cxokolado")[0].text == "cxokolado"


def test_esperanto_ratio(nlp):
    assert nlp("La kuko estas tre bongusta.").esperanto_ratio() == 1.0
    assert nlp("The cake is very tasty.").esperanto_ratio() < 0.5


def test_count_by_and_json(nlp):
    doc = nlp("Mi manĝas kukon.")
    assert doc.count_by("pos_") == {"PRON": 1, "VERB": 1, "NOUN": 1, "PUNCT": 1}
    data = json.loads(doc.to_json())
    assert data["tokens"][2]["lemma"] == "kuko"
    assert data["tokens"][2]["morph"] == "Case=Acc|Number=Sing"


def test_pipe(nlp):
    docs = list(nlp.pipe(["kafo", "teo"]))
    assert [d[0].lemma_ for d in docs] == ["kafo", "teo"]


def test_rejects_non_text(nlp):
    with pytest.raises(TypeError):
        nlp(None)


def test_empty_text(nlp):
    doc = nlp("")
    assert len(doc) == 0 and doc.sents == [] and doc.esperanto_ratio() == 0.0
