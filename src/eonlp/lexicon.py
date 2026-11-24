"""Léxico cerrado del Esperanto: palabras invariables, pronombres y correlativos.

En Esperanto casi todas las palabras "vacías" pertenecen a clases cerradas
(preposiciones, conjunciones, pronombres, correlativos...). Por eso se pueden
describir con listas finitas y el resto de palabras se analiza con reglas de
terminación (ver :mod:`eonlp.morphology`).

Este módulo construye ``CLOSED_LEXICON``: un diccionario
``forma -> (lema, POS, rasgos)`` que incluye también las formas flexionadas
(``min``, ``miajn``, ``tiujn``, ``kien``...).
"""

from __future__ import annotations

from typing import Dict, Tuple

# ---------------------------------------------------------------------------
# Clases cerradas (etiquetas POS de Universal Dependencies)
# ---------------------------------------------------------------------------

#: Preposiciones (ADP).
ADPOSITIONS = frozenset({
    "al", "anstataŭ", "antaŭ", "apud", "ĉe", "ĉirkaŭ", "da", "de", "dum",
    "ekster", "el", "en", "ĝis", "inter", "je", "kontraŭ", "krom", "kun",
    "laŭ", "malgraŭ", "per", "po", "por", "post", "preter", "pri", "pro",
    "sen", "sub", "super", "sur", "tra", "trans",
})

#: Conjunciones coordinantes (CCONJ).
COORDINATING = frozenset({"kaj", "aŭ", "sed", "nek", "do"})

#: Conjunciones subordinantes (SCONJ).
SUBORDINATING = frozenset({"ke", "se", "ĉar", "kvankam", "kvazaŭ", "ol", "ju", "des"})

#: Artículo (DET). ``l'`` es la forma elidida y se trata en el analizador.
ARTICLE = frozenset({"la"})

#: Pronombres personales (PRON). Con ``-n`` forman el acusativo y con ``-a`` el posesivo.
PERSONAL_PRONOUNS = frozenset({"mi", "vi", "li", "ŝi", "ĝi", "ni", "ili", "oni", "si", "ci"})

#: Numerales cardinales básicos (NUM).
NUMERALS = frozenset({"nul", "unu", "du", "tri", "kvar", "kvin", "ses", "sep", "ok", "naŭ",
                      "dek", "cent", "mil"})

#: Partículas (PART): negación, interrogación y partículas de foco.
PARTICLES = frozenset({"ne", "ĉu", "ja", "jen", "jes", "nur", "eĉ", "ankaŭ", "mem", "ĉi", "ajn"})

#: Adverbios primarios (ADV): no llevan la terminación ``-e``.
PRIMARY_ADVERBS = frozenset({
    "almenaŭ", "ambaŭ", "ankoraŭ", "apenaŭ", "baldaŭ", "for", "hieraŭ", "hodiaŭ",
    "jam", "ĵus", "morgaŭ", "nun", "plej", "pli", "plu", "preskaŭ", "tamen",
    "tre", "tro", "tuj", "plus", "minus", "adiaŭ",
})

#: Interjecciones (INTJ).
INTERJECTIONS = frozenset({"ha", "he", "ho", "hu", "nu", "ve", "fi", "hura", "bis", "aĥ", "ehe"})

#: Abreviaturas frecuentes (X). También se usan para no partir frases en ``ekz.``.
ABBREVIATIONS = frozenset({"ktp", "ekz", "k", "t.e", "s-ro", "s-ino", "d-ro", "n-ro", "ĉ", "p", "vd", "ks"})

#: Verbos muy frecuentes y poco temáticos. Se tratan como stopwords por su lema.
STOP_VERBS = frozenset({"esti", "havi", "povi", "devi"})

# ---------------------------------------------------------------------------
# Correlativos: tabla de Zamenhof (prefijo + sufijo)
# ---------------------------------------------------------------------------

