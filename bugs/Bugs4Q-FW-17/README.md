# Bugs4Q-FW-17

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-17` |
| Origen | Bugs4Q-Framework, bug 17 (`qiskit/17/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-aer#664](https://github.com/Qiskit/qiskit-aer/issues/664) ("Qasm simulator gives wrong result on measure when given a permutation", abierto el 19-mar-2020 y cerrado el 25-mar-2020) |
| Categoría (Framework) | output Wtong (sic; equivale a Output Wrong) |
| Archivos | `buggy_17.py`, `fixed_17.py`, `test_b17.py`, `test_f17.py` (los cuatro copiados sin cambios del Framework) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa aplica `X` al qubit 0 de un circuito de 3 qubits y mide con `qc.measure([1, 0, 2], [1, 0, 2])`, esperando que el `1` aparezca en el bit clásico 1 (`'010'`). El simulador devuelve `'001'`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: "{'001': 1}" != "{'010': 1}"
- {'001': 1}
?     -
+ {'010': 1}
?    +
```

El programa no lanza ninguna excepción; el fallo solo se detecta al comparar los conteos con los esperados.

El usuario esperaba recibir `{'010': 1}` (el qubit 0 guardado en el bit clásico 1), pero recibe `{'001': 1}`: el qubit 0 queda en el bit clásico 0.

## 3. Causa

Según la respuesta de un mantenedor en el issue, no es un defecto de Aer sino un malentendido de los argumentos de `measure`: la lista de qubits y la de bits clásicos se emparejan elemento a elemento (`zip`), así que `measure([1, 0, 2], [1, 0, 2])` mide `q1→c1`, `q0→c0`, `q2→c2`, igual que `measure([0, 1, 2], [0, 1, 2])`. La autora del issue aceptó que ese es el comportamiento especificado. Es un uso incorrecto de la API.

## 4. Corrección (`fixed`)

Cambio entre `buggy_17.py` y `fixed_17.py` (`modify_17.txt` del Framework):

```diff
-qc.measure([1, 0, 2], [1, 0, 2])
+qc.measure([1, 0, 2], [0, 1, 2])
```

(Además `fixed_17.py` tiene una línea en blanco extra.) El cambio está en el programa, no en la librería.

Con la lista de bits clásicos permutada, el emparejamiento queda `q1→c0`, `q0→c1`, `q2→c2`, de modo que el `1` del qubit 0 se guarda en el bit clásico 1 y el resultado es `'010'`, que es lo que el usuario quería.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.12.0`, `qiskit-aer==0.4.1` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra 0.12 usa alias de NumPy eliminados en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug17/requirements.txt`](../../envs/bug17/requirements.txt) |

El issue indica Aer `master` (marzo de 2020), sin versión de Python. Versiones probadas:

- Aer < 0.4.0 (p. ej. 0.3.4): no hay wheel para Python 3.8 en Windows.
- Terra 0.12.0 + Aer 0.4.1, Terra 0.13.0 + Aer 0.5.0 y Terra 0.16.4 + Aer 0.7.6 (todas con `numpy==1.19.5`): buggy falla y fixed pasa.

Se eligieron Terra 0.12.0 + Aer 0.4.1 por ser las versiones publicadas más cercanas a la fecha del issue y porque cumplen el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug17/.venv
envs/bug17/.venv/Scripts/python -m pip install -r envs/bug17/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 17

# opción B: manual
cd bugs/Bugs4Q-FW-17
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug17/.venv/Scripts/python -W ignore test_b17.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug17/.venv/Scripts/python -W ignore test_f17.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug17/.venv/bin/python` en lugar de `envs/bug17/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b17.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f17.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests ejecutan 1 shot con el método `statevector` y comprueban que los conteos sean `{'010': 1}`; solo cambia la lista de bits clásicos de `measure`. El resultado es determinista (no hay superposición).

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El Framework trae test para buggy y fixed; se usan sin modificar.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un uso incorrecto de la API (orden de argumentos de `measure`); el issue se cerró sin cambios en Aer. El resultado de buggy (`'001'`) es el correcto para ese código: el "bug" es la intención del usuario, fijada en el oráculo.
- Usa `execute(..., backend_options=...)`, API que desaparece en versiones modernas de Qiskit.
- El mensaje de error del test no señala la línea defectuosa (solo los conteos distintos); en C1 el modelo tiene que razonar sobre el emparejamiento qubit→bit de `measure` y el orden little-endian de los resultados.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
