# eonlp

**eonlp** es una librería de procesamiento del lenguaje natural para **Esperanto**,
construida desde cero y basada en reglas. Su interfaz imita la de spaCy.

Incluye:

- **Tokenizador**: palabras, números, compuestos con guion, elisión (`l'`, `dom'`) y sistema-x (`cx` → `ĉ`).
- **Segmentador de frases**, que respeta abreviaturas como `ekz.` o `ktp.`.
- **Lematizador**: `kukojn` → `kuko`, `manĝis` → `manĝi`, `kuirita` → `kuiri`.
- **Etiquetador POS** con las etiquetas de Universal Dependencies (`NOUN`, `VERB`, `ADP`, `PRON`...).
- **Rasgos morfológicos**: número, caso, tiempo, modo, voz (`Case=Acc|Number=Plur`).
- **Raíces** (*radikoj*): `kuketo`, `kafejo` → `kuk`, `kaf`.
- **Gestión de stopwords**, que se pueden añadir y quitar.
- Objetos **`Doc`**, **`Token`** y **`Span`**.

## Instalación

```bash
pip install git+https://github.com/USUARIO/REPOSITORIO.git
```

## Ejemplo rápido

```python
import eonlp

nlp = eonlp.load()
doc = nlp("La kuiristo bakis ĉokoladajn kukojn.")
for token in doc:
    print(token.text, token.lemma_, token.pos_, token.morph)
```

```text
La la DET PronType=Art
kuiristo kuiristo NOUN Case=Nom|Number=Sing
bakis baki VERB Mood=Ind|Tense=Past|VerbForm=Fin
ĉokoladajn ĉokolada ADJ Case=Acc|Number=Plur
kukojn kuko NOUN Case=Acc|Number=Plur
. . PUNCT
```
