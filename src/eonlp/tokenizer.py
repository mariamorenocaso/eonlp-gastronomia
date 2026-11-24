"""Tokenizador y segmentador de frases para Esperanto."""

from __future__ import annotations

import re
from typing import List, Tuple

from .lexicon import ABBREVIATIONS

_LETTER = r"[^\W\d_]"

_TOKEN_RE = re.compile(
    rf"(?P<elision>\b[lL]['’](?={_LETTER}|\s|$))"          # l' (artículo elidido)
    rf"|(?P<number>\d+(?:[.,]\d+)*)"                        # 1950, 5,50, 1.000
    rf"|(?P<word>{_LETTER}+(?:-{_LETTER}+)*(?:['’](?!{_LETTER}))?)"  # ĉokolad-kuko, dom'
    r"|(?P<ellipsis>\.\.\.|…)"                              # puntos suspensivos
    r"|(?P<other>\S)"                                       # cualquier otro carácter
)

#: Sistema-x: forma de escribir las letras con diacrítico usando una ``x``.
_X_SYSTEM = {
    "cx": "ĉ", "gx": "ĝ", "hx": "ĥ", "jx": "ĵ", "sx": "ŝ",
    "Cx": "Ĉ", "Gx": "Ĝ", "Hx": "Ĥ", "Jx": "Ĵ", "Sx": "Ŝ",
    "CX": "Ĉ", "GX": "Ĝ", "HX": "Ĥ", "JX": "Ĵ", "SX": "Ŝ",
}
_X_RE = re.compile(r"[cghjsCGHJS][xX]|(?<=[aeAE])[uU][xX]")

SENTENCE_END = frozenset({".", "!", "?", "...", "…"})

Token = Tuple[str, int]


def normalize_x_system(text: str) -> str:
    """Convierte el sistema-x a letras con diacrítico: ``cxokolado`` → ``ĉokolado``.

    La ``ux`` solo se convierte detrás de vocal (``aux`` → ``aŭ``) para no
    estropear palabras extranjeras como ``Linux``.
    """
    def repl(m: re.Match) -> str:
        s = m.group(0)
        if s[0] in "uU":
            return "ŭ" if s[0] == "u" else "Ŭ"
        return _X_SYSTEM[s]
    return _X_RE.sub(repl, text)


class Tokenizer:
    """Divide un texto en tokens (palabras, números y signos).

    Ejemplo:
        >>> Tokenizer()("En 1950 la ĉokolad-kuko kostis 5,50 €.")
        [('En', 0), ('1950', 3), ('la', 8), ('ĉokolad-kuko', 11), ('kostis', 24), ('5,50', 31), ('€', 36), ('.', 37)]
    """

    def __call__(self, text: str) -> List[Token]:
        """Devuelve una lista de pares ``(texto_del_token, posición_en_el_texto)``."""
        return [(m.group(0), m.start()) for m in _TOKEN_RE.finditer(text)]


def sentence_starts(tokens: List[str]) -> List[bool]:
    """Indica qué tokens empiezan frase.

    Una frase termina en ``.``, ``!``, ``?`` o ``...``, salvo que el punto
    vaya detrás de una abreviatura (``ekz.``, ``ktp.``).
    """
    starts = [False] * len(tokens)
    if not tokens:
        return starts
    starts[0] = True
    for i, tok in enumerate(tokens[:-1]):
        if tok in SENTENCE_END:
            prev = tokens[i - 1].lower() if i > 0 else ""
            if tok == "." and prev in ABBREVIATIONS:
                continue
            starts[i + 1] = True
    return starts
