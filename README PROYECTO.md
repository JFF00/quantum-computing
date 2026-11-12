# Static-Analysis-Guided LLM Repair of Quantum Programs


## 1. Objetivo y alcance

Determinar empíricamente si la evidencia del análisis estático ayuda a un LLM a reparar bugs en programas cuánticos de Qiskit. Se compararán cuatro condiciones:

| Condición | Información que recibe el LLM |
|---|---|
| **C0** | Código defectuoso exclusivamente |
| **C1** | Código + test fallido y error |
| **C2** | Código + warnings de análisis estático |
| **C3** | Código + test/error + warnings |

**Regla esencial:** la versión `fixed` del benchmark se utiliza *solo* para validación y nunca se entrega al LLM. Mantener igual el resto del prompt, modelo, parámetros y presupuesto de intentos entre condiciones para no confundir efectos.

## 2. Cómo comenzar

En Linux/macOS, desde la raíz del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/check_environment.py
python -m pytest -q
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/check_environment.py
python -m pytest -q
```

Para salir del entorno: `deactivate`. Si usa Conda, `conda env create -f environment.yml` y `conda activate quantum-repair-template` (**alternativa** al entorno `venv`, no ambos simultáneamente). Los archivos actuales solo instalan dependencias mínimas del *esqueleto*; **no instalan todavía las versiones históricas de Qiskit ni LintQ**.

**Verificación esperada:** `check_environment.py` imprime la presencia de la estructura mínima y `pytest` prueba la plantilla, **no** que Bugs4Q, LintQ o el LLM ya funcionen.

## 3. Mapa de carpetas y archivos: qué completar exactamente

Los nombres `bug_001` son marcadores internos: sustituirlos por el **identificador real y trazable de Bugs4Q**. No confundir identificador propio con identificador del benchmark.

### A. Archivos de la raíz

| Archivo | Qué es | Qué debe completar el estudiante y cómo verificarlo |
|---|---|---|
| `README.md` | Guía maestra | Mantener instrucciones de instalación actualizadas, enlazar al protocolo y describir estado real del pipeline. Añadir una sección `Estado actual`, fecha y pasos que funcionan. |
| `requirements.txt` | Dependencias del entorno base `pip` | Tras decidir versiones compatibles, escribir dependencias **con versión fijada**, sin mezclar paquetes de bugs incompatibles. Verificar instalando desde cero en un entorno nuevo. |
| `environment.yml` | Alternativa de entorno Conda | Fijar versión de Python y paquetes utilizados. Ejecutar `conda env create -f environment.yml` y guardar salida/versiones. No asumir que Conda y pip dan automáticamente el mismo entorno. |
| `.env.example` | Lista pública de nombres de variables | Definir variables necesarias (ej. nombre de clave de API) **sin escribir valores secretos**; el alumno crea `.env` local que NO se sube a Git. |
| `.gitignore` | Excepciones de Git | Añadir `.venv/`, `.env`, cachés, archivos grandes y cualquier dato con licencias que impidan redistribución; verificar con `git status`. |
| `.github/workflows/scaffold.yml` | Validación automática en GitHub Actions | Mantener el job de prueba del esqueleto; posteriormente incorporar únicamente pruebas que puedan ejecutarse sin claves privadas. Comprobar resultado en pestaña *Actions*. |

### B. `docs/` — documentación científica y seguimiento

| Archivo | Qué debe rellenar | Origen / evidencia requerida |
|---|---|---|
| `docs/literature_matrix.csv` | **Una fila por artículo**: autores, año, título, venue, DOI/URL, problema, método, dataset, métricas, resultados, limitaciones, relación con nuestro estudio. Meta semana 4: **10–15 trabajos**. | Artículos originales en ACM, IEEE, editoriales, Google Scholar y sus repositorios. No completar a partir del abstract solamente. |
| `docs/study_protocol.md` | RQ1–RQ3, hipótesis, criterios de inclusión/exclusión, selección de 25–35 bugs reproducibles (meta), definiciones de métricas, 4 condiciones, modelo, parámetros, número de intentos, unidad de análisis, validación, presupuesto, tratamiento de fallos y amenazas a validez. **Eliminar cada `PENDIENTE` justificando la decisión**. | Literatura, capacidad real de ejecución y decisiones explícitas discutidas con el supervisor. El protocolo debe cerrarse antes del experimento principal. |
| `docs/weekly_progress.md` | Por cada una de las 19 semanas: **fecha real, tarea, resultado, link a commit o archivo, bloqueo, sección del artículo actualizada**. | Evidencia rastreable en este mismo repositorio, nunca frases genéricas como «se avanzó». |
| `docs/weekly_delivery_checklist.md` | Marcar casillas solo con evidencia y agregar enlaces a logs, tablas, notebooks o commits. | Debe poder verificarlo el supervisor durante la reunión. |

**Ejemplo de fila bibliográfica** (solo estructura; no inventar resultados):

```text
Autores reales,2024,Título real,Evento o revista,DOI real,
Problema descrito,Método descrito,Dataset usado,Métricas del paper,
Resultado reportado,Limitación identificada,Relación con nuestro estudio
```

### C. `notebooks/` — formación y pruebas básicas

| Archivo | Qué debe incluir | Comprobación |
|---|---|---|
| `notebooks/qiskit_basics.ipynb` | Cinco circuitos ejecutables y explicados: por ejemplo estado de Bell, GHZ, X/H/CX, medición y teleportación básica. Para cada circuito: código, objetivo, salida real, interpretación y versión de librerías. | Ejecutar todas las celdas desde kernel limpio; explicar qué resultados son probabilísticos. Meta semana 2. |
| `notebooks/quantum_testing.ipynb` | Pruebas simples (idealmente pytest o aserciones) que muestren un caso correcto y un caso defectuoso; diferenciar test passing y corrección funcional. | Reejecutar y mostrar resultado, no almacenar únicamente imágenes. |

Ambos notebooks son **plantillas sin ejercicios terminados**. El alumno debe agregar código y resultados reales.

### D. `data/` — inventario, selección y trazabilidad

| Archivo | Qué debe completar | Cómo hacerlo |
|---|---|---|
| `data/bugs_inventory.xlsx` | **Una fila por candidato Bugs4Q**; ID original, URL/commit, referencias buggy/fixed, categoría, versiones Python/Qiskit, comando de test, resultados buggy/fixed, reproducibilidad, warnings y observaciones (según los encabezados del Excel). | Consultar repositorio original; ejecutar cada caso en entorno aislado. Marcar `PENDIENTE` si falta comprobar. **No copiar una cantidad de warnings sin ejecutar el analizador**. |
| `data/bugs.csv` | Exportación en texto con `bug_id,source_url,repository_commit,buggy_ref,fixed_ref,category,reproducible,status,notes`. | Llenar con el mismo ID y trazabilidad del Excel. La cabecera no constituye un dataset. |
| `data/selected_bugs.csv` | **Solo bugs aceptados** en el estudio: ID, por qué se seleccionaron, archivo de entorno, ruta de log de test y de análisis estático, estado. | Incluir únicamente los casos que satisfacen las reglas del protocolo; mantener también registro de exclusiones en Excel. |

**Cómo usar Excel:** abrir `data/bugs_inventory.xlsx` en Excel/LibreOffice, completar *una fila por bug*, guardar y, cuando sea necesario, actualizar los CSV con los mismos IDs. Los datos bibliográficos, el bug, los comandos, las versiones y los warnings se obtienen de fuentes **distintas**: el repositorio Bugs4Q aporta identificadores e información histórica disponible; los resultados de tests/warnings proceden de ejecuciones propias. No asumir que el repositorio de Bugs4Q trae un Excel con todas las métricas de este estudio.

### E. `bugs/` — una ficha verificable por bug

| Archivo | Qué debe rellenar | Comprobación |
|---|---|---|
| `bugs/bug_001/metadata.json` | Sustituir campos `PENDIENTE`: `bug_id`, `source_url`, `source_commit`, `buggy_ref`, `fixed_ref`, `python_version`, `qiskit_version`, `test_command`, `environment_notes`, `license_review`. | Todos deben corresponder al **mismo** bug. Validar JSON con `python -m json.tool bugs/bug_001/metadata.json`. |
| `bugs/bug_001/README.md` | Explicar bug en palabras propias: síntoma, causa conocida cuando esté documentada, fuente, instrucciones de instalación, comando real, resultado esperado y observado, por qué fue incluido. | Una persona externa debe entender cómo reproducirlo sin consultar al estudiante. |

Crear `bugs/<id_real>/` para nuevos casos, copiando solo la estructura y **sin inventar IDs**. Los códigos fuente originales se pueden mantener referenciados por URL/commit cuando su licencia o volumen aconseje no incorporarlos.

### F. `scripts/` — automatización del experimento

| Archivo | Responsabilidad y trabajo pendiente | Resultado verificable esperado |
|---|---|---|
| `scripts/check_environment.py` | **Ya implementado:** comprueba la presencia de algunos archivos del esqueleto. Ampliar más adelante con validaciones reales, sin confundir la estructura con reproducibilidad. | `python scripts/check_environment.py` debe terminar sin error; la salida no prueba el pipeline. |
| `scripts/reproduce_bug.py` | **Esqueleto:** leer `metadata.json`, preparar entorno por caso, obtener la versión `buggy`, ejecutar el test documentado y guardar código de salida, stdout y stderr; repetir con `fixed` por separado. | Dos registros identificables (buggy/fixed), comandos y versiones del entorno. El esqueleto actual **no ejecuta bugs**. |
| `scripts/run_tests.py` | **Esqueleto:** invocar comando auténtico de pruebas, fijar timeout, guardar logs y exit code, indicar qué tests fallan y si hay errores de instalación. | Archivo de test por bug y entorno; no mezclar «test fallido» con «no se pudo iniciar». |
| `scripts/run_static_analysis.py` | **Esqueleto:** integrar versión compatible de LintQ/CodeQL u otra herramienta aprobada, exportar SARIF/JSON, registrar regla, severidad, archivo, línea y warnings. | Reporte original + tabla estructurada por bug. No generar warnings ficticios. |
| `scripts/generate_prompts.py` | **Generador simple funcional:** construir texto desde `--condition`, `--buggy-file`, `--test-evidence` y `--static-evidence`. Después adaptar para usar exactamente el contenido y las reglas de las plantillas `prompts/C*.txt`; añadir validación de entradas. | Cuatro prompts guardados con archivos de evidencia reales y sin `fixed`. **Actualmente no invoca un LLM.** |
| `scripts/generate_patch.py` | **Esqueleto:** conectar SDK/API del LLM, fijar modelo y parámetros, guardar respuesta bruta y parche, manejar errores y contabilizar costo/tiempo. | Un patch y metadatos por `bug_id` + configuración + intento. **Actualmente no llama al modelo.** |
| `scripts/validate_patch.py` | **Esqueleto:** aplicar parche en copia aislada, comprobar sintaxis/importaciones, ejecutar tests, repetir análisis estático, revisar contra la solución de referencia y registrar decisión de validación. | Un informe por intento, separando parche plausible de validado. **Actualmente no valida.** |

**Prueba del generador de prompts** con un *archivo de prueba local* que NO es un bug real:

```bash
printf 'print("ejemplo")\n' > /tmp/demo_buggy.py
python scripts/generate_prompts.py \
  --condition C0 \
  --buggy-file /tmp/demo_buggy.py \
  --output /tmp/demo_C0.txt
