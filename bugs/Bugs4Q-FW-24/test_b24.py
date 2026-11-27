import unittest
import qiskit
from qiskit import *
from qiskit import IBMQ

class Test(unittest.TestCase):
	def test_b24(self):
		qr = QuantumRegister(2)
		cr = ClassicalRegister(2)
		circuit = QuantumCircuit(qr, cr)
		#%matplotlib inline
		circuit.draw(output='mpl')
		
		try:
			circuit.h(qr(0))
		except TypeError:
			self.fail("TypeError")

if __name__ == '__main__':
    unittest.main(argv=[''])
