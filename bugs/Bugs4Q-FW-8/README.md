# Bugs4Q-FW-8

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-8` |
| Origen | Bugs4Q-Framework, bug 8 (`qiskit/8/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#5580](https://github.com/Qiskit/qiskit-terra/issues/5580) ("qiskit.quantum_info.operators.Operator will give wrong result in the following condition", abierto el 30-dic-2020, cerrado el 26-ene-2021) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_8.py`, `fixed_8.py`, `test_b8.py`, `test_f8.py` (los cuatro copiados sin cambios del Framework) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa construye un `Operator` a partir de un circuito de 3 qubits con dos `crz`, lo añade a un circuito de 4 qubits sobre `[qae[0], b[0], b[1]]` y calcula la matriz unitaria total. La matriz obtenida no es la de "dos `crz` controladas por `qae[0]`" que el usuario esperaba: las fases aparecen en otras posiciones de la diagonal. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: '[[1.[152 chars]0.j  1. +0.j  0. +0.j  0. +0.j  0. +0.j  0. +0[2193 chars]9j]]' != '[[1.[152 chars]0.j  0.4-0.9j 0. +0.j  0. +0.j  0. +0.j  0. +0[2194 chars]9j]]'
Diff is 4265 characters long. Set self.maxDiff to None to see it.
```

No se lanza ninguna excepción; el fallo solo se detecta al comparar la matriz redondeada con la esperada.

El usuario debería haber recibido la misma unitaria que obtiene aplicando directamente `crz(pi/2, qae[0], b[0])` y `crz(pi/4, qae[0], b[1])`, pero recibe una matriz en la que el control efectivo es otro qubit.

## 3. Causa

El autor del issue atribuye el problema a `Operator` cuando la unitaria no actúa sobre todos los qubits del circuito. Sin embargo, el diff muestra que el error está en el programa: en el circuito auxiliar las `crz` usan el qubit 2 como control (`crz(pi/2, 2, 0)`), y al añadir `U` sobre `[qae[0], b[0], b[1]]` el qubit 2 se corresponde con `b[1]`, no con `qae[0]`. Es un mal uso de los índices de qubit (control y objetivo intercambiados), no un defecto de Qiskit. Solo se consultó el cuerpo del issue, no los comentarios del cierre.

## 4. Corrección (`fixed`)

Cambio entre `buggy_8.py` y `fixed_8.py` (`modify_8.txt` del Framework):

```diff
-circ.crz(pi/2,2,0)
-circ.crz(pi/4,2,1)
+circ.crz(pi/2,0,1)
+circ.crz(pi/4,0,2)
```

El cambio está en el programa, no en la librería.

Con el control en el qubit 0 del circuito auxiliar, que al hacer `append` se asigna a `qae[0]`, y los objetivos en los qubits 1 y 2 (asignados a `b[0]` y `b[1]`), la unitaria resultante coincide con la del circuito construido directamente con `crz` sobre los registros, que es la que el usuario esperaba.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.18.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (compatibilidad con Terra antiguo); `matplotlib==3.3.4` y `pylatexenc==2.10`, necesarios porque el test llama a `qc.draw('mpl')` |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug8/requirements.txt`](../../envs/bug8/requirements.txt) |

El issue indica Terra 0.16.1 (qiskit 0.23.2) y Python 3.7.4 (no disponible en este equipo; se usa 3.8). Se probaron, en el mismo entorno, Terra 0.15.0, 0.16.1, 0.16.4, 0.17.0, 0.17.4, 0.18.0 y 0.18.3:

- Sin `matplotlib`/`pylatexenc`, ambos tests terminan con `ImportError` en `qc.draw('mpl')` (no se pudo iniciar la comprobación).
- 0.15.0 – 0.17.4: la matriz de fixed coincide con la esperada, pero ambos tests fallan en la segunda aserción porque el dibujante de texto escribe `unitary` (minúscula) y el test espera `Unitary`.
- 0.18.0 y 0.18.3: buggy falla (matriz distinta) y fixed pasa.

