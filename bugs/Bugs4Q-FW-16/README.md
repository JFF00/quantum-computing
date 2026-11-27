# Bugs4Q-FW-16

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-16` |
| Origen | Bugs4Q-Framework, bug 16 (`qiskit/16/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-aer#135](https://github.com/Qiskit/qiskit-aer/issues/135) ("Statevector simulator gives incorrect result for ghz", abierto el 09-abr-2019 y cerrado el 11-abr-2019) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_16.py`, `fixed_16.py`, `test_b16.py`, `test_f16.py` (los cuatro copiados sin cambios del Framework) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa prepara un estado GHZ de 5 qubits, mide todos los qubits y pide el vector de estado al `statevector_simulator`. En lugar del estado GHZ (amplitud `0.70710678` en `|00000>` y en `|11111>`) se obtiene un vector con una sola amplitud `1` (en `|00000>` o en `|11111>`). Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: '[1.+0.j 0.+0.j 0.+0.j 0.+0.j 0.+0.j 0.+0.j[185 chars]0.j]' != '[0.70710678+0.j 0.        +0.j 0.        +[449 chars]0.j]'
```

En esta ejecución el estado colapsó a `|00000>`; en las ejecuciones 2 y 3 colapsó a `|11111>` (último elemento `1`).

El programa no lanza ninguna excepción; el fallo solo se detecta al comparar el vector de estado con el esperado.

El usuario debería recibir el vector del estado GHZ (superposición de `|00000>` y `|11111>`), pero recibe el estado ya colapsado por la medición (`|11111>` o `|00000>`, al azar).

## 3. Causa

Según la respuesta del mantenedor en el issue, el comportamiento es correcto: el circuito incluye `measure`, así que el vector devuelto es el estado **después** del colapso de la medición; para obtener el estado entrelazado hay que quitar la medición. Es un uso incorrecto de la API, no un defecto de Qiskit Aer. (En el mismo hilo se señala que `BasicAer`, en la versión de entonces, devolvía el estado previo a la medición por una optimización de muestreo, y que eso sí era un defecto de `BasicAer`; en la versión usada aquí `BasicAer` ya devuelve el estado colapsado, igual que Aer.)

## 4. Corrección (`fixed`)

Cambio entre `buggy_16.py` y `fixed_16.py` (`modify_16.txt` del Framework):

```diff
 ghz.barrier(qr)
-ghz.measure(qr,cr)
 ghz.draw()
```

El cambio está en el programa, no en la librería.

Al quitar la medición, el simulador de vector de estado devuelve el estado justo antes del final del circuito, que es el GHZ sin colapsar; el registro clásico queda sin usar.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.12.0` (sin `qiskit-aer`: el programa y los tests usan `BasicAer`) |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra 0.12 usa alias de NumPy eliminados en NumPy ≥ 1.24; además el oráculo compara el texto impreso del vector) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug16/requirements.txt`](../../envs/bug16/requirements.txt) |

El issue indica Qiskit Aer 0.1.1 (abril de 2019), sin versión de Python; la versión de Terra de esa fecha sería 0.8.x. Versiones probadas:

- Terra 0.8.0, 0.8.2, 0.9.0, 0.10.0, 0.11.0 y 0.11.1: no hay wheel para Python 3.8 en Windows; el sdist de 0.8.0 necesita Cython y un compilador de C (no disponible), así que no se pueden instalar.
- Terra 0.12.0, 0.13.0 y 0.16.4 (con `numpy==1.19.5`): buggy falla y fixed pasa.

Se eligió Terra 0.12.0 por ser la versión instalable más cercana a la fecha del issue que cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue. El Framework sustituye `Aer` por `BasicAer` en el programa, por lo que no se instala `qiskit-aer` (el issue es de Aer 0.1.1, que tampoco tiene wheel para Python 3.8).

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug16/.venv
envs/bug16/.venv/Scripts/python -m pip install -r envs/bug16/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 16

# opción B: manual
cd bugs/Bugs4Q-FW-16
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug16/.venv/Scripts/python -W ignore test_b16.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug16/.venv/Scripts/python -W ignore test_f16.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug16/.venv/bin/python` en lugar de `envs/bug16/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b16.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f16.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que el texto del vector de estado sea el del estado GHZ (`0.70710678` en la primera y la última posición); solo cambia la presencia de `measure`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El Framework trae test para buggy y fixed; se usan sin modificar.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un uso incorrecto de la API (medir antes de pedir el vector de estado); el issue se cerró sin cambios en Aer.
- El resultado de buggy es aleatorio (colapsa a `|00000>` o a `|11111>`), pero el test falla en ambos casos, así que el veredicto es estable.
- El oráculo compara el texto impreso del vector, que depende del formato de NumPy: es frágil fuera de la versión fijada.
- Se usa `BasicAer` (como en el Framework) y no Aer, que es el simulador del issue; con versiones antiguas de Terra (≤ 0.8, no instalables aquí) `BasicAer` devolvía el estado sin colapsar y el test de buggy podría haber pasado.
- El mensaje de error del test no señala la línea defectuosa (solo la aserción y un vector distinto); en C1 el modelo tiene que deducir que la medición colapsa el estado, lo que depende de su conocimiento del simulador.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
