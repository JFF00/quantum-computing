# Bugs4Q-FW-20

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-20` |
| Origen | Bugs4Q-Framework, bug 20 (`qiskit/20/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-metapackage#193](https://github.com/Qiskit/qiskit-metapackage/issues/193) ("AttributeError: 'str' object has no attribute 'configuration'", abierto el 03-abr-2019 y cerrado el 27-abr-2019) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_20.py`, `fixed_20.py` (copiados sin cambios del Framework); `test_b20.py`, `test_f20.py` (adaptados, ver sección 5); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

El Framework enlaza `https://github.com/Qiskit/qiskit/issues/193`. Ese repositorio era entonces el metapaquete `qiskit`, hoy renombrado `qiskit-metapackage`; el enlace antiguo ahora lleva a un pull request distinto de qiskit-terra. El código del bug coincide con el que publica un segundo usuario en qiskit-metapackage#193 (22-abr-2019).

## 2. Síntoma

`qk.execute(..., backend='my_backend', ...)` lanza `AttributeError`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
  File "test_b20.py", line 20, in test_b20
    job_1 = qk.execute([test_Z,test_X],backend='my_backend',shots=1000)
AttributeError: 'str' object has no attribute 'configuration'
```

El programa lanza una excepción (`AttributeError`), con el mismo mensaje que el título del issue.

El usuario debería recibir los conteos de los circuitos ejecutados en `qasm_simulator`, pero recibe un error porque `execute` recibe un texto en lugar de un objeto backend.

## 3. Causa

Según las respuestas en el issue, el parámetro `backend` de `execute` debe ser el objeto devuelto por `Aer.get_backend(...)`, no un string; al pasar `'my_backend'` entre comillas se envía el texto y no la variable `my_backend`. El usuario confirmó que, al quitar las comillas, funciona. Es un uso incorrecto de la API, no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_20.py` y `fixed_20.py` (`modify_20.txt` del Framework):

```diff
-job_1 = qk.execute([test_Z,test_X],backend='my_backend',shots=1000)
+job_1 = qk.execute([test_Z,test_X],backend=my_backend,shots=1000)
```

El cambio está en el programa, no en la librería.

Sin comillas se pasa el objeto `AerBackend` guardado en `my_backend`, que sí tiene `configuration()`, y `execute` puede transpilar y ejecutar los circuitos.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.12.0`, `qiskit-aer==0.4.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra 0.12 usa alias de NumPy eliminados en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug20/requirements.txt`](../../envs/bug20/requirements.txt) |

El issue no indica versiones (abril de 2019; por la fecha correspondería a Terra 0.7–0.8 y Aer 0.1–0.2; el traceback muestra `qiskit/tools/compiler.py` y rutas de Python 3.7). Versiones probadas:

- Terra 0.7.x – 0.11.x y Aer < 0.4.0: no hay wheel para Python 3.8 en Windows (el sdist de Terra 0.8.0 necesita Cython y un compilador de C, no disponible), así que no se pueden instalar.
- Terra 0.12.0 + Aer 0.4.0, Terra 0.13.0 + Aer 0.5.0 y Terra 0.16.4 + Aer 0.7.6 (todas con `numpy==1.19.5`): buggy lanza el `AttributeError` y fixed se ejecuta sin error.

Se eligieron Terra 0.12.0 + Aer 0.4.0 por ser las versiones instalables más cercanas a la fecha del issue que cumplen el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue. Para usar exactamente la época del issue haría falta Python 3.7 (no disponible en esta máquina) con Terra 0.7.x–0.8.x y Aer 0.1.x–0.2.x.

**Tests adaptados.** Los tests del Framework, sin cambios, invierten el criterio del proyecto: `test_b20.py` pasa si se lanza `AttributeError` y `test_f20.py` **también** exige un `AttributeError` (`self.fail('AttributeError not raised')`), por lo que falla con el programa corregido. Ejecutados tal cual en este entorno: buggy exit 0, fixed exit 1. Se cambió solo la rama del `try` en ambos tests, para que el test falle si se lanza la excepción:

```diff
         except AttributeError as e:
-            self.assertEqual(type(e), AttributeError)
-           
-        else:
-            self.fail('AttributeError not raised')
+            self.fail('AttributeError raised: %s' % e)
```

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug20/.venv
envs/bug20/.venv/Scripts/python -m pip install -r envs/bug20/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 20

# opción B: manual
cd bugs/Bugs4Q-FW-20
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug20/.venv/Scripts/python -W ignore test_b20.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug20/.venv/Scripts/python -W ignore test_f20.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug20/.venv/bin/python` en lugar de `envs/bug20/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b20.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f20.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests (adaptados) comprueban que `execute(...)`, `result()` y `get_counts` se ejecuten sin lanzar `AttributeError`; solo cambian las comillas alrededor de `my_backend`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un uso incorrecto de la API (string en lugar del objeto backend).
- Versión de Qiskit posterior a la del issue (Terra 0.12.0 frente a 0.7–0.8 en abril de 2019) por falta de wheels para Python 3.8; el mensaje de error es el mismo que el del issue.
- Los tests del Framework se adaptaron (oráculo invertido, ver sección 5); el `test_f20.py` original es erróneo. El oráculo solo comprueba la ausencia de `AttributeError`, no los conteos.
- Usa `circuito + circuito` (suma de `QuantumCircuit`), API que desaparece en versiones modernas de Qiskit. En fixed, `measure_X` no tiene mediciones y Aer avisa `No measurements in circuit`.
- El mensaje de error del test sí señala la línea defectuosa (`execute(..., backend='my_backend', ...)`) y el motivo (`'str' object has no attribute 'configuration'`), por lo que en C1 la pista es muy directa.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
