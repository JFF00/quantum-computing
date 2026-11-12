# Bugs4Q-FW-34

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-34` |
| Origen | Bugs4Q-Framework, bug 34 (`qiskit/34/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackExchange 15925](https://quantumcomputing.stackexchange.com/questions/15925/q-sphere-representation-of-bell-states) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_34.py`, `fixed_34.py`, `test_b34.py`, `test_f34.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

Al aplicar `H` en el qubit 0 y `CX(0,1)` sobre `Statevector.from_label('01')` no se obtiene el estado de Bell esperado `(|01> + |10>)/√2`, sino `(|00> - |11>)/√2`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: '[(0.707+0j), 0j, 0j, (-0.707+0j)]' != '[0j, (0.707+0j), (0.707+0j), 0j]'
```

No hay excepción; solo se detecta comparando el estado.

## 3. Causa

Qiskit usa orden little-endian: en la etiqueta `'01'` el qubit 0 es el dígito de la derecha. El usuario interpretó la etiqueta en el orden inverso, por lo que preparó un estado inicial distinto al que quería.

## 4. Corrección (`fixed`)

Cambio entre `buggy_34.py` y `fixed_34.py`:

```diff
-sv = Statevector.from_label('01')
+sv = Statevector.from_label('10')
```

El cambio está en el programa, no en la librería.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.18.3` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug34/requirements.txt`](../../envs/bug34/requirements.txt) |

El Framework no indica versiones. Se eligió Terra 0.18.3 porque en ella se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

`plot_state_qsphere` (la parte visual) no se prueba; el test comprueba directamente el vector de estado que se le pasaría.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.8 con Terra 0.18 se instala vía plataforma Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug34/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.8
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install -r envs/bug34/requirements.txt

cd bugs/Bugs4Q-FW-34
python -W ignore test_b34.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f34.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b34.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f34.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comparan el estado final redondeado; solo cambia la etiqueta inicial.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un bug de interpretación del orden de qubits (convención de la API), no un defecto de Qiskit.
- El test no ejercita `plot_state_qsphere`.
- El test fue escrito para este proyecto (el Framework no trae test para este bug).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
