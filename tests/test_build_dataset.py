"""Prueba del script del dataset sin conexión: se simulan las respuestas de la API."""

import csv
import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("requests")

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_dataset.py"
spec = importlib.util.spec_from_file_location("build_dataset", SCRIPT)
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)

CATEGORIES = {
    "Manĝaĵoj": (["Pano", "Supo"], ["Dolĉaĵoj", "Bakaĵoj"]),  # Dolĉaĵoj es raíz de otra clase
    "Bakaĵoj": (["Kuko"], []),                                 # Kuko: profundidad 1 en comida
    "Trinkaĵoj": (["Kafo", "Teo", "Supo"], []),
    "Dolĉaĵoj": (["Kuko", "Torto"], []),
}
TEXTS = {
    "Pano": "La pano estas bakita manĝaĵo el faruno kaj akvo.\n== Historio ==\nOni bakas panon en forno ekde antikvaj tempoj.\n== Referencoj ==\nNi ne volas ĉi tiun tekston en la datumaro.",
    "Kafo": "La kafo estas varma trinkaĵo farita el rostitaj kafograjnoj.\nMallonga.",
    "Teo": "La teo estas trinkaĵo el folioj, kiun oni trinkas varme.",
    "Kuko": "La kuko estas dolĉa deserto el faruno, sukero kaj ovoj.",
    "Torto": "La torto estas dolĉaĵo kun fruktoj; oni servas ĝin post la manĝo.\nThe tart is a very nice dessert from England and Wales.",
}


@pytest.fixture
def fake_api(monkeypatch):
    monkeypatch.setattr(bd, "PAUSE", 0)
    monkeypatch.setattr(bd, "category_members", lambda c: CATEGORIES.get(c, ([], [])))
    monkeypatch.setattr(bd, "article_text", lambda t: TEXTS.get(t, ""))


def config():
    return {
        "seed": 1, "depth": 1, "max_articles_per_class": 10, "min_articles_per_class": 1,
        "min_paragraph_chars": 30, "min_esperanto_ratio": 0.6,
        "classes": {
            "comida": {"categories": ["Manĝaĵoj"], "fallback_articles": []},
            "bebida": {"categories": ["Trinkaĵoj"], "fallback_articles": []},
            "postre": {"categories": ["Dolĉaĵoj"], "fallback_articles": []},
        },
        "reserved_articles": ["Torto"],
        "stop_sections": ["Referencoj"],
    }


def test_assignment_prefers_specific_class_and_drops_ties(fake_api):
    cfg = config()
    chosen, stats = bd.assign_articles(bd.collect_candidates(cfg["classes"], cfg["depth"]), cfg)
    assert sorted(chosen["comida"]) == ["Pano"]          # Supo empata; Kuko está más arriba en postre
    assert sorted(chosen["bebida"]) == ["Kafo", "Teo"]
    assert chosen["postre"] == ["Kuko"]                  # Torto está reservado
    assert stats["ambiguous"] == 1 and stats["reserved"] == 1


def test_build_writes_contract_files(fake_api, tmp_path):
    bd.build(config(), tmp_path)
    with open(tmp_path / "dataset.csv", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter=";"))
    assert rows[0] == ["text", "class"]
    assert all(len(r) == 2 for r in rows)
    texts = [r[0] for r in rows[1:]]
    assert not any("Referencoj" in t or "ne volas" in t for t in texts)   # sección final cortada
    report = json.loads((tmp_path / "noise_report.json").read_text(encoding="utf-8"))
    assert report["discarded_paragraphs"]["corto"] == 1
    assert report["discarded_paragraphs"]["seccion_final"] == 1
    with open(tmp_path / "dataset_meta.csv", encoding="utf-8") as f:
        meta = list(csv.reader(f, delimiter=";"))
    assert meta[0] == ["text", "class", "article"]


def test_clean_paragraph_removes_separator():
    assert ";" not in bd.clean_paragraph("unu; du [3] https://x.org tri")


def test_fallback_complements_valid_articles_instead_of_replacing(fake_api):
    """Si hay pocos candidatos, conservar siempre los artículos válidos encontrados."""
    cfg = config()
    cfg["min_articles_per_class"] = 8
    cfg["classes"]["comida"]["fallback_articles"] = ["Pico", "Pano", "Torto", "Kafo"]
    cfg["classes"]["bebida"]["fallback_articles"] = ["Suko", "Kafo"]
    cfg["classes"]["postre"]["fallback_articles"] = ["Bombono", "Kuko"]
    chosen, _ = bd.assign_articles(bd.collect_candidates(cfg["classes"], cfg["depth"]), cfg)
    assert set(chosen["comida"]) == {"Pano", "Pico"}  # ni Torto reservado ni Kafo de bebida
    assert set(chosen["bebida"]) == {"Kafo", "Teo", "Suko"}
    assert set(chosen["postre"]) == {"Kuko", "Bombono"}