Se eligió 0.18.0, la versión más cercana a la fecha del issue (dic-2020) que cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug8/.venv
envs/bug8/.venv/Scripts/python -m pip install -r envs/bug8/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 8

# opción B: manual
cd bugs/Bugs4Q-FW-8
$env:PYTHONIOENCODING = "utf-8"   # los tests imprimen caracteres de caja (┤ ├)
$env:MPLBACKEND = "Agg"           # qc.draw('mpl') sin ventana
../../envs/bug8/.venv/Scripts/python -W ignore test_b8.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug8/.venv/Scripts/python -W ignore test_f8.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug8/.venv/bin/python` en lugar de `envs/bug8/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b8.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f8.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban la misma matriz esperada (`np.round(uni.data, 1)` como texto, la de las dos `crz` controladas por `qae[0]`) y el mismo dibujo de texto del circuito con la caja `Unitary`; buggy falla en la primera aserción. El test es determinista (no hay simulación).

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio (dos líneas) está en el programa del usuario, no en Qiskit.
- El Framework trae test para buggy y fixed; se usan sin modificar.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un mal uso de los índices de qubit, no un defecto de `Operator`, aunque el issue lo presente así.
- El oráculo compara el texto de una matriz redondeada y un dibujo de texto, ambos sensibles a la versión (formato de `numpy`, `unitary`/`Unitary`); fuera de 0.18.x el test de fixed falla por el dibujo.
- La versión elegida (0.18.0, jul-2021) es posterior a la del issue (0.16.1) solo por el dibujo esperado; con 0.16.1 la matriz ya se reproduce igual.
- El mensaje de error del test es una comparación truncada de matrices de 16×16 (`[2193 chars]`), sin indicar qué línea del programa la produce; para C1 da poca información sobre la causa (las `crz` con control en el qubit 2).

## 9. Pendientes

- [x] Análisis estático (LintQ, 2026-11-27): 2 warnings `ql-unmeasurable-qubits` (media) en buggy y en fixed; no relacionados con el bug. Ver `static_analysis/`.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.

## 10. Test a nivel de programa (piloto)

Seleccionado para el piloto de la semana 10. Los tests de las secciones anteriores llevan el código del programa copiado dentro, por lo que no pueden validar un parche. [`test_program_8.py`](test_program_8.py) (escrito para el proyecto) ejecuta en cambio el **archivo** indicado en la variable `BUG_PROGRAM` mediante [`scripts/program_harness.py`](../../scripts/program_harness.py), que captura stdout, las variables finales del programa y las llamadas a `execute()` (inyectando `seed_simulator=1234` si el programa no fija semilla).

**Oráculo.** Lee la variable `uni` (Operator) del programa. Comprueba que es diagonal y que sus 16 fases coinciden (a 3 decimales) con las del test del Framework. No depende del dibujo `Unitary` (a diferencia de `test_b8.py`). El mensaje de fallo indica las posiciones de la diagonal incorrectas, no la causa.

El test no contiene el código corregido, para no filtrar la solución en la condición C1.

```powershell
cd bugs/Bugs4Q-FW-8
$env:BUG_PROGRAM = "buggy_8.py"; ../../envs/bug8/.venv/Scripts/python -W ignore test_program_8.py   # exit 1
$env:BUG_PROGRAM = "fixed_8.py"; ../../envs/bug8/.venv/Scripts/python -W ignore test_program_8.py   # exit 0
# o bien, desde la raíz: python scripts/run_bug_tests.py 8 --program-test
```

| Programa | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|
| `buggy_8.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/program_buggy_run1.log), [run2](logs/program_buggy_run2.log), [run3](logs/program_buggy_run3.log) |
| `fixed_8.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/program_fixed_run1.log), [run2](logs/program_fixed_run2.log), [run3](logs/program_fixed_run3.log) |

Fragmento de [`logs/program_buggy_run1.log`](logs/program_buggy_run1.log):

```
AssertionError: Lists differ: [1, 3, 5, 7, 8, 9, 10, 11, 12, 14] != []
```

Para validar un parche: guardarlo como archivo en esta carpeta y ejecutar el test con `BUG_PROGRAM=<archivo del parche>`.
