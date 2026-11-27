# Análisis estático con LintQ

## Herramienta y versiones

| Elemento | Valor |
|---|---|
| Analizador | LintQ (consultas CodeQL para Qiskit) — https://github.com/sola-st/LintQ |
| Commit de LintQ | `481ca24dfabf032eb93cdf728369242b25a5216e` (14-feb-2025) |
| Licencia de LintQ | MIT |
| CodeQL CLI | 2.11.2 (versión exacta exigida por `REQUIREMENTS.md` de LintQ) |
| Dependencia de consultas | `codeql/python-all` 0.6.2 |
| Qiskit dentro de la imagen | 0.45.2 (lo instala el Dockerfile de LintQ; CodeQL extrae esta librería para resolver la API) |
| Imagen Docker | `lintq`, construida localmente desde `config/dockerimage_for_codeql/DockerfileTemplate` |
| Suite usada | `LintQ-all.qls` (10 checkers: 6 de precisión `high` + 4 `medium`) |

La precisión de cada warning se guarda en la tabla, para poder filtrar después solo los
`high` (equivalente a `LintQ.qls`, la suite del artículo de LintQ) si así lo decide el
protocolo. Se ejecuta la suite completa para no perder información.

### Checkers incluidos

Descripciones resumidas del campo `@description` de cada consulta `.ql` en
`qlint/codeql/src/`:

| Precisión | ID | Descripción |
|---|---|---|
| high | `ql-conditional-without-measurement` | Puerta condicional aplicada sin una medición previa del qubit |
| high | `ql-double-measurement` | Dos mediciones consecutivas del mismo qubit |
| high | `ql-ghost-composition` | `compose()` sin `inplace=True` y sin guardar el resultado: el circuito compuesto se pierde |
| high | `ql-measure-all-abuse` | `measure_all` usado cuando debería usarse un registro clásico ya inicializado |
| high | `ql-op-after-optimization` | Operación (puerta o medición) añadida a un circuito ya transpilado |
| high | `ql-operation-after-measurement` | Medición de un qubit seguida de una puerta sobre el mismo qubit |
| medium | `ql-constant-classic-bit` | Qubits nunca usados pero medidos: bit clásico constante |
| medium | `ql-deprecated-identity` | Uso de la API obsoleta `iden()` en lugar de `identity()` |
| medium | `ql-oversized-circuit` | Circuito creado con más qubits de los que realmente usa |
| medium | `ql-unmeasurable-qubits` | Menos bits clásicos que qubits: el estado completo no puede medirse |

## Instalación (Windows, Docker Desktop)

Desde la raíz del proyecto (`tools/` está en `.gitignore`):

```bash
git clone https://github.com/sola-st/LintQ tools/LintQ
git -C tools/LintQ checkout 481ca24dfabf032eb93cdf728369242b25a5216e
cd tools/LintQ
docker build -f config/dockerimage_for_codeql/DockerfileTemplate -t lintq .
```

El script oficial `automation_scripts/create_docker_image_locally.py` no funciona en Windows
(`os.getuid()`); como el template no contiene el marcador `{your-UID}`, construirlo
directamente da la misma imagen. Comprobación (en Git Bash anteponer `MSYS_NO_PATHCONV=1`):

```bash
docker run --rm lintq codeql version --format=terse      # 2.11.2
docker run --rm lintq codeql pack ls /usr/local/codeql-home/
# Found mattepalte/qiskit@0.0.1 / mattepalte/qlint@0.0.1 / mattepalte/qlint-tests@0.0.0
```

## Ejecución

```powershell
py scripts/run_static_analysis.py            # bugs de data/selected_bugs.csv
py scripts/run_static_analysis.py 7 21       # bugs concretos
```

Cada archivo (`buggy_N.py`, `fixed_N.py`, `fixed_N_min.py`) se analiza **por separado**, con
su propia base de datos CodeQL, para que los warnings de cada versión no se mezclen. Cada
variante tarda unos 8 minutos (unos 5 de extracción, porque incluye la librería Qiskit,
y unos 3 de análisis).

## Salidas

| Archivo | Contenido |
|---|---|
| `bugs/<id>/static_analysis/<variante>.sarif` | Reporte original de LintQ (SARIF 2.1.0), sin modificar |
| `bugs/<id>/static_analysis/<variante>.csv` | Warnings: regla, precisión, severidad, archivo, línea, mensaje |
| `bugs/<id>/static_analysis/<variante>.log` | Comandos exactos, versiones, exit codes, stdout/stderr |
| `bugs/<id>/static_analysis/summary.json` | Conteos por regla y diferencia buggy vs fixed / fixed_min |
| `data/static_warnings.csv` | Tabla agregada de todos los bugs |

En la diferencia buggy/fixed, dos warnings se consideran el mismo si tienen la misma regla y
el mismo mensaje, ignorando las posiciones `(línea, columna)` que cita el mensaje.

## Reglas de interpretación

- Un exit code distinto de 0 se registra como `analysis_error`; **no** equivale a "0 warnings".
- "0 warnings" solo se reporta si `create` y `analyze` terminaron con exit 0.
- Que un warning desaparezca en `fixed` no prueba que señale la causa del bug: puede
  desaparecer porque el fix reescribe el código. Hay que compararlo también con la referencia
  mínima (`fixed_N_min.py`) cuando existe, y revisarlo a mano.
