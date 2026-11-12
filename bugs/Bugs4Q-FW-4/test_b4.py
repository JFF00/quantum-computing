import unittest
from qiskit import *
from qiskit.circuit.library import CDKMRippleCarryAdder


class Test(unittest.TestCase):
    def test_b4(self):
        p = QuantumCircuit(8)
        p.x(0)
        q = QuantumCircuit(8)
        q.x(0)

        adder = CDKMRippleCarryAdder(8)
        adder.compose(p, [1, 2, 3, 4, 5, 6, 7, 8], inplace=True, front=True)
        adder.compose(q, [9, 10, 11, 12, 13, 14, 15, 16], inplace=True, front=True)

        backend = Aer.get_backend('statevector_simulator')
        job = backend.run(adder)
        result = job.result()

        print(result.status)

        self.assertEqual(result.status, 'COMPLETED')


if __name__ == '__main__':
    unittest.main(argv=[''])
