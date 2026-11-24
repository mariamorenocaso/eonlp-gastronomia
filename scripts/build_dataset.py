"""Construye el dataset etiquetado (text;class) a partir de la Wikipedia en Esperanto.

Uso (desde la raíz del repositorio, con la librería instalada: ``pip install -e .[dataset]``)::

    python scripts/build_dataset.py --config config/gastronomio.json --out data

Genera en la carpeta de salida:

* ``dataset.csv``: el dataset que cumple el contrato de datos (UTF-8, ``;``, columnas ``text;class``).
* ``dataset_meta.csv``: lo mismo con una tercera columna ``article`` (artículo de origen).
  Sirve para separar entrenamiento y prueba por artículos. Es un fichero aparte para no romper el contrato.
* ``articles.json``: artículos usados por clase (las categorías de Wikipedia cambian con el tiempo).
* ``noise_report.json``: párrafos descartados por motivo y resumen por clase.

Todo el proceso es reproducible: la elección de artículos usa una semilla fija y
los párrafos se ordenan antes de guardar.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests

import eonlp

API = "https://eo.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "eonlp-dataset/1.0 (proyecto universitario de Mineria de Textos)"}
PAUSE = 0.2  # segundos entre peticiones para no saturar la API

nlp = eonlp.load()


# ---------------------------------------------------------------------------
# Acceso a la API de Wikipedia
# ---------------------------------------------------------------------------

def api_get(params: dict, retries: int = 3) -> Optional[dict]:
    """Hace una petición a la API con reintentos. Devuelve ``None`` si falla siempre."""
    params = {**params, "format": "json", "formatversion": "2"}
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(API, params=params, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as err:
            print(f"   intento {attempt}/{retries} fallido: {err}", file=sys.stderr)
            time.sleep(2 * attempt)
    return None


def category_members(category: str) -> Tuple[List[str], List[str]]:
    """Devuelve (artículos, subcategorías) de una categoría, siguiendo la paginación."""
    articles, subcats = [], []
    params = {"action": "query", "list": "categorymembers", "cmtitle": f"Kategorio:{category}",
              "cmtype": "page|subcat", "cmlimit": "500"}
    while True:
        data = api_get(params)
        if data is None:
            break
        for m in data.get("query", {}).get("categorymembers", []):
            if m["ns"] == 14:
                subcats.append(m["title"].split(":", 1)[1])
            elif m["ns"] == 0:
                articles.append(m["title"])
        if "continue" not in data:
            break
        params.update(data["continue"])
        time.sleep(PAUSE)
    return articles, subcats


def article_text(title: str) -> str:
    """Texto plano de un artículo (con los títulos de sección como ``== Título ==``)."""
    data = api_get({"action": "query", "prop": "extracts", "explaintext": "1",
                    "exsectionformat": "wiki", "redirects": "1", "titles": title})
    if not data:
        return ""
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return ""
    return pages[0].get("extract", "") or ""


# ---------------------------------------------------------------------------
# Elección de artículos
# ---------------------------------------------------------------------------

def collect_candidates(classes: dict, depth: int) -> Dict[str, Dict[str, int]]:
    """Para cada clase, devuelve ``{artículo: profundidad mínima a la que aparece}``.

    No se entra en una subcategoría que sea categoría raíz de otra clase:
    así ``Manĝaĵoj`` no arrastra a ``Dolĉaĵoj`` y los postres no acaban como "comida".
    """
    seeds = {cat: name for name, c in classes.items() for cat in c["categories"]}
    candidates: Dict[str, Dict[str, int]] = {}
    for name, cfg in classes.items():
        found: Dict[str, int] = {}
        visited: Set[str] = set()
        queue = [(cat, 0) for cat in cfg["categories"]]
        while queue:
            cat, level = queue.pop(0)
            if cat in visited:
                continue
            visited.add(cat)
            arts, subs = category_members(cat)
            if not arts and not subs:
                print(f"   AVISO: categoría vacía o no accesible: Kategorio:{cat}")
            for a in arts:
                found[a] = min(found.get(a, level), level)
            if level < depth:
                queue += [(s, level + 1) for s in subs if seeds.get(s, name) == name]
            time.sleep(PAUSE)
        candidates[name] = found
        print(f"{name}: {len(found)} artículos candidatos en {len(visited)} categorías")
    return candidates


def assign_articles(candidates: Dict[str, Dict[str, int]], cfg: dict) -> Tuple[Dict[str, List[str]], dict]:
    """Asigna cada artículo a una sola clase y elige una muestra por clase.

    Si un artículo aparece en varias clases, se queda en la que lo contiene a
    menor profundidad (la más específica). Si empatan, se descarta.
    """
    reserved = set(cfg.get("reserved_articles", []))
    owner: Dict[str, Optional[str]] = {}
    best_depth: Dict[str, int] = {}
    for cls, arts in candidates.items():
        for art, d in arts.items():
            if art not in best_depth or d < best_depth[art]:
                best_depth[art], owner[art] = d, cls
            elif d == best_depth[art] and owner[art] != cls:
                owner[art] = None                          # empate: ambiguo

    stats = {"ambiguous": sum(1 for o in owner.values() if o is None), "reserved": 0, "lists": 0}
    rng = random.Random(cfg["seed"])
    chosen: Dict[str, List[str]] = {}
    for cls, ccfg in cfg["classes"].items():
        valid = []
        for art, o in owner.items():
            if o != cls:
                continue
            if art in reserved:
                stats["reserved"] += 1
                continue
            if art.lower().startswith("listo de") or ":" in art:
                stats["lists"] += 1
                continue
            valid.append(art)
        valid.sort()
        if len(valid) < cfg["min_articles_per_class"]:
            # COMPLEMENTAR, no sustituir: antes se perdían artículos ya encontrados.
            # Evitar además artículos ambiguos o asignados a otra clase.
            extras = [a for a in ccfg.get("fallback_articles", [])
                      if a not in valid and a not in reserved
                      and (a not in owner or owner[a] == cls)]
            print(f"   {cls}: {len(valid)} artículos válidos; "
                  f"se añaden {len(extras)} candidatos de respaldo no ambiguos")
            valid.extend(extras)
        chosen[cls] = rng.sample(valid, min(len(valid), cfg["max_articles_per_class"]))
    return chosen, stats


# ---------------------------------------------------------------------------
# De artículo a párrafos
# ---------------------------------------------------------------------------

_HEADING = re.compile(r"^=+\s*(.*?)\s*=+$")


def clean_paragraph(text: str) -> str:
    """Limpia un párrafo y garantiza que no rompe el CSV."""
    text = text.replace(";", ",")                 # el separador del CSV no puede aparecer en el texto
    text = re.sub(r"\[\d+\]", "", text)           # referencias [1]
    text = re.sub(r"https?://\S+", "", text)      # URLs
    return re.sub(r"\s+", " ", text).strip()


def split_paragraphs(text: str, cfg: dict, reasons: Counter) -> List[str]:
    """Divide un artículo en párrafos útiles y cuenta los descartados por motivo."""
    stop_sections = {s.lower() for s in cfg.get("stop_sections", [])}
    out = []
    for raw in text.split("\n"):
        p = clean_paragraph(raw)
        if not p:
            continue
        heading = _HEADING.match(p)
        if heading:
            if heading.group(1).lower() in stop_sections:
                reasons["seccion_final"] += 1
                break                                 # referencias, enlaces...: no seguimos
            reasons["titulo"] += 1
            continue
        if len(p) < cfg["min_paragraph_chars"]:
            reasons["corto"] += 1
            continue
        if nlp(p).esperanto_ratio() < cfg["min_esperanto_ratio"]:
            reasons["no_esperanto"] += 1              # listas de nombres, otros idiomas...
            continue
        out.append(p)
    return out


def build(cfg: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    print("1) Leyendo categorías de Vikipedio...")
    candidates = collect_candidates(cfg["classes"], cfg["depth"])
    chosen, art_stats = assign_articles(candidates, cfg)
    print({c: len(a) for c, a in chosen.items()}, "artículos por clase")

    print("2) Descargando artículos...")
    rows: List[Tuple[str, str, str]] = []
    reasons: Counter = Counter()
    missing = []
    for cls, titles in chosen.items():
        for title in titles:
            text = article_text(title)
            time.sleep(PAUSE)
            if not text:
                missing.append(title)
                continue
            for p in split_paragraphs(text, cfg, reasons):
                rows.append((p, cls, title))

    print("3) Limpieza final...")
    by_text = defaultdict(set)
    for text, cls, _ in rows:
        by_text[text].add(cls)
    conflict = {t for t, cs in by_text.items() if len(cs) > 1}
    seen, final = set(), []
    for text, cls, title in sorted(rows, key=lambda r: (r[1], r[2], r[0])):
        if text in conflict:
            reasons["etiqueta_contradictoria"] += 1
            continue
        if text in seen:
            reasons["duplicado"] += 1
            continue
        seen.add(text)
        final.append((text, cls, title))

    if not final:
        sys.exit("No se ha obtenido ningún párrafo. ¿Hay conexión con Wikipedia?")
    counts = Counter(cls for _, cls, _ in final)
    empty_classes = [cls for cls in cfg["classes"] if counts.get(cls, 0) == 0]
    if empty_classes:
        sys.exit(f"Dataset incompleto, clases sin párrafos: {empty_classes}. "
                 "Revisa conexión y categorías; no se guardará un CSV incompleto.")

    with open(out_dir / "dataset.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["text", "class"])
        w.writerows((t, c) for t, c, _ in final)
    with open(out_dir / "dataset_meta.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["text", "class", "article"])
        w.writerows(final)
    with open(out_dir / "articles.json", "w", encoding="utf-8") as f:
        json.dump(chosen, f, ensure_ascii=False, indent=2)

    per_class = Counter(c for _, c, _ in final)
    report = {
        "paragraphs_kept": len(final),
        "paragraphs_per_class": dict(per_class),
        "articles_per_class": {c: len(a) for c, a in chosen.items()},
        "articles_without_text": missing,
        "discarded_paragraphs": dict(reasons),
        "article_selection": art_stats,
    }
    with open(out_dir / "noise_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    for cls in cfg["classes"]:
        n = per_class.get(cls, 0)
        if n < 300:
            print(f"AVISO: '{cls}' tiene {n} párrafos reales (se recomiendan más de 300). "
                  f"Aumenta max_articles_per_class, revisa categorías o añade fuentes reales.")
        if n == 0:
            print(f"ERROR: clase '{cls}' sin datos: el dataset no sirve para entrenar 3 categorías.")
    if any(per_class.get(cls, 0) == 0 for cls in cfg["classes"]):
        sys.exit("Dataset incompleto: hay clases sin datos. Comprueba las categorías y la conexión.")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="config/gastronomio.json", help="fichero JSON de configuración")
    parser.add_argument("--out", default="data", help="carpeta de salida")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    build(cfg, Path(args.out))


if __name__ == "__main__":
    main()
