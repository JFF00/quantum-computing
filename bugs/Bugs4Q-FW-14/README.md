# Bugs4Q-FW-14

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-14` |
| Origen | Bugs4Q-Framework, bug 14 (`qiskit/14/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#6255](https://github.com/Qiskit/qiskit-terra/issues/6255) ("Inconsistence between qasm and eval outputs of opflow expectation value", abierto y cerrado el 19-abr-2021) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_14.py`, `fixed_14.py` (copiados sin cambios del Framework); `test_b14.py`, `test_f14.py` (adaptados para este proyecto, ver sección 7); originales del Framework en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa calcula el valor esperado de un observable no hermítico, `(Z ^ I) - 1j * (Y ^ I)`, sobre un estado de 2 qubits de dos maneras: con `eval()` (cálculo exacto) y muestreando con `CircuitSampler` sobre `qasm_simulator`. El resultado exacto es ≈ `1j`, pero el muestreado es ≈ `0`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
Eval  (-2.22e-16+0.9999999999999992j)
Qasm  (0.003819999999999934+0j)
...
AssertionError: (0.003819999999999934+0j) != (-2.22e-16+0.9999999999999992j) within 0.05 delta (1.0000072961733821 difference)
```

No se lanza ninguna excepción; el fallo solo se ve al comparar los dos valores.

El usuario debería haber obtenido el mismo valor esperado (salvo ruido de muestreo) con QASM y con `eval()`, pero el valor de QASM pierde la parte imaginaria y sale ≈ 0 sin ningún aviso.

## 3. Causa

El autor del issue (que lo cerró él mismo el mismo día) indica que se resuelve convirtiendo `exp_val` con el conversor `PauliExpectation` antes de muestrear. En el log de fixed se ve el efecto de esa conversión: el término `Y ^ I` pasa a medirse como `Z ^ I` sobre un circuito con un cambio de base añadido (`SDG`, `H`); sin ella, `CircuitSampler` muestrea el `OperatorMeasurement` original y el término en `Y` no se mide correctamente. Se trata como uso incompleto de la API (falta un paso de conversión), no como defecto corregido en Qiskit: el issue se cerró sin PR.

## 4. Corrección (`fixed`)

Cambio entre `buggy_14.py` y `fixed_14.py` (`modify_14.txt` del Framework):

```diff
 from qiskit.utils import QuantumInstance
-
+from qiskit.opflow.expectations import PauliExpectation
 ...
 exp_val = ~StateFn(obs) @ StateFn(state)
+exp_val = PauliExpectation().convert(exp_val).reduce()
 ...
-print('Qasm ', CircuitSampler(QuantumInstance(Aer.get_backend('qasm_simulator'),
-                               shots=100000)).convert(exp_val).eval())  # = 0 (up to shot noise)
+print('Qasm ', CircuitSampler(QuantumInstance(Aer.get_backend('qasm_simulator'), shots=100000)).convert(PauliExpectation().convert(exp_val).reduce()).eval()) 
```

El cambio está en el programa, no en la librería.

`PauliExpectation` descompone el observable en suma de términos de Pauli y añade a cada circuito el cambio de base necesario para medirlo en la base Z, que es lo único que el simulador QASM puede muestrear. Con eso, el valor muestreado coincide con `eval()`.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.17.0`, `qiskit-aer==0.8.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (fijado por precaución, igual que en los demás bugs con Terra antiguo; no se probó con otras versiones de NumPy). `qiskit-aer` se instala porque el programa usa `Aer.get_backend('qasm_simulator')`. |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug14/requirements.txt`](../../envs/bug14/requirements.txt) |

El issue indica Terra 0.17.0 y Python 3.7.3 (macOS). Se probaron, con los tests del Framework y con los adaptados:

| Terra + Aer | Tests del Framework (buggy / fixed) | Tests adaptados (buggy / fixed) |
|---|---|---|
| 0.17.0 + 0.8.0 | falla / falla | falla / pasa |
| 0.17.4 + 0.8.2 | falla / falla | falla / pasa |
| 0.18.3 + 0.9.1 | falla / pasa | falla / pasa |
| 0.19.2 + 0.10.4 | falla / pasa | falla / pasa |

Con los tests del Framework, buggy falla en todas las versiones solo por el último dígito decimal (`...0.9999999999999992j` frente a `...0.9999999999999991j`), y fixed falla en 0.17.x porque allí `eval()` tras `PauliExpectation` da `-1j` en lugar de `+1j` (en 0.18.3 ya da `+1j`).

Se eligió 0.17.0 (con Aer 0.8.0, publicados ambos el 01-abr-2021) porque es la versión del issue y con los tests adaptados cumple el criterio buggy-falla / fixed-pasa. La versión de Python (3.8 en lugar de 3.7) es una decisión del investigador, no un dato del issue.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug14/.venv
envs/bug14/.venv/Scripts/python -m pip install -r envs/bug14/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 14

# opción B: manual
cd bugs/Bugs4Q-FW-14
$env:PYTHONIOENCODING = "utf-8"   # los tests imprimen el circuito con caracteres de caja
../../envs/bug14/.venv/Scripts/python -W ignore test_b14.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug14/.venv/Scripts/python -W ignore test_f14.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug14/.venv/bin/python` en lugar de `envs/bug14/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b14.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f14.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que el valor muestreado con `qasm_simulator` (100 000 shots) coincida con `eval()` con tolerancia absoluta 0.05 (`assertAlmostEqual(..., delta=0.05)` sobre números complejos); solo cambia la conversión con `PauliExpectation`.

