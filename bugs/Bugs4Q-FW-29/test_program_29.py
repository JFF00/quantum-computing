"""Test a nivel de programa (escrito para este proyecto, piloto).

Ejecuta el archivo indicado en BUG_PROGRAM (por defecto buggy_29.py). El módulo
program_harness registra el resultado de la llamada a execute() del programa e
inyecta una semilla fija (seed_simulator), así que el resultado es determinista.

Oráculo: en la estimación de fase de theta = 0.78 con 3 qubits, el resultado
más frecuente debe ser '011' y concentrar al menos la mitad de los shots
(mismo resultado esperado que el test del Framework: 750 +- 250 sobre 1000).
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from program_harness import ProgramRun, program_path  # noqa: E402

EXPECTED = "011"


class TestProgram29(unittest.TestCase):
    def test_program_29(self):
        run = ProgramRun(program_path(HERE, "buggy_29.py")).run()
        self.assertTrue(run.executions, "el programa no llamó a execute()")
        counts = run.executions[-1][1].get_counts()
        print(counts)
        total = sum(counts.values())
        best = max(counts, key=counts.get)
        self.assertEqual(best, EXPECTED, "resultado más frecuente %r; se esperaba %r" % (best, EXPECTED))
        self.assertGreaterEqual(counts[EXPECTED] / total, 0.5)


if __name__ == "__main__":
    unittest.main(argv=[""])
