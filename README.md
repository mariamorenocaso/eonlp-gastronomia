# Clasificación de textos gastronómicos en Esperanto

Práctica de **Minería de Textos** (CUNEF, curso 2026/2027).
Integrantes: María Moreno, Adriana Díaz y Sofía Pérez.

Sistema completo para clasificar párrafos en Esperanto en tres categorías cercanas:
**comida**, **bebida** y **postre**.

| Fase | Qué contiene | Dónde |
|---|---|---|
| 1. Repositorio y dataset | Script reproducible que construye el dataset desde Vikipedio | `scripts/`, `config/`, `data/` |
| 2. Librería | `eonlp`: tokenizador, lematizador, POS, rasgos morfológicos, raíces, stopwords, Doc/Token/Span | `src/eonlp/`, `tests/`, `docs/` |
| 3. Cuaderno | Vectorización, entrenamiento, evaluación y clasificación de páginas web | `notebooks/` |

## Instalación de la librería

```bash
pip install git+https://github.com/USUARIO/REPOSITORIO.git
```

```python
import eonlp

nlp = eonlp.load()
doc = nlp("La kuiristo bakis ĉokoladajn kukojn.")
[(t.text, t.lemma_, t.pos_, str(t.morph)) for t in doc]
```

La documentación completa está en `docs/` y se publica en Read the Docs.

## Estado del dataset y verificación

**Pendiente de generar con conexión real.** Este ZIP no contiene `data/dataset.csv`, ni se han calculado métricas de entrenamiento sobre Wikipedia. Los tests automáticos y la ejecución offline del notebook se realizan con datos de prueba; no deben presentarse como resultados reales en la entrega.

## Dataset

Una vez generado, `data/dataset.csv` cumple el contrato de datos: UTF-8, separador `;`, cabecera `text;class` y un párrafo por fila.

Para regenerarlo:

```bash
pip install -e ".[dataset]"
python scripts/build_dataset.py --config config/gastronomio.json --out data
```

Para usar otra temática basta con otro fichero de configuración (categorías de Vikipedio por clase).
Más detalles en [`docs/dataset.md`](docs/dataset.md).

## Tests

```bash
pip install -e ".[test]"
pytest -v
```

Los tests se ejecutan automáticamente con GitHub Actions en cada *push* (`.github/workflows/tests.yml`).

## Cuaderno

`notebooks/clasificacion_gastronomia.ipynb` funciona en Google Colab sin ficheros locales:
instala la librería y descarga el dataset desde este repositorio.
Para usar el dataset de otro equipo basta con cambiar `DATASET_URL` en la primera celda.

La opción `REGENERAR_DATASET` puede reconstruir el dataset desde el propio cuaderno usando los scripts del repositorio (más lento, porque hace llamadas a Vikipedio). Si ninguna página real puede descargarse en la evaluación web, el cuaderno lo marca explícitamente: una demostración local **no sustituye** la clasificación de páginas reales.

## Estructura

```
├── config/gastronomio.json      # categorías de Vikipedio por clase y parámetros
├── data/                        # dataset generado (dataset.csv, dataset_meta.csv, ...)
├── docs/                        # documentación (MkDocs + Read the Docs)
├── notebooks/                   # cuaderno de la Fase 3
├── scripts/build_dataset.py     # construcción del dataset
├── src/eonlp/                   # librería
└── tests/                       # pruebas unitarias (pytest)
```

## Licencia

MIT. Los textos del dataset proceden de Vikipedio (CC BY-SA 4.0).
