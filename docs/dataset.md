# Dataset

## Contrato de datos

`data/dataset.csv`: UTF-8, separador `;`, cabecera `text;class` y un párrafo por fila.

Clases: `comida`, `bebida` y `postre` (temática gastronomía).

## Resultado de la generación (noviembre de 2026)

| Clase | Categorías de Vikipedio | Artículos | Párrafos |
|---|---|---|---|
| comida | Manĝaĵoj, Manĝoj, Supoj, Salatoj, Viando, Legomoj | 200 | 1.186 |
| bebida | Trinkaĵoj, Alkoholaĵoj, Senalkoholaĵoj, Kafo, Teoj | 200 | 1.183 |
| postre | Dolĉaĵoj, Desertoj, Kukoj, Tortoj | 148 | 783 |

Todas las clases superan los 300 párrafos recomendados. `postre` tiene menos porque en Vikipedio hay menos artículos de esa temática.

**Párrafos descartados por el script** (`noise_report.json`):

| Motivo | Párrafos |
|---|---|
| Título de sección | 889 |
| Demasiado corto (menos de 40 caracteres) | 840 |
| Sección final (Referencoj, Vidu ankaŭ...) | 388 |
| No reconocido como Esperanto | 91 |
| Duplicado | 2 |
| Etiqueta contradictoria | 2 |

Además, se descartaron 62 artículos ambiguos (aparecían en varias clases a la misma profundidad), 11 artículos reservados para la prueba web y 11 listas.

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

## Revisión de etiquetas dudosas

Para localizar el ruido que queda tras los filtros, se predijo cada párrafo con un modelo que no lo había visto: lemas de `eonlp`, TF-IDF y regresión logística, con validación cruzada de 5 partes **por artículos**. Un párrafo se marca como **dudoso** si el modelo contradice su etiqueta con una confianza de 0,8 o más.

Resultado: **117 párrafos dudosos de 3.152 (3,7 %)**, recogidos en `data/revision_etiquetas.csv`.

| Etiqueta \ predicción | bebida | comida | postre |
|---|---|---|---|
| bebida | – | 13 | 18 |
| comida | 22 | – | 19 |
| postre | 29 | 16 | – |

Cada párrafo se ha revisado a mano y su columna `decision` indica una de estas opciones:

- `mantener`: la etiqueta es correcta y el modelo se equivoca (por ejemplo, un vino que se sirve con postres sigue siendo bebida).
- `cambiar_a_<clase>`: el párrafo habla claramente de otra clase.
- `eliminar`: el párrafo no habla de ninguna de las tres clases (botánica, historia, cifras...).

| Decisión | Párrafos |
|---|---|
| mantener | 67 |
| cambiar de clase | 17 (10 a bebida, 6 a postre, 1 a comida) |
| eliminar | 33 |

En el **57 %** de los casos dudosos la etiqueta era correcta y se equivocaba el modelo. Los errores reales de etiqueta son **50 párrafos (1,6 % del dataset)**: 17 de otra clase y 33 que no tratan de gastronomía.

**Qué hemos observado:**

- Muchos casos son párrafos que hablan de otra clase dentro de un artículo, por ejemplo una bebida servida con postre o un ingrediente que se usa en postres.
- Los párrafos a eliminar son sobre todo botánica (planta del café, hibisco, vid), historia de empresas (Cadbury, Haribo, Menier), química y anécdotas.
- Algunos artículos acumulan varios dudosos (Mielo, Cerealo, Citrono, Sabdarifo, Oliv-oleo). Son temas a caballo entre clases, y el artículo entero podría estar en la clase discutible (por ejemplo, *Panama raspaĵo*, un hielo raspado dulce, está en bebida).

La revisión **no modifica `dataset.csv`**, que sigue siendo exactamente lo que genera el script (reproducible). Sirve para cuantificar el ruido de etiquetas y justificar los errores del modelo.

## Control de calidad previo a la entrega

Comprueba que cada clase tenga artículos y, preferiblemente, más de 300 párrafos (recomendación del enunciado). Las categorías para gastronomía se contrastaron en noviembre de 2026; la API y su contenido pueden variar con el tiempo. Si Wikipedia no devuelve contenido, el programa aborta antes de publicar un dataset incompleto.

**Nota:** La proporción de tokens que nuestra librería reconoce como Esperanto es una heurística, no un detector lingüístico validado. Los desacuerdos del clasificador con las etiquetas sugieren candidatos a revisión, pero no representan errores comprobados sin evaluación manual.
