# Bugs4Q-FW-10

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-10` |
| Origen | Bugs4Q-Framework, bug 10 (`qiskit/10/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#4144](https://github.com/Qiskit/qiskit-terra/issues/4144) ("U1 gets decomposed into U3", abierto y cerrado el 13-abr-2020) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_10.py`, `fixed_10.py`, `test_b10.py`, `test_f10.py` (los cuatro copiados sin cambios del Framework) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa crea un circuito de un qubit con una puerta `u1(0.24)` e imprime `qc.decompose()`. En lugar de la puerta `U1(0.24)`, el circuito descompuesto muestra `U3(0,0,0.24)`. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: '     ┌──────────────┐\nq_0: ┤ U3(0,0,0.24) ├\n     └──────────────┘' != '     ┌──────────┐\nq_0: ┤ U1(0.24) ├\n     └──────────┘'
```

No se lanza ninguna excepción; el fallo solo se detecta al comparar el dibujo del circuito con el esperado.

El usuario esperaba seguir viendo una `U1(0.24)` (puerta "gratuita" en el hardware, según el issue) y recibió una `U3(0,0,0.24)`, equivalente pero más costosa.

## 3. Causa

Según el autor del issue, `decompose()` sustituye la `U1` por su definición, que en Terra de esa época está escrita en términos de `U3` (enlaza la línea de `qiskit/extensions/standard/u1.py` donde se hace ese mapeo). `decompose()` hace exactamente eso, reemplazar cada puerta por su definición, así que no es un fallo de cálculo: el circuito es equivalente. El issue se cerró a los ~15 minutos; solo se consultó el cuerpo del issue (no los comentarios), por lo que no se documenta aquí el motivo exacto del cierre. A la vista del `fixed`, se trata como un uso inadecuado de `decompose()` y no como un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_10.py` y `fixed_10.py` (`modify_10.txt` del Framework):

```diff
-print(qc.decompose())
+transpile(qc, basis_gates=['u1', 'u2', 'u3', 'cx'])
+print(qc)
```

El cambio está en el programa, no en la librería.

La corrección deja de llamar a `decompose()` e imprime el circuito original, en el que la puerta sigue siendo `U1`. La llamada a `transpile` con `u1` en la base no modifica `qc` (su resultado se descarta), así que lo que realmente arregla la salida es no descomponer el circuito.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.13.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug10/requirements.txt`](../../envs/bug10/requirements.txt) |

El issue indica Terra "latest" (abril de 2020, es decir, 0.13.0) y no indica versión de Python. Se probaron, en el mismo entorno, Terra 0.12.0, 0.13.0, 0.14.2, 0.15.0 y 0.16.4:

- 0.12.0: ambos tests fallan porque el dibujante de texto añade el estado inicial (`q_0: |0>┤ ...`) y los tests no lo esperan.
- 0.13.0 – 0.16.4: buggy falla (`U3(0,0,0.24)`) y fixed pasa.

Se eligió 0.13.0 por la fecha del issue (13-abr-2020, versión publicada en ese momento) y porque con ella se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del issue.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug10/.venv
envs/bug10/.venv/Scripts/python -m pip install -r envs/bug10/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 10

# opción B: manual
cd bugs/Bugs4Q-FW-10
$env:PYTHONIOENCODING = "utf-8"   # los tests imprimen caracteres de caja (┤ ├)
../../envs/bug10/.venv/Scripts/python -W ignore test_b10.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug10/.venv/Scripts/python -W ignore test_f10.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug10/.venv/bin/python` en lugar de `envs/bug10/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b10.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f10.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban el mismo dibujo de texto esperado, una sola caja `U1(0.24)` sobre `q_0`; el test es determinista (no hay simulación).

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El Framework trae test para buggy y fixed; se usan sin modificar.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- No es un defecto de Qiskit sino un uso de `decompose()` con una expectativa equivocada; el circuito descompuesto es equivalente.
- El `fixed` es débil: `transpile` no tiene efecto sobre `qc`, de modo que el test de fixed solo comprueba que dibujar el circuito original muestra `U1`.
- El oráculo compara dibujos de texto, que cambian entre versiones (ver 0.12.0), y la definición de `U1` también puede cambiar; el test es frágil fuera del rango probado (0.13.0 – 0.16.4).
- El mensaje de error del test muestra el diff `U3(0,0,0.24)` frente a `U1(0.24)` y apunta a la línea del `assertEqual` con `qc.decompose()`, lo que sugiere que la causa es la descomposición; para C1 es una pista bastante directa.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
