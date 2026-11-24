"""Análisis morfológico por reglas: lema, categoría gramatical (POS) y rasgos.

El Esperanto marca la categoría gramatical con la terminación de la palabra:

========  ===============================  ==========================
Final     Significado                      Ejemplo
========  ===============================  ==========================
``-o``    sustantivo                       ``kuko`` (pastel)
``-a``    adjetivo                         ``dolĉa`` (dulce)
``-e``    adverbio derivado                ``rapide`` (rápidamente)
``-i``    verbo en infinitivo              ``manĝi`` (comer)
``-as``   verbo en presente                ``manĝas``
``-is``   verbo en pasado                  ``manĝis``
``-os``   verbo en futuro                  ``manĝos``
``-us``   verbo en condicional             ``manĝus``
``-u``    verbo en imperativo              ``manĝu``
``-j``    plural (tras ``-o``/``-a``)      ``kukoj``
``-n``    acusativo (o dirección)          ``kukon``, ``hejmen``
========  ===============================  ==========================

Los participios se forman con ``-ant-/-int-/-ont-`` (activos) y
``-at-/-it-/-ot-`` (pasivos): ``kuirita`` = cocinado, lema ``kuiri``.

El orden del análisis es:

1. Puntuación, símbolos y números.
2. Elisión (``l'`` → ``la``; ``dom'`` → ``domo``).
3. Léxico cerrado (preposiciones, pronombres, correlativos...).
4. Reglas de terminación para las palabras de clase abierta.
5. Nombres propios: palabras en mayúscula que no empiezan frase.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Optional

from .lexicon import CLOSED_LEXICON

# ---------------------------------------------------------------------------
# Expresiones regulares de las terminaciones
# ---------------------------------------------------------------------------

#: Sustantivos y adjetivos: raíz + o/a + j opcional + n opcional.
_NOMINAL = re.compile(r"^(?P<stem>.{2,}?)(?P<vowel>[oa])(?P<plur>j?)(?P<acc>n?)$")
#: Adverbios derivados: raíz + e + n opcional (dirección).
_ADVERB = re.compile(r"^(?P<stem>.{2,}?)e(?P<acc>n?)$")
#: Verbos: raíz + terminación verbal.
_VERB = re.compile(r"^(?P<stem>.{2,}?)(?P<end>as|is|os|us|u|i)$")
#: Participios: raíz (mín. 3 letras) + sufijo participial.
_PARTICIPLE = re.compile(r"^(?P<root>.{3,}?)(?P<suf>ant|int|ont|at|it|ot)$")

_PUNCT = re.compile(r"^[^\w\s]+$")
_NUMBER = re.compile(r"^\d+(?:[.,]\d+)*$")
_SYMBOLS = frozenset("€$£%°+=<>§&#@*/×÷~^|")

_VERB_ENDINGS = {
    "as": {"VerbForm": "Fin", "Mood": "Ind", "Tense": "Pres"},
    "is": {"VerbForm": "Fin", "Mood": "Ind", "Tense": "Past"},
    "os": {"VerbForm": "Fin", "Mood": "Ind", "Tense": "Fut"},
    "us": {"VerbForm": "Fin", "Mood": "Cnd"},
    "u": {"VerbForm": "Fin", "Mood": "Imp"},
    "i": {"VerbForm": "Inf"},
}

_PARTICIPLE_FEATS = {
    "ant": ("Pres", "Act"), "int": ("Past", "Act"), "ont": ("Fut", "Act"),
    "at": ("Pres", "Pass"), "it": ("Past", "Pass"), "ot": ("Fut", "Pass"),
}

#: Raíces que acaban como un sufijo participial pero NO son participios.
#: Sin esta lista, ``tomata`` (de tomate) se analizaría como participio de ``*tomi``.
#: Muchas son del dominio gastronómico porque es donde más aparecen.
PARTICIPLE_EXCEPTIONS = frozenset({
    # comida y bebida
    "tomat", "salat", "granat", "muskat", "biskvit", "kompot", "karot", "abrikot",
    "ŝalot", "bergamot", "absint", "spirit", "apetit", "karbonhidrat", "hidrat",
    # otras palabras frecuentes
    "privat", "delikat", "akurat", "kvadrat", "demokrat", "soldat", "adekvat",
    "malsat", "kvalit", "favorit", "elit", "kredit", "eksplicit", "infinit",
    "pilot", "patriot", "idiot", "despot", "elefant", "diamant", "elegant",
    "konstant", "galant", "gigant", "variant", "konsonant", "labirint", "hiacint",
    "nitrat", "karbonat", "sulfat", "fosfat", "acetat", "silikat",
})


@dataclass
class Analysis:
    """Resultado del análisis de una palabra."""

    lemma: str
    pos: str
    morph: Dict[str, str] = field(default_factory=dict)


def _participle(stem: str) -> Optional[tuple]:
    """Si ``stem`` (sin la vocal final) es un participio, devuelve (raíz, tiempo, voz)."""
    if stem in PARTICIPLE_EXCEPTIONS:
        return None
    m = _PARTICIPLE.match(stem)
    if not m:
        return None
    tense, voice = _PARTICIPLE_FEATS[m.group("suf")]
    return m.group("root"), tense, voice


def analyze_open_class(word: str) -> Optional[Analysis]:
    """Analiza una palabra en minúscula de clase abierta por su terminación.

    Devuelve ``None`` si la palabra no tiene ninguna terminación del Esperanto
    (por ejemplo, un nombre extranjero como ``Napoleon``).
    """
    # 1) Sustantivos y adjetivos (incluidos los participios adjetivos)
    m = _NOMINAL.match(word)
    if m:
        stem, vowel = m.group("stem"), m.group("vowel")
        feats = {"Number": "Plur" if m.group("plur") else "Sing",
                 "Case": "Acc" if m.group("acc") else "Nom"}
        if vowel == "a":
            part = _participle(stem)
            if part:
                root, tense, voice = part
                feats.update(VerbForm="Part", Tense=tense, Voice=voice)
                return Analysis(root + "i", "ADJ", feats)
            return Analysis(stem + "a", "ADJ", feats)
        # Los participios sustantivados (manĝanto) se dejan como sustantivos:
        # hay demasiados sustantivos normales que acaban igual (elefanto, biskvito...).
        return Analysis(stem + "o", "NOUN", feats)

    # 2) Adverbios derivados (incluido el adverbio participial: manĝante)
    m = _ADVERB.match(word)
    if m:
        stem = m.group("stem")
        feats = {"Case": "Acc"} if m.group("acc") else {}
        part = _participle(stem)
        if part and not m.group("acc"):
            root, tense, voice = part
            feats.update(VerbForm="Part", Tense=tense, Voice=voice)
            return Analysis(root + "i", "ADV", feats)
        return Analysis(stem + "e", "ADV", feats)

    # 3) Verbos
    m = _VERB.match(word)
    if m:
        return Analysis(m.group("stem") + "i", "VERB", dict(_VERB_ENDINGS[m.group("end")]))

    return None


def analyze(text: str, sent_start: bool = False) -> Analysis:
    """Devuelve el lema, la POS (etiquetas UD) y los rasgos morfológicos de un token.

    Args:
        text: El token tal y como aparece en el texto.
        sent_start: Si el token empieza una frase. Sirve para no confundir
            una palabra en mayúscula a principio de frase con un nombre propio.
    """
    if not text:
        return Analysis(text, "X")

    # Puntuación, símbolos y números
    if _NUMBER.match(text):
        return Analysis(text, "NUM", {"NumType": "Card"})
    if _PUNCT.match(text):
        if all(ch in _SYMBOLS for ch in text):
            return Analysis(text, "SYM")
        return Analysis(text, "PUNCT")

    lower = text.lower()

    # Elisión del artículo y de la -o final de los sustantivos
    elided = False
    if lower in ("l'", "l’"):
        return Analysis("la", "DET", {"PronType": "Art"})
    if lower.endswith(("'", "’")) and len(lower) > 2:
        lower = lower[:-1] + "o"
        elided = True

    # Léxico cerrado
    if lower in CLOSED_LEXICON:
        lemma, pos, feats = CLOSED_LEXICON[lower]
        return Analysis(lemma, pos, dict(feats))

    # Palabras compuestas con guion: se analiza la última parte
    prefix = ""
    core = lower
    if "-" in lower:
        prefix, core = lower.rsplit("-", 1)
        prefix += "-"

    result = analyze_open_class(core)
    capitalized = text[0].isupper()

    if result is None:
        # Sin terminación esperantista: nombre propio extranjero o palabra desconocida
        if capitalized:
            return Analysis(text, "PROPN")
        return Analysis(lower, "X")

    result.lemma = prefix + result.lemma
    if elided:
        result.morph["Elided"] = "Yes"

    # Nombres propios esperantizados: Francio, Parizon...
    if capitalized and not sent_start and result.pos == "NOUN":
        result.pos = "PROPN"
        result.lemma = result.lemma[:1].upper() + result.lemma[1:]
    return result
