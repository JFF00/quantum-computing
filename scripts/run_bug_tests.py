"""Ejecuta los tests buggy/fixed de un bug dentro de SU entorno aislado.

Uso (desde la raíz del proyecto, con cualquier Python >= 3.7):

    python scripts/run_bug_tests.py 7            # 3 ejecuciones de cada test
    python scripts/run_bug_tests.py 7 --runs 5

Convenciones:
  - Entorno del bug:  envs/bug<N>/.venv   (creado con envs/bug<N>/requirements.txt)
  - Carpeta del bug:  bugs/Bugs4Q-FW-<N>/ con test_b<N>.py y test_f<N>.py
  - Logs generados:   bugs/Bugs4Q-FW-<N>/logs/{buggy,fixed}_test_run<k>.log
                      bugs/Bugs4Q-FW-<N>/logs/environment.txt  (Python + pip freeze)

Cada log guarda el comando, el intérprete, la fecha, la duración, el exit code,
stdout y stderr sin modificar. Un exit code distinto de 0/1, o un error de
importación, debe interpretarse como "no se pudo iniciar", no como test fallido.
"""
import argparse
import datetime
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def env_python(n):
    venv = os.path.join(ROOT, "envs", "bug%s" % n, ".venv")
    for rel in (("Scripts", "python.exe"), ("bin", "python")):
        p = os.path.join(venv, *rel)
        if os.path.exists(p):
            return p
    sys.exit("No existe el entorno %s. Créelo primero (ver README del bug)." % venv)


def run(cmd, cwd, timeout, extra_env=None):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout, env=dict(os.environ, PYTHONIOENCODING="utf-8",
                                                     MPLBACKEND="Agg", **(extra_env or {})))
        out, err, code = p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace"), p.returncode
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", "replace")
        err = (e.stderr or b"").decode("utf-8", "replace") + "\nTIMEOUT tras %ss" % timeout
        code = "timeout"
    return code, out, err, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bug", help="número del bug en Bugs4Q-Framework (p. ej. 7)")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--program-test", action="store_true",
                    help="ejecuta test_program_N.py contra buggy_N.py y contra la referencia "
                         "(fixed_N_min.py si existe, si no fixed_N.py); logs program_{buggy,fixed}_run<k>.log")
    a = ap.parse_args()

    n = a.bug
    py = env_python(n)
    bug_dir = os.path.join(ROOT, "bugs", "Bugs4Q-FW-%s" % n)
    logs = os.path.join(bug_dir, "logs")
    os.makedirs(logs, exist_ok=True)

    ver = subprocess.run([py, "-c", "import platform;print(platform.python_version())"],
                         stdout=subprocess.PIPE).stdout.decode().strip()
    freeze = subprocess.run([py, "-m", "pip", "freeze", "--all"], stdout=subprocess.PIPE).stdout.decode()
    freeze = "\n".join(l for l in freeze.splitlines() if l.split("==")[0] not in ("pip", "setuptools", "wheel"))
    with open(os.path.join(logs, "environment.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("Python %s\n%s\n" % (ver, freeze))

    if a.program_test:
        # Test a nivel de programa: el mismo test_program_N.py contra cada archivo de programa.
        test = "test_program_%s.py" % n
        ref = "fixed_%s_min.py" % n if os.path.exists(os.path.join(bug_dir, "fixed_%s_min.py" % n)) \
            else "fixed_%s.py" % n
        plan = [("program_buggy", test, {"BUG_PROGRAM": "buggy_%s.py" % n}),
                ("program_fixed", test, {"BUG_PROGRAM": ref})]
    else:
        plan = [("buggy", "test_b%s.py" % n, {}), ("fixed", "test_f%s.py" % n, {})]

    summary = []
    for version, test, extra_env in plan:
        for k in range(1, a.runs + 1):
            cmd = [py, "-W", "ignore", test]
            code, out, err, dt = run(cmd, bug_dir, a.timeout, extra_env)
            name = ("%s_run%d.log" if a.program_test else "%s_test_run%d.log") % (version, k)
            with open(os.path.join(logs, name), "w", encoding="utf-8", newline="\n") as f:
                f.write("# bug: Bugs4Q-FW-%s\n# version: %s\n# run: %d\n" % (n, version, k))
                envtxt = "".join("%s=%s " % kv for kv in extra_env.items())
                f.write("# command: %spython -W ignore %s   (cwd: bugs/Bugs4Q-FW-%s)\n" % (envtxt, test, n))
                f.write("# interpreter: envs/bug%s/.venv (Python %s, %s)\n" % (n, ver, sys.platform))
                f.write("# date: %s\n" % datetime.datetime.now().isoformat(timespec="seconds"))
                f.write("# duration_s: %.2f\n# exit_code: %s\n" % (dt, code))
                f.write("----- stdout -----\n%s\n----- stderr -----\n%s\n" % (out, err))
            summary.append((version, k, code))
            print("%s run%d -> exit %s (%.1fs)" % (version, k, code, dt))
    return summary


if __name__ == "__main__":
    main()
