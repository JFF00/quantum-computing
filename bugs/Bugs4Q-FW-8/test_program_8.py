"""Test a nivel de programa (escrito para este proyecto, piloto).

Ejecuta el archivo indicado en BUG_PROGRAM (por defecto buggy_8.py) y comprueba
el operador final. Requisito para el programa: definir `uni` (Operator del
circuito de 4 qubits).

Oráculo: `uni` debe ser diagonal con estas fases (redondeadas a 3 decimales).
Mismo valor esperado que el test del Framework (que compara la matriz como texto).
"""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from program_harness import ProgramRun, program_path  # noqa: E402

A, B = 0.383, 0.924
EXPECTED_DIAG = [1, A - B * 1j, 1, A - B * 1j, 1, B + A * 1j, 1, B + A * 1j,
                 1, B - A * 1j, 1, B - A * 1j, 1, A + B * 1j, 1, A + B * 1j]


class TestProgram8(unittest.TestCase):
    def test_program_8(self):
        run = ProgramRun(program_path(HERE, "buggy_8.py")).run()
        data = np.asarray(run.globals["uni"].data)

        self.assertEqual(data.shape, (16, 16))
        off = np.abs(data - np.diag(np.diag(data))).max()
        self.assertLess(off, 1e-6, "el operador debería ser diagonal")
        diag = np.round(np.diag(data), 3)
        bad = [i for i, (g, e) in enumerate(zip(diag, EXPECTED_DIAG)) if abs(g - e) > 2e-3]
        self.assertEqual(bad, [], "fases incorrectas en las posiciones diagonales %s:\n%s" % (bad, diag))


if __name__ == "__main__":
    unittest.main(argv=[""])
