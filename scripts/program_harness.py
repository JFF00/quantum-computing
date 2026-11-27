"""Ejecuta un programa Qiskit (buggy, fixed o parche) y expone lo que hizo.

Lo usan los tests `bugs/<id>/test_program_N.py`. A diferencia de los tests del
Framework (que copian el código del programa dentro del test), estos tests
ejecutan el ARCHIVO del programa, de modo que sirven para validar un parche.

Qué programa se ejecuta: variable de entorno BUG_PROGRAM (ruta relativa a la
carpeta del bug o absoluta). Si no está definida, se usa el buggy.

    BUG_PROGRAM=fixed_8.py python test_program_8.py

Compatible con Python 3.8 y qiskit-terra 0.12 – 0.18 (entornos del piloto).
"""
import contextlib
import io
import os
import runpy

SEED = 1234  # semilla inyectada en execute() si el programa no fija una


def program_path(bug_dir, default):
    p = os.environ.get("BUG_PROGRAM", default)
    return p if os.path.isabs(p) else os.path.join(bug_dir, p)


class ProgramRun:
    """Resultado de ejecutar el programa: globals, stdout y llamadas a execute()."""

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.globals = {}
        self.stdout = ""
        self.executions = []  # lista de (circuitos, Result)

    def run(self):
        import qiskit

        original = qiskit.execute
        runs = self.executions

        def recording_execute(experiments, backend, *args, **kwargs):
            kwargs.setdefault("seed_simulator", SEED)
            job = original(experiments, backend, *args, **kwargs)
            result = job.result()
            circuits = experiments if isinstance(experiments, list) else [experiments]
            runs.append((circuits, result))

            class _Job:  # devuelve siempre el mismo Result ya calculado
                def result(self, *a, **k):
                    return result

                def __getattr__(self, name):
                    return getattr(job, name)

            return _Job()

        qiskit.execute = recording_execute
        buf = io.StringIO()
        cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(self.path))
            with contextlib.redirect_stdout(buf):
                self.globals = runpy.run_path(self.path, run_name="__main__")
        finally:
            os.chdir(cwd)
            qiskit.execute = original
            self.stdout = buf.getvalue()
        return self


def clbit_value_counts(circuit, counts, clbit):
    """Distribución {'0': n, '1': m} de un bit clásico a partir de las cuentas."""
    regs = list(circuit.cregs)
    reg = getattr(clbit, "register", None)
    idx = getattr(clbit, "index", None)
    if reg is None:  # terra >= 0.17 con bits sin registro
        for r in regs:
            if clbit in list(r):
                reg, idx = r, list(r).index(clbit)
    ri = regs.index(reg)
    out = {"0": 0, "1": 0}
    for key, n in counts.items():
        parts = key.split()
        part = parts[len(regs) - 1 - ri] if len(parts) == len(regs) else key.replace(" ", "")
        if len(parts) != len(regs):  # un solo string sin espacios
            offset = sum(r.size for r in regs[:ri])
            part = part[len(part) - offset - reg.size: len(part) - offset]
        out[part[len(part) - 1 - idx]] += n
    return out


def last_measurement_of(circuit, qubit):
    """Bit clásico donde se mide por última vez `qubit` (o None si no se mide)."""
    clbit = None
    for item in circuit.data:
        inst, qargs, cargs = item[0], item[1], item[2]
        if inst.name == "measure" and qargs[0] == qubit:
            clbit = cargs[0]
    return clbit
