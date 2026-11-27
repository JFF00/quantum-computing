# Bugs4Q-FW-28

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-28` |
| Origen | Bugs4Q-Framework, bug 28 (`qiskit/28/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [Quantum Computing StackExchange 15966](https://quantumcomputing.stackexchange.com/questions/15966/was-the-quantum-circuit-attribute-iden-renamed) ("Was the Quantum Circuit Attribute "iden" renamed?", publicada el 10-feb-2021) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_28.py`, `fixed_28.py` (copiados sin cambios del Framework); `test_b28.py`, `test_f28.py` (adaptados, ver sección 4); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa aplica la puerta identidad con `circuit.iden(0)`, un método que ya no existe en la versión de Qiskit usada, y se detiene con `AttributeError`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
  File "test_b28.py", line 8, in test_b28
    circuit.iden(0)
AttributeError: 'QuantumCircuit' object has no attribute 'iden'
...
AssertionError: AttributeError raised
```

El programa lanza una excepción (`AttributeError: 'QuantumCircuit' object has no attribute 'iden'`), la misma que muestra el autor de la pregunta.

El usuario debería recibir un circuito de un qubit con una puerta `I`, pero el programa se detiene antes de dibujarlo.

## 3. Causa

Según las respuestas, `QuantumCircuit.iden()` fue marcado como obsoleto en qiskit-terra 0.13.0 y eliminado en qiskit-terra 0.16.0; su reemplazo es `i()` o `id()`. El autor seguía tutoriales antiguos. No es un defecto de Qiskit sino uso de una API eliminada (cambio de API entre versiones).

## 4. Corrección (`fixed`)

Cambio entre `buggy_28.py` y `fixed_28.py` (`modify_28.txt` del Framework):

```diff
-circuit.iden(0)
+circuit.id(0)
```

El cambio está en el programa, no en la librería.

El cambio resuelve el problema porque `id()` es el nombre actual del método que añade la puerta identidad; hace lo mismo que el antiguo `iden()`, que desde Terra 0.16 ya no existe.

### Modificación de los tests respecto al Framework

Los dos tests del Framework tienen la misma estructura: ejecutan el código dentro de un `try` y **fallan si no se lanza `AttributeError`** (`else: self.fail('AttributeError not raised')`). Con eso:

- `test_b28.py` original **pasa** con el programa buggy (comprueba que el bug se manifiesta).
- `test_f28.py` original **falla** con el programa fixed, porque `id(0)` no lanza ninguna excepción.

Es decir, con los tests originales se obtiene buggy-pasa (exit 0) / fixed-falla (exit 1, `AssertionError: AttributeError not raised`) en Terra 0.16.4 ([`logs/framework_original_buggy_test.log`](logs/framework_original_buggy_test.log), [`logs/framework_original_fixed_test.log`](logs/framework_original_fixed_test.log)). El test fixed del Framework parece copiado del buggy sin invertir la condición. Para aplicar el criterio del proyecto se cambió en **ambos** tests solo la rama del `except`, que ahora falla si se lanza `AttributeError`:

```diff
         except AttributeError:
             print('AttributeError raised')
-            pass
-        else:
-            self.fail('AttributeError not raised')
+            self.fail('AttributeError raised')
```

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.16.4` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug28/requirements.txt`](../../envs/bug28/requirements.txt) |

La pregunta no indica la versión instalada. Se probaron, con los tests del proyecto, Terra 0.15.0, 0.16.3, 0.16.4 y 0.17.4:

- 0.15.0: ambos tests pasan (`iden` todavía existe, solo emite un aviso de obsolescencia): no se reproduce.
- 0.16.3, 0.16.4 y 0.17.4: buggy falla y fixed pasa.

Se eligió Terra 0.16.4 por ser la versión publicada inmediatamente antes de la pregunta (febrero de 2021), dentro de la serie 0.16 en la que, según la respuesta, se eliminó `iden`, y porque cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug28/.venv
envs/bug28/.venv/Scripts/python -m pip install -r envs/bug28/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 28

# opción B: manual
cd bugs/Bugs4Q-FW-28
$env:PYTHONIOENCODING = "utf-8"   # los tests imprimen caracteres de caja
../../envs/bug28/.venv/Scripts/python -W ignore test_b28.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug28/.venv/Scripts/python -W ignore test_f28.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug28/.venv/bin/python` en lugar de `envs/bug28/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b28.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f28.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban que construir y dibujar el circuito no lanza `AttributeError`; solo cambia `iden` por `id`. El test es determinista.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (una línea) está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Los dos tests del Framework tuvieron que adaptarse: con los originales el test fixed falla siempre que `id()` exista (ver sección 4).
- El bug depende por completo de la versión: en Terra ≤ 0.15 el programa buggy funciona.
- Bug muy simple: la traza del test muestra la línea `circuit.iden(0)` dentro del `try` y el mensaje `'QuantumCircuit' object has no attribute 'iden'`, así que en C1 el test fallido prácticamente da la respuesta (el modelo solo tiene que conocer el nombre nuevo del método).

## 9. Pendientes

- [x] Análisis estático (LintQ, 2026-11-27): `ql-deprecated-identity` (media) en buggy, línea 4, que señala el bug, más 1 `ql-unmeasurable-qubits` (media) igual en buggy y fixed. Ver `static_analysis/`.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
