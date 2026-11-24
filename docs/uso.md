# Guía de uso

## Crear el modelo y analizar un texto

```python
import eonlp

nlp = eonlp.load()              # equivalente a spacy.load(...)
doc = nlp("Mi trinkas kafon. Vi manĝas kukon!")
```

## Recorrer los tokens

Cada `Token` tiene estos atributos:

| Atributo | Descripción | Ejemplo (`kukojn`) |
|---|---|---|
| `text` | texto original | `kukojn` |
| `lower_` | en minúscula | `kukojn` |
| `lemma_` | lema | `kuko` |
| `pos_` | categoría (UD) | `NOUN` |
| `morph` | rasgos morfológicos | `Case=Acc\|Number=Plur` |
| `root_` | raíz sin afijos | `kuk` |
| `is_stop`, `is_punct`, `is_alpha`, `like_num` | indicadores | `False`, `False`, `True`, `False` |
| `i`, `idx` | posición en tokens y en caracteres | depende del texto |

```python
for t in doc:
    print(t.text, t.lemma_, t.pos_, str(t.morph), t.is_stop)
```

## Frases y fragmentos

```python
[s.text for s in doc.sents]     # ['Mi trinkas kafon.', 'Vi manĝas kukon!']
doc[1:3].text                   # 'trinkas kafon'
```

## Preparar texto para un clasificador

`Doc.words` devuelve las palabras sin stopwords ni puntuación, con el atributo que se elija:

```python
doc.words()                     # lemas:  ['trinki', 'kafo', 'manĝi', 'kuko']
doc.words("lower_")             # formas: ['trinkas', 'kafon', 'manĝas', 'kukon']
doc.words("root_")              # raíces: ['trink', 'kaf', 'manĝ', 'kuk']
```

## Gestionar las stopwords

```python
"kaj" in nlp.stop_words         # True
nlp.add_stop_words("fari", "uzi")
nlp.remove_stop_words("ne")
nlp2 = eonlp.load(stop_words=["la", "kaj"])   # lista propia
```

Las stopwords se comprueban por forma **y por lema**: `estas`, `estis` y `estos` son stopwords porque su lema `esti` lo es.

## Otras utilidades

```python
doc.count_by("pos_")            # {'PRON': 2, 'VERB': 2, 'NOUN': 2, 'PUNCT': 2}
doc.esperanto_ratio()           # proporción de palabras reconocidas como Esperanto
doc.to_json()                   # exportar el análisis
list(nlp.pipe(["kafo", "teo"])) # analizar muchos textos
```
