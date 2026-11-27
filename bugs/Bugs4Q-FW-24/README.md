# Bugs4Q-FW-24

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-24` |
| Origen | Bugs4Q-Framework, bug 24 (`qiskit/24/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackOverflow 64707625](https://stackoverflow.com/questions/64707625/visualizing-circuits-in-qiskit-with-matplotlib) ("Visualizing circuits in qiskit with matplotlib", publicada el 06-nov-2020) |
| Categoría (Framework) | Name conflict/TypeError |
| Archivos | `buggy_24.py`, `fixed_24.py`, `test_f24.py` (copiados sin cambios del Framework); `test_b24.py` (adaptado, ver sección 4); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa crea un circuito de 2 qubits, lo dibuja con matplotlib e intenta aplicar una Hadamard con `circuit.h(qr(0))`, llamando al registro como si fuera una función. Se detiene con `TypeError`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
  File "test_b24.py", line 15, in test_b24
    circuit.h(qr(0))
TypeError: 'QuantumRegister' object is not callable
...
AssertionError: TypeError
```

El programa lanza una excepción (`TypeError: 'QuantumRegister' object is not callable`).

El usuario debería obtener el circuito con una puerta `H` sobre el qubit 0 (y su dibujo), pero el programa se detiene al intentar añadir la puerta.

**Diferencia con la pregunta original:** en la pregunta, en un notebook de Jupyter, el autor recibe `AttributeError: module 'qiskit.circuit' has no attribute 'draw'` (y `... no attribute 'h'`): la variable `circuit` apunta al módulo `qiskit.circuit` (importado con `from qiskit import *`) en lugar de al `QuantumCircuit`. Ese conflicto de nombres depende del estado del kernel del notebook y **no se reproduce** al ejecutar el código como script: aquí `circuit.draw(output='mpl')` funciona y el error observable es el `TypeError` de `qr(0)`, que es lo que comprueban los tests del Framework (categoría "Name conflict/TypeError").

## 3. Causa

Según las respuestas, el `AttributeError` de la pregunta se debe a un conflicto de nombres: Python toma `circuit` como el módulo `qiskit.circuit` y no como la variable del circuito; recomiendan reiniciar el kernel o usar otro nombre de variable. El `TypeError` que reproduce el Framework se debe a `qr(0)`: un `QuantumRegister` se indexa (`qr[0]`) o se usa el índice entero directamente, no se llama. Ambos son errores del programa del usuario, no defectos de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_24.py` y `fixed_24.py` (`modify_24.txt` del Framework):

```diff
-circuit = QuantumCircuit(qr, cr)
+qc = QuantumCircuit(qr, cr)
 #%matplotlib inline
-circuit.draw(output='mpl')
-circuit.h(qr(0))
+qc.draw(output='mpl')
+qc.h(0)
+qc.draw(output='mpl')
```

El cambio está en el programa, no en la librería.

El cambio resuelve el problema por dos vías: renombrar la variable a `qc` evita que choque con el módulo `qiskit.circuit` (la solución de las respuestas), y `qc.h(0)` usa el índice del qubit en lugar de llamar al registro, que es lo que elimina el `TypeError` observable en script.

### Modificación del test respecto al Framework

`test_b24.py` del Framework envuelve `circuit.h(qr(0))` en `with self.assertRaises(TypeError)`: comprueba que el bug se manifiesta, así que **pasa** (exit 0) con el programa buggy, igual que el fixed (exit 0 los dos en el entorno final: [`logs/framework_original_buggy_test.log`](logs/framework_original_buggy_test.log), [`logs/framework_original_fixed_test.log`](logs/framework_original_fixed_test.log)). Para aplicar el criterio del proyecto (buggy falla / fixed pasa) se sustituyó ese bloque por el mismo patrón que usa `test_f24.py`:

```diff
-		with self.assertRaises(TypeError):
+		try:
 			circuit.h(qr(0))
+		except TypeError:
+			self.fail("TypeError")
```

`test_f24.py` se usa sin cambios.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.16.0`, `qiskit-ibmq-provider==0.11.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24); `matplotlib==3.3.4` y `pylatexenc==2.11` (`draw(output='mpl')`); `qiskit-ibmq-provider==0.11.0` (el programa hace `from qiskit import IBMQ`; solo se importa, no se usa cuenta) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug24/requirements.txt`](../../envs/bug24/requirements.txt) |

La pregunta no indica versiones. Se probó:

- Terra 0.16.1 sin `qiskit-ibmq-provider`: ambos tests no pueden iniciarse (`ImportError: cannot import name 'IBMQ' from 'qiskit'`).
- Terra 0.16.1 + `qiskit-ibmq-provider` 0.11.1: buggy falla y fixed pasa.
- Terra 0.16.0 + `qiskit-ibmq-provider` 0.11.0: buggy falla y fixed pasa.

Se eligió Terra 0.16.0 + `qiskit-ibmq-provider` 0.11.0 porque son las versiones publicadas más recientes antes de la pregunta (octubre de 2020; 0.16.1 y 0.11.1 salieron el 12-nov-2020, después de la pregunta) y cumplen el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug24/.venv
envs/bug24/.venv/Scripts/python -m pip install -r envs/bug24/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 24

# opción B: manual
cd bugs/Bugs4Q-FW-24
$env:PYTHONIOENCODING = "utf-8"
$env:MPLBACKEND = "Agg"           # los tests dibujan con matplotlib; evita abrir ventanas
../../envs/bug24/.venv/Scripts/python -W ignore test_b24.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug24/.venv/Scripts/python -W ignore test_f24.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug24/.venv/bin/python` en lugar de `envs/bug24/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b24.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f24.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que dibujar el circuito y añadir la Hadamard no lanza `TypeError`; no comprueban el dibujo en sí. El test es determinista.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- **Reproducción parcial:** el síntoma de la pregunta (`AttributeError` por conflicto de nombres con el módulo `qiskit.circuit` en Jupyter) no se reproduce como script; solo se reproduce el `TypeError` de `qr(0)`, que el autor no llega a reportar como tal (en su notebook fallaba antes).
- El test buggy del Framework tuvo que adaptarse, porque el original comprueba que se lanza el `TypeError` y pasa en ambas versiones.
- El renombrado `circuit` → `qc` de la corrección no tiene efecto observable en el test.
- Requiere `qiskit-ibmq-provider` solo por el `import` de `IBMQ`, que el programa no usa.
- Bug muy simple: la traza del test muestra la línea `circuit.h(qr(0))` y `TypeError: 'QuantumRegister' object is not callable`, así que en C1 el test fallido prácticamente da la respuesta.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
