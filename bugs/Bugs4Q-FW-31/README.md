# Bugs4Q-FW-31

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-31` |
| Origen | Bugs4Q-Framework, bug 31 (`qiskit/31/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackExchange 8893](https://quantumcomputing.stackexchange.com/questions/8893/why-is-the-order-reversed-on-measurement) ("Why is the order reversed on measurement?", publicada y respondida el 21-nov-2019) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_31.py`, `fixed_31.py`, `test_b31.py`, `test_f31.py` (los cuatro copiados sin cambios del Framework) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa aplica `X` al qubit 0 y `CX(0, 1)`, mide los tres qubits en los bits `[0, 1, 2]` y espera leer `110` (q0 a la izquierda). Qiskit devuelve siempre `011`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
    self.assertEqual(counts['110'],1000)
KeyError: '110'
...
Total count: {'011': 1000}
```

El programa no lanza ninguna excepción; la `KeyError` la produce el test al buscar la clave `'110'`, que no existe en los conteos.

El usuario esperaba obtener `{'110': 1000}` (leyendo q0 como bit más significativo); en cambio recibe `{'011': 1000}`, porque Qiskit escribe el bit clásico 0 a la derecha.

## 3. Causa

Según la respuesta aceptada, es una cuestión de convención: Qiskit trata `q0` como el bit menos significativo (LSB), así que la cadena de resultados se lee de derecha a izquierda. Si se quiere que `q0` sea el más significativo hay que medirlo en el bit clásico más alto. No es un defecto de Qiskit, sino un malentendido de la convención de orden de bits (mal uso de la API).

## 4. Corrección (`fixed`)

Cambio entre `buggy_31.py` y `fixed_31.py` (`modify_31.txt` del Framework):

```diff
-circuit.measure([0,1,2], [0,1,2])
+circuit.measure([0,1,2], [2,1,0])
```

El cambio está en el programa, no en la librería.

La corrección funciona porque mide `q0` en el bit clásico 2, `q1` en el 1 y `q2` en el 0: al imprimir la cadena (bit 2 a la izquierda) el estado de `q0` aparece primero y el resultado es `110`, como esperaba el usuario.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.12.0`, `qiskit-aer==0.4.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug31/requirements.txt`](../../envs/bug31/requirements.txt) |

La pregunta no indica versiones. Por su fecha (noviembre de 2019) correspondería Qiskit 0.13 (Terra 0.10/0.11, Aer 0.3). Se probaron:

- Terra 0.11.x / Aer 0.3.4: no hay wheels para Python 3.8 en Windows (Terra 0.11.1 falla al compilar desde el sdist; Aer 0.3.4 no tiene distribución binaria para cp38), no se pudo instalar.
- Terra 0.12.0 + Aer 0.4.0 (primeras con wheel cp38 para Windows): buggy falla y fixed pasa.

Se eligió Terra 0.12.0 + Aer 0.4.0 por ser la combinación instalable más cercana a la fecha de la pregunta que cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta. El test usa `Aer`, así que se instala `qiskit-aer` (que a su vez trae `Cython` y `pybind11`).

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug31/.venv
envs/bug31/.venv/Scripts/python -m pip install -r envs/bug31/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 31

# opción B: manual
cd bugs/Bugs4Q-FW-31
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug31/.venv/Scripts/python -W ignore test_b31.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug31/.venv/Scripts/python -W ignore test_f31.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug31/.venv/bin/python` en lugar de `envs/bug31/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b31.py` | falla (exit 1) | falla, exit 1 las 3 veces (`KeyError: '110'`) | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f31.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests ejecutan 1000 shots en `Aer` y comprueban que `counts['110'] == 1000`. El circuito no tiene superposición, así que el resultado es determinista.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El Framework trae test para buggy y fixed; se usan sin modificar.
- El test falla en buggy y pasa en fixed, de forma estable (3/3) y determinista.
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un malentendido de la convención little-endian de Qiskit, no un defecto: el resultado `011` es correcto según la documentación. Que la versión buggy sea un "bug" depende de lo que el usuario quería leer.
- En buggy el test termina con error (`KeyError`) y no con `AssertionError`, porque la clave esperada no existe; igualmente da exit 1.
- No hay wheels de las versiones de la época (Terra 0.11 / Aer 0.3) para Python 3.8 en Windows; se usa Terra 0.12.0 + Aer 0.4.0.
- El mensaje del test (`KeyError: '110'` en la línea del `assertEqual`, con `{'011': 1000}` impreso) muestra el resultado invertido, lo que es una pista razonable hacia el orden de medición; aun así no señala la línea `circuit.measure(...)`. En C1 el LLM tendría que conocer la convención de orden de bits de Qiskit.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
