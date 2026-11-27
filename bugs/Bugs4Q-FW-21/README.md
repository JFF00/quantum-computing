# Bugs4Q-FW-21

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-21` |
| Origen | Bugs4Q-Framework, bug 21 (`qiskit/21/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackOverflow 60918011](https://stackoverflow.com/questions/60918011/implement-quantum-teleportation-in-qiskit) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_21.py`, `fixed_21.py`, `test_b21.py`, `test_f21.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa de teleportación prepara `|1>` en el qubit 0, pero el resultado nunca contiene el qubit teleportado: el bit más significativo de la memoria es siempre `0`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: '0' != '1'
```

No hay excepción; solo se detecta comparando la salida con la esperada.

## 3. Causa

`qc.measure(2, 2)` se agrega **después** de `execute(...)`, así que el circuito ejecutado nunca mide el qubit 2 y su bit clásico queda en 0. Además, las correcciones no se aplican de forma condicionada a los resultados clásicos.

## 4. Corrección (`fixed`)

Cambio entre `buggy_21.py` y `fixed_21.py`:

```diff
Reescritura completa: `fixed_21.py` es el ejemplo oficial de teleportación de Qiskit (registros clásicos separados, correcciones con `c_if` y medición del qubit 2 antes de ejecutar).
```

El cambio está en el programa, no en la librería.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.18.3`, `qiskit-aer==0.9.1` |
| Dependencias fijadas a mano | `qiskit-aer==0.9.1` (necesario para ejecutar `buggy_21.py`, que usa `Aer`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug21/requirements.txt`](../../envs/bug21/requirements.txt) |

El Framework no indica versiones. Se eligió Terra 0.18.3 porque en ella se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

Historial del entorno: el bug se probó primero en macOS (conda `osx-64`, Python 3.8.20, Terra 0.18.3 sin `qiskit-aer`). Al seleccionarlo para el piloto se reconstruyó en Windows con `uv` y se añadió `qiskit-aer==0.9.1`, porque los tests a nivel de programa (sección 10) ejecutan `buggy_21.py`, que importa `Aer`. Los logs actuales son de Windows.

Los tests `test_b21.py` y `test_f21.py` (escritos para el proyecto) usan `BasicAer` en lugar de `Aer`. `test_f21.py` reproduce el programa fixed pero prepara `X` en lugar de `u(0.3, 0.2, 0.1)` para que el resultado sea determinista (teleportar `|1>` debe dar `1`).

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug21/.venv
envs/bug21/.venv/Scripts/python -m pip install -r envs/bug21/requirements.txt

python scripts/run_bug_tests.py 21                  # tests test_b21/test_f21, 3 ejecuciones
python scripts/run_bug_tests.py 21 --program-test   # test a nivel de programa (sección 10)
```

En Linux/macOS: `envs/bug21/.venv/bin/python` en lugar de `envs/bug21/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b21.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f21.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests ejecutan 1 shot y comprueban que el bit del qubit 2 (primer carácter de la memoria) sea `1`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- El `fixed` es una reescritura completa, no una corrección mínima.
- El test de fixed difiere ligeramente del ejemplo original (prepara `X`) y ambos usan `BasicAer` en lugar de `Aer`.
- El test fue escrito para este proyecto (el Framework no trae test para este bug).

## 9. Pendientes

- [x] Análisis estático (LintQ, 2026-11-27): 2 warnings `ql-operation-after-measurement` (alta) en buggy, 0 en fixed y 2 en fixed_21_min.py; patrón cercano, no la causa. Ver `static_analysis/`.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.

## 10. Test a nivel de programa (piloto)

Seleccionado para el piloto de la semana 10. Los tests de las secciones anteriores llevan el código del programa copiado dentro, por lo que no pueden validar un parche. [`test_program_21.py`](test_program_21.py) (escrito para el proyecto) ejecuta en cambio el **archivo** indicado en la variable `BUG_PROGRAM` mediante [`scripts/program_harness.py`](../../scripts/program_harness.py), que captura stdout, las variables finales del programa y las llamadas a `execute()` (inyectando `seed_simulator=1234` si el programa no fija semilla).

**Oráculo.** Registra el circuito y el resultado de la llamada a `execute()` del programa (con semilla fija) y comprueba que el bit clásico del qubit 2 (el qubit teleportado) vale `1` en todos los shots. Si el qubit 2 no se mide en el circuito ejecutado, se lee el bit clásico 2. La referencia es `fixed_21_min.py` (corrección mínima escrita para el proyecto: mover `qc.measure(2, 2)` antes de `execute()`), porque `fixed_21.py` del Framework teleporta otro estado (`u(0.3, 0.2, 0.1)`) y no cumple este oráculo (comprobado: falla con `{'0': 1003, '1': 21}`). Las `cx`/`cz` incondicionales tras medir los qubits 0 y 1 equivalen a correcciones condicionadas (medición diferida), por lo que no hace falta `c_if`.

El test no contiene el código corregido, para no filtrar la solución en la condición C1.

```powershell
cd bugs/Bugs4Q-FW-21
$env:BUG_PROGRAM = "buggy_21.py"; ../../envs/bug21/.venv/Scripts/python -W ignore test_program_21.py   # exit 1
$env:BUG_PROGRAM = "fixed_21_min.py"; ../../envs/bug21/.venv/Scripts/python -W ignore test_program_21.py   # exit 0
# o bien, desde la raíz: python scripts/run_bug_tests.py 21 --program-test
```

| Programa | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|
| `buggy_21.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/program_buggy_run1.log), [run2](logs/program_buggy_run2.log), [run3](logs/program_buggy_run3.log) |
| `fixed_21_min.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/program_fixed_run1.log), [run2](logs/program_fixed_run2.log), [run3](logs/program_fixed_run3.log) |

Fragmento de [`logs/program_buggy_run1.log`](logs/program_buggy_run1.log):

```
AssertionError: 1 != 0 : el qubit teleportado debería medirse siempre como '1': {'0': 1, '1': 0}
```

Para validar un parche: guardarlo como archivo en esta carpeta y ejecutar el test con `BUG_PROGRAM=<archivo del parche>`.
