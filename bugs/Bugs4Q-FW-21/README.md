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
| Python | 3.8.20 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.18.3` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug21/requirements.txt`](../../envs/bug21/requirements.txt) |

El Framework no indica versiones. Se eligió Terra 0.18.3 porque en ella se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

Los tests usan `BasicAer` en lugar de `Aer` (no se instala `qiskit-aer`). `test_f21.py` reproduce el programa fixed pero prepara `X` en lugar de `u(0.3, 0.2, 0.1)` para que el resultado sea determinista (teleportar `|1>` debe dar `1`).

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.8 con Terra 0.18 se instala vía plataforma Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug21/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.8
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install -r envs/bug21/requirements.txt

cd bugs/Bugs4Q-FW-21
python -W ignore test_b21.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f21.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```

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

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
