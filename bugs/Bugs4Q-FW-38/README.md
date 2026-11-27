# Bugs4Q-FW-38

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-38` |
| Origen | Bugs4Q-Framework, bug 38 (`qiskit/38/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [Quantum Computing StackExchange 20894](https://quantumcomputing.stackexchange.com/questions/20894/saving-statevector-on-more-than-one-location-in-a-quantum-circuit-in-qiskit) ("Saving statevector on more than one location in a quantum circuit in Qiskit", publicada el 20-ago-2021) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_38.py`, `fixed_38.py` (copiados sin cambios del Framework); `test_b38.py`, `test_f38.py` (adaptados, ver sección 7); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa coloca tres `save_statevector()` en el mismo circuito para guardar el estado inicial, el estado tras la Hadamard y el estado final, y lo ejecuta en `aer_simulator`. Aer rechaza el Qobj y el resultado no contiene ningún vector de estado. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
Simulation failed and returned the following error message:
ERROR: Failed to load qobj: Duplicate key "statevector" in save instruction.
...
qiskit.exceptions.QiskitError: 'You have to select a circuit or schedule when there is more than one available'
```

Se lanza una excepción, pero no en la línea de la ejecución: `execute` solo imprime el error de Aer y la excepción (`QiskitError`) aparece después, en `job.result().get_statevector()`, con un mensaje que no tiene relación aparente con el problema.

El usuario debería haber recibido los tres vectores de estado intermedios (`|00>`, `(|00>+|01>)/√2` y `(|00>+|11>)/√2`); en cambio la simulación falla y no obtiene ninguno.

## 3. Causa

Según la respuesta de la pregunta, el problema es tener varias instrucciones `save_statevector()` en el mismo circuito: todas usan la clave por defecto `"statevector"` y Aer no admite claves duplicadas (otra respuesta indica que se puede hacer dando una etiqueta distinta a cada una, `label=...`). Es un uso incorrecto de la API, no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_38.py` y `fixed_38.py` (`modify_38.txt` del Framework, resumido):

```diff
-from qiskit.providers.aer.library import *
-q1 = QuantumCircuit(2)
-q1.save_statevector() # Save initial state
-q1.h(0)
-q1.save_statevector() # Save state after Hadamard
-q1.cx(0, 1)
-q1.save_statevector() # Save state after CNOT (also a final state)
-job = execute(q1, backend=Aer.get_backend('aer_simulator'), shots=1024)
-statevectors = job.result().get_statevector()
+from qiskit.quantum_info import Statevector
+qc = QuantumCircuit(2)
+st0 = Statevector.from_instruction(qc)
+qc.h(0)
+st1 = Statevector.from_instruction(qc)
+qc.cnot(0, 1)
+st2 = Statevector.from_instruction(qc)
+print(st0)
+print(st1)
+print(st2)
```

(`fixed_38.py` del Framework termina además con la salida de la respuesta pegada como código: tres expresiones `Statevector(...)` que se evalúan sin efecto; el test no las incluye.) El cambio está en el programa, no en la librería.

La corrección sigue la respuesta más votada: en lugar de pedir a Aer varios guardados con la misma clave, calcula cada estado intermedio con `Statevector.from_instruction` sobre el circuito construido hasta ese punto, sin pasar por el simulador. Es una reescritura del enfoque, no un cambio mínimo (el cambio mínimo sería poner una `label` distinta en cada `save_statevector`).

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.18.1`, `qiskit-aer==0.8.2` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug38/requirements.txt`](../../envs/bug38/requirements.txt) |

La pregunta no indica versiones. Terra 0.18.1 + Aer 0.8.2 son las versiones del metapaquete `qiskit==0.29.0` (agosto de 2021), vigente en la fecha de la pregunta; `save_statevector` existe en Aer desde 0.8. Se probaron:

- Terra 0.18.1 + Aer 0.8.2: buggy falla (error `Duplicate key "statevector"`) y fixed pasa.
- Terra 0.18.3 + Aer 0.9.1: mismo resultado (buggy falla, fixed pasa).

Se eligió Terra 0.18.1 + Aer 0.8.2 por ser las más cercanas a la fecha de la pregunta y cumplir el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug38/.venv
envs/bug38/.venv/Scripts/python -m pip install -r envs/bug38/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 38

# opción B: manual
cd bugs/Bugs4Q-FW-38
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug38/.venv/Scripts/python -W ignore test_b38.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug38/.venv/Scripts/python -W ignore test_f38.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug38/.venv/bin/python` en lugar de `envs/bug38/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b38.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f38.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests no tienen aserciones propias: comprueban únicamente que el código se ejecuta sin lanzar excepción (buggy lanza `QiskitError` en `get_statevector()`; fixed imprime los tres `Statevector`).

**Tests adaptados.** Los tests del Framework envuelven el código en `try: ... except Exception as e: print('Reason:', e) else: self.fail('Error not raised')`, es decir, *pasan cuando se lanza una excepción*. Con ese oráculo invertido, sin cambios, `test_b38.py` pasa (exit 0) y `test_f38.py` falla con `AssertionError: Error not raised` (exit 1), lo contrario del criterio del proyecto. La única modificación ha sido eliminar el bloque `try/except/else` (y desindentar el cuerpo) en ambos tests; el código de cada test es idéntico al del Framework.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un uso incorrecto de la API (claves duplicadas en `save_statevector`), no un defecto de Qiskit.
- Los tests del Framework se adaptaron (se quitó el `try/except/else` que invertía el oráculo); el oráculo es solo "no lanza excepción", sin comprobar los vectores obtenidos.
- El `fixed` cambia de enfoque (`Statevector.from_instruction` en vez de Aer), no es una corrección mínima.
- El traceback del test apunta a `get_statevector()` con el mensaje genérico `You have to select a circuit or schedule...`; la pista útil (`Duplicate key "statevector" in save instruction`) solo aparece impresa en stdout. Para C1 el LLM tendría que relacionar ese mensaje con las tres llamadas a `save_statevector`, que el traceback no señala.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
