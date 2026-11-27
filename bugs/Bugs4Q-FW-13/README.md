# Bugs4Q-FW-13

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-13` |
| Origen | Bugs4Q-Framework, bug 13 (`qiskit/13/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#6540](https://github.com/Qiskit/qiskit-terra/issues/6540) ("Error creating controlled unitary with nested QuantumCircuit objects.", abierto el 08-jun-2021, cerrado el 23-jun-2021) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_13.py`, `fixed_13.py` (copiados sin cambios del Framework); `test_b13.py`, `test_f13.py` (adaptados para este proyecto, ver sección 7); originales del Framework en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa añade un circuito `inner` dentro de otro circuito `outer` con `append` y luego intenta crear la versión controlada de `outer` con `outer_level.control()`. La llamada lanza una excepción. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
qiskit.exceptions.QiskitError: 'One or more instructions cannot be converted to a gate. "inner" is not a gate instruction'
...
qiskit.circuit.exceptions.CircuitError: 'The circuit contains non-unitary operations and cannot be controlled. Note that no qiskit.circuit.Instruction objects may be in the circuit for this operation.'
```

Sí se lanza una excepción (`CircuitError`, encadenada a la `QiskitError` que cita el issue) en la línea de `outer_level.control()`.

El usuario debería haber obtenido una puerta controlada de 3 qubits aplicada sobre `qc`, pero el programa se detiene con un error, aunque el circuito anidado es unitario (solo contiene una `X`).

## 3. Causa

Según la respuesta del mantenedor en el issue, Qiskit distingue entre `Gate` (operaciones unitarias, que se pueden controlar e invertir) e `Instruction` (todo lo demás). Al hacer `circuit1.append(circuit2)`, `circuit2` se convierte en una `Instruction`, y por eso `outer` ya no se puede controlar. Propone convertir explícitamente con `to_gate()` o usar `compose`. El autor del issue aceptó que es el comportamiento esperado: es un uso incorrecto de la API, no un defecto de Qiskit (cerrado sin PR).

## 4. Corrección (`fixed`)

Cambio entre `buggy_13.py` y `fixed_13.py` (`modify_13.txt` del Framework):

```diff
-outer_level.append(inner_level, [0,1])
+outer_level.append(inner_level.to_gate(), [0,1])
```

El cambio está en el programa, no en la librería.

Con `to_gate()` el circuito interno entra en `outer` como `Gate` y no como `Instruction`, así que `outer_level.control()` puede convertir todo `outer` en una puerta y crear su versión controlada.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.17.4` |
| Dependencias fijadas a mano | `numpy==1.19.5` (fijado por precaución, igual que en los demás bugs con Terra antiguo; no se probó con otras versiones de NumPy) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug13/requirements.txt`](../../envs/bug13/requirements.txt) |

El issue indica Terra 0.17.4 y Python 3.7.4 (Linux). Se probaron:

- Terra 0.17.4: tests del Framework → buggy pasa (exit 0) y fixed falla (exit 1); tests adaptados → buggy falla y fixed pasa.
- Terra 0.18.3: mismo resultado en ambos juegos de tests.

Se eligió 0.17.4 porque es la versión indicada en el issue y con los tests adaptados cumple el criterio buggy-falla / fixed-pasa. La versión de Python (3.8 en lugar de 3.7) es una decisión del investigador, no un dato del issue.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug13/.venv
envs/bug13/.venv/Scripts/python -m pip install -r envs/bug13/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 13

# opción B: manual
cd bugs/Bugs4Q-FW-13
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug13/.venv/Scripts/python -W ignore test_b13.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug13/.venv/Scripts/python -W ignore test_f13.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug13/.venv/bin/python` en lugar de `envs/bug13/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b13.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f13.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que construir el circuito y aplicar `outer_level.control()` no lance ninguna excepción; solo cambia el `append` del circuito interno. El test es determinista (no hay simulación).

**Modificación respecto al Framework.** Los tests originales ([`framework_tests/test_b13.py`](framework_tests/test_b13.py), [`framework_tests/test_f13.py`](framework_tests/test_f13.py)) exigen que se lance una excepción (`self.fail('Error not raised')` / `self.fail('There is no error raised')`), es decir, comprueban el comportamiento *buggy*: el de buggy pasa y el de fixed falla, al revés del criterio del proyecto (una ejecución en el entorno final, lanzada fuera de `run_bug_tests.py` con el mismo formato de log: [`logs/framework_original_buggy.log`](logs/framework_original_buggy.log), [`logs/framework_original_fixed.log`](logs/framework_original_fixed.log)). En los tests adaptados se quitó el bloque `else: self.fail(...)` y se añadió `self.fail('Error raised: ...')` dentro del `except`, de modo que el test falla si hay excepción. El código bajo prueba no cambia.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- Con los tests adaptados, falla en buggy y pasa en fixed de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado, con la versión de Terra del issue.

Limitaciones:
- Es un uso incorrecto de la API (`Instruction` en lugar de `Gate`), no un defecto de Qiskit.
- Los tests del Framework tienen el sentido invertido; los usados aquí son una adaptación del proyecto.
- El log del buggy muestra la traza completa, con la línea `qc.append(outer_level.control(), [0,1,2])` y el mensaje `"inner" is not a gate instruction`, que apunta directamente al `append` de `inner`. Para C1 es una evidencia buena: el error nombra el circuito problemático y la causa (no es una puerta).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
