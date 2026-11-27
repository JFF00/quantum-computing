# Bugs4Q-FW-11

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-11` |
| Origen | Bugs4Q-Framework, bug 11 (`qiskit/11/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#6892](https://github.com/Qiskit/qiskit-terra/issues/6892) ("Parametrised Global Phase in Ansatzes", abierto el 10-ago-2021, cerrado el 31-ago-2021) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_11.py`, `fixed_11.py`, `test_b11.py`, `test_f11.py` (los cuatro copiados sin cambios del Framework) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa asigna un `Parameter` `x` como fase global de un `EfficientSU2` y luego llama a `assign_parameters({x: 0.001}, inplace=True)`. Después de eso, `circuit.parameters` ya no contiene `x` y `circuit.global_phase` vale `0.001`: el circuito original quedó ligado y se perdió la versión parametrizada. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
    self.assertEqual(str(circuit.global_phase),'x')
AssertionError: '0.001' != 'x'
```

No se lanza ninguna excepción; el fallo solo se ve al comparar la fase global con la esperada.

El usuario esperaba conservar el circuito con la fase global `x` (y `Parameter(x)` en `circuit.parameters`), pero recibió el mismo circuito con la fase ya sustituida por `0.001` y sin aviso.

## 3. Causa

Según el mantenedor que responde en el issue, es el comportamiento esperado: `QuantumCircuit.parameters` solo enumera parámetros sin ligar, e `inplace=True` modifica el propio circuito, así que `x` desaparece. Para conservar las dos versiones hay que usar `inplace=False` y guardar el circuito ligado en otra variable. Es un uso incorrecto de la API, no un defecto de Qiskit (el issue se cerró sin PR).

## 4. Corrección (`fixed`)

Cambio entre `buggy_11.py` y `fixed_11.py` (`modify_11.txt` del Framework):

```diff
-circuit.assign_parameters({x: 0.001}, inplace=True)
+bound_circuit = circuit.assign_parameters({x: 0.001}, inplace=False)
```

El cambio está en el programa, no en la librería.

Con `inplace=False`, `assign_parameters` devuelve una copia ligada (`bound_circuit`) y deja `circuit` intacto, por lo que `circuit.global_phase` sigue siendo `x` y `Parameter(x)` sigue en `circuit.parameters` (se ve en la salida de [`logs/fixed_test_run1.log`](logs/fixed_test_run1.log)).

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.18.1` |
| Dependencias fijadas a mano | `numpy==1.19.5` (fijado por precaución, igual que en los demás bugs con Terra antiguo; no se probó con otras versiones de NumPy) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug11/requirements.txt`](../../envs/bug11/requirements.txt) |

El issue indica Terra 0.19.0 (versión de desarrollo en agosto de 2021; la 0.19.0 se publicó meses después) y Python 3.7.10. Se probaron Terra 0.18.1 y 0.19.2 con los tests del Framework:

- 0.18.1: buggy falla y fixed pasa.
- 0.19.2: mismo resultado (buggy falla, fixed pasa).

Se eligió 0.18.1 porque es la última versión publicada antes de la fecha del issue (publicada el 02-ago-2021; issue del 10-ago-2021) y cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue ni del benchmark.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug11/.venv
envs/bug11/.venv/Scripts/python -m pip install -r envs/bug11/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 11

# opción B: manual
cd bugs/Bugs4Q-FW-11
$env:PYTHONIOENCODING = "utf-8"   # la salida imprime caracteres no ASCII (θ)
../../envs/bug11/.venv/Scripts/python -W ignore test_b11.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug11/.venv/Scripts/python -W ignore test_f11.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug11/.venv/bin/python` en lugar de `envs/bug11/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b11.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f11.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que, tras `assign_parameters`, `str(circuit.global_phase)` siga siendo `'x'`; solo cambia el valor de `inplace`. El test es determinista (no hay simulación).

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El Framework trae test para buggy y fixed; se usan sin modificar.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un uso incorrecto de la API (`inplace=True`), no un defecto de Qiskit; el issue se cerró como comportamiento esperado.
- El test solo comprueba `global_phase`; no comprueba `circuit.parameters`, que es lo que el autor del issue reportó.
- El resultado no depende de la versión de Terra (igual en 0.18.1 y 0.19.2), así que no ayuda a datar el bug.
- El mensaje del test (`'0.001' != 'x'`) señala la línea del `assertEqual`, no la llamada a `assign_parameters`; en C1 el LLM tendría que deducir que la fase se ligó en el propio circuito por `inplace=True`. Es una pista razonable, pero indirecta.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
