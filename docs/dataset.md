# Dataset

## Contrato de datos

`data/dataset.csv`: UTF-8, separador `;`, cabecera `text;class` y un párrafo por fila.

Clases: `comida`, `bebida` y `postre` (temática gastronomía).

## Ficheros generados

| Fichero | Contenido |
|---|---|
| `data/dataset.csv` | Dataset que cumple el contrato |
| `data/dataset_meta.csv` | Igual que el anterior, con una columna `article` (artículo de origen) |
| `data/articles.json` | Artículos usados por clase |
| `data/noise_report.json` | Párrafos descartados por motivo y resumen por clase |

## Cómo se genera

```bash
pip install -e ".[dataset]"
python scripts/build_dataset.py --config config/gastronomio.json --out data
```

1. **Artículos**: se leen las categorías de Vikipedio indicadas en `config/gastronomio.json` y sus subcategorías directas.
   No se entra en una subcategoría que sea categoría raíz de otra clase (así `Manĝaĵoj` no arrastra `Dolĉaĵoj`).
2. **Asignación**: si un artículo aparece en varias clases, se queda en la que lo contiene a menor profundidad (la más específica). Si hay empate, se descarta por ambiguo.
3. **Reservados**: las páginas que se usan en el cuaderno para la prueba web nunca entran en el dataset.
4. **Muestra**: se eligen al azar, con semilla fija, hasta `max_articles_per_class` artículos por clase.
5. **Párrafos**: se descartan los títulos, los párrafos cortos, todo lo que va después de *Referencoj*, *Vidu ankaŭ*, etc., y los párrafos con menos de un 60 % de palabras reconocidas como Esperanto por `eonlp`.
6. **Limpieza**: se eliminan los duplicados y los párrafos que aparecen con dos etiquetas distintas.

## Ruido de etiquetas

Cada párrafo hereda la etiqueta de su artículo. Un párrafo como *"Ĝi estis fondita en 1950"* no dice nada de la clase.
El ruido se trata en dos niveles:

- **En el script**: filtros de longitud, sección e idioma, cuyos recuentos se guardan en `noise_report.json`.
- **En el cuaderno**: se mide con predicciones fuera de muestra. Los párrafos que el modelo contradice con mucha confianza se consideran posibles etiquetas dudosas.

## Control de calidad previo a la entrega

Comprueba que cada clase tenga artículos y, preferiblemente, más de 300 párrafos (recomendación del enunciado). Las categorías para gastronomía se contrastaron en noviembre de 2026; la API y su contenido pueden variar con el tiempo. Si Wikipedia no devuelve contenido, el programa aborta antes de publicar un dataset incompleto.

**Nota:** La proporción de tokens que nuestra librería reconoce como Esperanto es una heurística, no un detector lingüístico validado. Los desacuerdos del clasificador con las etiquetas sugieren candidatos a revisión, pero no representan errores comprobados sin evaluación manual.
