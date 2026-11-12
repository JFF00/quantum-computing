# Bugs4Q-FW-23

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-23` |
| Origen | Bugs4Q-Framework, bug 23 (`qiskit/23/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackOverflow 69245836](https://stackoverflow.com/questions/69245836/getting-figure-x-when-drawing-quantum-circuit-with-qiskit-mpl-output-mo) |
| Categoría (Framework) | Figure problem |
| Archivos | `buggy_23.py`, `fixed_23.py`, `test_b23.py`, `test_f23.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

`print(Qc.draw(output='mpl'))` imprime el texto `Figure(179.906x284.278)` en lugar de mostrar el circuito. No lanza excepción. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
- Figure(179.906x284.278)
```

El usuario espera ver el dibujo del circuito, pero recibe en la salida estándar la representación textual del objeto `Figure`.

## 3. Causa

`draw(output="mpl")` devuelve un objeto `matplotlib.figure.Figure`; `print` solo imprime su `repr`. Para visualizarlo hay que mostrar la figura (`.show()`), no imprimirla.

## 4. Corrección (`fixed`)

Cambio entre `buggy_23.py` y `fixed_23.py`:

```diff
-print(Qc.draw(output = 'mpl'))
-print ('')
+Qc.draw('mpl').show()
```

El cambio está en el programa, no en la librería.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.18.3` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug23/requirements.txt`](../../envs/bug23/requirements.txt) |

El Framework no indica versiones. Se eligió Terra 0.18.3 porque en ella se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

Los tests fuerzan el backend `Agg` de matplotlib (sin ventana) y capturan `stdout`; el test comprueba que no se imprima el `repr` de la `Figure`.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.8 con Terra 0.18 se instala vía plataforma Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug23/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.8
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install -r envs/bug23/requirements.txt

cd bugs/Bugs4Q-FW-23
python -W ignore test_b23.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f23.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b23.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f23.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comparan la salida estándar capturada; solo cambia `print(draw(...))` por `draw(...).show()`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un bug de uso incorrecto de la API y el efecto es visual; el test hace de proxy capturando `stdout`.
- Con `Agg`, `show()` no abre ventana, por lo que lo que se verifica es la ausencia del `repr`, no el dibujo.
- El test fue escrito para este proyecto (el Framework no trae test para este bug).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
