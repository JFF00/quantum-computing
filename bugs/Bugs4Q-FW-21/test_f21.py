import unittest
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import BasicAer
from qiskit import execute


class Test(unittest.TestCase):
    def test_f21(self):
        backend = BasicAer.get_backend("qasm_simulator")

        q = QuantumRegister(3, "q")
        c0 = ClassicalRegister(1, "c0")
        c1 = ClassicalRegister(1, "c1")
        c2 = ClassicalRegister(1, "c2")
        qc = QuantumCircuit(q, c0, c1, c2, name="teleport")

        # Prepare an initial state
        qc.x(q[0])

        # Prepare a Bell pair
        qc.h(q[1])
        qc.cx(q[1], q[2])

        # Barrier following state preparation
        qc.barrier(q)

        # Measure in the Bell basis
        qc.cx(q[0], q[1])
        qc.h(q[0])
        qc.measure(q[0], c0[0])
        qc.measure(q[1], c1[0])

        # Apply a correction
        qc.barrier(q)
        qc.z(q[2]).c_if(c0, 1)
        qc.x(q[2]).c_if(c1, 1)
        qc.measure(q[2], c2[0])

        job = execute(qc, backend=backend, shots=1, memory=True)
        result = job.result().get_memory()[0]
        print(result)

        self.assertEqual(result[0], '1')


if __name__ == '__main__':
    unittest.main(argv=[''])
