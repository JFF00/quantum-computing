# Bugs4Q-FW-26

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-26` |
| Origen | Bugs4Q-Framework, bug 26 (`qiskit/26/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackOverflow 62661255](https://stackoverflow.com/questions/62661255/2-entangle-qubit-gives-all-states-with-25) ("2 entangled qubit gives all states with 25 %", publicada el 30-jun-2020) |
| Categoría (Framework) | Wrong operation with GATE |
| Archivos | `buggy_26.py`, `fixed_26.py` (copiados sin cambios del Framework); `test_b26.py`, `test_f26.py` (adaptados, ver sección 4); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El autor quiere entrelazar dos qubits de forma que al medir salga siempre `01` o `10` con 50 % cada uno, pero aplica `H` a ambos qubits antes del `CNOT` y obtiene los cuatro estados con un 25 % cada uno. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
{'11': 244, '10': 260, '00': 254, '01': 266}
...
AssertionError: ('11': 0 != 244), ('00': 0 != 254), ('01': 500 != 266), ('10': 500 != 260) within 100 delta
```

El programa no lanza ninguna excepción; el fallo solo se detecta al comparar la distribución de conteos con la esperada.

El usuario debería obtener aproximadamente la mitad de los shots en `01` y la otra mitad en `10`, pero obtiene `00`, `01`, `10` y `11` con frecuencias similares.

## 3. Causa

Según las respuestas, aplicar `H` a los dos qubits crea la superposición uniforme de los cuatro estados, y el `CNOT` solo permuta dos de ellos (en la convención de Qiskit, `|01>` y `|11>`), así que el estado no cambia y cada resultado sale con un 25 %. Para obtener el estado de Bell con `01`/`10` hay que aplicar `H` al primer qubit y `X` al segundo antes del `CNOT`. Es un error del programa (puerta equivocada), no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_26.py` y `fixed_26.py` (`modify_26.txt` del Framework):

```diff
 circuit.h(0)
-circuit.h(1)
+circuit.x(1)
 circuit.cx(0,1)
```

El cambio está en el programa, no en la librería.

El cambio resuelve el problema porque con `X` el qubit 1 empieza en `|1>` (no en superposición); el `CNOT` controlado por el qubit 0 (en `|+>`) produce `(|01> + |10>)/√2`, de modo que solo se miden `01` y `10`, cada uno con un 50 %.

### Modificación de los tests respecto al Framework

Los tests del Framework usan `assertDictAlmostEqual(..., delta=500)` con 1024 shots. Con esa tolerancia cualquier distribución razonable está dentro del margen, así que ambos tests originales pasan (exit 0 los dos, en el entorno final: [`logs/framework_original_buggy_test.log`](logs/framework_original_buggy_test.log), [`logs/framework_original_fixed_test.log`](logs/framework_original_fixed_test.log)); además, el test buggy original afirma la distribución uniforme que produce el programa buggy. Para aplicar el criterio del proyecto (buggy falla / fixed pasa) se hicieron dos cambios mínimos:

```diff
 # test_b26.py: mismo valor esperado que el test fixed y tolerancia menor
-		self.assertDictAlmostEqual({'00':250 ,'01': 250,'10': 250,'11': 250},
+		self.assertDictAlmostEqual({'10': 500, '01': 500},
                                    counts,
-                                   delta=500)
+                                   delta=100)

 # test_f26.py: solo la tolerancia
-                                   delta=500)
+                                   delta=100)
```

Con 1024 shots y p = 0,5, cada conteo esperado es 512 con desviación típica 16; la tolerancia de 100 (respecto a 500) deja un margen de unas 5 desviaciones típicas para el fixed, y en el buggy `00` y `11` (~256) y `01`/`10` (~256) quedan muy fuera.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.17.0`, `qiskit-aer==0.8.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug26/requirements.txt`](../../envs/bug26/requirements.txt) |

La pregunta no trae código ni versiones; el código del Framework (`QasmSimulator().run(transpile(circuit, backend), shots=1024)`) es más moderno que la fecha de la pregunta. Se probaron, con los tests del proyecto:

- Terra 0.14.2 + Aer 0.5.2 (versiones de mediados de 2020): ambos tests terminan en error, `TypeError: run() got an unexpected keyword argument 'shots'` (Aer 0.5 solo acepta un `Qobj` en `run`). No se pudo ejecutar el programa.
- Terra 0.16.4 + Aer 0.7.6: ambos tests terminan en error, `AttributeError: 'QuantumCircuit' object has no attribute 'config'` (Aer 0.7 tampoco acepta circuitos en `run`).
- Terra 0.17.0 + Aer 0.8.0: buggy falla y fixed pasa.

Se eligió Terra 0.17.0 + Aer 0.8.0, la combinación más antigua probada en la que el código del Framework se ejecuta y se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug26/.venv
envs/bug26/.venv/Scripts/python -m pip install -r envs/bug26/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 26

# opción B: manual
cd bugs/Bugs4Q-FW-26
$env:PYTHONIOENCODING = "utf-8"   # los tests imprimen caracteres de caja
../../envs/bug26/.venv/Scripts/python -W ignore test_b26.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug26/.venv/Scripts/python -W ignore test_f26.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug26/.venv/bin/python` en lugar de `envs/bug26/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b26.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f26.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que los conteos estén a ±100 de `{'10': 500, '01': 500}` (1024 shots, sin semilla fija); solo cambia `h(1)` por `x(1)`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Los dos tests del Framework tuvieron que adaptarse (valor esperado del buggy y tolerancia de ambos), porque con `delta=500` no distinguen las versiones.
- El test es estadístico (simulación sin semilla); con la tolerancia elegida la probabilidad de un fallo espurio del fixed es despreciable, pero no nula.
- El código del Framework no es el de la pregunta (que no trae código) y requiere Aer ≥ 0.8, posterior a la fecha de la pregunta.
- El mensaje de error del test lista las diferencias por estado (por ejemplo, `'00': 0 != 254`) pero no apunta a ninguna línea del programa; para C1 el modelo tiene que deducir que la puerta `H` del segundo qubit debería ser `X`.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
