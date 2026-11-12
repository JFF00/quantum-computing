# Bugs4Q-FW-5



## 1. Identificación

| Campo | Valor |
|---|---|
| ID | `Bugs4Q-FW-5` |
| Origen | Bugs4Q-Framework, bug 5 (`qiskit/5/`), commit `e596a251ec723e58a042557277d584d56ffa1781` |
| Issue | [qiskit-terra#1446](https://github.com/Qiskit/qiskit-terra/issues/1446) |
| Categoría (Framework) | Output Wrong |
| Archivos | `buggy_5.py`, `fixed_5.py`, `test_b5.py`, `test_f5.py` |
| Metadatos | [`metadata.json`](metadata.json) |

## 2. Síntoma
python -m json.tool metadata.json
`qc.qasm()` devuelve solo la cabecera del circuito, sin registros ni medición. Fragmento de [`logs/buggy_test_run1.log`](logs/buggy_test_run1.log):

```
AssertionError: 'OPEN[19 chars]"qelib1.inc";\n' != 'OPEN[19 chars]"qelib1.inc";\nqreg q[1];\ncreg c[1];\nmeasure q[0] -> c[0];\n'
  OPENQASM 2.0;
  include "qelib1.inc";
+ qreg q[1];
+ creg c[1];
+ measure q[0] -> c[0];
```

El usuario espera de output el texto literal que se escribe en el codigo, sin embargo recibe un circuito vacío y las primeras líneas del texto, es decir un error que no se avisa, no lanza exception, solo se detecta comparando la salida real con la esperada.

## 3. Causa
Desde el issue, se explica que esto ocurre ya que la función from_qasm_str() es un constructor estático,opera sobre la clase para devolver un circuito basado en qasm, en el codigo buggy el usuario crea un circuito vacio y otro basado en qasm pero no se hace nada con él y por lo tanto se borra, finalmente se usa el circuito vacío inicial y por eso no se ve el circuito en el output.

## 4. Corrección (`fixed`)

Cambio entre `buggy_5.py` y `fixed_5.py`:

```diff
-qc = QuantumCircuit()
-qc.from_qasm_str(qasm)
+qc = QuantumCircuit.from_qasm_str(qasm)
```

(También se elimina un comentario con `Aer.get_backend`.) El cambio está en el programa, no en la librería.


La correción se define como el patrón habitual para usar la función, ya que así se crea un único circuito, en el patrón inicial se creaba uno pero la función creaba otro independiente del circuito de entrada.

## 5. Entorno

| Elemento | Valor |
|---|---|
| Python | 3.7.16 (conda, plataforma `osx-64`) |
| Qiskit | `qiskit-terra==0.7.0` |
| Dependencia fijada | `networkx==2.3` |
| Dependencias completas | [`logs/environment.txt`](logs/environment.txt), [`../../envs/bug5/requirements.txt`](../../envs/bug5/requirements.txt) |

Diferencias con el issue (reporta Terra 0.7.0 y Python 3.7.0):
- Python es 3.7.16 en lugar de 3.7.0.
- `networkx` debe fijarse a 2.3; con versiones posteriores ambos tests fallan por un error ajeno al bug (`'MultiDiGraph' object has no attribute 'node'`).
- No aparece el `SchemaValidationError` que se ve en el issue, pero sí el circuito vacío.

## 6. Cómo reproducirlo

Desde la raíz del proyecto (Mac con Apple Silicon; Python 3.7 solo existe para Intel):

```bash
source ~/miniconda3/etc/profile.d/conda.sh
ENV="$PWD/envs/bug5/.conda"
CONDA_SUBDIR=osx-64 conda create -y -p "$ENV" python=3.7
conda activate "$ENV"
conda config --env --set subdir osx-64
python -m pip install "qiskit-terra==0.7.0" "networkx==2.3"

cd bugs/Bugs4Q-FW-5
python -W ignore test_b5.py; echo "exit=$?"    # buggy: debe fallar (exit=1)
python -W ignore test_f5.py; echo "exit=$?"    # fixed: debe pasar (exit=0)
```



## 7. Resultado esperado y observado

| Versión | Test | Esperado | Observado (3 ejecuciones) | Logs |
|---|---|---|---|---|
| buggy | `test_b5.py` | falla (exit 1) | falla, exit 1 las 3 veces | [run1](logs/buggy_test_run1.log), [run2](logs/buggy_test_run2.log), [run3](logs/buggy_test_run3.log) |
| fixed | `test_f5.py` | pasa (exit 0) | pasa, exit 0 las 3 veces | [run1](logs/fixed_test_run1.log), [run2](logs/fixed_test_run2.log), [run3](logs/fixed_test_run3.log) |

Los dos tests comprueban la misma salida esperada de `qc.qasm()`; solo cambia cómo se construye el circuito.

## 8. Por qué se incluye

- Existe versión `fixed` y el cambio está en el programa del usuario, no en Qiskit.
- El test falla en buggy y pasa en fixed, de forma estable (3/3).
- Se ejecuta en un entorno fijado y documentado.

Limitaciones:
- Es un bug de uso incorrecto de la API.
- Al ser bug simple, el test fallido probablemente le de la respuesta de manera inmediata al modelo, de ser así, C2 Y C3 no tendrán mucho margen de evaluación por sobre C1.

## 9. Pendientes

- [ ] Análisis estático (LintQ) sin ejecutar: `static_warnings` en blanco en el inventario.
- [ ] Revisión de licencia (`license_review` = `PENDIENTE` en `metadata.json`).
- [ ] Decidir `selected` en `data/bugs_inventory.xlsx` y, si procede, añadir a `data/selected_bugs.csv`.
