# Bugs4Q-FW-30

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-30` |
| Origen | Bugs4Q-Framework, bug 30 (`qiskit/30/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackExchange 5959](https://quantumcomputing.stackexchange.com/questions/5959/grovers-algorithm-returns-skewed-probability-distribution) ("Grover's algorithm returns skewed probability distribution", publicada el 23-abr-2019; respuesta aceptada del propio autor el 07-may-2019) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_30.py`, `fixed_30.py` (sin cambios del Framework); `test_b30.py`, `test_f30.py` (**adaptados**, ver sección 5); tests originales del Framework, sin cambios, en [`framework_tests/`](framework_tests/) |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El programa implementa dos iteraciones de Grover con un oráculo construido con Toffolis sobre 3 ancillas, y "limpia" las ancillas con `reset` en lugar de deshacer las operaciones. La distribución de salida queda sesgada respecto a la del programa corregido. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
  File "test_b30.py", line 70, in test_f30
    self.assertDictAlmostEqual(expected, freqs, delta=0.01)
AssertionError: ('0010': 0.057 != 0.0938262939453125), ('0101': 0.057 != 0.03472900390625), ('1111': 0.076 != 0.1056976318359375), ('0110': 0.057 != 0.03466033935546875), ...
```

El programa no lanza ninguna excepción; el fallo solo se detecta al comparar la distribución medida con la esperada.

El usuario debería obtener la distribución del programa corregido (unos 0.076 / 0.057 / 0.050 por estado, ver sección 7); en cambio obtiene una distribución distinta, con estados como `0111` y `1111` cerca de 0.106 y otros como `0100` cerca de 0.035.

## 3. Causa

Según la respuesta aceptada (del propio autor), el problema es usar `reset` sobre ancillas que están entrelazadas con qubits en superposición: el Toffoli entrelaza las entradas con la salida, y al resetear la ancilla parte del estado colapsa y cambia la salida del circuito. La solución es "invertir" las puertas para devolver las ancillas a `|0>` antes de reutilizarlas. Es un error de diseño del circuito del usuario (mal uso de `reset`), no un defecto de Qiskit.

## 4. Corrección (`fixed`)

Cambio entre `buggy_30.py` y `fixed_30.py` (`modify_30.txt` del Framework, sin las líneas que solo cambian la sangría de comentarios):

```diff
     circuit.ccx( search_register[3], ancillaries[0], ancillaries[1] )
-    circuit.x( search_register[2] )
     ...
     circuit.ccx( ancillaries[1], ancillaries[2], m_qubit[0] )
-    circuit.x(ancillaries)
     circuit.x(m_qubit)
 
-    # Reset ancillaries to be used later
-    circuit.reset(ancillaries)
+# Return ancillaries to 0s so they can be used later
+    circuit.x(ancillaries)
+    circuit.ccx( search_register[0], search_register[1], ancillaries[2] )
+    circuit.ccx( search_register[3], ancillaries[0], ancillaries[1] )
+    circuit.ccx( search_register[1], search_register[2], ancillaries[0] )
+    circuit.x( search_register[2] )
     ...
     circuit.x(m_qubit)
+
+# Return ancillaries to 0s for use later
+    circuit.ccx( search_register[2], ancillaries[0], ancillaries[1] )
+    circuit.ccx( search_register[0], search_register[1], ancillaries[0] )
     circuit.h(search_register)
```

El cambio está en el programa, no en la librería.

La corrección funciona (según el autor) porque las ancillas se devuelven a `|0>` aplicando en orden inverso los mismos Toffolis que las calcularon, en vez de medirlas implícitamente con `reset`; así no se colapsa la superposición de los qubits de búsqueda. El `reset` final de cada iteración se mantiene en la versión fixed.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (CPython gestionado por `uv`, Windows x86-64) |
| Qiskit | `qiskit-terra==0.12.0`, `qiskit-aer==0.4.0` |
| Dependencias fijadas a mano | `numpy==1.19.5` (Terra antiguo usa `numpy.float`, eliminado en NumPy ≥ 1.24) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug30/requirements.txt`](../../envs/bug30/requirements.txt) |

La pregunta no indica versiones. Por su fecha (abril de 2019) correspondería Qiskit 0.9/0.10 (Terra 0.8, Aer 0.2), que no tienen wheels para Python 3.8. Se probaron:

