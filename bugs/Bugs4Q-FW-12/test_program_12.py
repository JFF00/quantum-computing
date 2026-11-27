"""Test a nivel de programa (escrito para este proyecto, piloto).

Ejecuta el archivo indicado en BUG_PROGRAM (por defecto buggy_12.py). El módulo
program_harness registra el circuito y el resultado de la llamada a execute()
del programa e inyecta una semilla fija (seed_simulator).

Oráculo (lo que pide el issue qiskit-terra#6571): el programa aplica H a los 2
qubits de 'qreg' y quiere guardar sus mediciones en el registro clásico que ya
creó ('creg', 2 bits). Entonces:
  - el circuito ejecutado no debe tener bits clásicos extra (2 en total), y
  - los resultados deben ser cadenas de 2 bits, con los 4 valores posibles
    ('00', '01', '10', '11'), porque ambos qubits están en superposición.
Con el error, measure_all() crea un registro nuevo y deja 'creg' vacío, así
que las claves salen como '00 00', '01 00', ...
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from program_harness import ProgramRun, program_path  # noqa: E402

EXPECTED_KEYS = ["00", "01", "10", "11"]


class TestProgram12(unittest.TestCase):
    def test_program_12(self):
        run = ProgramRun(program_path(HERE, "buggy_12.py")).run()
        self.assertTrue(run.executions, "el programa no llamó a execute()")
        circuits, result = run.executions[-1]
        circuit = circuits[0]
        counts = result.get_counts(circuit)
        print("bits clásicos:", circuit.num_clbits, "cuentas:", counts)
        self.assertEqual(circuit.num_clbits, 2,
                         "el circuito tiene %d bits clásicos; las mediciones deberían ir al "
                         "registro existente de 2 bits" % circuit.num_clbits)
        self.assertEqual(sorted(counts), EXPECTED_KEYS,
                         "resultados %s; se esperaban los 4 valores de 2 bits" % sorted(counts))


if __name__ == "__main__":
    unittest.main(argv=[""])
