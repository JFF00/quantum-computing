# Bugs4Q-FW-3

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-3` |
| Origen | Bugs4Q-Framework, bug 3 (`qiskit/3/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-experiments#302](https://github.com/Qiskit/qiskit-experiments/issues/302) ("`ProcessTomography` analysis step errors", abierto y cerrado el 04-ago-2021) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_3.py`, `fixed_3.py` (copiados sin cambios); `test_b3.py` (de `test_b3(failed).py`) y `test_f3.py`, adaptados (ver §7); `framework_tests/test_b3(failed).py`, `framework_tests/test_f3.py` (tests originales del Framework, sin cambios, conservados como referencia) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa ejecuta una tomografía de proceso de un qubit sobre un simulador Aer con el ruido de `FakeParis`. La ejecución sin análisis funciona, pero con `analysis=True` el post-procesado falla. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
Post processing function failed:
Traceback (most recent call last):
  ...
AttributeError: 'PauliMeasurementBasis' object has no attribute '_mats'
...
AssertionError: 'ERROR' != 'DONE'
```

La excepción (`AttributeError`) se lanza dentro del post-procesado y `qiskit-experiments` la captura y la registra: `block_for_results()` no la propaga y el programa termina sin error. Solo se ve en el log y en el estado del experimento (`ERROR`).

El usuario debería haber recibido el experimento con el análisis completado (con la corrección, el estado es `DONE` y hay 4 resultados de análisis); recibió un experimento en estado `ERROR` y sin resultados de análisis.

## 3. Causa

El autor del issue no identifica la causa ("I'm not familiar with the internals"). Del traceback y del diff se deduce que se pasa `PauliMeasurementBasis()` como `preparation_basis`; el ajuste por inversión lineal necesita una base de preparación (accede a `basis._mats`, atributo que la base de medida no tiene). Es un mal uso de la API (base de medida en lugar de base de preparación), no un defecto de Qiskit; el issue se cerró a la media hora. Solo se consultó el cuerpo del issue, no los comentarios del cierre.

## 4. Corrección (`fixed`)

Cambio entre `buggy_3.py` y `fixed_3.py` (`modify_3.txt` del Framework):

```diff
-tomo = ProcessTomography(
+# or       tomo = ProcessTomography(circuit=circ)
+tomo = ProcessTomography(                   
 ...
-    preparation_basis=PauliMeasurementBasis(),
+    preparation_basis=PauliPreparationBasis(),
```

El cambio está en el programa, no en la librería.

Con `PauliPreparationBasis()` como base de preparación (que es también la opción por defecto, de ahí el comentario `ProcessTomography(circuit=circ)`), se generan 12 circuitos en lugar de 9 y el ajuste encuentra los estados de preparación que necesita, así que el análisis termina correctamente.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-experiments==0.1.0`, `qiskit-terra==0.18.1`, `qiskit-aer==0.8.2` (`qiskit-ibmq-provider` instalado como dependencia de `qiskit-experiments`) |
| Dependencias fijadas a mano | ninguna aparte de los tres paquetes de Qiskit (el resto lo resolvió `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug3/requirements.txt`](../../envs/bug3/requirements.txt) |

El issue indica `qiskit-experiments` 0.1.0, `qiskit-terra` 0.18.1, `qiskit-aer` 0.8.2 y Python 3.8 (macOS Big Sur). Se usaron exactamente esas versiones de los tres paquetes y no se probaron otras: con ellas el `AttributeError` del issue aparece tal cual y, con los tests adaptados, se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug3/.venv
envs/bug3/.venv/Scripts/python -m pip install -r envs/bug3/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 3

# opción B: manual
cd bugs/Bugs4Q-FW-3
../../envs/bug3/.venv/Scripts/python -W ignore test_b3.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug3/.venv/Scripts/python -W ignore test_f3.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug3/.venv/bin/python` en lugar de `envs/bug3/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b3.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f3.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban lo mismo: que el experimento con `analysis=True` termina en estado `DONE` (`self.assertEqual(experiment.status(), 'DONE', experiment.errors())`). La simulación es con ruido y sin semilla, pero la aserción solo mira si el análisis termina, no los valores.

**Modificación respecto del Framework.** El Framework trae `test_b3(failed).py` (copiado como `test_b3.py`) y `test_f3.py`, que terminan con `self.assertIn('AttributeError', tomo.circuits(), "AttributeError not raised")`: busca la cadena `'AttributeError'` dentro de la lista de circuitos, lo que nunca se cumple, así que ambos fallan siempre (comprobado en este entorno: exit 1 los dos, `'AttributeError' not found in [<qiskit.circuit.quantumcircuit.QuantumCircuit object ...>]`). Además, la excepción del issue no se propaga (ver §2), por lo que no puede capturarse con `assertRaises`. En `test_b3.py` y `test_f3.py` se mantuvo todo el código y solo se sustituyeron esas tres líneas finales por la aserción sobre `experiment.status()` (con un comentario que lo indica). Los originales se conservan en `framework_tests/` con su nombre original.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (un argumento) está en el programa del usuario, no en Qiskit.
- El test (adaptado) falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado con las mismas versiones de Qiskit que el issue.

Limitaciones:
- Los tests del Framework no sirven tal cual (fallan siempre); se cambió la aserción final.
- Es un mal uso de la API, no un defecto de Qiskit; la excepción queda oculta en el post-procesado, por lo que el síntoma depende de mirar `status()`/`errors()`.
- Usa `qiskit.test.mock.FakeParis` y `qiskit.providers.aer`, APIs que desaparecen en versiones modernas: solo es reproducible en versiones antiguas.
- El test de fixed tarda ~30 s (simulación con ruido de 12 circuitos y análisis).
- El mensaje del test incluye el traceback registrado por `experiment.errors()`, que termina en `'PauliMeasurementBasis' object has no attribute '_mats'`; no señala la línea del programa, pero nombra la clase usada por error, así que para C1 es una pista bastante directa.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
