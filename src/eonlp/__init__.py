"""eonlp: librería de NLP para Esperanto basada en reglas, con una interfaz similar a spaCy.

Uso básico::

    import eonlp
    nlp = eonlp.load()
    doc = nlp("La kuiristo bakis ĉokoladajn kukojn.")
    [(t.text, t.lemma_, t.pos_) for t in doc]
"""

from .language import Language, load
from .lexicon import STOP_WORDS
from .morphology import Analysis, analyze
from .derivation import root_of
from .tokenizer import Tokenizer, normalize_x_system
from .tokens import Doc, Morph, Span, Token

__version__ = "1.0.0"

__all__ = [
    "Language", "load", "STOP_WORDS", "Analysis", "analyze", "root_of",
    "Tokenizer", "normalize_x_system", "Doc", "Morph", "Span", "Token", "__version__",
]
