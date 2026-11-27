# Bugs4Q-FW-37

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-37` |
| Origen | Bugs4Q-Framework, bug 37 (`qiskit/37/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [Quantum Computing StackExchange 6697](https://quantumcomputing.stackexchange.com/questions/6697/creating-and-running-parallel-circuits-in-qiskit) ("Creating and running parallel circuits in Qiskit", publicada el 06-jul-2019) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_37.py`, `fixed_37.py` (copiados sin cambios del Framework); `test_b37.py`, `test_f37.py` (adaptados, ver sección 7); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa crea 5 circuitos (cada uno con una `X` en un qubit distinto), los compila uno a uno con `compile(qc, backend)`, lanza un job por circuito y espera a que terminen consultando `JOB_FINAL_STATES`. En el entorno elegido `qiskit.compile` ya no existe. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
    qobj_list = [compile(qc, backend) for qc in qc_list]
TypeError: compile() missing required argument 'mode' (pos 3)
```

Se lanza una excepción en la línea de `compile`. Como el test hace `from qiskit import *` y Qiskit 0.12 ya no exporta `compile`, el nombre se resuelve a la función `compile` incorporada de Python, de ahí el `TypeError`. El programa `buggy_37.py` original, que importa `from qiskit import Aer, compile`, falla antes con `ImportError: cannot import name 'compile' from 'qiskit'` (comprobado a mano en el mismo entorno, no está en los logs).

El usuario quería obtener las cuentas de los 5 circuitos (`00001`, `00010`, `00100`, `01000`, `10000`); en la pregunta solo recibía un `DeprecationWarning` que anunciaba la retirada de `compile` en Terra 0.9, y en una versión posterior el programa deja de ejecutarse.

## 3. Causa

Según la respuesta aceptada, `compile` está obsoleto y se sustituye por `transpile` (optimiza los circuitos para el backend) y `assemble` (los empaqueta en un único Qobj); con todos los circuitos en un solo Qobj basta un único job, y los resultados de cada circuito se obtienen con `get_counts(circuito)`. Es el uso de una API obsoleta (luego eliminada), no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_37.py` y `fixed_37.py` (`modify_37.txt` del Framework):

```diff
+from qiskit import *
 from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
-from qiskit import Aer, compile
-from qiskit.backends.jobstatus import JOB_FINAL_STATES
+from qiskit import Aer
+
+from qiskit.compiler import transpile, assemble
 ...
-qobj_list = [compile(qc, backend) for qc in qc_list]
-job_list = [backend.run(qobj) for qobj in qobj_list]
-
-while job_list:
-    for job in job_list:
-        if job.status() in JOB_FINAL_STATES:
-            job_list.remove(job)
-            print(job.result().get_counts())
+transpiled_circs = transpile(qc_list, backend=backend)
+qobjs = assemble(transpiled_circs, backend=backend)
+job_info = backend.run(qobjs)
+for circ_index in range(len(transpiled_circs)):
+    print(job_info.result().get_counts(transpiled_circs[circ_index]))
```

El cambio está en el programa, no en la librería.

La corrección sustituye la API retirada (`compile`, `qiskit.backends.jobstatus`) por la vigente: `transpile` + `assemble` producen un único Qobj con los 5 circuitos, que se ejecuta como un solo job, así que desaparece también el bucle de sondeo del estado de los jobs.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.12.0`, `qiskit-aer==0.4.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa alias como `numpy.float`, eliminados en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug37/requirements.txt`](../../envs/bug37/requirements.txt) |

La pregunta no indica versiones, pero el aviso que cita (`compile` se eliminará en Terra 0.9) corresponde a Terra 0.8 (julio de 2019). Terra 0.8–0.11 no tiene wheel para Python 3.8 en Windows (se comprobó con `pip download --only-binary=:all:` para 0.8.2, 0.9.1, 0.10.0, 0.11.0 y 0.11.1: solo hay sdist, que requiere compilar), y solo se dispone de Python 3.8; la primera combinación instalable es Terra 0.12.0 + Aer 0.4.0 (metapaquete `qiskit==0.15.0`, febrero de 2020). Se probó:

- Terra 0.12.0 + Aer 0.4.0: buggy falla (`compile` ya no existe) y fixed pasa.

Se eligió esta versión por ser la instalable más cercana a la fecha de la pregunta y cumplir el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug37/.venv
envs/bug37/.venv/Scripts/python -m pip install -r envs/bug37/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 37

# opción B: manual
cd bugs/Bugs4Q-FW-37
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug37/.venv/Scripts/python -W ignore test_b37.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug37/.venv/Scripts/python -W ignore test_f37.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug37/.venv/bin/python` en lugar de `envs/bug37/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b37.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f37.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests no tienen aserciones propias: comprueban únicamente que el programa se ejecuta sin lanzar excepción (fixed imprime `{'00001': 1024}`, `{'00010': 1024}`, ..., `{'10000': 1024}`).

**Tests adaptados.** Los tests del Framework envuelven el código en `try: ... except Exception as e: print('Reason:', e) else: self.fail('Error not raised')`, es decir, *pasan cuando se lanza una excepción*; sin cambios darían buggy exit 0 y fixed exit 1, lo contrario del criterio del proyecto (comportamiento comprobado en el bug 38, que usa el mismo patrón). La única modificación ha sido eliminar el bloque `try/except/else` (y desindentar el cuerpo) en ambos tests; el código de cada test es idéntico al del Framework. Nótese que `test_b37.py` del Framework no importa `compile` ni `JOB_FINAL_STATES` (no se ha corregido).

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- En la versión de la pregunta (Terra 0.8) el programa no fallaba, solo mostraba un `DeprecationWarning`; la excepción aparece únicamente en versiones en las que `compile` ya se eliminó. Es el uso de una API obsoleta, no un defecto de Qiskit.
- El `TypeError` del test se debe a que el test no importa `compile` y se usa la función incorporada de Python; el programa original falla con `ImportError`. En ambos casos la causa es la misma (`qiskit.compile` no existe), pero el mensaje del test es engañoso.
- Los tests del Framework se adaptaron (se quitó el `try/except/else` que invertía el oráculo); el oráculo es solo "no lanza excepción", sin comprobar las cuentas.
- Versión de Qiskit alejada de la fecha de la pregunta (Terra 0.12 frente a 0.8) por falta de wheels para Python 3.8.
- El traceback apunta a la línea de `compile(qc, backend)`, pero el mensaje (`missing required argument 'mode'`) no menciona Qiskit; para C1 el LLM tendría que reconocer que `compile` es la API retirada y sustituirla por `transpile` + `assemble`.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
