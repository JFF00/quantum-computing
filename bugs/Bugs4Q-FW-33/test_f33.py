import unittest
from qiskit import *


class Test(unittest.TestCase):
    def test_f33(self):
        c = [ClassicalRegister(1) for _ in range(2)]
        q = QuantumRegister(1)
        qc = QuantumCircuit(q)
        for register in c:
            qc.add_register(register)
            qc.h(q)
        qc.measure(q, c[0])
        qc.x(q[0]).c_if(c[0], 0)
        qc.measure(q, c[1])

        print(qc)

        x_gate = [inst for inst, _, _ in qc.data if inst.name == 'x'][0]
        self.assertEqual(x_gate.condition[1], 0)


if __name__ == '__main__':
    unittest.main(argv=[''])
