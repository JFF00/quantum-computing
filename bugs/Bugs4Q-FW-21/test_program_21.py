"""Test a nivel de programa (escrito para este proyecto, piloto).

Ejecuta el archivo indicado en BUG_PROGRAM (por defecto buggy_21.py). El módulo
program_harness registra el circuito y el resultado de la llamada a execute()
del programa (con semilla fija).

Oráculo: el programa prepara |1> en el qubit 0 y lo teleporta al qubit 2, así
que en la ejecución el bit clásico asociado al qubit 2 debe valer '1' en todos
los shots. Si el qubit 2 no se mide en el circuito ejecutado, se lee el bit
clásico 2 (el que el programa usa para ese qubit).

Nota: fixed_21.py (Framework) teleporta otro estado (u(0.3, 0.2, 0.1)), por lo
que la referencia para este test es fixed_21_min.py.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from program_harness import (ProgramRun, clbit_value_counts,  # noqa: E402
                             last_measurement_of, program_path)


class TestProgram21(unittest.TestCase):
    def test_program_21(self):
        run = ProgramRun(program_path(HERE, "buggy_21.py")).run()
        self.assertTrue(run.executions, "el programa no llamó a execute()")
        circuits, result = run.executions[-1]
        circuit = circuits[0]

        clbit = last_measurement_of(circuit, circuit.qubits[2]) or circuit.clbits[2]
        values = clbit_value_counts(circuit, result.get_counts(circuit), clbit)
        print("bit del qubit teleportado:", values)
        self.assertEqual(values["0"], 0, "el qubit teleportado debería medirse siempre como '1': %s" % values)


if __name__ == "__main__":
    unittest.main(argv=[""])
