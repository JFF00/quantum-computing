"""Ejecuta LintQ (consultas CodeQL para Qiskit) sobre las versiones buggy/fixed de cada bug.

Uso (desde la raíz del proyecto, con cualquier Python >= 3.7 y Docker en marcha):

    python scripts/run_static_analysis.py                 # bugs de data/selected_bugs.csv
    python scripts/run_static_analysis.py 7 21            # bugs concretos
    python scripts/run_static_analysis.py 21 --suite high # solo checkers de precisión alta

Requisitos:
  - Imagen Docker `lintq` construida a partir de tools/LintQ (CodeQL CLI 2.11.2 fijado por
    LintQ). Ver docs/static_analysis.md para el comando exacto de construcción.

Qué hace, por bug y por variante (buggy, fixed y fixed_min si existe):
  1. Copia SOLO ese archivo .py a work/lintq/<bug>/<variante>/files/ (aislado: una base de
     datos CodeQL por archivo, así los warnings de buggy y fixed no se mezclan).
  2. `codeql database create --language=python` dentro del contenedor.
  3. `codeql database analyze` con la suite de LintQ -> SARIF v2.1.0 original.
  4. Convierte el SARIF a una tabla (regla, precisión, severidad, archivo, línea, mensaje).

Salidas (evidencia versionada):
  bugs/<bug>/static_analysis/<variante>.sarif   reporte original de LintQ, sin modificar
  bugs/<bug>/static_analysis/<variante>.csv     tabla de warnings derivada del SARIF
  bugs/<bug>/static_analysis/<variante>.log     comandos, versiones, exit codes, stdout/stderr
  bugs/<bug>/static_analysis/summary.json       conteos y diferencia buggy vs fixed
  data/static_warnings.csv                      tabla agregada de todos los bugs analizados

Un exit code distinto de 0 en create/analyze se registra como "analysis_error", nunca como
"0 warnings". La ausencia de warnings solo se reporta si el análisis terminó correctamente.
"""
import argparse
import csv
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINTQ_DIR = os.path.join(ROOT, "tools", "LintQ")
WORK = os.path.join(ROOT, "work", "lintq")
CONTAINER_DATA = "/home/codeql/project/data"
SUITES = {"all": "LintQ-all.qls", "high": "LintQ.qls"}
CSV_FIELDS = ["bug_id", "variant", "file", "rule_id", "rule_name", "precision", "severity",
              "start_line", "start_column", "end_line", "end_column", "message"]


def bug_id(n):
    return "Bugs4Q-FW-%s" % n


def selected_bugs():
    path = os.path.join(ROOT, "data", "selected_bugs.csv")
    with open(path, encoding="utf-8") as f:
        return [row["bug_id"].rsplit("-", 1)[1] for row in csv.DictReader(f)]


def variants(n):
    """Archivos a analizar: buggy, fixed y fixed_min (referencia mínima) si existe."""
    d = os.path.join(ROOT, "bugs", bug_id(n))
    out = []
    for name, fname in (("buggy", "buggy_%s.py" % n), ("fixed", "fixed_%s.py" % n),
                        ("fixed_min", "fixed_%s_min.py" % n)):
        p = os.path.join(d, fname)
        if os.path.exists(p):
            out.append((name, p))
    return out


def run(cmd, timeout):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        out, err, code = (p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace"),
                          p.returncode)
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", "replace")
        err = (e.stderr or b"").decode("utf-8", "replace") + "\nTIMEOUT tras %ss" % timeout
        code = "timeout"
    return code, out, err, time.time() - t0


def docker(image, mount, args):
    return ["docker", "run", "--rm", "-v", "%s:%s" % (mount, CONTAINER_DATA), image] + args


