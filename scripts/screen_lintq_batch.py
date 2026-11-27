"""Cribado rápido con LintQ: analiza TODOS los bugs en dos bases de datos CodeQL (una con
todos los buggy_N.py y otra con todos los fixed_N.py / fixed_N_min.py) en vez de una por archivo.

Uso (desde la raíz del proyecto, Docker en marcha):

    py scripts/screen_lintq_batch.py              # todos los bugs/Bugs4Q-FW-*
    py scripts/screen_lintq_batch.py 3 12 26      # solo esos

Por qué: con una base por archivo, cada variante tarda ~8 min porque el extractor de CodeQL
procesa también la librería qiskit importada. En lote, esa extracción se hace una sola vez.
Los programas no se importan entre sí y LintQ razona por circuito dentro de cada archivo, así
que los warnings se separan por archivo sin mezclarse. Los bugs del piloto (7, 8, 14, 21, 29)
sirven de control: el lote debe reproducir sus resultados del análisis individual.

Es un CRIBADO para elegir candidatos; no reemplaza el análisis individual de
run_static_analysis.py, que es el que se usa como evidencia por bug.

Salidas:
  data/lintq_screening/{buggy,fixed}.sarif   reportes originales
  data/lintq_screening/{buggy,fixed}.log     comandos, versiones, exit codes
  data/lintq_screening/warnings.csv          un warning por fila (bug, variante, regla, línea...)
  data/lintq_screening/summary.csv           por bug: conteos y warnings solo en buggy
"""
import argparse
import csv
import datetime
import glob
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_static_analysis import (CONTAINER_DATA, CSV_FIELDS, LINTQ_DIR, ROOT, SUITES, WORK,  # noqa: E402
                                 docker, parse_sarif, run, tool_versions, warning_key)

OUT = os.path.join(ROOT, "data", "lintq_screening")
FILE_RE = re.compile(r"^(buggy|fixed)_(\d+)(_min)?\.py$")


def collect(bugs):
    files = {"buggy": [], "fixed": []}
    for d in sorted(glob.glob(os.path.join(ROOT, "bugs", "Bugs4Q-FW-*"))):
        n = d.rsplit("-", 1)[1]
        if bugs and n not in bugs:
            continue
        for p in sorted(glob.glob(os.path.join(d, "*.py"))):
            m = FILE_RE.match(os.path.basename(p))
            if m and m.group(2) == n:
                files[m.group(1)].append(p)
    return files


