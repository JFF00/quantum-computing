# Bugs4Q-FW-29

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-29` |
| Origen | Bugs4Q-Framework, bug 29 (`qiskit/29/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackExchange 9246](https://quantumcomputing.stackexchange.com/questions/9246/quantum-phase-estimation-implementation) ("Quantum Phase Estimation implementation", publicada el 18-dic-2019; respuesta con la corrección el 05-ene-2020, no marcada como aceptada) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_29.py`, `fixed_29.py`, `test_b29.py`, `test_f29.py` (los cuatro copiados sin cambios del Framework) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa implementa estimación de fase (QPE) con 3 qubits auxiliares sobre una `cu1` de fase `theta = 0.78`. El resultado más probable debería ser `011` (0.75 en binario), pero aparece con poca frecuencia y el pico queda en `010`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
{'011': 91, '000': 21, '010': 483, '001': 3, '100': 128, '110': 137, '111': 137}
...
AssertionError: 91 != 750 within 250 delta (659 difference)
```

El programa no lanza ninguna excepción; el fallo solo se detecta al comparar los conteos con lo esperado.

El usuario debería obtener `011` (fase estimada 0.75) en la gran mayoría de los shots; en cambio obtiene `011` en menos del 10 % de los casos y una fase estimada equivocada (el usuario reporta 0.25).

## 3. Causa

Según la respuesta en StackExchange, el error está en la QFT inversa escrita por el usuario: faltan las puertas SWAP, la Hadamard debe aplicarse antes de las `cu1` de cada qubit y los ángulos de las `cu1` no son los correctos. Es un error de implementación del algoritmo en el programa del usuario, no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_29.py` y `fixed_29.py` (`modify_29.txt` del Framework):

```diff
+import numpy as np
 def qft_dagger(circ, q, n):
     """n-qubit inverse QFT on q in circ."""
-    for i in range(n-1,-1,-1):
-        for m in range(n-i,1,-1):
-            circ.cu1(-2*math.pi/2**m, q[i+m-1], q[i])
+    # SWAP gates
+    for i in range(n//2):
+        circ.swap(q[i], q[n - i - 1])
+
+    for i in reversed(range(n)):
         circ.h(q[i])
+        for m in reversed(range(i)):
+            circ.cu1(-2*np.pi/2**(i - m + 1), q[i], q[m])
         circ.barrier()
```

El cambio está en el programa, no en la librería.

La corrección funciona porque la nueva `qft_dagger` es la inversa real de la QFT del libro de Nielsen y Chuang: primero invierte el orden de los qubits con SWAP (la QFT del libro omite esos SWAP finales) y luego aplica, en orden inverso, cada Hadamard seguida de las rotaciones controladas con ángulo negativo `-2π/2^(i-m+1)`. Así los auxiliares quedan en el estado `|011>` correspondiente a 0.75.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.12.0` (solo `BasicAer`; no se necesita `qiskit-aer`) |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug29/requirements.txt`](../../envs/bug29/requirements.txt) |

La pregunta no indica versiones. Por su fecha (diciembre de 2019) la versión de entonces era Terra 0.11. Se probaron:

- 0.11.0 y 0.11.1: no hay wheel para Python 3.8 en Windows; la compilación desde el sdist falla, no se pudo instalar.
- 0.12.0 (febrero de 2020): buggy falla y fixed pasa.

Se eligió 0.12.0 por ser la versión instalable más cercana a la fecha de la pregunta que cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato de la pregunta.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug29/.venv
envs/bug29/.venv/Scripts/python -m pip install -r envs/bug29/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 29

# opción B: manual
cd bugs/Bugs4Q-FW-29
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug29/.venv/Scripts/python -W ignore test_b29.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug29/.venv/Scripts/python -W ignore test_f29.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug29/.venv/bin/python` en lugar de `envs/bug29/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b29.py` | falla (exit 1) | falla, exit 1 las 3 veces (`'011'` = 91, 77, 92) | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f29.py` | pasa (exit 0) | pasa, exit 0 las 3 veces (`'011'` = 809, 829, 815) | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests ejecutan 1000 shots en `BasicAer` y comprueban que `counts['011']` esté en 750 ± 250.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El Framework trae test para buggy y fixed; se usan sin modificar.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- La salida es probabilística (sin semilla). La tolerancia es amplia frente a lo observado: en las pruebas buggy dio entre 77 y 104 conteos de `011` y fixed entre 809 y 839, ambos a más de 300 conteos del límite inferior (500), por lo que un resultado inverso es prácticamente imposible.
- Es un error del algoritmo implementado por el usuario (QFT inversa mal escrita), no un mal uso de una función concreta de la API ni un defecto de Qiskit.
- El Framework ejecuta 1000 shots en lugar de los `2**17` del código original (la variable `shots` queda sin usar).
- No hay wheel de la versión de la época (Terra 0.11) para Python 3.8 en Windows; se usa 0.12.0.
- Usa `cu1` y `execute`, APIs eliminadas en Qiskit moderno.
- El mensaje del test (`91 != 750 within 250 delta`) solo indica que el resultado es incorrecto; no apunta a `qft_dagger`. En C1 el LLM dependería de reconocer por sí mismo la QFT inversa mal construida.

## 9. Pendientes

- [x] Análisis estático (LintQ, 2026-11-27): 1 warning `ql-unmeasurable-qubits` (media) en buggy y en fixed; no relacionado con el bug. Ver `static_analysis/`.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.

## 10. Test a nivel de programa (piloto)

Seleccionado para el piloto de la semana 10. Los tests de las secciones anteriores llevan el código del programa copiado dentro, por lo que no pueden validar un parche. [`test_program_29.py`](test_program_29.py) (escrito para el proyecto) ejecuta en cambio el **archivo** indicado en la variable `BUG_PROGRAM` mediante [`scripts/program_harness.py`](../../scripts/program_harness.py), que captura stdout, las variables finales del programa y las llamadas a `execute()` (inyectando `seed_simulator=1234` si el programa no fija semilla).

**Oráculo.** Registra el resultado de la llamada a `execute()` del programa, con `seed_simulator` fijo (el resultado es determinista), y comprueba que el resultado más frecuente es `'011'` con al menos el 50 % de los shots (mismo resultado esperado que el test del Framework, 750 ± 250 sobre 1000).

El test no contiene el código corregido, para no filtrar la solución en la condición C1.

```powershell
cd bugs/Bugs4Q-FW-29
$env:BUG_PROGRAM = "buggy_29.py"; ../../envs/bug29/.venv/Scripts/python -W ignore test_program_29.py   # exit 1
$env:BUG_PROGRAM = "fixed_29.py"; ../../envs/bug29/.venv/Scripts/python -W ignore test_program_29.py   # exit 0
# o bien, desde la raíz: python scripts/run_bug_tests.py 29 --program-test
```

| Programa | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|
| `buggy_29.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/program_buggy_run1.log), [run2](logs/program_buggy_run2.log), [run3](logs/program_buggy_run3.log) |
| `fixed_29.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/program_fixed_run1.log), [run2](logs/program_fixed_run2.log), [run3](logs/program_fixed_run3.log) |

Fragmento de [`logs/program_buggy_run1.log`](logs/program_buggy_run1.log):

```
AssertionError: '010' != '011'
```

Para validar un parche: guardarlo como archivo en esta carpeta y ejecutar el test con `BUG_PROGRAM=<archivo del parche>`.