def tool_versions(image):
    code, out, err, _ = run(["docker", "run", "--rm", image, "codeql", "version", "--format=terse"], 120)
    codeql = out.strip() if code == 0 else "ERROR: %s" % err.strip()
    code, out, _, _ = run(["docker", "image", "inspect", image, "--format", "{{.Id}}"], 60)
    image_id = out.strip() if code == 0 else "desconocido"
    code, out, _, _ = run(["git", "-C", LINTQ_DIR, "rev-parse", "HEAD"], 60)
    lintq_commit = out.strip() if code == 0 else "desconocido"
    return {"codeql_cli": codeql, "docker_image": image, "docker_image_id": image_id,
            "lintq_repo": "https://github.com/sola-st/LintQ", "lintq_commit": lintq_commit}


def parse_sarif(path, bid, variant):
    with open(path, encoding="utf-8") as f:
        sarif = json.load(f)
    rows = []
    for r in sarif.get("runs", []):
        rules = {}
        driver_rules = r.get("tool", {}).get("driver", {}).get("rules", [])
        for ext in r.get("tool", {}).get("extensions", []):
            driver_rules = driver_rules + ext.get("rules", [])
        for rule in driver_rules:
            rules[rule.get("id")] = rule
        for res in r.get("results", []):
            rid = res.get("ruleId") or res.get("rule", {}).get("id")
            rule = rules.get(rid, {})
            props = rule.get("properties", {})
            loc = (res.get("locations") or [{}])[0].get("physicalLocation", {})
            region = loc.get("region", {})
            rows.append({
                "bug_id": bid, "variant": variant,
                "file": loc.get("artifactLocation", {}).get("uri", ""),
                "rule_id": rid,
                "rule_name": rule.get("name", ""),
                "precision": props.get("precision", ""),
                "severity": props.get("problem.severity", res.get("level", "")),
                "start_line": region.get("startLine", ""),
                "start_column": region.get("startColumn", 1),  # SARIF: 1 por defecto
                "end_line": region.get("endLine", region.get("startLine", "")),
                "end_column": region.get("endColumn", ""),
                "message": res.get("message", {}).get("text", "").replace("\n", " "),
            })
    rows.sort(key=lambda x: (x["start_line"] or 0, x["rule_id"] or ""))
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)


