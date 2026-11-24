"""Clase principal :class:`Language`: convierte un texto en un :class:`~eonlp.tokens.Doc`."""

from __future__ import annotations

from typing import Iterable, Iterator, Optional

from .derivation import root_of
from .lexicon import STOP_WORDS
from .morphology import analyze
from .tokenizer import Tokenizer, normalize_x_system, sentence_starts
from .tokens import Doc, Token


class Language:
    """Modelo de NLP para Esperanto basado en reglas.

    Se usa como en spaCy::

        import eonlp
        nlp = eonlp.load()
        doc = nlp("Mi ŝatas manĝi kukojn.")
        for token in doc:
            print(token.text, token.lemma_, token.pos_, token.morph)

    Args:
        stop_words: Stopwords iniciales. Por defecto, :data:`eonlp.lexicon.STOP_WORDS`.
        normalize_x: Convertir el sistema-x (``cx`` → ``ĉ``) antes de analizar.
    """

    lang = "eo"

    def __init__(self, stop_words: Optional[Iterable[str]] = None, normalize_x: bool = True):
        self.tokenizer = Tokenizer()
        self.normalize_x = normalize_x
        self._stop_words = set(STOP_WORDS if stop_words is None else (w.lower() for w in stop_words))

    # --- gestión de stopwords ----------------------------------------------
    @property
    def stop_words(self) -> set:
        """Conjunto de stopwords del modelo (se puede modificar)."""
        return self._stop_words

    def add_stop_words(self, *words: str) -> None:
        """Añade stopwords: ``nlp.add_stop_words("fari", "uzi")``."""
        self._stop_words.update(w.lower() for w in words)

    def remove_stop_words(self, *words: str) -> None:
        """Elimina stopwords: ``nlp.remove_stop_words("ne")``."""
        self._stop_words.difference_update(w.lower() for w in words)

    def is_stop(self, word: str, lemma: Optional[str] = None) -> bool:
        """Indica si una palabra (o su lema) es stopword."""
        return word.lower() in self._stop_words or (lemma is not None and lemma.lower() in self._stop_words)

    # --- análisis -------------------------------------------------------------
    def __call__(self, text: str) -> Doc:
        """Analiza un texto y devuelve un :class:`Doc`."""
        if not isinstance(text, str):
            raise TypeError(f"Se esperaba un texto (str), no {type(text).__name__}")
        if self.normalize_x:
            text = normalize_x_system(text)

        doc = Doc(text)
        pieces = self.tokenizer(text)
        starts = sentence_starts([p[0] for p in pieces])
        for i, ((tok_text, idx), start) in enumerate(zip(pieces, starts)):
            a = analyze(tok_text, sent_start=start)
            root = root_of(a.lemma, a.pos)
            stop = a.pos not in ("PUNCT", "SYM") and self.is_stop(tok_text, a.lemma)
            doc.tokens.append(Token(doc, tok_text, i, idx, a.lemma, a.pos, a.morph, root, stop, start))
        return doc

    def pipe(self, texts: Iterable[str]) -> Iterator[Doc]:
        """Analiza muchos textos uno detrás de otro (como ``nlp.pipe`` de spaCy)."""
        for text in texts:
            yield self(text)

    def __repr__(self) -> str:
        return f"<eonlp.Language lang='eo' stop_words={len(self._stop_words)}>"


def load(**kwargs) -> Language:
    """Crea un modelo :class:`Language` (equivalente a ``spacy.load``)."""
    return Language(**kwargs)
