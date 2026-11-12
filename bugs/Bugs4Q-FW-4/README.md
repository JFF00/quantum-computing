# Bugs4Q-FW-4

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-4` |
| Origen | Bugs4Q-Framework, bug 4 (`qiskit/4/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit#1337](https://github.com/Qiskit/qiskit/issues/1337) |
| Categoría (Framework) | Simulation Failed |
| Archivos | `buggy_4.py`, `fixed_4.py`, `test_b4.py`, `test_f4.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

`backend.run(adder)` sobre el simulador `statevector_simulator` no simula: el resultado vuelve con error. No se lanza excepción; solo cambia el estado del resultado. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
ERROR:  [Experiment 0] Circuit CDKMRippleCarryAdder contains invalid instructions {"gates": {CDKMRippleCarryAdder}} for "statevector" method.
```

## 3. Causa

`CDKMRippleCarryAdder` es una puerta compuesta que Aer no reconoce. `backend.run` no transpila el circuito, a diferencia de `execute`, así que la puerta llega sin descomponer al simulador.

## 4. Corrección (`fixed`)

Cambio entre `buggy_4.py` y `fixed_4.py`:

```diff
-job = backend.run(adder)
+transpiled_adder = transpile(adder, backend)
+job = backend.run(transpiled_adder)
```

(También se elimina una línea en blanco.) El cambio está en el programa, no en la librería.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.20.2`, `qiskit-aer==0.10.4` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug4/requirements.txt`](../../envs/bug4/requirements.txt) |

El Framework no indica versiones. Se eligieron las versiones de la tabla porque con ellas se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.8 se instala vía plataforma Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug4/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.8
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install -r envs/bug4/requirements.txt

cd bugs/Bugs4Q-FW-4
python -W ignore test_b4.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f4.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b4.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f4.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que `result.status` sea `COMPLETED`; solo cambia si se transpila el circuito antes de `backend.run`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un bug de uso incorrecto de la API (falta `transpile`).
- Los tests importan `CDKMRippleCarryAdder` explícitamente (el original usa `circuit.library.arithmetic...`, que no resuelve con `from qiskit import *` en Terra 0.20).
- El test fue escrito para este proyecto (el Framework no trae test para este bug).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