def analyze_batch(group, paths, suite_file, image, versions, timeout):
    work = os.path.join(WORK, "_batch", group)
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(os.path.join(work, "files"))
    for p in paths:
        shutil.copy2(p, os.path.join(work, "files", os.path.basename(p)))
    shutil.copy2(os.path.join(LINTQ_DIR, suite_file), os.path.join(work, suite_file))
    create = docker(image, work, [
        "codeql", "database", "create", CONTAINER_DATA + "/codeql_db", "--language=python",
        "--source-root", CONTAINER_DATA + "/files", "--overwrite"])
    analyze = docker(image, work, [
        "codeql", "database", "analyze", "--format=sarifv2.1.0", "--threads=0",
        "--output=" + CONTAINER_DATA + "/lintq.sarif", "--rerun", "--",
        CONTAINER_DATA + "/codeql_db", CONTAINER_DATA + "/" + suite_file])
    log = ["fecha: %s" % datetime.datetime.now().isoformat(timespec="seconds"),
           "grupo: %s  archivos: %d" % (group, len(paths)), "suite: %s" % suite_file]
    log += ["%s: %s" % kv for kv in versions.items()]
    log += ["archivo: %s" % os.path.relpath(p, ROOT).replace("\\", "/") for p in paths]
    status = "ok"
    for label, cmd in (("create", create), ("analyze", analyze)):
        code, out, err, dur = run(cmd, timeout)
        log += ["", "=== %s" % label, "comando: %s" % subprocess.list2cmdline(cmd),
                "exit code: %s  duración: %.1fs" % (code, dur), "--- stdout", out, "--- stderr", err]
        print("  %s %s: exit %s (%.0fs)" % (group, label, code, dur), flush=True)
        if code != 0:
            status = "analysis_error (%s exit %s)" % (label, code)
            break
    rows = []
    sarif = os.path.join(work, "lintq.sarif")
    if status == "ok" and os.path.exists(sarif):
        shutil.copy2(sarif, os.path.join(OUT, group + ".sarif"))
        for r in parse_sarif(sarif, "", ""):
            m = FILE_RE.match(os.path.basename(r["file"]))
            if not m:
                continue
            r["bug_id"] = "Bugs4Q-FW-" + m.group(2)
            r["variant"] = m.group(1) + ("_min" if m.group(3) else "")
            rows.append(r)
    elif status == "ok":
        status = "analysis_error (no se generó SARIF)"
    log += ["", "estado: %s" % status, "warnings: %d" % len(rows)]
    with open(os.path.join(OUT, group + ".log"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    return status, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bugs", nargs="*")
    ap.add_argument("--suite", choices=sorted(SUITES), default="all")
    ap.add_argument("--image", default="lintq")
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    suite_file = SUITES[a.suite]
    versions = tool_versions(a.image)
    if versions["codeql_cli"].startswith("ERROR"):
        sys.exit("No se pudo ejecutar la imagen '%s': %s" % (a.image, versions["codeql_cli"]))
    files = collect(set(a.bugs))
    print("CodeQL %s, LintQ %s, %d buggy / %d fixed" % (
        versions["codeql_cli"], versions["lintq_commit"][:10], len(files["buggy"]), len(files["fixed"])))

    rows, status = [], {}
    for group in ("buggy", "fixed"):
        status[group], r = analyze_batch(group, files[group], suite_file, a.image, versions, a.timeout)
        rows += r
    rows.sort(key=lambda x: (int(x["bug_id"].rsplit("-", 1)[1]), x["variant"], int(x["start_line"] or 0)))
    with open(os.path.join(OUT, "warnings.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)

    fields = ["bug_id", "buggy_warnings", "fixed_warnings", "fixed_min_warnings", "buggy_rules",
              "only_in_buggy", "only_in_fixed", "high_precision_only_in_buggy"]
    summary = []
    for n in sorted({os.path.basename(p).split("_")[1].split(".")[0] for p in files["buggy"]}, key=int):
        bid = "Bugs4Q-FW-" + n
        by = {v: [r for r in rows if r["bug_id"] == bid and r["variant"] == v]
              for v in ("buggy", "fixed", "fixed_min")}
        has_fixed = any(os.path.basename(p) == "fixed_%s.py" % n for p in files["fixed"])
        kb = {warning_key(r) for r in by["buggy"]}
        kf = {warning_key(r) for r in by["fixed"]}
        only_b = [r for r in by["buggy"] if warning_key(r) not in kf]
        err = lambda g: "" if status[g] == "ok" else status[g]
        summary.append({
            "bug_id": bid,
            "buggy_warnings": err("buggy") or len(by["buggy"]),
            "fixed_warnings": err("fixed") or (len(by["fixed"]) if has_fixed else "sin fixed"),
            "fixed_min_warnings": len(by["fixed_min"]) if by["fixed_min"] else "",
            "buggy_rules": "; ".join(sorted({r["rule_id"] for r in by["buggy"]})),
            "only_in_buggy": "; ".join("%s L%s" % (r["rule_id"], r["start_line"]) for r in only_b),
            "only_in_fixed": "; ".join("%s: %s" % k for k in sorted(kf - kb)),
            "high_precision_only_in_buggy": sum(1 for r in only_b if r["precision"] == "high"),
        })
        print("%-14s buggy=%-3s fixed=%-9s solo_buggy=%s" % (
            bid, summary[-1]["buggy_warnings"], summary[-1]["fixed_warnings"], summary[-1]["only_in_buggy"]))
    with open(os.path.join(OUT, "summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(summary)
    print("Salidas en %s" % os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