- Para el prompt C2/C3 se usarán solo los warnings de la versión **buggy**.

## Resultados del piloto

Ejecución: 2026-11-27, suite `LintQ-all.qls`, imagen `lintq` (sha256:94b918cf6087).
Las 11 variantes terminaron con exit 0 en `create` y `analyze` (ningún `analysis_error`).

| Bug | Variante | Warnings | Regla (precisión) | Línea(s) | ¿Relacionado con el bug? |
|---|---|---|---|---|---|
| FW-7 | buggy | 1 | `ql-unmeasurable-qubits` (media) | 13 | No. `QuantumCircuit(qr)` sin bits clásicos; el circuito solo se usa para construir el DAG. |
| FW-7 | fixed | 1 | `ql-unmeasurable-qubits` (media) | 13 | Idéntico a buggy. |
| FW-8 | buggy | 2 | `ql-unmeasurable-qubits` (media) | 7, 14 | No. Los circuitos `circ` y `qc` se convierten a `Operator`, no se miden. |
| FW-8 | fixed | 2 | `ql-unmeasurable-qubits` (media) | 7, 14 | Idéntico a buggy. |
| FW-14 | buggy | 1 | `ql-unmeasurable-qubits` (media) | 6 | No. `state` es un estado para opflow (valor esperado), no se mide. |
| FW-14 | fixed | 1 | `ql-unmeasurable-qubits` (media) | 6 | Idéntico a buggy. |
| FW-21 | buggy | 2 | `ql-operation-after-measurement` (alta) | 18 (`cx`), 19 (`cz`) | Parcial. Patrón cercano (operar tras medir), no la causa (medir q2 después de `execute`). |
| FW-21 | fixed | 0 | — | — | El fix del Framework reescribe con `c_if`. |
| FW-21 | fixed_min | 2 | `ql-operation-after-measurement` (alta) | 20, 21 | Los mismos 2 warnings persisten en una corrección que pasa el test. |
| FW-29 | buggy | 1 | `ql-unmeasurable-qubits` (media) | 25 | No. `qpe` tiene 4 qubits y 3 bits: el qubit del estado propio no se mide a propósito. |
| FW-29 | fixed | 1 | `ql-unmeasurable-qubits` (media) | 30 | Idéntico a buggy (solo cambia la línea). |

Conclusiones:

- En FW-7, 8, 14 y 29 el único warning es `ql-unmeasurable-qubits` (precisión media), igual en
  buggy y fixed, y no relacionado con el bug. Ninguna regla de LintQ cubre índices de qubits,
  pasos faltantes de la API ni la estructura de la QFT.
- FW-21 es el único caso con un warning de precisión alta cercano al bug, pero no señala la
  causa y persiste en `fixed_21_min.py`.
- Implicación para C2/C3: en 4 de 5 bugs el prompt C2 contendrá solo warnings irrelevantes.
  Hay que revisar a mano si el modelo modifica código por esos warnings (p. ej. agrega
  mediciones innecesarias).

Detalle por bug: `bugs/<id>/static_analysis/{buggy,fixed,fixed_min}.{sarif,csv,log}` y
`summary.json`. Tabla agregada: `data/static_warnings.csv`.

## Bugs fuera del piloto con warnings relacionados (FW-12, FW-28)

Ejecución individual con `run_static_analysis.py 12 28` (2026-11-27, misma imagen y suite).
Se eligieron revisando a mano el código de los 42 bugs y buscando los patrones que cubren
las reglas de LintQ; el cribado en lote (`scripts/screen_lintq_batch.py`) se interrumpió y
no produjo resultados.

| Bug | Variante | Warnings | Regla (precisión) | Línea | ¿Relacionado con el bug? |
|---|---|---|---|---|---|
| FW-12 | buggy | 1 | `ql-measure-all-abuse` (alta) | 6 | **Sí.** Es exactamente el bug: `measure_all()` sobre un circuito que ya tiene un registro clásico de 2 bits. |
| FW-12 | fixed | 0 | — | — | Desaparece con el fix (`measure(qc.qubits, qc.clbits)`). |
| FW-28 | buggy | 2 | `ql-deprecated-identity` (media) | 4 | **Sí.** Es exactamente el bug: `iden()` fue eliminado. |
| FW-28 | buggy | | `ql-unmeasurable-qubits` (media) | 3 | No (circuito sin bits clásicos; igual en fixed). |
| FW-28 | fixed | 1 | `ql-unmeasurable-qubits` (media) | 3 | No. `ql-deprecated-identity` desaparece con el fix (`id(0)`). |

Notas:

- FW-12 es "Output Wrong" (salida con un registro extra, sin excepción) y cumple los criterios
  del piloto; se **añadió al piloto** (`data/selected_bugs.csv`) tras este análisis. Ojo: se
  eligió *por* tener un warning relacionado (sesgo de selección). Sus tests del Framework fueron
  adaptados (ver su README). Es el primer caso donde
  un warning de precisión alta señala la causa exacta y desaparece con el fix.
- FW-28 es "Throw Exceptions" (`AttributeError`), un cambio de nombre de API; no cumple el
  criterio del piloto de "no trivial", pero sirve como caso de control donde LintQ señala el bug.
