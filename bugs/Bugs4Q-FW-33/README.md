# Bugs4Q-FW-33

## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-33` |
| Origen | Bugs4Q-Framework, bug 33 (`qiskit/33/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [StackExchange 4260](https://quantumcomputing.stackexchange.com/questions/4260/how-to-create-a-condition-on-only-one-classical-bit-when-we-have-a-total-of-2-cl) |
| Categoría (Framework) | Throw Exceptions |
| Archivos | `buggy_33.py`, `fixed_33.py`, `test_b33.py`, `test_f33.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma

El usuario intenta condicionar una puerta a un solo bit de un registro clásico de 2 bits (`c_if` sobre `c[0]`). El código original ni siquiera es sintácticamente válido (`qc.x(q[0]).c[0]_if(...)`). En el test se usa la forma válida `c_if(c[0], 0)` y el fallo aparece al dibujar el circuito. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
KeyError: Clbit(ClassicalRegister(2, 'c0'), 0)
```

## 3. Causa

`c_if` solo admite un `ClassicalRegister` completo como condición, no un bit suelto de un registro mayor. Para condicionar a un solo bit hay que usar registros de 1 bit independientes.

## 4. Corrección (`fixed`)

Cambio entre `buggy_33.py` y `fixed_33.py`:

```diff
-c = ClassicalRegister(2)
-qc = QuantumCircuit(q,c)
+c = [ ClassicalRegister(1) for _ in range(2) ]
+qc = QuantumCircuit(q)
+for register in c:
+    qc.add_register( register )
+    qc.h(q)
-qc.x(q[0]).c[0]_if(c[0], 0)
+qc.x(q[0]).c_if(c[0], 0)
```

(También se agrega `from qiskit.visualization import circuit_drawer`.) El cambio está en el programa, no en la librería.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.8.20 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.18.3` |
| Dependencias fijadas a mano | ninguna (todas las dependencias se resolvieron con `pip`) |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug33/requirements.txt`](../../envs/bug33/requirements.txt) |

El Framework no indica versiones. Se eligió Terra 0.18.3 porque en ella se cumple el criterio buggy-falla / fixed-pasa. Es una decisión del investigador, no un dato del benchmark.

La línea original `.c[0]_if(...)` es un `SyntaxError`, por lo que no se puede ejecutar tal cual; `test_b33.py` usa la forma sintácticamente válida `c_if(c[0], 0)` con un registro de 2 bits, que es la intención del usuario.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.8 con Terra 0.18 se instala vía plataforma Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug33/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.8
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install -r envs/bug33/requirements.txt

cd bugs/Bugs4Q-FW-33
python -W ignore test_b33.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f33.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```

## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b33.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f33.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests construyen el circuito, lo dibujan (`print(qc)`) y comprueban que la `x` tiene condición `== 0`. En buggy el dibujo lanza `KeyError`.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- El fallo depende de la versión: en Terra 0.18.3 `c_if` acepta el `Clbit` pero el dibujo falla, no la construcción.
- El código buggy original es un `SyntaxError`, y el test lo corrige parcialmente para poder ejecutarlo.
- El test fue escrito para este proyecto (el Framework no trae test para este bug).

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
