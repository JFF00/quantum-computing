# Bugs4Q-FW-25

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-25` |
| Origen | Bugs4Q-Framework, bug 25 (`qiskit/25/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackOverflow 63283443](https://stackoverflow.com/questions/63283443/my-qiskit-codes-output-differ-from-the-lecturer-ryan-o-donnell) ("My qiskit code's output differ from the Lecturer: Ryan O'Donnell", publicada el 06-ago-2020) |
| Categoría (Framework) | Label convention is reversed(\|011>&\|110>) |
| Archivos | `buggy_25.py`, `fixed_25.py`, `test_f25.py` (copiados sin cambios del Framework); `test_b25.py` (adaptado, ver sección 4); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa pone en 1 los qubits 0 y 1 (la entrada que el autor etiqueta como `011`), aplica `ccx(0, 1, 2)` y mide. Según la tabla de la Toffoli de la clase que está comprobando, el autor esperaba la salida `011` y obtiene `111`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
{'111': 1024}
...
AssertionError: {'011': 1024} != {'111': 1024}
```

El programa no lanza ninguna excepción; el fallo solo se detecta al comparar los conteos con el valor esperado.

El usuario esperaba obtener `{'011': 1024}` (la salida de la fila `011` de la tabla del profesor), pero obtiene `{'111': 1024}`.

## 3. Causa

Según la respuesta aceptada, el código y la salida son correctos: en la tabla del profesor el estado se lee del primer al último qubit, mientras que Qiskit usa la convención inversa (el bit de más a la derecha es `q_0`). Lo que el autor llama `011` en la tabla corresponde a `110` en Qiskit, y viceversa. Es un malentendido de la convención de etiquetado (orden de bits), no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_25.py` y `fixed_25.py` (`modify_25.txt` del Framework marca todo el archivo, pero la única diferencia de código es esta línea, más una línea en blanco eliminada):

```diff
-circuit.ccx(0,1,2)
+circuit.ccx(2,1,0)
```

El cambio está en el programa, no en la librería.

El cambio resuelve el problema porque invierte el orden de los qubits de la Toffoli: el objetivo pasa a ser `q_0` y los controles `q_2` y `q_1`. Como `q_2` está en 0, la Toffoli no actúa y la cadena medida (en el orden de Qiskit, `q_2 q_1 q_0`) es `011`, que coincide con la fila que el autor esperaba según su lectura de la tabla.

### Modificación del test respecto al Framework

`test_b25.py` del Framework afirma `{'111': 1024}`, es decir, el resultado **que produce** el programa buggy: con él, el test buggy **pasa** (exit 0), igual que el fixed, y no distingue las dos versiones (exit 0 los dos en el entorno final, ver [`logs/framework_original_buggy_test.log`](logs/framework_original_buggy_test.log) y [`logs/framework_original_fixed_test.log`](logs/framework_original_fixed_test.log)). Para aplicar el criterio del proyecto (buggy falla / fixed pasa) se cambió solo el valor esperado de `test_b25.py` por el de `test_f25.py`:

```diff
-		self.assertDictEqual({'111': 1024}, counts1)
+		self.assertDictEqual({'011': 1024}, counts1)
```

`test_f25.py` se usa sin cambios.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.14.2`, `qiskit-aer==0.5.2` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra 0.14 usa `numpy.float`, eliminado en NumPy ≥ 1.24); `matplotlib==3.3.4` y `pylatexenc==2.11` (los tests llaman a `circuit.draw(output='mpl')`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug25/requirements.txt`](../../envs/bug25/requirements.txt) |

La pregunta indica Python 3.8.5 y `{'qiskit-terra': '0.14.2', 'qiskit-aer': '0.5.2', ..., 'qiskit': '0.19.6'}`. Se instalaron directamente Terra 0.14.2 y Aer 0.5.2 (los dos paquetes que usa el programa) y se cumple el criterio buggy-falla / fixed-pasa, así que no se probaron otras versiones. No se instalaron `qiskit-ignis`, `qiskit-aqua` ni `qiskit-ibmq-provider` (el programa no los usa). La versión de Python es 3.8.20 en lugar de 3.8.5. La elección de usar solo esos dos paquetes es del investigador.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug25/.venv
envs/bug25/.venv/Scripts/python -m pip install -r envs/bug25/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 25

# opción B: manual
cd bugs/Bugs4Q-FW-25
$env:PYTHONIOENCODING = "utf-8"
$env:MPLBACKEND = "Agg"           # los tests dibujan con matplotlib; evita abrir ventanas
../../envs/bug25/.venv/Scripts/python -W ignore test_b25.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug25/.venv/Scripts/python -W ignore test_f25.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug25/.venv/bin/python` en lugar de `envs/bug25/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b25.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f25.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban la misma salida esperada, `{'011': 1024}` con el `qasm_simulator` de Aer (1024 shots por defecto); el resultado es determinista porque el estado final es un estado de la base computacional.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado, con las versiones de Terra y Aer que reporta la pregunta.

Limitaciones:
- El test buggy del Framework tuvo que adaptarse (valor esperado), porque el original comprueba la salida buggy y pasa en ambas versiones.
- Según la respuesta aceptada, el programa buggy es correcto: el "bug" es la expectativa del usuario sobre el orden de los bits. La corrección del Framework (`ccx(2,1,0)`) hace coincidir la salida con esa expectativa, pero cambia qué qubit es el objetivo de la Toffoli; es discutible como "corrección".
- El mensaje de error del test (`{'011': 1024} != {'111': 1024}`) no apunta a ninguna línea; para C1 el modelo tiene que conocer la convención little-endian de Qiskit para relacionar la diferencia con el orden de los argumentos de `ccx`.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
