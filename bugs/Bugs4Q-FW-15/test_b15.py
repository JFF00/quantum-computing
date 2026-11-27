import unittest
from qiskit.circuit import Parameter
from qiskit.circuit.library import RealAmplitudes
from qiskit.opflow import CircuitStateFn
from qiskit.opflow.gradients import Gradient

class Test(unittest.TestCase):

    
    def test_b15(self):
        try:
            ansatz = RealAmplitudes(num_qubits=1, reps=1)
            for method in ['param_shift', 'fin_diff', 'lin_comb']:
                grad = Gradient(method).convert(CircuitStateFn(ansatz))
                print(f"{method} is ok")
        except TypeError as e:
            # Adaptado para este proyecto: el comportamiento esperado (issue) es
            # que 'lin_comb' no lance TypeError.
            print('Reason:', e)
            self.fail('TypeError raised: %s' % e)

if __name__ == '__main__':
    unittest.main(argv=[''])
