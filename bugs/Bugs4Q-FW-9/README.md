# Bugs4Q-FW-9
## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-9` |
| Origen | Bugs4Q-Framework, bug 9 (`qiskit/9/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#5249](https://github.com/Qiskit/qiskit-terra/issues/5249) ("Framechanges cannot be parametrized", abierto y cerrado el 16-oct-2020) |
| Categoría (Framework) | Wrong Command |
| Archivos | `buggy_9.py`, `fixed_9.py`, `test_b9.py`, `test_f9.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

Dentro de `pulse.build(...)`, el programa construye un `ShiftPhase` parametrizado, pero el schedule resultante no contiene ninguna instrucción: `phase_test_sched.instructions` devuelve `()`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: '()' != '((0, ShiftPhase(phase, DriveChannel(0))),)'
- ()
+ ((0, ShiftPhase(phase, DriveChannel(0))),)
```

El programa no lanza ninguna excepción; el fallo solo se detecta al comparar `instructions` con el valor esperado.

El usuario debería recibir un schedule con la instruccion de un ShiftPhase sobre un DriveChannel(0), sin embargo lo recibe vacío y sin aviso de error.

## 3. Causa
Desde el issue se obtiene, según el autor, que no es un bug si no que mal uso del comando.

## 4. Corrección (`fixed`)

Cambio entre `buggy_9.py` y `fixed_9.py`:

```diff
-    pulse.ShiftPhase(phase, pulse.drive_channel(0))
+    pulse.shift_phase(phase, pulse.drive_channel(0))
```

(El resto de diferencias son líneas en blanco.) El cambio está en el programa, no en la librería.


El cambio resuelve ya que el usuario utilizó la clase, no la función del builder, que se encuentra en minúsculas.


## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.16.1` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug9/requirements.txt`](../../envs/bug9/requirements.txt) |

El issue **no indica versiones** (los campos de Terra, Python y sistema operativo están vacíos). Se eligió Terra 0.16.1 por la fecha del issue (octubre de 2020) y porque con esa versión se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue.


## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.8 con Terra 0.16 se instala vía plataforma Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug9/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.8
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install "qiskit-terra==0.16.1"

cd bugs/Bugs4Q-FW-9
python -W ignore test_b9.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f9.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```
## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b9.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f9.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban la misma salida esperada, `'((0, ShiftPhase(phase, DriveChannel(0))),)'`; solo cambia la llamada dentro del builder.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un bug de uso incorrecto de la API (clase en lugar de función del builder), y el issue se cerró casi de inmediato: mal uso y no un defecto de Qiskit.
- El código usa `qiskit.test.mock` y `pulse.build`, APIs que desaparecen en versiones modernas de Qiskit, así que el bug solo es reproducible en versiones antiguas.
- El mensaje de error del test no indica donde está el error, por lo que en C1 probablemente dependa de el conocimiento del llm sobre la API.


## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
