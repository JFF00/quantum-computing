import unittest
from qiskit import *


class Test(unittest.TestCase):
    def test_b33(self):
        q = QuantumRegister(1)
        c = ClassicalRegister(2)
        qc = QuantumCircuit(q, c)

        qc.h(q)
        qc.measure(q[0], c[0])
        qc.x(q[0]).c_if(c[0], 0)
        qc.measure(q[0], c[1])

        print(qc)

        x_gate = [inst for inst, _, _ in qc.data if inst.name == 'x'][0]
        self.assertEqual(x_gate.condition[1], 0)


if __name__ == '__main__':
    unittest.main(argv=[''])
