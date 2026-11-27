# Bugs4Q-FW-39

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-39` |
| Origen | Bugs4Q-Framework, bug 39 (`qiskit/39/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [Quantum Computing StackExchange 18448](https://quantumcomputing.stackexchange.com/questions/18448/how-to-perform-a-plot-histogram-for-a-circuit) ("How to perform a plot histogram for a circuit?", publicada el 16-jul-2021) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_39.py`, `fixed_39.py`, `test_b39.py`, `test_f39.py` (los cuatro copiados sin cambios del Framework) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa construye un circuito de 4 qubits con CNOT y Toffoli, mide todos los qubits y dibuja el histograma. El histograma tiene una sola barra: los 1024 shots dan `0000`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
{'0000': 1024}
...
AssertionError: ('0100': 64 != 0), ('1011': 64 != 0), ... ('0000': 64 != 1024), ... within 30 delta
```

El programa no lanza ninguna excepción; el fallo solo se detecta al comparar las cuentas con la distribución esperada.

El usuario esperaba ver la probabilidad de los 16 resultados posibles; en cambio obtiene siempre `0000` con probabilidad 1.

## 3. Causa

Según la respuesta, el código es correcto como programa Qiskit, pero el circuito parte de `|0000>` y todas las puertas son controladas por qubits en `|0>`, así que no hacen nada y el resultado es `0000` con certeza. Es un error lógico del usuario en el diseño del circuito, no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_39.py` y `fixed_39.py` (`modify_39.txt` del Framework):

```diff
 qc = QuantumCircuit(4, 4)
+for i in range(4):
+    qc.h(i)
 qc.cx(3, 1)
```

(El resto de diferencias es el salto de línea final.) El cambio está en el programa, no en la librería.

Aplicar una Hadamard a cada qubit pone el registro en la superposición uniforme de los 16 estados de la base; las CNOT y Toffoli posteriores son permutaciones de esa base, así que la distribución sigue siendo uniforme y el histograma muestra los 16 resultados (≈64 cuentas cada uno con 1024 shots).

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.18.0`, `qiskit-aer==0.8.2` |
| Dependencias fijadas a mano | ninguna fijada por versión; se añadió `matplotlib` (lo usa `plot_histogram`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug39/requirements.txt`](../../envs/bug39/requirements.txt) |

La pregunta no indica versiones. Terra 0.18.0 + Aer 0.8.2 son las versiones del metapaquete `qiskit==0.28.0` (julio de 2021), vigente en la fecha de la pregunta. Se probaron:

- Terra 0.18.0 + Aer 0.8.2: buggy falla y fixed pasa.
- Terra 0.17.4 + Aer 0.8.2: mismo resultado (buggy falla, fixed pasa).

Se eligió Terra 0.18.0 + Aer 0.8.2 por la fecha de la pregunta y porque cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug39/.venv
envs/bug39/.venv/Scripts/python -m pip install -r envs/bug39/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 39

# opción B: manual
cd bugs/Bugs4Q-FW-39
$env:PYTHONIOENCODING = "utf-8"
$env:MPLBACKEND = "Agg"           # plot_histogram sin ventana
../../envs/bug39/.venv/Scripts/python -W ignore test_b39.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug39/.venv/Scripts/python -W ignore test_f39.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug39/.venv/bin/python` en lugar de `envs/bug39/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b39.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f39.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban con `assertDictAlmostEqual` (de `QiskitTestCase`) que cada uno de los 16 resultados tiene 64 ± 30 cuentas en 1024 shots; solo cambian las cuatro Hadamard iniciales.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El Framework trae test para buggy y fixed; se usan sin modificar.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un error lógico del usuario (circuito que no hace nada sobre `|0000>`), no un uso incorrecto de la API ni un defecto de Qiskit; además, la "corrección" cambia lo que calcula el circuito, según lo que sugiere la respuesta, y no es la única posible.
- El test de fixed es estadístico (simulación sin semilla): cada resultado debe quedar a menos de 30 cuentas de 64 (≈3,9 desviaciones típicas), así que un fallo espurio es muy improbable pero posible.
- El test depende de `qiskit.test.QiskitTestCase`, que desaparece en versiones modernas de Qiskit.
- El mensaje de error del test lista las cuentas esperadas frente a las obtenidas (`'0000': 64 != 1024`) pero no indica ninguna línea del programa; para C1 el LLM tendría que deducir que falta preparar una superposición.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
