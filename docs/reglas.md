# Gramática y reglas

La librería aprovecha que el Esperanto es **regular y sin excepciones**: la terminación de una palabra indica su categoría.

## Orden del análisis

1. **Números, puntuación y símbolos** (`1950` → `NUM`, `€` → `SYM`).
2. **Elisión**: `l'` → `la`; `dom'` → `domo`.
3. **Léxico cerrado**: preposiciones, conjunciones, pronombres, correlativos, numerales, partículas e interjecciones, con sus formas flexionadas (`min`, `miajn`, `tiujn`, `kien`).
4. **Reglas de terminación** para el resto de palabras.
5. **Nombres propios**: palabra en mayúscula que no empieza frase → `PROPN`.

## Terminaciones

| Final | POS | Rasgos | Ejemplo → lema |
|---|---|---|---|
| `-o(j)(n)` | NOUN | Number, Case | `kukojn` → `kuko` |
| `-a(j)(n)` | ADJ | Number, Case | `dolĉajn` → `dolĉa` |
| `-e(n)` | ADV | Case (dirección) | `hejmen` → `hejme` |
| `-i` | VERB | VerbForm=Inf | `manĝi` |
| `-as/-is/-os` | VERB | Tense=Pres/Past/Fut | `manĝis` → `manĝi` |
| `-us` | VERB | Mood=Cnd | `manĝus` → `manĝi` |
| `-u` | VERB | Mood=Imp | `manĝu` → `manĝi` |
| `-ant-/-int-/-ont-` + `a/e` | ADJ/ADV | VerbForm=Part, Voice=Act | `manĝanta` → `manĝi` |
| `-at-/-it-/-ot-` + `a/e` | ADJ/ADV | VerbForm=Part, Voice=Pass | `kuirita` → `kuiri` |

## Correlativos

Se generan con la tabla de Zamenhof: prefijos `ki-`, `ti-`, `i-`, `ĉi-`, `neni-` y sufijos `-u`, `-o`, `-a`, `-e`, `-el`, `-es`, `-am`, `-al`, `-om`.
Los acabados en `-u`/`-o` son `PRON`, los acabados en `-a`/`-es` son `DET` y el resto son `ADV`.

## Raíces

Se eliminan sufijos (`-et-`, `-eg-`, `-aĵ-`, `-ej-`, `-ist-`, `-ul-`, `-il-`, `-ec-`, `-ig-`, `-iĝ-`, `-ad-`, `-uj-`, `-ism-`, `-ebl-`, `-ind-`, `-em-`) y prefijos (`mal-`, `mis-`, `dis-`), siempre que queden al menos 3 letras.

## Limitaciones conocidas

- **Falsos participios**: raíces como `tomat-` o `salat-` acaban igual que un sufijo participial. Se resuelven con la lista `PARTICIPLE_EXCEPTIONS`, que no puede ser completa.
- **Participios sustantivados** (`manĝanto`, comensal): se dejan como sustantivos, porque hay muchos sustantivos que acaban igual (`elefanto`, `biskvito`).
- **Nombres extranjeros**: `Napoleon` se interpreta como acusativo de `Napoleo`. A principio de frase no se puede saber si una palabra es nombre propio.
- **Raíces**: el recorte de afijos es aproximado (`ekzemplo` conserva `ek-` porque ese prefijo no se recorta). Hay una lista de excepciones (`NO_STRIP`) para casos como `ĉokolado`.
- **Palabras extranjeras en `-i`** (`suŝi`) se etiquetan como verbos.