def analyze_variant(n, variant, src, suite_file, image, versions, timeout):
    bid = bug_id(n)
    out_dir = os.path.join(ROOT, "bugs", bid, "static_analysis")
    os.makedirs(out_dir, exist_ok=True)
    work = os.path.join(WORK, bid, variant)
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(os.path.join(work, "files"))
    shutil.copy2(src, os.path.join(work, "files", os.path.basename(src)))
    shutil.copy2(os.path.join(LINTQ_DIR, suite_file), os.path.join(work, suite_file))

    create = docker(image, work, [
        "codeql", "database", "create", CONTAINER_DATA + "/codeql_db", "--language=python",
        "--source-root", CONTAINER_DATA + "/files", "--overwrite"])
    analyze = docker(image, work, [
        "codeql", "database", "analyze", "--format=sarifv2.1.0", "--threads=0",
        "--output=" + CONTAINER_DATA + "/lintq.sarif", "--rerun", "--",
        CONTAINER_DATA + "/codeql_db", CONTAINER_DATA + "/" + suite_file])

    log = ["fecha: %s" % datetime.datetime.now().isoformat(timespec="seconds"),
           "bug: %s  variante: %s  archivo: %s" % (bid, variant, os.path.relpath(src, ROOT)),
           "suite: %s" % suite_file]
    log += ["%s: %s" % kv for kv in versions.items()]
    status, rows = "ok", []
    for label, cmd in (("create", create), ("analyze", analyze)):
        code, out, err, dur = run(cmd, timeout)
        log += ["", "=== %s" % label, "comando: %s" % subprocess.list2cmdline(cmd),
                "exit code: %s  duración: %.1fs" % (code, dur), "--- stdout", out, "--- stderr", err]
        if code != 0:
            status = "analysis_error (%s exit %s)" % (label, code)
            break

    sarif_src = os.path.join(work, "lintq.sarif")
    if status == "ok" and os.path.exists(sarif_src):
        shutil.copy2(sarif_src, os.path.join(out_dir, variant + ".sarif"))
        rows = parse_sarif(sarif_src, bid, variant)
        write_csv(os.path.join(out_dir, variant + ".csv"), rows)
    elif status == "ok":
        status = "analysis_error (no se generó SARIF)"
    log += ["", "estado: %s" % status, "warnings: %d" % len(rows)]
    with open(os.path.join(out_dir, variant + ".log"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    return status, rows


def warning_key(row):
    # Identifica un warning sin depender de la línea (buggy y fixed tienen líneas distintas):
    # los mensajes de LintQ citan posiciones como "(17, 1)", que se normalizan.
    return (row["rule_id"], re.sub(r"\(\d+, \d+\)", "(L, C)", row["message"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bugs", nargs="*", help="números de bug (por defecto, data/selected_bugs.csv)")
    ap.add_argument("--suite", choices=sorted(SUITES), default="all",
                    help="all = los 10 checkers de LintQ (high+medium); high = LintQ.qls")
    ap.add_argument("--image", default="lintq")
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args()

    bugs = a.bugs or selected_bugs()
    suite_file = SUITES[a.suite]
    versions = tool_versions(a.image)
    if versions["codeql_cli"].startswith("ERROR"):
        sys.exit("No se pudo ejecutar la imagen '%s': %s" % (a.image, versions["codeql_cli"]))
    print("CodeQL %s, LintQ %s, suite %s" % (versions["codeql_cli"], versions["lintq_commit"][:10], suite_file))

    all_rows = []
    for n in bugs:
        bid = bug_id(n)
        summary = {"bug_id": bid, "suite": suite_file, "tool": versions,
                   "date": datetime.datetime.now().isoformat(timespec="seconds"), "variants": {}}
        per_variant = {}
        for variant, src in variants(n):
            status, rows = analyze_variant(n, variant, src, suite_file, a.image, versions, a.timeout)
            per_variant[variant] = rows
            all_rows += rows
            summary["variants"][variant] = {
                "file": os.path.relpath(src, ROOT).replace("\\", "/"), "status": status,
                "warnings": len(rows),
                "by_rule": {r: sum(1 for x in rows if x["rule_id"] == r)
                            for r in sorted({x["rule_id"] for x in rows})}}
            print("%-14s %-10s %-40s warnings=%d" % (bid, variant, status, len(rows)))
        if "buggy" in per_variant:
            buggy_keys = {warning_key(r) for r in per_variant["buggy"]}
            for ref in ("fixed", "fixed_min"):
                if ref in per_variant and summary["variants"][ref]["status"] == "ok":
                    ref_keys = {warning_key(r) for r in per_variant[ref]}
                    summary["diff_buggy_vs_" + ref] = {
                        "only_in_buggy": sorted("%s: %s" % k for k in buggy_keys - ref_keys),
                        "only_in_" + ref: sorted("%s: %s" % k for k in ref_keys - buggy_keys),
                        "in_both": sorted("%s: %s" % k for k in buggy_keys & ref_keys)}
        with open(os.path.join(ROOT, "bugs", bid, "static_analysis", "summary.json"), "w",
                  encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    # Tabla agregada: se reescriben solo las filas de los bugs analizados en esta ejecución.
    agg = os.path.join(ROOT, "data", "static_warnings.csv")
    done = {bug_id(n) for n in bugs}
    keep = []
    if os.path.exists(agg):
        with open(agg, encoding="utf-8") as f:
            keep = [r for r in csv.DictReader(f) if r["bug_id"] not in done]
    write_csv(agg, keep + all_rows)
    print("Tabla agregada: %s" % os.path.relpath(agg, ROOT))


if __name__ == "__main__":
    main()
