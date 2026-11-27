# Bugs4Q-FW-36

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-36` |
| Origen | Bugs4Q-Framework, bug 36 (`qiskit/36/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [Quantum Computing StackExchange 5557](https://quantumcomputing.stackexchange.com/questions/5557/wait-gate-throws-an-error-notimplementederror-no-decomposition-rules-defin) ("\"Wait\" gate throws an error \"NotImplementedError: ('No decomposition rules defined for ', 'wait')\"", publicada el 25-feb-2019) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_36.py`, `fixed_36.py` (copiados sin cambios del Framework); `test_b36.py`, `test_f36.py` (adaptados, ver sección 7); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa intenta introducir un retardo entre una `X` y una `RX` con `circuit.wait(1e-6, qubit)` y ejecuta el circuito en el `statevector_simulator` de Aer. En el entorno elegido la puerta `wait` ya no existe y la llamada falla. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
    circuit.wait(1e-6, qubit)
AttributeError: 'QuantumCircuit' object has no attribute 'wait'
```

Se lanza una excepción en la propia línea de `wait`. No es la misma excepción que en la pregunta: con Terra 0.7 (la versión del usuario) `wait` existía y el error era `NotImplementedError: ('No decomposition rules defined for ', 'wait')` al ejecutar; en Terra 0.13 la puerta ha desaparecido y el error pasa a ser `AttributeError` (es la excepción que ya esperaba el test del Framework).

El usuario debería haber obtenido el vector de estado tras `X`, una espera y `RX(π)` (≈ `[-1, 0]` salvo fase); en cambio el programa termina con una excepción.

## 3. Causa

Según la respuesta aceptada, el comando `wait` está obsoleto (deprecated), y por eso falla. Propone usar en su lugar la puerta identidad rodeada de `barrier` para que el compilador no la elimine. Es un uso de una API obsoleta por parte del usuario, no un defecto de Qiskit que se corrigiera.

## 4. Corrección (`fixed`)

Cambio entre `buggy_36.py` y `fixed_36.py` (`modify_36.txt` del Framework):

```diff
-from qiskit.extensions.standard import RXGate, RYGate, RZGate, U3Gate
-from qiskit.extensions.simulator import wait
+from qiskit import *
+
 ...
-circuit.wait(1e-6, qubit)
+circuit.barrier(qubit)
+circuit.id(qubit)
+circuit.barrier(qubit)
```

El cambio está en el programa, no en la librería.

La espera se sustituye por una puerta identidad (`id`, que en la respuesta de 2019 se llamaba `iden`) entre dos `barrier`: la identidad ocupa el tiempo de una puerta de un qubit y las barreras impiden que el transpilador la elimine. Todas las instrucciones usadas existen en la API, así que el circuito se ejecuta.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.13.0`, `qiskit-aer==0.5.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa alias como `numpy.float`, eliminados en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug36/requirements.txt`](../../envs/bug36/requirements.txt) |

La pregunta indica Python 3.6, `qiskit 0.7.3`, `qiskit-terra 0.7.0` y `qiskit-aer 0.1.1`. Esas versiones no se pueden instalar aquí: solo hay Python 3.8 y las primeras versiones con wheel para cp38/Windows son Terra 0.12.0 y Aer 0.4.0 (Terra 0.9.1, 0.10.0 y 0.11.0 y Aer 0.3.4 solo tienen sdist). Se probaron:

- Terra 0.12.0 + Aer 0.4.0: buggy falla (`AttributeError: ... no attribute 'wait'`), pero fixed también falla (`AttributeError: ... no attribute 'id'`: en esa versión la identidad se llama `iden`).
- Terra 0.13.0 + Aer 0.5.0 (metapaquete `qiskit==0.18.0`, abril de 2020): buggy falla y fixed pasa.

Se eligió Terra 0.13.0 + Aer 0.5.0, la versión instalable más cercana a la fecha de la pregunta que cumple el criterio buggy-falla / fixed-pasa (`id` aparece en 0.13). Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug36/.venv
envs/bug36/.venv/Scripts/python -m pip install -r envs/bug36/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 36

# opción B: manual
cd bugs/Bugs4Q-FW-36
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug36/.venv/Scripts/python -W ignore test_b36.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug36/.venv/Scripts/python -W ignore test_f36.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug36/.venv/bin/python` en lugar de `envs/bug36/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b36.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f36.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests no tienen aserciones propias: comprueban únicamente que el circuito se construye y se simula sin lanzar excepción (fixed imprime el vector de estado `[-0.-1.j -0.+0.j]`).

**Tests adaptados.** Los tests del Framework envuelven el código en `try: ... except AttributeError: pass else: self.fail('AttributeError not raised')`, es decir, *pasan cuando se lanza la excepción*; sin cambios darían buggy exit 0 y fixed exit 1, lo contrario del criterio del proyecto (comportamiento comprobado en el bug 38, que usa el mismo patrón). La única modificación ha sido eliminar el bloque `try/except/else` (y desindentar el cuerpo) en ambos tests; el código de cada test es idéntico al del Framework.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- No se reproduce la excepción original de la pregunta (`NotImplementedError` al ejecutar, Terra 0.7 con Python 3.6, no instalables aquí), sino la de una versión posterior en la que `wait` ya se eliminó (`AttributeError` al construir el circuito). El síntoma depende por completo de la versión.
- Es el uso de una API obsoleta, no un defecto de Qiskit.
- Los tests del Framework se adaptaron (se quitó el `try/except/else` que invertía el oráculo); el oráculo es solo "no lanza excepción", sin comprobar el vector de estado. La identidad entre barreras tampoco equivale a una espera de 1 µs, solo a la duración de una puerta.
- El traceback señala exactamente la línea de `circuit.wait(...)` y dice que el método no existe, así que para C1 la pista es directa; el LLM solo necesita conocer el sustituto (`id` + `barrier`, o `delay` en versiones modernas).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