- Terra 0.11.x / Aer 0.3.4: sin wheel cp38 para Windows, no se pudo instalar.
- Terra 0.12.0 + Aer 0.4.0 (primeras con wheel cp38 para Windows) con los **tests originales del Framework**: buggy falla 20/20 ejecuciones, pero fixed solo pasa 7/20. El test original compara 1024 shots contra una única muestra fija (`'0111': 108`, …) con `delta=30`; la versión fixed da en promedio unos 78 conteos en `0111` (estimado con 10^6 shots), justo en el borde de la tolerancia, por lo que el oráculo original es inestable.
- Terra 0.12.0 + Aer 0.4.0 con los tests adaptados: buggy falla y fixed pasa (3/3).

Se eligió Terra 0.12.0 + Aer 0.4.0 por ser la combinación instalable más cercana a la fecha de la pregunta; es una decisión del investigador, no un dato de la pregunta.

**Modificación de los tests respecto al Framework** (igual en `test_b30.py` y `test_f30.py`; el circuito no se toca):

- `shots = 1024` → `shots = 2**17`.
- La aserción `assertDictAlmostEqual({...conteos fijos...}, counts, delta=30)` se sustituye por `assertDictAlmostEqual(expected, freqs, delta=0.01)`, donde `freqs` son frecuencias relativas y `expected` es la distribución de la versión fixed estimada con 10^6 shots en este entorno (redondeada a 3 decimales: 0.076–0.077 para 8 estados, 0.057 para 6 y 0.050 para 4).

Justificación: con 2^17 shots la desviación típica de cada frecuencia es ≈ 0.0007, así que 0.01 deja más de 10 desviaciones de margen para fixed; buggy se aparta entre 0.018 y 0.044 en 13 de los 16 estados. Esto elimina la inestabilidad del oráculo original sin cambiar el programa probado.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Windows PowerShell; requiere [`uv`](https://docs.astral.sh/uv/) para obtener Python 3.8):

```powershell
uv python install 3.8
uv venv --seed --python 3.8 envs/bug30/.venv
envs/bug30/.venv/Scripts/python -m pip install -r envs/bug30/requirements.txt

# opción A: script del proyecto (3 ejecuciones de cada test, regenera logs/)
python scripts/run_bug_tests.py 30

# opción B: manual
cd bugs/Bugs4Q-FW-30
$env:PYTHONIOENCODING = "utf-8"
../../envs/bug30/.venv/Scripts/python -W ignore test_b30.py; "exit=$LASTEXITCODE"   # buggy: exit=1
../../envs/bug30/.venv/Scripts/python -W ignore test_f30.py; "exit=$LASTEXITCODE"   # fixed: exit=0
```

En Linux/macOS: `envs/bug30/.venv/bin/python` en lugar de `envs/bug30/.venv/Scripts/python`.

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b30.py` | falla (exit 1) | falla, exit 1 las 3 veces (13 estados fuera de tolerancia) | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f30.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests ejecutan 2^17 shots en `Aer` y comprueban que la frecuencia de cada uno de los 16 estados esté a menos de 0.01 de la distribución de referencia de la versión fixed.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Los tests del Framework se **modificaron** (shots y oráculo, ver sección 5) porque el original falla en fixed en ~65 % de las ejecuciones.
- El oráculo es una "foto" de la salida de la versión fixed (estimada con muchos shots), no una propiedad derivada del algoritmo: certifica que buggy y fixed difieren, no que fixed sea un Grover correcto. De hecho la distribución fixed es casi uniforme (0.050–0.077), sin un pico claro en las soluciones.
- El método de `test_b30.py` se llama `test_f30` (así viene en el Framework; no afecta al resultado).
- Salida probabilística sin semilla; la tolerancia está justificada en la sección 5.
- La versión de la época (Qiskit 0.9/0.10) no es instalable con Python 3.8 en Windows; se usa Terra 0.12.0 + Aer 0.4.0.
- El mensaje del test lista los estados cuya frecuencia no coincide, pero no apunta a `reset` ni a ninguna línea del circuito. En C1 el LLM tendría que deducir por sí mismo el efecto de `reset` sobre ancillas entrelazadas, lo que es difícil.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
