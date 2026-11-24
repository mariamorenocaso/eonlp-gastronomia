"""Ejecuta los ejemplos de la documentación de los módulos (doctests)."""

import doctest

import eonlp.tokenizer


def test_tokenizer_docstring_examples():
    result = doctest.testmod(eonlp.tokenizer)
    assert result.failed == 0
