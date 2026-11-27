# Bugs4Q-FW-12

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-12` |
| Origen | Bugs4Q-Framework, bug 12 (`qiskit/12/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#6571](https://github.com/Qiskit/qiskit-terra/issues/6571) ("`measure_all` to use existing classical reg instead of creating new", abierto el 14-jun-2021, cerrado el 15-jun-2021) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_12.py`, `fixed_12.py` (copiados sin cambios del Framework); `test_b12.py`, `test_f12.py` (adaptados para este proyecto, ver sección 7); originales del Framework en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El circuito ya tiene un registro clásico de 2 bits (`creg`), pero `qc.measure_all()` crea un registro nuevo (`meas`) y mide ahí. Los resultados quedan con claves de 4 bits (`'10 00'`), donde la parte de `creg` siempre es `00`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: Lists differ: ['00 00', '01 00', '10 00', '11 00'] != ['00', '01', '10', '11']
```

No se lanza ninguna excepción; el fallo solo se ve al mirar las claves de `get_counts()`.

El usuario esperaba obtener los resultados en su registro `creg` (claves `'00'`, `'01'`, `'10'`, `'11'`), pero recibió un registro extra y un registro `creg` sin usar, lo que además ensucia el histograma.

## 3. Causa

`measure_all()` siempre añade un registro clásico nuevo; no reutiliza los existentes. En el issue, el mantenedor explica que es intencionado (reutilizar un registro podría sobrescribir información del usuario) y que, si ya existe el registro, basta con `qc.measure(qc.qubits, qc.clbits)`. Es un uso incorrecto (o una expectativa errónea) de la API, no un defecto de Qiskit; el issue se cerró sin cambios en la librería.

## 4. Corrección (`fixed`)

Cambio entre `buggy_12.py` y `fixed_12.py` (`modify_12.txt` del Framework):

```diff
-qc.measure_all()
+qc.measure(qc.qubits, qc.clbits)
```

El cambio está en el programa, no en la librería.

`qc.measure(qc.qubits, qc.clbits)` mide cada qubit en el bit clásico correspondiente del registro ya existente, sin crear `meas`, así que los conteos solo tienen las 4 claves de 2 bits.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.17.4`, `qiskit-aer==0.8.2` |
| Dependencias fijadas a mano | `numpy==1.19.5` (fijado por precaución, igual que en los demás bugs con Terra antiguo; no se probó con otras versiones de NumPy). `qiskit-aer` se instala porque el programa usa `Aer.get_backend('qasm_simulator')`. |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug12/requirements.txt`](../../envs/bug12/requirements.txt) |

El issue no indica versiones (los campos están vacíos). Se probaron:

- Terra 0.17.4 + Aer 0.8.2: tests del Framework → buggy pasa (exit 0) y fixed falla (exit 1); tests adaptados → buggy falla y fixed pasa.
- Terra 0.18.3 + Aer 0.9.1: mismo resultado en ambos juegos de tests.

Se eligió Terra 0.17.4 por ser la última versión publicada antes del issue (18-may-2021; issue del 14-jun-2021) y porque con los tests adaptados cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug12/.venv
envs/bug12/.venv/Scripts/python -m pip install -r envs/bug12/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 12

# opción B: manual
cd bugs/Bugs4Q-FW-12
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug12/.venv/Scripts/python -W ignore test_b12.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug12/.venv/Scripts/python -W ignore test_f12.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug12/.venv/bin/python` en lugar de `envs/bug12/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b12.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f12.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests simulan el circuito con 1024 shots en `qasm_simulator` de Aer y comprueban que las claves de `get_counts()` sean exactamente `['00', '01', '10', '11']`; solo cambia la instrucción de medida.

**Modificación respecto al Framework.** Los tests originales ([`framework_tests/test_b12.py`](framework_tests/test_b12.py), [`framework_tests/test_f12.py`](framework_tests/test_f12.py)) comprueban `assertIn('10 00', ...)`, es decir, el comportamiento *buggy*: el de buggy pasa y el de fixed falla, al revés del criterio del proyecto (una ejecución en el entorno final, lanzada fuera de `run_bug_tests.py` con el mismo formato de log: [`logs/framework_original_buggy.log`](logs/framework_original_buggy.log), [`logs/framework_original_fixed.log`](logs/framework_original_fixed.log)). En los tests adaptados se sustituyeron las cuatro líneas `assertIn('xx 00', ...)` por `assertEqual(sorted(res.get_counts().keys()), ['00', '01', '10', '11'])`, que expresa lo que el autor del issue esperaba. El resto (incluido `QiskitTestCase` y `assertDictAlmostEqual` con `delta=500`) se conserva.

**Test a nivel de programa** ([`test_program_12.py`](test_program_12.py), escrito para este proyecto). Ejecuta el archivo indicado en `BUG_PROGRAM` (por defecto `buggy_12.py`) mediante [`scripts/program_harness.py`](../../scripts/program_harness.py), que inyecta `seed_simulator=1234` en `execute()`. Oráculo: el circuito ejecutado tiene 2 bits clásicos (sin registro extra) y los conteos tienen exactamente las claves `['00', '01', '10', '11']`. No contiene el código corregido. Comando: `python scripts/run_bug_tests.py 12 --program-test`.

| Programa | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|
| `buggy_12.py` | falla (exit 1) | falla, exit 1 las 3 veces (`4 != 2` bits clásicos) | [run1](logs/program_buggy_run1.log), [run2](logs/program_buggy_run2.log), [run3](logs/program_buggy_run3.log) |
| `fixed_12.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/program_fixed_run1.log), [run2](logs/program_fixed_run2.log), [run3](logs/program_fixed_run3.log) |

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- Con los tests adaptados, falla en buggy y pasa en fixed de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un uso incorrecto de la API (o una petición de funcionalidad rechazada), no un defecto de Qiskit.
- Los tests del Framework tienen el sentido invertido; los usados aquí son una adaptación del proyecto (el oráculo es nuevo).
- Hay simulación con shots y sin semilla; el test solo depende de que aparezcan las 4 claves en 1024 shots, lo que es prácticamente seguro, pero no es estrictamente determinista. `assertDictAlmostEqual` con `delta=500` pasa también en buggy (las claves que faltan cuentan como 0), así que no aporta al oráculo.
- Requiere `qiskit-aer` (rueda binaria para Windows y Python 3.8).
- El mensaje del test (`Lists differ: ['00 00', ...] != ['00', ...]`) muestra el registro extra pero no señala `measure_all()`; en C1 el LLM tendría que saber que `measure_all` crea un registro nuevo. La pista es clara para quien conozca la API.

## 9. Pendientes

- [x] Análisis estático (LintQ, 2026-11-27): 1 warning `ql-measure-all-abuse` (alta) en buggy, línea 6, que señala el bug; 0 en fixed. Ver `static_analysis/`.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [x] Añadido a `data/selected_bugs.csv` (piloto) el 2026-11-27, después de ver los resultados de LintQ.
- [ ] Marcar `selected` en `data/bugs_inventory.xlsx`.
