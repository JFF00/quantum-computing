# Bugs4Q-FW-32

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-32` |
| Origen | Bugs4Q-Framework, bug 32 (`qiskit/32/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackExchange 9209](https://quantumcomputing.stackexchange.com/questions/9209/how-to-use-parallel-executions-of-circuits) ("How to use parallel executions of circuits?", publicada y respondida el 15-dic-2019; respuesta no marcada como aceptada) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_32.py`, `fixed_32.py` (sin cambios del Framework); `test_b32.py`, `test_f32.py` (**escritos para este proyecto**: el Framework no trae tests para este bug) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El usuario ejecuta 3 copias del mismo circuito en `Aer` con `max_parallel_experiments=3` esperando que se ejecuten en paralelo, pero no ve cambios en el resultado ni en el tiempo (≈10 s en ambos casos). Los metadatos del resultado muestran que Aer ejecutó un solo experimento a la vez. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
{'max_memory_mb': 15924, 'omp_enabled': True, 'parallel_experiments': 1, 'time_taken': 12.2684227}
{'max_memory_mb': 15924, 'omp_enabled': True, 'parallel_experiments': 1, 'time_taken': 11.3240296}
...
  File "test_b32.py", line 40, in test_b32
    self.assertGreater(parallel_result.metadata['parallel_experiments'], 1)
AssertionError: 1 not greater than 1
```

El programa no lanza ninguna excepción; el fallo solo se ve en los metadatos del resultado (`parallel_experiments`).

El usuario debería obtener `parallel_experiments` > 1 en la segunda ejecución (los 3 circuitos repartidos entre varios hilos); en cambio recibe `parallel_experiments: 1`, es decir, ejecución secuencial.

## 3. Causa

Según la respuesta, `max_parallel_experiments` solo puede paralelizar "hasta el valor de `max_parallel_threads`", y el usuario fijó `max_parallel_threads=1`; la respuesta sugiere subir `max_parallel_threads` por encima de 1 y cita la documentación de Aer. Es un mal uso de las opciones del backend (configuración incorrecta), no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_32.py` y `fixed_32.py` (`modify_32.txt` del Framework):

```diff
-backend_options = {'method': 'automatic','max_parallel_threads':1,'max_parallel_experiments':1,'max_parallel_shots':1}
+backend_options = {'method': 'automatic','max_parallel_threads':2,'max_parallel_experiments':1,'max_parallel_shots':1}
 ...
-backend_options = {'method': 'automatic','max_parallel_threads':1,'max_parallel_experiments':3,'max_parallel_shots':1}
+backend_options = {'method': 'automatic','max_parallel_threads':2,'max_parallel_experiments':3,'max_parallel_shots':1}
```

El cambio está en el programa, no en la librería.

La corrección funciona porque, según la documentación de Aer citada en la respuesta, `max_parallel_experiments` solo paraleliza "hasta el valor de `max_parallel_threads`": con `max_parallel_threads=1` el máximo efectivo es 1, y con `max_parallel_threads=2` la segunda ejecución pasa a correr 2 experimentos a la vez (`parallel_experiments: 2` en los logs).

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.12.0`, `qiskit-aer==0.4.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug32/requirements.txt`](../../envs/bug32/requirements.txt) |

La pregunta no indica versiones. Por su fecha (diciembre de 2019) correspondería Qiskit 0.14 (Terra 0.11, Aer 0.3.4). Se probaron:

- Terra 0.11.x / Aer 0.3.4: sin wheel cp38 para Windows, no se pudo instalar.
- Terra 0.12.0 + Aer 0.4.0 (primeras con wheel cp38 para Windows): buggy falla y fixed pasa. Esta versión aún acepta `backend_options` en `execute` y expone `parallel_experiments` en `result.metadata`.

Se eligió Terra 0.12.0 + Aer 0.4.0 por ser la combinación instalable más cercana a la fecha de la pregunta que cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

**Tests escritos para este proyecto.** `test_b32.py` y `test_f32.py` reproducen el programa completo (mismo circuito, 3 copias, 10^6 shots, las dos llamadas a `execute` con las `backend_options` de cada versión) e imprimen `result.metadata` de ambas ejecuciones. La única aserción, idéntica en los dos, es `assertGreater(parallel_result.metadata['parallel_experiments'], 1)` sobre la segunda ejecución (`max_parallel_experiments=3`). Se usa ese campo y no el tiempo de ejecución porque es determinista; el tiempo depende de la máquina. Requiere una CPU con al menos 2 núcleos (la máquina usada tiene 12).

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug32/.venv
envs/bug32/.venv/Scripts/python -m pip install -r envs/bug32/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 32

# opción B: manual
cd bugs/Bugs4Q-FW-32
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug32/.venv/Scripts/python -W ignore test_b32.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug32/.venv/Scripts/python -W ignore test_f32.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug32/.venv/bin/python` en lugar de `envs/bug32/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b32.py` | falla (exit 1) | falla, exit 1 las 3 veces (`parallel_experiments: 1`) | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f32.py` | pasa (exit 0) | pasa, exit 0 las 3 veces (`parallel_experiments: 2`) | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que la ejecución con `max_parallel_experiments=3` reporte `parallel_experiments > 1` en los metadatos de Aer.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (dos valores de configuración) está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3) y determinista.
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- El test fue escrito para este proyecto (el Framework no trae test para este bug).
- El síntoma que describe el usuario es de rendimiento (no mejora el tiempo); el test comprueba el paralelismo declarado por Aer, no el tiempo. En los logs de fixed la segunda ejecución tardó entre un 20 % y un 35 % menos que la primera (`time_taken`), pero los tiempos se midieron con la máquina cargada por otros procesos y no son un oráculo fiable.
- El resultado depende del hardware: en una máquina de 1 núcleo fixed también daría `parallel_experiments: 1`.
- La respuesta de StackExchange no está marcada como aceptada.
- `backend_options` en `execute` y la API de `Aer` de esta época ya no existen en Qiskit moderno.
- El mensaje del test (`AssertionError: 1 not greater than 1`) solo dice que no hubo paralelismo; no apunta a `max_parallel_threads`. En C1 el LLM tendría que conocer la relación entre las opciones de paralelismo de Aer.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
