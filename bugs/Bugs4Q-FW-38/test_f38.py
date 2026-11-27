import unittest
from qiskit import *
from qiskit.quantum_info import Statevector

class Test(unittest.TestCase):
    def test_f38(self):
        qc = QuantumCircuit(2)
        st0 = Statevector.from_instruction(qc)
        qc.h(0)
        st1 = Statevector.from_instruction(qc)
        qc.cnot(0, 1)
        st2 = Statevector.from_instruction(qc)

        print(st0)
        print(st1)
        print(st2)


if __name__ == '__main__':
    unittest.main()