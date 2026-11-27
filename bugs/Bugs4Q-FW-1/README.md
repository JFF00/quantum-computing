# Bugs4Q-FW-1

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-1` |
| Origen | Bugs4Q-Framework, bug 1 (`qiskit/1/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#5098](https://github.com/Qiskit/qiskit-terra/issues/5098) ("add the missing `label` parameter to gate functions that produce a single gate", abierto el 21-sep-2020; la API de GitHub da como fecha de cierre el 27-jul-2026) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_1.py`, `fixed_1.py` (copiados sin cambios); `test_b1.py`, `test_f1.py` (adaptados, ver §7); `framework_tests/test_b1.py`, `framework_tests/test_f1.py` (tests originales del Framework, sin cambios, conservados como referencia) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa añade una `cx` y una `ccx` pasando `label='Label'` y `ctrl_state` como enteros. La llamada a `ccx` lanza `TypeError` porque el método no acepta `label`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: TypeError raised: ccx() got an unexpected keyword argument 'label'
```

Sí se lanza una excepción (`TypeError`) en el programa; el test adaptado la captura y la convierte en fallo.

El usuario debería haber obtenido un circuito con la `ccx` etiquetada y con el estado de control indicado, pero el programa se interrumpe en la segunda puerta.

## 3. Causa

Según el autor del issue, varios métodos de `QuantumCircuit` que construyen puertas controladas (`ccx`, `toffoli`, `mcx`, `rccx`, `rcccx`, `fredkin`, `mcu1`) no aceptan `label` ni `ctrl_state`, aunque las clases de puerta sí; propone añadir esos parámetros y pasarlos a las clases. Es una limitación real de la API de Qiskit (parámetros que faltan), no un error de cálculo; el programa `fixed` la esquiva sin usar esos parámetros.

## 4. Corrección (`fixed`)

Cambio entre `buggy_1.py` y `fixed_1.py` (`modify_1.txt` del Framework):

```diff
-qc.cx(0, 1, label='Label', ctrl_state=0)
-qc.ccx(0, 1, 2, label='Label', ctrl_state=1)
+qc.cx(0, 1, ctrl_state='0')
+qc.ccx(0, 1, 2, ctrl_state='00')
```

El cambio está en el programa, no en la librería.

La corrección elimina el argumento `label`, que `ccx` no acepta, y pasa `ctrl_state` como cadena con un bit por cada control. Ojo: en las versiones de Terra de la época del issue (0.15 – 0.17) `ccx` tampoco acepta `ctrl_state`, así que el `fixed` también lanza `TypeError`; solo funciona a partir de Terra 0.18.0 (ver §5).

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.18.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (mismo criterio que el resto de bugs con Terra antiguo; no se comprobó si es imprescindible en 0.18.0) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug1/requirements.txt`](../../envs/bug1/requirements.txt) |

El issue indica Terra `master` (sep-2020), Python 3.8 y Ubuntu 18.04. Se probaron, ejecutando `buggy_1.py` y `fixed_1.py` en el mismo entorno, Terra 0.15.0, 0.16.0, 0.17.4, 0.18.0, 0.18.3, 0.19.2, 0.20.2 y 0.21.2:

- 0.15.0 – 0.17.4: buggy lanza `TypeError: ccx() got an unexpected keyword argument 'label'` y fixed lanza `TypeError: ccx() got an unexpected keyword argument 'ctrl_state'`.
- 0.18.0 – 0.21.2: buggy lanza el mismo `TypeError` por `label` y fixed se ejecuta sin error.

Con los tests originales del Framework, en 0.16.0 ambos pasan (exit 0) y en 0.18.0 buggy pasa (exit 0) y fixed falla (exit 1, `TypeError not raised`). Con los tests adaptados, en 0.18.0 buggy falla y fixed pasa. Se eligió 0.18.0, la primera versión probada en la que el `fixed` funciona y se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug1/.venv
envs/bug1/.venv/Scripts/python -m pip install -r envs/bug1/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 1

# opción B: manual
cd bugs/Bugs4Q-FW-1
../../envs/bug1/.venv/Scripts/python -W ignore test_b1.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug1/.venv/Scripts/python -W ignore test_f1.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug1/.venv/bin/python` en lugar de `envs/bug1/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b1.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f1.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban lo mismo: que construir el circuito no lanza `TypeError` (si se lanza, `self.fail('TypeError raised: ...')`). El test es determinista.

**Modificación respecto del Framework.** Los tests originales (`framework_tests/test_b1.py`, `framework_tests/test_f1.py`) exigen que se lance `TypeError` en ambos casos (`self.fail('TypeError not raised')` en caso contrario). Con esa aserción el test de fixed solo puede pasar si el programa corregido también falla, lo que contradice la corrección: no hay ninguna versión en la que den buggy-falla / fixed-pasa. En `test_b1.py` y `test_f1.py` se mantuvo el mismo código del programa y se invirtió solo la aserción: el bloque `except TypeError` ahora llama a `self.fail(...)` y se eliminó el `else: self.fail('TypeError not raised')`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (dos líneas) está en el programa del usuario, no en Qiskit.
- El test (adaptado) falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- El origen es una limitación real de la API de Qiskit (faltan `label`/`ctrl_state` en `ccx`); el `fixed` es un rodeo, no una corrección de un mal uso.
- El `fixed` solo funciona desde Terra 0.18.0, posterior al issue (jul-2021 frente a sep-2020); en la versión del issue también lanza `TypeError`.
- Los tests del Framework se adaptaron (aserción invertida); los originales se conservan junto a los adaptados.
- El mensaje de error del test (`ccx() got an unexpected keyword argument 'label'`) indica la puerta y el argumento que sobra, así que para C1 apunta directamente a la línea defectuosa.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
