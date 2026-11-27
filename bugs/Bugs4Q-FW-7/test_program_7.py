"""Test a nivel de programa (escrito para este proyecto, piloto).

Ejecuta el archivo indicado en BUG_PROGRAM (por defecto buggy_7.py) y comprueba
su estado final. Requisito para el programa: definir `circuit` (circuito con la
puerta controlada) y `dag` (DAG resultante tras quitar el control).

Oráculo: al quitar el control, la puerta base debe quedar aplicada sobre los
mismos qubits objetivo, y en el mismo orden, que en la puerta controlada original.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from program_harness import ProgramRun, program_path  # noqa: E402

from qiskit.converters import dag_to_circuit  # noqa: E402


class TestProgram7(unittest.TestCase):
    def test_program_7(self):
        run = ProgramRun(program_path(HERE, "buggy_7.py")).run()
        circuit, dag = run.globals["circuit"], run.globals["dag"]

        ctrl = [i for i in circuit.data if i[0].name != "barrier"][0]
        targets = [circuit.qubits.index(q) for q in ctrl[1][ctrl[0].num_ctrl_qubits:]]

        result = dag_to_circuit(dag)
        ops = [i for i in result.data if i[0].name != "barrier"]
        self.assertEqual(len(ops), 1, "el circuito resultante debe tener una sola puerta")
        got = [result.qubits.index(q) for q in ops[0][1]]
        self.assertEqual(got, targets,
                         "la puerta sin control se aplica sobre qubits %s; se esperaban %s" % (got, targets))


if __name__ == "__main__":
    unittest.main(argv=[""])
