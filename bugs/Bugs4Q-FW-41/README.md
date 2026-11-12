# Bugs4Q-FW-41

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-41` |
| Origen | Bugs4Q-Framework, bug 41 (`qiskit/41/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackExchange 24155](https://quantumcomputing.stackexchange.com/questions/24155/how-to-generate-statevector-evolution) |
| Categoría (Framework) | Simulation Failed |
| Archivos | `buggy_41.py`, `fixed_41.py`, `test_b41.py`, `test_f41.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

Ejecutar en `statevector_simulator` un circuito cuya inicialización usa la cadena `'10'` falla al pedir el vector de estado. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
qiskit.exceptions.QiskitError: 'You have to select a circuit or schedule when there is more than one available'
```

## 3. Causa

`QuantumCircuit.initialize` con una cadena como `'10'` no se interpreta como el vector de estado `|10>`; la transpilación genera un resultado inesperado. El estado inicial debe darse como vector de amplitudes.

## 4. Corrección (`fixed`)

Cambio entre `buggy_41.py` y `fixed_41.py`:

```diff
-qc = quantum_circuit(target_time=0.0, num_qubits=2, initial_state='10')
+qc = quantum_circuit(target_time=0.0, num_qubits=2, initial_state=[0, 0, 1, 0])
```

El cambio está en el programa, no en la librería.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.18.3`, `qiskit-aer==0.9.1` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug41/requirements.txt`](../../envs/bug41/requirements.txt) |

El Framework no indica versiones. Se eligieron las versiones de la tabla porque con ellas se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.8 se instala vía plataforma Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug41/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.8
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install -r envs/bug41/requirements.txt

cd bugs/Bugs4Q-FW-41
python -W ignore test_b41.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f41.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b41.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f41.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests construyen un circuito con `initialize`, lo ejecutan en `statevector_simulator` y comparan el vector con `[0, 0, 1, 0]`; solo cambia el argumento de `initialize`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- El test usa una versión reducida del programa original (solo `initialize`, sin las subrutinas XX, YY y ZZ ni `measure_all`).
- El fallo se manifiesta como excepción al leer el resultado, no como error de la ejecución.
- El test fue escrito para este proyecto (el Framework no trae test para este bug).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
