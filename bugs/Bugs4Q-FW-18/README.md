# Bugs4Q-FW-18

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-18` |
| Origen | Bugs4Q-Framework, bug 18 (`qiskit/18/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-metapackage#1119](https://github.com/Qiskit/qiskit-metapackage/issues/1119) ("Basis gates in _parse_transpile_args() function in the transpile.py file are not iterable as required by `zip`", abierto y cerrado el 19-nov-2020) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_18.py`, `fixed_18.py` (copiados sin cambios del Framework); `test_b18.py`, `test_f18.py` (adaptados, ver sección 5); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

El Framework enlaza `https://github.com/Qiskit/qiskit/issues/1119`. Ese repositorio era entonces el metapaquete `qiskit`, hoy renombrado `qiskit-metapackage`; el enlace antiguo ahora lleva a un issue distinto de qiskit-terra. El código del bug coincide con qiskit-metapackage#1119.

## 2. Síntoma

`execute(qc, backend, 100)` lanza `TypeError` antes de ejecutar el circuito. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
  File "test_b18.py", line 16, in test_b18
    result = execute(qc, backend, 100).result()
TypeError: 'int' object is not iterable
```

El programa lanza una excepción (`TypeError`) dentro de `transpile`; en el issue (Python 3.7) el mensaje era `zip argument #1 must support iteration`, aquí (Python 3.8) es `'int' object is not iterable`.

El usuario debería recibir los conteos del circuito de Bell, pero recibe una excepción interna de `transpile` que no menciona `shots`.

## 3. Causa

Según la respuesta del mantenedor en el issue, el error está en el código del usuario: el tercer argumento posicional de `execute()` no es `shots` sino una opción de transpilación que espera una lista (el mantenedor cita `coupling_map`; en Terra 0.16.1 el tercer parámetro es `basis_gates`), y `100` no es iterable. El autor del issue confirmó que la firma había cambiado y no lo había notado. Es un uso incorrecto de la API, no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_18.py` y `fixed_18.py`:

```diff
-    result = execute(qc, backend, 100).result()
+    result = execute(qc, backend, shots=100).result()
```

(`fixed_18.py` tiene además una línea en blanco inicial. El `modify_18.txt` del Framework compara por error el test con el programa; el cambio real es solo esta línea.) El cambio está en el programa, no en la librería.

Al pasar `100` por palabra clave, el valor llega a `shots` y `basis_gates` queda en su valor por defecto (`None`), así que `transpile` ya no intenta iterar sobre un entero.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.16.1`, `qiskit-aer==0.7.1` (las versiones del issue) |
| Dependencias fijadas a mano | `numpy==1.19.5` (con la NumPy que resuelve `pip`, 1.24.4, Terra 0.16.1 falla con `module 'numpy' has no attribute 'int'`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug18/requirements.txt`](../../envs/bug18/requirements.txt) |

El issue indica Qiskit 0.23.1 (Terra 0.16.1, Aer 0.7.1), Python 3.7.9 y macOS. Versiones probadas:

- Terra 0.16.1 + Aer 0.7.1 con `numpy==1.24.4`: el programa fixed falla con `AttributeError: module 'numpy' has no attribute 'int'` (error ajeno al bug).
- Terra 0.16.1 + Aer 0.7.1 con `numpy==1.19.5`: buggy lanza el `TypeError` y fixed se ejecuta sin error.
- Terra 0.16.4 + Aer 0.7.6 con `numpy==1.19.5`: mismo resultado.

Se eligieron Terra 0.16.1 + Aer 0.7.1 porque son las versiones del issue y cumplen el criterio buggy-falla / fixed-pasa. Python es 3.8.20 en lugar de 3.7.9 (no hay Python 3.7 disponible en esta máquina). Es una decisión del investigador, no un dato del issue.

**Tests adaptados.** Los tests del Framework, sin cambios, invierten el criterio del proyecto: `test_b18.py` pasa si se lanza `TypeError` y `test_f18.py` **también** exige un `TypeError` (`self.fail('TypeError not raised')`), por lo que falla con el programa corregido. Ejecutados tal cual en este entorno: buggy exit 0, fixed exit 1. Se cambió solo la rama del `try` en ambos tests, para que el test falle si se lanza la excepción:

```diff
         except TypeError as e:
-            self.assertEqual(type(e), TypeError)
-           
-        else:
-            self.fail('TypeError not raised')
+            self.fail('TypeError raised: %s' % e)
```

El resto del código de los tests (incluido el `if __name__ == "__main__":` dentro del método) se mantiene igual que en el Framework.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug18/.venv
envs/bug18/.venv/Scripts/python -m pip install -r envs/bug18/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 18

# opción B: manual
cd bugs/Bugs4Q-FW-18
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug18/.venv/Scripts/python -W ignore test_b18.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug18/.venv/Scripts/python -W ignore test_f18.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug18/.venv/bin/python` en lugar de `envs/bug18/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b18.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f18.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests (adaptados) comprueban que `execute(...)` y `get_counts` se ejecuten sin lanzar `TypeError`; solo cambia cómo se pasa el `100`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado, con las versiones de Qiskit del issue.

Limitaciones:
- Es un uso incorrecto de la API (argumento posicional en lugar de `shots=`); el issue se cerró a los 20 minutos.
- Los tests del Framework se adaptaron (oráculo invertido, ver sección 5); el `test_f18.py` original es erróneo (exige la excepción también en fixed).
- El oráculo solo comprueba que no haya `TypeError`; no comprueba los conteos. Con `statevector_simulator` se ignora `shots` y el resultado es un único shot (`{'00': 1}` o `{'11': 1}`).
- El mensaje de error del test sí señala la línea defectuosa (`execute(qc, backend, 100)`) y el tipo de error, por lo que en C1 el modelo tiene una pista muy directa.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
