import unittest
from qiskit import *
from qiskit.circuit.library import XGate


class Test(unittest.TestCase):
    def test_b6(self):
        qr = QuantumRegister(36, "qr")
        cr = ClassicalRegister(36, 'cr')
        qc = QuantumCircuit(qr, cr)
        for i in range(8, 12):
            qc.h(i)
        gate = XGate().control(num_ctrl_qubits=4, ctrl_state='1111')
        qc.append(gate, [8, 9, 10, 11]+[4])
        qc.barrier()
        for i in range(36):
            qc.measure(i, i)
        backend_sim = Aer.get_backend('qasm_simulator')
        job_sim = execute(qc, backend_sim, shots=1024)
        result_sim = job_sim.result()

        print(result_sim.status)

        self.assertEqual(result_sim.status, 'COMPLETED')


if __name__ == '__main__':
    unittest.main(argv=[''])
