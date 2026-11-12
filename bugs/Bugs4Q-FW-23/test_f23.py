import io
import unittest
from contextlib import redirect_stdout
import matplotlib
matplotlib.use('Agg')
from qiskit import *


class Test(unittest.TestCase):
    def test_f23(self):
        qr = QuantumRegister(2)
        cr = ClassicalRegister(2)

        Qc = QuantumCircuit(qr, cr)

        out = io.StringIO()
        with redirect_stdout(out):
            print('This is the initial state')
            Qc.draw('mpl').show()

        print(out.getvalue())

        self.assertEqual(out.getvalue(), 'This is the initial state\n')


if __name__ == '__main__':
    unittest.main(argv=[''])
