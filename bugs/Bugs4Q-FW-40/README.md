# Bugs4Q-FW-40

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-40` |
| Origen | Bugs4Q-Framework, bug 40 (`qiskit/40/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [Quantum Computing StackExchange 17651](https://quantumcomputing.stackexchange.com/questions/17651/setting-initial-state-in-qiskit-unitary-simulator) ("Setting initial state in Qiskit unitary simulator", publicada el 26-may-2021) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_40.py`, `fixed_40.py` (copiados sin cambios del Framework); `test_b40.py`, `test_f40.py` (adaptados, ver sección 7); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa fija el estado inicial de los qubits con `qc.initialize(...)`, aplica H, CNOT y H, y ejecuta el circuito sin transpilar (`assemble(qc)`) en el `unitary_simulator` de Aer. Aer rechaza la instrucción `initialize` y no devuelve ninguna unitaria. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
Simulation failed and returned the following error message:
ERROR: Failed to load qobj: Invalid qobj "initialize" instruction ("params" is incorrect length).
...
qiskit.exceptions.QiskitError: 'You have to select a circuit or schedule when there is more than one available'
```

El mensaje de Aer es exactamente el que cita la pregunta. Se lanza una excepción, pero en `result().get_unitary()` y con un mensaje genérico; el error real de Aer solo se imprime.

El usuario debería haber recibido la matriz unitaria 4x4 del circuito (y su representación LaTeX); en cambio la simulación falla y no obtiene nada.

## 3. Causa

Según la respuesta aceptada, el simulador unitario no soporta la instrucción `initialize`, así que el circuito debe transpilarse al conjunto de instrucciones del backend (`transpile(qc, backend=usim)`) antes de ensamblarlo. Es un uso incorrecto de la API, no un defecto de Qiskit. Además, el programa usa `array_to_latex(..., pretext=...)`, argumento que no existe (el correcto es `prefix`); la respuesta también lo cambia, aunque en buggy no se llega a ejecutar.

## 4. Corrección (`fixed`)

Cambio entre `buggy_40.py` y `fixed_40.py` (`modify_40.txt` del Framework, sin las líneas de comentarios eliminadas):

```diff
 qc.initialize(0,0)
-qc.initialize(0,0)
+qc.initialize(1,1)
 ...
-#display(qc.draw())
+qc.draw('mpl')
 usim = Aer.get_backend('unitary_simulator')
-qobj = assemble(qc)
+transpiled = transpile(qc, backend=usim)
+transpiled.draw('mpl')
+qobj = assemble(transpiled)
 unitary = usim.run(qobj).result().get_unitary()
-array_to_latex(unitary, pretext="\\text{Circuit = }\n")
+from qiskit.visualization import array_to_latex
+array_to_latex(unitary, prefix="\\text{Circuit = }\n")
```

El cambio está en el programa, no en la librería.

La línea que corrige el fallo es `transpile(qc, backend=usim)`: al transpilar, `initialize` se reescribe con las instrucciones del backend, así que Aer ya puede cargar el Qobj (en los logs de fixed la simulación termina sin error). Los demás cambios (segundo `initialize` sobre el qubit 1 con valor 1, que era la intención descrita en la pregunta; `prefix` en lugar de `pretext`; dibujos `mpl`) vienen de la respuesta.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.17.4`, `qiskit-aer==0.8.2` |
| Dependencias fijadas a mano | ninguna fijada por versión; se añadieron `matplotlib`, `pylatexenc` (para `draw('mpl')`) e `ipython` (lo exige `array_to_latex` en Terra 0.17) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug40/requirements.txt`](../../envs/bug40/requirements.txt) |

La pregunta no indica versiones. Terra 0.17.4 + Aer 0.8.2 son las versiones del metapaquete `qiskit` vigente en la fecha de la pregunta (mayo de 2021). Se probaron:

- Terra 0.17.4 + Aer 0.8.2, sin `ipython`: buggy falla con el error de la pregunta; fixed falla con `ImportError: No module named 'IPython'` en `array_to_latex` (dependencia ausente, no el bug). Se añadió `ipython`.
- Terra 0.17.4 + Aer 0.8.2 + `ipython` 8.12.3: buggy falla y fixed pasa.
- Terra 0.16.4 + Aer 0.7.6: ambos fallan con `TypeError: object of type 'int' has no len()` en `initialize(0, 0)`: esa versión aún no acepta un entero como estado inicial.

Se eligió Terra 0.17.4 + Aer 0.8.2 por la fecha de la pregunta y porque cumple el criterio buggy-falla / fixed-pasa; además reproduce el mensaje de error literal de la pregunta. Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug40/.venv
envs/bug40/.venv/Scripts/python -m pip install -r envs/bug40/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 40

# opción B: manual
cd bugs/Bugs4Q-FW-40
$env:PYTHONIOENCODING = "utf-8"
$env:MPLBACKEND = "Agg"           # draw('mpl') sin ventana
../../envs/bug40/.venv/Scripts/python -W ignore test_b40.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug40/.venv/Scripts/python -W ignore test_f40.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug40/.venv/bin/python` en lugar de `envs/bug40/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b40.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f40.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests no tienen aserciones propias: comprueban únicamente que el programa se ejecuta hasta `array_to_latex` sin lanzar excepción.

**Tests adaptados.** Los tests del Framework envuelven el código en `try: ... except Exception as e: print('Reason:', e) else: self.fail('Error not raised')`, es decir, *pasan cuando se lanza una excepción*; sin cambios darían buggy exit 0 y fixed exit 1, lo contrario del criterio del proyecto. La única modificación ha sido eliminar el bloque `try/except/else` (y desindentar el cuerpo) en ambos tests; el código de cada test es idéntico al del Framework.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3), y el buggy reproduce el mensaje de error literal de la pregunta.
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un uso incorrecto de la API (falta `transpile` antes de ejecutar en el simulador unitario), no un defecto de Qiskit.
- Los tests del Framework se adaptaron (se quitó el `try/except/else` que invertía el oráculo); el oráculo es solo "no lanza excepción", sin comparar la unitaria.
- El `fixed` mezcla la corrección con otros cambios (segundo `initialize` distinto, `prefix`, dibujos `mpl`), y depende de `ipython`, `matplotlib` y `pylatexenc`.
- El bug depende de la versión: con Terra 0.16 `initialize(0, 0)` ya falla antes por otro motivo.
- El traceback del test apunta a `get_unitary()` con un mensaje genérico; la pista útil (`Invalid qobj "initialize" instruction`) solo aparece impresa. Para C1 el LLM tendría que deducir que falta `transpile`, cosa que el error no indica directamente.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
