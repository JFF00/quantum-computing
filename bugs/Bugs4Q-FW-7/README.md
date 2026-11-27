# Bugs4Q-FW-7

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-7` |
| Origen | Bugs4Q-Framework, bug 7 (`qiskit/7/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#3799](https://github.com/Qiskit/qiskit-terra/issues/3799) ("DAGCircuit.substitute_node_with_dag shuffles wires with custom controlled gate", abierto y cerrado el 05-feb-2020) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_7.py`, `fixed_7.py`, `test_b7.py`, `test_f7.py` (los cuatro copiados sin cambios del Framework) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa quita el control de una puerta `ghz` controlada sustituyendo el nodo del DAG por un DAG temporal con la puerta base. El circuito resultante tiene los cables desordenados: la puerta `ghz` queda aplicada sobre `qr_0, qr_1, qr_3` (en otro orden) en lugar de `qr_0, qr_1, qr_2`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: '    [14 chars]_0: ┤2     ├\n      │      │\nqr_1: ┤0     ├\n[74 chars]───┘' != '    [14 chars]_0: ┤1     ├\n      │      │\nqr_1: ┤0 ghz ├\n[74 chars]    '
```

No hay excepción; el fallo solo se ve al comparar el dibujo del circuito con el esperado.

El usuario debería obtener la puerta `ghz` sobre `qr_0, qr_1, qr_2` con `qr_3` libre; sin embargo recibe la puerta sobre cables permutados (incluido `qr_3`) y sin ningún aviso de error.

## 3. Causa

En el DAG temporal la puerta base se aplica sobre `node.qargs[1:]` (los qubits *físicos* del nodo original: `qr_1, qr_0, qr_2`). `substitute_node_with_dag` empareja los cables del DAG temporal **por posición** con los `qargs` del nodo, así que usar de nuevo los qubits originales provoca una doble permutación. En el issue se explica que el DAG de reemplazo debe construirse con sus propios cables en orden.

## 4. Corrección (`fixed`)

Cambio entre `buggy_7.py` y `fixed_7.py` (`modify_7.txt` del Framework):

```diff
         unctl_dag.apply_operation_back(node.op.base_gate,
-                                       node.qargs[node.op.num_ctrl_qubits:],
+                               qr[node.op.num_ctrl_qubits:],
                                        node.op.params)
```

El cambio está en el programa, no en la librería.

El cambio resuelve porque el DAG temporal aplica la puerta base sobre sus propios cables en orden (`qr[1:]`), en vez de sobre los qubits del nodo original. Así, cuando `substitute_node_with_dag` empareja por posición los cables del DAG temporal con los del nodo, la permutación se aplica una sola vez.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.14.2` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra 0.14 usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug7/requirements.txt`](../../envs/bug7/requirements.txt) |

El issue indica Terra `master` (feb-2020) y Python 3.7. Se probaron, en el mismo entorno, Terra 0.13.0, 0.14.2, 0.15.0, 0.16.4 y 0.18.3:

- 0.13.0: ambos tests fallan porque el dibujante de texto escribe `Ghz` (mayúscula) y los tests esperan `ghz`.
- 0.14.2 – 0.18.3: buggy falla y fixed pasa.

Se eligió 0.14.2, la versión más cercana a la fecha del issue que cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug7/.venv
envs/bug7/.venv/Scripts/python -m pip install -r envs/bug7/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 7

# opción B: manual
cd bugs/Bugs4Q-FW-7
$env:PYTHONIOENCODING = "utf-8"   # los tests imprimen caracteres de caja (┤ ├)
../../envs/bug7/.venv/Scripts/python -W ignore test_b7.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug7/.venv/Scripts/python -W ignore test_f7.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug7/.venv/bin/python` en lugar de `envs/bug7/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b7.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f7.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban los mismos tres dibujos de texto (circuito original, circuito tras la sustitución y DAG temporal); falla la segunda aserción. El test es determinista (no hay simulación).

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El Framework trae test para buggy y fixed; se usan sin modificar.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- El oráculo compara dibujos de texto, que cambian entre versiones de Qiskit (ver 0.13.0): el test es frágil fuera de la versión elegida.
- El issue fue cerrado como uso incorrecto de la API, no como defecto de Qiskit.
- El mensaje de error del test muestra la diferencia entre los dibujos, pero no indica la línea defectuosa (`apply_operation_back`), por lo que en C1 la reparación depende del conocimiento del LLM sobre `substitute_node_with_dag`.
- Entorno ejecutado en Windows, a diferencia de los bugs anteriores (macOS osx-64); la versión de Python es la misma (3.8.20).

## 9. Pendientes

- [x] Análisis estático (LintQ, 2026-11-27): 1 warning `ql-unmeasurable-qubits` (media) en buggy y en fixed; no relacionado con el bug. Ver `static_analysis/`.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.

## 10. Test a nivel de programa (piloto)

Seleccionado para el piloto de la semana 10. Los tests de las secciones anteriores llevan el código del programa copiado dentro, por lo que no pueden validar un parche. [`test_program_7.py`](test_program_7.py) (escrito para el proyecto) ejecuta en cambio el **archivo** indicado en la variable `BUG_PROGRAM` mediante [`scripts/program_harness.py`](../../scripts/program_harness.py), que captura stdout, las variables finales del programa y las llamadas a `execute()` (inyectando `seed_simulator=1234` si el programa no fija semilla).

**Oráculo.** Lee las variables `circuit` y `dag` del programa. Comprueba que, tras quitar el control, la puerta base queda aplicada sobre los mismos qubits objetivo, y en el mismo orden, que en la puerta controlada original. No depende del dibujo de texto (a diferencia de `test_b7.py`), por lo que es estable entre versiones.

El test no contiene el código corregido, para no filtrar la solución en la condición C1.

```powershell
cd bugs/Bugs4Q-FW-7
$env:BUG_PROGRAM = "buggy_7.py"; ../../envs/bug7/.venv/Scripts/python -W ignore test_program_7.py   # exit 1
$env:BUG_PROGRAM = "fixed_7.py"; ../../envs/bug7/.venv/Scripts/python -W ignore test_program_7.py   # exit 0
# o bien, desde la raíz: python scripts/run_bug_tests.py 7 --program-test
```

| Programa | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|
| `buggy_7.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/program_buggy_run1.log), [run2](logs/program_buggy_run2.log), [run3](logs/program_buggy_run3.log) |
| `fixed_7.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/program_fixed_run1.log), [run2](logs/program_fixed_run2.log), [run3](logs/program_fixed_run3.log) |

Fragmento de [`logs/program_buggy_run1.log`](logs/program_buggy_run1.log):

```
AssertionError: Lists differ: [1, 3, 0] != [1, 0, 2]
```

Para validar un parche: guardarlo como archivo en esta carpeta y ejecutar el test con `BUG_PROGRAM=<archivo del parche>`.
