# Bugs4Q-FW-27

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-27` |
| Origen | Bugs4Q-Framework, bug 27 (`qiskit/27/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackOverflow 63342432](https://stackoverflow.com/questions/63342432/python-quantum-fourier-transform) ("Python quantum Fourier transform", publicada el 10-ago-2020) |
| Categoría (Framework) | QFT operation* |
| Archivos | `buggy_27.py`, `fixed_27.py`, `test_f27.py` (copiados sin cambios del Framework); `test_b27.py` (adaptado, ver sección 4); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa quiere aplicar la transformada de Fourier cuántica (QFT) sobre un estado preparado con `H`, `Z`, `S` y `T`, pero la función `IQFT` construye la transformada **inversa**, así que la medición da un resultado distinto. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
{'101': 500}
...
AssertionError: {'011': 500} != {'101': 500}
```

El programa no lanza ninguna excepción; el fallo solo se detecta al comparar los conteos con el valor esperado.

El usuario debería obtener `{'011': 500}` (el resultado de aplicar la QFT, que es lo que pregunta cómo conseguir), pero obtiene `{'101': 500}`, el resultado de aplicar la IQFT.

## 3. Causa

El autor de la pregunta indica que su código implementa la QFT inversa y pregunta qué cambiar para obtener la QFT "normal". La respuesta explica que el circuito de la QFT es el inverso del circuito de la IQFT, así que basta con invertir el circuito (a mano o con el método `inverse()`). Es un error de uso/concepto del programa, no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_27.py` y `fixed_27.py` (`modify_27.txt` del Framework; resumen, el diff completo reescribe el archivo):

```diff
-def IQFT(circuit, qin, n):
-    for i in range (int(n/2)):
-        circuit.swap(qin[i], qin[n -1 -i])
-    ...
+def QFT(n, inverse=False):
+    circuit = QuantumCircuit(n, name='IQFT' if inverse else 'QFT')
+    for i in range(int(n/2)):
+        circuit.swap(i, n - 1 - i)
+    ...
+    if inverse:
+        circuit = circuit.inverse()
+    return circuit
 ...
-IQFT(circuit, qin, n)
+iqft = QFT(n, inverse=True)
+circuit.compose(iqft, inplace=True)
```

El cambio está en el programa, no en la librería.

El cambio resuelve el problema porque las mismas puertas del código original (swap, H y `cu1` con fase negativa, es decir, la IQFT) se construyen ahora en un subcircuito aparte y, con `inverse=True`, se invierte ese subcircuito con `inverse()`; la inversa de la IQFT es la QFT, y es lo que se añade al circuito con `compose`. El nombre del parámetro es confuso (`inverse=True` produce la QFT) porque el bloque base es la IQFT del usuario; así viene en la respuesta y en el Framework.

### Modificación del test respecto al Framework

`test_b27.py` del Framework afirma `{'101': 500}`, es decir, el resultado **que produce** el programa buggy: con él, el test buggy **pasa** (exit 0), igual que el fixed, y no distingue las dos versiones (exit 0 los dos en el entorno final, ver [`logs/framework_original_buggy_test.log`](logs/framework_original_buggy_test.log) y [`logs/framework_original_fixed_test.log`](logs/framework_original_fixed_test.log)). Para aplicar el criterio del proyecto (buggy falla / fixed pasa) se cambió solo el valor esperado de `test_b27.py` por el de `test_f27.py`:

```diff
-		self.assertDictEqual({'101': 500}, counts)
+		self.assertDictEqual({'011': 500}, counts)
```

`test_f27.py` se usa sin cambios.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.15.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug27/requirements.txt`](../../envs/bug27/requirements.txt) |

La pregunta **no indica versiones**. Se probaron, en el mismo entorno y con los tests del proyecto, Terra 0.14.2, 0.15.0, 0.16.4 y 0.17.4: en todas el test buggy falla (exit 1) y el fixed pasa (exit 0). Se eligió Terra 0.15.0 porque es la versión publicada justo antes de la pregunta (agosto de 2020) y cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

Los tests usan `BasicAer` (como el programa original), así que no hace falta `qiskit-aer`.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug27/.venv
envs/bug27/.venv/Scripts/python -m pip install -r envs/bug27/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 27

# opción B: manual
cd bugs/Bugs4Q-FW-27
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug27/.venv/Scripts/python -W ignore test_b27.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug27/.venv/Scripts/python -W ignore test_f27.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug27/.venv/bin/python` en lugar de `envs/bug27/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b27.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f27.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban la misma salida esperada, `{'011': 500}` con 500 shots; el resultado es determinista porque el estado final es un estado de la base computacional.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- El test buggy del Framework tuvo que adaptarse (valor esperado), porque el original comprueba la salida buggy y pasa en ambas versiones.
- El "bug" es más una pregunta conceptual (cómo pasar de IQFT a QFT) que un fallo del programa: la versión buggy hace exactamente lo que su nombre dice.
- La corrección es una reescritura amplia (nueva función, `inverse()`, `compose`), no un cambio de una línea.
- `cu1` está obsoleto desde Terra 0.16 y fue eliminado más tarde, así que el código solo funciona en versiones antiguas de Qiskit.
- El mensaje de error del test (`{'011': 500} != {'101': 500}`) solo muestra que los conteos no coinciden y no apunta a ninguna línea del programa; para C1 el modelo tendría que deducir por su conocimiento de la QFT que hay que invertir el circuito.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
