import unittest
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, Aer, transpile, assemble


def quantum_circuit(num_qubits, initial_state):
    qr = QuantumRegister(num_qubits)
    qc = QuantumCircuit(qr)
    qc.initialize(initial_state)
    return qc


class Test(unittest.TestCase):
    def test_f41(self):
        qc = quantum_circuit(num_qubits=2, initial_state=[0, 0, 1, 0])

        backend = Aer.get_backend('statevector_simulator')
        qobj = transpile(qc, backend)
        job = assemble(qobj)
        run_job = backend.run(job)
        sv = run_job.result().get_statevector()

        print(sv)

        self.assertEqual(str(np.round(np.asarray(sv), 3).tolist()),
                         '[0j, 0j, (1+0j), 0j]')


if __name__ == '__main__':
    unittest.main(argv=[''])
