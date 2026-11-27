# Bugs4Q-FW-19

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-19` |
| Origen | Bugs4Q-Framework, bug 19 (`qiskit/19/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-metapackage#1003](https://github.com/Qiskit/qiskit-metapackage/issues/1003) ("QiskitError: 'Label contains invalid characters.'", abierto el 08-ago-2020 y cerrado el 11-ago-2020) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_19.py`, `fixed_19.py` (copiados sin cambios del Framework); `test_b19.py`, `test_f19.py` (adaptados, ver sección 5); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

El Framework enlaza `https://github.com/Qiskit/qiskit/issues/1003`. Ese repositorio era entonces el metapaquete `qiskit`, hoy renombrado `qiskit-metapackage`; el enlace antiguo ahora lleva a un pull request distinto de qiskit-terra. El código del bug coincide con qiskit-metapackage#1003.

## 2. Síntoma

`qi.Operator.from_label('CX')` lanza `QiskitError`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
  File "test_b19.py", line 21, in test_b19
    qi.Operator.from_label('CX')
qiskit.exceptions.QiskitError: 'Label contains invalid characters.'
```

El programa lanza una excepción (`QiskitError`), el mismo mensaje que muestra el issue.

El usuario esperaba recibir el `Operator` de la puerta CNOT, pero recibe un error porque la etiqueta no es válida.

## 3. Causa

Según la respuesta en el issue, `Operator.from_label` construye el producto tensorial de operadores de **un qubit**, uno por carácter de la etiqueta (`I`, `X`, `Y`, `Z`, `H`, `S`, `T`, `0`, `1`, `+`, `-`, `r`, `l`); `'CX'` no es una etiqueta válida porque `C` no es un operador de un qubit. Es un uso incorrecto de la API, no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_19.py` y `fixed_19.py` (`modify_19.txt` del Framework):

```diff
-qi.Operator.from_label('HI')
-
-# error at this line
-qi.Operator.from_label('CX')
+qi.Operator.from_label('H') 
+qi.Operator.from_label('X')
```

El cambio está en el programa, no en la librería.

Las etiquetas `'H'` y `'X'` solo contienen caracteres válidos (operadores de un qubit), así que `from_label` ya no lanza la excepción. La corrección del Framework evita el error pero no construye el operador CNOT que buscaba el usuario (para eso habría que usar, p. ej., `Operator(CXGate())`).

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.14.2` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra 0.14 usa `numpy.float`, eliminado en NumPy ≥ 1.24); `matplotlib` (3.6.3) instalada porque el programa llama a `qc.draw('mpl')` |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug19/requirements.txt`](../../envs/bug19/requirements.txt) |

El issue indica "Qiskit version: 0.14.2" (la versión de Terra; el traceback incluye la expresión regular de `from_label` de esa versión), Python 3.7.8 y el entorno de IBM Quantum. Versiones probadas (todas con `numpy==1.19.5` y matplotlib):

- Terra 0.12.0: ambos tests fallan al importar (`cannot import name 'CXGate' from 'qiskit.extensions'`; en esa versión la clase se llamaba `CnotGate`).
- Terra 0.13.0 y 0.14.2: buggy falla y fixed pasa.
- Terra 0.16.4: ambos tests fallan porque `qc.draw('mpl')` exige `pylatexenc`, que no está instalado (error ajeno al bug).

Se eligió Terra 0.14.2 porque es la versión del issue y cumple el criterio buggy-falla / fixed-pasa. Python es 3.8.20 en lugar de 3.7.8 (no hay Python 3.7 disponible en esta máquina). Es una decisión del investigador, no un dato del issue.

**Tests adaptados.** Los tests del Framework, sin cambios, invierten el criterio del proyecto: `test_b19.py` pasa si se lanza cualquier excepción, y `test_f19.py` **también** exige una excepción (`self.fail('There is no error raised')`), por lo que falla con el programa corregido. Ejecutados tal cual en este entorno: buggy exit 0, fixed exit 1. Se cambió solo la rama del `try` en ambos tests, para que el test falle si se lanza una excepción:

```diff
         except Exception as e:
             #self.assertEqual(type(e), TypeError)
-            print('Reason:', e)
-        else:
-            self.fail('There is no error raised')
+            self.fail('Exception raised: %s' % e)
```

Observación: como los tests originales capturan `Exception`, sin matplotlib (o sin `pylatexenc` en Terra ≥ 0.16) el `test_f19.py` original habría "pasado" por un error de dibujo ajeno al bug; por eso se instala matplotlib.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug19/.venv
envs/bug19/.venv/Scripts/python -m pip install -r envs/bug19/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 19

# opción B: manual
cd bugs/Bugs4Q-FW-19
$env:PYTHONIOENCODING = "utf-8"
$env:MPLBACKEND = "Agg"           # qc.draw('mpl') sin ventana
../../envs/bug19/.venv/Scripts/python -W ignore test_b19.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug19/.venv/Scripts/python -W ignore test_f19.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug19/.venv/bin/python` en lugar de `envs/bug19/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b19.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f19.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests (adaptados) comprueban que el dibujo del circuito y las llamadas a `Operator.from_label` se ejecuten sin lanzar ninguna excepción; solo cambian las etiquetas.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado, con la versión de Terra del issue.

Limitaciones:
- Es un uso incorrecto de la API (etiqueta de dos qubits que no es producto de operadores de un qubit).
- El `fixed` no es equivalente a la intención del usuario: evita la excepción pero no construye el operador CNOT.
- Los tests del Framework se adaptaron (oráculo invertido, ver sección 5); el `test_f19.py` original es erróneo. El oráculo solo comprueba la ausencia de excepciones, no el valor de los operadores.
- Depende de matplotlib (`qc.draw('mpl')`) y de `qiskit.extensions.CXGate`, que solo existe entre Terra 0.13 y 0.46.
- El mensaje de error del test sí señala la línea defectuosa (`from_label('CX')`) y el motivo (`Label contains invalid characters`); además `buggy_19.py` contiene el comentario `# error at this line`. En C1 la pista es muy directa.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