cat /tmp/demo_C0.txt
```

Para C1 se necesita `--test-evidence`, para C2 `--static-evidence` y para C3 **ambos**. Un prompt creado con datos de demostración no equivale a un experimento sobre Bugs4Q.

### G. `prompts/` — cuatro condiciones comparables

| Archivo | Qué debe rellenar | Qué información está prohibida |
|---|---|---|
| `prompts/C0_baseline.txt` | Instrucciones comunes + marcador de **código buggy**. | Tests, errores, warnings, versión `fixed`. |
| `prompts/C1_test_guided.txt` | Misma instrucción + **código buggy + salida del test fallido/error**. | Warnings estáticos y `fixed`. |
| `prompts/C2_static_guided.txt` | Misma instrucción + **código buggy + warnings estáticos**. | Salida de tests/errores y `fixed`. |
| `prompts/C3_hybrid.txt` | Misma instrucción + **código buggy + tests/errores + warnings**. | `fixed`. |

Los marcadores `{BUGGY_CODE}`, etc. deben ser sustituidos por información real de ejecución. Antes de usar un LLM, guardar el **prompt final enviado**, no solo la plantilla. Establecer en el protocolo cómo se manejan warnings vacíos, entradas muy largas y casos sin tests fallidos.

### H. `results/` — evidencia del experimento (no hay resultados cargados)

| Archivo | Qué debe rellenar | Cómo se verifica |
|---|---|---|
| `results/README.md` | Convenciones de IDs, rutas, denominadores, significado de `validated` y cómo se generan las salidas. | Otro investigador debe poder encontrar cualquier intento. |
| `results/bug_001/README.md` | Índice de pruebas del bug, ejecución de analizador, prompts, parches y validación; agregar enlaces relativos a archivos auténticos creados después. | No describir ejecuciones que aún no se hicieron. |
| `results/results.csv` | **Una fila por intento** (identificador, configuración, modelo/parámetros, rutas de prompt/patch/log, compilación, tests, validación, warnings antes/después, warnings introducidos, tamaño y duración). | Cada fila debe señalar archivos de evidencia existentes; la cabecera actual está vacía. |

Cuando se ejecute un caso, conservar en subcarpetas los *logs crudos* y el parche generado. No reemplazar fallos ni resultados negativos por resúmenes manuales. El piloto corresponde a semana 10; el conjunto de datos completo, a semana 13.

### I. `analysis/` — métricas y figuras (etapa posterior)

| Archivo | Qué completar | Momento |
|---|---|---|
| `analysis/README.md` | Explicar cálculo de tasas por intento y por bug, comparaciones C2 vs. C0 y C3 vs. C1, manejo de intervalos de incertidumbre y casos sin warnings. | Diseñar desde el protocolo; producir tablas/gráficos definitivos semanas 14–15. |

Guardar allí luego scripts de cálculo, tablas y figuras a partir de `results/results.csv`, sin editar manualmente el CSV de origen para producir gráficos favorables.

### J. `paper/` — artículo científico en LaTeX

| Archivo | Qué debe escribir | Cuándo |
|---|---|---|
| `paper/main.tex` | Archivo principal; mantener `\input` a secciones, título/autoría provisional y estilo acordado. | Desde semana 3. |
| `paper/references.bib` | Entradas BibTeX verificadas para 10–15 trabajos y las herramientas/benchmark que efectivamente se usen; verificar autores, DOI y año. | Semanas 3–4; actualizar todo el proyecto. |
| `paper/sections/introduction.tex` | Problema, motivación, brecha, RQ y contribuciones esperadas (no inventar hallazgos). | Semanas 3–6. |
| `paper/sections/background.tex` | Qiskit, bugs, testing, análisis estático, APR, patch plausible/validado. | Semanas 1–4. |
| `paper/sections/related_work.tex` | Comparación **crítica** de estudios, métodos/datasets y diferencia frente al proyecto. | Semanas 3–5. |
| `paper/sections/study_design.tex` | RQ1–RQ3, hipótesis, C0–C3, dataset, criterios, métricas, repeticiones, oráculos y procedimientos. | Semanas 5–6, ajustar explícitamente con piloto. |
| `paper/sections/experimental_setup.tex` | Versiones, entornos, herramienta estática, LLM, prompts, tests, ejecución y diagrama del pipeline. | Semanas 7–10. |
| `paper/sections/results.tex` | Tablas y gráficos **derivados de datos reales**, respuesta por RQ. | Semanas 11–15. |
| `paper/sections/discussion.tex` | Interpretación de beneficios/daños de los warnings, casos positivos y negativos, implicaciones. | Semanas 14–17. |
| `paper/sections/threats.tex` | Sesgos del dataset, compatibilidad histórica, tests incompletos, falsos positivos, aleatoriedad y contaminación. | Empezar semana 5 y actualizar. |
| `paper/sections/conclusion.tex` | Hallazgos sustentados por evidencia, limitaciones y futuro trabajo. | Semanas 16–17. |
| `paper/figures/` | Diagramas y gráficos finales con nombre y fuente reproducible. | Desde semana 9 (pipeline) y semanas 14–15 (resultados). |

**Regla de escritura:** cada semana debe aportar al menos una modificación sustantiva del paper y registrarla en `docs/weekly_progress.md`. Las secciones vacías son tareas pendientes, no entregables científicos terminados.

### K. `tests/` — pruebas del propio software de investigación

| Archivo | Qué hacer | Verificación |
|---|---|---|
| `tests/test_scaffold.py` | Mantener y ampliar pruebas de estructura, lectura del inventario, validación de metadatos, construcción de C0–C3 y parsing de métricas. | `python -m pytest -q`. Probar también entradas erróneas. |

## 4. Enlaces y obtención de datos

- [Bugs4Q Framework](https://github.com/Z-928/Bugs4Q-Framework): consultar su README y comandos disponibles **según el commit usado**.
- [Catálogo de Bugs4Q](https://github.com/z-928/bugs4q): revisar metadatos y referencias buggy/fixed; registrar URL y commit exactos.
- [LintQ](https://github.com/sola-st/LintQ): revisar requisitos CodeQL/Docker, reglas y formato SARIF según versión elegida.
- [Qiskit (IBM)](https://quantum.cloud.ibm.com/docs/): estudiar APIs y migraciones de versión.
- Literatura: ACM Digital Library, IEEE Xplore, Google Scholar y páginas oficiales de artículos.

**El repositorio externo no garantiza** contener `test_command`, versiones compatibles ni warnings del estudio: deben verificarse, reproducirse y documentarse en este repositorio.

## 5. Orden recomendado hasta la semana 8 (estimada al 9 de octubre de 2026)

- [ ] **Semanas 1–2:** entorno inicial y notebook con cinco circuitos que se ejecutan.
- [ ] **Semanas 3–4:** 10–15 trabajos en `docs/literature_matrix.csv` y borradores `background`, `related_work`.
- [ ] **Semanas 5–6:** protocolo de investigación y criterios de selección documentados.
- [ ] **Semana 7:** seleccionar **un bug real**, registrar su metadato y reproducir buggy/fixed o documentar bloqueos con logs; primer reporte estático.
- [ ] **Semana 8:** disponer de las cuatro plantillas C0–C3, generación de prompts, primer intento de integración y evidencia correspondiente.
- [ ] **Semana 9 (próxima):** automatizar el pipeline completo para un bug.
- [ ] **Semana 10:** piloto de cinco bugs en cuatro condiciones.

Si el inicio real del proyecto fue diferente, actualizar el calendario. No marcar tareas completas por la sola presencia de carpetas.

## 6. Qué enviar al supervisor cada viernes

1. URL del repositorio y **commit** de entrega (por ejemplo, `git rev-parse HEAD`).
2. `docs/weekly_progress.md` completado con enlaces a evidencia.
3. Excel/CSV actualizado, sin filas ficticias.
4. Comandos exactos que ejecutó, versión del entorno y logs (test/analizador), incluso si fallaron.
5. Diferencias concretas en `paper/` respecto de la semana anterior.
6. Pendientes y solución que propone para los bloqueos.

Ejemplo de comandos útiles:

```bash
git status
git add README.md docs data bugs scripts prompts paper notebooks tests
# Revisar archivos antes de confirmar
git diff --cached --stat
git commit -m "Semana 08: documentar bug y preparar prompts"
git rev-parse HEAD
```

**Nunca** incluir en commits claves de API, tokens ni `.env`. Revisar siempre `git diff --cached` antes de subir.

## 7. Definición de «listo» para un archivo o actividad

Una actividad solo se considera terminada cuando (1) tiene contenido real, (2) proviene de una fuente o ejecución identificable, (3) puede verificarse mediante comando, enlace o log y (4) queda vinculada a un commit y al avance del artículo cuando corresponda.

Los scripts de Bugs4Q, análisis estático, reparación y validación son **esqueletos declarados**: requieren implementación y pruebas antes de utilizarlos en una investigación publicada.