"""Test a nivel de programa (escrito para este proyecto, piloto).

Ejecuta el archivo indicado en BUG_PROGRAM (por defecto buggy_14.py) y lee la
línea `Qasm <valor>` que imprime el programa.

Oráculo: el valor esperado estimado con el simulador QASM debe ser 1j (el valor
exacto que indica el propio programa en su comentario `# = 0+1j`), con tolerancia
0.05 por ruido de muestreo (100000 shots).
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from program_harness import ProgramRun, program_path  # noqa: E402

EXPECTED = 1j


class TestProgram14(unittest.TestCase):
    def test_program_14(self):
        run = ProgramRun(program_path(HERE, "buggy_14.py")).run()
        print(run.stdout)
        m = re.findall(r"Qasm\s+\(?([-+0-9.e]+[-+][0-9.e]+j)\)?", run.stdout)
        self.assertTrue(m, "el programa no imprimió la línea 'Qasm <valor>'")
        qasm = complex(m[-1])
        self.assertAlmostEqual(qasm, EXPECTED, delta=0.05,
                               msg="valor QASM %s; se esperaba %s" % (qasm, EXPECTED))


if __name__ == "__main__":
    unittest.main(argv=[""])
