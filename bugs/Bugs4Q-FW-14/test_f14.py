import unittest
from qiskit import Aer, QuantumCircuit

from qiskit.opflow import CircuitSampler, StateFn, Z, Y, I
from qiskit.utils import QuantumInstance
from qiskit.opflow.expectations import PauliExpectation

class Test(unittest.TestCase):
    def test_f14(self):
        
        state = QuantumCircuit(2)

        state.h(1)
        state.sdg(1)
        state.cz(0, 1)
        state.h(1)
        print(state)
        
        obs = (Z ^ I) - 1j * (Y ^ I)
        exp_val = ~StateFn(obs) @ StateFn(state)
        exp_val = PauliExpectation().convert(exp_val).reduce()

        print(exp_val)

        eval_val = exp_val.eval()
        qasm_val = CircuitSampler(QuantumInstance(Aer.get_backend('qasm_simulator'),
                                  shots=100000)).convert(exp_val).eval()
        print('Eval ', eval_val)
        print('Qasm ', qasm_val)

        # Adaptado para este proyecto: el comportamiento esperado (issue) es que
        # la salida QASM coincida con eval (salvo ruido de muestreo).
        self.assertAlmostEqual(complex(qasm_val), complex(eval_val), delta=0.05)


if __name__ == '__main__':
    unittest.main(argv=[''])
