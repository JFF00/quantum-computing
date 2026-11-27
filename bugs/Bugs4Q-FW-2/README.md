# Bugs4Q-FW-2

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-2` |
| Origen | Bugs4Q-Framework, bug 2 (`qiskit/2/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-machine-learning#177](https://github.com/Qiskit/qiskit-machine-learning/issues/177) ("ad_hoc_data(…) resulting in the test dataset as an array instead of a dictionary", abierto el 31-jul-2021, cerrado el 01-ago-2021) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_2.py`, `fixed_2.py` (copiados sin cambios del Framework); `test_b2.py`, `test_f2.py` (escritos para este proyecto: el Framework no trae tests para este bug) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa (copiado de un tutorial de Qiskit) desempaqueta el resultado de `ad_hoc_data(...)` como `sample_Total, training_input, test_input, class_labels`, esperando que `test_input` sea un diccionario `{clase: muestras}`. En `qiskit-machine-learning` la función devuelve arrays de NumPy, así que el paso siguiente del issue (`split_dataset_to_data_and_labels(test_input)`, que llama a `test_input.keys()`) lanza `AttributeError`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
    sorted_classes_name = sorted(list(test_input.keys()))
AttributeError: 'numpy.ndarray' object has no attribute 'keys'
```

Sí se lanza una excepción (`AttributeError`), aunque no en la llamada a `ad_hoc_data` sino al usar su resultado: el desempaquetado en cuatro variables no falla y deja datos con un significado distinto del esperado.

El usuario esperaba recibir el conjunto de test como diccionario por clase; recibió un `numpy.ndarray` (las características de test) y el programa falla al tratarlo como diccionario.

## 3. Causa

Según el autor del issue, `ad_hoc_data` devuelve el conjunto de test como array en lugar de diccionario, mientras que el código del tutorial (basado en `qiskit-aqua`, `split_dataset_to_data_and_labels`) espera un diccionario. Del diff se deduce que es un cambio de API entre `qiskit-aqua` y `qiskit-machine-learning`: la nueva función devuelve `(train_features, train_labels, test_features, test_labels[, sample_total])`. Es un mal uso de la API nueva (código escrito para la antigua), no un defecto de Qiskit. Solo se consultó el cuerpo del issue, no los comentarios del cierre.

## 4. Corrección (`fixed`)

Cambio entre `buggy_2.py` y `fixed_2.py` (`modify_2.txt` del Framework):

```diff
-sample_Total,training_input,test_input,class_labels = ad_hoc_data(training_size=training_dataset_size,
-                                                               test_size=testing_dataset_size,
-                                                               gap=0.3,
-                                                               n=feature_dim,
-                                                               plot_data=True)
-
+train_features, train_labels, test_features, test_labels, adhoc_total = ad_hoc_data(
+    training_size=training_dataset_size,
+    test_size=testing_dataset_size,
+    n=feature_dim,
+    gap=0.3,
+    plot_data=True, one_hot=False, include_sample_total=True
+)
```

El cambio está en el programa, no en la librería.

La corrección desempaqueta el resultado con la firma real de `qiskit-machine-learning` (características y etiquetas por separado, más la muestra total al pedir `include_sample_total=True`) y pide etiquetas no codificadas en one-hot, de modo que cada variable contiene lo que su nombre indica y el conjunto de test se usa como array.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-machine-learning==0.2.0`, `qiskit-terra==0.18.0` |
| Dependencias fijadas a mano | `matplotlib==3.4.2` (`plot_data=True` lo requiere; sin él ambos tests terminan con `MissingOptionalLibraryError`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug2/requirements.txt`](../../envs/bug2/requirements.txt) |

El issue indica `qiskit-machine-learning` 0.2.0, Python 3.8.5 y Windows 10. Se probaron `qiskit-machine-learning` 0.1.0, 0.2.0 y 0.2.1 (con Terra 0.18.0):

- Sin `matplotlib`: ambos tests terminan con `MissingOptionalLibraryError` (no se pudo iniciar la comprobación).
- 0.1.0, 0.2.0 y 0.2.1 con `matplotlib`: buggy falla (`AttributeError`) y fixed pasa.

Se eligió 0.2.0 porque es la versión indicada en el issue y en ella se cumple el criterio buggy-falla / fixed-pasa; Terra 0.18.0 es la versión publicada en la fecha del issue. Es una decisión del investigador, no un dato del benchmark.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug2/.venv
envs/bug2/.venv/Scripts/python -m pip install -r envs/bug2/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 2

# opción B: manual
cd bugs/Bugs4Q-FW-2
$env:MPLBACKEND = "Agg"   # plot_data=True dibuja con matplotlib; sin ventana
../../envs/bug2/.venv/Scripts/python -W ignore test_b2.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug2/.venv/Scripts/python -W ignore test_f2.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug2/.venv/bin/python` en lugar de `envs/bug2/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b2.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f2.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban lo mismo: que el conjunto de test obtenido por el programa contiene `2 * testing_dataset_size` = 20 muestras. En buggy se cuentan como lo haría `split_dataset_to_data_and_labels` (recorriendo `test_input.keys()`), que es el uso que el programa del issue hace del resultado; en fixed, con `len(test_features)`. El generador del conjunto `ad_hoc` es aleatorio, pero la comprobación (tipo y número de muestras) no depende de la semilla.

**Tests escritos para este proyecto.** El Framework no trae tests para el bug 2, y `buggy_2.py` por sí solo no lanza ninguna excepción (el error del issue aparece en la línea siguiente, que no está en el programa del Framework). Por eso `test_b2.py` ejecuta la llamada de `buggy_2.py` y añade el paso del issue que consume `test_input` como diccionario; `test_f2.py` ejecuta la llamada de `fixed_2.py`. Ambos mantienen los parámetros del programa (incluido `plot_data=True`) y omiten las variables no usadas (`random_seed`, `shots`).

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado, con la versión de `qiskit-machine-learning` que indica el issue.

Limitaciones:
- El test fue escrito para este proyecto y añade al buggy una línea que no está en `buggy_2.py` (el uso de `test_input.keys()`, tomado del issue); sin ella el programa buggy no falla.
- Es un mal uso de la API (código escrito para `qiskit-aqua`), no un defecto de Qiskit.
- Requiere `matplotlib` solo por `plot_data=True`.
- El mensaje de error (`'numpy.ndarray' object has no attribute 'keys'`) apunta a la línea del test que usa `test_input`, no a la llamada a `ad_hoc_data` donde está el desempaquetado incorrecto; para C1 da una pista útil (el tipo devuelto) pero no la línea a corregir.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
