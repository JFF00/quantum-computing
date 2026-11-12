import unittest
import numpy as np
from qiskit import *
from qiskit.quantum_info import *


class Test(unittest.TestCase):
    def test_f34(self):
        sv = Statevector.from_label('10')
        mycircuit = QuantumCircuit(2)
        mycircuit.h(0)
        mycircuit.cx(0, 1)
        new_sv = sv.evolve(mycircuit)

        print(new_sv.data)

        self.assertEqual(str(np.round(new_sv.data, 3).tolist()),
                         '[0j, (0.707+0j), (0.707+0j), 0j]')


if __name__ == '__main__':
    unittest.main(argv=[''])
