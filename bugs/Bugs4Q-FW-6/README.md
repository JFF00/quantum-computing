# Bugs4Q-FW-6

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-6` |
| Origen | Bugs4Q-Framework, bug 6 (`qiskit/6/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit#1337](https://github.com/Qiskit/qiskit/issues/1337) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_6.py`, `fixed_6.py`, `test_b6.py`, `test_f6.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El circuito de 36 qubits ejecutado en `qasm_simulator` no se simula: el resultado vuelve con error de memoria. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
ERROR:  [Experiment 0] Insufficient memory to run circuit circuit-0 using the statevector simulator. Required memory: 1048576M, max memory: 8192M
```

## 3. Causa

El método por defecto de `qasm_simulator` es `statevector`, que necesita 2^36 amplitudes (1 TB). El circuito es poco entrelazado y se puede simular con otro método.

## 4. Corrección (`fixed`)

Cambio entre `buggy_6.py` y `fixed_6.py`:

```diff
+from qiskit.providers.aer import AerSimulator
-backend_sim = Aer.get_backend('qasm_simulator')
+backend_sim = AerSimulator(method='matrix_product_state')
```

El cambio está en el programa, no en la librería. Aer detecta la falta de memoria antes de reservarla, por lo que el test falla sin consumir recursos de la máquina.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.20.2`, `qiskit-aer==0.10.4` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug6/requirements.txt`](../../envs/bug6/requirements.txt) |

El Framework no indica versiones. Se eligieron las versiones de la tabla porque con ellas se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.8 se instala vía plataforma Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug6/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.8
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install -r envs/bug6/requirements.txt

cd bugs/Bugs4Q-FW-6
python -W ignore test_b6.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f6.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b6.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f6.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que `result.status` sea `COMPLETED`; solo cambia el método del simulador.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un límite de recursos del método de simulación, más que un bug de la API; el resultado depende de `max_memory_mb` (8192 MB en esta máquina).
- El test fue escrito para este proyecto (el Framework no trae test para este bug).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
