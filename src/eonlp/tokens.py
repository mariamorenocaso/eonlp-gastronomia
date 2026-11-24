"""Objetos que estructuran el resultado del análisis: :class:`Token`, :class:`Span` y :class:`Doc`.

Imitan la interfaz de spaCy: los atributos de texto acaban en ``_``
(``lemma_``, ``pos_``) y un :class:`Doc` se recorre como una lista de tokens.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Dict, Iterator, List, Optional, Union


class Morph(dict):
    """Rasgos morfológicos de un token, en formato Universal Dependencies.

    Es un diccionario normal que además se imprime como ``Case=Acc|Number=Plur``.
    """

    def __str__(self) -> str:
        return "|".join(f"{k}={v}" for k, v in sorted(self.items()))

    def __repr__(self) -> str:
        return f"Morph({self})"


class Token:
    """Una palabra, número o signo de puntuación dentro de un :class:`Doc`.

    Attributes:
        text: Texto original del token.
        i: Posición del token dentro del documento.
        idx: Posición del primer carácter dentro del texto.
        lower_: Texto en minúscula.
        lemma_: Forma base (``kukojn`` → ``kuko``, ``manĝis`` → ``manĝi``).
        pos_: Categoría gramatical con etiquetas UD (``NOUN``, ``VERB``, ``ADP``...).
        morph: Rasgos morfológicos (:class:`Morph`).
        root_: Raíz sin afijos (``kuketojn`` → ``kuk``).
        is_stop: Si es una stopword.
        is_punct: Si es un signo de puntuación.
        is_alpha: Si está formado solo por letras.
        is_digit: Si está formado solo por dígitos.
        like_num: Si parece un número (``1950``, ``5,50``, ``tri``).
        is_sent_start: Si empieza una frase.
    """

    __slots__ = ("doc", "text", "i", "idx", "lower_", "lemma_", "pos_", "morph",
                 "root_", "is_stop", "is_punct", "is_alpha", "is_digit", "like_num",
                 "is_sent_start")

    def __init__(self, doc: "Doc", text: str, i: int, idx: int, lemma: str, pos: str,
                 morph: Dict[str, str], root: str, is_stop: bool, is_sent_start: bool):
        self.doc = doc
        self.text = text
        self.i = i
        self.idx = idx
        self.lower_ = text.lower()
        self.lemma_ = lemma
        self.pos_ = pos
        self.morph = Morph(morph)
        self.root_ = root
        self.is_stop = is_stop
        self.is_punct = pos == "PUNCT"
        self.is_alpha = text.replace("-", "").isalpha()
        self.is_digit = text.isdigit()
        self.like_num = pos == "NUM"
        self.is_sent_start = is_sent_start

    def __len__(self) -> int:
        return len(self.text)

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return self.text

    def to_dict(self) -> dict:
        """Devuelve los atributos del token como diccionario (útil para tablas)."""
        return {
            "i": self.i, "text": self.text, "lemma": self.lemma_, "pos": self.pos_,
            "morph": str(self.morph), "root": self.root_, "is_stop": self.is_stop,
            "is_punct": self.is_punct, "is_sent_start": self.is_sent_start,
        }


class Span:
    """Fragmento continuo de un :class:`Doc` (por ejemplo, una frase)."""

    def __init__(self, doc: "Doc", start: int, end: int):
        self.doc = doc
        self.start = start
        self.end = end

    @property
    def tokens(self) -> List[Token]:
        return self.doc.tokens[self.start:self.end]

    @property
    def text(self) -> str:
        if self.start >= self.end:
            return ""
        first, last = self.doc.tokens[self.start], self.doc.tokens[self.end - 1]
        return self.doc.text[first.idx:last.idx + len(last.text)]

    def __iter__(self) -> Iterator[Token]:
        return iter(self.tokens)

    def __len__(self) -> int:
        return self.end - self.start

    def __getitem__(self, i: int) -> Token:
        return self.tokens[i]

    def __repr__(self) -> str:
        return self.text


class Doc:
    """Texto analizado: secuencia de :class:`Token` con acceso a frases y utilidades.

    Se crea llamando al modelo: ``doc = nlp("Mi manĝas kukon.")``.
    """

    def __init__(self, text: str):
        self.text = text
        self.tokens: List[Token] = []

    # --- interfaz de secuencia -------------------------------------------
    def __iter__(self) -> Iterator[Token]:
        return iter(self.tokens)

    def __len__(self) -> int:
        return len(self.tokens)

    def __getitem__(self, key: Union[int, slice]) -> Union[Token, Span]:
        if isinstance(key, slice):
            start, stop, _ = key.indices(len(self.tokens))
            return Span(self, start, stop)
        return self.tokens[key]

    def __repr__(self) -> str:
        return self.text

    # --- frases ------------------------------------------------------------
    @property
    def sents(self) -> List[Span]:
        """Lista de frases del documento."""
        starts = [t.i for t in self.tokens if t.is_sent_start] + [len(self.tokens)]
        return [Span(self, a, b) for a, b in zip(starts, starts[1:]) if a < b]

    # --- utilidades ----------------------------------------------------------
    def words(self, attr: str = "lemma_", remove_stop: bool = True, remove_punct: bool = True,
              min_len: int = 1, alpha_only: bool = False) -> List[str]:
        """Devuelve una lista de palabras lista para vectorizar.

        Args:
            attr: Atributo que se devuelve (``"lemma_"``, ``"lower_"``, ``"root_"``...).
            remove_stop: Quitar stopwords.
            remove_punct: Quitar puntuación y símbolos.
            min_len: Longitud mínima de la palabra.
            alpha_only: Quedarse solo con palabras formadas por letras.
        """
        out = []
        for t in self.tokens:
            if remove_punct and t.pos_ in ("PUNCT", "SYM"):
                continue
            if remove_stop and t.is_stop:
                continue
            if alpha_only and not t.is_alpha:
                continue
            value = getattr(t, attr)
            if attr != "text":
                value = value.lower()
            if len(value) >= min_len:
                out.append(value)
        return out

    def count_by(self, attr: str = "pos_") -> Dict[str, int]:
        """Cuenta los tokens según un atributo, por ejemplo ``doc.count_by("pos_")``."""
        return dict(Counter(getattr(t, attr) for t in self.tokens))

    def esperanto_ratio(self) -> float:
        """Proporción de palabras reconocidas como Esperanto (0 a 1).

        Una palabra se considera reconocida si no es ``X`` ni ``PROPN``. Sirve
        para descartar párrafos en otros idiomas o listas de nombres propios.
        """
        words = [t for t in self.tokens if t.is_alpha]
        if not words:
            return 0.0
        known = sum(1 for t in words if t.pos_ not in ("X", "PROPN"))
        return known / len(words)

    def to_dict(self) -> dict:
        """Devuelve el documento como diccionario serializable."""
        return {"text": self.text, "tokens": [t.to_dict() for t in self.tokens],
                "sents": [s.text for s in self.sents]}

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Devuelve el documento en formato JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