CORRELATIVE_PREFIXES = ("ki", "ti", "i", "ĉi", "neni")
CORRELATIVE_SUFFIXES = ("u", "o", "a", "e", "el", "es", "am", "al", "om")

#: POS de cada sufijo correlativo.
_CORRELATIVE_POS = {
    "u": "PRON", "o": "PRON",          # kiu, kio
    "a": "DET", "es": "DET",           # kia, kies
    "e": "ADV", "el": "ADV", "am": "ADV", "al": "ADV", "om": "ADV",
}

#: Tipo semántico de cada prefijo (rasgo PronType de UD).
_PREFIX_TYPE = {"ki": "Int,Rel", "ti": "Dem", "i": "Ind", "ĉi": "Tot", "neni": "Neg"}

Analysis = Tuple[str, str, Dict[str, str]]


def _build_lexicon() -> Dict[str, Analysis]:
    lex: Dict[str, Analysis] = {}

    def add(form: str, lemma: str, pos: str, **feats: str) -> None:
        # La primera entrada gana: así "ĉi" queda como partícula y no como prefijo.
        lex.setdefault(form, (lemma, pos, dict(feats)))

    for w in PARTICLES:
        add(w, w, "PART")
    for w in ARTICLE:
        add(w, w, "DET", PronType="Art")
    for w in ADPOSITIONS:
        add(w, w, "ADP")
    for w in COORDINATING:
        add(w, w, "CCONJ")
    for w in SUBORDINATING:
        add(w, w, "SCONJ")
    for w in NUMERALS:
        add(w, w, "NUM", NumType="Card")
    for w in PRIMARY_ADVERBS:
        add(w, w, "ADV")
    for w in INTERJECTIONS:
        add(w, w, "INTJ")
    for w in ABBREVIATIONS:
        add(w, w, "X", Abbr="Yes")

    # Pronombres personales: nominativo, acusativo y posesivos.
    for p in PERSONAL_PRONOUNS:
        add(p, p, "PRON", PronType="Prs", Case="Nom")
        add(p + "n", p, "PRON", PronType="Prs", Case="Acc")
        poss = p + "a"
        add(poss, poss, "DET", Poss="Yes", Number="Sing", Case="Nom")
        add(poss + "n", poss, "DET", Poss="Yes", Number="Sing", Case="Acc")
        add(poss + "j", poss, "DET", Poss="Yes", Number="Plur", Case="Nom")
        add(poss + "jn", poss, "DET", Poss="Yes", Number="Plur", Case="Acc")

    # Correlativos y sus formas flexionadas.
    for pre in CORRELATIVE_PREFIXES:
        for suf in CORRELATIVE_SUFFIXES:
            base = pre + suf
            pos = _CORRELATIVE_POS[suf]
            ptype = _PREFIX_TYPE[pre]
            add(base, base, pos, PronType=ptype)
            if suf in ("u", "a"):                       # tiu, tiuj, tiun, tiujn
                add(base + "j", base, pos, PronType=ptype, Number="Plur", Case="Nom")
                add(base + "n", base, pos, PronType=ptype, Number="Sing", Case="Acc")
                add(base + "jn", base, pos, PronType=ptype, Number="Plur", Case="Acc")
            elif suf == "o":                            # tion
                add(base + "n", base, pos, PronType=ptype, Case="Acc")
            elif suf == "e":                            # tien (dirección)
                add(base + "n", base, pos, PronType=ptype, Case="Acc")
    return lex


#: Diccionario ``forma -> (lema, POS, rasgos)`` de todas las palabras de clase cerrada.
CLOSED_LEXICON: Dict[str, Analysis] = _build_lexicon()


def _default_stop_words() -> frozenset:
    """Stopwords por defecto: todo el léxico cerrado más los verbos poco temáticos."""
    return frozenset(CLOSED_LEXICON) | STOP_VERBS


#: Lista de stopwords por defecto (formas y lemas en minúscula).
STOP_WORDS = _default_stop_words()
