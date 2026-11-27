import unittest


class Test(unittest.TestCase):

    
    def test_b1(self):
        try:
            from qiskit import QuantumCircuit
            qc = QuantumCircuit(3)
            qc.cx(0, 1, label='Label', ctrl_state=0)
            qc.ccx(0, 1, 2, label='Label', ctrl_state=1)
        except TypeError as e:
            self.fail('TypeError raised: %s' % e)

if __name__ == '__main__':
    unittest.main(argv=[''])
