# Bugs4Q-FW-35

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-35` |
| Origen | Bugs4Q-Framework, bug 35 (`qiskit/35/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackExchange 12076](https://quantumcomputing.stackexchange.com/questions/12076/real-device-error-mitigation-with-qiskit) ("Real-device error mitigation with qiskit", publicada y respondida el 19-may-2020) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_35.py`, `fixed_35.py` (sin cambios del Framework); `test_b35.py`, `test_f35.py` (**adaptados**, ver sección 5); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El usuario genera los circuitos de calibración de medida de `qiskit-ignis` (`complete_meas_cal`) y los transpila para un dispositivo real de IBM con un `initial_layout` explícito. La transpilación falla con un error poco descriptivo. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
  File "test_b35.py", line 26, in test_b35
    qk.compiler.transpile(meas_calibs, backend=FakeParis(), initial_layout=layout)
qiskit.dagcircuit.exceptions.DAGCircuitError: 'not a DAG'
...
AssertionError: transpile raised DAGCircuitError: 'not a DAG'
```

El programa lanza una excepción (`DAGCircuitError: 'not a DAG'`) dentro de `transpile`; es el mismo mensaje que reporta el usuario.

El usuario debería recibir los 8 circuitos de calibración transpilados sobre los qubits físicos elegidos; en cambio recibe una excepción que no menciona el layout.

## 3. Causa

Según la respuesta aceptada, el `layout` asigna dos qubits virtuales al mismo qubit físico: `qreg[0]` y `qreg[5]` van ambos al 12. Basta con cambiar uno de ellos a otro qubit físico. Es un error del usuario al construir el layout (mal uso de la API); Qiskit no lo valida y falla más adelante con un mensaje confuso, pero la pregunta no lo trata como defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_35.py` y `fixed_35.py` (`modify_35.txt` del Framework):

```diff
-layout = {qreg[0]: 12, 
+layout = {qreg[0]: 10, 
```

El cambio está en el programa, no en la librería.

La corrección funciona porque con `qreg[0] → 10` los 7 qubits virtuales quedan asignados a 7 qubits físicos distintos (10, 11, 13, 17, 14, 12, 6), así que el layout es una asignación válida y el transpilador puede construir el circuito físico.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.14.1`, `qiskit-ignis==0.3.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug35/requirements.txt`](../../envs/bug35/requirements.txt) |

La pregunta no indica versiones. Por su fecha (mayo de 2020) corresponde Qiskit 0.19 (Terra 0.14.1, Ignis 0.3.0), que sí tiene wheels para Python 3.8 en Windows. Se probaron:

- Terra 0.14.1 + Ignis 0.3.0 con los **tests originales del Framework**: ambos fallan (exit 1) con `AssertionError: Error not raised`. El Framework quitó el `backend=_backend` del original; sin backend (sin mapa de acoplamiento) `transpile` acepta el layout duplicado sin error. Además, `test_f35.py` del Framework también espera una excepción, así que con esos tests nunca se puede obtener buggy-falla / fixed-pasa.
- Terra 0.14.1 + Ignis 0.3.0 con backend simulado `FakeParis` (27 qubits, de `qiskit.test.mock`): buggy lanza `DAGCircuitError: 'not a DAG'` (el error del usuario) y fixed transpila los 8 circuitos.
- Terra 0.16.4 + Ignis 0.5.2 (entorno temporal, solo sonda): mismo comportamiento (sin backend no hay error; con `FakeParis`, buggy `'not a DAG'` y fixed sin error).

Se eligió Terra 0.14.1 + Ignis 0.3.0 por coincidir con la fecha de la pregunta y cumplir el criterio buggy-falla / fixed-pasa con los tests adaptados. Es una decisión del investigador, no un dato de la pregunta.

**Sin dispositivo real.** El original usa un backend real de IBM Quantum (`_backend`, no identificado en la pregunta). No hace falta cuenta: el error ocurre en `transpile`, antes de enviar nada. Se sustituye por `FakeParis` (27 qubits, dispositivo de IBM disponible en mayo de 2020 y compatible con los índices 6–17 del layout). Que el usuario usara un dispositivo de 27 qubits es una suposición; cualquier backend simulado con ≥ 18 qubits (se comprobó también `FakeBoeblingen` y `FakeRochester`) da el mismo resultado.

**Modificación de los tests respecto al Framework** (igual en `test_b35.py` y `test_f35.py`; solo cambia el layout entre ambos):

- Se añade `from qiskit.test.mock import FakeParis` y `backend=FakeParis()` en la llamada a `transpile` (recupera el `backend=_backend` del código original).
- Se invierte el oráculo: en lugar de exigir que se lance una excepción (`self.fail('Error not raised')` en el `else`), el test falla si `transpile` lanza una excepción (`self.fail('transpile raised ...')`). El oráculo original esperaba excepción también en fixed, lo cual contradice la corrección.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug35/.venv
envs/bug35/.venv/Scripts/python -m pip install -r envs/bug35/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 35

# opción B: manual
cd bugs/Bugs4Q-FW-35
$env:PYTHONIOENCODING = "utf-8"   # los tests imprimen caracteres de caja (░ ║)
../../envs/bug35/.venv/Scripts/python -W ignore test_b35.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug35/.venv/Scripts/python -W ignore test_f35.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug35/.venv/bin/python` en lugar de `envs/bug35/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b35.py` | falla (exit 1) | falla, exit 1 las 3 veces (`DAGCircuitError: 'not a DAG'`) | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f35.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests generan los circuitos de calibración, los transpilan para `FakeParis` con el layout de cada versión y fallan si `transpile` lanza una excepción.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (un número) está en el programa del usuario, no en Qiskit.
- Reproduce exactamente la excepción reportada (`'not a DAG'`) sin hardware real ni cuenta de IBM Quantum.
- El test falla en buggy y pasa en fixed, de forma estable (3/3) y determinista.
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Los tests del Framework se **modificaron** (backend simulado y oráculo invertido, ver sección 5): tal como están, fallan en buggy y en fixed.
- El backend real del usuario no se conoce; `FakeParis` es una elección del investigador.
- Depende de `qiskit-ignis` y de `qiskit.test.mock`, ambos eliminados en Qiskit moderno.
- El mensaje de error (`DAGCircuitError: 'not a DAG'`) no menciona el layout ni el qubit duplicado, y la traza apunta solo a la línea de `transpile`. En C1 el LLM tendría que revisar el diccionario `layout` por su cuenta; el valor duplicado (12) es fácil de ver si lo inspecciona.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
