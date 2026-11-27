# Bugs4Q-FW-15

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-15` |
| Origen | Bugs4Q-Framework, bug 15 (`qiskit/15/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#7032](https://github.com/Qiskit/qiskit-terra/issues/7032) ("\"lin_comb\" of Gradient framework cannot recognize parameters", abierto y cerrado el 17-sep-2021) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_15.py`, `fixed_15.py` (copiados sin cambios del Framework); `test_b15.py`, `test_f15.py` (adaptados para este proyecto, ver sección 7); originales del Framework en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa calcula el gradiente de un `CircuitStateFn` construido sobre `RealAmplitudes` con los tres métodos de `Gradient`. `param_shift` y `fin_diff` funcionan, pero `lin_comb` lanza `TypeError`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
param_shift is ok
fin_diff is ok
...
TypeError: Unrecognized parameterized gate, <qiskit.circuit.gate.Gate object at 0x00000245034D68B0>
```

(La dirección de memoria cambia en cada ejecución.)

Sí se lanza una excepción (`TypeError`) dentro de `Gradient('lin_comb').convert(...)`.

El usuario debería haber obtenido el operador gradiente también con `lin_comb`, como con los otros dos métodos, pero recibió un error que dice que no reconoce la puerta parametrizada.

## 3. Causa

En el issue, el propio mantenedor que lo abrió comenta que la biblioteca de circuitos necesita `decompose()` para `lin_comb`: `RealAmplitudes` está envuelto como una única puerta (`RealAmplitudes`), y `lin_comb` solo sabe derivar puertas parametrizadas estándar (`ry`, etc.). El issue se cerró el mismo día con ese *workaround* y sin PR, así que se trata como limitación/uso de la API más que como defecto corregido en Qiskit. En Terra 0.19.2 el programa buggy ya no falla (ver sección 5), lo que indica que el comportamiento cambió en versiones posteriores.

## 4. Corrección (`fixed`)

Cambio entre `buggy_15.py` y `fixed_15.py` (`modify_15.txt` del Framework):

```diff
-ansatz = RealAmplitudes(num_qubits=1, reps=1)
+ansatz = RealAmplitudes(num_qubits=1, reps=1).decompose()
```

El cambio está en el programa, no en la librería.

`decompose()` sustituye la puerta compuesta `RealAmplitudes` por sus puertas `ry` parametrizadas, que `lin_comb` sí reconoce, así que los tres métodos pueden construir el gradiente.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.18.2` |
| Dependencias fijadas a mano | `numpy==1.19.5` (fijado por precaución, igual que en los demás bugs con Terra antiguo; no se probó con otras versiones de NumPy) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug15/requirements.txt`](../../envs/bug15/requirements.txt) |

El issue indica Terra "latest" (rama principal en septiembre de 2021) y Python 3.9.7. Se probaron:

- Terra 0.18.2: tests del Framework → buggy pasa (exit 0) y fixed falla (exit 1); tests adaptados → buggy falla y fixed pasa.
- Terra 0.19.2: el programa buggy ya no lanza `TypeError`; tests del Framework → ambos fallan; tests adaptados → ambos pasan. No reproduce.

Se eligió 0.18.2 porque es la última versión publicada antes del issue (09-sep-2021; issue del 17-sep-2021) y con los tests adaptados cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug15/.venv
envs/bug15/.venv/Scripts/python -m pip install -r envs/bug15/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 15

# opción B: manual
cd bugs/Bugs4Q-FW-15
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug15/.venv/Scripts/python -W ignore test_b15.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug15/.venv/Scripts/python -W ignore test_f15.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug15/.venv/bin/python` en lugar de `envs/bug15/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b15.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f15.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que los tres métodos (`param_shift`, `fin_diff`, `lin_comb`) conviertan el `CircuitStateFn` sin lanzar `TypeError`; solo cambia el `decompose()`. El test es determinista (no hay simulación).

**Modificación respecto al Framework.** Los tests originales ([`framework_tests/test_b15.py`](framework_tests/test_b15.py), [`framework_tests/test_f15.py`](framework_tests/test_f15.py)) exigen que se lance `TypeError` (`self.fail('TypeError not raised')` en ambos), es decir, comprueban el comportamiento *buggy*: el de buggy pasa y el de fixed falla, al revés del criterio del proyecto (una ejecución en el entorno final, lanzada fuera de `run_bug_tests.py` con el mismo formato de log: [`logs/framework_original_buggy.log`](logs/framework_original_buggy.log), [`logs/framework_original_fixed.log`](logs/framework_original_fixed.log)). En los tests adaptados se quitó el bloque `else: self.fail(...)` y se añadió `self.fail('TypeError raised: ...')` dentro del `except`, de modo que el test falla si hay `TypeError`. El código bajo prueba no cambia.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- Con los tests adaptados, falla en buggy y pasa en fixed de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Depende de la versión: en Terra 0.19.2 el programa buggy ya funciona, así que el bug solo se observa con Terra 0.18.x. `qiskit.opflow` desaparece en versiones modernas de Qiskit.
- Los tests del Framework tienen el sentido invertido; los usados aquí son una adaptación del proyecto.
- El mensaje del test (`TypeError raised: Unrecognized parameterized gate, <qiskit.circuit.gate.Gate object at 0x...>`) no nombra `RealAmplitudes` ni la línea del `ansatz` (la traza apunta a la llamada a `Gradient(method).convert`). Además, que `param_shift` y `fin_diff` sí funcionen puede despistar. En C1 el LLM tendría que saber que `lin_comb` necesita el circuito descompuesto; la evidencia es útil pero indirecta.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
