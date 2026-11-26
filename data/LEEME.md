# Carpeta `data/`

Ficheros generados con `python scripts/build_dataset.py --config config/gastronomio.json --out data` (noviembre de 2026).

| Fichero | Contenido |
|---|---|
| `dataset.csv` | Dataset oficial: UTF-8, separador `;`, columnas `text;class`, un párrafo por fila (3.152 párrafos). |
| `dataset_meta.csv` | Igual, con una tercera columna `article` (artículo de origen). Se usa en el cuaderno para separar entrenamiento y prueba por artículos. |
| `articles.json` | Artículos de Vikipedio usados en cada clase. |
| `noise_report.json` | Párrafos descartados por motivo, artículos ambiguos y resumen por clase. |
| `revision_etiquetas.csv` | Párrafos con etiqueta posiblemente dudosa y la decisión de la revisión manual (ver `docs/dataset.md`). |