**Modificación respecto al Framework.** Los tests originales ([`framework_tests/test_b14.py`](framework_tests/test_b14.py), [`framework_tests/test_f14.py`](framework_tests/test_f14.py)) comparan `str(exp_val.eval())` con la cadena exacta `'(-2.22e-16+0.9999999999999991j)'`. Ese oráculo no mide el síntoma del issue (QASM ≠ `eval`): solo mira `eval()`, y en buggy falla por un dígito de redondeo; además, los nombres de los métodos están intercambiados (`test_b14.py` contiene `test_f14` y viceversa). Con Terra 0.17.0 fallan los dos (una ejecución en el entorno final, lanzada fuera de `run_bug_tests.py` con el mismo formato de log: [`logs/framework_original_buggy.log`](logs/framework_original_buggy.log), [`logs/framework_original_fixed.log`](logs/framework_original_fixed.log)). En los tests adaptados se guardan `eval()` y el resultado de QASM en variables y se sustituye la aserción por `assertAlmostEqual(complex(qasm_val), complex(eval_val), delta=0.05)`, que es el comportamiento esperado que describe el issue; los nombres de método se corrigieron (`test_b14` en `test_b14.py`, `test_f14` en `test_f14.py`). El código bajo prueba no cambia (el test fixed muestrea el `exp_val` ya convertido, equivalente a `fixed_14.py`, que lo convierte dos veces).

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- Con los tests adaptados, falla en buggy y pasa en fixed de forma estable (3/3) y en las 4 combinaciones de versiones probadas.
- Se ejecuta en un entorno fijado y documentado, con la versión de Terra del issue.

Limitaciones:
- Es un uso incompleto de la API (falta `PauliExpectation`), no un defecto de Qiskit.
- El oráculo es nuevo (los tests del Framework no sirven: comparan una cadena con 16 decimales).
- Hay muestreo sin semilla; con 100 000 shots el ruido es del orden de 0.003, muy por debajo de la tolerancia 0.05, pero no es estrictamente determinista.
- En Terra 0.17.x el signo de `eval()` cambia entre buggy (`+1j`) y fixed (`-1j`); el test adaptado solo compara QASM con `eval()` dentro de cada versión, así que no se ve afectado, pero es una rareza de esa versión.
- Requiere `qiskit-aer` (rueda binaria para Windows y Python 3.8). `qiskit.opflow` y `QuantumInstance` desaparecen en versiones modernas de Qiskit.
- El mensaje del test (`(0.00…+0j) != (-2.22e-16+0.99…j) within 0.05 delta`) muestra que QASM pierde la parte imaginaria, pero no señala ninguna línea del programa (el programa no tiene ninguna línea "incorrecta": falta un paso). En C1 el LLM tendría que conocer `PauliExpectation`; la evidencia es débil para localizar el arreglo.

## 9. Pendientes

- [x] Análisis estático (LintQ, 2026-11-27): 1 warning `ql-unmeasurable-qubits` (media) en buggy y en fixed; no relacionado con el bug. Ver `static_analysis/`.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.

## 10. Test a nivel de programa (piloto)

Seleccionado para el piloto de la semana 10. Los tests de las secciones anteriores llevan el código del programa copiado dentro, por lo que no pueden validar un parche. [`test_program_14.py`](test_program_14.py) (escrito para el proyecto) ejecuta en cambio el **archivo** indicado en la variable `BUG_PROGRAM` mediante [`scripts/program_harness.py`](../../scripts/program_harness.py), que captura stdout, las variables finales del programa y las llamadas a `execute()` (inyectando `seed_simulator=1234` si el programa no fija semilla).

**Oráculo.** Lee la línea `Qasm <valor>` que imprime el programa y comprueba que el valor esperado estimado con el simulador QASM es 1j (el valor exacto que indica el propio programa en su comentario), con tolerancia 0.05. No se compara con `eval()`: en Terra 0.17.0 la versión fixed da `eval() = -1j` pero `Qasm = +1j`.

El test no contiene el código corregido, para no filtrar la solución en la condición C1.

```powershell
cd bugs/Bugs4Q-FW-14
$env:BUG_PROGRAM = "buggy_14.py"; ../../envs/bug14/.venv/Scripts/python -W ignore test_program_14.py   # exit 1
$env:BUG_PROGRAM = "fixed_14.py"; ../../envs/bug14/.venv/Scripts/python -W ignore test_program_14.py   # exit 0
# o bien, desde la raíz: python scripts/run_bug_tests.py 14 --program-test
```

| Programa | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|
| `buggy_14.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/program_buggy_run1.log), [run2](logs/program_buggy_run2.log), [run3](logs/program_buggy_run3.log) |
| `fixed_14.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/program_fixed_run1.log), [run2](logs/program_fixed_run2.log), [run3](logs/program_fixed_run3.log) |

Fragmento de [`logs/program_buggy_run1.log`](logs/program_buggy_run1.log):

```
AssertionError: (0.002940000000000054+0j) != 1j within 0.05 delta (1.0000043217906611 difference) : valor QASM (0.002940000000000054+0j); se esperaba 1j
```

Para validar un parche: guardarlo como archivo en esta carpeta y ejecutar el test con `BUG_PROGRAM=<archivo del parche>`.
