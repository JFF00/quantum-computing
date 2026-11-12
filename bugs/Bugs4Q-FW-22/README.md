# Bugs4Q-FW-22

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-22` |
| Origen | Bugs4Q-Framework, bug 22 (`qiskit/22/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackOverflow 69598995](https://stackoverflow.com/questions/69598995/qiskits-draw-only-shows-the-circuits-name-and-not-the-architecture) |
| Categoría (Framework) | Unfamiliar with API |
| Archivos | `buggy_22.py`, `fixed_22.py`, `test_b22.py`, `test_f22.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

`ZZFeatureMap(...).draw()` muestra solo una caja con el nombre del circuito, no sus puertas. No lanza excepción; solo se detecta al inspeccionar el dibujo. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: 0 != 4
     ┌──────────────────────────┐
q_0: ┤0                         ├
     │  ZZFeatureMap(x[0],x[1]) │
q_1: ┤1                         ├
     └──────────────────────────┘
```

El usuario espera ver la arquitectura (H, P, CX), pero recibe una única caja.

## 3. Causa

`ZZFeatureMap` es un circuito compuesto: sus puertas están empaquetadas dentro de una sola instrucción, y `draw()` dibuja esa instrucción sin abrirla. No es un defecto de Qiskit sino desconocimiento de la API.

## 4. Corrección (`fixed`)

Cambio entre `buggy_22.py` y `fixed_22.py`:

```diff
-zz.draw("mpl")
+zz.decompose().draw("mpl")
```

El cambio está en el programa, no en la librería. `decompose()` expande la caja en sus puertas básicas antes de dibujar.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.18.3` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug22/requirements.txt`](../../envs/bug22/requirements.txt) |

El Framework no indica versiones. Se eligió Terra 0.18.3 porque en ella se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

Los tests usan `draw("text")` en lugar de `draw("mpl")` para poder comprobar el dibujo sin abrir una figura; el comportamiento (caja única vs. puertas expandidas) es el mismo.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.8 con Terra 0.18 se instala vía plataforma Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug22/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.8
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install -r envs/bug22/requirements.txt

cd bugs/Bugs4Q-FW-22
python -W ignore test_b22.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f22.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b22.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f22.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests cuentan las puertas `H` del dibujo esperadas (4: 2 qubits × 2 repeticiones); solo cambia si se llama a `decompose()`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un bug de uso incorrecto de la API y el efecto es visual, por lo que el test hace de proxy sobre el dibujo en texto.
- El test fue escrito para este proyecto (el Framework no trae test para este bug).
- Al ser bug simple, el test fallido probablemente le dé la respuesta inmediata al modelo (poco margen para C2/C3 sobre C1).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
