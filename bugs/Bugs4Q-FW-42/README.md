# Bugs4Q-FW-42

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-42` |
| Origen | Bugs4Q-Framework, bug 42 (`qiskit/42/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [Quantum Computing StackExchange 9195](https://quantumcomputing.stackexchange.com/questions/9195/attributeerror-result-object-has-no-attribute-get-data) ("AttributeError: 'Result' object has no attribute 'get_data'", publicada el 13-dic-2019) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_42.py`, `fixed_42.py` (copiados sin cambios del Framework); `test_b42.py`, `test_f42.py` (adaptados, ver sección 7); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa (un circuito de 4 qubits para resolver un sistema lineal, ejecutado 10 veces en `qasm_simulator`) acumula en cada iteración las cuentas de `1000` y `1100` leyéndolas con `result.get_data("solve_linear_sys")['counts']`. La primera lectura falla. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
    n0 = n0 + result.get_data("solve_linear_sys")['counts']['1000']
AttributeError: 'Result' object has no attribute 'get_data'
```

Se lanza una excepción en la línea de `get_data`, con el mismo mensaje que cita la pregunta.

El usuario debería haber obtenido, tras cada iteración, las cuentas acumuladas `n0`, `n1` y su cociente `p`; en cambio el programa se detiene en la primera iteración.

## 3. Causa

Según la respuesta aceptada, `Result.get_data()` se renombró a `Result.data()`. El método que usaba el programa había desaparecido de la API de Qiskit; es el uso de una API obsoleta, no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_42.py` y `fixed_42.py` (`modify_42.txt` del Framework):

```diff
-    n0 = n0 + result.get_data("solve_linear_sys")['counts']['1000']
-    n1 = n1 + result.get_data("solve_linear_sys")['counts']['1100']
+    n0 = n0 + result.get_counts()['1000']
+    n1 = n1 + result.get_counts()['1100']
```

El cambio está en el programa, no en la librería.

En lugar del método retirado, el `fixed` lee las cuentas con `result.get_counts()`, que devuelve directamente el diccionario de cuentas del único circuito ejecutado (lo mismo que contenía `get_data(...)['counts']`). Difiere de la respuesta, que propone `result.data(...)`, pero la intención es la misma.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.12.0`, `qiskit-aer==0.4.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa alias como `numpy.float`, eliminados en NumPy ≥ 1.24); `matplotlib==3.3.4` (para `plot_histogram`, versión de la época de Terra 0.12) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug42/requirements.txt`](../../envs/bug42/requirements.txt) |

La pregunta no indica versiones (el usuario usaba Google Colab en diciembre de 2019, cuando la última versión publicada era Terra 0.11). Terra 0.11.x no tiene wheel para Python 3.8 en Windows (solo sdist), y solo se dispone de Python 3.8; la primera combinación instalable es Terra 0.12.0 + Aer 0.4.0 (metapaquete `qiskit==0.15.0`, febrero de 2020). Se probó:

- Terra 0.12.0 + Aer 0.4.0 + matplotlib 3.3.4: buggy falla con el `AttributeError` de la pregunta y fixed pasa.

Se eligió esta versión por ser la instalable más cercana a la fecha de la pregunta y cumplir el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug42/.venv
envs/bug42/.venv/Scripts/python -m pip install -r envs/bug42/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 42

# opción B: manual
cd bugs/Bugs4Q-FW-42
$env:PYTHONIOENCODING = "utf-8"
$env:MPLBACKEND = "Agg"           # plot_histogram sin ventana
../../envs/bug42/.venv/Scripts/python -W ignore test_b42.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug42/.venv/Scripts/python -W ignore test_f42.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug42/.venv/bin/python` en lugar de `envs/bug42/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b42.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f42.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests no tienen aserciones propias: comprueban únicamente que las 10 iteraciones se ejecutan sin lanzar excepción (fixed imprime los resultados y los valores acumulados de `n0`, `n1` y `p`).

**Tests adaptados.** Los tests del Framework envuelven el código en `try: ... except Exception as e: print('Reason:', e) else: self.fail('Error not raised')`, es decir, *pasan cuando se lanza una excepción*; sin cambios darían buggy exit 0 y fixed exit 1, lo contrario del criterio del proyecto (comportamiento comprobado en el bug 38, que usa el mismo patrón). La única modificación ha sido eliminar el bloque `try/except/else` (y desindentar el cuerpo) en ambos tests; el código de cada test es idéntico al del Framework.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3), y el buggy reproduce el mensaje de error literal de la pregunta.
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es el uso de una API retirada (`get_data`), no un defecto de Qiskit; el bug solo existe en versiones posteriores a esa retirada.
- Los tests del Framework se adaptaron (se quitó el `try/except/else` que invertía el oráculo); el oráculo es solo "no lanza excepción", sin comprobar las cuentas.
- El fixed depende del azar: si en alguna iteración no apareciera `1000` o `1100` habría `KeyError` (o `ZeroDivisionError` si `n1` fuera 0). Con 8192 shots no ha ocurrido en ninguna ejecución, pero la simulación no tiene semilla.
- Versión de Qiskit algo posterior a la de la pregunta (Terra 0.12 frente a 0.11) por falta de wheels para Python 3.8.
- El traceback señala exactamente la línea de `get_data` y dice que el método no existe, así que para C1 la pista es directa; el LLM solo necesita conocer el sustituto (`get_counts()` o `data()`).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
