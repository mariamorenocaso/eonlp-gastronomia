"""Comprobaciones de empaquetado: el notebook no transforma demos en resultados reales."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_config_has_three_distinct_gastronomy_classes():
    cfg = json.loads((ROOT / "config/gastronomio.json").read_text(encoding="utf-8"))
    assert set(cfg["classes"]) == {"comida", "bebida", "postre"}
    for label, cls in cfg["classes"].items():
        assert cls["categories"], f"La categoría {label} no tiene semillas"
        assert "Deserto" not in cls["categories"]
        assert "Pladoj" not in cls["categories"]
        assert "Alkoholaj trinkaĵoj" not in cls["categories"]
    assert "Desertoj" in cfg["classes"]["postre"]["categories"]


def test_notebook_has_real_web_evaluation_separate_from_demo():
    notebook = json.loads((ROOT / "notebooks/clasificacion_gastronomia.ipynb").read_text(encoding="utf-8"))
    all_code = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    assert "REGENERAR_DATASET" in all_code
    assert "tabla_web = pd.DataFrame(resultados)" in all_code
    assert "demostracion.append" in all_code
    assert "resultados.append" in all_code
    assert "resultados.append({\"Página\": nombre" in all_code
    assert "Páginas web bien clasificadas" in all_code
    assert "Pendiente: no se descargaron páginas reales" in all_code
