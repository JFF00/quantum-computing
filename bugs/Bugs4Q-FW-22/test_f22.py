import unittest
from qiskit.circuit.library import ZZFeatureMap


class Test(unittest.TestCase):
    def test_f22(self):
        zz = ZZFeatureMap(2, entanglement="full", reps=2)
        drawing = str(zz.decompose().draw("text"))

        print(drawing)

        self.assertEqual(drawing.count('┤ H ├'), 4)


if __name__ == '__main__':
    unittest.main(argv=[''])
