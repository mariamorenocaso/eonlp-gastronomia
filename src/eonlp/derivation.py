"""Extracción de la raíz (*radiko*) de una palabra.

El Esperanto forma palabras nuevas con prefijos y sufijos regulares:
``kuko`` (pastel) → ``kuketo`` (galleta); ``kafo`` (café) → ``kafejo`` (cafetería);
``kuiri`` (cocinar) → ``kuiristo`` (cocinero). El lematizador deja estas palabras
separadas; la raíz las agrupa (``kuk``, ``kaf``, ``kuir``).

Solo se quitan afijos "seguros" y nunca se deja una raíz de menos de 3 letras,
para no destrozar palabras cortas (``vino`` no pierde ``-in-``, ``biero`` no pierde ``-er-``).
"""

from __future__ import annotations

#: Sufijos que se eliminan (de más largo a más corto para que ``-ism-`` gane a ``-is-``).
SUFFIXES = ("ism", "ist", "ebl", "ind", "aĵ", "ej", "et", "eg", "ul", "il", "ec",
            "ig", "iĝ", "ad", "uj", "em")

#: Prefijos que se eliminan. ``re-``, ``ge-`` o ``ek-`` no se usan porque
#: chocan con muchas raíces (``recepto``, ``geografio``, ``ekzemplo``).
PREFIXES = ("mal", "mis", "dis")

#: Raíces que acaban como un sufijo pero no lo llevan (``ĉokolado`` no es "ĉokol + -ad-").
#: Al llegar a una de ellas se deja de recortar.
NO_STRIP = frozenset({
    # comida y bebida
    "ĉokolad", "limonad", "marmelad", "avokad", "oranĝad", "spaget", "kotlet", "omlet",
    "kroket", "baget", "sorbet", "buket", "vanil",
    # otras palabras frecuentes
    "paket", "planet", "kabinet", "etiket", "raket", "tablet", "toalet", "klarnet",
    "grenad", "parad", "balad", "fasad", "brazil", "april", "pilul", "modul",
    "formul", "kapsul", "stimul", "sistem", "problem", "koleg", "strateg",
})

MIN_ROOT = 3
MAX_STEPS = 3


def root_of(lemma: str, pos: str) -> str:
    """Devuelve la raíz de un lema de clase abierta.

    Para el resto de categorías (preposiciones, puntuación...) devuelve el lema.
    """
    if pos not in ("NOUN", "ADJ", "ADV", "VERB") or len(lemma) < 3:
        return lemma

    word = lemma.lower()
    if word[-1] in "oaei":
        word = word[:-1]

    for _ in range(MAX_STEPS):
        if word in NO_STRIP:
            break
        changed = False
        for suf in SUFFIXES:
            if word.endswith(suf) and len(word) - len(suf) >= MIN_ROOT:
                word = word[: -len(suf)]
                changed = True
                break
        if not changed:
            break

    for pre in PREFIXES:
        if word.startswith(pre) and len(word) - len(pre) >= MIN_ROOT:
            word = word[len(pre):]
            break
    return word
